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
	addon_version="2026.23.5",
	
	# Brief changelog for this version
	# Translators: what's new content for the add-on version
	addon_changelog=_("""
### Added
- **Obligato mode (background music)** — Play a favourite station quietly in the background, on its own independent audio output and volume, no matter what plays (or doesn't play) as the main media.
  - New shortcut: `Ctrl+Win+Shift+M` toggles Obligato mode on and off.
  - On first press, a dialog lets you choose the background station (from your favourites), the output device (**Same as main output** by default, **System default**, or any specific device), and the background volume as a percentage of the main player's current volume (25%–150%). Your choices are remembered for next time.
  - Runs on a fully separate playback engine from the main player, so switching stations, podcasts, or audio books — or stopping the main player entirely — never interrupts it.
  - Background volume automatically stays proportional to the main player's volume as it changes (`Ctrl+Win+↑`/`↓`).
  - Pausing the main player (`Ctrl+Win+P`) pauses the background station too, and resuming the main player resumes it; a full stop of the main player is not treated as a pause.
  - Requires at least one favourite station; if none exist, FreeRadio prompts you to add one first.
  - Start/stop announcements respect the **Mute notifications** setting.
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