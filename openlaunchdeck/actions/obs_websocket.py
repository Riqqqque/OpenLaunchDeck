from __future__ import annotations

from .base import ActionResult, BaseAction


class ObsWebSocketAction(BaseAction):
    type_name = "obs_websocket"
    display_name = "OBS WebSocket"
    description = "OBS WebSocket action definition. The transport is not implemented yet."
    config_fields = [
        {"name": "operation", "label": "Operation", "type": "text"},
        {"name": "scene_name", "label": "Scene Name", "type": "text"},
    ]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        return ActionResult.fail("OBS WebSocket support is not implemented yet.")
