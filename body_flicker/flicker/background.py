"""Builds the empty-room picture.

The only clean result comes from frames of a truly empty room: nobody detected and
nothing moving, for a run of frames in a row. Body masks are never perfect, so frames
with a person in them could leave a stray arm or shadow in the picture.

As a last resort, for someone who never leaves, a second picture is kept from the
parts of each frame that a person is not covering. Whatever was never seen is painted
in from its surroundings. That leaves a visible smudge, which is still far less
obvious than a frozen person.
"""

from __future__ import annotations

import cv2
import numpy as np

from .compositing import over

# Uncertain pixels count as person, so soft edges such as hair are never collected.
PERSON_THRESHOLD = 0.15
# Margin around the person, as a share of mask width.
MARGIN_FRACTION = 0.03
FILL_DIVISOR = 4
FILL_RADIUS = 5

# Above this share of the frame, somebody is still in view.
EMPTY_PERSON_SHARE = 0.015
# Catches what the mask misses: a limb at the edge of the frame, or a door closing.
MOTION_SIZE = (160, 90)
MOTION_LEVEL = 25
MOTION_SHARE = 0.01


class BackgroundCollector:
    def __init__(self, size: tuple[int, int], frames_needed: int):
        width, height = size
        self._size = size
        self._frames_needed = frames_needed

        self._empty_sum = np.zeros((height, width, 3), dtype=np.float32)
        self._empty_frames = 0
        self._empty_reference: np.ndarray | None = None

        self._partial_sum = np.zeros((height, width, 3), dtype=np.float32)
        self._partial_count = np.zeros((height, width), dtype=np.float32)
        self._ones = np.ones((height, width), dtype=np.uint8)

    def add(self, frame: np.ndarray, person_mask: np.ndarray) -> None:
        """Takes one camera frame and the mask computed from that same frame."""
        self._track_empty_room(frame, person_mask)

        clean = self._clean_area(person_mask)
        cv2.accumulate(frame, self._partial_sum, mask=clean)
        cv2.accumulate(self._ones, self._partial_count, mask=clean)

    def _track_empty_room(self, frame: np.ndarray, person_mask: np.ndarray) -> None:
        if float((person_mask > PERSON_THRESHOLD).mean()) > EMPTY_PERSON_SHARE:
            self._restart_empty_run()
            return

        small = cv2.resize(frame, MOTION_SIZE, interpolation=cv2.INTER_AREA)
        if self._empty_reference is not None:
            change = cv2.absdiff(small, self._empty_reference).max(axis=2)
            if float((change > MOTION_LEVEL).mean()) > MOTION_SHARE:
                self._restart_empty_run()

        if self._empty_frames == 0:
            self._empty_reference = small
        cv2.accumulate(frame, self._empty_sum)
        self._empty_frames += 1

    def _restart_empty_run(self) -> None:
        self._empty_sum[:] = 0.0
        self._empty_frames = 0
        self._empty_reference = None

    def _clean_area(self, person_mask: np.ndarray) -> np.ndarray:
        person = (person_mask > PERSON_THRESHOLD).astype(np.uint8) * 255
        radius = max(round(person.shape[1] * MARGIN_FRACTION), 1)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1)
        )
        person = cv2.dilate(person, kernel)
        person = cv2.resize(person, self._size, interpolation=cv2.INTER_NEAREST)
        return cv2.bitwise_not(person)

    @property
    def empty_progress(self) -> float:
        """How much of the required empty-room run is done, from 0 to 1."""
        return min(self._empty_frames / self._frames_needed, 1.0)

    @property
    def has_data(self) -> bool:
        return bool(self._partial_count.max() > 0)

    def build_empty(self) -> np.ndarray:
        """Returns the picture of the empty room."""
        return (self._empty_sum / self._empty_frames + 0.5).astype(np.uint8)

    def build_partial(self) -> tuple[np.ndarray, float]:
        """Returns the last-resort picture and the share that was painted in."""
        plate = self._partial_sum / np.maximum(self._partial_count, 1.0)[..., None]
        plate = (plate + 0.5).astype(np.uint8)
        unseen = (self._partial_count == 0).astype(np.uint8) * 255
        guessed = float(unseen.mean()) / 255.0
        if guessed == 0.0:
            return plate, guessed

        # Painting in is slow at full size, and the result is soft anyway.
        width, height = self._size
        small_size = (width // FILL_DIVISOR, height // FILL_DIVISOR)
        small = cv2.resize(plate, small_size, interpolation=cv2.INTER_AREA)
        small_unseen = cv2.resize(unseen, small_size, interpolation=cv2.INTER_NEAREST)
        small_unseen = cv2.dilate(small_unseen, np.ones((3, 3), dtype=np.uint8))
        filled = cv2.inpaint(small, small_unseen, FILL_RADIUS, cv2.INPAINT_TELEA)
        filled = cv2.resize(filled, self._size, interpolation=cv2.INTER_LINEAR)

        grown = cv2.dilate(unseen, np.ones((9, 9), dtype=np.uint8))
        return over(plate, filled, cv2.GaussianBlur(grown, (9, 9), 0)), guessed
