"""Runs hand tracking and body segmentation on the raw camera feed.

This works on a separate thread, so slow inference makes tracking skip frames but
never delays the video going to the call. It only ever sees camera frames, which
is why the sign still works while the output shows an empty room.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from .capture import Frame, LatestValue
from .config import Config, SignConfig
from .engine import HandInfo, VisionResult
from .gesture import read_sign
from .models import BODY_MODEL, HAND_MODEL


class Analyzer:
    """Wraps the two MediaPipe models."""

    def __init__(self, model_folder: Path, sign: SignConfig, input_width: int):
        self._sign = sign
        self._input_width = input_width
        self._hands = vision.HandLandmarker.create_from_options(
            vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(model_folder / HAND_MODEL)),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=2,
            )
        )
        self._body = vision.ImageSegmenter.create_from_options(
            vision.ImageSegmenterOptions(
                base_options=BaseOptions(model_asset_path=str(model_folder / BODY_MODEL)),
                running_mode=vision.RunningMode.VIDEO,
                output_confidence_masks=True,
                output_category_mask=False,
            )
        )
        self._last_timestamp_ms = 0

    def analyze(self, image: np.ndarray) -> tuple[np.ndarray, tuple[HandInfo, ...]]:
        """Returns the person mask and hands for one BGR frame."""
        height, width = image.shape[:2]
        if width > self._input_width:
            size = (self._input_width, round(height * self._input_width / width))
            image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # The models require strictly increasing timestamps in video mode.
        timestamp_ms = max(int(time.monotonic() * 1000), self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp_ms

        body = self._body.segment_for_video(mp_image, timestamp_ms)
        mask = np.squeeze(body.confidence_masks[0].numpy_view()).astype(np.float32).copy()

        hands = self._hands.detect_for_video(mp_image, timestamp_ms)
        found = []
        for world, image_marks in zip(hands.hand_world_landmarks, hands.hand_landmarks):
            points = np.array([(p.x, p.y, p.z) for p in world], dtype=np.float32)
            flat = np.array([(p.x, p.y) for p in image_marks], dtype=np.float32)
            found.append(HandInfo(read_sign(points, self._sign), flat))
        return mask, tuple(found)

    def close(self) -> None:
        self._hands.close()
        self._body.close()


class VisionWorker:
    def __init__(self, config: Config, frames: LatestValue, model_folder: Path):
        self._frames = frames
        self._analyzer = Analyzer(model_folder, config.sign, config.vision.input_width)
        self._min_period = 1.0 / config.vision.max_rate_hz
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="vision", daemon=True)
        self.latest = LatestValue()
        self.error: str | None = None
        self.rest_until = 0.0  # on the time.monotonic clock

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if not self._thread.is_alive():
            self._analyzer.close()

    def _run(self) -> None:
        version = 0
        while not self._stop.is_set():
            if time.monotonic() < self.rest_until:
                self._stop.wait(0.02)
                continue
            frame, newest = self._frames.wait_for_newer(version, timeout=0.2)
            if newest == version or not isinstance(frame, Frame):
                continue
            version = newest
            started = time.monotonic()
            try:
                mask, hands = self._analyzer.analyze(frame.image)
            except Exception as error:  # surfaced in the preview; video keeps flowing
                self.error = f"Tracking stopped: {error}"
                return
            elapsed = time.monotonic() - started
            self.latest.set(
                VisionResult(
                    timestamp=frame.timestamp,
                    frame=frame.image,
                    mask=mask,
                    hands=hands,
                    inference_ms=elapsed * 1000,
                )
            )
            # Resting between runs leaves CPU for the video, which matters most
            # during the effect. A 0.6 second hold needs nothing faster.
            self._stop.wait(max(self._min_period - elapsed, 0.0))
