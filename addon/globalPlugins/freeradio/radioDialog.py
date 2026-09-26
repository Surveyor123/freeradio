# -*- coding: utf-8 -*-
# FreeRadio - Station Browser Dialog
# Initial UI event handling patterns and dialog base inspired by work by Gary Mp (GaryMp/freeradio).

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
# ngettext is injected by initTranslation alongside _; capture it the same way.
ngettext = globals().get("ngettext", lambda s, p, n: s if n == 1 else p)

import config
import datetime
import os
import re
import sys
import threading
import time
import ui
import wx
import winsound
import gui
from . import podcast
from . import getem
from . import librivox
from . import gutenberg_audiobooks
from . import jukebox
import urllib.parse
import urllib.request
from gui import nvdaControls
from html import unescape

_ = _tr
del _tr

# --- Native multi-folder picker -------------------------------------------------
# wx.DirDialog has no multi-select mode (unlike wx.FileDialog's FD_MULTIPLE), so
# to give jukebox folder-adding the same "pick several, confirm once" experience
# as file-adding, we call the Windows Common Item Dialog (IFileOpenDialog) with
# FOS_PICKFOLDERS | FOS_ALLOWMULTISELECT directly via comtypes. This dialog has
# no ready-made comtypes/pywin32 wrapper, so the interfaces are declared here by
# hand from the documented vtable layout. If anything about this fails on a given
# system (missing comtypes, a COM error, etc.), callers fall back to looping
# wx.DirDialog, so this is a pure enhancement and never a hard requirement.
_SIGDN_FILESYSPATH = 0x80058000
_FOS_PICKFOLDERS = 0x00000020
_FOS_FORCEFILESYSTEM = 0x00000040
_FOS_ALLOWMULTISELECT = 0x00000200
# HRESULT for "the user closed the dialog without making a selection".
_ERROR_CANCELLED_HRESULT = -2147023673  # HRESULT_FROM_WIN32(ERROR_CANCELLED), i.e. 0x800704C7


def _build_ifileopendialog_classes():
	"""Builds and returns the (IFileOpenDialog, CLSID_FileOpenDialog) pair used by
	_pick_folders_native(). Kept in its own function so any failure to import
	comtypes, or to build these interfaces, is an ordinary exception the caller
	can catch, rather than breaking this module for every other feature at
	import time."""
	import comtypes
	from comtypes import GUID, COMMETHOD, IUnknown
	from ctypes import HRESULT, POINTER, c_void_p, c_int, c_uint, c_ulong, c_wchar_p
	from ctypes.wintypes import DWORD, HWND

	class IModalWindow(IUnknown):
		_iid_ = GUID("{B4DB1657-70D7-485E-8E3E-6FCB5A5C1802}")
		_methods_ = [
			COMMETHOD([], HRESULT, "Show", (["in"], HWND, "hwndOwner")),
		]

	class IShellItem(IUnknown):
		_iid_ = GUID("{43826D1E-E718-42EE-BC55-A1E261C37BFE}")
		_methods_ = [
			COMMETHOD(
				[], HRESULT, "BindToHandler",
				(["in"], POINTER(IUnknown), "pbc"),
				(["in"], POINTER(GUID), "bhid"),
				(["in"], POINTER(GUID), "riid"),
				(["out"], POINTER(c_void_p), "ppv"),
			),
			COMMETHOD([], HRESULT, "GetParent", (["out"], POINTER(POINTER(IUnknown)), "ppsi")),
			COMMETHOD(
				[], HRESULT, "GetDisplayName",
				(["in"], c_int, "sigdnName"),
				(["out"], POINTER(c_wchar_p), "ppszName"),
			),
			COMMETHOD(
				[], HRESULT, "GetAttributes",
				(["in"], c_ulong, "sfgaoMask"),
				(["out"], POINTER(c_ulong), "psfgaoAttribs"),
			),
			COMMETHOD(
				[], HRESULT, "Compare",
				(["in"], POINTER(IUnknown), "psi"),
				(["in"], c_uint, "hint"),
				(["out"], POINTER(c_int), "piOrder"),
			),
		]

	class IShellItemArray(IUnknown):
		_iid_ = GUID("{B63EA76D-1F85-456F-A19C-48159EFA858B}")
		_methods_ = [
			COMMETHOD(
				[], HRESULT, "BindToHandler",
				(["in"], POINTER(IUnknown), "pbc"),
				(["in"], POINTER(GUID), "bhid"),
				(["in"], POINTER(GUID), "riid"),
				(["out"], POINTER(c_void_p), "ppvOut"),
			),
			COMMETHOD(
				[], HRESULT, "GetPropertyStore",
				(["in"], c_int, "flags"),
				(["in"], POINTER(GUID), "riid"),
				(["out"], POINTER(c_void_p), "ppv"),
			),
			COMMETHOD(
				[], HRESULT, "GetPropertyDescriptionList",
				(["in"], POINTER(GUID), "keyType"),
				(["in"], POINTER(GUID), "riid"),
				(["out"], POINTER(c_void_p), "ppv"),
			),
			COMMETHOD(
				[], HRESULT, "GetAttributes",
				(["in"], c_int, "AttribFlags"),
				(["in"], c_ulong, "sfgaoMask"),
				(["out"], POINTER(c_ulong), "psfgaoAttribs"),
			),
			COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(DWORD), "pdwNumItems")),
			COMMETHOD(
				[], HRESULT, "GetItemAt",
				(["in"], DWORD, "dwIndex"),
				(["out"], POINTER(POINTER(IShellItem)), "ppsi"),
			),
			COMMETHOD([], HRESULT, "EnumItems", (["out"], POINTER(POINTER(IUnknown)), "ppenumShellItems")),
		]

	class IFileDialog(IModalWindow):
		_iid_ = GUID("{42F85136-DB7E-439C-85F1-E4075D135FC8}")
		_methods_ = [
			COMMETHOD(
				[], HRESULT, "SetFileTypes",
				(["in"], c_uint, "cFileTypes"),
				(["in"], c_void_p, "rgFilterSpec"),
			),
			COMMETHOD([], HRESULT, "SetFileTypeIndex", (["in"], c_uint, "iFileType")),
			COMMETHOD([], HRESULT, "GetFileTypeIndex", (["out"], POINTER(c_uint), "piFileType")),
			COMMETHOD(
				[], HRESULT, "Advise",
				(["in"], POINTER(IUnknown), "pfde"),
				(["out"], POINTER(DWORD), "pdwCookie"),
			),
			COMMETHOD([], HRESULT, "Unadvise", (["in"], DWORD, "dwCookie")),
			COMMETHOD([], HRESULT, "SetOptions", (["in"], DWORD, "fos")),
			COMMETHOD([], HRESULT, "GetOptions", (["out"], POINTER(DWORD), "pfos")),
			COMMETHOD([], HRESULT, "SetDefaultFolder", (["in"], POINTER(IShellItem), "psi")),
			COMMETHOD([], HRESULT, "SetFolder", (["in"], POINTER(IShellItem), "psi")),
			COMMETHOD([], HRESULT, "GetFolder", (["out"], POINTER(POINTER(IShellItem)), "ppsi")),
			COMMETHOD([], HRESULT, "GetCurrentSelection", (["out"], POINTER(POINTER(IShellItem)), "ppsi")),
			COMMETHOD([], HRESULT, "SetFileName", (["in"], c_wchar_p, "pszName")),
			COMMETHOD([], HRESULT, "GetFileName", (["out"], POINTER(c_wchar_p), "pszName")),
			COMMETHOD([], HRESULT, "SetTitle", (["in"], c_wchar_p, "pszTitle")),
			COMMETHOD([], HRESULT, "SetOkButtonLabel", (["in"], c_wchar_p, "pszText")),
			COMMETHOD([], HRESULT, "SetFileNameLabel", (["in"], c_wchar_p, "pszLabel")),
			COMMETHOD([], HRESULT, "GetResult", (["out"], POINTER(POINTER(IShellItem)), "ppsi")),
			COMMETHOD(
				[], HRESULT, "AddPlace",
				(["in"], POINTER(IShellItem), "psi"),
				(["in"], c_int, "fdap"),
			),
			COMMETHOD([], HRESULT, "SetDefaultExtension", (["in"], c_wchar_p, "pszDefaultExtension")),
			COMMETHOD([], HRESULT, "Close", (["in"], HRESULT, "hr")),
			COMMETHOD([], HRESULT, "SetClientGuid", (["in"], POINTER(GUID), "guid")),
			COMMETHOD([], HRESULT, "ClearClientData"),
			COMMETHOD([], HRESULT, "SetFilter", (["in"], POINTER(IUnknown), "pFilter")),
		]

	class IFileOpenDialog(IFileDialog):
		_iid_ = GUID("{D57C7288-D4AD-4768-BE02-9D969532D960}")
		_methods_ = [
			COMMETHOD([], HRESULT, "GetResults", (["out"], POINTER(POINTER(IShellItemArray)), "ppenum")),
			COMMETHOD([], HRESULT, "GetSelectedItems", (["out"], POINTER(POINTER(IShellItemArray)), "ppsai")),
		]

	clsid_file_open_dialog = GUID("{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}")
	return comtypes, IFileOpenDialog, IShellItem, clsid_file_open_dialog


def _pick_folders_native(parent, title):
	"""Shows the native Windows "pick folders" dialog with multi-select enabled
	and returns a list of the chosen folder paths (empty if the user cancelled).
	Returns None - rather than raising - if the native dialog could not be used
	at all on this system, so callers know to fall back to another approach."""
	try:
		comtypes, IFileOpenDialog, IShellItem, clsid_file_open_dialog = _build_ifileopendialog_classes()
		dialog = comtypes.CoCreateInstance(
			clsid_file_open_dialog, interface=IFileOpenDialog, clsctx=comtypes.CLSCTX_INPROC_SERVER
		)
		options = dialog.GetOptions()
		dialog.SetOptions(options | _FOS_PICKFOLDERS | _FOS_FORCEFILESYSTEM | _FOS_ALLOWMULTISELECT)
		dialog.SetTitle(title)
		try:
			hwnd = parent.GetHandle()
		except Exception:
			hwnd = 0
		try:
			dialog.Show(hwnd)
		except comtypes.COMError as e:
			if e.hresult == _ERROR_CANCELLED_HRESULT:
				return []
			raise
		results = dialog.GetResults()
		count = results.GetCount()
		paths = []
		for i in range(count):
			item = results.GetItemAt(i)
			paths.append(item.GetDisplayName(_SIGDN_FILESYSPATH))
		return paths
	except Exception:
		return None

# stationManager is part of this package; We cannot do relative import because
# radioDialog is loaded directly as a module. We get it from sys.modules.
# If it is not loaded yet (theoretical) we use the Exception base class.
def _get_radio_browser_error():
	for key, mod in sys.modules.items():
		if key.endswith("stationManager") and hasattr(mod, "RadioBrowserError"):
			return mod.RadioBrowserError
	return Exception

def _notify(msg):
	"""Proxy to the package-level _notify in __init__.py.

	Fetched lazily via sys.modules to avoid a circular import.
	Falls back to ui.message when the plugin module is not yet loaded.
	"""
	for key, mod in sys.modules.items():
		if key.endswith("freeradio") and not key.endswith(("radioDialog", "stationManager", "utils", "radioPlayer", "recorder", "musicRecognizer")):
			fn = getattr(mod, "_notify", None)
			if callable(fn):
				fn(msg)
				return
	ui.message(msg)

_RadioBrowserError = None  # Determined at first use

def _radio_browser_error():
	global _RadioBrowserError
	if _RadioBrowserError is None:
		_RadioBrowserError = _get_radio_browser_error()
	return _RadioBrowserError


def _build_folder_picker(parent, sizer, initial_folder=""):
	"""Build the per-schedule "save recording to" controls: a default/custom
	radio pair, a path field, and a Browse... button. Shared by the Add
	Schedule panel and EditScheduleDialog so both stay in sync.

	Returns (default_rb, custom_rb, path_ctrl, browse_btn).
	"""
	sizer.Add(
		# Translators: Label above the folder-choice controls for where a recording will be saved (shared by the Add Schedule panel and EditScheduleDialog).
		wx.StaticText(parent, label=_("Save recording to:")),
		0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
	)
	default_rb = wx.RadioButton(
		# Translators: Radio button: save this recording to FreeRadio's default recordings folder.
		parent, label=_("&Default recordings folder"), style=wx.RB_GROUP,
	)
	# Translators: Radio button: save this recording to a specific folder chosen below.
	custom_rb = wx.RadioButton(parent, label=_("&Selected folder:"))
	sizer.Add(default_rb, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
	sizer.Add(custom_rb,  0, wx.LEFT | wx.RIGHT | wx.TOP, 4)

	path_row  = wx.BoxSizer(wx.HORIZONTAL)
	path_ctrl = wx.TextCtrl(parent, value=initial_folder)
	# Translators: Accessible name for the custom-folder path field (same text as its radio-button label above).
	path_ctrl.SetName(_("Selected folder:"))
	# Translators: Button label; opens a folder-picker to choose where to save this recording.
	browse_btn = wx.Button(parent, label=_("Bro&wse..."))
	path_row.Add(path_ctrl, 1, wx.RIGHT, 4)
	path_row.Add(browse_btn, 0)
	sizer.Add(path_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

	has_custom = bool(initial_folder.strip())
	custom_rb.SetValue(has_custom)
	default_rb.SetValue(not has_custom)
	path_ctrl.Enable(has_custom)
	browse_btn.Enable(has_custom)

	def _on_mode_changed(event):
		enabled = custom_rb.GetValue()
		path_ctrl.Enable(enabled)
		browse_btn.Enable(enabled)
		event.Skip()

	def _on_browse(event):
		dlg = wx.DirDialog(
			# Translators: Title of the folder-picker dialog used by the Browse button next to a custom recordings-folder path.
			parent, _("Select recordings folder"),
			defaultPath=path_ctrl.GetValue().strip(),
		)
		try:
			if dlg.ShowModal() == wx.ID_OK:
				path_ctrl.SetValue(dlg.GetPath())
				custom_rb.SetValue(True)
				path_ctrl.Enable(True)
				browse_btn.Enable(True)
		finally:
			dlg.Destroy()

	default_rb.Bind(wx.EVT_RADIOBUTTON, _on_mode_changed)
	custom_rb.Bind(wx.EVT_RADIOBUTTON,  _on_mode_changed)
	browse_btn.Bind(wx.EVT_BUTTON,      _on_browse)

	return default_rb, custom_rb, path_ctrl, browse_btn


def _folder_picker_value(custom_rb, path_ctrl):
	"""Return the output_folder string to persist: "" selects the global
	default; otherwise the folder the user chose/typed."""
	return path_ctrl.GetValue().strip() if custom_rb.GetValue() else ""


from .utils import (
	country_name,
	country_name   as _country_name,
	station_label  as _station_label,
	first_tag      as _first_tag,
	tr_sort_key    as _tr_sort_key,
	matches_query  as _matches_query,
	_COUNTRY_NAMES,
	_NAME_TO_CODE,
	name_to_code,
)




def _matches_favorites_term(s, term):
	"""Does a single search *term* match *s*, either the way the shared
	matches_query() does (name/tags/etc.) or against s's "group" field
	(the M3U group-title/folder a favourite was imported under, or one
	assigned by hand via Assign to Group)? Display only - never touches
	station["name"] itself.
	"""
	if _matches_query(s, term):
		return True
	group = (s.get("group") or "").strip()
	return bool(group) and term.lower() in group.lower()


def _matches_favorites_query(s, query):
	"""Match the favourites filter box's *query* against *s*.

	The query is split on whitespace into separate terms so a group name
	and part of a station name can be typed together and each match a
	different field - e.g. "NPR News" finds "NPR Newscast" (group "NPR",
	name contains "News") even though "NPR News" never appears as one
	contiguous phrase anywhere. Every term must match somewhere (AND
	across terms); a single-word query behaves exactly as before.
	Only used for the Favourites tab; every other list is unaffected.
	"""
	terms = query.split()
	if not terms:
		return True
	return all(_matches_favorites_term(s, term) for term in terms)


def check_stream_url(url, timeout=8):
	"""Probe *url* and return (ok: bool, detail: str).

	Resolves playlists (.m3u/.pls/ASX) to their first stream URL, then
	attempts a HEAD/GET to verify the endpoint responds with an audio
	content-type.  Runs synchronously; call from a worker thread.

	Returns:
	    (True,  resolved_url)   – reachable audio stream
	    (False, error_message)  – unreachable or non-audio response
	"""
	import urllib.request as _req
	import urllib.error   as _err
	from urllib.parse import urljoin as _urljoin

	if not url or not url.strip():
		# Translators: Error returned by check_stream_url() when the URL field was left blank.
		return False, _("URL is empty.")

	url = url.strip()

	# --- playlist resolution (same logic as radioPlayer._resolve_playlist_url) ---
	try:
		req = _req.Request(
			url,
			headers={"User-Agent": "FreeRadio-NVDA/1.0", "Icy-MetaData": "1"},
		)
		with _req.urlopen(req, timeout=timeout) as resp:
			final_url = resp.url if hasattr(resp, "url") else url
			ct = (resp.headers.get("content-type") or "").lower().split(";")[0].strip()
			data = resp.read(8192).decode("utf-8", "ignore")

		audio_types = ("audio/", "application/ogg", "video/")
		if any(ct.startswith(t) for t in audio_types):
			return True, final_url

		# Playlist containers
		base = final_url
		if ct in ("audio/x-mpegurl", "application/x-mpegurl",
		          "audio/mpegurl", "application/vnd.apple.mpegurl") or \
				url.lower().endswith((".m3u", ".m3u8")):
			for line in data.splitlines():
				line = line.strip()
				if line and not line.startswith("#"):
					return True, _urljoin(base, line)
		if ct == "audio/x-scpls" or url.lower().endswith(".pls"):
			for line in data.splitlines():
				if line.lower().startswith("file1="):
					return True, _urljoin(base, line.split("=", 1)[1].strip())
		import re as _re
		if ct in ("video/x-ms-asf", "audio/x-ms-wax", "audio/x-ms-wmx") or \
				any(url.lower().endswith(e) for e in (".asx", ".wmx", ".wax")):
			m = _re.search(r"href\s*=\s*[\"']([^\"']+)[\"']", data, _re.IGNORECASE)
			if m:
				return True, _urljoin(base, m.group(1))

		# Got a response but content-type is not audio — still reachable
		# Translators: Error returned when the URL responds but isn't recognised as an audio stream or a playlist container (m3u/pls/asx) pointing to one; %s is the response's content-type.
		return False, _("Response received but content type is not audio: %s") % ct

	except _err.HTTPError as e:
		# Translators: Error returned when the server responds with an HTTP error status; %d is the status code, %s its reason phrase.
		return False, _("HTTP error %d: %s") % (e.code, e.reason)
	except _err.URLError as e:
		# Translators: Error returned when the connection to the URL fails outright (DNS, refused, timeout); %s is the underlying reason.
		return False, _("Connection failed: %s") % str(e.reason)
	except OSError as e:
		# Translators: Generic fallback error for any other unexpected exception while checking the URL; %s is the exception message.
		return False, _("Network error: %s") % str(e)
	except Exception as e:
		return False, str(e)


def _html_to_text(text):
	"""Strip HTML tags and decode entities from an RSS/Atom description.

	podcast.py stores <description>/<atom:summary> as-is, which is
	commonly raw HTML ("<p>...</p>", "&amp;", etc.) - not something a
	screen reader should read literally. Deliberately simple (no
	external HTML parser dependency): drop tags, decode entities,
	collapse the blank lines that tends to leave behind.

	Module-level (rather than a RadioDialog method) since it never
	touched self to begin with, and trackInfoMixin.py's station-details
	dialog needs to reuse it too - see _format_audiobook_lines()/
	_format_podcast_episode_lines() below.
	"""
	if not text:
		return text
	text = re.sub(r"<[^>]+>", " ", text)
	text = unescape(text)
	text = re.sub(r"[ \t]+", " ", text)
	text = re.sub(r"\n\s*\n+", "\n\n", text)
	return text.strip()


def _format_audiobook_lines(source_label="", author="", narrator="", publisher="",
		format_label="", chapter_count=0, description="",
		original_title="", director="", release_year="", imdb_rating="", actors=""):
	"""Shared line-builder for GETEM/LibriVox audiobook metadata: Source/
	Original title/Author/Director/Narrator/Cast/Publisher/Type/Release
	year/IMDB rating/part-count/description, in that order, one per
	line (blank fields omitted). Reused by
	RadioDialog._format_getem_details() (the Audio Books tab's details
	box) and trackInfoMixin._build_audiobook_details() (the station-
	details dialog's "Audio book details" row), so both show identical,
	identically-translated text for the same underlying book instead of
	each maintaining its own copy of these strings. Does NOT include the
	book's title or detail_url - callers that want those (both current
	callers do) add them themselves, since where those two lines belong
	relative to the rest differs slightly between the two dialogs.

	original_title/director/release_year/imdb_rating/actors only ever
	have a value for GETEM's "Sesli Betimleme" (audio description)
	works - see getem._extract_audiobook_extra_fields() - and are
	simply omitted, same as any other blank field, for a plain
	audiobook/talking-book (or a LibriVox book, which never sets them
	at all) that doesn't carry them."""
	lines = []
	if source_label:
		# Translators: Field-name:value lines for the audio-book details block; see this function's docstring above for the full field list and where it's shown.
		lines.append(_("Source: %s") % source_label)
	if original_title:
		# Translators: Field:value line for a book's original-language title (GETEM audio-description works only); see _format_audiobook_lines' docstring for the full field list.
		lines.append(_("Original title: %s") % original_title)
	if author:
		# Translators: Field:value line for the book's author.
		lines.append(_("Author: %s") % author)
	if director:
		# Translators: Field:value line for the book's director (GETEM audio-description works only, e.g. an audio-described film).
		lines.append(_("Director: %s") % director)
	if narrator:
		# Translators: Field:value line for the book's narrator/reader name.
		lines.append(_("Narrator: %s") % narrator)
	if actors:
		# Translators: Field label for the 'actors' value specifically (GETEM audio-description works only); kept short as 'Cast' rather than 'Actors' to match common media-details wording.
		lines.append(_("Cast: %s") % actors)
	if publisher:
		# Translators: Field:value line for the book's publisher.
		lines.append(_("Publisher: %s") % publisher)
	if format_label:
		# Translators: Field:value line for the book's format/type label (e.g. 'AI narration').
		lines.append(_("Type: %s") % format_label)
	if release_year:
		# Translators: Field:value line for the work's release year (GETEM audio-description works only).
		lines.append(_("Release year: %s") % release_year)
	if imdb_rating:
		# Translators: Field:value line for the work's IMDB rating (GETEM audio-description works only).
		lines.append(_("IMDB rating: %s") % imdb_rating)
	if chapter_count:
		# Translators: Plural forms for the part/chapter count line at the end of the details block, e.g. '12 parts'.
		lines.append(ngettext("%d part", "%d parts", chapter_count) % chapter_count)
	if description:
		text = _html_to_text(description)
		if text:
			lines.append("")
			lines.append(text)
	return lines


def _format_podcast_episode_lines(author="", published="", duration="", description=""):
	"""Shared line-builder for podcast episode metadata: By/Published/
	Duration/description, in that order (blank fields omitted). Reused
	by RadioDialog._format_episode_details() (the Podcasts tab's episode
	details box) and trackInfoMixin._build_podcast_details() (the
	station-details dialog's "Episode details" row) for the same reason
	_format_audiobook_lines() above is shared between their audiobook
	equivalents. *author* is the podcast's (feed's) author, not
	per-episode - _format_episode_details() doesn't pass one today since
	PodcastEpisode has no author of its own, but the station-details
	dialog does (station_dict carries "podcast_author" - see
	RadioDialog._on_episode_play()), and "By: %s" is the exact string
	_format_feed_details() already uses for that same value, so reusing
	it here needs no new translatable string either."""
	lines = []
	if author:
		# Translators: Field:value line for the podcast's/episode's author; see this function's docstring above for why it reuses the feed-details 'By:' string.
		lines.append(_("By: %s") % author)
	if published:
		# Translators: Field:value line for the episode's publish date.
		lines.append(_("Published: %s") % published)
	if duration:
		# Translators: Field:value line for the episode's duration.
		lines.append(_("Duration: %s") % duration)
	if description:
		text = _html_to_text(description)
		if text:
			lines.append("")
			lines.append(text)
	return lines


def _enabled_audiobook_sources():
	"""Which audio book sources (currently "getem"/"librivox"/"gutenberg")
	the user has enabled in Settings - see FreeRadioSettingsPanel's "Audio
	book sources" checklist, which is what edits config.conf["freeradio"]
	["audiobook_sources"]. Returns a set of the enabled keys - all three are
	enabled by default (the confspec default is "getem,librivox,gutenberg"),
	so an upgrade from a version before this option existed searches
	exactly as before. An empty set is a legitimate result (the user
	unchecked everything), not a fallback case - _on_getem_search() handles
	that by simply finding nothing rather than searching everything."""
	raw = config.conf["freeradio"].get("audiobook_sources", "getem,librivox,gutenberg")
	return {s.strip() for s in raw.split(",") if s.strip()}


class RadioDialog(wx.Dialog):
	"""Station browser with Favourites and All Stations tabs.

	The dialog is never destroyed while the plugin is running — closing only
	hides it.  The plugin calls _force_destroy() on terminate().
	"""

# Time to delay country combo changes (ms).
	# Requests are not opened for each item as the user quickly scrolls through the list;
	# If the user pauses for this period, a single request is sent.
	_COMBO_DEBOUNCE_MS = 400

	def __init__(self, parent, station_manager, player, play_callback, recorder=None, timer_manager=None, plugin=None):
		super().__init__(
			parent,
			# Translators: Title of the main FreeRadio station-browser dialog itself.
			title=_("FreeRadio - Station Browser"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		self._manager       = station_manager
		self._player        = player
		self._play_callback = play_callback
		self._recorder      = recorder
		self._timer_manager = timer_manager
		self._plugin        = plugin
		self._podcast_manager = podcast.PodcastManager()
		self._getem_library   = getem.GetemLibrary()
		self._librivox_library = librivox.LibrivoxLibrary()
		self._gutenberg_library = gutenberg_audiobooks.GutenbergLibrary()
		self._jukebox_manager = jukebox.JukeboxManager()
		# Cancels an in-flight disk search (see jukebox.search_disk_for_audio)
		# as soon as a newer one is requested, so a slow, stale search can't
		# overwrite fresher results after the fact.
		self._jukebox_search_cancel = None
		self._jukebox_search_seq = 0     # bumped on every new search; used to
		                                  # discard replies from superseded ones
		self._jukebox_results = []       # list of absolute file paths, current search results
		self._jukebox_selected_tracks = []  # tracks of the currently-focused jukebox entry (file: itself; folder: its scanned tracks)
		self._all_stations    = []
		self._extra_stations  = []   # additional stations from country selection
		self._search_stations = []   # Stations from API text search
		self._stations        = []
		self._combo_fetch_id = 0
		self._moving_station_index = -1  # Index of the item picked for X-based reordering
		self._combo_debounce_timer = None  # wx.CallLater for country combo debounce
		self._search_debounce_timer = None
		self._search_fetch_id = 0
		self._total_found = None  # Total stations found by API (may exceed displayed limit)
		self._country_station_counts = {}  # code -> stationcount from API, populated by _fetch_countries
		self._sched_index_map = []  # Maps schedule listbox rows to ScheduledRecording objects (None for headers)

		# Multi-mark state for the "mark several items with '.', then remove
		# them all at once with Delete or the context menu's Remove Selected"
		# flow - see _toggle_*_mark()/_on_*_remove_selected() below. Each set
		# holds a stable identity key for the marked rows in that list, not
		# list indices, since indices shift on every refresh:
		#   favourites         -> station "stationuuid"
		#   liked songs        -> the raw song line as stored in likedSongs.txt
		#   audio-book library -> book.identity_key()
		#   jukebox entries    -> entry.path
		self._fav_marked     = set()
		self._liked_marked   = set()
		self._getem_marked   = set()
		self._jukebox_marked = set()

		self._build_ui()
		self._prepopulate_country_combo()
		threading.Thread(target=self._fetch_all,       daemon=True).start()
		threading.Thread(target=self._fetch_countries, daemon=True).start()

		# NOTE: previously had a wx.Timer here that live-updated the playing
		# episode's row (elapsed/total duration) once a second. Removed:
		# on MSW, SetString() on the focused row still got spoken by NVDA
		# every time it changed, so it made the episode list unusable while
		# a podcast was playing and that row had focus. The row's duration
		# now only reflects the last saved position (updated when the list
		# is rebuilt), not a live-ticking value.


	def _build_ui(self):
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		self._notebook    = wx.Notebook(self)
		self._notebook.SetName("")
		self._all_panel    = wx.Panel(self._notebook)
		self._fav_panel    = wx.Panel(self._notebook)
		self._rec_panel    = wx.Panel(self._notebook)
		self._timer_panel  = wx.Panel(self._notebook)
		self._liked_panel  = wx.Panel(self._notebook)
		self._podcast_panel = wx.Panel(self._notebook)
		self._getem_panel   = wx.Panel(self._notebook)
		self._jukebox_panel = wx.Panel(self._notebook)
		# Tab labels no longer carry letter accelerators; numeric shortcuts
		# Alt+1..8 are handled in _on_char_hook via an accelerator table.
		# Translators: Tab label for the main catalog browser (all stations from Radio Browser/TuneIn/iHeart, searchable).
		self._notebook.AddPage(self._all_panel,   _("All Stations"))
		# Translators: Tab label for the user's saved favourite stations.
		self._notebook.AddPage(self._fav_panel,   _("Favourites"))
		# Translators: Tab label for the recording controls and active/past recordings list.
		self._notebook.AddPage(self._rec_panel,   _("Recording"))
		# Translators: Tab label for scheduled recording timers.
		self._notebook.AddPage(self._timer_panel, _("Timer"))
		# Translators: Tab label for the list of liked/favourited songs (with lyrics lookup).
		self._notebook.AddPage(self._liked_panel, _("Liked Songs"))
		# Translators: Tab label for podcast subscriptions and episodes.
		self._notebook.AddPage(self._podcast_panel, _("Podcasts"))
		# Translators: Tab label for the audio-book library (GETEM/LibriVox/Project Gutenberg).
		self._notebook.AddPage(self._getem_panel, _("Audio Books"))
		# Translators: Tab label for the local jukebox (user-added audio files/folders).
		self._notebook.AddPage(self._jukebox_panel, _("Jukebox"))
		self._notebook.SetSelection(0)  # Start on the All Stations tab
		main_sizer.Add(self._notebook, 1, wx.EXPAND | wx.ALL, 5)

		# Audio Output Device line (visible on all tabs)
		device_row = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Static label for the output-device choice control, shown above every tab.
		self._dev_label = wx.StaticText(self, label=_("Output device:"))
		device_row.Add(self._dev_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
		# Translators: Placeholder shown in the output-device dropdown while the device list is still being fetched.
		self._device_choice = wx.Choice(self, choices=[_("Loading...")])
		# Translators: Accessible name for the output-device dropdown (same text as its static label).
		self._device_choice.SetName(_("Output device:"))
		self._device_choice.SetMinSize((200, -1))
		device_row.Add(self._device_choice, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
		main_sizer.Add(device_row, 0, wx.EXPAND | wx.TOP, 4)
		self._dialog_audio_devices = []   # (index, name)
		self._audio_devices_loading = False
		self._audio_devices_last_refresh = 0.0
		
		self.refresh_audio_devices(force=True)

		# Volume and Effects row (visible on all tabs)
		audio_row = wx.BoxSizer(wx.HORIZONTAL)

		# Translators: Static label for the volume spin control, shown above every tab.
		_vol_label = wx.StaticText(self, label=_("Volume:"))
		audio_row.Add(_vol_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)

		self._vol_spin = wx.SpinCtrl(self, min=0, max=200,
		                             initial=config.conf["freeradio"]["volume"])
		# Translators: Accessible name for the volume spin control (same text as its static label).
		self._vol_spin.SetName(_("Volume:"))
		self._vol_spin.SetMinSize((70, -1))
		audio_row.Add(self._vol_spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

		# Effects
		# Translators: Static label for the audio-effects checklist, shown above every tab.
		self._fx_label = wx.StaticText(self, label=_("Effects:"))
		audio_row.Add(self._fx_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)

		self._fx_keys = ["chorus", "compressor", "distortion",
		                 "echo", "flanger", "gargle", "reverb",
		                 "eq_bass", "eq_treble", "eq_vocal"]
		# Translators: Names of the audio effects in the Effects checklist, in the same order as self._fx_keys just above: chorus, compressor, distortion, echo, flanger, gargle, reverb, then the three EQ boost bands.
		_fx_display = [
			_("Chorus"), _("Compressor"), _("Distortion"),
			_("Echo"), _("Flanger"), _("Gargle"), _("Reverb"),
			_("EQ: Bass Boost"), _("EQ: Treble Boost"), _("EQ: Vocal Boost"),
		]
		self._fx_choice = wx.CheckListBox(self, choices=_fx_display)
		# Translators: Accessible name for the audio-effects checklist (same text as its static label).
		self._fx_choice.SetName(_("Effects:"))
		_saved_fx = config.conf["freeradio"].get("audio_fx", "none")
		_active = {x.strip() for x in _saved_fx.split(",") if x.strip() != "none"}
		for i, key in enumerate(self._fx_keys):
			self._fx_choice.Check(i, key in _active)
		audio_row.Add(self._fx_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

		main_sizer.Add(audio_row, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)

		# EQ gain row — shown only when at least one EQ effect is enabled
		eq_row = wx.BoxSizer(wx.HORIZONTAL)
		self._eq_bands = [
			# Translators: Label for the bass-boost EQ gain spin control, shown only while that effect is checked.
			("eq_bass",   _("Bass gain (dB):"),   9),
			# Translators: Label for the treble-boost EQ gain spin control, shown only while that effect is checked.
			("eq_treble", _("Treble gain (dB):"), 9),
			# Translators: Label for the vocal-boost EQ gain spin control, shown only while that effect is checked.
			("eq_vocal",  _("Vocal gain (dB):"),  6),
		]
		self._eq_spins = {}   # band -> SpinCtrl
		for band, label, default_db in self._eq_bands:
			lbl = wx.StaticText(self, label=label)
			eq_row.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
			saved_db = config.conf["freeradio"].get("eq_gain_" + band, default_db)
			spin = wx.SpinCtrl(self, min=-15, max=15, initial=int(saved_db))
			spin.SetName(label)
			spin.SetMinSize((60, -1))
			eq_row.Add(spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
			self._eq_spins[band] = spin
			spin.Bind(wx.EVT_SPINCTRL, lambda evt, b=band: self._on_eq_gain_changed(evt, b))

		self._eq_row_sizer = eq_row
		main_sizer.Add(eq_row, 0, wx.EXPAND | wx.BOTTOM, 4)


		# action buttons
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Button label; plays or pauses the currently selected/playing station.
		self._play_btn    = wx.Button(self, label=_("&Play/Pause"))
		# Translators: Button label; removes the selected custom station (only enabled for user-added stations, not the built-in catalog).
		self._del_btn     = wx.Button(self, label=_("&Delete Station"))
		self._del_btn.Enable(False)
		# Translators: Button label; adds the currently selected station to favourites.
		self._fav_btn     = wx.Button(self, label=_("Add to Fa&vorites"))
		# Translators: Button label; opens the selected station's details dialog (info, description, tags).
		self._details_btn = wx.Button(self, label=_("Station Detai&ls"))
		self._details_btn.Enable(False)
		# Translators: Button label; opens the dialog for manually adding a custom station by stream URL.
		self._add_btn     = wx.Button(self, label=_("Add C&ustom Station..."))
		# Manually re-syncs the local station list cache from the Radio Browser
		# API, instead of waiting for the periodic background refresh.
		# Translators: Button label; manually re-fetches the full station catalog from Radio Browser's server.
		self._refresh_catalog_btn = wx.Button(self, label=_("&Update Station List"))
		self._refresh_catalog_btn.SetToolTip(
			# Translators: Tooltip for the Update Station List button.
			_("Re-downloads the full station list from the server, so search and browsing use the latest data.")
		)
		# Translators: Button label; closes the station browser dialog.
		self._close_btn   = wx.Button(self, label=_("&Close"))
		for btn in (self._play_btn, self._del_btn, self._fav_btn, self._details_btn, self._add_btn, self._refresh_catalog_btn, self._close_btn):
			btn_sizer.Add(btn, 0, wx.ALL, 5)
		main_sizer.Add(btn_sizer, 0, wx.CENTER | wx.BOTTOM, 8)

		self.SetSizer(main_sizer)
		self.SetMinSize((560, 620))
		self.Fit()

		# Type-ahead state for country combo
		self._country_search_str    = ""
		self._country_search_timer  = None
		self._country_search_cur    = None
		self._country_search_anchor = None  # position before typing sequence started
		# Type-ahead state for station list boxes (one set per list)
		self._list_search_str    = ""
		self._list_search_timer  = None
		self._list_search_cur    = None
		self._list_search_anchor = None  # position before typing sequence started
		self._build_all_tab()
		self._build_fav_tab()
		self._build_rec_tab()
		self._build_timer_tab()
		self._build_liked_tab()
		self._build_podcast_tab()
		self._build_audiobooks_tab()
		self._build_jukebox_tab()

		self._play_btn.Bind(wx.EVT_BUTTON,    self._on_play_clicked)
		self._del_btn.Bind(wx.EVT_BUTTON,     self._on_delete_station)
		self._del_btn.Bind(wx.EVT_KEY_DOWN,   self._on_del_btn_key)
		self._fav_btn.Bind(wx.EVT_BUTTON,     self._on_toggle_favorite)
		self._details_btn.Bind(wx.EVT_BUTTON, self._on_details_clicked)
		self._add_btn.Bind(wx.EVT_BUTTON,     self._on_add_custom)
		self._refresh_catalog_btn.Bind(wx.EVT_BUTTON, self._on_refresh_catalog)
		self._close_btn.Bind(wx.EVT_BUTTON,   self._on_close_btn)

		self._vol_spin.Bind(wx.EVT_SPINCTRL,    self._on_vol_changed)
		self._fx_choice.Bind(wx.EVT_CHECKLISTBOX, self._on_fx_changed)
		self._fx_choice.Bind(wx.EVT_LISTBOX,      self._on_fx_focus)
		self._device_choice.Bind(wx.EVT_CHOICE,   self._on_device_changed)
		self._device_choice.Bind(wx.EVT_SET_FOCUS, self._on_device_choice_focus)

		# Apply saved EQ gains to player on startup and update row visibility
		wx.CallAfter(self._init_eq_gains)

		for btn in (self._play_btn, self._del_btn, self._fav_btn,
		            self._details_btn, self._add_btn, self._refresh_catalog_btn, self._close_btn):
			btn.Bind(wx.EVT_SET_FOCUS, self._on_button_focused)

		self._notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_tab_changed)
		self.Bind(wx.EVT_CLOSE,     self._on_window_close)
		self.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

		self._play_btn.SetDefault()
		wx.CallAfter(self._search.SetFocus)

	def focus_favorites(self):
		"""Switch to the Favourites tab and give the list focus.

		Called from _open_dialog() via wx.CallLater(0) so the notebook HWND is
		fully realized.  Guards against a corrupted notebook (GetPageCount() == 0)
		as a safety net.
		"""
		if not self:
			return
		try:
			if self._notebook.GetPageCount() == 0:
				return
			self._notebook.SetSelection(1)  # Favourites tab index
		except Exception:
			return
		self._refresh_fav_list()
		favs = self._manager.get_favorites()
		if favs and self._fav_list.GetSelection() == wx.NOT_FOUND:
			self._fav_list.SetSelection(0)
		self._fav_list.SetFocus()

	def focus_search(self):
		"""Switch to the All Stations tab and focus on the search box.

		Called from _open_dialog() via wx.CallLater(0).
		Guards against a corrupted notebook as a safety net.
		"""
		if not self:
			return
		try:
			if self._notebook.GetPageCount() == 0:
				return
			self._notebook.SetSelection(0)
		except Exception:
			return
		self._search.SetFocus()
		self._search.SelectAll()

	def focus_tab(self, tab_index):
		"""Switch to the specified tab and focus on the first focusable item.
		Indices: 0=All Stations, 1=Favourites, 2=Recording, 3=Timer, 4=Liked Songs,
		5=Podcasts, 6=Audio Books, 7=Jukebox.

		Called from _open_dialog() via wx.CallLater(0).
		Guards against a corrupted notebook as a safety net.
		"""
		if not self:
			return
		try:
			if self._notebook.GetPageCount() == 0:
				return
			self._notebook.SetSelection(tab_index)
		except Exception:
			return
		# Move focus to the first focusable child of the selected panel.
		panel = self._notebook.GetPage(tab_index)
		for child in panel.GetChildren():
			if child.AcceptsFocus() and child.IsEnabled() and child.IsShown():
				child.SetFocus()
				return

	def focus_podcasts(self):
		"""Switch to the Podcasts tab and give the subscription list focus.

		Called from _open_dialog() via wx.CallLater(0) - see script_openPodcasts
		(Ctrl+Windows+O) in __init__.py. Guards against a corrupted notebook
		as a safety net."""
		if not self:
			return
		try:
			if self._notebook.GetPageCount() == 0:
				return
			self._notebook.SetSelection(5)  # Podcasts tab index
		except Exception:
			return
		# SetSelection() here is programmatic, so it does not fire the
		# wx.EVT_NOTEBOOK_PAGE_CHANGED handler that would normally populate
		# this tab's list (see _apply_tab_side_effects) - populate it here
		# explicitly instead, same as focus_favorites() does for the
		# Favourites tab.
		self._refresh_podcast_list()
		feeds = self._podcast_manager.get_feeds()
		if feeds and self._podcast_list.GetSelection() == wx.NOT_FOUND:
			self._podcast_list.SetSelection(0)
		self._podcast_list.SetFocus()

	def focus_audiobooks(self):
		"""Switch to the Audio Books tab and give the library list focus.

		Called from _open_dialog() via wx.CallLater(0) - see script_openLibrary
		(Ctrl+Windows+L) in __init__.py. Guards against a corrupted notebook
		as a safety net."""
		if not self:
			return
		try:
			if self._notebook.GetPageCount() == 0:
				return
			self._notebook.SetSelection(6)  # Audio Books tab index
		except Exception:
			return
		# Programmatic SetSelection() bypasses _apply_tab_side_effects (see
		# focus_podcasts() for the same note) - refresh the library listbox
		# explicitly before reading from it below.
		self._refresh_getem_library_list()
		books = self._merged_library_books()
		if books and self._getem_library_ctrl.GetSelection() == wx.NOT_FOUND:
			self._getem_library_ctrl.SetSelection(0)
		self._getem_library_ctrl.SetFocus()

	def focus_jukebox(self):
		"""Switch to the Jukebox tab. On the very first open (nothing in
		this tab has had focus yet), gives the search box focus. On later
		opens, restores focus to whichever control in this tab was last
		focused - see _on_jukebox_child_focus() - so re-opening the dialog
		doesn't keep bouncing focus back to the search box.

		Called from _open_dialog() via wx.CallLater(0) - see
		script_openJukebox (Ctrl+Windows+U) in __init__.py. Guards against
		a corrupted notebook as a safety net."""
		if not self:
			return
		try:
			if self._notebook.GetPageCount() == 0:
				return
			self._notebook.SetSelection(7)  # Jukebox tab index
		except Exception:
			return
		# Programmatic SetSelection() bypasses _apply_tab_side_effects (see
		# focus_podcasts() for the same note) - refresh the entries listbox
		# explicitly so it isn't left empty/stale.
		self._refresh_jukebox_list()
		target = getattr(self, "_jukebox_last_focused", None)
		try:
			restorable = bool(target) and target.IsShown() and target.IsEnabled()
		except RuntimeError:
			# Underlying C++ object was destroyed (e.g. a since-removed
			# control) - fall back to the search box below.
			restorable = False
		if restorable:
			target.SetFocus()
		else:
			self._jukebox_search.SetFocus()
			self._jukebox_search.SelectAll()

	def _build_fav_tab(self):
		sizer = wx.BoxSizer(wx.VERTICAL)

		# Filter row: label + text field that narrows the favourites list in real time.
		sizer.Add(
			# Translators: Label above the field that filters the favourites list below it.
			wx.StaticText(self._fav_panel, label=_("Filter:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._fav_filter = wx.TextCtrl(self._fav_panel)
		# Translators: Accessible name for the favourites filter field.
		self._fav_filter.SetName(_("Filter favourites"))
		sizer.Add(self._fav_filter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		self._fav_list = wx.ListBox(self._fav_panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the favourites list.
		self._fav_list.SetName(_("Favourites"))
		sizer.Add(self._fav_list, 1, wx.EXPAND | wx.ALL, 5)

		btn_row = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Button label; saves the currently selected station's audio profile (volume/effects/EQ), so it's re-applied automatically whenever that station is played.
		self._save_audio_btn = wx.Button(self._fav_panel, label=_("Save Audio Pr&ofile for This Station"))
		self._save_audio_btn.Enable(False)
		btn_row.Add(self._save_audio_btn, 0, wx.RIGHT, 6)

		# Translators: Button label; removes the saved audio profile for the selected favourite station.
		self._clear_audio_btn = wx.Button(self._fav_panel, label=_("Clear Audio Prof&ile"))
		self._clear_audio_btn.Enable(False)
		btn_row.Add(self._clear_audio_btn, 0, wx.RIGHT, 6)

		# Translators: Button label; opens a rename prompt for the selected custom favourite station.
		self._rename_btn = wx.Button(self._fav_panel, label=_("Re&name Station"))
		self._rename_btn.Enable(False)
		btn_row.Add(self._rename_btn, 0)

		sizer.Add(btn_row, 0, wx.LEFT | wx.BOTTOM, 5)

		# Second button row: export and import favourites.
		io_row = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Button label; opens a file-save dialog to export the favourites list (JSON or M3U).
		self._fav_export_btn = wx.Button(self._fav_panel, label=_("E&xport Favourites..."))
		io_row.Add(self._fav_export_btn, 0, wx.RIGHT, 6)
		# Translators: Button label; opens a file-picker to import favourites from a JSON or M3U file.
		self._fav_import_btn = wx.Button(self._fav_panel, label=_("&Import Favourites..."))
		io_row.Add(self._fav_import_btn, 0)
		sizer.Add(io_row, 0, wx.LEFT | wx.BOTTOM, 5)

		self._fav_panel.SetSizer(sizer)

		self._fav_list.Bind(wx.EVT_CHAR,           self._on_list_char)
		self._fav_list.Bind(wx.EVT_LISTBOX,        self._on_selection_changed)
		self._fav_list.Bind(wx.EVT_LISTBOX_DCLICK, self._on_play_clicked)
		self._fav_list.Bind(wx.EVT_KEY_DOWN,       self._on_fav_list_key)
		self._fav_list.Bind(wx.EVT_SET_FOCUS, self._on_fav_list_focus)
		self._save_audio_btn.Bind(wx.EVT_BUTTON,   self._on_save_audio_profile)
		self._clear_audio_btn.Bind(wx.EVT_BUTTON,  self._on_clear_audio_profile)
		self._rename_btn.Bind(wx.EVT_BUTTON,       self._on_rename_station)
		self._fav_export_btn.Bind(wx.EVT_BUTTON,   self._on_fav_export)
		self._fav_import_btn.Bind(wx.EVT_BUTTON,   self._on_fav_import)
		# Filter text field: rebuild the list on every keystroke.
		self._fav_filter.Bind(wx.EVT_TEXT,     self._on_fav_filter_changed)
		# Allow Down arrow to move focus from the filter field into the list.
		self._fav_filter.Bind(wx.EVT_KEY_DOWN, self._on_fav_filter_key)

	def _build_all_tab(self):
		sizer = wx.BoxSizer(wx.VERTICAL)

		filter_sizer = wx.BoxSizer(wx.HORIZONTAL)

		# Sort combo
		# Translators: Label for the station-list sort-order combo box, on the All Stations tab.
		filter_sizer.Add(wx.StaticText(self._all_panel, label=_("Sort:")),
		                 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._sort_cb = wx.ComboBox(
			self._all_panel,
			style=wx.CB_READONLY,
			# Translators: The two sort-order choices for the All Stations list: alphabetical by name, or by the station's Radio Browser rating/votes.
			choices=[_("Alphabetical"), _("By Rating")],
		)
		# Translators: Accessible name for the sort-order combo box (same text as its static label).
		self._sort_cb.SetName(_("Sort:"))
		self._sort_cb.SetSelection(0)
		filter_sizer.Add(self._sort_cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)

		# Country combo
		# Translators: Label for the country filter combo box.
		filter_sizer.Add(wx.StaticText(self._all_panel, label=_("Country:")),
		                 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		_all_country_names = sorted(country_name(code) for code in _COUNTRY_NAMES)
		# Translators: First entry in the country filter combo box, meaning no country restriction (show all countries).
		self._country_cb = wx.ComboBox(self._all_panel, style=wx.CB_READONLY, choices=[_("All")] + _all_country_names)
		self._country_cb.SetSelection(0)
		filter_sizer.Add(self._country_cb, 1)
		sizer.Add(filter_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# Result limit row
		limit_sizer = wx.BoxSizer(wx.HORIZONTAL)
		limit_sizer.Add(
			# Translators: Label for the spin control capping how many stations are fetched per country from Radio Browser.
			wx.StaticText(self._all_panel, label=_("Result limit per country:")),
			0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4,
		)
		_saved_limit = config.conf["freeradio"].get("result_limit", 1000)
		self._limit_spin = wx.SpinCtrl(
			self._all_panel, min=100, max=10000, initial=_saved_limit,
		)
		# Translators: Accessible name for the result-limit spin control (shorter than its static label above).
		self._limit_spin.SetName(_("Result limit:"))
		self._limit_spin.SetMinSize((80, -1))
		limit_sizer.Add(self._limit_spin, 0, wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(limit_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# Translators: Label above the free-text search field for the All Stations list.
		sizer.Add(wx.StaticText(self._all_panel, label=_("Search:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._search = wx.TextCtrl(self._all_panel)
		sizer.Add(self._search, 0, wx.EXPAND | wx.ALL, 5)

		hint = wx.StaticText(
			self._all_panel,
			# Translators: Grey hint text under the search field, explaining that results filter live as you type; the '·' is a visual separator, not meant to be read as punctuation.
			label=_("Type to search · results update automatically"),
		)
		hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
		sizer.Add(hint, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)

		# Translators: Placeholder status text shown while the station catalog is being loaded from disk/network.
		self._status = wx.StaticText(self._all_panel, label=_("Loading stations..."))
		sizer.Add(self._status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		# Translators: Label above the resulting station list itself.
		sizer.Add(wx.StaticText(self._all_panel, label=_("Stations:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._all_list = wx.ListBox(self._all_panel, style=wx.LB_SINGLE)
		sizer.Add(self._all_list, 1, wx.EXPAND | wx.ALL, 5)
		self._all_panel.SetSizer(sizer)

		self._search.Bind(wx.EVT_TEXT,         self._on_text_changed)
		self._search.Bind(wx.EVT_KEY_DOWN,     self._on_search_key)
		self._sort_cb.Bind(wx.EVT_COMBOBOX,    self._on_sort_changed)
		self._country_cb.Bind(wx.EVT_COMBOBOX, self._on_combo_changed)
		self._country_cb.Bind(wx.EVT_CHAR,     self._on_country_char)
		self._limit_spin.Bind(wx.EVT_SPINCTRL, self._on_limit_changed)

		self._all_list.Bind(wx.EVT_CHAR,           self._on_list_char)
		self._all_list.Bind(wx.EVT_LISTBOX,        self._on_selection_changed)
		self._all_list.Bind(wx.EVT_LISTBOX_DCLICK, self._on_play_clicked)
		self._all_list.Bind(wx.EVT_KEY_DOWN,       self._on_list_key)
		self._all_list.Bind(wx.EVT_SET_FOCUS,      lambda e: (self._play_btn.SetDefault(), e.Skip()))

	def _build_rec_tab(self):
		sizer = wx.BoxSizer(wx.VERTICAL)

		# Instant Recording section removed entirely.
		# Only Scheduled Recording remains.

		sizer.Add(wx.StaticLine(self._rec_panel), 0, wx.EXPAND | wx.ALL, 8)

		# Translators: Section heading above the scheduled-recording setup controls, on the Recording tab.
		sizer.Add(wx.StaticText(self._rec_panel, label=_("Scheduled Recording")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# Translators: Label for the station-selection list (used both as a static label and as the accessible name below).
		station_label = _("Station:")
		st_lbl = wx.StaticText(self._rec_panel, label=station_label)
		sizer.Add(st_lbl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# Filter field for the scheduled-recording station list.
		sizer.Add(
			# Translators: Label above the filter text field that narrows the station list below it.
			wx.StaticText(self._rec_panel, label=_("Filter:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._sched_station_filter = wx.TextCtrl(self._rec_panel)
		# Translators: Accessible name for the station filter text field.
		self._sched_station_filter.SetName(_("Filter stations"))
		sizer.Add(self._sched_station_filter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# Use a ListBox instead of an editable ComboBox so screen readers
		# announce each item as the user navigates the list.
		self._sched_station_cb = wx.ListBox(self._rec_panel, style=wx.LB_SINGLE)
		self._sched_station_cb.SetMinSize((-1, 80))
		self._sched_station_cb.SetName(station_label)
		sizer.Add(self._sched_station_cb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		# Translators: Label for the start-time field (also used as its accessible name below); the value must be typed as HH:MM.
		time_label = _("Start time (HH:MM):")
		sizer.Add(wx.StaticText(self._rec_panel, label=time_label),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._sched_time = wx.TextCtrl(self._rec_panel, value="")
		self._sched_time.SetName(time_label)
		sizer.Add(self._sched_time, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		# Translators: Label for the recording-duration field (also used as its accessible name below); value is in minutes.
		dur_label = _("Duration (minutes):")
		sizer.Add(wx.StaticText(self._rec_panel, label=dur_label),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._sched_dur = wx.SpinCtrl(self._rec_panel, min=1, max=600, initial=60)
		self._sched_dur.SetName(dur_label)
		sizer.Add(self._sched_dur, 0, wx.LEFT | wx.RIGHT, 8)

		# --- Recurrence mode ---
		sizer.Add(
			# Translators: Label above the two recurrence radio buttons (once vs. weekly).
			wx.StaticText(self._rec_panel, label=_("Recurrence:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._sched_rec_once = wx.RadioButton(
			self._rec_panel,
			# Translators: Radio button: schedule a single one-time recording.
			label=_("Only &once"),
			style=wx.RB_GROUP,
		)
		# Repeats every week on the selected active days, with no end —
		# the user removes it from the schedule list when they want it to
		# stop (see "&Remove Selected").
		self._sched_rec_indef = wx.RadioButton(
			self._rec_panel,
			# Translators: Radio button: repeat the recording every week indefinitely, on the days chosen below.
			label=_("Repeat &weekly"),
		)
		self._sched_rec_once.SetValue(True)
		sizer.Add(self._sched_rec_once,   0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		sizer.Add(self._sched_rec_indef,  0, wx.LEFT | wx.RIGHT | wx.TOP, 4)

		# --- Day-of-week selection ---
		# nvdaControls.CustomCheckListBox exposes each item as
		# ROLE_SYSTEM_CHECKBUTTON so NVDA announces state natively.
		# Hidden when recurrence is "once" since day selection is irrelevant.
		self._sched_days_label = wx.StaticText(
			# Translators: Label above the day-of-week checklist, shown only for the weekly-repeat recurrence mode.
			self._rec_panel, label=_("Active days:"),
		)
		sizer.Add(self._sched_days_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		_day_labels = [
			# Translators: Day-of-week checklist items, Monday through Sunday (continues on the next line).
			_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
			_("Friday"), _("Saturday"), _("Sunday"),
		]
		self._sched_days_clb = nvdaControls.CustomCheckListBox(
			self._rec_panel, choices=_day_labels,
		)
		# Translators: Accessible name for the day-of-week checklist (same text as its static label).
		self._sched_days_clb.SetName(_("Active days:"))
		# No day pre-checked — the user picks explicitly each time.
		# An empty selection is treated as "every day" by the recorder.
		self._sched_days_clb.Checked = []
		self._sched_days_clb.Select(0)
		sizer.Add(self._sched_days_clb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		# Translators: Label above the two playback-mode radio buttons for a scheduled recording.
		sizer.Add(wx.StaticText(self._rec_panel, label=_("Playback during recording:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._sched_mode_play = wx.RadioButton(
			self._rec_panel,
			# Translators: Radio button: play the station out loud while also recording it.
			label=_("Record while &listening (play and record simultaneously)"),
			style=wx.RB_GROUP,
		)
		self._sched_mode_rec  = wx.RadioButton(
			self._rec_panel,
			# Translators: Radio button: record silently, without audio output, to save resources.
			label=_("Record &only (no audio output)"),
		)
		self._sched_mode_rec.SetValue(True)
		sizer.Add(self._sched_mode_play, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		sizer.Add(self._sched_mode_rec,  0, wx.LEFT | wx.RIGHT | wx.TOP, 4)

		(
			self._sched_folder_default_rb,
			self._sched_folder_custom_rb,
			self._sched_folder_path,
			self._sched_folder_browse_btn,
		) = _build_folder_picker(self._rec_panel, sizer)

		# Translators: Button label; adds the configured recording to the schedule list below.
		self._sched_add_btn = wx.Button(self._rec_panel, label=_("&Add to Schedule"))
		sizer.Add(self._sched_add_btn, 0, wx.ALL, 8)

		# Translators: Label above the list of already-scheduled recordings.
		sizer.Add(wx.StaticText(self._rec_panel, label=_("Upcoming scheduled recordings:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._sched_list = wx.ListBox(self._rec_panel, style=wx.LB_SINGLE)
		sizer.Add(self._sched_list, 1, wx.EXPAND | wx.ALL, 8)

		self._rec_panel.SetSizer(sizer)

		# _rec_btn bind removed. Edit/Remove are no longer dedicated buttons —
		# their functionality moved into the list's context menu — see
		# _show_sched_context_menu(); reached via the Applications key /
		# Shift+F10, or Delete / Shift+Delete removes directly.
		self._sched_add_btn.Bind(wx.EVT_BUTTON, self._on_sched_add)
		self._sched_list.Bind(wx.EVT_LISTBOX,   self._on_sched_selected)
		self._sched_list.Bind(wx.EVT_CHAR,      self._on_list_char)
		self._sched_list.Bind(wx.EVT_KEY_DOWN,  self._on_sched_list_key)
		self._sched_station_cb.Bind(wx.EVT_SET_FOCUS, self._on_sched_station_focus)
		# Filter field: rebuild the station list on every keystroke.
		self._sched_station_filter.Bind(wx.EVT_TEXT,     self._on_sched_station_filter_changed)
		# Allow Down arrow to move focus from the filter field into the list.
		self._sched_station_filter.Bind(wx.EVT_KEY_DOWN, self._on_sched_station_filter_key)
		# Show/hide the active-days list when the recurrence mode changes.
		self._sched_rec_once.Bind(wx.EVT_RADIOBUTTON,   self._on_sched_recurrence_changed)
		self._sched_rec_indef.Bind(wx.EVT_RADIOBUTTON,  self._on_sched_recurrence_changed)
		# Type-ahead for the station listbox is handled in _on_char_hook.
		wx.CallAfter(self._sched_station_filter.SetFocus)

	def _build_timer_tab(self):
		"""Timer tab: start (alarm) or stop (sleep) the radio at a specific time."""
		sizer = wx.BoxSizer(wx.VERTICAL)

		# Translators: Label above the two timer-action radio buttons (start vs stop) on the Timer tab.
		sizer.Add(wx.StaticText(self._timer_panel, label=_("Timer action:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._timer_rb_start = wx.RadioButton(
			self._timer_panel,
			# Translators: Radio button: this timer's action is to start playing a station (an 'alarm' style timer).
			label=_("&Start radio at specified time (alarm)"),
			style=wx.RB_GROUP,
		)
		self._timer_rb_stop = wx.RadioButton(
			self._timer_panel,
			# Translators: Radio button: this timer's action is to stop playback (a 'sleep' style timer).
			label=_("St&op radio at specified time (sleep)"),
		)
		self._timer_rb_start.SetValue(True)
		sizer.Add(self._timer_rb_start, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		sizer.Add(self._timer_rb_stop,  0, wx.LEFT | wx.RIGHT | wx.TOP, 4)

		self._timer_time_label = wx.StaticText(
			# Translators: Label for the timer start-time field (also used as its accessible name below); value is typed as HH:MM.
			self._timer_panel, label=_("Start time (HH:MM):")
		)
		sizer.Add(self._timer_time_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._timer_time = wx.TextCtrl(self._timer_panel, value="")
		# Translators: Accessible name for the timer start-time field (same text as its static label above).
		self._timer_time.SetName(_("Start time (HH:MM):"))
		sizer.Add(self._timer_time, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		# --- Recurrence mode --- same two options, same strings, and the
		# same underlying recurrence/active_days model as the Recording
		# tab's scheduling section (recorder.ScheduledRecording) - see
		# TimerManager.add_sleep()/add_alarm().
		sizer.Add(
			# Translators: Label above the two recurrence radio buttons (once vs. weekly) - same wording as the Recording tab's scheduling section.
			wx.StaticText(self._timer_panel, label=_("Recurrence:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._timer_rec_once = wx.RadioButton(
			self._timer_panel,
			# Translators: Radio button: schedule a single one-time timer - same wording as the Recording tab's scheduling section.
			label=_("Only &once"),
			style=wx.RB_GROUP,
		)
		# Repeats every week on the selected active days, with no end - the
		# user removes it from the pending-timers list to stop it, same
		# convention as a recurring scheduled recording.
		self._timer_rec_weekly = wx.RadioButton(
			self._timer_panel,
			# Translators: Radio button: repeat the recording every week indefinitely, on the days chosen below - same wording as the Recording tab's scheduling section.
			label=_("Repeat &weekly"),
		)
		self._timer_rec_once.SetValue(True)
		sizer.Add(self._timer_rec_once,   0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		sizer.Add(self._timer_rec_weekly, 0, wx.LEFT | wx.RIGHT | wx.TOP, 4)

		# --- Day-of-week selection --- shown only for weekly repeat; an
		# empty selection means every day, same as the Recording tab.
		self._timer_days_label = wx.StaticText(
			# Translators: Label above the day-of-week checklist, shown only for the weekly-repeat recurrence mode - same wording as the Recording tab's scheduling section.
			self._timer_panel, label=_("Active days:"),
		)
		sizer.Add(self._timer_days_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		_timer_day_labels = [
			# Translators: Day-of-week checklist items, Monday through Sunday - same wording as the Recording tab's scheduling section.
			_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
			_("Friday"), _("Saturday"), _("Sunday"),
		]
		self._timer_days_clb = nvdaControls.CustomCheckListBox(
			self._timer_panel, choices=_timer_day_labels,
		)
		# Translators: Accessible name for the day-of-week checklist (same text as its static label).
		self._timer_days_clb.SetName(_("Active days:"))
		self._timer_days_clb.Checked = []
		self._timer_days_clb.Select(0)
		sizer.Add(self._timer_days_clb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._timer_days_label.Show(False)
		self._timer_days_clb.Show(False)

		self._timer_station_label = wx.StaticText(
			# Translators: Label for the station-selection list, used for the 'start radio' timer action (also used as its accessible name below).
			self._timer_panel, label=_("Station:")
		)
		sizer.Add(self._timer_station_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# Filter field for the timer station list.
		sizer.Add(
			# Translators: Label above the field that filters the timer station list below it.
			wx.StaticText(self._timer_panel, label=_("Filter:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._timer_station_filter = wx.TextCtrl(self._timer_panel)
		# Translators: Accessible name for the timer station filter field.
		self._timer_station_filter.SetName(_("Filter stations"))
		sizer.Add(self._timer_station_filter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# Use a ListBox instead of an editable ComboBox so screen readers
		# announce each item as the user navigates the list.
		self._timer_station_cb = wx.ListBox(
			self._timer_panel, style=wx.LB_SINGLE
		)
		self._timer_station_cb.SetMinSize((-1, 80))
		# Translators: Accessible name for the timer station list (same text as its static label above).
		self._timer_station_cb.SetName(_("Station:"))
		sizer.Add(self._timer_station_cb,    0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		# Translators: Button label; adds the configured timer to the pending-timers list below.
		self._timer_add_btn = wx.Button(self._timer_panel, label=_("&Add Timer"))
		sizer.Add(self._timer_add_btn, 0, wx.ALL, 8)

		sizer.Add(wx.StaticLine(self._timer_panel), 0, wx.EXPAND | wx.ALL, 4)

		# Translators: Label above the list of not-yet-fired timers.
		sizer.Add(wx.StaticText(self._timer_panel, label=_("Pending timers:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._timer_list = wx.ListBox(self._timer_panel, style=wx.LB_SINGLE)
		sizer.Add(self._timer_list, 1, wx.EXPAND | wx.ALL, 8)

		# Translators: Button label; deletes the selected pending timer.
		self._timer_del_btn = wx.Button(self._timer_panel, label=_("&Remove Selected Timer"))
		self._timer_del_btn.Enable(False)
		sizer.Add(self._timer_del_btn, 0, wx.LEFT | wx.BOTTOM, 8)

		self._timer_panel.SetSizer(sizer)

		self._timer_rb_start.Bind(wx.EVT_RADIOBUTTON, self._on_timer_action_changed)
		self._timer_rb_stop.Bind(wx.EVT_RADIOBUTTON,  self._on_timer_action_changed)
		self._timer_rec_once.Bind(wx.EVT_RADIOBUTTON,   self._on_timer_recurrence_changed)
		self._timer_rec_weekly.Bind(wx.EVT_RADIOBUTTON, self._on_timer_recurrence_changed)
		self._timer_add_btn.Bind(wx.EVT_BUTTON,        self._on_timer_add)
		self._timer_del_btn.Bind(wx.EVT_BUTTON,        self._on_timer_del)
		self._timer_list.Bind(wx.EVT_LISTBOX,          self._on_timer_selected)
		self._timer_list.Bind(wx.EVT_CHAR,             self._on_list_char)
		self._timer_station_cb.Bind(wx.EVT_SET_FOCUS,  self._on_timer_station_focus)
		# Filter field: rebuild the station list on every keystroke.
		self._timer_station_filter.Bind(wx.EVT_TEXT,     self._on_timer_station_filter_changed)
		# Allow Down arrow to move focus from the filter field into the list.
		self._timer_station_filter.Bind(wx.EVT_KEY_DOWN, self._on_timer_station_filter_key)
		# Type-ahead for the station listbox is handled in _on_char_hook.

		self._timer_stations = []
		self._timer_action_changed_update()


	def _active_list(self):
		sel = self._notebook.GetSelection()
		if sel == 1:
			return self._fav_list
		if sel == 5:  # Podcasts
			return self._episode_list
		return self._all_list

	def _resolve_station_from_combo(self, combo, station_list):
		"""Return the station object that matches the combo/listbox current selection.

		Supports both wx.ListBox and wx.ComboBox widgets.  For a ListBox,
		GetSelection() is always reliable.  For an editable ComboBox three
		strategies are tried in order:

		1. GetSelection() index — fast path when an item was chosen from the list.
		2. Case-insensitive exact match on GetValue() against station names.
		3. Case-insensitive prefix match (first station whose name starts with the
		   typed text) — lets users type just the beginning of a long name.

		Returns None when no station can be resolved.
		"""
		if not station_list:
			return None

		idx = combo.GetSelection()
		if idx != wx.NOT_FOUND and 0 <= idx < len(station_list):
			return station_list[idx]

		# ListBox has no GetValue(); fall back to None when the widget does not
		# support free-text input (i.e. it is a wx.ListBox, not a wx.ComboBox).
		if not hasattr(combo, "GetValue"):
			return None

		typed = combo.GetValue().strip().lower()
		if not typed:
			return None

		# Exact match first
		for s in station_list:
			if s.get("name", "").strip().lower() == typed:
				return s

		# Prefix match
		for s in station_list:
			if s.get("name", "").strip().lower().startswith(typed):
				return s

		return None

	def _apply_tab_side_effects(self, sel):
		"""Central handler for all side-effects that must run whenever the active
		notebook tab changes, regardless of whether the change was triggered by a
		wx.NotebookEvent (Ctrl+Tab, mouse click) or by a programmatic SetSelection
		call (Alt+1..5 shortcuts).

		Responsibilities:
		  - Show/hide action buttons that are irrelevant on the rec/timer/liked tabs.
		  - Trigger per-tab data refresh.
		  - Set _tab_just_switched so the focus handler can suppress redundant
		    screen-reader announcements.

		The Recording, Timer and Liked Songs refreshes are deferred via
		wx.CallLater(0) so that the tab panel is painted before the listbox/combo
		population runs.  Without this deferral the Clear()+Append() calls block
		the wx paint cycle and the tab switch feels sluggish.
		"""
		on_rec_or_timer = (sel in (2, 3, 4, 5, 6, 7))
		self._play_btn.Show(not on_rec_or_timer)
		self._fav_btn.Show(not on_rec_or_timer)
		self._del_btn.Show(not on_rec_or_timer)
		self._details_btn.Show(not on_rec_or_timer)
		self._add_btn.Show(not on_rec_or_timer)
		self.Layout()

		self._tab_just_switched = True
		if sel == 1:
			wx.CallLater(0, self._update_fav_button)
			wx.CallLater(0, self._update_save_audio_btn)
		elif sel == 2:
			wx.CallLater(0, self._refresh_sched_stations)
			wx.CallLater(0, self._refresh_sched_list)
		elif sel == 3:
			wx.CallLater(0, self._refresh_timer_stations)
			wx.CallLater(0, self._refresh_timer_list)
			# Defer focus change until after the tab panel is fully shown and
			# the refresh calls above have been queued, so focus isn't stolen
			# back by those refreshes.
			wx.CallLater(0, self._focus_timer_action_group)
		elif sel == 4:
			wx.CallLater(0, self._refresh_liked_list)
		elif sel == 5:
			# Populate the list from whatever is already on disk/in memory
			# first (fast, local, no network) so the tab never appears
			# empty while _refresh_all_podcast_feeds()'s background network
			# refresh (which only repopulates the list once it finishes) is
			# still in flight.
			wx.CallLater(0, self._refresh_podcast_list)
			wx.CallLater(0, self._refresh_all_podcast_feeds)
		elif sel == 6:
			wx.CallLater(0, self._refresh_getem_library_list)
		elif sel == 7:
			wx.CallLater(0, self._refresh_jukebox_list)
		if sel != 1 and hasattr(self, "_save_audio_btn"):
			self._save_audio_btn.Enable(False)

	def _focus_timer_action_group(self):
		"""When the Timer tab is opened, move focus to the Timer action
		(Start/Stop) radio buttons instead of the recurrence options."""
		if not self:
			return
		try:
			# Focus whichever radio button is currently selected so that
			# screen readers announce it as "checked" rather than "not checked".
			target = self._timer_rb_stop if self._timer_rb_stop.GetValue() else self._timer_rb_start
			target.SetFocus()
		except Exception:
			pass

	def _on_tab_changed_index(self, sel):
		"""Switch tab programmatically (e.g. Alt+1..5) and apply all side-effects.
		Also announces the new tab name to screen readers via ui.message, because
		wx.NotebookEvent is not fired for programmatic SetSelection calls.
		"""
		self._apply_tab_side_effects(sel)
		ui.message(self._notebook.GetPageText(sel))

	def _on_tab_changed(self, event):
		"""wx.EVT_NOTEBOOK_PAGE_CHANGED handler (user interaction / Ctrl+Tab).

		Guard against the wxAssertionError that fires when the Win32 tab-control
		item count is out of sync with wxNotebook's internal page list (typically
		happens if the dialog is shown/hidden very rapidly, e.g. via a double
		hotkey press).  If the notebook is in a corrupted state we skip the side-
		effects silently; _open_dialog() will detect the bad state on the next
		hotkey press and rebuild the dialog from scratch.
		"""
		try:
			sel = event.GetSelection()
			# A mismatch between wx's internal page list and the Win32 tab-control
			# produces GetPageCount() == 0 even though pages were added.  Bail out
			# early rather than letting _apply_tab_side_effects touch the notebook.
			if not self or self._notebook.GetPageCount() == 0:
				event.Skip()
				return
			self._apply_tab_side_effects(sel)
		except Exception:
			pass
		event.Skip()


	def refresh_audio_devices(self, force=False):
		"""Odśwież listę urządzeń audio w głównym oknie dodatku."""
		if getattr(self, "_audio_devices_loading", False):
			return
		now = time.monotonic()
		if not force and now - getattr(self, "_audio_devices_last_refresh", 0.0) < 1.0:
			return
		self._audio_devices_last_refresh = now
		self._audio_devices_loading = True
		threading.Thread(target=self._load_audio_devices, daemon=True).start()

	def _load_audio_devices(self):
		"""Get the device list from BASS in the background, transfer it to the Choice control."""
		devices = []
		try:
			devices = self._player.get_audio_devices()
		except Exception:
			pass
		wx.CallAfter(self._populate_audio_devices, devices)

	def _audio_device_name_for_index(self, device_index):
		for idx, name in self._dialog_audio_devices:
			if idx == device_index:
				return "" if idx == -1 else name
		return ""

	def _populate_audio_devices(self, devices):
		"""Fill the Choice control with the device list and select the saved one."""
		self._audio_devices_loading = False
		if not self or not self._device_choice:
			return
		# Translators: Same 'System default' first-entry convention as the main output-device picker (see audioDeviceMixin.py), used here to populate this dialog's own device list.
		new_devices = [(-1, _("System default"))] + list(devices)
		saved = config.conf["freeradio"].get("audio_device", -1)
		saved_name = config.conf["freeradio"].get("audio_device_name", "")
		resolved = saved
		match = "missing"
		try:
			resolved, resolved_name, match = self._player.resolve_audio_device(
				devices,
				saved,
				saved_name,
			)
		except Exception:
			resolved_name = saved_name
		if match == "name" and resolved != saved:
			config.conf["freeradio"]["audio_device"] = resolved
			config.conf["freeradio"]["audio_device_name"] = resolved_name
			try:
				actual = self._player.switch_output_device(resolved)
			except Exception:
				actual = getattr(self._player, "_output_device_index", resolved)
			if actual != resolved:
				config.conf["freeradio"]["audio_device"] = actual
				config.conf["freeradio"]["audio_device_name"] = ""
				for idx, name in new_devices:
					if idx == actual:
						config.conf["freeradio"]["audio_device_name"] = "" if idx == -1 else name
						break
				resolved = actual
		elif match == "index" and not saved_name and resolved != -1:
			config.conf["freeradio"]["audio_device_name"] = resolved_name
		sel = 0
		for i, (idx, _name) in enumerate(new_devices):
			if idx == resolved:
				sel = i
				break
		if new_devices != self._dialog_audio_devices:
			self._dialog_audio_devices = new_devices
			self._device_choice.Clear()
			for _idx, name in self._dialog_audio_devices:
				self._device_choice.Append(name)
		self._device_choice.SetSelection(sel)

	def _on_device_choice_focus(self, event):
		self.refresh_audio_devices()
		event.Skip()

	def _on_device_changed(self, event):
		"""When the user changes the device selection, apply it instantly and save it in the config."""
		sel = self._device_choice.GetSelection()
		if 0 <= sel < len(self._dialog_audio_devices):
			new_index, new_name = self._dialog_audio_devices[sel]
			if new_index == -1:
				new_name = ""
		else:
			new_index = -1
			new_name = ""
		config.conf["freeradio"]["audio_device"] = new_index
		config.conf["freeradio"]["audio_device_name"] = new_name
		try:
			actual = self._player.switch_output_device(new_index)
		except Exception:
			actual = getattr(self._player, "_output_device_index", new_index)
		if actual != new_index:
			config.conf["freeradio"]["audio_device"] = actual
			config.conf["freeradio"]["audio_device_name"] = self._audio_device_name_for_index(actual)
			for i, (idx, _name) in enumerate(self._dialog_audio_devices):
				if idx == actual:
					self._device_choice.SetSelection(i)
					break
		event.Skip()

	def _on_vol_changed(self, event):
		"""When the volume changes, instantly apply it to the player and save it in the config."""
		vol = self._vol_spin.GetValue()
		self._player.set_volume(vol)
		config.conf["freeradio"]["volume"] = min(100, vol)
		event.Skip()

	def _on_fx_focus(self, event):
		"""Tell the enabled/disabled status of an effect in the list when hovering over it."""
		idx = event.GetSelection()
		if idx != wx.NOT_FOUND:
			label = self._fx_choice.GetString(idx)
			is_checked = self._fx_choice.IsChecked(idx)
			# Translators: Effect on/off status spoken when hovering over an item in the Effects checklist; %(effect)s is the effect name, %(state)s the enabled/disabled word below.
			ui.message(_("%(effect)s %(state)s") % {
				"effect": label,
				# Translators: The two possible %(state)s values above, and in the two other identical announcements in _on_fx_changed/_toggle_fx_by_index below.
				"state": _("enabled") if is_checked else _("disabled"),
			})
		event.Skip()

	def _on_fx_changed(self, event):
		"""Instantly apply all checked effects and save them in the config."""
		idx = event.GetInt()
		is_checked = self._fx_choice.IsChecked(idx)
		label = self._fx_choice.GetString(idx)
		# Translators: Same effect on/off announcement as _on_fx_focus above, spoken here after actually toggling the effect (checklist click).
		ui.message(_("%(effect)s %(state)s") % {
			"effect": label,
			"state": _("enabled") if is_checked else _("disabled"),
		})
		checked = self._fx_choice.GetCheckedItems()
		active = [self._fx_keys[i] for i in checked if 0 <= i < len(self._fx_keys)]
		fx_str = ",".join(active) if active else "none"
		try:
			self._player.set_fx(fx_str)
		except Exception:
			pass
		config.conf["freeradio"]["audio_fx"] = fx_str
		self._update_eq_row_visibility(active)
		event.Skip()

	def _toggle_fx_by_index(self, idx):
		"""Toggle a single effect on/off via Ctrl+1..Ctrl+0, mirroring
		_on_fx_changed's apply/announce/save logic but driven by a keyboard
		shortcut instead of a checklist click."""
		if not (0 <= idx < len(self._fx_keys)):
			return
		is_checked = not self._fx_choice.IsChecked(idx)
		self._fx_choice.Check(idx, is_checked)
		label = self._fx_choice.GetString(idx)
		# Translators: Same effect on/off announcement, spoken here after toggling via the Ctrl+1..Ctrl+0 keyboard shortcuts.
		ui.message(_("%(effect)s %(state)s") % {
			"effect": label,
			"state": _("enabled") if is_checked else _("disabled"),
		})
		checked = self._fx_choice.GetCheckedItems()
		active = [self._fx_keys[i] for i in checked if 0 <= i < len(self._fx_keys)]
		fx_str = ",".join(active) if active else "none"
		try:
			self._player.set_fx(fx_str)
		except Exception:
			pass
		config.conf["freeradio"]["audio_fx"] = fx_str
		self._update_eq_row_visibility(active)

	def _update_eq_row_visibility(self, active_fx_list=None):
		"""Show EQ gain controls only for the EQ bands that are currently enabled."""
		if active_fx_list is None:
			checked = self._fx_choice.GetCheckedItems()
			active_fx_list = [self._fx_keys[i] for i in checked if 0 <= i < len(self._fx_keys)]
		eq_active = {k for k in active_fx_list if k in ("eq_bass", "eq_treble", "eq_vocal")}
		any_visible = False
		for band, _label, _default in self._eq_bands:
			spin = self._eq_spins[band]
			# Find the StaticText label widget for this spin (it's the sibling before it)
			visible = band in eq_active
			spin.Show(visible)
			# Also show/hide the label (StaticText) that precedes the spin in eq_row
			sizer = self._eq_row_sizer
			for i, item in enumerate(sizer.GetChildren()):
				wnd = item.GetWindow()
				if wnd is spin and i > 0:
					prev = sizer.GetChildren()[i - 1].GetWindow()
					if prev:
						prev.Show(visible)
			if visible:
				any_visible = True
		self.Layout()

	def _init_eq_gains(self):
		"""Apply saved EQ gain values to the player and set initial row visibility."""
		for band, _label, default_db in self._eq_bands:
			saved_db = config.conf["freeradio"].get("eq_gain_" + band, default_db)
			try:
				self._player.set_eq_gain(band, saved_db)
			except Exception:
				pass
		# Set row visibility based on currently saved active effects
		_saved_fx = config.conf["freeradio"].get("audio_fx", "none")
		active = [x.strip() for x in _saved_fx.split(",") if x.strip() != "none"]
		self._update_eq_row_visibility(active)

	def _on_eq_gain_changed(self, event, band):
		"""Instantly apply EQ gain change and save it to config."""
		gain_db = self._eq_spins[band].GetValue()
		config.conf["freeradio"]["eq_gain_" + band] = gain_db
		try:
			self._player.set_eq_gain(band, gain_db)
		except Exception:
			pass
		event.Skip()

	def _on_fav_list_focus(self, event):
		self._play_btn.SetDefault()
		if self._fav_list.GetSelection() == wx.NOT_FOUND and self._fav_list.GetCount() > 0:
			pending = getattr(self, "_fav_pending_name", "")
			idx = self._fav_list.FindString(pending) if pending else wx.NOT_FOUND
			self._fav_list.SetSelection(idx if idx != wx.NOT_FOUND else 0)
		if not getattr(self, "_tab_just_switched", False):
			# Translators: Spoken when the favourites list gains focus, reminding the user how the comma-to-reorder command works (see _handle_fav_move_x).
			ui.message(_("Press comma to pick a station, navigate to the target position, then press comma again to drop."))
		self._tab_just_switched = False
		event.Skip()

	def _on_fav_filter_changed(self, event):
		"""Rebuild the favourites list whenever the filter field changes.

		The list is repopulated in real time; the previous selection is restored
		when the station is still visible after filtering, so the user does not
		lose their place while editing the query.
		"""
		self._refresh_fav_list()
		# Announce how many results remain so screen-reader users get feedback.
		count = self._fav_list.GetCount()
		if count == 0:
			# Translators: Spoken when the favourites filter matches nothing.
			ui.message(_("No favourites found"))
		else:
			# Translators: Plural forms spoken after filtering the favourites list; %d is how many match.
			ui.message(ngettext("%d favourite", "%d favourites", count) % count)
		event.Skip()


	def _on_fav_filter_key(self, event):
		"""Handle key presses in the filter field.

		Down arrow moves focus to the favourites list (mirrors the behaviour of
		the search field on the All Stations tab).  All other keys are passed on.
		"""
		if event.GetKeyCode() == wx.WXK_DOWN:
			self._fav_list.SetFocus()
			if self._fav_list.GetCount() > 0 and self._fav_list.GetSelection() == wx.NOT_FOUND:
				self._fav_list.SetSelection(0)
		else:
			event.Skip()


	def _refresh_sched_stations(self):
		"""Populate the station listbox in the Recording tab from favourites.

		Preserves the current selection by station name so that a tab-switch
		refresh does not silently deselect the station the user had chosen.
		SetSelection is intentionally NOT called here: calling it while focus is
		on a different control causes Win32 to fire EVENT_OBJECT_SELECTION, which
		NVDA announces even though the listbox does not have focus.  Instead, the
		selection is applied lazily in _on_sched_station_focus when the user
		actually tabs into the listbox.
		"""
		favs = self._manager.get_favorites()
		# Apply the filter if the filter field exists and has text.
		query = getattr(self, "_sched_station_filter", None)
		query = query.GetValue().strip().lower() if query else ""
		filtered = [s for s in favs if not query or query in s.get("name", "").lower()] if query else list(favs)
		# Cache the filtered station list so _resolve_station_from_combo uses the right subset.
		self._sched_stations = filtered
		# Remember which station was selected before clearing the list.
		prev_idx = self._sched_station_cb.GetSelection()
		prev_name = (
			self._sched_station_cb.GetString(prev_idx)
			if prev_idx != wx.NOT_FOUND else ""
		)
		self._sched_station_cb.Clear()
		for s in filtered:
			self._sched_station_cb.Append(s.get("name", "?").strip())
		# Store the name to restore; the actual SetSelection is deferred to focus time.
		self._sched_station_pending_name = prev_name

	def _refresh_sched_list(self):
		"""Rebuild the scheduled recordings listbox.

		Each entry is a single line with station name first.  Recurring
		entries show the day pattern; one-off entries show the full date.
		  BBC Radio 4 — Every Monday, Saturday — 18:00, 60 min, Record only
		  TRT Radyo 1 — Every day — 20:00, 30 min, Listen and record
		  TRT FM — 15.06.2025 14:00 — 45 min, Record only
		"""
		_FULL_DAY_NAMES = [
			# Translators: Day names used when listing a recurring schedule's active days; see the format examples in this method's docstring above.
			_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
			_("Friday"), _("Saturday"), _("Sunday"),
		]

		self._sched_list.Clear()
		self._sched_index_map = []

		if not self._recorder:
			return

		for rec in self._recorder.get_schedules():
			station = rec.station.get("name", "?").strip()
			# Translators: Mode word used in each schedule-list line below (see the docstring's format examples): whether the recording plays out loud too, or is silent/record-only.
			mode    = _("Record only") if rec.record_only else _("Listen and record")

			if rec.recurrence != "once":
				days = sorted(rec.active_days) if rec.active_days else list(range(7))
				if days == list(range(7)):
					# Translators: Recurrence description shown when a weekly schedule has every day of the week checked (no day restriction).
					when = _("Every day")
				else:
					# Translators: Recurrence description shown when a weekly schedule is restricted to specific days; %s is a comma-joined list of day names from _FULL_DAY_NAMES above, e.g. 'Every Monday, Saturday'.
					when = _("Every %s") % ", ".join(_FULL_DAY_NAMES[d] for d in days)
				t    = rec.start_time.strftime("%H:%M")
				# Translators: One line of the scheduled-recordings list for a recurring entry; see the docstring's examples above for the exact layout ('Station — Every ... — HH:MM, N min, Mode').
				line = _("%s — %s — %s, %d min, %s") % (station, when, t, rec.duration_minutes, mode)
			else:
				ts   = rec.start_time.strftime("%d.%m.%Y %H:%M")
				line = "%s — %s — %d min, %s" % (station, ts, rec.duration_minutes, mode)

			self._sched_list.Append(line)
			self._sched_index_map.append(rec)

	def _on_sched_station_focus(self, event):
		"""Apply the pending selection when the station listbox actually gets focus.

		_refresh_sched_stations deliberately skips SetSelection to avoid
		Win32 firing EVENT_OBJECT_SELECTION (which NVDA announces) while
		focus is elsewhere.  We do it here instead, when the user has
		genuinely navigated to the listbox.
		"""
		if self._sched_station_cb.GetSelection() == wx.NOT_FOUND and self._sched_station_cb.GetCount() > 0:
			pending = getattr(self, "_sched_station_pending_name", "")
			idx = self._sched_station_cb.FindString(pending) if pending else wx.NOT_FOUND
			self._sched_station_cb.SetSelection(idx if idx != wx.NOT_FOUND else 0)
		event.Skip()


	def _on_sched_station_filter_changed(self, event):
		"""Rebuild the scheduled-recording station list whenever the filter changes."""
		self._refresh_sched_stations()
		count = self._sched_station_cb.GetCount()
		if count == 0:
			# Translators: Spoken when the recording-schedule station filter matches nothing.
			ui.message(_("No stations found"))
		else:
			# Translators: Plural forms spoken after filtering the recording-schedule station list; %d is how many match.
			ui.message(ngettext("%d station", "%d stations", count) % count)
		event.Skip()

	def _on_sched_station_filter_key(self, event):
		"""Down arrow moves focus from the filter field into the station list."""
		if event.GetKeyCode() == wx.WXK_DOWN:
			self._sched_station_cb.SetFocus()
			if self._sched_station_cb.GetCount() > 0 and self._sched_station_cb.GetSelection() == wx.NOT_FOUND:
				self._sched_station_cb.SetSelection(0)
		else:
			event.Skip()

	def _on_sched_recurrence_changed(self, event):
		"""Show/hide the active-days list based on recurrence mode."""
		# Day selection is always shown — in 'once' mode each checked day gets
		# its own one-off entry; in 'indefinite' mode the days restrict recurrence.
		self._sched_days_label.Show(True)
		self._sched_days_clb.Show(True)
		self._rec_panel.Layout()
		event.Skip()


	# _on_rec_btn removed entirely.

	def _on_sched_add(self, event):
		if not self._recorder:
			# Translators: Spoken when adding a schedule but the recorder subsystem failed to initialise.
			ui.message(_("Recording is not available"))
			return

		time_str = self._sched_time.GetValue().strip()
		try:
			parts = time_str.split(":")
			if len(parts) != 2:
				raise ValueError()
			hour, minute = int(parts[0]), int(parts[1])
			if not (0 <= hour <= 23 and 0 <= minute <= 59):
				raise ValueError()
		except (ValueError, IndexError):
			# Translators: Spoken when the typed start time doesn't parse as a valid HH:MM 24-hour time.
			ui.message(_("Invalid time format. Use HH:MM"))
			self._sched_time.SetFocus()
			return

		# --- Collect active days (0=Mon … 6=Sun) ---
		active_days = list(self._sched_days_clb.Checked)
		# If no days are checked, treat as all days active (no restriction).

		# --- Recurrence mode ---
		if self._sched_rec_indef.GetValue():
			recurrence      = "indefinite"
			max_occurrences = 0
		else:
			recurrence      = "once"
			max_occurrences = 0

		dur = self._sched_dur.GetValue()
		station = self._resolve_station_from_combo(
			self._sched_station_cb,
			getattr(self, "_sched_stations", []),
		)
		if station is None:
			# Translators: Spoken when trying to add a schedule with no station chosen in the list.
			ui.message(_("Please select a station"))
			return
		record_only = self._sched_mode_rec.GetValue()
		output_folder = _folder_picker_value(self._sched_folder_custom_rb, self._sched_folder_path)

		now = datetime.datetime.now()
		base = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

		if recurrence == "once" and active_days:
			# Create one entry per selected day, each scheduled for the next
			# occurrence of that weekday at the given time.
			all_conflict_names = []
			added_dates = []
			for weekday in sorted(active_days):
				# Find the next date that falls on this weekday.
				days_ahead = (weekday - now.weekday()) % 7
				candidate = base + datetime.timedelta(days=days_ahead)
				# If the candidate is in the past (same weekday, time already gone),
				# move to the following week.
				if candidate <= now:
					candidate += datetime.timedelta(days=7)
				_rec, conflict_names = self._recorder.add_schedule(
					station, candidate, dur,
					record_only=record_only,
					recurrence="once",
					active_days=[],
					max_occurrences=0,
					output_folder=output_folder,
				)
				added_dates.append(candidate.strftime("%d.%m.%Y"))
				if conflict_names:
					all_conflict_names.append(conflict_names)
			self._refresh_sched_list()
			record_only = _rec.record_only
			# Translators: Mode word used inside the 'Schedule added' announcement below: whether the recording plays out loud too, or is silent/record-only. Used for both the multi-date (once, several days checked) and single-date branches.
			mode_str = _("Record only") if record_only else _("Listen and record")
			# Translators: Confirmation spoken after adding a one-time schedule that expands to one entry per checked weekday; %(station)s is the station, %(time)s the HH:MM time, %(dates)s the comma-joined list of dates, %(mode)s the mode word above.
			ui.message(_("Schedule added: %(station)s at %(time)s on %(dates)s (%(mode)s)") % {
				"station": station.get("name", "?"),
				"time":    time_str,
				"dates":   ", ".join(added_dates),
				"mode":    mode_str,
			})
			if all_conflict_names:
				wx.CallAfter(
					wx.MessageBox,
					# Translators: Body of the warning dialog shown when one or more of the new schedule's dates overlaps an existing recording; %(names)s is a comma-joined list of the conflicting recordings' station names.
					_("Time conflict with: %(names)s. Switched to record-only mode.") % {
						"names": ", ".join(all_conflict_names)
					},
					# Translators: Title of the schedule-conflict warning dialog.
					_("Schedule Conflict"),
					wx.OK | wx.ICON_WARNING,
					self,
				)
		else:
			# Recurring mode, or once with no days selected.
			start = base
			if start <= now:
				candidate = start + datetime.timedelta(days=1)
				if active_days:
					for _day in range(7):
						if candidate.weekday() in active_days:
							break
						candidate += datetime.timedelta(days=1)
				start = candidate
			elif active_days and start.weekday() not in active_days:
				candidate = start + datetime.timedelta(days=1)
				for _day in range(7):
					if candidate.weekday() in active_days:
						break
					candidate += datetime.timedelta(days=1)
				start = candidate

			_rec, conflict_names = self._recorder.add_schedule(
				station, start, dur,
				record_only=record_only,
				recurrence=recurrence,
				active_days=active_days,
				max_occurrences=max_occurrences,
				output_folder=output_folder,
			)
			self._refresh_sched_list()
			record_only = _rec.record_only
			# Translators: Same mode word as in the multi-date branch above, reused here for the single-date scheduling branch.
			mode_str = _("Record only") if record_only else _("Listen and record")
			date_str = start.strftime("%d.%m.%Y")
			# Translators: Confirmation spoken after adding a single (non-multi-date) schedule; %(station)s is the station, %(date)s the date, %(time)s the HH:MM time, %(mode)s the mode word from above.
			ui.message(_("Schedule added: %(station)s on %(date)s at %(time)s (%(mode)s)") % {
				"station": station.get("name", "?"), "date": date_str, "time": time_str, "mode": mode_str
			})
			if conflict_names:
				wx.CallAfter(
					wx.MessageBox,
					# Translators: Same conflict-warning message as above, used in the single-date scheduling branch; %(names)s is the conflicting recording(s).
					_("Time conflict with: %(names)s. Switched to record-only mode.") % {"names": conflict_names},
					# Translators: Same dialog title as above, reused in the single-date scheduling branch.
					_("Schedule Conflict"),
					wx.OK | wx.ICON_WARNING,
					self,
				)

	def _on_sched_del(self, event):
		if not self._recorder:
			return
		idx = self._sched_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		index_map = getattr(self, "_sched_index_map", [])
		if idx >= len(index_map):
			return
		self._recorder.remove_schedule(index_map[idx])
		self._refresh_sched_list()
		# Select whatever now sits at the removed position (i.e. the item
		# that followed it) or, if it was the last item, whatever is now
		# last (i.e. the item that preceded it).
		count = self._sched_list.GetCount()
		if count:
			new_idx = idx if idx < count else count - 1
			self._sched_list.SetSelection(new_idx)
			self._on_sched_selected(None)
		# Translators: Spoken after deleting a scheduled recording.
		ui.message(_("Schedule deleted"))

	def _on_sched_edit(self, event):
		if not self._recorder:
			return
		idx = self._sched_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		index_map = getattr(self, "_sched_index_map", [])
		if idx >= len(index_map):
			return
		rec = index_map[idx]
		dlg = EditScheduleDialog(self, rec)
		if dlg.ShowModal() == wx.ID_OK:
			updated = dlg.get_values()
			# Apply, re-sort and snapshot atomically with respect to the
			# scheduler thread.  Persist only after releasing the schedule lock
			# to keep the lock order consistent with Recorder._persist_schedules().
			with self._recorder._scheduled_lock:
				rec.start_time       = updated["start_time"]
				rec.duration_minutes = updated["duration_minutes"]
				rec.recurrence       = updated["recurrence"]
				rec.active_days      = updated["active_days"]
				rec.max_occurrences  = updated["max_occurrences"]
				rec.record_only      = updated["record_only"]
				rec.output_folder    = updated["output_folder"]
				rec.fired            = False   # reset so scheduler picks it up again
				self._recorder._scheduled.sort(key=lambda r: r.start_time)
			self._recorder._persist_schedules()
			self._refresh_sched_list()
			# Translators: Spoken after saving changes in EditScheduleDialog.
			ui.message(_("Schedule updated"))
		dlg.Destroy()

	def _on_sched_selected(self, event):
		pass

	def _on_sched_list_key(self, event):
		"""Scheduled recordings list — Delete/Shift+Delete remove the selected
		schedule directly; Applications key / Shift+F10 opens the context
		menu that also carries Edit/Remove (see _show_sched_context_menu)."""
		key = event.GetKeyCode()
		if key == wx.WXK_DELETE:
			self._on_sched_del(event)
			return
		if key == wx.WXK_WINDOWS_MENU or (key == wx.WXK_F10 and event.ShiftDown()):
			self._show_sched_context_menu()
			return
		event.Skip()

	def _show_sched_context_menu(self):
		"""Context menu for the selected item in the scheduled recordings
		list — carries the Edit/Remove actions that used to live on
		dedicated buttons."""
		idx = self._sched_list.GetSelection()
		index_map = getattr(self, "_sched_index_map", [])
		has_selection = idx != wx.NOT_FOUND and idx < len(index_map)

		menu = wx.Menu()

		# Translators: Context-menu item; opens EditScheduleDialog for the selected scheduled recording.
		item_edit = menu.Append(wx.ID_ANY, _("&Edit Selected"))
		item_edit.Enable(has_selection)
		self.Bind(wx.EVT_MENU, self._on_sched_edit, item_edit)

		# Translators: Context-menu item; deletes the selected scheduled recording.
		item_remove = menu.Append(wx.ID_ANY, _("&Remove Selected"))
		item_remove.Enable(has_selection)
		self.Bind(wx.EVT_MENU, self._on_sched_del, item_remove)

		self.PopupMenu(menu, self._sched_list.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()



	def _fetch_all(self):
		import threading as _threading
		RadioBrowserError = _radio_browser_error()

		stations_top     = [None]
		stations_country = [None]

		def fetch_top():
			try:
				stations_top[0] = self._manager.get_top_stations(limit=1000)
			except RadioBrowserError as exc:
				import logging
				logging.getLogger(__name__).warning("FreeRadio: fetch_top failed: %s", exc)

		def fetch_country():
			try:
				cc = self._manager.get_user_countrycode()
				if cc:
					result = self._manager.get_stations_by_country(cc)
					# It can return a tuple of the form (stations, total_count) from the API.
					# We just take the first [0] element, which is the list of stations.
					stations_country[0] = result[0] if isinstance(result, tuple) else result
			except RadioBrowserError as exc:
				import logging
				logging.getLogger(__name__).warning("FreeRadio: fetch_country failed: %s", exc)

		t1 = _threading.Thread(target=fetch_top,     daemon=True)
		t2 = _threading.Thread(target=fetch_country, daemon=True)
		t1.start(); t2.start()
		t1.join();  t2.join()

		if stations_top[0] is None:
			wx.CallAfter(self._show_error)
			return

		seen     = {}
		combined = []
		for s in (stations_country[0] or []) + stations_top[0]:
			uid = s.get("stationuuid", "")
			if uid and uid not in seen:
				seen[uid] = True
				combined.append(s)

		favs = self._manager.get_favorites()
		fav_uids = {s.get("stationuuid") for s in combined}
		for fav in favs:
			if fav.get("stationuuid") not in fav_uids:
				combined.insert(0, fav)

		wx.CallAfter(
			self._on_stations_merged,
			combined,
			# Translators: Status text shown on the Favourites/other tabs' station combo boxes while the initial top-stations list is still loading; %d is how many have loaded so far.
			_("Top stations (%d)") % len(combined),
		)

	def _on_refresh_catalog(self, event):
		"""Manually re-sync the local station list cache from the Radio
		Browser API, instead of waiting for the periodic background refresh."""
		if self._manager.is_syncing():
			# Translators: Spoken if the Update Station List button/command is used while a refresh is already running.
			ui.message(_("Station list refresh already in progress"))
			return
		self._refresh_catalog_btn.Disable()
		# Translators: Spoken when a manual catalog refresh starts.
		ui.message(_("Refreshing station list from the server..."))
		# Translators: Status-line text (shorter than the spoken announcement above) shown while the manual refresh is running.
		self._status.SetLabel(_("Refreshing station list..."))

		def _done():
			wx.CallAfter(self._on_catalog_refreshed)

		self._manager.refresh_catalog_async(on_done=_done)

	def _on_catalog_refreshed(self):
		if not self:
			return
		self._refresh_catalog_btn.Enable()
		# Translators: Spoken when a manual catalog refresh finishes successfully.
		ui.message(_("Station list updated"))
		# Translators: Status-line text shown after a manual catalog refresh finishes.
		self._status.SetLabel(_("Station list updated."))
		# Re-run whatever is currently shown so results reflect the new list.
		query = self._search.GetValue().strip()
		if query:
			self._schedule_search(query)
		else:
			threading.Thread(target=self._fetch_all, daemon=True).start()

	def _prepopulate_country_combo(self):
		"""As soon as the dialog opens, add all countries from the local dictionary to the combo.
		API response is not expected; All countries are visible even if there is no network connection."""
		all_names = sorted(country_name(code) for code in _COUNTRY_NAMES)
		# Translators: Initial population of the country combo with the same 'All' first-entry convention as _populate_country_combo.
		self._country_cb.Set([_("All")] + all_names)
		self._country_cb.SetSelection(0)

	def _fetch_countries(self):
		"""Pull all countries from the API and pre-populate the country combo."""
		RadioBrowserError = _radio_browser_error()
		try:
			countries_data = self._manager.get_countries()
		except RadioBrowserError as exc:
			import logging
			logging.getLogger(__name__).warning("FreeRadio: _fetch_countries failed: %s", exc)
			return
		if not countries_data or not self:
			return
		names = []
		counts = {}
		for c in countries_data:
			code = c.get("iso_3166_1", "").strip().upper()
			if not code:
				code = c.get("name", "").strip().upper()
			count = int(c.get("stationcount", 0) or 0)
			if len(code) == 2 and count > 0:
				names.append(_country_name(code))
				counts[code] = count
		names = sorted(set(names))
		wx.CallAfter(self._populate_country_combo, names, counts)

	def _populate_country_combo(self, all_country_names, counts=None):
		if not self:
			return
		if counts:
			self._country_station_counts.update(counts)
		cur = self._country_cb.GetStringSelection()
		# Translators: Same 'All' entry as the country combo's first item on the All Stations tab, excluded here while merging newly-seen country names into this combo's choices.
		existing = set(self._country_cb.GetStrings()) - {_("All")}
		merged = sorted(existing | set(all_country_names))
		# Translators: Rebuilds this combo's choice list with 'All' first, followed by the merged/sorted country names.
		self._country_cb.Set([_("All")] + merged)
		ci = self._country_cb.FindString(cur)
		self._country_cb.SetSelection(ci if ci != wx.NOT_FOUND else 0)

	def _on_stations_merged(self, new_stations, status_text):
		if not self:
			return
		seen = {s.get("stationuuid") for s in self._all_stations}
		for s in new_stations:
			uid = s.get("stationuuid")
			if uid not in seen:
				self._all_stations.append(s)
				seen.add(uid)

		self._apply_filters(status_text)
		self._refresh_fav_list()

	def _apply_filters(self, status_override=None, announce=False):
		text = self._search.GetValue().strip()
		ci   = self._country_cb.GetSelection()
		sel_country = "" if ci <= 0 else self._country_cb.GetString(ci)

		# All pool: local + country data + text search
		pool = self._all_stations + self._extra_stations + self._search_stations

		result = []
		seen   = set()
		for s in pool:
			uid = s.get("stationuuid", "")
			if uid in seen:
				continue
			seen.add(uid)
			if sel_country and _country_name(s.get("countrycode", "")) != sel_country:
				continue
			if text and not _matches_query(s, text):
				continue
			result.append(s)

		if getattr(self, "_sort_cb", None) and self._sort_cb.GetSelection() == 1:
			result.sort(key=lambda s: s.get("votes", 0), reverse=True)
		else:
			result.sort(key=_tr_sort_key)
		self._stations = result
		self._all_list.Clear()
		for s in result:
			self._all_list.Append(_station_label(s))

		text = self._search.GetValue().strip()
		if sel_country and text:
			# Translators: Status-line text on the All Stations tab when both a search term and a country filter are active; %(query)s is the typed search text, %(country)s the selected country, %(count)d the number of matching stations.
			label = _("\"%(query)s\" in %(country)s: %(count)d") % {"query": text, "country": sel_country, "count": len(result)}
		elif sel_country:
			# Translators: Status-line text when only a country filter is active (no search text); %(count)d is the number of stations, %(country)s the selected country.
			label = _("%(count)d stations in %(country)s") % {"count": len(result), "country": sel_country}
		elif text:
			# Translators: Status-line text when only a search term is active (no country filter); %(query)s is the typed search text, %(count)d the number of matches.
			label = _("\"%(query)s\": %(count)d") % {"query": text, "count": len(result)}
		else:
			# Translators: Status-line text when neither a search term nor a country filter is active; %(count)d is the total number of stations shown.
			label = _("%(count)d stations") % {"count": len(result)}
			
		# Append a hint when the displayed count equals the configured limit.
		# Only issue a limit warning if a search or country filter is active.
		user_limit = config.conf["freeradio"].get("result_limit", 1000)
		is_filtered = bool(sel_country or text)
		
		if is_filtered and len(result) >= user_limit and not status_override:
			# For country filters, _total_found comes from the stationcount cache
			# (limit-independent). For text searches, search_stations fetches up to
			# 50000 results internally so total_found is also reliable.
			total = (
				self._total_found
				if self._total_found and self._total_found > len(result)
				else None
			)
			if total:
				# Translators: Appended to the status line when the result-limit cap was hit but the true total is known; %(shown)d is how many are displayed, %(total)d the actual total available.
				label += " " + _("(%(shown)d of %(total)d shown — increase result limit to see more)") % {"shown": len(result), "total": total}
			else:
				# Translators: Appended to the status line when the result-limit cap was hit and the true total isn't known.
				label += " " + _("(limit reached — increase result limit to see more)")
			
		if status_override and not result:
			label = status_override
			
		self._status.SetLabel(label)
		if announce:
			ui.message(label)

	def _refresh_fav_list(self):
		"""Repopulate the favourites list, applying the filter field if non-empty.

		Keeps the current selection on the same station (by stationuuid) when
		possible so that typing in the filter box does not jump the selection.
		"""
		# Remember which station is currently selected so we can restore it.
		prev_sel = self._fav_list.GetSelection()
		prev_uuid = None
		if prev_sel != wx.NOT_FOUND and prev_sel < len(getattr(self, "_fav_filtered", [])):
			prev_uuid = self._fav_filtered[prev_sel].get("stationuuid")

		query = getattr(self, "_fav_filter", None)
		query = query.GetValue().strip() if query else ""

		favs = self._manager.get_favorites()

		if query:
			filtered = [s for s in favs if _matches_favorites_query(s, query)]
		else:
			filtered = list(favs)

		# Cache filtered list so key handlers can map list indices back to stations.
		self._fav_filtered = filtered

		self._fav_list.Clear()
		for s in filtered:
			label = self._fav_display_label(s, s.get("stationuuid") in self._fav_marked)
			self._fav_list.Append(label)

		# Restore selection: prefer the previously selected station; fall back to 0.
		if filtered:
			restore = 0
			if prev_uuid:
				for i, s in enumerate(filtered):
					if s.get("stationuuid") == prev_uuid:
						restore = i
						break
			self._fav_list.SetSelection(restore)

		self._update_fav_button()
		self._update_save_audio_btn()

	def _refresh_fav_list_no_select(self):
		"""Used in tab switching: populates the list but does not call SetSelection.

		SetSelection sends Windows EVENT_OBJECT_SELECTION to NVDA's list,
		causing it to announce; This is not desired when reading the tab name.
		The pending selection is applied lazily in _on_fav_list_focus.
		"""
		query = getattr(self, "_fav_filter", None)
		query = query.GetValue().strip() if query else ""

		favs = self._manager.get_favorites()

		if query:
			filtered = [s for s in favs if _matches_favorites_query(s, query)]
		else:
			filtered = list(favs)

		self._fav_filtered = filtered

		# Remember current selection before clearing, so focus handler can restore it.
		prev_sel = self._fav_list.GetSelection()
		self._fav_pending_name = (
			self._fav_list.GetString(prev_sel)
			if prev_sel != wx.NOT_FOUND else ""
		)

		self._fav_list.Clear()
		for s in filtered:
			label = self._fav_display_label(s, s.get("stationuuid") in self._fav_marked)
			self._fav_list.Append(label)
		self._update_fav_button()

	def _show_error(self):
		if not self:
			return
		# Translators: Status-line text shown on the All Stations tab when the Radio Browser API is unreachable.
		self._status.SetLabel(_("Could not connect to radio directory. Check your internet connection."))
		self._all_list.Clear()
		self._stations = []


	def _schedule_search(self, query):
		"""Cancel any pending search timer and schedule a new debounced API search.

		Reads the currently selected country from the combo box so the results
		are always scoped to whatever country is active at call time.
		"""
		if self._search_debounce_timer:
			try:
				self._search_debounce_timer.Stop()
			except Exception:
				pass
			self._search_debounce_timer = None

		self._search_fetch_id += 1
		fetch_id = self._search_fetch_id

		ci = self._country_cb.GetSelection()
		selected_country = name_to_code(self._country_cb.GetString(ci)) if ci > 0 else None
		user_limit = config.conf["freeradio"].get("result_limit", 1000)

		def _do_search():
			self._search_debounce_timer = None
			if not self or fetch_id != self._search_fetch_id:
				return
			try:
				stations, total_found = self._manager.search_stations(query, limit=user_limit, countrycode=selected_country)
			except Exception:
				stations, total_found = [], 0
			if not self or fetch_id != self._search_fetch_id:
				return
			
			# Status override parameter is passed as None so _apply_filters 
			# can use its own consistent "limit reached" message logic.
			wx.CallAfter(self._on_search_results, stations, None, fetch_id, total_found)

			# TuneIn and iHeartRadio are fetched on their own background
			# thread EACH (not one combined call) so that a slow or
			# unreachable source — e.g. iHeart failing outright on networks
			# where it's blocked — never delays the other source's results
			# from showing up.
			def _make_external_fetcher(search_fn):
				def _fetch():
					try:
						extra = search_fn(query, limit=50)
					except Exception:
						extra = []
					if not self or fetch_id != self._search_fetch_id or not extra:
						return
					wx.CallAfter(self._on_external_search_results, extra, fetch_id)
				return _fetch

			threading.Thread(
				target=_make_external_fetcher(self._manager.search_tunein), daemon=True
			).start()
			threading.Thread(
				target=_make_external_fetcher(self._manager.search_iheart), daemon=True
			).start()

		self._search_debounce_timer = wx.CallLater(500, _do_search)

	def _on_text_changed(self, event):
		query = self._search.GetValue().strip()
		if not query:
			# Search box cleared: cancel any pending timer and show unfiltered results.
			if self._search_debounce_timer:
				try:
					self._search_debounce_timer.Stop()
				except Exception:
					pass
				self._search_debounce_timer = None
			self._search_stations = []
			self._apply_filters()
			event.Skip()
			return
		self._schedule_search(query)
		event.Skip()

	def _typeahead(self, ch, get_count, get_string, get_sel, set_sel, fire_evt, state_attr, fire_on_reset=False):
		"""Windows Explorer type-ahead.

		Single character:
		  - Always advance to the next match after the current position (wraps around).
		  - This means pressing "a" always moves forward, even if the current item
		    already starts with "a".

		Multiple characters typed quickly (before the reset timer fires):
		  - The search starts from the position recorded before the typing sequence began (anchor).
		  - This prevents e.g. typing "tu" from jumping past the intended match: "t" may move
		    the selection to an intermediate item, but the following "u" searches from the
		    original anchor rather than from that intermediate position.
		  - If the extended prefix has no match, fall back to the new character alone
		    and search from the anchor.

		Note: due to wx event ordering, SetSelection may not be reflected yet in the
		next EVT_CHAR call. The last matched index and the anchor are therefore tracked
		in instance state rather than read back from the widget.
		"""
		timer_attr  = state_attr + "_timer"
		str_attr    = state_attr + "_str"
		cur_attr    = state_attr + "_cur"     # index of the last matched item
		anchor_attr = state_attr + "_anchor"  # selection index before the typing sequence started

		timer = getattr(self, timer_attr, None)
		if timer:
			try:
				timer.Stop()
			except Exception:
				pass

		prev    = getattr(self, str_attr, "")
		buf     = prev + ch
		count   = get_count()

		# Use our own tracked current rather than relying on wx selection state.
		current = getattr(self, cur_attr, None)
		if current is None:
			current = get_sel()

		# Anchor: recorded once on the first character of a typing sequence;
		# unchanged for subsequent characters; cleared when the reset timer fires.
		anchor = getattr(self, anchor_attr, None)
		if anchor is None:
			anchor = current if (current is not None and current != wx.NOT_FOUND) else 0
			setattr(self, anchor_attr, anchor)

		if len(buf) == 1:
			# Single character: search forward from the item after the current one.
			# This way the user always moves *past* the current position, regardless
			# of whether the current item starts with this character or not.
			# If no match is found wrapping around, fall back to index 0.
			if current is not None and current != wx.NOT_FOUND and 0 <= current < count:
				start = (current + 1) % count
			else:
				start = 0
		else:
			# Multi-character prefix: always search forward from anchor + 1.
			# This ensures that each additional character narrows the search
			# relative to where the user was before typing started, not relative
			# to where the previous character happened to land.
			start = (anchor + 1) % count

		match = wx.NOT_FOUND
		for offset in range(count):
			i = (start + offset) % count
			if get_string(i).lower().startswith(buf):
				match = i
				break

		if match == wx.NOT_FOUND and len(buf) > 1:
			# Extended prefix found no match — retry with just the new character from anchor.
			buf = ch
			start = (anchor + 1) % count
			for offset in range(count):
				i = (start + offset) % count
				if get_string(i).lower().startswith(buf):
					match = i
					break

		setattr(self, str_attr, buf)

		if match != wx.NOT_FOUND:
			setattr(self, cur_attr, match)
			set_sel(match)
			if not fire_on_reset:
				fire_evt()

		def _reset():
			setattr(self, str_attr,    "")
			setattr(self, timer_attr,  None)
			setattr(self, cur_attr,    None)
			setattr(self, anchor_attr, None)
			if fire_on_reset:
				fire_evt()
		setattr(self, timer_attr, wx.CallLater(600, _reset))

	def _typeahead_listboxes(self):
		"""Return every listbox that supports type-ahead, paired with its
		own state attribute name.

		Kept as a single central list because both _do_list_typeahead() and
		_on_char_hook() read from the same mapping; adding a new listbox
		only requires one line here. Each listbox having its own state
		attribute means a character typed in one list never pollutes
		another list's search buffer / current index / anchor.
		"""
		return (
			(self._all_list,               "_list_search_all"),
			(self._fav_list,               "_list_search_fav"),
			(self._sched_list,             "_list_search_sched"),
			(self._sched_station_cb,       "_list_search_sched_station"),
			(self._timer_list,             "_list_search_timer"),
			(self._timer_station_cb,       "_list_search_timer_station"),
			(self._liked_list,             "_list_search_liked"),
			(self._podcast_list,           "_list_search_podcast"),
			(self._podcast_results,        "_list_search_podcast_results"),
			(self._podcast_preview_list,   "_list_search_podcast_preview"),
			(self._episode_list,           "_list_search_episode"),
			(self._getem_results,          "_list_search_getem_results"),
			(self._getem_library_ctrl,     "_list_search_getem_library"),
			(self._jukebox_search_results, "_list_search_jukebox_results"),
			(self._jukebox_list,           "_list_search_jukebox"),
			(self._jukebox_tracks_list,    "_list_search_jukebox_tracks"),
		)

	def _on_country_char(self, event):
		"""Type-ahead search for the country combo box.

		Matches standard Windows Explorer list behaviour:
		- Single char: jump to first match; if already on a match, advance to next.
		- Multiple chars typed quickly (within 600 ms s): prefix search.
		"""
		key = event.GetUnicodeKey()
		# See _on_list_char for why space (32) is excluded rather than
		# included. The country combo has no Space action of its own, but
		# keeping the two checks identical avoids surprise later if one is
		# changed without the other.
		if key == wx.WXK_NONE or key <= 32:
			event.Skip()
			return

		# GetUnicodeKey() may return WXK_NONE for some non-ASCII keys on
		# certain keyboard layouts; fall back to GetKeyCode() in that case.
		ch = chr(key).lower() if key != wx.WXK_NONE else chr(event.GetKeyCode()).lower()
		if not ch.isprintable():
			event.Skip()
			return
		self._typeahead(
			ch           = ch,
			get_count    = self._country_cb.GetCount,
			get_string   = self._country_cb.GetString,
			get_sel      = self._country_cb.GetSelection,
			set_sel      = self._country_cb.SetSelection,
			fire_evt     = lambda: wx.PostEvent(
				self._country_cb,
				wx.CommandEvent(wx.EVT_COMBOBOX.typeId, self._country_cb.GetId())),
			state_attr   = "_country_search",
			fire_on_reset = True,
		)

	def _reset_country_search(self):
		self._country_search_str   = ""
		self._country_search_timer = None

	def _do_list_typeahead(self, listbox, ch):
		"""Core type-ahead dispatch shared by _on_list_char and
		_on_char_hook.

		Each listbox gets its own isolated state so that typing in one
		list never pollutes the search string, current index, or anchor
		of another. See _typeahead_listboxes() for the authoritative
		mapping.
		"""
		state_attr = "_list_search_all"
		for lb, attr in self._typeahead_listboxes():
			if lb is listbox:
				state_attr = attr
				break
		self._typeahead(
			ch         = ch,
			get_count  = listbox.GetCount,
			get_string = listbox.GetString,
			get_sel    = listbox.GetSelection,
			set_sel    = listbox.SetSelection,
			fire_evt   = lambda: wx.PostEvent(
				listbox,
				wx.CommandEvent(wx.EVT_LISTBOX.typeId, listbox.GetId())),
			state_attr = state_attr,
		)

	def _on_list_char(self, event):
		"""Type-ahead search for _all_list and _fav_list via EVT_CHAR.

		For _sched_list, _timer_list and _liked_list the type-ahead is handled
		earlier in _on_char_hook so that the native Windows ListBox character
		handler never gets a chance to interfere.

		Matches standard Windows Explorer list behaviour:
		- Single char: jump to first match after current position; wraps around.
		- Multiple chars typed quickly (within 600 ms): prefix search.
		"""
		key = event.GetUnicodeKey()
		# Strictly less than or equal to 32: space (32) is excluded here too,
		# so it never reaches the type-ahead buffer even if EVT_CHAR somehow
		# fires for it (some wx builds still dispatch EVT_CHAR after a
		# handled EVT_KEY_DOWN). Space is a play/pause action key on several
		# lists - see _on_list_key / _on_fav_list_key.
		if key == wx.WXK_NONE or key <= 32:
			event.Skip()
			return

		listbox = event.GetEventObject()
		# GetUnicodeKey() may return WXK_NONE for some non-ASCII keys on
		# certain keyboard layouts; fall back to GetKeyCode() in that case.
		ch = chr(key).lower() if key != wx.WXK_NONE else chr(event.GetKeyCode()).lower()
		if not ch.isprintable():
			event.Skip()
			return

		self._do_list_typeahead(listbox, ch)

	def _reset_list_search(self):
		self._list_search_str   = ""
		self._list_search_timer = None

	def _on_limit_changed(self, event):
		"""Save the new result limit to config and re-trigger search/country fetch."""
		limit = self._limit_spin.GetValue()
		config.conf["freeradio"]["result_limit"] = limit
		# Re-run the active search or country fetch with the new limit.
		query = self._search.GetValue().strip()
		if query:
			self._search_stations = []
			self._schedule_search(query)
		else:
			ci = self._country_cb.GetSelection()
			if ci > 0:
				# Simulate a combo change to re-fetch with the new limit.
				self._extra_stations = []
				wx.PostEvent(
					self._country_cb,
					wx.CommandEvent(wx.EVT_COMBOBOX.typeId, self._country_cb.GetId()),
				)
			else:
				self._apply_filters()

	def _on_sort_changed(self, event):
		"""Re-apply filters with the newly selected sort order."""
		self._apply_filters()

	def _on_combo_changed(self, event):
		if not self._all_stations:
			event.Skip()
			return

		ci = self._country_cb.GetSelection()
		sel_country = "" if ci <= 0 else self._country_cb.GetString(ci)

		if not sel_country:
			if self._combo_debounce_timer is not None:
				try:
					self._combo_debounce_timer.Stop()
				except Exception:
					pass
				self._combo_debounce_timer = None
			self._extra_stations = []
			# If there is an active search query, re-run it without a country filter.
			# Suppress the intermediate announce here; _on_search_results will announce
			# the final result once the new search completes, avoiding double/triple
			# NVDA speech (e.g. "35 stations" -> "All" -> '"blues": 462').
			query = self._search.GetValue().strip()
			if query:
				self._search_stations = []
				self._apply_filters(announce=False)
				self._schedule_search(query)
			else:
				self._apply_filters(announce=True)
			event.Skip()
			return

		# New country selected: clear old country stations first
		self._extra_stations = []

		# Debounce: cancel previous timer
		if self._combo_debounce_timer is not None:
			try:
				self._combo_debounce_timer.Stop()
			except Exception:
				pass
			self._combo_debounce_timer = None

		self._combo_fetch_id += 1
		fetch_id = self._combo_fetch_id
		country_snap = sel_country

		def _do_fetch():
			self._combo_debounce_timer = None
			if not self or fetch_id != self._combo_fetch_id:
				return
			user_limit = config.conf["freeradio"].get("result_limit", 1000)

			def fetch():
				RadioBrowserError = _radio_browser_error()
				country_code = name_to_code(country_snap)
				try:
					results, total_found = self._manager.get_stations_by_country(
						country_code, limit=user_limit,
					)
					results = results[:user_limit]
				except RadioBrowserError:
					return
				if not self or fetch_id != self._combo_fetch_id:
					return
				wx.CallAfter(self._on_combo_fetch_done, results, total_found, fetch_id)

			threading.Thread(target=fetch, daemon=True).start()

		self._combo_debounce_timer = wx.CallLater(self._COMBO_DEBOUNCE_MS, _do_fetch)
		event.Skip()

	def _on_combo_fetch_done(self, new_stations, total_found, fetch_id):
		if not self or fetch_id != self._combo_fetch_id:
			return
		
		query = self._search.GetValue().strip()
		has_query = bool(query)
		
		self._extra_stations = new_stations or []
		# Prefer the cached stationcount from _fetch_countries (accurate, limit-independent).
		# Fall back to total_found from the API response only if the cache has no entry.
		ci = self._country_cb.GetSelection()
		if ci > 0:
			sel_country = self._country_cb.GetString(ci)
			cc = name_to_code(sel_country)
			cached = self._country_station_counts.get(cc.upper()) if cc else None
			self._total_found = cached if cached else total_found
		else:
			self._total_found = total_found
		
		# Apply filters. If there is no search query, this will automatically
		# append and announce the standard "limit reached" message if needed.
		# If there is a search query, we suppress the announcement to avoid double speech.
		self._apply_filters(announce=not has_query)

		# If an active search query exists, re-run the search scoped to the new country.
		if has_query:
			self._search_stations = []
			self._schedule_search(query)

	def _on_search_results(self, stations, status_text, fetch_id=None, total_found=None):
		if not self:
			return
		if fetch_id is not None and fetch_id != self._search_fetch_id:
			return
		self._search_stations = stations
		if total_found is not None:
			self._total_found = total_found
		self._apply_filters(status_text, announce=True)
		self._refresh_fav_list()

	def _on_external_search_results(self, extra_stations, fetch_id):
		"""Merge TuneIn/iHeartRadio results into the currently displayed
		Radio Browser search results once they arrive. Announced (spoken)
		like any other result update — this is the last count the user
		would otherwise hear, since it happens after the initial Radio
		Browser announcement from _on_search_results."""
		if not self or fetch_id != self._search_fetch_id or not extra_stations:
			return
		existing_uuids = {s.get("stationuuid", "") for s in self._search_stations}
		new_ones = [s for s in extra_stations if s.get("stationuuid", "") not in existing_uuids]
		if not new_ones:
			return
		self._search_stations = self._search_stations + new_ones
		self._apply_filters(announce=True)
		self._refresh_fav_list()


	def _get_selected_station(self):
		lst = self._active_list()
		idx = lst.GetSelection()
		if idx == wx.NOT_FOUND:
			return None, -1
		if self._notebook.GetSelection() == 1:  # Favourites
			# Use _fav_filtered so the index matches the (possibly filtered) list
			# that is currently displayed.  Fall back to full favourites list when
			# the filter has not been applied yet (e.g. during initialisation).
			favs = getattr(self, "_fav_filtered", None)
			if favs is None:
				favs = self._manager.get_favorites()
			if idx >= len(favs):
				return None, -1
			return favs[idx], idx
		elif self._notebook.GetSelection() == 5:  # Podcasts
			episodes = getattr(self, "_episode_filtered", None) or []
			if idx >= len(episodes):
				return None, -1
			return episodes[idx].to_dict(), idx
		else:
			if idx >= len(self._stations):
				return None, -1
			return self._stations[idx], idx

	def _on_selection_changed(self, event):
		self._update_fav_button()
		self._update_save_audio_btn()

	def _update_save_audio_btn(self):
		"""Enable/disable the Save, Clear Audio Profile and Rename buttons based on current selection."""
		if not hasattr(self, "_save_audio_btn"):
			return
		is_fav_tab = (self._notebook.GetSelection() == 1)
		station, _idx = self._get_selected_station()
		is_fav = bool(station and self._manager.is_favorite(station))
		has_profile = bool(station and station.get("station_audio"))
		self._save_audio_btn.Enable(is_fav_tab and is_fav)
		self._clear_audio_btn.Enable(is_fav_tab and is_fav and has_profile)
		self._rename_btn.Enable(is_fav_tab and is_fav)

	def _prompt_and_build_audio_profile(self, existing, allow_speed=False):
		"""Shared "what would you like to save" dialog for audio profiles -
		used by favourites (_on_save_audio_profile), podcast feeds
		(_on_save_feed_audio_profile), GETEM/LibriVox library books
		(_on_save_getem_audio_profile), and jukebox files
		(_save_jukebox_file_profile). Reads the live volume/effects/EQ
		(and, when *allow_speed* is True, the live playback speed and
		pitch transpose) straight off the current UI/player state and
		merges them into *existing* according to the option the user
		picks, so a choice that doesn't touch a given field (e.g.
		"Volume only") leaves whatever was already saved for the others
		untouched.

		Each entry in *combos* pairs a translated label with the set of
		fields it saves ("volume", "effects", "speed", and/or
		"transpose"). "speed" and "transpose" are only offered when
		*allow_speed* is True, since regular station favourites don't
		support a saved playback speed or pitch shift - only podcasts,
		audio books and jukebox tracks do.

		The original options (Volume only / Effects only / Volume and
		effects / ... ) are preserved exactly as before; the pitch-
		transpose combinations are appended after them so a saved profile
		can carry transpose alone or alongside any of the other fields.

		Returns the new profile dict, or None if the user cancelled.
		"""
		combos = [
			# Translators: Option in audio profile save dialog: save volume level only
			(_("Volume only"), {"volume"}),
			# Translators: Option in audio profile save dialog: save effects (FX/EQ) only
			(_("Effects only"), {"effects"}),
			# Translators: Option in audio profile save dialog: save both volume and effects
			(_("Volume and effects"), {"volume", "effects"}),
		]
		if allow_speed:
			combos.extend([
				# Translators: Option in audio profile save dialog: save volume level and the current playback speed
				(_("Volume and playback speed"), {"volume", "speed"}),
				# Translators: Option in audio profile save dialog: save effects (FX/EQ) and the current playback speed
				(_("Effects and playback speed"), {"effects", "speed"}),
				# Translators: Option in audio profile save dialog: save the current playback speed only
				(_("Playback speed only"), {"speed"}),
				# Translators: Option in audio profile save dialog: save volume, effects, and the current playback speed
				(_("Volume, effects, and playback speed"), {"volume", "effects", "speed"}),
				# Translators: Option in audio profile save dialog: save the current pitch transpose only
				(_("Pitch transpose only"), {"transpose"}),
				# Translators: Option in audio profile save dialog: save volume level and the current pitch transpose
				(_("Volume and pitch transpose"), {"volume", "transpose"}),
				# Translators: Option in audio profile save dialog: save effects (FX/EQ) and the current pitch transpose
				(_("Effects and pitch transpose"), {"effects", "transpose"}),
				# Translators: Option in audio profile save dialog: save the current playback speed and pitch transpose
				(_("Playback speed and pitch transpose"), {"speed", "transpose"}),
				# Translators: Option in audio profile save dialog: save volume, effects, and the current pitch transpose
				(_("Volume, effects, and pitch transpose"), {"volume", "effects", "transpose"}),
				# Translators: Option in audio profile save dialog: save volume, playback speed, and pitch transpose
				(_("Volume, playback speed, and pitch transpose"), {"volume", "speed", "transpose"}),
				# Translators: Option in audio profile save dialog: save effects, playback speed, and pitch transpose
				(_("Effects, playback speed, and pitch transpose"), {"effects", "speed", "transpose"}),
				# Translators: Option in audio profile save dialog: save volume, effects, playback speed, and pitch transpose
				(_("Volume, effects, playback speed, and pitch transpose"), {"volume", "effects", "speed", "transpose"}),
			])

		choices = [label for label, _fields in combos]

		dlg = wx.SingleChoiceDialog(
			self,
			# Translators: Message shown in the audio profile save dialog
			_("What would you like to save in the audio profile?"),
			# Translators: Title of the audio profile save dialog
			_("Save Audio Profile"),
			choices,
		)
		# Pre-select the most complete option (last one) as the default.
		dlg.SetSelection(len(choices) - 1)
		result = dlg.ShowModal()
		sel = dlg.GetSelection()
		dlg.Destroy()

		if result != wx.ID_OK:
			return None

		fields = combos[sel][1]

		# Read current UI/player values.
		vol = self._vol_spin.GetValue()
		checked = self._fx_choice.GetCheckedItems()
		active = [self._fx_keys[i] for i in checked if 0 <= i < len(self._fx_keys)]
		fx_str = ",".join(active) if active else "none"

		eq_gains = {}
		for band, _label, _default in self._eq_bands:
			eq_gains[band] = self._eq_spins[band].GetValue()

		# Build the profile dict: only the fields covered by the chosen
		# combo are (re)written; anything else keeps whatever was already
		# saved in *existing* (e.g. picking "Playback speed only" for a
		# podcast that already had a volume/effects profile leaves those
		# untouched).
		profile = dict(existing or {})
		if "volume" in fields:
			profile["volume"] = vol
		if "effects" in fields:
			profile["fx"] = fx_str
			profile["eq_gains"] = eq_gains
		if "speed" in fields:
			profile["speed"] = self._player.get_playback_rate()
		if "transpose" in fields:
			profile["transpose"] = self._player.get_transpose()
		return profile

	def _on_save_audio_profile(self, event):
		"""Save audio profile for the selected station.

		Asks the user what to include before saving:
		  - Volume only
		  - Effects only (FX + EQ gains)
		  - Volume and effects
		"""
		station, _idx = self._get_selected_station()
		if not station or not self._manager.is_favorite(station):
			return

		profile = self._prompt_and_build_audio_profile(station.get("station_audio"), allow_speed=False)
		if profile is None:
			return

		station["station_audio"] = profile
		self._manager._save_favorites()

		name = station.get("name", "").strip()
		# Translators: Spoken after saving a station-specific audio profile (volume/effects/EQ); %(station)s is the station name.
		ui.message(_("Audio profile saved for %(station)s") % {"station": name})

	def _on_clear_audio_profile(self, event):
		"""Remove the station-specific audio profile from the selected favourite."""
		station, _idx = self._get_selected_station()
		if not station or not self._manager.is_favorite(station):
			return
		if "station_audio" not in station:
			return
		del station["station_audio"]
		self._manager._save_favorites()
		name = station.get("name", "").strip()
		# Translators: Spoken after clearing a station's saved audio profile; %(station)s is the station name.
		ui.message(_("Audio profile cleared for %(station)s") % {"station": name})
		self._update_save_audio_btn()


	def _on_fav_export(self, event=None):
		"""Show a file-save dialog and export favourites as JSON or M3U."""
		# Translators: File-type filter list ('wildcard') for the favourites-export file-save dialog; each '|'-separated pair is a display label then a glob pattern, don't translate the patterns after the pipes, only the descriptive labels before them.
		wildcard = _(
			"JSON favourites (*.json)|*.json"
			"|M3U playlist (*.m3u)|*.m3u"
		)
		dlg = wx.FileDialog(
			self,
			# Translators: Title of the file-save dialog for exporting favourites.
			message=_("Export Favourites"),
			wildcard=wildcard,
			style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
			defaultFile="freeradio_favourites",
		)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		path = dlg.GetPath()
		fmt  = dlg.GetFilterIndex()   # 0 = JSON, 1 = M3U
		dlg.Destroy()

		# Append the correct extension if the user omitted it.
		ext = ".json" if fmt == 0 else ".m3u"
		if not path.lower().endswith(ext):
			path += ext

		try:
			if fmt == 0:
				self._manager.export_favorites_json(path)
			else:
				self._manager.export_favorites_m3u(path)
		except Exception as exc:
			wx.MessageBox(
				# Translators: Body of the error dialog shown when writing the export file fails; %(error)s is the underlying error message.
				_("Export failed: %(error)s") % {"error": str(exc)},
				# Translators: Title of the export-error dialog.
				_("Export Error"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return

		count = len(self._manager.get_favorites())
		wx.MessageBox(
			# Translators: Plural forms of the success message after exporting favourites; %(count)d is how many stations were exported, %(path)s the file path they were saved to.
			ngettext(
				"Exported %(count)d station to:\n%(path)s",
				"Exported %(count)d stations to:\n%(path)s",
				count,
			) % {"count": count, "path": path},
			# Translators: Title of the export-success dialog.
			_("Export Complete"),
			wx.OK | wx.ICON_INFORMATION,
			self,
		)

	def _on_fav_import(self, event=None):
		"""Show a file-open dialog, ask merge/replace, then import favourites."""
		# Translators: File-type filter list ('wildcard') for the favourites-import file picker; each '|'-separated pair is a display label then a glob pattern, don't translate the patterns after the pipes, only the descriptive labels before them.
		wildcard = _(
			"Supported files (*.json;*.m3u)|*.json;*.m3u"
			"|JSON favourites (*.json)|*.json"
			"|M3U playlist (*.m3u)|*.m3u"
		)
		dlg = wx.FileDialog(
			self,
			# Translators: Title of the file-picker dialog for importing favourites.
			message=_("Import Favourites"),
			wildcard=wildcard,
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		path = dlg.GetPath()
		dlg.Destroy()

		# Ask the user whether to merge or replace.
		choice = wx.MessageBox(
			# Translators: Body of the merge-vs-replace confirmation dialog shown after choosing a file to import; describes what the Yes and No buttons do (this dialog uses stock Yes/No/Cancel buttons, not custom labels).
			_(
				"How should the imported stations be added?\n\n"
				"Yes  — Merge: add new stations without removing existing ones.\n"
				"No   — Replace: clear the current list and load from file."
			),
			# Translators: Title of the merge-vs-replace confirmation dialog (same title as the file-picker above).
			_("Import Favourites"),
			wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION,
			self,
		)
		if choice == wx.CANCEL:
			return
		merge = (choice == wx.YES)

		try:
			added = self._manager.import_favorites(path, merge=merge)
		except ValueError as exc:
			wx.MessageBox(
				# Translators: Body of the error dialog shown when the favourites file exists but its content is invalid; %(error)s is the underlying error message.
				_("Import failed: %(error)s") % {"error": str(exc)},
				# Translators: Title of the import-error dialog.
				_("Import Error"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return
		except Exception as exc:
			wx.MessageBox(
				# Translators: Body of the error dialog shown when the favourites file can't be read at all (e.g. permissions, disk error); %(error)s is the underlying error message.
				_("Could not read the file: %(error)s") % {"error": str(exc)},
				# Translators: Same import-error dialog title as above, reused for the file-read failure case.
				_("Import Error"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return

		self._refresh_fav_list()
		self._refresh_sched_stations()
		self._refresh_timer_stations()

		if merge:
			# Translators: Plural forms of the success message after merging imported favourites; %(count)d is how many new stations were added.
			msg = ngettext(
				"Import complete: %(count)d new station added.",
				"Import complete: %(count)d new stations added.",
				added,
			) % {"count": added}
		else:
			total = len(self._manager.get_favorites())
			# Translators: Plural forms of the success message after replacing favourites outright; %(count)d is the total number of stations now in the list.
			msg = ngettext(
				"Favourites replaced with %(count)d station from the file.",
				"Favourites replaced with %(count)d stations from the file.",
				total,
			) % {"count": total}
		# Translators: Title of the final import-success dialog.
		wx.MessageBox(msg, _("Import Complete"), wx.OK | wx.ICON_INFORMATION, self)

	def _on_rename_station(self, event=None):
		"""Rename the selected favourite station.

		Opens a single-field dialog pre-filled with the current display name.
		On confirmation the new name is written to station["name"], the
		favourites list is saved, and all visible lists are refreshed so the
		change is reflected immediately everywhere (fav list, sched/timer combos).
		The renamed station keeps its selection in the favourites list.
		"""
		station, _idx = self._get_selected_station()
		if not station or not self._manager.is_favorite(station):
			return

		current_name = station.get("name", "").strip()

		dlg = wx.TextEntryDialog(
			self,
			# Translators: Prompt of the rename dialog for a custom favourite station.
			_("Enter a new name for the station:"),
			# Translators: Title of the rename dialog.
			_("Rename Station"),
			current_name,
		)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return

		new_name = dlg.GetValue().strip()
		dlg.Destroy()

		if not new_name:
			# Translators: Spoken if the user submits an empty name in the rename dialog.
			ui.message(_("Name cannot be empty"))
			return
		if new_name == current_name:
			return

		station["name"] = new_name
		self._manager._save_favorites()

		# Refresh all views that show station names.
		self._refresh_fav_list()
		self._refresh_sched_stations()
		self._refresh_timer_stations()

		# Translators: Spoken after successfully renaming a station; %s is the new name.
		ui.message(_("Renamed to: %s") % new_name)

	def _update_fav_button(self):
		station, _idx = self._get_selected_station()
		is_fav = bool(station and self._manager.is_favorite(station))
		self._del_btn.Enable(is_fav)
		self._fav_btn.Enable(bool(station) and not is_fav)
		self._details_btn.Enable(bool(station))

	def _on_play_clicked(self, event):
		if self._player.is_playing():
			self._player.pause()
			# Translators: Same "Paused" wording as the F7 shortcut and the NVDA pause command; spoken here when the Play/Pause button pauses playback.
			_notify(_("Paused"))
			return
		station, idx = self._get_selected_station()
		if not station:
			return
		# If we're merely paused on this same item, resume it in place instead
		# of reconnecting from scratch. This matters most for podcasts: a
		# fresh play() only seeks back to the last *saved* position, not the
		# exact point playback was paused at, so it can appear to restart the
		# episode from the beginning.
		# Compared by URL only (not stationuuid): podcast episodes from the
		# same show can share a common feed/show id, so a stationuuid match
		# would wrongly treat two different episodes as "the same paused
		# item" and just resume the old one instead of loading the newly
		# selected episode from its own saved position.
		if self._player.has_media():
			current = self._player.get_current_station() or {}
			same_item = bool(station.get("url")) and station.get("url") == current.get("url")
			if same_item:
				self._player.resume()
				self._update_fav_button()
				return
		if self._notebook.GetSelection() == 1:  # Favourites
			# Always pass the full (unfiltered) favourites list and find the
			# station's real index in it, so next/prev navigation in the plugin
			# works correctly even when a filter is active.
			all_favs = self._manager.get_favorites()
			try:
				real_idx = next(
					i for i, s in enumerate(all_favs)
					if s.get("stationuuid") == station.get("stationuuid")
				)
			except StopIteration:
				real_idx = idx
			self._play_callback(station, all_favs, real_idx)
		elif self._notebook.GetSelection() == 5:  # Podcasts
			self._play_callback(station, [station], 0)
		else:
			self._play_callback(station, self._stations, idx)
		self._update_fav_button()

	def _on_toggle_favorite(self, event):
		station, _idx = self._get_selected_station()
		if not station:
			return
		self._manager.add_favorite(station)
		# Translators: Spoken after adding a station to favourites via the toggle-favourite command/button.
		ui.message(_("Added to favorites"))
		self._refresh_fav_list()
		self._update_fav_button()
		if self._plugin is not None:
			try:
				self._plugin._rebuild_station_scripts()
			except Exception:
				pass

	def _on_details_clicked(self, event):
		station, _idx = self._get_selected_station()
		if not station:
			return
		self._show_station_details_for(station)

	def _show_station_details_for(self, station):
		"""Shows the details of the selected station in the same structure as the dialog in __init__.py."""
		s = station

		# Translators: Field-name labels for the station-details dialog's info table (label, value pairs) below; kept short since they're column-style row headers, not full sentences.
		rows = []
		name = s.get("name", "").strip()
		if name:
			# Translators: Field-name row header in the station-details dialog's info table (see _show_station_details_for docstring); value is the station name.
			rows.append((_("Station"), name))
		country_code = s.get("countrycode", "").strip()
		country      = s.get("country", "").strip()
		if country_code:
			display_country = _country_name(country_code)
			if country and country.lower() != display_country.lower():
				display_country = "%s (%s)" % (display_country, country)
			# Translators: Field-name row header for the country field; value is the resolved country name, optionally with the raw code in parentheses.
			rows.append((_("Country"), display_country))
		elif country:
			# Translators: Same field-name row header as above, used when only the raw country string (no resolvable code) is available.
			rows.append((_("Country"), country))
		language = s.get("language", "").strip()
		if language:
			# Translators: Field-name row header for the station's language field.
			rows.append((_("Language"), language))
		tags = s.get("tags", "").strip()
		if tags:
			first_tags = ", ".join(t.strip() for t in tags.split(",")[:5] if t.strip())
			# Translators: Field-name row header for the station's tags/genre field; value is the first few comma-joined tags.
			rows.append((_("Genre"), first_tags))
		bitrate = s.get("bitrate", 0)
		try:
			bitrate = int(bitrate)
		except (TypeError, ValueError):
			bitrate = 0
		codec = s.get("codec", "").strip()
		if bitrate and codec:
			# Translators: Field label used when both codec and bitrate are known together, e.g. 'MP3, 128 kbps' as the value.
			rows.append((_("Format"), "%s, %d kbps" % (codec, bitrate)))
		elif bitrate:
			# Translators: Field-name row header shown when only the bitrate (no codec) is known; value is e.g. '128 kbps'.
			rows.append((_("Bitrate"), "%d kbps" % bitrate))
		elif codec:
			# Translators: Field-name row header shown when only the codec (no bitrate) is known.
			rows.append((_("Codec"), codec))
		homepage = s.get("homepage", "").strip()
		if homepage:
			# Translators: Field-name row header for the station's homepage URL.
			rows.append((_("Website"), homepage))
		stream_url = (s.get("url_resolved") or s.get("url", "")).strip()
		if stream_url:
			# Translators: Field-name row header for the resolved audio stream URL.
			rows.append((_("Stream URL"), stream_url))
		votes = s.get("votes", 0)
		try:
			votes = int(votes)
		except (TypeError, ValueError):
			votes = 0
		if votes:
			# Translators: Field-name row header for the station's Radio Browser vote count.
			rows.append((_("Votes"), str(votes)))

		if not rows:
			# Translators: Spoken if none of the above fields have any data to show for this station.
			ui.message(_("No station detail available"))
			return

		dlg = wx.Dialog(
			self,
			# Translators: Title of the station-details dialog.
			title=_("Station Details"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		sizer = wx.BoxSizer(wx.VERTICAL)

		grid = wx.FlexGridSizer(cols=2, vgap=6, hgap=8)
		grid.AddGrowableCol(1, 1)

		first_ctrl = None
		for field, value in rows:
			label = wx.StaticText(dlg, label=field + ":")
			ctrl  = wx.TextCtrl(
				dlg,
				value=value,
				style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_SIMPLE,
			)
			ctrl.SetName(field)
			line_height = ctrl.GetCharHeight()
			line_count  = max(1, value.count("\n") + 1)
			ctrl.SetMinSize((-1, line_height * line_count + 8))
			grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
			grid.Add(ctrl,  1, wx.EXPAND)
			if first_ctrl is None:
				first_ctrl = ctrl

		sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 10)

		# Translators: Button label; copies all the detail rows above (as text) to the clipboard.
		copy_btn = wx.Button(dlg, label=_("&Copy all to clipboard"))
		def _on_copy(evt):
			text = "\n".join("%s: %s" % (f, v) for f, v in rows)
			if wx.TheClipboard.Open():
				wx.TheClipboard.SetData(wx.TextDataObject(text))
				wx.TheClipboard.Close()
				# Translators: Spoken after the Copy button in the station-details dialog succeeds.
				ui.message(_("Station details copied to clipboard"))
		copy_btn.Bind(wx.EVT_BUTTON, _on_copy)

		btn_row = wx.BoxSizer(wx.HORIZONTAL)
		btn_row.Add(copy_btn, 0, wx.RIGHT, 8)
		btn_row.Add(dlg.CreateButtonSizer(wx.OK), 0)
		sizer.Add(btn_row, 0, wx.ALIGN_RIGHT | wx.ALL, 8)

		dlg.SetSizer(sizer)
		dlg.SetSize((580, min(120 + len(rows) * 38, 520)))
		dlg.CenterOnParent()

		if first_ctrl:
			wx.CallAfter(first_ctrl.SetFocus)

		dlg.ShowModal()
		dlg.Destroy()

	def _marked_suffix(self):
		# Translators: Short suffix appended to a list row's display text
		# when the row is marked for bulk removal (see
		# _toggle_*_mark()/_on_*_remove_selected()). Read aloud by screen
		# readers right after the row's name, so the marked state is
		# announced while simply arrowing through the list, not only at
		# the moment '.' is pressed.
		return _(" (marked)")

	def _with_marked_suffix(self, label, marked):
		"""Append the "(marked)" suffix to *label* when *marked* is True."""
		return (label + self._marked_suffix()) if marked else label

	def _fav_display_label(self, station, marked=False):
		"""Build a favourites-list row's full text for *station*.

		Base station label, then " \u2014 Group" when the favourite has a
		folder/group (from an M3U group-title tag, say) so browsing the
		list tells you where each station came from - this is display-only
		and never touches station["name"] itself, which is still used
		as-is for playback announcements, notifications, and export.
		The "(marked)" suffix, if any, always comes last. Used by every
		place a favourite row's text is built (initial render, the
		no-select refresh, and the '.' mark toggle) so they stay identical.
		"""
		label = _station_label(station)
		group = (station.get("group") or "").strip()
		if group:
			# Translators: Suffix shown after a favourite's name to indicate its folder/group (e.g. "AZPM Jazz — AZPM"); %(group)s is the folder/group name.
			label += _(" \u2014 %(group)s") % {"group": group}
		return self._with_marked_suffix(label, marked)

	def _strip_marked_suffix(self, text):
		"""Undo _with_marked_suffix() - used wherever a list row's raw
		display text is also used as data (the Liked Songs list stores
		the song itself as the row text)."""
		suffix = self._marked_suffix()
		if suffix and text.endswith(suffix):
			return text[: -len(suffix)]
		return text

	def _confirm_bulk_remove(self, count, title, message):
		"""Shared "are you sure?" prompt for the multi-mark bulk-removal
		flows below (favourites/liked songs/audio books/jukebox). *message*
		is the already-formatted body text (it needs *count* to build the
		wording, so callers build it themselves via ngettext). Returns True
		if the user confirmed."""
		if count <= 0:
			return False
		dlg = wx.MessageDialog(
			self, message, title,
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		)
		result = dlg.ShowModal()
		dlg.Destroy()
		return result == wx.ID_YES

	def _on_delete_station(self, event):
		station, _idx = self._get_selected_station()
		if not station or not self._manager.is_favorite(station):
			return
		# Translators: Fallback station name (used only for the confirmation message below) if the station has no name field at all.
		name = station.get("name", _("Unknown")).strip()
		# Translators: Body of the delete-confirmation dialog; %s is the station name.
		msg = _("Do you want to delete the station \"%s\"?") % name
		dlg = wx.MessageDialog(
			# Translators: Title of the delete-station confirmation dialog.
			self, msg, _("Delete Station"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		)
		result = dlg.ShowModal()
		dlg.Destroy()
		if result == wx.ID_YES:
			# Remember the deleted index so we can restore focus afterwards.
			deleted_idx = _idx
			self._manager.remove_favorite(station)
			self._fav_marked.discard(station.get("stationuuid"))
			# Translators: Spoken after a custom station is deleted.
			ui.message(_("Station deleted"))
			self._refresh_fav_list()
			self._update_fav_button()
			if self._plugin is not None:
				try:
					self._plugin._rebuild_station_scripts()
				except Exception:
					pass
			# After deletion keep focus on the next item (or the last one if the
			# deleted item was at the end); move to Play button if the list is empty.
			count = self._fav_list.GetCount()
			if count > 0:
				new_idx = min(deleted_idx, count - 1)
				self._fav_list.SetSelection(new_idx)
				self._fav_list.SetFocus()
			else:
				self._play_btn.SetFocus()

	def _on_add_custom(self, event):
		dlg = AddCustomStationDialog(self)
		if dlg.ShowModal() == wx.ID_OK:
			name, url = dlg.get_values()
			if name and url:
				station = self._manager.add_custom_station(name, url)
				self._all_stations.insert(0, station)
				self._apply_filters()
				self._refresh_fav_list()
				# Translators: Spoken after successfully adding a custom station; %s is the station name.
				ui.message(_("Station added: %s") % name)
				if self._plugin is not None:
					try:
						self._plugin._rebuild_station_scripts()
					except Exception:
						pass
		dlg.Destroy()


	def _test_selected_station(self):
		"""Probe the selected station's stream URL in a background thread and
		announce the result via ui.message / NVDA speech."""
		station, _idx = self._get_selected_station()
		if not station:
			# Translators: Spoken when the Test URL context-menu action is used with no station selected.
			ui.message(_("No station selected."))
			return
		url = station.get("url_resolved") or station.get("url") or ""
		if not url:
			# Translators: Spoken when trying to test a station entry that has no stream URL at all.
			ui.message(_("This station has no URL."))
			return
		name = station.get("name", "?").strip()
		# Translators: Spoken when a station stream check starts; %s is the station name.
		ui.message(_("Checking stream for %s, please wait…") % name)

		def _worker():
			ok, detail = check_stream_url(url)
			wx.CallAfter(self._on_test_station_done, name, ok, detail)

		threading.Thread(target=_worker, daemon=True).start()

	def _on_test_station_done(self, name, ok, detail):
		if ok:
			# Translators: Spoken after a background stream check confirms a station is reachable; %(name)s is the station name.
			ui.message(_("%(name)s: stream is reachable.") % {"name": name})
		else:
			# Translators: Spoken after a background stream check finds a station unreachable; %(name)s is the station name, %(detail)s the reason from check_stream_url().
			ui.message(_("%(name)s: stream check failed — %(detail)s") % {
				"name": name, "detail": detail})

	def _show_station_context_menu(self):
		"""Context menu for the selected station in the All-stations or Favourites list.

		Items are always appended so screen readers announce them in a consistent
		order.  Fav-only actions are disabled (greyed out) when the selected
		station is not a favourite or the active tab is All Stations.
		"""
		station, _idx = self._get_selected_station()
		if not station:
			return

		is_fav_tab = (self._notebook.GetSelection() == 1)
		is_fav     = bool(station and self._manager.is_favorite(station))
		has_profile = bool(station and station.get("station_audio"))

		menu = wx.Menu()

		# --- Details ---
		# Translators: Context-menu item; same action as the Station Details button.
		item_details = menu.Append(wx.ID_ANY, _("Station Detai&ls"))
		self.Bind(wx.EVT_MENU, lambda e: self._show_station_details_for(station), item_details)

		menu.AppendSeparator()

		# --- Favourite management ---
		# Translators: Context-menu item; same action as the Add to Favourites button.
		item_add_fav = menu.Append(wx.ID_ANY, _("Add to Fa&vorites"))
		item_add_fav.Enable(bool(station) and not is_fav)
		self.Bind(wx.EVT_MENU, self._on_toggle_favorite, item_add_fav)

		# Translators: Context-menu item; same action as the Delete Station button (custom stations only).
		item_del_fav = menu.Append(wx.ID_ANY, _("&Delete Station"))
		item_del_fav.Enable(is_fav)
		self.Bind(wx.EVT_MENU, self._on_delete_station, item_del_fav)

		# Translators: Context-menu item; bulk-deletes every favourite station marked with '.', asking for confirmation once for the whole batch.
		item_del_selected = menu.Append(wx.ID_ANY, _("Remove &Selected"))
		item_del_selected.Enable(is_fav_tab and bool(self._fav_marked))
		self.Bind(wx.EVT_MENU, self._on_fav_remove_selected, item_del_selected)

		# Translators: Context-menu item; same action as the Rename Station button.
		item_rename = menu.Append(wx.ID_ANY, _("Re&name Station"))
		item_rename.Enable(is_fav_tab and is_fav)
		self.Bind(wx.EVT_MENU, self._on_rename_station, item_rename)

		# Translators: Context-menu item; assigns a user-typed folder/group name to every '.'-marked favourite (or just the focused one if none are marked), so favourites can be organised into groups manually - not only ones imported with a group-title tag.
		item_assign_group = menu.Append(wx.ID_ANY, _("Assign to &Group..."))
		item_assign_group.Enable(is_fav_tab and is_fav)
		self.Bind(wx.EVT_MENU, lambda e: self._on_fav_assign_group(station), item_assign_group)

		menu.AppendSeparator()

		# --- Audio profile ---
		# Translators: Context-menu item; same action as the Save Audio Profile button.
		item_save_profile = menu.Append(wx.ID_ANY, _("Save Audio Pr&ofile for This Station"))
		item_save_profile.Enable(is_fav_tab and is_fav)
		self.Bind(wx.EVT_MENU, self._on_save_audio_profile, item_save_profile)

		# Translators: Context-menu item; same action as the Clear Audio Profile button.
		item_del_profile = menu.Append(wx.ID_ANY, _("Clear Audio Prof&ile"))
		item_del_profile.Enable(is_fav_tab and is_fav and has_profile)
		self.Bind(wx.EVT_MENU, self._on_clear_audio_profile, item_del_profile)

		menu.AppendSeparator()

		# --- Stream test ---
		# Translators: Context-menu item; re-checks whether the station's stream URL is currently reachable.
		item_test = menu.Append(wx.ID_ANY, _("&Test URL"))
		self.Bind(wx.EVT_MENU, lambda e: self._test_selected_station(), item_test)

		lst = self._active_list()
		self.PopupMenu(menu, lst.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _on_close_btn(self, event):
		self.Hide()
		gui.mainFrame.postPopup()

	def _on_window_close(self, event):
		self.Hide()
		gui.mainFrame.postPopup()

	def _force_destroy(self):
		self.Bind(wx.EVT_CLOSE, None)
		self.Destroy()
		gui.mainFrame.postPopup()


	def _on_button_focused(self, event):
		event.GetEventObject().SetDefault()
		event.Skip()

	def _on_del_btn_key(self, event):
		if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			if self._del_btn.IsEnabled():
				self._on_delete_station(event)
		else:
			event.Skip()

	def _open_help(self):
		"""F1 — Opens the plug-in guide in the browser based on the active NVDA language.
		First doc/<lang>/readme.html, then doc/<short_lang>/readme.html,
		If not found, it opens doc/readme.html."""
		import languageHandler
		addon = addonHandler.getCodeAddon()
		addon_path = addon.path
		lang = languageHandler.getLanguage()          # e.g. "tr_TR", "en", "fr"
		short_lang = lang.split("_")[0]               # e.g. "tr", "en", "fr"

		candidates = [
			os.path.join(addon_path, "doc", lang, "readme.html"),
			os.path.join(addon_path, "doc", short_lang, "readme.html"),
			os.path.join(addon_path, "doc", "readme.html"),
		]

		for path in candidates:
			if os.path.isfile(path):
				os.startfile(path)
				return

		# Translators: Spoken if the bundled help document can't be located on disk.
		ui.message(_("Help file not found."))

	def _on_char_hook(self, event):
		key     = event.GetKeyCode()
		focused = wx.Window.FindFocus()

		if key == wx.WXK_ESCAPE or (key == wx.WXK_F4 and event.AltDown()):
			self.Hide()
			gui.mainFrame.postPopup()
			return

		if key == ord(",") and focused == self._fav_list:
			self._handle_fav_move_x()
			return

		# '.' marks/unmarks the focused row for the "mark several items,
		# then remove them all at once" flow in the Favourites, Liked
		# Songs, Audio Books library, and Jukebox lists - handled globally
		# here (same as ',' above) since these lists' own EVT_KEY_DOWN
		# handlers don't reliably see the period key on every keyboard
		# layout.
		if key == ord("."):
			if focused == self._fav_list:
				self._toggle_fav_mark()
				return
			if focused == self._liked_list:
				self._toggle_liked_mark()
				return
			if focused == self._getem_library_ctrl:
				self._toggle_getem_mark()
				return
			if focused == self._jukebox_list:
				self._toggle_jukebox_mark()
				return

		# Shift+End marks/unmarks (same predictable-direction logic as '.',
		# see _mark_range()) from the focused row to the last row; Shift+Home
		# does the same from the focused row to the first row. Same four
		# lists as '.' above, handled globally for the same reason.
		if key in (wx.WXK_END, wx.WXK_HOME) and event.ShiftDown():
			toward_end = (key == wx.WXK_END)
			if focused == self._fav_list:
				self._mark_range_fav(toward_end)
				return
			if focused == self._liked_list:
				self._mark_range_liked(toward_end)
				return
			if focused == self._getem_library_ctrl:
				self._mark_range_getem(toward_end)
				return
			if focused == self._jukebox_list:
				self._mark_range_jukebox(toward_end)
				return

		if key in (wx.WXK_F3, wx.WXK_F4):
			tab = self._notebook.GetSelection()
			# Only All Stations / Favourites are handled here — other tabs
			# (e.g. Podcasts) define their own F3/F4 behaviour further below,
			# so we must NOT return early for them.
			if tab in (0, 1):
				if tab == 0:  # All Stations
					stations = self._stations
					lst = self._all_list
				else:  # Favourites — navigate the visible (filtered) list
					stations = getattr(self, "_fav_filtered", None) or self._manager.get_favorites()
					lst = self._fav_list
				count = len(stations)
				if count > 0:
					cur = lst.GetSelection()
					if key == wx.WXK_F4:
						next_idx = (cur + 1) % count if cur != wx.NOT_FOUND else 0
					else:
						next_idx = (cur - 1) % count if cur != wx.NOT_FOUND else count - 1
					lst.SetSelection(next_idx)
					s = stations[next_idx]
					if tab == 1:
						# Resolve to real index in the full list for the plugin.
						all_favs = self._manager.get_favorites()
						try:
							real_idx = next(i for i, f in enumerate(all_favs) if f.get("stationuuid") == s.get("stationuuid"))
						except StopIteration:
							real_idx = next_idx
						self._play_callback(s, all_favs, real_idx, announce=True)
					else:
						self._play_callback(s, stations, next_idx, announce=True)
					self._update_fav_button()
					self._update_save_audio_btn()
				return
			# Fall through for other tabs (e.g. Podcasts, handled below).

		if key == wx.WXK_F5:
			vol = max(0, self._player.get_volume() - 5)
			self._player.set_volume(vol)
			config.conf["freeradio"]["volume"] = min(100, vol)
			self._vol_spin.SetValue(vol)
			# Translators: Spoken when F5 (volume down) is pressed inside the dialog; %d is the new volume level. Same wording as the main volumeDown NVDA command.
			_notify(_("Volume %d") % vol)
			if self._plugin:
				try:
					self._plugin._sync_dialog_volume(vol)
				except Exception:
					pass
			return

		if key == wx.WXK_F6:
			vol = min(200, self._player.get_volume() + 5)
			self._player.set_volume(vol)
			config.conf["freeradio"]["volume"] = min(100, vol)
			self._vol_spin.SetValue(vol)
			# Translators: Spoken when F6 (volume up) is pressed inside the dialog; %d is the new volume level. Same wording as the main volumeUp NVDA command.
			_notify(_("Volume %d") % vol)
			if self._plugin:
				try:
					self._plugin._sync_dialog_volume(vol)
				except Exception:
					pass
			return

		if key == wx.WXK_F2:
			if self._plugin:
				try:
					self._plugin._whats_playing_from_dialog()
				except Exception:
					pass
			return

		if key == wx.WXK_F7:
			if self._player.is_playing():
				self._player.pause()
				# Translators: Spoken when F7 pauses playback from inside the dialog.
				_notify(_("Paused"))
			else:
				if self._player.has_media():
					self._player.resume()
					# Translators: Spoken when F7 resumes playback from inside the dialog.
					_notify(_("Playing"))
			return

		if key == wx.WXK_F8:
			if self._plugin:
				wx.CallAfter(self._plugin._stop_from_dialog)
			return

		if key == wx.WXK_F9:
			# Rename the selected favourite — only meaningful on the Favourites tab.
			if self._notebook.GetSelection() == 1 and self._rename_btn.IsEnabled():
				self._on_rename_station()
			return

		if key == wx.WXK_F11:
			# Open the main-output picker only on demand.  The plugin decides
			# whether multiple physical devices are available before showing it.
			if self._plugin:
				self._plugin._request_output_device_selection()
			return

		if key == wx.WXK_F1:
			self._open_help()
			return

		# Applications key or Shift+F10 → context menu for the active station list
		is_context_key = (key == wx.WXK_WINDOWS_MENU or
		                  (key == wx.WXK_F10 and event.ShiftDown()))
		if is_context_key and focused in (self._all_list, self._fav_list):
			self._show_station_context_menu()
			return
		if is_context_key and focused == self._podcast_list:
			self._show_feed_context_menu()
			return
		if is_context_key and focused == self._episode_list:
			self._show_episode_context_menu()
			return
		if is_context_key and focused == self._podcast_results:
			self._show_podcast_result_context_menu()
			return
		if is_context_key and focused == self._podcast_preview_list:
			self._show_podcast_preview_context_menu()
			return
		if is_context_key and focused == self._getem_results:
			self._show_getem_result_context_menu()
			return
		if is_context_key and focused == self._getem_library_ctrl:
			self._show_getem_library_context_menu()
			return
		if is_context_key and focused == self._jukebox_search_results:
			self._show_jukebox_result_context_menu()
			return
		if is_context_key and focused == self._jukebox_list:
			self._show_jukebox_entry_context_menu()
			return
		if is_context_key and focused == self._jukebox_tracks_list:
			self._show_jukebox_track_context_menu()
			return

		if key == wx.WXK_TAB and event.ControlDown() and not event.AltDown():
			count = self._notebook.GetPageCount()
			cur   = self._notebook.GetSelection()
			if event.ShiftDown():
				nxt = (cur - 1) % count
			else:
				nxt = (cur + 1) % count
			self._notebook.SetSelection(nxt)
			self._notebook.SetFocus()
			return

		if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			if focused == self._fav_btn and self._fav_btn.IsEnabled():
				self._on_toggle_favorite(event)
				return
			if focused == self._add_btn:
				self._on_add_custom(event)
				return
			if focused == self._close_btn:
				self.Hide()
				gui.mainFrame.postPopup()
				return
			if focused in (self._all_list, self._fav_list):
				station, idx = self._get_selected_station()
				if station:
					if self._notebook.GetSelection() == 1:  # Favourites
						all_favs = self._manager.get_favorites()
						try:
							real_idx = next(i for i, f in enumerate(all_favs) if f.get("stationuuid") == station.get("stationuuid"))
						except StopIteration:
							real_idx = idx
						self._play_callback(station, all_favs, real_idx, announce=True)
					else:
						self._play_callback(station, self._stations, idx, announce=True)
					self._update_fav_button()
				return
			if focused == self._play_btn:
				self._on_play_clicked(event)
				return
			# Podcast tab: call the field's submit action directly instead of
			# relying on Skip() to reach the control's own EVT_KEY_DOWN handler —
			# Enter on a TextCtrl inside a dialog can be swallowed by native
			# default-button navigation before it ever gets there, which is why
			# Skip()-ing it here was not reliably triggering the search/add.
			if focused == self._podcast_search:
				self._on_podcast_search(event)
				return
			if focused == self._episode_list:
				self._on_episode_play(None)
				return
			if focused == self._podcast_results:
				self._on_podcast_subscribe_from_results(None)
				return
			if focused == self._podcast_preview_list:
				self._on_podcast_preview_toggle(None)
				return
			if focused == self._getem_search:
				self._on_getem_search(event)
				return
			if focused == self._getem_results:
				self._on_getem_add_to_library(None)
				return
			if focused == self._getem_library_ctrl:
				self._on_getem_play(None)
				return
			if focused == self._jukebox_search:
				self._on_jukebox_search(event)
				return
			if focused == self._jukebox_search_results:
				self._on_jukebox_add_from_results(None)
				return
			if focused == self._jukebox_list:
				self._on_jukebox_entry_play(None)
				return
			if focused == self._jukebox_tracks_list:
				self._on_jukebox_track_play(None)
				return
			if focused == self._jukebox_add_file_btn:
				self._on_jukebox_add_file(event)
				return
			if focused == self._jukebox_add_folder_btn:
				self._on_jukebox_add_folder(event)
				return
			if focused == self._jukebox_remove_btn and self._jukebox_remove_btn.IsEnabled():
				self._on_jukebox_remove_entry(event)
				return
			# For any other widget (country combo, search box, fav filter,
			# timer/sched/liked lists, SpinCtrl, RadioButton, etc.) Enter must
			# NOT bubble up to the default button (Play/Pause).  Consume it here.
			return

		if event.ControlDown() and not event.AltDown() and not event.ShiftDown():
			if key == wx.WXK_UP:
				vol = min(200, self._player.get_volume() + 5)
				self._player.set_volume(vol)
				config.conf["freeradio"]["volume"] = min(100, vol)
				# Translators: Spoken when Ctrl+Up (volume up) is pressed inside the dialog on a focused control that doesn't otherwise handle it; %d is the new volume level. Same wording as the main volumeUp NVDA command.
				_notify(_("Volume %d") % vol)
				self._vol_spin.SetValue(vol)
				return
			if key == wx.WXK_DOWN:
				vol = max(0, self._player.get_volume() - 5)
				self._player.set_volume(vol)
				config.conf["freeradio"]["volume"] = min(100, vol)
				# Translators: Spoken when Ctrl+Down (volume down) is pressed inside the dialog; %d is the new volume level. Same wording as the main volumeDown NVDA command.
				_notify(_("Volume %d") % vol)
				self._vol_spin.SetValue(vol)
				return
			# Ctrl+1..Ctrl+9 and Ctrl+0 toggle the 10 audio effects in the
			# order they appear in self._fx_keys / the Effects checklist
			# (1=Chorus, 2=Compressor, ..., 9=EQ: Bass Boost, 0=EQ: Vocal Boost).
			if ord("1") <= key <= ord("9"):
				self._toggle_fx_by_index(key - ord("1"))
				return
			if key == ord("0"):
				self._toggle_fx_by_index(9)
				return

		if event.AltDown():
			if key == ord("R"):
				# Switch to All Stations tab first so that the notebook selection
				# always matches the search box and its results list.  Without this,
				# F3/F4 and Enter would still act on whichever tab was active before.
				if self._notebook.GetSelection() != 0:
					self._notebook.SetSelection(0)
					self._apply_tab_side_effects(0)
				self._search.SetFocus()
				self._search.SelectAll()
				return
			if key == ord("V"):
				if self._fav_btn.IsEnabled():
					self._on_toggle_favorite(event)
				return
			if key == ord("K"):
				self.Hide()
				gui.mainFrame.postPopup()
				return
			# Numeric tab shortcuts: Alt+1..8 switch to the corresponding tab.
			# Tab order: 1=All Stations, 2=Favourites, 3=Recording, 4=Timer, 5=Liked Songs, 6=Podcasts, 7=Audio Books, 8=Jukebox
			if ord("1") <= key <= ord("8"):
				tab_index = key - ord("1")   # 1->0, 2->1, ..., 8->7
				self._notebook.SetSelection(tab_index)
				self._on_tab_changed_index(tab_index)
				return

		# Type-ahead for every listbox that supports it. EVT_CHAR is
		# unreliable on some native Windows ListBox controls (they can
		# consume WM_CHAR before wxPython dispatches EVT_CHAR); intercepting
		# here, before event.Skip(), guarantees our handler sees the
		# character first and the native control never gets a chance to
		# interfere. See _typeahead_listboxes() for the authoritative list
		# of widgets this covers.
		#
		# NOTE: strictly greater than 32 (not >=) - space (32) is a special
		# action key on several of these lists (play/pause, preview toggle
		# - see _on_list_key/_on_episode_key/_on_getem_results_key/
		# _on_jukebox_tracks_key etc.) and must be allowed to fall through
		# to those EVT_KEY_DOWN handlers instead of being consumed here as
		# a type-ahead character.
		if not event.ControlDown() and not event.AltDown():
			typeahead_widgets = tuple(lb for lb, _ in self._typeahead_listboxes())
			if focused in typeahead_widgets:
				ukey = event.GetUnicodeKey()
				if ukey != wx.WXK_NONE and ukey > 32:
					ch = chr(ukey).lower()
				elif 32 < key <= 126:
					ch = chr(key).lower()
				else:
					ch = None
				if ch and ch.isprintable():
					self._do_list_typeahead(focused, ch)
					return

		# --- Unique shortcuts to the Podcast tab ---
		# These work anywhere on the tab — the user does not need to be
		# focused on one of the listboxes for them to apply.
		if self._notebook.GetSelection() == 5:  # Podcast tab
			focused = wx.Window.FindFocus()

			# Feed selection: Shift+F3 / Shift+F4 (checked before the plain
			# F3/F4 case below, since Shift+F3/F4 also match key in (F3, F4)).
			if key == wx.WXK_F3 and event.ShiftDown():
				self._select_prev_feed()
				return
			if key == wx.WXK_F4 and event.ShiftDown():
				self._select_next_feed()
				return

			# Episode switching: F3 / F4 (and Ctrl+Left / Ctrl+Right while
			# focused on one of the podcast lists).
			if key == wx.WXK_F3:
				self._play_prev_episode()
				return
			if key == wx.WXK_F4:
				self._play_next_episode()
				return
			if focused in (self._episode_list, self._podcast_list, self._podcast_results):
				if key == wx.WXK_LEFT and event.ControlDown():
					self._play_prev_episode()
					return
				if key == wx.WXK_RIGHT and event.ControlDown():
					self._play_next_episode()
					return

		# --- Unique shortcuts to the Audio Books tab ---
		# A book is a single source even though it's split into parts -
		# see GetemBook.last_chapter_index - so F3/F4 (and Ctrl+Left/
		# Ctrl+Right on the library list) here switch BOOKS, the reverse
		# of the Podcast tab above (where F3/F4 is the finer-grained
		# "episode" switch and Shift+F3/F4 is the coarser "feed" switch):
		# on this tab the part is the finer-grained unit, so it's the one
		# that moves to the Shift-modified keys instead.
		if self._notebook.GetSelection() == 6:  # Audio Books tab
			focused = wx.Window.FindFocus()
			if key == wx.WXK_F3 and event.ShiftDown():
				self._play_prev_getem_chapter()
				return
			if key == wx.WXK_F4 and event.ShiftDown():
				self._play_next_getem_chapter()
				return
			if key == wx.WXK_F3:
				self._play_prev_getem_book()
				return
			if key == wx.WXK_F4:
				self._play_next_getem_book()
				return
			if focused == self._getem_library_ctrl:
				if key == wx.WXK_LEFT and event.ControlDown():
					self._play_prev_getem_book()
					return
				if key == wx.WXK_RIGHT and event.ControlDown():
					self._play_next_getem_book()
					return

		# --- Unique shortcuts to the Jukebox tab ---
		# It's the same logic as in the Podcasts tab: F3/F4 = previous/next track
		# (Episode equivalent), Shift+F3/F4 = previous/next jukebox entry
		# (feed equivalent), Ctrl+Left/Right to select previous/next in the track list.
		# Plays the track
		if self._notebook.GetSelection() == 7:  # Jukebox tab
			focused = wx.Window.FindFocus()
			if key == wx.WXK_F3 and event.ShiftDown():
				self._select_prev_jukebox_entry()
				return
			if key == wx.WXK_F4 and event.ShiftDown():
				self._select_next_jukebox_entry()
				return
			if key == wx.WXK_F3:
				self._play_prev_jukebox_track()
				return
			if key == wx.WXK_F4:
				self._play_next_jukebox_track()
				return
			if focused in (self._jukebox_tracks_list, self._jukebox_list):
				if key == wx.WXK_LEFT and event.ControlDown():
					self._play_prev_jukebox_track()
					return
				if key == wx.WXK_RIGHT and event.ControlDown():
					self._play_next_jukebox_track()
					return

		event.Skip()

	def _handle_fav_move_x(self):
		"""Reorder favourites via X+X.  Works correctly even when a filter is active:
		the visible list indices are resolved back to positions in the full favourites
		list before the move is applied, so the order is always saved correctly."""
		idx = self._fav_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return

		# The displayed list may be a filtered subset; resolve to the full list.
		filtered = getattr(self, "_fav_filtered", None) or self._manager.get_favorites()
		favs     = self._manager.get_favorites()

		if idx >= len(filtered):
			return

		def _real_idx(station):
			"""Return the station's index in the full favourites list."""
			uid = station.get("stationuuid")
			try:
				return next(i for i, s in enumerate(favs) if s.get("stationuuid") == uid)
			except StopIteration:
				return -1

		if self._moving_station_index == -1:
			self._moving_station_index = idx
			station_name = filtered[idx].get("name", "").strip()
			winsound.Beep(440, 100)  # Mid tone: item picked
			# Translators: Spoken when the 'move favourite' keyboard command (comma) is pressed the first time on a station, picking it up for reordering; %s is the station name. Press comma again elsewhere in the list to drop it there.
			ui.message(_("%s selected. Navigate to the target position and press comma again to drop.") % station_name)

		else:
			if self._moving_station_index == idx:
				self._moving_station_index = -1
				winsound.Beep(330, 150)  # Low tone: cancelled
				# Translators: Spoken if the move-in-progress is cancelled (e.g. Escape) before a drop position is chosen.
				ui.message(_("Move cancelled"))
				return

			source_vis = self._moving_station_index
			target_vis = idx

			source_station = filtered[source_vis]
			target_station = filtered[target_vis]

			source_real = _real_idx(source_station)
			target_real = _real_idx(target_station)

			if source_real == -1 or target_real == -1:
				self._moving_station_index = -1
				return

			station = favs.pop(source_real)
			# After popping, the target index may have shifted by one.
			insert_at = target_real if target_real <= source_real else target_real - 1
			favs.insert(insert_at, station)

			self._manager._favorites = favs
			self._manager._save_favorites()
			self._refresh_fav_list()

			# Restore selection to the moved station in the (now refreshed) list.
			new_filtered = getattr(self, "_fav_filtered", [])
			new_uid = station.get("stationuuid")
			new_vis = next(
				(i for i, s in enumerate(new_filtered) if s.get("stationuuid") == new_uid),
				target_vis,
			)
			self._fav_list.SetSelection(new_vis)
			self._moving_station_index = -1
			winsound.Beep(880, 100)  # High tone: successfully moved
			# Translators: Spoken after successfully reordering a favourite station; %s is the station name.
			ui.message(_("Moved: %s") % station.get("name", "").strip())

	def _on_search_key(self, event):
		key = event.GetKeyCode()
		if key == wx.WXK_DOWN:
			self._all_list.SetFocus()
			if self._all_list.GetCount() > 0 and self._all_list.GetSelection() == wx.NOT_FOUND:
				self._all_list.SetSelection(0)
		else:
			event.Skip()

	def _get_list_page_size(self, listbox):
		try:
			rows_per_page = listbox.GetCountPerPage()
			if rows_per_page > 1:
				return rows_per_page - 1
		except Exception:
			pass
		try:
			row_height = max(1, listbox.GetCharHeight())
			height = max(listbox.GetClientSize().height, listbox.GetSize().height)
			visible_rows = height // row_height
		except Exception:
			visible_rows = 10
		if visible_rows <= 1:
			visible_rows = 10
		return max(1, visible_rows - 1)

	def _move_list_page(self, listbox, direction):
		count = listbox.GetCount()
		if count <= 0:
			return False
		current = listbox.GetSelection()
		if current == wx.NOT_FOUND:
			target = 0 if direction > 0 else count - 1
		else:
			target = current + (self._get_list_page_size(listbox) * direction)
			target = max(0, min(count - 1, target))
		listbox.SetSelection(target)
		try:
			listbox.EnsureVisible(target)
		except Exception:
			pass
		wx.PostEvent(
			listbox,
			wx.CommandEvent(wx.EVT_LISTBOX.typeId, listbox.GetId()),
		)
		self._update_fav_button()
		self._update_save_audio_btn()
		return True

	def _on_list_key(self, event):
		key = event.GetKeyCode()
		if key == wx.WXK_UP and self._active_list().GetSelection() == 0:
			if self._notebook.GetSelection() == 0:  # All Stations
				self._search.SetFocus()
		elif key in (wx.WXK_PAGEUP, wx.WXK_PAGEDOWN):
			direction = -1 if key == wx.WXK_PAGEUP else 1
			if not self._move_list_page(self._all_list, direction):
				event.Skip()
		elif key == wx.WXK_SPACE:
			if self._player.is_playing():
				self._player.pause()
				# Translators: Same "Paused" wording as elsewhere; spoken here when Space pauses playback from the All Stations list.
				_notify(_("Paused"))
			else:
				station, idx = self._get_selected_station()
				if station:
					if self._notebook.GetSelection() == 1:  # Favourites
						all_favs = self._manager.get_favorites()
						try:
							real_idx = next(i for i, s in enumerate(all_favs) if s.get("stationuuid") == station.get("stationuuid"))
						except StopIteration:
							real_idx = idx
						self._play_callback(station, all_favs, real_idx, announce=True)
					else:
						self._play_callback(station, self._stations, idx, announce=True)
					self._update_fav_button()
		elif key == wx.WXK_RIGHT:
			lst = self._all_list
			count = lst.GetCount()
			if count == 0:
				event.Skip()
				return
			idx = lst.GetSelection()
			next_idx = (idx + 1) % count if idx != wx.NOT_FOUND else 0
			lst.SetSelection(next_idx)
			if next_idx < len(self._stations):
				self._play_callback(self._stations[next_idx], self._stations, next_idx, announce=False)
			self._update_fav_button()
			self._update_save_audio_btn()
		elif key == wx.WXK_LEFT:
			lst = self._all_list
			count = lst.GetCount()
			if count == 0:
				event.Skip()
				return
			idx = lst.GetSelection()
			prev_idx = (idx - 1) % count if idx != wx.NOT_FOUND else 0
			lst.SetSelection(prev_idx)
			if prev_idx < len(self._stations):
				self._play_callback(self._stations[prev_idx], self._stations, prev_idx, announce=False)
			self._update_fav_button()
			self._update_save_audio_btn()
		else:
			event.Skip()

	def _on_fav_list_key(self, event):
		"""Favourites list — Space to play/pause, Left/Right to navigate and play."""
		key = event.GetKeyCode()

		if key in (wx.WXK_PAGEUP, wx.WXK_PAGEDOWN):
			direction = -1 if key == wx.WXK_PAGEUP else 1
			if not self._move_list_page(self._fav_list, direction):
				event.Skip()
		elif key == wx.WXK_SPACE:
			if self._player.is_playing():
				self._player.pause()
				# Translators: Same "Paused" wording as elsewhere; spoken here when Space pauses playback from the Favourites list.
				_notify(_("Paused"))
			else:
				station, idx = self._get_selected_station()
				if station:
					# Pass the full favourites list so next/prev in the plugin
					# navigates all favourites, not just the filtered subset.
					all_favs = self._manager.get_favorites()
					try:
						real_idx = next(
							i for i, s in enumerate(all_favs)
							if s.get("stationuuid") == station.get("stationuuid")
						)
					except StopIteration:
						real_idx = idx
					self._play_callback(station, all_favs, real_idx, announce=True)
					self._update_fav_button()
		elif key == wx.WXK_RIGHT:
			# Navigate within the currently visible (possibly filtered) list.
			favs = getattr(self, "_fav_filtered", None) or self._manager.get_favorites()
			count = self._fav_list.GetCount()
			if count == 0:
				event.Skip()
				return
			idx = self._fav_list.GetSelection()
			next_idx = (idx + 1) % count if idx != wx.NOT_FOUND else 0
			self._fav_list.SetSelection(next_idx)
			if next_idx < len(favs):
				s = favs[next_idx]
				all_favs = self._manager.get_favorites()
				try:
					real_idx = next(i for i, f in enumerate(all_favs) if f.get("stationuuid") == s.get("stationuuid"))
				except StopIteration:
					real_idx = next_idx
				self._play_callback(s, all_favs, real_idx, announce=False)
			self._update_fav_button()
			self._update_save_audio_btn()
		elif key == wx.WXK_LEFT:
			favs = getattr(self, "_fav_filtered", None) or self._manager.get_favorites()
			count = self._fav_list.GetCount()
			if count == 0:
				event.Skip()
				return
			idx = self._fav_list.GetSelection()
			prev_idx = (idx - 1) % count if idx != wx.NOT_FOUND else 0
			self._fav_list.SetSelection(prev_idx)
			if prev_idx < len(favs):
				s = favs[prev_idx]
				all_favs = self._manager.get_favorites()
				try:
					real_idx = next(i for i, f in enumerate(all_favs) if f.get("stationuuid") == s.get("stationuuid"))
				except StopIteration:
					real_idx = prev_idx
				self._play_callback(s, all_favs, real_idx, announce=False)
			self._update_fav_button()
			self._update_save_audio_btn()
		elif key == wx.WXK_DELETE:
			if self._fav_marked:
				self._on_fav_remove_selected(event)
			elif self._del_btn.IsEnabled():
				self._on_delete_station(event)
		else:
			event.Skip()

	def _mark_range(self, listbox, marked_set, identity_of, redraw, toward_end):
		"""Shared Shift+End/Shift+Home range-mark logic for the four
		multi-select lists (Favourites, Liked Songs, Audio Books, Jukebox).

		Looks at the currently focused row's mark state to decide whether
		the whole range is being marked or unmarked - so the action is
		predictable rather than toggling each row independently - then
		applies that from the current row to the last row (toward_end=True,
		like Shift+End) or to the first row (toward_end=False, like
		Shift+Home), inclusive of the current row. Moves focus to the far
		end of the range afterwards, mirroring how Shift+End/Home behave
		in text fields. Returns (should_mark, changed_count), or None if
		there was nothing to do (empty list, nothing focused, or the
		focused row has no identity - e.g. a placeholder row).

		*identity_of(idx)* must return a hashable identity for row *idx*,
		or None to skip it. *redraw(idx)* must re-render row *idx*'s
		display text from the current contents of *marked_set*.
		"""
		count = listbox.GetCount()
		current = listbox.GetSelection()
		if count == 0 or current == wx.NOT_FOUND:
			return None
		cur_id = identity_of(current)
		if cur_id is None:
			return None
		should_mark = cur_id not in marked_set

		if toward_end:
			indices = range(current, count)
			focus_idx = count - 1
		else:
			indices = range(0, current + 1)
			focus_idx = 0

		changed = 0
		for i in indices:
			ident = identity_of(i)
			if ident is None:
				continue
			marked = ident in marked_set
			if should_mark and not marked:
				marked_set.add(ident)
				changed += 1
			elif not should_mark and marked:
				marked_set.discard(ident)
				changed += 1
		for i in indices:
			redraw(i)
		listbox.SetSelection(focus_idx)
		return should_mark, changed

	def _mark_range_fav(self, toward_end):
		"""Shift+End/Shift+Home for the Favourites list - see _mark_range()."""
		filtered = getattr(self, "_fav_filtered", None) or []

		def identity_of(i):
			return filtered[i].get("stationuuid") if i < len(filtered) else None

		def redraw(i):
			station = filtered[i]
			self._fav_list.SetString(
				i, self._fav_display_label(station, station.get("stationuuid") in self._fav_marked)
			)

		result = self._mark_range(self._fav_list, self._fav_marked, identity_of, redraw, toward_end)
		if not result:
			return
		should_mark, changed = result
		if should_mark:
			# Translators: Spoken after Shift+End/Shift+Home marks a range of favourites for the multi-select removal flow; %d is how many were newly marked.
			ui.message(ngettext("Marked %d favourite", "Marked %d favourites", changed) % changed)
		else:
			# Translators: Spoken after Shift+End/Shift+Home unmarks a range of favourites; %d is how many were unmarked.
			ui.message(ngettext("Unmarked %d favourite", "Unmarked %d favourites", changed) % changed)

	def _mark_range_liked(self, toward_end):
		"""Shift+End/Shift+Home for the Liked Songs list - see _mark_range()."""
		placeholders = (_("No liked songs yet."), _("No results found."))

		def identity_of(i):
			text = self._strip_marked_suffix(self._liked_list.GetString(i))
			return None if text in placeholders else text

		def redraw(i):
			song = self._strip_marked_suffix(self._liked_list.GetString(i))
			if song in placeholders:
				return
			self._liked_list.SetString(i, self._with_marked_suffix(song, song in self._liked_marked))

		result = self._mark_range(self._liked_list, self._liked_marked, identity_of, redraw, toward_end)
		if not result:
			return
		should_mark, changed = result
		if should_mark:
			# Translators: Spoken after Shift+End/Shift+Home marks a range of liked songs for the multi-select removal flow; %d is how many were newly marked.
			ui.message(ngettext("Marked %d song", "Marked %d songs", changed) % changed)
		else:
			# Translators: Spoken after Shift+End/Shift+Home unmarks a range of liked songs; %d is how many were unmarked.
			ui.message(ngettext("Unmarked %d song", "Unmarked %d songs", changed) % changed)

	def _mark_range_getem(self, toward_end):
		"""Shift+End/Shift+Home for the Audio Books library list - see _mark_range()."""
		books = self._merged_library_books()

		def identity_of(i):
			return books[i].identity_key() if i < len(books) else None

		def redraw(i):
			book = books[i]
			label = self._format_getem_result_label(book)
			self._getem_library_ctrl.SetString(
				i, self._with_marked_suffix(label, book.identity_key() in self._getem_marked)
			)

		result = self._mark_range(self._getem_library_ctrl, self._getem_marked, identity_of, redraw, toward_end)
		if not result:
			return
		should_mark, changed = result
		if should_mark:
			# Translators: Spoken after Shift+End/Shift+Home marks a range of audio books for the multi-select removal flow; %d is how many were newly marked.
			ui.message(ngettext("Marked %d book", "Marked %d books", changed) % changed)
		else:
			# Translators: Spoken after Shift+End/Shift+Home unmarks a range of audio books; %d is how many were unmarked.
			ui.message(ngettext("Unmarked %d book", "Unmarked %d books", changed) % changed)

	def _mark_range_jukebox(self, toward_end):
		"""Shift+End/Shift+Home for the Jukebox list - see _mark_range()."""
		entries = self._jukebox_manager.get_entries()

		def identity_of(i):
			return entries[i].path if i < len(entries) else None

		def redraw(i):
			entry = entries[i]
			self._jukebox_list.SetString(
				i, self._with_marked_suffix(entry.display_label(), entry.path in self._jukebox_marked)
			)

		result = self._mark_range(self._jukebox_list, self._jukebox_marked, identity_of, redraw, toward_end)
		if not result:
			return
		should_mark, changed = result
		if should_mark:
			# Translators: Spoken after Shift+End/Shift+Home marks a range of jukebox entries for the multi-select removal flow; %d is how many were newly marked.
			ui.message(ngettext("Marked %d jukebox entry", "Marked %d jukebox entries", changed) % changed)
		else:
			# Translators: Spoken after Shift+End/Shift+Home unmarks a range of jukebox entries; %d is how many were unmarked.
			ui.message(ngettext("Unmarked %d jukebox entry", "Unmarked %d jukebox entries", changed) % changed)

	def _toggle_fav_mark(self):
		"""Mark/unmark the focused favourite station with '.' for the
		Remove Selected bulk-delete flow (Delete key or context menu).
		Updates the row's display text immediately (see
		_fav_display_label()) so the marked state is visible/announced
		while simply arrowing through the list afterwards, not only at
		the moment of marking."""
		station, idx = self._get_selected_station()
		if not station or idx < 0:
			return
		uuid = station.get("stationuuid")
		if not uuid:
			return
		name = _station_label(station)
		if uuid in self._fav_marked:
			self._fav_marked.discard(uuid)
			# Translators: Spoken after unmarking a favourite station in the multi-select removal flow; %s is the station name.
			ui.message(_("Unmarked: %s") % name)
		else:
			self._fav_marked.add(uuid)
			# Translators: Spoken after marking a favourite station in the multi-select removal flow; %s is the station name.
			ui.message(_("Marked: %s") % name)
		self._fav_list.SetString(idx, self._fav_display_label(station, uuid in self._fav_marked))
		self._fav_list.SetSelection(idx)

	def _on_fav_assign_group(self, station):
		"""Assign a user-typed folder/group name to every favourite marked
		with '.' (or just *station* if nothing is marked), so favourites
		can be organised into groups by hand - not only ones that arrived
		with a group-title tag from an M3U import. An empty name clears
		the group, removing the "— Group" suffix from those rows.
		"""
		favs = self._manager.get_favorites()
		marked = self._fav_marked
		if marked:
			targets = [s for s in favs if s.get("stationuuid") in marked]
		else:
			targets = [station] if station else []
		if not targets:
			return

		current = (station.get("group") or "").strip() if station else ""
		dlg = wx.TextEntryDialog(
			self,
			# Translators: Prompt of the dialog that assigns a folder/group name to the marked favourite(s); leaving the field empty removes them from any group instead.
			_("Enter a group name (leave empty to remove from a group):"),
			# Translators: Title of the assign-to-group dialog.
			_("Assign to Group"),
			current,
		)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		new_group = dlg.GetValue().strip()
		dlg.Destroy()

		for s in targets:
			s["group"] = new_group
		self._manager._save_favorites()
		self._fav_marked.clear()
		self._refresh_fav_list()

		count = len(targets)
		if new_group:
			# Translators: Spoken after assigning marked favourite(s) to a group; %(count)d is how many stations, %(group)s the group name.
			ui.message(ngettext(
				"Assigned %(count)d favourite to group \"%(group)s\"",
				"Assigned %(count)d favourites to group \"%(group)s\"",
				count,
			) % {"count": count, "group": new_group})
		else:
			# Translators: Spoken after clearing the group from marked favourite(s); %(count)d is how many stations.
			ui.message(ngettext(
				"Removed %(count)d favourite from its group",
				"Removed %(count)d favourites from their groups",
				count,
			) % count)

	def _on_fav_remove_selected(self, event=None):
		"""Bulk-remove every favourite station currently marked with '.',
		asking for confirmation once for the whole batch."""
		marked = self._fav_marked
		if not marked:
			return
		favs = self._manager.get_favorites()
		stations = [s for s in favs if s.get("stationuuid") in marked]
		count = len(stations)
		if count == 0:
			self._fav_marked.clear()
			return
		# Translators: Body of the bulk-delete confirmation dialog for favourite stations; %d is how many stations are marked.
		message = ngettext(
			"Do you want to delete the %d marked station?",
			"Do you want to delete the %d marked stations?",
			count,
		) % count
		# Translators: Title of the bulk-delete confirmation dialog for favourite stations.
		if not self._confirm_bulk_remove(count, _("Delete Stations"), message):
			return
		for s in stations:
			self._manager.remove_favorite(s)
		self._fav_marked.clear()
		if self._plugin is not None:
			try:
				self._plugin._rebuild_station_scripts()
			except Exception:
				pass
		# Translators: Spoken after bulk-deleting marked favourite stations; %d is how many were removed.
		ui.message(ngettext("%d station deleted", "%d stations deleted", count) % count)
		self._refresh_fav_list()
		self._update_fav_button()
		count_left = self._fav_list.GetCount()
		if count_left > 0:
			self._fav_list.SetSelection(0)
			self._fav_list.SetFocus()
		else:
			self._play_btn.SetFocus()

	def _timer_action_changed_update(self):
		"""Show/hide station area and update label according to Start/Stop selection."""
		is_start = self._timer_rb_start.GetValue()
		self._timer_station_label.Show(is_start)
		# Also show/hide the filter field that sits between the label and the listbox.
		if hasattr(self, "_timer_station_filter"):
			self._timer_station_filter.Show(is_start)
		self._timer_station_cb.Show(is_start)
		# Translators: Timer time-field label, which switches wording depending on the chosen timer action (start/alarm vs stop/sleep); the field itself is shared between both modes.
		lbl = _("Start time (HH:MM):") if is_start else _("Stop time (HH:MM):")
		self._timer_time_label.SetLabel(lbl)
		self._timer_time.SetName(lbl)
		self._timer_panel.Layout()

	def _on_timer_action_changed(self, event):
		self._timer_action_changed_update()
		event.Skip()

	def _on_timer_recurrence_changed(self, event):
		"""Show/hide the active-days checklist based on recurrence mode."""
		weekly = self._timer_rec_weekly.GetValue()
		self._timer_days_label.Show(weekly)
		self._timer_days_clb.Show(weekly)
		self._timer_panel.Layout()
		event.Skip()

	def _refresh_timer_stations(self):
		"""Timer tab: fill the station listbox from favourites.

		Preserves the current selection by station name so that a tab-switch
		refresh does not silently deselect the station the user had chosen.
		SetSelection is intentionally NOT called here — see _refresh_sched_stations
		for the rationale.  Selection is applied lazily in _on_timer_station_focus.
		"""
		favs = self._manager.get_favorites()
		# Apply the filter if the filter field exists and has text.
		query = getattr(self, "_timer_station_filter", None)
		query = query.GetValue().strip().lower() if query else ""
		filtered = [s for s in favs if not query or query in s.get("name", "").lower()] if query else list(favs)
		# Cache the filtered station list so _resolve_station_from_combo uses the right subset.
		self._timer_stations = filtered
		# Remember which station was selected before clearing the list.
		prev_idx = self._timer_station_cb.GetSelection()
		prev_name = (
			self._timer_station_cb.GetString(prev_idx)
			if prev_idx != wx.NOT_FOUND else ""
		)
		self._timer_station_cb.Clear()
		for s in filtered:
			self._timer_station_cb.Append(s.get("name", "?").strip())
		# Store the name to restore; the actual SetSelection is deferred to focus time.
		self._timer_station_pending_name = prev_name

	def _refresh_timer_list(self):
		"""Write pending timers to the listbox."""
		_FULL_DAY_NAMES = [
			# Translators: Day names used when listing a recurring timer's active days - same wording as the Recording tab's scheduling section.
			_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
			_("Friday"), _("Saturday"), _("Sunday"),
		]
		self._timer_list.Clear()
		if self._timer_manager:
			for entry in self._timer_manager.get_timers():
				entry_id, dt, action, label, notify_cb = entry
				time_str = dt.strftime("%d.%m.%Y %H:%M")
				# Translators: Internal marker value distinguishing a sleep-timer entry from an alarm entry in the timer list; not itself user-visible (the visible strings are built separately below).
				is_alarm = (label != _("Sleep timer") and label != "Sleep timer")
				if is_alarm:
					# Translators: One line of the pending-timers list for an alarm (start-radio) timer; %(time)s is the HH:MM time, %(station)s the station name.
					text = _("Alarm %(time)s — %(station)s") % {
						"time": time_str, "station": label
					}
				else:
					# Translators: One line of the pending-timers list for a sleep (stop-radio) timer; %(time)s is the HH:MM time.
					text = _("Sleep %(time)s") % {"time": time_str}
				meta = getattr(action, "_timer_meta", None) or {}
				if meta.get("recurrence") == "weekly":
					days = sorted(meta.get("active_days") or [])
					if not days or days == list(range(7)):
						# Translators: Recurrence description shown when a weekly timer has every day of the week checked (no day restriction) - same wording as the Recording tab's scheduling section.
						when = _("Every day")
					else:
						# Translators: Recurrence description shown when a weekly timer is restricted to specific days; %s is a comma-joined list of day names - same wording as the Recording tab's scheduling section.
						when = _("Every %s") % ", ".join(_FULL_DAY_NAMES[d] for d in days)
					text += "  — " + when
				self._timer_list.Append(text)
		self._timer_del_btn.Enable(self._timer_list.GetCount() > 0)

	def _on_timer_station_focus(self, event):
		"""Apply the pending selection when the station listbox actually gets focus.

		_refresh_timer_stations deliberately skips SetSelection to avoid
		Win32 firing EVENT_OBJECT_SELECTION (which NVDA announces) while
		focus is elsewhere.  We do it here instead, when the user has
		genuinely navigated to the listbox.
		"""
		if self._timer_station_cb.GetSelection() == wx.NOT_FOUND and self._timer_station_cb.GetCount() > 0:
			pending = getattr(self, "_timer_station_pending_name", "")
			idx = self._timer_station_cb.FindString(pending) if pending else wx.NOT_FOUND
			self._timer_station_cb.SetSelection(idx if idx != wx.NOT_FOUND else 0)
		event.Skip()

	def _on_timer_station_filter_changed(self, event):
		"""Rebuild the timer station list whenever the filter changes."""
		self._refresh_timer_stations()
		count = self._timer_station_cb.GetCount()
		if count == 0:
			# Translators: Spoken when the timer station filter matches nothing.
			ui.message(_("No stations found"))
		else:
			# Translators: Plural forms spoken after filtering the timer station list; %d is how many match.
			ui.message(ngettext("%d station", "%d stations", count) % count)
		event.Skip()

	def _on_timer_station_filter_key(self, event):
		"""Down arrow moves focus from the filter field into the station list."""
		if event.GetKeyCode() == wx.WXK_DOWN:
			self._timer_station_cb.SetFocus()
			if self._timer_station_cb.GetCount() > 0 and self._timer_station_cb.GetSelection() == wx.NOT_FOUND:
				self._timer_station_cb.SetSelection(0)
		else:
			event.Skip()

	def _on_timer_add(self, event):
		if not self._timer_manager:
			# Translators: Spoken when adding a timer but the timer subsystem failed to initialise.
			ui.message(_("Timer manager is not available"))
			return

		time_str = self._timer_time.GetValue().strip()
		try:
			parts = time_str.split(":")
			if len(parts) != 2:
				raise ValueError()
			hour, minute = int(parts[0]), int(parts[1])
			if not (0 <= hour <= 23 and 0 <= minute <= 59):
				raise ValueError()
		except (ValueError, IndexError):
			# Translators: Spoken when the typed time doesn't parse as a valid HH:MM 24-hour time; same message as the recording-schedule form.
			ui.message(_("Invalid time format. Use HH:MM"))
			self._timer_time.SetFocus()
			return

		now  = datetime.datetime.now()
		when = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
		if when <= now:
			when += datetime.timedelta(days=1)

		# --- Recurrence mode --- same model as the Recording tab's
		# scheduling section (recorder.ScheduledRecording): "weekly" repeats
		# indefinitely on active_days ([] means every day) until removed.
		recurrence  = "weekly" if self._timer_rec_weekly.GetValue() else "once"
		active_days = list(self._timer_days_clb.Checked) if recurrence == "weekly" else []
		if recurrence == "weekly" and active_days and when.weekday() not in active_days:
			for _day in range(7):
				when += datetime.timedelta(days=1)
				if when.weekday() in active_days:
					break

		# Computed after any day-of-week rollover above, so it stays accurate
		# even when a weekly timer's next active day is further out than
		# literally tomorrow (in which case this is simply False and the
		# day name inside the recurrence description below carries that
		# information instead).
		next_day = (when.date() - now.date()).days == 1

		is_start = self._timer_rb_start.GetValue()

		# Duplicate check: warn and abort if any timer already exists at the
		# same HH:MM, regardless of kind (alarm and sleep timers conflict too).
		existing = self._timer_manager.get_timers()
		for _eid, dt, _action, label, _cb in existing:
			meta = getattr(_action, "_timer_meta", None)
			if meta and dt.hour == when.hour and dt.minute == when.minute:
				ui.message(
					# Translators: Spoken when trying to add a timer at a time that already has one (alarm or sleep) scheduled; %(time)s is the HH:MM time, %(label)s a short description of the conflicting timer.
					_("A timer already exists at %(time)s (%(label)s). Remove it first.") % {
						"time":  dt.strftime("%H:%M"),
						"label": label,
					}
				)
				return

		if is_start:
			station = self._resolve_station_from_combo(
				self._timer_station_cb,
				getattr(self, "_timer_stations", []),
			)
			if station is None:
				# Translators: Spoken when adding an alarm-type timer with no station chosen.
				ui.message(_("Please select a station"))
				return
			self._timer_manager.add_alarm(
				start_dt=when,
				station=station,
				play_callback=self._play_callback,
				recurrence=recurrence,
				active_days=active_days,
			)
			name = station.get("name", "?").strip()
			# Translators: Confirmation spoken after adding an alarm (start-radio) timer; %(station)s is the station name, %(time)s the HH:MM time it will fire.
			msg  = _("Alarm added: %(station)s at %(time)s") % {
				"station": name,
				"time":    when.strftime("%H:%M"),
			}
		else:
			self._timer_manager.add_sleep(stop_dt=when, recurrence=recurrence, active_days=active_days)
			# Translators: Confirmation spoken after adding a sleep (stop-radio) timer; %s is the HH:MM time it will fire.
			msg = _("Sleep timer added: radio will stop at %s") % when.strftime("%H:%M")

		if next_day:
			# Translators: Appended to the confirmation message when the timer's time has rolled over to the next day (e.g. it's 23:00 and the timer is set for 01:00).
			msg += "  " + _("(tomorrow)")
		if recurrence == "weekly":
			days_sorted = sorted(active_days) if active_days else list(range(7))
			if days_sorted == list(range(7)):
				# Translators: Recurrence description appended to the timer-added confirmation - same wording as the Recording tab's scheduling section.
				when_desc = _("Every day")
			else:
				_FULL_DAY_NAMES = [
					_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
					_("Friday"), _("Saturday"), _("Sunday"),
				]
				# Translators: Recurrence description appended to the timer-added confirmation - same wording as the Recording tab's scheduling section.
				when_desc = _("Every %s") % ", ".join(_FULL_DAY_NAMES[d] for d in days_sorted)
			msg += "  " + when_desc
		ui.message(msg)
		self._refresh_timer_list()

	def _on_timer_del(self, event):
		if not self._timer_manager:
			return
		idx = self._timer_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		timers = self._timer_manager.get_timers()
		if idx < len(timers):
			entry_id = timers[idx][0]  # tuple: (entry_id, dt, action, label, notify_cb)
			self._timer_manager.remove(entry_id)
			self._refresh_timer_list()
			# Translators: Spoken after deleting a pending alarm/sleep timer.
			ui.message(_("Timer removed"))

	def _on_timer_selected(self, event):
		self._timer_del_btn.Enable(self._timer_list.GetSelection() != wx.NOT_FOUND)

	# ------------------------------------------------------------------ #
	# Liked Songs tab                                                      #
	# ------------------------------------------------------------------ #

	def _liked_songs_path(self):
		"""Return the path to likedSongs.txt, mirroring __init__.py logic."""
		custom_dir = config.conf["freeradio"].get("recordings_dir", "").strip()
		if custom_dir and os.path.isabs(custom_dir):
			recordings_dir = custom_dir
		else:
			recordings_dir = os.path.join(
				os.path.expanduser("~"), "Documents", "FreeRadio Recordings"
			)
		return os.path.join(recordings_dir, "likedSongs.txt")

	def _build_liked_tab(self):
		"""Liked Songs tab: list + Spotify / YouTube / Lyrics / Remove / Refresh buttons."""
		sizer = wx.BoxSizer(wx.VERTICAL)

		sizer.Add(
			# Translators: Label above the liked-songs list.
			wx.StaticText(self._liked_panel, label=_("Liked Songs:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)

		# Filter field for the liked songs list.
		sizer.Add(
			# Translators: Label above the field that filters the liked-songs list below it.
			wx.StaticText(self._liked_panel, label=_("Filter:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._liked_filter = wx.TextCtrl(self._liked_panel)
		# Translators: Accessible name for the liked-songs filter field.
		self._liked_filter.SetName(_("Filter liked songs"))
		sizer.Add(self._liked_filter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		self._liked_list = wx.ListBox(self._liked_panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the liked-songs list (same text as its static label above).
		self._liked_list.SetName(_("Liked Songs"))
		sizer.Add(self._liked_list, 1, wx.EXPAND | wx.ALL, 5)

		btn_row = wx.BoxSizer(wx.HORIZONTAL)

		self._liked_spotify_btn = wx.Button(
			# Translators: Button label; opens a web search for the selected song on Spotify.
			self._liked_panel, label=_("Play on &Spotify")
		)
		self._liked_youtube_btn = wx.Button(
			# Translators: Button label; opens a web search for the selected song on YouTube.
			self._liked_panel, label=_("Play on Y&ouTube")
		)
		self._liked_lyrics_btn = wx.Button(
			# Translators: Button label; looks up and shows lyrics for the selected song.
			self._liked_panel, label=_("Show &Lyrics")
		)
		self._liked_remove_btn = wx.Button(
			# Translators: Button label; removes the selected song from the liked list.
			self._liked_panel, label=_("Re&move")
		)
		self._liked_refresh_btn = wx.Button(
			# Translators: Button label; re-fetches/refreshes the liked-songs list from disk.
			self._liked_panel, label=_("R&efresh")
		)

		for btn in (
			self._liked_spotify_btn,
			self._liked_youtube_btn,
			self._liked_lyrics_btn,
			self._liked_remove_btn,
			self._liked_refresh_btn,
		):
			btn_row.Add(btn, 0, wx.RIGHT, 6)

		sizer.Add(btn_row, 0, wx.LEFT | wx.BOTTOM, 5)
		self._liked_panel.SetSizer(sizer)

		self._liked_list.Bind(wx.EVT_CHAR,    self._on_list_char)
		self._liked_list.Bind(wx.EVT_LISTBOX, self._on_liked_selected)
		self._liked_list.Bind(wx.EVT_KEY_DOWN, self._on_liked_list_key)
		# Filter field: rebuild the liked songs list on every keystroke.
		self._liked_filter.Bind(wx.EVT_TEXT,     self._on_liked_filter_changed)
		# Allow Down arrow to move focus from the filter field into the list.
		self._liked_filter.Bind(wx.EVT_KEY_DOWN, self._on_liked_filter_key)
		self._liked_spotify_btn.Bind(wx.EVT_BUTTON, self._on_liked_spotify)
		self._liked_youtube_btn.Bind(wx.EVT_BUTTON, self._on_liked_youtube)
		self._liked_lyrics_btn.Bind(wx.EVT_BUTTON,  self._on_liked_lyrics)
		self._liked_remove_btn.Bind(wx.EVT_BUTTON,  self._on_liked_remove)
		self._liked_refresh_btn.Bind(wx.EVT_BUTTON, self._on_liked_refresh)

		self._liked_spotify_btn.Enable(False)
		self._liked_youtube_btn.Enable(False)
		self._liked_lyrics_btn.Enable(False)
		self._liked_remove_btn.Enable(False)

		# Alt+O → YouTube, Alt+M → Remove, Alt+E → Refresh
		accel_entries = [
			wx.AcceleratorEntry(wx.ACCEL_ALT, ord("O"), self._liked_youtube_btn.GetId()),
			wx.AcceleratorEntry(wx.ACCEL_ALT, ord("M"), self._liked_remove_btn.GetId()),
			wx.AcceleratorEntry(wx.ACCEL_ALT, ord("E"), self._liked_refresh_btn.GetId()),
		]
		self._liked_panel.SetAcceleratorTable(wx.AcceleratorTable(accel_entries))

		# Deferred: populated lazily the first time this tab becomes active
		# (see _apply_tab_side_effects, sel == 4), not eagerly at dialog
		# construction time. There is no direct hotkey that jumps straight
		# to this tab, so the tab-switch path always covers it.

	def _refresh_liked_list(self):
		"""Read likedSongs.txt, apply the filter field, and populate the listbox."""
		self._liked_list.Clear()
		path = self._liked_songs_path()
		query = getattr(self, "_liked_filter", None)
		query = query.GetValue().strip().lower() if query else ""
		if os.path.isfile(path):
			try:
				with open(path, encoding="utf-8") as fh:
					lines = [l.rstrip("\n") for l in fh if l.strip()]
				# Apply the filter: only show lines that contain the query string.
				if query:
					lines = [l for l in lines if query in l.lower()]
				for line in lines:
					label = self._with_marked_suffix(line, line in self._liked_marked)
					self._liked_list.Append(label)
				if not lines:
					# Translators: Placeholder row shown when the liked-songs filter matches nothing.
					self._liked_list.Append(_("No results found."))
			except Exception as e:
				# Translators: Placeholder row shown when the liked-songs text file exists but can't be read; %s is the underlying error.
				self._liked_list.Append(_("Could not read file: %s") % str(e))
		else:
			# Translators: Placeholder row shown when the liked-songs file is empty or has not been created yet.
			self._liked_list.Append(_("No liked songs yet."))
		self._liked_spotify_btn.Enable(False)
		self._liked_youtube_btn.Enable(False)
		self._liked_lyrics_btn.Enable(False)
		self._liked_remove_btn.Enable(False)

	def _on_liked_filter_changed(self, event):
		"""Rebuild the liked songs list whenever the filter field changes.

		Announces the result count so screen-reader users get immediate feedback.
		"""
		self._refresh_liked_list()
		count = sum(
			1 for i in range(self._liked_list.GetCount())
			# Translators: Same two placeholder rows as in _on_liked_remove (empty-list / filtered-to-nothing), excluded when counting real songs for the filter-result announcement below.
			if self._liked_list.GetString(i) not in (_("No liked songs yet."), _("No results found."))
		)
		if count == 0:
			# Translators: Spoken when the liked-songs filter matches nothing (list has real songs, just none matching the filter text).
			ui.message(_("No results found"))
		else:
			# Translators: Plural forms spoken after filtering the liked-songs list; %d is how many songs match.
			ui.message(ngettext("%d song", "%d songs", count) % count)
		event.Skip()

	def _on_liked_filter_key(self, event):
		"""Down arrow moves focus from the filter field into the liked songs list."""
		if event.GetKeyCode() == wx.WXK_DOWN:
			self._liked_list.SetFocus()
			if self._liked_list.GetCount() > 0 and self._liked_list.GetSelection() == wx.NOT_FOUND:
				self._liked_list.SetSelection(0)
		else:
			event.Skip()

	def _on_liked_selected(self, event):
		has_sel = self._liked_list.GetSelection() != wx.NOT_FOUND
		# Disable buttons if the placeholder "no songs" line is shown
		real_song = has_sel and self._liked_list.GetCount() > 0 and \
			self._liked_list.GetString(self._liked_list.GetSelection()) not in (
				# Translators: Same placeholder row as elsewhere in this tab (see _on_liked_remove); only this one is checked here since a filtered-to-nothing list still has real buttons disabled by has_sel above.
				_("No liked songs yet."),
			)
		self._liked_spotify_btn.Enable(real_song)
		self._liked_youtube_btn.Enable(real_song)
		self._liked_lyrics_btn.Enable(real_song)
		self._liked_remove_btn.Enable(real_song)
		event.Skip()

	def _get_liked_selection(self):
		"""Return the selected song string (with any "(marked)" suffix
		stripped), or None."""
		idx = self._liked_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return None
		text = self._strip_marked_suffix(self._liked_list.GetString(idx))
		# Translators: Same two placeholder rows as in _on_liked_remove/_get_liked_selection callers, treated as "nothing selected".
		if text in (_("No liked songs yet."), _("No results found.")):
			return None
		return text

	def _on_liked_spotify(self, event):
		import urllib.parse
		import webbrowser
		song = self._get_liked_selection()
		if not song:
			return
		query = urllib.parse.quote(song)
		# Try the Spotify URI scheme first — opens the desktop app if installed.
		# os.startfile launches the URI via the registered handler (spotify.exe).
		# If the app is not installed, startfile raises OSError; fall back to browser.
		try:
			os.startfile("spotify:search:" + urllib.parse.quote(song, safe=""))
		except OSError:
			# autoplay=true makes the web player start the first result automatically
			url = "https://open.spotify.com/search/" + query + "?autoplay=true"
			webbrowser.open(url)

	def _on_liked_youtube(self, event):
		import urllib.parse
		import webbrowser
		song = self._get_liked_selection()
		if not song:
			return
		url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(song)
		webbrowser.open(url)

	def _on_liked_list_key(self, event):
		"""Liked Songs list — Delete removes every marked song (or, if
		none are marked, triggers the Remove button as before); '.' is
		handled globally in _on_char_hook(), same as the Favourites list's
		','; Applications key / Shift+F10 opens the context menu."""
		key = event.GetKeyCode()
		if key == wx.WXK_DELETE:
			if self._liked_marked:
				self._on_liked_remove_selected(event)
			elif self._liked_remove_btn.IsEnabled():
				self._on_liked_remove(event)
			return
		if key == wx.WXK_WINDOWS_MENU or (key == wx.WXK_F10 and event.ShiftDown()):
			self._show_liked_context_menu()
			return
		event.Skip()

	def _toggle_liked_mark(self):
		"""Mark/unmark the focused liked song with '.' for the Remove
		Selected bulk-delete flow (Delete key or context menu). Updates
		the row's display text immediately so the marked state is
		visible/announced while simply arrowing through the list
		afterwards, not only at the moment of marking."""
		idx = self._liked_list.GetSelection()
		song = self._get_liked_selection()
		if not song:
			return
		if song in self._liked_marked:
			self._liked_marked.discard(song)
			# Translators: Spoken after unmarking a liked song in the multi-select removal flow; %s is the song string.
			ui.message(_("Unmarked: %s") % song)
		else:
			self._liked_marked.add(song)
			# Translators: Spoken after marking a liked song in the multi-select removal flow; %s is the song string.
			ui.message(_("Marked: %s") % song)
		self._liked_list.SetString(idx, self._with_marked_suffix(song, song in self._liked_marked))
		self._liked_list.SetSelection(idx)

	def _on_liked_remove_selected(self, event=None):
		"""Bulk-remove every liked song currently marked with '.', asking
		for confirmation once for the whole batch."""
		marked = self._liked_marked
		if not marked:
			return
		count = len(marked)
		# Translators: Body of the bulk-remove confirmation dialog for liked songs; %d is how many songs are marked.
		message = ngettext(
			"Do you want to remove the %d marked song from liked songs?",
			"Do you want to remove the %d marked songs from liked songs?",
			count,
		) % count
		# Translators: Title of the bulk-remove confirmation dialog for liked songs.
		if not self._confirm_bulk_remove(count, _("Remove Songs"), message):
			return
		path = self._liked_songs_path()
		try:
			with open(path, encoding="utf-8") as fh:
				lines = [l.rstrip("\n") for l in fh]
			new_lines = [l for l in lines if l not in marked]
			with open(path, "w", encoding="utf-8") as fh:
				fh.write("\n".join(new_lines))
				if new_lines:
					fh.write("\n")
		except Exception as e:
			# Translators: Spoken if writing the updated liked-songs file back to disk fails; %s is the underlying error message.
			ui.message(_("Could not remove song: %s") % str(e))
			return
		self._liked_marked.clear()
		# Translators: Spoken after bulk-removing marked liked songs; %d is how many were removed.
		ui.message(ngettext("%d song removed", "%d songs removed", count) % count)
		self._refresh_liked_list()
		if self._liked_list.GetCount() > 0:
			self._liked_list.SetSelection(0)
			self._on_liked_selected(wx.CommandEvent())
			self._liked_list.SetFocus()
		else:
			self._liked_refresh_btn.SetFocus()

	def _show_liked_context_menu(self):
		"""Context menu for the selected item in the Liked Songs list.

		Mirrors the existing action buttons on the tab; items are disabled
		when no real song is selected so screen readers still announce a
		consistent menu.
		"""
		song = self._get_liked_selection()

		menu = wx.Menu()

		# Translators: Context-menu item; same action as the Play on Spotify button.
		item_spotify = menu.Append(wx.ID_ANY, _("Play on &Spotify"))
		item_spotify.Enable(bool(song))
		self.Bind(wx.EVT_MENU, self._on_liked_spotify, item_spotify)

		# Translators: Context-menu item; same action as the Play on YouTube button.
		item_youtube = menu.Append(wx.ID_ANY, _("Play on Y&ouTube"))
		item_youtube.Enable(bool(song))
		self.Bind(wx.EVT_MENU, self._on_liked_youtube, item_youtube)

		# Translators: Context-menu item; same action as the Show Lyrics button.
		item_lyrics = menu.Append(wx.ID_ANY, _("Show &Lyrics"))
		item_lyrics.Enable(bool(song))
		self.Bind(wx.EVT_MENU, self._on_liked_lyrics, item_lyrics)

		menu.AppendSeparator()

		# Translators: Context-menu item; same action as the Remove button.
		item_remove = menu.Append(wx.ID_ANY, _("Re&move"))
		item_remove.Enable(bool(song))
		self.Bind(wx.EVT_MENU, self._on_liked_remove, item_remove)

		# Translators: Context-menu item; bulk-removes every liked song marked with '.', asking for confirmation once for the whole batch.
		item_remove_selected = menu.Append(wx.ID_ANY, _("Remove &Selected"))
		item_remove_selected.Enable(bool(self._liked_marked))
		self.Bind(wx.EVT_MENU, self._on_liked_remove_selected, item_remove_selected)

		menu.AppendSeparator()

		# Translators: Context-menu item; same action as the Refresh button.
		item_refresh = menu.Append(wx.ID_ANY, _("R&efresh"))
		self.Bind(wx.EVT_MENU, self._on_liked_refresh, item_refresh)

		self.PopupMenu(menu, self._liked_list.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _on_liked_remove(self, event):
		idx = self._liked_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		song = self._strip_marked_suffix(self._liked_list.GetString(idx))
		# Translators: Two placeholder rows shown in the (otherwise empty or filtered-empty) liked-songs list; both are checked here so trying to remove a placeholder row is silently ignored instead of erroring.
		if song in (_("No liked songs yet."), _("No results found.")):
			return
		# Ask for confirmation before removing the song.
		dlg = wx.MessageDialog(
			self,
			# Translators: Body of the remove-confirmation dialog; %s is the song string as stored in the liked-songs file (e.g. "Artist - Title").
			_("Do you want to remove \"%s\" from liked songs?") % song,
			# Translators: Title of the remove-song confirmation dialog.
			_("Remove Song"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		)
		result = dlg.ShowModal()
		dlg.Destroy()
		if result != wx.ID_YES:
			return
		path = self._liked_songs_path()
		try:
			with open(path, encoding="utf-8") as fh:
				lines = [l.rstrip("\n") for l in fh]
			# Remove only the first occurrence
			removed = False
			new_lines = []
			for line in lines:
				if not removed and line == song:
					removed = True
				else:
					new_lines.append(line)
			with open(path, "w", encoding="utf-8") as fh:
				fh.write("\n".join(new_lines))
				if new_lines:
					fh.write("\n")
		except Exception as e:
			# Translators: Spoken if writing the updated liked-songs file back to disk fails; %s is the underlying error message.
			ui.message(_("Could not remove song: %s") % str(e))
			return
		# Remember the deleted index so we can restore focus afterwards.
		deleted_idx = idx
		self._liked_marked.discard(song)
		self._refresh_liked_list()
		# Translators: Spoken after successfully removing a song; %s is the removed song string.
		ui.message(_("Removed: %s") % song)
		# After deletion keep focus on the next item (or the last one if the
		# deleted item was at the end); move to Refresh button if the list is empty.
		count = self._liked_list.GetCount()
		real_song_count = sum(
			1 for i in range(count)
			# Translators: Same two placeholder-row strings as above, excluded when counting how many real songs remain after a removal.
			if self._liked_list.GetString(i) not in (_("No liked songs yet."), _("No results found."))
		)
		if real_song_count > 0:
			new_idx = min(deleted_idx, real_song_count - 1)
			self._liked_list.SetSelection(new_idx)
			self._liked_list.SetFocus()
			# Update button states.
			self._on_liked_selected(wx.CommandEvent())
		else:
			self._liked_refresh_btn.SetFocus()

	def _on_liked_refresh(self, event):
		self._refresh_liked_list()
		# Translators: Spoken after the Refresh button reloads the liked-songs list from disk.
		ui.message(_("Liked songs list refreshed"))

	def _on_liked_lyrics(self, event):
		song = self._get_liked_selection()
		if not song:
			return
		self._liked_lyrics_btn.Enable(False)
		# Translators: Spoken when a lyrics lookup starts for the selected liked song.
		ui.message(_("Fetching lyrics…"))
		from . import lyricsService

		def _on_result(lyrics, error):
			wx.CallAfter(self._liked_lyrics_btn.Enable, True)
			if lyrics:
				wx.CallAfter(self._show_lyrics_dialog, song, lyrics)
			else:
				# Translators: Spoken when a lyrics lookup for a liked song finds nothing; %s is the song string.
				wx.CallAfter(ui.message, _("Lyrics not found for: %s") % song)

		lyricsService.fetch_lyrics(song, _on_result)

	def _show_lyrics_dialog(self, song, lyrics):
		dlg = LyricsDialog(self, song, lyrics)
		dlg.ShowModal()
		dlg.Destroy()


	# ------------------------------------------------------------------ #
	# Podcast Tab
	# ------------------------------------------------------------------ #

	def _build_podcast_tab(self):
		"""Podcast subscriptions and episodes tab."""
		panel = self._podcast_panel
		sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Search row ---
		search_sizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Label for the podcast search field.
		search_sizer.Add(wx.StaticText(panel, label=_("Search:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._podcast_search = wx.TextCtrl(panel)
		# Translators: Accessible name/hint for the podcast search field: it accepts either a search phrase or a direct feed URL, and searches or subscribes on Enter.
		self._podcast_search.SetName(_("Search podcasts, or enter a podcast feed URL. Press enter to search or add"))
		search_sizer.Add(self._podcast_search, 1, wx.EXPAND)
		sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 8)

		# --- Search results list ---
		# Hidden until a search is actually performed - see
		# _on_podcast_search() and _set_podcast_results_visible(). Keeping
		# it out of the way when there's nothing to search for avoids an
		# empty "Search results" list/label sitting in the tab from the
		# moment it's opened.
		# Translators: Label above the search-results list of podcasts.
		self._podcast_results_label = wx.StaticText(panel, label=_("Search results:"))
		sizer.Add(self._podcast_results_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._podcast_results = wx.ListBox(panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the podcast search-results list.
		self._podcast_results.SetName(_("Podcast search results"))
		self._podcast_results.SetMinSize((-1, 80))
		sizer.Add(self._podcast_results, 0, wx.EXPAND | wx.ALL, 8)

		# --- Preview episodes for the selected search result ---
		# Lets the user browse a feed's episodes before deciding to subscribe.
		# Subscribing itself is done via the search results' context menu
		# (Applications key / Shift+F10), not a button. Hidden alongside the
		# search results list until a search has been performed.
		# Translators: Label above the read-only episode list previewing a selected search result, before subscribing.
		self._podcast_preview_label = wx.StaticText(panel, label=_("Episodes in selected result:"))
		sizer.Add(self._podcast_preview_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._podcast_preview_list = wx.ListBox(panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the episode-preview list.
		self._podcast_preview_list.SetName(_("Episode preview for selected search result"))
		self._podcast_preview_list.SetMinSize((-1, 80))
		sizer.Add(self._podcast_preview_list, 0, wx.EXPAND | wx.ALL, 8)
		self._podcast_search_sizer = sizer
		self._set_podcast_results_visible(False)

		# --- Separator ---
		sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 4)

		# --- Subscriptions list ---
		# Translators: Label above the list of subscribed podcast feeds.
		sizer.Add(wx.StaticText(panel, label=_("Subscriptions:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._podcast_list = wx.ListBox(panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the podcast-subscriptions list.
		self._podcast_list.SetName(_("Podcast subscriptions"))
		self._podcast_list.SetMinSize((-1, 80))
		sizer.Add(self._podcast_list, 0, wx.EXPAND | wx.ALL, 8)

		# --- Selected feed details (read-only, reachable by Tab right
		# after the subscriptions list) ---
		self._feed_details = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
		# Translators: Accessible name for the read-only feed-details text field.
		self._feed_details.SetName(_("Feed details"))
		self._feed_details.SetMinSize((-1, 60))
		sizer.Add(self._feed_details, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		# --- Episode filter ---
		ep_filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Label for the field that filters the episode list below by title or number.
		ep_filter_sizer.Add(wx.StaticText(panel, label=_("Filter:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._episode_filter = wx.TextCtrl(panel)
		# Translators: Accessible name/hint for the episode filter field.
		self._episode_filter.SetName(_("Filter episodes by title or number"))
		ep_filter_sizer.Add(self._episode_filter, 1, wx.EXPAND)
		sizer.Add(ep_filter_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# --- Episodes list ---
		# Translators: Label above the list of episodes for the selected subscription.
		sizer.Add(wx.StaticText(panel, label=_("Episodes:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._episode_list = wx.ListBox(panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the podcast-episodes list.
		self._episode_list.SetName(_("Podcast episodes"))
		self._episode_list.SetMinSize((-1, 120))
		sizer.Add(self._episode_list, 1, wx.EXPAND | wx.ALL, 8)

		# --- Selected episode details (read-only, reachable by Tab right
		# after the episode list) ---
		self._episode_details = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
		# Translators: Accessible name for the read-only episode-details text field.
		self._episode_details.SetName(_("Episode details"))
		self._episode_details.SetMinSize((-1, 60))
		sizer.Add(self._episode_details, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		# Episode buttons — playing an episode is available via Enter/Space
		# on the list and via the context menu, so there's no separate
		# "Play Episode" button here.
		ep_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Button label; downloads the currently selected episode to disk.
		self._episode_download_btn = wx.Button(panel, label=_("&Download Episode"))
		self._episode_download_btn.Enable(False)
		ep_btn_sizer.Add(self._episode_download_btn, 0)
		sizer.Add(ep_btn_sizer, 0, wx.LEFT | wx.BOTTOM, 8)

		panel.SetSizer(sizer)

		# --- Bind events ---
		self._podcast_search.Bind(wx.EVT_KEY_DOWN, self._on_podcast_search_key)
		self._podcast_results.Bind(wx.EVT_LISTBOX, self._on_podcast_result_selected)
		self._podcast_list.Bind(wx.EVT_LISTBOX, self._on_podcast_selected)
		self._podcast_list.Bind(wx.EVT_CHAR, self._on_list_char)
		self._podcast_results.Bind(wx.EVT_CHAR, self._on_list_char)
		self._podcast_preview_list.Bind(wx.EVT_CHAR, self._on_list_char)
		self._podcast_list.Bind(wx.EVT_KEY_DOWN, self._on_podcast_list_key)
		self._episode_filter.Bind(wx.EVT_TEXT,     self._on_episode_filter_changed)
		self._episode_filter.Bind(wx.EVT_KEY_DOWN, self._on_episode_filter_key)
		self._episode_list.Bind(wx.EVT_LISTBOX, self._on_episode_selected)
		self._episode_list.Bind(wx.EVT_CHAR, self._on_list_char)
		self._episode_list.Bind(wx.EVT_KEY_DOWN, self._on_episode_key)
		self._episode_download_btn.Bind(wx.EVT_BUTTON, self._on_episode_download)

		# Deferred: populated lazily the first time this tab becomes active,
		# either via tab-switch (_apply_tab_side_effects, sel == 5) or via
		# focus_podcasts() when the dialog is opened straight to this tab -
		# not eagerly at dialog construction time.

	def _refresh_podcast_list(self):
		"""Populate the podcast subscription listbox.

		Preserves whichever feed/episode is selected *at the moment this runs*
		(not a snapshot from earlier), since wx.ListBox.Clear() resets the
		selection to NOT_FOUND. This matters most for the background bulk
		refresh: if the user switches to a different feed or episode while the
		refresh is still in flight, this must keep following that new choice
		rather than snapping back to whatever was selected when the refresh
		started. If the previously-selected feed/episode is gone (e.g. removed
		meanwhile) it falls back to index 0.
		"""
		current_feed_url = None
		idx = self._podcast_list.GetSelection()
		feeds_before = self._podcast_manager.get_feeds()
		if idx != wx.NOT_FOUND and idx < len(feeds_before):
			current_feed_url = feeds_before[idx].url

		current_episode_url = None
		if current_feed_url is not None:
			ep_idx = self._episode_list.GetSelection()
			filtered = getattr(self, "_episode_filtered", [])
			if ep_idx != wx.NOT_FOUND and ep_idx < len(filtered):
				current_episode_url = filtered[ep_idx].url

		self._podcast_list.Clear()
		feeds = self._podcast_manager.get_feeds()
		for feed in feeds:
			count = len(feed.episodes)
			label = f"{feed.title} ({count} ep.)" if count > 0 else feed.title
			self._podcast_list.Append(label)

		restore_idx = wx.NOT_FOUND
		if current_feed_url:
			for i, feed in enumerate(feeds):
				if feed.url == current_feed_url:
					restore_idx = i
					break

		if restore_idx != wx.NOT_FOUND:
			self._podcast_list.SetSelection(restore_idx)
			self._refresh_episode_list(restore_episode_url=current_episode_url)
		elif self._podcast_list.GetCount() > 0:
			self._podcast_list.SetSelection(0)
			self._on_podcast_selected(None)

	def _refresh_all_podcast_feeds(self):
		"""Re-fetch every subscribed feed in the background, then repopulate the UI.

		Called whenever the Podcasts tab is opened so new episodes show up
		without the user having to refresh each feed by hand. _refresh_podcast_list
		preserves whatever feed/episode is selected when it runs (i.e. at
		completion time, not when the refresh started), so switching selection
		while the refresh is still running just works.
		"""
		feeds = self._podcast_manager.get_feeds()
		if not feeds:
			self._refresh_podcast_list()
			return
		if getattr(self, "_podcast_bulk_refreshing", False):
			return
		self._podcast_bulk_refreshing = True
		# Translators: Spoken when refreshing every subscribed podcast feed at once (as opposed to a single feed).
		ui.message(_("Updating podcast feeds..."))

		def _do_refresh_all():
			for feed in feeds:
				try:
					self._podcast_manager.refresh_feed(feed.url)
				except Exception:
					pass
			wx.CallAfter(self._on_all_podcast_feeds_refreshed)

		threading.Thread(target=_do_refresh_all, daemon=True).start()

	def _on_all_podcast_feeds_refreshed(self):
		self._podcast_bulk_refreshing = False
		if not self:
			return
		self._refresh_podcast_list()
		# Translators: Spoken after all subscribed feeds finish refreshing.
		ui.message(_("Podcast feeds updated."))

	def _on_podcast_add(self, url):
		"""Add a feed directly from a URL typed into the search field - see
		_on_podcast_search(), which routes here instead of doing an iTunes
		search whenever the field's contents look like a URL."""
		self._podcast_search.Disable()
		# Translators: Spoken when subscribing to a feed by pasted URL (as opposed to from a search result).
		ui.message(_("Fetching podcast feed..."))

		def _do_add():
			feed, error = self._podcast_manager.add_feed(url)
			wx.CallAfter(self._on_podcast_add_done, feed, error)

		threading.Thread(target=_do_add, daemon=True).start()

	def _on_podcast_add_done(self, feed, error):
		self._podcast_search.Enable()
		if error:
			# Translators: Spoken when subscribing to a feed fails; %s is the underlying error.
			ui.message(_("Could not add feed: %s") % error)
			return
		self._podcast_search.SetValue("")
		self._set_podcast_results_visible(False)
		# Translators: Spoken after successfully subscribing to a feed; %s is the feed title.
		ui.message(_("Feed added: %s") % feed.title)
		self._refresh_podcast_list()

	def _on_podcast_selected(self, event):
		idx = self._podcast_list.GetSelection()
		feeds = self._podcast_manager.get_feeds()
		feed = feeds[idx] if idx != wx.NOT_FOUND and idx < len(feeds) else None
		self._feed_details.ChangeValue(self._format_feed_details(feed))
		# Switching feeds starts with an empty filter and the fresh episode list.
		self._episode_filter.ChangeValue("")
		self._refresh_episode_list()

	def _get_selected_podcast_feed(self):
		"""Return the PodcastFeed currently selected in the subscriptions
		list, or None. Used to look up (or set) the feed-wide audio
		profile that applies to all of its episodes - see
		_on_episode_play(), _on_save_feed_audio_profile()."""
		idx = self._podcast_list.GetSelection()
		feeds = self._podcast_manager.get_feeds()
		if idx == wx.NOT_FOUND or idx >= len(feeds):
			return None
		return feeds[idx]

	def _on_save_feed_audio_profile(self, event):
		"""Save an audio profile (volume/effects/EQ, and optionally
		playback speed) that applies to every episode of the selected
		podcast feed - see playbackCoreMixin._play_station() and
		_on_episode_play()."""
		feed = self._get_selected_podcast_feed()
		if not feed:
			return
		profile = self._prompt_and_build_audio_profile(feed.audio_profile, allow_speed=True)
		if profile is None:
			return
		feed.audio_profile = profile
		self._podcast_manager._save()
		# Translators: Spoken after saving a podcast-feed-specific audio profile; %(feed)s is the feed title.
		ui.message(_("Audio profile saved for %(feed)s") % {"feed": feed.title})

	def _on_clear_feed_audio_profile(self, event):
		"""Remove the saved audio profile from the selected podcast feed."""
		feed = self._get_selected_podcast_feed()
		if not feed or not feed.audio_profile:
			return
		feed.audio_profile = None
		self._podcast_manager._save()
		# Translators: Spoken after clearing a feed's saved audio profile; %(feed)s is the feed title.
		ui.message(_("Audio profile cleared for %(feed)s") % {"feed": feed.title})

	def _format_feed_details(self, feed):
		"""Build the text shown in the read-only feed-details field for the
		given PodcastFeed (or "" if none is selected).
		"""
		if feed is None:
			return ""
		lines = [feed.title]
		if feed.author:
			# Translators: Field:value line for the feed's author, in the feed-details text block.
			lines.append(_("By: %s") % feed.author)
		count = len(feed.episodes)
		# Translators: Plural forms for the episode-count line in the feed-details text block.
		lines.append(ngettext("%d episode", "%d episodes", count) % count)
		if feed.description:
			description = _html_to_text(feed.description)
			if description:
				lines.append("")
				lines.append(description)
		lines.append("")
		lines.append(feed.url)
		return "\n".join(lines)

	def _refresh_episode_list(self, restore_episode_url=None):
		"""Populate the episode listbox for the currently selected feed,
		preserving the user's current selection and focus if active."""
		# Remember selection index before clearing
		prev_idx = self._episode_list.GetSelection()

		self._episode_list.Clear()
		self._episode_filtered = []
		self._episode_download_btn.Enable(False)
		self._episode_details.ChangeValue("")

		idx = self._podcast_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		feeds = self._podcast_manager.get_feeds()
		if idx >= len(feeds):
			return
		feed = feeds[idx]

		query = self._episode_filter.GetValue().strip().lower()
		if query:
			episodes = [
				ep for ep in feed.episodes
				if query in ep.title.lower() or (ep.number is not None and str(ep.number) == query)
			]
		else:
			episodes = list(feed.episodes)
		self._episode_filtered = episodes

		for ep in episodes:
			self._episode_list.Append(ep.display_label(player=self._player))

		count = self._episode_list.GetCount()
		if count == 0:
			return

		select_idx = 0
		if restore_episode_url:
			for i, ep in enumerate(episodes):
				if ep.url == restore_episode_url:
					select_idx = i
					break
		elif prev_idx != wx.NOT_FOUND and prev_idx < count:
			select_idx = prev_idx

		self._episode_list.SetSelection(select_idx)
		self._on_episode_selected(None)

	def _on_episode_filter_changed(self, event):
		"""Rebuild the episode list whenever the filter field changes."""
		self._refresh_episode_list()
		count = self._episode_list.GetCount()
		if count == 0:
			# Translators: Spoken when the episode filter matches nothing.
			ui.message(_("No episodes found"))
		else:
			# Translators: Plural forms spoken after filtering the episode list; %d is how many match. Same wording as the feed-details episode count above.
			ui.message(ngettext("%d episode", "%d episodes", count) % count)
		event.Skip()

	def _on_episode_filter_key(self, event):
		"""Down arrow moves focus from the filter field into the episode list."""
		if event.GetKeyCode() == wx.WXK_DOWN:
			self._episode_list.SetFocus()
			if self._episode_list.GetCount() > 0 and self._episode_list.GetSelection() == wx.NOT_FOUND:
				self._episode_list.SetSelection(0)
		else:
			event.Skip()

	def _on_podcast_list_key(self, event):
		"""Podcast subscriptions list — Delete key removes the focused feed."""
		if event.GetKeyCode() == wx.WXK_DELETE:
			self._on_podcast_remove(event)
			return
		event.Skip()

	def _on_podcast_refresh(self, event):
		idx = self._podcast_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		feeds = self._podcast_manager.get_feeds()
		if idx >= len(feeds):
			return
		feed = feeds[idx]

		# Translators: Spoken when manually refreshing a single feed (as opposed to all feeds); %s is the feed title.
		ui.message(_("Refreshing feed: %s") % feed.title)

		def _do_refresh():
			updated_feed, error = self._podcast_manager.refresh_feed(feed.url)
			wx.CallAfter(self._on_podcast_refresh_done, updated_feed, error)

		threading.Thread(target=_do_refresh, daemon=True).start()

	def _on_podcast_refresh_done(self, feed, error):
		if error:
			# Translators: Spoken when manually refreshing a podcast feed fails; %s is the underlying error.
			ui.message(_("Refresh failed: %s") % error)
			return
		# Translators: Spoken after successfully refreshing a feed; %s is the feed title.
		ui.message(_("Feed refreshed: %s") % feed.title)
		self._refresh_podcast_list()

	def _on_podcast_remove(self, event):
		idx = self._podcast_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		feeds = self._podcast_manager.get_feeds()
		if idx >= len(feeds):
			return
		feed = feeds[idx]

		dlg = wx.MessageDialog(
			self,
			# Translators: Body of the unsubscribe-confirmation dialog; %s is the podcast feed title.
			_("Do you want to remove the feed \"%s\"?") % feed.title,
			# Translators: Title of the unsubscribe-confirmation dialog.
			_("Remove Feed"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		)
		result = dlg.ShowModal()
		dlg.Destroy()
		if result != wx.ID_YES:
			return

		self._podcast_manager.remove_feed(feed.url)
		# The feed's own audio profile is discarded automatically along with
		# the rest of the feed object above. Its episodes' saved resume
		# positions live separately, in RadioPlayer's own store (keyed by
		# episode URL), and are cleaned up here so they don't linger for
		# episodes the user can no longer see or resume.
		if feed.episodes and self._player:
			urls = [ep.url for ep in feed.episodes if ep.url]
			self._player.clear_podcast_positions(urls)
		# Translators: Spoken after successfully unsubscribing from a feed; %s is the feed title.
		ui.message(_("Feed removed: %s") % feed.title)
		self._refresh_podcast_list()

	def _on_episode_selected(self, event):
		idx = self._episode_list.GetSelection()
		has_ep = idx != wx.NOT_FOUND
		self._episode_download_btn.Enable(has_ep)
		episodes = getattr(self, "_episode_filtered", None) or []
		ep = episodes[idx] if has_ep and idx < len(episodes) else None
		self._episode_details.ChangeValue(self._format_episode_details(ep))

	def _format_episode_details(self, ep):
		"""Build the text shown in the read-only episode-details field for
		the given PodcastEpisode (or "" if none is selected).

		published is a datetime (or None) on PodcastEpisode - interpolated
		the same way display_label() already does elsewhere in this file,
		rather than assuming a particular strftime format. The By/
		Published/Duration/description lines are built by the shared
		_format_podcast_episode_lines() - see its docstring.
		"""
		if ep is None:
			return ""
		lines = [ep.title]
		lines.extend(_format_podcast_episode_lines(
			published=str(ep.published) if ep.published else "",
			duration=ep.duration,
			description=ep.description,
		))
		lines.append("")
		lines.append(ep.url)
		return "\n".join(lines)

	def _html_to_text(self, text):
		"""Kept as a thin wrapper - see the module-level _html_to_text()
		this delegates to, which is what new code (including
		trackInfoMixin.py) should call directly."""
		return _html_to_text(text)

	def refresh_episode_progress(self, url):
		"""Refresh a single episode row's [Listened]/duration display right
		after its position was saved due to a pause or the episode
		finishing (not the periodic autosave). Deliberately event-driven
		instead of a continuously-ticking timer - a per-second live update
		used to make NVDA re-announce the focused row every second while a
		podcast was playing, so that was removed. This only fires on real
		state changes (pause / finish), so it's safe to update even while
		the row has focus.

		Uses SetString() rather than _refresh_episode_list(): that does a
		Clear()+Append() which would drop the current selection, and
		SetSelection() afterwards would make NVDA re-announce the item.
		"""
		if not url:
			return
		episodes = getattr(self, "_episode_filtered", None) or []
		for i, ep in enumerate(episodes):
			if ep.url == url:
				try:
					new_label = ep.display_label(self._player)
					if self._episode_list.GetString(i) != new_label:
						self._episode_list.SetString(i, new_label)
				except Exception:
					pass
				break

	def refresh_jukebox_track_progress(self, url):
		"""Refresh a single jukebox track row's [Listened]/duration
		display right after its position was saved due to a pause or the
		track finishing - the jukebox counterpart of
		refresh_episode_progress(). Called from the same
		on_podcast_progress_saved callback: jukebox tracks share the
		podcast positions store with podcast episodes and audio-book
		chapters (see radioPlayer._is_seekable_media(), which includes
		"jukebox"), and the URL the callback carries for a jukebox track
		is just its file path (JukeboxTrack.to_dict() sets "url" to
		path).

		SetString() is used rather than rebuilding the list, for the same
		reason as refresh_episode_progress(): a Clear()+Append() would
		drop the current selection, and SetSelection() afterwards would
		make NVDA re-announce the focused row."""
		if not url:
			return
		tracks = getattr(self, "_jukebox_selected_tracks", None) or []
		for i, track in enumerate(tracks):
			if track.path == url:
				try:
					new_label = track.display_label(self._player)
					if self._jukebox_tracks_list.GetString(i) != new_label:
						self._jukebox_tracks_list.SetString(i, new_label)
				except Exception:
					pass
				break

	def _on_episode_key(self, event):
		key = event.GetKeyCode()
		if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			self._on_episode_play(event)
			return
		if key == wx.WXK_SPACE:
			# Space: pause whatever is currently playing; otherwise start
			# playback of the focused episode (regardless of whether the
			# player merely has stale/paused media loaded from before).
			if self._player.is_playing():
				self._player.pause()
				# Translators: Same "Paused" wording as elsewhere; spoken here when Space pauses playback from the podcast episode list.
				_notify(_("Paused"))
			else:
				self._on_episode_play(None)
			return
		if key == wx.WXK_RIGHT:
			count = self._episode_list.GetCount()
			if count == 0:
				event.Skip()
				return
			idx = self._episode_list.GetSelection()
			next_idx = (idx + 1) % count if idx != wx.NOT_FOUND else 0
			self._episode_list.SetSelection(next_idx)
			self._on_episode_play(None, idx=next_idx, announce=False)
			return
		if key == wx.WXK_LEFT:
			count = self._episode_list.GetCount()
			if count == 0:
				event.Skip()
				return
			idx = self._episode_list.GetSelection()
			prev_idx = (idx - 1) % count if idx != wx.NOT_FOUND else 0
			self._episode_list.SetSelection(prev_idx)
			self._on_episode_play(None, idx=prev_idx, announce=False)
			return
		event.Skip()

	def _on_episode_play(self, event, idx=None, announce=True):
		if idx is None:
			idx = self._episode_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		episodes = getattr(self, "_episode_filtered", None) or []
		if idx >= len(episodes):
			return
		episode = episodes[idx]

		station_dict = episode.to_dict()
		# Apply the feed-wide audio profile (volume/effects/EQ and,
		# optionally, playback speed) if the currently selected feed has
		# one saved - see _on_save_feed_audio_profile() and
		# playbackCoreMixin._play_station().
		feed = self._get_selected_podcast_feed()
		if feed:
			# Carried through to config.conf["freeradio"]["last_station_podcast_feed_url"]
			# by playbackCoreMixin._play_station() - lets a "resume last
			# station" on the next NVDA startup look this feed's audio
			# profile back up and apply it too, the same way
			# _rebuild_getem_resume_url() does for audio books (see
			# GlobalPlugin._resume_last_station()).
			station_dict["podcast_feed_url"] = feed.url
			if feed.author:
				station_dict["podcast_author"] = feed.author
			if feed.audio_profile:
				station_dict["station_audio"] = feed.audio_profile
			# The feed (podcast) title is included here for the same
			# reason as RadioDialog._format_getem_now_playing_name() -
			# PodcastEpisode.to_dict() only knows its own episode title
			# (an episode has no reference back to its feed), but this
			# "name" is what playbackCoreMixin._play_station() announces
			# as "what's playing" and shows in Ctrl+Win+I's station info,
			# and a bare episode title on its own doesn't say which
			# podcast it's from.
			if episode.title and episode.title != feed.title:
				station_dict["name"] = "%s — %s" % (feed.title, episode.title)
			else:
				station_dict["name"] = feed.title
		self._play_callback(station_dict, [station_dict], 0, announce=announce)

	def _on_episode_download(self, event):
		idx = self._episode_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		episodes = getattr(self, "_episode_filtered", None) or []
		if idx >= len(episodes):
			return
		episode = episodes[idx]

		out_path, filename = podcast.episode_download_target(episode.title, episode.url)

		if os.path.exists(out_path):
			# Translators: Spoken when trying to download an episode that was already downloaded before; %s is the existing filename.
			ui.message(_("File already exists: %s") % filename)
			return

		# Translators: Spoken when an episode download starts; %s is the episode title.
		ui.message(_("Downloading: %s") % episode.title)
		self._episode_download_btn.Disable()

		def _do_download():
			try:
				podcast.download_episode_file(episode.url, out_path)
				# Translators: Spoken when a podcast episode download finishes; %s is the saved filename.
				wx.CallAfter(ui.message, _("Download complete: %s") % filename)
			except Exception as e:
				# Translators: Spoken when a podcast episode download fails; %s is the underlying error.
				wx.CallAfter(ui.message, _("Download failed: %s") % str(e))
			finally:
				wx.CallAfter(self._episode_download_btn.Enable, True)

		threading.Thread(target=_do_download, daemon=True).start()

	def _set_podcast_results_visible(self, visible):
		"""Show or hide the search-results list and the episode-preview
		list (with their labels) in the Podcast tab. Hidden until a search
		is actually performed, so an empty "Search results" list/label
		doesn't sit in the tab from the moment it's opened."""
		sizer = getattr(self, "_podcast_search_sizer", None)
		widgets = (
			self._podcast_results_label, self._podcast_results,
			self._podcast_preview_label, self._podcast_preview_list,
		)
		for widget in widgets:
			if sizer:
				sizer.Show(widget, visible)
			else:
				widget.Show(visible)
		try:
			if sizer:
				sizer.Layout()
			else:
				self._podcast_panel.Layout()
		except Exception:
			pass

	def _on_podcast_search_key(self, event):
		if event.GetKeyCode() == wx.WXK_RETURN:
			self._on_podcast_search(event)
		else:
			event.Skip()

	def _on_podcast_search(self, event):
		query = self._podcast_search.GetValue().strip()
		if not query:
			# Translators: Spoken when the podcast search/subscribe field is submitted empty.
			ui.message(_("Please enter a search term or podcast feed URL."))
			return

		# A pasted/typed feed URL is added directly instead of being run
		# through the iTunes search API - see _on_podcast_add().
		if query.startswith(("http://", "https://")):
			self._on_podcast_add(query)
			return

		self._set_podcast_results_visible(True)
		self._podcast_search.Disable()
		# Translators: Spoken when a podcast keyword search starts.
		ui.message(_("Searching for podcasts..."))

		def _do_search():
			results = podcast.search_podcasts(query)
			wx.CallAfter(self._on_podcast_search_done, results)

		threading.Thread(target=_do_search, daemon=True).start()

	def _on_podcast_search_done(self, results):
		self._podcast_search.Enable()
		self._podcast_results.Clear()
		self._podcast_search_results = results
		if not results:
			# Translators: Spoken when a podcast keyword search returns no results.
			ui.message(_("No podcasts found."))
			return
		for item in results:
			label = f"{item['title']} — {item['artist']}"
			self._podcast_results.Append(label)
		# Translators: Spoken after a podcast keyword search finds results; %d is the count.
		ui.message(_("%d podcasts found.") % len(results))
		if results:
			self._podcast_results.SetSelection(0)
			self._on_podcast_result_selected(None)

	def _on_podcast_result_selected(self, event):
		"""When a search result is selected, fetch that feed's episodes in
		the background and show them in the preview list so the user can
		get a sense of the show before subscribing."""
		idx = self._podcast_results.GetSelection()
		self._podcast_preview_list.Clear()
		self._podcast_preview_episodes = []
		self._podcast_preview_feed_title = ""
		self._podcast_preview_feed = None
		if idx == wx.NOT_FOUND:
			return
		results = getattr(self, "_podcast_search_results", [])
		if idx >= len(results):
			return
		item = results[idx]
		feed_url = item.get('feedUrl')
		if not feed_url:
			# Translators: Placeholder row shown in the episode-preview list when the selected search result has no usable feed link.
			self._podcast_preview_list.Append(_("This podcast has no feed URL."))
			return

		self._podcast_preview_fetch_id = getattr(self, "_podcast_preview_fetch_id", 0) + 1
		fetch_id = self._podcast_preview_fetch_id
		# Translators: Placeholder row shown in the episode-preview list while fetching a feed to preview.
		self._podcast_preview_list.Append(_("Loading episodes..."))

		def _do_fetch():
			feed, error = self._podcast_manager.fetch_preview(feed_url)
			wx.CallAfter(self._on_podcast_preview_done, feed, error, fetch_id)

		threading.Thread(target=_do_fetch, daemon=True).start()

	def _on_podcast_preview_done(self, feed, error, fetch_id):
		if not self or fetch_id != getattr(self, "_podcast_preview_fetch_id", None):
			# Superseded by a newer selection - discard this result.
			return
		self._podcast_preview_list.Clear()
		if error or not feed or not feed.episodes:
			self._podcast_preview_episodes = []
			self._podcast_preview_feed_title = ""
			self._podcast_preview_feed = None
			# Translators: Placeholder row shown in the episode-preview list when a previewed feed has no episodes.
			self._podcast_preview_list.Append(_("No episodes found."))
			return
		self._podcast_preview_episodes = feed.episodes
		# Kept alongside the episodes so _on_podcast_preview_toggle() can
		# include the feed's title/url/author in the played station_dict,
		# the same way _on_episode_play() does for a subscribed feed - see
		# there for why. Stored as the whole *feed* object (rather than
		# separate title/url/author attributes) now that more than just
		# the title is needed.
		self._podcast_preview_feed = feed
		self._podcast_preview_feed_title = feed.title
		for ep in feed.episodes:
			self._podcast_preview_list.Append(ep.display_label())

	def _is_previewing(self, episode):
		"""Whether *episode* (from the preview list) is the item currently
		loaded in the player, regardless of whether it's playing or paused."""
		if not episode.url or not self._player.has_media():
			return False
		current = self._player.get_current_station() or {}
		return current.get("url") == episode.url

	def _on_podcast_preview_toggle(self, event):
		"""Preview (play) the selected episode from the search-result preview
		list, or stop it if it's already the one being previewed."""
		idx = self._podcast_preview_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		episodes = getattr(self, "_podcast_preview_episodes", None) or []
		if idx >= len(episodes):
			return
		episode = episodes[idx]

		if self._is_previewing(episode):
			if self._plugin:
				wx.CallAfter(self._plugin._stop_from_dialog)
			return

		station_dict = episode.to_dict()
		feed = getattr(self, "_podcast_preview_feed", None)
		feed_title = getattr(self, "_podcast_preview_feed_title", "") or ""
		if feed_title and episode.title and episode.title != feed_title:
			station_dict["name"] = "%s — %s" % (feed_title, episode.title)
		elif feed_title:
			station_dict["name"] = feed_title
		if feed:
			# Same fields _on_episode_play() attaches for a subscribed
			# feed, so the station-details dialog shows a "Podcast" link
			# and author here too, not just once the user has subscribed.
			station_dict["podcast_feed_url"] = feed.url
			if feed.author:
				station_dict["podcast_author"] = feed.author
		self._play_callback(station_dict, [station_dict], 0, announce=True)

	def _show_podcast_preview_context_menu(self):
		"""Context menu for the selected item in the episode preview list."""
		idx = self._podcast_preview_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		episodes = getattr(self, "_podcast_preview_episodes", None) or []
		if idx >= len(episodes):
			return
		episode = episodes[idx]

		menu = wx.Menu()
		# Translators: Same Preview/Stop Preview toggle pattern as the GETEM/jukebox context menus, applied to a podcast episode preview.
		label = _("&Stop Preview") if self._is_previewing(episode) else _("&Preview")
		item_preview = menu.Append(wx.ID_ANY, label)
		self.Bind(wx.EVT_MENU, self._on_podcast_preview_toggle, item_preview)

		self.PopupMenu(menu, self._podcast_preview_list.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _on_podcast_subscribe_from_results(self, event):
		"""Subscribe to the feed currently selected in the search results
		list. Reached via the search results' context menu or Enter."""
		idx = self._podcast_results.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		results = getattr(self, "_podcast_search_results", [])
		if idx >= len(results):
			return
		item = results[idx]
		feed_url = item.get('feedUrl')
		if not feed_url:
			# Translators: Spoken when trying to subscribe directly from a search result that has no usable feed link.
			ui.message(_("This podcast has no feed URL."))
			return

		# Translators: Spoken when subscribing to a feed directly from a search result.
		ui.message(_("Adding feed..."))

		def _do_add():
			feed, error = self._podcast_manager.add_feed(feed_url)
			wx.CallAfter(self._on_podcast_subscribe_from_results_done, feed, error)

		threading.Thread(target=_do_add, daemon=True).start()

	def _on_podcast_subscribe_from_results_done(self, feed, error):
		if error:
			# Translators: Same error as _on_podcast_add_done, spoken here after subscribing directly from a search result instead of a pasted URL.
			ui.message(_("Could not add feed: %s") % error)
			return
		# Translators: Same confirmation as _on_podcast_add_done, spoken here after subscribing directly from a search result.
		ui.message(_("Feed added: %s") % feed.title)
		self._refresh_podcast_list()

	def _play_prev_episode(self):
		"""Play the previous episode (select the previous item in the episode list, move
		focus to it, and play)."""
		idx = self._episode_list.GetSelection()
		if idx <= 0:
			# Translators: Spoken when trying to play the previous episode while already on the first one in the list.
			ui.message(_("Already at first episode"))
			return
		self._episode_list.SetSelection(idx - 1)
		self._episode_list.SetFocus()
		self._on_episode_play(None)

	def _play_next_episode(self):
		"""Play the next episode, moving focus to the episode list."""
		idx = self._episode_list.GetSelection()
		if idx == wx.NOT_FOUND:
			if self._episode_list.GetCount() > 0:
				self._episode_list.SetSelection(0)
				self._episode_list.SetFocus()
				self._on_episode_play(None)
			return
		if idx >= self._episode_list.GetCount() - 1:
			# Translators: Spoken when trying to play the next episode while already on the last one.
			ui.message(_("Already at last episode"))
			return
		self._episode_list.SetSelection(idx + 1)
		self._episode_list.SetFocus()
		self._on_episode_play(None)

	def _select_prev_feed(self):
		"""Select the previous podcast channel (previous in the subscription
		list) and move focus to it."""
		idx = self._podcast_list.GetSelection()
		if idx <= 0:
			# Translators: Spoken when cycling to the previous podcast feed while already on the first one.
			ui.message(_("Already at first feed"))
			return
		new_idx = idx - 1
		self._podcast_list.SetSelection(new_idx)
		was_focused = wx.Window.FindFocus() == self._podcast_list
		self._podcast_list.SetFocus()
		self._on_podcast_selected(None)
		if not was_focused:
			ui.message(self._podcast_list.GetString(new_idx))

	def _select_next_feed(self):
		"""Select the next podcast channel and move focus to it."""
		idx = self._podcast_list.GetSelection()
		if idx == wx.NOT_FOUND:
			if self._podcast_list.GetCount() > 0:
				self._podcast_list.SetSelection(0)
				was_focused = wx.Window.FindFocus() == self._podcast_list
				self._podcast_list.SetFocus()
				self._on_podcast_selected(None)
				if not was_focused:
					ui.message(self._podcast_list.GetString(0))
			return
		if idx >= self._podcast_list.GetCount() - 1:
			# Translators: Spoken when cycling to the next podcast feed while already on the last one.
			ui.message(_("Already at last feed"))
			return
		new_idx = idx + 1
		self._podcast_list.SetSelection(new_idx)
		was_focused = wx.Window.FindFocus() == self._podcast_list
		self._podcast_list.SetFocus()
		self._on_podcast_selected(None)
		if not was_focused:
			ui.message(self._podcast_list.GetString(new_idx))

	def _show_podcast_result_context_menu(self):
		"""Context menu for the selected item in the podcast search results list."""
		idx = self._podcast_results.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		results = getattr(self, "_podcast_search_results", [])
		if idx >= len(results):
			return

		menu = wx.Menu()

		# Translators: Context-menu item; subscribes to the selected podcast search result.
		item_subscribe = menu.Append(wx.ID_ANY, _("&Subscribe"))
		self.Bind(wx.EVT_MENU, self._on_podcast_subscribe_from_results, item_subscribe)

		self.PopupMenu(menu, self._podcast_results.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _show_feed_context_menu(self):
		"""Context menu for the selected feed in the podcast subscriptions list."""
		idx = self._podcast_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		feeds = self._podcast_manager.get_feeds()
		if idx >= len(feeds):
			return
		feed = feeds[idx]

		menu = wx.Menu()

		# Translators: Context-menu item; re-fetches the selected feed for new episodes right now.
		item_refresh = menu.Append(wx.ID_ANY, _("&Refresh Feed"))
		self.Bind(wx.EVT_MENU, self._on_podcast_refresh, item_refresh)

		# Translators: Context-menu item; unsubscribes from the selected feed.
		item_remove = menu.Append(wx.ID_ANY, _("Re&move Feed"))
		self.Bind(wx.EVT_MENU, self._on_podcast_remove, item_remove)

		menu.AppendSeparator()

		# Translators: Context menu item - saves an audio profile (volume/effects/speed) that applies to every episode of this podcast
		item_save_profile = menu.Append(wx.ID_ANY, _("Save Audio Pr&ofile for This Podcast"))
		self.Bind(wx.EVT_MENU, self._on_save_feed_audio_profile, item_save_profile)

		# Translators: Context menu item - removes the saved audio profile from this podcast
		item_clear_profile = menu.Append(wx.ID_ANY, _("Clear Audio Prof&ile"))
		item_clear_profile.Enable(bool(feed.audio_profile))
		self.Bind(wx.EVT_MENU, self._on_clear_feed_audio_profile, item_clear_profile)

		menu.AppendSeparator()

		# Translators: Context-menu item; copies the feed's URL to the clipboard.
		item_copy_url = menu.Append(wx.ID_ANY, _("&Copy Feed URL"))
		self.Bind(wx.EVT_MENU, lambda e: self._copy_to_clipboard(feed.url), item_copy_url)

		self.PopupMenu(menu, self._podcast_list.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _play_prev_jukebox_track(self):
		"""Play the previous track (the previous item in the playlist)."""
		idx = self._jukebox_tracks_list.GetSelection()
		if idx == wx.NOT_FOUND or idx <= 0:
			# Translators: Spoken when trying to play the previous jukebox track while already on the first one.
			ui.message(_("Already at first track"))
			return
		self._jukebox_tracks_list.SetSelection(idx - 1)
		self._jukebox_tracks_list.SetFocus()
		self._on_jukebox_track_play(None)

	def _play_next_jukebox_track(self):
		"""Play the next track."""
		idx = self._jukebox_tracks_list.GetSelection()
		count = self._jukebox_tracks_list.GetCount()
		if idx == wx.NOT_FOUND:
			if count > 0:
				self._jukebox_tracks_list.SetSelection(0)
				self._jukebox_tracks_list.SetFocus()
				self._on_jukebox_track_play(None)
			return
		if idx >= count - 1:
			# Translators: Spoken when trying to play the next jukebox track while already on the last one.
			ui.message(_("Already at last track"))
			return
		self._jukebox_tracks_list.SetSelection(idx + 1)
		self._jukebox_tracks_list.SetFocus()
		self._on_jukebox_track_play(None)

	def _select_prev_jukebox_entry(self):
		"""Select the previous jukebox entry (file or folder)."""
		idx = self._jukebox_list.GetSelection()
		if idx == wx.NOT_FOUND or idx <= 0:
			# Translators: Spoken when cycling to the previous jukebox library entry while already on the first one.
			ui.message(_("Already at first item"))
			return
		new_idx = idx - 1
		self._jukebox_list.SetSelection(new_idx)
		was_focused = wx.Window.FindFocus() == self._jukebox_list
		self._jukebox_list.SetFocus()
		self._on_jukebox_entry_selected(None)
		if not was_focused:
			ui.message(self._jukebox_list.GetString(new_idx))

	def _select_next_jukebox_entry(self):
		"""Select the next jukebox entry."""
		idx = self._jukebox_list.GetSelection()
		count = self._jukebox_list.GetCount()
		if idx == wx.NOT_FOUND:
			if count > 0:
				self._jukebox_list.SetSelection(0)
				was_focused = wx.Window.FindFocus() == self._jukebox_list
				self._jukebox_list.SetFocus()
				self._on_jukebox_entry_selected(None)
				if not was_focused:
					ui.message(self._jukebox_list.GetString(0))
			return
		if idx >= count - 1:
			# Translators: Spoken when cycling to the next jukebox library entry while already on the last one.
			ui.message(_("Already at last item"))
			return
		new_idx = idx + 1
		self._jukebox_list.SetSelection(new_idx)
		was_focused = wx.Window.FindFocus() == self._jukebox_list
		self._jukebox_list.SetFocus()
		self._on_jukebox_entry_selected(None)
		if not was_focused:
			ui.message(self._jukebox_list.GetString(new_idx))

	def _show_episode_context_menu(self):
		"""Context menu for the selected episode in the episode list."""
		idx = self._episode_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		episodes = getattr(self, "_episode_filtered", None) or []
		if idx >= len(episodes):
			return
		episode = episodes[idx]

		menu = wx.Menu()

		# Translators: Context-menu item; plays the selected episode.
		item_play = menu.Append(wx.ID_ANY, _("&Play Episode"))
		self.Bind(wx.EVT_MENU, self._on_episode_play, item_play)

		# Translators: Context-menu item; downloads a permanent local copy of the selected episode.
		item_download = menu.Append(wx.ID_ANY, _("&Download Episode"))
		self.Bind(wx.EVT_MENU, self._on_episode_download, item_download)

		menu.AppendSeparator()

		# Audio profile commands, mirrored from the feed's own context menu
		# (_show_feed_context_menu()) so they're reachable without switching
		# back to the podcast list. These always act on the podcast-wide
		# profile (applies to every episode) - not a per-episode one, since
		# episodes don't have their own audio profiles.
		feed = self._get_selected_podcast_feed()

		# Translators: Context menu item - saves an audio profile (volume/effects/speed) that applies to every episode of this podcast
		item_save_profile = menu.Append(wx.ID_ANY, _("Save Audio Pr&ofile for This Podcast"))
		self.Bind(wx.EVT_MENU, self._on_save_feed_audio_profile, item_save_profile)

		# Translators: Context menu item - removes the saved audio profile from this podcast
		item_clear_profile = menu.Append(wx.ID_ANY, _("Clear Audio Prof&ile"))
		item_clear_profile.Enable(bool(feed and feed.audio_profile))
		self.Bind(wx.EVT_MENU, self._on_clear_feed_audio_profile, item_clear_profile)

		menu.AppendSeparator()

		# Translators: Context-menu item; copies the episode's direct audio URL to the clipboard.
		item_copy_url = menu.Append(wx.ID_ANY, _("&Copy Episode URL"))
		self.Bind(wx.EVT_MENU, lambda e: self._copy_to_clipboard(episode.url), item_copy_url)

		self.PopupMenu(menu, self._episode_list.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _copy_to_clipboard(self, text):
		if not text:
			return
		if wx.TheClipboard.Open():
			try:
				wx.TheClipboard.SetData(wx.TextDataObject(text))
			finally:
				wx.TheClipboard.Close()
			# Translators: Spoken after any "Copy ..." context-menu action succeeds (URL, path, etc.) - a single generic confirmation shared by all of them.
			ui.message(_("Copied to clipboard"))

	# ------------------------------------------------------------------ #
	# Audio Books Tab (unified GETEM + LibriVox library)
	# ------------------------------------------------------------------ #

	# Every _on_getem_*/_play_getem_*/etc. method below goes through these
	# two instead of hardcoding the `getem` module or `self._getem_library`,
	# which is what lets the same set of methods (names kept as `_getem_*`
	# for historical/git-blame continuity, even though they now serve
	# either source) drive GETEM or LibriVox interchangeably. getem.py and
	# librivox.py deliberately expose matching function names/signatures
	# (resolve_media, get_stream_url, download_chapter_to, download_target,
	# book_download_dir, download_book_chapter_target) and
	# GetemBook/LibrivoxBook share the same attributes and
	# to_dict()/to_library_dict()/from_dict() shape, so no source-specific
	# branching is needed anywhere except the search call itself
	# (search_getem vs search_librivox - see _on_getem_search()), since the
	# two APIs' search entry points genuinely differ (GETEM needs a login
	# session; LibriVox doesn't).
	#
	# There is no "Source" dropdown: the Library list and search results
	# are a single merged list drawn from both self._getem_library and
	# self._librivox_library, with each row's source shown only as a label
	# (see _audiobook_source_label_for()/_format_getem_result_label()).
	# Every book object stays a plain GetemBook or LibrivoxBook instance
	# either way, so which underlying module/library a given book belongs
	# to is always resolved from the book itself via isinstance() -
	# _audiobook_module_for()/_audiobook_library_for() below - rather than
	# from any "currently selected" state.
	def _audiobook_module_for(self, book):
		"""Which of getem/librivox/gutenberg_audiobooks produced *book* -
		each source's book class is distinct (see librivox.py's module
		docstring for why they're attribute-compatible but still separate
		classes), so this is a plain isinstance check."""
		if isinstance(book, librivox.LibrivoxBook):
			return librivox
		if isinstance(book, gutenberg_audiobooks.GutenbergAudiobook):
			return gutenberg_audiobooks
		return getem

	def _audiobook_library_for(self, book):
		"""Which of self._getem_library/self._librivox_library/
		self._gutenberg_library *book* belongs to - the library-side
		equivalent of _audiobook_module_for()."""
		if isinstance(book, librivox.LibrivoxBook):
			return self._librivox_library
		if isinstance(book, gutenberg_audiobooks.GutenbergAudiobook):
			return self._gutenberg_library
		return self._getem_library

	def _audiobook_source_label_for(self, book):
		if isinstance(book, librivox.LibrivoxBook):
			# Translators: Source-name label for a book from the LibriVox catalog, shown alongside the audio-book details.
			return _("LibriVox")
		if isinstance(book, gutenberg_audiobooks.GutenbergAudiobook):
			# Translators: Source-name label for a book from the Project Gutenberg Open Audiobook Collection.
			return _("Project Gutenberg")
		# Translators: Source-name label for a book from GETEM (Boğaziçi University audio e-library) - the fallback when the book is neither LibriVox nor Project Gutenberg.
		return _("GETEM")

	def _merged_library_books(self):
		"""Every saved audio book across GETEM, LibriVox, and Project
		Gutenberg, combined into one list and sorted by title so the
		Library list reads as one shelf rather than three concatenated
		ones."""
		books = (
			self._getem_library.get_books()
			+ self._librivox_library.get_books()
			+ self._gutenberg_library.get_books()
		)
		books.sort(key=lambda b: (b.title or "").casefold())
		return books

	def _audiobook_search_field_label(self):
		# Translators: Accessible name of the audio book search field - searches both GETEM and LibriVox at once
		return _("Search audio books by title, author, narrator, subject, or publisher. Press enter to search")

	def _build_audiobooks_tab(self):
		"""Audio book search and library tab. Search UI is modeled on the
		Podcasts tab above: a single search field, a results list that
		only appears once a search has actually been run, and adding an
		item to the library is done from the results list's context menu
		rather than a dedicated button - see _show_getem_result_context_menu().

		Both supported catalogs (GETEM and LibriVox) are searched
		together and shown in one merged results list and one merged
		Library list - see _merged_library_books()/_on_getem_search() -
		with each row's source shown only as a label
		(_audiobook_source_label_for()), rather than through a "Source"
		dropdown that would otherwise need switching back and forth.
		"""
		panel = self._getem_panel
		sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Search row ---
		search_sizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Label for the audio-book search field (searches GETEM/LibriVox/Project Gutenberg catalogs together).
		search_sizer.Add(wx.StaticText(panel, label=_("Search:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._getem_search = wx.TextCtrl(panel)
		self._getem_search.SetName(self._audiobook_search_field_label())
		search_sizer.Add(self._getem_search, 1, wx.EXPAND)
		sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 8)

		# --- Search results list ---
		# Hidden until a search is actually performed, same as the
		# Podcasts tab's search results - see _set_getem_results_visible().
		# Translators: Label above the audio-book search-results list.
		self._getem_results_label = wx.StaticText(panel, label=_("Search results:"))
		sizer.Add(self._getem_results_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._getem_results = wx.ListBox(panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the audio-book search-results list.
		self._getem_results.SetName(_("Audio book search results"))
		self._getem_results.SetMinSize((-1, 100))
		sizer.Add(self._getem_results, 0, wx.EXPAND | wx.ALL, 8)
		self._getem_search_sizer = sizer
		self._set_getem_results_visible(False)

		# --- Separator ---
		sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 4)

		# --- Library list ---
		# Translators: Label above the user's saved audio-book library list.
		sizer.Add(wx.StaticText(panel, label=_("My Library:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._getem_library_ctrl = wx.ListBox(panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the audio-book library list.
		self._getem_library_ctrl.SetName(_("Audio books library"))
		self._getem_library_ctrl.SetMinSize((-1, 120))
		sizer.Add(self._getem_library_ctrl, 1, wx.EXPAND | wx.ALL, 8)

		# --- Selected item details (read-only, reachable by Tab right
		# after either list) ---
		self._getem_details = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
		# Translators: Accessible name for the read-only audio-book details text field.
		self._getem_details.SetName(_("Audio book details"))
		self._getem_details.SetMinSize((-1, 80))
		sizer.Add(self._getem_details, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		panel.SetSizer(sizer)

		# --- Bind events ---
		self._getem_search.Bind(wx.EVT_KEY_DOWN, self._on_getem_search_key)
		self._getem_results.Bind(wx.EVT_LISTBOX, self._on_getem_result_selected)
		self._getem_results.Bind(wx.EVT_CHAR, self._on_list_char)
		self._getem_results.Bind(wx.EVT_KEY_DOWN, self._on_getem_results_key)
		self._getem_library_ctrl.Bind(wx.EVT_LISTBOX, self._on_getem_library_selected)
		self._getem_library_ctrl.Bind(wx.EVT_CHAR, self._on_list_char)
		self._getem_library_ctrl.Bind(wx.EVT_KEY_DOWN, self._on_getem_library_key)

		# _refresh_getem_library_list() is deliberately not called here:
		# _open_dialog() in __init__.py already calls it unconditionally
		# right after constructing the dialog (to also cover a background
		# auto-advanced GETEM chapter), so calling it again here just
		# duplicated that work on every first open. Tab-switch
		# (_apply_tab_side_effects, sel == 6) and focus_audiobooks() also
		# call it explicitly when needed.
		self._sync_getem_now_playing_from_player()

	def refresh_getem_libraries_from_disk(self):
		"""Reload both audio-book libraries from disk.

		self._getem_library/self._librivox_library are created once when
		this dialog is built and normally kept in memory for the dialog's
		whole lifetime - every mark_progress()/add_book()/etc. call goes
		through these same instances, so they always reflect the truth
		while the dialog is open and driving playback itself.

		The exception is while this dialog is closed/hidden: a playing
		GETEM/LibriVox chapter can keep auto-advancing on its own via
		GlobalPlugin._advance_getem_chapter_headless(), which has no
		dialog instance to reach into and so marks progress through its
		own, freshly-instantiated library object instead. That write
		lands correctly on disk but never reaches these in-memory copies,
		so a book's last_chapter_index here can go stale while the dialog
		is hidden - and _play_getem_book() would then silently resume an
		earlier part than was actually last played the next time the user
		reopens the dialog and plays that book from the library list
		(F3/F4's _getem_now_playing state doesn't have this problem - see
		_sync_getem_now_playing_from_player() - because it's rebuilt from
		the player's own live station dict, not from these library
		objects).

		Called from GlobalPlugin._open_dialog() every time the dialog is
		(re)shown, right alongside that same _sync_getem_now_playing_from_player()
		resync and for the same underlying reason."""
		self._getem_library = getem.GetemLibrary()
		self._librivox_library = librivox.LibrivoxLibrary()
		self._gutenberg_library = gutenberg_audiobooks.GutenbergLibrary()

	def _sync_getem_now_playing_from_player(self):
		"""If an audio book chapter (GETEM or LibriVox) is already playing
		by the time this tab is first built - e.g. it was resumed within
		this session, or (for GETEM specifically - see the note below)
		automatically on NVDA startup via GlobalPlugin._resume_last_station()/
		_rebuild_getem_resume_url() in playbackCoreMixin.py - then
		_getem_now_playing wouldn't otherwise get set until the user
		manually starts something from this tab, leaving F3/F4 book/chapter
		navigation (_play_prev/next_getem_book/chapter) with nothing to
		work from even though something is audibly playing. Reconstructs
		it from the player's own current station dict instead, checking
		both libraries since the dict alone (see LibrivoxBook.to_dict()/
		GetemBook.to_dict()) doesn't say which source a book came from.

		NOTE: _rebuild_getem_resume_url() in playbackCoreMixin.py only
		knows about GETEM's own config.conf keys today, so resuming a
		LibriVox book specifically across an NVDA *restart* needs that
		file updated too - this method already handles the LibriVox case
		correctly for anything resumed earlier in the *same* session."""
		current = self._player.get_current_station() or {}
		if current.get("media_kind") != "audiobook":
			return
		detail_url = current.get("getem_detail_url")
		if not detail_url:
			return
		book = self._getem_library.get_book_by_key(detail_url) or self._librivox_library.get_book_by_key(detail_url)
		if not book or not book.chapters:
			return
		try:
			chapter_index = int(current.get("getem_chapter_index", 0))
		except (TypeError, ValueError):
			chapter_index = 0
		if not (0 <= chapter_index < len(book.chapters)):
			chapter_index = 0
		self._getem_now_playing = (book, chapter_index)

	def _set_getem_results_visible(self, visible):
		"""Show or hide the search-results list (with its label) in the
		Audio Books tab. Hidden until a search is actually performed."""
		sizer = getattr(self, "_getem_search_sizer", None)
		widgets = (self._getem_results_label, self._getem_results)
		for widget in widgets:
			if sizer:
				sizer.Show(widget, visible)
			else:
				widget.Show(visible)
		try:
			if sizer:
				sizer.Layout()
			else:
				self._getem_panel.Layout()
		except Exception:
			pass

	def _format_getem_result_label(self, book):
		"""Listbox label for a GetemBook/LibrivoxBook: title, author, its
		format (the user-facing "type" of the source - human/computer
		narration, audio description, radio theatre, etc.), and which
		source it came from - shown here since the Library and search
		results lists are now merged across both sources (see
		_merged_library_books())."""
		parts = [book.title]
		if book.author:
			parts.append(book.author)
		label = " — ".join(parts)
		if book.format_label:
			label += f" ({book.format_label})"
		label += " — %s" % self._audiobook_source_label_for(book)
		return label

	def _format_getem_details(self, book):
		"""Build the text shown in the read-only "Audio book details" field
		for the given book (or "" if none is selected). The Source/Author/
		Narrator/Publisher/Type/part-count/description lines are built by
		the shared _format_audiobook_lines() - see its docstring - so this
		stays in sync with the same fields shown in the station-details
		dialog (trackInfoMixin._build_audiobook_details()) for whichever
		book/chapter is actually playing."""
		if book is None:
			return ""
		lines = [book.title]
		lines.extend(_format_audiobook_lines(
			source_label=self._audiobook_source_label_for(book),
			author=book.author,
			narrator=book.narrator,
			publisher=book.publisher,
			format_label=book.format_label,
			chapter_count=len(book.chapters),
			description=book.description,
			# LibriVox books never set these - getattr() with a
			# default keeps this working for both sources.
			original_title=getattr(book, "original_title", ""),
			director=getattr(book, "director", ""),
			release_year=getattr(book, "release_year", ""),
			imdb_rating=getattr(book, "imdb_rating", ""),
			actors=getattr(book, "actors", ""),
		))
		lines.append("")
		lines.append(book.detail_url)
		return "\n".join(lines)

	def _on_getem_search_key(self, event):
		if event.GetKeyCode() == wx.WXK_RETURN:
			self._on_getem_search(event)
		else:
			event.Skip()

	def _on_getem_search(self, event):
		query = self._getem_search.GetValue().strip()
		if not query:
			# Translators: Spoken when the search button/enter is used with an empty search box.
			ui.message(_("Please enter a search term."))
			return

		enabled_sources = _enabled_audiobook_sources()
		if not enabled_sources:
			# Translators: Spoken when the user tries to search but disabled every audio-book source (GETEM/LibriVox/Project Gutenberg) in Settings.
			ui.message(_(
				"No audio book sources are enabled. Enable at least one "
				"in FreeRadio settings."
			))
			return

		self._set_getem_results_visible(True)
		self._getem_search.Disable()

		self._getem_search_id = getattr(self, "_getem_search_id", 0) + 1
		search_id = self._getem_search_id

		# A pasted book link - e.g. an archive.org "details" URL for a
		# LibriVox recording or a Project Gutenberg Open Audiobook
		# Collection title, or a GETEM catalog page URL - is resolved
		# directly to that one book instead of being treated as a keyword
		# search, and fed through the same _on_getem_search_done() path as
		# an ordinary search result (as a one-item list), so "Add to
		# Library"/"Preview" on it work exactly the same way. See
		# librivox.looks_like_book_url()/get_book_by_url() and (once
		# added) their GETEM equivalents. Gated on enabled_sources the
		# same as the keyword-search path below, so disabling a source in
		# Settings also stops a pasted link for it from being resolved.
		#
		# LibriVox and Project Gutenberg links are both bare archive.org
		# "details" URLs, indistinguishable by shape alone - so when both
		# sources are enabled, gutenberg_audiobooks.get_book_by_url() is
		# tried first, since it actually checks the resolved item's
		# uploader before accepting it (see its docstring), and only
		# falls through to librivox.get_book_by_url() - which accepts any
		# archive.org details URL unconditionally - if that rejects it or
		# the source is disabled. This is the disambiguation
		# gutenberg_audiobooks.py's own module docstring says a caller
		# would need to do itself, done here rather than there since only
		# this tab has both sources enabled at once to disambiguate between.
		is_archive_org_url = librivox.looks_like_book_url(query)
		is_librivox_url = "librivox" in enabled_sources and is_archive_org_url
		is_gutenberg_url = "gutenberg" in enabled_sources and is_archive_org_url
		is_getem_url = (
			"getem" in enabled_sources
			and hasattr(getem, "looks_like_book_url")
			and getem.looks_like_book_url(query)
		)
		if is_librivox_url or is_gutenberg_url or is_getem_url:
			# Translators: Spoken while resolving a pasted book-detail URL directly to one book (rather than running a keyword search).
			ui.message(_("Loading..."))

			def _do_url_lookup():
				book, error = None, None
				if is_gutenberg_url:
					book, error = gutenberg_audiobooks.get_book_by_url(query)
				if not book and is_librivox_url:
					book, error = librivox.get_book_by_url(query)
				if not book and is_getem_url:
					book, error = getem.get_book_by_url(query)
				books = [book] if book else []
				wx.CallAfter(self._on_getem_search_done, books, error, search_id)

			threading.Thread(target=_do_url_lookup, daemon=True).start()
			return

		# Translators: Spoken while a keyword search across the enabled audio-book sources is in progress.
		ui.message(_("Searching..."))

		def _do_search():
			# search_getem()/search_librivox()/search_gutenberg_audiobooks()
			# are the one genuine source-specific call in this tab (see the
			# note near _audiobook_module_for() above) - GETEM's search
			# needs an authenticated session, the other two don't, so
			# they aren't unified under one function name. All enabled
			# sources are searched every time now that there's no
			# "Source" dropdown to pick just one - results are merged
			# into a single list, each row still tagged with its own
			# source via _format_getem_result_label(). Only a source the
			# user has checked in Settings (see
			# _enabled_audiobook_sources()) is searched at all.
			if "getem" in enabled_sources:
				getem_books, getem_error = getem.search_getem(query)
			else:
				getem_books, getem_error = [], None
			if "librivox" in enabled_sources:
				librivox_books, librivox_error = librivox.search_librivox(query)
			else:
				librivox_books, librivox_error = [], None
			if "gutenberg" in enabled_sources:
				gutenberg_books, gutenberg_error = gutenberg_audiobooks.search_gutenberg_audiobooks(query)
			else:
				gutenberg_books, gutenberg_error = [], None
			books = list(getem_books or []) + list(librivox_books or []) + list(gutenberg_books or [])
			# Only surface an error message if NONE of the sources
			# returned any results - a real result from one source is
			# shown even if another one genuinely failed, rather than
			# hiding a working result behind another source's error.
			error = None
			if not books:
				error = getem_error or librivox_error or gutenberg_error
			wx.CallAfter(self._on_getem_search_done, books, error, search_id)

		threading.Thread(target=_do_search, daemon=True).start()

	def _on_getem_search_done(self, books, error, search_id):
		if search_id != getattr(self, "_getem_search_id", None):
			return  # A newer search was started before this one finished.
		self._getem_search.Enable()
		self._getem_results.Clear()
		self._getem_search_results = books
		if error:
			ui.message(error)
			return
		if not books:
			# Translators: Spoken when an audio-book search returns no results.
			ui.message(_("No audio books found."))
			return
		for book in books:
			self._getem_results.Append(self._format_getem_result_label(book))
		# Translators: Spoken after an audio-book search finds results; %d is the count.
		ui.message(_("%d audio books found.") % len(books))
		self._getem_results.SetSelection(0)
		self._on_getem_result_selected(None)

	def _maybe_fetch_getem_extra_fields(self, book):
		"""Kicks off a background fetch of *book*'s GETEM detail page to
		fill in its "Sesli Betimleme"-only fields (original title/
		director/release year/IMDB rating/cast - see
		getem.fetch_audiobook_extra_fields()) and refresh the details box
		once it lands - so these show up as soon as a search result or
		library entry is selected, without requiring the book to be added
		to the library or played first (only that resolves
		getem.GetemBook.chapters, not these). No-ops for anything that
		isn't a getem.GetemBook (LibriVox/Gutenberg books never carry
		these fields) or that already has them filled in - see
		getem.fetch_audiobook_extra_fields()'s own no-op check, which
		this mirrors to avoid spinning up a thread for nothing."""
		if not isinstance(book, getem.GetemBook):
			return
		if any(getattr(book, attr, "") for attr in
				("original_title", "director", "release_year", "imdb_rating", "actors")):
			return

		self._getem_details_fetch_id = getattr(self, "_getem_details_fetch_id", 0) + 1
		fetch_id = self._getem_details_fetch_id

		def _worker():
			getem.fetch_audiobook_extra_fields(book)
			wx.CallAfter(_apply)

		def _apply():
			# Guards against a slow fetch for a book the user has since
			# navigated away from landing on top of whatever is now shown.
			if not self or fetch_id != self._getem_details_fetch_id:
				return
			self._getem_details.ChangeValue(self._format_getem_details(book))

		threading.Thread(target=_worker, daemon=True).start()

	def _on_getem_result_selected(self, event):
		idx = self._getem_results.GetSelection()
		results = getattr(self, "_getem_search_results", None) or []
		book = results[idx] if idx != wx.NOT_FOUND and idx < len(results) else None
		self._getem_details.ChangeValue(self._format_getem_details(book))
		self._maybe_fetch_getem_extra_fields(book)

	def _on_getem_add_to_library(self, event):
		"""Adds the selected search result to the library. Reached via the
		search results' context menu or Enter - there is no separate button."""
		idx = self._getem_results.GetSelection()
		results = getattr(self, "_getem_search_results", None) or []
		if idx == wx.NOT_FOUND or idx >= len(results):
			return
		book = results[idx]
		library = self._audiobook_library_for(book)
		if library.is_in_library(book):
			# Translators: Spoken when trying to add a search result that is already saved.
			ui.message(_("This audio book is already in your library."))
			return
		if library.add_book(book):
			# Translators: Spoken after successfully adding a book to the library; %s is the book title.
			ui.message(_("Added to library: %s") % book.title)
			self._refresh_getem_library_list()
		else:
			# Translators: Generic fallback spoken if adding the book to the library fails for an unspecified reason.
			ui.message(_("Could not add to library."))

	def _show_getem_result_context_menu(self):
		"""Context menu for the selected item in the search results list."""
		idx = self._getem_results.GetSelection()
		results = getattr(self, "_getem_search_results", None) or []
		if idx == wx.NOT_FOUND or idx >= len(results):
			return
		book = results[idx]

		menu = wx.Menu()
		# Translators: Context-menu item; subscribes/saves the selected search result to the audio-book library.
		item_add = menu.Append(wx.ID_ANY, _("&Add to Library"))
		self.Bind(wx.EVT_MENU, self._on_getem_add_to_library, item_add)

		menu.AppendSeparator()

		# Translators: Context-menu item label toggles between these two: 'Preview' plays a short sample of the selected search result before adding it, 'Stop Preview' appears while that sample is playing.
		label = _("&Stop Preview") if self._is_previewing_getem_book(book) else _("&Preview")
		item_preview = menu.Append(wx.ID_ANY, label)
		self.Bind(wx.EVT_MENU, self._on_getem_preview_toggle, item_preview)

		self.PopupMenu(menu, self._getem_results.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _is_previewing_getem_book(self, book):
		"""Whether *book* (from the search results list) is the audio book
		currently loaded in the player, regardless of whether it's playing
		or paused - the GETEM equivalent of _is_previewing() for podcast
		episodes, matched on getem_detail_url (see GetemBook.to_dict())
		rather than on url, since a book's stream URL changes per part."""
		if not book or not book.detail_url or not self._player.has_media():
			return False
		current = self._player.get_current_station() or {}
		return current.get("getem_detail_url") == book.detail_url

	def _on_getem_results_key(self, event):
		if event.GetKeyCode() == wx.WXK_SPACE:
			self._on_getem_preview_toggle(None)
			return
		event.Skip()

	def _on_getem_preview_toggle(self, event):
		"""Preview (play) the selected search result from its first part,
		or stop it if it's already the one being previewed. Reached via
		the search results' context menu or Space - mirrors
		_on_podcast_preview_toggle(). Doesn't add the book to the library;
		_play_getem_book()/_start_getem_chapter() only persist progress
		for books that are already in it (see GetemLibrary.mark_progress())."""
		idx = self._getem_results.GetSelection()
		results = getattr(self, "_getem_search_results", None) or []
		if idx == wx.NOT_FOUND or idx >= len(results):
			return
		book = results[idx]

		if self._is_previewing_getem_book(book):
			if self._plugin:
				wx.CallAfter(self._plugin._stop_from_dialog)
			return

		self._play_getem_book(book)

	def _refresh_getem_library_list(self):
		"""Populate the library listbox from the merged GETEM + LibriVox
		library (see _merged_library_books()), preserving whichever book is
		selected at the moment this runs (mirrors _refresh_podcast_list())."""
		prev_key = None
		idx = self._getem_library_ctrl.GetSelection()
		books_before = self._merged_library_books()
		if idx != wx.NOT_FOUND and idx < len(books_before):
			prev_key = books_before[idx].identity_key()

		self._getem_library_ctrl.Clear()
		books = self._merged_library_books()
		for book in books:
			label = self._format_getem_result_label(book)
			label = self._with_marked_suffix(label, book.identity_key() in self._getem_marked)
			self._getem_library_ctrl.Append(label)

		if not books:
			self._getem_details.ChangeValue("")
			return

		restore_idx = 0
		if prev_key:
			for i, book in enumerate(books):
				if book.identity_key() == prev_key:
					restore_idx = i
					break
		self._getem_library_ctrl.SetSelection(restore_idx)
		self._on_getem_library_selected(None)

	def _on_getem_library_selected(self, event):
		idx = self._getem_library_ctrl.GetSelection()
		books = self._merged_library_books()
		book = books[idx] if idx != wx.NOT_FOUND and idx < len(books) else None
		self._getem_details.ChangeValue(self._format_getem_details(book))
		self._maybe_fetch_getem_extra_fields(book)

	def _on_getem_library_key(self, event):
		# '.' (mark for bulk removal) is handled globally in
		# _on_char_hook(), same as the Favourites list's ','.
		key = event.GetKeyCode()
		if key == wx.WXK_DELETE:
			# Delete / Shift+Delete both remove the selected book from the
			# library — the keycode is the same either way. If one or more
			# books are marked, remove all of them at once instead.
			if self._getem_marked:
				self._on_getem_remove_selected(event)
			else:
				self._on_getem_remove_from_library(event)
			return
		if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			self._on_getem_play(None)
			return
		if key == wx.WXK_SPACE:
			# Space: pause whatever is currently playing; otherwise start
			# (or resume) the highlighted book - matches the Space handling
			# on the station lists (_on_list_key/_on_fav_list_key) and the
			# podcast episode list (_on_episode_key).
			if self._player.is_playing():
				self._player.pause()
				# Translators: Same "Paused" wording as elsewhere; spoken here when Space pauses playback from the audio-book library list.
				_notify(_("Paused"))
			else:
				self._on_getem_play(None)
			return
		event.Skip()

	def _toggle_getem_mark(self):
		"""Mark/unmark the focused audio book with '.' for the Remove
		Selected bulk-delete flow (Delete key or context menu). Updates
		the row's display text immediately so the marked state is
		visible/announced while simply arrowing through the list
		afterwards, not only at the moment of marking."""
		idx = self._getem_library_ctrl.GetSelection()
		books = self._merged_library_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		book = books[idx]
		key = book.identity_key()
		if key in self._getem_marked:
			self._getem_marked.discard(key)
			# Translators: Spoken after unmarking an audio book in the multi-select removal flow; %s is the book title.
			ui.message(_("Unmarked: %s") % book.title)
		else:
			self._getem_marked.add(key)
			# Translators: Spoken after marking an audio book in the multi-select removal flow; %s is the book title.
			ui.message(_("Marked: %s") % book.title)
		label = self._format_getem_result_label(book)
		self._getem_library_ctrl.SetString(idx, self._with_marked_suffix(label, key in self._getem_marked))
		self._getem_library_ctrl.SetSelection(idx)

	def _on_getem_remove_selected(self, event=None):
		"""Bulk-remove every audio book currently marked with '.', asking
		for confirmation once for the whole batch."""
		marked = self._getem_marked
		if not marked:
			return
		books = [b for b in self._merged_library_books() if b.identity_key() in marked]
		count = len(books)
		if count == 0:
			self._getem_marked.clear()
			return
		# Translators: Body of the bulk-remove confirmation dialog for audio books; %d is how many books are marked.
		message = ngettext(
			"Do you want to remove the %d marked book from the library?",
			"Do you want to remove the %d marked books from the library?",
			count,
		) % count
		# Translators: Title of the bulk-remove confirmation dialog for audio books.
		if not self._confirm_bulk_remove(count, _("Remove From Library"), message):
			return
		removed = 0
		for book in books:
			library = self._audiobook_library_for(book)
			module = self._audiobook_module_for(book)
			if library.remove_book(book):
				removed += 1
				if book.chapters and self._player:
					# See the matching note in
					# _on_getem_remove_from_library above.
					urls = [
						ch["url"] for ch in book.chapters if ch.get("url")
					]
					self._player.clear_podcast_positions(urls)
		self._getem_marked.clear()
		# Translators: Spoken after bulk-removing marked audio books from the library; %d is how many were removed.
		ui.message(ngettext("%d book removed", "%d books removed", removed) % removed)
		self._refresh_getem_library_list()
		count_left = self._getem_library_ctrl.GetCount()
		if count_left > 0:
			self._getem_library_ctrl.SetSelection(0)
			self._on_getem_library_selected(None)
			self._getem_library_ctrl.SetFocus()
		else:
			self._getem_search.SetFocus()

	def _on_getem_play(self, event):
		idx = self._getem_library_ctrl.GetSelection()
		books = self._merged_library_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		self._play_getem_book(books[idx])

	def _play_getem_book(self, book):
		"""Resolves (if needed) and starts playing *book*, resuming from
		whichever part it was last left off on (book.last_chapter_index -
		see getem.GetemLibrary.mark_progress()/librivox.LibrivoxLibrary
		.mark_progress()). Every part of a multi-part work is fed to the
		player as the same played item - see GetemBook.to_dict()/
		LibrivoxBook.to_dict() and _start_getem_chapter() - so it gets the
		same resume/seek/speed-change handling a podcast episode does,
		without a separate per-part row anywhere in the UI: the book is
		one source, not one row per part. Works against whichever source
		*book* actually came from - see _audiobook_module_for()."""
		if book.chapters:
			start_idx = min(max(book.last_chapter_index, 0), len(book.chapters) - 1)
			self._start_getem_chapter(book, start_idx)
			return

		# Translators: Spoken while resolving a book's chapter list before playing it for the first time; %s is the book title.
		ui.message(_("Loading: %s") % book.title)
		module = self._audiobook_module_for(book)

		def _do_resolve():
			resolved_book, error = module.resolve_media(book)
			wx.CallAfter(self._on_getem_media_resolved, resolved_book, error)

		threading.Thread(target=_do_resolve, daemon=True).start()

	def _on_getem_media_resolved(self, book, error):
		if error:
			ui.message(error)
			return
		library = self._audiobook_library_for(book)
		if library.is_in_library(book):
			# Persist the now-resolved chapter list so this work doesn't
			# need re-resolving (and, for GETEM, re-logging-in) the next
			# time it's played.
			library.save()
		start_idx = min(max(book.last_chapter_index, 0), len(book.chapters) - 1) if book.chapters else 0
		self._start_getem_chapter(book, start_idx)

	def _format_getem_now_playing_name(self, book, chapter):
		""""What's playing" label for a GETEM/LibriVox chapter -
		playbackCoreMixin._play_station() announces this and shows it in
		Ctrl+Win+I's station info, so it needs the book title, not just
		the chapter/part name: a bare label like "Part 3" (or a LibriVox
		chapter title with no book context at all) means nothing on its
		own. Avoids a duplicated "Title — Title" for a single-file GETEM
		work, where getem._label_chapters() already sets the chapter's
		own title to the book's title."""
		if chapter["title"] and chapter["title"] != book.title:
			return "%s — %s" % (book.title, chapter["title"])
		return book.title

	def _start_getem_chapter(self, book, chapter_index):
		"""Plays the given part. For GETEM, this points the player at the
		local streaming proxy (see getem.get_stream_url()) rather than
		downloading the whole chapter first, since a remote GETEM URL only
		works with our Python session's login cookie, which the audio
		backend (BASS, in its own subprocess) has no way to send when it
		opens a URL on its own - the proxy is what supplies that cookie on
		its behalf. LibriVox needs no such proxy (its chapter URLs are
		already public - see librivox.get_stream_url()), but the call is
		made through the same module.get_stream_url() either way so this
		method doesn't need to know which source it's dealing with."""
		if chapter_index < 0 or chapter_index >= len(book.chapters):
			return
		library = self._audiobook_library_for(book)
		module = self._audiobook_module_for(book)
		self._getem_now_playing = (book, chapter_index)
		library.mark_progress(book, chapter_index)
		chapter = book.chapters[chapter_index]

		# Translators: Spoken when starting a specific GETEM chapter/part; %s is the chapter title.
		ui.message(_("Loading: %s") % chapter["title"])

		stream_url = module.get_stream_url(chapter["url"], referer=book.detail_url)
		station_dict = book.to_dict()
		# Apply the book-wide audio profile (volume/effects/EQ and,
		# optionally, playback speed) if one was saved - see
		# _on_save_getem_audio_profile() and playbackCoreMixin._play_station().
		if book.audio_profile:
			station_dict["station_audio"] = book.audio_profile
		# The book title is included here (not just the chapter/part name)
		# since this "name" is what playbackCoreMixin._play_station()
		# announces as "what's playing" and saves as
		# config.conf["freeradio"]["last_station_name"] - a bare chapter
		# label like "Part 3" (or, for a single-file GETEM work,
		# getem._label_chapters() already sets chapter["title"] to the
		# book's own title, in which case there's nothing to add here)
		# means nothing on its own without which book it belongs to.
		station_dict["name"] = self._format_getem_now_playing_name(book, chapter)
		station_dict["url"] = stream_url
		station_dict["url_resolved"] = stream_url
		# Carried through to config.conf["freeradio"]["last_station_getem_chapter_index"]
		# by playbackCoreMixin._play_station() - lets a "resume last
		# station" on the next NVDA startup know which part to rebuild a
		# fresh proxy URL for (see GlobalPlugin._rebuild_getem_resume_url()),
		# since the proxy URL saved this session won't still be valid then.
		# NOTE: that rebuild path is GETEM-specific today (see
		# _sync_getem_now_playing_from_player() above) - restart-resume for
		# a LibriVox book needs playbackCoreMixin.py updated too, though a
		# LibriVox chapter URL being a plain public link means it may not
		# even need a "rebuild" step once that's done.
		# Key the resume-position store on the chapter's own stable
		# upstream URL, not the session-random local proxy URL that
		# station_dict["url"] carries - see RadioPlayer._podcast_position_key()
		# for why.
		station_dict["podcast_resume_key"] = chapter["url"]
		station_dict["getem_chapter_index"] = chapter_index
		# The chapter/part title itself, separate from station_dict["name"]
		# (which is prefixed with the book title for "what's playing"
		# announcements - see _format_getem_now_playing_name() above).
		# trackInfoMixin._build_station_details() shows this as its own
		# "Chapter" row for audiobooks.
		station_dict["audiobook_chapter_title"] = chapter.get("title", "")
		self._play_callback(station_dict, [station_dict], 0, announce=True)

	def _getem_current_book_index(self, books):
		"""Index (within *books*) of whichever audio book is currently
		loaded/playing, falling back to the library list's own selection
		if nothing is playing yet - used by _play_prev_getem_book()/
		_play_next_getem_book()."""
		playing = getattr(self, "_getem_now_playing", None)
		if playing:
			key = playing[0].identity_key()
			for i, b in enumerate(books):
				if b.identity_key() == key:
					return i
		return self._getem_library_ctrl.GetSelection()

	def _play_prev_getem_book(self):
		"""Plays the previous audio book in the library, resuming wherever
		it was last left off - the book-level equivalent of
		_play_prev_getem_chapter(), and the primary F3 action on this tab
		since a book (not a part) is the source the listener thinks in
		terms of - see GetemBook.last_chapter_index. Operates on whichever
		source *book* actually came from - see _merged_library_books()."""
		books = self._merged_library_books()
		if not books:
			# Translators: Spoken when F3 (previous book) is pressed with no books in the audio-book library.
			ui.message(_("Library is empty"))
			return
		idx = self._getem_current_book_index(books)
		if idx <= 0:
			# Translators: Spoken when F3 (previous book) is pressed while already on the first book.
			ui.message(_("Already at first book"))
			return
		new_idx = idx - 1
		self._getem_library_ctrl.SetSelection(new_idx)
		self._getem_library_ctrl.SetFocus()
		self._on_getem_library_selected(None)
		self._play_getem_book(books[new_idx])

	def _play_next_getem_book(self):
		"""Plays the next audio book in the library, resuming wherever it
		was last left off - the book-level equivalent of
		_play_next_getem_chapter(), and the primary F4 action on this tab.
		Operates on whichever source is currently selected - see
		_merged_library_books()."""
		books = self._merged_library_books()
		if not books:
			# Translators: Spoken when F4 (next book) is pressed with no books in the audio-book library.
			ui.message(_("Library is empty"))
			return
		idx = self._getem_current_book_index(books)
		if idx >= len(books) - 1:
			# Translators: Spoken when F4 (next book) is pressed while already on the last book.
			ui.message(_("Already at last book"))
			return
		new_idx = idx + 1
		self._getem_library_ctrl.SetSelection(new_idx)
		self._getem_library_ctrl.SetFocus()
		self._on_getem_library_selected(None)
		self._play_getem_book(books[new_idx])

	def _focus_getem_library_row(self, book):
		"""Move selection and focus in the library list to *book*'s row —
		there is no separate per-part/chapter widget, so this is the
		"related item" F3/F4/Shift+F3/Shift+F4 move focus to on this tab
		when only the chapter (not the book) changed."""
		books = self._merged_library_books()
		try:
			row = next(i for i, b in enumerate(books) if b.identity_key() == book.identity_key())
		except StopIteration:
			return
		self._getem_library_ctrl.SetSelection(row)
		self._getem_library_ctrl.SetFocus()
		self._on_getem_library_selected(None)

	def _play_prev_getem_chapter(self):
		"""Plays the previous part of whichever audio book is currently
		loaded - the equivalent of _play_prev_episode() on the Podcasts tab."""
		playing = getattr(self, "_getem_now_playing", None)
		if not playing:
			return
		book, idx = playing
		if idx <= 0:
			# Translators: Spoken when Shift+F3 (previous part) is pressed while already on the first part of a book.
			ui.message(_("Already at first part"))
			return
		self._focus_getem_library_row(book)
		self._start_getem_chapter(book, idx - 1)

	def _play_next_getem_chapter(self, auto=False):
		"""Plays the next part of whichever audio book is currently loaded.

		*auto* is True when called from _on_playback_finished() right after
		a part played to the end on its own, rather than from a user key
		press: in that case, running off the end of the book is the normal,
		expected outcome (not a mistake to report as "already at last
		part"), so a softer "book finished" message is given instead, and
		focus is left where it is since the user didn't ask for this."""
		playing = getattr(self, "_getem_now_playing", None)
		if not playing:
			return
		book, idx = playing
		if idx >= len(book.chapters) - 1:
			if auto:
				# Translators: Spoken when Shift+F4 (next part) is pressed on the last part of a book, meaning the whole book is now finished; %s is the book title.
				ui.message(_("Finished: %s") % book.title)
			else:
				# Translators: Spoken when Shift+F4 (next part) is pressed and there is no next part at all (single-part work).
				ui.message(_("Already at last part"))
			return
		if not auto:
			self._focus_getem_library_row(book)
		self._start_getem_chapter(book, idx + 1)

	def _on_playback_finished(self, station):
		"""Called (via radioPlayer.RadioPlayer.on_podcast_finished, wired up
		alongside on_podcast_progress_saved/on_device_lost) when whatever
		was playing reached its end on its own - as opposed to being paused
		or stopped by the user. For a GETEM audio book part, or a track
		played as part of a jukebox folder sequence (see
		_on_jukebox_entry_play()), this is the cue to automatically move on
		to the next part/track; regular podcast episodes and individually-
		played jukebox tracks are left as-is (the user only asked for
		auto-advance on audio books and jukebox folders) and are still
		advanced manually.

		Only called while this dialog is open and shown - see
		GlobalPlugin._on_podcast_finished_ui() in __init__.py, which calls
		playbackCoreMixin._advance_jukebox_folder_headless() instead
		whenever it isn't, so a folder sequence keeps advancing even after
		the window is closed. Both read the same
		"jukebox_folder_path"/"jukebox_track_index" station-dict fields, so
		which one handled the previous track doesn't matter to either."""
		if not station:
			return
		media_kind = station.get("media_kind")
		if media_kind == "audiobook":
			playing = getattr(self, "_getem_now_playing", None)
			if not playing:
				return
			book, idx = playing
			# Make sure the finished item still belongs to the book we
			# think is loaded - e.g. the user could have already skipped
			# away from it by hand right as it ended.
			if book.detail_url != station.get("getem_detail_url"):
				return
			self._play_next_getem_chapter(auto=True)
			return
		if media_kind == "jukebox":
			folder_path = station.get("jukebox_folder_path")
			if not folder_path:
				# A single file, or a track played directly from the
				# tracks list rather than through a folder sequence -
				# nothing to advance to.
				return
			try:
				index = int(station.get("jukebox_track_index", -1))
			except (TypeError, ValueError):
				return
			entry = self._jukebox_manager.get_folder_entry(folder_path)
			if not entry:
				return
			tracks = entry.tracks()
			next_index = index + 1
			if next_index >= len(tracks):
				# Translators: Spoken when a jukebox folder finishes playing all its tracks; %s is the folder/entry title.
				ui.message(_("Finished: %s") % entry.title)
				return
			self._play_jukebox_folder_track(entry, tracks, next_index)
			self.sync_jukebox_track_selection(folder_path, next_index)

	def sync_jukebox_track_selection(self, folder_path, index):
		"""Update the tracks list's selection to *index*, but only if the
		jukebox entries list is currently showing *folder_path*'s tracks -
		i.e. the folder being advanced/skipped is the one the user is
		actually looking at right now. A no-op otherwise (some other entry
		is selected), so a folder auto-advancing or being Ctrl+Win+J/K-
		skipped never disturbs an unrelated view. Never moves keyboard
		focus - see _on_jukebox_entry_play(). Called from
		_on_playback_finished() above for the natural-finish case, and
		from playbackCoreMixin._advance_jukebox_folder_headless() (via
		GlobalPlugin's self._dialog) for the Ctrl+Win+J/K track-boundary
		case, so both ways a folder can move to a different track keep the
		list in sync."""
		entry = self._get_selected_jukebox_entry()
		if not entry or entry.kind != "folder" or entry.path != folder_path:
			return
		if 0 <= index < self._jukebox_tracks_list.GetCount():
			self._jukebox_tracks_list.SetSelection(index)

	def _show_getem_library_context_menu(self):
		"""Context menu for the selected item in the library list: play,
		copy the URL, save/clear its audio profile, or remove from the
		library. Operates on whichever source *book* actually came from -
		see _audiobook_library_for()/_audiobook_module_for()."""
		idx = self._getem_library_ctrl.GetSelection()
		books = self._merged_library_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		book = books[idx]

		menu = wx.Menu()

		# Translators: Context-menu item; plays the selected audio-book/chapter from the library.
		item_play = menu.Append(wx.ID_ANY, _("&Play Media"))
		self.Bind(wx.EVT_MENU, self._on_getem_play, item_play)

		menu.AppendSeparator()

		# Translators: Context-menu item; downloads a permanent local copy of the selected book/chapter.
		item_download = menu.Append(wx.ID_ANY, _("&Download Book"))
		self.Bind(wx.EVT_MENU, lambda e: self._download_getem_book(book), item_download)

		menu.AppendSeparator()

		# Translators: Context-menu item; copies the book's detail-page URL to the clipboard.
		item_copy_url = menu.Append(wx.ID_ANY, _("&Copy the URL"))
		self.Bind(wx.EVT_MENU, lambda e: self._copy_to_clipboard(book.detail_url), item_copy_url)

		menu.AppendSeparator()

		# Translators: Context menu item - saves an audio profile (volume/effects/speed) that applies to every part/chapter of this audio book
		item_save_profile = menu.Append(wx.ID_ANY, _("Save Audio Pr&ofile for This Book"))
		self.Bind(wx.EVT_MENU, self._on_save_getem_audio_profile, item_save_profile)

		# Translators: Context menu item - removes the saved audio profile from this audio book
		item_clear_profile = menu.Append(wx.ID_ANY, _("Clear Audio Prof&ile"))
		item_clear_profile.Enable(bool(book.audio_profile))
		self.Bind(wx.EVT_MENU, self._on_clear_getem_audio_profile, item_clear_profile)

		menu.AppendSeparator()

		# Translators: Context-menu item; removes the selected book from the saved library.
		item_remove = menu.Append(wx.ID_ANY, _("&Remove from the Library"))
		self.Bind(wx.EVT_MENU, self._on_getem_remove_from_library, item_remove)

		# Translators: Context-menu item; bulk-removes every audio book marked with '.', asking for confirmation once for the whole batch.
		item_remove_selected = menu.Append(wx.ID_ANY, _("Remove &Selected"))
		item_remove_selected.Enable(bool(self._getem_marked))
		self.Bind(wx.EVT_MENU, self._on_getem_remove_selected, item_remove_selected)

		self.PopupMenu(menu, self._getem_library_ctrl.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _on_save_getem_audio_profile(self, event):
		"""Save an audio profile (volume/effects/EQ, and optionally
		playback speed) that applies to every part/chapter of the selected
		audio book - see playbackCoreMixin._play_station() and
		_start_getem_chapter(). Operates on whichever source *book*
		actually came from - see _audiobook_library_for()."""
		idx = self._getem_library_ctrl.GetSelection()
		books = self._merged_library_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		book = books[idx]
		library = self._audiobook_library_for(book)
		profile = self._prompt_and_build_audio_profile(book.audio_profile, allow_speed=True)
		if profile is None:
			return
		book.audio_profile = profile
		library.save()
		# Translators: Spoken after saving an audio profile that applies to every part of a GETEM audio book; %(book)s is the book title.
		ui.message(_("Audio profile saved for %(book)s") % {"book": book.title})

	def _on_clear_getem_audio_profile(self, event):
		"""Remove the saved audio profile from the selected audio book."""
		idx = self._getem_library_ctrl.GetSelection()
		books = self._merged_library_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		book = books[idx]
		library = self._audiobook_library_for(book)
		if not book.audio_profile:
			return
		book.audio_profile = None
		library.save()
		# Translators: Spoken after clearing a book's saved audio profile; %(book)s is the book title.
		ui.message(_("Audio profile cleared for %(book)s") % {"book": book.title})

	def _on_getem_remove_from_library(self, event):
		idx = self._getem_library_ctrl.GetSelection()
		books = self._merged_library_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		book = books[idx]
		library = self._audiobook_library_for(book)
		module = self._audiobook_module_for(book)
		if library.remove_book(book):
			self._getem_marked.discard(book.identity_key())
			# The book's own audio profile is discarded automatically along
			# with the rest of the book object above. Its per-chapter
			# resume positions live separately, in RadioPlayer's own store
			# (keyed by each chapter's stream URL - see
			# getem.get_stream_url()/librivox.get_stream_url()), and are
			# cleaned up here so they don't linger for a book the user can
			# no longer see or resume.
			if book.chapters and self._player:
				# The resume store is keyed on each chapter's real URL
				# (see _start_getem_chapter's "podcast_resume_key"
				# handling and RadioPlayer._podcast_position_key()), so
				# that - not the session-random proxy URL - is what has
				# to be cleared here.
				urls = [
					ch["url"] for ch in book.chapters if ch.get("url")
				]
				self._player.clear_podcast_positions(urls)
			# Translators: Spoken after removing a book from the audio-book library; %s is the book title.
			ui.message(_("Removed from library: %s") % book.title)
			self._refresh_getem_library_list()
			# After removal, move focus to the next book (or the new last
			# one if the removed book was at the end); if the library is
			# now empty, move focus to the search box instead - mirrors
			# _on_jukebox_remove_entry()'s post-deletion focus handling.
			count = self._getem_library_ctrl.GetCount()
			if count > 0:
				new_idx = min(idx, count - 1)
				self._getem_library_ctrl.SetSelection(new_idx)
				self._on_getem_library_selected(None)
				self._getem_library_ctrl.SetFocus()
			else:
				self._getem_search.SetFocus()

	def download_getem_book_by_detail_url(self, detail_url):
		"""Downloads every part of the audio book (GETEM or LibriVox)
		identified by *detail_url* into its own folder under the recordings
		directory - reached from GlobalPlugin._download_current_getem_book()
		in __init__.py, the Ctrl+Win+V action while one of its parts is
		playing (see script_addToFavorites()). Looks first at whichever
		book is currently loaded (self._getem_now_playing already has its
		resolved chapter list), then falls back to either library, so this
		works whether or not the currently-playing book was ever added to
		one."""
		playing = getattr(self, "_getem_now_playing", None)
		book = playing[0] if playing and playing[0].detail_url == detail_url else None
		if book is None:
			book = self._getem_library.get_book_by_key(detail_url) or self._librivox_library.get_book_by_key(detail_url)
		if book is None:
			# Translators: Spoken when a pasted book-detail link can't be resolved to a real book.
			ui.message(_("Could not find this audio book."))
			return
		self._download_getem_book(book)

	def _download_getem_book(self, book):
		"""Saves a permanent, user-visible copy of every part of *book* into
		its own folder named after the book (see getem.book_download_dir()/
		librivox.book_download_dir()) - the "Download Book" library
		context-menu action and its Ctrl+Win+V equivalent. Distinct from a
		single-part download: resolves the full chapter list first if it
		isn't already known."""
		if book.chapters:
			self._start_getem_book_download(book)
			return

		# Translators: Same message as _play_getem_book, spoken here while resolving a book's chapter list before downloading it.
		ui.message(_("Loading: %s") % book.title)
		module = self._audiobook_module_for(book)

		def _do_resolve():
			resolved_book, error = module.resolve_media(book)
			wx.CallAfter(self._on_getem_book_download_resolve_done, resolved_book, error)

		threading.Thread(target=_do_resolve, daemon=True).start()

	def _on_getem_book_download_resolve_done(self, book, error):
		if error:
			ui.message(error)
			return
		library = self._audiobook_library_for(book)
		if library.is_in_library(book):
			library.save()
		self._start_getem_book_download(book)

	def _start_getem_book_download(self, book):
		if not book.chapters:
			# Translators: Spoken when trying to download a book whose chapter/part list resolved to nothing playable.
			ui.message(_("No audio parts found for this book."))
			return

		# Guard against firing the same book's download twice in a row
		# (e.g. Ctrl+Win+V pressed twice while it's already under way) -
		# there's no per-part row in the UI to disable like the podcast
		# episode list's download button does.
		key = book.identity_key()
		if getattr(self, "_getem_book_download_active", None) == key:
			# Translators: Spoken when trying to start a download for a book that is already downloading; %s is the book title.
			ui.message(_("Already downloading: %s") % book.title)
			return
		self._getem_book_download_active = key

		# Translators: Spoken when a book download starts; %s is the book title.
		ui.message(_("Downloading book: %s") % book.title)
		module = self._audiobook_module_for(book)

		def _do_download():
			out_dir = module.book_download_dir(book)
			try:
				os.makedirs(out_dir, exist_ok=True)
			except Exception as e:
				wx.CallAfter(self._on_getem_book_download_done, book, 0, len(book.chapters), str(e))
				return

			saved = 0
			last_error = None
			for i, chapter in enumerate(book.chapters):
				out_path = module.download_book_chapter_target(book, chapter, i)
				if os.path.exists(out_path):
					saved += 1
					continue
				try:
					module.download_chapter_to(chapter["url"], out_path, referer=book.detail_url)
					saved += 1
				except FileExistsError:
					saved += 1
				except Exception as e:
					last_error = str(e)
			wx.CallAfter(self._on_getem_book_download_done, book, saved, len(book.chapters), last_error)

		threading.Thread(target=_do_download, daemon=True).start()

	def _on_getem_book_download_done(self, book, saved, total, error):
		if getattr(self, "_getem_book_download_active", None) == book.identity_key():
			self._getem_book_download_active = None
		if saved >= total:
			# Translators: Spoken when every part of a book downloaded successfully; %s is the book title.
			ui.message(_("Download complete: %s") % book.title)
		elif saved > 0:
			# Translators: Spoken when a book download partially fails; %(saved)d is the number of parts saved, %(total)d the total number of parts, %(title)s the book title, %(error)s the error from the last failed part.
			ui.message(_("Downloaded %(saved)d of %(total)d parts of %(title)s. Last error: %(error)s") % {
				"saved": saved,
				"total": total,
				"title": book.title,
				"error": error,
			})
		else:
			# Translators: Spoken when a book download fails entirely (zero parts saved); %s is the error message, or the book title if no specific error was captured.
			ui.message(_("Download failed: %s") % (error or book.title))

	# ------------------------------------------------------------------
	# Jukebox tab
	# ------------------------------------------------------------------

	def _build_jukebox_tab(self):
		"""Local jukebox tab: an on-demand filename search across all
		locally attached drives, plus a manually curated library of
		individually added audio files and folders. Modeled on the
		Podcast tab's shape (search/results above a separator, the
		persisted list below) so the two tabs feel consistent - see
		_build_podcast_tab()."""
		panel = self._jukebox_panel
		sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Disk search row ---
		search_sizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Label for the jukebox device-search field.
		search_sizer.Add(wx.StaticText(panel, label=_("Search on devices:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._jukebox_search = wx.TextCtrl(panel)
		# Translators: Accessible name/hint for the jukebox device-search field: searches local audio files by filename.
		self._jukebox_search.SetName(_("Search audio files on your computer by filename. Press enter to search"))
		search_sizer.Add(self._jukebox_search, 1, wx.EXPAND)
		sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 8)

		# --- Search results list ---
		# Hidden until a search is actually performed - see
		# _set_jukebox_results_visible(), mirroring
		# _set_podcast_results_visible()'s reasoning exactly.
		# Translators: Label above the list of audio files found by the device search.
		self._jukebox_results_label = wx.StaticText(panel, label=_("Search results:"))
		sizer.Add(self._jukebox_results_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._jukebox_search_results = wx.ListBox(panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the device-search results list.
		self._jukebox_search_results.SetName(_("Audio files found on your devices"))
		self._jukebox_search_results.SetMinSize((-1, 100))
		sizer.Add(self._jukebox_search_results, 0, wx.EXPAND | wx.ALL, 8)
		self._jukebox_search_sizer = sizer
		self._set_jukebox_results_visible(False)

		# --- Separator ---
		sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 4)

		# --- Jukebox entries (manually added files/folders) ---
		# Translators: Label above the list of files/folders already added to the jukebox library.
		sizer.Add(wx.StaticText(panel, label=_("Jukebox:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._jukebox_list = wx.ListBox(panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the jukebox library list.
		self._jukebox_list.SetName(_("Files and folders in your jukebox"))
		self._jukebox_list.SetMinSize((-1, 100))
		sizer.Add(self._jukebox_list, 0, wx.EXPAND | wx.ALL, 8)

		# --- Tracks in the selected entry (podcast-episode-style side
		# list) - for a "file" entry this is just that one file; for a
		# "folder" entry it's every audio file found inside it. See
		# jukebox.JukeboxEntry.tracks(). ---
		# Translators: Label above the list of tracks contained in the selected jukebox entry (a folder's individual audio files).
		sizer.Add(wx.StaticText(panel, label=_("Tracks:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._jukebox_tracks_list = wx.ListBox(panel, style=wx.LB_SINGLE)
		# Translators: Accessible name for the jukebox tracks list.
		self._jukebox_tracks_list.SetName(_("Tracks in the selected jukebox item"))
		self._jukebox_tracks_list.SetMinSize((-1, 120))
		sizer.Add(self._jukebox_tracks_list, 1, wx.EXPAND | wx.ALL, 8)

		add_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Button label; adds a single audio file (via a file picker) to the jukebox library.
		self._jukebox_add_file_btn = wx.Button(panel, label=_("Add &File..."))
		# Translators: Button label; adds a whole folder (via a folder picker) to the jukebox library.
		self._jukebox_add_folder_btn = wx.Button(panel, label=_("Add F&older..."))
		# Translators: Button label; removes the selected file/folder from the jukebox library.
		self._jukebox_remove_btn = wx.Button(panel, label=_("&Remove"))
		self._jukebox_remove_btn.Enable(False)
		for btn in (self._jukebox_add_file_btn, self._jukebox_add_folder_btn, self._jukebox_remove_btn):
			add_btn_sizer.Add(btn, 0, wx.RIGHT, 8)
		sizer.Add(add_btn_sizer, 0, wx.LEFT | wx.BOTTOM, 8)



		panel.SetSizer(sizer)

		# --- Bind events ---
		self._jukebox_search.Bind(wx.EVT_KEY_DOWN, self._on_jukebox_search_key)
		self._jukebox_search_results.Bind(wx.EVT_KEY_DOWN, self._on_jukebox_search_results_key)
		self._jukebox_list.Bind(wx.EVT_LISTBOX, self._on_jukebox_entry_selected)
		self._jukebox_list.Bind(wx.EVT_CHAR, self._on_list_char)
		self._jukebox_search_results.Bind(wx.EVT_CHAR, self._on_list_char)
		self._jukebox_tracks_list.Bind(wx.EVT_CHAR, self._on_list_char)
		self._jukebox_list.Bind(wx.EVT_KEY_DOWN, self._on_jukebox_list_key)
		self._jukebox_tracks_list.Bind(wx.EVT_KEY_DOWN, self._on_jukebox_tracks_key)
		self._jukebox_add_file_btn.Bind(wx.EVT_BUTTON, self._on_jukebox_add_file)
		self._jukebox_add_folder_btn.Bind(wx.EVT_BUTTON, self._on_jukebox_add_folder)
		self._jukebox_remove_btn.Bind(wx.EVT_BUTTON, self._on_jukebox_remove_entry)

		# Remember whichever control in this tab last had focus, so
		# focus_jukebox() can restore it on the next open instead of always
		# jumping to the search box - see _on_jukebox_child_focus().
		self._jukebox_last_focused = None
		panel.Bind(wx.EVT_CHILD_FOCUS, self._on_jukebox_child_focus)

		# Deferred: populated lazily the first time this tab becomes active,
		# either via tab-switch (_apply_tab_side_effects, sel == 7) or via
		# focus_jukebox() when the dialog is opened straight to this tab -
		# not eagerly at dialog construction time. This matters most here,
		# since _refresh_jukebox_list() ends up calling entry.tracks() on
		# the selected entry, which for a folder entry can mean scanning the
		# whole folder on disk.

	def _on_jukebox_child_focus(self, event):
		"""Track whichever control inside the Jukebox tab last had focus,
		so focus_jukebox() can restore it on the next open."""
		self._jukebox_last_focused = event.GetWindow()
		event.Skip()

	def _set_jukebox_results_visible(self, visible):
		"""Show or hide the device-search results list (with its label) in
		the Jukebox tab - mirrors _set_podcast_results_visible()."""
		sizer = getattr(self, "_jukebox_search_sizer", None)
		widgets = (self._jukebox_results_label, self._jukebox_search_results)
		for widget in widgets:
			if sizer:
				sizer.Show(widget, visible)
			else:
				widget.Show(visible)
		try:
			if sizer:
				sizer.Layout()
			else:
				self._jukebox_panel.Layout()
		except Exception:
			pass

	def _on_jukebox_search_key(self, event):
		if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			self._on_jukebox_search(event)
		else:
			event.Skip()

	def _on_jukebox_search(self, event):
		"""Search every locally attached drive for audio files whose
		filename contains the typed text - see
		jukebox.search_disk_for_audio(). Network (mapped/UNC) drives are
		included only if the "Include network drives when searching the
		jukebox" setting is on (off by default - see
		jukebox._list_drive_roots()'s include_network parameter). Runs on
		a background thread; a fresh search cancels whichever one is
		still in flight via self._jukebox_search_cancel, and
		self._jukebox_search_seq guards against a superseded search's
		results overwriting a newer one."""
		query = self._jukebox_search.GetValue().strip()
		if not query:
			# Translators: Spoken when the jukebox device-search is used with an empty search box.
			ui.message(_("Please enter a search term."))
			return

		if self._jukebox_search_cancel is not None:
			self._jukebox_search_cancel.set()
		cancel_event = threading.Event()
		self._jukebox_search_cancel = cancel_event
		self._jukebox_search_seq += 1
		seq = self._jukebox_search_seq

		self._jukebox_results = []
		self._set_jukebox_results_visible(True)
		self._jukebox_search_results.Clear()
		# Translators: Placeholder row shown in the results list while a device search is in progress.
		self._jukebox_search_results.Append(_("Searching..."))
		# Translators: Spoken when a jukebox device search starts; %s is the search text.
		ui.message(_("Searching devices for \"%s\"...") % query)

		include_network = config.conf["freeradio"].get("jukebox_search_network_drives", False)

		def _do_search():
			results = jukebox.search_disk_for_audio(
				query, cancel_event=cancel_event, include_network=include_network,
			)
			wx.CallAfter(self._on_jukebox_search_done, results, seq)

		threading.Thread(target=_do_search, daemon=True).start()

	def _on_jukebox_search_done(self, results, seq):
		if not self or seq != self._jukebox_search_seq:
			# A newer search has since been started - discard this reply.
			return
		self._jukebox_search_results.Clear()
		self._jukebox_results = results
		if not results:
			# Translators: Placeholder row shown in the results list when a device search finds nothing.
			self._jukebox_search_results.Append(_("No matching audio files found."))
			# Translators: Spoken alongside the placeholder row above.
			ui.message(_("No matching audio files found."))
			return
		for path in results:
			self._jukebox_search_results.Append(os.path.basename(path))
		self._jukebox_search_results.SetSelection(0)
		# Translators: Plural forms spoken after a successful device search; %d is how many audio files were found.
		ui.message(ngettext("%d file found.", "%d files found.", len(results)) % len(results))

	def _is_previewing_jukebox_path(self, path):
		"""Whether *path* is the file currently loaded in the player,
		regardless of whether it's playing or paused - mirrors
		_is_previewing() for the Podcast tab's preview list."""
		if not path or not self._player.has_media():
			return False
		current = self._player.get_current_station() or {}
		return current.get("url") == path

	def _on_jukebox_search_results_key(self, event):
		key = event.GetKeyCode()
		if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			self._on_jukebox_add_from_results(None)
			return
		if key == wx.WXK_SPACE:
			self._on_jukebox_preview_toggle(None)
			return
		event.Skip()

	def _on_jukebox_preview_toggle(self, event):
		idx = self._jukebox_search_results.GetSelection()
		if idx == wx.NOT_FOUND or idx >= len(self._jukebox_results):
			return
		path = self._jukebox_results[idx]

		if self._is_previewing_jukebox_path(path):
			if self._plugin:
				wx.CallAfter(self._plugin._stop_from_dialog)
			return

		station_dict = jukebox.JukeboxTrack(path).to_dict()
		profile = self._jukebox_manager.get_track_profile(path)
		if profile:
			station_dict["station_audio"] = profile
		self._play_callback(station_dict, [station_dict], 0, announce=True)

	def _on_jukebox_add_from_results(self, event):
		"""Add the selected device-search result to the jukebox - reached
		via the search results' context menu or Enter."""
		idx = self._jukebox_search_results.GetSelection()
		if idx == wx.NOT_FOUND or idx >= len(self._jukebox_results):
			return
		path = self._jukebox_results[idx]
		entry, error = self._jukebox_manager.add_file(path)
		if error:
			ui.message(error)
			return
		# Translators: Same confirmation as adding a folder; spoken here after adding a single audio file from a device-search result.
		ui.message(_("Added to jukebox: %s") % entry.title)
		self._refresh_jukebox_list(select_path=path)

	def _show_jukebox_result_context_menu(self):
		"""Context menu for the selected item in the device-search results list."""
		idx = self._jukebox_search_results.GetSelection()
		if idx == wx.NOT_FOUND or idx >= len(self._jukebox_results):
			return

		menu = wx.Menu()
		# Translators: Same Preview/Stop Preview toggle pattern as the GETEM search-result context menu, applied to a jukebox device-search result.
		label = _("&Stop Preview") if self._is_previewing_jukebox_path(self._jukebox_results[idx]) else _("&Preview")
		item_preview = menu.Append(wx.ID_ANY, label)
		self.Bind(wx.EVT_MENU, self._on_jukebox_preview_toggle, item_preview)

		# Translators: Context-menu item; adds the selected device-search result to the jukebox library.
		item_add = menu.Append(wx.ID_ANY, _("&Add to Jukebox"))
		self.Bind(wx.EVT_MENU, self._on_jukebox_add_from_results, item_add)

		self.PopupMenu(menu, self._jukebox_search_results.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _refresh_jukebox_list(self, select_path=None):
		"""Populate the jukebox entries listbox, preserving whichever
		entry is selected at the moment this runs (or selecting
		*select_path* if given) - mirrors _refresh_podcast_list()'s
		selection-preservation reasoning."""
		current_path = select_path
		if current_path is None:
			idx = self._jukebox_list.GetSelection()
			entries_before = self._jukebox_manager.get_entries()
			if idx != wx.NOT_FOUND and idx < len(entries_before):
				current_path = entries_before[idx].path

		self._jukebox_list.Clear()
		entries = self._jukebox_manager.get_entries()
		for entry in entries:
			label = self._with_marked_suffix(entry.display_label(), entry.path in self._jukebox_marked)
			self._jukebox_list.Append(label)

		restore_idx = wx.NOT_FOUND
		if current_path:
			for i, entry in enumerate(entries):
				if entry.path == current_path:
					restore_idx = i
					break

		if restore_idx != wx.NOT_FOUND:
			self._jukebox_list.SetSelection(restore_idx)
		elif entries:
			self._jukebox_list.SetSelection(0)
		self._on_jukebox_entry_selected(None)

	def _get_selected_jukebox_entry(self):
		idx = self._jukebox_list.GetSelection()
		entries = self._jukebox_manager.get_entries()
		if idx == wx.NOT_FOUND or idx >= len(entries):
			return None
		return entries[idx]

	def _on_jukebox_entry_selected(self, event):
		entry = self._get_selected_jukebox_entry()
		self._jukebox_remove_btn.Enable(entry is not None)

		# Preserve whichever track is currently selected before the list
		# gets rebuilt (this runs on every _refresh_jukebox_list() call,
		# not just when the user actually switches entries) - mirrors how
		# _refresh_jukebox_list() itself preserves the entries selection.
		# Without this, restoring keyboard focus to this list (see
		# focus_jukebox()) always landed on a list with nothing selected.
		current_track_path = None
		tidx = self._jukebox_tracks_list.GetSelection()
		prev_tracks = getattr(self, "_jukebox_selected_tracks", None) or []
		if tidx != wx.NOT_FOUND and tidx < len(prev_tracks):
			current_track_path = prev_tracks[tidx].path

		# Bumping this generation counter invalidates any duration-probing
		# background thread still running for the previously selected
		# entry (see _probe_jukebox_track_durations()) - it compares its
		# own captured generation against the current one before ever
		# touching the list control, so a slow probe from an entry the
		# user has since navigated away from can't land its results on
		# (or crash against) today's list.
		self._jukebox_tracks_generation = getattr(self, "_jukebox_tracks_generation", 0) + 1
		generation = self._jukebox_tracks_generation

		self._jukebox_tracks_list.Clear()
		self._jukebox_selected_tracks = entry.tracks() if entry else []
		# Populate immediately with bare titles - probe_duration=False
		# skips each track's header read (see JukeboxTrack.display_label()).
		# Landing on a folder with many tracks (e.g. right after adding it,
		# or when arrowing onto it in a freshly reopened dialog, where
		# nothing is cached yet) used to read every file's header here,
		# synchronously, before the UI/NVDA's speech could continue - for a
		# crowded folder that's a long silence. Real durations are filled
		# in afterwards, off the UI thread, by _probe_jukebox_track_durations().
		for track in self._jukebox_selected_tracks:
			self._jukebox_tracks_list.Append(track.display_label(self._player, probe_duration=False))

		if current_track_path:
			for i, track in enumerate(self._jukebox_selected_tracks):
				if track.path == current_track_path:
					self._jukebox_tracks_list.SetSelection(i)
					break

		if self._jukebox_selected_tracks:
			threading.Thread(
				target=self._probe_jukebox_track_durations,
				args=(self._jukebox_selected_tracks, generation),
				daemon=True,
			).start()

	def _probe_jukebox_track_durations(self, tracks, generation):
		"""Background counterpart to _on_jukebox_entry_selected(): reads
		each track's real duration (a per-file header probe - disk I/O)
		and updates its list label once known, so a folder with many
		tracks doesn't block the UI thread while every file in it gets
		opened and parsed.

		Label updates are batched (_FLUSH_SIZE at a time) rather than
		posted one wx.CallAfter per track: each wx.CallAfter is a Windows
		PostMessage under the hood, and posting one per file for a
		crowded folder (thousands of tracks probed within a couple of
		seconds) can exceed the OS message-queue quota, which surfaces as
		"OSError: [WinError 1816] Not enough quota is available to
		process this command." and drops the update. Batching cuts the
		message count by _FLUSH_SIZE, and the wx.CallAfter itself is
		still guarded (see _apply_jukebox_track_labels()) in case the
		quota is hit anyway - a dropped batch just means those labels
		stay untimed until the entry is reselected (a cache hit by then,
		so effectively instant).

		*generation* is the token captured by the caller at selection
		time; it's checked before every single-file probe and again
		before every UI update, so a probe left over from an entry the
		user has already navigated away from stops - rather than racing
		to write into - the list that's on screen now."""
		_FLUSH_SIZE = 25
		batch = []
		for i, track in enumerate(tracks):
			if getattr(self, "_jukebox_tracks_generation", None) != generation:
				return
			label = track.display_label(self._player)
			batch.append((i, label))
			if len(batch) >= _FLUSH_SIZE:
				wx.CallAfter(self._apply_jukebox_track_labels, batch, generation)
				batch = []
		if batch:
			wx.CallAfter(self._apply_jukebox_track_labels, batch, generation)

	def _apply_jukebox_track_labels(self, batch, generation):
		"""UI-thread callback for _probe_jukebox_track_durations(): writes
		a batch of probed labels into the tracks list, unless the
		selection has since moved on (generation mismatch). Individual
		indices past the current list length (list cleared/shrunk since)
		are skipped rather than raising. The whole call is wrapped since,
		rarely, even a batched wx.CallAfter can itself be refused by the
		OS message queue (see the docstring above) - if so this batch's
		labels are simply left untimed rather than crashing the probing
		thread."""
		try:
			if getattr(self, "_jukebox_tracks_generation", None) != generation:
				return
			count = self._jukebox_tracks_list.GetCount()
			for index, label in batch:
				if index < count:
					self._jukebox_tracks_list.SetString(index, label)
		except OSError:
			pass  # message-queue quota hit (see docstring above); this batch's labels stay untimed until the entry is reselected

	def _play_jukebox_track(self, track, announce=True, folder_path=None, folder_index=None):
		"""Play *track*. Its per-file audio profile (if the user saved
		one) is looked up here by absolute path and attached to the
		station dict as "station_audio", so playbackCoreMixin._play_station()
		applies it - the same mechanism podcasts and audio books use.
		Every playback path funnels through here (Enter/Space on the
		entries list, Enter/Space on the tracks list, F3/F4, and
		Ctrl+Left/Right), so the profile is applied consistently
		whichever way the track was started.

		*folder_path*/*folder_index* are set only when this track is being
		played as part of a folder sequence (see _play_jukebox_folder_track()
		below) - they're attached to the station dict as
		"jukebox_folder_path"/"jukebox_track_index" so a natural finish can
		auto-advance to the next track purely from the finished station's
		own fields, exactly the way a GETEM chapter carries
		"getem_detail_url"/"getem_chapter_index" for the same purpose (see
		playbackCoreMixin._advance_getem_chapter_headless()). This also
		means a track started any other way (tracks list, F3/F4, a single-
		file entry) simply doesn't carry these fields, so
		_on_playback_finished()/_advance_jukebox_folder_headless() have
		nothing to advance and correctly leave it as a one-off play - no
		separate "clear the folder state" bookkeeping needed."""
		station_dict = track.to_dict()
		profile = self._jukebox_manager.get_track_profile(track.path)
		if profile:
			station_dict["station_audio"] = profile
		if folder_path is not None:
			station_dict["jukebox_folder_path"] = folder_path
			station_dict["jukebox_track_index"] = folder_index
		self._play_callback(station_dict, [station_dict], 0, announce=announce)

	def _play_jukebox_folder_track(self, entry, tracks, index, announce=True):
		"""Play tracks[index] as part of *entry* (a folder), tagging the
		station dict so it can auto-advance to the next track on its own
		once this one plays through to the end - see _play_jukebox_track()'s
		docstring for how, and _on_playback_finished()/
		_advance_jukebox_folder_headless() for where that's picked back up.

		*tracks* is the snapshot taken when the folder started playing (see
		_on_jukebox_entry_play()); the advance path itself always re-reads
		entry.tracks() fresh (see _on_playback_finished()), so a background
		rescan mid-sequence only affects tracks not yet reached, never
		shifts the one already playing."""
		if index < 0 or index >= len(tracks):
			return
		self._play_jukebox_track(tracks[index], announce=announce, folder_path=entry.path, folder_index=index)

	def _on_jukebox_entry_play(self, event):
		"""Play the selected jukebox entry: for a file, just that file; for
		a folder, every track it contains in order, automatically
		advancing to the next one as each finishes on its own - the same
		auto-advance GETEM audio book parts get, and (like GETEM) it
		keeps advancing even if this dialog is later closed - see
		playbackCoreMixin._advance_jukebox_folder_headless(). The
		sequence starts from whichever track is currently highlighted in
		the tracks list (self._jukebox_tracks_list) rather than always
		the first one, so re-playing a folder you were partway through
		picks up where you last looked instead of restarting from track 1
		every time. If nothing in the tracks list is selected (e.g. right
		after adding the folder, or reopening the dialog fresh), it falls
		back to wherever this folder was last actually played to - saved
		across sessions by RadioPlayer.save_jukebox_folder_position() -
		and only defaults to the first track if the folder's never been
		played, or its saved track index no longer exists (fewer tracks
		now than when it was saved). Either way, the tracks list's
		selection (not keyboard focus - SetSelection() alone doesn't move
		that) is updated to match the track that actually starts playing,
		so the list reflects reality if the user tabs over to look at it
		afterwards. See jukebox.JukeboxEntry's docstring for why a folder
		itself isn't directly playable."""
		entry = self._get_selected_jukebox_entry()
		if not entry:
			return
		tracks = entry.tracks()
		if not tracks:
			# Translators: Spoken when trying to play a jukebox library entry that has no usable audio files.
			ui.message(_("No playable audio in this item."))
			return
		if entry.kind == "folder":
			start = self._jukebox_tracks_list.GetSelection()
			if start == wx.NOT_FOUND or start >= len(tracks):
				start = 0
				saved = self._player.get_jukebox_folder_position(entry.path)
				if saved is not None:
					saved_index, _saved_path = saved
					if 0 <= saved_index < len(tracks):
						start = saved_index
			self._jukebox_tracks_list.SetSelection(start)
			self._play_jukebox_folder_track(entry, tracks, start)
		else:
			self._jukebox_tracks_list.SetSelection(0)
			self._play_jukebox_track(tracks[0])

	def _on_jukebox_list_key(self, event):
		"""Jukebox entries list - Space pauses if something is playing,
		otherwise plays the focused entry; Enter always plays directly;
		'.' marks/unmarks the focused entry for bulk removal; Delete
		removes every marked entry (or, if none are marked, the focused
		entry, with confirmation) when the Remove button is enabled.
		Mirrors _on_episode_key()'s Space/Enter handling and
		_on_liked_list_key()'s Delete handling - wx reports Shift+Delete
		with the same WXK_DELETE key code, so both are handled here."""
		key = event.GetKeyCode()
		if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			self._on_jukebox_entry_play(event)
			return
		if key == wx.WXK_SPACE:
			if self._player.is_playing():
				self._player.pause()
				# Translators: Same "Paused" wording as elsewhere; spoken here when Space pauses playback from the jukebox library list.
				_notify(_("Paused"))
			else:
				self._on_jukebox_entry_play(None)
			return
		if key == wx.WXK_DELETE:
			if self._jukebox_marked:
				self._on_jukebox_remove_selected(event)
			elif self._jukebox_remove_btn.IsEnabled():
				self._on_jukebox_remove_entry(event)
			return
		event.Skip()

	def _toggle_jukebox_mark(self):
		"""Mark/unmark the focused jukebox entry with '.' for the Remove
		Selected bulk-delete flow (Delete key or context menu). Updates
		the row's display text immediately so the marked state is
		visible/announced while simply arrowing through the list
		afterwards, not only at the moment of marking."""
		idx = self._jukebox_list.GetSelection()
		entry = self._get_selected_jukebox_entry()
		if not entry:
			return
		if entry.path in self._jukebox_marked:
			self._jukebox_marked.discard(entry.path)
			# Translators: Spoken after unmarking a jukebox entry in the multi-select removal flow; %s is the entry title.
			ui.message(_("Unmarked: %s") % entry.title)
		else:
			self._jukebox_marked.add(entry.path)
			# Translators: Spoken after marking a jukebox entry in the multi-select removal flow; %s is the entry title.
			ui.message(_("Marked: %s") % entry.title)
		label = self._with_marked_suffix(entry.display_label(), entry.path in self._jukebox_marked)
		self._jukebox_list.SetString(idx, label)
		self._jukebox_list.SetSelection(idx)

	def _on_jukebox_remove_selected(self, event=None):
		"""Bulk-remove every jukebox entry currently marked with '.',
		asking for confirmation once for the whole batch."""
		marked = self._jukebox_marked
		if not marked:
			return
		entries = [e for e in self._jukebox_manager.get_entries() if e.path in marked]
		count = len(entries)
		if count == 0:
			self._jukebox_marked.clear()
			return
		# Translators: Body of the bulk-remove confirmation dialog for jukebox entries; %d is how many entries are marked.
		message = ngettext(
			"Do you want to remove the %d marked entry from the jukebox?",
			"Do you want to remove the %d marked entries from the jukebox?",
			count,
		) % count
		# Translators: Title of the bulk-remove confirmation dialog for jukebox entries.
		if not self._confirm_bulk_remove(count, _("Remove From Jukebox"), message):
			return
		for entry in entries:
			self._jukebox_manager.remove_entry(entry.path)
			self._player.clear_jukebox_folder_position(entry.path)
		self._jukebox_marked.clear()
		# Translators: Spoken after bulk-removing marked jukebox entries; %d is how many were removed.
		ui.message(ngettext("%d entry removed", "%d entries removed", count) % count)
		self._refresh_jukebox_list()
		count_left = self._jukebox_list.GetCount()
		if count_left > 0:
			self._jukebox_list.SetSelection(0)
			self._on_jukebox_entry_selected(None)
			self._jukebox_list.SetFocus()
		else:
			self._jukebox_add_file_btn.SetFocus()

	def _on_jukebox_track_play(self, event):
		idx = self._jukebox_tracks_list.GetSelection()
		tracks = getattr(self, "_jukebox_selected_tracks", None) or []
		if idx == wx.NOT_FOUND or idx >= len(tracks):
			return
		self._play_jukebox_track(tracks[idx])

	def _on_jukebox_tracks_key(self, event):
		key = event.GetKeyCode()
		if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			self._on_jukebox_track_play(event)
			return
		if key == wx.WXK_SPACE:
			if self._player.is_playing():
				self._player.pause()
				# Translators: Same "Paused" wording as elsewhere; spoken here when Space pauses playback from the jukebox tracks list.
				_notify(_("Paused"))
			else:
				self._on_jukebox_track_play(None)
			return
		event.Skip()

	def _show_jukebox_track_context_menu(self):
		"""Context menu for the selected track. Save/Clear Audio Profile
		act on this exact file (its absolute path), so two tracks inside
		the same folder entry carry independent profiles."""
		idx = self._jukebox_tracks_list.GetSelection()
		tracks = getattr(self, "_jukebox_selected_tracks", None) or []
		if idx == wx.NOT_FOUND or idx >= len(tracks):
			return
		track = tracks[idx]
		has_profile = bool(self._jukebox_manager.get_track_profile(track.path))

		menu = wx.Menu()
		# Translators: Context-menu item; plays the selected track from within a jukebox folder entry.
		item_play = menu.Append(wx.ID_ANY, _("&Play"))
		self.Bind(wx.EVT_MENU, self._on_jukebox_track_play, item_play)

		menu.AppendSeparator()

		# Translators: Jukebox track context menu item - saves an audio profile (volume/effects/speed/transpose) that applies to this file
		item_save_profile = menu.Append(wx.ID_ANY, _("Save Audio Pr&ofile for This File"))
		self.Bind(wx.EVT_MENU, self._on_save_jukebox_track_audio_profile, item_save_profile)

		# Translators: Jukebox track context menu item - removes the saved audio profile from this file
		item_clear_profile = menu.Append(wx.ID_ANY, _("Clear Audio Prof&ile"))
		item_clear_profile.Enable(has_profile)
		self.Bind(wx.EVT_MENU, self._on_clear_jukebox_track_audio_profile, item_clear_profile)

		menu.AppendSeparator()
		# Translators: Context-menu item; copies the selected track's file path to the clipboard.
		item_copy_path = menu.Append(wx.ID_ANY, _("&Copy Path"))
		self.Bind(wx.EVT_MENU, lambda e: self._copy_to_clipboard(track.path), item_copy_path)

		self.PopupMenu(menu, self._jukebox_tracks_list.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _on_jukebox_add_file(self, event):
		ext_pattern = ";".join("*" + ext for ext in jukebox.AUDIO_EXTENSIONS)
		# Translators: File-type filter label for the add-audio-files picker; %s is a glob pattern of supported extensions (e.g. '*.mp3;*.ogg'), also appended raw after the '|' as required by the file-dialog format - don't translate the pattern itself.
		wildcard = _("Audio files (%s)") % ext_pattern + "|" + ext_pattern
		dlg = wx.FileDialog(
			self,
			# Translators: Title of the file-picker dialog for adding files to the jukebox.
			message=_("Add audio files to the jukebox"),
			wildcard=wildcard,
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
		)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		paths = dlg.GetPaths()
		dlg.Destroy()

		added = 0
		last_path = None
		errors = []
		for path in paths:
			entry, error = self._jukebox_manager.add_file(path)
			if error:
				errors.append("%s: %s" % (os.path.basename(path), error))
			else:
				added += 1
				last_path = entry.path
		if added:
			self._refresh_jukebox_list(select_path=last_path)
		if errors:
			ui.message("; ".join(errors))
		elif added:
			# Translators: Plural forms spoken after adding files to the jukebox via the file picker; %d is how many were added.
			ui.message(ngettext("%d file added.", "%d files added.", added) % added)

	def _pick_folders_via_loop(self, title):
		"""Fallback for when the native multi-select folder picker isn't
		available: reopens wx.DirDialog next to the last pick, one folder
		at a time, until the user cancels it."""
		paths = []
		start_dir = ""
		while True:
			dlg = wx.DirDialog(self, title, defaultPath=start_dir)
			if dlg.ShowModal() != wx.ID_OK:
				dlg.Destroy()
				break
			path = dlg.GetPath()
			dlg.Destroy()
			# Reopen next to the folder just picked, so adding several
			# sibling folders doesn't mean renavigating from scratch each time.
			start_dir = os.path.dirname(path)
			paths.append(path)
		return paths

	def _on_jukebox_add_folder(self, event):
		"""Lets the user add several folders at once, the same way multiple
		files can be added: tries the native Windows multi-select folder
		picker first, and only falls back to reopening the ordinary folder
		picker (one folder at a time, until cancelled) if that native
		dialog isn't available on this system."""
		# Translators: Title of the dialog used to add one or more folders to the jukebox at once.
		title = _("Add folders to the jukebox")
		paths = _pick_folders_native(self, title)
		if paths is None:
			paths = self._pick_folders_via_loop(title)

		added_entries = []
		errors = []
		for path in paths:
			entry, error = self._jukebox_manager.add_folder(path)
			if error:
				errors.append("%s: %s" % (os.path.basename(path), error))
			else:
				added_entries.append(entry)

		if added_entries:
			self._refresh_jukebox_list(select_path=added_entries[-1].path)
		if errors:
			ui.message("; ".join(errors))
		elif len(added_entries) == 1:
			# Translators: Same confirmation as adding a single file; spoken here after adding a single folder to the jukebox.
			ui.message(_("Added to jukebox: %s") % added_entries[0].title)
		elif added_entries:
			# Translators: Plural forms spoken after adding several folders to the jukebox in one go (one folder picker used repeatedly); %d is how many folders were added.
			ui.message(ngettext("%d folder added.", "%d folders added.", len(added_entries)) % len(added_entries))

	def _on_jukebox_remove_entry(self, event):
		entry = self._get_selected_jukebox_entry()
		if not entry:
			return
		title = entry.title
		# Ask for confirmation before removing the entry - mirrors
		# _on_liked_remove()'s confirmation prompt.
		dlg = wx.MessageDialog(
			self,
			# Translators: Body of the remove-confirmation dialog; %s is the jukebox entry title.
			_("Do you want to remove \"%s\" from the jukebox?") % title,
			# Translators: Title of the jukebox remove-confirmation dialog.
			_("Remove From Jukebox"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		)
		result = dlg.ShowModal()
		dlg.Destroy()
		if result != wx.ID_YES:
			return
		# Remember the removed index so we can move focus to whichever
		# entry takes its place afterwards.
		deleted_idx = self._jukebox_list.GetSelection()
		self._jukebox_manager.remove_entry(entry.path)
		self._jukebox_marked.discard(entry.path)
		self._player.clear_jukebox_folder_position(entry.path)
		# Translators: Spoken after successfully removing a jukebox entry; %s is its title.
		ui.message(_("Removed from jukebox: %s") % title)
		self._refresh_jukebox_list()
		# After removal, move focus to the next entry (or the new last
		# entry if the removed one was at the end); if the jukebox is now
		# empty, move focus to Add File instead - mirrors
		# _on_liked_remove()'s post-deletion focus handling.
		count = self._jukebox_list.GetCount()
		if count > 0 and deleted_idx != wx.NOT_FOUND:
			new_idx = min(deleted_idx, count - 1)
			self._jukebox_list.SetSelection(new_idx)
			self._on_jukebox_entry_selected(None)
			self._jukebox_list.SetFocus()
		else:
			self._jukebox_add_file_btn.SetFocus()

	def _on_jukebox_rescan_folder(self, event):
		entry = self._get_selected_jukebox_entry()
		if not entry or entry.kind != "folder":
			return
		self._jukebox_manager.rescan_folder(entry.path)
		# Translators: Spoken after re-scanning a jukebox folder entry for changes on device; %s is the folder's title.
		ui.message(_("Rescanned: %s") % entry.title)
		self._refresh_jukebox_list(select_path=entry.path)

	def _save_jukebox_file_profile(self, path, display_name):
		"""Shared body of the Save Audio Profile actions - both the
		single-file entry's context menu and the track list's context
		menu funnel through here so the two views behave identically for
		what is, in both cases, the same underlying file."""
		existing = self._jukebox_manager.get_track_profile(path)
		profile = self._prompt_and_build_audio_profile(existing, allow_speed=True)
		if profile is None:
			return
		self._jukebox_manager.set_track_profile(path, profile)
		# Translators: Spoken after saving an audio profile for a single jukebox file; %(file)s is its display name.
		ui.message(_("Audio profile saved for %(file)s") % {"file": display_name})

	def _clear_jukebox_file_profile(self, path, display_name):
		"""Shared body of the Clear Audio Profile actions - see
		_save_jukebox_file_profile()."""
		if not self._jukebox_manager.get_track_profile(path):
			return
		self._jukebox_manager.set_track_profile(path, None)
		# Translators: Spoken after clearing a jukebox file's saved audio profile; %(file)s is its display name.
		ui.message(_("Audio profile cleared for %(file)s") % {"file": display_name})

	def _on_save_jukebox_entry_audio_profile(self, event):
		"""Save an audio profile for the selected *file* jukebox entry.
		A folder entry has no profile of its own - profiles are per file
		and saved from the Tracks list (or from that folder's own
		individual track context menus) - so this is a no-op for folders,
		and the menu item is disabled for them accordingly."""
		entry = self._get_selected_jukebox_entry()
		if not entry or entry.kind != "file":
			return
		self._save_jukebox_file_profile(entry.path, entry.title)

	def _on_clear_jukebox_entry_audio_profile(self, event):
		"""Remove the saved profile from the selected *file* jukebox entry."""
		entry = self._get_selected_jukebox_entry()
		if not entry or entry.kind != "file":
			return
		self._clear_jukebox_file_profile(entry.path, entry.title)

	def _on_save_jukebox_track_audio_profile(self, event):
		"""Save an audio profile for the selected track (this exact file)."""
		idx = self._jukebox_tracks_list.GetSelection()
		tracks = getattr(self, "_jukebox_selected_tracks", None) or []
		if idx == wx.NOT_FOUND or idx >= len(tracks):
			return
		track = tracks[idx]
		self._save_jukebox_file_profile(track.path, track.title)

	def _on_clear_jukebox_track_audio_profile(self, event):
		"""Remove the saved profile from the selected track."""
		idx = self._jukebox_tracks_list.GetSelection()
		tracks = getattr(self, "_jukebox_selected_tracks", None) or []
		if idx == wx.NOT_FOUND or idx >= len(tracks):
			return
		track = tracks[idx]
		self._clear_jukebox_file_profile(track.path, track.title)

	def _show_jukebox_entry_context_menu(self):
		"""Context menu for the selected item in the jukebox entries list.

		The Save/Clear Audio Profile items apply to *single-file* entries
		only - a folder has no profile of its own (profiles are per file
		and saved from the Tracks list), so they're shown disabled for
		folder entries to make that visible rather than hiding them and
		leaving the menu looking inconsistent between the two kinds."""
		entry = self._get_selected_jukebox_entry()
		if not entry:
			return

		menu = wx.Menu()
		# Translators: Context-menu item; plays the selected jukebox file/folder.
		item_play = menu.Append(wx.ID_ANY, _("&Play"))
		self.Bind(wx.EVT_MENU, self._on_jukebox_entry_play, item_play)

		if entry.kind == "folder":
			# Translators: Context-menu item; re-scans a jukebox folder entry for added/removed files on device.
			item_rescan = menu.Append(wx.ID_ANY, _("&Rescan Folder"))
			self.Bind(wx.EVT_MENU, self._on_jukebox_rescan_folder, item_rescan)

		# Translators: Context-menu item; removes the selected entry from the jukebox library.
		item_remove = menu.Append(wx.ID_ANY, _("Re&move"))
		self.Bind(wx.EVT_MENU, self._on_jukebox_remove_entry, item_remove)

		# Translators: Context-menu item; bulk-removes every jukebox entry marked with '.', asking for confirmation once for the whole batch.
		item_remove_selected = menu.Append(wx.ID_ANY, _("Remove &Selected"))
		item_remove_selected.Enable(bool(self._jukebox_marked))
		self.Bind(wx.EVT_MENU, self._on_jukebox_remove_selected, item_remove_selected)

		menu.AppendSeparator()

		is_file = (entry.kind == "file")
		has_profile = bool(is_file and self._jukebox_manager.get_track_profile(entry.path))

		# Translators: Jukebox context menu item - saves an audio profile (volume/effects/speed/transpose) that applies to this file
		item_save_profile = menu.Append(wx.ID_ANY, _("Save Audio Pr&ofile for This File"))
		item_save_profile.Enable(is_file)
		self.Bind(wx.EVT_MENU, self._on_save_jukebox_entry_audio_profile, item_save_profile)

		# Translators: Jukebox context menu item - removes the saved audio profile from this file
		item_clear_profile = menu.Append(wx.ID_ANY, _("Clear Audio Prof&ile"))
		item_clear_profile.Enable(has_profile)
		self.Bind(wx.EVT_MENU, self._on_clear_jukebox_entry_audio_profile, item_clear_profile)

		menu.AppendSeparator()
		# Translators: Context-menu item; copies the selected entry's file/folder path to the clipboard.
		item_copy_path = menu.Append(wx.ID_ANY, _("&Copy Path"))
		self.Bind(wx.EVT_MENU, lambda e: self._copy_to_clipboard(entry.path), item_copy_path)

		self.PopupMenu(menu, self._jukebox_list.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()


class LyricsDialog(wx.Dialog):
	"""Read-only lyrics viewer."""

	def __init__(self, parent, song, lyrics):
		super().__init__(
			parent,
			# Translators: Title of the lyrics dialog; %s is the song string (e.g. "Artist - Title").
			title=_("Lyrics — %s") % song,
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		sizer = wx.BoxSizer(wx.VERTICAL)

		sizer.Add(
			# Translators: Heading inside the lyrics dialog restating which song the lyrics are for; %s is the song string.
			wx.StaticText(self, label=_("Lyrics for: %s") % song),
			0, wx.EXPAND | wx.ALL, 8,
		)

		self._text = wx.TextCtrl(
			self,
			value=lyrics,
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
		)
		# Translators: Accessible name for the read-only lyrics text area.
		self._text.SetName(_("Lyrics"))
		sizer.Add(self._text, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		btn_sizer = wx.StdDialogButtonSizer()
		# Translators: Button label; closes the lyrics dialog.
		close_btn = wx.Button(self, wx.ID_CLOSE, label=_("&Close"))
		close_btn.SetDefault()
		btn_sizer.AddButton(close_btn)
		btn_sizer.Realize()
		sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)

		close_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
		self.Bind(wx.EVT_CHAR_HOOK, self._on_key)

		self.SetSizer(sizer)
		self.SetSize((520, 540))
		self.SetMinSize((350, 300))
		wx.CallAfter(self._text.SetFocus)

	def _on_key(self, event):
		if event.GetKeyCode() == wx.WXK_ESCAPE:
			self.EndModal(wx.ID_CLOSE)
		else:
			event.Skip()


class AddCustomStationDialog(wx.Dialog):

	def __init__(self, parent):
		# Translators: Title of the dialog for manually adding a custom station by stream URL.
		super().__init__(parent, title=_("Add Custom Station"))
		sizer = wx.BoxSizer(wx.VERTICAL)

		# Translators: Label for the custom-station name field.
		sizer.Add(wx.StaticText(self, label=_("Station name:")), 0, wx.EXPAND | wx.ALL, 5)
		self._name = wx.TextCtrl(self)
		sizer.Add(self._name, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# Translators: Label for the custom-station stream-URL field.
		sizer.Add(wx.StaticText(self, label=_("Stream URL:")), 0, wx.EXPAND | wx.ALL, 5)
		self._url = wx.TextCtrl(self)
		sizer.Add(self._url, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# URL test button + status label
		test_row = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Button label; checks whether the typed stream URL is reachable and playable before adding the station.
		self._test_btn = wx.Button(self, label=_("&Test URL"))
		test_row.Add(self._test_btn, 0, wx.RIGHT, 8)
		self._test_status = wx.StaticText(self, label="")
		test_row.Add(self._test_status, 1, wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(test_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# Translators: Button label; opens Radio Browser's own website to submit this station to their public directory (separate from just adding it locally to FreeRadio).
		self._rb_btn = wx.Button(self, label=_("Add to &Radio Browser directory…"))
		sizer.Add(self._rb_btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		btn_sizer = wx.StdDialogButtonSizer()
		# Translators: Button label; confirms and adds the custom station to favourites.
		ok_btn = wx.Button(self, wx.ID_OK, label=_("&Add"))
		ok_btn.SetDefault()
		btn_sizer.AddButton(ok_btn)
		btn_sizer.AddButton(wx.Button(self, wx.ID_CANCEL))
		btn_sizer.Realize()
		sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)

		self.SetSizer(sizer)
		self.Fit()
		self.SetMinSize((400, -1))
		wx.CallAfter(self._name.SetFocus)

		self._test_btn.Bind(wx.EVT_BUTTON, self._on_test_url)
		self._rb_btn.Bind(wx.EVT_BUTTON, self._on_open_radio_browser)

	def _on_open_radio_browser(self, event):
		import webbrowser
		webbrowser.open("https://www.radio-browser.info/add")

	def _on_test_url(self, event):
		url = self._url.GetValue().strip()
		if not url:
			# Translators: Status text shown next to the Test URL button when it's pressed with an empty URL field.
			self._test_status.SetLabel(_("Please enter a URL first."))
			# Translators: Spoken alongside the status text above.
			ui.message(_("Please enter a URL first."))
			return
		self._test_btn.Enable(False)
		# Translators: Status text shown next to the Test URL button while the check is in progress.
		self._test_status.SetLabel(_("Checking…"))
		# Translators: Spoken when the URL check starts.
		ui.message(_("Checking stream URL, please wait…"))

		def _worker():
			ok, detail = check_stream_url(url)
			wx.CallAfter(self._on_test_done, ok, detail)

		threading.Thread(target=_worker, daemon=True).start()

	def _on_test_done(self, ok, detail):
		if not self:
			return
		self._test_btn.Enable(True)
		if ok:
			# Translators: Status text shown next to the Test URL button when the stream checked out as playable; the '✓' is a visual checkmark, not meant to be read as punctuation.
			label = _("✓ Stream reachable")
			self._test_status.SetLabel(label)
			# Translators: Spoken when the stream check succeeds.
			ui.message(_("Stream is reachable."))
		else:
			# Translators: Status text shown when the stream check failed; the '✗' is a visual cross mark, %s is the specific error from check_stream_url().
			label = _("✗ %s") % detail
			self._test_status.SetLabel(label)
			# Translators: Spoken when the stream check fails; %s is the specific error from check_stream_url().
			ui.message(_("Stream check failed: %s") % detail)
		self.Layout()
		self.Fit()

	def get_values(self):
		return self._name.GetValue().strip(), self._url.GetValue().strip()

class EditScheduleDialog(wx.Dialog):
	"""Dialog for editing an existing ScheduledRecording.

	Pre-fills all fields from the given rec object.  On OK, call get_values()
	to retrieve a dict with the updated settings.
	"""

	def __init__(self, parent, rec):
		super().__init__(
			parent,
			# Translators: Title of the dialog for editing an existing scheduled recording; %s is the station name.
			title=_("Edit Schedule — %s") % rec.station.get("name", "?"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		self._rec          = rec

		sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Time ---
		# Translators: Label for the start-time field (also used as its accessible name below); value is typed as HH:MM.
		sizer.Add(wx.StaticText(self, label=_("Start time (HH:MM):")), 0, wx.EXPAND | wx.ALL, 8)
		self._time_ctrl = wx.TextCtrl(self, value=rec.start_time.strftime("%H:%M"))
		# Translators: Accessible name for the start-time field (same text as its static label above).
		self._time_ctrl.SetName(_("Start time (HH:MM):"))
		sizer.Add(self._time_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		# --- Duration ---
		# Translators: Label for the recording-duration field (also used as its accessible name below); value is in minutes.
		sizer.Add(wx.StaticText(self, label=_("Duration (minutes):")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._dur_spin = wx.SpinCtrl(self, min=1, max=600, initial=rec.duration_minutes)
		# Translators: Accessible name for the duration field (same text as its static label above).
		self._dur_spin.SetName(_("Duration (minutes):"))
		sizer.Add(self._dur_spin, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		# --- Recurrence ---
		# Translators: Label above the recurrence radio buttons (once vs. weekly) - same wording as the Recording tab's scheduling section.
		sizer.Add(wx.StaticText(self, label=_("Recurrence:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		# Translators: Radio button: this is a single one-time recording.
		self._rec_once  = wx.RadioButton(self, label=_("Only &once"), style=wx.RB_GROUP)
		# Repeats every week on the selected active days, with no end —
		# the user removes it from the schedule list to stop it. Legacy
		# entries saved with the old fixed-count "weekly" mode are treated
		# the same way here; saving will convert them to indefinite.
		# Translators: Radio button: this recording repeats every week on the checked days.
		self._rec_indef = wx.RadioButton(self, label=_("Repeat &weekly"))
		for rb in (self._rec_once, self._rec_indef):
			sizer.Add(rb, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		if rec.recurrence in ("weekly", "indefinite"):
			self._rec_indef.SetValue(True)
		else:
			self._rec_once.SetValue(True)

		# --- Active days ---
		# Translators: Day-of-week checklist items, Monday through Sunday (continues on the next line) - same as the Recording tab.
		_day_labels = [
			_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
			_("Friday"), _("Saturday"), _("Sunday"),
		]
		# Translators: Label above the day-of-week checklist, shown only for the weekly-repeat recurrence mode.
		self._days_label = wx.StaticText(self, label=_("Active days:"))
		sizer.Add(self._days_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._days_clb = nvdaControls.CustomCheckListBox(self, choices=_day_labels)
		# Translators: Accessible name for the day-of-week checklist (same text as its static label above).
		self._days_clb.SetName(_("Active days:"))
		checked = rec.active_days if rec.active_days else list(range(7))
		self._days_clb.Checked = checked
		if checked:
			self._days_clb.Select(checked[0])
		sizer.Add(self._days_clb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		# --- Playback mode ---
		# Translators: Label above the two playback-mode radio buttons for this scheduled recording.
		sizer.Add(wx.StaticText(self, label=_("Playback during recording:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		# Translators: Radio button: play the station out loud while also recording it.
		self._mode_play = wx.RadioButton(self, label=_("Record while &listening (play and record simultaneously)"),  style=wx.RB_GROUP)
		# Translators: Radio button: record silently, without audio output.
		self._mode_rec  = wx.RadioButton(self, label=_("Record &only (no audio output)"))
		sizer.Add(self._mode_play, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		sizer.Add(self._mode_rec,  0, wx.LEFT | wx.RIGHT | wx.TOP, 4)
		if rec.record_only:
			self._mode_rec.SetValue(True)
		else:
			self._mode_play.SetValue(True)

		# --- Output folder ---
		(
			self._folder_default_rb,
			self._folder_custom_rb,
			self._folder_path,
			self._folder_browse_btn,
		) = _build_folder_picker(self, sizer, initial_folder=rec.output_folder or "")

		# --- OK / Cancel ---
		btn_sizer = wx.StdDialogButtonSizer()
		# Translators: 'Save' button label; commits the edited schedule entry.
		ok_btn = wx.Button(self, wx.ID_OK, label=_("&Save"))
		ok_btn.SetDefault()
		btn_sizer.AddButton(ok_btn)
		btn_sizer.AddButton(wx.Button(self, wx.ID_CANCEL))
		btn_sizer.Realize()
		sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)

		self.SetSizer(sizer)
		self.Fit()
		self.SetMinSize((360, -1))

		# Wire up visibility toggles
		for rb in (self._rec_once, self._rec_indef):
			rb.Bind(wx.EVT_RADIOBUTTON, self._on_recurrence_changed)
		ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)

		self._update_visibility()
		wx.CallAfter(self._time_ctrl.SetFocus)

	# ------------------------------------------------------------------
	def _update_visibility(self):
		self._days_label.Show(True)
		self._days_clb.Show(True)
		self.Layout()

	def _on_recurrence_changed(self, event):
		self._update_visibility()
		event.Skip()

	def _on_ok(self, event):
		time_str = self._time_ctrl.GetValue().strip()
		try:
			parts = time_str.split(":")
			if len(parts) != 2:
				raise ValueError()
			hour, minute = int(parts[0]), int(parts[1])
			if not (0 <= hour <= 23 and 0 <= minute <= 59):
				raise ValueError()
		except (ValueError, IndexError):
			# Translators: Same time-format error as the Add Schedule form, shown here when saving an edited schedule with an invalid time.
			ui.message(_("Invalid time format. Use HH:MM"))
			self._time_ctrl.SetFocus()
			return

		# Build new start_time, keeping original date for once-off entries,
		# or using today/tomorrow for recurring ones.
		import datetime as _dt
		rec = self._rec
		if rec.recurrence == "once":
			# Keep the original date; only the time changes.
			new_start = rec.start_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
		else:
			now       = _dt.datetime.now()
			new_start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
			if new_start <= now:
				new_start += _dt.timedelta(days=1)

		self._result = {
			"start_time":       new_start,
			"duration_minutes": self._dur_spin.GetValue(),
			"recurrence":       "indefinite" if self._rec_indef.GetValue() else "once",
			"active_days":      list(self._days_clb.Checked),
			"max_occurrences":  0,
			"record_only":      self._mode_rec.GetValue(),
			"output_folder":    _folder_picker_value(self._folder_custom_rb, self._folder_path),
		}
		self.EndModal(wx.ID_OK)

	def get_values(self):
		return self._result