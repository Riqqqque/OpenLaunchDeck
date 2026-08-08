# Sound Library

The Sound Library is a native card browser for previewing and assigning short sounds. Open it from **Soundboard > Browse Sound Library** or select a Play Sound action and click **Library** beside its file field.

The selected pad appears in the top-right corner. Each card has two direct controls:

- **Preview** plays a quiet preview without changing the profile.
- **Use A1** assigns a local sound to the selected pad. An online result uses **Get + Use** until its download finishes.

## Starter Sounds

The first tab opens immediately with **OpenLaunchDeck Essentials**, a small set of original WAV effects included with the app. It covers alerts, reactions, gaming, transitions, stream tools, and utility feedback.

1. Select a pad in the main grid.
2. Open the Sound Library.
3. Stay on **Starter Sounds**.
4. Click **Preview** on any card.
5. Click **Use A1** when it is the sound you want.

No account or network request is needed. On first use, the app copies the selected collection into AppData so profile paths never depend on the install folder.

## My Sounds

Use **My Sounds** for files already managed by OpenLaunchDeck:

1. Click **Import Local Sound**.
2. Choose a `.wav`, `.mp3`, or `.ogg` file up to 25 MB.
3. Preview the new card.
4. Click **Use A1**.

The original file is left alone. The imported copy uses a content hash, so importing the same file again does not create another audio file.

Managed files live under:

```text
%APPDATA%\OpenLaunchDeck\imported_assets\sound_library
```

## Online Search

Online search is optional and uses Freesound. OpenLaunchDeck does not ship a shared provider credential.

1. Open **Online Search**.
2. Click **Connect Provider**.
3. Click **Get a Key**, sign in to Freesound, and create or copy a personal API key.
4. Paste the key and click **Save Key**.
5. Choose a category or enter a search.
6. Sort by **Popular**, **Newest**, **Top rated**, or **Best match**.
7. Preview a card, then click **Get + Use**.

The key is encrypted for the current Windows account. It is sent in an authorization header and is not placed in request URLs, profiles, or logs. **Manage Provider > Forget** removes it.

Search hides results marked explicit and limits clip length. CC0 is the default license filter. Broader filters are available, but every result still shows its creator and license.

## Assignment Behavior

Assignment enables the selected pad, sets its action to Play Sound, and adds a short label when the pad has no label. Existing Play Sound volume, voice-route, loop, repeat, playing-color, and page-change values are preserved.

The profile saves immediately. Clicking the on-screen pad still only selects it; use **Test Action** or the physical Launchpad to play it intentionally.

## Licensing And Credits

The online browser is a search and download tool, not a license guarantee.

- CC0 is the simplest starting point.
- Attribution licenses require creator credit.
- NonCommercial terms may not fit monetized streams or videos.
- Familiar music, shows, games, voices, and catchphrases can involve rights beyond an uploader's selected license.

Use **Source** to inspect the original page and **Copy Credit** to copy the selected credit line. A combined index is kept at:

```text
%APPDATA%\OpenLaunchDeck\imported_assets\sound_library\ATTRIBUTION.txt
```

The original starter effects are distributed with OpenLaunchDeck under the project license. No copyrighted media clips or third-party audio drivers are included.

## Responsiveness And Storage

- Search and downloads use Qt's asynchronous network APIs.
- Preview audio streams through QtMultimedia.
- Downloads stream into bounded `.part` files instead of Python memory.
- Files larger than 25 MB are rejected.
- Canceled and failed downloads remove partial files.
- Only trusted HTTPS Freesound URLs are accepted.
- Card layout reflows after resize without polling in the background.
