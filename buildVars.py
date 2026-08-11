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
	addon_version="2026.22.0",
	
	# Brief changelog for this version
	# Translators: what's new content for the add-on version
	addon_changelog=_("""
## Podcasts (New)
FreeRadio now includes a full-featured, fully accessible podcast player.
- **Subscribe to any podcast** — by pasting a direct RSS/Atom feed URL, or by searching the iTunes podcast directory by title, topic, or host name.
- **Preview before subscribing** — selecting a search result loads its episode list (titles and publish dates) so you can hear what the show is about before committing; preview episodes play through the normal player and can be stopped from the same context menu.
- **Manage subscriptions** — refresh a feed for new episodes, remove a subscription, or copy its feed URL, all from a context menu (Applications key / `Shift+F10`, or right-click). Feeds also refresh automatically in the background when you open the tab.
- **Browse and play episodes** — each episode shows its publish date, title, a "Listened" marker once fully played, and its duration (or elapsed/total progress if partially played). Play, pause, and resume with `Enter`/`Space`; jump between episodes with `F3`/`F4`, or between feeds with `Shift+F3`/`Shift+F4`.
- **Resume where you left off** — playback position is saved automatically, immediately on pause or when an episode finishes, and periodically in the background while listening, so you never lose much progress even after a crash or restart.
- **Filter episodes** — type in the filter field to narrow a feed's episode list in real time; NVDA announces the match count.
- **Download episodes** — save any episode to your recordings folder for offline listening.
- **Podcast-aware time-shift** — rewind/fast-forward 5 seconds at a time within an episode using the existing time-shift shortcuts (`Ctrl+Win+J`/`Ctrl+Win+K`).
- Runs on the BASS backend for seekable, resumable playback; falls back to the existing external-player chain (VLC → PotPlayer → WMP) if BASS is unavailable, though seek/resume won't work in that case.
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