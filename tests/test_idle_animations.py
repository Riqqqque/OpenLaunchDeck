import base64
import itertools
import json
import zlib

import pytest

from openlaunchdeck.animations import builtin
from openlaunchdeck.animations.builtin import BUILTIN_ANIMATIONS
from openlaunchdeck.animations.library import AnimationLibrary
from openlaunchdeck.animations.model import (
    FRAME_SIZE,
    MAX_FRAMES,
    SHARE_CODE_PREFIX,
    AnimationError,
    IdleAnimation,
    blank_frame,
    decode_share_code,
    encode_share_code,
    normalize_color,
    scale_color,
)
from openlaunchdeck.animations.player import IdleAnimationPlayer
from openlaunchdeck.models.settings import Settings


def _animation(**overrides):
    data = {"name": "Blink", "fps": 4, "frames": [blank_frame(), ["#ff0000"] * FRAME_SIZE]}
    data.update(overrides)
    return IdleAnimation.from_dict(data)


def test_there_are_fifteen_unique_builtin_animations():
    ids = [animation.id for animation in BUILTIN_ANIMATIONS]

    assert len(ids) == 15
    assert len(set(ids)) == 15
    assert all(animation.name and animation.description for animation in BUILTIN_ANIMATIONS)


@pytest.mark.parametrize("animation", BUILTIN_ANIMATIONS, ids=lambda item: item.id)
def test_builtin_animations_produce_valid_deterministic_frames(animation):
    first = list(itertools.islice(animation.iter_frames(42), 90))
    second = list(itertools.islice(animation.iter_frames(42), 90))

    assert first == second
    assert 1 <= animation.fps <= 30
    for frame in first:
        assert len(frame) == FRAME_SIZE
        assert all(normalize_color(color) == color for color in frame)
    assert len({tuple(frame) for frame in first}) > 1, "animation should actually move"


def test_model_rejects_bad_data():
    with pytest.raises(AnimationError, match="name"):
        _animation(name="  ")
    with pytest.raises(AnimationError, match="frames per second"):
        _animation(fps=0)
    with pytest.raises(AnimationError, match="frames per second"):
        _animation(fps=True)
    with pytest.raises(AnimationError, match="exactly 64"):
        _animation(frames=[["#000000"] * 63])
    with pytest.raises(AnimationError, match="Invalid pad color"):
        _animation(frames=[["red"] * FRAME_SIZE])
    with pytest.raises(AnimationError, match="limited"):
        _animation(frames=[blank_frame()] * (MAX_FRAMES + 1))
    with pytest.raises(AnimationError, match="newer"):
        _animation(version=99)


def test_model_normalizes_colors_and_text():
    animation = _animation(name="  Neon   Wave ", frames=[["#F0A"] * FRAME_SIZE], author="  Rique ")

    assert animation.name == "Neon Wave"
    assert animation.author == "Rique"
    assert animation.frames[0][0] == "#ff00aa"
    assert scale_color("#ff8000", 0.5) == "#804000"


def test_share_code_round_trip_and_rejects_tampering():
    animation = _animation(description="Two-frame blink")

    code = encode_share_code(animation)
    restored = decode_share_code(f"  {code[:20]}\n{code[20:]}  ")

    assert code.startswith(SHARE_CODE_PREFIX)
    assert restored.name == "Blink"
    assert restored.frames == animation.frames
    with pytest.raises(AnimationError, match="isn't"):
        decode_share_code("hello")
    with pytest.raises(AnimationError, match="damaged"):
        decode_share_code(SHARE_CODE_PREFIX + "!!!not-base64!!!")


def test_share_code_refuses_oversized_payloads_before_parsing():
    bomb = zlib.compress(b"[" + b"0," * 900_000 + b"0]", 9)
    code = SHARE_CODE_PREFIX + base64.urlsafe_b64encode(bomb).decode().rstrip("=")

    with pytest.raises(AnimationError, match="too large"):
        decode_share_code(code)


def test_library_saves_imports_exports_and_deletes(tmp_path, monkeypatch):
    from openlaunchdeck.animations import library as library_module

    monkeypatch.setattr(library_module, "BACKUPS_DIR", tmp_path / "backups")
    library = AnimationLibrary(directory=tmp_path / "animations")
    saved = library.save(_animation())
    copy = library.import_share_code(library.share_code(saved.id))
    export_path = tmp_path / "shared.json"
    library.export_file("rainbow_wave", export_path)
    imported = library.import_file(export_path)

    assert saved.id == "blink"
    assert copy.id == "blink_2"
    assert imported.name == "Rainbow Wave"
    assert imported.frame_count == 200
    assert {item.id for item in AnimationLibrary(directory=tmp_path / "animations").user_animations()} == {
        "blink",
        "blink_2",
        "rainbow_wave_2",
    }
    assert library.delete("blink") is True
    assert library.delete("rainbow_wave") is False
    assert (tmp_path / "backups" / "deleted_animations" / "blink.json").exists()


def test_library_skips_broken_files(tmp_path):
    directory = tmp_path / "animations"
    directory.mkdir()
    (directory / "broken.json").write_text("{nope", encoding="utf-8")
    (directory / "wrong.json").write_text(json.dumps({"name": "x", "frames": []}), encoding="utf-8")

    library = AnimationLibrary(directory=directory)

    assert library.user_animations() == []
    assert len(library.all()) == 15


class FakeLighting:
    def __init__(self):
        self.overlay_active = False
        self.frames = []
        self.ended = 0

    def begin_overlay(self):
        if self.overlay_active:
            return False
        self.overlay_active = True
        return True

    def send_overlay_frame(self, colors):
        self.frames.append(colors)
        return len(colors)

    def end_overlay(self):
        self.overlay_active = False
        self.ended += 1


class FakeDevice:
    connected = True


class FakeSettingsService:
    def __init__(self, **values):
        self.settings = Settings(idle_animation_enabled=True, idle_animation_timeout_seconds=15, **values)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _player(tmp_path, clock, **settings):
    lighting = FakeLighting()
    device = FakeDevice()
    player = IdleAnimationPlayer(
        lighting_service=lighting,
        device=device,
        settings_service=FakeSettingsService(**settings),
        library=AnimationLibrary(directory=tmp_path / "animations"),
        clock=clock,
    )
    return player, lighting, device


def _step(player):
    with player._state_lock:
        return player._step_locked()


def test_player_waits_for_the_idle_timeout_then_plays_and_stops_on_activity(tmp_path):
    clock = Clock()
    player, lighting, _device = _player(tmp_path, clock)

    clock.now += 14
    _step(player)
    assert lighting.frames == []

    clock.now += 2
    delay = _step(player)
    assert player.playing
    assert len(lighting.frames) == 1 and len(lighting.frames[0]) == 64
    assert delay == pytest.approx(1 / 20)

    assert player.note_activity() is True
    assert not player.playing and lighting.ended == 1
    clock.now += 5
    _step(player)
    assert not player.playing


def test_player_respects_switches_device_and_blockers(tmp_path):
    clock = Clock()
    player, lighting, device = _player(tmp_path, clock, idle_animation_brightness=50, idle_animation_speed=200)

    player.settings_service.settings.idle_animation_enabled = False
    clock.now += 60
    _step(player)
    assert not player.playing

    player.settings_service.settings.idle_animation_enabled = True
    device.connected = False
    _step(player)
    assert not player.playing

    device.connected = True
    player.can_start = lambda: False
    _step(player)
    assert not player.playing

    player.can_start = lambda: True
    delay = _step(player)
    assert player.playing
    assert delay == pytest.approx(1 / 30)
    assert max(int(color[1:3], 16) for color in lighting.frames[-1].values()) <= 128

    device.connected = False
    _step(player)
    assert not player.playing and lighting.ended == 1


def test_preview_plays_immediately_for_a_while_even_when_disabled(tmp_path):
    clock = Clock()
    player, lighting, _device = _player(tmp_path, clock)
    player.settings_service.settings.idle_animation_enabled = False

    assert player.preview("heartbeat", seconds=3) is True
    _step(player)
    assert player.current_animation_id == "heartbeat"
    clock.now += 4
    _step(player)

    assert not player.playing
    assert lighting.ended == 1
    assert player.preview("does_not_exist") is False


def test_shuffle_and_unknown_ids_fall_back_safely(tmp_path):
    clock = Clock()
    player, _lighting, _device = _player(tmp_path, clock, idle_animation_id="gone")
    clock.now += 20
    _step(player)
    assert player.current_animation_id == "rainbow_wave"

    player.note_activity()
    player.settings_service.settings.idle_animation_shuffle = True
    clock.now += 20
    _step(player)
    assert player.current_animation_id in builtin.BUILTIN_BY_ID


def test_player_thread_shuts_down_promptly(tmp_path):
    clock = Clock()
    player, _lighting, _device = _player(tmp_path, clock)
    player.start()
    player.shutdown()

    assert not player._thread.is_alive()


def test_idle_animation_settings_are_clamped():
    settings = Settings.from_dict(
        {
            "idle_animation_timeout_seconds": "1",
            "idle_animation_speed": 9999,
            "idle_animation_brightness": "abc",
            "idle_animation_id": "   ",
            "idle_animation_enabled": "yes",
        }
    )

    assert settings.idle_animation_timeout_seconds == 3
    assert settings.idle_animation_speed == 300
    assert settings.idle_animation_brightness == 100
    assert settings.idle_animation_id == "rainbow_wave"
    assert settings.idle_animation_enabled is True
    assert Settings().idle_animation_enabled is False
    assert Settings().idle_animation_timeout_seconds == 15


def test_settings_dialog_idle_animation_tab_saves_choices(tmp_path):
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from openlaunchdeck.services.settings_service import SettingsService
    from openlaunchdeck.ui.settings_dialog import SettingsDialog

    QApplication.instance() or QApplication([])
    service = SettingsService()
    previews = []

    class Player:
        def preview(self, animation_id, seconds, speed, brightness):
            previews.append((animation_id, speed, brightness))
            return True

    library = AnimationLibrary(directory=tmp_path / "animations")
    library.save(_animation(name="My Blink", author="Rique"))
    dialog = SettingsDialog(service, animation_library=library, idle_player=Player())

    labels = [dialog.idle_animation.itemText(index) for index in range(dialog.idle_animation.count())]
    assert labels[0] == "Rainbow Wave"
    assert "My Blink by Rique" in labels
    dialog.idle_enabled.setChecked(True)
    dialog.idle_timeout.setValue(45)
    dialog.idle_animation.setCurrentIndex(dialog.idle_animation.findData("fire"))
    dialog.idle_speed.spin.setValue(150)
    dialog.idle_brightness.spin.setValue(60)
    dialog._preview_idle_on_device()
    dialog.accept()

    settings = service.settings
    assert previews == [("fire", 150, 60)]
    assert settings.idle_animation_enabled is True
    assert settings.idle_animation_timeout_seconds == 45
    assert settings.idle_animation_id == "fire"
    assert settings.idle_animation_speed == 150
    assert settings.idle_animation_brightness == 60


def _qt_app():
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_animation_editor_paints_frames_undoes_and_saves(tmp_path):
    _qt_app()
    from openlaunchdeck.ui.animation_editor_dialog import AnimationEditorDialog

    library = AnimationLibrary(directory=tmp_path / "animations")
    editor = AnimationEditorDialog(library)

    editor._choose_color("#22d3ee")
    editor._push_undo()
    editor._paint_cell(0, False)
    editor._duplicate_frame()
    editor._shift_frame(0, 1)
    assert editor.frames[1][1] == "#22d3ee" and editor.frames[1][0] == "#000000"
    editor.undo()
    assert editor.frames[1][0] == "#22d3ee"
    editor.redo()
    assert editor.frames[1][1] == "#22d3ee"

    editor._save()
    assert editor.saved_animation is None, "saving without a name is refused"
    editor.name_edit.setText("Cyan Step")
    editor.author_edit.setText("Rique")
    editor.fps.setValue(6)
    editor._save()

    saved = library.get(editor.saved_animation.id)
    assert saved.name == "Cyan Step"
    assert saved.author == "Rique"
    assert saved.fps == 6
    assert saved.frame_count == 2


def test_animation_library_dialog_uses_shares_and_imports(tmp_path, monkeypatch):
    app = _qt_app()
    from openlaunchdeck.services.settings_service import SettingsService
    from openlaunchdeck.ui import animation_library_dialog as dialog_module

    library = AnimationLibrary(directory=tmp_path / "animations")
    service = SettingsService()
    service.update(idle_animation_enabled=False, idle_animation_id="rainbow_wave")
    dialog = dialog_module.AnimationLibraryDialog(library, service)

    assert len(dialog._cards) == 15
    dialog._select("fire")
    dialog._use_selected()
    assert service.settings.idle_animation_id == "fire"
    assert service.settings.idle_animation_enabled is True
    assert dialog.delete_button.isEnabled() is False
    assert dialog.edit_button.text() == "Edit a copy"

    dialog._copy_share_code()
    code = app.clipboard().text()
    assert code.startswith("OLDA1:")
    monkeypatch.setattr(dialog_module.QInputDialog, "getMultiLineText", lambda *args, **kwargs: (code, True))
    dialog._import_share_code()

    imported = library.get(dialog.selected_id)
    assert imported.name == "Campfire"
    assert not getattr(imported, "builtin", False)
    dialog._set_filter("mine")
    assert list(dialog._cards) == [imported.id]
