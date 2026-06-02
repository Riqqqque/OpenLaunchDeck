from openlaunchdeck.devices.launchpad_mini_mk3 import (
    PROGRAMMER_MODE_SYSEX,
    LaunchpadMiniMk3,
    color_to_palette_value,
)


class FakeOutputPort:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)


def test_color_to_palette_value_uses_named_colors():
    assert color_to_palette_value("red") == 5
    assert color_to_palette_value("cyan") == 37
    assert color_to_palette_value("not-a-color") == 0


def test_batch_lighting_sends_midi_messages():
    device = LaunchpadMiniMk3()
    port = FakeOutputPort()
    outgoing = []
    device.output_port = port
    device.connected = True
    device.midi_out_callback = lambda message, text: outgoing.append(text)

    sent = device.set_many_pad_colors({"A1": "red", "A2": "green"})

    assert sent == 2
    assert len(port.messages) == 2
    assert len(outgoing) == 2


def test_enter_programmer_mode_sends_documented_sysex_message():
    device = LaunchpadMiniMk3()
    port = FakeOutputPort()
    device.output_port = port

    device.enter_programmer_mode()

    assert len(port.messages) == 1
    assert port.messages[0].type == "sysex"
    assert list(port.messages[0].data) == PROGRAMMER_MODE_SYSEX
