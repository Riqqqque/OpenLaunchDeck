# Sound Library

The Sound Library provides a native in-app workflow for finding, previewing, downloading, importing, and assigning short sounds. Open it from **Soundboard > Browse Sound Library** or click **Library** beside a Play Sound action.

## Online Search

Online search uses the Freesound API. OpenLaunchDeck does not ship a shared API credential. Each user supplies a personal Freesound API key:

1. Open **Soundboard > Browse Sound Library**.
2. Click **Get Key** and sign in to Freesound.
3. Create or copy an API key.
4. Paste the key into OpenLaunchDeck and click **Save Key**.
5. Search by text or choose a category.
6. Sort by most downloaded, newest, top rated, or best match.
7. Preview a result, then choose **Download** or **Download & Assign**.

The saved key is encrypted for the current Windows account. It is sent in the request header, not placed in request URLs, profile files, or logs. **Forget** removes it from settings.

Searches hide results marked explicit and limit clip length. The default license filter shows CC0 sounds. Broader filters are available, but the license displayed for each result still applies.

## Licensing And Credits

The Sound Library is a search and download tool, not a license guarantee.

- **CC0** sounds generally do not require attribution, though credit is still useful.
- **Attribution** sounds require creator credit.
- **Attribution-NonCommercial** sounds have additional restrictions and may not fit monetized streams, videos, or other commercial use.
- A familiar phrase, song, show clip, game clip, or celebrity recording may include rights beyond the uploader's chosen license.

Review the source page and license before publishing or monetizing content. Freesound also has separate API terms. Open **Provider Terms** from the library before using online search in a commercial product or workflow.

OpenLaunchDeck stores source, creator, and license metadata beside each downloaded sound. A combined credit list is maintained at:

```text
%APPDATA%\OpenLaunchDeck\imported_assets\sound_library\ATTRIBUTION.txt
```

Use **Copy Credit** to copy the selected sound's credit line.

## My Library

The **My Library** tab contains sounds downloaded through the browser and files imported with **Import Local Sound**. Supported import types are `.wav`, `.mp3`, and `.ogg`, with a 25 MB per-file limit.

Library files live under:

```text
%APPDATA%\OpenLaunchDeck\imported_assets\sound_library
```

Importing does not change the original file. OpenLaunchDeck copies it into the library using a content hash, so importing the same file again does not create another audio copy.

## Assigning A Sound

1. Select a grid pad in the main window.
2. Open the Sound Library.
3. Select a downloaded or imported sound.
4. Click **Assign to Pad**.

For an online result that is not downloaded yet, click **Download & Assign**. The pad becomes enabled, uses the Play Sound action, and receives a short label when it does not already have one. Existing Play Sound volume, routing, loop, repeat, color, and page-change settings are preserved.

The app saves the profile immediately after assignment. Clicking a grid pad still only selects it; it does not play the sound. Use **Test** or press the physical pad when ready.

## Network And Storage Behavior

- Search and download requests are asynchronous and do not block the main window.
- Requests have timeouts and downloads can be canceled by closing the dialog.
- Preview audio streams through QtMultimedia.
- Downloads stream to a temporary `.part` file instead of loading the whole clip into memory.
- Files larger than 25 MB are rejected.
- Partial files are removed after cancellation or failure.
- Only HTTPS Freesound source and preview URLs are accepted.

No sounds or third-party audio drivers are bundled with OpenLaunchDeck.
