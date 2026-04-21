# FreeRadio — NVDA Add-on

FreeRadio is an internet radio add-on for the NVDA screen reader. Its primary goal is to give users easy access to thousands of internet radio stations. The entire interface and all features have been designed with full accessibility for NVDA in mind.

## Radio Browser Directory

FreeRadio uses the [Radio Browser](https://www.radio-browser.info/) open database for its station catalogue. Radio Browser is a community-managed, free directory hosting more than 50,000 internet radio stations from around the world. No registration or account is required and its API is open to everyone. Each station includes address, country, genre, language and bitrate information; stations are ranked by user votes. FreeRadio connects to this API through mirror servers located in Germany, the Netherlands and Austria; if one server is unreachable, it automatically switches to the next.

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
| `Ctrl+Win+↑` | Volume up | Increases volume by 10; maximum 100. |
| `Ctrl+Win+↓` | Volume down | Decreases volume by 10; minimum 0. |
| `Ctrl+Win+V` | Add to favourites | Adds the currently playing station to the favourites list. Announces if the station is already in the list. |
| `Ctrl+Win+I` | Station info | Announces the currently playing station name. Press twice to show details such as country, genre and bitrate in a dialog. Press three times to copy the current track info (ICY metadata) to the clipboard if available; if no metadata is present, starts Shazam music recognition instead. |
| `Ctrl+Win+M` | Audio mirror | Mirrors the current stream to an additional audio output device simultaneously. Press again to stop mirroring. |
| `Ctrl+Win+E` | Instant recording | Starts recording the current station. Press again to stop; playback continues uninterrupted. |
| `Ctrl+Win+W` | Open recordings folder | Opens the folder containing recorded files in File Explorer. |

Next / previous shortcuts only navigate the favourites list; they do not work with the all stations list. When a list is focused in the browser window, the left and right arrow keys serve the same purpose — see In-Dialog Shortcuts.

## Station Browser

FreeRadio also adds a **FreeRadio** submenu to the NVDA Tools menu. From there you can directly open the Station Browser and FreeRadio Settings.

The window opened with `Ctrl+Win+R` contains four tabs: All Stations, Favourites, Recording and Timer. You can navigate between tabs with `Ctrl+Tab`.

When the All Stations tab opens, the top 1,000 most-voted stations are automatically loaded from Radio Browser. Selecting a country from the dropdown updates the list to show that country's stations. Typing in the search field instantly filters the loaded list; pressing `Enter` or the Search button performs a full search across the entire Radio Browser database simultaneously by name, country and genre.

The **Output Device** dropdown at the bottom of the browser window — outside the tabs — lists all BASS-recognised audio output devices. Selecting a device immediately redirects audio output to it and saves the choice permanently; the same device is used automatically in the next session. If the selected device is not connected, the add-on falls back to the system default automatically. This control is only functional when the BASS backend is active.

The **Volume** (0–200) and **Effects** controls in the same area can be adjusted at any time while the window is open. From the Effects list, Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb, EQ: Bass Boost, EQ: Treble Boost and EQ: Vocal Boost can be enabled simultaneously; changes are applied to the active stream instantly. These controls are fully functional only when the BASS backend is active.

The **Play/Pause** button is also located at the bottom of the window. If no station is playing it starts the selected station; if a station is already playing it pauses playback.

When a station is selected in the list, the **Station Details** button displays information such as country, language, genre, format, bitrate, website and stream URL in a separate dialog. Each field appears in its own read-only text box; you can move between fields with Tab and copy all information to the clipboard at once with the **Copy all to clipboard** button. This button is available in both the All Stations and Favourites tabs.

### In-Dialog Shortcuts

The following keys work only while the Station Browser window is active.

### F Keys

| Shortcut | Function | Description |
|---|---|---|
| `F1` | Help guide | Opens the add-on's help file in the default browser. The guide for the active NVDA language is searched first; if not found, the default guide is opened. |
| `F2` | Now playing | Announces the current station name and ICY metadata track info if available. |
| `F3` | Previous station | Moves to the previous station in the All Stations or Favourites tab and starts playing immediately. Jumps to the end when at the beginning of the list. |
| `F4` | Next station | Moves to the next station in the All Stations or Favourites tab and starts playing immediately. Wraps to the beginning at the end of the list. |
| `F5` | Volume down | Decreases volume by 10 (minimum 0). |
| `F6` | Volume up | Increases volume by 10 (maximum 200). |
| `F7` | Pause / resume | Pauses if a station is playing; resumes if paused and media is loaded. |
| `F8` | Stop | Fully stops the current station and resets the player. |

### List and Navigation Shortcuts

| Shortcut | Function | Description |
|---|---|---|
| `→` | Next station | When the All Stations or Favourites list is focused, moves to the next station and plays it immediately. Wraps to the beginning at the end of the list. |
| `←` | Previous station | When the All Stations or Favourites list is focused, moves to the previous station and plays it immediately. Jumps to the end when at the beginning. |
| `Enter` | Play | When the All Stations or Favourites list is focused, starts playing the selected station immediately. Switches to the selected station even if another station is already playing. |
| `Space` | Play / Pause | Pauses if a station is playing; otherwise starts playing the selected station. |
| `Ctrl+Tab` | Next tab | Switches to the next tab (All Stations → Favourites → Recording → Timer). |
| `Ctrl+Shift+Tab` | Previous tab | Returns to the previous tab. |
| `Escape` | Hide | Hides the window; the add-on continues playing in the background. |

### Volume Shortcuts

| Shortcut | Function | Description |
|---|---|---|
| `Ctrl+↑` | Volume up | Increases volume by 10. Only works while the browser window is open. |
| `Ctrl+↓` | Volume down | Decreases volume by 10. Only works while the browser window is open. |

### Alt Key Shortcuts

| Shortcut | Function | Description |
|---|---|---|
| `Alt+R` | Go to search field | Moves focus to the search text box. |
| `Alt+A` | Search online | Searches Radio Browser with the text in the search field; name, country and genre are searched simultaneously. |
| `Alt+V` | Add / remove favourite | Adds the selected station to favourites; removes it if already in the list. |
| `Alt+T` | All Stations | Switches to the All Stations tab. |
| `Alt+F` | Favourites | Switches to the Favourites tab and focuses the list. |
| `Alt+Y` | Recording | Switches to the Recording tab. |
| `Alt+Z` | Timer | Switches to the Timer tab. |
| `Alt+K` | Close | Closes the window; the add-on continues playing in the background. |

## Favourites

The favourites list is a personal station collection stored permanently. To add a station, select it in the list and press the Add to Favourites button or use the `Alt+V` shortcut. The same shortcut removes a station that is already in the list when it is selected.

Favourites can be played with `Ctrl+Win+→` and `Ctrl+Win+←`; these shortcuts work even when the browser window is not open.

### Reordering Favourites

With a station selected in the Favourites tab, press `X` to enter move mode — you will hear a beep. Navigate to the target position with the arrow keys, then press `X` again. The station is placed at the chosen position and the new order is saved immediately. Pressing `X` again at the same position cancels the move.

### Adding a Custom Station

To add a station that is not in Radio Browser, use the Add Custom Station button. In the dialog that appears, enter the station name and stream URL to add it directly to your favourites. Custom stations can be played and reordered just like any other favourite.

### Station Audio Profile

The Favourites tab includes two buttons for managing per-station audio settings:

**Save Audio Profile for This Station** — saves the current volume level and active effects (chorus, EQ, etc.) as a profile tied to that specific station. Whenever that station starts playing, its saved volume and effects are automatically applied, overriding the global defaults.

**Clear Audio Profile** — removes the saved audio profile from the selected station. After clearing, the station reverts to the global volume and effects settings. This button is only active when the selected station already has a saved profile.

Both buttons are located below the favourites list and are only enabled when a station in the list is selected.

## Music Recognition

Pressing `Ctrl+Win+I` three times triggers Shazam-based music recognition for the currently playing stream. Recognition only starts when no ICY metadata (track info broadcast by the station) is available; if metadata is present, it is copied to the clipboard instead.

Recognition works as follows: a short audio sample is captured from the stream using ffmpeg, the Shazam fingerprinting algorithm is applied, and the result is sent to Shazam's servers. If recognition succeeds, the track title, artist, album and release year are announced by NVDA and automatically copied to the clipboard. If the **Save liked songs to a text file** option is enabled, the recognition result is also appended to `likedSongs.txt`.

**Audio feedback:** Two rising beeps sound when recognition starts, and two falling beeps when it ends. A short beep plays every 2 seconds while the process is running.

**Requirement:** ffmpeg.exe is required. An ffmpeg.exe placed in the add-on folder is used automatically; if it is in a different location, the path can be set in Settings. Download ffmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).

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

Recordings are saved to `Documents\FreeRadio Recordings\` by default. The filename includes the station name and recording start time. The recordings folder can be changed at any time from NVDA Menu → Preferences → Settings → FreeRadio → **Recordings folder**. Because the recording engine connects directly to the stream, the audio is written to disk as received — no processing or re-encoding is applied; recording quality is identical to the broadcast quality.

**Instant recording:** While a station is playing, press `Ctrl+Win+E`. Press again to stop. Playback continues uninterrupted throughout.

**Scheduled recording:** Open the Recording tab in the browser. Select a station from your favourites, enter the start time in HH:MM format and the duration in minutes, then choose a recording mode:

- **Record while listening** — plays and records simultaneously. A playback backend is started using the BASS → VLC → PotPlayer → Windows Media Player priority order.
- **Record only** — records silently in the background without any audio output; the recording engine connects directly to the stream.

If the entered time has already passed, the recording is scheduled for the following day. NVDA announces when a recording starts and when it finishes.

## Timer

Open the Timer tab in the station browser (`Alt+Z`). Two types of timer can be added:

**Alarm — start radio:** Automatically starts playing a selected station from your favourites at the specified time. Choose a station and enter the time in HH:MM format.

**Sleep — stop radio:** Stops playback at the specified time. When the timer fires, volume is gradually reduced over 60 seconds before playback stops. No station selection is needed; just enter the time.

For both types, if the entered time has already passed the action is scheduled for the following day. Pending timers are listed in the tab; select one and press the Remove Selected Timer button to cancel it.

## Settings

The following options can be configured from NVDA Menu → Preferences → Settings → FreeRadio:

| Option | Description |
|---|---|
| Audio output device (BASS backend) | Sets the audio output device for radio playback. The list includes all BASS-compatible devices on the system plus a "System default" option. Changes are applied immediately on save; if the selected device is disconnected, the add-on automatically falls back to the system default and announces the change. Only active when the BASS backend is in use. |
| Volume | Sets the add-on's starting volume (0–200). Changes made during playback with `Ctrl+Win+↑` / `Ctrl+Win+↓` are also reflected here. |
| Default audio effect | Sets the audio effect applied when NVDA starts or a station begins playing. The selected effect corresponds to the Effects list in the Station Browser. Only active when the BASS backend is in use. |
| Resume last station on NVDA startup | When enabled, the last played station automatically restarts every time NVDA starts. |
| Auto-announce track changes (ICY metadata) | When enabled, NVDA automatically reads the new track name each time it changes on a station that broadcasts ICY metadata. The first track is also announced immediately when switching to a new station. Disabled by default. |
| Save liked songs to a text file | When enabled, track info copied to the clipboard by pressing `Ctrl+Win+I` three times is also appended to `Documents\FreeRadio Recordings\likedSongs.txt`. If no ICY metadata is available, the Shazam recognition result is saved to the same file. Disabled by default. |
| When Ctrl+Win+P is pressed with no active playback | Determines what happens when this shortcut is pressed and nothing is playing: start the last station or open the favourites list. |
| When Ctrl+Win+P is pressed twice | Selects what happens when the shortcut is pressed twice in quick succession: do nothing, open the favourites list, open the recording tab or open the timer tab. When "do nothing" is selected, the first press responds instantly with no delay. |
| When Ctrl+Win+P is pressed three times | Selects what happens when the shortcut is pressed three times in quick succession: do nothing, open the favourites list, open the search tab, open the recording tab or open the timer tab. |
| ffmpeg.exe path | Path to the ffmpeg.exe used for music recognition. If left blank, an ffmpeg.exe in the add-on folder is used automatically. |
| VLC path | If VLC is not installed or is in a non-standard location, the full path to the executable can be entered here. |
| wmplayer.exe path | Enter the path to Windows Media Player here if needed. |
| PotPlayer path | If PotPlayer is in a non-standard location, its path can be entered here. |
| Recordings folder | Sets the folder where recorded files are saved. If left blank, the default location `Documents\FreeRadio Recordings\` is used. A Browse button lets you select the folder interactively. Changes take effect immediately after saving. |

## Auto-announce Track Changes

When the **Auto-announce track changes** option is enabled in Settings, FreeRadio checks the active station's ICY metadata stream in the background approximately every 5 seconds. When the track changes, the new title is automatically read by NVDA — no keypress required.

When switching to a new station, the first track info is announced as soon as the connection is established. If you switch to a station that does not broadcast ICY metadata, the system stays silent and the previous station's track info is not repeated.

This feature is disabled by default and can be toggled from NVDA Menu → Preferences → Settings → FreeRadio.

## Liked Songs

When the **Save liked songs to a text file** option is enabled, track info copied to the clipboard by pressing `Ctrl+Win+I` three times is also appended line by line to `Documents\FreeRadio Recordings\likedSongs.txt`.

On stations that broadcast ICY metadata, the track title and artist are saved directly. On stations without ICY metadata, the Shazam recognition result is saved to the same file — both sources share the same list. The file is created automatically if it does not exist; each entry is appended to the end of the file and previous entries are never deleted.

## Playback

The add-on selects a playback backend using the following priority order:

1. **BASS** — the default and primary backend. No separate installation is required; it is bundled with the add-on. BASS sends audio directly to the Windows audio stack and appears in the Windows volume mixer as an independent audio source named "pythonw.exe", separate from NVDA. This means FreeRadio audio flows on a completely separate channel from NVDA speech: the radio does not cut out, mix with, or get affected by NVDA's own audio settings while NVDA is speaking. The user can adjust the radio volume independently from NVDA in the Windows Volume Mixer. Supports HTTP, HTTPS and most embedded stream formats. Audio mirroring is only available with this backend.
2. **VLC** — takes over if BASS fails. Searched automatically in common installation locations, user profile folders and the system PATH.
3. **PotPlayer** — tried if VLC is not found. Searched automatically in common installation locations.
4. **Windows Media Player** — used as a last resort; requires the WMP component to be installed on the system.

## License

GPL v2
