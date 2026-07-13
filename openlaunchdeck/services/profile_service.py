from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from ..config_store import read_json, write_json
from ..models.page import Page
from ..models.profile import Profile
from ..paths import BACKUPS_DIR, PROFILES_DIR, STARTER_PROFILES_DIR, ensure_user_dirs


class ProfileService:
    def __init__(self, logger=None) -> None:
        ensure_user_dirs()
        self.logger = logger
        self.profiles: dict[str, Profile] = {}
        self._profile_paths: dict[str, Path] = {}
        self.current_profile_id = ""
        self.current_page_id = ""
        self.load_profiles()

    def load_profiles(self) -> None:
        self.profiles.clear()
        self._profile_paths.clear()
        self.ensure_starter_profiles()
        for path in sorted(PROFILES_DIR.glob("*.json")):
            try:
                data = read_json(path, {})
                profile = Profile.from_dict(data)
                original_id = profile.id
                profile.id = self._unique_profile_id(profile.id, fallback=path.stem)
                self.profiles[profile.id] = profile
                self._profile_paths[profile.id] = path
                if self._has_stale_button_ids(data) or profile.id != original_id:
                    self.save_profile(profile)
                    if self.logger:
                        self.logger.info("Repaired profile data: %s", path)
            except Exception:
                if self.logger:
                    self.logger.exception("Profile failed to load: %s", path)
        if not self.profiles:
            profile = Profile.blank()
            self.profiles[profile.id] = profile
            self.save_profile(profile)
        first = next(iter(self.profiles.values()))
        self.current_profile_id = first.id
        self.current_page_id = first.default_page

    def ensure_starter_profiles(self) -> None:
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        if any(PROFILES_DIR.glob("*.json")):
            return
        if STARTER_PROFILES_DIR.exists():
            for source in STARTER_PROFILES_DIR.glob("*.json"):
                shutil.copy2(source, PROFILES_DIR / source.name)

    @property
    def current_profile(self) -> Profile:
        return self.profiles[self.current_profile_id]

    @property
    def current_page(self) -> Page:
        return self.current_profile.get_page(self.current_page_id)

    def set_current_profile(self, profile_id: str) -> bool:
        if profile_id not in self.profiles:
            return False
        self.current_profile_id = profile_id
        self.current_page_id = self.profiles[profile_id].default_page
        return True

    def set_current_page(self, page_id: str) -> bool:
        if page_id not in self.current_profile.page_ids():
            return False
        self.current_page_id = page_id
        return True

    def save_current(self) -> None:
        self.save_profile(self.current_profile)

    def save_profile(self, profile: Profile) -> None:
        original_id = profile.id
        profile.id = self._safe_profile_id(profile.id, fallback=profile.name)
        path = self._profile_paths.pop(original_id, None) or self._profile_paths.get(profile.id)
        if path is None or not self._is_profiles_path(path):
            path = PROFILES_DIR / f"{profile.id}.json"
        self._profile_paths[profile.id] = path
        write_json(path, profile.to_dict())

    def create_profile(self, name: str) -> Profile:
        profile_id = self._slug(name) or f"profile_{uuid.uuid4().hex[:8]}"
        while profile_id in self.profiles:
            profile_id = f"{profile_id}_{uuid.uuid4().hex[:4]}"
        profile = Profile.blank(name=name, profile_id=profile_id)
        self.profiles[profile.id] = profile
        self._profile_paths[profile.id] = PROFILES_DIR / f"{profile.id}.json"
        self.save_profile(profile)
        return profile

    def duplicate_profile(self, profile_id: str) -> Profile:
        source = self.profiles[profile_id]
        profile = Profile.from_dict(source.to_dict())
        profile.name = f"{source.name} Copy"
        profile.id = self._unique_profile_id(self._slug(profile.name), fallback="profile")
        self.profiles[profile.id] = profile
        self._profile_paths[profile.id] = PROFILES_DIR / f"{profile.id}.json"
        self.save_profile(profile)
        return profile

    def delete_profile(self, profile_id: str) -> bool:
        if profile_id not in self.profiles or len(self.profiles) <= 1:
            return False
        path = self._profile_paths.pop(profile_id, PROFILES_DIR / f"{profile_id}.json")
        if path.exists() and self._is_profiles_path(path):
            backup_dir = BACKUPS_DIR / "deleted_profiles"
            backup_dir.mkdir(parents=True, exist_ok=True)
            target = self._unique_path(backup_dir / path.name)
            shutil.move(str(path), str(target))
        self.profiles.pop(profile_id)
        if self.current_profile_id == profile_id:
            first = next(iter(self.profiles.values()))
            self.current_profile_id = first.id
            self.current_page_id = first.default_page
        return True

    def add_page(self, name: str = "New Page") -> Page:
        base_id = self._slug(name) or "page"
        page_id = base_id
        index = 2
        while page_id in self.current_profile.page_ids():
            page_id = f"{base_id}_{index}"
            index += 1
        page = Page.blank(name=name, page_id=page_id)
        self.current_profile.pages.append(page)
        self.save_current()
        return page

    def duplicate_page(self, page_id: str) -> Page:
        source = self.current_profile.get_page(page_id)
        data = source.to_dict()
        data["name"] = f"{source.name} Copy"
        data["id"] = self._slug(data["name"])
        page = Page.from_dict(data)
        while page.id in self.current_profile.page_ids():
            page.id = f"{page.id}_{uuid.uuid4().hex[:4]}"
        self.current_profile.pages.append(page)
        self.save_current()
        return page

    def delete_page(self, page_id: str) -> bool:
        profile = self.current_profile
        if len(profile.pages) <= 1:
            return False
        profile.pages = [page for page in profile.pages if page.id != page_id]
        if profile.default_page == page_id:
            profile.default_page = profile.pages[0].id
        if self.current_page_id == page_id:
            self.current_page_id = profile.default_page
        self.save_current()
        return True

    def import_profile(self, path: Path) -> Profile:
        data = read_json(path, {})
        if not isinstance(data, dict) or not str(data.get("name") or "").strip():
            raise ValueError("Profile JSON must contain a profile name.")
        profile = Profile.from_dict(data)
        profile.id = self._unique_profile_id(profile.id, fallback=profile.name)
        self.profiles[profile.id] = profile
        self._profile_paths[profile.id] = PROFILES_DIR / f"{profile.id}.json"
        self.save_profile(profile)
        return profile

    def export_profile(self, profile_id: str, path: Path) -> None:
        profile = self.profiles[profile_id]
        write_json(path, profile.to_dict())

    @staticmethod
    def _slug(text: str) -> str:
        slug = "".join(char.lower() if char.isalnum() else "_" for char in text.strip())
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug.strip("_")

    @classmethod
    def _safe_profile_id(cls, value: str, fallback: str = "profile") -> str:
        return (cls._slug(str(value or "")) or cls._slug(fallback) or "profile")[:80]

    def _unique_profile_id(self, value: str, fallback: str = "profile") -> str:
        base = self._safe_profile_id(value, fallback)
        candidate = base
        index = 2
        while candidate in self.profiles:
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    @staticmethod
    def _is_profiles_path(path: Path) -> bool:
        try:
            path.resolve().relative_to(PROFILES_DIR.resolve())
        except (OSError, ValueError):
            return False
        return True

    @staticmethod
    def _unique_path(path: Path) -> Path:
        candidate = path
        index = 2
        while candidate.exists():
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            index += 1
        return candidate

    @staticmethod
    def _has_stale_button_ids(data: object) -> bool:
        if not isinstance(data, dict):
            return False
        for page in data.get("pages", []):
            if not isinstance(page, dict):
                continue
            buttons = page.get("buttons", {})
            if not isinstance(buttons, dict):
                continue
            for button_id, button in buttons.items():
                if isinstance(button, dict) and button.get("id") not in (None, "", button_id):
                    return True
        return False
