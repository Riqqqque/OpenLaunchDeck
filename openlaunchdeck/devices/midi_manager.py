from __future__ import annotations


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


def _find_launchpad_name(ports: list[str]) -> str:
    for port in ports:
        lower = port.lower()
        if "launchpad" in lower and ("mk3" in lower or "mini" in lower):
            return port
    for port in ports:
        if "launchpad" in port.lower():
            return port
    return ""
