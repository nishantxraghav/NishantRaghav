"""Runs the real MediaPipe models on real photos.

Set FLICKER_SAMPLES to a folder holding the MediaPipe sample images. These tests
are skipped without it, because the photos are not part of the project.
"""

import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from flicker.config import BackgroundConfig, Config, SignConfig
from flicker.engine import Engine, VisionResult
from flicker.models import ensure_models
from flicker.vision import Analyzer

SAMPLES = Path(os.environ.get("FLICKER_SAMPLES", "no-samples-configured"))
ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(not SAMPLES.is_dir(), reason="FLICKER_SAMPLES not set")


@pytest.fixture()
def analyzer():
    tool = Analyzer(ensure_models(ROOT / "models"), SignConfig(), input_width=640)
    yield tool
    tool.close()


def load(name):
    image = cv2.imread(str(SAMPLES / name))
    assert image is not None, name
    return image


def analyze_settled(analyzer, image):
    """Video mode tracks across frames, so give it several like a live feed."""
    result = None
    for _ in range(5):
        result = analyzer.analyze(image)
    return result


@pytest.mark.parametrize(
    "photo", ["victory.jpg", "pointing_up.jpg", "thumbs_up.jpg", "thumbs_down.jpg"]
)
def test_real_hand_photos_do_not_trigger_the_sign(analyzer, photo):
    _, hands = analyze_settled(analyzer, load(photo))
    assert hands, f"no hand found in {photo}"
    assert not any(hand.reading.is_sign for hand in hands)


def test_real_peace_sign_is_blocked_by_the_touching_check(analyzer):
    _, hands = analyze_settled(analyzer, load("victory.jpg"))
    assert "touch" in hands[0].reading.problem
    assert hands[0].reading.tip_gap > SignConfig().max_tip_gap * 1.5


def painted_room(width, height):
    room = np.full((height, width, 3), (120, 150, 175), dtype=np.uint8)
    room[height * 3 // 4:] = (70, 95, 120)
    cv2.rectangle(room, (80, 120), (360, 400), (205, 195, 170), -1)
    cv2.rectangle(room, (940, 90), (1200, 520), (90, 110, 150), -1)
    return room


def person_cutout(analyzer, height):
    photo = load("portrait.jpg")
    mask, _ = analyze_settled(analyzer, photo)
    size = (round(photo.shape[1] * height / photo.shape[0]), height)
    return cv2.resize(photo, size), cv2.resize(mask, size)[..., None]


def place_person(room, person, mask, x):
    if x >= room.shape[1]:
        return room.copy()
    frame = room.astype(np.float32)
    width = person.shape[1]
    left, right = max(x, 0), min(x + width, room.shape[1])
    cut = (slice(None), slice(left - x, right - x))
    frame[:, left:right] = frame[:, left:right] * (1 - mask[cut]) + person[cut] * mask[cut]
    return frame.astype(np.uint8)


def capture_with_real_tracking(analyzer, positions, seconds_each, timeout=30.0):
    """Runs a capture on a person sitting, then moving, using the real body model."""
    room = painted_room(1280, 720)
    person, mask = person_cutout(analyzer, 720)
    engine = Engine(Config(background=BackgroundConfig(timeout_seconds=timeout)), seed=1)
    engine.begin_background_capture(0.0)
    now = 5.0
    for x in positions:
        frame = place_person(room, person, mask, x)
        for _ in range(int(seconds_each * 15)):
            person_mask, _ = analyzer.analyze(frame)
            result = VisionResult(now, frame, person_mask)
            for _ in range(2):  # the video runs at twice the tracking rate
                engine.step(frame, result, now)
                now += 1 / 30
            if engine.plate is not None:
                return engine, room
    return engine, room


def share_of_wrong_pixels(plate, room):
    difference = np.abs(plate.astype(int) - room.astype(int)).max(axis=2)
    return float((difference > 25).mean())


def test_real_tracking_gets_the_exact_room_once_the_person_leaves(analyzer):
    engine, room = capture_with_real_tracking(
        analyzer, [230, -420, 700, 1400], seconds_each=2
    )
    assert engine.plate is not None, "capture never finished"
    assert engine.warning == ""
    assert np.abs(engine.plate.astype(int) - room.astype(int)).max() <= 1


def test_real_tracking_does_not_finish_while_a_person_is_in_view(analyzer):
    engine, _ = capture_with_real_tracking(analyzer, [230, -420, 700], seconds_each=2)
    assert engine.plate is None


def test_real_tracking_keeps_a_motionless_person_out_of_the_background(analyzer):
    engine, room = capture_with_real_tracking(
        analyzer, [230], seconds_each=16, timeout=15.0
    )
    assert engine.plate is not None, "capture never finished"
    assert "smudge" in engine.warning
    assert share_of_wrong_pixels(engine.plate, room) < 0.12


def test_person_mask_is_high_on_the_person_and_low_on_the_background(analyzer):
    mask, _ = analyze_settled(analyzer, load("portrait.jpg"))
    height, width = mask.shape
    assert mask.ndim == 2
    assert mask[height // 3:2 * height // 3, width // 3:2 * width // 3].mean() > 0.8
    assert mask[: height // 10, : width // 10].mean() < 0.1


def test_portrait_never_triggers_the_sign(analyzer):
    # The model can imagine a hand in a portrait, so only the sign result matters.
    _, hands = analyze_settled(analyzer, load("portrait.jpg"))
    assert not any(hand.reading.is_sign for hand in hands)
