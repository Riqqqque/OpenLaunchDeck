import sys

from openlaunchdeck.services.update_service import UpdateService


def test_github_release_fallback_requires_installer_checksum(monkeypatch):
    calls = []
    release = {
        "tag_name": "v0.2.0",
        "html_url": "https://example.com/releases/v0.2.0",
        "published_at": "2026-01-01T00:00:00Z",
        "assets": [
            {
                "name": "OpenLaunchDeckSetup-0.2.0.exe",
                "browser_download_url": "https://example.com/OpenLaunchDeckSetup-0.2.0.exe",
            },
            {
                "name": "OpenLaunchDeckSetup-0.2.0.exe.sha256",
                "browser_download_url": "https://example.com/OpenLaunchDeckSetup-0.2.0.exe.sha256",
            },
        ],
    }

    class Response:
        def __init__(self, payload=None, text=""):
            self.payload = payload
            self.text = text

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class Requests:
        @staticmethod
        def get(url, **kwargs):
            calls.append((url, kwargs))
            if url.endswith(".sha256"):
                return Response(text=f"{'a' * 64}  OpenLaunchDeckSetup-0.2.0.exe")
            return Response(payload=release)

    monkeypatch.setitem(sys.modules, "requests", Requests)

    manifest = UpdateService("0.1.0").fetch_release_manifest("stable")

    assert manifest.latest_version == "0.2.0"
    assert manifest.sha256 == "a" * 64
    assert manifest.download_url.endswith("OpenLaunchDeckSetup-0.2.0.exe")
    assert calls[0][0].endswith("/releases/latest")
    assert calls[0][1]["timeout"] == 10
