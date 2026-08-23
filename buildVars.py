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
	addon_version="2026.23.2",
	
	# Brief changelog for this version
	# Translators: what's new content for the add-on version
	addon_changelog=_("""
## scheduled recording fixes
**Fixed**
- Recurring scheduled recordings would only fire once and never repeat correctly.
  - Fixed a thread-safety race where the scheduler loop's per-second cleanup of the schedule list could silently drop a freshly re-queued recurring recording before it was ever saved or checked.
  - Fixed date calculation for recurring schedules: the next occurrence was always computed a full week ahead before checking active days, so a schedule set to record every day (e.g. daily at 09:00) actually only re-fired once a week on the original weekday. It now correctly schedules the very next matching day.
**Note**
- Existing entries in `freeradio_schedules.json` created before this fix may still hold a `start_time` computed by the old logic (a week ahead). Recreate those schedules, or manually correct their `start_time`, to get correct daily firing going forward.
## Fixes for chapter Auto-advance and playback speed
**Bug Fix — Audio Book Chapter Auto-Advance Stopped When FreeRadio Window Was Closed**
- Fixed an issue where an audio book would correctly move to its next chapter when it finished playing while the FreeRadio window was open on the Audio Books tab, but silently stopped at the end of a chapter instead of advancing if the window was closed or hidden.
- Chapter auto-advance no longer depends on the FreeRadio dialog being open: it now runs independently in the background, using the finished chapter's own book/part information to look up the next chapter and start it directly.
- Progress tracking (which chapter/part you're on) is now saved correctly even while advancing in the background.
- When the FreeRadio window is reopened, its "now playing" state (used by F3/F4 chapter/book navigation) is refreshed from the player, so it correctly reflects a book that kept advancing while the window was closed.
**Bug Fix — Playback Speed Leaking Between Audio Books/Podcasts**
- Fixed an issue where saving an audio profile with a sped-up playback rate (e.g. 1.4x) for one book, then switching to another book with no saved profile, would leave the second book playing at the first book's speed instead of normal speed.
- Playback speed now follows the same rule already used for volume/effects/EQ: if the book or podcast being played has a saved profile with a speed, that speed is applied; otherwise, speed resets to normal (1.0x) rather than carrying over from whatever was played previously.
- Arabic localization update
## startup resume fixes
**Bug Fix — Audio Profile Not Applied on Startup Resume**
- Fixed an issue where a saved audio profile (volume/effects/EQ/speed) for a podcast or audio book was applied correctly when starting playback from the dialog, but was ignored when the station resumed automatically on NVDA startup.
- Playing a podcast episode now also records which feed it belongs to; playing an audio book chapter already recorded which book it belongs to.
- On startup resume:
  - For audio books, the saved book profile is now looked up and applied together with the rebuilt playback URL.
  - For podcast episodes, the subscribed feed is looked up independently (without needing the dialog open) and its saved profile, if any, is applied the same way.
- As a result, resumed playback on NVDA startup now respects the same volume, effects, EQ, and playback speed settings as playback started manually from the dialog.
## Recording tab rearrangements and audio profiles for podcasts and audio books
**Recording Tab**
- Removed the "Edit" and "Remove" buttons; their functionality moved into the list's context menu (Applications key / Shift+F10).
- Delete / Shift+Delete now removes the selected schedule directly.
- Default mode is now "Record only".
- After removing a schedule, the next item in the list (or the previous one, if it was the last) is automatically selected.
**Podcast and Audio Book Tabs**
- F3 / F4 / Shift+F3 / Shift+F4 now also move keyboard focus to the relevant list (previously they only changed the selection).
- On the Audio Book tab, since there's no separate list item for chapters, changing chapters moves focus to the book's row in the library list instead.
- Delete / Shift+Delete in the Audio Book library list now removes the selected book directly (previously only available via the context menu).
**Audio Profiles — Podcast and Audio Book Support**
- The audio profile feature (volume/effects/EQ) from Favorites has been extended to podcast feeds and audio book library entries:
  - Podcasts: the profile is saved on the feed and applies to **all of its episodes**.
  - Audio Books: the profile is saved on the book and applies to **all of its chapters**.
- Profiles can now also include **playback speed** (for podcast/audiobook content only); a new "Volume, effects, and playback speed" option captures the current speed when saving.
- Episodes/chapters without a saved profile keep whatever playback speed is currently active (sticky) rather than being forced back to normal speed.
- Added "Save Audio Profile" / "Clear Audio Profile" items to the context menus (Podcast: subscriptions list; Audio Book: library list).
- When unsubscribing from a podcast or removing a book from the library:
  - The saved audio profile is automatically cleared.
  - The resume ("where you left off") positions for all of that feed's episodes / that book's chapters are also cleared.
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