from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from openlaunchdeck.actions.registry import create_default_registry


ROOT = Path(__file__).resolve().parents[1]
WIKI_DIR = ROOT / "docs" / "wiki"
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _local_markdown_targets(path: Path) -> list[Path]:
    targets: list[Path] = []
    for raw_target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
        target = raw_target.strip().strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target_path = unquote(target.split("#", 1)[0])
        if target_path:
            targets.append((path.parent / target_path).resolve())
    return targets


def test_local_markdown_links_resolve():
    markdown_files = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "SUPPORT.md"]
    markdown_files.extend((ROOT / "docs").rglob("*.md"))

    broken: list[str] = []
    for source in markdown_files:
        for target in _local_markdown_targets(source):
            if not target.exists():
                broken.append(f"{source.relative_to(ROOT)} -> {target}")

    assert broken == []


def test_wiki_sidebar_links_every_user_page_once():
    published_pages = {
        path.name
        for path in WIKI_DIR.glob("*.md")
        if path.name not in {"README.md", "_Sidebar.md", "_Footer.md"}
    }
    sidebar = (WIKI_DIR / "_Sidebar.md").read_text(encoding="utf-8")
    sidebar_targets = [
        target.split("#", 1)[0]
        for target in MARKDOWN_LINK.findall(sidebar)
        if target.endswith(".md")
    ]

    assert set(sidebar_targets) == published_pages
    assert len(sidebar_targets) == len(set(sidebar_targets))


def test_actions_reference_covers_registered_actions():
    reference = (WIKI_DIR / "Actions-Reference.md").read_text(encoding="utf-8")

    missing = [action.display_name for action in create_default_registry().all() if f"## {action.display_name}" not in reference]

    assert missing == []


def test_maintainer_readme_is_not_in_public_wiki_navigation():
    sidebar = (WIKI_DIR / "_Sidebar.md").read_text(encoding="utf-8")
    home = (WIKI_DIR / "Home.md").read_text(encoding="utf-8")

    assert "README.md" not in sidebar
    assert "README.md" not in home
