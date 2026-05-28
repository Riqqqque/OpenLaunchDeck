from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .page import Page


@dataclass(slots=True)
class Profile:
    name: str
    id: str
    pages: list[Page] = field(default_factory=lambda: [Page.blank()])
    default_page: str = "main"
    settings: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def blank(cls, name: str = "Blank", profile_id: str = "blank") -> "Profile":
        return cls(name=name, id=profile_id, pages=[Page.blank()], default_page="main")

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Profile":
        if not isinstance(data, dict):
            return cls.blank()
        raw_pages = data.get("pages")
        pages = [Page.from_dict(page) for page in raw_pages] if isinstance(raw_pages, list) else []
        if not pages:
            pages = [Page.blank()]
        default_page = str(data.get("default_page") or pages[0].id)
        return cls(
            name=str(data.get("name") or "Untitled"),
            id=str(data.get("id") or "untitled"),
            default_page=default_page,
            pages=pages,
            settings=data.get("settings") if isinstance(data.get("settings"), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            "default_page": self.default_page,
            "settings": dict(self.settings),
            "pages": [page.to_dict() for page in self.pages],
        }

    def get_page(self, page_id: str | None = None) -> Page:
        wanted = page_id or self.default_page
        for page in self.pages:
            if page.id == wanted:
                return page
        return self.pages[0]

    def page_ids(self) -> list[str]:
        return [page.id for page in self.pages]
