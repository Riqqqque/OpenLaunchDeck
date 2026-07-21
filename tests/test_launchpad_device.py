from openlaunchdeck.devices.launchpad_mini_mk3 import (
    PROGRAMMER_MODE_SYSEX,
    LaunchpadMiniMk3,
    color_to_palette_value,
)


class FakeOutputPort:
    def __init__(self):
        self.messages = []
        self.closed = False

    def send(self, message):
        self.messages.append(message)


class FailingOutputPort:
    def send(self, message):
        raise OSError("port disappeared")


class FakeInputPort:
    def __init__(self, closed=False):
        self.closed = closed


class FakePadMessage:
    type = "note_on"
    note = 81
    velocity = 127
    channel = 0


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


def test_strict_programmer_mode_reports_output_failure():
    device = LaunchpadMiniMk3()
    device.output_port = FailingOutputPort()
    device.connected = True

    try:
        device.enter_programmer_mode(strict=True)
    except RuntimeError as exc:
        assert "programmer_mode" in str(exc)
    else:
        raise AssertionError("Strict Programmer Mode did not report the output failure.")
    assert device.connected is False


def test_connection_health_detects_closed_input_port_without_hardware():
    device = LaunchpadMiniMk3()
    device.connected = True
    device.input_port_name = "Launchpad Input"
    device.output_port_name = "Launchpad Output"
    device.input_port = FakeInputPort(closed=True)
    device.output_port = FakeOutputPort()

    healthy, message = device.connection_health(["Launchpad Input"], ["Launchpad Output"])

    assert not healthy
    assert "input port is closed" in message.lower()


def test_connection_health_detects_port_removed_from_windows():
    device = LaunchpadMiniMk3()
    device.connected = True
    device.input_port_name = "Launchpad Input"
    device.input_port = FakeInputPort()

    healthy, message = device.connection_health([], [])

    assert not healthy
    assert "disappeared" in message.lower()


def test_button_callback_failure_does_not_disconnect_midi_transport():
    device = LaunchpadMiniMk3()
    device.connected = True
    device.button_callback = lambda *_args: (_ for _ in ()).throw(RuntimeError("UI callback failed"))

    device._on_message(FakePadMessage())

    assert device.connected is True
    assert device.last_input_monotonic > 0


def test_closed_transport_ignores_late_input_callback():
    events = []
    device = LaunchpadMiniMk3(button_callback=lambda *args: events.append(args))

    device._on_message(FakePadMessage())

    assert events == []
    assert device.last_input_monotonic == 0


def test_debug_output_callback_failure_does_not_disconnect_midi_transport():
    device = LaunchpadMiniMk3()
    device.output_port = FakeOutputPort()
    device.connected = True
    device.midi_out_callback = lambda *_args: (_ for _ in ()).throw(RuntimeError("debug window closed"))

    sent = device.set_many_pad_colors({"A1": "green"})

    assert sent == 1
    assert device.connected is True


def test_disconnect_notification_is_emitted_once_per_failure():
    reasons = []
    device = LaunchpadMiniMk3(disconnect_callback=reasons.append)
    device.connected = True

    device.mark_disconnected("first failure")
    device.mark_disconnected("duplicate failure")

    assert reasons == ["first failure"]
