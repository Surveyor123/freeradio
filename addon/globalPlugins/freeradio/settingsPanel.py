# -*- coding: utf-8 -*-
# FreeRadio - Settings panel (NVDA Settings > FreeRadio category)
#
# Extracted from __init__.py. GlobalPlugin is looked up lazily via
# _get_freeradio_plugin() (deferred import) rather than imported at module
# load time, since __init__.py imports FreeRadioSettingsPanel from this
# module before GlobalPlugin is defined - a top-level import here would be
# circular.

import os
import threading
import config
import globalPluginHandler
import gui
from gui import guiHelper, nvdaControls
import ui
import wx

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr

from . import (
	_notify,
	_braille_messages_enabled,
	_list_sapi5_voices,
	_audio_device_refresh_mode,
	_AUDIO_DEVICE_REFRESH_MODE_KEYS,
)
from . import radioPlayer
from . import getem


def _get_freeradio_plugin():
	"""Return the running FreeRadio GlobalPlugin instance, or None.

	GlobalPlugin is imported here (not at module level) to avoid a circular
	import, since __init__.py imports this module while building GlobalPlugin.
	"""
	from . import GlobalPlugin
	for plugin in globalPluginHandler.runningPlugins:
		if isinstance(plugin, GlobalPlugin):
			return plugin
	return None


class FreeRadioSettingsPanel(gui.settingsDialogs.SettingsPanel):
	title = _("FreeRadio")

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

		# --- Time-shift buffer checkbox ---
		# Off by default: keeps a rolling ~10 minute local buffer of the
		# live stream so the user can rewind/fast-forward it like a
		# cassette tape. Requires the BASS backend.
		self._timeshift_enabled = wx.CheckBox(
			self,
			label=_("&Enable time-shift buffer (rewind live radio, no effect on potcasts and audio books)")
		)
		self._timeshift_enabled.SetValue(config.conf["freeradio"].get("timeshift_enabled", False))
		sHelper.addItem(self._timeshift_enabled)

		# --- Time-shift buffer duration ---
		self._timeshift_duration_seconds = [600, 1800, 3600, 7200, 18000]
		duration_label = _("Time-shift buffer duration:")
		self._timeshift_duration_choice = sHelper.addLabeledControl(
			duration_label,
			wx.Choice,
			choices=[
				_("10 minutes"), _("30 minutes"), _("1 hour"),
				_("2 hours"), _("5 hours"),
			],
		)
		saved_seconds = config.conf["freeradio"].get("timeshift_buffer_seconds", 600)
		try:
			sel_index = self._timeshift_duration_seconds.index(saved_seconds)
		except ValueError:
			sel_index = 0
		self._timeshift_duration_choice.SetSelection(sel_index)

		self._timeshift_duration_hint = wx.StaticText(
			self,
			label=_("Longer buffers use more temporary disk space, especially for "
			        "high-bitrate stations — a 5-hour buffer can use several gigabytes."),
		)
		self._timeshift_duration_hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
		sHelper.addItem(self._timeshift_duration_hint)

		# --- Audio output device (BASS only) ---
		self._audio_devices = []   # (index, name) list — populated from BASS
		device_label = _("Audio output device (BASS backend):")
		self._device_choice = sHelper.addLabeledControl(
			device_label,
			wx.Choice,
			choices=[_("Loading devices...")],
		)
		self._device_choice.SetName(device_label)

		refresh_label = _("Audio device refresh mode (BASS backend):")
		self._audio_device_refresh_label = wx.StaticText(self, label=refresh_label)
		sHelper.addItem(self._audio_device_refresh_label)
		self._audio_device_refresh_choice = wx.Choice(
			self,
			choices=[
				_("Reliable, refresh device numbers live"),
				_("Fast, use current BASS device list"),
			],
		)
		self._audio_device_refresh_choice.SetName(refresh_label)
		_saved_refresh_mode = _audio_device_refresh_mode()
		self._audio_device_refresh_choice.SetSelection(
			_AUDIO_DEVICE_REFRESH_MODE_KEYS.index(_saved_refresh_mode)
		)
		sHelper.addItem(self._audio_device_refresh_choice)

		self._volume = sHelper.addLabeledControl(
			_("Volume (0-100):"),
			wx.SpinCtrl,
			min=0,
			max=200,
			initial=config.conf["freeradio"]["volume"],
		)

		# --- Audio effects (BASS only) ---
		self._fx_static = wx.StaticText(self, label=_("Audio Effects (BASS backend only):"))
		sHelper.addItem(self._fx_static)

		_fx_keys  = ["chorus", "compressor", "distortion",
		             "echo", "flanger", "gargle", "reverb",
		             "eq_bass", "eq_treble", "eq_vocal"]
		_fx_display = [
			_("Chorus"),
			_("Compressor"),
			_("Distortion"),
			_("Echo"),
			_("Flanger"),
			_("Gargle"),
			_("Reverb"),
			_("EQ: Bass Boost"),
			_("EQ: Treble Boost"),
			_("EQ: Vocal Boost"),
		]
		self._fx_keys = _fx_keys
		self._fx_choice = sHelper.addLabeledControl(
			_("Audio &effects:"),
			nvdaControls.CustomCheckListBox,
			choices=_fx_display,
		)
		_saved_fx = config.conf["freeradio"].get("audio_fx", "none")
		_active = {x.strip() for x in _saved_fx.split(",") if x.strip() != "none"}
		for i, key in enumerate(_fx_keys):
			self._fx_choice.Check(i, key in _active)
		self._fx_choice.Bind(wx.EVT_CHECKLISTBOX, self._on_fx_check)
		self._fx_choice.Bind(wx.EVT_LISTBOX,      self._on_fx_hover)

		# --- EQ gain controls (shown only for active EQ bands) ---
		self._eq_bands_settings = [
			("eq_bass",   _("&Bass gain (dB):"),   9),
			("eq_treble", _("&Treble gain (dB):"), 9),
			("eq_vocal",  _("&Vocal gain (dB):"),  6),
		]
		self._eq_spins_settings = {}
		self._eq_spin_labels_settings = {}
		for band, label, default_db in self._eq_bands_settings:
			lbl = wx.StaticText(self, label=label)
			sHelper.addItem(lbl)
			saved_db = config.conf["freeradio"].get("eq_gain_" + band, default_db)
			spin = wx.SpinCtrl(self, min=-15, max=15, initial=int(saved_db))
			spin.SetName(label)
			sHelper.addItem(spin)
			spin.Bind(wx.EVT_SPINCTRL, lambda evt, b=band: self._on_eq_gain_settings(evt, b))
			self._eq_spins_settings[band] = spin
			self._eq_spin_labels_settings[band] = lbl
		_cf_label = _("Station &switch transition (BASS backend only):")
		_cf_choices = [
			_("Instant cut (no crossfade)"),
			_("Short crossfade (1 second)"),
			_("Normal crossfade (2 seconds)"),
			_("Station tuning sound effect"),
		]
		self._cf_keys = ["off", "short", "normal", "tuning"]
		self._crossfade_choice = sHelper.addLabeledControl(
			_cf_label,
			wx.Choice,
			choices=_cf_choices,
		)
		self._crossfade_choice.SetName(_cf_label)
		_saved_cf = config.conf["freeradio"].get("crossfade", "off")
		self._crossfade_choice.SetSelection(
			self._cf_keys.index(_saved_cf) if _saved_cf in self._cf_keys else 0
		)

		self._resume = wx.CheckBox(self, label=_("&Resume last station on NVDA startup"))
		self._resume.SetValue(config.conf["freeradio"].get("resume_on_start", False))
		sHelper.addItem(self._resume)

		self._announce_track_changes = wx.CheckBox(
			self,
			label=_("&Auto-announce track changes (ICY metadata)"),
		)
		self._announce_track_changes.SetValue(
			config.conf["freeradio"].get("announce_track_changes", False)
		)
		sHelper.addItem(self._announce_track_changes)

		_voice_label = _("Track change &voice:")
		sHelper.addItem(wx.StaticText(self, label=_voice_label))
		self._track_change_voice = wx.Choice(
			self,
			choices=[_("NVDA"), _("SAPI5")],
		)
		self._track_change_voice.SetName(_voice_label)
		_saved_voice = config.conf["freeradio"].get("track_change_voice", "nvda")
		self._track_change_voice.SetSelection(0 if _saved_voice != "sapi5" else 1)
		self._track_change_voice.Enable(
			config.conf["freeradio"].get("announce_track_changes", False)
		)
		sHelper.addItem(self._track_change_voice)

		# SAPI5 voice selector — populated on a background thread to avoid blocking UI.
		_sapi5v_label = _("SAPI5 &voice:")
		sHelper.addItem(wx.StaticText(self, label=_sapi5v_label))
		self._sapi5_voice_choice = wx.Choice(self, choices=[_("Default (system)")])
		self._sapi5_voice_choice.SetName(_sapi5v_label)
		self._sapi5_voice_choice.SetSelection(0)
		_is_sapi5 = _saved_voice == "sapi5"
		_announce_on = config.conf["freeradio"].get("announce_track_changes", False)
		self._sapi5_voice_choice.Enable(_announce_on and _is_sapi5)
		sHelper.addItem(self._sapi5_voice_choice)
		self._sapi5_voice_names = []  # parallel list: [""] + actual voice names

		def _load_sapi5_voices():
			voices = _list_sapi5_voices()
			def _populate():
				if not self:
					return
				saved_name = config.conf["freeradio"].get("sapi5_voice_name", "")
				self._sapi5_voice_names = [""] + voices
				labels = [_("Default (system)")] + voices
				self._sapi5_voice_choice.Set(labels)
				sel = 0
				if saved_name and saved_name in voices:
					sel = voices.index(saved_name) + 1
				self._sapi5_voice_choice.SetSelection(sel)
			wx.CallAfter(_populate)
		import threading as _t
		_t.Thread(target=_load_sapi5_voices, daemon=True).start()

		def _on_voice_combo(e):
			is_sapi5 = self._track_change_voice.GetSelection() == 1
			enabled  = self._announce_track_changes.GetValue()
			self._sapi5_voice_choice.Enable(enabled and is_sapi5)

		self._announce_track_changes.Bind(
			wx.EVT_CHECKBOX,
			lambda e: (
				self._track_change_voice.Enable(e.IsChecked()),
				self._sapi5_voice_choice.Enable(
					e.IsChecked() and self._track_change_voice.GetSelection() == 1
				),
			),
		)
		self._track_change_voice.Bind(wx.EVT_CHOICE, _on_voice_combo)

		self._mute_notifications = wx.CheckBox(
			self,
			label=_("&Mute notifications (station changes, playback, recording)"),
		)
		self._mute_notifications.SetValue(
			config.conf["freeradio"].get("mute_notifications", False)
		)
		sHelper.addItem(self._mute_notifications)

		self._braille_messages = wx.CheckBox(
			self,
			label=_("&Show FreeRadio messages on the braille display"),
		)
		self._braille_messages.SetValue(_braille_messages_enabled())
		sHelper.addItem(self._braille_messages)

		self._save_liked_songs = wx.CheckBox(
			self,
			label=_("&Save liked songs to a text file"),
		)
		self._save_liked_songs.SetValue(
			config.conf["freeradio"].get("save_liked_songs", False)
		)
		sHelper.addItem(self._save_liked_songs)

		hotkey_p_label = _("When Ctrl+Win+P is pressed with no active playback:")
		hotkey_p_choices = [
			_("Resume last station"),
			_("Open favourites list"),
		]
		self._hotkey_p_action = sHelper.addLabeledControl(
			hotkey_p_label,
			wx.Choice,
			choices=hotkey_p_choices,
		)
		current_action = config.conf["freeradio"].get("hotkey_p_action", "resume")
		self._hotkey_p_action.SetSelection(0 if current_action == "resume" else 1)

		hotkey_p_double_label = _("When Ctrl+Win+P is pressed twice:")
		hotkey_p_double_choices = [
			_("Do nothing"),
			_("Open favourites list"),
			_("Open station search"),
			_("Open recording tab"),
			_("Open timer tab"),
			_("Open liked songs tab"),
			_("Open addon settings"),
			_("Announce currently playing station"),
			_("Stop radio"),
		]
		self._hotkey_p_double = sHelper.addLabeledControl(
			hotkey_p_double_label,
			wx.Choice,
			choices=hotkey_p_double_choices,
		)
		_double_map = ["none", "favorites", "search", "recording", "timer", "liked", "settings", "announce", "stop"]
		current_double = config.conf["freeradio"].get("hotkey_p_double", "none")
		self._hotkey_p_double.SetSelection(
			_double_map.index(current_double) if current_double in _double_map else 0
		)

		hotkey_p_triple_label = _("When Ctrl+Win+P is pressed three times:")
		hotkey_p_triple_choices = [
			_("Do nothing"),
			_("Open favourites list"),
			_("Open station search"),
			_("Open recording tab"),
			_("Open timer tab"),
			_("Open liked songs tab"),
			_("Open addon settings"),
			_("Announce currently playing station"),
			_("Stop radio"),
		]
		self._hotkey_p_triple = sHelper.addLabeledControl(
			hotkey_p_triple_label,
			wx.Choice,
			choices=hotkey_p_triple_choices,
		)
		_triple_map = ["none", "favorites", "search", "recording", "timer", "liked", "settings", "announce", "stop"]
		current_triple = config.conf["freeradio"].get("hotkey_p_triple", "none")
		self._hotkey_p_triple.SetSelection(
			_triple_map.index(current_triple) if current_triple in _triple_map else 0
		)

		# --- Music Recognition ---
		sHelper.addItem(wx.StaticText(self, label=_("Music Recognition via Shazam (Ctrl+Win+I × 3):")))
		ffmpeg_label = _("ffmpeg.exe path (optional; auto-used from addon folder if empty):")
		sHelper.addItem(wx.StaticText(self, label=ffmpeg_label))
		ffmpeg_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self._ffmpeg_path = wx.TextCtrl(
			self,
			value=config.conf["freeradio"].get("ffmpeg_path", ""),
		)
		self._ffmpeg_path.SetName(ffmpeg_label)
		ffmpeg_browse = wx.Button(self, label=_("Brows&e..."))
		ffmpeg_sizer.Add(self._ffmpeg_path, 1, wx.EXPAND | wx.RIGHT, 5)
		ffmpeg_sizer.Add(ffmpeg_browse, 0)
		sHelper.addItem(ffmpeg_sizer, flag=wx.EXPAND)
		ffmpeg_browse.Bind(wx.EVT_BUTTON, self._on_browse_ffmpeg)

		# --- Recordings folder ---
		rec_dir_label = _("Recordings folder:")
		sHelper.addItem(wx.StaticText(self, label=rec_dir_label))
		rec_dir_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self._recordings_dir = wx.TextCtrl(
			self,
			value=config.conf["freeradio"].get("recordings_dir", ""),
		)
		self._recordings_dir.SetName(rec_dir_label)
		_default_hint = wx.StaticText(
			self,
			label=_("(empty = default: Documents\\FreeRadio Recordings)"),
		)
		_default_hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
		rec_dir_browse = wx.Button(self, label=_("Brow&se folder..."))
		rec_dir_sizer.Add(self._recordings_dir, 1, wx.EXPAND | wx.RIGHT, 5)
		rec_dir_sizer.Add(rec_dir_browse, 0)
		sHelper.addItem(rec_dir_sizer, flag=wx.EXPAND)
		sHelper.addItem(_default_hint)
		rec_dir_browse.Bind(wx.EVT_BUTTON, self._on_browse_recordings_dir)

		# --- Audio book sources ---
		# A plain checklist, not per-source settings screens - as more
		# sources are added later, they just join _AUDIOBOOK_SOURCE_KEYS/
		# _AUDIOBOOK_SOURCE_DISPLAY below and this list grows with them,
		# no other code here needs to change. Mirrors the "Audio effects"
		# nvdaControls.CustomCheckListBox pattern above (self._fx_choice) - same
		# comma-separated-keys-in-one-string storage shape, just a
		# different config key. Both sources enabled by default (see the
		# "audiobook_sources" confspec default in __init__.py); the
		# actual filtering happens in
		# radioDialog._enabled_audiobook_sources()/_on_getem_search().
		_AUDIOBOOK_SOURCE_KEYS = ["getem", "librivox"]
		# Reuses the exact same bare "GETEM"/"LibriVox" strings
		# RadioDialog._audiobook_source_label_for() already shows next to
		# each book in the Audio Books tab, rather than introducing new,
		# differently-worded translations for the same two names.
		_AUDIOBOOK_SOURCE_DISPLAY = [_("GETEM"), _("LibriVox")]
		self._audiobook_source_keys = _AUDIOBOOK_SOURCE_KEYS
		self._audiobook_sources_choice = sHelper.addLabeledControl(
			_("Audio book &sources:"),
			nvdaControls.CustomCheckListBox,
			choices=_AUDIOBOOK_SOURCE_DISPLAY,
		)
		_saved_audiobook_sources = config.conf["freeradio"].get("audiobook_sources", "getem,librivox")
		_active_audiobook_sources = {s.strip() for s in _saved_audiobook_sources.split(",") if s.strip()}
		for i, key in enumerate(_AUDIOBOOK_SOURCE_KEYS):
			self._audiobook_sources_choice.Check(i, key in _active_audiobook_sources)

		# --- GETEM audio books account ---
		# Credentials are not part of config.conf (which is stored as
		# plain text) - they're saved separately, encrypted with the
		# Windows Data Protection API; see getem.save_credentials().
		sHelper.addItem(wx.StaticText(self, label=_("GETEM Audio Books Account:")))

		getem_username_label = _("GETEM username:")
		sHelper.addItem(wx.StaticText(self, label=getem_username_label))
		_saved_getem_username, _saved_getem_password = getem.load_credentials()
		self._getem_username = wx.TextCtrl(self, value=_saved_getem_username)
		self._getem_username.SetName(getem_username_label)
		sHelper.addItem(self._getem_username, flag=wx.EXPAND)

		getem_password_label = _("GETEM password:")
		sHelper.addItem(wx.StaticText(self, label=getem_password_label))
		self._getem_password = wx.TextCtrl(self, value=_saved_getem_password, style=wx.TE_PASSWORD)
		self._getem_password.SetName(getem_password_label)
		sHelper.addItem(self._getem_password, flag=wx.EXPAND)

		_getem_hint = wx.StaticText(
			self,
			label=_("Stored encrypted on this computer, for this Windows user only. Leave both fields empty and save to remove them."),
		)
		_getem_hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
		sHelper.addItem(_getem_hint)

		# --- Recording output format ---
		recording_format_label = _("Recording output format:")
		self._recording_format_keys = ["original", "audio_only", "mp3"]
		self._recording_format = sHelper.addLabeledControl(
			recording_format_label,
			wx.Choice,
			choices=[
				_("Original stream format (no conversion)"),
				_("Audio only, original codec (no quality loss)"),
				_("MP3 (convert audio)"),
			],
		)
		_saved_recording_format = config.conf["freeradio"].get("recording_format", "original")
		self._recording_format.SetSelection(
			self._recording_format_keys.index(_saved_recording_format)
			if _saved_recording_format in self._recording_format_keys else 0
		)

		mp3_bitrate_label = _("MP3 recording bitrate:")
		self._mp3_bitrate_values = [96, 128, 160, 192, 256, 320]
		self._recording_mp3_bitrate = sHelper.addLabeledControl(
			mp3_bitrate_label,
			wx.Choice,
			choices=["%d kb/s" % value for value in self._mp3_bitrate_values],
		)
		_saved_bitrate = config.conf["freeradio"].get("recording_mp3_bitrate", 128)
		self._recording_mp3_bitrate.SetSelection(
			self._mp3_bitrate_values.index(_saved_bitrate)
			if _saved_bitrate in self._mp3_bitrate_values else 1
		)

		# --- Internet check ---
		self._disable_internet_check = wx.CheckBox(
			self,
			label=_("&Disable internet connectivity check before playing (recommended if DNS is blocked)"),
		)
		self._disable_internet_check.SetValue(
			config.conf["freeradio"].get("disable_internet_check", False)
		)
		sHelper.addItem(self._disable_internet_check)

		# --- Updates ---
		self._auto_check_updates = wx.CheckBox(
			self,
			label=_("&Automatically check for updates on startup"),
		)
		self._auto_check_updates.SetValue(
			config.conf["freeradio"].get("auto_check_updates", True)
		)
		sHelper.addItem(self._auto_check_updates)

		self._check_now_btn = wx.Button(self, label=_("Check for Updates &Now"))
		self._check_now_btn.Bind(wx.EVT_BUTTON, self._on_check_now)
		sHelper.addItem(self._check_now_btn)

		# Load audio devices in the background.
		threading.Thread(target=self._load_devices, daemon=True).start()

	def _load_devices(self):
		"""Fetch device list from BASS in background and pass it to the UI."""
		devices = []
		plugin = _get_freeradio_plugin()
		if plugin:
			try:
				devices = plugin._player.get_audio_devices()
			except Exception:
				pass
		wx.CallAfter(self._populate_devices, devices)

	def _audio_device_name_for_index(self, device_index):
		for idx, name in self._audio_devices:
			if idx == device_index:
				return "" if idx == -1 else name
		return ""

	def _populate_devices(self, devices):
		"""Populate the Choice control with the device list and select the saved device."""
		if not self or not self._device_choice:
			return
		self._audio_devices = [(-1, _("System default"))] + list(devices)
		self._device_choice.Clear()
		for _idx, name in self._audio_devices:
			self._device_choice.Append(name)
		saved = config.conf["freeradio"].get("audio_device", -1)
		saved_name = config.conf["freeradio"].get("audio_device_name", "")
		resolved = saved
		match = "missing"
		plugin = _get_freeradio_plugin()
		if plugin:
			try:
				resolved, resolved_name, match = plugin._player.resolve_audio_device(
					devices,
					saved,
					saved_name,
				)
			except Exception:
				resolved_name = saved_name
		if match == "name" and resolved != saved:
			config.conf["freeradio"]["audio_device"] = resolved
			config.conf["freeradio"]["audio_device_name"] = resolved_name
			plugin = _get_freeradio_plugin()
			if plugin:
				try:
					actual = plugin._player.switch_output_device(resolved)
				except Exception:
					actual = getattr(plugin._player, "_output_device_index", resolved)
				if actual != resolved:
					config.conf["freeradio"]["audio_device"] = actual
					config.conf["freeradio"]["audio_device_name"] = self._audio_device_name_for_index(actual)
					resolved = actual
		elif match == "index" and not saved_name and resolved != -1:
			config.conf["freeradio"]["audio_device_name"] = resolved_name
		sel = 0
		for i, (idx, _name) in enumerate(self._audio_devices):
			if idx == resolved:
				sel = i
				break
		self._device_choice.SetSelection(sel)

	def _on_fx_hover(self, event):
		"""Announce the enabled/disabled state of an effect when focused in the list."""
		idx = event.GetSelection()
		if idx != wx.NOT_FOUND:
			label = self._fx_choice.GetString(idx)
			is_checked = self._fx_choice.IsChecked(idx)
			ui.message(_("%(effect)s %(state)s") % {
				"effect": label,
				"state": _("enabled") if is_checked else _("disabled"),
			})
		event.Skip()

	def _on_fx_check(self, event):
		"""Save to config and apply to player immediately when a selection changes."""
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
		config.conf["freeradio"]["audio_fx"] = fx_str
		plugin = _get_freeradio_plugin()
		if plugin:
			try:
				plugin._player.set_fx(fx_str)
			except Exception:
				pass
		self._update_eq_spins_visibility()

	def _update_eq_spins_visibility(self):
		"""Show EQ gain controls only for the EQ bands that are currently checked."""
		checked = self._fx_choice.GetCheckedItems()
		active_eq = {self._fx_keys[i] for i in checked
		             if 0 <= i < len(self._fx_keys) and
		             self._fx_keys[i] in ("eq_bass", "eq_treble", "eq_vocal")}
		for band in self._eq_spins_settings:
			visible = band in active_eq
			self._eq_spins_settings[band].Show(visible)
			self._eq_spin_labels_settings[band].Show(visible)
		self.Layout()

	def _on_eq_gain_settings(self, event, band):
		"""Apply and save EQ gain change immediately from the settings panel."""
		gain_db = self._eq_spins_settings[band].GetValue()
		config.conf["freeradio"]["eq_gain_" + band] = gain_db
		plugin = _get_freeradio_plugin()
		if plugin:
			try:
				plugin._player.set_eq_gain(band, gain_db)
			except Exception:
				pass
		event.Skip()

	def _on_browse_ffmpeg(self, event):
		with wx.FileDialog(
			self,
			_("Select ffmpeg.exe"),
			wildcard="ffmpeg.exe|ffmpeg.exe|Executable files (*.exe)|*.exe",
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				self._ffmpeg_path.SetValue(dlg.GetPath())

	def _on_check_now(self, event):
		"""Trigger a manual update check from the settings panel."""
		self._check_now_btn.Disable()
		self._check_now_btn.SetLabel(_("Checking..."))
		def _run():
			plugin = _get_freeradio_plugin()
			if plugin:
				plugin._check_for_updates(silent=False)
			wx.CallAfter(self._restore_check_btn)
		threading.Thread(target=_run, daemon=True).start()

	def _restore_check_btn(self):
		"""Re-enable the check button after the update check completes."""
		if self and self._check_now_btn:
			self._check_now_btn.Enable()
			self._check_now_btn.SetLabel(_("Check for Updates &Now"))

	def _on_browse_recordings_dir(self, event):
		current = self._recordings_dir.GetValue().strip()
		start_dir = current if (current and os.path.isdir(current)) else os.path.join(
			os.path.expanduser("~"), "Documents"
		)
		with wx.DirDialog(
			self,
			_("Select recordings folder"),
			defaultPath=start_dir,
			style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
		) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				self._recordings_dir.SetValue(dlg.GetPath())

	def onSave(self):
		vol = self._volume.GetValue()
		config.conf["freeradio"]["volume"]          = min(100, vol)
		config.conf["freeradio"]["resume_on_start"]        = self._resume.GetValue()
		config.conf["freeradio"]["announce_track_changes"] = self._announce_track_changes.GetValue()
		config.conf["freeradio"]["track_change_voice"] = (
			"sapi5" if self._track_change_voice.GetSelection() == 1 else "nvda"
		)
		_sapi5v_sel = self._sapi5_voice_choice.GetSelection()
		config.conf["freeradio"]["sapi5_voice_name"] = (
			self._sapi5_voice_names[_sapi5v_sel]
			if 0 <= _sapi5v_sel < len(self._sapi5_voice_names) else ""
		)
		config.conf["freeradio"]["mute_notifications"]     = self._mute_notifications.GetValue()
		config.conf["freeradio"]["braille_messages"]       = self._braille_messages.GetValue()
		config.conf["freeradio"]["save_liked_songs"]        = self._save_liked_songs.GetValue()
		
		_refresh_sel = self._audio_device_refresh_choice.GetSelection()
		new_audio_device_refresh_mode = (
			_AUDIO_DEVICE_REFRESH_MODE_KEYS[_refresh_sel]
			if 0 <= _refresh_sel < len(_AUDIO_DEVICE_REFRESH_MODE_KEYS)
			else "reliable"
		)
		config.conf["freeradio"]["audio_device_refresh_mode"] = new_audio_device_refresh_mode
		
		# Audio output device
		old_device_index = config.conf["freeradio"].get("audio_device", -1)
		old_device_name = config.conf["freeradio"].get("audio_device_name", "")
		sel = self._device_choice.GetSelection()
		if 0 <= sel < len(self._audio_devices):
			new_device_index, new_device_name = self._audio_devices[sel]
			if new_device_index == -1:
				new_device_name = ""
		else:
			new_device_index = -1
			new_device_name = ""
		config.conf["freeradio"]["audio_device"] = new_device_index
		config.conf["freeradio"]["audio_device_name"] = new_device_name
		
		config.conf["freeradio"]["hotkey_p_action"] = (
			"resume" if self._hotkey_p_action.GetSelection() == 0 else "favorites"
		)
		_double_map = ["none", "favorites", "search", "recording", "timer", "liked", "settings", "announce", "stop"]
		sel = self._hotkey_p_double.GetSelection()
		config.conf["freeradio"]["hotkey_p_double"] = (
			_double_map[sel] if 0 <= sel < len(_double_map) else "none"
		)
		_triple_map = ["none", "favorites", "search", "recording", "timer", "liked", "settings", "announce", "stop"]
		sel = self._hotkey_p_triple.GetSelection()
		config.conf["freeradio"]["hotkey_p_triple"] = (
			_triple_map[sel] if 0 <= sel < len(_triple_map) else "none"
		)
		try:
			config.conf["freeradio"]["ffmpeg_path"] = self._ffmpeg_path.GetValue().strip()
		except (KeyError, AttributeError):
			pass
		
		# Audio effects
		try:
			checked = self._fx_choice.GetCheckedItems()
			active = [self._fx_keys[i] for i in checked if 0 <= i < len(self._fx_keys)]
			config.conf["freeradio"]["audio_fx"] = ",".join(active) if active else "none"
		except (AttributeError, IndexError):
			pass
		
		config.conf["freeradio"]["recordings_dir"] = self._recordings_dir.GetValue().strip()

		# Audio book sources: which of GETEM/LibriVox the Audio Books tab's
		# search actually queries - see
		# radioDialog._enabled_audiobook_sources(). Unlike audio_fx above,
		# an empty selection is saved as-is (an empty string) rather than
		# falling back to a sentinel/default - the user unchecking both is
		# a legitimate ("search nothing") choice, and _on_getem_search()
		# handles that case with its own message.
		try:
			checked = self._audiobook_sources_choice.GetCheckedItems()
			active_sources = [
				self._audiobook_source_keys[i] for i in checked
				if 0 <= i < len(self._audiobook_source_keys)
			]
			config.conf["freeradio"]["audiobook_sources"] = ",".join(active_sources)
		except (AttributeError, IndexError):
			pass

		# GETEM credentials: stored encrypted, outside of config.conf - see
		# getem.save_credentials(). Both fields empty clears any saved
		# credentials rather than leaving the old ones in place.
		_getem_username = self._getem_username.GetValue().strip()
		_getem_password = self._getem_password.GetValue().strip()
		getem.save_credentials(_getem_username, _getem_password)

		_format_sel = self._recording_format.GetSelection()
		_recording_format = (
			self._recording_format_keys[_format_sel]
			if 0 <= _format_sel < len(self._recording_format_keys) else "original"
		)
		config.conf["freeradio"]["recording_format"] = _recording_format
		_bitrate_sel = self._recording_mp3_bitrate.GetSelection()
		_recording_bitrate = (
			self._mp3_bitrate_values[_bitrate_sel]
			if 0 <= _bitrate_sel < len(self._mp3_bitrate_values) else 128
		)
		config.conf["freeradio"]["recording_mp3_bitrate"] = _recording_bitrate
		config.conf["freeradio"]["auto_check_updates"] = self._auto_check_updates.GetValue()
		config.conf["freeradio"]["disable_internet_check"] = self._disable_internet_check.GetValue()

		# Crossfade
		_cf_sel = self._crossfade_choice.GetSelection()
		_cf_val = self._cf_keys[_cf_sel] if 0 <= _cf_sel < len(self._cf_keys) else "off"
		config.conf["freeradio"]["crossfade"] = _cf_val

		# Time-shift buffer
		new_timeshift_enabled = self._timeshift_enabled.GetValue()
		config.conf["freeradio"]["timeshift_enabled"] = new_timeshift_enabled
		_duration_sel = self._timeshift_duration_choice.GetSelection()
		new_timeshift_seconds = (
			self._timeshift_duration_seconds[_duration_sel]
			if 0 <= _duration_sel < len(self._timeshift_duration_seconds) else 600
		)
		config.conf["freeradio"]["timeshift_buffer_seconds"] = new_timeshift_seconds

		plugin = _get_freeradio_plugin()
		if plugin:
			plugin._recorder.set_output_format(
				_recording_format,
				_recording_bitrate,
				config.conf["freeradio"].get("ffmpeg_path", ""),
			)
			plugin._player.set_audio_device_refresh_mode(new_audio_device_refresh_mode)
			plugin._player.set_volume(vol)
			plugin._player.set_timeshift_enabled(new_timeshift_enabled)
			plugin._player.set_timeshift_capacity_seconds(new_timeshift_seconds)
			
			# Apply new audio output device immediately if changed
			if new_device_index != old_device_index or new_device_name != old_device_name:
				try:
					actual_device_index = plugin._player.switch_output_device(new_device_index)
				except Exception:
					actual_device_index = getattr(plugin._player, "_output_device_index", new_device_index)
				if actual_device_index != new_device_index:
					config.conf["freeradio"]["audio_device"] = actual_device_index
					config.conf["freeradio"]["audio_device_name"] = self._audio_device_name_for_index(actual_device_index)
					new_device_index = actual_device_index
					new_device_name = config.conf["freeradio"].get("audio_device_name", "")
				wx.CallAfter(plugin._sync_dialog_device, new_device_index)
				if plugin._dialog and hasattr(plugin._dialog, "refresh_audio_devices"):
					wx.CallAfter(plugin._dialog.refresh_audio_devices, True)
			# Apply FX immediately
			try:
				plugin._player.set_fx(config.conf["freeradio"].get("audio_fx", "none"))
			except Exception:
				pass
			# Apply crossfade / station-tuning transition immediately
			_cf_map = {"off": 0.0, "short": 1.0, "normal": 2.0, "tuning": 0.0}
			_new_cf = config.conf["freeradio"].get("crossfade", "off")
			try:
				plugin._player.set_tuning_effect_enabled(_new_cf == "tuning")
				plugin._player.set_crossfade_duration(_cf_map.get(_new_cf, 0.0))
			except Exception:
				pass
			
			plugin._recorder._volume = vol


