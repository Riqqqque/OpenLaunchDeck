from __future__ import annotations

import json
import math
import random
import struct
import wave
from pathlib import Path


RATE = 32_000
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "openlaunchdeck" / "resources" / "starter_sounds"


def tone(frequency: float, duration: float, volume: float = 0.55, decay: float = 2.5) -> list[float]:
    count = int(RATE * duration)
    return [
        math.sin(2 * math.pi * frequency * index / RATE) * volume * math.exp(-decay * index / count)
        for index in range(count)
    ]


def silence(duration: float) -> list[float]:
    return [0.0] * int(RATE * duration)


def mix(*tracks: list[float]) -> list[float]:
    length = max((len(track) for track in tracks), default=0)
    output = [0.0] * length
    for track in tracks:
        for index, sample in enumerate(track):
            output[index] += sample
    return output


def sequence(*tracks: list[float]) -> list[float]:
    output: list[float] = []
    for track in tracks:
        output.extend(track)
    return output


def sweep(start: float, end: float, duration: float, volume: float = 0.5, noise: float = 0.0) -> list[float]:
    rng = random.Random(8142)
    count = int(RATE * duration)
    phase = 0.0
    output = []
    for index in range(count):
        progress = index / max(1, count - 1)
        frequency = start + (end - start) * progress
        phase += 2 * math.pi * frequency / RATE
        envelope = math.sin(math.pi * progress) ** 1.3
        output.append((math.sin(phase) * volume + rng.uniform(-noise, noise)) * envelope)
    return output


def noise_hit(duration: float, volume: float = 0.65) -> list[float]:
    rng = random.Random(2087)
    count = int(RATE * duration)
    return [rng.uniform(-1.0, 1.0) * volume * math.exp(-8 * index / count) for index in range(count)]


def normalize(samples: list[float]) -> list[float]:
    peak = max((abs(sample) for sample in samples), default=1.0)
    scale = 0.88 / peak if peak > 0.88 else 1.0
    fade = min(180, len(samples) // 4)
    output = []
    for index, sample in enumerate(samples):
        envelope = 1.0
        if index < fade:
            envelope *= index / max(1, fade)
        if index >= len(samples) - fade:
            envelope *= (len(samples) - index - 1) / max(1, fade)
        output.append(sample * scale * max(0.0, envelope))
    return output


def write_wave(path: Path, samples: list[float]) -> None:
    values = normalize(samples)
    frames = b"".join(struct.pack("<h", max(-32768, min(32767, int(value * 32767)))) for value in values)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(frames)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sounds = [
        ("alert_chime", "Alert Chime", "Alerts", ("alert", "stream", "notification"), sequence(mix(tone(660, 0.18), tone(990, 0.18, 0.25)), silence(0.04), mix(tone(880, 0.3), tone(1320, 0.3, 0.22)))),
        ("notification_pop", "Notification Pop", "Alerts", ("notification", "pop", "short"), mix(tone(720, 0.18, 0.5, 5.5), sweep(500, 1150, 0.16, 0.25))),
        ("success", "Success", "Utility", ("success", "confirm", "positive"), sequence(tone(523.25, 0.12), tone(659.25, 0.12), tone(783.99, 0.28))),
        ("error", "Error", "Utility", ("error", "warning", "negative"), sequence(tone(330, 0.16), silence(0.035), tone(247, 0.3, 0.62))),
        ("censor_beep", "Censor Beep", "Reactions", ("censor", "beep", "reaction"), tone(1000, 0.7, 0.46, 0.15)),
        ("transition_whoosh", "Transition Whoosh", "Transitions", ("whoosh", "transition", "sweep"), sweep(110, 1800, 0.65, 0.28, 0.18)),
        ("dramatic_hit", "Dramatic Hit", "Reactions", ("impact", "dramatic", "reaction"), mix(noise_hit(0.55), tone(72, 0.75, 0.72, 4.8), tone(144, 0.4, 0.25, 6.0))),
        ("level_up", "Level Up", "Gaming", ("game", "level", "achievement"), sequence(tone(440, 0.1), tone(554.37, 0.1), tone(659.25, 0.1), tone(880, 0.35))),
        ("camera_shutter", "Camera Shutter", "Stream Tools", ("camera", "photo", "screenshot"), sequence(noise_hit(0.08, 0.45), silence(0.035), mix(noise_hit(0.12, 0.65), tone(130, 0.16, 0.25, 8.0)))),
        ("button_click", "Button Click", "Utility", ("click", "button", "interface"), mix(noise_hit(0.07, 0.34), tone(880, 0.08, 0.22, 8.0))),
    ]
    manifest = []
    for sound_id, name, category, tags, samples in sounds:
        filename = f"{sound_id}.wav"
        write_wave(OUTPUT / filename, samples)
        manifest.append(
            {
                "id": sound_id,
                "name": name,
                "file": filename,
                "category": category,
                "tags": list(tags),
                "description": f"Original {category.casefold()} sound included with OpenLaunchDeck.",
            }
        )
    (OUTPUT / "manifest.json").write_text(json.dumps({"sounds": manifest}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
