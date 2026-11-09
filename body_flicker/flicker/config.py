"""Loads and validates config.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path


class ConfigError(Exception):
    """The config file is missing a valid value. The message is shown to the user."""


@dataclass(frozen=True)
class CameraConfig:
    index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30


@dataclass(frozen=True)
class SignConfig:
    hold_seconds: float = 0.6
    cooldown_seconds: float = 2.0
    dropout_grace_seconds: float = 0.15
    max_tip_gap: float = 0.35
    extended_ratio: float = 1.2
    curled_ratio: float = 1.1
    thumb_max_reach: float = 0.9


@dataclass(frozen=True)
class EffectConfig:
    style: str = "electric"
    duration_seconds: float = 0.4
    smoke_seconds: float = 1.3
    leaf_seconds: float = 2.6
    spark_seconds: float = 0.8
    mask_feather_px: int = 9
    shake_pixels: float = 9.0
    flash_strength: float = 0.25


@dataclass(frozen=True)
class BackgroundConfig:
    countdown_seconds: float = 5.0
    frames: int = 15
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class VisionConfig:
    input_width: int = 640
    max_rate_hz: float = 15.0
    max_sign_age_seconds: float = 0.3


@dataclass(frozen=True)
class PreviewConfig:
    width: int = 640
    mirror: bool = True


@dataclass(frozen=True)
class Config:
    camera: CameraConfig = field(default_factory=CameraConfig)
    sign: SignConfig = field(default_factory=SignConfig)
    effect: EffectConfig = field(default_factory=EffectConfig)
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    preview: PreviewConfig = field(default_factory=PreviewConfig)


EFFECT_STYLES = ("electric", "smoke")

# Values that may legitimately be zero. Every other number must be positive.
_ZERO_ALLOWED = {
    "camera.index",
    "sign.cooldown_seconds",
    "sign.dropout_grace_seconds",
    "effect.mask_feather_px",
    "effect.shake_pixels",
    "effect.flash_strength",
    "background.countdown_seconds",
}


def _build_section(name: str, section_type: type, values: dict):
    known = {f.name: f for f in fields(section_type)}
    unknown = sorted(set(values) - set(known))
    if unknown:
        raise ConfigError(f"Unknown setting [{name}] {unknown[0]} in the config file.")

    for key, value in values.items():
        label = f"{name}.{key}"
        expected = type(getattr(section_type(), key))
        whole_number_for_float = expected is float and type(value) is int
        if type(value) is not expected and not whole_number_for_float:
            raise ConfigError(f"{label} must be a {expected.__name__}, got {value!r}.")
        if expected in (int, float):
            minimum_ok = value >= 0 if label in _ZERO_ALLOWED else value > 0
            if not minimum_ok:
                raise ConfigError(f"{label} is out of range: {value!r}.")
    if name == "effect" and values.get("style", EFFECT_STYLES[0]) not in EFFECT_STYLES:
        choices = " or ".join(f'"{style}"' for style in EFFECT_STYLES)
        raise ConfigError(f"effect.style must be {choices}, got {values['style']!r}.")
    return section_type(**values)


def load_config(path: Path) -> Config:
    """Reads the config file. A missing file means all defaults."""
    if not path.exists():
        return Config()
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path.name} has a syntax error: {error}") from error

    sections = {f.name: f.default_factory for f in fields(Config)}
    unknown = sorted(set(data) - set(sections))
    if unknown:
        raise ConfigError(f"Unknown section [{unknown[0]}] in the config file.")
    built = {}
    for name, section_type in sections.items():
        values = data.get(name, {})
        if not isinstance(values, dict):
            raise ConfigError(f"[{name}] must be a section in the config file.")
        built[name] = _build_section(name, section_type, values)
    return Config(**built)
