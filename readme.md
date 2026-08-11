# FreeRadio — NVDA Add-on

FreeRadio is an internet radio add-on for the NVDA screen reader. Its primary goal is to give users easy access to thousands of internet radio stations and podcasts. The entire interface and all features have been designed with full accessibility for NVDA in mind.

## Radio Browser Directory

FreeRadio uses the [Radio Browser](https://www.radio-browser.info/) open database for its station catalogue. Radio Browser is a community-managed, free directory hosting more than 50,000 internet radio stations from around the world. No registration or account is required and its API is open to everyone. Each station includes address, country, genre, language and bitrate information; stations are ranked by user votes. FreeRadio connects to this API through mirror servers located in Germany, the Netherlands and Austria; if one server is unreachable, it automatically switches to the next.

To keep the browser responsive and avoid hitting the API on every search or country change, FreeRadio keeps a local cache of the station catalogue on disk. This cache is refreshed automatically in the background on a periodic schedule, so the list you see is normally already up to date without any action on your part. You can also force an immediate re-sync at any time with the **Update Station List** button — see [Station Browser](#station-browser) below.

## Adding a Station to Radio Browser

If a station you are looking for is not in the Radio Browser directory, you can submit it yourself at [https://www.radio-browser.info/add](https://www.radio-browser.info/add). No account or registration is needed.

Fill in the form on that page:

- **Stream URL** *(required)* — the direct URL of the audio stream, ending in `.mp3`, `.aac`, `.ogg` or similar. This is not the station website address; it is the raw stream address you would paste into a media player. Most stations publish their stream URL on their website or in their "Listen live" section.
- **Station name** *(required)* — the name of the station as it should appear in the directory.
- **Homepage** — the station's website address.
- **Country and language** — select the country and the broadcast language from the dropdown lists.
- **Tags** — genre or topic keywords separated by commas, for example `news`, `jazz`, `classical`. These are used for searching and filtering.
- **Logo URL** — a direct link to the station's logo image, if available.

After submitting, the station is reviewed and added to the public directory. Once accepted it will appear in FreeRadio's search and country listings automatically, since the directory is refreshed from the live API.

## Requirements

- NVDA 2024.1 or later
- Windows 10 or later
- Internet connection

## Installation

Download the `.nvda-addon` file, press Enter on it and restart NVDA when prompted.

## Keyboard Shortcuts

All shortcuts can be reassigned from NVDA Menu → Preferences → Input Gestures → FreeRadio. These shortcuts work from anywhere, regardless of which window has focus.

| Shortcut | Function | Description |
|---|---|---|
| `Ctrl+Win+R` | Open station browser | Opens the browser window if closed, or brings it to the foreground if already open. |
| `Ctrl+Win+P` | Pause / resume | Pauses the current station if playing; resumes if paused. If nothing is playing, starts the last station or opens the favourites list depending on your setting. Pressing twice in quick succession jumps directly to a tab of your choice. Pressing three times can trigger a separate action depending on your setting. |
| `Ctrl+Win+S` | Stop | Fully stops the current station and resets the player. |
| `Ctrl+Win+→` | Next favourite | Moves to the next station in the favourites list. Wraps around to the beginning at the end of the list. |
| `Ctrl+Win+←` | Previous favourite | Moves to the previous station in the favourites list. Jumps to the end when at the beginning. |
| `Ctrl+Win+↑` | Volume up | Increases volume by 5; maximum 200. |
| `Ctrl+Win+↓` | Volume down | Decreases volume by 5; minimum 0. |
| `Ctrl+Win+V` | Add to favourites | Adds the currently playing station to the favourites list. Announces if the station is already in the list. |
| `Ctrl+Win+I` | Station info | Announces the currently playing station name. Press twice to show details such as country, genre and bitrate in a dialog. Press three times to copy the current track info (ICY metadata) to the clipboard if available; if no metadata is present, starts Shazam music recognition instead. Press four times to force music recognition in case of wrong ICY metadata. |
| `Ctrl+Win+M` | Audio mirror | Mirrors the current stream to an additional audio output device simultaneously. Press again to stop mirroring. |
| `Ctrl+Win+E` | Instant recording | Press once to start recording the current station; press again to stop. Press **twice** to start a **song recording** — the file is named after the current track and the recording stops automatically when the track changes. Press twice again while a song recording is active to stop it early. Playback continues uninterrupted in all recording modes. Only available for stations that broadcast ICY metadata. |
| `Ctrl+Win+W` | Open recordings folder | Opens the folder containing recorded files in File Explorer. |
| `Ctrl+Win+J` | Time-shift rewind | Rewinds live radio by 15 seconds. The first press enters time-shift mode; each further press moves 15 seconds further back, up to the buffer limit (~10 minutes). Requires the time-shift buffer to be enabled in Settings. |
| `Ctrl+Win+K` | Time-shift fast-forward | Moves forward 15 seconds while time-shifted. Once the live edge is reached, playback automatically returns to live and this becomes a no-op until you rewind again. |
| `Ctrl+Win+T` | Toggle time-shift buffer | Enables or disables the time-shift buffer on the fly, mirroring the Settings checkbox. Disabling immediately returns to live playback if time-shifted and stops the background capture. |
| *(unassigned)* | Toggle mute notifications | Toggles the Mute Notifications setting on the fly. Assign a key combination via NVDA Menu → Preferences → Input Gestures → FreeRadio. |
| *(unassigned)* | Play favourite station directly | Each station in your favourites list appears as a separate entry in NVDA Menu → Preferences → Input Gestures → **FreeRadio Stations**. Assign any keyboard shortcut to a station to start playing it instantly from anywhere, without opening the browser. |

Next / previous shortcuts only navigate the favourites list; they do not work with the all stations list. When a list is focused in the browser window, the left and right arrow keys serve the same purpose — see In-Dialog Shortcuts.

## Station Browser

FreeRadio also adds a **FreeRadio** submenu to the NVDA Tools menu. From there you can directly open the Station Browser and FreeRadio Settings.

The window opened with `Ctrl+Win+R` contains six tabs: All Stations, Favourites, Recording, Timer, Liked Songs, and Podcasts. You can navigate between tabs with `Ctrl+Tab` or using `Alt+1` through `Alt+6`.

When the All Stations tab opens, the top 1,000 most-voted stations are automatically loaded from Radio Browser. Selecting a country from the dropdown updates the list to show that country's stations. Typing in the search field instantly performs a full search across the entire Radio Browser database simultaneously by name, country and genre.

The **Output Device** dropdown at the bottom of the browser window — outside the tabs — lists all BASS-recognised audio output devices. Selecting a device immediately redirects audio output to it and saves the choice permanently; the same device is used automatically in the next session. If the selected device is not connected, the add-on falls back to the system default automatically. This control is only functional when the BASS backend is active.

The **Volume** (0–200) and **Effects** controls in the same area can be adjusted at any time while the window is open. From the Effects list, Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb, EQ: Bass Boost, EQ: Treble Boost and EQ: Vocal Boost can be enabled simultaneously; changes are applied to the active stream instantly. Each effect can also be toggled instantly with `Ctrl+1` through `Ctrl+0` without leaving the keyboard — see [Effect Shortcuts](#effect-shortcuts). These controls are fully functional only when the BASS backend is active.

When one or more EQ effects are enabled, a **gain control** appears for each active band. The gain can be set between −15 dB and +15 dB; the default values are Bass +9 dB, Treble +9 dB, and Vocal +6 dB. The gain controls are shown only for the EQ bands that are currently checked, and are hidden automatically when an EQ effect is unchecked. Gain values are saved globally and restored on the next session.

The **Play/Pause** button is also located at the bottom of the window. If no station is playing it starts the selected station; if a station is already playing it pauses playback.

The **Update Station List** button re-syncs the local station catalogue from the Radio Browser API immediately, instead of waiting for the periodic background refresh. While the refresh is running the button is disabled and NVDA announces that a refresh is in progress; if you press it again before the current refresh finishes, NVDA lets you know one is already underway. Once the refresh completes, NVDA announces that the station list has been updated and the currently displayed search results or country listing are refreshed automatically to reflect the new data.

When a station is selected in the list, the **Station Details** button displays information such as country, language, genre, format, bitrate, website and stream URL in a separate dialog. Each field appears in its own read-only text box; you can move between fields with Tab and copy all information to the clipboard at once with the **Copy all to clipboard** button. This button is available in both the All Stations and Favourites tabs.

### Station Context Menu

Right-click a station in the All Stations or Favourites list, or select it and press the Applications key or `Shift+F10`, to open a context menu with quick actions:

- **Station Details** — same as the Station Details button described above.
- **Add to Favourites** *(All Stations tab)* / **Delete Station** *(Favourites tab)*.
- **Rename Station** *(Favourites tab)* — same as `F9`.
- **Save Audio Profile for This Station** / **Clear Audio Profile** *(Favourites tab)* — see [Station Audio Profile](#station-audio-profile).
- **Test URL** — checks whether the selected station's stream is currently reachable without starting playback, and announces the result (reachable, or the reason it failed, such as an HTTP error or network timeout).

Only the items relevant to the current tab and selection are shown as available.

### In-Dialog Shortcuts

The following keys work only while the Station Browser window is active.

#### F Keys

| Shortcut | Function | Description |
|---|---|---|
| `F1` | Help guide | Opens the add-on's help file in the default browser. The guide for the active NVDA language is searched first; if not found, the default guide is opened. |
| `F2` | What's playing | Announces the currently playing station and track name. Press twice to show details such as country, genre and bitrate in a dialog. Press three times to copy the current track info (ICY metadata) to the clipboard if available; if no metadata is present, starts Shazam music recognition instead. Press four times to force music recognition in case of wrong ICY metadata. |
| `F3` | Previous item | On All Stations or Favourites tabs: moves to the previous station and starts playing immediately. On Podcasts tab: moves to the previous episode in the episode list and plays it. |
| `F4` | Next item | On All Stations or Favourites tabs: moves to the next station and starts playing immediately. On Podcasts tab: moves to the next episode and plays it. |
| `Shift+F3` | Previous feed | On Podcasts tab only: moves up one feed in the subscriptions list. |
| `Shift+F4` | Next feed | On Podcasts tab only: moves down one feed in the subscriptions list. |
| `F5` | Volume down | Decreases volume by 5 (minimum 0). |
| `F6` | Volume up | Increases volume by 5 (maximum 200). |
| `F7` | Pause / resume | Pauses if a station is playing; resumes if paused and media is loaded. |
| `F8` | Stop | Fully stops the current station and resets the player. |
| `F9` | Rename | Opens rename dialog for the focused station in the Favourites tab. |

#### List and Navigation Shortcuts

| Shortcut | Function | Description |
|---|---|---|
| `→` | Next item | When a station list is focused (All Stations / Favourites), moves to the next station and plays it immediately. When the episode list is focused (Podcasts), moves to the next episode and plays it. Wraps to the beginning at the end of the list. |
| `←` | Previous item | When a station list is focused, moves to the previous station and plays it. When the episode list is focused, moves to the previous episode and plays it. Jumps to the end when at the beginning. |
| `Ctrl+→` | Next episode | When the Podcasts tab is active, moves to the next episode and plays it (same as `→` while episode list is focused). |
| `Ctrl+←` | Previous episode | When the Podcasts tab is active, moves to the previous episode and plays it (same as `←` while episode list is focused). |
| `Enter` | Play | When a station or episode list is focused, starts playing the selected item immediately. Switches to the selected station even if another station is already playing. |
| `Space` | Play / Pause | Pauses if a station is playing; otherwise starts playing the selected item. |
| `Ctrl+Tab` | Next tab | Switches to the next tab (All Stations → Favourites → Recording → Timer → Liked Songs → Podcasts). |
| `Ctrl+Shift+Tab` | Previous tab | Switches to the previous tab. |
| `Escape` | Hide | Hides the window; the add-on continues playing in the background. |

#### Volume Shortcuts

| Shortcut | Function | Description |
|---|---|---|
| `Ctrl+↑` | Volume up | Increases volume by 5. Only works while the browser window is open. |
| `Ctrl+↓` | Volume down | Decreases volume by 5. Only works while the browser window is open. |

#### Effect Shortcuts

| Shortcut | Function | Description |
|---|---|---|
| `Ctrl+1` | Toggle Chorus | Enables or disables the Chorus effect and applies it to the active stream instantly. |
| `Ctrl+2` | Toggle Compressor | Enables or disables the Compressor effect and applies it to the active stream instantly. |
| `Ctrl+3` | Toggle Distortion | Enables or disables the Distortion effect and applies it to the active stream instantly. |
| `Ctrl+4` | Toggle Echo | Enables or disables the Echo effect and applies it to the active stream instantly. |
| `Ctrl+5` | Toggle Flanger | Enables or disables the Flanger effect and applies it to the active stream instantly. |
| `Ctrl+6` | Toggle Gargle | Enables or disables the Gargle effect and applies it to the active stream instantly. |
| `Ctrl+7` | Toggle Reverb | Enables or disables the Reverb effect and applies it to the active stream instantly. |
| `Ctrl+8` | Toggle EQ: Bass Boost | Enables or disables the Bass Boost EQ band and applies it to the active stream instantly. |
| `Ctrl+9` | Toggle EQ: Treble Boost | Enables or disables the Treble Boost EQ band and applies it to the active stream instantly. |
| `Ctrl+0` | Toggle EQ: Vocal Boost | Enables or disables the Vocal Boost EQ band and applies it to the active stream instantly. |

Each shortcut mirrors checking or unchecking the corresponding entry in the **Effects** list: NVDA announces whether the effect was enabled or disabled, the change is saved automatically, and the EQ gain control for that band (if applicable) appears or disappears accordingly. Only available when the BASS backend is active.

#### Alt Key Shortcuts

| Shortcut | Function | Description |
|---|---|---|
| `Alt+R` | Go to search field | Moves focus to the search text box. Searches Radio Browser with the text in the search field; name, country and genre are searched simultaneously. |
| `Alt+V` | Add / remove favourite | Adds the selected station to favourites; removes it if already in the list. |
| `Alt+1` | All Stations | Switches to the All Stations tab. |
| `Alt+2` | Favourites | Switches to the Favourites tab. |
| `Alt+3` | Recording | Switches to the Recording tab. |
| `Alt+4` | Timer | Switches to the Timer tab. |
| `Alt+5` | Liked Songs | Switches to the Liked Songs tab. |
| `Alt+6` | Podcasts | Switches to the Podcasts tab. |
| `Alt+K` | Close | Closes the window; the add-on continues playing in the background. |

## Favourites

The favourites list is a personal station collection stored permanently. To add a station, select it in the list and press the Add to Favourites button or use the `Alt+V` shortcut. The same shortcut removes a station that is already in the list when it is selected.

Favourites can be played with `Ctrl+Win+→` and `Ctrl+Win+←`; these shortcuts work even when the browser window is not open.

To delete a station from the favourites list, select it and press the **Delete Station** button or the `Delete` key. After deletion, focus and selection automatically move to the next station in the list. If the deleted station was the last one, focus moves to the previous station. If the list becomes empty, focus moves to the Play button.

### Exporting and Importing Favourites

The Favourites tab includes two buttons for backing up and restoring your station list:

**Export Favourites…** — saves your entire favourites list to a file. A save dialog lets you choose between two formats:
- **JSON** (`.json`) — a complete backup that preserves station names, stream URLs, and all metadata. Recommended for restoring your list later or moving it to another computer.
- **M3U playlist** (`.m3u`) — a standard playlist format compatible with most media players and radio apps. Note that M3U does not store all station metadata, so restoring from M3U may result in less detail than a JSON backup.

**Import Favourites…** — loads stations from a previously exported JSON or M3U file. After selecting the file, you are asked how to add the stations:
- **Yes (Merge)** — adds the imported stations to your existing list without removing any current favourites. Duplicate stations are not added twice.
- **No (Replace)** — clears your current favourites list entirely and replaces it with the contents of the imported file.
- **Cancel** — returns to the browser without making any changes.

After a successful import, the favourites list, scheduled-recording station list, and timer station list are all refreshed automatically.

### Reordering Favourites

With a station selected in the Favourites tab, press `comma` to enter move mode — you will hear a beep. Navigate to the target position with the arrow keys, then press `comma` again. The station is placed at the chosen position and the new order is saved immediately. Pressing `comma` again at the same position cancels the move.

### Direct Keyboard Shortcuts for Favourite Stations

Every station in your favourites list is registered as a separate script in NVDA's Input Gestures dialog, under the **FreeRadio Stations** category. You can assign any keyboard shortcut to any station and press it from anywhere — no need to open the browser window first.

To assign a shortcut:

1. Open NVDA Menu → Preferences → Input Gestures.
2. Expand the **FreeRadio Stations** category.
3. Find the station by name, select it, and press **Add**.
4. Press the desired key combination and confirm.

The shortcut activates the station immediately. If the station is later removed from your favourites, its entry disappears from the category and any shortcut assigned to it is automatically cleared by NVDA. When a new station is added to favourites, it appears in the category straight away — the Input Gestures dialog does not need to be reopened.

### Adding a Custom Station

To add a station that is not in Radio Browser, use the Add Custom Station button. In the dialog that appears, enter the station name and stream URL to add it directly to your favourites. Custom stations can be played and reordered just like any other favourite.

Two additional buttons are available in this dialog:

- **Test URL** — checks the stream URL you've entered before adding the station, and announces whether it is reachable. Useful for catching a typo or a dead link before it ends up in your favourites list.
- **Add to Radio Browser directory…** — opens the [Radio Browser submission page](https://www.radio-browser.info/add) in your default browser, so you can share the station with the wider Radio Browser community once you've confirmed it works. See [Adding a Station to Radio Browser](#adding-a-station-to-radio-browser) above for what the submission form expects.

### Station Audio Profile

The Favourites tab includes two buttons for managing per-station audio settings:

**Save Audio Profile for This Station** — saves the current volume level, active effects (chorus, EQ, etc.), and EQ gain values as a profile tied to that specific station. Whenever that station starts playing, its saved volume, effects and gain settings are automatically applied, overriding the global defaults.

**Clear Audio Profile** — removes the saved audio profile from the selected station. After clearing, the station reverts to the global volume, effects and EQ gain settings. This button is only active when the selected station already has a saved profile.

Both buttons are located below the favourites list and are only enabled when a station in the list is selected.

## Music Recognition

Pressing `Ctrl+Win+I` three times triggers Shazam-based music recognition for the currently playing stream. Recognition only starts when no ICY metadata (track info broadcast by the station) is available; if metadata is present, it is copied to the clipboard instead.

Recognition works as follows: a short audio sample is captured from the stream using ffmpeg, the Shazam fingerprinting algorithm is applied, and the result is sent to Shazam's servers. If recognition succeeds, the track title, artist, album and release year are announced by NVDA and automatically copied to the clipboard. If the **Save liked songs to a text file** option is enabled, the recognition result is also appended to `likedSongs.txt`.

**Audio feedback:** Two rising beeps sound when recognition starts, and two falling beeps when it ends. A short beep plays every 2 seconds while the process is running.

**Requirement:** ffmpeg.exe is required. An ffmpeg.exe placed in the add-on folder is used automatically; if it is in a different location, the path can be set in Settings. Download ffmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).

**A note on stations that insert ads:** some stations serve a short ad to every brand-new connection made to their stream, separate from the broadcast you're already listening to. Recognition avoids sampling that ad by reusing FreeRadio's existing background stream connection (the same one used for [Time-Shift](#time-shift-rewind-live-radio)) instead of opening a new one, so it identifies whatever is actually playing rather than an ad. This works automatically and needs no configuration.

## Audio Mirror

The `Ctrl+Win+M` shortcut mirrors the currently playing stream to a second audio output device simultaneously. This is useful for listening on two different devices at the same time, such as speakers and headphones.

On first press, a selection dialog listing the available output devices appears. Once a device is chosen, mirroring begins and main playback continues uninterrupted. Pressing the shortcut again stops mirroring.

**Use cases:**
- **Speakers + headphones** — Let a guest follow the same broadcast on headphones while you listen through the computer speakers.
- **Recording setup** — Route the main output to speakers and the second output to an external recorder or audio interface for external capture.
- **Multi-room** — Play through a Bluetooth speaker and the built-in speaker simultaneously; no extra software needed to carry audio to another room.
- **Remote monitoring** — In a screen-sharing or remote desktop session, both the local and remote sides can hear the same stream simultaneously.

> **Note:** Audio mirroring is only available when the BASS backend is active. If the volume is changed while mirroring is active, both outputs are updated simultaneously.

## Recording

Recordings are saved to `Documents\FreeRadio Recordings\` by default. The filename includes the station name (or song title, in song recording mode) and the recording start time. The recordings folder can be changed at any time from NVDA Menu → Preferences → Settings → FreeRadio → **Recordings folder**. Because the recording engine connects directly to the stream, the audio is written to disk as received — no processing or re-encoding is applied; recording quality is identical to the broadcast quality.

**Instant recording:** While a station is playing, press `Ctrl+Win+E` once. Press again to stop. Playback continues uninterrupted throughout.

**Song recording:** Press `Ctrl+Win+E` **twice** in quick succession while a station that broadcasts ICY metadata is playing. The recording starts immediately and is named after the current track title. When the track changes, the recording stops automatically and NVDA announces the saved filename. If you want to end the recording early before the track finishes, press `Ctrl+Win+E` twice again. If the current station does not broadcast ICY metadata, song recording is not available and NVDA will inform you.

**Scheduled recording:** Open the Recording tab in the browser. Select a station from your favourites, enter the start time in HH:MM format and the duration in minutes, select one or more active days, then choose a recurrence mode and a recording mode:

**Active days:** Check one or more days of the week. In single-recording mode, a separate entry is created for each selected day, each placed on the next upcoming occurrence of that day. In recurring mode, the recording repeats only on the checked days. If no days are checked, the recording is not restricted to specific days.

**Recurrence:**
- **Record once** — records a single time on each selected day. Each entry is placed on the next upcoming occurrence of that day; if the selected time has already passed today, the entry moves to the same day next week automatically.
- **Repeat weekly** — repeats every week on the selected active days until removed from the schedule list.

**Recording mode:**
- **Record while listening** — plays and records simultaneously. A playback backend is started using the BASS → VLC → PotPlayer → Windows Media Player priority order.
- **Record only** — records silently in the background without any audio output; the recording engine connects directly to the stream.

NVDA announces when a recording starts and when it finishes. If NVDA is restarted while a scheduled recording is active, the recording resumes automatically on startup.

Like music recognition, instant and song recording reuse FreeRadio's existing background stream connection when it's available, rather than opening a new one, so a recording captures what's actually airing even on stations that would otherwise serve a fresh ad to a brand-new connection. This does not apply to scheduled **Record only** recordings, since no station is already playing at the time they start.

## Time-Shift (Rewind Live Radio)

Time-shift lets you rewind the station you're currently listening to, like a DVR or a cassette tape — pause the moment, go back a few minutes, and catch up to live again whenever you want. Playback never has to stop for this: rewinding and fast-forwarding both happen instantly on the same audio stream.

This feature is **disabled by default**. Enable it from NVDA Menu → Preferences → Settings → FreeRadio → **Enable time-shift buffer (rewind live radio, ~10 minutes)**, or toggle it instantly at any time with `Ctrl+Win+T`.

> **Note:** FreeRadio now keeps a small background capture of the currently playing station running at all times — not just when this setting is enabled — because [Music Recognition](#music-recognition) and [Recording](#recording) both rely on it for the ad-avoidance behaviour described in those sections. When this setting is **off**, that background capture is kept to about the last 45 seconds and `Ctrl+Win+J`/`Ctrl+Win+K` remain unavailable — only the buffer size changes, not whether it runs. Enabling the setting grows the same capture to the full ~10-minute rewind buffer described below.

### How It Works

Once enabled, FreeRadio continuously captures the currently playing station into a rolling local buffer in the background, independently of normal playback. The buffer holds roughly the **last 10 minutes** of audio; older audio is automatically discarded from the front as new audio arrives, so the buffer always represents "the recent past" relative to the live edge.

- **`Ctrl+Win+J`** — Rewind 15 seconds. The first press switches you from live playback into time-shifted playback, starting 15 seconds behind the live edge. Each further press moves another 15 seconds further back, up to the buffer limit.
- **`Ctrl+Win+K`** — Fast-forward 15 seconds while time-shifted. Once you reach the live edge, playback automatically switches back to the live stream and NVDA announces "Back to live" — you don't need to do anything extra to resume normal listening.
- **`Ctrl+Win+T`** — Turns the whole feature on or off. Turning it off while time-shifted immediately returns you to live playback and stops the background capture for the current station.

Background capture keeps running the entire time you're time-shifted, so the live edge keeps moving forward even while you're listening to something a few minutes old — exactly like a real DVR.

### Enabling and Buffer Warm-Up

The buffer starts filling as soon as a station starts playing (once the feature is enabled) or the moment you enable the feature while already listening to a station. Because of this, rewinding is only possible once a few seconds of audio have actually been captured — if you press `Ctrl+Win+J` immediately after switching stations, NVDA will let you know there isn't enough buffered audio yet. Simply wait a few seconds and try again.

Switching to a different station always restarts the buffer for the new station; the previous station's buffered audio is discarded.

### Supported Streams

Time-shift works with the same range of streams FreeRadio already supports:

- Plain HTTP/HTTPS streams (MP3, AAC, OGG, etc.), including Shoutcast/Icecast-style servers.
- **HLS (`.m3u8`) streams** — FreeRadio resolves the station's master playlist, follows the media playlist, and downloads segments in the background to keep the buffer filled, the same way it works for plain streams.

In the rare case that a station's playlist cannot be read at all (for example, a broken or unreachable `.m3u8` manifest), NVDA will tell you rewinding isn't available for that particular station.

### Requirements and Limitations

- **Requires the BASS backend.** Time-shift is not available when BASS is disabled and playback falls back to VLC, PotPlayer, or Windows Media Player. The background capture itself (and the ad-avoidance it provides to Music Recognition and Recording) is also unavailable in that case, since it depends on the same BASS-based connection.
- The buffer is approximately 10 minutes; you cannot rewind further back than that.
- The buffer is per-station: switching stations, stopping playback, or restarting NVDA clears it and starts fresh.
- Time-shifted playback uses its own local buffer file and does not produce a saved recording — if you want to keep the audio permanently, use Instant Recording (`Ctrl+Win+E`) as well.

## Timer

Open the Timer tab in the station browser (`Alt+4`). Two types of timer can be added:

**Alarm — start radio:** Automatically starts playing a selected station from your favourites at the specified time. Choose a station and enter the time in HH:MM format.

**Sleep — stop radio:** Stops playback at the specified time. When the timer fires, volume is gradually reduced over 60 seconds before playback stops. No station selection is needed; just enter the time.

For both types, if the entered time has already passed the action is scheduled for the following day. Adding a timer is blocked if another timer — of any type — already exists at the same time; a message informs you of the conflict and prompts you to remove the existing entry first. Pending timers are listed in the tab; select one and press the Remove Selected Timer button to cancel it.

## Podcasts

FreeRadio includes a full-featured podcast player. You can subscribe to any RSS or Atom podcast feed, browse episodes, play them, download them, and resume playback from where you left off — all fully accessible.

### Accessing the Podcasts Tab

Open the station browser with `Ctrl+Win+R` and switch to the **Podcasts** tab using `Ctrl+Tab` or `Alt+6`. The tab is organised into three main areas:

1. **Search and add** — top section for discovering new podcasts, including a preview list that shows the episodes of whichever search result is currently selected.
2. **Subscriptions** — list of your subscribed feeds.
3. **Episodes** — list of episodes for the selected feed, with playback controls.

### Adding a Podcast Feed

You can add a podcast feed in two ways:

**By URL:**
- In the **"Or enter podcast URL"** field, paste the full RSS or Atom feed URL (e.g. `https://example.com/feed.xml`).
- Press Enter or click the **Add Feed** button.
- FreeRadio fetches the feed, validates it, and adds it to your subscriptions. If the feed is valid, you will hear a confirmation with the feed title. If it fails, an error message explains why.

**By searching:**
- In the **Search** field, type a keyword (podcast title, topic, or host name) and press Enter.
- FreeRadio searches the iTunes podcast directory and displays matching podcasts in the **Search results** list.
- Selecting a result fetches that feed in the background and lists its episodes in the **Episodes in selected result** list right below, so you can preview what the show actually contains before deciding to subscribe — see [Previewing Episodes Before Subscribing](#previewing-episodes-before-subscribing) below.
- Once you're happy with what you see, select the result and either press `Enter`, or open its context menu (Applications key / `Shift+F10`, or right‑click) and choose **Subscribe**, to add it to your subscriptions. The feed is added immediately and appears in your subscriptions list. There is no separate "Add Selected from Search" button — `Enter` or the context menu is the only way to subscribe from search results, keeping the interface clean and accessible.

> **Tip:** You can also type a feed URL directly into the search field — if it looks like a valid URL, the add‑on will attempt to add it as a feed without searching.

**Context menu for search results:** Right‑click a search result, or select it and press the Applications key / `Shift+F10`, to open a menu with a single **Subscribe** action, identical to pressing `Enter` on the result.

### Previewing Episodes Before Subscribing

Before committing to a subscription, you can listen to a podcast's episodes straight from the search results. Whenever you select a podcast in the **Search results** list, FreeRadio fetches that feed and shows its episodes — title and publish date — in the **Episodes in selected result** list underneath.

- Select an episode in that preview list and press `Enter`, or open its context menu (Applications key / `Shift+F10`, or right‑click) and choose **Preview**, to start playing it through the normal player. All the usual playback controls (pause, volume, time‑shift, etc.) work on it exactly as they would on any other station or episode.
- While an episode is being previewed, the same context menu shows **Stop Preview** in place of **Preview** — choose it, or press `Enter` again on that episode, to stop.
- Previewing does not subscribe you to anything; it's purely for listening before you decide. The preview list itself is temporary — it's replaced as soon as you select a different search result, and it does not persist anywhere the way your actual subscriptions do.

### Managing Subscriptions

Once you have added some feeds, they appear in the **Subscriptions** list. Each entry shows the feed title and the number of episodes available.

- **Select a feed** to see its episodes in the lower list. The **Feed details** read‑only text box below the subscriptions list shows the feed title, author, description, episode count, and URL.
- **Refresh a feed** — select it and press the **Refresh Feed** button (available via context menu, see below) to fetch the latest episodes. All feeds are also refreshed automatically in the background when you open the Podcasts tab, so you usually see the most recent episodes without manual intervention.
- **Remove a feed** — select it and press `Delete` or use the context menu to remove it from your subscriptions. You will be asked for confirmation before removal.

**Context menu for feeds:** Right‑click a feed, or select it and press the Applications key / `Shift+F10`, to open a menu with:
- **Refresh Feed** — fetch new episodes now.
- **Remove Feed** — delete the subscription.
- **Copy Feed URL** — copy the feed URL to the clipboard.

### Browsing and Playing Episodes

Select a feed in the subscriptions list; its episodes appear in the **Episodes** list below. Each episode shows:
- Its episode number (1 = the oldest episode in the feed, counting up to the newest).
- Its publication date (if available).
- Its title.
- A **"Listened"** prefix if the episode has been fully played.
- A duration suffix, either total duration (if never played) or elapsed/total progress (if partially played).

**Playback:**
- Select an episode and press `Enter` or `Space` to start playing it. If an episode was partially played before, it resumes from where you left off.
- The row does *not* update while the episode is playing — this is intentional, so NVDA doesn't repeatedly re-announce the row while you're sitting on it. Its "Listened" flag and duration are refreshed immediately the moment you pause the episode or it finishes playing, so the display is always accurate right when it matters; it simply doesn't tick up second by second during playback.
- Use `F3` / `F4` on the Podcasts tab to move to the previous / next episode and play it immediately. You can also use `←` / `→` while the episode list is focused, or `Ctrl+←` / `Ctrl+→` anywhere on the Podcasts tab — both work identically.
- Use `Shift+F3` / `Shift+F4` to move between feeds without playing episodes.
- Press `Space` while an episode is playing to pause or resume playback.

**Resuming playback:** FreeRadio saves your position in each podcast episode automatically — immediately whenever you pause or the episode finishes, and every 15 seconds in the background while you keep listening, so a crash or unexpected restart won't lose much progress. If you stop or pause playback and come back later, the episode resumes from the saved position. If you play the episode to the very end (within the last 3 seconds), it is marked as "Listened" and will not resume — it starts from the beginning next time, and the "Listened" prefix appears in the list.

**Context menu for episodes:** Right‑click an episode, or select it and press the Applications key / `Shift+F10`, to open a menu with:
- **Play Episode** — start playback.
- **Download Episode** — download the episode file to your recordings folder.
- **Copy Episode URL** — copy the direct audio URL to the clipboard.

### Downloading Episodes

Select an episode and click the **Download Episode** button (or use the context menu). The episode is downloaded to your recordings folder (`Documents\FreeRadio Recordings\` by default). The filename is based on the episode title and the detected file extension (`.mp3`, `.m4a`, `.ogg`, etc.). NVDA announces when the download starts and finishes. If the file already exists, you are informed and the download is skipped.

### Filtering Episodes

Above the episode list is a **Filter** field. As you type, the episode list is filtered in real time to show episodes whose title contains the typed text, or whose episode number matches it exactly — so typing `47` jumps straight to episode 47 even if "47" doesn't appear anywhere in its title. NVDA announces the number of matching episodes after each change. Press the `Down` arrow from the filter field to move focus directly into the filtered list.

### Podcast Playback Details

Podcast episodes are played using the **BASS backend** (the same engine used for radio streams). Because episodes are downloaded progressively and are seekable, you can use the time-shift rewind/forward shortcuts (`Ctrl+Win+J`/`Ctrl+Win+K`) while playing a podcast to jump back or forward **5 seconds** at a time (instead of the 15‑second rewind used for live radio). The position is saved automatically so you can resume later.

If the BASS backend is disabled (or fails), podcast playback falls back to the same chain of external players (VLC → PotPlayer → WMP) used for radio, but **seek and resume functionality will not work** in that case — the episode will play from the beginning each time. For the full podcast experience, keep the BASS backend enabled.

### Podcast Data Storage

Your subscriptions are stored in `freeradio_podcasts.json` in the NVDA user configuration folder. Episode positions are stored separately in `podcast_positions.json` in the same location. Both files are plain JSON and can be backed up or transferred to another computer.

## Liked Songs

When the **Save liked songs to a text file** option is enabled, track info copied to the clipboard by pressing `Ctrl+Win+I` three times is also appended line by line to `Documents\FreeRadio Recordings\likedSongs.txt`.

On stations that broadcast ICY metadata, the track title and artist are saved directly. On stations without ICY metadata, the Shazam recognition result is saved to the same file — both sources share the same list. The file is created automatically if it does not exist; each entry is appended to the end of the file and previous entries are never deleted.

## Liked Songs Tab

The **Liked Songs** tab in the station browser displays all tracks saved in `likedSongs.txt`. The list is automatically reloaded from the file each time the tab is opened.

A **Filter** field above the list lets you narrow the displayed tracks in real time. Type any part of a song title or artist name and the list updates instantly on every keystroke. NVDA announces the number of matching results after each change. Press the `Down` arrow from the filter field to move focus directly into the list.

Selecting a track from the list enables the following actions:

- **Play on Spotify:** Tries to open the Spotify desktop app directly. If the app is not installed, falls back to the Spotify website and automatically starts playing the first result.
- **Play on YouTube (`Alt+O`):** Searches YouTube for the selected track and opens the results in the default browser.
- **Show Lyrics:** Fetches and displays the lyrics for the selected track. Lyrics are retrieved from [lrclib.net](https://lrclib.net) (free, no account required). A short "Fetching lyrics…" message is announced while the search runs in the background. If lyrics are found, they open in a read-only dialog where you can read them with NVDA and copy them to the clipboard. If no lyrics are found, NVDA announces this. The button is temporarily disabled while a fetch is in progress to prevent duplicate requests.
- **Remove (`Alt+M`):** Deletes the selected track from `likedSongs.txt` and updates the list. The `Delete` key also triggers this button when the list is focused.
- **Refresh (`Alt+E`):** Reloads the list from the file.

The Spotify, YouTube, Show Lyrics, and Remove buttons are only enabled when a real track is selected in the list.

### Lyrics Service

FreeRadio uses [lrclib.net](https://lrclib.net) to fetch lyrics — a free, open database that requires no API key or account. The lookup process parses the track string stored in `likedSongs.txt` and tries progressively looser queries until lyrics are found:

1. Exact match using the full artist name and cleaned title (noise suffixes such as "Remastered", "Live", or year tags are stripped before searching).
2. Exact match using the full artist name and the original title (if cleaning changed it).
3. Exact match using only the first artist name and the cleaned title (for multi-artist strings such as "Artist A & Artist B").
4. Fuzzy search using the first artist name and the cleaned title.
5. Fuzzy search using the raw track string as a last resort.

When plain lyrics are available they are shown as-is. When only time-synced LRC lyrics are available, the timestamps are stripped and the plain text is shown. Instrumental tracks are reported as not found.

## Settings

The following options can be configured from NVDA Menu → Preferences → Settings → FreeRadio:

| Option | Description |
|---|---|
| Audio output device (BASS backend) | Sets the audio output device for radio playback. The list includes all BASS-compatible devices on the system plus a "System default" option. Changes are applied immediately on save; if the selected device is disconnected, the add-on automatically falls back to the system default and announces the change. Only active when the BASS backend is in use. |
| Audio device refresh mode (BASS backend) | Controls how FreeRadio refreshes BASS output-device numbers. **Reliable** mode (default) probes devices live and tracks Bluetooth/USB changes more accurately, but can make device changes slightly slower. **Fast** mode uses the current BASS device list and is quicker, but device numbers may stay stale until BASS or NVDA is restarted. |
| Volume | Sets the add-on's starting volume (0–200). Changes made during playback with `Ctrl+Win+↑` / `Ctrl+Win+↓` are also reflected here. |
| Default audio effect | Sets the audio effect applied when NVDA starts or a station begins playing. The selected effect corresponds to the Effects list in the Station Browser. Only active when the BASS backend is in use. |
| EQ gain (Bass / Treble / Vocal) | Sets the gain level in dB for each EQ band (−15 to +15). These values apply when the corresponding EQ effect is active and are saved globally. Per-station overrides can be stored using the **Save Audio Profile** button in the Favourites tab. Only active when the BASS backend is in use. |
| Station switch transition (BASS backend) | Controls the transition behaviour when switching between stations. **Instant cut** (default) stops the previous station immediately before the new one starts. **Short crossfade (1 second)** and **Normal crossfade (2 seconds)** start the new station immediately with no gap, then gradually fade out the previous station in the background once the new stream is confirmed active. **Station tuning sound effect** stops the previous station immediately and plays a station tuner sound effect before the new one starts. Has no effect and no performance impact when set to Instant cut. Only available when the BASS backend is in use. |
| Resume last station on NVDA startup | When enabled, the last played station automatically restarts every time NVDA starts. |
| Auto-announce track changes (ICY metadata) | When enabled, NVDA automatically reads the new track name each time it changes on a station that broadcasts ICY metadata. The first track is also announced immediately when switching to a new station. Disabled by default. |
| Mute notifications | When enabled, NVDA does not announce station changes, playback state changes (play, pause, stop), or recording events (started, stopped, finished). Error messages, favourites feedback, music recognition results, and update notifications are not affected. Can also be toggled on the fly via an unassigned input gesture. Disabled by default. |
| Braille messages | When enabled, FreeRadio also sends its notifications directly to the braille display. This is useful for track titles, station changes, playback state and volume changes. Disabled by default. |
| Enable time-shift buffer (rewind live radio, ~10 minutes) | Turns the rewind controls (`Ctrl+Win+J`/`Ctrl+Win+K`) on or off and grows the background capture from ~45 seconds up to ~10 minutes. A small background capture of the currently playing station always runs, even when this is off — see the note in the **Time-Shift** section below. Can also be toggled instantly with `Ctrl+Win+T`. Requires the BASS backend. Disabled by default — see the **Time-Shift** section below for full details. |
| Save liked songs to a text file | When enabled, track info copied to the clipboard by pressing `Ctrl+Win+I` three times is also appended to `Documents\FreeRadio Recordings\likedSongs.txt`. If no ICY metadata is available, the Shazam recognition result is saved to the same file. Disabled by default. |
| When Ctrl+Win+P is pressed with no active playback | Determines what happens when this shortcut is pressed and nothing is playing: start the last station or open the favourites list. |
| When Ctrl+Win+P is pressed twice | Selects what happens when the shortcut is pressed twice in quick succession: do nothing, open the favourites list, open the recording tab or open the timer tab. When "do nothing" is selected, the first press responds instantly with no delay. |
| When Ctrl+Win+P is pressed three times | Selects what happens when the shortcut is pressed three times in quick succession: do nothing, open the favourites list, open station search, open the recording tab or open the timer tab. |
| Check for updates automatically | When enabled, a background update check runs each time NVDA starts; you are notified if a new version is found. When disabled, automatic checks stop but manual checks remain available. |
| ffmpeg.exe path | Path to the ffmpeg.exe used for music recognition. If left blank, an ffmpeg.exe in the add-on folder is used automatically. |
| VLC path | If VLC is not installed or is in a non-standard location, the full path to the executable can be entered here. |
| wmplayer.exe path | Enter the path to Windows Media Player here if needed. |
| PotPlayer path | If PotPlayer is in a non-standard location, its path can be entered here. |
| Recordings folder | Sets the folder where recorded files are saved. If left blank, the default location `Documents\FreeRadio Recordings\` is used. A Browse button lets you select the folder interactively. Changes take effect immediately after saving. |
| Disable internet connectivity check before playing | Recommended for users who experience a delay before a station starts playing. Also useful when DNS is blocked. |

## Mute Notifications

When **Mute notifications** is enabled in Settings, NVDA silences the following automatic announcements:

- Station name when a new station starts playing
- Playback state changes: play, pause, stop
- Recording events: started, stopped, finished (instant, song and scheduled recordings)
- ICY track change announcements, even when **Auto-announce track changes** is also enabled

The following announcements are intentionally **not** affected: error messages, favourites feedback (added / already in list), music recognition results, and update notifications.

The setting can be toggled from NVDA Menu → Preferences → Settings → FreeRadio, or instantly at any time via an unassigned input gesture (assign one from NVDA Menu → Preferences → Input Gestures → FreeRadio). When toggled, NVDA announces "Notifications muted" or "Notifications unmuted" once to confirm the change.

## Auto-announce Track Changes

When the **Auto-announce track changes** option is enabled in Settings, FreeRadio checks the active station's ICY metadata stream in the background approximately every 5 seconds. When the track changes, the new title is automatically read by NVDA — no keypress required.

When switching to a new station, the first track info is announced as soon as the connection is established. If you switch to a station that does not broadcast ICY metadata, the system stays silent and the previous station's track info is not repeated.

This feature is disabled by default and can be toggled from NVDA Menu → Preferences → Settings → FreeRadio.

## Playback

The add-on selects a playback backend using the following priority order:

1. **BASS** — the default and primary backend. No separate installation is required; it is bundled with the add-on. BASS sends audio directly to the Windows audio stack and appears in the Windows volume mixer as an independent audio source named "pythonw.exe", separate from NVDA. This means FreeRadio audio flows on a completely separate channel from NVDA speech: the radio does not cut out, mix with, or get affected by NVDA's own audio settings while NVDA is speaking. The user can adjust the radio volume independently from NVDA in the Windows Volume Mixer. Supports HTTP, HTTPS and most embedded stream formats. Audio mirroring and podcast seek/resume are only available with this backend.
2. **VLC** — takes over if BASS fails. Searched automatically in common installation locations, user profile folders and the system PATH.
3. **PotPlayer** — tried if VLC is not found. Searched automatically in common installation locations.
4. **Windows Media Player** — used as a last resort; requires the WMP component to be installed on the system.

Podcast episodes are always played through BASS if available, because BASS can open the stream as a seekable file (even while downloading) and allows precise position tracking and resuming. If BASS is disabled, podcasts fall back to the external player chain, but seek and resume will not work.

## Update Check

FreeRadio automatically checks for new versions via GitHub.

**Automatic check:** Runs silently in the background 15 seconds after NVDA starts. If a new version is found, you are notified; if none is found, no message is shown.

**Manual check:** Can be triggered on demand from NVDA Tools → FreeRadio → **Check for Updates…**. When started this way, the result is announced even if the version is up to date.

**When an update is found:** A dialog opens showing the version number and your installed version.

- If a directly downloadable `.nvda-addon` file is available on the GitHub release, a **Download and Install** button is shown. Once confirmed, the file is downloaded in the background, NVDA announces when the download starts, and NVDA's own installation screen opens automatically.
- If no direct download link is available, an **Open Page** button is shown and the GitHub release page opens in the default browser.

**To disable automatic checks:** Turn off the **Check for updates automatically** option from NVDA Menu → Preferences → Settings → FreeRadio.

## License

GPL v2