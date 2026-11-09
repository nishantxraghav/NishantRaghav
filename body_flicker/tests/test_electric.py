"""Tests for the electric style: the overload, the collapse and the lightning."""

from pathlib import Path

import numpy as np
import pytest

from test_engine import BODY, CONFIG, STEP, Rig, red_pixels, room, with_person
from flicker.config import ConfigError, load_config
from flicker.effects import prepare_mask
from flicker.electric import COLLAPSE_END, Lightning, render_electric
from flicker.engine import Mode

SIZE = (320, 180)


def body_mask():
    mask = np.zeros((180, 320), dtype=np.uint8)
    mask[BODY] = 255
    return mask


def changed(frame, base, threshold=60):
    return np.abs(frame.astype(int) - base.astype(int)).sum(axis=2) > threshold


def test_electric_is_the_default_style():
    assert CONFIG.effect.style == "electric"


def test_unknown_style_is_rejected(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text('[effect]\nstyle = "fire"\n')
    with pytest.raises(ConfigError, match="effect.style"):
        load_config(path)


def test_render_starts_on_the_real_picture_and_ends_on_the_room():
    raw, plate = with_person(), room()
    assert np.array_equal(render_electric(raw, plate, body_mask(), 0.0), raw)
    assert np.array_equal(render_electric(raw, plate, body_mask(), 1.0), plate)


def test_body_overloads_white_hot_before_it_goes():
    raw, plate = with_person(), room()
    frame = render_electric(raw, plate, body_mask(), 0.15)
    assert frame[BODY].mean() > raw[BODY].mean() + 60


def test_body_squeezes_into_a_line():
    raw, plate = with_person(), room()
    widths = []
    for progress in (0.2, 0.45, 0.55):
        frame = render_electric(raw, plate, body_mask(), progress)
        columns = np.nonzero(changed(frame, plate, 200).any(axis=0))[0]
        widths.append(columns.max() - columns.min())
    assert widths[0] > widths[1] > widths[2]
    assert widths[2] < (BODY[1].stop - BODY[1].start) * 0.3


def test_body_glows_blue_around_its_edge():
    raw, plate = with_person(), room()
    frame = render_electric(raw, plate, body_mask(), 0.3)
    outside = frame[100:120, 192:200].astype(int) - plate[100:120, 192:200].astype(int)
    assert outside[..., 0].mean() > outside[..., 2].mean() + 5


def test_render_without_a_person_does_not_crash():
    empty = np.zeros((180, 320), dtype=np.uint8)
    frame = render_electric(with_person(), room(), empty, 0.5)
    assert frame.shape == (180, 320, 3)


def make_lightning(lead=0.2):
    return Lightning((160, 90), 60.0, SIZE, 1.0, 0.8, seed=4, lead=lead)


def drawn(lightning, now):
    frame = room()
    lightning.draw(frame, now)
    return frame


def test_lightning_only_adds_light():
    frame = drawn(make_lightning(), 1.05)
    assert (frame.astype(int) >= room().astype(int)).all()
    assert changed(frame, room()).sum() > 200


def test_lightning_crackles_while_charging_but_not_before():
    lightning = make_lightning(lead=0.2)
    assert np.array_equal(drawn(lightning, 0.7), room())
    assert changed(drawn(lightning, 0.9), room()).sum() > 0


def test_strike_comes_down_from_the_top_of_the_picture():
    frame = drawn(make_lightning(), 1.01)
    assert changed(frame[:10], room()[:10]).sum() > 0


def test_lightning_fades_out_and_ends():
    lightning = make_lightning()
    strike = changed(drawn(lightning, 1.05), room()).sum()
    late = changed(drawn(lightning, 1.7), room()).sum()
    assert late < strike * 0.3
    assert not lightning.alive(1.8)
    assert np.array_equal(drawn(lightning, 1.8), room())


def test_lightning_depends_on_time_rather_than_frame_rate():
    first, second = make_lightning(), make_lightning()
    for now in (0.9, 1.0, 1.1):
        first.draw(room(), now)
    assert np.array_equal(drawn(first, 1.2), drawn(second, 1.2))


def test_electric_vanish_ends_on_the_clean_room():
    rig = Rig()
    outcome = rig.vanish()
    assert outcome.mode is Mode.GONE
    assert red_pixels(outcome.frame) == 0
    assert np.array_equal(outcome.frame, rig.engine.plate)


def test_electric_vanish_flashes_the_whole_picture_at_the_strike():
    rig = Rig()
    rig.engine.request_toggle()
    strike = rig.now + CONFIG.effect.duration_seconds * COLLAPSE_END
    rig.run(strike - rig.now)
    corners = [rig.tick().frame[5, 5].astype(int).sum() for _ in range(2)]
    assert max(corners) > rig.engine.plate[5, 5].astype(int).sum() + 60


def test_electric_reappear_starts_hidden_and_ends_on_the_live_feed():
    rig = Rig()
    rig.vanish()
    rig.engine.request_toggle()
    first = rig.tick()
    assert red_pixels(first.frame) == 0
    rig.run(1.5)
    frame = with_person()
    outcome = rig.tick(frame=frame)
    assert outcome.mode is Mode.PRESENT
    assert np.array_equal(outcome.frame, frame)


def test_electric_mask_from_the_engine_is_usable():
    mask = prepare_mask(np.ones((45, 80), dtype=np.float32), SIZE, 2)
    frame = render_electric(with_person(), room(), mask, 0.4)
    assert frame.shape == (180, 320, 3)
