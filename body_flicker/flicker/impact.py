"""The physical punch of the effect: a shockwave, a flash of light and a camera shake.

The smoke style uses a warm, local flash. The electric style uses a wide blue-white
strobe, like lightning.

The shockwave bends the picture behind the smoke, as a pressure wave would. The
flash lights up the room around the burst. The shake moves the whole picture.
"""

from __future__ import annotations

import cv2
import numpy as np

SHOCK_SECONDS = 0.26
FLASH_SECONDS = 0.14
SHAKE_SECONDS = 0.36
SHAKE_RATE = 19.0
DIVISOR = 4
FLASH_COLOUR = (215, 235, 255)  # BGR, a warm white
STROBE_HZ = 30.0


class Impact:
    def __init__(
        self,
        centre: tuple[float, float],
        reach: float,
        frame_size: tuple[int, int],
        start: float,
        shake_pixels: float,
        flash_strength: float,
        seed: int,
        flash_colour: tuple[int, int, int] = FLASH_COLOUR,
        flash_spread: float = 1.6,
        flash_seconds: float = FLASH_SECONDS,
        strobe: bool = False,
    ):
        """`flash_spread` is how far the light reaches, in multiples of `reach`.

        `strobe` makes the flash flicker like lightning instead of fading smoothly.
        """
        width, height = frame_size
        self._start = start
        self._reach = reach
        self._shake_pixels = shake_pixels
        self._flash_strength = flash_strength
        self._flash_seconds = flash_seconds
        self._strobe = strobe
        self._size = frame_size
        self._phases = np.random.default_rng(seed).uniform(0, 2 * np.pi, 2)

        x_small = np.linspace(0, width, width // DIVISOR, dtype=np.float32) - centre[0]
        y_small = np.linspace(0, height, height // DIVISOR, dtype=np.float32) - centre[1]
        x_grid, y_grid = np.meshgrid(x_small, y_small)
        self._distance = np.maximum(np.hypot(x_grid, y_grid), 1.0)
        self._unit_x = x_grid / self._distance
        self._unit_y = y_grid / self._distance
        self._map_x, self._map_y = np.meshgrid(
            np.arange(width, dtype=np.float32), np.arange(height, dtype=np.float32)
        )

        falloff = np.exp(-((self._distance / (reach * flash_spread)) ** 2))[..., None]
        glow = (falloff * np.array(flash_colour, dtype=np.float32)).astype(np.uint8)
        self._glow = cv2.resize(glow, frame_size, interpolation=cv2.INTER_LINEAR)

    def alive(self, now: float) -> bool:
        return now - self._start < max(SHOCK_SECONDS, self._flash_seconds, SHAKE_SECONDS)

    def refract(self, frame: np.ndarray, now: float) -> np.ndarray:
        """Bends the picture around an expanding ring."""
        age = (now - self._start) / SHOCK_SECONDS
        if not 0.0 <= age < 1.0:
            return frame
        radius = self._reach * (0.2 + 1.5 * (1.0 - (1.0 - age) ** 2))
        ring_width = self._reach * 0.22
        ring = np.exp(-(((self._distance - radius) / ring_width) ** 2))
        push = ring * self._reach * 0.09 * (1.0 - age) ** 1.5

        bend_x = cv2.resize(self._unit_x * push, self._size, interpolation=cv2.INTER_LINEAR)
        bend_y = cv2.resize(self._unit_y * push, self._size, interpolation=cv2.INTER_LINEAR)
        return cv2.remap(
            frame,
            self._map_x - bend_x,
            self._map_y - bend_y,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )

    def flash(self, frame: np.ndarray, now: float) -> np.ndarray:
        seconds = now - self._start
        age = seconds / self._flash_seconds
        if not 0.0 <= age < 1.0 or self._flash_strength <= 0.0:
            return frame
        level = self._flash_strength * (1.0 - age) ** 2
        if self._strobe and int(seconds * STROBE_HZ) % 2 == 1:
            level *= 0.3
        return cv2.addWeighted(frame, 1.0, self._glow, level, 0.0)

    def shake(self, frame: np.ndarray, now: float) -> np.ndarray:
        age = now - self._start
        if not 0.0 <= age < SHAKE_SECONDS or self._shake_pixels <= 0.0:
            return frame
        strength = self._shake_pixels * np.exp(-age * 11.0)
        wave = 2 * np.pi * SHAKE_RATE * age
        matrix = np.float32(
            (
                (1, 0, strength * np.sin(wave + self._phases[0])),
                (0, 1, strength * 0.7 * np.sin(wave * 1.3 + self._phases[1])),
            )
        )
        return cv2.warpAffine(
            frame,
            matrix,
            (frame.shape[1], frame.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
