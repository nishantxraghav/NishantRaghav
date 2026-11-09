"""The state machine that turns camera frames into the call's video.

The engine has no threads or hardware access. It is given each frame, the latest
tracking result and the current time, which keeps it fully testable.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import cv2
import numpy as np

from .background import BackgroundCollector
from .config import Config
from .effects import person_anchor, prepare_mask, render_transition
from .electric import COLLAPSE_END, Lightning, render_electric
from .gesture import HoldDetector, SignReading
from .impact import Impact
from .particles import Burst

# A vanish explodes part-way through, once the body starts to break up.
VANISH_SMOKE_AT = 0.3
# A reappearance spends this share of its time pulling the leaves in. The burst
# then lands just as the body starts to show, so the smoke hides the join.
GATHER_SHARE = 0.45
# Warn if more of the background than this had to be painted in.
MAX_GUESSED_BACKGROUND = 0.02
# Tracking pauses during the effect, so a mask can be this old when it is needed.
MAX_MASK_AGE = 1.3
# Tracking competes with the effect for CPU, so it rests for this long after a
# trigger. No sign can fire during the cooldown, so nothing is lost.
TRACKING_REST_SECONDS = 0.9
# Coming back should feel quick, so the smoke clears sooner than after a vanish.
RETURN_SMOKE_SHARE = 0.65
# Lightning is brighter than a puff of smoke, so the electric flash is stronger,
# wider and bluer.
ELECTRIC_FLASH_BOOST = 3.0
ELECTRIC_FLASH_COLOUR = (255, 225, 190)  # BGR, a cold blue-white
ELECTRIC_FLASH_SPREAD = 4.0
ELECTRIC_FLASH_SECONDS = 0.2


class Mode(enum.Enum):
    PRESENT = "present"
    VANISHING = "vanishing"
    GONE = "gone"
    APPEARING = "appearing"


@dataclass(frozen=True)
class HandInfo:
    reading: SignReading
    image_points: np.ndarray  # 21 (x, y) values from 0 to 1, in camera coordinates


@dataclass(frozen=True)
class VisionResult:
    """Tracking output. It always comes from the raw camera feed.

    Tracking can take 200 ms, so the live picture has moved on by the time a result
    arrives. `frame` is the exact camera frame this result describes. Anything that
    combines a mask with a picture must use this frame so the two line up.
    """

    timestamp: float
    frame: np.ndarray
    mask: np.ndarray | None
    hands: tuple[HandInfo, ...] = ()
    inference_ms: float = 0.0

    @property
    def sign_active(self) -> bool:
        return any(hand.reading.is_sign for hand in self.hands)


@dataclass
class StepResult:
    frame: np.ndarray
    mode: Mode
    hold_progress: float
    message: str = ""
    warning: str = ""


class Engine:
    def __init__(self, config: Config, seed: int | None = None):
        self._config = config
        self._rng = np.random.default_rng(seed)
        self._hold = HoldDetector(config.sign)
        self._size = (config.camera.width, config.camera.height)

        self.mode = Mode.PRESENT
        self.plate: np.ndarray | None = None
        self.warning = ""

        self._toggle_requested = False
        self._transition_start = 0.0
        self._direction = 1
        self._snapshot: np.ndarray | None = None
        self._snapshot_mask: np.ndarray | None = None
        self._return_mask: np.ndarray | None = None
        self.tracking_rests_until = 0.0
        self._bursts: list[Burst | Lightning] = []
        self._electric = config.effect.style == "electric"
        self._impact: Impact | None = None
        self._vanish_smoke_done = False

        self._capturing = False
        self._capture_begins = 0.0
        self._collector: BackgroundCollector | None = None
        self._last_collected: float | None = None

    @property
    def capturing(self) -> bool:
        return self._capturing

    def request_toggle(self) -> None:
        """Manual trigger. Ignored while a transition or capture is running."""
        self._toggle_requested = True

    def begin_background_capture(self, now: float) -> None:
        """Starts the countdown. Any running transition finishes immediately."""
        if self.mode is Mode.VANISHING:
            self.mode = Mode.GONE
        elif self.mode is Mode.APPEARING:
            self.mode = Mode.PRESENT
        self._bursts = []
        self._impact = None
        self.tracking_rests_until = 0.0  # the capture needs tracking straight away
        self._capturing = True
        self._capture_begins = now + self._config.background.countdown_seconds
        self._collector = BackgroundCollector(self._size, self._config.background.frames)
        self.warning = ""

    def step(self, frame: np.ndarray, vision: VisionResult | None, now: float) -> StepResult:
        # A mask brings its own frame, so it stays useful for a while. A sign does
        # not: a stalled tracker must not keep reporting a hand that has moved.
        fresh = vision
        sign_active = False
        if vision is not None:
            age = now - vision.timestamp
            if age > MAX_MASK_AGE:
                fresh = None
            sign_active = (
                age <= self._config.vision.max_sign_age_seconds and vision.sign_active
            )

        message = self._update_capture(fresh, now)
        self._update_sign(sign_active, now)
        self._apply_toggle(frame, fresh, now)
        self._spawn_vanish_smoke(now)
        self._finish_transition(now)
        output = self._render(frame, fresh, now)
        return StepResult(
            frame=output,
            mode=self.mode,
            hold_progress=self._hold.progress,
            message=message,
            warning=self.warning,
        )

    def _update_capture(self, vision: VisionResult | None, now: float) -> str:
        if not self._capturing:
            return ""
        if now < self._capture_begins:
            seconds_left = int(np.ceil(self._capture_begins - now))
            return f"Get ready to leave: {seconds_left}"

        # Without a mask there is no way to tell which pixels are the person. Each
        # result is used once, with its own frame, so lag cannot let the body in.
        if (
            vision is not None
            and vision.mask is not None
            and vision.timestamp != self._last_collected
        ):
            self._collector.add(vision.frame, vision.mask)
            self._last_collected = vision.timestamp

        progress = self._collector.empty_progress
        if progress >= 1.0:
            self.plate = self._collector.build_empty()
            self._finish_capture()
            return ""

        deadline = self._capture_begins + self._config.background.timeout_seconds
        if now >= deadline and self._collector.has_data:
            self.plate, guessed = self._collector.build_partial()
            self._finish_capture()
            if guessed > MAX_GUESSED_BACKGROUND:
                self.warning = "You may leave a smudge: press B and leave the frame fully"
            return ""

        if progress > 0.0:
            return f"Stay out of frame: {progress * 100:.0f}%"
        return "Leave the frame completely"

    def _finish_capture(self) -> None:
        self._capturing = False
        self._collector = None

    def _update_sign(self, active: bool, now: float) -> None:
        if self._capturing or self.mode in (Mode.VANISHING, Mode.APPEARING):
            self._hold.update(False, now)
            return
        if self._hold.update(active, now):
            self._toggle_requested = True

    def _apply_toggle(
        self, frame: np.ndarray, vision: VisionResult | None, now: float
    ) -> None:
        requested = self._toggle_requested
        self._toggle_requested = False
        if not requested or self._capturing or self.plate is None:
            return

        if self.mode is Mode.PRESENT:
            self.mode = Mode.VANISHING
            # The vanish plays over a frozen snapshot, so the mask stays aligned
            # with the body for the whole effect.
            self._snapshot = frame if vision is None else vision.frame
            self._snapshot_mask = self._full_mask(vision)
            self._vanish_smoke_done = False
            if self._electric:
                # The strike lands as the body finishes squeezing into a line.
                self._make_lightning(self._snapshot_mask, now, COLLAPSE_END)
        elif self.mode is Mode.GONE:
            self.mode = Mode.APPEARING
            self._return_mask = self._full_mask(vision)
            if self._electric:
                # Played backwards, the line appears first and the body grows from it.
                self._make_lightning(self._return_mask, now, 1.0 - COLLAPSE_END)
            else:
                gather = self._config.effect.duration_seconds * GATHER_SHARE
                self._make_burst(self._return_mask, now + gather, gather)
        else:
            return
        self.tracking_rests_until = now + min(
            TRACKING_REST_SECONDS, self._config.sign.cooldown_seconds
        )
        self._transition_start = now
        self._direction = int(self._rng.choice((-1, 1)))

    def _spawn_vanish_smoke(self, now: float) -> None:
        # Checked before the transition ends, so a slow frame cannot skip the smoke.
        if (
            self.mode is Mode.VANISHING
            and not self._electric
            and not self._vanish_smoke_done
            and self._progress(now) >= VANISH_SMOKE_AT
        ):
            self._make_burst(self._snapshot_mask, now)
            self._vanish_smoke_done = True

    def _finish_transition(self, now: float) -> None:
        if self.mode not in (Mode.VANISHING, Mode.APPEARING):
            return
        if self._progress(now) < 1.0:
            return
        if self.mode is Mode.VANISHING:
            self.mode = Mode.GONE
            self._snapshot = None
            self._snapshot_mask = None
        else:
            self.mode = Mode.PRESENT
            self._return_mask = None

    def _progress(self, now: float) -> float:
        elapsed = now - self._transition_start
        return min(elapsed / self._config.effect.duration_seconds, 1.0)

    def _full_mask(self, vision: VisionResult | None) -> np.ndarray:
        mask = vision.mask if vision is not None else None
        return prepare_mask(mask, self._size, self._config.effect.mask_feather_px)

    def _make_burst(self, mask: np.ndarray, start: float, gather: float = 0.0) -> None:
        effect = self._config.effect
        centre, size = person_anchor(mask)
        seed = int(self._rng.integers(0, 2**31))
        smoke_life = effect.smoke_seconds * (RETURN_SMOKE_SHARE if gather > 0.0 else 1.0)
        self._bursts.append(
            Burst(
                centre,
                size,
                start,
                smoke_life,
                seed,
                leaf_life=effect.leaf_seconds,
                ambient=self._room_colour(centre, size),
                gather=gather,
            )
        )
        self._impact = Impact(
            centre,
            size,
            self._size,
            start,
            effect.shake_pixels * self._size[1] / 720,
            effect.flash_strength,
            seed,
        )

    def _make_lightning(self, mask: np.ndarray, now: float, strike_share: float) -> None:
        """Starts the arcs now, with the strike `strike_share` into the transition."""
        effect = self._config.effect
        centre, size = person_anchor(mask)
        seed = int(self._rng.integers(0, 2**31))
        lead = effect.duration_seconds * strike_share
        strike = now + lead
        self._bursts.append(
            Lightning(centre, size, self._size, strike, effect.spark_seconds, seed, lead)
        )
        self._impact = Impact(
            centre,
            size,
            self._size,
            strike,
            effect.shake_pixels * self._size[1] / 720,
            effect.flash_strength * ELECTRIC_FLASH_BOOST,
            seed,
            flash_colour=ELECTRIC_FLASH_COLOUR,
            flash_spread=ELECTRIC_FLASH_SPREAD,
            flash_seconds=ELECTRIC_FLASH_SECONDS,
            strobe=True,
        )

    def _room_colour(
        self, centre: tuple[float, float], size: float
    ) -> tuple[float, float, float]:
        """The average colour of the room around a point, for tinting the smoke."""
        x, y = int(centre[0]), int(centre[1])
        reach = int(size)
        area = self.plate[max(y - reach, 0) : y + reach, max(x - reach, 0) : x + reach]
        return tuple(float(channel) for channel in cv2.mean(area)[:3])

    def _render(
        self, frame: np.ndarray, vision: VisionResult | None, now: float
    ) -> np.ndarray:
        render = render_electric if self._electric else render_transition
        if self.mode is Mode.VANISHING:
            output = render(
                self._snapshot,
                self.plate,
                self._snapshot_mask,
                self._progress(now),
                self._direction,
            )
        elif self.mode is Mode.APPEARING:
            output = render(
                frame,
                self.plate,
                self._return_mask,
                1.0 - self._progress(now),
                self._direction,
            )
        elif self.mode is Mode.GONE:
            output = self.plate
        else:
            output = frame

        impact = self._impact
        if impact is not None and impact.alive(now):
            output = impact.refract(output, now)

        self._bursts = [burst for burst in self._bursts if burst.alive(now)]
        if self._bursts and (output is frame or output is self.plate):
            output = output.copy()
        for burst in self._bursts:
            burst.draw(output, now)

        if impact is not None and impact.alive(now):
            output = impact.flash(output, now)
            output = impact.shake(output, now)
        return output
