"""Recognises the ninja seal and decides when a held sign should fire.

Sign checks use MediaPipe's 3D world landmarks, so they are unaffected by how far
the hand is from the camera. All distances are divided by the palm length.
Thresholds were measured on real photos: neighbouring fingertips sit about 0.17
palm lengths apart, and a real peace sign measured 0.67 to 0.98.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import SignConfig

WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20


@dataclass(frozen=True)
class SignReading:
    """The result for one hand. `problem` says what is stopping the sign."""

    is_sign: bool
    tip_gap: float
    problem: str


def _reach_ratio(points: np.ndarray, tip: int) -> float:
    """How far a fingertip reaches from the wrist compared with its middle joint.

    Above 1 the finger is pointing away from the palm; below 1 it is folded back.
    """
    wrist = points[WRIST]
    middle_joint = points[tip - 2]
    joint_distance = np.linalg.norm(middle_joint - wrist)
    if joint_distance == 0:
        return 0.0
    return float(np.linalg.norm(points[tip] - wrist) / joint_distance)


def read_sign(points: np.ndarray, config: SignConfig) -> SignReading:
    """Checks 21 hand landmarks (x, y, z) for the two-finger seal."""
    palm = np.linalg.norm(points[WRIST] - points[MIDDLE_MCP])
    if palm == 0:
        return SignReading(False, 0.0, "hand not clear")

    tip_gap = float(np.linalg.norm(points[INDEX_TIP] - points[MIDDLE_TIP]) / palm)
    thumb_reach = float(np.linalg.norm(points[THUMB_TIP] - points[MIDDLE_MCP]) / palm)

    problem = ""
    if _reach_ratio(points, INDEX_TIP) < config.extended_ratio:
        problem = "straighten index finger"
    elif _reach_ratio(points, MIDDLE_TIP) < config.extended_ratio:
        problem = "straighten middle finger"
    elif _reach_ratio(points, RING_TIP) > config.curled_ratio:
        problem = "curl ring finger"
    elif _reach_ratio(points, PINKY_TIP) > config.curled_ratio:
        problem = "curl little finger"
    elif tip_gap > config.max_tip_gap:
        problem = "touch your two fingers together"
    elif thumb_reach > config.thumb_max_reach:
        problem = "tuck your thumb in"

    return SignReading(not problem, tip_gap, problem)


class HoldDetector:
    """Fires once when a sign is held long enough.

    After firing, the sign must be released before it can fire again, and the
    cooldown must have passed. Short tracking dropouts do not reset the hold.
    """

    def __init__(self, config: SignConfig):
        self._hold = config.hold_seconds
        self._cooldown = config.cooldown_seconds
        self._grace = config.dropout_grace_seconds
        self._started_at: float | None = None
        self._last_seen: float | None = None
        self._ready_at = float("-inf")
        self._needs_release = False
        self.progress = 0.0

    def update(self, active: bool, now: float) -> bool:
        """Takes the current sign state. Returns True on the moment it fires."""
        if active:
            self._last_seen = now
        held = active or (
            self._last_seen is not None and now - self._last_seen <= self._grace
        )

        if not held:
            self._started_at = None
            self._needs_release = False
            self.progress = 0.0
            return False

        if self._needs_release or now < self._ready_at:
            self._started_at = None
            self.progress = 0.0
            return False

        if self._started_at is None:
            self._started_at = now
        self.progress = min((now - self._started_at) / self._hold, 1.0)

        if self.progress < 1.0:
            return False
        self._started_at = None
        self._needs_release = True
        self._ready_at = now + self._cooldown
        self.progress = 0.0
        return True
