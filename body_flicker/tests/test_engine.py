"""State machine and effect tests, using painted frames instead of a camera."""

import numpy as np
import pytest

from flicker.config import (
    BackgroundConfig,
    CameraConfig,
    Config,
    EffectConfig,
)
from flicker.effects import person_anchor, prepare_mask, render_transition
from flicker.engine import Engine, HandInfo, Mode, VisionResult
from flicker.gesture import SignReading
from flicker.particles import Burst

WIDTH, HEIGHT = 320, 180
STEP = 1 / 30
BODY = (slice(50, 170), slice(130, 190))

CONFIG = Config(
    camera=CameraConfig(width=WIDTH, height=HEIGHT),
    background=BackgroundConfig(countdown_seconds=1.0, frames=5),
    effect=EffectConfig(mask_feather_px=2, smoke_seconds=0.9, leaf_seconds=1.0),
)
SMOKE_CONFIG = Config(
    camera=CONFIG.camera,
    background=CONFIG.background,
    effect=EffectConfig(
        style="smoke", mask_feather_px=2, smoke_seconds=0.9, leaf_seconds=1.0
    ),
)


def room():
    frame = np.full((HEIGHT, WIDTH, 3), 90, dtype=np.uint8)
    frame[:, :, 0] = np.linspace(40, 200, WIDTH).astype(np.uint8)
    return frame


def with_person():
    frame = room()
    frame[BODY] = (20, 30, 230)
    return frame


def person_mask():
    mask = np.zeros((HEIGHT // 4, WIDTH // 4), dtype=np.float32)
    mask[50 // 4:170 // 4, 130 // 4:190 // 4] = 1.0
    return mask


def empty_mask():
    return np.zeros((HEIGHT // 4, WIDTH // 4), dtype=np.float32)


def vision(now, sign=False, mask=True, frame=None):
    """`mask` is True for a visible person, False for none, or an array to use."""
    hands = ()
    if frame is None:
        frame = with_person()
    if sign:
        reading = SignReading(True, 0.1, "")
        hands = (HandInfo(reading, np.zeros((21, 2), dtype=np.float32)),)
    if mask is True:
        mask = person_mask()
    elif mask is False:
        mask = None
    return VisionResult(now, frame, mask, hands)


class Rig:
    """Drives an engine forward through simulated time."""

    def __init__(self, config=CONFIG):
        self.engine = Engine(config, seed=7)
        self.now = 0.0
        self.engine.begin_background_capture(self.now)
        self.run(1.5, frame=room(), mask=empty_mask())

    def tick(self, frame=None, sign=False, mask=True, result=None):
        frame = with_person() if frame is None else frame
        seen = result if result is not None else vision(self.now, sign, mask, frame)
        outcome = self.engine.step(frame, seen, self.now)
        self.now += STEP
        return outcome

    def run(self, seconds, **kwargs):
        outcome = None
        for _ in range(int(round(seconds / STEP))):
            outcome = self.tick(**kwargs)
        return outcome

    def vanish(self):
        self.engine.request_toggle()
        return self.run(1.5)


def red_pixels(frame):
    # Green must be low too, or a flash-lit yellow leaf would count as the person.
    return int(((frame[..., 2] > 180) & (frame[..., 1] < 100) & (frame[..., 0] < 80)).sum())


def test_background_is_captured_after_the_countdown():
    rig = Rig()
    assert rig.engine.plate is not None
    assert np.abs(rig.engine.plate.astype(int) - room().astype(int)).max() <= 1


def test_countdown_message_is_shown_and_the_feed_is_passed_through():
    engine = Engine(CONFIG)
    engine.begin_background_capture(0.0)
    frame = with_person()
    outcome = engine.step(frame, None, 0.2)
    assert outcome.message == "Get ready to leave: 1"
    assert np.array_equal(outcome.frame, frame)


def test_person_is_passed_through_untouched_while_visible():
    rig = Rig()
    frame = with_person()
    outcome = rig.tick(frame=frame)
    assert outcome.mode is Mode.PRESENT
    assert np.array_equal(outcome.frame, frame)


def test_held_sign_makes_the_person_vanish():
    rig = Rig()
    rig.run(0.5, sign=True)
    assert rig.engine.mode is Mode.PRESENT
    rig.run(0.2, sign=True)
    assert rig.engine.mode is Mode.VANISHING


def test_vanish_takes_the_configured_time():
    rig = Rig()
    rig.engine.request_toggle()
    began = rig.now
    while rig.tick().mode is not Mode.GONE:
        assert rig.now - began < 1.0
    assert rig.now - began == pytest.approx(0.4, abs=STEP * 2)


def test_only_the_clean_background_remains_after_the_smoke_clears():
    rig = Rig()
    outcome = rig.vanish()
    assert outcome.mode is Mode.GONE
    assert red_pixels(outcome.frame) == 0
    assert np.array_equal(outcome.frame, rig.engine.plate)


def test_smoke_body_flickers_and_breaks_up_during_the_vanish():
    rig = Rig(SMOKE_CONFIG)
    rig.engine.request_toggle()
    counts = [red_pixels(rig.tick().frame) for _ in range(13)]
    solid = BODY[0].stop - BODY[0].start
    solid *= BODY[1].stop - BODY[1].start
    assert counts[0] > solid * 0.8
    assert any(count < solid * 0.5 for count in counts[1:4]), counts
    assert any(count > solid * 0.8 for count in counts[3:]), counts
    assert counts[-1] == 0


def test_smoke_appears_during_the_vanish():
    rig = Rig(SMOKE_CONFIG)
    rig.engine.request_toggle()
    rig.run(0.5)
    frame = rig.tick().frame
    changed = np.abs(frame.astype(int) - rig.engine.plate.astype(int)).sum(axis=2) > 40
    assert changed.sum() > 500


def test_sign_seen_on_the_raw_feed_brings_the_person_back():
    rig = Rig()
    rig.vanish()
    assert rig.engine.mode is Mode.GONE
    outcome = rig.run(2.0, sign=True)
    assert outcome.mode is not Mode.GONE


def test_reappearing_ends_on_the_live_feed():
    rig = Rig()
    rig.vanish()
    rig.engine.request_toggle()
    rig.run(1.5)
    frame = with_person()
    outcome = rig.tick(frame=frame)
    assert outcome.mode is Mode.PRESENT
    assert np.array_equal(outcome.frame, frame)


def test_reappearing_starts_hidden_and_finishes_solid():
    rig = Rig()
    rig.vanish()
    rig.engine.request_toggle()
    outcomes = [rig.tick() for _ in range(13)]
    counts = [red_pixels(outcome.frame) for outcome in outcomes]
    assert counts[0] == 0
    assert counts[-1] > max(counts[:3])


def test_a_sign_during_a_transition_is_ignored():
    rig = Rig()
    rig.engine.request_toggle()
    for _ in range(6):
        rig.tick(sign=True)
    assert rig.engine.mode is Mode.VANISHING
    rig.engine.request_toggle()
    rig.run(0.6)
    assert rig.engine.mode is Mode.GONE


def test_sign_is_ignored_until_a_background_exists():
    engine = Engine(CONFIG)
    now = 0.0
    frame = with_person()
    for _ in range(90):
        outcome = engine.step(frame, vision(now, sign=True), now)
        now += STEP
        assert outcome.mode is Mode.PRESENT


def test_sign_is_ignored_during_recapture():
    rig = Rig()
    rig.engine.begin_background_capture(rig.now)
    rig.run(0.8, sign=True)
    assert rig.engine.mode is Mode.PRESENT


def test_manual_trigger_needs_a_background():
    engine = Engine(CONFIG)
    engine.request_toggle()
    assert engine.step(with_person(), None, 0.0).mode is Mode.PRESENT


def test_stale_tracking_result_cannot_fire_the_sign():
    rig = Rig()
    old_result = vision(rig.now, sign=True)
    rig.run(2.0, result=old_result)
    assert rig.engine.mode is Mode.PRESENT


def test_missing_mask_still_vanishes_cleanly():
    rig = Rig()
    rig.engine.request_toggle()
    outcome = rig.run(1.5, mask=False)
    assert outcome.mode is Mode.GONE
    assert np.array_equal(outcome.frame, rig.engine.plate)


def test_recapture_while_gone_keeps_the_person_hidden():
    rig = Rig()
    rig.vanish()
    old_plate = rig.engine.plate.copy()
    rig.engine.begin_background_capture(rig.now)
    outcome = rig.tick()
    assert outcome.mode is Mode.GONE
    assert np.array_equal(outcome.frame, old_plate)


def test_recapture_finishes_a_running_transition():
    rig = Rig()
    rig.engine.request_toggle()
    rig.tick()
    rig.engine.begin_background_capture(rig.now)
    assert rig.tick().mode is Mode.GONE


def test_clean_capture_has_no_warning():
    assert Rig().engine.warning == ""


def test_engine_never_modifies_the_camera_frame_or_plate():
    rig = Rig()
    plate = rig.engine.plate.copy()
    frame = with_person()
    original = frame.copy()
    rig.engine.request_toggle()
    for _ in range(60):
        rig.tick(frame=frame)
    rig.engine.request_toggle()
    for _ in range(60):
        rig.tick(frame=frame)
    assert np.array_equal(frame, original)
    assert np.array_equal(rig.engine.plate, plate)


def test_prepare_mask_scales_and_feathers():
    mask = prepare_mask(person_mask(), (WIDTH, HEIGHT), 3)
    assert mask.shape == (HEIGHT, WIDTH)
    assert mask.dtype == np.uint8
    assert mask[100, 160] > 240
    assert mask[10, 10] < 3
    assert 0 < mask[100, 129] < 255


def test_prepare_mask_without_a_mask_is_empty():
    assert prepare_mask(None, (WIDTH, HEIGHT), 3).sum() == 0


def test_smoke_is_placed_on_the_person():
    mask = prepare_mask(person_mask(), (WIDTH, HEIGHT), 0)
    (x, y), size = person_anchor(mask)
    assert x == pytest.approx(160, abs=8)
    assert y == pytest.approx(110, abs=8)
    assert size > 0


def test_smoke_defaults_to_the_centre_without_a_person():
    (x, y), _ = person_anchor(np.zeros((HEIGHT, WIDTH), dtype=np.float32))
    assert (x, y) == (WIDTH / 2, HEIGHT / 2)


def test_transition_is_fully_clean_at_the_end():
    mask = prepare_mask(person_mask(), (WIDTH, HEIGHT), 2)
    plate = room()
    assert np.array_equal(render_transition(with_person(), plate, mask, 1.0, 1), plate)


def test_transition_starts_on_the_real_picture():
    mask = prepare_mask(person_mask(), (WIDTH, HEIGHT), 2)
    frame = with_person()
    assert np.array_equal(render_transition(frame, room(), mask, 0.0, 1), frame)


def test_burst_depends_on_age_rather_than_frame_rate():
    canvas_a, canvas_b = room(), room()
    Burst((160, 90), 60, 10.0, 0.9, seed=3).draw(canvas_a, 10.3)
    burst = Burst((160, 90), 60, 10.0, 0.9, seed=3)
    for moment in (10.05, 10.1, 10.2):
        burst.draw(room(), moment)
    burst.draw(canvas_b, 10.3)
    assert np.array_equal(canvas_a, canvas_b)


@pytest.mark.parametrize("centre", [(0, 0), (WIDTH, HEIGHT), (-50, 90), (WIDTH + 50, -40)])
def test_burst_at_or_past_the_frame_edge_does_not_crash(centre):
    frame = room()
    burst = Burst(centre, 60, 0.0, 0.9, seed=1)
    for age in (0.01, 0.2, 0.5, 0.8):
        burst.draw(frame, age)


def test_finished_burst_draws_nothing():
    frame = room()
    Burst((160, 90), 60, 0.0, 0.9, seed=1).draw(frame, 2.0)
    assert np.array_equal(frame, room())
