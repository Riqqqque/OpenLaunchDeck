from openlaunchdeck.audio.audio_engine import AudioEngine


class FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class FakeQUrl:
    @staticmethod
    def fromLocalFile(path):
        return path


class FakeAudioOutput:
    def __init__(self, device=None):
        self.device = device
        self.volume = 0

    def setVolume(self, volume):
        self.volume = volume


class FakeMediaDevices:
    devices = []

    @staticmethod
    def audioOutputs():
        return list(FakeMediaDevices.devices)


class FakeDevice:
    def __init__(self, device_id, description):
        self._device_id = device_id
        self._description = description

    def id(self):
        return self._device_id.encode()

    def description(self):
        return self._description


class FakeMediaPlayer:
    class MediaStatus:
        EndOfMedia = "end"

    class Loops:
        Infinite = -1

    def __init__(self):
        self.mediaStatusChanged = FakeSignal()
        self.errorOccurred = FakeSignal()
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


def install_fake_qt(engine):
    FakeMediaDevices.devices = []
    engine.qt_available = True
    engine._qt = (FakeQUrl, FakeAudioOutput, FakeMediaDevices, FakeMediaPlayer)


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
    path.write_bytes(b"fake wav bytes")
    engine = AudioEngine(global_volume=50)
    install_fake_qt(engine)
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
    assert instance.audio_output.volume == 0.2
    assert instance.player.loops == -1
    assert changed


def test_audio_engine_already_playing_behaviors(tmp_path):
    path = tmp_path / "sound.mp3"
    path.write_bytes(b"fake mp3 bytes")
    engine = AudioEngine()
    install_fake_qt(engine)
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
    path.write_bytes(b"fake wav bytes")
    engine = AudioEngine()
    install_fake_qt(engine)

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
    path.write_bytes(b"fake wav bytes")
    engine = AudioEngine()
    install_fake_qt(engine)

    result = engine.play_button_sound("A8", {"file_path": str(path), "route_to_voice_chat": True})

    assert result.success is False
    assert "voice chat output" in result.message.lower()


def test_selected_default_output_must_be_available(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"fake wav bytes")
    engine = AudioEngine(default_output_device_id="missing-output")
    install_fake_qt(engine)
    FakeMediaDevices.devices = [FakeDevice("real-output", "Speakers")]

    result = engine.play_button_sound("A1", {"file_path": str(path)})

    assert result.success is False
    assert "selected soundboard output" in result.message.lower()
    assert not engine.currently_playing()


def test_system_default_output_can_be_used_without_saved_device(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"fake wav bytes")
    engine = AudioEngine(default_output_device_id="")
    install_fake_qt(engine)

    result = engine.play_button_sound("A1", {"file_path": str(path)})

    assert result.success is True
    assert engine.currently_playing()[0].audio_output.device is None


def test_voice_chat_route_plays_to_voice_output_and_monitor(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"fake wav bytes")
    engine = AudioEngine(voice_chat_output_device_id="voice-cable", monitor_voice_chat_routes=True)
    install_fake_qt(engine)
    FakeMediaDevices.devices = [FakeDevice("voice-cable", "Cable Input")]

    result = engine.play_button_sound("A8", {"file_path": str(path), "route_to_voice_chat": True, "volume": 25})

    assert result.success is True
    instances = engine.currently_playing()
    assert len(instances) == 2
    assert sum(1 for instance in instances if instance.routed_to_voice_chat) == 1
    assert any(instance.audio_output.device is None for instance in instances)
    assert any(getattr(instance.audio_output.device, "_device_id", "") == "voice-cable" for instance in instances)


def test_voice_chat_route_can_disable_monitor(tmp_path):
    path = tmp_path / "sound.wav"
    path.write_bytes(b"fake wav bytes")
    engine = AudioEngine(voice_chat_output_device_id="voice-cable", monitor_voice_chat_routes=False)
    install_fake_qt(engine)
    FakeMediaDevices.devices = [FakeDevice("voice-cable", "Cable Input")]

    result = engine.play_button_sound("A8", {"file_path": str(path), "route_to_voice_chat": True})

    assert result.success is True
    assert len(engine.currently_playing()) == 1
    assert engine.currently_playing()[0].routed_to_voice_chat is True
