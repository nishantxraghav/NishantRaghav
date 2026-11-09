"""Wires the camera, tracking, engine, virtual camera and preview together."""

from __future__ import annotations

import argparse
import sys
import time
import winsound
from collections import deque
from pathlib import Path

import numpy as np
import pyvirtualcam

from .capture import CameraError, FileSource, Frame, FrameSource, WebcamSource
from .config import Config, ConfigError, load_config
from .engine import Engine, VisionResult
from .models import ModelError, ensure_models
from .preview import PreviewWindow, Stats, compose_preview
from .vision import VisionWorker

ROOT = Path(__file__).resolve().parent.parent
CAMERA_STALL_SECONDS = 2.0

VIRTUAL_CAMERA_HELP = (
    "The OBS virtual camera is not available, so nothing will reach your call.\n"
    "  1. Install OBS Studio from https://obsproject.com\n"
    "  2. Open OBS once, then close it. If OBS is running its own virtual camera,\n"
    "     click Stop Virtual Camera there.\n"
    "  3. Restart this app."
)


class VirtualCamera:
    """Sends frames to the OBS virtual camera, if it is available."""

    def __init__(self, camera, enabled: bool = True):
        self._camera = None
        if not enabled:
            return
        try:
            self._camera = pyvirtualcam.Camera(
                width=camera.width,
                height=camera.height,
                fps=camera.fps,
                fmt=pyvirtualcam.PixelFormat.BGR,
                backend="obs",
            )
            print(f"Sending video to: {self._camera.device}")
        except RuntimeError as error:
            print(f"\n{VIRTUAL_CAMERA_HELP}\n  (details: {error})\n", file=sys.stderr)

    @property
    def active(self) -> bool:
        return self._camera is not None

    def send(self, image: np.ndarray) -> None:
        if self._camera is not None:
            self._camera.send(image)

    def close(self) -> None:
        if self._camera is not None:
            self._camera.close()


def _run_loop(
    config: Config,
    source: FrameSource,
    vision: VisionWorker,
    sink: VirtualCamera,
    window: PreviewWindow | None,
    duration: float | None,
) -> None:
    engine = Engine(config)
    period = 1.0 / config.camera.fps
    frame_times: deque[float] = deque(maxlen=30)
    started = time.monotonic()
    next_frame = started

    engine.begin_background_capture(started)

    while duration is None or time.monotonic() - started < duration:
        frame: Frame | None = source.latest.get()
        if frame is None:
            time.sleep(0.005)
            continue

        now = time.monotonic()
        result: VisionResult | None = vision.latest.get()
        was_capturing = engine.capturing
        step = engine.step(frame.image, result, now)
        vision.rest_until = engine.tracking_rests_until
        sink.send(step.frame)
        if was_capturing and not engine.capturing:
            # You are away from the screen at this point, so a sound says it is done.
            winsound.MessageBeep(winsound.MB_OK)

        frame_times.append(now)
        if window is not None:
            fps = 0.0
            if len(frame_times) > 1:
                fps = (len(frame_times) - 1) / max(frame_times[-1] - frame_times[0], 1e-6)

            alert = vision.error or ""
            if not alert and now - frame.timestamp > CAMERA_STALL_SECONDS:
                alert = "Camera stopped sending frames"
            if not alert and not sink.active:
                alert = "OBS virtual camera missing: see the console for the fix"

            image = compose_preview(
                step.frame,
                result.hands if result is not None else (),
                step,
                Stats(fps, result.inference_ms if result else 0.0, sink.active),
                config.preview,
                alert,
            )
            key = window.show(image)
            if key == "q":
                return
            if key == "b":
                engine.begin_background_capture(now)
            elif key == "t":
                engine.request_toggle()

        next_frame = max(next_frame + period, time.monotonic() - period)
        wait = next_frame - time.monotonic()
        if wait > 0:
            time.sleep(wait)


def run(config: Config, source_path: Path | None, use_vcam: bool, show: bool, duration) -> int:
    try:
        models = ensure_models(ROOT / "models")
        source = (
            FileSource(source_path, config.camera)
            if source_path is not None
            else WebcamSource(config.camera)
        )
    except (ModelError, CameraError) as error:
        print(f"\n{error}\n", file=sys.stderr)
        return 1

    vision = VisionWorker(config, source.latest, models)
    sink = VirtualCamera(config.camera, enabled=use_vcam)
    window = PreviewWindow() if show else None

    source.start()
    vision.start()
    try:
        _run_loop(config, source, vision, sink, window, duration)
    except KeyboardInterrupt:
        pass
    finally:
        vision.stop()
        source.stop()
        sink.close()
        if window is not None:
            window.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Anime body flicker for video calls.")
    parser.add_argument("--config", type=Path, default=ROOT / "config.toml")
    parser.add_argument("--source", type=Path, help="use a video or image instead of the webcam")
    parser.add_argument("--no-vcam", action="store_true", help="preview only")
    parser.add_argument("--no-preview", action="store_true", help="hide the preview window")
    parser.add_argument("--duration", type=float, help="quit after this many seconds")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as error:
        print(f"\n{error}\n", file=sys.stderr)
        return 1
    return run(config, args.source, not args.no_vcam, not args.no_preview, args.duration)
