from __future__ import annotations

import base64
import ctypes
import sys
from ctypes import wintypes


PREFIX = "dpapi:"
CRYPTPROTECT_UI_FORBIDDEN = 0x1


class SecretStorageError(RuntimeError):
    pass


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("size", wintypes.DWORD),
        ("data", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def protect_secret(value: str) -> str:
    if not value:
        return ""
    if sys.platform != "win32":
        raise SecretStorageError("Secure credential storage is available on Windows only.")
    encrypted = _crypt_protect(value.encode("utf-8"))
    return PREFIX + base64.b64encode(encrypted).decode("ascii")


def unprotect_secret(value: str) -> str:
    if not value:
        return ""
    if not value.startswith(PREFIX) or sys.platform != "win32":
        return ""
    try:
        encrypted = base64.b64decode(value[len(PREFIX) :], validate=True)
        return _crypt_unprotect(encrypted).decode("utf-8")
    except (ValueError, UnicodeError, OSError):
        return ""


def _blob(value: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(value)
    pointer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
    return _DataBlob(len(value), pointer), buffer


def _crypt_protect(value: bytes) -> bytes:
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    source, source_buffer = _blob(value)
    destination = _DataBlob()
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        wintypes.LPCWSTR,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL
    if not crypt32.CryptProtectData(
        ctypes.byref(source),
        "OpenLaunchDeck Sound Library",
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(destination),
    ):
        raise SecretStorageError(f"Windows could not protect the credential ({ctypes.get_last_error()}).")
    try:
        return ctypes.string_at(destination.data, destination.size)
    finally:
        kernel32.LocalFree(ctypes.cast(destination.data, ctypes.c_void_p))
        del source_buffer


def _crypt_unprotect(value: bytes) -> bytes:
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    source, source_buffer = _blob(value)
    destination = _DataBlob()
    description = wintypes.LPWSTR()
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source),
        ctypes.byref(description),
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(destination),
    ):
        raise SecretStorageError(f"Windows could not read the protected credential ({ctypes.get_last_error()}).")
    try:
        return ctypes.string_at(destination.data, destination.size)
    finally:
        if description:
            kernel32.LocalFree(ctypes.cast(description, ctypes.c_void_p))
        kernel32.LocalFree(ctypes.cast(destination.data, ctypes.c_void_p))
        del source_buffer
