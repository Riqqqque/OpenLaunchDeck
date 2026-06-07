import json
from pathlib import Path

from openlaunchdeck.models.profile import Profile
from openlaunchdeck.paths import STARTER_PROFILES_DIR


PRIVATE_MARKERS = [
    "C:" + "\\Users\\",
    ".".join(("192", "168", "")),
    "@" + "gmail.com",
    "@" + "outlook.com",
    "@" + "hotmail.com",
    "replace" + "-this",
    "place" + "holder",
    "plan" + "ned",
    "example" + ".com",
    "example" + ".local",
]


def test_starter_profiles_are_valid_json_and_loadable():
    paths = sorted(Path(STARTER_PROFILES_DIR).glob("*.json"))

    assert paths
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        profile = Profile.from_dict(data)
        assert profile.id
        assert profile.pages
        assert len(profile.get_page(profile.default_page).buttons) == 64


def test_starter_profiles_do_not_contain_private_values():
    for path in Path(STARTER_PROFILES_DIR).glob("*.json"):
        text = path.read_text(encoding="utf-8")
        for marker in PRIVATE_MARKERS:
            assert marker not in text
