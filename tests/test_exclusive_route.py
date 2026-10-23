import threading
import time
from array import array

from openlaunchdeck.audio.audio_engine import AudioEngine
from openlaunchdeck.audio.exclusive_route import ExclusiveVoiceRoute, MixerClip, mix_int16


def pcm(*samples):
    return array("h", samples).tobytes()


def samples(data):
    values = array("h")
    values.frombytes(data)
    return list(values)


def test_mix_applies_gain_sums_and_clips():
    mixed = mix_int16([(pcm(1000, -1000, 30000, 0), 1.0), (pcm(500, 500, 10000, 0), 0.5)], 8)

    assert samples(mixed) == [1250, -750, 32767, 0]
    assert mix_int16([(pcm(5, 6), 1.0)], 4) == pcm(5, 6)
    assert mix_int16([], 4) == bytes(4)
    assert samples(mix_int16([(pcm(7), 1.0)], 4)) == [7, 0], "short sources are padded with silence"


def test_clip_streams_loops_and_reports_the_end():
    ended = []
    clip = MixerClip(1.0, loop=False, on_finished=lambda: ended.append(True))
    clip.append(pcm(1, 2, 3))
    assert clip.read(4) == pcm(1, 2)
    assert clip.read(4) == pcm(3), "waits for the decoder instead of ending early"
    clip.append(pcm(4))
    clip.mark_decoded()
    assert clip.read(4) == pcm(4)
    assert ended == [True] and clip.done

    looping = MixerClip(0.5, loop=True, on_finished=None)
    looping.append(pcm(1, 2))
    looping.mark_decoded()
    assert looping.read(8) == pcm(1, 2, 1, 2)
    looping.output.setVolume(0.25)
    assert looping.gain == 0.25
    looping.stop()
    assert looping.read(4) == b""


class FakeRender:
    sample_rate = 48000
    channels = 2
    frames_per_period = 4

    def __init__(self):
        self.written = []
        self.closed = False

    def start(self):
        pass

    def wait(self, timeout):
        time.sleep(0.002)
        return True

    def write(self, data):
        self.written.append(data)

    def close(self):
        self.closed = True


class FakeCapture:
    def __init__(self):
        self.closed = False

    def start(self):
        pass

    def read_available(self):
        return pcm(100, 100, 100, 100, 100, 100, 100, 100)

    def close(self):
        self.closed = True


class FakeBackend:
    def __init__(self, fail=None):
        self.fail = fail
        self.render = FakeRender()
        self.capture = FakeCapture()
        self.threads = []

    def begin_thread(self):
        self.threads.append(threading.current_thread().name)

    def end_thread(self):
        pass

    def open_exclusive_render(self, device_id, formats, period):
        if self.fail:
            raise OSError(self.fail)
        return self.render

    def open_shared_capture(self, device_id, sample_rate, channels):
        return self.capture


def wait_for(condition, timeout=2.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.005)
    return False


def test_route_mixes_microphone_and_clips_on_its_own_thread():
    backend = FakeBackend()
    route = ExclusiveVoiceRoute(backend=backend)

    result = route.start("mic", "cable", volume=50, input_name="Mic", output_name="Cable")
    assert result.success and route.running and route.output_id == "cable"
    assert "hidden from screen-share audio" in route.state.message
    assert wait_for(lambda: backend.render.written)
    assert samples(backend.render.written[-1]) == [50] * 8, "microphone volume applies"

    clip = route.add_clip(1.0, loop=True, on_finished=None)
    clip.append(pcm(1000) * 8)
    clip.mark_decoded()
    assert wait_for(lambda: samples(backend.render.written[-1])[0] == 1050)

    route.stop()
    assert backend.threads == ["openlaunchdeck-voice-route"]
    assert backend.render.closed and backend.capture.closed
    assert not route.running and clip.done


def test_route_reports_failure_so_the_engine_can_fall_back():
    route = ExclusiveVoiceRoute(backend=FakeBackend(fail="exclusive mode is not allowed"))

    result = route.start("mic", "cable")

    assert not result.success
    assert "exclusive mode is not allowed" in result.message
    assert not route.running


def test_route_marks_itself_stopped_when_the_device_fails():
    backend = FakeBackend()
    route = ExclusiveVoiceRoute(backend=backend)
    route.start("mic", "cable")

    def broken_write(_data):
        raise OSError("device unplugged")

    backend.render.write = broken_write
    assert wait_for(lambda: not route.running)
    state = route.refresh_state()
    assert not state.running
    assert "stopped unexpectedly" in state.message
    route.stop()


class SharedBridgeDouble:
    def __init__(self):
        from openlaunchdeck.audio.mic_bridge import MicBridgeState

        self.state = MicBridgeState()
        self.started = 0
        self.stopped = 0

    def start(self, *_args):
        from openlaunchdeck.actions.base import ActionResult
        from openlaunchdeck.audio.mic_bridge import MicBridgeState

        self.started += 1
        self.state = MicBridgeState(running=True, message="Microphone route is on.")
        return ActionResult.ok("Microphone route is on.")

    def stop(self):
        self.stopped += 1

    def set_volume(self, _volume):
        pass


def test_engine_prefers_exclusive_route_and_falls_back_to_shared():
    engine = AudioEngine(
        voice_chat_output_device_id="cable",
        voice_route_microphone_device_id="mic",
        exclusive_route=ExclusiveVoiceRoute(backend=FakeBackend()),
    )
    engine.mic_bridge = SharedBridgeDouble()

    assert engine.set_voice_route_microphone_enabled(True).success
    assert engine.voice_route_hidden_from_screen_share
    assert engine.mic_bridge.started == 0
    assert engine.voice_route_microphone_state().running

    engine.set_voice_route_exclusive(False)
    assert not engine.voice_route_hidden_from_screen_share
    assert engine.mic_bridge.started == 1

    failing = AudioEngine(
        voice_chat_output_device_id="cable",
        exclusive_route=ExclusiveVoiceRoute(backend=FakeBackend(fail="device in use")),
    )
    failing.mic_bridge = SharedBridgeDouble()
    assert failing.set_voice_route_microphone_enabled(True).success
    assert failing.mic_bridge.started == 1, "falls back to the shared route"
    engine.shutdown()
    failing.shutdown()


def test_voice_routed_clips_use_the_mixer_only_while_the_exclusive_route_runs(tmp_path, monkeypatch):
    from openlaunchdeck.audio import audio_engine as engine_module
    from test_audio_engine import install_qt_test_double

    decoded = []
    monkeypatch.setattr(
        engine_module,
        "start_clip_decoder",
        lambda clip, path, rate, channels, on_error: (decoded.append((path, rate, channels)), clip.append(pcm(5) * 8), clip.mark_decoded()),
    )
    sound = tmp_path / "clip.wav"
    sound.write_bytes(b"RIFF")
    engine = AudioEngine(
        voice_chat_output_device_id="cable",
        monitor_voice_chat_routes=True,
        exclusive_route=ExclusiveVoiceRoute(backend=FakeBackend()),
    )
    install_qt_test_double(engine)
    engine.mic_bridge = SharedBridgeDouble()
    engine.set_voice_route_microphone_enabled(True)

    result = engine.play_button_sound("A1", {"file_path": str(sound), "route_to_voice_chat": True, "_page_id": "p"})

    assert result.success
    playing = engine.currently_playing()
    voice = [item for item in playing if item.routed_to_voice_chat]
    monitor = [item for item in playing if not item.routed_to_voice_chat]
    assert len(voice) == 1 and isinstance(voice[0].player, MixerClip)
    assert len(monitor) == 1 and not isinstance(monitor[0].player, MixerClip), "your own monitor copy is unchanged"
    assert decoded == [(str(sound), 48000, 2)]
    engine.set_global_volume(50)
    assert voice[0].player.gain == voice[0].audio_output._clip.gain < 1.0
    assert wait_for(lambda: voice[0].instance_id not in {item.instance_id for item in engine.currently_playing()})

    engine.set_voice_route_exclusive(False)
    engine.play_button_sound("A2", {"file_path": str(sound), "route_to_voice_chat": True, "_page_id": "p"})
    assert not any(isinstance(item.player, MixerClip) for item in engine.currently_playing() if item.button_id == "A2")
    engine.shutdown()
