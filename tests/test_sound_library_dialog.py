import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from openlaunchdeck.models.settings import Settings
from openlaunchdeck.models.sound_library import SoundLibraryItem
from openlaunchdeck.services import sound_library_service as library_module
from openlaunchdeck.ui.sound_library_dialog import SoundLibraryDialog


class SettingsServiceDouble:
    def __init__(self) -> None:
        self.settings = Settings()

    def update(self, **changes):
        for key, value in changes.items():
            setattr(self.settings, key, value)
        return self.settings


def _item() -> SoundLibraryItem:
    return SoundLibraryItem(
        provider="Freesound",
        sound_id=7,
        name="Quick alert",
        creator="sound-maker",
        license_name="Creative Commons 0",
        duration=1.2,
        preview_url="https://cdn.freesound.org/previews/7/7.mp3",
        source_url="https://freesound.org/people/sound-maker/sounds/7/",
        downloads=100,
        rating=4.2,
    )


def test_sound_library_assigns_an_existing_download(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", tmp_path)
    dialog = SoundLibraryDialog(SettingsServiceDouble(), selected_button_provider=lambda: "A1")
    item = _item()
    downloaded = dialog.service.downloaded_path(item)
    downloaded.write_bytes(b"ID3test")
    dialog._online_items = [item]
    dialog.tabs.setCurrentWidget(dialog.online_page)
    dialog._populate_online_table()
    assignments = []
    dialog.assign_requested.connect(lambda path, name: assignments.append((path, name)))

    dialog.assign_selected()

    assert assignments == [(str(downloaded), "Quick alert")]
    assert dialog.target_label.text() == "Selected pad: A1"
    dialog.close()
    dialog.deleteLater()
    app.processEvents()


def test_sound_library_requires_a_selected_pad_for_assignment(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", tmp_path)
    dialog = SoundLibraryDialog(SettingsServiceDouble(), selected_button_provider=lambda: "")
    item = _item()
    downloaded = dialog.service.downloaded_path(item)
    downloaded.write_bytes(b"ID3test")
    dialog._online_items = [item]
    dialog.tabs.setCurrentWidget(dialog.online_page)
    dialog._populate_online_table()
    assignments = []
    dialog.assign_requested.connect(lambda path, name: assignments.append((path, name)))

    dialog.assign_selected()

    assert assignments == []
    assert "Select a Launchpad pad" in dialog.status_label.text()
    dialog.close()
    dialog.deleteLater()
    app.processEvents()


def test_sound_library_cards_keep_controls_inside_their_frames(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", tmp_path)
    dialog = SoundLibraryDialog(SettingsServiceDouble(), selected_button_provider=lambda: "A1")
    dialog.resize(720, 620)
    dialog.show()
    app.processEvents()

    cards = dialog._cards["starter"]
    assert cards
    for card in cards:
        card.layout().activate()
        assert card.height() == 206
        assert card.preview_button.geometry().bottom() < card.height()
        assert card.use_button.geometry().bottom() < card.height()

    columns = dialog._gallery_columns(dialog.starter_scroll)
    rows = (len(cards) + columns - 1) // columns
    margins = dialog.starter_grid.contentsMargins()
    expected_height = rows * 206 + max(0, rows - 1) * dialog.starter_grid.verticalSpacing()
    expected_height += margins.top() + margins.bottom()
    assert dialog.starter_cards.minimumHeight() == expected_height
    for index in range(len(cards)):
        row, column, row_span, column_span = dialog.starter_grid.getItemPosition(index)
        assert (row, column, row_span, column_span) == (index // columns, index % columns, 1, 1)

    dialog.close()
    dialog.deleteLater()
    app.processEvents()


def test_sound_library_separates_starter_and_user_sounds(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", tmp_path)
    dialog = SoundLibraryDialog(SettingsServiceDouble(), selected_button_provider=lambda: "A1")

    assert dialog._starter_items
    assert all(item.provider == "OpenLaunchDeck Essentials" for item in dialog._starter_items)
    assert all(item.provider != "OpenLaunchDeck Essentials" for item in dialog._local_items)
    assert dialog.provider_credentials.isHidden()

    dialog.close()
    dialog.deleteLater()
    app.processEvents()
