from __future__ import annotations

import json

from ..constants import DEFAULT_HTTP_TIMEOUT_SECONDS
from .base import ActionResult, BaseAction


class HttpRequestAction(BaseAction):
    type_name = "http_request"
    display_name = "HTTP Request"
    description = "Send an HTTP request or webhook."
    config_fields = [
        {"name": "method", "label": "Method", "type": "choice", "choices": ["GET", "POST", "PUT", "PATCH", "DELETE"], "default": "GET"},
        {"name": "url", "label": "URL", "type": "text", "placeholder": "https://example.com/webhook"},
        {"name": "headers", "label": "Headers JSON", "type": "multiline", "placeholder": "Optional JSON object, such as {\"Authorization\": \"Bearer ...\"}"},
        {
            "name": "body",
            "label": "Request Body",
            "type": "multiline",
            "visible_if": {"method": ["POST", "PUT", "PATCH", "DELETE"]},
        },
        {"name": "timeout", "label": "Timeout", "type": "number", "min": 1, "max": 60, "default": DEFAULT_HTTP_TIMEOUT_SECONDS, "suffix": " seconds"},
    ]
    blocking = True
    allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}

    def validate(self, config: dict) -> list[str]:
        method = str(config.get("method") or "GET").upper()
        if method not in self.allowed_methods:
            return ["Choose a supported HTTP method."]
        url = str(config.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            return ["Enter a valid HTTP or HTTPS URL."]
        raw_headers = str(config.get("headers") or "").strip()
        if raw_headers:
            try:
                headers = json.loads(raw_headers)
            except json.JSONDecodeError as exc:
                return [f"Headers JSON is invalid: {exc.msg}"]
            if not isinstance(headers, dict):
                return ["Headers JSON must be an object."]
        try:
            timeout = float(config.get("timeout") or DEFAULT_HTTP_TIMEOUT_SECONDS)
        except (TypeError, ValueError):
            return ["HTTP timeout must be a number."]
        return [] if 0 < timeout <= 60 else ["HTTP timeout must be between 1 and 60 seconds."]

    def execute(self, context, config: dict) -> ActionResult:
        try:
            import requests
        except Exception:
            return ActionResult.fail("HTTP dependency is not installed.")
        method = str(config.get("method") or "GET").upper()
        if method not in self.allowed_methods:
            return ActionResult.fail("HTTP method is not supported.")
        url = str(config.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            return ActionResult.fail("Enter a valid HTTP or HTTPS URL.")
        headers: dict[str, str] = {}
        raw_headers = str(config.get("headers") or "").strip()
        if raw_headers:
            try:
                parsed = json.loads(raw_headers)
            except json.JSONDecodeError as exc:
                return ActionResult.fail(f"Headers JSON is invalid: {exc}")
            if not isinstance(parsed, dict):
                return ActionResult.fail("Headers JSON must be an object.")
            headers = {str(key): str(value) for key, value in parsed.items()}
        try:
            timeout = float(config.get("timeout") or DEFAULT_HTTP_TIMEOUT_SECONDS)
        except (TypeError, ValueError):
            return ActionResult.fail("HTTP timeout must be a number.")
        if timeout <= 0 or timeout > 60:
            return ActionResult.fail("HTTP timeout must be between 1 and 60 seconds.")
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                data=str(config.get("body") or "") or None,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            return ActionResult.fail(f"HTTP request failed: {exc}")
        if response.status_code >= 400:
            return ActionResult.fail(f"HTTP request returned {response.status_code}.", response=response.text[:500])
        return ActionResult.ok(f"HTTP request returned {response.status_code}.", status_code=response.status_code)
