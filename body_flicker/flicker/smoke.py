"""Volumetric-looking smoke.

Soft puffs give the overall shape. Noise then eats into them so the edges break up
into billows and wisps, and more of the smoke is eaten away as it ages. The maths
runs at quarter size, which is cheap, and smoke is soft enough to scale up well.
"""

from __future__ import annotations

import cv2
import numpy as np

from .compositing import over_premultiplied, smoothstep

DIVISOR = 4
TILE_SIZE = 256
PUFF_COUNT = 16
MAX_OPACITY = 0.96
WHITE = np.array((250, 252, 253), dtype=np.float32)  # BGR
GREY = np.array((150, 146, 144), dtype=np.float32)


def _make_noise_tile() -> np.ndarray:
    """Cloud-like noise that repeats seamlessly, from 0 to 1."""
    rng = np.random.default_rng(42)
    spectrum = np.fft.fft2(rng.normal(size=(TILE_SIZE, TILE_SIZE)))
    frequency = np.hypot(*np.meshgrid(np.fft.fftfreq(TILE_SIZE), np.fft.fftfreq(TILE_SIZE)))
    frequency[0, 0] = 1.0
    tile = np.real(np.fft.ifft2(spectrum / frequency**1.5))
    tile = (tile - tile.min()) / (tile.max() - tile.min())
    return tile.astype(np.float32)


_NOISE = _make_noise_tile()


class Smoke:
    """One smoke cloud. `ambient` is the room's colour, used to tint it."""

    def __init__(
        self,
        centre: np.ndarray,
        size: float,
        life: float,
        rng: np.random.Generator,
        ambient: tuple[float, float, float],
    ):
        self._centre = centre
        self._size = size
        self._life = life
        angles = rng.uniform(0, 2 * np.pi, PUFF_COUNT)
        spread = rng.uniform(0.1, 1.0, PUFF_COUNT)
        self._offsets = np.stack(
            (np.cos(angles) * spread, np.sin(angles) * spread * 0.8), axis=1
        ).astype(np.float32)
        self._radii = rng.uniform(0.3, 0.55, PUFF_COUNT).astype(np.float32)
        self._delays = rng.uniform(0.0, 0.1, PUFF_COUNT).astype(np.float32)
        self._phase = rng.uniform(0, TILE_SIZE, 4).astype(np.float32)

        # Tinting by the room is what makes the smoke feel lit by the same light.
        room = np.array(ambient, dtype=np.float32)
        self._light = WHITE * 0.88 + room * 0.12
        self._shadow = GREY * 0.6 + room * 0.4

    def draw(self, frame: np.ndarray, seconds: float) -> None:
        amount = seconds / self._life
        if not 0.0 <= amount < 1.0:
            return

        # The cloud blooms fast, so it hides the body as the body breaks up.
        ages = np.clip((seconds - self._delays) / (self._life * 0.62), 0.0, 1.0)
        expand = 1.0 - (1.0 - ages) ** 4
        positions = self._centre + self._offsets * (expand * self._size * 0.92)[:, None]
        positions[:, 1] -= self._size * 0.28 * amount
        radii = self._radii * self._size * (0.62 + 0.72 * expand)

        height, width = frame.shape[:2]
        blur_radius = self._size * 0.26
        margin = blur_radius * 1.9 + DIVISOR
        left = max(int((positions[:, 0] - radii).min() - margin), 0)
        top = max(int((positions[:, 1] - radii).min() - margin), 0)
        right = min(int((positions[:, 0] + radii).max() + margin), width)
        bottom = min(int((positions[:, 1] + radii).max() + margin), height)
        small_width = (right - left) // DIVISOR
        small_height = (bottom - top) // DIVISOR
        if small_width < 4 or small_height < 4:
            return

        canvas = np.zeros((small_height, small_width), dtype=np.uint8)
        scaled = (positions - (left, top)) / DIVISOR
        for (x, y), radius in zip(scaled, radii / DIVISOR):
            if radius >= 0.5:
                cv2.circle(canvas, (int(x), int(y)), int(radius), 255, cv2.FILLED)
        # A wide blur means the cloud has no outline. Its edges come from the noise.
        blur = max(int(blur_radius / DIVISOR * 2) | 1, 3)
        shape = cv2.GaussianBlur(canvas, (blur, blur), 0).astype(np.float32) / 255.0

        # Billows grow outward with the cloud, while finer detail churns upward.
        columns = np.arange(small_width, dtype=np.float32) * DIVISOR + left
        rows = np.arange(small_height, dtype=np.float32) * DIVISOR + top
        x_grid, y_grid = np.meshgrid(
            columns - self._centre[0], rows - self._centre[1]
        )
        grow = 1.0 / (1.0 + 1.3 * float(expand.mean()))
        coarse_scale = TILE_SIZE * 0.55 / self._size * grow
        coarse = cv2.remap(
            _NOISE,
            x_grid * coarse_scale + self._phase[0],
            y_grid * coarse_scale + self._phase[1],
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_WRAP,
        )
        fine_scale = coarse_scale * 2.6
        fine = cv2.remap(
            _NOISE,
            x_grid * fine_scale + self._phase[2],
            y_grid * fine_scale + self._phase[3] + seconds * 45.0,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_WRAP,
        )

        # Noise is added rather than multiplied, which pushes the edge in and out so
        # it frays into wisps. Multiplying would only dim a clean outline.
        density = shape * 1.3 + (coarse - 0.5) * 1.5 + (fine - 0.5) * 0.7
        erosion = 0.3 + 0.95 * amount**1.4
        alpha = smoothstep(erosion, erosion + 0.55, density)
        alpha = alpha * smoothstep(0.0, 0.3, shape)  # no stray specks far from the cloud
        alpha = alpha * (1.0 - smoothstep(0.55, 1.0, amount)) * MAX_OPACITY

        # Light from above: billows facing it are bright and their undersides dark.
        shift = max(int(self._size / (DIVISOR * 10)), 1)
        above = np.vstack((np.repeat(density[:1], shift, axis=0), density[:-shift]))
        height_light = 1.0 - (rows - rows[0]) / max(float(rows[-1] - rows[0]), 1.0)
        shading = 0.56 + (density - above) * 3.4 + height_light[:, None] * 0.3
        shading = np.clip(shading + (coarse - 0.5) * 0.8, 0.0, 1.0)
        colour = self._shadow + (self._light - self._shadow) * shading[..., None]
        colour = colour * alpha[..., None]

        size = (right - left, bottom - top)
        area = frame[top:bottom, left:right]
        area[:] = over_premultiplied(
            area,
            cv2.resize(colour.astype(np.uint8), size, interpolation=cv2.INTER_LINEAR),
            cv2.resize((alpha * 255.0).astype(np.uint8), size, interpolation=cv2.INTER_LINEAR),
        )
