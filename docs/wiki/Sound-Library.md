# Sound Library

The Sound Library lets you preview a sound and put it on the selected Launchpad pad without managing paths by hand.

Open it from either place:

- **Soundboard > Browse Sound Library**
- Select a pad, choose **Play Sound**, then click **Library** beside **Sound File**

The top-right label shows the current target, such as **Selected pad: A1**. If it says `none`, close the library, select a grid pad, and reopen it.

## Fastest First Sound

Use the first tab when you just want something that works:

1. Select a pad in the main grid.
2. Open the Sound Library.
3. Stay on **Starter Sounds**.
4. Click **Preview** on an alert, reaction, transition, gaming, camera, or utility card.
5. Click **Use A1** on the sound you want.
6. Close the library and click **Test Action**.

Starter Sounds are original lightweight WAV effects included with OpenLaunchDeck. They need no account or internet connection.

## Import A Sound You Already Have

1. Open **My Sounds**.
2. Click **Import Local Sound**.
3. Choose a `.wav`, `.mp3`, or `.ogg` file up to 25 MB.
4. Click **Preview** on the imported card.
5. Click **Use A1**.

OpenLaunchDeck copies the file into AppData and leaves the original untouched. Importing the same file again reuses the managed copy.

## Search Public Sounds

Online Search is optional and uses Freesound with your own API key.

### Connect Once

1. Open **Online Search**.
2. Click **Connect Provider**.
3. Click **Get a Key**.
4. Sign in to Freesound and create or copy an API key.
5. Paste it into OpenLaunchDeck and click **Save Key**.

The key is encrypted for your Windows account. It is not stored in profiles, placed in request URLs, or written to logs. Use **Manage Provider > Forget** to remove it.

### Find And Use A Result

1. Choose a category or type a search.
2. Choose **Popular**, **Newest**, **Top rated**, or **Best match**.
3. Keep **CC0 only** selected for the simplest license starting point.
4. Choose a maximum length.
5. Click **Search**.
6. Preview cards until you find the right sound.
7. Click **Get + Use**.

The download streams into AppData, its source and license are recorded, and the pad is assigned after the download passes validation.

## What Assignment Changes

The selected pad becomes enabled and uses the Play Sound action. A short label is added only when the pad was unlabeled. Existing Play Sound volume, voice routing, loop, repeat, playing color, and page-change settings are preserved.

Clicking an on-screen pad only selects it. It never plays the sound. Use **Test Action** or the physical Launchpad when you are ready.

## Licenses And Credits

Every public result shows its creator and license. OpenLaunchDeck helps retain that information, but it cannot guarantee that an upload is legally usable in every stream or video.

- CC0 is the simplest starting point.
- Attribution licenses require creator credit.
- NonCommercial terms may not fit monetized content.
- Music, shows, games, celebrity voices, and familiar catchphrases may involve rights beyond the selected upload license.

Use **Source** to inspect the original page and **Copy Credit** to copy a credit line. The combined credit file is:

```text
%APPDATA%\OpenLaunchDeck\imported_assets\sound_library\ATTRIBUTION.txt
```

## Storage And Performance

- Managed audio and metadata stay in `%APPDATA%\OpenLaunchDeck\imported_assets\sound_library`.
- Search and downloads run asynchronously.
- Previews stream through QtMultimedia.
- Downloads have timeouts and a 25 MB limit.
- Partial files are removed after cancellation or failure.
- Results marked explicit are hidden.
- The included starter collection is about 0.3 MB.
- No copyrighted media clips or third-party audio drivers are included.

For volume, looping, output devices, microphone mixing, Discord, and in-game voice chat, continue to [Soundboard and Voice Chat](Soundboard-and-Discord-Routing.md).
