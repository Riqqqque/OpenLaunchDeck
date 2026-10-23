from __future__ import annotations

import colorsys
import itertools
import math
import random
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from .model import FRAME_SIZE, GRID_SIZE, OFF

Frame = list[str]


@dataclass(frozen=True, slots=True)
class BuiltinAnimation:
    id: str
    name: str
    description: str
    fps: int
    _factory: Callable[[int], Iterator[Frame]]
    author: str = "OpenLaunchDeck"
    builtin: bool = True

    def iter_frames(self, seed: int = 0) -> Iterator[Frame]:
        return self._factory(seed)


def _clamp(value: float) -> float:
    return 0.0 if value < 0.0 else 1.0 if value > 1.0 else value


def rgb(red: float, green: float, blue: float) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        round(_clamp(red) * 255), round(_clamp(green) * 255), round(_clamp(blue) * 255)
    )


def hsv(hue: float, saturation: float = 1.0, value: float = 1.0) -> str:
    return rgb(*colorsys.hsv_to_rgb(hue % 1.0, _clamp(saturation), _clamp(value)))


def _hex_to_rgb(color: str) -> tuple[float, float, float]:
    return tuple(int(color[offset : offset + 2], 16) / 255 for offset in (1, 3, 5))  # type: ignore[return-value]


def blend(first: str, second: str, amount: float) -> str:
    amount = _clamp(amount)
    a, b = _hex_to_rgb(first), _hex_to_rgb(second)
    return rgb(*(x + (y - x) * amount for x, y in zip(a, b)))


def dim(color: str, amount: float) -> str:
    return blend(OFF, color, amount)


def gradient(stops: list[str], position: float) -> str:
    position = _clamp(position) * (len(stops) - 1)
    index = min(int(position), len(stops) - 2)
    return blend(stops[index], stops[index + 1], position - index)


def _cells() -> Iterator[tuple[int, int, int]]:
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            yield row * GRID_SIZE + col, row, col


def _timed(fps: int, render: Callable[[float, int], Frame]) -> Callable[[int], Iterator[Frame]]:
    # Stateless animations: each frame depends only on time (and the seed).
    def factory(seed: int) -> Iterator[Frame]:
        for index in itertools.count():
            yield render(index / fps, seed)

    return factory


def _rainbow_wave(t: float, _seed: int) -> Frame:
    return [hsv((row + col) / 14 + t * 0.35) for _index, row, col in _cells()]


AURORA = ["#06291f", "#13c98c", "#2fe0c3", "#7c5cff", "#d16bff"]


def _aurora(t: float, _seed: int) -> Frame:
    frame = []
    for _index, row, col in _cells():
        curtain = 0.5 + 0.5 * math.sin(col * 0.75 + t * 1.2 + math.sin(t * 0.4 + col * 0.3) * 1.5)
        fall = 1.0 - row / 11
        shimmer = 0.75 + 0.25 * math.sin(t * 3.1 + row * 0.9 + col * 0.4)
        level = _clamp(curtain * fall * shimmer)
        frame.append(dim(gradient(AURORA[1:], _clamp(row / 7 * 0.7 + curtain * 0.3)), level ** 0.8))
    return frame


def _ripple(t: float, _seed: int) -> Frame:
    frame = []
    for _index, row, col in _cells():
        distance = math.hypot(row - 3.5, col - 3.5)
        wave = 0.5 + 0.5 * math.cos(distance * 1.7 - t * 5.0)
        frame.append(hsv(t * 0.08 + distance * 0.06, 0.85, wave ** 3))
    return frame


def _plasma(t: float, _seed: int) -> Frame:
    frame = []
    for _index, row, col in _cells():
        value = (
            math.sin(col * 0.8 + t)
            + math.sin(row * 0.7 - t * 1.1)
            + math.sin((col + row) * 0.5 + t * 0.7)
            + math.sin(math.hypot(col - 3.5, row - 3.5) * 0.9 - t * 1.3)
        )
        frame.append(hsv(value / 8 + t * 0.05, 0.9, 0.55 + 0.45 * math.sin(value)))
    return frame


def _scanner(t: float, _seed: int) -> Frame:
    sweep = (t * 1.1) % 2.0
    position = (sweep if sweep <= 1.0 else 2.0 - sweep) * 7
    frame = []
    for _index, row, col in _cells():
        beam = max(0.0, 1.0 - abs(col - position) * 0.42) ** 2
        band = 0.25 + 0.75 * (1.0 - abs(row - 3.5) / 4.0)
        frame.append(dim("#ff1f45", beam * band))
    return frame


def _spiral(t: float, _seed: int) -> Frame:
    frame = []
    for _index, row, col in _cells():
        angle = math.atan2(row - 3.5, col - 3.5)
        distance = math.hypot(row - 3.5, col - 3.5)
        arm = 0.5 + 0.5 * math.sin(angle * 2 + distance * 0.95 - t * 4.0)
        frame.append(hsv(angle / (2 * math.pi) + t * 0.12, 0.9, arm ** 2))
    return frame


HEART = [
    ".XX..XX.",
    "XXXXXXXX",
    "XXXXXXXX",
    "XXXXXXXX",
    ".XXXXXX.",
    "..XXXX..",
    "...XX...",
    "........",
]


def _heartbeat(t: float, _seed: int) -> Frame:
    phase = t % 1.2
    beat = max(math.exp(-phase * 9), 0.75 * math.exp(-max(0.0, phase - 0.28) * 9) if phase >= 0.28 else 0.0)
    level = 0.18 + 0.82 * beat
    frame = []
    for _index, row, col in _cells():
        if HEART[row][col] == "X":
            frame.append(dim(blend("#ff2e6e", "#ff8fb5", (7 - row) / 14), level))
        else:
            frame.append(dim("#3a0a1c", beat * 0.6))
    return frame


NEBULA = ["#ff5fa2", "#8b5cf6", "#7af5d8", "#8b5cf6", "#ff5fa2"]


def _nebula(t: float, _seed: int) -> Frame:
    breath = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2 * math.pi / 4.0))
    return [dim(gradient(NEBULA, ((row + col) / 14 + t * 0.08) % 1.0), breath) for _index, row, col in _cells()]


def _twinkle(seed: int) -> Iterator[Frame]:
    rng = random.Random(seed)
    tints = ["#fff6d8", "#ffd27a", "#bfe3ff", "#ffffff"]
    stars = [(rng.random(), 1.5 + rng.random() * 3.0, rng.choice(tints)) for _ in range(FRAME_SIZE)]
    for index in itertools.count():
        t = index / 15
        yield [
            dim(tint, max(0.0, math.sin(2 * math.pi * (t / period + phase))) ** 6)
            for phase, period, tint in stars
        ]


def _falling(seed: int, head: str, trail: str, trail_length: int, speeds: tuple[float, float]) -> Iterator[Frame]:
    rng = random.Random(seed)
    columns = [[-rng.random() * 10, speeds[0] + rng.random() * (speeds[1] - speeds[0])] for _ in range(GRID_SIZE)]
    while True:
        frame = [OFF] * FRAME_SIZE
        for col, (position, _speed) in enumerate(columns):
            for step in range(trail_length + 1):
                row = math.floor(position) - step
                if 0 <= row < GRID_SIZE:
                    color = head if step == 0 else dim(trail, (1.0 - step / (trail_length + 1)) ** 1.5)
                    frame[row * GRID_SIZE + col] = color
        yield frame
        for drop in columns:
            drop[0] += drop[1]
            if drop[0] - trail_length > GRID_SIZE:
                drop[0] = -rng.random() * 6
                drop[1] = speeds[0] + rng.random() * (speeds[1] - speeds[0])


def _rain(seed: int) -> Iterator[Frame]:
    return _falling(seed, "#d6f0ff", "#2f7bff", 3, (0.35, 0.8))


def _matrix(seed: int) -> Iterator[Frame]:
    return _falling(seed, "#d9ffe6", "#16d35a", 5, (0.2, 0.55))


FIRE = ["#000000", "#5a0800", "#c21d00", "#ff6a00", "#ffc23a", "#fff4c8"]


def _fire(seed: int) -> Iterator[Frame]:
    rng = random.Random(seed)
    heat = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE + 1)]
    while True:
        for col in range(GRID_SIZE):
            heat[GRID_SIZE][col] = 0.7 + rng.random() * 0.3
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                below = heat[row + 1]
                spread = (below[col] * 2 + below[max(0, col - 1)] + below[min(GRID_SIZE - 1, col + 1)]) / 4
                heat[row][col] = max(0.0, spread - 0.11 - rng.random() * 0.13)
        yield [gradient(FIRE, heat[row][col]) for _index, row, col in _cells()]


def _snake(seed: int) -> Iterator[Frame]:
    del seed
    path = _spiral_path()
    length = 12
    for index in itertools.count():
        frame = [OFF] * FRAME_SIZE
        for step in range(length):
            cell = path[(index - step) % len(path)]
            frame[cell] = dim(hsv(index / 90 + step / 30, 0.9), (1.0 - step / length) ** 1.3)
        yield frame


def _spiral_path() -> list[int]:
    top, bottom, left, right = 0, GRID_SIZE - 1, 0, GRID_SIZE - 1
    cells: list[int] = []
    while top <= bottom and left <= right:
        cells.extend(top * GRID_SIZE + col for col in range(left, right + 1))
        cells.extend(row * GRID_SIZE + right for row in range(top + 1, bottom + 1))
        if top < bottom:
            cells.extend(bottom * GRID_SIZE + col for col in range(right - 1, left - 1, -1))
        if left < right:
            cells.extend(row * GRID_SIZE + left for row in range(bottom - 1, top, -1))
        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1
    return cells + cells[-2:0:-1]


LIFE = ["#7af5d8", "#5ad1ff", "#8b5cf6", "#ff5fa2"]


def _life(seed: int) -> Iterator[Frame]:
    rng = random.Random(seed)

    def fresh() -> list[int]:
        return [1 if rng.random() < 0.36 else 0 for _ in range(FRAME_SIZE)]

    ages = fresh()
    history: list[tuple[bool, ...]] = []
    generation = 0
    while True:
        yield [OFF if age == 0 else LIFE[min(len(LIFE) - 1, (age - 1) // 3)] for age in ages]
        next_ages = []
        for index, row, col in _cells():
            neighbors = sum(
                1
                for d_row in (-1, 0, 1)
                for d_col in (-1, 0, 1)
                if (d_row or d_col) and ages[((row + d_row) % GRID_SIZE) * GRID_SIZE + (col + d_col) % GRID_SIZE]
            )
            alive = ages[index] > 0
            if alive and neighbors in (2, 3):
                next_ages.append(ages[index] + 1)
            elif not alive and neighbors == 3:
                next_ages.append(1)
            else:
                next_ages.append(0)
        generation += 1
        signature = tuple(age > 0 for age in next_ages)
        if signature in history or sum(signature) < 4 or generation > 160:
            next_ages, history, generation = fresh(), [], 0
        else:
            history = (history + [signature])[-8:]
        ages = next_ages


LAVA = ["#14031f", "#6b0f3a", "#e0323c", "#ff8a1f", "#ffd45c"]


def _lava_lamp(t: float, seed: int) -> Frame:
    rng = random.Random(seed)
    blobs = [(rng.random() * 6, 0.25 + rng.random() * 0.35, 0.3 + rng.random() * 0.4, 0.9 + rng.random() * 0.6) for _ in range(4)]
    centers = [
        (3.5 + 2.8 * math.sin(t * speed_x + phase), 3.5 + 3.2 * math.sin(t * speed_y + phase * 1.7), radius)
        for phase, speed_x, speed_y, radius in blobs
    ]
    frame = []
    for _index, row, col in _cells():
        field_value = sum(radius * radius / (0.6 + (col - x) ** 2 + (row - y) ** 2) for x, y, radius in centers)
        frame.append(gradient(LAVA, _clamp((field_value - 0.35) / 2.2)))
    return frame


BUILTIN_ANIMATIONS: tuple[BuiltinAnimation, ...] = (
    BuiltinAnimation("rainbow_wave", "Rainbow Wave", "A smooth diagonal rainbow that rolls across the grid.", 20, _timed(20, _rainbow_wave)),
    BuiltinAnimation("nebula", "Nebula Breathe", "Pink, violet, and mint drift and slowly breathe.", 15, _timed(15, _nebula)),
    BuiltinAnimation("aurora", "Aurora", "Green and violet curtains ripple down from the top row.", 15, _timed(15, _aurora)),
    BuiltinAnimation("ripple", "Ripple", "Color rings spread out from the center like a drop in water.", 20, _timed(20, _ripple)),
    BuiltinAnimation("plasma", "Plasma", "Classic flowing plasma with shifting colors.", 20, _timed(20, _plasma)),
    BuiltinAnimation("spiral", "Spiral", "Rainbow arms spin around the center.", 20, _timed(20, _spiral)),
    BuiltinAnimation("rain", "Rain", "Blue drops fall down every column at their own pace.", 15, _rain),
    BuiltinAnimation("matrix", "Digital Rain", "Green code streams fall with bright leading pads.", 12, _matrix),
    BuiltinAnimation("twinkle", "Starfield", "Pads twinkle like stars in warm and cool whites.", 15, _twinkle),
    BuiltinAnimation("fire", "Campfire", "Flickering flames rise from the bottom row.", 15, _fire),
    BuiltinAnimation("lava_lamp", "Lava Lamp", "Warm blobs slowly drift, merge, and split.", 15, _timed(15, _lava_lamp)),
    BuiltinAnimation("scanner", "Scanner", "A red beam sweeps side to side.", 24, _timed(24, _scanner)),
    BuiltinAnimation("snake", "Snake", "A rainbow snake winds through the grid in a spiral.", 12, _snake),
    BuiltinAnimation("heartbeat", "Heartbeat", "A pink heart pulses with a lub-dub rhythm.", 20, _timed(20, _heartbeat)),
    BuiltinAnimation("life", "Game of Life", "Conway's Game of Life, colored by how long each cell survives.", 8, _life),
)

BUILTIN_BY_ID = {animation.id: animation for animation in BUILTIN_ANIMATIONS}
