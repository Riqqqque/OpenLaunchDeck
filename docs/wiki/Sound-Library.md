# Sound Library

The Sound Library lets you find, preview, download, import, and assign short sounds without leaving OpenLaunchDeck.

Open it in either place:

- **Soundboard > Browse Sound Library**
- Select a pad, choose **Play Sound**, then click **Library** beside **Sound File**

## First-Time Setup

Online search uses Freesound and your own API key.

1. Open the Sound Library.
2. Click **Get Key**.
3. Sign in to Freesound and create or copy an API key.
4. Paste the key into OpenLaunchDeck.
5. Click **Save Key**.

The key is encrypted for your current Windows account. It is not stored in profiles, placed in request URLs, or written to logs. Use **Forget** to remove it.

You do not need an API key to import and organize your own local files in **My Library**.

## Find A Sound

1. Choose a category such as **Reaction / meme**, **Gaming**, **Alerts**, or **Transitions**.
2. Change the search text when you want something more specific.
3. Choose a sort:
   - **Most downloaded** for popular results
   - **Newest** for recent uploads
   - **Top rated** for highly rated results
   - **Best match** for the closest text match
4. Leave **License** on **CC0 only** for the simplest starting point.
5. Pick a maximum clip length.
6. Click **Search**.
7. Select a row and click **Preview**.

Double-clicking a result also previews it. Use **Stop** to end the preview.

## Download And Assign

To download first:

1. Select a result.
2. Click **Download**.
3. Open **My Library** to find it later.

To put it directly on a pad:

1. Select the target pad in the main window.
2. Select the sound in the library.
3. Click **Download & Assign**.

For an existing item in **My Library**, use **Assign to Pad**. The profile is saved immediately. Existing Play Sound settings on that pad are preserved.

Clicking an on-screen grid pad only selects it. Use **Test** or the physical Launchpad pad when you intentionally want to play the sound.

## Import Your Own Files

1. Open **My Library**.
2. Click **Import Local Sound**.
3. Choose a `.wav`, `.mp3`, or `.ogg` file up to 25 MB.
4. Select the imported sound and click **Assign to Pad**.

OpenLaunchDeck copies the file into its AppData library. Importing the same file again reuses the existing copy.

## Licenses And Credits

Every online result shows its creator and license. The default search shows CC0 sounds, but you are responsible for checking whether a sound is appropriate for your use.

- CC0 is the simplest option.
- Attribution licenses require credit.
- NonCommercial licenses may not fit monetized streams or videos.
- Familiar music, show clips, game clips, voices, or catchphrases can involve rights beyond the upload license.

Use **View Source** to inspect the original page and **Copy Credit** to copy a credit line. Open **Provider Terms** before using the online API in a commercial workflow.

OpenLaunchDeck keeps a combined credit file at:

```text
%APPDATA%\OpenLaunchDeck\imported_assets\sound_library\ATTRIBUTION.txt
```

## Safety And Performance

- Search and downloads run asynchronously.
- Preview audio streams instead of loading the full file into memory.
- Downloads use temporary files and have a 25 MB limit.
- Canceled and failed downloads remove partial files.
- Results marked explicit are hidden.
- No audio clips or audio drivers are bundled.

For playback volume, looping, repeated presses, output devices, and voice chat, continue to [Soundboard and Voice Chat](Soundboard-and-Discord-Routing.md).
