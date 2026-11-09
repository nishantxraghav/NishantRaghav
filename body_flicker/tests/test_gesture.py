"""Sign logic tests, using a synthetic hand built from joint positions."""

import numpy as np
import pytest

from flicker.config import SignConfig
from flicker.gesture import HoldDetector, read_sign

CONFIG = SignConfig()

# Knuckle positions in palm lengths, wrist at the origin, fingers pointing +y.
KNUCKLES = {"index": -0.27, "middle": -0.05, "ring": 0.16, "little": 0.35}


def _finger(base_x, height, spread, extended):
    """Returns the four joints of one finger."""
    base = np.array([base_x, height, 0.0])
    if extended:
        step = np.array([np.sin(spread), np.cos(spread), 0.0])
        return [base, base + step * 0.45, base + step * 0.72, base + step * 0.95]
    # Folded back into the palm, so the tip ends closer to the wrist than the joint.
    return [
        base,
        base + np.array([0.0, 0.32, -0.25]),
        base + np.array([0.0, 0.10, -0.42]),
        base + np.array([0.0, -0.18, -0.28]),
    ]


def make_hand(
    index=True, middle=True, ring=False, little=False, spread=0.0, thumb_out=False
):
    thumb = [
        np.array([-0.3, 0.2, -0.05]),
        np.array([-0.42, 0.42, -0.1]),
        np.array([-0.38, 0.62, -0.2]),
    ]
    thumb.append(
        np.array([-1.0, 0.75, -0.2]) if thumb_out else np.array([-0.05, 0.72, -0.34])
    )
    joints = [np.zeros(3), *thumb]
    joints += _finger(KNUCKLES["index"], 0.96, -spread, index)
    joints += _finger(KNUCKLES["middle"], 1.0, spread, middle)
    joints += _finger(KNUCKLES["ring"], 0.95, 0.0, ring)
    joints += _finger(KNUCKLES["little"], 0.86, 0.0, little)
    return np.array(joints, dtype=np.float64)


def rotated(points, rng):
    matrix, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    return points @ matrix


def test_the_seal_is_recognised():
    reading = read_sign(make_hand(), CONFIG)
    assert reading.is_sign, reading.problem


@pytest.mark.parametrize(
    "name, hand, hint",
    [
        ("peace sign", make_hand(spread=0.3), "touch"),
        ("open palm", make_hand(ring=True, little=True), "ring"),
        ("fist", make_hand(index=False, middle=False), "index"),
        ("pointing", make_hand(middle=False), "middle"),
        ("three fingers", make_hand(ring=True), "ring"),
        ("rock sign", make_hand(middle=False, little=True), "middle"),
        ("thumb out", make_hand(thumb_out=True), "thumb"),
    ],
)
def test_other_hand_shapes_are_rejected_with_a_useful_hint(name, hand, hint):
    reading = read_sign(hand, CONFIG)
    assert not reading.is_sign, name
    assert hint in reading.problem


def test_result_does_not_depend_on_hand_angle_or_size():
    rng = np.random.default_rng(1)
    for _ in range(200):
        scale = rng.uniform(0.05, 3.0)
        assert read_sign(rotated(make_hand(), rng) * scale, CONFIG).is_sign
        assert not read_sign(rotated(make_hand(spread=0.3), rng) * scale, CONFIG).is_sign


def test_degenerate_landmarks_do_not_crash():
    assert not read_sign(np.zeros((21, 3)), CONFIG).is_sign


def run_hold(detector, signal, start=0.0, end=10.0, step=1 / 30):
    """Feeds signal(t) to the detector and returns the times it fired."""
    fired = []
    for tick in range(int((end - start) / step)):
        now = start + tick * step
        if detector.update(signal(now), now):
            fired.append(now)
    return fired


def test_fires_after_the_hold_time_and_not_before():
    fired = run_hold(HoldDetector(CONFIG), lambda t: t >= 1.0)
    assert len(fired) == 1
    assert fired[0] == pytest.approx(1.6, abs=0.04)


def test_brief_sign_does_not_fire():
    assert run_hold(HoldDetector(CONFIG), lambda t: 1.0 <= t < 1.4) == []


def test_continuous_hold_fires_only_once():
    assert len(run_hold(HoldDetector(CONFIG), lambda t: True, end=20.0)) == 1


def test_cooldown_blocks_a_quick_second_use():
    # Second sign begins 0.5s after the first fires, inside the cooldown.
    fired = run_hold(HoldDetector(CONFIG), lambda t: 1.0 <= t < 1.7 or 2.1 <= t < 2.9)
    assert len(fired) == 1


def test_sign_works_again_after_the_cooldown():
    fired = run_hold(HoldDetector(CONFIG), lambda t: 1.0 <= t < 1.7 or 4.0 <= t < 5.0)
    assert len(fired) == 2
    assert fired[1] == pytest.approx(4.6, abs=0.04)


def test_sign_held_through_end_of_cooldown_needs_a_release():
    fired = run_hold(HoldDetector(CONFIG), lambda t: t >= 1.0, end=8.0)
    assert len(fired) == 1


def test_short_tracking_dropout_does_not_reset_the_hold():
    signal = lambda t: t >= 1.0 and not 1.3 <= t < 1.4
    fired = run_hold(HoldDetector(CONFIG), signal)
    assert fired[0] == pytest.approx(1.6, abs=0.04)


def test_long_dropout_resets_the_hold():
    signal = lambda t: 1.0 <= t < 1.4 or 1.8 <= t < 2.2
    assert run_hold(HoldDetector(CONFIG), signal) == []


def test_hold_time_is_real_time_at_low_frame_rates():
    fired = run_hold(HoldDetector(CONFIG), lambda t: t >= 1.0, step=1 / 10)
    assert fired[0] == pytest.approx(1.6, abs=0.11)
