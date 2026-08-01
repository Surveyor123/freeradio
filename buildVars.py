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
	addon_version="2026.21.0",
	
	# Brief changelog for this version
	# Translators: what's new content for the add-on version
	addon_changelog=_("""
**Fixed**
- **ICY "Now Playing" titles containing an apostrophe were truncated.** The `StreamTitle` regex in `radioPlayer.py` stopped at the first `'` it found, so any title with an apostrophe (e.g. *"Don't Stop Believin'"*) was cut short. The parser now matches up to the closing `';` delimiter that ICY metadata actually uses, so apostrophes inside the title no longer break the match.
- Added: **Liked song context menu (Liked Songs Tab)**
- Right-click a station (or press the Applications key / Shift+F10) to bring up a new context menu with quick actions
- Fixed: rewind/fast-forward stopped working after pausing and resuming
  playback. Pausing and resuming advanced the internal playback generation
  counter twice without re-syncing the time-shift buffer's own counter,
  so the buffer was permanently (and incorrectly) treated as stale for
  the rest of the session.
- Fixed: on HLS (.m3u8) stations, rewinding or fast-forwarding could land
  at the wrong point in time, and the "N seconds behind live" readout
  could show inconsistent or even negative values. The buffered-duration
  estimate was based on wall-clock time since capture started, which
  drifts from the actual amount of audio captured on HLS stations
  (manifest polling delays, segment-fetch latency, and bursty catch-up
  downloads all throw it off). Buffered duration for HLS is now computed
  from each segment's own declared duration, matching what is actually
  in the buffer.

- Improved: trimming the old end of an HLS time-shift buffer now always
  drops whole segments instead of an estimated byte count, avoiding a
  rare risk of cutting a segment in half and producing a corrupt tail.
- **Time-shift (rewind) buffer could silently stop engaging, even after re-enabling it.** `rewind_timeshift()` gates on two internal generation counters staying in sync; a few code paths (station launch, resume-from-pause, a successful stall reconnect) correctly re-synced them, but `set_timeshift_enabled()` did not. If playback generation advanced elsewhere (e.g. a brief stream stall/reconnect) without a matching sync, rewind would permanently report "not enough buffered audio," regardless of wait time, and toggling time-shift off/on for the same station could not fix it — only switching stations (which goes through the syncing path) sometimes did. `set_timeshift_enabled()` now re-syncs the buffer generation after (re)starting capture, closing that gap.
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