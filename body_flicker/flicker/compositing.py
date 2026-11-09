"""Fast 8-bit alpha blending.

Blending 720p frames in floating point takes far longer than one 30 FPS frame, so
all full-size compositing goes through OpenCV's integer operations instead. Each
blend also stops at the edges of its alpha, because even the integer version is
the most expensive step of the effect.
"""

from __future__ import annotations

import cv2
import numpy as np

_SCALE = 1.0 / 255.0


def smoothstep(low: float, high: float, value):
    amount = np.clip((value - low) / (high - low), 0.0, 1.0)
    return amount * amount * (3.0 - 2.0 * amount)


def _three_channel(alpha: np.ndarray) -> np.ndarray:
    return cv2.merge((alpha, alpha, alpha))


def over(base: np.ndarray, colour: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Puts `colour` over `base`, using a single-channel uint8 alpha."""
    left, top, width, height = cv2.boundingRect(alpha)
    result = base.copy()
    if width == 0 or height == 0:
        return result
    area = (slice(top, top + height), slice(left, left + width))
    weights = _three_channel(alpha[area])
    result[area] = cv2.add(
        cv2.multiply(base[area], cv2.bitwise_not(weights), scale=_SCALE),
        cv2.multiply(colour[area], weights, scale=_SCALE),
    )
    return result


def over_premultiplied(base: np.ndarray, colour: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Like `over`, for a colour layer already multiplied by its alpha."""
    left, top, width, height = cv2.boundingRect(alpha)
    result = base.copy()
    if width == 0 or height == 0:
        return result
    area = (slice(top, top + height), slice(left, left + width))
    inverse = cv2.bitwise_not(_three_channel(alpha[area]))
    result[area] = cv2.add(cv2.multiply(base[area], inverse, scale=_SCALE), colour[area])
    return result


def premultiply(colour: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    return cv2.multiply(colour, _three_channel(alpha), scale=_SCALE)


def scaled(image: np.ndarray, amount: float) -> np.ndarray:
    return cv2.convertScaleAbs(image, alpha=amount)
