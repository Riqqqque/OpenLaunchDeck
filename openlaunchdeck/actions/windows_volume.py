from __future__ import annotations

import ctypes
import sys
import uuid


CLSCTX_ALL = 0x17
ERENDER = 0
EMULTIMEDIA = 1
ECONSOLE = 0
RPC_E_CHANGED_MODE = -2147417850


class Guid(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_string(cls, value: str) -> "Guid":
        raw = uuid.UUID(value)
        data4 = (ctypes.c_ubyte * 8).from_buffer_copy(raw.bytes[8:])
        return cls(raw.time_low, raw.time_mid, raw.time_hi_version, data4)


CLSID_MMDEVICE_ENUMERATOR = Guid.from_string("BCDE0395-E52F-467C-8E3D-C4579291692E")
IID_IMMDEVICE_ENUMERATOR = Guid.from_string("A95664D2-9614-4F35-A746-DE8DB63617E6")
IID_IAUDIO_ENDPOINT_VOLUME = Guid.from_string("5CDF2C82-841E-4546-9722-0CF74078229A")


def _method(pointer: ctypes.c_void_p, index: int, restype, *argtypes):
    vtable = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vtable[index])


def _check(result: int, message: str) -> None:
    if result < 0:
        raise OSError(result, message)


def _release(pointer: ctypes.c_void_p | None) -> None:
    if pointer:
        try:
            _method(pointer, 2, ctypes.c_ulong)(pointer)
        except Exception:
            pass


class WindowsVolumeController:
    def __init__(self, role: int = EMULTIMEDIA) -> None:
        self.role = role

    def get_volume_percent(self) -> int:
        with self._endpoint_volume() as volume:
            value = ctypes.c_float()
            _check(_method(volume, 9, ctypes.c_long, ctypes.POINTER(ctypes.c_float))(volume, ctypes.byref(value)), "Could not read volume.")
            return max(0, min(100, round(float(value.value) * 100)))

    def set_volume_percent(self, percent: int) -> None:
        value = max(0, min(100, int(percent))) / 100.0
        with self._endpoint_volume() as volume:
            _check(_method(volume, 7, ctypes.c_long, ctypes.c_float, ctypes.c_void_p)(volume, ctypes.c_float(value), None), "Could not set volume.")

    def set_muted(self, muted: bool) -> None:
        with self._endpoint_volume() as volume:
            _check(_method(volume, 14, ctypes.c_long, ctypes.c_int, ctypes.c_void_p)(volume, int(bool(muted)), None), "Could not set mute.")

    def toggle_mute(self) -> bool:
        with self._endpoint_volume() as volume:
            muted = ctypes.c_int()
            _check(_method(volume, 15, ctypes.c_long, ctypes.POINTER(ctypes.c_int))(volume, ctypes.byref(muted)), "Could not read mute.")
            new_state = not bool(muted.value)
            _check(_method(volume, 14, ctypes.c_long, ctypes.c_int, ctypes.c_void_p)(volume, int(new_state), None), "Could not set mute.")
            return new_state

    def step_up(self) -> None:
        with self._endpoint_volume() as volume:
            _check(_method(volume, 17, ctypes.c_long, ctypes.c_void_p)(volume, None), "Could not raise volume.")

    def step_down(self) -> None:
        with self._endpoint_volume() as volume:
            _check(_method(volume, 18, ctypes.c_long, ctypes.c_void_p)(volume, None), "Could not lower volume.")

    def _endpoint_volume(self) -> "_EndpointVolumeHandle":
        return _EndpointVolumeHandle(self.role)


class _EndpointVolumeHandle:
    def __init__(self, role: int) -> None:
        self.role = role
        self.initialized_com = False
        self.enumerator = ctypes.c_void_p()
        self.device = ctypes.c_void_p()
        self.volume = ctypes.c_void_p()

    def __enter__(self) -> ctypes.c_void_p:
        ole32 = ctypes.windll.ole32
        init_result = ole32.CoInitialize(None)
        self.initialized_com = init_result >= 0
        if init_result < 0 and init_result != RPC_E_CHANGED_MODE:
            _check(init_result, "Could not initialize Windows audio control.")

        _check(
            ole32.CoCreateInstance(
                ctypes.byref(CLSID_MMDEVICE_ENUMERATOR),
                None,
                CLSCTX_ALL,
                ctypes.byref(IID_IMMDEVICE_ENUMERATOR),
                ctypes.byref(self.enumerator),
            ),
            "Could not open Windows audio endpoint enumerator.",
        )

        get_default_endpoint = _method(
            self.enumerator,
            4,
            ctypes.c_long,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        )
        result = get_default_endpoint(self.enumerator, ERENDER, self.role, ctypes.byref(self.device))
        if result < 0 and self.role != ECONSOLE:
            result = get_default_endpoint(self.enumerator, ERENDER, ECONSOLE, ctypes.byref(self.device))
        _check(result, "Could not open the default playback endpoint.")

        activate = _method(
            self.device,
            3,
            ctypes.c_long,
            ctypes.POINTER(Guid),
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        )
        _check(
            activate(
                self.device,
                ctypes.byref(IID_IAUDIO_ENDPOINT_VOLUME),
                CLSCTX_ALL,
                None,
                ctypes.byref(self.volume),
            ),
            "Could not open Windows endpoint volume control.",
        )
        return self.volume

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        _release(self.volume)
        _release(self.device)
        _release(self.enumerator)
        if self.initialized_com:
            ctypes.windll.ole32.CoUninitialize()


def create_volume_controller() -> WindowsVolumeController | None:
    if sys.platform != "win32":
        return None
    return WindowsVolumeController()
