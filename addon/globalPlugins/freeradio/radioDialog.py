# -*- coding: utf-8 -*-
# FreeRadio - Station Browser Dialog

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
import urllib.parse
import urllib.request
from gui import nvdaControls
from html import unescape

_ = _tr
del _tr

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
		wx.StaticText(parent, label=_("Save recording to:")),
		0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
	)
	default_rb = wx.RadioButton(
		parent, label=_("&Default recordings folder"), style=wx.RB_GROUP,
	)
	custom_rb = wx.RadioButton(parent, label=_("&Selected folder:"))
	sizer.Add(default_rb, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
	sizer.Add(custom_rb,  0, wx.LEFT | wx.RIGHT | wx.TOP, 4)

	path_row  = wx.BoxSizer(wx.HORIZONTAL)
	path_ctrl = wx.TextCtrl(parent, value=initial_folder)
	path_ctrl.SetName(_("Selected folder:"))
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
		return False, _("Response received but content type is not audio: %s") % ct

	except _err.HTTPError as e:
		return False, _("HTTP error %d: %s") % (e.code, e.reason)
	except _err.URLError as e:
		return False, _("Connection failed: %s") % str(e.reason)
	except OSError as e:
		return False, _("Network error: %s") % str(e)
	except Exception as e:
		return False, str(e)


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
		# Tab labels no longer carry letter accelerators; numeric shortcuts
		# Alt+1..5 are handled in _on_char_hook via an accelerator table.
		self._notebook.AddPage(self._all_panel,   _("All Stations"))
		self._notebook.AddPage(self._fav_panel,   _("Favourites"))
		self._notebook.AddPage(self._rec_panel,   _("Recording"))
		self._notebook.AddPage(self._timer_panel, _("Timer"))
		self._notebook.AddPage(self._liked_panel, _("Liked Songs"))
		self._notebook.AddPage(self._podcast_panel, _("Podcasts"))
		self._notebook.AddPage(self._getem_panel, _("Audio Books"))
		self._notebook.SetSelection(0)  # Start on the All Stations tab
		main_sizer.Add(self._notebook, 1, wx.EXPAND | wx.ALL, 5)

		disable_bass = config.conf["freeradio"].get("disable_bass", False)

		# Audio Output Device line (visible on all tabs, only if BASS is enabled)
		device_row = wx.BoxSizer(wx.HORIZONTAL)
		self._dev_label = wx.StaticText(self, label=_("Output device:"))
		device_row.Add(self._dev_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
		self._device_choice = wx.Choice(self, choices=[_("Loading...")])
		self._device_choice.SetName(_("Output device:"))
		self._device_choice.SetMinSize((200, -1))
		device_row.Add(self._device_choice, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
		main_sizer.Add(device_row, 0, wx.EXPAND | wx.TOP, 4)
		self._dialog_audio_devices = []   # (index, name)
		self._audio_devices_loading = False
		self._audio_devices_last_refresh = 0.0
		
		if not disable_bass:
			self.refresh_audio_devices(force=True)
		else:
			self._dev_label.Hide()
			self._device_choice.Hide()

		# Volume and Effects row (visible on all tabs)
		audio_row = wx.BoxSizer(wx.HORIZONTAL)

		_vol_label = wx.StaticText(self, label=_("Volume:"))
		audio_row.Add(_vol_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)

		self._vol_spin = wx.SpinCtrl(self, min=0, max=200,
		                             initial=config.conf["freeradio"]["volume"])
		self._vol_spin.SetName(_("Volume:"))
		self._vol_spin.SetMinSize((70, -1))
		audio_row.Add(self._vol_spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

		# Effects - only if BASS is enabled
		self._fx_label = wx.StaticText(self, label=_("Effects:"))
		audio_row.Add(self._fx_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)

		self._fx_keys = ["chorus", "compressor", "distortion",
		                 "echo", "flanger", "gargle", "reverb",
		                 "eq_bass", "eq_treble", "eq_vocal"]
		_fx_display = [
			_("Chorus"), _("Compressor"), _("Distortion"),
			_("Echo"), _("Flanger"), _("Gargle"), _("Reverb"),
			_("EQ: Bass Boost"), _("EQ: Treble Boost"), _("EQ: Vocal Boost"),
		]
		self._fx_choice = wx.CheckListBox(self, choices=_fx_display)
		self._fx_choice.SetName(_("Effects:"))
		_saved_fx = config.conf["freeradio"].get("audio_fx", "none")
		_active = {x.strip() for x in _saved_fx.split(",") if x.strip() != "none"}
		for i, key in enumerate(self._fx_keys):
			self._fx_choice.Check(i, key in _active)
		audio_row.Add(self._fx_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

		if disable_bass:
			self._fx_label.Hide()
			self._fx_choice.Hide()

		main_sizer.Add(audio_row, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)

		# EQ gain row — shown only when at least one EQ effect is enabled
		eq_row = wx.BoxSizer(wx.HORIZONTAL)
		self._eq_bands = [
			("eq_bass",   _("Bass gain (dB):"),   9),
			("eq_treble", _("Treble gain (dB):"), 9),
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

		if disable_bass:
			for spin in self._eq_spins.values():
				spin.Hide()
			for item in eq_row.GetChildren():
				wnd = item.GetWindow()
				if wnd:
					wnd.Hide()


		# action buttons
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self._play_btn    = wx.Button(self, label=_("&Play/Pause"))
		self._del_btn     = wx.Button(self, label=_("&Delete Station"))
		self._del_btn.Enable(False)
		self._fav_btn     = wx.Button(self, label=_("Add to Fa&vorites"))
		self._details_btn = wx.Button(self, label=_("Station Detai&ls"))
		self._details_btn.Enable(False)
		self._add_btn     = wx.Button(self, label=_("Add C&ustom Station..."))
		# Manually re-syncs the local station list cache from the Radio Browser
		# API, instead of waiting for the periodic background refresh.
		self._refresh_catalog_btn = wx.Button(self, label=_("&Update Station List"))
		self._refresh_catalog_btn.SetToolTip(
			_("Re-downloads the full station list from the server, so search and browsing use the latest data.")
		)
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
		Indices: 0=All Stations, 1=Favourites, 2=Recording, 3=Timer, 4=Liked Songs.

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

	def _build_fav_tab(self):
		sizer = wx.BoxSizer(wx.VERTICAL)

		# Filter row: label + text field that narrows the favourites list in real time.
		sizer.Add(
			wx.StaticText(self._fav_panel, label=_("Filter:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._fav_filter = wx.TextCtrl(self._fav_panel)
		self._fav_filter.SetName(_("Filter favourites"))
		sizer.Add(self._fav_filter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		self._fav_list = wx.ListBox(self._fav_panel, style=wx.LB_SINGLE)
		self._fav_list.SetName(_("Favourites"))
		sizer.Add(self._fav_list, 1, wx.EXPAND | wx.ALL, 5)

		btn_row = wx.BoxSizer(wx.HORIZONTAL)
		self._save_audio_btn = wx.Button(self._fav_panel, label=_("Save Audio Pr&ofile for This Station"))
		self._save_audio_btn.Enable(False)
		btn_row.Add(self._save_audio_btn, 0, wx.RIGHT, 6)

		self._clear_audio_btn = wx.Button(self._fav_panel, label=_("Clear Audio Prof&ile"))
		self._clear_audio_btn.Enable(False)
		btn_row.Add(self._clear_audio_btn, 0, wx.RIGHT, 6)

		self._rename_btn = wx.Button(self._fav_panel, label=_("Re&name Station"))
		self._rename_btn.Enable(False)
		btn_row.Add(self._rename_btn, 0)

		sizer.Add(btn_row, 0, wx.LEFT | wx.BOTTOM, 5)

		# Second button row: export and import favourites.
		io_row = wx.BoxSizer(wx.HORIZONTAL)
		self._fav_export_btn = wx.Button(self._fav_panel, label=_("E&xport Favourites..."))
		io_row.Add(self._fav_export_btn, 0, wx.RIGHT, 6)
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
		filter_sizer.Add(wx.StaticText(self._all_panel, label=_("Sort:")),
		                 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._sort_cb = wx.ComboBox(
			self._all_panel,
			style=wx.CB_READONLY,
			choices=[_("Alphabetical"), _("By Rating")],
		)
		self._sort_cb.SetName(_("Sort:"))
		self._sort_cb.SetSelection(0)
		filter_sizer.Add(self._sort_cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)

		# Country combo
		filter_sizer.Add(wx.StaticText(self._all_panel, label=_("Country:")),
		                 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		_all_country_names = sorted(country_name(code) for code in _COUNTRY_NAMES)
		self._country_cb = wx.ComboBox(self._all_panel, style=wx.CB_READONLY, choices=[_("All")] + _all_country_names)
		self._country_cb.SetSelection(0)
		filter_sizer.Add(self._country_cb, 1)
		sizer.Add(filter_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# Result limit row
		limit_sizer = wx.BoxSizer(wx.HORIZONTAL)
		limit_sizer.Add(
			wx.StaticText(self._all_panel, label=_("Result limit per country:")),
			0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4,
		)
		_saved_limit = config.conf["freeradio"].get("result_limit", 1000)
		self._limit_spin = wx.SpinCtrl(
			self._all_panel, min=100, max=10000, initial=_saved_limit,
		)
		self._limit_spin.SetName(_("Result limit:"))
		self._limit_spin.SetMinSize((80, -1))
		limit_sizer.Add(self._limit_spin, 0, wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(limit_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		sizer.Add(wx.StaticText(self._all_panel, label=_("Search:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._search = wx.TextCtrl(self._all_panel)
		sizer.Add(self._search, 0, wx.EXPAND | wx.ALL, 5)

		hint = wx.StaticText(
			self._all_panel,
			label=_("Type to search · results update automatically"),
		)
		hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
		sizer.Add(hint, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)

		self._status = wx.StaticText(self._all_panel, label=_("Loading stations..."))
		sizer.Add(self._status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

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

		sizer.Add(wx.StaticText(self._rec_panel, label=_("Scheduled Recording")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		station_label = _("Station:")
		st_lbl = wx.StaticText(self._rec_panel, label=station_label)
		sizer.Add(st_lbl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# Filter field for the scheduled-recording station list.
		sizer.Add(
			wx.StaticText(self._rec_panel, label=_("Filter:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._sched_station_filter = wx.TextCtrl(self._rec_panel)
		self._sched_station_filter.SetName(_("Filter stations"))
		sizer.Add(self._sched_station_filter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# Use a ListBox instead of an editable ComboBox so screen readers
		# announce each item as the user navigates the list.
		self._sched_station_cb = wx.ListBox(self._rec_panel, style=wx.LB_SINGLE)
		self._sched_station_cb.SetMinSize((-1, 80))
		self._sched_station_cb.SetName(station_label)
		sizer.Add(self._sched_station_cb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		time_label = _("Start time (HH:MM):")
		sizer.Add(wx.StaticText(self._rec_panel, label=time_label),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._sched_time = wx.TextCtrl(self._rec_panel, value="")
		self._sched_time.SetName(time_label)
		sizer.Add(self._sched_time, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		dur_label = _("Duration (minutes):")
		sizer.Add(wx.StaticText(self._rec_panel, label=dur_label),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._sched_dur = wx.SpinCtrl(self._rec_panel, min=1, max=600, initial=60)
		self._sched_dur.SetName(dur_label)
		sizer.Add(self._sched_dur, 0, wx.LEFT | wx.RIGHT, 8)

		# --- Recurrence mode ---
		sizer.Add(
			wx.StaticText(self._rec_panel, label=_("Recurrence:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._sched_rec_once = wx.RadioButton(
			self._rec_panel,
			label=_("Record &once"),
			style=wx.RB_GROUP,
		)
		# Repeats every week on the selected active days, with no end —
		# the user removes it from the schedule list when they want it to
		# stop (see "&Remove Selected").
		self._sched_rec_indef = wx.RadioButton(
			self._rec_panel,
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
			self._rec_panel, label=_("Active days:"),
		)
		sizer.Add(self._sched_days_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		_day_labels = [
			_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
			_("Friday"), _("Saturday"), _("Sunday"),
		]
		self._sched_days_clb = nvdaControls.CustomCheckListBox(
			self._rec_panel, choices=_day_labels,
		)
		self._sched_days_clb.SetName(_("Active days:"))
		# No day pre-checked — the user picks explicitly each time.
		# An empty selection is treated as "every day" by the recorder.
		self._sched_days_clb.Checked = []
		self._sched_days_clb.Select(0)
		sizer.Add(self._sched_days_clb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		sizer.Add(wx.StaticText(self._rec_panel, label=_("Playback during recording:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._sched_mode_play = wx.RadioButton(
			self._rec_panel,
			label=_("Record while &listening (play and record simultaneously)"),
			style=wx.RB_GROUP,
		)
		self._sched_mode_rec  = wx.RadioButton(
			self._rec_panel,
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

		self._sched_add_btn = wx.Button(self._rec_panel, label=_("&Add to Schedule"))
		sizer.Add(self._sched_add_btn, 0, wx.ALL, 8)

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

		sizer.Add(wx.StaticText(self._timer_panel, label=_("Timer action:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._timer_rb_start = wx.RadioButton(
			self._timer_panel,
			label=_("&Start radio at specified time (alarm)"),
			style=wx.RB_GROUP,
		)
		self._timer_rb_stop = wx.RadioButton(
			self._timer_panel,
			label=_("St&op radio at specified time (sleep)"),
		)
		self._timer_rb_start.SetValue(True)
		sizer.Add(self._timer_rb_start, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		sizer.Add(self._timer_rb_stop,  0, wx.LEFT | wx.RIGHT | wx.TOP, 4)

		self._timer_time_label = wx.StaticText(
			self._timer_panel, label=_("Start time (HH:MM):")
		)
		sizer.Add(self._timer_time_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._timer_time = wx.TextCtrl(self._timer_panel, value="")
		self._timer_time.SetName(_("Start time (HH:MM):"))
		sizer.Add(self._timer_time, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		self._timer_station_label = wx.StaticText(
			self._timer_panel, label=_("Station:")
		)
		sizer.Add(self._timer_station_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# Filter field for the timer station list.
		sizer.Add(
			wx.StaticText(self._timer_panel, label=_("Filter:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._timer_station_filter = wx.TextCtrl(self._timer_panel)
		self._timer_station_filter.SetName(_("Filter stations"))
		sizer.Add(self._timer_station_filter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# Use a ListBox instead of an editable ComboBox so screen readers
		# announce each item as the user navigates the list.
		self._timer_station_cb = wx.ListBox(
			self._timer_panel, style=wx.LB_SINGLE
		)
		self._timer_station_cb.SetMinSize((-1, 80))
		self._timer_station_cb.SetName(_("Station:"))
		sizer.Add(self._timer_station_cb,    0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		self._timer_add_btn = wx.Button(self._timer_panel, label=_("&Add Timer"))
		sizer.Add(self._timer_add_btn, 0, wx.ALL, 8)

		sizer.Add(wx.StaticLine(self._timer_panel), 0, wx.EXPAND | wx.ALL, 4)

		sizer.Add(wx.StaticText(self._timer_panel, label=_("Pending timers:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._timer_list = wx.ListBox(self._timer_panel, style=wx.LB_SINGLE)
		sizer.Add(self._timer_list, 1, wx.EXPAND | wx.ALL, 8)

		self._timer_del_btn = wx.Button(self._timer_panel, label=_("&Remove Selected Timer"))
		self._timer_del_btn.Enable(False)
		sizer.Add(self._timer_del_btn, 0, wx.LEFT | wx.BOTTOM, 8)

		self._timer_panel.SetSizer(sizer)

		self._timer_rb_start.Bind(wx.EVT_RADIOBUTTON, self._on_timer_action_changed)
		self._timer_rb_stop.Bind(wx.EVT_RADIOBUTTON,  self._on_timer_action_changed)
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
		on_rec_or_timer = (sel in (2, 3, 4, 5, 6))
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
		elif sel == 4:
			wx.CallLater(0, self._refresh_liked_list)
		elif sel == 5:
			wx.CallLater(0, self._refresh_all_podcast_feeds)
		elif sel == 6:
			wx.CallLater(0, self._refresh_getem_library_list)
		if sel != 1 and hasattr(self, "_save_audio_btn"):
			self._save_audio_btn.Enable(False)

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
		if config.conf["freeradio"].get("disable_bass", False):
			return
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
		if config.conf["freeradio"].get("disable_bass", False):
			self._audio_devices_loading = False
			return
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
		if config.conf["freeradio"].get("disable_bass", False):
			event.Skip()
			return
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
		if config.conf["freeradio"].get("disable_bass", False):
			event.Skip()
			return
		idx = event.GetSelection()
		if idx != wx.NOT_FOUND:
			label = self._fx_choice.GetString(idx)
			is_checked = self._fx_choice.IsChecked(idx)
			ui.message(_("%(effect)s %(state)s") % {
				"effect": label,
				"state": _("enabled") if is_checked else _("disabled"),
			})
		event.Skip()

	def _on_fx_changed(self, event):
		"""Instantly apply all checked effects and save them in the config."""
		if config.conf["freeradio"].get("disable_bass", False):
			event.Skip()
			return
		idx = event.GetInt()
		is_checked = self._fx_choice.IsChecked(idx)
		label = self._fx_choice.GetString(idx)
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
		if config.conf["freeradio"].get("disable_bass", False):
			return
		if not (0 <= idx < len(self._fx_keys)):
			return
		is_checked = not self._fx_choice.IsChecked(idx)
		self._fx_choice.Check(idx, is_checked)
		label = self._fx_choice.GetString(idx)
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
		if config.conf["freeradio"].get("disable_bass", False):
			return
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
		if config.conf["freeradio"].get("disable_bass", False):
			return
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
		if config.conf["freeradio"].get("disable_bass", False):
			event.Skip()
			return
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
			ui.message(_("No favourites found"))
		else:
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
			_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
			_("Friday"), _("Saturday"), _("Sunday"),
		]

		self._sched_list.Clear()
		self._sched_index_map = []

		if not self._recorder:
			return

		for rec in self._recorder.get_schedules():
			station = rec.station.get("name", "?").strip()
			mode    = _("Record only") if rec.record_only else _("Listen and record")

			if rec.recurrence != "once":
				days = sorted(rec.active_days) if rec.active_days else list(range(7))
				if days == list(range(7)):
					when = _("Every day")
				else:
					when = _("Every %s") % ", ".join(_FULL_DAY_NAMES[d] for d in days)
				t    = rec.start_time.strftime("%H:%M")
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
			ui.message(_("No stations found"))
		else:
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
			ui.message(_("Please select a station"))
			return
		record_only = self._sched_mode_rec.GetValue()
		player_paths = {
			"vlc":       self._player._vlc_path,
			"potplayer": self._player._potplayer_path,
			"wmp":       self._player._wmp_path,
		}
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
					player_paths=player_paths,
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
			mode_str = _("Record only") if record_only else _("Listen and record")
			ui.message(_("Schedule added: %(station)s at %(time)s on %(dates)s (%(mode)s)") % {
				"station": station.get("name", "?"),
				"time":    time_str,
				"dates":   ", ".join(added_dates),
				"mode":    mode_str,
			})
			if all_conflict_names:
				wx.CallAfter(
					wx.MessageBox,
					_("Time conflict with: %(names)s. Switched to record-only mode.") % {
						"names": ", ".join(all_conflict_names)
					},
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
				player_paths=player_paths,
				record_only=record_only,
				recurrence=recurrence,
				active_days=active_days,
				max_occurrences=max_occurrences,
				output_folder=output_folder,
			)
			self._refresh_sched_list()
			record_only = _rec.record_only
			mode_str = _("Record only") if record_only else _("Listen and record")
			date_str = start.strftime("%d.%m.%Y")
			ui.message(_("Schedule added: %(station)s on %(date)s at %(time)s (%(mode)s)") % {
				"station": station.get("name", "?"), "date": date_str, "time": time_str, "mode": mode_str
			})
			if conflict_names:
				wx.CallAfter(
					wx.MessageBox,
					_("Time conflict with: %(names)s. Switched to record-only mode.") % {"names": conflict_names},
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
		dlg = EditScheduleDialog(
			self,
			rec,
			player_paths={
				"vlc":       self._player._vlc_path,
				"potplayer": self._player._potplayer_path,
				"wmp":       self._player._wmp_path,
			},
		)
		if dlg.ShowModal() == wx.ID_OK:
			updated = dlg.get_values()
			# Apply changes to the existing ScheduledRecording in-place
			rec.start_time       = updated["start_time"]
			rec.duration_minutes = updated["duration_minutes"]
			rec.recurrence       = updated["recurrence"]
			rec.active_days      = updated["active_days"]
			rec.max_occurrences  = updated["max_occurrences"]
			rec.record_only      = updated["record_only"]
			rec.output_folder    = updated["output_folder"]
			rec.fired            = False   # reset so scheduler picks it up again
			# Re-sort and persist
			self._recorder._scheduled.sort(key=lambda r: r.start_time)
			from . import recorder as _rec_mod
			_rec_mod._save_schedules(self._recorder._scheduled)
			self._refresh_sched_list()
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

		item_edit = menu.Append(wx.ID_ANY, _("&Edit Selected"))
		item_edit.Enable(has_selection)
		self.Bind(wx.EVT_MENU, self._on_sched_edit, item_edit)

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
			_("Top stations (%d)") % len(combined),
		)

	def _on_refresh_catalog(self, event):
		"""Manually re-sync the local station list cache from the Radio
		Browser API, instead of waiting for the periodic background refresh."""
		if self._manager.is_syncing():
			ui.message(_("Station list refresh already in progress"))
			return
		self._refresh_catalog_btn.Disable()
		ui.message(_("Refreshing station list from the server..."))
		self._status.SetLabel(_("Refreshing station list..."))

		def _done():
			wx.CallAfter(self._on_catalog_refreshed)

		self._manager.refresh_catalog_async(on_done=_done)

	def _on_catalog_refreshed(self):
		if not self:
			return
		self._refresh_catalog_btn.Enable()
		ui.message(_("Station list updated"))
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
		existing = set(self._country_cb.GetStrings()) - {_("All")}
		merged = sorted(existing | set(all_country_names))
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
			label = _("\"%(query)s\" in %(country)s: %(count)d") % {"query": text, "country": sel_country, "count": len(result)}
		elif sel_country:
			label = _("%(count)d stations in %(country)s") % {"count": len(result), "country": sel_country}
		elif text:
			label = _("\"%(query)s\": %(count)d") % {"query": text, "count": len(result)}
		else:
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
				label += " " + _("(%(shown)d of %(total)d shown — increase result limit to see more)") % {"shown": len(result), "total": total}
			else:
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
			filtered = [s for s in favs if _matches_query(s, query)]
		else:
			filtered = list(favs)

		# Cache filtered list so key handlers can map list indices back to stations.
		self._fav_filtered = filtered

		self._fav_list.Clear()
		for s in filtered:
			self._fav_list.Append(_station_label(s))

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
			filtered = [s for s in favs if _matches_query(s, query)]
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
			self._fav_list.Append(_station_label(s))
		self._update_fav_button()

	def _show_error(self):
		if not self:
			return
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

	def _on_country_char(self, event):
		"""Type-ahead search for the country combo box.

		Matches standard Windows Explorer list behaviour:
		- Single char: jump to first match; if already on a match, advance to next.
		- Multiple chars typed quickly (within 600 ms s): prefix search.
		"""
		key = event.GetUnicodeKey()
		if key == wx.WXK_NONE or key < 32:
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
		"""Core type-ahead dispatch shared by _on_list_char and _on_char_hook.

		Each listbox gets its own isolated state so that typing in one list
		never pollutes the search string, current index, or anchor of another.
		"""
		_list_state_map = {
			id(self._all_list):          "_list_search_all",
			id(self._fav_list):          "_list_search_fav",
			id(self._sched_list):        "_list_search_sched",
			id(self._sched_station_cb):  "_list_search_sched_station",
			id(self._timer_list):        "_list_search_timer",
			id(self._timer_station_cb):  "_list_search_timer_station",
			id(self._liked_list):        "_list_search_liked",
		}
		state_attr = _list_state_map.get(id(listbox), "_list_search_all")
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
		if key == wx.WXK_NONE or key < 32:
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
		(_on_save_feed_audio_profile), and GETEM library books
		(_on_save_getem_audio_profile). Reads the live volume/effects/EQ
		(and, when *allow_speed* is True, the live playback speed) straight
		off the current UI/player state and merges them into *existing*
		according to the option the user picks, so a choice that doesn't
		touch a given field (e.g. "Volume only") leaves whatever was
		already saved for the others untouched.

		Returns the new profile dict, or None if the user cancelled.
		"""
		choices = [
			# Translators: Option in audio profile save dialog: save volume level only
			_("Volume only"),
			# Translators: Option in audio profile save dialog: save effects (FX/EQ) only
			_("Effects only"),
			# Translators: Option in audio profile save dialog: save both volume and effects
			_("Volume and effects"),
		]
		if allow_speed:
			# Translators: Option in audio profile save dialog: save volume, effects, and the current playback speed
			choices.append(_("Volume, effects, and playback speed"))

		dlg = wx.SingleChoiceDialog(
			self,
			# Translators: Message shown in the audio profile save dialog
			_("What would you like to save in the audio profile?"),
			# Translators: Title of the audio profile save dialog
			_("Save Audio Profile"),
			choices,
		)
		# Pre-select the most complete option as the default.
		dlg.SetSelection(len(choices) - 1)
		result = dlg.ShowModal()
		sel = dlg.GetSelection()
		dlg.Destroy()

		if result != wx.ID_OK:
			return None

		# Read current UI/player values.
		vol = self._vol_spin.GetValue()
		checked = self._fx_choice.GetCheckedItems()
		active = [self._fx_keys[i] for i in checked if 0 <= i < len(self._fx_keys)]
		fx_str = ",".join(active) if active else "none"

		eq_gains = {}
		for band, _label, _default in self._eq_bands:
			eq_gains[band] = self._eq_spins[band].GetValue()

		# Build the profile dict based on the user's choice.
		existing = existing or {}
		if sel == 0:
			# Volume only: keep any existing effects/speed, replace volume.
			profile = dict(existing)
			profile["volume"] = vol
		elif sel == 1:
			# Effects only: keep any existing volume/speed, replace fx/eq_gains.
			profile = dict(existing)
			profile["fx"] = fx_str
			profile["eq_gains"] = eq_gains
		elif sel == 2:
			# Volume and effects: keep any existing speed, replace the rest.
			profile = dict(existing)
			profile["volume"] = vol
			profile["fx"] = fx_str
			profile["eq_gains"] = eq_gains
		else:
			# Volume, effects and speed: replace everything.
			profile = dict(existing)
			profile["volume"] = vol
			profile["fx"] = fx_str
			profile["eq_gains"] = eq_gains
			profile["speed"] = self._player.get_playback_rate()
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
		ui.message(_("Audio profile cleared for %(station)s") % {"station": name})
		self._update_save_audio_btn()


	def _on_fav_export(self, event=None):
		"""Show a file-save dialog and export favourites as JSON or M3U."""
		wildcard = _(
			"JSON favourites (*.json)|*.json"
			"|M3U playlist (*.m3u)|*.m3u"
		)
		dlg = wx.FileDialog(
			self,
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
				_("Export failed: %(error)s") % {"error": str(exc)},
				_("Export Error"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return

		count = len(self._manager.get_favorites())
		wx.MessageBox(
			ngettext(
				"Exported %(count)d station to:\n%(path)s",
				"Exported %(count)d stations to:\n%(path)s",
				count,
			) % {"count": count, "path": path},
			_("Export Complete"),
			wx.OK | wx.ICON_INFORMATION,
			self,
		)

	def _on_fav_import(self, event=None):
		"""Show a file-open dialog, ask merge/replace, then import favourites."""
		wildcard = _(
			"Supported files (*.json;*.m3u)|*.json;*.m3u"
			"|JSON favourites (*.json)|*.json"
			"|M3U playlist (*.m3u)|*.m3u"
		)
		dlg = wx.FileDialog(
			self,
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
			_(
				"How should the imported stations be added?\n\n"
				"Yes  — Merge: add new stations without removing existing ones.\n"
				"No   — Replace: clear the current list and load from file."
			),
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
				_("Import failed: %(error)s") % {"error": str(exc)},
				_("Import Error"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return
		except Exception as exc:
			wx.MessageBox(
				_("Could not read the file: %(error)s") % {"error": str(exc)},
				_("Import Error"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return

		self._refresh_fav_list()
		self._refresh_sched_stations()
		self._refresh_timer_stations()

		if merge:
			msg = ngettext(
				"Import complete: %(count)d new station added.",
				"Import complete: %(count)d new stations added.",
				added,
			) % {"count": added}
		else:
			total = len(self._manager.get_favorites())
			msg = ngettext(
				"Favourites replaced with %(count)d station from the file.",
				"Favourites replaced with %(count)d stations from the file.",
				total,
			) % {"count": total}
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
			_("Enter a new name for the station:"),
			_("Rename Station"),
			current_name,
		)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return

		new_name = dlg.GetValue().strip()
		dlg.Destroy()

		if not new_name:
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
			_notify(_("Radio paused"))
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

		rows = []
		name = s.get("name", "").strip()
		if name:
			rows.append((_("Station"), name))
		country_code = s.get("countrycode", "").strip()
		country      = s.get("country", "").strip()
		if country_code:
			display_country = _country_name(country_code)
			if country and country.lower() != display_country.lower():
				display_country = "%s (%s)" % (display_country, country)
			rows.append((_("Country"), display_country))
		elif country:
			rows.append((_("Country"), country))
		language = s.get("language", "").strip()
		if language:
			rows.append((_("Language"), language))
		tags = s.get("tags", "").strip()
		if tags:
			first_tags = ", ".join(t.strip() for t in tags.split(",")[:5] if t.strip())
			rows.append((_("Genre"), first_tags))
		bitrate = s.get("bitrate", 0)
		try:
			bitrate = int(bitrate)
		except (TypeError, ValueError):
			bitrate = 0
		codec = s.get("codec", "").strip()
		if bitrate and codec:
			rows.append((_("Format"), "%s, %d kbps" % (codec, bitrate)))
		elif bitrate:
			rows.append((_("Bitrate"), "%d kbps" % bitrate))
		elif codec:
			rows.append((_("Codec"), codec))
		homepage = s.get("homepage", "").strip()
		if homepage:
			rows.append((_("Website"), homepage))
		stream_url = (s.get("url_resolved") or s.get("url", "")).strip()
		if stream_url:
			rows.append((_("Stream URL"), stream_url))
		votes = s.get("votes", 0)
		try:
			votes = int(votes)
		except (TypeError, ValueError):
			votes = 0
		if votes:
			rows.append((_("Votes"), str(votes)))

		if not rows:
			ui.message(_("No station detail available"))
			return

		dlg = wx.Dialog(
			self,
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

		copy_btn = wx.Button(dlg, label=_("&Copy all to clipboard"))
		def _on_copy(evt):
			text = "\n".join("%s: %s" % (f, v) for f, v in rows)
			if wx.TheClipboard.Open():
				wx.TheClipboard.SetData(wx.TextDataObject(text))
				wx.TheClipboard.Close()
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

	def _on_delete_station(self, event):
		station, _idx = self._get_selected_station()
		if not station or not self._manager.is_favorite(station):
			return
		name = station.get("name", _("Unknown")).strip()
		msg = _("Do you want to delete the station \"%s\"?") % name
		dlg = wx.MessageDialog(
			self, msg, _("Delete Station"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		)
		result = dlg.ShowModal()
		dlg.Destroy()
		if result == wx.ID_YES:
			# Remember the deleted index so we can restore focus afterwards.
			deleted_idx = _idx
			self._manager.remove_favorite(station)
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
			ui.message(_("No station selected."))
			return
		url = station.get("url_resolved") or station.get("url") or ""
		if not url:
			ui.message(_("This station has no URL."))
			return
		name = station.get("name", "?").strip()
		ui.message(_("Checking stream for %s, please wait…") % name)

		def _worker():
			ok, detail = check_stream_url(url)
			wx.CallAfter(self._on_test_station_done, name, ok, detail)

		threading.Thread(target=_worker, daemon=True).start()

	def _on_test_station_done(self, name, ok, detail):
		if ok:
			ui.message(_("%(name)s: stream is reachable.") % {"name": name})
		else:
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
		item_details = menu.Append(wx.ID_ANY, _("Station Detai&ls"))
		self.Bind(wx.EVT_MENU, lambda e: self._show_station_details_for(station), item_details)

		menu.AppendSeparator()

		# --- Favourite management ---
		item_add_fav = menu.Append(wx.ID_ANY, _("Add to Fa&vorites"))
		item_add_fav.Enable(bool(station) and not is_fav)
		self.Bind(wx.EVT_MENU, self._on_toggle_favorite, item_add_fav)

		item_del_fav = menu.Append(wx.ID_ANY, _("&Delete Station"))
		item_del_fav.Enable(is_fav)
		self.Bind(wx.EVT_MENU, self._on_delete_station, item_del_fav)

		item_rename = menu.Append(wx.ID_ANY, _("Re&name Station"))
		item_rename.Enable(is_fav_tab and is_fav)
		self.Bind(wx.EVT_MENU, self._on_rename_station, item_rename)

		menu.AppendSeparator()

		# --- Audio profile ---
		item_save_profile = menu.Append(wx.ID_ANY, _("Save Audio Pr&ofile for This Station"))
		item_save_profile.Enable(is_fav_tab and is_fav)
		self.Bind(wx.EVT_MENU, self._on_save_audio_profile, item_save_profile)

		item_del_profile = menu.Append(wx.ID_ANY, _("Clear Audio Prof&ile"))
		item_del_profile.Enable(is_fav_tab and is_fav and has_profile)
		self.Bind(wx.EVT_MENU, self._on_clear_audio_profile, item_del_profile)

		menu.AppendSeparator()

		# --- Stream test ---
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
				_notify(_("Radio paused"))
			else:
				if self._player.has_media():
					self._player.resume()
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
			if focused == self._podcast_url:
				self._on_podcast_add(event)
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
			# For any other widget (country combo, search box, fav filter,
			# timer/sched/liked lists, SpinCtrl, RadioButton, etc.) Enter must
			# NOT bubble up to the default button (Play/Pause).  Consume it here.
			return

		if event.ControlDown() and not event.AltDown() and not event.ShiftDown():
			if key == wx.WXK_UP:
				vol = min(200, self._player.get_volume() + 5)
				self._player.set_volume(vol)
				config.conf["freeradio"]["volume"] = min(100, vol)
				_notify(_("Volume %d") % vol)
				self._vol_spin.SetValue(vol)
				return
			if key == wx.WXK_DOWN:
				vol = max(0, self._player.get_volume() - 5)
				self._player.set_volume(vol)
				config.conf["freeradio"]["volume"] = min(100, vol)
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
			# Numeric tab shortcuts: Alt+1..7 switch to the corresponding tab.
			# Tab order: 1=All Stations, 2=Favourites, 3=Recording, 4=Timer, 5=Liked Songs, 6=Podcasts, 7=Audio Books
			if ord("1") <= key <= ord("7"):
				tab_index = key - ord("1")   # 1->0, 2->1, ..., 7->6
				self._notebook.SetSelection(tab_index)
				self._on_tab_changed_index(tab_index)
				return

		# Type-ahead for lists where EVT_CHAR is unreliable because the native
		# Windows ListBox control can consume WM_CHAR before wxPython dispatches
		# EVT_CHAR.  _sched_list / _timer_list / _liked_list have no EVT_KEY_DOWN
		# handler (unlike _all_list / _fav_list), making them more susceptible.
		# Intercepting here — before event.Skip() — ensures the character is
		# consumed entirely by our handler and never reaches the native control.
		if (not event.ControlDown() and not event.AltDown()
				and focused in (self._sched_list, self._sched_station_cb,
				                self._timer_list, self._timer_station_cb,
				                self._liked_list)):
			ukey = event.GetUnicodeKey()
			if ukey != wx.WXK_NONE and ukey >= 32:
				ch = chr(ukey).lower()
			elif 32 <= key <= 126:
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
			ui.message(_("%s selected. Navigate to the target position and press comma again to drop.") % station_name)

		else:
			if self._moving_station_index == idx:
				self._moving_station_index = -1
				winsound.Beep(330, 150)  # Low tone: cancelled
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
				_notify(_("Radio paused"))
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
				_notify(_("Radio paused"))
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
			if self._del_btn.IsEnabled():
				self._on_delete_station(event)
		else:
			event.Skip()


	def _timer_action_changed_update(self):
		"""Show/hide station area and update label according to Start/Stop selection."""
		is_start = self._timer_rb_start.GetValue()
		self._timer_station_label.Show(is_start)
		# Also show/hide the filter field that sits between the label and the listbox.
		if hasattr(self, "_timer_station_filter"):
			self._timer_station_filter.Show(is_start)
		self._timer_station_cb.Show(is_start)
		lbl = _("Start time (HH:MM):") if is_start else _("Stop time (HH:MM):")
		self._timer_time_label.SetLabel(lbl)
		self._timer_time.SetName(lbl)
		self._timer_panel.Layout()

	def _on_timer_action_changed(self, event):
		self._timer_action_changed_update()
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
		self._timer_list.Clear()
		if self._timer_manager:
			for entry in self._timer_manager.get_timers():
				entry_id, dt, action, label, notify_cb = entry
				time_str = dt.strftime("%d.%m.%Y %H:%M")
				is_alarm = (label != _("Sleep timer") and label != "Sleep timer")
				if is_alarm:
					text = _("Alarm %(time)s — %(station)s") % {
						"time": time_str, "station": label
					}
				else:
					text = _("Sleep %(time)s") % {"time": time_str}
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
			ui.message(_("No stations found"))
		else:
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
			ui.message(_("Invalid time format. Use HH:MM"))
			self._timer_time.SetFocus()
			return

		now  = datetime.datetime.now()
		when = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
		if when <= now:
			when    += datetime.timedelta(days=1)
			next_day = True
		else:
			next_day = False

		is_start = self._timer_rb_start.GetValue()

		# Duplicate check: warn and abort if any timer already exists at the
		# same HH:MM, regardless of kind (alarm and sleep timers conflict too).
		existing = self._timer_manager.get_timers()
		for _eid, dt, _action, label, _cb in existing:
			meta = getattr(_action, "_timer_meta", None)
			if meta and dt.hour == when.hour and dt.minute == when.minute:
				ui.message(
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
				ui.message(_("Please select a station"))
				return
			self._timer_manager.add_alarm(
				start_dt=when,
				station=station,
				play_callback=self._play_callback,
			)
			name = station.get("name", "?").strip()
			msg  = _("Alarm added: %(station)s at %(time)s") % {
				"station": name,
				"time":    when.strftime("%H:%M"),
			}
		else:
			self._timer_manager.add_sleep(stop_dt=when)
			msg = _("Sleep timer added: radio will stop at %s") % when.strftime("%H:%M")

		if next_day:
			msg += "  " + _("(tomorrow)")
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
			wx.StaticText(self._liked_panel, label=_("Liked Songs:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)

		# Filter field for the liked songs list.
		sizer.Add(
			wx.StaticText(self._liked_panel, label=_("Filter:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._liked_filter = wx.TextCtrl(self._liked_panel)
		self._liked_filter.SetName(_("Filter liked songs"))
		sizer.Add(self._liked_filter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		self._liked_list = wx.ListBox(self._liked_panel, style=wx.LB_SINGLE)
		self._liked_list.SetName(_("Liked Songs"))
		sizer.Add(self._liked_list, 1, wx.EXPAND | wx.ALL, 5)

		btn_row = wx.BoxSizer(wx.HORIZONTAL)

		self._liked_spotify_btn = wx.Button(
			self._liked_panel, label=_("Play on &Spotify")
		)
		self._liked_youtube_btn = wx.Button(
			self._liked_panel, label=_("Play on Y&ouTube")
		)
		self._liked_lyrics_btn = wx.Button(
			self._liked_panel, label=_("Show &Lyrics")
		)
		self._liked_remove_btn = wx.Button(
			self._liked_panel, label=_("Re&move")
		)
		self._liked_refresh_btn = wx.Button(
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

		self._refresh_liked_list()

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
					self._liked_list.Append(line)
				if not lines:
					self._liked_list.Append(_("No results found."))
			except Exception as e:
				self._liked_list.Append(_("Could not read file: %s") % str(e))
		else:
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
			if self._liked_list.GetString(i) not in (_("No liked songs yet."), _("No results found."))
		)
		if count == 0:
			ui.message(_("No results found"))
		else:
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
				_("No liked songs yet."),
			)
		self._liked_spotify_btn.Enable(real_song)
		self._liked_youtube_btn.Enable(real_song)
		self._liked_lyrics_btn.Enable(real_song)
		self._liked_remove_btn.Enable(real_song)
		event.Skip()

	def _get_liked_selection(self):
		"""Return the selected song string, or None."""
		idx = self._liked_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return None
		text = self._liked_list.GetString(idx)
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
		"""Liked Songs list — Delete key triggers Remove button when enabled;
		Applications key / Shift+F10 opens the context menu."""
		key = event.GetKeyCode()
		if key == wx.WXK_DELETE:
			if self._liked_remove_btn.IsEnabled():
				self._on_liked_remove(event)
			return
		if key == wx.WXK_WINDOWS_MENU or (key == wx.WXK_F10 and event.ShiftDown()):
			self._show_liked_context_menu()
			return
		event.Skip()

	def _show_liked_context_menu(self):
		"""Context menu for the selected item in the Liked Songs list.

		Mirrors the existing action buttons on the tab; items are disabled
		when no real song is selected so screen readers still announce a
		consistent menu.
		"""
		song = self._get_liked_selection()

		menu = wx.Menu()

		item_spotify = menu.Append(wx.ID_ANY, _("Play on &Spotify"))
		item_spotify.Enable(bool(song))
		self.Bind(wx.EVT_MENU, self._on_liked_spotify, item_spotify)

		item_youtube = menu.Append(wx.ID_ANY, _("Play on Y&ouTube"))
		item_youtube.Enable(bool(song))
		self.Bind(wx.EVT_MENU, self._on_liked_youtube, item_youtube)

		item_lyrics = menu.Append(wx.ID_ANY, _("Show &Lyrics"))
		item_lyrics.Enable(bool(song))
		self.Bind(wx.EVT_MENU, self._on_liked_lyrics, item_lyrics)

		menu.AppendSeparator()

		item_remove = menu.Append(wx.ID_ANY, _("Re&move"))
		item_remove.Enable(bool(song))
		self.Bind(wx.EVT_MENU, self._on_liked_remove, item_remove)

		menu.AppendSeparator()

		item_refresh = menu.Append(wx.ID_ANY, _("R&efresh"))
		self.Bind(wx.EVT_MENU, self._on_liked_refresh, item_refresh)

		self.PopupMenu(menu, self._liked_list.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _on_liked_remove(self, event):
		idx = self._liked_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		song = self._liked_list.GetString(idx)
		if song in (_("No liked songs yet."), _("No results found.")):
			return
		# Ask for confirmation before removing the song.
		dlg = wx.MessageDialog(
			self,
			_("Do you want to remove \"%s\" from liked songs?") % song,
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
			ui.message(_("Could not remove song: %s") % str(e))
			return
		# Remember the deleted index so we can restore focus afterwards.
		deleted_idx = idx
		self._refresh_liked_list()
		ui.message(_("Removed: %s") % song)
		# After deletion keep focus on the next item (or the last one if the
		# deleted item was at the end); move to Refresh button if the list is empty.
		count = self._liked_list.GetCount()
		real_song_count = sum(
			1 for i in range(count)
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
		ui.message(_("Liked songs list refreshed"))

	def _on_liked_lyrics(self, event):
		song = self._get_liked_selection()
		if not song:
			return
		self._liked_lyrics_btn.Enable(False)
		ui.message(_("Fetching lyrics…"))
		from . import lyricsService

		def _on_result(lyrics, error):
			wx.CallAfter(self._liked_lyrics_btn.Enable, True)
			if lyrics:
				wx.CallAfter(self._show_lyrics_dialog, song, lyrics)
			else:
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
		search_sizer.Add(wx.StaticText(panel, label=_("Search:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._podcast_search = wx.TextCtrl(panel)
		self._podcast_search.SetName(_("Search podcasts. Press enter to search"))
		search_sizer.Add(self._podcast_search, 1, wx.EXPAND)
		sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 8)

		# --- Search results list ---
		# Hidden until a search is actually performed - see
		# _on_podcast_search() and _set_podcast_results_visible(). Keeping
		# it out of the way when there's nothing to search for avoids an
		# empty "Search results" list/label sitting in the tab from the
		# moment it's opened.
		self._podcast_results_label = wx.StaticText(panel, label=_("Search results:"))
		sizer.Add(self._podcast_results_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._podcast_results = wx.ListBox(panel, style=wx.LB_SINGLE)
		self._podcast_results.SetName(_("Podcast search results"))
		self._podcast_results.SetMinSize((-1, 80))
		sizer.Add(self._podcast_results, 0, wx.EXPAND | wx.ALL, 8)

		# --- Preview episodes for the selected search result ---
		# Lets the user browse a feed's episodes before deciding to subscribe.
		# Subscribing itself is done via the search results' context menu
		# (Applications key / Shift+F10), not a button. Hidden alongside the
		# search results list until a search has been performed.
		self._podcast_preview_label = wx.StaticText(panel, label=_("Episodes in selected result:"))
		sizer.Add(self._podcast_preview_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._podcast_preview_list = wx.ListBox(panel, style=wx.LB_SINGLE)
		self._podcast_preview_list.SetName(_("Episode preview for selected search result"))
		self._podcast_preview_list.SetMinSize((-1, 80))
		sizer.Add(self._podcast_preview_list, 0, wx.EXPAND | wx.ALL, 8)
		self._podcast_search_sizer = sizer
		self._set_podcast_results_visible(False)

		# --- Separator ---
		sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 4)

		# --- Add feed row (manual) ---
		add_sizer = wx.BoxSizer(wx.HORIZONTAL)
		add_sizer.Add(wx.StaticText(panel, label=_("Or enter podcast URL:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._podcast_url = wx.TextCtrl(panel)
		self._podcast_url.SetName(_("Podcast URL"))
		add_sizer.Add(self._podcast_url, 1, wx.EXPAND | wx.RIGHT, 4)
		self._podcast_add_btn = wx.Button(panel, label=_("&Add Feed"))
		add_sizer.Add(self._podcast_add_btn, 0)
		sizer.Add(add_sizer, 0, wx.EXPAND | wx.ALL, 8)

		# --- Subscriptions list ---
		sizer.Add(wx.StaticText(panel, label=_("Subscriptions:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._podcast_list = wx.ListBox(panel, style=wx.LB_SINGLE)
		self._podcast_list.SetName(_("Podcast subscriptions"))
		self._podcast_list.SetMinSize((-1, 80))
		sizer.Add(self._podcast_list, 0, wx.EXPAND | wx.ALL, 8)

		# --- Selected feed details (read-only, reachable by Tab right
		# after the subscriptions list) ---
		self._feed_details = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
		self._feed_details.SetName(_("Feed details"))
		self._feed_details.SetMinSize((-1, 60))
		sizer.Add(self._feed_details, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		# --- Episode filter ---
		ep_filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
		ep_filter_sizer.Add(wx.StaticText(panel, label=_("Filter:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._episode_filter = wx.TextCtrl(panel)
		self._episode_filter.SetName(_("Filter episodes by title or number"))
		ep_filter_sizer.Add(self._episode_filter, 1, wx.EXPAND)
		sizer.Add(ep_filter_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		# --- Episodes list ---
		sizer.Add(wx.StaticText(panel, label=_("Episodes:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._episode_list = wx.ListBox(panel, style=wx.LB_SINGLE)
		self._episode_list.SetName(_("Podcast episodes"))
		self._episode_list.SetMinSize((-1, 120))
		sizer.Add(self._episode_list, 1, wx.EXPAND | wx.ALL, 8)

		# --- Selected episode details (read-only, reachable by Tab right
		# after the episode list) ---
		self._episode_details = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
		self._episode_details.SetName(_("Episode details"))
		self._episode_details.SetMinSize((-1, 60))
		sizer.Add(self._episode_details, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		# Episode buttons — playing an episode is available via Enter/Space
		# on the list and via the context menu, so there's no separate
		# "Play Episode" button here.
		ep_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self._episode_download_btn = wx.Button(panel, label=_("&Download Episode"))
		self._episode_download_btn.Enable(False)
		ep_btn_sizer.Add(self._episode_download_btn, 0)
		sizer.Add(ep_btn_sizer, 0, wx.LEFT | wx.BOTTOM, 8)

		panel.SetSizer(sizer)

		# --- Bind events ---
		self._podcast_search.Bind(wx.EVT_KEY_DOWN, self._on_podcast_search_key)
		self._podcast_results.Bind(wx.EVT_LISTBOX, self._on_podcast_result_selected)
		self._podcast_add_btn.Bind(wx.EVT_BUTTON, self._on_podcast_add)
		self._podcast_list.Bind(wx.EVT_LISTBOX, self._on_podcast_selected)
		self._podcast_list.Bind(wx.EVT_CHAR, self._on_list_char)
		self._podcast_list.Bind(wx.EVT_KEY_DOWN, self._on_podcast_list_key)
		self._episode_filter.Bind(wx.EVT_TEXT,     self._on_episode_filter_changed)
		self._episode_filter.Bind(wx.EVT_KEY_DOWN, self._on_episode_filter_key)
		self._episode_list.Bind(wx.EVT_LISTBOX, self._on_episode_selected)
		self._episode_list.Bind(wx.EVT_CHAR, self._on_list_char)
		self._episode_list.Bind(wx.EVT_KEY_DOWN, self._on_episode_key)
		self._episode_download_btn.Bind(wx.EVT_BUTTON, self._on_episode_download)

		self._podcast_url.Bind(wx.EVT_KEY_DOWN, self._on_podcast_url_key)

		self._refresh_podcast_list()

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
		ui.message(_("Podcast feeds updated."))

	def _on_podcast_url_key(self, event):
		if event.GetKeyCode() == wx.WXK_RETURN:
			self._on_podcast_add(event)
		else:
			event.Skip()

	def _on_podcast_add(self, event):
		url = self._podcast_url.GetValue().strip()
		if not url:
			ui.message(_("Please enter a podcast URL."))
			return
		if not url.startswith(("http://", "https://")):
			ui.message(_("URL must start with http:// or https://"))
			return

		self._podcast_add_btn.Disable()
		self._podcast_url.Disable()
		ui.message(_("Fetching podcast feed..."))

		def _do_add():
			feed, error = self._podcast_manager.add_feed(url)
			wx.CallAfter(self._on_podcast_add_done, feed, error)

		threading.Thread(target=_do_add, daemon=True).start()

	def _on_podcast_add_done(self, feed, error):
		self._podcast_add_btn.Enable()
		self._podcast_url.Enable()
		if error:
			ui.message(_("Could not add feed: %s") % error)
			return
		self._podcast_url.SetValue("")
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
		ui.message(_("Audio profile saved for %(feed)s") % {"feed": feed.title})

	def _on_clear_feed_audio_profile(self, event):
		"""Remove the saved audio profile from the selected podcast feed."""
		feed = self._get_selected_podcast_feed()
		if not feed or not feed.audio_profile:
			return
		feed.audio_profile = None
		self._podcast_manager._save()
		ui.message(_("Audio profile cleared for %(feed)s") % {"feed": feed.title})

	def _format_feed_details(self, feed):
		"""Build the text shown in the read-only feed-details field for the
		given PodcastFeed (or "" if none is selected).
		"""
		if feed is None:
			return ""
		lines = [feed.title]
		if feed.author:
			lines.append(_("By: %s") % feed.author)
		count = len(feed.episodes)
		lines.append(ngettext("%d episode", "%d episodes", count) % count)
		if feed.description:
			description = self._html_to_text(feed.description)
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
			ui.message(_("No episodes found"))
		else:
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

		ui.message(_("Refreshing feed: %s") % feed.title)

		def _do_refresh():
			updated_feed, error = self._podcast_manager.refresh_feed(feed.url)
			wx.CallAfter(self._on_podcast_refresh_done, updated_feed, error)

		threading.Thread(target=_do_refresh, daemon=True).start()

	def _on_podcast_refresh_done(self, feed, error):
		if error:
			ui.message(_("Refresh failed: %s") % error)
			return
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
			_("Do you want to remove the feed \"%s\"?") % feed.title,
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
		rather than assuming a particular strftime format.
		"""
		if ep is None:
			return ""
		lines = [ep.title]
		if ep.published:
			lines.append(_("Published: %s") % ep.published)
		if ep.duration:
			lines.append(_("Duration: %s") % ep.duration)
		if ep.description:
			description = self._html_to_text(ep.description)
			if description:
				lines.append("")
				lines.append(description)
		lines.append("")
		lines.append(ep.url)
		return "\n".join(lines)

	def _html_to_text(self, text):
		"""Strip HTML tags and decode entities from an RSS/Atom description.

		podcast.py stores <description>/<atom:summary> as-is, which is
		commonly raw HTML ("<p>...</p>", "&amp;", etc.) - not something a
		screen reader should read literally. Deliberately simple (no
		external HTML parser dependency): drop tags, decode entities,
		collapse the blank lines that tends to leave behind.
		"""
		if not text:
			return text
		text = re.sub(r"<[^>]+>", " ", text)
		text = unescape(text)
		text = re.sub(r"[ \t]+", " ", text)
		text = re.sub(r"\n\s*\n+", "\n\n", text)
		return text.strip()

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
			if feed.audio_profile:
				station_dict["station_audio"] = feed.audio_profile
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
			ui.message(_("File already exists: %s") % filename)
			return

		ui.message(_("Downloading: %s") % episode.title)
		self._episode_download_btn.Disable()

		def _do_download():
			try:
				podcast.download_episode_file(episode.url, out_path)
				wx.CallAfter(ui.message, _("Download complete: %s") % filename)
			except Exception as e:
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
			ui.message(_("Please enter a search term."))
			return

		self._set_podcast_results_visible(True)
		self._podcast_search.Disable()
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
			ui.message(_("No podcasts found."))
			return
		for item in results:
			label = f"{item['title']} — {item['artist']}"
			self._podcast_results.Append(label)
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
		if idx == wx.NOT_FOUND:
			return
		results = getattr(self, "_podcast_search_results", [])
		if idx >= len(results):
			return
		item = results[idx]
		feed_url = item.get('feedUrl')
		if not feed_url:
			self._podcast_preview_list.Append(_("This podcast has no feed URL."))
			return

		self._podcast_preview_fetch_id = getattr(self, "_podcast_preview_fetch_id", 0) + 1
		fetch_id = self._podcast_preview_fetch_id
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
			self._podcast_preview_list.Append(_("No episodes found."))
			return
		self._podcast_preview_episodes = feed.episodes
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
			ui.message(_("This podcast has no feed URL."))
			return

		ui.message(_("Adding feed..."))

		def _do_add():
			feed, error = self._podcast_manager.add_feed(feed_url)
			wx.CallAfter(self._on_podcast_subscribe_from_results_done, feed, error)

		threading.Thread(target=_do_add, daemon=True).start()

	def _on_podcast_subscribe_from_results_done(self, feed, error):
		if error:
			ui.message(_("Could not add feed: %s") % error)
			return
		ui.message(_("Feed added: %s") % feed.title)
		self._refresh_podcast_list()

	def _play_prev_episode(self):
		"""Play the previous episode (select the previous item in the episode list, move
		focus to it, and play)."""
		idx = self._episode_list.GetSelection()
		if idx <= 0:
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

		item_refresh = menu.Append(wx.ID_ANY, _("&Refresh Feed"))
		self.Bind(wx.EVT_MENU, self._on_podcast_refresh, item_refresh)

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

		item_copy_url = menu.Append(wx.ID_ANY, _("&Copy Feed URL"))
		self.Bind(wx.EVT_MENU, lambda e: self._copy_to_clipboard(feed.url), item_copy_url)

		self.PopupMenu(menu, self._podcast_list.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

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

		item_play = menu.Append(wx.ID_ANY, _("&Play Episode"))
		self.Bind(wx.EVT_MENU, self._on_episode_play, item_play)

		item_download = menu.Append(wx.ID_ANY, _("&Download Episode"))
		self.Bind(wx.EVT_MENU, self._on_episode_download, item_download)

		menu.AppendSeparator()

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
			ui.message(_("Copied to clipboard"))

	# ------------------------------------------------------------------ #
	# Audio Books Tab (GETEM e-library)
	# ------------------------------------------------------------------ #

	def _build_audiobooks_tab(self):
		"""Audio book search and library tab. Search UI is modeled on the
		Podcasts tab above: a single search field, a results list that
		only appears once a search has actually been run, and adding an
		item to the library is done from the results list's context menu
		rather than a dedicated button - see _show_getem_result_context_menu().
		"""
		panel = self._getem_panel
		sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Search row ---
		search_sizer = wx.BoxSizer(wx.HORIZONTAL)
		search_sizer.Add(wx.StaticText(panel, label=_("Search:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		self._getem_search = wx.TextCtrl(panel)
		self._getem_search.SetName(_("Search GETEM audio books by title, author, narrator, subject, or publisher. Press enter to search"))
		search_sizer.Add(self._getem_search, 1, wx.EXPAND)
		sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 8)

		# --- Search results list ---
		# Hidden until a search is actually performed, same as the
		# Podcasts tab's search results - see _set_getem_results_visible().
		self._getem_results_label = wx.StaticText(panel, label=_("Search results:"))
		sizer.Add(self._getem_results_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._getem_results = wx.ListBox(panel, style=wx.LB_SINGLE)
		self._getem_results.SetName(_("GETEM search results"))
		self._getem_results.SetMinSize((-1, 100))
		sizer.Add(self._getem_results, 0, wx.EXPAND | wx.ALL, 8)
		self._getem_search_sizer = sizer
		self._set_getem_results_visible(False)

		# --- Separator ---
		sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 4)

		# --- Library list ---
		sizer.Add(wx.StaticText(panel, label=_("My Library:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._getem_library_ctrl = wx.ListBox(panel, style=wx.LB_SINGLE)
		self._getem_library_ctrl.SetName(_("Audio books library"))
		self._getem_library_ctrl.SetMinSize((-1, 120))
		sizer.Add(self._getem_library_ctrl, 1, wx.EXPAND | wx.ALL, 8)

		# --- Selected item details (read-only, reachable by Tab right
		# after either list) ---
		self._getem_details = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
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

		self._refresh_getem_library_list()
		self._sync_getem_now_playing_from_player()

	def _sync_getem_now_playing_from_player(self):
		"""If a GETEM audio book chapter is already playing by the time this
		tab is first built - e.g. it was resumed automatically on NVDA
		startup, see GlobalPlugin._resume_last_station()/
		_rebuild_getem_resume_url() in playbackCoreMixin.py - then
		_getem_now_playing wouldn't otherwise get set until the user
		manually starts something from this tab, leaving F3/F4 book/chapter
		navigation (_play_prev/next_getem_book/chapter) with nothing to
		work from even though something is audibly playing. Reconstructs
		it from the player's own current station dict instead."""
		current = self._player.get_current_station() or {}
		if "audiobook" not in current.get("tags", ""):
			return
		detail_url = current.get("getem_detail_url")
		if not detail_url:
			return
		book = self._getem_library.get_book_by_key(detail_url)
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
		"""Listbox label for a GetemBook: title, author, and its format
		(the user-facing "type" of the source - human/computer narration,
		audio description, radio theatre, etc.)."""
		parts = [book.title]
		if book.author:
			parts.append(book.author)
		label = " — ".join(parts)
		if book.format_label:
			label += f" ({book.format_label})"
		return label

	def _format_getem_details(self, book):
		if book is None:
			return ""
		lines = [book.title]
		if book.author:
			lines.append(_("Author: %s") % book.author)
		if book.narrator:
			lines.append(_("Narrator: %s") % book.narrator)
		if book.publisher:
			lines.append(_("Publisher: %s") % book.publisher)
		if book.format_label:
			lines.append(_("Type: %s") % book.format_label)
		if book.chapters:
			lines.append(ngettext("%d part", "%d parts", len(book.chapters)) % len(book.chapters))
		if book.description:
			description = self._html_to_text(book.description)
			if description:
				lines.append("")
				lines.append(description)
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
			ui.message(_("Please enter a search term."))
			return

		self._set_getem_results_visible(True)
		self._getem_search.Disable()
		ui.message(_("Searching GETEM..."))

		self._getem_search_id = getattr(self, "_getem_search_id", 0) + 1
		search_id = self._getem_search_id

		def _do_search():
			books, error = getem.search_getem(query)
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
			ui.message(_("No audio books found."))
			return
		for book in books:
			self._getem_results.Append(self._format_getem_result_label(book))
		ui.message(_("%d audio books found.") % len(books))
		self._getem_results.SetSelection(0)
		self._on_getem_result_selected(None)

	def _on_getem_result_selected(self, event):
		idx = self._getem_results.GetSelection()
		results = getattr(self, "_getem_search_results", None) or []
		book = results[idx] if idx != wx.NOT_FOUND and idx < len(results) else None
		self._getem_details.ChangeValue(self._format_getem_details(book))

	def _on_getem_add_to_library(self, event):
		"""Adds the selected search result to the library. Reached via the
		search results' context menu or Enter - there is no separate button."""
		idx = self._getem_results.GetSelection()
		results = getattr(self, "_getem_search_results", None) or []
		if idx == wx.NOT_FOUND or idx >= len(results):
			return
		book = results[idx]
		if self._getem_library.is_in_library(book):
			ui.message(_("This audio book is already in your library."))
			return
		if self._getem_library.add_book(book):
			ui.message(_("Added to library: %s") % book.title)
			self._refresh_getem_library_list()
		else:
			ui.message(_("Could not add to library."))

	def _show_getem_result_context_menu(self):
		"""Context menu for the selected item in the search results list."""
		idx = self._getem_results.GetSelection()
		results = getattr(self, "_getem_search_results", None) or []
		if idx == wx.NOT_FOUND or idx >= len(results):
			return
		book = results[idx]

		menu = wx.Menu()
		item_add = menu.Append(wx.ID_ANY, _("&Add to Library"))
		self.Bind(wx.EVT_MENU, self._on_getem_add_to_library, item_add)

		menu.AppendSeparator()

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
		"""Populate the library listbox, preserving whichever book is
		selected at the moment this runs (mirrors _refresh_podcast_list())."""
		prev_key = None
		idx = self._getem_library_ctrl.GetSelection()
		books_before = self._getem_library.get_books()
		if idx != wx.NOT_FOUND and idx < len(books_before):
			prev_key = books_before[idx].identity_key()

		self._getem_library_ctrl.Clear()
		books = self._getem_library.get_books()
		for book in books:
			self._getem_library_ctrl.Append(self._format_getem_result_label(book))

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
		books = self._getem_library.get_books()
		book = books[idx] if idx != wx.NOT_FOUND and idx < len(books) else None
		self._getem_details.ChangeValue(self._format_getem_details(book))

	def _on_getem_library_key(self, event):
		key = event.GetKeyCode()
		if key == wx.WXK_DELETE:
			# Delete / Shift+Delete both remove the selected book from the
			# library — the keycode is the same either way.
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
				_notify(_("Paused"))
			else:
				self._on_getem_play(None)
			return
		event.Skip()

	def _on_getem_play(self, event):
		idx = self._getem_library_ctrl.GetSelection()
		books = self._getem_library.get_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		self._play_getem_book(books[idx])

	def _play_getem_book(self, book):
		"""Resolves (if needed) and starts playing *book*, resuming from
		whichever part it was last left off on (book.last_chapter_index -
		see getem.GetemLibrary.mark_progress()). Every part of a
		multi-part work is fed to the player as the same played item - see
		getem.GetemBook.to_dict() and _start_getem_chapter() - so it gets
		the same resume/seek/speed-change handling a podcast episode does,
		without a separate per-part row anywhere in the UI: the book is
		one source, not one row per part."""
		if book.chapters:
			start_idx = min(max(book.last_chapter_index, 0), len(book.chapters) - 1)
			self._start_getem_chapter(book, start_idx)
			return

		ui.message(_("Loading: %s") % book.title)

		def _do_resolve():
			resolved_book, error = getem.resolve_media(book)
			wx.CallAfter(self._on_getem_media_resolved, resolved_book, error)

		threading.Thread(target=_do_resolve, daemon=True).start()

	def _on_getem_media_resolved(self, book, error):
		if error:
			ui.message(error)
			return
		if self._getem_library.is_in_library(book):
			# Persist the now-resolved chapter list so this work doesn't
			# need re-resolving (and re-logging-in) the next time it's played.
			self._getem_library.save()
		start_idx = min(max(book.last_chapter_index, 0), len(book.chapters) - 1) if book.chapters else 0
		self._start_getem_chapter(book, start_idx)

	def _start_getem_chapter(self, book, chapter_index):
		"""Plays the given part by pointing the player at the local GETEM
		streaming proxy (see getem.get_stream_url()) rather than
		downloading the whole chapter first - playback starts as soon as
		the first bytes come back, the same as a normal podcast episode.
		A remote GETEM URL can't be handed to the player directly: it only
		works with our Python session's login cookie, which the audio
		backend (BASS, in its own subprocess) has no way to send when it
		opens a URL on its own - the proxy is what supplies that cookie
		on its behalf."""
		if chapter_index < 0 or chapter_index >= len(book.chapters):
			return
		self._getem_now_playing = (book, chapter_index)
		self._getem_library.mark_progress(book, chapter_index)
		chapter = book.chapters[chapter_index]

		ui.message(_("Loading: %s") % chapter["title"])

		stream_url = getem.get_stream_url(chapter["url"], referer=book.detail_url)
		station_dict = book.to_dict()
		# Apply the book-wide audio profile (volume/effects/EQ and,
		# optionally, playback speed) if one was saved - see
		# _on_save_getem_audio_profile() and playbackCoreMixin._play_station().
		if book.audio_profile:
			station_dict["station_audio"] = book.audio_profile
		station_dict["name"] = chapter["title"]
		station_dict["url"] = stream_url
		station_dict["url_resolved"] = stream_url
		# Carried through to config.conf["freeradio"]["last_station_getem_chapter_index"]
		# by playbackCoreMixin._play_station() - lets a "resume last
		# station" on the next NVDA startup know which part to rebuild a
		# fresh proxy URL for (see GlobalPlugin._rebuild_getem_resume_url()),
		# since the proxy URL saved this session won't still be valid then.
		station_dict["getem_chapter_index"] = chapter_index
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
		terms of - see GetemBook.last_chapter_index."""
		books = self._getem_library.get_books()
		if not books:
			ui.message(_("Library is empty"))
			return
		idx = self._getem_current_book_index(books)
		if idx <= 0:
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
		_play_next_getem_chapter(), and the primary F4 action on this tab."""
		books = self._getem_library.get_books()
		if not books:
			ui.message(_("Library is empty"))
			return
		idx = self._getem_current_book_index(books)
		if idx >= len(books) - 1:
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
		books = self._getem_library.get_books()
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
				ui.message(_("Finished: %s") % book.title)
			else:
				ui.message(_("Already at last part"))
			return
		if not auto:
			self._focus_getem_library_row(book)
		self._start_getem_chapter(book, idx + 1)

	def _on_playback_finished(self, station):
		"""Called (via radioPlayer.RadioPlayer.on_podcast_finished, wired up
		alongside on_podcast_progress_saved/on_device_lost) when whatever
		was playing reached its end on its own - as opposed to being paused
		or stopped by the user. For a GETEM audio book part, this is the cue
		to automatically move on to the next part; regular podcast episodes
		are left as-is (the user only asked for auto-advance on audio
		books) and are still advanced manually via _play_next_episode()."""
		if not station or "audiobook" not in station.get("tags", ""):
			return
		playing = getattr(self, "_getem_now_playing", None)
		if not playing:
			return
		book, idx = playing
		# Make sure the finished item still belongs to the book we think is
		# loaded - e.g. the user could have already skipped away from it by
		# hand right as it ended.
		if book.detail_url != station.get("getem_detail_url"):
			return
		self._play_next_getem_chapter(auto=True)

	def _show_getem_library_context_menu(self):
		"""Context menu for the selected item in the library list: play,
		copy the URL, save/clear its audio profile, or remove from the library."""
		idx = self._getem_library_ctrl.GetSelection()
		books = self._getem_library.get_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		book = books[idx]

		menu = wx.Menu()

		item_play = menu.Append(wx.ID_ANY, _("&Play Media"))
		self.Bind(wx.EVT_MENU, self._on_getem_play, item_play)

		menu.AppendSeparator()

		item_download = menu.Append(wx.ID_ANY, _("&Download Book"))
		self.Bind(wx.EVT_MENU, lambda e: self._download_getem_book(book), item_download)

		menu.AppendSeparator()

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

		item_remove = menu.Append(wx.ID_ANY, _("&Remove from the Library"))
		self.Bind(wx.EVT_MENU, self._on_getem_remove_from_library, item_remove)

		self.PopupMenu(menu, self._getem_library_ctrl.GetScreenPosition() - self.GetScreenPosition())
		menu.Destroy()

	def _on_save_getem_audio_profile(self, event):
		"""Save an audio profile (volume/effects/EQ, and optionally
		playback speed) that applies to every part/chapter of the selected
		audio book - see playbackCoreMixin._play_station() and
		_start_getem_chapter()."""
		idx = self._getem_library_ctrl.GetSelection()
		books = self._getem_library.get_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		book = books[idx]
		profile = self._prompt_and_build_audio_profile(book.audio_profile, allow_speed=True)
		if profile is None:
			return
		book.audio_profile = profile
		self._getem_library.save()
		ui.message(_("Audio profile saved for %(book)s") % {"book": book.title})

	def _on_clear_getem_audio_profile(self, event):
		"""Remove the saved audio profile from the selected audio book."""
		idx = self._getem_library_ctrl.GetSelection()
		books = self._getem_library.get_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		book = books[idx]
		if not book.audio_profile:
			return
		book.audio_profile = None
		self._getem_library.save()
		ui.message(_("Audio profile cleared for %(book)s") % {"book": book.title})

	def _on_getem_remove_from_library(self, event):
		idx = self._getem_library_ctrl.GetSelection()
		books = self._getem_library.get_books()
		if idx == wx.NOT_FOUND or idx >= len(books):
			return
		book = books[idx]
		if self._getem_library.remove_book(book):
			# The book's own audio profile is discarded automatically along
			# with the rest of the GetemBook object above. Its per-chapter
			# resume positions live separately, in RadioPlayer's own store
			# (keyed by each chapter's proxy stream URL - see
			# getem.get_stream_url()), and are cleaned up here so they
			# don't linger for a book the user can no longer see or resume.
			if book.chapters and self._player:
				urls = [
					getem.get_stream_url(ch["url"], referer=book.detail_url)
					for ch in book.chapters if ch.get("url")
				]
				self._player.clear_podcast_positions(urls)
			ui.message(_("Removed from library: %s") % book.title)
			self._refresh_getem_library_list()

	def download_getem_book_by_detail_url(self, detail_url):
		"""Downloads every part of the GETEM audio book identified by
		*detail_url* into its own folder under the recordings directory -
		reached from GlobalPlugin._download_current_getem_book() in
		__init__.py, the Ctrl+Win+V action while one of its parts is
		playing (see script_addToFavorites()). Looks first at whichever
		book is currently loaded (self._getem_now_playing already has its
		resolved chapter list), then falls back to the library, so this
		works whether or not the currently-playing book was ever added to
		it."""
		playing = getattr(self, "_getem_now_playing", None)
		book = playing[0] if playing and playing[0].detail_url == detail_url else None
		if book is None:
			book = self._getem_library.get_book_by_key(detail_url)
		if book is None:
			ui.message(_("Could not find this audio book."))
			return
		self._download_getem_book(book)

	def _download_getem_book(self, book):
		"""Saves a permanent, user-visible copy of every part of *book* into
		its own folder named after the book (see getem.book_download_dir()) -
		the "Download Book" library context-menu action and its Ctrl+Win+V
		equivalent. Distinct from a single-part download: resolves the full
		chapter list first if it isn't already known."""
		if book.chapters:
			self._start_getem_book_download(book)
			return

		ui.message(_("Loading: %s") % book.title)

		def _do_resolve():
			resolved_book, error = getem.resolve_media(book)
			wx.CallAfter(self._on_getem_book_download_resolve_done, resolved_book, error)

		threading.Thread(target=_do_resolve, daemon=True).start()

	def _on_getem_book_download_resolve_done(self, book, error):
		if error:
			ui.message(error)
			return
		if self._getem_library.is_in_library(book):
			self._getem_library.save()
		self._start_getem_book_download(book)

	def _start_getem_book_download(self, book):
		if not book.chapters:
			ui.message(_("No audio parts found for this book."))
			return

		# Guard against firing the same book's download twice in a row
		# (e.g. Ctrl+Win+V pressed twice while it's already under way) -
		# there's no per-part row in the UI to disable like the podcast
		# episode list's download button does.
		key = book.identity_key()
		if getattr(self, "_getem_book_download_active", None) == key:
			ui.message(_("Already downloading: %s") % book.title)
			return
		self._getem_book_download_active = key

		ui.message(_("Downloading book: %s") % book.title)

		def _do_download():
			out_dir = getem.book_download_dir(book)
			try:
				os.makedirs(out_dir, exist_ok=True)
			except Exception as e:
				wx.CallAfter(self._on_getem_book_download_done, book, 0, len(book.chapters), str(e))
				return

			saved = 0
			last_error = None
			for i, chapter in enumerate(book.chapters):
				out_path = getem.download_book_chapter_target(book, chapter, i)
				if os.path.exists(out_path):
					saved += 1
					continue
				try:
					getem.download_chapter_to(chapter["url"], out_path, referer=book.detail_url)
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
			ui.message(_("Download complete: %s") % book.title)
		elif saved > 0:
			ui.message(_("Downloaded %(saved)d of %(total)d parts of %(book.title)s. Last error: %(error)s") % (saved, total, book.title, error))
		else:
			ui.message(_("Download failed: %s") % (error or book.title))


class LyricsDialog(wx.Dialog):
	"""Read-only lyrics viewer."""

	def __init__(self, parent, song, lyrics):
		super().__init__(
			parent,
			title=_("Lyrics — %s") % song,
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		sizer = wx.BoxSizer(wx.VERTICAL)

		sizer.Add(
			wx.StaticText(self, label=_("Lyrics for: %s") % song),
			0, wx.EXPAND | wx.ALL, 8,
		)

		self._text = wx.TextCtrl(
			self,
			value=lyrics,
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
		)
		self._text.SetName(_("Lyrics"))
		sizer.Add(self._text, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		btn_sizer = wx.StdDialogButtonSizer()
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
		super().__init__(parent, title=_("Add Custom Station"))
		sizer = wx.BoxSizer(wx.VERTICAL)

		sizer.Add(wx.StaticText(self, label=_("Station name:")), 0, wx.EXPAND | wx.ALL, 5)
		self._name = wx.TextCtrl(self)
		sizer.Add(self._name, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		sizer.Add(wx.StaticText(self, label=_("Stream URL:")), 0, wx.EXPAND | wx.ALL, 5)
		self._url = wx.TextCtrl(self)
		sizer.Add(self._url, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# URL test button + status label
		test_row = wx.BoxSizer(wx.HORIZONTAL)
		self._test_btn = wx.Button(self, label=_("&Test URL"))
		test_row.Add(self._test_btn, 0, wx.RIGHT, 8)
		self._test_status = wx.StaticText(self, label="")
		test_row.Add(self._test_status, 1, wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(test_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		self._rb_btn = wx.Button(self, label=_("Add to &Radio Browser directory…"))
		sizer.Add(self._rb_btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		btn_sizer = wx.StdDialogButtonSizer()
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
			self._test_status.SetLabel(_("Please enter a URL first."))
			ui.message(_("Please enter a URL first."))
			return
		self._test_btn.Enable(False)
		self._test_status.SetLabel(_("Checking…"))
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
			label = _("✓ Stream reachable")
			self._test_status.SetLabel(label)
			ui.message(_("Stream is reachable."))
		else:
			label = _("✗ %s") % detail
			self._test_status.SetLabel(label)
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

	def __init__(self, parent, rec, player_paths=None):
		super().__init__(
			parent,
			title=_("Edit Schedule — %s") % rec.station.get("name", "?"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		self._rec          = rec
		self._player_paths = player_paths or {}

		sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Time ---
		sizer.Add(wx.StaticText(self, label=_("Start time (HH:MM):")), 0, wx.EXPAND | wx.ALL, 8)
		self._time_ctrl = wx.TextCtrl(self, value=rec.start_time.strftime("%H:%M"))
		self._time_ctrl.SetName(_("Start time (HH:MM):"))
		sizer.Add(self._time_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		# --- Duration ---
		sizer.Add(wx.StaticText(self, label=_("Duration (minutes):")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._dur_spin = wx.SpinCtrl(self, min=1, max=600, initial=rec.duration_minutes)
		self._dur_spin.SetName(_("Duration (minutes):"))
		sizer.Add(self._dur_spin, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		# --- Recurrence ---
		sizer.Add(wx.StaticText(self, label=_("Recurrence:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._rec_once  = wx.RadioButton(self, label=_("Record &once"), style=wx.RB_GROUP)
		# Repeats every week on the selected active days, with no end —
		# the user removes it from the schedule list to stop it. Legacy
		# entries saved with the old fixed-count "weekly" mode are treated
		# the same way here; saving will convert them to indefinite.
		self._rec_indef = wx.RadioButton(self, label=_("Repeat &weekly"))
		for rb in (self._rec_once, self._rec_indef):
			sizer.Add(rb, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		if rec.recurrence in ("weekly", "indefinite"):
			self._rec_indef.SetValue(True)
		else:
			self._rec_once.SetValue(True)

		# --- Active days ---
		_day_labels = [
			_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
			_("Friday"), _("Saturday"), _("Sunday"),
		]
		self._days_label = wx.StaticText(self, label=_("Active days:"))
		sizer.Add(self._days_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._days_clb = nvdaControls.CustomCheckListBox(self, choices=_day_labels)
		self._days_clb.SetName(_("Active days:"))
		checked = rec.active_days if rec.active_days else list(range(7))
		self._days_clb.Checked = checked
		if checked:
			self._days_clb.Select(checked[0])
		sizer.Add(self._days_clb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		# --- Playback mode ---
		sizer.Add(wx.StaticText(self, label=_("Playback during recording:")), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._mode_play = wx.RadioButton(self, label=_("Record while &listening (play and record simultaneously)"),  style=wx.RB_GROUP)
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