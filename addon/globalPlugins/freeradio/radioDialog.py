# -*- coding: utf-8 -*-
# FreeRadio - Station Browser Dialog

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]

import config
import datetime
import os
import sys
import threading
import ui
import wx
import winsound  # Added for sound effects

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

_RadioBrowserError = None  # Determined at first use

def _radio_browser_error():
	global _RadioBrowserError
	if _RadioBrowserError is None:
		_RadioBrowserError = _get_radio_browser_error()
	return _RadioBrowserError


_COUNTRY_NAMES = {
	"AD": "Andorra", "AE": "Birleşik Arap Emirlikleri", "AF": "Afganistan",
	"AG": "Antigua ve Barbuda", "AI": "Anguilla", "AL": "Arnavutluk",
	"AM": "Ermenistan", "AO": "Angola", "AQ": "Antarktika",
	"AR": "Arjantin", "AS": "Amerikan Samoası", "AT": "Avusturya",
	"AU": "Avustralya", "AW": "Aruba", "AX": "Åland Adaları",
	"AZ": "Azerbaycan", "BA": "Bosna-Hersek", "BB": "Barbados",
	"BD": "Bangladeş", "BE": "Belçika", "BF": "Burkina Faso",
	"BG": "Bulgaristan", "BH": "Bahreyn", "BI": "Burundi",
	"BJ": "Benin", "BL": "Saint-Barthélemy", "BM": "Bermuda",
	"BN": "Brunei", "BO": "Bolivya", "BQ": "Karayip Hollandası",
	"BR": "Brezilya", "BS": "Bahamalar", "BT": "Bhutan",
	"BV": "Bouvet Adası", "BW": "Botsvana", "BY": "Beyaz Rusya",
	"BZ": "Belize", "CA": "Kanada", "CC": "Cocos Adaları",
	"CD": "Kongo (Demokratik Cumhuriyet)", "CF": "Orta Afrika Cumhuriyeti",
	"CG": "Kongo", "CH": "İsviçre", "CI": "Fildişi Sahili",
	"CK": "Cook Adaları", "CL": "Şili", "CM": "Kamerun",
	"CN": "Çin", "CO": "Kolombiya", "CR": "Kosta Rika",
	"CU": "Küba", "CV": "Yeşil Burun Adaları", "CW": "Curaçao",
	"CX": "Christmas Adası", "CY": "Kıbrıs", "CZ": "Çekya",
	"DE": "Almanya", "DJ": "Cibuti", "DK": "Danimarka",
	"DM": "Dominika", "DO": "Dominik Cumhuriyet", "DZ": "Cezayir",
	"EC": "Ekvador", "EE": "Estonya", "EG": "Mısır",
	"EH": "Batı Sahra", "ER": "Eritre", "ES": "İspanya",
	"ET": "Etiyopya", "FI": "Finlandiya", "FJ": "Fiji",
	"FK": "Falkland Adaları", "FM": "Mikronezya", "FO": "Faroe Adaları",
	"FR": "Fransa", "GA": "Gabon", "GB": "Birleşik Krallık",
	"GD": "Grenada", "GE": "Gürcistan", "GF": "Fransız Guyanası",
	"GG": "Guernsey", "GH": "Gana", "GI": "Cebelitarık",
	"GL": "Grönland", "GM": "Gambiya", "GN": "Gine",
	"GP": "Guadeloupe", "GQ": "Ekvator Ginesi", "GR": "Yunanistan",
	"GS": "Güney Georgia ve Sandwich Adaları", "GT": "Guatemala",
	"GU": "Guam", "GW": "Gine-Bissau", "GY": "Guyana",
	"HK": "Hong Kong", "HM": "Heard ve McDonald Adaları",
	"HN": "Honduras", "HR": "Hırvatistan", "HT": "Haiti",
	"HU": "Macaristan", "ID": "Endonezya", "IE": "İrlanda",
	"IL": "İsrail", "IM": "Man Adası", "IN": "Hindistan",
	"IO": "Hint Okyanusu İngiliz Toprağı", "IQ": "Irak",
	"IR": "İran", "IS": "İzlanda", "IT": "İtalya",
	"JE": "Jersey", "JM": "Jamaika", "JO": "Ürdün",
	"JP": "Japonya", "KE": "Kenya", "KG": "Kırgızistan",
	"KH": "Kamboçya", "KI": "Kiribati", "KM": "Komorlar",
	"KN": "Saint Kitts ve Nevis", "KP": "Kuzey Kore", "KR": "Güney Kore",
	"KW": "Kuveyt", "KY": "Cayman Adaları", "KZ": "Kazakistan",
	"LA": "Laos", "LB": "Lübnan", "LC": "Saint Lucia",
	"LI": "Lihtenştayn", "LK": "Sri Lanka", "LR": "Liberya",
	"LS": "Lesotho", "LT": "Litvanya", "LU": "Lüksemburg",
	"LV": "Letonya", "LY": "Libya", "MA": "Fas",
	"MC": "Monako", "MD": "Moldova", "ME": "Karadağ",
	"MF": "Saint-Martin", "MG": "Madagaskar", "MH": "Marshall Adaları",
	"MK": "Kuzey Makedonya", "ML": "Mali", "MM": "Myanmar",
	"MN": "Moğolistan", "MO": "Makao", "MP": "Kuzey Mariana Adaları",
	"MQ": "Martinik", "MR": "Moritanya", "MS": "Montserrat",
	"MT": "Malta", "MU": "Mauritius", "MV": "Maldivler",
	"MW": "Malavi", "MX": "Meksika", "MY": "Malezya",
	"MZ": "Mozambik", "NA": "Namibya", "NC": "Yeni Kaledonya",
	"NE": "Nijer", "NF": "Norfolk Adası", "NG": "Nijerya",
	"NI": "Nikaragua", "NL": "Hollanda", "NO": "Norveç",
	"NP": "Nepal", "NR": "Nauru", "NU": "Niue",
	"NZ": "Yeni Zelanda", "OM": "Umman", "PA": "Panama",
	"PE": "Peru", "PF": "Fransız Polinezyası", "PG": "Papua Yeni Gine",
	"PH": "Filipinler", "PK": "Pakistan", "PL": "Polonya",
	"PM": "Saint-Pierre ve Miquelon", "PN": "Pitcairn Adaları",
	"PR": "Porto Riko", "PS": "Filistin", "PT": "Portekiz",
	"PW": "Palau", "PY": "Paraguay", "QA": "Katar",
	"RE": "Réunion", "RO": "Romanya", "RS": "Sırbistan",
	"RU": "Rusya", "RW": "Ruanda", "SA": "Suudi Arabistan",
	"SB": "Solomon Adaları", "SC": "Seyşeller", "SD": "Sudan",
	"SE": "İsveç", "SG": "Singapur", "SH": "Saint Helena",
	"SI": "Slovenya", "SJ": "Svalbard ve Jan Mayen", "SK": "Slovakya",
	"SL": "Sierra Leone", "SM": "San Marino", "SN": "Senegal",
	"SO": "Somali", "SR": "Surinam", "SS": "Güney Sudan",
	"ST": "São Tomé ve Príncipe", "SV": "El Salvador", "SX": "Sint Maarten",
	"SY": "Suriye", "SZ": "Esvatini", "TC": "Turks ve Caicos Adaları",
	"TD": "Çad", "TF": "Fransız Güney Toprakları", "TG": "Togo",
	"TH": "Tayland", "TJ": "Tacikistan", "TK": "Tokelau",
	"TL": "Doğu Timor", "TM": "Türkmenistan", "TN": "Tunus",
	"TO": "Tonga", "TR": "Türkiye", "TT": "Trinidad ve Tobago",
	"TV": "Tuvalu", "TW": "Tayvan", "TZ": "Tanzanya",
	"UA": "Ukrayna", "UG": "Uganda", "UM": "ABD Küçük Dış Adaları",
	"US": "Amerika Birleşik Devletleri", "UY": "Uruguay", "UZ": "Özbekistan",
	"VA": "Vatikan", "VC": "Saint Vincent ve Grenadinler", "VE": "Venezuela",
	"VG": "Britanya Virjin Adaları", "VI": "ABD Virjin Adaları",
	"VN": "Vietnam", "VU": "Vanuatu", "WF": "Wallis ve Futuna",
	"WS": "Samoa", "XK": "Kosova", "YE": "Yemen",
	"YT": "Mayotte", "ZA": "Güney Afrika", "ZM": "Zambiya",
	"ZW": "Zimbabve",
}


def _country_name(code):
	"""Return the full country name for a two-letter ISO code, or the code itself if unknown."""
	return _COUNTRY_NAMES.get(code.upper(), code.upper())


_NAME_TO_CODE = {v: k for k, v in _COUNTRY_NAMES.items()}


def _station_label(station):
	name    = station.get("name", _("Unknown"))
	country = station.get("countrycode", "")
	tags    = station.get("tags", "")
	parts   = [name.strip()]
	if country:
		parts.append(_country_name(country))
	if tags:
		first_tag = tags.split(",")[0].strip()
		if first_tag:
			parts.append(first_tag)
	return " - ".join(parts)


def _first_tag(station):
	tags = station.get("tags", "")
	if not tags:
		return ""
	return tags.split(",")[0].strip().lower()


# Character order for Turkish alphabetical sorting
# (In Turkish, İ/i, Ğ/ğ, Ş/ş, Ü/ü, Ö/ö, Ç/ç are in different positions than the English alphabet)
_TR_ORDER = "aAbBcCçÇdDeEfFgGğĞhHıIiİjJkKlLmMnNoOöÖpPrRsSSşŞtTuUüÜvVyYzZ0123456789"
_TR_CHAR_KEY = {ch: idx for idx, ch in enumerate(_TR_ORDER)}


def _tr_sort_key(station):
	"""Generates key from station name for Turkish alphabetical sorting."""
	name = station.get("name", "").strip()
	return [_TR_CHAR_KEY.get(ch, len(_TR_ORDER) + ord(ch)) for ch in name]


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
		self._all_stations    = []
		self._extra_stations  = []   # additional stations from country selection
		self._search_stations = []   # Stations from API text search
		self._stations        = []
		self._combo_fetch_id = 0
		self._moving_station_index = -1  # Index of the item picked for X-based reordering
		self._combo_debounce_timer = None  # wx.CallLater for country combo debounce

		self._build_ui()
		self._prepopulate_country_combo()
		threading.Thread(target=self._fetch_all,       daemon=True).start()
		threading.Thread(target=self._fetch_countries, daemon=True).start()


	def _build_ui(self):
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		self._notebook    = wx.Notebook(self)
		self._notebook.SetName("")
		self._all_panel    = wx.Panel(self._notebook)
		self._fav_panel    = wx.Panel(self._notebook)
		self._rec_panel    = wx.Panel(self._notebook)
		self._timer_panel  = wx.Panel(self._notebook)
		self._liked_panel  = wx.Panel(self._notebook)
		self._notebook.AddPage(self._all_panel,   _("&All Stations"))
		self._notebook.AddPage(self._fav_panel,   _("&Favourites"))
		self._notebook.AddPage(self._rec_panel,   _("&Recording"))
		self._notebook.AddPage(self._timer_panel, _("&Timer"))
		self._notebook.AddPage(self._liked_panel, _("&Liked Songs"))
		self._notebook.SetSelection(0)  # Start on the All Stations tab
		main_sizer.Add(self._notebook, 1, wx.EXPAND | wx.ALL, 5)

		import config as _cfg
		disable_bass = _cfg.conf["freeradio"].get("disable_bass", False)

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
		
		if not disable_bass:
			threading.Thread(target=self._load_audio_devices, daemon=True).start()
		else:
			self._dev_label.Hide()
			self._device_choice.Hide()

		# Volume and Effects row (visible on all tabs)
		audio_row = wx.BoxSizer(wx.HORIZONTAL)

		_vol_label = wx.StaticText(self, label=_("Volume:"))
		audio_row.Add(_vol_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)

		self._vol_spin = wx.SpinCtrl(self, min=0, max=200,
		                             initial=_cfg.conf["freeradio"]["volume"])
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
		_saved_fx = _cfg.conf["freeradio"].get("audio_fx", "none")
		_active = {x.strip() for x in _saved_fx.split(",") if x.strip() != "none"}
		for i, key in enumerate(self._fx_keys):
			self._fx_choice.Check(i, key in _active)
		audio_row.Add(self._fx_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

		if disable_bass:
			self._fx_label.Hide()
			self._fx_choice.Hide()

		main_sizer.Add(audio_row, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)


		# action buttons
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self._play_btn    = wx.Button(self, label=_("&Play/Pause"))
		self._del_btn     = wx.Button(self, label=_("&Delete Station"))
		self._del_btn.Enable(False)
		self._fav_btn     = wx.Button(self, label=_("Add to Fa&vorites"))
		self._details_btn = wx.Button(self, label=_("Station Detai&ls"))
		self._details_btn.Enable(False)
		self._add_btn     = wx.Button(self, label=_("Add C&ustom Station..."))
		self._close_btn   = wx.Button(self, label=_("&Close"))
		for btn in (self._play_btn, self._del_btn, self._fav_btn, self._details_btn, self._add_btn, self._close_btn):
			btn_sizer.Add(btn, 0, wx.ALL, 5)
		main_sizer.Add(btn_sizer, 0, wx.CENTER | wx.BOTTOM, 8)

		self.SetSizer(main_sizer)
		self.SetMinSize((560, 620))
		self.Fit()

		self._build_all_tab()
		self._build_fav_tab()
		self._build_rec_tab()
		self._build_timer_tab()
		self._build_liked_tab()

		self._play_btn.Bind(wx.EVT_BUTTON,    self._on_play_clicked)
		self._del_btn.Bind(wx.EVT_BUTTON,     self._on_delete_station)
		self._del_btn.Bind(wx.EVT_KEY_DOWN,   self._on_del_btn_key)
		self._fav_btn.Bind(wx.EVT_BUTTON,     self._on_toggle_favorite)
		self._details_btn.Bind(wx.EVT_BUTTON, self._on_details_clicked)
		self._add_btn.Bind(wx.EVT_BUTTON,     self._on_add_custom)
		self._close_btn.Bind(wx.EVT_BUTTON,   self._on_close_btn)

		self._vol_spin.Bind(wx.EVT_SPINCTRL,    self._on_vol_changed)
		self._fx_choice.Bind(wx.EVT_CHECKLISTBOX, self._on_fx_changed)
		self._fx_choice.Bind(wx.EVT_LISTBOX,      self._on_fx_focus)
		self._device_choice.Bind(wx.EVT_CHOICE,   self._on_device_changed)

		for btn in (self._play_btn, self._del_btn, self._fav_btn,
		            self._details_btn, self._add_btn, self._close_btn):
			btn.Bind(wx.EVT_SET_FOCUS, self._on_button_focused)

		self._notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_tab_changed)
		self.Bind(wx.EVT_CLOSE,     self._on_window_close)
		self.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

		self._play_btn.SetDefault()
		wx.CallAfter(self._search.SetFocus)

	def focus_favorites(self):
		"""Switch to the Favorites tab and give the list focus."""
		self._notebook.SetSelection(1)  # Favourites tab index
		self._refresh_fav_list()
		favs = self._manager.get_favorites()
		if favs and self._fav_list.GetSelection() == wx.NOT_FOUND:
			self._fav_list.SetSelection(0)
		self._fav_list.SetFocus()

	def focus_search(self):
		"""Switch to the All Stations tab and focus on the search box."""
		self._notebook.SetSelection(0)
		self._search.SetFocus()
		self._search.SelectAll()

	def focus_tab(self, tab_index):
		"""Switch to the specified tab and focus on the first focusable item.
		Indices: 0=All Stations, 1=Favourites, 2=Recording, 3=Timer, 4=Liked Songs."""
		self._notebook.SetSelection(tab_index)
		# Go to the first focusable control of each tab
		panel = self._notebook.GetPage(tab_index)
		for child in panel.GetChildren():
			if child.AcceptsFocus() and child.IsEnabled() and child.IsShown():
				child.SetFocus()
				return

	def _build_fav_tab(self):
		sizer = wx.BoxSizer(wx.VERTICAL)
		self._fav_list = wx.ListBox(self._fav_panel, style=wx.LB_SINGLE)
		self._fav_list.SetName(_("Favourites"))
		sizer.Add(self._fav_list, 1, wx.EXPAND | wx.ALL, 5)

		btn_row = wx.BoxSizer(wx.HORIZONTAL)
		self._save_audio_btn = wx.Button(self._fav_panel, label=_("Save Audio Pr&ofile for This Station"))
		self._save_audio_btn.Enable(False)
		btn_row.Add(self._save_audio_btn, 0, wx.RIGHT, 6)

		self._clear_audio_btn = wx.Button(self._fav_panel, label=_("Clear Audio Prof&ile"))
		self._clear_audio_btn.Enable(False)
		btn_row.Add(self._clear_audio_btn, 0)

		sizer.Add(btn_row, 0, wx.LEFT | wx.BOTTOM, 5)

		self._fav_panel.SetSizer(sizer)

		self._fav_list.Bind(wx.EVT_LISTBOX,        self._on_selection_changed)
		self._fav_list.Bind(wx.EVT_LISTBOX_DCLICK, self._on_play_clicked)
		self._fav_list.Bind(wx.EVT_KEY_DOWN,       self._on_fav_list_key)
		self._fav_list.Bind(wx.EVT_SET_FOCUS, self._on_fav_list_focus)
		self._save_audio_btn.Bind(wx.EVT_BUTTON,   self._on_save_audio_profile)
		self._clear_audio_btn.Bind(wx.EVT_BUTTON,  self._on_clear_audio_profile)

	def _build_all_tab(self):
		sizer = wx.BoxSizer(wx.VERTICAL)

		filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
		filter_sizer.Add(wx.StaticText(self._all_panel, label=_("Country:")),
		                 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		_all_country_names = sorted(_COUNTRY_NAMES.values())
		self._country_cb = wx.ComboBox(self._all_panel, style=wx.CB_READONLY, choices=[_("All")] + _all_country_names)
		self._country_cb.SetSelection(0)
		filter_sizer.Add(self._country_cb, 1)
		sizer.Add(filter_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		sizer.Add(wx.StaticText(self._all_panel, label=_("Search:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		search_row = wx.BoxSizer(wx.HORIZONTAL)
		self._search     = wx.TextCtrl(self._all_panel)
		self._search_btn = wx.Button(self._all_panel, label=_("&Search"))
		search_row.Add(self._search,     1, wx.RIGHT, 5)
		search_row.Add(self._search_btn, 0)
		sizer.Add(search_row, 0, wx.EXPAND | wx.ALL, 5)

		hint = wx.StaticText(
			self._all_panel,
			label=_("Type to filter · Enter or Search to search all stations online"),
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
		self._search_btn.Bind(wx.EVT_BUTTON,   self._on_api_search)
		self._country_cb.Bind(wx.EVT_COMBOBOX, self._on_combo_changed)

		self._all_list.Bind(wx.EVT_LISTBOX,        self._on_selection_changed)
		self._all_list.Bind(wx.EVT_LISTBOX_DCLICK, self._on_play_clicked)
		self._all_list.Bind(wx.EVT_KEY_DOWN,       self._on_list_key)
		self._all_list.Bind(wx.EVT_SET_FOCUS,      lambda e: (self._play_btn.SetDefault(), e.Skip()))
		self._search_btn.Bind(wx.EVT_SET_FOCUS,    self._on_button_focused)

	def _build_rec_tab(self):
		sizer = wx.BoxSizer(wx.VERTICAL)

		sizer.Add(wx.StaticText(self._rec_panel, label=_("Instant Recording")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._rec_status = wx.StaticText(self._rec_panel, label=_("Not recording"))
		sizer.Add(self._rec_status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._rec_btn = wx.Button(self._rec_panel, label=_("Start &Recording"))
		sizer.Add(self._rec_btn, 0, wx.ALL, 8)

		sizer.Add(wx.StaticLine(self._rec_panel), 0, wx.EXPAND | wx.ALL, 8)

		sizer.Add(wx.StaticText(self._rec_panel, label=_("Scheduled Recording")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

		station_label = _("Station:")
		st_lbl = wx.StaticText(self._rec_panel, label=station_label)
		self._sched_station_cb = wx.ComboBox(self._rec_panel, style=wx.CB_READONLY, choices=[])
		sizer.Add(st_lbl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		sizer.Add(self._sched_station_cb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		self._sched_station_cb.SetName(station_label)

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
		self._sched_mode_play.SetValue(True)
		sizer.Add(self._sched_mode_play, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		sizer.Add(self._sched_mode_rec,  0, wx.LEFT | wx.RIGHT | wx.TOP, 4)

		self._sched_add_btn = wx.Button(self._rec_panel, label=_("&Add to Schedule"))
		sizer.Add(self._sched_add_btn, 0, wx.ALL, 8)

		sizer.Add(wx.StaticText(self._rec_panel, label=_("Upcoming scheduled recordings:")),
		          0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self._sched_list = wx.ListBox(self._rec_panel, style=wx.LB_SINGLE)
		sizer.Add(self._sched_list, 1, wx.EXPAND | wx.ALL, 8)

		self._sched_del_btn = wx.Button(self._rec_panel, label=_("&Remove Selected"))
		self._sched_del_btn.Enable(False)
		sizer.Add(self._sched_del_btn, 0, wx.LEFT | wx.BOTTOM, 8)

		self._rec_panel.SetSizer(sizer)

		self._rec_btn.Bind(wx.EVT_BUTTON,       self._on_rec_btn)
		self._sched_add_btn.Bind(wx.EVT_BUTTON, self._on_sched_add)
		self._sched_del_btn.Bind(wx.EVT_BUTTON, self._on_sched_del)
		self._sched_list.Bind(wx.EVT_LISTBOX,   self._on_sched_selected)

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
		self._timer_station_cb = wx.ComboBox(
			self._timer_panel, style=wx.CB_READONLY, choices=[]
		)
		self._timer_station_cb.SetName(_("Station:"))
		sizer.Add(self._timer_station_label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
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

		self._timer_stations = []
		self._timer_action_changed_update()


	def _active_list(self):
		sel = self._notebook.GetSelection()
		if sel == 1:
			return self._fav_list
		return self._all_list

	def _on_tab_changed(self, event):
		sel = event.GetSelection()
		on_rec_or_timer = (sel in (2, 3, 4))
		self._play_btn.Show(not on_rec_or_timer)
		self._fav_btn.Show(not on_rec_or_timer)
		self._del_btn.Show(not on_rec_or_timer)
		self._details_btn.Show(not on_rec_or_timer)
		self._add_btn.Show(not on_rec_or_timer)
		self.Layout()

		self._tab_just_switched = True
		if sel == 1:
			self._refresh_fav_list_no_select()
			self._update_fav_button()
			self._update_save_audio_btn()
		elif sel == 2:
			self._refresh_sched_stations()
			self._refresh_sched_list()
		elif sel == 3:
			self._refresh_timer_stations()
			self._refresh_timer_list()
		elif sel == 4:
			self._refresh_liked_list()
		if sel != 1 and hasattr(self, "_save_audio_btn"):
			self._save_audio_btn.Enable(False)
		event.Skip()


	def _load_audio_devices(self):
		"""Get the device list from BASS in the background, transfer it to the Choice control."""
		import config as _cfg
		if _cfg.conf["freeradio"].get("disable_bass", False):
			return
		devices = []
		try:
			devices = self._player.get_audio_devices()
		except Exception:
			pass
		wx.CallAfter(self._populate_audio_devices, devices)

	def _populate_audio_devices(self, devices):
		"""Fill the Choice control with the device list and select the saved one."""
		if not self or not self._device_choice:
			return
		import config as _cfg
		self._dialog_audio_devices = [(-1, _("System default"))] + list(devices)
		self._device_choice.Clear()
		for _idx, name in self._dialog_audio_devices:
			self._device_choice.Append(name)
		saved = _cfg.conf["freeradio"].get("audio_device", -1)
		sel = 0
		for i, (idx, _name) in enumerate(self._dialog_audio_devices):
			if idx == saved:
				sel = i
				break
		self._device_choice.SetSelection(sel)

	def _on_device_changed(self, event):
		"""When the user changes the device selection, apply it instantly and save it in the config."""
		import config as _cfg
		if _cfg.conf["freeradio"].get("disable_bass", False):
			event.Skip()
			return
		sel = self._device_choice.GetSelection()
		if 0 <= sel < len(self._dialog_audio_devices):
			new_index = self._dialog_audio_devices[sel][0]
		else:
			new_index = -1
		_cfg.conf["freeradio"]["audio_device"] = new_index
		try:
			self._player.switch_output_device(new_index)
		except Exception:
			pass
		actual = getattr(self._player, "_output_device_index", new_index)
		if actual != new_index:
			_cfg.conf["freeradio"]["audio_device"] = actual
			for i, (idx, _name) in enumerate(self._dialog_audio_devices):
				if idx == actual:
					self._device_choice.SetSelection(i)
					break
		event.Skip()

	def _on_vol_changed(self, event):
		"""When the volume changes, instantly apply it to the player and save it in the config."""
		import config as _cfg
		vol = self._vol_spin.GetValue()
		self._player.set_volume(vol)
		_cfg.conf["freeradio"]["volume"] = min(100, vol)
		event.Skip()

	def _on_fx_focus(self, event):
		"""Tell the enabled/disabled status of an effect in the list when hovering over it."""
		import config as _cfg
		if _cfg.conf["freeradio"].get("disable_bass", False):
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
		import config as _cfg
		if _cfg.conf["freeradio"].get("disable_bass", False):
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
		_cfg.conf["freeradio"]["audio_fx"] = fx_str
		event.Skip()

	def _on_fav_list_focus(self, event):
		"""When the favorites list gets focus: select the first item (if there is no selection),
		voice hint message, set default button."""
		self._play_btn.SetDefault()
		if self._fav_list.GetSelection() == wx.NOT_FOUND and self._fav_list.GetCount() > 0:
			self._fav_list.SetSelection(0)
		if not getattr(self, "_tab_just_switched", False):
			ui.message(_("Press X to pick a station, navigate to the target position, then press X again to drop."))
		self._tab_just_switched = False
		event.Skip()


	def _refresh_sched_stations(self):
		"""Populate station combobox in recording tab from favourites."""
		favs = self._manager.get_favorites()
		self._sched_station_cb.Clear()
		for s in favs:
			self._sched_station_cb.Append(s.get("name", "?").strip())
		if favs:
			self._sched_station_cb.SetSelection(0)
		self._sched_stations = favs

	def _refresh_sched_list(self):
		"""Rebuild the scheduled recordings listbox."""
		self._sched_list.Clear()
		if self._recorder:
			for rec in self._recorder.get_schedules():
				self._sched_list.Append(str(rec))
		self._sched_del_btn.Enable(self._sched_list.GetCount() > 0)


	def _on_rec_btn(self, event):
		if not self._recorder:
			ui.message(_("Recording is not available"))
			return
		if self._recorder.is_recording():
			path = self._recorder.stop(self._player)
			self._rec_btn.SetLabel(_("Start &Recording"))
			self._rec_status.SetLabel(
				_("Saved: %s") % os.path.basename(path) if path else _("Not recording")
			)
			ui.message(_("Recording stopped"))
		else:
			if not self._player.has_media():
				ui.message(_("No station is playing"))
				return
			name = self._player.get_current_name()
			self._recorder.start(self._player, name)
			self._rec_btn.SetLabel(_("Stop &Recording"))
			self._rec_status.SetLabel(_("Recording: %s") % name)
			ui.message(_("Recording started: %s") % name)

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

		now   = datetime.datetime.now()
		start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
		next_day = False
		if start <= now:
			start    += datetime.timedelta(days=1)
			next_day  = True

		dur = self._sched_dur.GetValue()
		idx = self._sched_station_cb.GetSelection()
		if idx == wx.NOT_FOUND or not hasattr(self, "_sched_stations") or idx >= len(self._sched_stations):
			ui.message(_("Please select a station"))
			return

		station     = self._sched_stations[idx]
		record_only = self._sched_mode_rec.GetValue()
		player_paths = {
			"vlc":       self._player._vlc_path,
			"potplayer": self._player._potplayer_path,
			"wmp":       self._player._wmp_path,
		}
		_rec, conflict_names = self._recorder.add_schedule(
			station, start, dur,
			player_paths=player_paths,
			record_only=record_only,
		)
		self._refresh_sched_list()
		# record_only may have been forced on due to conflict — read back from rec
		record_only = _rec.record_only
		mode_str  = _("record only") if record_only else _("listen and record")
		date_str  = start.strftime("%d.%m.%Y")
		if next_day:
			ui.message(_("Time has passed today. Schedule added for tomorrow: %s at %s (%s)") % (
				station.get("name", "?"), time_str, mode_str
			))
		else:
			ui.message(_("Schedule added: %s on %s at %s (%s)") % (
				station.get("name", "?"), date_str, time_str, mode_str
			))
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
		schedules = self._recorder.get_schedules()
		if idx < len(schedules):
			self._recorder.remove_schedule(schedules[idx])
			self._refresh_sched_list()
			ui.message(_("Schedule deleted"))

	def _on_sched_selected(self, event):
		self._sched_del_btn.Enable(self._sched_list.GetSelection() != wx.NOT_FOUND)


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
					stations_country[0] = self._manager.get_stations_by_country(cc)
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

	def _prepopulate_country_combo(self):
		"""As soon as the dialog opens, add all countries from the local dictionary to the combo.
		API response is not expected; All countries are visible even if there is no network connection."""
		all_names = sorted(_COUNTRY_NAMES.values())
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
		for c in countries_data:
			code = c.get("iso_3166_1", "").strip().upper()
			if not code:
				code = c.get("name", "").strip().upper()
			count = int(c.get("stationcount", 0) or 0)
			if len(code) == 2 and count > 0:
				names.append(_country_name(code))
		names = sorted(set(names))
		wx.CallAfter(self._populate_country_combo, names)

	def _populate_country_combo(self, all_country_names):
		if not self:
			return
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
# Stations searched via API are exempt from local text filter
		# (already filtered by API); Only the country filter is applied.
		search_uids = {s.get("stationuuid") for s in self._search_stations}

		result = []
		seen   = set()
		for s in pool:
			uid = s.get("stationuuid", "")
			if uid in seen:
				continue
			seen.add(uid)
			if sel_country and _country_name(s.get("countrycode", "")) != sel_country:
				continue
			if text and uid not in search_uids:
				haystack = " ".join([
					s.get("name", ""),
					s.get("countrycode", ""),
					_country_name(s.get("countrycode", "")),
					s.get("tags", ""),
				])
				if text not in haystack:
					continue
			result.append(s)

		result.sort(key=_tr_sort_key)
		self._stations = result
		self._all_list.Clear()
		for s in result:
			self._all_list.Append(_station_label(s))

		if sel_country and status_override:
			label = _("%s (%d in %s)") % (status_override, len(result), sel_country)
		elif sel_country:
			label = _("%d stations in %s") % (len(result), sel_country)
		elif status_override:
			label = status_override
		else:
			label = _("%d stations") % len(result)
		self._status.SetLabel(label)
		if announce:
			ui.message(label)

		if result:
			self._all_list.SetSelection(0)
		self._update_fav_button()

	def _refresh_fav_list(self):
		favs = self._manager.get_favorites()
		self._fav_list.Clear()
		for s in favs:
			self._fav_list.Append(_station_label(s))
		if favs:
			self._fav_list.SetSelection(0)
		self._update_fav_button()
		self._update_save_audio_btn()

	def _refresh_fav_list_no_select(self):
		"""Used in tab switching: populates the list but does not call SetSelection.
		SetSelection sends Windows EVENT_OBJECT_SELECTION to NVDA's list
		Causes it to announce ; This is not desired when reading the tab name."""
		favs = self._manager.get_favorites()
		self._fav_list.Clear()
		for s in favs:
			self._fav_list.Append(_station_label(s))
		self._update_fav_button()

	def _show_error(self):
		if not self:
			return
		self._status.SetLabel(_("Could not connect to radio directory. Check your internet connection."))
		self._all_list.Clear()
		self._stations = []


	def _on_text_changed(self, event):
		if self._all_stations:
			if not self._search.GetValue().strip():
				self._extra_stations  = []
				self._search_stations = []
			self._apply_filters()
		event.Skip()

	def _on_combo_changed(self, event):
		if not self._all_stations:
			event.Skip()
			return

		ci = self._country_cb.GetSelection()
		sel_country = "" if ci <= 0 else self._country_cb.GetString(ci)

		if not sel_country:
			# If there is a debounce timer, cancel it
			if self._combo_debounce_timer is not None:
				try:
					self._combo_debounce_timer.Stop()
				except Exception:
					pass
				self._combo_debounce_timer = None
			self._extra_stations = []
			self._apply_filters(announce=True)
			event.Skip()
			return

		# Debounce: cancel previous delay, start new one.
# HTTP request for each item as the user quickly scrolls through the list
		# instead of starting, _COMBO_DEBOUNCE_MS pauses for ms
		# a single request is sent.
		if self._combo_debounce_timer is not None:
			try:
				self._combo_debounce_timer.Stop()
			except Exception:
				pass
			self._combo_debounce_timer = None

		self._combo_fetch_id += 1
		fetch_id     = self._combo_fetch_id
		country_snap = sel_country  # hard copy for lambda

		def _do_fetch():
			self._combo_debounce_timer = None
			if not self or fetch_id != self._combo_fetch_id:
				return

			def fetch():
				RadioBrowserError = _radio_browser_error()
				country_code = _NAME_TO_CODE.get(country_snap, country_snap)
				try:
					data    = self._manager.get_stations_by_country(country_code)
					results = data or []
				except RadioBrowserError:
					# Network error: freeze silently, do not touch the current list.
					return
				if not self or fetch_id != self._combo_fetch_id:
					return
				wx.CallAfter(self._on_combo_fetch_done, results, fetch_id)

			threading.Thread(target=fetch, daemon=True).start()

		self._combo_debounce_timer = wx.CallLater(self._COMBO_DEBOUNCE_MS, _do_fetch)
		event.Skip()

	def _on_combo_fetch_done(self, new_stations, fetch_id):
		if not self or fetch_id != self._combo_fetch_id:
			return
		if not new_stations:
# Network error or empty result: do not touch the current list and status.
			# The user will already get the result on the next try;
			# Showing unnecessary error messages would be annoying.
			return
		seen_all   = {s.get("stationuuid") for s in self._all_stations}
		seen_extra = {s.get("stationuuid") for s in self._extra_stations}
		for s in new_stations:
			uid = s.get("stationuuid", "")
			if uid and uid not in seen_all and uid not in seen_extra:
				self._extra_stations.append(s)
				seen_extra.add(uid)
		self._apply_filters(announce=True)

	def _on_api_search(self, event=None):
		query = self._search.GetValue().strip()
		if not query:
			return
		self._status.SetLabel(_("Searching online for \"%s\"...") % query)
		threading.Thread(target=self._fetch_api_search, args=(query,), daemon=True).start()

	def _fetch_api_search(self, query):
		RadioBrowserError = _radio_browser_error()
		try:
			stations = self._manager.search_stations(query)
		except RadioBrowserError:
			stations = None
		if not self or not self.IsShown():
			return
		if stations is None:
			wx.CallAfter(self._show_error)
			return
		status = _("Search \"%s\": %d results") % (query, len(stations))
		wx.CallAfter(self._on_search_results, stations, status)

	def _on_search_results(self, stations, status_text):
		"""Put search results in separate list; Do not touch country data."""
		if not self:
			return
		self._search_stations = []
		for s in stations:
			uid = s.get("stationuuid", "")
			if uid:
				self._search_stations.append(s)
		self._apply_filters(status_text, announce=True)
		self._refresh_fav_list()


	def _get_selected_station(self):
		lst = self._active_list()
		idx = lst.GetSelection()
		if idx == wx.NOT_FOUND:
			return None, -1
		if self._notebook.GetSelection() == 1:  # Favourites
			favs = self._manager.get_favorites()
			if idx >= len(favs):
				return None, -1
			return favs[idx], idx
		else:
			if idx >= len(self._stations):
				return None, -1
			return self._stations[idx], idx

	def _on_selection_changed(self, event):
		self._update_fav_button()
		self._update_save_audio_btn()

	def _update_save_audio_btn(self):
		"""Enable/disable the Save and Clear Audio Profile buttons based on current selection."""
		if not hasattr(self, "_save_audio_btn"):
			return
		is_fav_tab = (self._notebook.GetSelection() == 1)
		station, _ = self._get_selected_station()
		is_fav = bool(station and self._manager.is_favorite(station))
		has_profile = bool(station and station.get("station_audio"))
		self._save_audio_btn.Enable(is_fav_tab and is_fav)
		self._clear_audio_btn.Enable(is_fav_tab and is_fav and has_profile)

	def _on_save_audio_profile(self, event):
		"""Save current volume and active effects as an audio profile for the selected station."""
		station, _idx = self._get_selected_station()
		if not station or not self._manager.is_favorite(station):
			return

		vol = self._vol_spin.GetValue()
		checked = self._fx_choice.GetCheckedItems()
		active = [self._fx_keys[i] for i in checked if 0 <= i < len(self._fx_keys)]
		fx_str = ",".join(active) if active else "none"

		station["station_audio"] = {"volume": vol, "fx": fx_str}
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

	def _update_fav_button(self):
		station, _idx = self._get_selected_station()
		is_fav = bool(station and self._manager.is_favorite(station))
		self._del_btn.Enable(is_fav)
		self._fav_btn.Enable(bool(station) and not is_fav)
		self._details_btn.Enable(bool(station))

	def _on_play_clicked(self, event):
		if self._player.is_playing():
			self._player.pause()
			ui.message(_("Radio paused"))
			return
		station, idx = self._get_selected_station()
		if not station:
			return
		if self._notebook.GetSelection() == 1:  # Favourites
			self._play_callback(station, self._manager.get_favorites(), idx)
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

	def _on_details_clicked(self, event):
		station, _ = self._get_selected_station()
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
			self._manager.remove_favorite(station)
			ui.message(_("Station deleted"))
			self._refresh_fav_list()
			self._update_fav_button()

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
		dlg.Destroy()


	def _on_close_btn(self, event):
		self.Hide()

	def _on_window_close(self, event):
		self.Hide()

	def _force_destroy(self):
		self.Bind(wx.EVT_CLOSE, None)
		self.Destroy()


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
		lang = languageHandler.getLanguage()          # ör: "tr_TR", "en", "fr"
		short_lang = lang.split("_")[0]               # ör: "tr", "en", "fr"

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

		if key == wx.WXK_ESCAPE:
			self.Hide()
			return

		if key == ord("X") and focused == self._fav_list:
			self._handle_fav_move_x()
			return

		if key in (wx.WXK_F3, wx.WXK_F4):
			tab = self._notebook.GetSelection()
			if tab == 0:  # All Stations
				stations = self._stations
				lst = self._all_list
			elif tab == 1:  # favorites
				stations = self._manager.get_favorites()
				lst = self._fav_list
			else:
				stations = None
				lst = None
			if stations is not None:
				count = len(stations)
				if count > 0:
					cur = lst.GetSelection()
					if key == wx.WXK_F4:
						next_idx = (cur + 1) % count if cur != wx.NOT_FOUND else 0
					else:
						next_idx = (cur - 1) % count if cur != wx.NOT_FOUND else count - 1
					lst.SetSelection(next_idx)
					self._play_callback(stations[next_idx], stations, next_idx, announce=True)
					self._update_fav_button()
					self._update_save_audio_btn()
				return

		if key == wx.WXK_F5:
			vol = max(0, self._player.get_volume() - 10)
			self._player.set_volume(vol)
			import config as _cfg
			_cfg.conf["freeradio"]["volume"] = min(100, vol)
			ui.message(_("Volume %d") % vol)
			self._vol_spin.SetValue(vol)
			if self._plugin:
				try:
					self._plugin._sync_dialog_volume(vol)
				except Exception:
					pass
			return

		if key == wx.WXK_F6:
			vol = min(200, self._player.get_volume() + 10)
			self._player.set_volume(vol)
			import config as _cfg
			_cfg.conf["freeradio"]["volume"] = min(100, vol)
			ui.message(_("Volume %d") % vol)
			self._vol_spin.SetValue(vol)
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
				ui.message(_("Radio paused"))
			else:
				if self._player.has_media():
					self._player.resume()
					ui.message(_("Playing"))
			return

		if key == wx.WXK_F8:
			if self._plugin:
				wx.CallAfter(self._plugin._stop_from_dialog)
			return

		if key == wx.WXK_F1:
			self._open_help()
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
			if focused == self._search:
				self._on_api_search()
				return
			if focused == self._fav_btn and self._fav_btn.IsEnabled():
				self._on_toggle_favorite(event)
				return
			if focused == self._add_btn:
				self._on_add_custom(event)
				return
			if focused == self._close_btn:
				self.Hide()
				return
			if focused in (self._all_list, self._fav_list):
				station, idx = self._get_selected_station()
				if station:
					if self._notebook.GetSelection() == 1:  # Favourites
						self._play_callback(station, self._manager.get_favorites(), idx, announce=True)
					else:
						self._play_callback(station, self._stations, idx, announce=True)
					self._update_fav_button()
				return
			if focused == self._play_btn:
				self._on_play_clicked(event)
				return

		if event.ControlDown() and not event.AltDown() and not event.ShiftDown():
			if key == wx.WXK_UP:
				vol = min(200, self._player.get_volume() + 10)
				self._player.set_volume(vol)
				config.conf["freeradio"]["volume"] = min(100, vol)
				ui.message(_("Volume %d") % vol)
				self._vol_spin.SetValue(vol)
				return
			if key == wx.WXK_DOWN:
				vol = max(0, self._player.get_volume() - 10)
				self._player.set_volume(vol)
				config.conf["freeradio"]["volume"] = min(100, vol)
				ui.message(_("Volume %d") % vol)
				self._vol_spin.SetValue(vol)
				return

		if event.AltDown():
			if key == ord("R"):
				self._search.SetFocus()
				return
			if key == ord("A"):
				self._on_api_search()
				return
			if key == ord("V"):
				if self._fav_btn.IsEnabled():
					self._on_toggle_favorite(event)
				return
			if key == ord("T"):
				self._notebook.SetSelection(0)
				return
			if key == ord("F"):
				self._notebook.SetSelection(1)
				return
			if key == ord("Z"):
				self._notebook.SetSelection(3)
				return
			if key == ord("Y"):
				self._notebook.SetSelection(2)
				return
			if key == ord("K"):
				self.Hide()
				return

		event.Skip()

	def _handle_fav_move_x(self):
		idx = self._fav_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return

		favs = self._manager.get_favorites()
		
		if self._moving_station_index == -1:
			self._moving_station_index = idx
			station_name = favs[idx].get("name", "").strip()
			winsound.Beep(440, 100)  # Mid tone: item picked
			ui.message(_("%s selected. Navigate to the target position and press X again to drop.") % station_name)
		
		else:
			if self._moving_station_index == idx:
				self._moving_station_index = -1
				winsound.Beep(330, 150)  # Low tone: cancelled
				ui.message(_("Move cancelled"))
				return

			source_idx = self._moving_station_index
			target_idx = idx
			
			station = favs.pop(source_idx)
			favs.insert(target_idx, station)
			
			self._manager._favorites = favs
			self._manager._save_favorites()
			self._refresh_fav_list()
			
			self._fav_list.SetSelection(target_idx)
			self._moving_station_index = -1
			winsound.Beep(880, 100)  # High tone: successfully moved
			ui.message(_("Moved: %s") % station.get("name", "").strip())

	def _on_search_key(self, event):
		key = event.GetKeyCode()
		if key == wx.WXK_DOWN:
			self._all_list.SetFocus()
			if self._all_list.GetCount() > 0 and self._all_list.GetSelection() == wx.NOT_FOUND:
				self._all_list.SetSelection(0)
		elif key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			self._on_api_search()
		else:
			event.Skip()

	def _on_list_key(self, event):
		key = event.GetKeyCode()
		if key == wx.WXK_UP and self._active_list().GetSelection() == 0:
			if self._notebook.GetSelection() == 0:  # All Stations
				self._search.SetFocus()
		elif key == wx.WXK_SPACE:
			if self._player.is_playing():
				self._player.pause()
				ui.message(_("Radio paused"))
			else:
				station, idx = self._get_selected_station()
				if station:
					if self._notebook.GetSelection() == 1:  # Favourites
						self._play_callback(station, self._manager.get_favorites(), idx, announce=True)
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

		if key == wx.WXK_SPACE:
			if self._player.is_playing():
				self._player.pause()
				ui.message(_("Radio paused"))
			else:
				station, idx = self._get_selected_station()
				if station:
					self._play_callback(station, self._manager.get_favorites(), idx, announce=True)
					self._update_fav_button()
		elif key == wx.WXK_RIGHT:
			favs = self._manager.get_favorites()
			count = self._fav_list.GetCount()
			if count == 0:
				event.Skip()
				return
			idx = self._fav_list.GetSelection()
			next_idx = (idx + 1) % count if idx != wx.NOT_FOUND else 0
			self._fav_list.SetSelection(next_idx)
			if next_idx < len(favs):
				self._play_callback(favs[next_idx], favs, next_idx, announce=False)
			self._update_fav_button()
			self._update_save_audio_btn()
		elif key == wx.WXK_LEFT:
			favs = self._manager.get_favorites()
			count = self._fav_list.GetCount()
			if count == 0:
				event.Skip()
				return
			idx = self._fav_list.GetSelection()
			prev_idx = (idx - 1) % count if idx != wx.NOT_FOUND else 0
			self._fav_list.SetSelection(prev_idx)
			if prev_idx < len(favs):
				self._play_callback(favs[prev_idx], favs, prev_idx, announce=False)
			self._update_fav_button()
			self._update_save_audio_btn()
		else:
			event.Skip()


	def _timer_action_changed_update(self):
		"""Show/hide station area and update label according to Start/Stop selection."""
		is_start = self._timer_rb_start.GetValue()
		self._timer_station_label.Show(is_start)
		self._timer_station_cb.Show(is_start)
		lbl = _("Start time (HH:MM):") if is_start else _("Stop time (HH:MM):")
		self._timer_time_label.SetLabel(lbl)
		self._timer_time.SetName(lbl)
		self._timer_panel.Layout()

	def _on_timer_action_changed(self, event):
		self._timer_action_changed_update()
		event.Skip()

	def _refresh_timer_stations(self):
		"""Timer tab fill station combo from favorites."""
		favs = self._manager.get_favorites()
		self._timer_station_cb.Clear()
		for s in favs:
			self._timer_station_cb.Append(s.get("name", "?").strip())
		if favs:
			self._timer_station_cb.SetSelection(0)
		self._timer_stations = favs

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

		if is_start:
			idx = self._timer_station_cb.GetSelection()
			if idx == wx.NOT_FOUND or idx >= len(self._timer_stations):
				ui.message(_("Please select a station"))
				return
			station = self._timer_stations[idx]
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
		import config as _cfg
		custom_dir = _cfg.conf["freeradio"].get("recordings_dir", "").strip()
		if custom_dir and os.path.isabs(custom_dir):
			recordings_dir = custom_dir
		else:
			recordings_dir = os.path.join(
				os.path.expanduser("~"), "Documents", "FreeRadio Recordings"
			)
		return os.path.join(recordings_dir, "likedSongs.txt")

	def _build_liked_tab(self):
		"""Liked Songs tab: list + Spotify / YouTube / Remove / Refresh buttons."""
		sizer = wx.BoxSizer(wx.VERTICAL)

		sizer.Add(
			wx.StaticText(self._liked_panel, label=_("Liked Songs:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		self._liked_list = wx.ListBox(self._liked_panel, style=wx.LB_SINGLE)
		self._liked_list.SetName(_("Liked Songs"))
		sizer.Add(self._liked_list, 1, wx.EXPAND | wx.ALL, 5)

		btn_row = wx.BoxSizer(wx.HORIZONTAL)

		self._liked_spotify_btn = wx.Button(
			self._liked_panel, label=_("Play on &Spotify")
		)
		self._liked_youtube_btn = wx.Button(
			self._liked_panel, label=_("Play on YouTube (Alt+&O)")
		)
		self._liked_remove_btn = wx.Button(
			self._liked_panel, label=_("Re&move (Alt+M)")
		)
		self._liked_refresh_btn = wx.Button(
			self._liked_panel, label=_("R&efresh (Alt+E)")
		)

		for btn in (
			self._liked_spotify_btn,
			self._liked_youtube_btn,
			self._liked_remove_btn,
			self._liked_refresh_btn,
		):
			btn_row.Add(btn, 0, wx.RIGHT, 6)

		sizer.Add(btn_row, 0, wx.LEFT | wx.BOTTOM, 5)
		self._liked_panel.SetSizer(sizer)

		self._liked_list.Bind(wx.EVT_LISTBOX, self._on_liked_selected)
		self._liked_spotify_btn.Bind(wx.EVT_BUTTON, self._on_liked_spotify)
		self._liked_youtube_btn.Bind(wx.EVT_BUTTON, self._on_liked_youtube)
		self._liked_remove_btn.Bind(wx.EVT_BUTTON,  self._on_liked_remove)
		self._liked_refresh_btn.Bind(wx.EVT_BUTTON, self._on_liked_refresh)

		self._liked_spotify_btn.Enable(False)
		self._liked_youtube_btn.Enable(False)
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
		"""Read likedSongs.txt and populate the listbox."""
		self._liked_list.Clear()
		path = self._liked_songs_path()
		if os.path.isfile(path):
			try:
				with open(path, encoding="utf-8") as fh:
					lines = [l.rstrip("\n") for l in fh if l.strip()]
				for line in lines:
					self._liked_list.Append(line)
			except Exception as e:
				self._liked_list.Append(_("Could not read file: %s") % str(e))
		else:
			self._liked_list.Append(_("No liked songs yet."))
		self._liked_spotify_btn.Enable(False)
		self._liked_youtube_btn.Enable(False)
		self._liked_remove_btn.Enable(False)

	def _on_liked_selected(self, event):
		has_sel = self._liked_list.GetSelection() != wx.NOT_FOUND
		# Disable buttons if the placeholder "no songs" line is shown
		real_song = has_sel and self._liked_list.GetCount() > 0 and \
			self._liked_list.GetString(self._liked_list.GetSelection()) not in (
				_("No liked songs yet."),
			)
		self._liked_spotify_btn.Enable(real_song)
		self._liked_youtube_btn.Enable(real_song)
		self._liked_remove_btn.Enable(real_song)
		event.Skip()

	def _get_liked_selection(self):
		"""Return the selected song string, or None."""
		idx = self._liked_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return None
		text = self._liked_list.GetString(idx)
		if text == _("No liked songs yet."):
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

	def _on_liked_remove(self, event):
		idx = self._liked_list.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		song = self._liked_list.GetString(idx)
		if song == _("No liked songs yet."):
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
		self._refresh_liked_list()
		ui.message(_("Removed: %s") % song)

	def _on_liked_refresh(self, event):
		self._refresh_liked_list()
		ui.message(_("Liked songs list refreshed"))


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

		btn_sizer = wx.StdDialogButtonSizer()
		ok_btn = wx.Button(self, wx.ID_OK, label=_("&Add"))
		ok_btn.SetDefault()
		btn_sizer.AddButton(ok_btn)
		btn_sizer.AddButton(wx.Button(self, wx.ID_CANCEL))
		btn_sizer.Realize()
		sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)

		self.SetSizer(sizer)
		self.Fit()
		self.SetMinSize((350, -1))
		wx.CallAfter(self._name.SetFocus)

	def get_values(self):
		return self._name.GetValue().strip(), self._url.GetValue().strip()