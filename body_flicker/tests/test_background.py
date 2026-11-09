"""The person must never be saved into the empty-room picture.

A person in that picture makes vanishing look like the video has paused.
"""

import numpy as np

from test_engine import (
    BODY,
    CONFIG,
    HEIGHT,
    STEP,
    WIDTH,
    empty_mask,
    person_mask,
    red_pixels,
    room,
    vision,
    with_person,
)
from flicker.background import BackgroundCollector
from flicker.engine import Engine, Mode

SIZE = (WIDTH, HEIGHT)
MARKER = (slice(80, 120), slice(150, 170))
MARKER_COLOUR = (0, 240, 240)


def room_with_marker():
    """A room with something on the wall that the person sits in front of."""
    frame = room()
    frame[MARKER] = MARKER_COLOUR
    return frame


def run_capture(engine, seconds, frame, mask=True, now=0.0):
    outcome = None
    for _ in range(int(seconds / STEP)):
        outcome = engine.step(frame, vision(now, mask=mask, frame=frame), now)
        now += STEP
    return outcome, now


def started_engine():
    engine = Engine(CONFIG, seed=1)
    engine.begin_background_capture(0.0)
    return engine


def test_body_part_the_mask_misses_leaves_no_trace_once_the_room_is_empty():
    """The mask misses an arm while the person leaves. Real masks are never perfect."""
    engine = started_engine()
    arm = (slice(60, 120), slice(40, 120))
    sitting = with_person()
    sitting[arm] = (20, 30, 230)
    _, now = run_capture(engine, 3.0, sitting)  # the mask only covers the body

    run_capture(engine, 2.0, room(), mask=empty_mask(), now=now)
    assert engine.plate is not None
    assert np.abs(engine.plate.astype(int) - room().astype(int)).max() <= 1


def test_undetected_movement_restarts_the_empty_room_run():
    """An arm at the frame edge that the mask misses must not reach the picture."""
    engine = started_engine()
    waving = room()
    waving[:, :60] = (20, 30, 230)
    now = 1.0
    for tick in range(60):
        frame = waving if tick % 3 == 0 else room()
        engine.step(frame, vision(now, mask=empty_mask(), frame=frame), now)
        now += STEP
    assert engine.plate is None


def test_coming_back_too_early_restarts_the_empty_room_run():
    engine = started_engine()
    _, now = run_capture(engine, 1.1, room(), mask=empty_mask())
    assert 0.0 < engine.step(room(), None, now).message.count("%")
    _, now = run_capture(engine, 0.1, with_person(), now=now)
    outcome = engine.step(room(), None, now)
    assert outcome.message == "Leave the frame completely"


def test_slow_exposure_change_does_not_block_the_capture():
    """Webcams slowly adjust brightness when a person leaves."""
    engine = started_engine()
    now = 1.0
    for tick in range(30):
        frame = np.clip(room().astype(int) + tick // 3, 0, 255).astype(np.uint8)
        engine.step(frame, vision(now, mask=empty_mask(), frame=frame), now)
        now += STEP
    assert engine.plate is not None


def test_person_who_stays_in_shot_is_not_saved_into_the_background():
    engine = started_engine()
    frame = with_person()
    _, now = run_capture(engine, 35.0, frame)
    assert engine.plate is not None
    assert red_pixels(engine.plate) == 0

    engine.request_toggle()
    outcome, _ = run_capture(engine, 2.0, frame, now=now)
    assert outcome.mode is Mode.GONE
    assert red_pixels(outcome.frame) == 0


def test_staying_in_shot_gives_a_warning_about_the_smudge():
    engine = started_engine()
    outcome, _ = run_capture(engine, 35.0, with_person())
    assert "smudge" in outcome.warning


def test_guessed_area_blends_with_the_room():
    engine = started_engine()
    run_capture(engine, 35.0, with_person())
    difference = np.abs(engine.plate.astype(int) - room().astype(int))
    assert difference.max() <= 30


def test_capture_waits_while_the_person_is_in_the_way():
    engine = started_engine()
    outcome, _ = run_capture(engine, 10.0, with_person())
    assert engine.plate is None
    assert outcome.message == "Leave the frame completely"
    assert outcome.mode is Mode.PRESENT


def test_output_is_the_live_camera_while_waiting():
    engine = started_engine()
    frame = with_person()
    outcome, _ = run_capture(engine, 3.0, frame)
    assert np.array_equal(outcome.frame, frame)


def test_moving_aside_reveals_the_real_room_behind_the_person():
    engine = started_engine()
    sitting = room_with_marker()
    sitting[BODY] = (20, 30, 230)
    _, now = run_capture(engine, 3.0, sitting)
    assert engine.plate is None

    run_capture(engine, 2.0, room_with_marker(), mask=empty_mask(), now=now)
    assert engine.plate is not None
    assert engine.warning == ""
    assert np.abs(engine.plate.astype(int) - room_with_marker().astype(int)).max() <= 1


def test_leaning_never_finishes_the_capture_early():
    engine = started_engine()
    now = 1.0
    left, right = empty_mask(), empty_mask()
    left[:, :40] = 1.0
    right[:, 40:] = 1.0
    for tick in range(int(10 / STEP)):
        mask = left if tick % 60 < 30 else right
        engine.step(room(), vision(now, mask=mask, frame=room()), now)
        now += STEP
    assert engine.plate is None


def test_last_resort_uses_what_leaning_revealed():
    collector = BackgroundCollector(SIZE, 5)
    left, right = empty_mask(), empty_mask()
    left[:, :30] = 1.0  # narrower, so the margins around the masks do not overlap
    right[:, 50:] = 1.0
    collector.add(room(), left)
    collector.add(room(), right)
    plate, guessed = collector.build_partial()
    assert guessed == 0.0
    assert np.array_equal(plate, room())


def test_slow_tracking_still_finishes_the_capture():
    """Results arrive 250 ms late and only 7 times a second, as measured live."""
    engine = started_engine()
    room_frame = room()
    now, result = 0.0, None
    for tick in range(int(6 / STEP)):
        if tick % 4 == 0:
            result = vision(now - 0.25, mask=empty_mask(), frame=room_frame)
        engine.step(room_frame, result, now)
        now += STEP
    assert engine.plate is not None


def test_late_mask_is_paired_with_its_own_frame_and_not_the_live_one():
    """The mask says the room is clear, but the live picture has a person in it."""
    engine = started_engine()
    live = with_person()
    now = 1.5
    for _ in range(60):
        late = vision(now - 0.25, mask=empty_mask(), frame=room())
        engine.step(live, late, now)
        now += STEP
    assert engine.plate is not None
    assert red_pixels(engine.plate) == 0


def test_a_tracking_result_is_only_counted_once():
    engine = started_engine()
    result = vision(1.2, mask=empty_mask(), frame=room())
    now = 1.3
    for _ in range(12):  # within the age limit, and more steps than `frames` needs
        engine.step(room(), result, now)
        now += STEP
    assert engine.plate is None


def test_vanish_uses_the_frame_the_mask_came_from():
    """A person who moved after the mask was made must not leave a piece behind."""
    engine = started_engine()
    _, now = run_capture(engine, 1.5, room(), mask=empty_mask())
    moved = room()
    moved[50:170, 200:260] = (20, 30, 230)  # the live picture, further to the right
    late = vision(now - 0.25, frame=with_person())
    engine.request_toggle()
    outcome = engine.step(moved, late, now)
    assert outcome.mode is Mode.VANISHING
    assert red_pixels(outcome.frame[50:170, 200:260]) == 0
    assert red_pixels(outcome.frame[BODY]) > 0


def test_capture_waits_forever_without_any_tracking():
    engine = started_engine()
    frame = with_person()
    now = 0.0
    for _ in range(int(30 / STEP)):
        engine.step(frame, None, now)
        now += STEP
    assert engine.plate is None


def test_recapture_keeps_the_old_background_until_the_new_one_is_ready():
    engine = started_engine()
    _, now = run_capture(engine, 1.5, room(), mask=empty_mask())
    plate = engine.plate.copy()
    engine.begin_background_capture(now)
    run_capture(engine, 3.0, with_person(), now=now)
    assert np.array_equal(engine.plate, plate)
