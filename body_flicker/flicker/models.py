"""Downloads and verifies the MediaPipe model files."""

from __future__ import annotations

import hashlib
import urllib.error
import urllib.request
from pathlib import Path

HAND_MODEL = "hand_landmarker.task"
BODY_MODEL = "selfie_segmenter.tflite"

_BASE = "https://storage.googleapis.com/mediapipe-models"
_MODELS = {
    HAND_MODEL: (
        f"{_BASE}/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1",
    ),
    BODY_MODEL: (
        f"{_BASE}/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite",
        "191ac9529ae506ee0beefa6b2c945a172dab9d07d1e802a290a4e4038226658b",
    ),
}


class ModelError(Exception):
    """A model could not be downloaded. The message is shown to the user."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_models(folder: Path) -> Path:
    """Makes sure both models exist and are intact, downloading them if needed."""
    folder.mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in _MODELS.items():
        target = folder / name
        if target.exists() and _sha256(target) == expected:
            continue

        print(f"Downloading {name}...")
        partial = target.with_suffix(target.suffix + ".part")
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                partial.write_bytes(response.read())
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            partial.unlink(missing_ok=True)
            raise ModelError(
                f"Could not download {name}: {error}\n"
                "Check your internet connection and try again."
            ) from error

        if _sha256(partial) != expected:
            partial.unlink(missing_ok=True)
            raise ModelError(f"The downloaded {name} failed its integrity check.")
        partial.replace(target)
    return folder
