"""A burst of smoke and leaves.

Everything is a formula of the burst's age, so it looks the same at any frame rate.
"""

from __future__ import annotations

import numpy as np

from .leaves import Leaves
from .smoke import Smoke


class Burst:
    """Smoke and leaves at one point. `gather` seconds of leaves spiral in first."""

    def __init__(
        self,
        centre: tuple[float, float],
        size: float,
        start: float,
        life: float,
        seed: int | None = None,
        leaf_life: float | None = None,
        ambient: tuple[float, float, float] = (128.0, 128.0, 128.0),
        gather: float = 0.0,
    ):
        rng = np.random.default_rng(seed)
        location = np.array(centre, dtype=np.float32)
        self.start = start
        self._gather = gather
        self._leaf_life = life if leaf_life is None else leaf_life
        self._end = start + max(life, self._leaf_life)
        self._smoke = Smoke(location, float(size), life, rng, ambient)
        self._leaves = Leaves(location, float(size), self._leaf_life, rng)

    def alive(self, now: float) -> bool:
        return now < self._end

    def draw(self, frame: np.ndarray, now: float) -> None:
        """Draws the burst onto a uint8 BGR frame in place."""
        seconds = now - self.start
        if seconds < 0.0:
            if self._gather > 0.0 and seconds >= -self._gather:
                self._leaves.draw_gather(frame, 1.0 + seconds / self._gather)
            return
        self._smoke.draw(frame, seconds)
        self._leaves.draw_burst(frame, seconds)
