# -*- coding: utf-8 -*-
# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries
from site_scons.site_tools.NVDATool.utils import _

# Add-on information variables
addon_info = AddonInfo(
	# add-on Name/identifier, internal for NVDA
	addon_name="freeradio",
	
	# Add-on summary/title, usually the user visible name of the add-on
	# Translators: Summary/title for this add-on
	addon_summary=_("freeRadio"),
	
	# Add-on description
	# Translators: Long description to be shown for this add-on
	addon_description=_("""FreeRadio is an internet radio add-on for NVDA that provides seamless access to thousands of stations via the Radio Browser open directory. It features a fully accessible station browser with search, country filter, favourites management, and per-station audio profiles. Playback is handled by a prioritised backend chain (BASS, VLC, PotPlayer, Windows Media Player) with support for volume control, audio effects, output device selection, and simultaneous audio mirroring to a second device. Additional features include instant and scheduled recording, sleep and alarm timers, automatic ICY metadata announcements, Shazam-based music recognition, and a liked-songs log. All controls and shortcuts are designed for NVDA accessibility."""),
	
	# version
	addon_version="2026.23.0",
	
	# Brief changelog for this version
	# Translators: what's new content for the add-on version
	addon_changelog=_("""
## Audio Books (GETEM)
- Added a new **Audio Books** tab (`Alt+7`) powered by [GETEM](https://getem.boun.edu.tr/), Boğaziçi University's digital library for the visually impaired — the first to be supported audio book sources.
- Search GETEM's catalogue by title, author, narrator, subject, or publisher; results are automatically filtered to audio-only formats (human/computer narration, audio description, radio drama, DAISY talking books, etc.).
- Preview any search result before committing to it, or add it straight to a personal library.
- Multi-part works are handled as a single library entry: playback automatically resumes from the last part and position you left off on, even across NVDA restarts.
- Play audio books through the same BASS-backed player used for radio and podcasts, with full support for pause/resume, volume, time-shift, playback speed, and output device selection.
- Download an entire book — all parts, correctly numbered and named — to your recordings folder for offline listening.
- GETEM sign-in credentials are stored encrypted on disk (Windows Data Protection API) and entered once from FreeRadio's Settings panel.
- Fixed duplicate/repeated audio in recordings and Time-Shift on HLS streams that rotate session tokens in their segment URLs.
## Fixed:
- Cleaned up leftover time-shift buffer files (`freeradio_timeshift_*.buf`) from previous sessions on startup. These are normally deleted when time-shift capture stops cleanly, but an abrupt shutdown (crash, power loss, Windows force-closing NVDA) would skip that step and leave the file in the temp folder — these could accumulate over time, especially with longer buffer durations. The add-on now clears out any matching leftover files each time it starts, before any new capture session begins.
- Podcast playback speed reverting to normal (1.0x) after switching episodes or resuming from pause. The chosen speed is now resent to the audio engine every time a podcast stream is (re)started, so it stays in effect across episode changes, pause/resume, and station-transition effects (crossfade/tuning) instead of silently resetting.
## Fixed
- Fixed a bug where playing a podcast episode could cause a temporary buffer file (`freeradio_timeshift_*.buf` in the system temp folder) to grow to several gigabytes within minutes, potentially filling up the disk.
  - The time-shift (rewind) capture — designed for continuous live radio streams — was also being started for on-demand podcast/audio book playback. Since those sources can be read far faster than real-time the buffer's time-based trimming couldn't keep up, and each time a chapter finished downloading it was mistaken for a dropped connection and re-downloaded into the same file instead of being cleaned up.
  - The time-shift buffer is no longer started for podcasts or audio books at all — they already support proper rewind/fast-forward/resume through their own seekable file playback, so nothing is lost.
  - Live radio time-shift/rewind behavior is unaffected.
## Fixed
- **Recording no longer stops when playback changes.** Instant and song-capture
  recordings were tied to the main player's shared time-shift buffer as an
  optimisation to avoid capturing a freshly-inserted ad on a brand-new
  connection. That buffer is a single instance shared by the whole player, so
  switching stations (or resuming after a long pause) silently cut off any
  recording that was reading from it. Recordings now always open their own
  independent connection, so switching stations, pausing/resuming, or
  stopping playback no longer affects an active recording. The now-unused
  buffer-tailing code path was removed.
- **Scheduled recordings no longer report false success.** If a station's
  stream failed to connect for an entire scheduled recording window, the
  add-on still announced "Recording started" and, at the end, "Recording
  finished" — with no file ever written. A scheduled recording that never
  connects now reports a failure instead of a false "finished" notification.
## Changed (internal, no functional impact)
`__init__.py` has been split from a single ~4,200-line file into ten focused
modules, each ~100–400 lines. `GlobalPlugin` itself is now under 300 lines
containing only setup/teardown and script routing; everything else is a mixin
NVDA's script discovery picks up through normal class inheritance, so all
keyboard shortcuts and default gestures behave exactly as before.

| File | Contents |
--|---|
| `settingsPanel.py` | The NVDA Settings → FreeRadio panel |
| `timerManager.py` | Sleep/alarm timer scheduling |
| `audioDeviceMixin.py` | Output device selection, audio mirroring |
| `playbackCoreMixin.py` | Pause/resume, stop, next/prev station |
| `timeshiftMixin.py` | Rewind/fast-forward, time-shift toggle |
| `audioFxMixin.py` | Volume, EQ/bass/treble/vocal boost, crossfade, playback rate |
| `recordingMixin.py` | Instant recording toggle, recordings folder, podcast download |
| `trackInfoMixin.py` | "What's playing", station details, track info, ICY polling |
| `miscTogglesMixin.py` | Notification mute, BASS backend, track-change announce/voice, liked songs |
"""),
	
	# Author(s)
	addon_author="Çağrı Doğan <cagrid@hotmail.com>",
	
	# URL for the add-on documentation support
	addon_url="https://github.com/Surveyor123/freeradio",
	
	# URL for the add-on repository where the source code can be found
	addon_sourceURL="https://github.com/Surveyor123/freeradio",
	
	# Documentation file name
	addon_docFileName="readme.html",
	
	# Minimum NVDA version supported
	addon_minimumNVDAVersion="2024.1.0",
	
	# Last NVDA version supported/tested
	addon_lastTestedNVDAVersion="2026.1.1",
	
	# Add-on update channel (None denotes stable releases)
	addon_updateChannel=None,
	
	# Add-on license
	addon_license="GPL-2.0",
	addon_licenseURL=None,
)

# Define the python files that are the sources of your add-on.
# We point to the specific directory where your code lives.
pythonSources: list[str] = ["addon/globalPlugins/freeradio/*.py"]

# Files that contain strings for translation. Usually your python sources
i18nSources: list[str] = pythonSources + ["buildVars.py"]

# Files that will be ignored when building the nvda-addon file
excludedFiles: list[str] = []

# Base language for the NVDA add-on
# Since your code strings (e.g. _("Table")) are in English, we keep this as "en".
baseLanguage: str = "en"

# Markdown extensions for add-on documentation
markdownExtensions: list[str] = []

# Custom braille translation tables
brailleTables: BrailleTables = {}

# Custom speech symbol dictionaries
symbolDictionaries: SymbolDictionaries = {}