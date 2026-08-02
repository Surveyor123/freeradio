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
	addon_version="2026.21.1",
	
	# Brief changelog for this version
	# Translators: what's new content for the add-on version
	addon_changelog=_("""
- Add braille messages and improve BASS device handling 
**TimeShift fixes**
- **Time-shift buffer could get stuck reporting "not enough buffered audio" indefinitely.** Restarting the buffer's capture session (on station switch, on a BASS stall reconnect, and when toggling the rewind feature on) happened without any coordination between those three code paths. If two of them landed close together — most commonly a fast station switch overlapping with the buffer still starting up for the previous station — they could race, and the buffer could end up capturing one station while its internal generation counter pointed at another. Rewind would then refuse with "not enough buffered audio" no matter how long you waited, since nothing made the two ever match again on its own; switching stations or toggling the rewind setting off and back on happened to reset the counters and mask the problem. A shared lock now serializes these restart sequences and re-validates the current station right before acting, so a stale restart can no longer overwrite a newer one.
- **Rewinding, then pausing for a while, then resuming broke further navigation.** On resume after a pause longer than ~10 seconds, playback always reconnected to the live stream, but the internal "time-shifted" flag was never cleared to match. The app kept behaving as if playback was still reading from the local buffer file, so subsequent rewind/fast-forward presses tried to seek inside a stream that could no longer be seeked, and silently did nothing — matching the reported behavior where navigation stopped working until the buffer was toggled off/on. The long-pause reconnect path now resets that state the same way a genuine station relaunch already did.
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