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
	addon_description=_("""FreeRadio is an internet radio, podcast, and audio-book add-on for NVDA that provides seamless access to thousands of internet radio stations via the Radio Browser open directory, RSS/Atom podcast feeds, and the libriVox + GETEM digital library for the visually impaired. It features a fully accessible station browser with search, country filter, favourites management, and per-station, per-podcast, and per-audio-book audio profiles. Podcast episodes and audio book chapters resume automatically from where you left off, with adjustable pitch-preserving playback speed. Playback is handled by BASS, with support for volume control, audio effects, output device selection, and simultaneous audio mirroring to a second device. Additional features include instant and scheduled recording, time-shift rewind of live radio, sleep and alarm timers, automatic ICY metadata announcements, Shazam-based music recognition, and a liked-songs log with lyrics lookup. All controls and shortcuts are designed for NVDA accessibility."""),
	
	# version
	addon_version="2026.24.0",
	
	# Brief changelog for this version
	# Translators: what's new content for the add-on version
	addon_changelog=_("""
## New features:
- Local Jukebox tab: search audio files stored on any attached drive by filename, or build a persistent personal library of files and folders. Jukebox tracks get the same treatment as podcasts and audio books: automatic resume, tiered rewind/fast-forward, playback speed, pitch transpose, and per-item audio profiles. Open the Jukebox tab from anywhere with Ctrl+Win+U, or from the Station Browser with Alt+8.
- Transpose (pitch shift): shift the pitch of podcasts, audio books, and jukebox tracks up or down without changing their speed, using Shift+Win+K (raise) and Shift+Win+J (lower). Each step is one eighth of a whole tone (0.25 semitones); the range is -12.00 to +12.00 semitones. Requires bass_fx.dll.
- Jukebox tab keyboard shortcuts: F3 / F4 move between tracks within the selected jukebox item; Shift+F3 / Shift+F4 move between jukebox entries; Ctrl+Left / Ctrl+Right do the same as F3 / F4 while the tracks or entries list is focused. Space previews a disk-search result or pauses the current playback; Enter adds a disk-search result to the jukebox or plays the focused item directly.

Improvements:
- Playback speed shortcuts (Ctrl+Win+Shift+K / Ctrl+Win+Shift+J) now also apply to jukebox tracks, not just podcasts and audio books.
- Ctrl+Win+V (Add to Favourites / Download Media) now tells the user explicitly that the shortcut only applies to stations, podcasts, and audio books when a jukebox track is currently playing, instead of silently treating the jukebox track as a station.
- The Station Browser now contains eight tabs instead of seven; tab navigation shortcuts run from Alt+1 through Alt+8.
- Ctrl+Tab / Ctrl+Shift+Tab tab cycling now includes the Jukebox tab.
- Ctrl+Win+I (What's playing) now also announces jukebox track names.
- Ctrl+Win+J and Ctrl+Win+K (tiered seek) now also work on jukebox tracks.
- Ctrl+Win+T (Toggle time-shift buffer) now clarifies that it has no effect on podcast, audio book, or jukebox playback.
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
	addon_minimumNVDAVersion="2025.1.0",
	
	# Last NVDA version supported/tested
	addon_lastTestedNVDAVersion="2026.2.0",
	
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