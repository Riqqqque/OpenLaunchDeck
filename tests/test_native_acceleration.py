import hashlib

import pytest

from openlaunchdeck import native_acceleration


def setup_function():
    native_acceleration.configure(False)


def test_python_fallback_button_mapping_helpers():
    assert native_acceleration.native_available() is False
    assert native_acceleration.validate_button_id("A1") is True
    assert native_acceleration.validate_button_id("H8") is True
    assert native_acceleration.validate_button_id("I1") is False
    assert native_acceleration.button_id_to_index("A1") == 0
    assert native_acceleration.button_id_to_index("H8") == 63
    assert native_acceleration.button_id_to_index("bad") == -1
    assert native_acceleration.index_to_button_id(0) == "A1"
    assert native_acceleration.index_to_button_id(63) == "H8"


def test_python_fallback_rejects_bad_index():
    with pytest.raises(ValueError):
        native_acceleration.index_to_button_id(64)


def test_python_fallback_hash_and_checksum(tmp_path):
    text = '{"name":"Basic PC"}'
    expected_text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    file_path = tmp_path / "payload.bin"
    file_path.write_bytes(b"payload")
    expected_file_hash = hashlib.sha256(b"payload").hexdigest()

    assert native_acceleration.calculate_profile_hash(text) == expected_text_hash
    assert native_acceleration.verify_sha256(file_path, expected_file_hash) is True
    assert native_acceleration.verify_sha256(file_path, "0" * 64) is False
