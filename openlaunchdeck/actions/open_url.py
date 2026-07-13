from __future__ import annotations

from urllib.parse import urlparse
import webbrowser

from .base import ActionResult, BaseAction


class OpenUrlAction(BaseAction):
    type_name = "open_url"
    display_name = "Open URL"
    description = "Open a URL in the default browser."
    config_fields = [{"name": "url", "label": "URL", "type": "text"}]
    blocking = True

    def validate(self, config: dict) -> list[str]:
        url = str(config.get("url") or "")
        parsed = urlparse(url)
        return [] if parsed.scheme in {"http", "https"} and parsed.netloc else ["Enter a valid HTTP or HTTPS URL."]

    def execute(self, context, config: dict) -> ActionResult:
        errors = self.validate(config)
        if errors:
            return ActionResult.fail(errors[0])
        url = str(config["url"])
        opened = webbrowser.open(url)
        if not opened:
            return ActionResult.fail("Windows did not accept the URL open request.")
        return ActionResult.ok(f"Opened {url}.")
