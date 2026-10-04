# Idle Animations

When the Launchpad sits unused for a while, OpenLaunchDeck can play an animation across the 8x8 pads. Press any pad or hardware button and your deck lighting comes straight back.

Idle animations are off until you turn them on.

## Turn It On

1. Open **Settings > Settings > Idle Animation**.
2. Check **Play an animation on the Launchpad when the pads sit unused**.
3. Set **Start after** to how long the pads must go unused. The default is 15 seconds, and anything from 3 seconds to an hour works.
4. Pick an **Animation**, or check **Pick a different animation each time**.
5. Adjust **Speed** and **Brightness**, then click **Save**.

Use **Preview on Launchpad** to see the selected animation on the hardware for 8 seconds without waiting.

### The Press That Wakes The Deck

By default, the press that stops an animation also runs that pad's action. Turn off **Run the pad's action when a press stops the animation** if you'd rather the first press only wake the pads, like a screensaver.

### When Animations Don't Start

An animation only starts when:

- the Launchpad is connected (Simulation mode never animates the hardware)
- no pad is armed for a dangerous-action confirmation or flashing
- MIDI Debug calibration isn't running

Pressing a pad in the app, using **Test Action**, or reconnecting the Launchpad also restarts the idle countdown.

## Built-In Animations

| Animation | Looks like |
| --- | --- |
| Rainbow Wave | A smooth diagonal rainbow rolling across the grid |
| Nebula Breathe | Pink, violet, and mint drifting and slowly breathing |
| Aurora | Green and violet curtains rippling down from the top |
| Ripple | Color rings spreading out from the center |
| Plasma | Classic flowing plasma |
| Spiral | Rainbow arms spinning around the center |
| Rain | Blue drops falling down each column |
| Digital Rain | Green code streams with bright leading pads |
| Starfield | Pads twinkling in warm and cool whites |
| Campfire | Flames flickering up from the bottom row |
| Lava Lamp | Warm blobs drifting, merging, and splitting |
| Scanner | A red beam sweeping side to side |
| Snake | A rainbow snake winding through the grid |
| Heartbeat | A pink heart pulsing with a lub-dub rhythm |
| Game of Life | Conway's Game of Life, colored by cell age |

## The Animation Library

Open **Device > Idle Animations…**, or click **Browse, make, and share animations…** on the Idle Animation settings tab.

Every card plays its animation live. Select one to see details, then:

- **Use as idle animation** makes it the idle animation and turns idle animations on.
- **Preview on Launchpad** plays it on the hardware for 8 seconds.
- **Edit** opens your animation in the editor. Built-in animations show **Edit a copy**, which records about 10 seconds of the animation into frames you can change.
- **Copy share code** and **Export file…** share it with other people.
- **Delete** removes one of your animations. A copy is kept in the `backups\deleted_animations` folder. Built-in animations can't be deleted.

## Make Your Own

Click **New animation** in the library.

- Left-click or drag on the grid to paint with the selected color. Right-click to erase a pad.
- Pick colors from the palette, or click **Custom color…** for any color. Alt-click a pad, or use **Pick**, to reuse a color already on the grid.
- **Fill** and **Clear** affect the whole frame. The arrow buttons shift every pad one step and wrap around the edge, which makes scrolling effects quick to build.
- **Add**, **Duplicate**, **Delete**, and the ◀ ▶ buttons manage frames. **Duplicate** then shift is the fastest way to animate movement.
- Check **Show previous frame** to see the last frame faintly behind the current one.
- **Play** loops the animation in the editor. **fps** sets frames per second (1 to 30).
- Ctrl+Z undoes and Ctrl+Y redoes.

Give it a name, add your name as **Author** if you plan to share it, and click **Save animation**.

Animations can have up to 600 frames.

## Share And Import

There are two ways to share an animation. Neither one needs an account or an internet connection.

**Share code.** Select an animation and click **Copy share code**. The code starts with `OLDA1:`. Short animations fit in a chat message; longer ones produce codes too long for apps like Discord, so the library tells you when to share a file instead. To add someone else's, copy their code and click **Paste share code…** in the library.

**File.** Click **Export file…** to save a `.json` file. Others add it with **Import file…**.

Imported animations show the original author's name. Files and codes are checked before they're added, and anything damaged, oversized, or from a newer version of OpenLaunchDeck is rejected with a message.

## Where Animations Are Stored

Your saved and imported animations live in:

```text
%APPDATA%\OpenLaunchDeck\animations
```

Each animation is one `.json` file, so you can back up or copy the folder. See [Settings And Data](Settings-And-Data.md).

## Hardware Notes

Idle animations use the Launchpad Mini MK3's RGB lighting message so colors aren't limited to the 128-color palette. If an animation shows wrong colors or nothing at all, open **Device > MIDI Debug** and confirm the device is in Programmer Mode. See [Launchpad Mini MK3 Setup](Launchpad-Mini-MK3-Setup.md).
