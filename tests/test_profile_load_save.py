from openlaunchdeck.models.profile import Profile


def test_profile_round_trip_fills_missing_buttons():
    profile = Profile.from_dict(
        {
            "name": "Test",
            "id": "test",
            "default_page": "main",
            "pages": [
                {
                    "name": "Main",
                    "id": "main",
                    "buttons": {
                        "A1": {
                            "label": "Browser",
                            "color": "green",
                            "action": {"type": "open_url", "config": {"url": "https://example.com"}},
                        }
                    },
                }
            ],
        }
    )

    assert profile.get_page("main").get_button("A1").label == "Browser"
    assert len(profile.get_page("main").buttons) == 64
    assert profile.to_dict()["pages"][0]["buttons"]["H8"]["action"]["type"] == "noop"
