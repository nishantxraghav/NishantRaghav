"""The electric style: the body overloads, zips into a line and is gone in a strike.

`render_electric` draws the body. `progress` runs from 0 (fully present) to 1 (fully
gone), and reappearing plays the same timeline backwards. `Lightning` draws the arcs,
the strike and the sparks on top. Both are formulas of time, so they look the same at
any frame rate.
"""

from __future__ import annotations

import cv2
import numpy as np

from .compositing import over, smoothstep

# Body timeline, as shares of the transition.
BLEND_END = 0.08        # eases in from the real picture so the first frame has no pop
BLINK = (0.10, 0.20)    # one frame of white-hot overload before the body settles back
HEAT_START = 0.22
HEAT_END = 0.45
COLLAPSE_START = 0.35   # the body squeezes sideways into a line...
COLLAPSE_END = 0.58     # ...and is a line here: the strike lands at this moment
BEAM_END = 0.78         # the leftover line fades out by here

WHITE_HOT = (255, 248, 236)     # BGR
GLOW_BGR = (255, 165, 60)       # electric blue
CORE_BGR = (255, 246, 228)
SPARK_BGR = (255, 228, 170)
GLOW_DIVISOR = 4

STRIKE_SECONDS = 0.16
FORK_SECONDS = 0.30
FLICKER_HZ = 30.0       # how often the bolts change shape
SPARKS = 48
SPARK_TRAIL = 0.035     # seconds of motion each spark streak shows
SPARK_DRAG = 3.0


def _glow(alpha: np.ndarray, colour: tuple[int, int, int]) -> np.ndarray:
    """Turns a single-channel uint8 intensity into a coloured light layer."""
    return cv2.merge(tuple(cv2.convertScaleAbs(alpha, alpha=c / 255.0) for c in colour))


def _slide_rows(image: np.ndarray, amount: int) -> np.ndarray:
    """Slides rows sideways, leaving empty pixels behind rather than wrapping."""
    if amount == 0:
        return image
    slid = np.zeros_like(image)
    if amount > 0:
        slid[:, amount:] = image[:, :-amount]
    else:
        slid[:, :amount] = image[:, -amount:]
    return slid


def _paste(canvas: np.ndarray, patch: np.ndarray, left: int, top: int) -> None:
    """Copies a patch into a canvas, clipping whatever falls off the edge."""
    height, width = canvas.shape[:2]
    x0, y0 = max(left, 0), max(top, 0)
    x1 = min(left + patch.shape[1], width)
    y1 = min(top + patch.shape[0], height)
    if x1 <= x0 or y1 <= y0:
        return
    canvas[y0:y1, x0:x1] = patch[y0 - top : y1 - top, x0 - left : x1 - left]


def _glitch(body: np.ndarray, alpha: np.ndarray, amount: float, progress: float):
    """Tears the body into horizontal bands that jump sideways, like a bad signal."""
    if amount <= 0.0 or body.shape[1] < 8:
        return body, alpha
    rng = np.random.default_rng(int(progress * 60))
    bands = np.linspace(0, body.shape[0], 11).astype(int)
    reach = max(int(body.shape[1] * 0.1 * amount), 1)
    body, alpha = body.copy(), alpha.copy()
    for top, bottom in zip(bands[:-1], bands[1:]):
        if rng.random() < 0.45:
            amount_px = int(rng.integers(-reach, reach + 1))
            body[top:bottom] = _slide_rows(body[top:bottom], amount_px)
            alpha[top:bottom] = _slide_rows(alpha[top:bottom], amount_px)
    return body, alpha


def render_electric(
    raw: np.ndarray,
    plate: np.ndarray,
    mask: np.ndarray,
    progress: float,
    direction: int = 1,
) -> np.ndarray:
    """Renders one frame. `raw` supplies the body, `plate` the empty room."""
    if progress >= 1.0:
        return plate.copy()
    if progress <= 0.0:
        return raw.copy()

    height, width = raw.shape[:2]
    result = plate.copy()
    left, top, box_width, box_height = cv2.boundingRect(mask)
    light = np.zeros((height // GLOW_DIVISOR, width // GLOW_DIVISOR), dtype=np.uint8)

    if box_width > 0:
        area = (slice(top, top + box_height), slice(left, left + box_width))
        columns = mask[area].sum(axis=0, dtype=np.float64)
        centre_x = left + float((columns * np.arange(box_width)).sum() / columns.sum())

        if progress < COLLAPSE_END:
            body, alpha = raw[area], mask[area]
            heat = float(smoothstep(HEAT_START, HEAT_END, progress))
            if BLINK[0] <= progress < BLINK[1]:
                heat = 1.0
            if heat > 0.0:
                hot = np.empty_like(body)
                hot[:] = WHITE_HOT
                body = cv2.addWeighted(body, 1.0 - heat, hot, heat, 0.0)

            squeeze = float(smoothstep(COLLAPSE_START, COLLAPSE_END, progress))
            new_width = max(round(box_width * (1.0 - squeeze)), 2)
            if new_width != box_width:
                body = cv2.resize(body, (new_width, box_height), interpolation=cv2.INTER_AREA)
                alpha = cv2.resize(alpha, (new_width, box_height), interpolation=cv2.INTER_AREA)
            tear = float(smoothstep(HEAT_START, COLLAPSE_START, progress)) * (1.0 - squeeze)
            body, alpha = _glitch(body, alpha, tear, progress)

            new_left = round(centre_x - new_width / 2)
            layer = np.zeros_like(raw)
            full_alpha = np.zeros(mask.shape, dtype=np.uint8)
            _paste(layer, body, new_left, top)
            _paste(full_alpha, alpha, new_left, top)
            result = over(result, layer, full_alpha)

            # A blue rim and aura that build as the charge does.
            small = cv2.resize(full_alpha, light.shape[::-1], interpolation=cv2.INTER_AREA)
            rim = cv2.morphologyEx(small, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
            aura = cv2.GaussianBlur(small, (0, 0), 4.0)
            charge = float(smoothstep(0.0, 0.3, progress))
            light = cv2.max(
                cv2.convertScaleAbs(rim, alpha=charge),
                cv2.convertScaleAbs(aura, alpha=0.5 * charge),
            )

        # The line the body squeezed into, lingering for a moment as a beam.
        beam = float(smoothstep(COLLAPSE_START, COLLAPSE_END, progress)) * (
            1.0 - float(smoothstep(COLLAPSE_END, BEAM_END, progress))
        )
        if beam > 0.0:
            x = int(np.clip(round(centre_x), 0, width - 1))
            cv2.line(
                light,
                (x // GLOW_DIVISOR, top // GLOW_DIVISOR),
                (x // GLOW_DIVISOR, (top + box_height) // GLOW_DIVISOR),
                int(255 * beam),
                2,
            )
            half = max(round(3 * beam * height / 720), 1)
            strip = result[top : top + box_height, max(x - half, 0) : x + half + 1]
            hot = np.empty_like(strip)
            hot[:] = WHITE_HOT
            strip[:] = cv2.addWeighted(strip, 1.0 - beam, hot, beam, 0.0)

    if light.any():
        light = cv2.GaussianBlur(light, (0, 0), 1.5)
        glow = cv2.resize(_glow(light, GLOW_BGR), (width, height), interpolation=cv2.INTER_LINEAR)
        result = cv2.add(result, glow)

    blend = float(smoothstep(0.0, BLEND_END, progress))
    if blend < 1.0:
        result = cv2.addWeighted(raw, 1.0 - blend, result, blend, 0.0)
    return result


def _bolt(rng: np.random.Generator, start, end, jag: float, detail: int = 5) -> np.ndarray:
    """A jagged line from start to end, made by repeatedly bending its midpoints."""
    points = np.array((start, end), dtype=np.float32)
    offset = float(np.hypot(*(points[1] - points[0]))) * jag
    for _ in range(detail):
        heads, tails = points[:-1], points[1:]
        along = tails - heads
        length = np.maximum(np.hypot(along[:, 0], along[:, 1]), 1e-6)[:, None]
        normal = np.stack((-along[:, 1], along[:, 0]), axis=1) / length
        middles = (heads + tails) / 2 + normal * rng.uniform(-offset, offset, (len(heads), 1))
        joined = np.empty((len(points) + len(middles), 2), dtype=np.float32)
        joined[0::2] = points
        joined[1::2] = middles
        points = joined
        offset /= 2
    return points


def _pointing(rng: np.random.Generator, origin, length: float, angle: float) -> np.ndarray:
    return np.asarray(origin, dtype=np.float32) + length * np.array(
        (np.cos(angle), np.sin(angle)), dtype=np.float32
    )


class Lightning:
    """Crackling arcs that charge up, a strike at `start`, then forks and sparks.

    The charge-up begins `lead` seconds before `start`.
    """

    def __init__(
        self,
        centre: tuple[float, float],
        size: float,
        frame_size: tuple[int, int],
        start: float,
        life: float,
        seed: int,
        lead: float = 0.0,
    ):
        rng = np.random.default_rng(seed)
        self._centre = np.array(centre, dtype=np.float32)
        self._size = float(size)
        self._scale = frame_size[1] / 720
        self.start = start
        self._life = life
        self._lead = lead
        self._seed = seed
        self._strike_x = float(centre[0] + rng.uniform(-0.35, 0.35) * size)

        angles = rng.uniform(0.0, 2 * np.pi, SPARKS)
        speeds = rng.uniform(1.5, 5.0, SPARKS) * size
        self._spark_velocity = np.stack((np.cos(angles), np.sin(angles)), axis=1) * speeds[:, None]
        self._spark_origin = self._centre + rng.normal(0.0, size * 0.15, (SPARKS, 2))
        self._spark_life = rng.uniform(0.25, 1.0, SPARKS) * life

    def alive(self, now: float) -> bool:
        return now < self.start + self._life

    def draw(self, frame: np.ndarray, now: float) -> None:
        """Draws onto a uint8 BGR frame in place. Light only ever adds brightness."""
        seconds = now - self.start
        if seconds < -self._lead or seconds >= self._life:
            return
        tick = int(np.floor(seconds * FLICKER_HZ)) + 100_000
        rng = np.random.default_rng((self._seed, tick))
        bolts = self._bolts(rng, seconds)
        sparks = self._sparks(seconds)
        if bolts or sparks:
            self._render(frame, bolts, sparks)

    def _bolts(self, rng: np.random.Generator, seconds: float) -> list[tuple[np.ndarray, float]]:
        size, centre = self._size, self._centre
        bolts = []

        if seconds < 0.0:
            # Charging: short arcs crawl over the body, more and brighter as it builds.
            charge = 1.0 + seconds / self._lead
            for _ in range(1 + round(4 * charge)):
                origin = centre + rng.normal(0.0, 1.0, 2) * (size * 0.3, size * 0.6)
                end = _pointing(rng, origin, size * rng.uniform(0.25, 0.55), rng.uniform(0, 2 * np.pi))
                bolts.append((_bolt(rng, origin, end, 0.35, 4), 0.35 + 0.65 * charge))
            return bolts

        if seconds < STRIKE_SECONDS:
            # The strike, from the top of the picture down into where the body was.
            fade = 1.0 - 0.5 * seconds / STRIKE_SECONDS
            flicker = 1.0 if int(seconds * FLICKER_HZ) % 2 == 0 else 0.6
            top = (self._strike_x + rng.uniform(-0.1, 0.1) * size, -10.0)
            bottom = (centre[0], centre[1] + size * 0.25)
            main = _bolt(rng, top, bottom, 0.16, 6)
            bolts.append((main, fade * flicker))
            for index in rng.choice(np.arange(8, len(main) - 8), 4, replace=False):
                heading = np.arctan2(*(main[index + 1] - main[index])[::-1])
                angle = heading + rng.choice((-1, 1)) * rng.uniform(0.4, 1.0)
                end = _pointing(rng, main[index], size * rng.uniform(0.3, 0.7), angle)
                bolts.append((_bolt(rng, main[index], end, 0.3, 4), 0.6 * fade * flicker))

        if seconds < FORK_SECONDS:
            # Forks thrown out sideways from the impact.
            fade = 1.0 - seconds / FORK_SECONDS
            for _ in range(6):
                end = _pointing(
                    rng, centre, size * rng.uniform(0.7, 1.5) * (0.6 + 0.4 * (1 - fade)),
                    rng.uniform(0, 2 * np.pi),
                )
                bolts.append((_bolt(rng, centre, end, 0.3, 5), fade))

        # A few leftover crackles that die away.
        fade = 1.0 - seconds / self._life
        if rng.random() < fade:
            for _ in range(int(rng.integers(1, 3))):
                origin = centre + rng.normal(0.0, 1.0, 2) * (size * 0.4, size * 0.5)
                end = _pointing(rng, origin, size * rng.uniform(0.15, 0.4), rng.uniform(0, 2 * np.pi))
                bolts.append((_bolt(rng, origin, end, 0.4, 3), 0.7 * fade))
        return bolts

    def _spark_position(self, seconds: np.ndarray) -> np.ndarray:
        travel = (1.0 - np.exp(-SPARK_DRAG * seconds)) / SPARK_DRAG
        fall = 0.5 * self._size * 4.0 * seconds**2
        position = self._spark_origin + self._spark_velocity * travel[:, None]
        position[:, 1] += fall
        return position

    def _sparks(self, seconds: float) -> list[tuple[np.ndarray, np.ndarray, float]]:
        if seconds <= 0.0:
            return []
        live = seconds < self._spark_life
        if not live.any():
            return []
        now = np.full(SPARKS, seconds)
        heads = self._spark_position(now)
        tails = self._spark_position(np.maximum(now - SPARK_TRAIL, 0.0))
        fades = 1.0 - seconds / self._spark_life
        return [(tails[i], heads[i], float(fades[i])) for i in np.nonzero(live)[0]]

    def _render(self, frame, bolts, sparks) -> None:
        height, width = frame.shape[:2]
        small = np.zeros((height // GLOW_DIVISOR, width // GLOW_DIVISOR), dtype=np.uint8)
        glow_width = max(round(3 * self._scale), 2)
        for points, strength in bolts:
            outline = (points / GLOW_DIVISOR).astype(np.int32)
            cv2.polylines(small, [outline], False, int(255 * strength), glow_width, cv2.LINE_AA)
        for tail, head, fade in sparks:
            cv2.line(
                small,
                tuple((tail / GLOW_DIVISOR).astype(int)),
                tuple((head / GLOW_DIVISOR).astype(int)),
                int(200 * fade),
                1,
                cv2.LINE_AA,
            )

        light = cv2.max(
            cv2.GaussianBlur(small, (0, 0), 1.5),
            cv2.convertScaleAbs(cv2.GaussianBlur(small, (0, 0), 5.0), alpha=1.6),
        )
        glow = cv2.resize(_glow(light, GLOW_BGR), (width, height), interpolation=cv2.INTER_LINEAR)
        cv2.add(frame, glow, dst=frame)

        # White-hot cores, added on top so they can never darken the picture.
        cores = np.zeros_like(small, shape=(height, width))
        core_width = max(round(1.5 * self._scale), 1)
        for points, strength in bolts:
            cv2.polylines(
                cores, [points.astype(np.int32)], False, int(255 * strength), core_width, cv2.LINE_AA
            )
        for tail, head, fade in sparks:
            cv2.line(
                cores,
                tuple(tail.astype(int)),
                tuple(head.astype(int)),
                int(255 * fade),
                core_width,
                cv2.LINE_AA,
            )
        left, top, box_width, box_height = cv2.boundingRect(cores)
        if box_width and box_height:
            area = (slice(top, top + box_height), slice(left, left + box_width))
            frame[area] = cv2.add(frame[area], _glow(cores[area], CORE_BGR))
