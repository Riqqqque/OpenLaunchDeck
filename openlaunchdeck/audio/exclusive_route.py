"""Voice route that Discord's screen-share audio can't pick up.

Discord (and other apps) capture "everything except me" for screen-share audio with
Windows application loopback. That capture only sees streams that go through the
shared Windows mixer, so the shared-mode microphone passthrough to a virtual cable
gets sent a second time inside the stream, which viewers hear as an echo.

This route opens the voice output (the virtual cable) in WASAPI exclusive mode, which
bypasses the shared mixer, and mixes the microphone and voice-routed soundboard clips
itself. Anything that can't run in exclusive mode falls back to the shared MicBridge.
"""

from __future__ import annotations

import ctypes
import sys
import threading
import time
import uuid
from array import array
from collections.abc import Callable
from typing import Any

from ..actions.base import ActionResult
from .mic_bridge import MicBridgeState

# 20 ms periods leave headroom for a Python render thread without adding much delay.
PERIOD_SECONDS = 0.02
# Formats tried for the exclusive stream, most common first.
EXCLUSIVE_FORMATS = ((48000, 2), (44100, 2))
SAMPLE_BYTES = 2
# Keep at most this much microphone audio queued so delay can't build up.
MAX_MIC_QUEUE_SECONDS = 0.08
START_TIMEOUT_SECONDS = 4.0
STOP_TIMEOUT_SECONDS = 1.5


def mix_int16(chunks: list[tuple[bytes, float]], byte_count: int) -> bytes:
    """Mix 16-bit PCM chunks with per-chunk gain, clipping to the int16 range."""
    live = [(data, gain) for data, gain in chunks if data and gain > 0]
    if not live:
        return bytes(byte_count)
    if len(live) == 1 and live[0][1] == 1.0 and len(live[0][0]) == byte_count:
        return live[0][0]
    total = [0] * (byte_count // SAMPLE_BYTES)
    for data, gain in live:
        samples = array("h")
        samples.frombytes(data[: byte_count - byte_count % SAMPLE_BYTES])
        if gain == 1.0:
            total = [a + b for a, b in zip(total, samples)] + total[len(samples) :]
        else:
            total = [a + int(b * gain) for a, b in zip(total, samples)] + total[len(samples) :]
    clipped = array("h", [32767 if value > 32767 else -32768 if value < -32768 else value for value in total])
    return clipped.tobytes()


class ClipOutput:
    """Stands in for QAudioOutput so the engine can change a mixed clip's volume."""

    def __init__(self, clip: "MixerClip") -> None:
        self._clip = clip

    def setVolume(self, gain: float) -> None:  # noqa: N802 - matches QAudioOutput
        self._clip.gain = max(0.0, float(gain))


class MixerClip:
    """A soundboard clip played inside the exclusive voice route."""

    def __init__(self, gain: float, loop: bool, on_finished: Callable[[], None] | None) -> None:
        self.gain = max(0.0, float(gain))
        self.loop = loop
        self.on_finished = on_finished
        self.output = ClipOutput(self)
        self.decoder: Any = None
        self._chunks: list[bytes] = []
        self._chunk_index = 0
        self._offset = 0
        self._decoded = False
        self._stopped = False
        self._finished = False
        self._lock = threading.Lock()

    def append(self, data: bytes) -> None:
        if data:
            with self._lock:
                self._chunks.append(bytes(data))

    def mark_decoded(self) -> None:
        with self._lock:
            self._decoded = True

    def stop(self) -> None:
        with self._lock:
            self._stopped = True
        decoder = self.decoder
        self.decoder = None
        if decoder is not None:
            try:
                decoder.stop()
            except Exception:
                pass

    @property
    def done(self) -> bool:
        with self._lock:
            return self._stopped or self._finished

    def read(self, byte_count: int) -> bytes:
        """Return up to byte_count bytes; shorter only while waiting for the decoder."""
        out = bytearray()
        finished = False
        with self._lock:
            if self._stopped or self._finished:
                return b""
            while len(out) < byte_count:
                if self._chunk_index >= len(self._chunks):
                    if not self._decoded:
                        break
                    if self.loop and self._chunks:
                        self._chunk_index, self._offset = 0, 0
                        continue
                    self._finished = finished = True
                    break
                chunk = self._chunks[self._chunk_index]
                take = chunk[self._offset : self._offset + byte_count - len(out)]
                out += take
                self._offset += len(take)
                if self._offset >= len(chunk):
                    self._chunk_index += 1
                    self._offset = 0
        if finished and self.on_finished is not None:
            try:
                self.on_finished()
            except Exception:
                pass
        return bytes(out)


class ExclusiveVoiceRoute:
    """Microphone plus voice-routed clips, written to the voice output in exclusive mode."""

    def __init__(self, logger=None, backend=None) -> None:
        self.logger = logger
        self.backend = backend or WasapiBackend()
        self.state = MicBridgeState()
        self.sample_rate = 0
        self.channels = 0
        self.underruns = 0
        self._volume = 1.0
        self._clips: list[MixerClip] = []
        self._clips_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._output_id = ""

    @property
    def running(self) -> bool:
        return self._running

    @property
    def output_id(self) -> str:
        return self._output_id if self._running else ""

    def start(
        self,
        input_device_id: str,
        output_device_id: str,
        volume: int = 100,
        input_name: str = "Microphone",
        output_name: str = "Voice route",
    ) -> ActionResult:
        self.stop()
        if not output_device_id:
            return ActionResult.fail("Choose a voice route output before routing the microphone.")
        self._volume = max(0, min(100, int(volume))) / 100.0
        self._stop_event.clear()
        ready = threading.Event()
        outcome: dict[str, Any] = {}
        self._thread = threading.Thread(
            target=self._run,
            args=(input_device_id, output_device_id, ready, outcome),
            name="openlaunchdeck-voice-route",
            daemon=True,
        )
        self._thread.start()
        if not ready.wait(START_TIMEOUT_SECONDS):
            self.stop()
            return ActionResult.fail("The exclusive voice route didn't start in time.")
        error = outcome.get("error")
        if error:
            self._thread.join(timeout=STOP_TIMEOUT_SECONDS)
            self._thread = None
            return ActionResult.fail(f"Exclusive voice route unavailable: {error}")
        self._output_id = output_device_id
        self.state = MicBridgeState(
            running=True,
            input_id=input_device_id,
            input_name=input_name,
            output_id=output_device_id,
            output_name=output_name,
            message=f"Microphone route is on: {input_name} -> {output_name} (hidden from screen-share audio).",
        )
        if self.logger:
            self.logger.info(
                "Exclusive voice route started: %s -> %s at %s Hz.", input_name, output_name, self.sample_rate
            )
        return ActionResult.ok(self.state.message)

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=STOP_TIMEOUT_SECONDS)
        self._thread = None
        self._running = False
        self._output_id = ""
        self._finish_all_clips()
        self.state = MicBridgeState()

    def set_volume(self, volume: int) -> None:
        self._volume = max(0, min(100, int(volume))) / 100.0

    def refresh_state(self) -> MicBridgeState:
        if self.state.running and not self._running:
            self.state = MicBridgeState(
                input_id=self.state.input_id,
                input_name=self.state.input_name,
                output_id=self.state.output_id,
                output_name=self.state.output_name,
                message="Microphone route stopped unexpectedly.",
            )
        return self.state

    def add_clip(self, gain: float, loop: bool, on_finished: Callable[[], None] | None) -> MixerClip:
        clip = MixerClip(gain, loop, on_finished)
        with self._clips_lock:
            self._clips.append(clip)
        return clip

    def _finish_all_clips(self) -> None:
        with self._clips_lock:
            clips, self._clips = self._clips, []
        for clip in clips:
            if not clip.done:
                clip.stop()
                if clip.on_finished is not None:
                    try:
                        clip.on_finished()
                    except Exception:
                        pass

    def _run(self, input_id: str, output_id: str, ready: threading.Event, outcome: dict) -> None:
        render = capture = None
        try:
            self.backend.begin_thread()
            render = self.backend.open_exclusive_render(output_id, EXCLUSIVE_FORMATS, PERIOD_SECONDS)
            self.sample_rate, self.channels = render.sample_rate, render.channels
            capture = self.backend.open_shared_capture(input_id, render.sample_rate, render.channels)
            render.start()
            capture.start()
        except Exception as exc:
            outcome["error"] = str(exc) or exc.__class__.__name__
            for stream in (capture, render):
                if stream is not None:
                    stream.close()
            self.backend.end_thread()
            ready.set()
            return
        self._running = True
        ready.set()
        block = render.channels * SAMPLE_BYTES
        period_bytes = render.frames_per_period * block
        max_mic_bytes = int(render.sample_rate * MAX_MIC_QUEUE_SECONDS) * block
        mic_queue = bytearray()
        period = render.frames_per_period / render.sample_rate
        last_write: float | None = None
        try:
            while not self._stop_event.is_set():
                if not render.wait(0.5):
                    self.underruns += 1
                    continue
                now = time.perf_counter()
                # A gap well past one period means the device ran dry: an audible glitch.
                if last_write is not None and now - last_write > period * 1.9:
                    self.underruns += 1
                last_write = now
                mic_queue += capture.read_available()
                if len(mic_queue) > max_mic_bytes:
                    # Both lengths are whole frames, so this keeps samples aligned.
                    del mic_queue[: len(mic_queue) - max_mic_bytes]
                mic = bytes(mic_queue[:period_bytes])
                del mic_queue[:period_bytes]
                chunks = [(mic, self._volume)]
                with self._clips_lock:
                    self._clips = [clip for clip in self._clips if not clip.done]
                    clips = list(self._clips)
                for clip in clips:
                    chunks.append((clip.read(period_bytes), clip.gain))
                render.write(mix_int16(chunks, period_bytes))
        except Exception as exc:
            if self.logger:
                self.logger.warning("Exclusive voice route stopped: %s", exc)
        finally:
            self._running = False
            for stream in (capture, render):
                try:
                    stream.close()
                except Exception:
                    pass
            self.backend.end_thread()
            if self.underruns and self.logger:
                self.logger.warning("Exclusive voice route had %s late audio periods.", self.underruns)


# Windows WASAPI backend


class _Guid(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort), ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)]

    @classmethod
    def parse(cls, value: str) -> "_Guid":
        raw = uuid.UUID(value)
        return cls(raw.time_low, raw.time_mid, raw.time_hi_version, (ctypes.c_ubyte * 8).from_buffer_copy(raw.bytes[8:]))


class _WaveFormat(ctypes.Structure):
    _fields_ = [
        ("wFormatTag", ctypes.c_ushort),
        ("nChannels", ctypes.c_ushort),
        ("nSamplesPerSec", ctypes.c_ulong),
        ("nAvgBytesPerSec", ctypes.c_ulong),
        ("nBlockAlign", ctypes.c_ushort),
        ("wBitsPerSample", ctypes.c_ushort),
        ("cbSize", ctypes.c_ushort),
    ]

    @classmethod
    def pcm16(cls, sample_rate: int, channels: int) -> "_WaveFormat":
        block = channels * SAMPLE_BYTES
        return cls(1, channels, sample_rate, sample_rate * block, block, 16, 0)


_CLSID_ENUMERATOR = "BCDE0395-E52F-467C-8E3D-C4579291692E"
_IID_ENUMERATOR = "A95664D2-9614-4F35-A746-DE8DB63617E6"
_IID_AUDIO_CLIENT = "1CB9AD4C-DBFA-4c32-B178-C2F568A703B2"
_IID_RENDER_CLIENT = "F294ACFC-3146-4483-A7BF-ADDCA7C260E2"
_IID_CAPTURE_CLIENT = "C8ADBD64-E71E-48a0-A4DE-185C395CD317"
_CLSCTX_ALL = 0x17
_SHARED, _EXCLUSIVE = 0, 1
_FLAG_EVENTCALLBACK = 0x00040000
_FLAG_AUTOCONVERTPCM = 0x80000000
_FLAG_SRC_DEFAULT_QUALITY = 0x08000000
_BUFFER_SILENT = 0x2
_E_BUFFER_SIZE_NOT_ALIGNED = -2004287463  # 0x88890019
_E_EXCLUSIVE_MODE_NOT_ALLOWED = -2004287474  # 0x8889000E
_E_DEVICE_IN_USE = -2004287478  # 0x8889000A
_E_UNSUPPORTED_FORMAT = -2004287480  # 0x88890008


def _kernel32():
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateEventW.restype = ctypes.c_void_p
    kernel32.CreateEventW.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
    kernel32.WaitForSingleObject.restype = ctypes.c_ulong
    kernel32.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    return kernel32


def _method(pointer, index: int, *argtypes):
    vtable = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    return ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argtypes)(vtable[index])


def _check(result: int, what: str) -> None:
    if result < 0:
        reason = {
            _E_EXCLUSIVE_MODE_NOT_ALLOWED: "Windows doesn't allow exclusive control of this device",
            _E_DEVICE_IN_USE: "another app is using this device in exclusive mode",
        }.get(result, f"error 0x{result & 0xFFFFFFFF:08X}")
        raise OSError(result, f"{what}: {reason}")


def _release(pointer) -> None:
    if pointer:
        try:
            ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(
                ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents[2]
            )(pointer)
        except Exception:
            pass


class _Endpoint:
    """An activated IAudioClient for one device."""

    def __init__(self, device_id: str, capture: bool) -> None:
        ole32 = ctypes.windll.ole32
        self.enumerator = ctypes.c_void_p()
        self.device = ctypes.c_void_p()
        self.client = ctypes.c_void_p()
        _check(
            ole32.CoCreateInstance(
                ctypes.byref(_Guid.parse(_CLSID_ENUMERATOR)), None, _CLSCTX_ALL,
                ctypes.byref(_Guid.parse(_IID_ENUMERATOR)), ctypes.byref(self.enumerator),
            ),
            "Couldn't open the Windows audio device list",
        )
        if device_id:
            result = _method(self.enumerator, 5, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p))(
                self.enumerator, device_id, ctypes.byref(self.device)
            )
        else:
            result = _method(self.enumerator, 4, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))(
                self.enumerator, 1 if capture else 0, 0, ctypes.byref(self.device)
            )
        _check(result, "Audio device not found")
        self.activate()

    def activate(self) -> None:
        _release(self.client)
        self.client = ctypes.c_void_p()
        _check(
            _method(self.device, 3, ctypes.POINTER(_Guid), ctypes.c_ulong, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))(
                self.device, ctypes.byref(_Guid.parse(_IID_AUDIO_CLIENT)), _CLSCTX_ALL, None, ctypes.byref(self.client)
            ),
            "Couldn't open the audio device",
        )

    def call(self, index: int, *args_and_types):
        types = args_and_types[0::2]
        values = args_and_types[1::2]
        return _method(self.client, index, *types)(self.client, *values)

    def service(self, iid: str) -> ctypes.c_void_p:
        pointer = ctypes.c_void_p()
        _check(
            _method(self.client, 14, ctypes.POINTER(_Guid), ctypes.POINTER(ctypes.c_void_p))(
                self.client, ctypes.byref(_Guid.parse(iid)), ctypes.byref(pointer)
            ),
            "Couldn't open the audio stream",
        )
        return pointer

    def close(self) -> None:
        for pointer in (self.client, self.device, self.enumerator):
            _release(pointer)
        self.client = self.device = self.enumerator = ctypes.c_void_p()


class _ExclusiveRender:
    def __init__(self, device_id: str, formats, period_seconds: float) -> None:
        self.endpoint = _Endpoint(device_id, capture=False)
        self.event = _kernel32().CreateEventW(None, 0, 0, None)
        self.render_client = ctypes.c_void_p()
        last_error: Exception | None = None
        for sample_rate, channels in formats:
            # Some drivers answer IsFormatSupported inconsistently for exclusive mode,
            # so try Initialize directly and move on only when the format is rejected.
            fmt = _WaveFormat.pcm16(sample_rate, channels)
            period = int(period_seconds * 10_000_000)
            result = self._initialize(fmt, period)
            if result == _E_BUFFER_SIZE_NOT_ALIGNED:
                frames = ctypes.c_uint32()
                self.endpoint.call(4, ctypes.POINTER(ctypes.c_uint32), ctypes.byref(frames))
                period = int(round(10_000_000 * frames.value / sample_rate))
                self.endpoint.activate()
                result = self._initialize(fmt, period)
            if result == _E_UNSUPPORTED_FORMAT:
                last_error = OSError(result, f"{sample_rate} Hz isn't supported in exclusive mode")
                self.endpoint.activate()
                continue
            _check(result, "Couldn't open the voice route in exclusive mode")
            self.sample_rate, self.channels = sample_rate, channels
            break
        else:
            raise last_error or OSError("No supported exclusive format")
        frames = ctypes.c_uint32()
        _check(self.endpoint.call(4, ctypes.POINTER(ctypes.c_uint32), ctypes.byref(frames)), "Couldn't read the buffer size")
        self.frames_per_period = frames.value
        _check(self.endpoint.call(13, ctypes.c_void_p, self.event), "Couldn't set the audio event")
        self.render_client = self.endpoint.service(_IID_RENDER_CLIENT)
        self._write_raw(None)  # Start from silence.

    def _initialize(self, fmt: _WaveFormat, period: int) -> int:
        return self.endpoint.call(
            3,
            ctypes.c_int, _EXCLUSIVE,
            ctypes.c_ulong, _FLAG_EVENTCALLBACK,
            ctypes.c_longlong, period,
            ctypes.c_longlong, period,
            ctypes.POINTER(_WaveFormat), ctypes.byref(fmt),
            ctypes.c_void_p, None,
        )

    def _write_raw(self, data: bytes | None) -> None:
        pointer = ctypes.c_void_p()
        _check(
            _method(self.render_client, 3, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p))(
                self.render_client, self.frames_per_period, ctypes.byref(pointer)
            ),
            "Couldn't write to the voice route",
        )
        if data:
            ctypes.memmove(pointer, data, min(len(data), self.frames_per_period * self.channels * SAMPLE_BYTES))
        _check(
            _method(self.render_client, 4, ctypes.c_uint32, ctypes.c_ulong)(
                self.render_client, self.frames_per_period, 0 if data else _BUFFER_SILENT
            ),
            "Couldn't write to the voice route",
        )

    def start(self) -> None:
        _check(self.endpoint.call(10), "Couldn't start the voice route")

    def wait(self, timeout: float) -> bool:
        return _kernel32().WaitForSingleObject(self.event, int(timeout * 1000)) == 0

    def write(self, data: bytes) -> None:
        self._write_raw(data)

    def close(self) -> None:
        try:
            self.endpoint.call(11)
        except Exception:
            pass
        _release(self.render_client)
        self.render_client = ctypes.c_void_p()
        self.endpoint.close()
        if self.event:
            _kernel32().CloseHandle(self.event)
            self.event = None


class _SharedCapture:
    def __init__(self, device_id: str, sample_rate: int, channels: int) -> None:
        self.endpoint = _Endpoint(device_id, capture=True)
        self.block = channels * SAMPLE_BYTES
        fmt = _WaveFormat.pcm16(sample_rate, channels)
        _check(
            self.endpoint.call(
                3,
                ctypes.c_int, _SHARED,
                ctypes.c_ulong, _FLAG_AUTOCONVERTPCM | _FLAG_SRC_DEFAULT_QUALITY,
                ctypes.c_longlong, 2_000_000,
                ctypes.c_longlong, 0,
                ctypes.POINTER(_WaveFormat), ctypes.byref(fmt),
                ctypes.c_void_p, None,
            ),
            "Couldn't open the microphone",
        )
        self.capture_client = self.endpoint.service(_IID_CAPTURE_CLIENT)

    def start(self) -> None:
        _check(self.endpoint.call(10), "Couldn't start the microphone")

    def read_available(self) -> bytes:
        out = bytearray()
        packet = ctypes.c_uint32()
        get_next = _method(self.capture_client, 5, ctypes.POINTER(ctypes.c_uint32))
        get_buffer = _method(
            self.capture_client, 3,
            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_ulong),
            ctypes.c_void_p, ctypes.c_void_p,
        )
        release = _method(self.capture_client, 4, ctypes.c_uint32)
        while True:
            _check(get_next(self.capture_client, ctypes.byref(packet)), "Couldn't read the microphone")
            if packet.value == 0:
                return bytes(out)
            data = ctypes.c_void_p()
            frames = ctypes.c_uint32()
            flags = ctypes.c_ulong()
            _check(get_buffer(self.capture_client, ctypes.byref(data), ctypes.byref(frames), ctypes.byref(flags), None, None), "Couldn't read the microphone")
            size = frames.value * self.block
            out += bytes(size) if flags.value & _BUFFER_SILENT or not data.value else ctypes.string_at(data, size)
            release(self.capture_client, frames.value)

    def close(self) -> None:
        try:
            self.endpoint.call(11)
        except Exception:
            pass
        _release(self.capture_client)
        self.capture_client = ctypes.c_void_p()
        self.endpoint.close()


class WasapiBackend:
    """Real Windows audio. Every call happens on the route's own thread."""

    available = sys.platform == "win32"

    def begin_thread(self) -> None:
        if not self.available:
            raise OSError("Exclusive audio is only available on Windows")
        ctypes.windll.ole32.CoInitializeEx(None, 0)
        try:
            task = ctypes.c_ulong()
            ctypes.windll.avrt.AvSetMmThreadCharacteristicsW("Pro Audio", ctypes.byref(task))
        except (AttributeError, OSError):
            pass

    def end_thread(self) -> None:
        if self.available:
            ctypes.windll.ole32.CoUninitialize()

    def open_exclusive_render(self, device_id: str, formats, period_seconds: float):
        return _ExclusiveRender(device_id, formats, period_seconds)

    def open_shared_capture(self, device_id: str, sample_rate: int, channels: int):
        return _SharedCapture(device_id, sample_rate, channels)


def start_clip_decoder(clip: MixerClip, file_path: str, sample_rate: int, channels: int, on_error: Callable[[], None]) -> None:
    """Decode a clip to the route's PCM format with Qt, feeding the clip as data arrives.

    Runs on the Qt main thread, like the rest of soundboard playback.
    """
    from PySide6.QtCore import QUrl
    from PySide6.QtMultimedia import QAudioDecoder, QAudioFormat

    decoder = QAudioDecoder()
    audio_format = QAudioFormat()
    audio_format.setSampleRate(sample_rate)
    audio_format.setChannelCount(channels)
    audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
    decoder.setAudioFormat(audio_format)
    decoder.setSource(QUrl.fromLocalFile(file_path))

    def buffer_ready() -> None:
        while decoder.bufferAvailable():
            buffer = decoder.read()
            clip.append(bytes(buffer.constData()))

    def finished() -> None:
        clip.mark_decoded()
        clip.decoder = None

    def failed(*_args) -> None:
        clip.stop()
        clip.decoder = None
        on_error()

    decoder.bufferReady.connect(buffer_ready)
    decoder.finished.connect(finished)
    decoder.error.connect(failed)
    clip.decoder = decoder
    decoder.start()
