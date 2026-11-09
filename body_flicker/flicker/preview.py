"""The small local window. Nothing drawn here reaches the video call."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .config import PreviewConfig
from .engine import HandInfo, Mode, StepResult

WINDOW = "Body Flicker"
BAR_HEIGHT = 74
FONT = cv2.FONT_HERSHEY_SIMPLEX
WHITE = (240, 240, 240)
GREY = (170, 170, 170)
GREEN = (110, 220, 120)
AMBER = (60, 190, 250)
RED = (70, 70, 240)
FINGER_DOTS = (4, 8, 12, 16, 20)

MODE_LABELS = {
    Mode.PRESENT: "VISIBLE",
    Mode.VANISHING: "VANISHING",
    Mode.GONE: "GONE",
    Mode.APPEARING: "REAPPEARING",
}


@dataclass(frozen=True)
class Stats:
    fps: float
    inference_ms: float
    virtual_camera: bool


def _text(canvas, text, origin, colour=WHITE, scale=0.45, thickness=1):
    cv2.putText(canvas, text, origin, FONT, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(canvas, text, origin, FONT, scale, colour, thickness, cv2.LINE_AA)


def _fit(image: np.ndarray, width: int, mirror: bool) -> np.ndarray:
    height = round(image.shape[0] * width / image.shape[1])
    fitted = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    return cv2.flip(fitted, 1) if mirror else fitted


def hand_problem(hands: tuple[HandInfo, ...]) -> str:
    if not hands:
        return "No hand seen"
    closest = min(hands, key=lambda hand: (not hand.reading.is_sign, hand.reading.tip_gap))
    if closest.reading.is_sign:
        return "Sign seen, hold it"
    return f"Sign: {closest.reading.problem}"


def compose_preview(
    output: np.ndarray,
    hands: tuple[HandInfo, ...],
    result: StepResult,
    stats: Stats,
    settings: PreviewConfig,
    alert: str = "",
) -> np.ndarray:
    """Builds the preview image: the call's video with hand dots and a status bar.

    The picture is mirrored here and only here. Hand dots use the same mirroring,
    so they stay on the hand. They are drawn even while you are hidden, so you can
    find your hand when the picture shows an empty room.
    """
    view = _fit(output, settings.width, settings.mirror)
    height, width = view.shape[:2]

    for hand in hands:
        colour = GREEN if hand.reading.is_sign else AMBER
        for x, y in hand.image_points[list(FINGER_DOTS)]:
            shown_x = 1.0 - x if settings.mirror else x
            cv2.circle(view, (int(shown_x * width), int(y * height)), 4, colour, -1, cv2.LINE_AA)

    if result.hold_progress > 0 and hands:
        signing = next((hand for hand in hands if hand.reading.is_sign), hands[0])
        x, y = signing.image_points[list(FINGER_DOTS)].mean(axis=0)
        shown_x = 1.0 - x if settings.mirror else x
        centre = (int(shown_x * width), int(y * height))
        sweep = int(360 * result.hold_progress)
        cv2.ellipse(view, centre, (32, 32), -90, 0, sweep, GREEN, 3, cv2.LINE_AA)

    if result.message:
        _text(view, result.message, (14, 36), WHITE, 0.8, 2)

    bar = np.full((BAR_HEIGHT, width, 3), 28, dtype=np.uint8)
    mode_colour = GREEN if result.mode is Mode.PRESENT else AMBER
    _text(bar, MODE_LABELS[result.mode], (10, 22), mode_colour, 0.55, 1)
    _text(bar, f"{stats.fps:.0f} FPS   tracking {stats.inference_ms:.0f} ms", (140, 22), GREY)
    camera_state = ("Virtual camera on", GREEN) if stats.virtual_camera else ("Preview only", RED)
    _text(bar, camera_state[0], (width - 160, 22), camera_state[1])

    notice = alert or result.warning
    if notice:
        _text(bar, notice[:78], (10, 44), RED)
    else:
        _text(bar, hand_problem(hands), (10, 44), GREY)
    _text(bar, "B background    T test trigger    Q quit", (10, 65), GREY, 0.42)

    return np.vstack((view, bar))


class PreviewWindow:
    def __init__(self):
        cv2.namedWindow(WINDOW, cv2.WINDOW_AUTOSIZE)
        self._shown = False

    def show(self, image: np.ndarray) -> str:
        """Displays a frame. Returns the pressed key, or 'q' if the window closed."""
        cv2.imshow(WINDOW, image)
        key = cv2.waitKey(1) & 0xFF
        if self._shown and cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            return "q"
        self._shown = True
        return chr(key).lower() if key != 0xFF else ""

    def close(self) -> None:
        cv2.destroyAllWindows()
