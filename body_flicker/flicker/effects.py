"""Draws the body during a vanish or reappear.

`progress` runs from 0 (fully present) to 1 (fully gone). Reappearing is the same
timeline played backwards.
"""

from __future__ import annotations

import cv2
import numpy as np

from .compositing import over, over_premultiplied, premultiply, scaled, smoothstep

FLICKER_END = 0.30
FLICKER_SLOT = 0.10
FLICKER_LEVELS = (1.0, 0.2, 1.0)
STRETCH_START = 0.10
STRETCH_END = 0.55
GHOST_START = 0.05
GHOST_END = 0.55
# Afterimages split into colours, like a lens that cannot keep up with the motion.
GHOST_TINTS = tuple(
    np.diag(channels).astype(np.float32)
    for channels in ((1.5, 0.45, 0.35), (0.4, 1.35, 0.45), (0.35, 0.45, 1.5))  # BGR
)
RAW_BLEND_END = 0.12


def prepare_mask(
    mask: np.ndarray | None, size: tuple[int, int], feather_px: int
) -> np.ndarray:
    """Turns a 0-1 person mask into a soft uint8 mask at frame size (width, height)."""
    width, height = size
    if mask is None:
        return np.zeros((height, width), dtype=np.uint8)

    # Widen the mask slightly so no edge of the body is left behind.
    small = (np.clip((mask - 0.3) / 0.35, 0.0, 1.0) * 255.0).astype(np.uint8)
    if feather_px > 0:
        # Blurring at the mask's own size is much cheaper than at frame size.
        radius = max(round(feather_px * small.shape[1] / width), 1)
        small = cv2.GaussianBlur(small, (radius * 2 + 1, radius * 2 + 1), 0)
    return cv2.resize(small, size, interpolation=cv2.INTER_LINEAR)


def person_anchor(mask: np.ndarray) -> tuple[tuple[float, float], float]:
    """Returns the centre and rough size of the person, for placing the smoke."""
    height, width = mask.shape[:2]
    rows, columns = np.nonzero(mask[::4, ::4] > 127)
    if len(rows) == 0:
        return (width / 2.0, height / 2.0), height * 0.32
    centre = (float(columns.mean()) * 4.0, float(rows.mean()) * 4.0)
    tallest = float(rows.max() - rows.min()) * 4.0
    return centre, float(np.clip(tallest * 0.42, height * 0.2, height * 0.45))


def _shift(image: np.ndarray, pixels: float) -> np.ndarray:
    """Slides an image sideways by whole pixels, leaving black behind it."""
    amount = int(round(pixels))
    shifted = np.zeros_like(image)
    if amount > 0:
        shifted[:, amount:] = image[:, :-amount]
    elif amount < 0:
        shifted[:, :amount] = image[:, -amount:]
    else:
        shifted[:] = image
    return shifted


def _speed_layer(
    body: np.ndarray, mask: np.ndarray, progress: float, direction: int
) -> tuple[np.ndarray, np.ndarray] | None:
    """Builds afterimages and the stretched body at half size for speed.

    Returns a premultiplied colour layer and its alpha, both at half size.
    """
    ghost_amount = (progress - GHOST_START) / (GHOST_END - GHOST_START)
    stretch_amount = (progress - STRETCH_START) / (STRETCH_END - STRETCH_START)
    ghosts_on = 0.0 < ghost_amount < 1.0
    stretch_on = 0.0 < stretch_amount < 1.0
    if not ghosts_on and not stretch_on:
        return None

    height, width = body.shape[:2]
    half_size = (width // 2, height // 2)
    small_body = cv2.resize(body, half_size, interpolation=cv2.INTER_AREA)
    small_mask = cv2.resize(mask, half_size, interpolation=cv2.INTER_AREA)
    body_layer = premultiply(small_body, small_mask)

    colour = np.zeros_like(body_layer)
    alpha = np.zeros_like(small_mask)

    if ghosts_on:
        spacing = half_size[0] * 0.075 * ghost_amount * direction
        strength = 0.6 * (1.0 - ghost_amount)
        for index, tint in enumerate(GHOST_TINTS, start=1):
            ghost_alpha = scaled(_shift(small_mask, spacing * index), strength)
            ghost_colour = cv2.transform(_shift(body_layer, spacing * index), tint)
            colour = cv2.add(colour, scaled(ghost_colour, strength))
            alpha = cv2.max(alpha, ghost_alpha)

    if stretch_on:
        length = int(9 + half_size[0] * 0.22 * stretch_amount) | 1
        level = 1.0 - stretch_amount
        offset = direction * length * 0.3
        blur_colour = scaled(_shift(cv2.blur(body_layer, (length, 1)), offset), level)
        blur_alpha = scaled(_shift(cv2.blur(small_mask, (length, 1)), offset), level)
        colour = over_premultiplied(colour, blur_colour, blur_alpha)
        alpha = cv2.max(alpha, blur_alpha)

    return colour, alpha


def _body_level(progress: float) -> float:
    """How solid the sharp body is: flickers a few frames, then it is gone."""
    if progress >= FLICKER_END:
        return 0.0
    slot = min(int(progress / FLICKER_SLOT), len(FLICKER_LEVELS) - 1)
    return FLICKER_LEVELS[slot]


def render_transition(
    raw: np.ndarray,
    plate: np.ndarray,
    mask: np.ndarray,
    progress: float,
    direction: int,
) -> np.ndarray:
    """Renders one frame. `raw` supplies the body, `plate` the empty room."""
    if progress >= 1.0:
        return plate.copy()
    if progress <= 0.0:
        return raw.copy()

    result = plate
    level = _body_level(progress)

    speed = _speed_layer(raw, mask, progress, direction)
    if speed is not None:
        colour, alpha = speed
        if progress < FLICKER_END:
            # Blink the speed trails with the body, or they hide the flicker.
            colour, alpha = scaled(colour, level), scaled(alpha, level)
        size = (raw.shape[1], raw.shape[0])
        result = over_premultiplied(
            result,
            cv2.resize(colour, size, interpolation=cv2.INTER_LINEAR),
            cv2.resize(alpha, size, interpolation=cv2.INTER_LINEAR),
        )

    if level > 0.0:
        result = over(result, raw, scaled(mask, level))

    # Ease in from the real picture so there is no pop at the first frame, even
    # if the room has changed slightly since the background was captured.
    blend = float(smoothstep(0.0, RAW_BLEND_END, progress))
    if blend < 1.0:
        result = cv2.addWeighted(raw, 1.0 - blend, result, blend, 0.0)

    return result.copy() if result is plate else result
