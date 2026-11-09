"""Leaves that burst out, then flutter down, or spiral in before a reappearance.

Each leaf is a detailed picture drawn once at startup, then turned in 3D per frame.
Positions follow formulas of time: air drag slows the burst, then the leaf falls at
a gentle steady speed while swaying.
"""

from __future__ import annotations

import cv2
import numpy as np

from .compositing import over_premultiplied, scaled, smoothstep

COUNT = 26
SPRITE_LENGTH = 128
SPRITE_WIDTH = 64
DRAG = 3.2
LEAF_PALETTES = (  # BGR: (shadow, sunlit)
    ((28, 88, 40), (58, 170, 96)),
    ((22, 104, 58), (52, 186, 130)),
    ((24, 72, 34), (44, 138, 72)),
    ((26, 112, 92), (58, 190, 170)),
)


def _make_sprite(shadow, sunlit, seed: int) -> np.ndarray:
    """Draws one leaf with veins. Returns premultiplied BGRA."""
    rng = np.random.default_rng(seed)
    height, width = SPRITE_WIDTH, SPRITE_LENGTH
    centre = height / 2

    along = np.linspace(-1, 1, 48)
    half_width = 0.46 * height * (1 - along**2) ** 0.75 * (1 - 0.3 * along)
    x_line = (along + 1) / 2 * (width - 1)
    outline = np.concatenate(
        (
            np.stack((x_line, centre - half_width), axis=1),
            np.stack((x_line[::-1], centre + half_width[::-1]), axis=1),
        )
    )
    alpha = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(alpha, [np.round(outline * 16).astype(np.int32)], 255, cv2.LINE_AA, 4)

    x_grid = np.linspace(0, 1, width, dtype=np.float32)[None, :]
    y_grid = np.linspace(0, 1, height, dtype=np.float32)[:, None]
    mix = np.clip(0.25 + 0.75 * y_grid + 0.25 * (x_grid - 0.5), 0, 1)[..., None]
    colour = np.array(shadow, np.float32) + (
        np.array(sunlit, np.float32) - np.array(shadow, np.float32)
    ) * (1 - mix)
    colour = np.clip(colour * rng.uniform(0.92, 1.08, (height, width, 1)), 0, 255).astype(np.uint8)

    vein = tuple(int(min(channel * 1.45, 255)) for channel in sunlit)
    midrib_y = int(centre)
    cv2.line(colour, (0, midrib_y), (width - 1, midrib_y), vein, 1, cv2.LINE_AA)
    for x in range(14, width - 18, 15):
        reach = float(np.interp(x, x_line, half_width)) * 0.85
        for side in (-1, 1):
            tip = (x + 14, int(centre + side * reach))
            cv2.line(colour, (x, midrib_y), tip, vein, 1, cv2.LINE_AA)

    alpha_float = (alpha.astype(np.float32) / 255.0)[..., None]
    sprite = np.dstack(((colour * alpha_float).astype(np.uint8), alpha))
    return sprite


_SPRITES = tuple(
    _make_sprite(shadow, sunlit, index)
    for index, (shadow, sunlit) in enumerate(LEAF_PALETTES)
)
# Leaves close to the camera are out of focus, which sells the depth.
_SOFT_SPRITES = tuple(cv2.GaussianBlur(sprite, (9, 9), 0) for sprite in _SPRITES)


class Leaves:
    def __init__(
        self,
        centre: np.ndarray,
        size: float,
        life: float,
        rng: np.random.Generator,
    ):
        self._centre = centre
        self._size = size
        self._life = life

        angles = rng.uniform(0, 2 * np.pi, COUNT).astype(np.float32)
        speeds = rng.uniform(1.8, 5.4, COUNT).astype(np.float32) * size
        self._angles = angles
        self._velocity = np.stack(
            (np.cos(angles) * speeds, np.sin(angles) * speeds * 0.75 - size * 0.8), axis=1
        ).astype(np.float32)
        self._fall = rng.uniform(0.28, 0.6, COUNT).astype(np.float32) * size
        self._sway = rng.uniform(0.08, 0.3, COUNT).astype(np.float32) * size
        self._sway_rate = rng.uniform(1.8, 3.6, COUNT).astype(np.float32)
        self._phases = rng.uniform(0, 2 * np.pi, COUNT).astype(np.float32)
        self._spins = rng.uniform(-5.0, 5.0, COUNT).astype(np.float32)
        self._flips = rng.uniform(3.0, 8.0, COUNT).astype(np.float32)
        # A few leaves are near the camera: bigger and out of focus.
        depth = rng.uniform(0.0, 1.0, COUNT)
        self._near = depth > 0.82
        self._lengths = (rng.uniform(0.055, 0.085, COUNT) * (1.0 + self._near * 1.1)).astype(
            np.float32
        ) * size
        self._sprites = rng.integers(0, len(_SPRITES), COUNT)
        self._lives = rng.uniform(0.55, 1.0, COUNT).astype(np.float32) * life

    def draw_burst(self, frame: np.ndarray, seconds: float) -> None:
        """Draws the leaves `seconds` after the burst."""
        if seconds < 0.0 or seconds >= self._life:
            return
        slowing = (1.0 - np.exp(-DRAG * seconds)) / DRAG + 0.05  # starts already spread
        x = self._centre[0] + self._velocity[:, 0] * slowing
        y = self._centre[1] + self._velocity[:, 1] * slowing
        y = y + self._fall * (seconds - slowing)
        settled = 1.0 - np.exp(-DRAG * seconds)
        x = x + self._sway * settled * np.sin(self._sway_rate * seconds + self._phases)

        drift = np.exp(-DRAG * seconds)
        stretch = np.clip(self._velocity * drift[None] / self._size * 0.09, -1.2, 1.2)
        fade = 1.0 - smoothstep(0.7, 1.0, seconds / self._lives)
        spins = self._phases + self._spins * seconds
        flips = self._phases * 2.0 + self._flips * seconds
        self._draw_all(frame, x, y, spins, flips, fade, stretch)

    def draw_gather(self, frame: np.ndarray, progress: float) -> None:
        """Draws the leaves spiralling in. `progress` runs from 0 to 1."""
        remaining = (1.0 - progress) ** 1.4
        radii = self._size * (0.5 + np.hypot(*self._velocity.T) / self._size * 0.24) * remaining
        angles = self._angles + 4.0 * remaining
        x = self._centre[0] + np.cos(angles) * radii
        y = self._centre[1] + np.sin(angles) * radii * 0.7
        fade = np.full(COUNT, float(smoothstep(0.0, 0.35, progress)), dtype=np.float32)
        stretch = np.stack((-np.sin(angles), np.cos(angles)), axis=1) * 0.5
        spins = self._phases + self._spins * progress
        flips = self._phases * 2.0 + self._flips * progress
        self._draw_all(frame, x, y, spins, flips, fade, stretch)

    def _draw_all(self, frame, xs, ys, spins, flips, fades, stretches) -> None:
        for index in range(COUNT):
            if fades[index] > 0.02:
                self._draw_one(
                    frame,
                    index,
                    float(xs[index]),
                    float(ys[index]),
                    float(spins[index]),
                    float(flips[index]),
                    float(fades[index]),
                    stretches[index],
                )

    def _draw_one(self, frame, index, x, y, spin, flip, fade, stretch) -> None:
        height, width = frame.shape[:2]
        sprites = _SOFT_SPRITES if self._near[index] else _SPRITES
        sprite = sprites[self._sprites[index]]

        # A tumbling leaf looks thinner as it turns edge-on, and catches less light.
        turned = abs(np.cos(flip))
        scale = float(self._lengths[index]) / (SPRITE_LENGTH / 2)
        cos_spin, sin_spin = np.cos(spin), np.sin(spin)
        transform = np.array(
            (
                (cos_spin * scale, -sin_spin * scale * max(turned, 0.14)),
                (sin_spin * scale, cos_spin * scale * max(turned, 0.14)),
            ),
            dtype=np.float32,
        )
        # Fast leaves smear along the direction they are moving.
        speed = float(np.hypot(*stretch))
        if speed > 0.05:
            along = stretch / speed
            transform = (np.eye(2, dtype=np.float32) + speed * np.outer(along, along)) @ transform

        reach = int(float(self._lengths[index]) * (1.2 + speed)) + 2
        left, top = max(int(x) - reach, 0), max(int(y) - reach, 0)
        right, bottom = min(int(x) + reach, width), min(int(y) + reach, height)
        if right - left < 2 or bottom - top < 2:
            return

        middle = np.array((SPRITE_LENGTH / 2, SPRITE_WIDTH / 2), dtype=np.float32)
        offset = np.array((x - left, y - top), dtype=np.float32) - transform @ middle
        matrix = np.column_stack((transform, offset))
        drawn = cv2.warpAffine(sprite, matrix, (right - left, bottom - top))

        light = (0.62 + 0.45 * turned) * fade
        area = frame[top:bottom, left:right]
        area[:] = over_premultiplied(
            area, scaled(drawn[..., :3], light), scaled(drawn[..., 3], fade)
        )
