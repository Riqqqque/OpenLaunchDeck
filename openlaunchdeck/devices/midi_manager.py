from __future__ import annotations

import re


class MidiManager:
    def __init__(self, logger=None) -> None:
        self.logger = logger

    @staticmethod
    def available_input_ports() -> list[str]:
        try:
            import mido
            return list(mido.get_input_names())
        except Exception:
            return []

    @staticmethod
    def available_output_ports() -> list[str]:
        try:
            import mido
            return list(mido.get_output_names())
        except Exception:
            return []

    @classmethod
    def detect_launchpad_ports(cls) -> tuple[str, str]:
        inputs = cls.available_input_ports()
        outputs = cls.available_output_ports()
        input_port = _find_launchpad_name(inputs)
        output_port = _find_launchpad_name(outputs)
        return input_port, output_port

    @classmethod
    def resolve_launchpad_ports(cls, input_port: str, output_port: str) -> tuple[str, str]:
        return (
            _resolve_launchpad_port(input_port, cls.available_input_ports()),
            _resolve_launchpad_port(output_port, cls.available_output_ports()),
        )


def _find_launchpad_name(ports: list[str]) -> str:
    matches = sorted(
        [(_launchpad_port_score(port), -index, port) for index, port in enumerate(ports)],
        reverse=True,
    )
    for score, _index, port in matches:
        if score > 0:
            return port
    return ""


def _resolve_launchpad_port(configured_port: str, available_ports: list[str]) -> str:
    preferred_port = _find_launchpad_name(available_ports)
    if not configured_port:
        return preferred_port
    if configured_port not in available_ports:
        return preferred_port or configured_port
    if (
        preferred_port
        and preferred_port != configured_port
        and _launchpad_port_score(configured_port) > 0
        and _launchpad_port_score(preferred_port) > _launchpad_port_score(configured_port)
    ):
        return preferred_port
    return configured_port


def _launchpad_port_score(port: str) -> int:
    lower = port.lower()
    compact = "".join(character for character in lower if character.isalnum())
    score = 0
    if "lpminimk3" in compact:
        score += 100
    if "launchpad" in lower:
        score += 90
    if "novation" in lower:
        score += 25
    if "mini" in lower or "mini" in compact:
        score += 15
    if "mk3" in lower or "mk3" in compact:
        score += 15
    if "midiin2" in compact or "midiout2" in compact:
        score += 45
    if re.search(r"(?:^|\s)lpminimk3\s+midi\s+1$", lower):
        score += 40
    if "daw" in lower:
        score -= 30
    return score
