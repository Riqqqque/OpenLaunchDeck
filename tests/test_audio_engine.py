from openlaunchdeck.actions.base import ActionResult
from openlaunchdeck.audio.audio_engine import AudioEngine
from openlaunchdeck.audio.mic_bridge import MicBridgeState


class SignalTestDouble:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class QUrlTestDouble:
    @staticmethod
    def fromLocalFile(path):
        return path


class AudioOutputTestDouble:
    def __init__(self, device=None):
        self.device = device
        self.volume = 0

    def setVolume(self, volume):
        self.volume = volume


class MediaDevicesTestDouble:
    devices = []

    @staticmethod
    def audioOutputs():
        return list(MediaDevicesTestDouble.devices)


class DeviceTestDouble:
    def __init__(self, device_id, description):
        self._device_id = device_id
        self._description = description

    def id(self):
        return self._device_id.encode()

    def description(self):
        return self._description


class MediaPlayerTestDouble:
    class MediaStatus:
        EndOfMedia = "end"

    class Loops:
        Infinite = -1

    def __init__(self):
        self.mediaStatusChanged = SignalTestDouble()
        self.errorOccurred = SignalTestDouble()
        self.audio_output = None
        self.source = ""
        self.loops = 1
        self.playing = False
        self.stopped = False

    def setAudioOutput(self, audio_output):
        self.audio_output = audio_output

    def setSource(self, source):
        self.source = source

    def setLoops(self, loops):
        self.loops = loops

    def play(self):
        self.playing = True

    def stop(self):
        self.stopped = True
        self.playing = False


class MicBridgeTestDouble:
    def __init__(self):
        self.started_with = []
        self.stopped = False
        self.volume = None
        self.state = MicBridgeState()

    def start(self, input_device_id, output_device_id, volume):
        self.started_with.append((input_device_id, output_device_id, volume))
        self.state = MicBridgeState(
            running=True,
            input_id=input_device_id,
            input_name="Mic",
            output_id=output_device_id,
            output_name="Route",
            message="Microphone route is on.",
        )
        return ActionResult.ok("Microphone route is on.")

    def stop(self):
        self.stopped = True
        self.state = MicBridgeState()

    def set_volume(self, volume):
        self.volume = volume


def install_qt_test_double(engine):
    MediaDevicesTestDouble.devices = []
    engine.qt_available = True
    engine._qt = (QUrlTestDouble, AudioOutputTestDouble, MediaDevicesTestDouble, MediaPlayerTestDouble)


def test_soundboard_gain_uses_quiet_curve_and_preserves_zero():
    from openlaunchdeck.audio.audio_engine import soundboard_gain

    assert abs(soundboard_gain(100, 100) - 1.0) < 0.000001
    assert abs(soundboard_gain(50, 100) - 0.25) < 0.000001
    assert abs(soundboard_gain(40, 50) - 0.04) < 0.000001
    assert abs(soundboard_gain(0, 100) - 0.0) < 0.000001


def test_audio_engine_reports_missing_file():
    engine = AudioEngine()
    result = engine.play_button_sound("A1", {"file_path": "missing-file.wav"})

    assert result.success is False
    assert "missing" in result.message.lower()


def test_audio_engine_rejects_unsupported_format(tmp_path):
    path = tmp_path / "sound.txt"
    path.write_text("not audio", encoding="utf-8")
    engine = AudioEngine()

    result = engine.play_button_sound("A1", {"file_path": str(path)})

    assert result.success is False
    assert "unsupported" in result.message.lower()


def test_audio_engine_plays_local_file_with_volume_and_loop(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine(global_volume=50)
    install_qt_test_double(engine)
    changed = []
    engine.state_changed_callback = lambda: changed.append(True)

    result = engine.play_button_sound(
        "A1",
        {
            "file_path": str(path),
            "volume": 40,
            "loop": True,
            "behavior_when_already_playing": "restart",
            "_page_id": "main",
        },
    )

    assert result.success is True
    instance = engine.currently_playing()[0]
    assert instance.button_id == "A1"
    assert instance.page_id == "main"
    assert abs(instance.audio_output.volume - 0.04) < 0.000001
    assert instance.player.loops == -1
    assert changed


def test_audio_engine_zero_button_volume_stays_silent(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine(global_volume=100)
    install_qt_test_double(engine)

    result = engine.play_button_sound("A1", {"file_path": str(path), "volume": 0})

    assert result.success is True
    assert abs(engine.currently_playing()[0].audio_output.volume - 0.0) < 0.000001


def test_global_volume_updates_existing_instances_with_same_curve(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine(global_volume=100)
    install_qt_test_double(engine)

    assert engine.play_button_sound("A1", {"file_path": str(path), "volume": 100}).success is True
    instance = engine.currently_playing()[0]
    assert abs(instance.audio_output.volume - 1.0) < 0.000001

    engine.set_global_volume(50)

    assert abs(instance.audio_output.volume - 0.25) < 0.000001


def test_audio_engine_already_playing_behaviors(tmp_path):
    path = tmp_path / "sound.mp3"
    path.write_bytes(b"minimal mp3 bytes")
    engine = AudioEngine()
    install_qt_test_double(engine)
    config = {"file_path": str(path), "behavior_when_already_playing": "restart"}

    assert engine.play_button_sound("A1", config).success is True
    first = engine.currently_playing()[0]
    assert engine.play_button_sound("A1", config).success is True
    assert first.player.stopped is True
    assert len(engine.currently_playing()) == 1

    overlap = dict(config, behavior_when_already_playing="overlap")
    assert engine.play_button_sound("A1", overlap).success is True
    assert len(engine.currently_playing()) == 2

    ignore = dict(config, behavior_when_already_playing="ignore")
    assert engine.play_button_sound("A1", ignore).success is True
    assert len(engine.currently_playing()) == 2

    toggle = dict(config, behavior_when_already_playing="toggle_stop")
    assert engine.play_button_sound("A1", toggle).success is True
    assert len(engine.currently_playing()) == 0


def test_audio_engine_stop_scopes(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine()
    install_qt_test_double(engine)

    engine.play_button_sound("A1", {"file_path": str(path), "_page_id": "main"})
    engine.play_button_sound("A2", {"file_path": str(path), "_page_id": "main"})
    engine.play_button_sound("B1", {"file_path": str(path), "_page_id": "other"})
    engine.stop_button("A1")
    assert {item.button_id for item in engine.currently_playing()} == {"A2", "B1"}
    engine.stop_page("main")
    assert {item.button_id for item in engine.currently_playing()} == {"B1"}
    engine.stop_all()
    assert not engine.currently_playing()


def test_voice_chat_route_requires_output_device(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine()
    install_qt_test_double(engine)

    result = engine.play_button_sound("A8", {"file_path": str(path), "route_to_voice_chat": True})

    assert result.success is False
    assert "voice route output" in result.message.lower()


def test_selected_default_output_must_be_available(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine(default_output_device_id="missing-output")
    install_qt_test_double(engine)
    MediaDevicesTestDouble.devices = [DeviceTestDouble("real-output", "Speakers")]

    result = engine.play_button_sound("A1", {"file_path": str(path)})

    assert result.success is False
    assert "selected soundboard output" in result.message.lower()
    assert not engine.currently_playing()


def test_system_default_output_can_be_used_without_saved_device(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine(default_output_device_id="")
    install_qt_test_double(engine)

    result = engine.play_button_sound("A1", {"file_path": str(path)})

    assert result.success is True
    assert engine.currently_playing()[0].audio_output.device is None


def test_voice_chat_route_plays_to_voice_output_and_monitor(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine(voice_chat_output_device_id="voice-cable", monitor_voice_chat_routes=True)
    install_qt_test_double(engine)
    MediaDevicesTestDouble.devices = [DeviceTestDouble("voice-cable", "Cable Input")]

    result = engine.play_button_sound("A8", {"file_path": str(path), "route_to_voice_chat": True, "volume": 25})

    assert result.success is True
    instances = engine.currently_playing()
    assert len(instances) == 2
    assert sum(1 for instance in instances if instance.routed_to_voice_chat) == 1
    assert any(instance.audio_output.device is None for instance in instances)
    assert any(getattr(instance.audio_output.device, "_device_id", "") == "voice-cable" for instance in instances)
    assert {round(instance.audio_output.volume, 6) for instance in instances} == {0.0625}


def test_voice_chat_route_can_disable_monitor(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine(voice_chat_output_device_id="voice-cable", monitor_voice_chat_routes=False)
    install_qt_test_double(engine)
    MediaDevicesTestDouble.devices = [DeviceTestDouble("voice-cable", "Cable Input")]

    result = engine.play_button_sound("A8", {"file_path": str(path), "route_to_voice_chat": True})

    assert result.success is True
    assert len(engine.currently_playing()) == 1
    assert engine.currently_playing()[0].routed_to_voice_chat is True


def test_voice_chat_route_cleans_up_when_monitor_output_is_missing(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"minimal wav bytes")
    engine = AudioEngine(
        default_output_device_id="missing-monitor",
        voice_chat_output_device_id="voice-cable",
        monitor_voice_chat_routes=True,
    )
    install_qt_test_double(engine)
    MediaDevicesTestDouble.devices = [DeviceTestDouble("voice-cable", "Cable Input")]

    result = engine.play_button_sound("A8", {"file_path": str(path), "route_to_voice_chat": True})

    assert result.success is False
    assert "selected soundboard output" in result.message.lower()
    assert not engine.currently_playing()


def test_audio_engine_microphone_route_starts_stops_and_restarts():
    engine = AudioEngine(
        voice_chat_output_device_id="voice-route",
        voice_route_microphone_enabled=False,
        voice_route_microphone_device_id="mic-1",
        voice_route_microphone_volume=65,
    )
    bridge = MicBridgeTestDouble()
    engine.mic_bridge = bridge

    result = engine.set_voice_route_microphone_enabled(True)
    engine.set_voice_route_microphone_volume(45)
    engine.set_voice_route_microphone_device("mic-2")
    engine.set_voice_chat_output_device("voice-route-2")
    off_result = engine.set_voice_route_microphone_enabled(False)

    assert result.success is True
    assert bridge.started_with[0] == ("mic-1", "voice-route", 65)
    assert ("mic-2", "voice-route", 45) in bridge.started_with
    assert bridge.started_with[-1] == ("mic-2", "voice-route-2", 45)
    assert bridge.volume == 45
    assert off_result.success is True
    assert bridge.stopped is True

