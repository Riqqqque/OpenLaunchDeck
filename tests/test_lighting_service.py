from openlaunchdeck.models.page import Page
from openlaunchdeck.services.dangerous_confirm import DangerousConfirmService
from openlaunchdeck.services.lighting_service import LightingService
import time


class FakeDevice:
    connected = True

    def __init__(self):
        self.batches = []
        self.single = []
        self.cleared = False

    def set_many_pad_colors(self, colors):
        self.batches.append(dict(colors))
        return len(colors)

    def set_pad_color(self, button_id, color):
        self.single.append((button_id, color))

    def clear_all_pads(self):
        self.cleared = True


class FakeAudio:
    def __init__(self, playing):
        self.playing = set(playing)

    def is_button_playing(self, button_id):
        return button_id in self.playing


def test_lighting_refresh_skips_redundant_state():
    device = FakeDevice()
    service = LightingService(device=device)
    page = Page.blank()

    service.refresh_page(page)
    service.refresh_page(page)

    assert len(device.batches) == 1
    assert len(device.batches[0]) == 64


def test_lighting_marks_sound_and_armed_states():
    device = FakeDevice()
    service = LightingService(device=device)
    page = Page.blank()
    page.get_button("A1").active_color = "cyan"
    dangerous = DangerousConfirmService()
    dangerous.arm_or_confirm("A2")

    colors = service.build_page_colors(page, FakeAudio({"A1"}), dangerous)

    assert colors["A1"] == "cyan"
    assert colors["A2"] == "yellow"


def test_lighting_clear_resets_cache():
    device = FakeDevice()
    service = LightingService(device=device)
    service.refresh_page(Page.blank())
    service.clear()

    assert device.cleared is True
    assert service._last_colors == {}


def test_async_lighting_output_uses_worker():
    device = FakeDevice()
    service = LightingService(device=device, async_output=True)

    try:
        service.refresh_page(Page.blank())
        deadline = time.monotonic() + 1
        while not device.batches and time.monotonic() < deadline:
            time.sleep(0.01)

        assert len(device.batches) == 1
        assert len(device.batches[0]) == 64
    finally:
        service.shutdown()
