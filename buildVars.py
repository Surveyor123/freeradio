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
	addon_description=_("""FreeRadio is an internet radio, podcast, and audio-book add-on for NVDA that provides seamless access to thousands of internet radio stations via the Radio Browser open directory, RSS/Atom podcast feeds, and the GETEM digital library for the visually impaired. It features a fully accessible station browser with search, country filter, favourites management, and per-station, per-podcast, and per-audio-book audio profiles. Podcast episodes and audio book chapters resume automatically from where you left off, with adjustable pitch-preserving playback speed. Playback is handled by a prioritised backend chain (BASS, VLC, PotPlayer, Windows Media Player) with support for volume control, audio effects, output device selection, and simultaneous audio mirroring to a second device. Additional features include instant and scheduled recording, time-shift rewind of live radio, sleep and alarm timers, automatic ICY metadata announcements, Shazam-based music recognition, and a liked-songs log with lyrics lookup. All controls and shortcuts are designed for NVDA accessibility."""),
	
	# version
	addon_version="2026.23.3",
	
	# Brief changelog for this version
	# Translators: what's new content for the add-on version
	addon_changelog=_("""
**Security**
- Certificate verification for streaming connections (live playback, recording, and time-shift) is now enabled by default, closing a gap where every station's stream could previously be intercepted or substituted without warning. Stations with known broken/expired certificates automatically fall back to an unverified connection so they keep working — nothing else changes for those stations, and only they pay a small extra delay the first time they're opened each session.
**Fixed**
- **Audio books:** Fixed a rare timing issue where, right as one chapter finished and the next was about to start automatically, playback could occasionally jump backward to an already-heard chapter instead of continuing forward. Most noticeable during long unattended listening sessions.
- **Scheduled recordings:** Recurring recordings now recover much more reliably after your PC wakes from sleep or when NVDA was closed for a while:
  - A missed recurring recording on a multi-day schedule (e.g. Mon/Wed/Fri) no longer skips ahead by a full week — it correctly finds the next eligible day.
  - Old, incorrectly saved schedule dates from earlier versions are automatically fixed on load — no need to recreate them.
  - If a recording's start was delayed (e.g. by sleep), it now records only the time actually remaining in its original window, instead of starting a full-length recording late.
  - Schedule data is now saved more safely, preventing rare cases of a damaged or incomplete schedule file.
  - While a scheduled recording is in progress, Windows is prevented from going into idle sleep automatically.
**Added**
- New keyboard shortcuts for quick access:
  - `Ctrl+Windows+L` — jumps straight to the Audio Books tab (focus on your library).
  - `Ctrl+Windows+O` — jumps straight to the Podcasts tab (focus on your subscriptions).
  - Both open the FreeRadio window if it's closed, or bring it to the front if it's already open.
- More audio profile options when saving a profile for a podcast or audiobook: **Volume and playback speed**, **Effects and playback speed**, and **Playback speed only**, alongside the existing Volume only / Effects only / Volume and effects / Volume, effects, and playback speed choices.
- The **Save Audio Profile for This Podcast** and **Clear Audio Profile** commands are now also available from the episode context menu, so you don't need to switch back to the podcast list to reach them. They still apply to the whole podcast, not to a single episode.

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