import time

from openlaunchdeck.services.dangerous_confirm import DangerousConfirmService


def test_dangerous_button_requires_second_press():
    service = DangerousConfirmService(arm_seconds=1)

    assert service.arm_or_confirm("A1") is False
    assert service.is_armed("A1") is True
    assert service.arm_or_confirm("A1") is True
    assert service.is_armed("A1") is False


def test_dangerous_arm_expires():
    service = DangerousConfirmService(arm_seconds=0.01)
    assert service.arm_or_confirm("A1") is False
    time.sleep(0.02)
    assert service.is_armed("A1") is False
