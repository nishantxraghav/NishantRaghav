"""Tests for the smoke, leaves, impact and how they are sequenced."""

from dataclasses import replace

import numpy as np

from test_engine import CONFIG, STEP, Rig, room
from flicker.config import EffectConfig
from flicker.engine import Engine, Mode, TRACKING_REST_SECONDS
from flicker.impact import Impact
from flicker.leaves import Leaves
from flicker.particles import Burst
from flicker.smoke import Smoke

SIZE = (320, 180)
CENTRE = np.array((160, 90), dtype=np.float32)


def difference(first, second):
    return np.abs(first.astype(int) - second.astype(int)).sum(axis=2)


def drawn_smoke(ambient, seconds=0.3):
    frame = np.full((180, 320, 3), 80, dtype=np.uint8)
    rng = np.random.default_rng(1)
    Smoke(CENTRE, 70.0, 1.3, rng, ambient).draw(frame, seconds)
    return frame


def test_smoke_has_soft_edges_rather_than_an_outline():
    frame = drawn_smoke((128, 128, 128))
    changed = difference(frame, np.full_like(frame, 80))
    partly = ((changed > 12) & (changed < changed.max() * 0.8)).sum()
    assert partly > (changed > 12).sum() * 0.2


def test_smoke_takes_on_the_colour_of_the_room():
    blue_room = drawn_smoke((220, 60, 40))[60:120, 130:190].reshape(-1, 3).mean(axis=0)
    red_room = drawn_smoke((40, 60, 220))[60:120, 130:190].reshape(-1, 3).mean(axis=0)
    assert blue_room[0] > red_room[0]
    assert red_room[2] > blue_room[2]


def test_smoke_fades_away_over_its_life():
    blank = np.full((180, 320, 3), 80, dtype=np.uint8)
    early = difference(drawn_smoke((128, 128, 128), 0.3), blank).sum()
    late = difference(drawn_smoke((128, 128, 128), 1.2), blank).sum()
    assert late < early * 0.2


def test_leaves_keep_falling_after_the_smoke_has_cleared():
    frame = room()
    burst = Burst(CENTRE, 70.0, 0.0, 1.0, seed=2, leaf_life=2.6)
    burst.draw(frame, 1.5)
    assert burst.alive(1.5)
    assert difference(frame, room()).sum() > 0


def test_leaves_end_lower_than_they_peak():
    def lowest_leaf(seconds):
        frame = room()
        Leaves(CENTRE, 40.0, 3.0, np.random.default_rng(2)).draw_burst(frame, seconds)
        rows = np.nonzero(difference(frame, room()).sum(axis=1))[0]
        return rows.mean()

    assert lowest_leaf(2.0) > lowest_leaf(0.5)


def test_leaves_spiral_inward_before_a_return():
    def spread(progress):
        frame = room()
        Leaves(CENTRE, 40.0, 3.0, np.random.default_rng(2)).draw_gather(frame, progress)
        rows, columns = np.nonzero(difference(frame, room()))
        return np.hypot(columns - 160, rows - 90).mean()

    assert spread(0.9) < spread(0.4)


def test_burst_draws_only_gathering_leaves_before_it_starts():
    frame = room()
    Burst(CENTRE, 70.0, 10.0, 1.0, seed=2, gather=0.2).draw(frame, 9.9)
    assert difference(frame, room()).sum() > 0


def test_burst_draws_nothing_before_the_gather_begins():
    frame = room()
    Burst(CENTRE, 70.0, 10.0, 1.0, seed=2, gather=0.2).draw(frame, 9.0)
    assert np.array_equal(frame, room())


def make_impact(shake=8.0, flash=0.5):
    return Impact((160, 90), 70.0, SIZE, 0.0, shake, flash, seed=1)


def test_shockwave_bends_the_picture_then_stops():
    frame = room()
    frame[::8] = 255
    impact = make_impact()
    assert difference(impact.refract(frame, 0.1), frame).sum() > 0
    assert impact.refract(frame, 1.0) is frame


def test_flash_brightens_most_at_the_centre():
    frame = np.full((180, 320, 3), 60, dtype=np.uint8)
    lit = make_impact().flash(frame, 0.01)
    assert lit[90, 160].sum() > lit[5, 5].sum() > frame[5, 5].sum() - 1


def test_shake_moves_the_picture_then_settles():
    frame = room()
    impact = make_impact()
    assert difference(impact.shake(frame, 0.05), frame).sum() > 0
    assert impact.shake(frame, 1.0) is frame


def test_shake_and_flash_can_be_turned_off():
    frame = room()
    impact = make_impact(shake=0.0, flash=0.0)
    assert impact.shake(frame, 0.05) is frame
    assert impact.flash(frame, 0.01) is frame


def test_effect_never_changes_the_edges_of_the_frame_to_black():
    frame = room()
    shaken = make_impact(shake=12.0).shake(frame, 0.04)
    assert shaken[:, 0].min() >= 40 - 1


def test_tracking_rests_during_the_effect_so_it_gets_the_cpu():
    rig = Rig()
    assert rig.engine.tracking_rests_until <= rig.now
    rig.engine.request_toggle()
    rig.tick()
    assert rig.engine.tracking_rests_until > rig.now
    assert rig.engine.tracking_rests_until <= rig.now + TRACKING_REST_SECONDS


def test_tracking_rest_never_outlasts_the_cooldown():
    config = replace(CONFIG, sign=replace(CONFIG.sign, cooldown_seconds=0.3))
    rig = Rig(config)
    rig.engine.request_toggle()
    began = rig.now
    rig.tick()
    assert rig.engine.tracking_rests_until <= began + 0.3 + STEP


def test_background_capture_cancels_the_tracking_rest():
    rig = Rig()
    rig.engine.request_toggle()
    rig.tick()
    rig.engine.begin_background_capture(rig.now)
    assert rig.engine.tracking_rests_until == 0.0


def test_return_uses_the_mask_from_when_it_was_triggered():
    """Tracking rests during the return, so no new masks arrive to rely on."""
    rig = Rig()
    rig.vanish()
    rig.engine.request_toggle()
    rig.tick()
    outcomes = [rig.tick(result=None, mask=False) for _ in range(5)]
    assert all(outcome.mode is Mode.APPEARING for outcome in outcomes)


def test_new_burst_does_not_erase_leaves_still_falling():
    config = replace(CONFIG, effect=EffectConfig(style="smoke", leaf_seconds=4.0, mask_feather_px=2))
    rig = Rig(config)
    rig.engine.request_toggle()
    rig.run(1.0)
    rig.engine.request_toggle()
    rig.run(0.4)
    assert len(rig.engine._bursts) == 2
