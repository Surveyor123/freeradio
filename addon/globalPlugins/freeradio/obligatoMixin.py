# -*- coding: utf-8 -*-
# FreeRadio - Obligato mode (background music)
#
# "Obligato" plays a favourite station quietly in the background on its own
# independent BASS engine (a second, standalone radioPlayer.RadioPlayer
# instance with its own subprocess), so it keeps playing - unaffected by
# whatever the main player is doing (station, podcast, audio book, or
# nothing at all) - until the user explicitly toggles it off again. The one
# exception is pausing: pausing the main player pauses the background
# station too, and resuming the main player resumes it - see
# ObligatoMixin._obligato_sync_loop(). Toggled with Ctrl+Shift+Windows+M.
#
# Mixed into GlobalPlugin, so `self` here is a GlobalPlugin instance -
# self._player, self._manager, and self._check_internet (defined elsewhere
# on GlobalPlugin) are used as normal instance attributes/methods via the
# class's MRO, no import needed for those. self._obligato_* attributes are
# initialised in GlobalPlugin.__init__() in __init__.py, and
# self._terminate_obligato() is called from GlobalPlugin.terminate().

import threading

import config
import gui
import ui
import wx
from scriptHandler import script

from . import radioPlayer
from . import _notifications_muted

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr


# Choices offered in the "Background volume" combo box, expressed as a
# percentage of the main player's current volume.
_VOLUME_RATIO_CHOICES = [5, 10, 25, 50, 75, 100, 125, 150]


class ObligatoDialog(wx.Dialog):
	"""Accessible picker shown when Obligato mode is switched on: which
	favourite station to loop in the background, which output device to
	send it to, and how loud relative to the main player's volume.

	On OK, call get_values() to retrieve (station, device_choice, ratio).
	"""

	def __init__(self, parent, favorites, devices):
		super().__init__(
			parent,
			# Translators: Title of the Obligato mode setup dialog.
			title=_("Obligato Mode"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		self._favorites = favorites

		sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Background station ---
		sizer.Add(
			wx.StaticText(self, label=_("Background station:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8,
		)
		station_names = [
			s.get("name", "").strip() or s.get("url", "") for s in favorites
		]
		self._station_list = wx.ListBox(self, choices=station_names, style=wx.LB_SINGLE)
		self._station_list.SetName(_("Background station:"))
		sizer.Add(self._station_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		saved_uuid = config.conf["freeradio"].get("obligato_station_uuid", "")
		station_selection = 0
		if saved_uuid:
			for i, s in enumerate(favorites):
				if s.get("stationuuid") == saved_uuid:
					station_selection = i
					break
		if favorites:
			self._station_list.SetSelection(station_selection)

		# --- Audio output ---
		sizer.Add(
			wx.StaticText(self, label=_("Audio output:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8,
		)
		# ("same" | "default" | device_index, display label)
		self._device_choices = (
			[("same", _("Same as main output")), ("default", _("System default"))]
			+ [(idx, name) for (idx, name) in devices]
		)
		self._device_combo = wx.Choice(
			self, choices=[label for (_val, label) in self._device_choices]
		)
		self._device_combo.SetName(_("Audio output:"))
		sizer.Add(self._device_combo, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		saved_device = config.conf["freeradio"].get("obligato_audio_device", "same")
		saved_device_name = config.conf["freeradio"].get("obligato_audio_device_name", "")
		device_selection = 0
		if saved_device == "default":
			for i, (val, _label) in enumerate(self._device_choices):
				if val == "default":
					device_selection = i
					break
		elif saved_device and saved_device != "same":
			try:
				saved_index = int(saved_device)
			except (TypeError, ValueError):
				saved_index = None
			for i, (val, label) in enumerate(self._device_choices):
				if isinstance(val, int) and (
					val == saved_index or (saved_device_name and label == saved_device_name)
				):
					device_selection = i
					break
		self._device_combo.SetSelection(device_selection)

		# --- Background volume ---
		sizer.Add(
			wx.StaticText(self, label=_("Background volume:")),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8,
		)
		ratio_labels = []
		for r in _VOLUME_RATIO_CHOICES:
			if r == 100:
				# Translators: Volume option meaning the background station plays at the
				# same level as the main player.
				ratio_labels.append(_("100% (same as main volume)"))
			else:
				# Translators: Volume option expressed as a percentage of the main
				# player's current volume, e.g. "50% of main volume". %d is the percentage.
				ratio_labels.append(_("%d%% of main volume") % r)
		self._volume_combo = wx.Choice(self, choices=ratio_labels)
		self._volume_combo.SetName(_("Background volume:"))
		sizer.Add(self._volume_combo, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		saved_ratio = config.conf["freeradio"].get("obligato_volume_ratio", 50)
		try:
			ratio_selection = _VOLUME_RATIO_CHOICES.index(int(saved_ratio))
		except ValueError:
			ratio_selection = _VOLUME_RATIO_CHOICES.index(50)
		self._volume_combo.SetSelection(ratio_selection)

		# --- OK / Cancel ---
		btn_sizer = wx.StdDialogButtonSizer()
		ok_btn = wx.Button(self, wx.ID_OK, label=_("&Start"))
		ok_btn.SetDefault()
		btn_sizer.AddButton(ok_btn)
		btn_sizer.AddButton(wx.Button(self, wx.ID_CANCEL))
		btn_sizer.Realize()
		sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)

		self.SetSizer(sizer)
		self.Fit()
		self.SetMinSize((360, -1))

		ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)

		if favorites:
			wx.CallAfter(self._station_list.SetFocus)

	def _on_ok(self, event):
		if not self._favorites or self._station_list.GetSelection() == wx.NOT_FOUND:
			ui.message(_("Please select a station for the background music."))
			self._station_list.SetFocus()
			return
		self.EndModal(wx.ID_OK)

	def get_values(self):
		"""Returns (station, device_choice, ratio).
		device_choice is (kind, index_or_None, name) where kind is one of
		"same" / "default" / "device"."""
		station = self._favorites[self._station_list.GetSelection()]
		val, label = self._device_choices[self._device_combo.GetSelection()]
		if val == "same":
			device_choice = ("same", None, "")
		elif val == "default":
			device_choice = ("default", None, "")
		else:
			device_choice = ("device", val, label)
		ratio = _VOLUME_RATIO_CHOICES[self._volume_combo.GetSelection()]
		return station, device_choice, ratio


class ObligatoMixin:
	"""Toggleable background-music mode: loops a chosen favourite station
	on its own independent output, at a volume tied to the main player's
	volume and paused/resumed in step with it, regardless of what plays as
	the main media."""

	@script(
		description=_("Toggle Obligato background music mode"),
		category=_("FreeRadio"),
		# Default binding lives in GlobalPlugin.__gestures - see __init__.py.
	)
	def script_toggleObligato(self, gesture):
		self._toggle_obligato()

	def _toggle_obligato(self):
		if self._obligato_active:
			self._stop_obligato()
			return

		favorites = self._manager.get_favorites()
		if not favorites:
			ui.message(
				_("No favourite stations. Add a station to favourites first to use Obligato mode.")
			)
			return

		if self._obligato_dialog_open:
			return
		self._obligato_dialog_open = True

		def _fetch_devices():
			try:
				devices = self._player.get_audio_devices()
			except Exception:
				devices = []
			wx.CallAfter(self._show_obligato_dialog, favorites, devices)

		threading.Thread(target=_fetch_devices, daemon=True).start()

	def _show_obligato_dialog(self, favorites, devices):
		try:
			gui.mainFrame.prePopup()
			dlg = ObligatoDialog(gui.mainFrame, favorites, devices)
			result = dlg.ShowModal()
			if result == wx.ID_OK:
				station, device_choice, ratio = dlg.get_values()
				self._start_obligato(station, device_choice, ratio)
			dlg.Destroy()
		finally:
			gui.mainFrame.postPopup()
			self._obligato_dialog_open = False

	def _start_obligato(self, station, device_choice, ratio):
		"""Persist the chosen settings and launch the background station
		on a brand-new, fully independent RadioPlayer (its own subprocess),
		off the main thread so the picker dialog closes immediately."""
		kind, index, name = device_choice
		config.conf["freeradio"]["obligato_station_uuid"] = station.get("stationuuid", "")
		config.conf["freeradio"]["obligato_station_name"] = station.get("name", "")
		config.conf["freeradio"]["obligato_station_url"] = station.get("url", "")
		if kind == "device":
			config.conf["freeradio"]["obligato_audio_device"] = str(index)
			config.conf["freeradio"]["obligato_audio_device_name"] = name or ""
		else:
			config.conf["freeradio"]["obligato_audio_device"] = kind
			config.conf["freeradio"]["obligato_audio_device_name"] = ""
		config.conf["freeradio"]["obligato_volume_ratio"] = ratio

		# Stop any previous background player before starting a new one -
		# not currently reachable from the UI (the toggle gesture stops
		# Obligato outright rather than reopening the picker while active),
		# but keeps _start_obligato safe to call more than once.
		previous_player = self._obligato_player
		self._obligato_player = None
		if self._obligato_sync_stop:
			self._obligato_sync_stop.set()

		# Same "prefer the resolved stream URL, fall back to the raw one"
		# rule _play_station() uses in playbackCoreMixin.py.
		url_resolved = station.get("url_resolved", "")
		url = url_resolved or station.get("url", "")
		name_display = station.get("name", "").strip()

		if not url:
			ui.message(_("No stream URL available for this station"))
			return

		def _launch():
			if previous_player:
				try:
					previous_player.terminate()
				except Exception:
					pass

			if not config.conf["freeradio"].get("disable_internet_check", False):
				if not self._check_internet():
					wx.CallAfter(
						ui.message,
						_("No internet connection. Please check your connection and try again."),
					)
					return

			resolved_device = self._resolve_obligato_device(kind, index, name)
			try:
				player = radioPlayer.RadioPlayer(output_device=resolved_device)
			except Exception:
				wx.CallAfter(ui.message, _("Could not start Obligato mode."))
				return
			# play() launches the connection on its own background thread
			# and never blocks / never returns success or failure directly
			# (see RadioPlayer.play()'s _bg_launch) - a failed connection
			# attempt is instead reported asynchronously through this
			# callback, same as the main player's on_play_failed wiring in
			# GlobalPlugin.__init__(). Captured as a closure over *player*
			# (rather than a shared bound method) so a stale failure from a
			# player that's already been replaced/stopped can't be mistaken
			# for the current one.
			def _on_failed(station, url, reason, _player=player):
				wx.CallAfter(self._on_obligato_play_failed_ui, _player, station, url, reason)
			player.on_play_failed = _on_failed

			main_volume = self._player.get_volume()
			effective_volume = max(0, min(200, int(round(main_volume * ratio / 100))))
			player.set_volume(effective_volume)

			player.play(url, name_display, url_resolved=url_resolved, station=station)
			wx.CallAfter(self._on_obligato_started, player, station, ratio, name_display)

		threading.Thread(target=_launch, daemon=True).start()

	def _on_obligato_started(self, player, station, ratio, name_display):
		self._obligato_player = player
		self._obligato_active = True
		self._obligato_station = station
		self._obligato_ratio = ratio
		self._obligato_sync_stop = threading.Event()
		self._obligato_sync_thread = threading.Thread(
			target=self._obligato_sync_loop,
			args=(player, self._obligato_sync_stop),
			daemon=True,
		)
		self._obligato_sync_thread.start()
		if not _notifications_muted():
			ui.message(_("Obligato mode started: %s") % name_display)

	def _obligato_sync_loop(self, player, stop_event):
		"""While Obligato is active, keep the background station in step
		with the main player:
		- Volume stays proportional to the main player's volume, so
		  changing the main volume (e.g. via Ctrl+Windows+Up/Down) scales
		  the background music the same way.
		- Pausing the main player (Ctrl+Windows+P) pauses the background
		  station too, and resuming the main player resumes it - a full
		  stop of the main player (no media loaded at all) is NOT treated
		  as a pause, since Obligato is meant to keep playing regardless of
		  what the main player is doing once nothing is paused there.
		"""
		last_main_volume = None
		last_main_paused = None
		while True:
			if self._obligato_player is not player:
				return
			try:
				main_volume = self._player.get_volume()
				main_paused = self._player.has_media() and not self._player.is_playing()
			except Exception:
				main_volume, main_paused = last_main_volume, last_main_paused

			if main_paused != last_main_paused:
				last_main_paused = main_paused
				try:
					if main_paused:
						player.pause()
					else:
						player.resume()
				except Exception:
					pass

			if main_volume != last_main_volume:
				last_main_volume = main_volume
				effective_volume = max(0, min(200, int(round(main_volume * self._obligato_ratio / 100))))
				try:
					player.set_volume(effective_volume)
				except Exception:
					pass

			if stop_event.wait(1.0):
				return

	def _on_obligato_play_failed_ui(self, player, station, url, reason):
		"""Runs on the main thread. *player* is the specific background
		RadioPlayer instance that failed - only tear down Obligato state if
		it's still the active one; a failure reported after the user has
		already stopped/restarted Obligato just needs that stale instance
		terminated, not the current session touched."""
		name = (station or {}).get("name", "").strip() or url
		ui.message(_("Could not play %(name)s in Obligato mode: %(reason)s") % {
			"name": name, "reason": reason,
		})
		if self._obligato_player is player:
			self._stop_obligato()
		else:
			try:
				player.terminate()
			except Exception:
				pass

	def _stop_obligato(self):
		player = self._obligato_player
		self._obligato_active = False
		self._obligato_player = None
		self._obligato_station = None
		if self._obligato_sync_stop:
			self._obligato_sync_stop.set()
		self._obligato_sync_stop = None

		def _shutdown():
			if player:
				try:
					player.terminate()
				except Exception:
					pass
			if not _notifications_muted():
				wx.CallAfter(ui.message, _("Obligato mode stopped"))

		threading.Thread(target=_shutdown, daemon=True).start()

	def _resolve_obligato_device(self, kind, index, name):
		"""Resolve the dialog's device choice to a concrete BASS device
		index at launch time (not when the dialog was shown), so "same as
		main output" reflects the main player's *current* output device."""
		if kind == "same":
			return getattr(self._player, "_output_device_index", -1)
		if kind == "default":
			return -1
		try:
			devices = self._player.get_audio_devices()
		except Exception:
			devices = []
		resolved_index, _resolved_name, match = self._player.resolve_audio_device(
			devices, index, name or ""
		)
		if match == "missing":
			return -1
		return resolved_index

	def _terminate_obligato(self):
		"""Called from GlobalPlugin.terminate() on add-on unload/NVDA exit."""
		if self._obligato_sync_stop:
			self._obligato_sync_stop.set()
		self._obligato_sync_stop = None
		player = self._obligato_player
		self._obligato_player = None
		self._obligato_active = False
		if player:
			try:
				player.terminate()
			except Exception:
				pass
