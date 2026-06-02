from openlaunchdeck.config_store import read_json, write_json


def test_read_json_accepts_utf8_bom(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"theme":"dark"}', encoding="utf-8-sig")

    assert read_json(path, {}) == {"theme": "dark"}


def test_write_json_uses_plain_utf8(tmp_path):
    path = tmp_path / "settings.json"

    write_json(path, {"theme": "dark"})

    assert path.read_bytes().startswith(b"{")
    assert read_json(path, {}) == {"theme": "dark"}
