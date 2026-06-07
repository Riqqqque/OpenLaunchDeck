from openlaunchdeck.audio.mic_bridge import MicBridge


class AudioFormatTestDouble:
    pass


class DeviceTestDouble:
    def __init__(self, device_id, description):
        self._device_id = device_id
        self._description = description
        self._format = AudioFormatTestDouble()

    def id(self):
        return self._device_id.encode()

    def description(self):
        return self._description

    def preferredFormat(self):
        return self._format

    def isFormatSupported(self, _audio_format):
        return True


class AudioSourceTestDouble:
    stopped = False
    started = False

    def __init__(self, device, audio_format):
        self.device = device
        self.audio_format = audio_format

    def start(self):
        self.started = True
        return object()

    def stop(self):
        self.stopped = True


class AudioSinkTestDouble:
    last_instance = None

    def __init__(self, device, audio_format):
        self.device = device
        self.audio_format = audio_format
        self.started_with = None
        self.stopped = False
        self.volume = None
        AudioSinkTestDouble.last_instance = self

    def setVolume(self, volume):
        self.volume = volume

    def start(self, source_device):
        self.started_with = source_device

    def stop(self):
        self.stopped = True


class MediaDevicesTestDouble:
    inputs = []
    outputs = []

    @staticmethod
    def audioInputs():
        return list(MediaDevicesTestDouble.inputs)

    @staticmethod
    def audioOutputs():
        return list(MediaDevicesTestDouble.outputs)

    @staticmethod
    def defaultAudioInput():
        return MediaDevicesTestDouble.inputs[0] if MediaDevicesTestDouble.inputs else None


def install_qt_test_double(bridge):
    bridge.qt_available = True
    bridge._qt = (AudioSinkTestDouble, AudioSourceTestDouble, MediaDevicesTestDouble)


def test_mic_bridge_starts_selected_input_to_selected_output():
    bridge = MicBridge()
    install_qt_test_double(bridge)
    MediaDevicesTestDouble.inputs = [DeviceTestDouble("mic-1", "Streamer Mic")]
    MediaDevicesTestDouble.outputs = [DeviceTestDouble("route-1", "Voice Bridge Output")]

    result = bridge.start("mic-1", "route-1", volume=55)

    assert result.success is True
    assert bridge.state.running is True
    assert bridge.state.input_name == "Streamer Mic"
    assert bridge.state.output_name == "Voice Bridge Output"
    assert AudioSinkTestDouble.last_instance.volume == 0.55


def test_mic_bridge_uses_default_input_when_not_selected():
    bridge = MicBridge()
    install_qt_test_double(bridge)
    MediaDevicesTestDouble.inputs = [DeviceTestDouble("default-mic", "Default Mic")]
    MediaDevicesTestDouble.outputs = [DeviceTestDouble("route-1", "Voice Bridge Output")]

    result = bridge.start("", "route-1")

    assert result.success is True
    assert bridge.state.input_id == "default-mic"


def test_mic_bridge_fails_without_output_route():
    bridge = MicBridge()
    install_qt_test_double(bridge)
    MediaDevicesTestDouble.inputs = [DeviceTestDouble("mic-1", "Streamer Mic")]
    MediaDevicesTestDouble.outputs = []

    result = bridge.start("mic-1", "missing-output")

    assert result.success is False
    assert "output" in result.message.lower()
    assert bridge.state.running is False


def test_mic_bridge_updates_volume_and_stops():
    bridge = MicBridge()
    install_qt_test_double(bridge)
    MediaDevicesTestDouble.inputs = [DeviceTestDouble("mic-1", "Streamer Mic")]
    MediaDevicesTestDouble.outputs = [DeviceTestDouble("route-1", "Voice Bridge Output")]

    bridge.start("mic-1", "route-1", volume=10)
    sink = AudioSinkTestDouble.last_instance
    bridge.set_volume(80)
    bridge.stop()

    assert sink.volume == 0.8
    assert sink.stopped is True
    assert bridge.state.running is False
