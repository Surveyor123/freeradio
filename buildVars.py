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
	addon_description=_("""FreeRadio is an internet radio, podcast, and audio-book add-on for NVDA that provides seamless access to thousands of internet radio stations via the Radio Browser open directory, RSS/Atom podcast feeds, and the libriVox + GETEM digital library for the visually impaired. It features a fully accessible station browser with search, country filter, favourites management, and per-station, per-podcast, and per-audio-book audio profiles. Podcast episodes and audio book chapters resume automatically from where you left off, with adjustable pitch-preserving playback speed. Playback is handled by a prioritised backend chain (BASS, VLC, PotPlayer, Windows Media Player) with support for volume control, audio effects, output device selection, and simultaneous audio mirroring to a second device. Additional features include instant and scheduled recording, time-shift rewind of live radio, sleep and alarm timers, automatic ICY metadata announcements, Shazam-based music recognition, and a liked-songs log with lyrics lookup. All controls and shortcuts are designed for NVDA accessibility."""),
	
	# version
	addon_version="2026.23.4",
	
	# Brief changelog for this version
	# Translators: what's new content for the add-on version
	addon_changelog=_("""
- Removed VLC / PotPlayer / Windows Media Player fallback support. BASS is
now the sole, mandatory playback backend. This removes the "Disable BASS
backend" option and its VLC/wmplayer/PotPlayer path settings from the
FreeRadio settings panel; if BASS itself fails to start, playback now
fails with a clear error instead of silently switching to another
player.
- Internal cleanup: removed unused code paths and a dead
"player_paths" field from scheduled recordings that was never actually
used for playback.
- **Seeking within a podcast or audio book now supports tap-to-jump amounts:** a single press seeks 12 seconds, two quick presses seek 1 minute, three quick presses seek 5 minutes. Holding the key down still seeks continuously in the original 5-second steps, unchanged.
**Improved**
- Station search now also matches on **codec**, **bitrate**, and **language**, in addition to name, country, and tags. For example, searching "aac" or "320" now finds stations using that codec or bitrate, and results can be combined with other terms (e.g. "jazz 320"). Partialy closing #30
Add a new source for audio books
- Added LibriVox as a second audio book source alongside GETEM. Both catalogs now share the same Audio Books tab: search, browse, play, and resume progress work the same way regardless of which source a book came from.
- Searching the Audio Books tab now queries GETEM and LibriVox together, and results from both are combined into a single list.
- Pasting a LibriVox or Getem book URL directly into the search field now resolves and adds that book.
- Added an "Audio book sources" option to the settings panel: a checkbox list lets you choose which of GETEM and LibriVox are searched (both are enabled by default).
- **GETEM catalog & detail-page parsing: replaced regex scraping with a real DOM parser**
The HTML-scraping code that read GETEM's search results and work-detail pages relied on regexes over raw HTML and a literal string split to find each result row. That approach breaks silently the moment the site changes something cosmetic — element order, an extra wrapper tag, a label nested one level deeper — without changing what the page actually means.
Replaced it with a small, dependency-free DOM builder on top of Python's standard `html.parser.HTMLParser`, then rewrote every scraping function to query that tree by tag/class instead of matching raw markup:
- **Catalog search results**: each result row is now parsed as its own real subtree, so a field missing from one row can no longer leak text belonging to the next row — a risk the old row-splitting approach carried.
- **Format-filter options, hidden form fields**: read directly from parsed `<select>`/`<option>` elements instead of locating them by substring search.
- **Work-detail pages**: chapter links, title, and metadata fields (author/narrator/publisher/etc.) are now found by walking the tree rather than requiring an exact tag sequence; a field's own label text is excluded via nesting-depth-independent lookup instead of an assumed fixed `</div></div>` boundary.
- **URL resolution**: relative/absolute link handling now goes through `urllib.parse.urljoin`, which correctly covers protocol-relative and query-only links the old hand-written checks didn't.
- No public function signatures changed, so nothing else in the add-on needed touching. Verified against hand-built fixtures covering the exact failure modes the old code was vulnerable to (reordered attributes, div/span markup variance, a field missing mid-listing, a link wrapped in an extra tag, a deeply nested label) — all resolved correctly.
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