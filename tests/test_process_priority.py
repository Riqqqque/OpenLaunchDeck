from __future__ import annotations

from openlaunchdeck import app as app_module


class PriorityKernelDouble:
    def __init__(self, current_priority: int, set_result: int = 1) -> None:
        self.current_priority = current_priority
        self.set_result = set_result
        self.set_calls: list[tuple[int, int]] = []

    def GetCurrentProcess(self) -> int:
        return 100

    def GetPriorityClass(self, process: int) -> int:
        assert process == 100
        return self.current_priority

    def SetPriorityClass(self, process: int, priority: int) -> int:
        assert process == 100
        self.set_calls.append((process, priority))
        if self.set_result:
            self.current_priority = priority
        return self.set_result


def test_windows_process_priority_drops_realtime_to_normal(monkeypatch):
    monkeypatch.setattr(app_module.sys, "platform", "win32")
    kernel = PriorityKernelDouble(app_module.REALTIME_PRIORITY_CLASS)

    changed = app_module._set_windows_process_priority(kernel32=kernel)

    assert changed is True
    assert kernel.set_calls == [(100, app_module.NORMAL_PRIORITY_CLASS)]
    assert kernel.current_priority == app_module.NORMAL_PRIORITY_CLASS


def test_windows_process_priority_drops_above_normal_to_normal(monkeypatch):
    monkeypatch.setattr(app_module.sys, "platform", "win32")
    kernel = PriorityKernelDouble(app_module.ABOVE_NORMAL_PRIORITY_CLASS)

    changed = app_module._set_windows_process_priority(kernel32=kernel)

    assert changed is True
    assert kernel.set_calls == [(100, app_module.NORMAL_PRIORITY_CLASS)]
    assert kernel.current_priority == app_module.NORMAL_PRIORITY_CLASS


def test_windows_process_priority_leaves_normal_alone(monkeypatch):
    monkeypatch.setattr(app_module.sys, "platform", "win32")
    kernel = PriorityKernelDouble(app_module.NORMAL_PRIORITY_CLASS)

    changed = app_module._set_windows_process_priority(kernel32=kernel)

    assert changed is False
    assert kernel.set_calls == []


def test_windows_process_priority_is_noop_off_windows(monkeypatch):
    monkeypatch.setattr(app_module.sys, "platform", "linux")
    kernel = PriorityKernelDouble(app_module.REALTIME_PRIORITY_CLASS)

    changed = app_module._set_windows_process_priority(kernel32=kernel)

    assert changed is False
    assert kernel.set_calls == []
