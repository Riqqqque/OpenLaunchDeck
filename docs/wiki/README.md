# Wiki Source

This folder is the source of truth for the public OpenLaunchDeck wiki.

## Publishing

1. Edit and review the Markdown files in this folder.
2. Run the repository tests to validate local links and navigation.
3. Clone `https://github.com/Riqqqque/OpenLaunchDeck.wiki.git`.
4. Sync the source into the clone:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync-wiki.ps1 -WikiPath <wiki-clone-path>
```

5. Review, commit, and push the wiki repository.

The sync script does not publish this maintainer README. It publishes the user-facing pages, removes stale pages from the wiki clone, and converts local `.md` links to extensionless GitHub Wiki links.

## Navigation

Every user-facing page must be linked from `_Sidebar.md`. `Home.md` is the landing page and `_Footer.md` provides repository, download, and issue links.
