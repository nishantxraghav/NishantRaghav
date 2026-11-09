"""Reads frames on a background thread and keeps only the newest one."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .config import CameraConfig


class CameraError(Exception):
    """The camera could not be used. The message is shown to the user."""


@dataclass(frozen=True)
class Frame:
    image: np.ndarray
    timestamp: float


class LatestValue:
    """A one-slot mailbox. Slow readers skip values and never block the writer."""

    def __init__(self):
        self._condition = threading.Condition()
        self._value = None
        self._version = 0

    def set(self, value) -> None:
        with self._condition:
            self._value = value
            self._version += 1
            self._condition.notify_all()

    def get(self):
        with self._condition:
            return self._value

    def wait_for_newer(self, version: int, timeout: float) -> tuple[object | None, int]:
        """Waits for a value newer than `version`. Returns (value, its version)."""
        with self._condition:
            self._condition.wait_for(lambda: self._version > version, timeout)
            return self._value, self._version


class FrameSource:
    """Runs a read loop on its own thread and publishes to `latest`."""

    def __init__(self, camera: CameraConfig):
        self._size = (camera.width, camera.height)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="capture", daemon=True)
        self.latest = LatestValue()

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._close()

    def _read(self) -> np.ndarray | None:
        raise NotImplementedError

    def _close(self) -> None:
        pass

    def _run(self) -> None:
        while not self._stop.is_set():
            image = self._read()
            if image is None:
                time.sleep(0.02)
                continue
            if (image.shape[1], image.shape[0]) != self._size:
                image = cv2.resize(image, self._size, interpolation=cv2.INTER_AREA)
            self.latest.set(Frame(image, time.monotonic()))


class WebcamSource(FrameSource):
    def __init__(self, camera: CameraConfig):
        super().__init__(camera)
        self._capture = cv2.VideoCapture(camera.index, cv2.CAP_DSHOW)
        if not self._capture.isOpened():
            raise CameraError(
                f"Could not open camera {camera.index}. Close other apps that use the "
                "camera, or change [camera] index in config.toml."
            )
        # MJPG is what lets most laptop webcams reach 720p at 30 FPS over USB.
        self._capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, camera.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, camera.height)
        self._capture.set(cv2.CAP_PROP_FPS, camera.fps)
        self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        ok, _ = self._capture.read()
        if not ok:
            self._capture.release()
            raise CameraError(
                f"Camera {camera.index} opened but sent no picture. Another app may be "
                "using it, or Windows may be blocking camera access in Privacy settings."
            )

    def _read(self) -> np.ndarray | None:
        ok, image = self._capture.read()
        return image if ok else None

    def _close(self) -> None:
        self._capture.release()


class FileSource(FrameSource):
    """Plays a video on a loop, or repeats an image, in place of a webcam."""

    def __init__(self, path: Path, camera: CameraConfig):
        super().__init__(camera)
        self._period = 1.0 / camera.fps
        self._next_time = 0.0
        self._still = cv2.imread(str(path)) if path.suffix.lower() in {
            ".jpg", ".jpeg", ".png", ".bmp"
        } else None
        self._video = None
        if self._still is None:
            self._video = cv2.VideoCapture(str(path))
            if not self._video.isOpened():
                raise CameraError(f"Could not read the source file: {path}")

    def _read(self) -> np.ndarray | None:
        wait = self._next_time - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._next_time = time.monotonic() + self._period

        if self._still is not None:
            return self._still.copy()
        ok, image = self._video.read()
        if not ok:
            self._video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, image = self._video.read()
        return image if ok else None

    def _close(self) -> None:
        if self._video is not None:
            self._video.release()
