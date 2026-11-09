"""Tests for config loading, threading, the preview and missing hardware."""

import threading
import time
from pathlib import Path

import numpy as np
import pytest

from flicker import app
from flicker.capture import CameraError, Frame, LatestValue, WebcamSource
from flicker.config import CameraConfig, Config, ConfigError, PreviewConfig, load_config
from flicker.engine import HandInfo, Mode, StepResult
from flicker.gesture import SignReading
from flicker.preview import Stats, compose_preview, hand_problem

ROOT = Path(__file__).resolve().parent.parent


def write_config(tmp_path, text):
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_shipped_config_matches_the_defaults():
    assert load_config(ROOT / "config.toml") == Config()


def test_missing_config_uses_defaults(tmp_path):
    assert load_config(tmp_path / "absent.toml") == Config()


def test_partial_config_keeps_other_defaults(tmp_path):
    config = load_config(write_config(tmp_path, "[sign]\nhold_seconds = 1\n"))
    assert config.sign.hold_seconds == 1
    assert config.sign.cooldown_seconds == 2.0


@pytest.mark.parametrize(
    "text, fragment",
    [
        ("[sign]\nhold_secnds = 1\n", "hold_secnds"),
        ("[signs]\nhold_seconds = 1\n", "signs"),
        ("[sign]\nhold_seconds = -1\n", "out of range"),
        ("[camera]\nwidth = 0\n", "out of range"),
        ("[camera]\nwidth = 12.5\n", "int"),
        ("[preview]\nmirror = 1\n", "bool"),
        ("[sign\n", "syntax"),
    ],
)
def test_bad_config_gives_a_clear_error(tmp_path, text, fragment):
    with pytest.raises(ConfigError, match=fragment):
        load_config(write_config(tmp_path, text))


def test_latest_value_drops_old_values_for_slow_readers():
    box = LatestValue()
    for value in range(100):
        box.set(value)
    assert box.get() == 99


def test_latest_value_wait_times_out_without_a_new_value():
    box = LatestValue()
    box.set("first")
    _, version = box.wait_for_newer(0, 0.01)
    started = time.monotonic()
    value, same_version = box.wait_for_newer(version, 0.05)
    assert value == "first"
    assert same_version == version
    assert time.monotonic() - started < 1.0


def test_latest_value_wakes_a_waiting_reader():
    box = LatestValue()
    threading.Timer(0.02, box.set, ("new",)).start()
    value, _ = box.wait_for_newer(0, 2.0)
    assert value == "new"


class FakeSource:
    def __init__(self):
        self.latest = LatestValue()
        self.latest.set(Frame(np.zeros((180, 320, 3), dtype=np.uint8), time.monotonic()))


class SlowVision:
    """Tracking that has produced nothing yet and never blocks the caller."""

    error = None

    def __init__(self):
        self.latest = LatestValue()


class CountingSink:
    active = True

    def __init__(self):
        self.sent = 0

    def send(self, image):
        self.sent += 1


def test_video_keeps_flowing_when_tracking_has_no_result():
    config = Config(camera=CameraConfig(width=320, height=180, fps=30))
    sink = CountingSink()
    app._run_loop(config, FakeSource(), SlowVision(), sink, None, duration=0.5)
    assert sink.sent >= 10


def test_missing_virtual_camera_is_reported_without_crashing(monkeypatch, capsys):
    def no_driver(**_):
        raise RuntimeError("OBS Virtual Camera device not found")

    monkeypatch.setattr(app.pyvirtualcam, "Camera", no_driver)
    sink = app.VirtualCamera(CameraConfig())
    assert not sink.active
    sink.send(np.zeros((720, 1280, 3), dtype=np.uint8))
    sink.close()
    assert "Install OBS Studio" in capsys.readouterr().err


def test_camera_that_will_not_open_gives_a_clear_error(monkeypatch):
    class Closed:
        def __init__(self, *_):
            pass

        def isOpened(self):
            return False

    monkeypatch.setattr("flicker.capture.cv2.VideoCapture", Closed)
    with pytest.raises(CameraError, match="Could not open camera"):
        WebcamSource(CameraConfig())


def test_camera_that_sends_no_picture_gives_a_clear_error(monkeypatch):
    class Silent:
        def __init__(self, *_):
            self.released = False

        def isOpened(self):
            return True

        def set(self, *_):
            return True

        def read(self):
            return False, None

        def release(self):
            self.released = True

    monkeypatch.setattr("flicker.capture.cv2.VideoCapture", Silent)
    with pytest.raises(CameraError, match="sent no picture"):
        WebcamSource(CameraConfig())


def make_hand_info(x, is_sign=True, problem=""):
    points = np.full((21, 2), (x, 0.5), dtype=np.float32)
    return HandInfo(SignReading(is_sign, 0.1, problem), points)


def preview_for(hands, mirror, alert=""):
    output = np.zeros((720, 1280, 3), dtype=np.uint8)
    step = StepResult(output, Mode.GONE, 0.0)
    settings = PreviewConfig(mirror=mirror)
    return compose_preview(output, hands, step, Stats(30, 12, True), settings, alert)


def hand_dots(image):
    """Finds the green hand dot's x position in the preview's picture."""
    view = image[:360]
    columns = np.nonzero((view[..., 1] > 180) & (view[..., 0] < 160))[1]
    return float(columns.mean()) / view.shape[1]


def test_hand_dots_stay_on_the_hand_when_the_preview_is_mirrored():
    hand = (make_hand_info(0.2),)
    plain = hand_dots(preview_for(hand, mirror=False))
    mirrored = hand_dots(preview_for(hand, mirror=True))
    assert plain == pytest.approx(0.2, abs=0.05)
    assert mirrored == pytest.approx(0.8, abs=0.05)


def test_preview_mirrors_the_picture_but_output_is_left_untouched():
    output = np.zeros((720, 1280, 3), dtype=np.uint8)
    output[:, :640] = (0, 0, 255)
    untouched = output.copy()
    step = StepResult(output, Mode.PRESENT, 0.0)
    settings = PreviewConfig(mirror=True)
    image = compose_preview(output, (), step, Stats(30, 12, True), settings)
    assert image[200, 100, 2] < 50
    assert image[200, 500, 2] > 200
    assert np.array_equal(output, untouched)


def test_hint_prefers_the_hand_making_the_sign():
    hands = (make_hand_info(0.2, False, "curl ring finger"), make_hand_info(0.8))
    assert hand_problem(hands) == "Sign seen, hold it"
    assert hand_problem(hands[:1]) == "Sign: curl ring finger"
    assert hand_problem(()) == "No hand seen"
