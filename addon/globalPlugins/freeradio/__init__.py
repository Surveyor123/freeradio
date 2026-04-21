# -*- coding: utf-8 -*-

import config
import os
import globalPluginHandler
import globalVars
import gui
from gui import guiHelper
import logging
import threading
import ui
import wx
from scriptHandler import script, getLastScriptRepeatCount
import speech


log = logging.getLogger(__name__)

import addonHandler
addonHandler.initTranslation()


try:
	_ = globals()['_']
except KeyError:
	log.warning("Translation function '_' not found, using fallback.")
	def _(text):
		return text


from . import radioPlayer, stationManager, recorder as recorderModule

if globalVars.appArgs.secure:
	GlobalPlugin = globalPluginHandler.GlobalPlugin


def _init_config():
	config.conf.spec["freeradio"] = {
		"volume":           "integer(default=100, min=0, max=100)",
		"vlc_path":         "string(default='')",
		"wmp_path":         "string(default='')",
		"potplayer_path":   "string(default='')",
		"last_station_url": "string(default='')",
		"last_station_name":"string(default='')",
		"last_station_uuid":"string(default='')",
		"resume_on_start":  "boolean(default=False)",
		"hotkey_p_action":  "string(default='resume')",
		"hotkey_p_double":  "string(default='none')",
		"hotkey_p_triple":  "string(default='none')",
		"ffmpeg_path":       "string(default='')",
		"audio_fx":          "string(default='none')",
		"audio_device":      "integer(default=-1)",
		"disable_bass":          "boolean(default=False)",
		"announce_track_changes":"boolean(default=False)",
		"save_liked_songs":       "boolean(default=False)",
		"recordings_dir":         "string(default='')",
	}

_init_config()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super().__init__()
		disable_bass = config.conf["freeradio"].get("disable_bass", False)
		self._player  = radioPlayer.RadioPlayer(disable_bass=disable_bass)
		self._player.set_volume(config.conf["freeradio"]["volume"])
		# Apply saved audio output device (only if BASS is enabled)
		if not disable_bass:
			_saved_device = config.conf["freeradio"].get("audio_device", -1)
			if _saved_device != -1:
				try:
					self._player.switch_output_device(_saved_device)
				except Exception:
					pass
			# Apply saved audio FX setting
			_saved_fx = config.conf["freeradio"].get("audio_fx", "none")
			if _saved_fx and _saved_fx != "none":
				self._player.set_fx(_saved_fx)
		# Notify and reset settings when audio device is lost
		self._player.on_device_lost = self._on_audio_device_lost
		self._manager = stationManager.StationManager()
		# Initialize Recorder with dll_dir, player_paths, volume and main player reference
		dll_dir = os.path.dirname(os.path.abspath(__file__))
		player_paths = {
			"vlc": config.conf["freeradio"].get("vlc_path", ""),
			"potplayer": config.conf["freeradio"].get("potplayer_path", ""),
			"wmp": config.conf["freeradio"].get("wmp_path", ""),
		}
		self._recorder = recorderModule.Recorder(
			dll_dir=dll_dir,
			player_paths=player_paths,
			volume=config.conf["freeradio"]["volume"],
			main_player=self._player,   # pass main player to avoid interruption
		)
		self._recorder._notify_start  = lambda rec: wx.CallAfter(
			ui.message, _("Recording started: %s") % rec.station.get("name", "")
		)
		self._recorder._notify_finish = lambda rec: wx.CallAfter(
			ui.message, _("Recording finished: %s") % os.path.basename(rec.output_path or "")
		)
		self._stations      = []
		self._current_index = -1
		self._dialog        = None
		gui.NVDASettingsDialog.categoryClasses.append(FreeRadioSettingsPanel)
		_timers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timers.json")
		self._timer_manager = _TimerManager(
			self._player, self._manager,
			save_path=_timers_path,
			play_callback=self._on_station_selected,
		)
		if config.conf["freeradio"].get("resume_on_start"):
			wx.CallAfter(self._resume_last_station)
		wx.CallAfter(self._build_tools_menu)

		# ICY metadata auto-announce
		self._icy_last_title   = None
		self._icy_poll_stop    = threading.Event()
		self._icy_poll_thread  = threading.Thread(
			target=self._icy_poll_loop, daemon=True
		)
		self._icy_poll_thread.start()

	def _build_tools_menu(self):
		"""Add a FreeRadio submenu under NVDA's Tools menu."""
		tools_menu = gui.mainFrame.sysTrayIcon.toolsMenu
		self._freeradio_menu = wx.Menu()

		item_browser = self._freeradio_menu.Append(
			wx.ID_ANY,
			# Translators: Menu item that opens the FreeRadio station browser dialog
			_("Station &Browser...\tCtrl+Win+R"),
		)
		gui.mainFrame.sysTrayIcon.Bind(
			wx.EVT_MENU, lambda evt: wx.CallAfter(self._open_dialog), item_browser
		)

		item_settings = self._freeradio_menu.Append(
			wx.ID_ANY,
			# Translators: Menu item that opens FreeRadio settings in NVDA preferences
			_("FreeRadio &Settings..."),
		)
		gui.mainFrame.sysTrayIcon.Bind(
			wx.EVT_MENU, self._on_menu_settings, item_settings
		)

		self._tools_menu_item = tools_menu.AppendSubMenu(
			self._freeradio_menu,
			# Translators: Label of the FreeRadio submenu in NVDA Tools menu
			_("&FreeRadio"),
		)

	def _on_menu_settings(self, evt):
		"""Open NVDA Settings dialog on the FreeRadio category."""
		wx.CallAfter(
			gui.mainFrame._popupSettingsDialog,
			gui.NVDASettingsDialog,
			FreeRadioSettingsPanel,
		)



	def _start_music_recognition(self, stream_url):
		"""
		Start music recognition via Shazam in a background thread.
		The result is announced via NVDA and copied to the clipboard.
		Concurrent call protection is handled in the musicRecognizer module.
		"""
		from . import musicRecognizer
		dll_dir     = os.path.dirname(os.path.abspath(__file__))
		ffmpeg_path = config.conf["freeradio"].get("ffmpeg_path", "").strip() \
		              or os.path.join(dll_dir, "ffmpeg.exe")

		def _on_result(result):
			if result.success:
				label = result.full_label()
				wx.CallAfter(self._copy_to_clipboard, label)
			else:
				wx.CallAfter(
					ui.message,
					_("Recognition failed: %s") % result.error_msg,
				)

		musicRecognizer.recognize_async(stream_url, ffmpeg_path, "", _on_result)

	def terminate(self):
		try:
			gui.NVDASettingsDialog.categoryClasses.remove(FreeRadioSettingsPanel)
		except ValueError:
			pass

		# Safely remove the FreeRadio submenu from the Tools menu
		try:
			if hasattr(self, "_tools_menu_item") and self._tools_menu_item:
				tools_menu = gui.mainFrame.sysTrayIcon.toolsMenu
				# Use Delete instead of Remove to fully destroy the item and allow clean NVDA shutdown
				tools_menu.Delete(self._tools_menu_item.GetId())
				self._tools_menu_item = None
		except Exception:
			log.debug("FreeRadio: Tools menu item could not be removed", exc_info=True)

		try:
			if hasattr(self, "_freeradio_menu") and self._freeradio_menu:
				self._freeradio_menu.Destroy()
				self._freeradio_menu = None
		except Exception:
			pass

		self._icy_poll_stop.set()
		self._timer_manager.terminate()
		self._player.terminate()
		self._recorder.terminate()

		if self._dialog:
			try:
				self._dialog._force_destroy()
			except Exception:
				pass
			self._dialog = None

		super().terminate()


	@script(
		description=_("Mirror audio to an additional output device"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+m",
	)
	def script_mirrorAudio(self, gesture):
		# If BASS is disabled, the mirror feature will not work
		if config.conf["freeradio"].get("disable_bass", False):
			ui.message(_("Audio mirror requires BASS backend. Enable it in FreeRadio settings."))
			return

		# Stop existing mirror if active
		if self._player.get_mirror_device() is not None:
			self._player.stop_mirror()
			ui.message(_("Audio mirror stopped"))
			return

		if not self._player.has_media():
			ui.message(_("No station is playing"))
			return

		# Prevent opening multiple instances of the dialog
		if getattr(self, "_mirror_dialog_open", False):
			return
		self._mirror_dialog_open = True

		def _fetch_and_show():
			devices = self._player.get_audio_devices()
			if not devices:
				wx.CallAfter(ui.message, _("No audio output devices found"))
				self._mirror_dialog_open = False
				return
			wx.CallAfter(self._show_mirror_dialog, devices)

		threading.Thread(target=_fetch_and_show, daemon=True).start()

	def _show_mirror_dialog(self, devices):
		# devices: list of [index, name] from bass_host
		choices = [name for (_idx, name) in devices]
		try:
			gui.mainFrame.prePopup()
			dlg = wx.SingleChoiceDialog(
				gui.mainFrame,
				_("Select additional output device for audio mirror:"),
				_("Mirror Audio"),
				choices,
			)
			dlg.SetFocus()
			result = dlg.ShowModal()
			if result == wx.ID_OK:
				sel = dlg.GetSelection()
				dev_index, dev_name = devices[sel]

				def _do_mirror():
					ok = self._player.start_mirror(dev_index)
					if ok:
						wx.CallAfter(ui.message, _("Mirroring to: %s") % dev_name)
					else:
						wx.CallAfter(ui.message, _("Could not mirror to: %s") % dev_name)

				threading.Thread(target=_do_mirror, daemon=True).start()
			dlg.Destroy()
		finally:
			gui.mainFrame.postPopup()
			self._mirror_dialog_open = False

	@script(
		description=_("Open FreeRadio station browser"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+r",
	)
	def script_openDialog(self, gesture):
		wx.CallAfter(self._open_dialog)

	@script(
		description=_("Pause or resume FreeRadio playback"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+p",
	)
	def script_pauseResume(self, gesture):
		_double_action = config.conf["freeradio"].get("hotkey_p_double", "none")
		_triple_action = config.conf["freeradio"].get("hotkey_p_triple", "none")

		def _run_action(action):
			if action == "favorites":
				wx.CallAfter(self._open_dialog_on_favorites)
			elif action == "search":
				wx.CallAfter(self._open_dialog_on_search)
			elif action == "recording":
				wx.CallAfter(self._open_dialog_on_tab, 2)
			elif action == "timer":
				wx.CallAfter(self._open_dialog_on_tab, 3)

		repeat = getLastScriptRepeatCount()

		# Triple press
		if repeat >= 2:
			# Cancel double-press timer
			timer = getattr(self, "_pause_resume_timer", None)
			if timer:
				timer.Stop()
				self._pause_resume_timer = None
			if _triple_action != "none":
				_run_action(_triple_action)
			return

		# Double press
		if repeat == 1:
			if _double_action == "none":
				return
			# Cancel single-press timer
			timer = getattr(self, "_pause_resume_timer", None)
			if timer:
				timer.Stop()
				self._pause_resume_timer = None
			_run_action(_double_action)
			return

		# Single press
		_has_media  = self._player.has_media()
		_is_playing = self._player.is_playing()
		_last_url   = config.conf["freeradio"].get("last_station_url", "").strip()
		_action     = config.conf["freeradio"].get("hotkey_p_action", "resume")

		def _do_single_press():
			self._pause_resume_timer = None
			if _has_media:
				if _is_playing:
					self._player.pause()
					ui.message(_("Radio paused"))
				else:
					self._player.resume()
					ui.message(_("Playing"))
				return
			if _action == "favorites":
				self._open_dialog_on_favorites()
			else:
				if _last_url:
					self._resume_last_station()

		# No delay needed if double-press is disabled
		if _double_action == "none":
			_do_single_press()
			return

		# Double-press is enabled: delay single-press so a second keypress can cancel it
		old_timer = getattr(self, "_pause_resume_timer", None)
		if old_timer:
			old_timer.Stop()
		self._pause_resume_timer = wx.CallLater(350, _do_single_press)

	@script(
		description=_("Stop FreeRadio playback"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+s",
	)
	def script_stop(self, gesture):
		has_instant   = self._recorder.is_recording()
		active_sched  = self._recorder.get_active_scheduled()
		has_scheduled = bool(active_sched)

		if has_instant or has_scheduled:
			# Active recording(s) in progress — inform user and ask for confirmation
			parts = []
			if has_instant:
				parts.append(_("Instant recording: %s") % self._recorder.get_station_name())
			for sched_rec in active_sched:
				parts.append(_("Scheduled recording: %s") % sched_rec.station.get("name", "").strip())
			rec_list = "\n".join(parts)
			msg = _(
				"The following recordings are active and will be stopped:\n%s\n\nStop radio and end all recordings?"
			) % rec_list

			def _confirm():
				dlg = wx.MessageDialog(
					gui.mainFrame,
					msg,
					_("Active Recordings"),
					wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
				)
				result = dlg.ShowModal()
				dlg.Destroy()
				if result == wx.ID_YES:
					if self._recorder.is_recording():
						self._recorder.stop(self._player)
					self._recorder.stop_active_scheduled()
					if self._player.has_media():
						self._player.stop()
					self._stations      = []
					self._current_index = -1
					ui.message(_("Radio stopped"))

			wx.CallAfter(_confirm)
			return

		if not self._player.has_media():
			gesture.send()
			return
		self._player.stop()
		self._stations      = []
		self._current_index = -1
		ui.message(_("Radio stopped"))

	@script(
		description=_("Play next station"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+rightArrow",
	)
	def script_nextStation(self, gesture):
		favs = self._manager.get_favorites()
		if not favs or not self._player.has_media():
			gesture.send()
			return
		
		current_station = self._player.get_current_station()
		current_uuid = current_station.get("stationuuid", "") if current_station else ""
		
		# Find current index by stationuuid
		if current_uuid:
			for i, s in enumerate(favs):
				if s.get("stationuuid", "") == current_uuid:
					self._current_index = i
					break
			else:
				# If not found, reset to -1
				self._current_index = -1
		else:
			# Fallback to name comparison for backward compatibility
			current_name = self._player.get_current_name()
			fav_names = [s.get("name", "").strip() for s in favs]
			if current_name in fav_names:
				self._current_index = fav_names.index(current_name)
			else:
				self._current_index = -1
		
		self._current_index = (self._current_index + 1) % len(favs)
		self._stations = favs
		self._play_station(favs[self._current_index])

	@script(
		description=_("Play previous station"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+leftArrow",
	)
	def script_prevStation(self, gesture):
		favs = self._manager.get_favorites()
		if not favs or not self._player.has_media():
			gesture.send()
			return
		
		current_station = self._player.get_current_station()
		current_uuid = current_station.get("stationuuid", "") if current_station else ""
		
		# Find current index by stationuuid
		if current_uuid:
			for i, s in enumerate(favs):
				if s.get("stationuuid", "") == current_uuid:
					self._current_index = i
					break
			else:
				# If not found, reset to -1
				self._current_index = -1
		else:
			# Fallback to name comparison for backward compatibility
			current_name = self._player.get_current_name()
			fav_names = [s.get("name", "").strip() for s in favs]
			if current_name in fav_names:
				self._current_index = fav_names.index(current_name)
			else:
				self._current_index = -1
		
		self._current_index = (self._current_index - 1) % len(favs)
		self._stations = favs
		self._play_station(favs[self._current_index])

	@script(
		description=_("Add currently playing station to favourites"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+v",
	)
	def script_addToFavorites(self, gesture):
		station = self._player.get_current_station()
		if not station:
			ui.message(_("No station is playing"))
			return
		if self._manager.is_favorite(station):
			ui.message(_("Already in favourites: %s") % station.get("name", "").strip())
			return
		self._manager.add_favorite(station)
		ui.message(_("Added to favourites: %s") % station.get("name", "").strip())

	@script(
		description=_("Announce currently playing station. Press twice for full details."),
		category=_("FreeRadio"),
		gesture="kb:control+windows+i",
	)
	def script_whatsPlaying(self, gesture):
		active_sched = self._recorder.get_active_scheduled()

		if not self._player.has_media():
			# Radio inactive but a scheduled recording may still be running
			if active_sched:
				parts = [_("Radio inactive. Active scheduled recordings:")]
				for sched_rec in active_sched:
					parts.append(sched_rec.station.get("name", "").strip())
				ui.message("  ".join(parts))
			else:
				ui.message(_("FreeRadio is not active"))
			return
		name = self._player.get_current_name()
		repeat = getLastScriptRepeatCount()

		if repeat == 0:
			if self._player.is_playing():
				# Generate a new token on each call; the thread only speaks
				# if its own token is still current (i.e. no second press arrived).
				import time as _time
				token = _time.monotonic()
				self._whats_playing_token = token

				def _announce(tok=token):
					from . import radioPlayer as _rp
					icy = self._player.get_icy_title()
					if not icy:
						url = (
							getattr(self._player, "_current_url_resolved", None)
							or getattr(self._player, "_current_url", None)
						)
						if url:
							icy = _rp._read_icy_title(url)
					# If token changed, a second (or later) press arrived — abort.
					if getattr(self, "_whats_playing_token", None) != tok:
						return
					if icy:
						msg = _("Playing: %(station)s — %(track)s") % {
							"station": name, "track": icy
						}
					else:
						msg = _("Playing: %s") % name
					# Announce instant recording if active
					if self._recorder.is_recording():
						rec_name = self._recorder.get_station_name()
						msg += ". " + _("Recording: %s") % rec_name
					# Announce active scheduled recordings
					active_sched = self._recorder.get_active_scheduled()
					for sched_rec in active_sched:
						sched_name = sched_rec.station.get("name", "").strip()
						msg += ". " + _("Scheduled recording: %s") % sched_name
					wx.CallAfter(ui.message, msg)
				threading.Thread(target=_announce, daemon=True).start()
			else:
				msg = _("Paused: %s") % name
				# Announce instant recording even while paused
				if self._recorder.is_recording():
					rec_name = self._recorder.get_station_name()
					msg += ". " + _("Recording: %s") % rec_name
				# Announce active scheduled recordings
				active_sched = self._recorder.get_active_scheduled()
				for sched_rec in active_sched:
					sched_name = sched_rec.station.get("name", "").strip()
					msg += ". " + _("Scheduled recording: %s") % sched_name
				ui.message(msg)

		elif repeat == 1:
			# Second press: cancel single-press thread.
			# Delay dialog open; a third press can cancel via CallLater.
			self._whats_playing_token = None
			old_dlg_timer = getattr(self, "_whats_playing_dlg_timer", None)
			if old_dlg_timer:
				old_dlg_timer.Stop()
			def _open_dialog():
				self._whats_playing_dlg_timer = None
				if not getattr(self, "_whats_playing_dialog_open", False):
					self._whats_playing_dialog_open = True
					self._show_station_details_dialog()
			self._whats_playing_dlg_timer = wx.CallLater(350, _open_dialog)

		elif repeat == 2:
			# Third press: cancel dialog timer.
			# If ICY metadata is available → copy to clipboard; otherwise start Shazam recognition.
			self._whats_playing_token = None
			dlg_timer = getattr(self, "_whats_playing_dlg_timer", None)
			if dlg_timer:
				dlg_timer.Stop()
				self._whats_playing_dlg_timer = None
			def _copy_or_recognize():
				from . import radioPlayer as _rp
				icy = self._player.get_icy_title()
				if not icy:
					url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if url:
						icy = _rp._read_icy_title(url)

				if icy:
					# ICY info available — copy to clipboard
					wx.CallAfter(self._copy_to_clipboard, icy)
				else:
					# No ICY metadata — try Shazam recognition
					stream_url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if not stream_url:
						wx.CallAfter(ui.message, _("No track info available"))
						return
					wx.CallAfter(
						ui.message,
						_("No track metadata found. Starting music recognition…"),
					)
					self._start_music_recognition(stream_url)

			threading.Thread(target=_copy_or_recognize, daemon=True).start()

	@script(
		description=_("Increase FreeRadio volume by 10"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+upArrow",
	)
	def script_volumeUp(self, gesture):
		vol = min(200, self._player.get_volume() + 10)
		self._player.set_volume(vol)
		config.conf["freeradio"]["volume"] = min(100, vol)
		ui.message(_("Volume %d") % vol)
		self._sync_dialog_volume(vol)

	@script(
		description=_("Decrease FreeRadio volume by 10"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+downArrow",
	)
	def script_volumeDown(self, gesture):
		vol = max(0, self._player.get_volume() - 10)
		self._player.set_volume(vol)
		config.conf["freeradio"]["volume"] = min(100, vol)
		ui.message(_("Volume %d") % vol)
		self._sync_dialog_volume(vol)

	def _sync_dialog_volume(self, vol):
		"""Update the volume SpinCtrl in the browser dialog if it is open."""
		if self._dialog and self._dialog.IsShown():
			try:
				self._dialog._vol_spin.SetValue(vol)
			except Exception:
				pass

	def _sync_dialog_audio(self, vol, fx_str):
		"""Update both the volume SpinCtrl and effects CheckListBox in the browser dialog."""
		if self._dialog and self._dialog.IsShown():
			try:
				self._dialog._vol_spin.SetValue(vol)
			except Exception:
				pass
			try:
				active = {x.strip() for x in fx_str.split(",") if x.strip() != "none"}
				for i, key in enumerate(self._dialog._fx_keys):
					self._dialog._fx_choice.Check(i, key in active)
			except Exception:
				pass

	def _sync_dialog_device(self, device_index):
		"""Update the device Choice in the browser dialog when changed from the settings panel."""
		if self._dialog and self._dialog.IsShown() and hasattr(self._dialog, "_device_choice"):
			try:
				devices = self._dialog._dialog_audio_devices
				for i, (idx, _name) in enumerate(devices):
					if idx == device_index:
						self._dialog._device_choice.SetSelection(i)
						break
			except Exception:
				pass

	def _whats_playing_from_dialog(self):
		"""It is called up from the station window when F2 is pressed.
		First press → announce player, second press → detail dialog, third press → copy to clipboard / Shazam."""
		import time as _time

		active_sched = self._recorder.get_active_scheduled()

		if not self._player.has_media():
			if active_sched:
				parts = [_("Radio inactive. Active scheduled recordings:")]
				for sched_rec in active_sched:
					parts.append(sched_rec.station.get("name", "").strip())
				ui.message("  ".join(parts))
			else:
				ui.message(_("FreeRadio is not active"))
			return

		name = self._player.get_current_name()

		# Counter: increase the counter if pressed again within 600 ms from the last press time
		now = _time.monotonic()
		last_t = getattr(self, "_f2_last_time", 0)
		count  = getattr(self, "_f2_count", 0)

		if now - last_t < 0.6:
			count += 1
		else:
			count = 0

		self._f2_last_time = now
		self._f2_count     = count

		if count == 0:
			# First press: announce what's playing
			if self._player.is_playing():
				token = _time.monotonic()
				self._whats_playing_token = token

				def _announce(tok=token):
					from . import radioPlayer as _rp
					icy = self._player.get_icy_title()
					if not icy:
						url = (
							getattr(self._player, "_current_url_resolved", None)
							or getattr(self._player, "_current_url", None)
						)
						if url:
							icy = _rp._read_icy_title(url)
					if getattr(self, "_whats_playing_token", None) != tok:
						return
					if icy:
						msg = _("Playing: %(station)s — %(track)s") % {
							"station": name, "track": icy
						}
					else:
						msg = _("Playing: %s") % name
					if self._recorder.is_recording():
						msg += ". " + _("Recording: %s") % self._recorder.get_station_name()
					for sched_rec in self._recorder.get_active_scheduled():
						msg += ". " + _("Scheduled recording: %s") % sched_rec.station.get("name", "").strip()
					wx.CallAfter(ui.message, msg)
				threading.Thread(target=_announce, daemon=True).start()
			else:
				msg = _("Paused: %s") % name
				if self._recorder.is_recording():
					msg += ". " + _("Recording: %s") % self._recorder.get_station_name()
				for sched_rec in active_sched:
					msg += ". " + _("Scheduled recording: %s") % sched_rec.station.get("name", "").strip()
				ui.message(msg)

		elif count == 1:
			# Second press: details dialogue
			self._whats_playing_token = None
			old_dlg_timer = getattr(self, "_whats_playing_dlg_timer", None)
			if old_dlg_timer:
				old_dlg_timer.Stop()
			def _open_details():
				self._whats_playing_dlg_timer = None
				if not getattr(self, "_whats_playing_dialog_open", False):
					self._whats_playing_dialog_open = True
					self._show_station_details_dialog()
			self._whats_playing_dlg_timer = wx.CallLater(350, _open_details)

		elif count >= 2:
			# Third press: copy to clipboard / Shazam
			self._whats_playing_token = None
			dlg_timer = getattr(self, "_whats_playing_dlg_timer", None)
			if dlg_timer:
				dlg_timer.Stop()
				self._whats_playing_dlg_timer = None

			def _copy_or_recognize():
				from . import radioPlayer as _rp
				icy = self._player.get_icy_title()
				if not icy:
					url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if url:
						icy = _rp._read_icy_title(url)
				if icy:
					wx.CallAfter(self._copy_to_clipboard, icy)
				else:
					stream_url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if not stream_url:
						wx.CallAfter(ui.message, _("No track info available"))
						return
					wx.CallAfter(ui.message, _("No track metadata found. Starting music recognition…"))
					self._start_music_recognition(stream_url)
				self._f2_count = 0  # reset counter

			threading.Thread(target=_copy_or_recognize, daemon=True).start()

	def _stop_from_dialog(self):
		"""Called from the station window when F8 is pressed — same logic as script_stop."""
		has_instant   = self._recorder.is_recording()
		active_sched  = self._recorder.get_active_scheduled()
		has_scheduled = bool(active_sched)

		if has_instant or has_scheduled:
			parts = []
			if has_instant:
				parts.append(_("Instant recording: %s") % self._recorder.get_station_name())
			for sched_rec in active_sched:
				parts.append(_("Scheduled recording: %s") % sched_rec.station.get("name", "").strip())
			rec_list = "\n".join(parts)
			msg = _(
				"The following recordings are active and will be stopped:\n%s\n\nStop radio and end all recordings?"
			) % rec_list

			def _confirm():
				dlg = wx.MessageDialog(
					gui.mainFrame,
					msg,
					_("Active Recordings"),
					wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
				)
				result = dlg.ShowModal()
				dlg.Destroy()
				if result == wx.ID_YES:
					if self._recorder.is_recording():
						self._recorder.stop(self._player)
					self._recorder.stop_active_scheduled()
					if self._player.has_media():
						self._player.stop()
					self._stations      = []
					self._current_index = -1
					ui.message(_("Radio stopped"))

			wx.CallAfter(_confirm)
			return

		if not self._player.has_media():
			ui.message(_("FreeRadio is not active"))
			return

		self._player.stop()
		self._stations      = []
		self._current_index = -1
		ui.message(_("Radio stopped"))

	def _on_audio_device_lost(self, lost_index):
		"""Called from a background thread when the selected audio device is removed.

		Resets config and dialog to system default (-1), then notifies the user via NVDA.
		"""
		try:
			config.conf["freeradio"]["audio_device"] = -1
		except Exception:
			pass
		wx.CallAfter(self._on_audio_device_lost_ui, lost_index)

	def _on_audio_device_lost_ui(self, lost_index):
		"""Runs on the main thread: syncs dialog and settings panel, then announces to user."""
		self._sync_dialog_device(-1)
		try:
			for win in wx.GetTopLevelWindows():
				if isinstance(win, gui.NVDASettingsDialog):
					panel = win.FindWindowByName("FreeRadio")
					if panel and hasattr(panel, "_populate_devices"):
						panel._populate_devices(panel._audio_devices)
					break
		except Exception:
			pass
		ui.message(_("Audio device disconnected. Switched to system default."))

	@script(
		description=_("Start or stop instant recording"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+e",
	)
	def script_toggleRecord(self, gesture):
		if self._recorder.is_recording():
			path = self._recorder.stop(self._player)
			if path:
				ui.message(_("Recording stopped: %s") % os.path.basename(path))
			else:
				ui.message(_("Recording stopped"))
			return
		if not self._player.has_media():
			ui.message(_("No station is playing"))
			return
		name = self._player.get_current_name()
		self._recorder.start(self._player, name)
		ui.message(_("Recording started: %s") % name)

	@script(
		description=_("Open FreeRadio recordings folder"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+w",
	)
	def script_openRecordingsFolder(self, gesture):
		custom_dir = config.conf["freeradio"].get("recordings_dir", "").strip()
		if custom_dir and os.path.isabs(custom_dir):
			recordings_dir = custom_dir
		else:
			recordings_dir = os.path.join(os.path.expanduser("~"), "Documents", "FreeRadio Recordings")
		os.makedirs(recordings_dir, exist_ok=True)
		try:
			os.startfile(recordings_dir)
		except Exception as e:
			ui.message(_("Could not open recordings folder: %s") % str(e))

	def _open_dialog(self):
		if self._dialog is None:
			from .radioDialog import RadioDialog
			gui.mainFrame.prePopup()
			self._dialog = RadioDialog(
				gui.mainFrame,
				self._manager,
				self._player,
				self._on_station_selected,
				recorder=self._recorder,
				timer_manager=self._timer_manager,
				plugin=self,
			)
		if not self._dialog.IsShown():
			self._dialog.Show()
		self._dialog.Raise()

	def _open_dialog_on_favorites(self):
		self._open_dialog()
		if self._dialog:
			wx.CallAfter(self._dialog.focus_favorites)

	def _open_dialog_on_search(self):
		self._open_dialog()
		if self._dialog:
			wx.CallAfter(self._dialog.focus_search)

	def _open_dialog_on_tab(self, tab_index):
		"""Open the dialog and switch to the given tab (0=All, 1=Favs, 2=Rec, 3=Timer)."""
		self._open_dialog()
		if self._dialog:
			wx.CallAfter(self._dialog.focus_tab, tab_index)

	def _on_station_selected(self, station, stations, index, announce=True):
		self._stations      = stations
		self._current_index = index
		self._play_station(station, announce)

	def _resume_last_station(self):
		url  = config.conf["freeradio"].get("last_station_url", "").strip()
		name = config.conf["freeradio"].get("last_station_name", "").strip()
		uuid = config.conf["freeradio"].get("last_station_uuid", "").strip()
		
		if not url:
			return
		
		station = None
		# First try to find by stationuuid
		if uuid:
			for s in self._manager.get_favorites():
				if s.get("stationuuid", "") == uuid:
					station = s
					break
		
		# If not found by uuid, try by URL
		if station is None:
			for s in self._manager.get_favorites():
				if s.get("url_resolved", "") == url or s.get("url", "") == url:
					station = s
					break
		
		# If still not found, create a minimal station object
		if station is None:
			station = {
				"name": name, 
				"url": url, 
				"url_resolved": url,
				"stationuuid": uuid, 
				"countrycode": "", 
				"tags": "", 
				"votes": 0
			}
		
		self._play_station(station)

	def _build_station_details(self):
		"""Return station information (including stream URL) as a list of (label, value) rows."""
		from .radioDialog import _country_name
		s = self._player.get_current_station()
		if not s:
			return []

		rows = []

		name = s.get("name", "").strip()
		if name:
			rows.append((_("Station"), name))

		icy = self._player.get_icy_title()
		if icy:
			rows.append((_("Now playing"), icy))

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
			first_tags = ", ".join(
				t.strip() for t in tags.split(",")[:5] if t.strip()
			)
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

		stream_url = s.get("url_resolved", "").strip() or s.get("url", "").strip()
		if stream_url:
			rows.append((_("Stream URL"), stream_url))

		votes = s.get("votes", 0)
		try:
			votes = int(votes)
		except (TypeError, ValueError):
			votes = 0
		if votes:
			rows.append((_("Votes"), str(votes)))

		return rows

	def _show_station_details_dialog(self):
		"""Show station details in an accessible dialog window."""
		rows = self._build_station_details()
		if not rows:
			ui.message(_("No station detail available"))
			return

		dlg = wx.Dialog(
			gui.mainFrame,
			title=_("Station Details"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		sizer = wx.BoxSizer(wx.VERTICAL)

		# One label + read-only text box per field.
		# NVDA reads this as "Label: value, read-only edit"; Tab navigates between fields.
		grid = wx.FlexGridSizer(cols=2, vgap=6, hgap=8)
		grid.AddGrowableCol(1, 1)

		field_ctrls = {}  # field_name -> TextCtrl (for later updates)
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
			field_ctrls[field] = ctrl
			if first_ctrl is None:
				first_ctrl = ctrl

		sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 10)

		# "Copy all" button — copies all details to clipboard in one action
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

		# If track info is not yet available, fetch it in the background and insert into dialog
		now_playing_label = _("Now playing")
		if now_playing_label not in field_ctrls:
			def _fetch_icy_and_update():
				from . import radioPlayer as _rp
				icy = self._player.get_icy_title()
				if not icy:
					url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if url:
						icy = _rp._read_icy_title(url)
				if not icy:
					return

				def _insert_icy():
					if not dlg or not dlg.IsShown():
						return
					station_label = _("Station")
					insert_pos = 0
					for i, (f, v) in enumerate(rows):
						if f == station_label:
							insert_pos = i + 1
							break
					rows.insert(insert_pos, (now_playing_label, icy))
					grid.Clear(True)
					field_ctrls.clear()
					for field, value in rows:
						lbl = wx.StaticText(dlg, label=field + ":")
						ctrl = wx.TextCtrl(
							dlg,
							value=value,
							style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_SIMPLE,
						)
						ctrl.SetName(field)
						line_height = ctrl.GetCharHeight()
						line_count  = max(1, value.count("\n") + 1)
						ctrl.SetMinSize((-1, line_height * line_count + 8))
						grid.Add(lbl,  0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
						grid.Add(ctrl, 1, wx.EXPAND)
						field_ctrls[field] = ctrl
					dlg.SetSize((580, min(120 + len(rows) * 38, 520)))
					dlg.Layout()

				wx.CallAfter(_insert_icy)

			threading.Thread(target=_fetch_icy_and_update, daemon=True).start()

		gui.mainFrame.prePopup()
		dlg.ShowModal()
		dlg.Destroy()
		gui.mainFrame.postPopup()
		self._whats_playing_dialog_open = False

	def _announce_station_details(self):
		"""Voice announcement — repeat==1 now opens a dialog; kept for internal use."""
		rows = self._build_station_details()
		if rows:
			ui.message("  ".join("%s: %s" % (k, v) for k, v in rows))
		else:
			ui.message(_("No station detail available"))

	def _copy_to_clipboard(self, text):
		if wx.TheClipboard.Open():
			wx.TheClipboard.SetData(wx.TextDataObject(text))
			wx.TheClipboard.Close()
			ui.message(_("Copied: %s") % text)
		else:
			ui.message(_("Could not access clipboard"))
		# Save to likedSongs.txt if the option is enabled
		if config.conf["freeradio"].get("save_liked_songs", False):
			try:
				custom_dir = config.conf["freeradio"].get("recordings_dir", "").strip()
				if custom_dir and os.path.isabs(custom_dir):
					recordings_dir = custom_dir
				else:
					recordings_dir = os.path.join(os.path.expanduser("~"), "Documents", "FreeRadio Recordings")
				os.makedirs(recordings_dir, exist_ok=True)
				liked_path = os.path.join(recordings_dir, "likedSongs.txt")
				with open(liked_path, "a", encoding="utf-8") as fh:
					fh.write("%s\n" % text)
			except Exception as e:
				log.error("FreeRadio: could not save liked song: %s", e)

	def _icy_poll_loop(self):
		"""Background thread: polls ICY metadata every ~5 s and announces changes."""
		import time as _time
		_INTERVAL = 5.0
		while not self._icy_poll_stop.wait(timeout=_INTERVAL):
			try:
				if not config.conf["freeradio"].get("announce_track_changes", False):
					continue
				if not self._player.is_playing():
					# Player stopped/paused — clear memory so stale title is never re-announced
					self._icy_last_title = None
					continue
				icy = self._player.get_icy_title()
				if not icy:
					from . import radioPlayer as _rp
					url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if url:
						icy = _rp._read_icy_title(url)

				if not icy:
					# This station publishes no ICY metadata.
					# Wipe last title so we never repeat the previous station's track
					# if/when we return to a metadata-capable station later.
					self._icy_last_title = ""
					continue

				if self._icy_last_title is None:
					# First read after a station change — announce immediately and store.
					self._icy_last_title = icy
					wx.CallAfter(ui.message, icy)
					continue

				if icy != self._icy_last_title:
					self._icy_last_title = icy
					wx.CallAfter(ui.message, icy)
			except Exception:
				pass

	def _play_station(self, station, announce=True):
		name         = station.get("name", _("Unknown station")).strip()
		url_resolved = station.get("url_resolved", "")
		url          = url_resolved or station.get("url", "")
		station_uuid = station.get("stationuuid", "")

		if not url:
			ui.message(_("No stream URL available for this station"))
			return

		try:
			config.conf["freeradio"]["last_station_url"]  = url_resolved or url
			config.conf["freeradio"]["last_station_name"] = name
			config.conf["freeradio"]["last_station_uuid"] = station_uuid
		except Exception:
			pass

		# Apply station-specific audio profile if one exists, else restore global settings
		station_audio = station.get("station_audio")
		disable_bass = config.conf["freeradio"].get("disable_bass", False)
		if station_audio and not disable_bass:
			vol = station_audio.get("volume", config.conf["freeradio"]["volume"])
			fx  = station_audio.get("fx", "none")
			self._player.set_volume(vol)
			try:
				self._player.set_fx(fx)
			except Exception:
				pass
			self._sync_dialog_audio(vol, fx)
		else:
			# Restore global settings
			global_vol = config.conf["freeradio"]["volume"]
			global_fx  = config.conf["freeradio"].get("audio_fx", "none")
			self._player.set_volume(global_vol)
			if not disable_bass:
				try:
					self._player.set_fx(global_fx)
				except Exception:
					pass
			self._sync_dialog_audio(global_vol, global_fx)

		self._pending_url     = url
		self._pending_station = station
		self._icy_last_title  = None        # None = station just changed; suppress first read
		wx.CallAfter(self._start_playing, url, name, url_resolved)
		if announce:
			wx.CallAfter(ui.message, name)

	def _start_playing(self, url, name, url_resolved=""):
		station = getattr(self, "_pending_station", {})
		try:
			self._player.play(url, name, url_resolved=url_resolved, station=station)
		except RuntimeError as e:
			if "wmp_not_available" in str(e):
				ui.message(_(
					"Could not play station: Windows Media Player is not available "
					"on this system. Please install VLC media player."
				))
			else:
				ui.message(_("Could not play station: %s") % str(e))
		except Exception as e:
			ui.message(_("Could not play station: %s") % str(e))


class FreeRadioSettingsPanel(gui.settingsDialogs.SettingsPanel):
	title = _("FreeRadio")

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

		# --- Disable BASS backend checkbox ---
		self._disable_bass = wx.CheckBox(
			self,
			label=_("&Disable BASS backend (use VLC/PotPlayer/WMP instead)")
		)
		self._disable_bass.SetValue(config.conf["freeradio"].get("disable_bass", False))
		self._disable_bass.Bind(wx.EVT_CHECKBOX, self._on_disable_bass_changed)
		sHelper.addItem(self._disable_bass)

		# Hint text for BASS-dependent features
		self._bass_hint = wx.StaticText(
			self,
			label=_("Note: Audio device selection, effects, and mirroring require BASS backend.")
		)
		self._bass_hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
		sHelper.addItem(self._bass_hint)

		# --- Audio output device (BASS only) ---
		self._audio_devices = []   # (index, name) list — populated from BASS
		device_label = _("Audio output device (BASS backend):")
		self._device_choice = sHelper.addLabeledControl(
			device_label,
			wx.Choice,
			choices=[_("Loading devices...")],
		)
		self._device_choice.SetName(device_label)

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
			wx.CheckListBox,
			choices=_fx_display,
		)
		_saved_fx = config.conf["freeradio"].get("audio_fx", "none")
		_active = {x.strip() for x in _saved_fx.split(",") if x.strip() != "none"}
		for i, key in enumerate(_fx_keys):
			self._fx_choice.Check(i, key in _active)
		self._fx_choice.Bind(wx.EVT_CHECKLISTBOX, self._on_fx_check)
		self._fx_choice.Bind(wx.EVT_LISTBOX,      self._on_fx_hover)

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
		]
		self._hotkey_p_double = sHelper.addLabeledControl(
			hotkey_p_double_label,
			wx.Choice,
			choices=hotkey_p_double_choices,
		)
		_double_map = ["none", "favorites", "search", "recording", "timer"]
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
		]
		self._hotkey_p_triple = sHelper.addLabeledControl(
			hotkey_p_triple_label,
			wx.Choice,
			choices=hotkey_p_triple_choices,
		)
		_triple_map = ["none", "favorites", "search", "recording", "timer"]
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

		vlc_label = _("VLC path (optional, auto-detected if empty):")
		sHelper.addItem(wx.StaticText(self, label=vlc_label))
		vlc_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self._vlc_path = wx.TextCtrl(self, value=config.conf["freeradio"].get("vlc_path", ""))
		self._vlc_path.SetName(vlc_label)
		vlc_browse = wx.Button(self, label=_("&Browse..."))
		vlc_sizer.Add(self._vlc_path, 1, wx.EXPAND | wx.RIGHT, 5)
		vlc_sizer.Add(vlc_browse, 0)
		sHelper.addItem(vlc_sizer, flag=wx.EXPAND)
		vlc_browse.Bind(wx.EVT_BUTTON, self._on_browse_vlc)

		wmp_label = _("wmplayer.exe path (optional, used if VLC not found):")
		sHelper.addItem(wx.StaticText(self, label=wmp_label))
		wmp_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self._wmp_path = wx.TextCtrl(self, value=config.conf["freeradio"].get("wmp_path", ""))
		self._wmp_path.SetName(wmp_label)
		wmp_browse = wx.Button(self, label=_("B&rowse..."))
		wmp_sizer.Add(self._wmp_path, 1, wx.EXPAND | wx.RIGHT, 5)
		wmp_sizer.Add(wmp_browse, 0)
		sHelper.addItem(wmp_sizer, flag=wx.EXPAND)
		wmp_browse.Bind(wx.EVT_BUTTON, self._on_browse_wmp)

		pot_label = _("PotPlayer path (optional, auto-detected if empty):")
		sHelper.addItem(wx.StaticText(self, label=pot_label))
		pot_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self._pot_path = wx.TextCtrl(self, value=config.conf["freeradio"].get("potplayer_path", ""))
		self._pot_path.SetName(pot_label)
		pot_browse = wx.Button(self, label=_("Bro&wse..."))
		pot_sizer.Add(self._pot_path, 1, wx.EXPAND | wx.RIGHT, 5)
		pot_sizer.Add(pot_browse, 0)
		sHelper.addItem(pot_sizer, flag=wx.EXPAND)
		pot_browse.Bind(wx.EVT_BUTTON, self._on_browse_pot)

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
			label=_("(empty = default: Documents\FreeRadio Recordings)"),
		)
		_default_hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
		rec_dir_browse = wx.Button(self, label=_("Brow&se folder..."))
		rec_dir_sizer.Add(self._recordings_dir, 1, wx.EXPAND | wx.RIGHT, 5)
		rec_dir_sizer.Add(rec_dir_browse, 0)
		sHelper.addItem(rec_dir_sizer, flag=wx.EXPAND)
		sHelper.addItem(_default_hint)
		rec_dir_browse.Bind(wx.EVT_BUTTON, self._on_browse_recordings_dir)

		# Initial visibility state based on disable_bass setting
		wx.CallAfter(self._update_bass_controls_visibility)
		# Load audio devices in the background (only if BASS is enabled)
		if not config.conf["freeradio"].get("disable_bass", False):
			threading.Thread(target=self._load_devices, daemon=True).start()

	def _on_disable_bass_changed(self, event):
		"""Update visibility of BASS-dependent controls when checkbox changes."""
		self._update_bass_controls_visibility()
		event.Skip()

	def _update_bass_controls_visibility(self):
		"""Show/hide BASS-dependent controls based on disable_bass checkbox."""
		disable_bass = self._disable_bass.GetValue()
		
		# Audio device selection - BASS only
		self._device_choice.Show(not disable_bass)
		# Find the label for device choice (it's a StaticText)
		parent = self._device_choice.GetParent()
		for child in parent.GetChildren():
			if isinstance(child, wx.StaticText) and child.GetLabel() == _("Audio output device (BASS backend):"):
				child.Show(not disable_bass)
				break
		
		# Audio effects label and checklistbox - BASS only
		self._fx_static.Show(not disable_bass)
		self._fx_choice.Show(not disable_bass)
		# Find the label for fx choice ("Audio &effects:")
		for child in parent.GetChildren():
			if isinstance(child, wx.StaticText) and child.GetLabel().startswith(_("Audio &effects:")):
				child.Show(not disable_bass)
				break
		
		# Bass hint - show only when BASS is disabled
		self._bass_hint.Show(disable_bass)
		
		# If BASS is being enabled and the device list hasn't been populated yet,
		# trigger a background load now so the Choice is not stuck on "Loading devices..."
		if not disable_bass and self._device_choice.GetCount() <= 1:
			_label = self._device_choice.GetString(0) if self._device_choice.GetCount() == 1 else ""
			if _label in (_("Loading devices..."), ""):
				threading.Thread(target=self._load_devices, daemon=True).start()
		
		# Relayout the panel
		parent.Layout()
		self.Layout()

	def _load_devices(self):
		"""Fetch device list from BASS in background and pass it to the UI."""
		devices = []
		if not config.conf["freeradio"].get("disable_bass", False):
			for plugin in globalPluginHandler.runningPlugins:
				if isinstance(plugin, GlobalPlugin):
					try:
						devices = plugin._player.get_audio_devices()
					except Exception:
						pass
					break
		wx.CallAfter(self._populate_devices, devices)

	def _populate_devices(self, devices):
		"""Populate the Choice control with the device list and select the saved device."""
		if not self or not self._device_choice:
			return
		self._audio_devices = [(-1, _("System default"))] + list(devices)
		self._device_choice.Clear()
		for _idx, name in self._audio_devices:
			self._device_choice.Append(name)
		# Select the saved device
		saved = config.conf["freeradio"].get("audio_device", -1)
		sel = 0
		for i, (idx, _name) in enumerate(self._audio_devices):
			if idx == saved:
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
		for plugin in globalPluginHandler.runningPlugins:
			if isinstance(plugin, GlobalPlugin):
				try:
					plugin._player.set_fx(fx_str)
				except Exception:
					pass
				break

	def _on_browse_vlc(self, event):
		with wx.FileDialog(
			self,
			_("Select VLC executable"),
			wildcard="vlc.exe|vlc.exe|Executable files (*.exe)|*.exe",
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				self._vlc_path.SetValue(dlg.GetPath())

	def _on_browse_wmp(self, event):
		with wx.FileDialog(
			self,
			_("Select wmplayer.exe"),
			wildcard="wmplayer.exe|wmplayer.exe|Executable files (*.exe)|*.exe",
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				self._wmp_path.SetValue(dlg.GetPath())

	def _on_browse_pot(self, event):
		with wx.FileDialog(
			self,
			_("Select PotPlayer executable"),
			wildcard="PotPlayerMini64.exe|PotPlayerMini64.exe|PotPlayerMini.exe|PotPlayerMini.exe|Executable files (*.exe)|*.exe",
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				self._pot_path.SetValue(dlg.GetPath())

	def _on_browse_ffmpeg(self, event):
		with wx.FileDialog(
			self,
			_("Select ffmpeg.exe"),
			wildcard="ffmpeg.exe|ffmpeg.exe|Executable files (*.exe)|*.exe",
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				self._ffmpeg_path.SetValue(dlg.GetPath())

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
		config.conf["freeradio"]["save_liked_songs"]        = self._save_liked_songs.GetValue()
		
		# Save disable_bass setting
		new_disable_bass = self._disable_bass.GetValue()
		old_disable_bass = config.conf["freeradio"].get("disable_bass", False)
		config.conf["freeradio"]["disable_bass"] = new_disable_bass
		
		# Audio output device (only if BASS enabled)
		if not new_disable_bass:
			sel = self._device_choice.GetSelection()
			if 0 <= sel < len(self._audio_devices):
				new_device_index = self._audio_devices[sel][0]
			else:
				new_device_index = -1
			old_device_index = config.conf["freeradio"].get("audio_device", -1)
			config.conf["freeradio"]["audio_device"] = new_device_index
		else:
			new_device_index = -1
			old_device_index = config.conf["freeradio"].get("audio_device", -1)
		
		config.conf["freeradio"]["hotkey_p_action"] = (
			"resume" if self._hotkey_p_action.GetSelection() == 0 else "favorites"
		)
		_double_map = ["none", "favorites", "search", "recording", "timer"]
		sel = self._hotkey_p_double.GetSelection()
		config.conf["freeradio"]["hotkey_p_double"] = (
			_double_map[sel] if 0 <= sel < len(_double_map) else "none"
		)
		_triple_map = ["none", "favorites", "search", "recording", "timer"]
		sel = self._hotkey_p_triple.GetSelection()
		config.conf["freeradio"]["hotkey_p_triple"] = (
			_triple_map[sel] if 0 <= sel < len(_triple_map) else "none"
		)
		try:
			config.conf["freeradio"]["ffmpeg_path"] = self._ffmpeg_path.GetValue().strip()
		except (KeyError, AttributeError):
			pass
		try:
			config.conf["freeradio"]["vlc_path"]       = self._vlc_path.GetValue().strip()
			config.conf["freeradio"]["wmp_path"]        = self._wmp_path.GetValue().strip()
			config.conf["freeradio"]["potplayer_path"]  = self._pot_path.GetValue().strip()
		except KeyError:
			pass
		
		# Audio effects (only if BASS enabled)
		if not new_disable_bass:
			try:
				checked = self._fx_choice.GetCheckedItems()
				active = [self._fx_keys[i] for i in checked if 0 <= i < len(self._fx_keys)]
				config.conf["freeradio"]["audio_fx"] = ",".join(active) if active else "none"
			except (AttributeError, IndexError):
				pass
		else:
			config.conf["freeradio"]["audio_fx"] = "none"
		
		config.conf["freeradio"]["recordings_dir"] = self._recordings_dir.GetValue().strip()

		for plugin in globalPluginHandler.runningPlugins:
			if isinstance(plugin, GlobalPlugin):
				plugin._player.set_volume(vol)
				
				# Handle BASS disable change
				if new_disable_bass != old_disable_bass:
					# Recreate player with new backend setting
					was_playing = plugin._player.is_playing()
					current_url = plugin._player._current_url
					current_name = plugin._player._current_name
					current_station = plugin._player._current_station
					current_url_resolved = plugin._player._current_url_resolved
					
					plugin._player.terminate()
					plugin._player = radioPlayer.RadioPlayer(disable_bass=new_disable_bass)
					plugin._player.set_volume(vol)
					plugin._player.on_device_lost = plugin._on_audio_device_lost
					
					if was_playing and current_url:
						wx.CallAfter(
							plugin._player.play,
							current_url,
							current_name,
							url_resolved=current_url_resolved,
							station=current_station
						)
				elif not new_disable_bass:
					# Apply new audio output device immediately if changed
					if new_device_index != old_device_index:
						try:
							plugin._player.switch_output_device(new_device_index)
						except Exception:
							pass
						wx.CallAfter(plugin._sync_dialog_device, new_device_index)
					# Apply FX immediately
					try:
						plugin._player.set_fx(config.conf["freeradio"].get("audio_fx", "none"))
					except Exception:
						pass
				
				plugin._player.update_paths(
					vlc_path=config.conf["freeradio"].get("vlc_path") or None,
					wmp_path=config.conf["freeradio"].get("wmp_path") or None,
					potplayer_path=config.conf["freeradio"].get("potplayer_path") or None,
				)
				# Also update Recorder's player_paths and volume if needed
				plugin._recorder._player_paths = {
					"vlc": config.conf["freeradio"].get("vlc_path", ""),
					"potplayer": config.conf["freeradio"].get("potplayer_path", ""),
					"wmp": config.conf["freeradio"].get("wmp_path", ""),
				}
				plugin._recorder._volume = vol
				break


class _TimerManager:
	"""Manages sleep (stop) and alarm (start) timers for FreeRadio.

	Timers are persisted to disk (timers.json); future entries survive NVDA
	or system restarts and are re-attached on load.
	"""

	def __init__(self, player, station_manager, save_path=None, play_callback=None):
		self._player          = player
		self._manager         = station_manager
		self._save_path       = save_path
		self._play_callback   = play_callback
		self._stop_event      = threading.Event()
		self._wakeup          = threading.Event()
		self._timers          = []
		self._lock            = threading.Lock()
		self._load()
		self._thread          = threading.Thread(target=self._loop, daemon=True)
		self._thread.start()

	def add_sleep(self, stop_dt, notify_callback=None):
		"""Schedule a stop at stop_dt (datetime). Returns entry id."""
		_stop = self._action_stop
		def _sleep_action():
			_stop()
		return self._add(stop_dt, _sleep_action, _("Sleep timer"), notify_callback,
						kind="sleep", station=None)

	def add_alarm(self, start_dt, station, play_callback, notify_callback=None):
		"""Schedule playback of station at start_dt. Returns entry id."""
		def action():
			play_callback(station, [station], 0)
		return self._add(start_dt, action, station.get("name", "?"), notify_callback,
						kind="alarm", station=station)

	def remove(self, entry_id):
		with self._lock:
			self._timers = [t for t in self._timers if t[0] != entry_id]
		self._save()
		self._wakeup.set()

	def get_timers(self):
		with self._lock:
			return list(self._timers)

	def terminate(self):
		self._stop_event.set()
		self._wakeup.set()



	def _save(self):
		"""Write pending timers to JSON file."""
		if not self._save_path:
			return
		import json as _json, datetime as _dt
		records = []
		with self._lock:
			for entry_id, dt, action, label, notify_cb in self._timers:
				# action callable is not serialisable; store kind/station metadata instead
				meta = getattr(action, "_timer_meta", None)
				if meta is None:
					continue
				records.append({
					"id":      entry_id,
					"dt":      dt.isoformat(),
					"label":   label,
					"kind":    meta["kind"],
					"station": meta.get("station"),
				})
		try:
			with open(self._save_path, "w", encoding="utf-8") as fh:
				_json.dump(records, fh, ensure_ascii=False, indent=2)
		except Exception as exc:
			log.error("FreeRadio: failed to save timers: %s", exc)

	def _load(self):
		"""Load timers from JSON file; skip entries that are already in the past."""
		if not self._save_path:
			return
		import json as _json, datetime as _dt
		try:
			with open(self._save_path, "r", encoding="utf-8") as fh:
				records = _json.load(fh)
		except FileNotFoundError:
			return
		except Exception as exc:
			log.error("FreeRadio: failed to load timers: %s", exc)
			return

		now = _dt.datetime.now()
		for rec in records:
			try:
				dt = _dt.datetime.fromisoformat(rec["dt"])
			except Exception:
				continue
			if dt <= now:
				continue  # past — skip
			kind    = rec.get("kind", "sleep")
			label   = rec.get("label", "")
			station = rec.get("station")
			entry_id = rec.get("id")
			if not entry_id:
				import uuid as _uuid
				entry_id = str(_uuid.uuid4())

			if kind == "sleep":
				_stop = self._action_stop
				def _sleep_action():
					_stop()
				_sleep_action._timer_meta = {"kind": "sleep", "station": None}
				action = _sleep_action
			elif kind == "alarm" and station and self._play_callback:
				_st = station
				_cb = self._play_callback
				def _make_alarm_action(s, cb):
					def _action():
						cb(s, [s], 0)
					_action._timer_meta = {"kind": "alarm", "station": s}
					return _action
				action = _make_alarm_action(_st, _cb)
			else:
				continue

			with self._lock:
				self._timers.append((entry_id, dt, action, label, None))

		with self._lock:
			self._timers.sort(key=lambda t: t[1])

	def _add(self, dt, action, label, notify_callback, kind="sleep", station=None):
		import uuid as _uuid
		entry_id = str(_uuid.uuid4())
		# Attach metadata to the callable for serialisation
		action._timer_meta = {"kind": kind, "station": station}
		with self._lock:
			self._timers.append((entry_id, dt, action, label, notify_callback))
			self._timers.sort(key=lambda t: t[1])
		self._save()
		self._wakeup.set()
		return entry_id

	def _action_stop(self):
		"""Stop playback, fading out over ~60 s if the player is active."""
		if self._player.is_playing():
			threading.Thread(target=self._fade_and_stop, daemon=True).start()
		else:
			self._player.stop()
			wx.CallAfter(ui.message, _("Sleep timer: radio stopped"))

	def _fade_and_stop(self):
		"""Gradually reduce volume to 0 over 60 seconds, then stop."""
		import time
		_FADE_DURATION  = 60
		_FADE_STEPS     = 20
		_STEP_INTERVAL  = _FADE_DURATION / _FADE_STEPS

		original_volume = self._player.get_volume()
		wx.CallAfter(ui.message, _("Sleep timer: fading out…"))

		for step in range(_FADE_STEPS):
			for tick in range(int(_STEP_INTERVAL * 10)):
				time.sleep(0.1)
				if not self._player.is_playing():
					self._player.set_volume(original_volume)
					return

			new_vol = max(0, int(original_volume * (1 - (step + 1) / _FADE_STEPS)))
			self._player.set_volume(new_vol)

		self._player.stop()
		self._player.set_volume(original_volume)
		wx.CallAfter(ui.message, _("Sleep timer: radio stopped"))

	def _loop(self):
		import datetime as _dt
		# Waits dynamically until the next timer fires; _wakeup is signalled
		# whenever a timer is added or removed to interrupt the sleep early.
		_MAX_SLEEP = 60  # seconds — ceiling for long waits
		while not self._stop_event.is_set():
			now = _dt.datetime.now()
			fired = []
			with self._lock:
				remaining = []
				for entry in self._timers:
					entry_id, dt, action, label, notify_cb = entry
					if now >= dt:
						fired.append(entry)
					else:
						remaining.append(entry)
				self._timers = remaining

			if fired:
				self._save()  # fired entries are gone from the list — update disk
			for entry_id, dt, action, label, notify_cb in fired:
				try:
					wx.CallAfter(action)
				except Exception as e:
					log.error("FreeRadio timer action failed: %s", e)
				if notify_cb:
					try:
						wx.CallAfter(notify_cb, label)
					except Exception:
						pass

			# Calculate time remaining until the next timer.
			with self._lock:
				if self._timers:
					next_dt = self._timers[0][1]
					wait = max(0.1, (next_dt - _dt.datetime.now()).total_seconds())
					wait = min(wait, _MAX_SLEEP)
				else:
					wait = _MAX_SLEEP

			self._wakeup.clear()
			self._wakeup.wait(timeout=wait)