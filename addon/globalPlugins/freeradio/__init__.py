# -*- coding: utf-8 -*-

import braille
import config
import os
import tempfile
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


import addonHandler
addonHandler.initTranslation()

log = logging.getLogger(__name__)


def _speak_on_demand(msg):
	"""Announce a message regardless of NVDA's current speech mode.

	When a script uses speakOnDemand=True, NVDA allows speech only while the
	script is executing on the main thread.  Any speech triggered later — e.g.
	from a background thread via wx.CallAfter — arrives after NVDA has already
	left that "on demand" window, so the output is silently suppressed.

	The reliable workaround (also used by Resource Monitor and similar add-ons)
	is to briefly force speech mode to SpeechMode.talk before speaking, then
	restore whatever mode was active.  This must be called from the main thread
	(use wx.CallAfter when coming from a background thread).

	Args:
		msg: The string to announce.
	"""
	# SpeechMode was introduced in NVDA 2021.1.  Guard for older builds just in
	# case, although any NVDA that supports speakOnDemand already has it.
	try:
		previous_mode = speech.getState().speechMode
		speech.setSpeechMode(speech.SpeechMode.talk)
		try:
			speech.speakMessage(msg)
		finally:
			speech.setSpeechMode(previous_mode)
	except Exception:
		# Fallback: plain ui.message (works on older NVDA without on-demand mode).
		ui.message(msg)
	_braille_message(msg)


def _notifications_muted():
	"""Return True when the user has enabled 'Mute notifications' in settings."""
	return config.conf["freeradio"].get("mute_notifications", False)


def _braille_messages_enabled():
	return config.conf["freeradio"].get(
		"braille_messages",
		config.conf["freeradio"].get("braille_messages_outside_dialog", False),
	)


def _braille_message(msg):
	if not msg or not _braille_messages_enabled():
		return
	try:
		handler = getattr(braille, "handler", None)
		if handler:
			handler.message(str(msg))
	except Exception as e:
		log.debug("FreeRadio: braille message failed: %s", e)


def _notify(msg):
	"""Announce msg via ui.message unless notifications are muted."""
	if not _notifications_muted():
		ui.message(msg)
		_braille_message(msg)


def _notify_on_demand(msg):
	"""Announce msg via _speak_on_demand unless notifications are muted."""
	if not _notifications_muted():
		_speak_on_demand(msg)


def _format_duration(seconds):
	"""Format a duration in seconds as H:MM:SS, or M:SS under an hour."""
	seconds = max(0, int(round(seconds)))
	hours, rem = divmod(seconds, 3600)
	minutes, secs = divmod(rem, 60)
	if hours:
		return "%d:%02d:%02d" % (hours, minutes, secs)
	return "%d:%02d" % (minutes, secs)


def _sapi5_speak(msg):
	"""Speak *msg* using the selected SAPI5 voice on a background thread.

	Respects the mute-notifications setting — does nothing when muted.
	Tries two methods in order:
	1. win32com.client — synchronous speak (flag=0) so the SpVoice object stays
	   alive until speech finishes.  CoInitialize is called explicitly because
	   NVDA addon threads may not have a COM apartment set up.
	2. PowerShell fallback — works even without win32com (uses default voice).
	"""
	if _notifications_muted():
		return
	wx.CallAfter(_braille_message, msg)
	def _speak():
		import config as _config
		voice_name = _config.conf["freeradio"].get("sapi5_voice_name", "")
		text = msg.replace('"', "'")  # PowerShell fallback: avoid quote issues

		# --- Method 1: comtypes (bundled with NVDA, preferred) ---
		try:
			import comtypes.client
			spk = comtypes.client.CreateObject("SAPI.SpVoice")
			if voice_name:
				voices = spk.GetVoices()
				for i in range(voices.Count):
					v = voices.Item(i)
					if v.GetDescription() == voice_name:
						spk.Voice = v
						break
			spk.Speak(msg, 0)  # 0 = SVSFlagDefault (synchronous)
			return
		except Exception as e:
			log.warning("FreeRadio: comtypes SAPI5 speak failed: %s", e)

		# --- Method 2: win32com ---
		try:
			import pythoncom
			import win32com.client
			pythoncom.CoInitialize()
			try:
				spk = win32com.client.Dispatch("SAPI.SpVoice")
				if voice_name:
					for v in spk.GetVoices():
						if v.GetDescription() == voice_name:
							spk.Voice = v
							break
				spk.Speak(msg, 0)
			finally:
				pythoncom.CoUninitialize()
			return
		except Exception as e:
			log.warning("FreeRadio: win32com SAPI5 speak failed: %s", e)

		# --- Method 2: PowerShell fallback (default voice only) ---
		try:
			import subprocess
			voice_line = (
				f'$s.SelectVoice("{voice_name}");' if voice_name else ""
			)
			script = (
				"Add-Type -AssemblyName System.Speech;"
				"$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
				f'{voice_line}$s.Speak("{text}");'
			)
			subprocess.Popen(
				["powershell", "-WindowStyle", "Hidden", "-Command", script],
				creationflags=0x08000000,  # CREATE_NO_WINDOW
			)
		except Exception:
			pass

	import threading as _threading
	_threading.Thread(target=_speak, daemon=True).start()


def _list_sapi5_voices():
	"""Return a list of available SAPI5 voice description strings.

	Uses comtypes (bundled with NVDA) instead of win32com.
	Returns an empty list if SAPI is unavailable or broken.
	"""
	try:
		import comtypes.client
		import comtypes.gen.SpeechLib as SpeechLib
		spk = comtypes.client.CreateObject("SAPI.SpVoice")
		voices = spk.GetVoices()
		result = []
		for i in range(voices.Count):
			try:
				result.append(voices.Item(i).GetDescription())
			except Exception:
				pass
		log.info("FreeRadio: found %d SAPI5 voices: %s", len(result), result)
		return result
	except Exception as e:
		log.warning("FreeRadio: _list_sapi5_voices failed: %s", e)

	# Fallback: comtypes without pre-generated SpeechLib
	try:
		import comtypes.client
		spk = comtypes.client.CreateObject("SAPI.SpVoice")
		# GetVoices returns an ISpeechObjectTokens collection
		voices = spk.GetVoices()
		result = [voices.Item(i).GetDescription() for i in range(voices.Count)]
		log.info("FreeRadio: SAPI5 voices (fallback): %s", result)
		return result
	except Exception as e:
		log.warning("FreeRadio: _list_sapi5_voices fallback failed: %s", e)
		return []


try:
	_ = globals()['_']
except KeyError:
	log.warning("Translation function '_' not found, using fallback.")
	def _(text):
		return text


from . import radioPlayer, stationManager, recorder as recorderModule

if globalVars.appArgs.secure:
	GlobalPlugin = globalPluginHandler.GlobalPlugin


_AUDIO_DEVICE_REFRESH_MODE_KEYS = ["reliable", "fast"]


def _audio_device_refresh_mode():
	mode = config.conf["freeradio"].get("audio_device_refresh_mode", "reliable")
	return mode if mode in _AUDIO_DEVICE_REFRESH_MODE_KEYS else "reliable"


def _init_config():
	config.conf.spec["freeradio"] = {
		"volume":           "integer(default=100, min=0, max=100)",
		"vlc_path":         "string(default='')",
		"wmp_path":         "string(default='')",
		"potplayer_path":   "string(default='')",
		"last_station_url": "string(default='')",
		"last_station_name":"string(default='')",
		"last_station_uuid":"string(default='')",
		"last_station_tags":"string(default='')",
		"resume_on_start":  "boolean(default=False)",
		"hotkey_p_action":  "string(default='resume')",
		"hotkey_p_double":  "string(default='none')",
		"hotkey_p_triple":  "string(default='none')",
		"ffmpeg_path":       "string(default='')",
		"audio_fx":          "string(default='none')",
		"audio_device":      "integer(default=-1)",
		"audio_device_name": "string(default='')",
		"audio_device_refresh_mode": "string(default='reliable')",
		"eq_gain_eq_bass":   "integer(default=9)",
		"eq_gain_eq_treble": "integer(default=9)",
		"eq_gain_eq_vocal":  "integer(default=6)",
		"disable_bass":          "boolean(default=False)",
		"announce_track_changes":"boolean(default=False)",
		"track_change_voice":    "string(default='nvda')",
		"sapi5_voice_name":      "string(default='')",
		"mute_notifications":    "boolean(default=False)",
		"braille_messages":      "boolean(default=False)",
		"braille_messages_outside_dialog": "boolean(default=False)",
		"save_liked_songs":       "boolean(default=False)",
		"recordings_dir":         "string(default='')",
		"auto_check_updates":     "boolean(default=True)",
		"disable_internet_check": "boolean(default=False)",
		"crossfade":              "string(default='off')",  # off | short | normal | tuning
		"result_limit":           "integer(default=1000, min=100, max=10000)",
		"timeshift_enabled":      "boolean(default=False)",
	}

_init_config()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super().__init__()
		disable_bass = config.conf["freeradio"].get("disable_bass", False)
		self._player  = radioPlayer.RadioPlayer(disable_bass=disable_bass)
		self._player.set_audio_device_refresh_mode(_audio_device_refresh_mode())
		self._player.set_volume(config.conf["freeradio"]["volume"])
		# Time-shift buffer (rewind/fast-forward live radio) - disabled by
		# default, opt-in via the settings panel or config.
		self._player.set_timeshift_enabled(
			config.conf["freeradio"].get("timeshift_enabled", False)
		)
		# Apply saved audio output device (only if BASS is enabled)
		if not disable_bass:
			_saved_device = config.conf["freeradio"].get("audio_device", -1)
			_saved_device_name = config.conf["freeradio"].get("audio_device_name", "")
			_devices = []
			try:
				_devices = self._player.get_audio_devices()
			except Exception:
				pass
			if _devices:
				if _saved_device_name:
					try:
						_resolved_device, _resolved_name, _match = self._player.resolve_audio_device(
							_devices,
							_saved_device,
							_saved_device_name,
						)
						if _match == "name" and _resolved_device != _saved_device:
							_saved_device = _resolved_device
							config.conf["freeradio"]["audio_device"] = _resolved_device
							config.conf["freeradio"]["audio_device_name"] = _resolved_name
					except Exception:
						pass
				elif _saved_device != -1:
					try:
						_resolved_device, _resolved_name, _match = self._player.resolve_audio_device(
							_devices,
							_saved_device,
							"",
						)
						if _match == "index":
							config.conf["freeradio"]["audio_device_name"] = _resolved_name
					except Exception:
						pass
			if _saved_device != -1:
				try:
					_actual_device = self._player.switch_output_device(_saved_device)
					if _actual_device != _saved_device:
						config.conf["freeradio"]["audio_device"] = _actual_device
						_actual_name = ""
						for _idx, _name in _devices:
							if _idx == _actual_device:
								_actual_name = _name
								break
						config.conf["freeradio"]["audio_device_name"] = _actual_name
				except Exception:
					pass
			# Apply saved audio FX setting
			_saved_fx = config.conf["freeradio"].get("audio_fx", "none")
			if _saved_fx and _saved_fx != "none":
				self._player.set_fx(_saved_fx)
			# Apply saved crossfade / station-tuning transition setting
			_cf_map = {"off": 0.0, "short": 1.0, "normal": 2.0, "tuning": 0.0}
			_saved_cf = config.conf["freeradio"].get("crossfade", "off")
			self._player.set_tuning_effect_enabled(_saved_cf == "tuning")
			self._player.set_crossfade_duration(_cf_map.get(_saved_cf, 0.0))
		# Notify and reset settings when audio device is lost
		self._player.on_device_lost = self._on_audio_device_lost
		# Refresh the podcast episode list's row when a position is saved
		# due to a pause or the episode finishing (not the periodic autosave).
		self._player.on_podcast_progress_saved = self._on_podcast_progress_saved
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
			_notify, _("Recording started: %s") % rec.station.get("name", "")
		)
		self._recorder._notify_finish = lambda rec: wx.CallAfter(
			_notify, _("Recording finished: %s") % os.path.basename(rec.output_path or "")
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
		# Check for updates in the background after a short delay
		if config.conf["freeradio"].get("auto_check_updates", True):
			t = threading.Timer(15.0, self._check_for_updates, kwargs={"silent": True})
			t.daemon = True
			t.start()

		# ICY metadata auto-announce
		self._icy_last_title   = None
		self._icy_poll_stop    = threading.Event()
		self._icy_poll_thread  = threading.Thread(
			target=self._icy_poll_loop, daemon=True
		)
		self._icy_poll_thread.start()

		# Build dynamic scripts for favourite stations so they appear in
		# NVDA's Input Gestures dialog under "FreeRadio Stations".
		self._station_script_names = []   # track names for cleanup
		self._rebuild_station_scripts()

	def _rebuild_station_scripts(self):
		"""Create or refresh one script per favourite station.

		Each script is named  script_playFavoriteStation_<sanitised_uuid>
		and appears in the "FreeRadio Stations" category of NVDA's Input
		Gestures dialog.  The user can assign any keyboard shortcut there;
		NVDA stores it in userGestureMap and it persists across sessions as
		long as the station remains a favourite.

		Call this whenever the favourites list changes (add / remove / reload).
		"""
		import inputCore

		# ── 1. Remove scripts that no longer correspond to a favourite ───────
		favs     = self._manager.get_favorites()
		fav_uids = {self._sanitise_uuid(s.get("stationuuid", "")) for s in favs}

		stale = [n for n in self._station_script_names if n not in
		         {"script_playFavoriteStation_" + uid for uid in fav_uids}]
		for name in stale:
			try:
				delattr(self.__class__, name)
			except AttributeError:
				pass
		self._station_script_names = [
			n for n in self._station_script_names if n not in stale
		]

		# ── 2. Create / refresh a script for every favourite ─────────────────
		_CATEGORY = _("FreeRadio Stations")

		for station in favs:
			uid        = self._sanitise_uuid(station.get("stationuuid", ""))
			if not uid:
				continue
			script_name = "script_playFavoriteStation_" + uid
			station_name = station.get("name", "").strip()

			# Build the script function with a closure over *station*.
			def _make_script(s):
				def _script(self_plugin, gesture):
					favs_now = self_plugin._manager.get_favorites()
					match    = next(
						(x for x in favs_now
						 if x.get("stationuuid") == s.get("stationuuid")),
						None,
					)
					if match is None:
						ui.message(
							_("Station no longer in favourites: %s")
							% s.get("name", "").strip()
						)
						return
					self_plugin._stations      = favs_now
					self_plugin._current_index = favs_now.index(match)
					self_plugin._play_station(match)
				# NVDA reads __doc__ as the script description and
				# __name__ as the script identifier.
				_script.__doc__      = _("%s playback shortcut ()") % s.get("name", "").strip()
				_script.__name__     = script_name
				_script.category     = _CATEGORY
				# No default gesture — user assigns one via Input Gestures dialog.
				_script.__gestures__ = {}
				return _script

			fn = _make_script(station)
			# Attach to the class so NVDA discovers it via introspection.
			if not hasattr(self.__class__, script_name):
				setattr(self.__class__, script_name, fn)
				self._station_script_names.append(script_name)
			else:
				# Update description in case the station was renamed.
				existing = getattr(self.__class__, script_name)
				existing.__doc__ = fn.__doc__

	@staticmethod
	def _sanitise_uuid(uid):
		"""Return a string safe to use as part of a Python identifier."""
		return uid.replace("-", "_").replace(".", "_")

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

		item_update = self._freeradio_menu.Append(
			wx.ID_ANY,
			# Translators: Menu item that manually triggers the update check
			_("Check for &Updates..."),
		)
		gui.mainFrame.sysTrayIcon.Bind(
			wx.EVT_MENU,
			lambda evt: threading.Thread(
				target=self._check_for_updates, kwargs={"silent": False}, daemon=True
			).start(),
			item_update,
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

		# Try to pull a short snippet of "what's airing right now" out of the
		# player's own time-shift buffer instead of opening a second
		# connection to stream_url. Some stations serve a freshly-inserted
		# ad to every brand-new connection, so a second connection made just
		# for recognition would sample that ad instead of the actual track -
		# even though the main playback connection is already well past it.
		local_snippet = None
		try:
			buf = self._player.get_timeshift_buffer()
		except Exception:
			buf = None
		if buf is not None and buf.is_active() and buf.is_tail_safe():
			try:
				fd, snippet_path = tempfile.mkstemp(prefix="freeradio_recognize_", suffix=".buf")
				os.close(fd)
				if buf.extract_recent_snippet(18, snippet_path):
					local_snippet = snippet_path
				else:
					try:
						os.remove(snippet_path)
					except OSError:
						pass
			except Exception:
				log.warning("FreeRadio: could not extract recognition snippet from time-shift buffer", exc_info=True)

		def _on_result(result):
			if result.success:
				label = result.full_label()
				wx.CallAfter(self._copy_to_clipboard, label)
			else:
				wx.CallAfter(
					ui.message,
					_("Recognition failed: %s") % result.error_msg,
				)
			if local_snippet:
				try:
					os.remove(local_snippet)
				except OSError:
					pass

		musicRecognizer.recognize_async(stream_url, ffmpeg_path, "", _on_result, local_file=local_snippet)

	def terminate(self):
		# Remove all dynamically created favourite-station scripts from the class.
		for name in getattr(self, "_station_script_names", []):
			try:
				delattr(self.__class__, name)
			except AttributeError:
				pass
		self._station_script_names = []

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
			elif action == "liked":
				# Open the browser dialog and switch to the Liked Songs tab (index 4).
				wx.CallAfter(self._open_dialog_on_tab, 4)
			elif action == "settings":
				# Open NVDA Settings directly on the FreeRadio category.
				wx.CallAfter(
					gui.mainFrame._popupSettingsDialog,
					gui.NVDASettingsDialog,
					FreeRadioSettingsPanel,
				)
			elif action == "announce":
				# Announce the currently playing station without opening any dialog.
				wx.CallAfter(self._announce_now)
			elif action == "stop":
				# Stop radio playback immediately.
				wx.CallAfter(self._stop_from_dialog)

		repeat = getLastScriptRepeatCount()

		# Snapshot playback state once — used only by the single-press handler.
		_has_media  = self._player.has_media()
		_is_playing = self._player.is_playing()
		_last_url   = config.conf["freeradio"].get("last_station_url", "").strip()
		_action     = config.conf["freeradio"].get("hotkey_p_action", "resume")

		# Always cancel any pending timer so only the latest press schedules work.
		old_timer = getattr(self, "_pause_resume_timer", None)
		if old_timer:
			old_timer.Stop()
			self._pause_resume_timer = None

		# --- Triple press ---
		if repeat >= 2:
			# The double-press action must NOT have run yet (its timer is cancelled above).
			# Execute the triple action immediately.
			if _triple_action != "none":
				_run_action(_triple_action)
			return

		# --- Double press ---
		if repeat == 1:
			if _double_action == "none":
				return
			# If triple is also configured, delay execution so a third press can cancel it.
			if _triple_action != "none":
				def _do_double():
					self._pause_resume_timer = None
					_run_action(_double_action)
				self._pause_resume_timer = wx.CallLater(350, _do_double)
			else:
				# No triple configured — run double immediately.
				_run_action(_double_action)
			return

		# --- Single press ---
		def _do_single_press():
			self._pause_resume_timer = None
			if _has_media:
				if _is_playing:
					self._player.pause()
					_notify(_("Radio paused"))
				else:
					self._player.resume()
					_notify(_("Playing"))
				return
			if _action == "favorites":
				self._open_dialog_on_favorites()
			else:
				if _last_url:
					self._resume_last_station()

		# If neither double nor triple is configured, act immediately.
		if _double_action == "none" and _triple_action == "none":
			_do_single_press()
			return

		# At least double (or triple) is configured: delay single so further presses can cancel it.
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
					_notify(_("Radio stopped"))

			wx.CallAfter(_confirm)
			return

		if not self._player.has_media():
			gesture.send()
			return
		self._player.stop()
		self._stations      = []
		self._current_index = -1
		_notify(_("Radio stopped"))

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
		description=_("Time-shift: rewind 15 seconds (enters time-shift mode if not already active)"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+j",
	)
	def script_timeshiftRewind(self, gesture):
		# Podcast oynatılıyorsa dosya içinde geri sar
		station = self._player.get_current_station()
		if station and "podcast" in station.get("tags", ""):
			ok, pos = self._player.seek_relative(-5)
			if ok:
				_notify(_("Rewound 5 seconds"))
			else:
				_notify(_("Could not seek"))
			return

		if not config.conf["freeradio"].get("timeshift_enabled", False):
			_notify(_("Time-shift buffer is disabled. Enable it in FreeRadio settings."))
			return
		if not self._player.has_media():
			gesture.send()
			return

		ok, position, buffered, reason = self._player.rewind_timeshift(15)
		if not ok:
			_TIMESHIFT_REASON_MESSAGES = {
				"bass_disabled":   _("Time-shift requires the BASS audio backend, which is currently disabled."),
				"feature_disabled": _("Time-shift buffer is disabled. Enable it in FreeRadio settings."),
				"wrong_backend":   _("Time-shift is not available for the current playback backend."),
				"hls_unsupported": _("Time-shift could not read this station's stream playlist."),
				"no_buffer_yet":   _("Not enough buffered audio to rewind yet. Wait a few seconds after the station starts playing and try again."),
				"no_buffer_file":  _("Time-shift buffer file is not ready yet."),
				"engine_error":    _("Could not switch to time-shifted playback."),
			}
			_notify(_TIMESHIFT_REASON_MESSAGES.get(reason, _("Could not rewind")))
			return
		_notify(_("Rewound to %.0f seconds behind live") % (buffered - position))

	@script(
		description=_("Time-shift: fast-forward 15 seconds, or return to live if already caught up"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+k",
	)
	def script_timeshiftForward(self, gesture):
		# Podcast oynatılıyorsa dosya içinde ileri sar
		station = self._player.get_current_station()
		if station and "podcast" in station.get("tags", ""):
			ok, pos = self._player.seek_relative(5)
			if ok:
				_notify(_("Forwarded 5 seconds"))
			else:
				_notify(_("Could not seek"))
			return

		if not config.conf["freeradio"].get("timeshift_enabled", False):
			_notify(_("Time-shift buffer is disabled. Enable it in FreeRadio settings."))
			return
		if not self._player.is_timeshifted():
			_notify(_("Already listening live"))
			return

		ok, position, at_live_edge = self._player.forward_timeshift(15)
		if not ok:
			_notify(_("Could not fast-forward"))
			return
		if at_live_edge:
			_notify(_("Back to live"))
		else:
			buffered = self._player.get_timeshift_buffered_seconds()
			_notify(_("Fast-forwarded, still %.0f seconds behind live") %
				(buffered - position))

	@script(
		description=_("Enable or disable the time-shift (rewind) buffer"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+t",
	)
	def script_toggleTimeshift(self, gesture):
		current = config.conf["freeradio"].get("timeshift_enabled", False)
		new_value = not current
		config.conf["freeradio"]["timeshift_enabled"] = new_value

		if self._player is not None:
			try:
				self._player.set_timeshift_enabled(new_value)
			except Exception as e:
				log.warning("FreeRadio: could not apply timeshift_enabled change: %s", e, exc_info=True)

		# Best-effort: keep the Settings panel's checkbox in sync if it
		# happens to be open right now (mirrors script_toggleBassBackend's
		# approach for its own checkbox).
		if self._dialog is not None and hasattr(self._dialog, "_timeshift_enabled"):
			try:
				self._dialog._timeshift_enabled.SetValue(new_value)
			except Exception:
				pass

		ui.message(_("Time-shift buffer %s") % (_("enabled") if new_value else _("disabled")))

	@script(
		description=_("Add currently playing station to favourites, or download the episode if a podcast is playing"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+v",
	)
	def script_addToFavorites(self, gesture):
		station = self._player.get_current_station()
		if not station:
			ui.message(_("No station is playing"))
			return
		if "podcast" in station.get("tags", ""):
			self._download_current_podcast_episode(station)
			return
		if self._manager.is_favorite(station):
			ui.message(_("Already in favourites: %s") % station.get("name", "").strip())
			return
		self._manager.add_favorite(station)
		ui.message(_("Added to favourites: %s") % station.get("name", "").strip())
		self._rebuild_station_scripts()

	def _download_current_podcast_episode(self, station):
		"""Download the currently playing podcast episode, used by
		Ctrl+Win+V in place of "add to favourites" when a podcast episode
		(rather than a radio station) is playing. Works regardless of
		whether the browser dialog is open."""
		title = station.get("name", "").strip() or _("Episode")
		url = station.get("url") or station.get("url_resolved")
		if not url:
			ui.message(_("This episode has no downloadable URL."))
			return

		from . import podcast
		out_path, filename = podcast.episode_download_target(title, url)
		if os.path.exists(out_path):
			ui.message(_("File already exists: %s") % filename)
			return

		ui.message(_("Downloading: %s") % title)

		def _do_download():
			try:
				podcast.download_episode_file(url, out_path)
				wx.CallAfter(ui.message, _("Download complete: %s") % filename)
			except Exception as e:
				wx.CallAfter(ui.message, _("Download failed: %s") % str(e))

		threading.Thread(target=_do_download, daemon=True).start()

	@script(
		description=_("Announce currently playing station. Press twice for full details, three times to copy track info, four times to force music recognition."),
		category=_("FreeRadio"),
		gesture="kb:control+windows+i",
		speakOnDemand=True,
	)
	def script_whatsPlaying(self, gesture):
		active_sched = self._recorder.get_active_scheduled()

		if not self._player.has_media():
			# Radio inactive but a scheduled recording may still be running.
			# These run from the main thread so _speak_on_demand can be called directly.
			if active_sched:
				parts = [_("Radio inactive. Active scheduled recordings:")]
				for sched_rec in active_sched:
					parts.append(sched_rec.station.get("name", "").strip())
				_speak_on_demand("  ".join(parts))
			else:
				_speak_on_demand(_("FreeRadio is not active"))
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
					# Podcast: append elapsed/remaining time.
					station = self._player.get_current_station()
					if station and "podcast" in station.get("tags", ""):
						ok, pos, length = self._player.get_playback_position()
						if ok and length > 0:
							msg += ". " + _("%(elapsed)s elapsed, %(remaining)s remaining") % {
								"elapsed": _format_duration(pos),
								"remaining": _format_duration(max(0.0, length - pos)),
							}
					# Announce instant recording if active
					if self._recorder.is_recording():
						rec_name = self._recorder.get_station_name()
						msg += ". " + _("Recording: %s") % rec_name
					# Announce active scheduled recordings
					active_sched = self._recorder.get_active_scheduled()
					for sched_rec in active_sched:
						sched_name = sched_rec.station.get("name", "").strip()
						msg += ". " + _("Scheduled recording: %s") % sched_name
					# Use _speak_on_demand so the message is announced even when
					# NVDA's speech mode is set to 'on demand'.
					wx.CallAfter(_speak_on_demand, msg)
				threading.Thread(target=_announce, daemon=True).start()
			else:
				msg = _("Paused: %s") % name
				# Podcast: append elapsed/remaining time even when paused
				station = self._player.get_current_station()
				if station and "podcast" in station.get("tags", ""):
					ok, pos, length = self._player.get_playback_position()
					if not ok or pos <= 0.0:
						# Fallback to saved position if live player handle is closed
						url = station.get("url")
						pos = self._player.get_podcast_position(url)
						length = getattr(station, "duration_seconds", 0) or 0
						ok = pos > 0.0
					if ok and pos > 0.0:
						if length > 0:
							msg += ". " + _("%(elapsed)s elapsed, %(remaining)s remaining") % {
								"elapsed": _format_duration(pos),
								"remaining": _format_duration(max(0.0, length - pos)),
							}
						else:
							msg += ". " + _("%(elapsed)s elapsed") % {"elapsed": _format_duration(pos)}

				# Announce instant recording even while paused
				if self._recorder.is_recording():
					rec_name = self._recorder.get_station_name()
					msg += ". " + _("Recording: %s") % rec_name
				# Announce active scheduled recordings
				active_sched = self._recorder.get_active_scheduled()
				for sched_rec in active_sched:
					sched_name = sched_rec.station.get("name", "").strip()
					msg += ". " + _("Scheduled recording: %s") % sched_name
				# Paused state is reported from the main thread, so call
				# _speak_on_demand directly (no wx.CallAfter needed here).
				_speak_on_demand(msg)

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
			import time as _time
			token = _time.monotonic()
			self._whats_playing_token = token
			dlg_timer = getattr(self, "_whats_playing_dlg_timer", None)
			if dlg_timer:
				dlg_timer.Stop()
				self._whats_playing_dlg_timer = None
			def _copy_or_recognize(tok=token):
				from . import radioPlayer as _rp
				icy = self._player.get_icy_title()
				if not icy:
					url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if url:
						icy = _rp._read_icy_title(url)

				# If 4× pressed, token has changed — cancel transaction
				if getattr(self, "_whats_playing_token", None) != tok:
					return

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
						wx.CallAfter(_speak_on_demand, _("No track info available"))
						return
					wx.CallAfter(
						_speak_on_demand,
						_("No track metadata found. Starting music recognition…"),
					)
					self._start_music_recognition(stream_url)

			threading.Thread(target=_copy_or_recognize, daemon=True).start()

		elif repeat == 3:
			# Fourth press: force Shazam recognition regardless of ICY metadata.
			self._whats_playing_token = None
			dlg_timer = getattr(self, "_whats_playing_dlg_timer", None)
			if dlg_timer:
				dlg_timer.Stop()
				self._whats_playing_dlg_timer = None
			stream_url = (
				getattr(self._player, "_current_url_resolved", None)
				or getattr(self._player, "_current_url", None)
			)
			if not stream_url:
				# Called from the main thread (no wx.CallAfter needed).
				_speak_on_demand(_("No track info available"))
			else:
				_speak_on_demand(_("Starting music recognition…"))
				self._start_music_recognition(stream_url)

	@script(
		# Equivalent to pressing Control+Windows+I (or F2 in the dialog) twice.
		# Opens the station details dialog for the currently playing station.
		# Provided as an unbound gesture so users who have difficulty with
		# rapid key presses can assign a single keystroke to this action.
		description=_("Show details of the currently playing station"),
		category=_("FreeRadio"),
	)
	def script_showStationDetails(self, gesture):
		if not self._player.has_media():
			ui.message(_("FreeRadio is not active"))
			return
		if not getattr(self, "_whats_playing_dialog_open", False):
			self._whats_playing_dialog_open = True
			wx.CallAfter(self._show_station_details_dialog)

	@script(
		# Equivalent to pressing Control+Windows+I (or F2 in the dialog) three times.
		# Copies the current ICY track title to the clipboard, or starts Shazam
		# music recognition when no metadata is available.
		# Provided as an unbound gesture so users who have difficulty with
		# rapid key presses can assign a single keystroke to this action.
		description=_("Copy current track info to clipboard, or start music recognition if unavailable"),
		category=_("FreeRadio"),
		speakOnDemand=True,
	)
	def script_copyTrackInfo(self, gesture):
		if not self._player.has_media():
			_speak_on_demand(_("FreeRadio is not active"))
			return
		import time as _time
		token = _time.monotonic()
		self._whats_playing_token = token

		def _copy_or_recognize(tok=token):
			from . import radioPlayer as _rp
			icy = self._player.get_icy_title()
			if not icy:
				url = (
					getattr(self._player, "_current_url_resolved", None)
					or getattr(self._player, "_current_url", None)
				)
				if url:
					icy = _rp._read_icy_title(url)
			# Abort if a concurrent gesture (e.g. force-recognition) changed the token.
			if getattr(self, "_whats_playing_token", None) != tok:
				return
			if icy:
				wx.CallAfter(self._copy_to_clipboard, icy)
			else:
				stream_url = (
					getattr(self._player, "_current_url_resolved", None)
					or getattr(self._player, "_current_url", None)
				)
				if not stream_url:
					wx.CallAfter(_speak_on_demand, _("No track info available"))
					return
				wx.CallAfter(_speak_on_demand, _("No track metadata found. Starting music recognition…"))
				self._start_music_recognition(stream_url)

		threading.Thread(target=_copy_or_recognize, daemon=True).start()

	@script(
		# Equivalent to pressing Control+Windows+I (or F2 in the dialog) four times.
		# Forces Shazam music recognition regardless of whether ICY metadata is present.
		# Provided as an unbound gesture so users who have difficulty with
		# rapid key presses can assign a single keystroke to this action.
		description=_("Force music recognition for the currently playing stream"),
		category=_("FreeRadio"),
		speakOnDemand=True,
	)
	def script_forceMusicRecognition(self, gesture):
		if not self._player.has_media():
			_speak_on_demand(_("FreeRadio is not active"))
			return
		stream_url = (
			getattr(self._player, "_current_url_resolved", None)
			or getattr(self._player, "_current_url", None)
		)
		if not stream_url:
			_speak_on_demand(_("No track info available"))
		else:
			_speak_on_demand(_("Starting music recognition…"))
			self._start_music_recognition(stream_url)

	@script(
		description=_("Increase FreeRadio volume by 5"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+upArrow",
	)
	def script_volumeUp(self, gesture):
		vol = min(200, self._player.get_volume() + 5)
		self._player.set_volume(vol)
		config.conf["freeradio"]["volume"] = min(100, vol)
		_notify(_("Volume %d") % vol)
		self._sync_dialog_volume(vol)

	@script(
		description=_("Decrease FreeRadio volume by 5"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+downArrow",
	)
	def script_volumeDown(self, gesture):
		vol = max(0, self._player.get_volume() - 5)
		self._player.set_volume(vol)
		config.conf["freeradio"]["volume"] = min(100, vol)
		_notify(_("Volume %d") % vol)
		self._sync_dialog_volume(vol)

	def _sync_dialog_volume(self, vol):
		"""Update the volume SpinCtrl in the browser dialog if it is open."""
		if self._dialog and self._dialog.IsShown():
			try:
				self._dialog._vol_spin.SetValue(vol)
			except Exception:
				pass

	def _sync_dialog_audio(self, vol, fx_str, eq_gains=None):
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
			# Sync EQ gain spin controls
			if eq_gains and hasattr(self._dialog, "_eq_spins"):
				for band, gain_db in eq_gains.items():
					try:
						self._dialog._eq_spins[band].SetValue(int(gain_db))
					except Exception:
						pass
			# Update EQ row visibility
			try:
				self._dialog._update_eq_row_visibility(list(active))
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
		"""Called from the station browser when F2 is pressed.

		Mirrors script_whatsPlaying exactly:
		  1× → announce what is playing
		  2× → open station details dialog (delayed so a 3rd press can cancel)
		  3× → copy ICY track to clipboard, or start Shazam if no metadata
		  4× → force Shazam recognition regardless of ICY metadata

		A manual time-based counter is used instead of getLastScriptRepeatCount()
		because F2 is a dialog-local key, not an NVDA script gesture.
		Presses within 600 ms of each other are counted as multi-press.
		"""
		import time as _time

		active_sched = self._recorder.get_active_scheduled()

		if not self._player.has_media():
			# Radio inactive — report any active scheduled recordings.
			if active_sched:
				parts = [_("Radio inactive. Active scheduled recordings:")]
				for sched_rec in active_sched:
					parts.append(sched_rec.station.get("name", "").strip())
				ui.message("  ".join(parts))
			else:
				ui.message(_("FreeRadio is not active"))
			return

		name = self._player.get_current_name()

		# --- Multi-press counter (time-based) ---
		now   = _time.monotonic()
		last_t = getattr(self, "_f2_last_time", 0)
		count  = getattr(self, "_f2_count", 0)

		if now - last_t < 0.6:
			count += 1
		else:
			count = 0

		self._f2_last_time = now
		self._f2_count     = count

		# --- 1st press: announce what is playing ---
		if count == 0:
			if self._player.is_playing():
				# Generate a token so the background thread can detect a follow-up press.
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
					# Abort if a later press has already changed the token.
					if getattr(self, "_whats_playing_token", None) != tok:
						return
					if icy:
						msg = _("Playing: %(station)s — %(track)s") % {
							"station": name, "track": icy
						}
					else:
						msg = _("Playing: %s") % name
					station = self._player.get_current_station()
					if station and "podcast" in station.get("tags", ""):
						ok, pos, length = self._player.get_playback_position()
						if ok and length > 0:
							msg += ". " + _("%(elapsed)s elapsed, %(remaining)s remaining") % {
								"elapsed": _format_duration(pos),
								"remaining": _format_duration(max(0.0, length - pos)),
							}
					if self._recorder.is_recording():
						msg += ". " + _("Recording: %s") % self._recorder.get_station_name()
					for sched_rec in self._recorder.get_active_scheduled():
						msg += ". " + _("Scheduled recording: %s") % sched_rec.station.get("name", "").strip()
					wx.CallAfter(ui.message, msg)
				threading.Thread(target=_announce, daemon=True).start()
			else:
				msg = _("Paused: %s") % name
				station = self._player.get_current_station()
				if station and "podcast" in station.get("tags", ""):
					ok, pos, length = self._player.get_playback_position()
					if not ok or pos <= 0.0:
						url = station.get("url")
						pos = self._player.get_podcast_position(url)
						length = getattr(station, "duration_seconds", 0) or 0
						ok = pos > 0.0
					if ok and pos > 0.0:
						if length > 0:
							msg += ". " + _("%(elapsed)s elapsed, %(remaining)s remaining") % {
								"elapsed": _format_duration(pos),
								"remaining": _format_duration(max(0.0, length - pos)),
							}
						else:
							msg += ". " + _("%(elapsed)s elapsed") % {"elapsed": _format_duration(pos)}

				if self._recorder.is_recording():
					msg += ". " + _("Recording: %s") % self._recorder.get_station_name()
				for sched_rec in active_sched:
					msg += ". " + _("Scheduled recording: %s") % sched_rec.station.get("name", "").strip()
				ui.message(msg)

		# --- 2nd press: open station details dialog (delayed, cancelable) ---
		elif count == 1:
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

		# --- 3rd press: copy ICY track to clipboard, or start Shazam if no metadata ---
		elif count == 2:
			token = _time.monotonic()
			self._whats_playing_token = token
			dlg_timer = getattr(self, "_whats_playing_dlg_timer", None)
			if dlg_timer:
				dlg_timer.Stop()
				self._whats_playing_dlg_timer = None

			def _copy_or_recognize(tok=token):
				from . import radioPlayer as _rp
				icy = self._player.get_icy_title()
				if not icy:
					url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if url:
						icy = _rp._read_icy_title(url)
				# If a 4th press arrived the token has already changed — abort.
				if getattr(self, "_whats_playing_token", None) != tok:
					return
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
			threading.Thread(target=_copy_or_recognize, daemon=True).start()

		# --- 4th press: force Shazam recognition regardless of ICY metadata ---
		elif count == 3:
			self._whats_playing_token = None
			dlg_timer = getattr(self, "_whats_playing_dlg_timer", None)
			if dlg_timer:
				dlg_timer.Stop()
				self._whats_playing_dlg_timer = None
			stream_url = (
				getattr(self._player, "_current_url_resolved", None)
				or getattr(self._player, "_current_url", None)
			)
			if not stream_url:
				ui.message(_("No track info available"))
			else:
				ui.message(_("Starting music recognition…"))
				self._start_music_recognition(stream_url)
			# Reset counter so a further press starts from 1× again.
			self._f2_count = 0

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
					_notify(_("Radio stopped"))

			wx.CallAfter(_confirm)
			return

		if not self._player.has_media():
			ui.message(_("FreeRadio is not active"))
			return

		self._player.stop()
		self._stations      = []
		self._current_index = -1
		_notify(_("Radio stopped"))

	def _announce_now(self):
		"""Announce the currently playing station name (and ICY track if available).
		Used as a hotkey action so the user can get station info without opening any dialog.
		Mirrors the single-press behaviour of script_whatsPlaying.
		"""
		if not self._player.has_media():
			ui.message(_("FreeRadio is not active"))
			return
		name = self._player.get_current_name()
		if self._player.is_playing():
			def _read_and_announce():
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
					msg = _("Playing: %(station)s — %(track)s") % {
						"station": name, "track": icy
					}
				else:
					msg = _("Playing: %s") % name
				station = self._player.get_current_station()
				if station and "podcast" in station.get("tags", ""):
					ok, pos, length = self._player.get_playback_position()
					if ok and length > 0:
						msg += ". " + _("%(elapsed)s elapsed, %(remaining)s remaining") % {
							"elapsed": _format_duration(pos),
							"remaining": _format_duration(max(0.0, length - pos)),
						}
				wx.CallAfter(ui.message, msg)
			threading.Thread(target=_read_and_announce, daemon=True).start()
		else:
			_notify(_("Paused: %s") % name)

	def _on_audio_device_lost(self, lost_index):
		"""Called from a background thread when the selected audio device is removed.

		Resets config and dialog to system default (-1), then notifies the user via NVDA.
		"""
		try:
			config.conf["freeradio"]["audio_device"] = -1
			config.conf["freeradio"]["audio_device_name"] = ""
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

	def _on_podcast_progress_saved(self, url):
		"""Called (possibly from a background thread - e.g. from
		radioPlayer's stall/finish detection) right after a podcast's
		position is saved due to a pause or the episode finishing, NOT the
		periodic autosave. Marshals onto the UI thread and asks the dialog,
		if open, to refresh just that one episode row - deliberately not a
		continuously-ticking update, which used to make NVDA re-announce
		the focused row every second while a podcast was playing."""
		wx.CallAfter(self._on_podcast_progress_saved_ui, url)

	def _on_podcast_progress_saved_ui(self, url):
		if self._dialog and self._dialog.IsShown():
			try:
				self._dialog.refresh_episode_progress(url)
			except Exception:
				pass

	@script(
		description=_("Start or stop instant recording"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+e",
	)
	def script_toggleRecord(self, gesture):
		# Always cancel any pending delayed action so that only the latest press counts.
		old_timer = getattr(self, "_record_action_timer", None)
		if old_timer:
			old_timer.Stop()
			self._record_action_timer = None

		repeat = getLastScriptRepeatCount()

		# ------------------------------------------------------------------ #
		# Double press → song-capture mode (or stop it if already recording)  #
		# ------------------------------------------------------------------ #
		if repeat >= 1:
			# A single-press action was queued but not yet executed — cancel it
			# so the double press does not also trigger a normal instant recording.

			if self._recorder.is_song_capture():
				# Song-capture is active: user manually ends the recording early.
				path = self._recorder.stop_song_capture()
				if path:
					_notify(_("Song recording stopped: %s") % os.path.basename(path))
				else:
					_notify(_("Song recording stopped"))
				return

			if not self._player.has_media():
				ui.message(_("No station is playing"))
				return

			# Check whether the current station publishes ICY metadata.
			def _start_song_capture():
				from . import radioPlayer as _rp

				# Try the fast in-memory title first; fall back to a live HTTP probe.
				icy = self._player.get_icy_title()
				if not icy:
					url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if url:
						icy = _rp._read_icy_title(url)

				if not icy:
					# Station does not broadcast ICY metadata — inform the user and abort.
					wx.CallAfter(
						ui.message,
						_("This station does not broadcast track metadata. Song recording is not available."),
					)
					return

				# Stop any plain instant recording that may already be running.
				if self._recorder.is_recording() and not self._recorder.is_song_capture():
					self._recorder.stop(self._player)

				try:
					self._recorder.start_song_capture(self._player, icy, timeshift_buffer=self._player.get_timeshift_buffer())
					wx.CallAfter(
						ui.message,
						_("Song recording started: %s") % icy,
					)
				except Exception as exc:
					log.error("FreeRadio: song capture failed to start: %s", exc)
					wx.CallAfter(ui.message, _("Could not start song recording"))

			threading.Thread(target=_start_song_capture, daemon=True).start()
			return

		# ------------------------------------------------------------------ #
		# Single press → instant recording (stop if active; start if not)     #
		# The action is delayed slightly so a quick double press can cancel it #
		# before it fires.                                                     #
		# ------------------------------------------------------------------ #
		def _do_single_press():
			self._record_action_timer = None

			# If a song-capture is active, a single press does nothing here —
			# the user must double-press to stop song-capture mode.
			if self._recorder.is_song_capture():
				return

			if self._recorder.is_recording():
				path = self._recorder.stop(self._player)
				if path:
					wx.CallAfter(_notify, _("Recording stopped: %s") % os.path.basename(path))
				else:
					wx.CallAfter(_notify, _("Recording stopped"))
				return

			if not self._player.has_media():
				wx.CallAfter(ui.message, _("No station is playing"))
				return

			name = self._player.get_current_name()
			try:
				self._recorder.start(self._player, name, timeshift_buffer=self._player.get_timeshift_buffer())
				wx.CallAfter(_notify, _("Recording started: %s") % name)
			except Exception as exc:
				log.error("FreeRadio: instant recording failed to start: %s", exc)
				wx.CallAfter(ui.message, _("Could not start recording"))

		# Delay single-press action by 350 ms so a second press can cancel it.
		self._record_action_timer = wx.CallLater(350, _do_single_press)

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

	@script(
		description=_("Toggle mute notifications (station changes, playback, recording, volume level)"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleMuteNotifications(self, gesture):
		current = config.conf["freeradio"].get("mute_notifications", False)
		config.conf["freeradio"]["mute_notifications"] = not current
		if not current:
			# Notifications are now muted — speak this final confirmation before silencing.
			ui.message(_("Notifications muted"))
		else:
			ui.message(_("Notifications unmuted"))

	@script(
		description=_("Enable or disable the BASS audio backend"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleBassBackend(self, gesture):
		current = config.conf["freeradio"].get("disable_bass", False)
		config.conf["freeradio"]["disable_bass"] = not current

		if self._dialog is not None and hasattr(self._dialog, "_disable_bass"):
			try:
				self._dialog._disable_bass.SetValue(not current)
			except Exception:
				pass

		label = _("&Disable BASS backend (use VLC/PotPlayer/WMP instead)").replace("&", "")
		ui.message(_("%(effect)s %(state)s") % {
			"effect": label,
			"state": _("enabled") if not current else _("disabled"),
		})
		ui.message(_("Restart NVDA for this change to take effect."))

	@script(
		description=_("Toggle bass boost"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleBassBoost(self, gesture):
		self._toggle_eq_band("eq_bass", _("EQ: Bass Boost"))

	@script(
		description=_("Toggle treble boost"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleTrebleBoost(self, gesture):
		self._toggle_eq_band("eq_treble", _("EQ: Treble Boost"))

	@script(
		description=_("Toggle vocal boost"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleVocalBoost(self, gesture):
		self._toggle_eq_band("eq_vocal", _("EQ: Vocal Boost"))

	def _toggle_eq_band(self, band, label):
		"""Toggle an EQ band on/off.

		The BASS engine only applies a ParamEQ gain if the corresponding
		effect name (e.g. "eq_bass") is part of the active FX list, so
		toggling must add/remove that name from "audio_fx" via set_fx,
		in addition to (re)applying the saved gain via set_eq_gain.
		"""
		if config.conf["freeradio"].get("disable_bass", False):
			ui.message(_("Note: Audio device selection, effects, and mirroring require BASS backend."))
			return

		fx_str = config.conf["freeradio"].get("audio_fx", "none")
		active = [f.strip() for f in fx_str.split(",") if f.strip() and f.strip() != "none"]

		gain_key = "eq_gain_" + band
		_eq_defaults = {"eq_bass": 9, "eq_treble": 9, "eq_vocal": 6}

		if band in active:
			# Currently on: remove from the active FX list.
			active.remove(band)
			turning_on = False
		else:
			# Currently off: add to the active FX list.
			active.append(band)
			turning_on = True
			# Ensure a sensible (non-zero) gain is set.
			if config.conf["freeradio"].get(gain_key, 0) == 0:
				config.conf["freeradio"][gain_key] = _eq_defaults.get(band, 6)

		new_fx_str = ",".join(active) if active else "none"
		config.conf["freeradio"]["audio_fx"] = new_fx_str
		gain_db = config.conf["freeradio"].get(gain_key, _eq_defaults.get(band, 6))

		if self._player is not None:
			try:
				self._player.set_fx(new_fx_str)
				self._player.set_eq_gain(band, gain_db)
			except Exception:
				pass

		# Keep the settings panel's effects list and EQ spin controls in sync.
		if self._dialog is not None:
			try:
				if hasattr(self._dialog, "_fx_choice") and hasattr(self._dialog, "_fx_keys"):
					if band in self._dialog._fx_keys:
						idx = self._dialog._fx_keys.index(band)
						self._dialog._fx_choice.Check(idx, turning_on)
						if hasattr(self._dialog, "_update_eq_spins_visibility"):
							self._dialog._update_eq_spins_visibility()
				if hasattr(self._dialog, "_eq_spins_settings"):
					spin = self._dialog._eq_spins_settings.get(band)
					if spin is not None:
						spin.SetValue(gain_db)
			except Exception:
				pass

		# Keep the station browser dialog's effects list and EQ spin controls in sync.
		self._sync_dialog_audio(
			self._player.get_volume() if self._player is not None else 0,
			new_fx_str,
			eq_gains={band: gain_db},
		)

		ui.message(_("%(effect)s %(state)s") % {
			"effect": label,
			"state": _("enabled") if turning_on else _("disabled"),
		})

	@script(
		description=_("Toggle station switch transition (crossfade)"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleStationTransition(self, gesture):
		_cf_order = ["off", "short", "normal", "tuning"]
		_cf_labels = {
			"off":    _("Instant cut (no crossfade)"),
			"short":  _("Short crossfade (1 second)"),
			"normal": _("Normal crossfade (2 seconds)"),
			"tuning": _("Station tuning sound effect"),
		}
		_cf_map = {"off": 0.0, "short": 1.0, "normal": 2.0, "tuning": 0.0}

		current = config.conf["freeradio"].get("crossfade", "off")
		try:
			idx = _cf_order.index(current)
		except ValueError:
			idx = 0
		new_value = _cf_order[(idx + 1) % len(_cf_order)]

		config.conf["freeradio"]["crossfade"] = new_value
		if self._player is not None:
			try:
				self._player.set_tuning_effect_enabled(new_value == "tuning")
				self._player.set_crossfade_duration(_cf_map.get(new_value, 0.0))
			except Exception:
				pass

		# Keep the settings panel's choice control in sync if it's open.
		if self._dialog is not None and hasattr(self._dialog, "_crossfade_choice"):
			try:
				self._dialog._crossfade_choice.SetSelection(_cf_order.index(new_value))
			except Exception:
				pass

		ui.message(_cf_labels.get(new_value, new_value))

	@script(
		description=_("Enable or disable auto-announce track changes (ICY metadata)"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleAnnounceTrackChanges(self, gesture):
		current = config.conf["freeradio"].get("announce_track_changes", False)
		config.conf["freeradio"]["announce_track_changes"] = not current

		# Keep the settings panel's checkbox and voice choice in sync if it's open.
		if self._dialog is not None and hasattr(self._dialog, "_announce_track_changes"):
			try:
				self._dialog._announce_track_changes.SetValue(not current)
				if hasattr(self._dialog, "_track_change_voice"):
					self._dialog._track_change_voice.Enable(not current)
			except Exception:
				pass

		ui.message(_("%(effect)s %(state)s") % {
			"effect": _("&Auto-announce track changes (ICY metadata)").replace("&", ""),
			"state": _("enabled") if not current else _("disabled"),
		})

	@script(
		description=_("Switch track change announcement voice"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_switchTrackChangeVoice(self, gesture):
		current = config.conf["freeradio"].get("track_change_voice", "nvda")
		new_value = "sapi5" if current != "sapi5" else "nvda"
		config.conf["freeradio"]["track_change_voice"] = new_value

		# Keep the settings panel's voice choice in sync if it's open.
		if self._dialog is not None and hasattr(self._dialog, "_track_change_voice"):
			try:
				self._dialog._track_change_voice.SetSelection(0 if new_value != "sapi5" else 1)
			except Exception:
				pass

		ui.message("SAPI5" if new_value == "sapi5" else "NVDA")

	@script(
		description=_("Turn on or off saving liked songs to a text file"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_toggleSaveLikedSongs(self, gesture):
		current = config.conf["freeradio"].get("save_liked_songs", False)
		config.conf["freeradio"]["save_liked_songs"] = not current

		# Keep the settings panel's checkbox in sync if it's open.
		if self._dialog is not None and hasattr(self._dialog, "_save_liked_songs"):
			try:
				self._dialog._save_liked_songs.SetValue(not current)
			except Exception:
				pass

		ui.message(_("%(effect)s %(state)s") % {
			"effect": _("&Save liked songs to a text file").replace("&", ""),
			"state": _("enabled") if not current else _("disabled"),
		})

	def _open_dialog(self, focus=None):
		"""Show the station browser dialog, optionally switching to a specific tab.

		focus — controls which tab/widget receives focus after the dialog is shown:
		  None          : no tab switch; focus stays wherever the dialog left it.
		  "favorites"   : switch to the Favourites tab (index 1).
		  "search"      : switch to the All Stations tab and focus the search box.
		  0..4 (int)    : switch to the tab at that index.
		                  0=All Stations, 1=Favourites, 2=Recording,
		                  3=Timer, 4=Liked Songs.

		All tab switching is done here — after Show() and Raise() — so that the
		notebook HWND is guaranteed to be fully realized before SetSelection is
		called.  This avoids the wxAssertionError / SystemError that fires when
		SetSelection is called on a notebook whose Win32 tab-control item count
		is still out of sync with wxNotebook's internal page list.

		If a dialog instance exists but its underlying wx object is no longer
		valid (bool(wx_object) is False when the C++ peer has been destroyed) or
		its notebook has become corrupted, it is destroyed and rebuilt from scratch.
		"""
		if self._dialog is not None:
			notebook_ok = False
			try:
				notebook_ok = bool(self._dialog) and self._dialog._notebook.GetPageCount() > 0
			except Exception:
				pass
			if not notebook_ok:
				try:
					self._dialog.Bind(wx.EVT_CLOSE, None)
					self._dialog.Destroy()
				except Exception:
					pass
				# The corrupt dialog already called postPopup() when it was hidden,
				# but if it was never properly shown the prePopup() call that
				# accompanied its creation is still unbalanced.  Call postPopup()
				# here to restore the counter before we create a fresh dialog below.
				try:
					gui.mainFrame.postPopup()
				except Exception:
					pass
				self._dialog = None

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
			# prePopup() was called once when the dialog was first created.  Every
			# time the dialog is hidden, radioDialog calls postPopup() to balance it.
			# So each re-show needs a matching prePopup() call.
			gui.mainFrame.prePopup()
			self._dialog.Show()
		self._dialog.Raise()
		try:
			self._dialog.refresh_audio_devices(force=True)
		except Exception:
			pass

		# Apply the requested tab/focus after yielding to the event loop once
		# (wx.CallLater with 0 ms).  This gives wx time to render Show()/Raise()
		# before SetSelection runs — eliminating the lag on Recording/Timer tabs —
		# and also ensures the notebook HWND is fully realized on first creation,
		# which fixes the wrong-tab-on-first-open bug (IsShown() is still False
		# at this point when the dialog was just constructed).
		if focus is None:
			return
		def _apply_focus():
			if not self._dialog:
				return
			try:
				if focus == "favorites":
					self._dialog.focus_favorites()
				elif focus == "search":
					self._dialog.focus_search()
				elif isinstance(focus, int):
					self._dialog.focus_tab(focus)
			except Exception:
				pass
		wx.CallLater(0, _apply_focus)

	def _open_dialog_on_favorites(self):
		"""Open the dialog and switch to the Favourites tab."""
		self._open_dialog(focus="favorites")

	def _open_dialog_on_search(self):
		"""Open the dialog and switch to the All Stations tab / search box."""
		self._open_dialog(focus="search")

	def _open_dialog_on_tab(self, tab_index):
		"""Open the dialog and switch to the given tab.
		Indices: 0=All Stations, 1=Favourites, 2=Recording, 3=Timer, 4=Liked Songs.
		"""
		self._open_dialog(focus=tab_index)

	def _on_station_selected(self, station, stations, index, announce=True):
		self._stations      = stations
		self._current_index = index
		self._play_station(station, announce)

	def _check_for_updates(self, silent=False):
		"""Fetch the latest release from GitHub and prompt the user if a newer version is available.
		silent=True: only notify when an update is found (used on startup).
		silent=False: always report the result (used when triggered manually from menu)."""
		import json
		import urllib.request
		import urllib.error
		import webbrowser

		API_URL = "https://api.github.com/repos/Surveyor123/freeradio/releases/latest"

		# Retrieve the currently installed addon version via addonHandler
		current_version = None
		try:
			for addon in addonHandler.getAvailableAddons():
				if addon.manifest.get("name") == "freeradio":
					current_version = addon.manifest.get("version", "")
					break
		except Exception:
			pass

		# Fetch latest release metadata from GitHub
		try:
			req = urllib.request.Request(
				API_URL,
				headers={"User-Agent": "freeradio-nvda-addon"},
			)
			with urllib.request.urlopen(req, timeout=10) as resp:
				data = json.loads(resp.read().decode("utf-8"))
		except urllib.error.HTTPError as e:
			if e.code == 404:
				# No releases published on GitHub yet
				log.warning("FreeRadio: No releases found on GitHub.")
				if not silent:
					wx.CallAfter(ui.message, _("No releases found on GitHub yet."))
			else:
				log.warning(f"FreeRadio: Update check HTTP error: {e.code}")
				if not silent:
					wx.CallAfter(ui.message, _("Update check failed (HTTP %d).") % e.code)
			return
		except Exception as e:
			log.warning(f"FreeRadio: Update check failed: {e}")
			if not silent:
				wx.CallAfter(ui.message, _("Update check failed. Please check your internet connection."))
			return

		latest_tag = data.get("tag_name", "").lstrip("v")
		release_url = data.get("html_url", "https://github.com/Surveyor123/freeradio/releases/latest")

		# Find the .nvda-addon asset download URL if available
		download_url = release_url
		for asset in data.get("assets", []):
			if asset.get("name", "").endswith(".nvda-addon"):
				download_url = asset.get("browser_download_url", release_url)
				break

		if not latest_tag:
			if not silent:
				wx.CallAfter(ui.message, _("Could not determine latest version."))
			return

		# Compare versions as tuples of integers for reliable ordering
		def _parse(v):
			try:
				return tuple(int(x) for x in v.split("."))
			except Exception:
				return (0,)

		is_newer = _parse(latest_tag) > _parse(current_version or "0")

		if is_newer:
			def _prompt():
				# Decide button labels based on whether a direct .nvda-addon asset exists
				direct_install = download_url != release_url
				if direct_install:
					msg = _(
						# Translators: Update dialog message when direct install is available. %(new)s=new version, %(current)s=current version
						"A new version of FreeRadio is available: %(new)s.\n"
						"You have version %(current)s.\n\n"
						"Would you like to download and install it now?"
					) % {"new": latest_tag, "current": current_version or _("unknown")}
					yes_label = _("&Install")
				else:
					msg = _(
						# Translators: Update dialog message when only a download page is available. %(new)s=new version, %(current)s=current version
						"A new version of FreeRadio is available: %(new)s.\n"
						"You have version %(current)s.\n\n"
						"Would you like to open the download page?"
					) % {"new": latest_tag, "current": current_version or _("unknown")}
					yes_label = _("&Open Page")

				dlg = wx.MessageDialog(
					gui.mainFrame,
					msg,
					_("FreeRadio Update Available"),
					wx.YES_NO | wx.YES_DEFAULT | wx.ICON_INFORMATION,
				)
				dlg.SetYesNoLabels(yes_label, _("&Cancel"))
				if dlg.ShowModal() == wx.ID_YES:
					if direct_install:
						# Download the .nvda-addon and hand it to NVDA for installation
						threading.Thread(
							target=_do_install,
							args=(download_url, latest_tag),
							daemon=True,
						).start()
					else:
						webbrowser.open(release_url)
				dlg.Destroy()

			def _do_install(url, version):
				import tempfile
				wx.CallAfter(ui.message, _("Downloading FreeRadio %s…") % version)
				try:
					req = urllib.request.Request(
						url,
						headers={"User-Agent": "freeradio-nvda-addon"},
					)
					with urllib.request.urlopen(req, timeout=60) as resp:
						data_bytes = resp.read()
					tmp_path = os.path.join(
						tempfile.gettempdir(),
						"freeradio-%s.nvda-addon" % version,
					)
					with open(tmp_path, "wb") as fh:
						fh.write(data_bytes)
				except Exception as e:
					log.error("FreeRadio: Download failed: %s", e)
					wx.CallAfter(
						ui.message,
						_("Download failed: %s") % str(e),
					)
					return
				# os.startfile triggers NVDA's built-in addon installer for .nvda-addon files
				try:
					os.startfile(tmp_path)
				except Exception as e:
					log.error("FreeRadio: Could not launch installer: %s", e)
					wx.CallAfter(
						ui.message,
						_("Could not launch installer. File saved to: %s") % tmp_path,
					)

			wx.CallAfter(_prompt)
		else:
			if not silent:
				def _up_to_date():
					dlg = wx.MessageDialog(
						gui.mainFrame,
						_("FreeRadio is up to date. Installed: %s") % (current_version or _("unknown")),
						_("FreeRadio Update Check"),
						wx.OK | wx.ICON_INFORMATION,
					)
					dlg.ShowModal()
					dlg.Destroy()
				wx.CallAfter(_up_to_date)

	def _check_internet(self, timeout=3):
		"""Internet connectivity check - all targets tested in parallel.
		Returns True as soon as any host responds; waits at most `timeout` seconds.
		Falls back to HTTP requests only if all socket probes fail.
		"""
		import socket
		import urllib.request

		test_hosts = [
			("8.8.8.8", 53),         # Google DNS
			("1.1.1.1", 53),         # Cloudflare DNS
			("208.67.222.222", 53),  # OpenDNS
		]

		success = threading.Event()

		def _probe(host, port):
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.settimeout(timeout)
				s.connect((host, port))
				s.close()
				success.set()
			except Exception:
				pass

		for host, port in test_hosts:
			threading.Thread(target=_probe, args=(host, port), daemon=True).start()

		# Return immediately when the first probe succeeds; give up after timeout.
		if success.wait(timeout=timeout):
			return True

		# Last resort: Try HTTP request (to Radio Browser API)
		try:
			req = urllib.request.Request(
				"https://de1.api.radio-browser.info/json/stats",
				headers={"User-Agent": "FreeRadio/1.0"}
			)
			with urllib.request.urlopen(req, timeout=timeout) as resp:
				return resp.status == 200
		except Exception:
			pass

		# Try an HTTP site (for broader compatibility)
		try:
			req = urllib.request.Request(
				"http://neverssl.com/online",
				headers={"User-Agent": "FreeRadio/1.0"}
			)
			with urllib.request.urlopen(req, timeout=timeout) as resp:
				return resp.status == 200
		except Exception:
			return False

	def _resume_last_station(self):
		url  = config.conf["freeradio"].get("last_station_url", "").strip()
		name = config.conf["freeradio"].get("last_station_name", "").strip()
		uuid = config.conf["freeradio"].get("last_station_uuid", "").strip()
		tags = config.conf["freeradio"].get("last_station_tags", "").strip()
		# Safety net for a config saved before "last_station_tags" existed
		# (or any other reason it came back empty): a URL that has a
		# recorded podcast resume position is, by construction, a podcast
		# episode, even without the tag.
		if "podcast" not in tags and self._player.has_podcast_position_entry(url):
			tags = "podcast"
		
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
		
		# If still not found, create a minimal station object. Podcast
		# episodes never end up in favourites, so this is always the path
		# they take - carry over the saved "tags" (e.g. "podcast") so
		# _play_station()/RadioPlayer.play() still recognise it as a
		# podcast and seek to the saved position instead of restarting
		# from 0:00.
		if station is None:
			station = {
				"name": name, 
				"url": url, 
				"url_resolved": url,
				"stationuuid": uuid, 
				"countrycode": "", 
				"tags": tags, 
				"votes": 0
			}
		
		self._play_station(station)

	def _build_station_details(self):
		"""Return station information (including stream URL) as a list of (label, value) rows."""
		from .utils import country_name as _country_name
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
				# Duplicate check: don't add the same song if it is already in the list
				existing = []
				if os.path.isfile(liked_path):
					with open(liked_path, encoding="utf-8") as fh:
						existing = [l.rstrip("\n") for l in fh if l.strip()]
				if text in existing:
					ui.message(_("Already in liked songs: %s") % text)
				else:
					with open(liked_path, "a", encoding="utf-8") as fh:
						fh.write("%s\n" % text)
			except Exception as e:
				log.error("FreeRadio: could not save liked song: %s", e)

	def _icy_poll_loop(self):
		"""Background thread: polls ICY metadata every ~5 s and announces changes.

		When a song-capture recording is active the loop also watches for track
		changes.  As soon as the ICY title differs from the one that was current
		when recording started, the recording is stopped automatically and the
		user is notified via NVDA speech.
		"""
		import time as _time
		_INTERVAL = 5.0
		while not self._icy_poll_stop.wait(timeout=_INTERVAL):
			try:
				if not self._player.is_playing():
					# Player stopped/paused — clear memory so stale title is never re-announced.
					self._icy_last_title = None
					# If a song-capture was running while the station stopped, end it cleanly.
					if self._recorder.is_song_capture():
						path = self._recorder.stop_song_capture()
						if path:
							wx.CallAfter(
								ui.message,
								_("Song recording saved: %s") % os.path.basename(path),
							)
					continue

				# Fetch the current ICY title (in-memory cache first, live probe as fallback).
				icy = self._player.get_icy_title()
				if not icy:
					from . import radioPlayer as _rp
					url = (
						getattr(self._player, "_current_url_resolved", None)
						or getattr(self._player, "_current_url", None)
					)
					if url:
						icy = _rp._read_icy_title(url)

				# ---------------------------------------------------------- #
				# Song-capture auto-stop: end recording when the track changes #
				# ---------------------------------------------------------- #
				if self._recorder.is_song_capture():
					recorded_title = self._recorder.get_song_title()
					if icy and recorded_title and icy != recorded_title:
						# The track has changed — stop the recording automatically.
						path = self._recorder.stop_song_capture()
						if path:
							wx.CallAfter(
								ui.message,
								_("Song recording saved: %s") % os.path.basename(path),
							)
						else:
							wx.CallAfter(_notify, _("Song recording stopped"))

				if not icy:
					# This station publishes no ICY metadata.
					# Wipe last title so we never repeat the previous station's track
					# if/when we return to a metadata-capable station later.
					self._icy_last_title = ""
					continue

				# ---------------------------------------------------------- #
				# Track-change announcements (controlled by user setting)      #
				# ---------------------------------------------------------- #
				if not config.conf["freeradio"].get("announce_track_changes", False):
					# Still keep _icy_last_title current for song-capture comparisons.
					if self._icy_last_title is None:
						self._icy_last_title = icy
					elif icy != self._icy_last_title:
						self._icy_last_title = icy
					continue

				if self._icy_last_title is None:
					# First read after a station change — announce immediately and store.
					self._icy_last_title = icy
					if config.conf["freeradio"].get("track_change_voice", "nvda") == "sapi5":
						_sapi5_speak(icy)
					else:
						wx.CallAfter(_notify, icy)
					continue

				if icy != self._icy_last_title:
					self._icy_last_title = icy
					if config.conf["freeradio"].get("track_change_voice", "nvda") == "sapi5":
						_sapi5_speak(icy)
					else:
						wx.CallAfter(_notify, icy)
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

		# Check internet connectivity before attempting to stream
		# (skipped if the user has disabled this check in settings)
		if not config.conf["freeradio"].get("disable_internet_check", False):
			if not self._check_internet():
				ui.message(_("No internet connection. Please check your connection and try again."))
				return

		try:
			config.conf["freeradio"]["last_station_url"]  = url_resolved or url
			config.conf["freeradio"]["last_station_name"] = name
			config.conf["freeradio"]["last_station_uuid"] = station_uuid
			# Needed so a podcast episode resumed on the next NVDA startup is
			# still recognised as a podcast (see _resume_last_station) -
			# without this, the reconstructed station dict has no "tags",
			# the seek-to-saved-position logic never triggers, and the
			# episode silently restarts from 0:00 instead of resuming.
			config.conf["freeradio"]["last_station_tags"] = station.get("tags", "")
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
			# Apply station-specific EQ gains if present
			eq_gains = station_audio.get("eq_gains", {})
			for band, gain_db in eq_gains.items():
				try:
					self._player.set_eq_gain(band, gain_db)
				except Exception:
					pass
			self._sync_dialog_audio(vol, fx, eq_gains=eq_gains)
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
				# Restore global EQ gains
				_eq_defaults = {"eq_bass": 9, "eq_treble": 9, "eq_vocal": 6}
				for band, default_db in _eq_defaults.items():
					gain_db = config.conf["freeradio"].get("eq_gain_" + band, default_db)
					try:
						self._player.set_eq_gain(band, gain_db)
					except Exception:
						pass
			self._sync_dialog_audio(global_vol, global_fx)

		self._pending_url     = url
		self._pending_station = station
		self._icy_last_title  = None        # None = station just changed; suppress first read
		wx.CallAfter(self._start_playing, url, name, url_resolved)
		if announce:
			if not _notifications_muted():
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

		# --- Time-shift buffer checkbox ---
		# Off by default: keeps a rolling ~10 minute local buffer of the
		# live stream so the user can rewind/fast-forward it like a
		# cassette tape. Requires the BASS backend.
		self._timeshift_enabled = wx.CheckBox(
			self,
			label=_("&Enable time-shift buffer (rewind live radio, ~10 minutes)")
		)
		self._timeshift_enabled.SetValue(config.conf["freeradio"].get("timeshift_enabled", False))
		sHelper.addItem(self._timeshift_enabled)

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
			wx.CheckListBox,
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
			label=_("(empty = default: Documents\\FreeRadio Recordings)"),
		)
		_default_hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
		rec_dir_browse = wx.Button(self, label=_("Brow&se folder..."))
		rec_dir_sizer.Add(self._recordings_dir, 1, wx.EXPAND | wx.RIGHT, 5)
		rec_dir_sizer.Add(rec_dir_browse, 0)
		sHelper.addItem(rec_dir_sizer, flag=wx.EXPAND)
		sHelper.addItem(_default_hint)
		rec_dir_browse.Bind(wx.EVT_BUTTON, self._on_browse_recordings_dir)

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
		self._audio_device_refresh_label.Show(not disable_bass)
		self._audio_device_refresh_choice.Show(not disable_bass)
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

		# EQ gain spins - BASS only; also respect active-band visibility
		if disable_bass:
			for band in self._eq_spins_settings:
				self._eq_spins_settings[band].Show(False)
				self._eq_spin_labels_settings[band].Show(False)
		else:
			self._update_eq_spins_visibility()
		
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
		for plugin in globalPluginHandler.runningPlugins:
			if isinstance(plugin, GlobalPlugin):
				try:
					resolved, resolved_name, match = plugin._player.resolve_audio_device(
						devices,
						saved,
						saved_name,
					)
				except Exception:
					resolved_name = saved_name
				break
		if match == "name" and resolved != saved:
			config.conf["freeradio"]["audio_device"] = resolved
			config.conf["freeradio"]["audio_device_name"] = resolved_name
			for plugin in globalPluginHandler.runningPlugins:
				if isinstance(plugin, GlobalPlugin):
					try:
						actual = plugin._player.switch_output_device(resolved)
					except Exception:
						actual = getattr(plugin._player, "_output_device_index", resolved)
					if actual != resolved:
						config.conf["freeradio"]["audio_device"] = actual
						config.conf["freeradio"]["audio_device_name"] = self._audio_device_name_for_index(actual)
						resolved = actual
					break
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
		for plugin in globalPluginHandler.runningPlugins:
			if isinstance(plugin, GlobalPlugin):
				try:
					plugin._player.set_fx(fx_str)
				except Exception:
					pass
				break
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
		for plugin in globalPluginHandler.runningPlugins:
			if isinstance(plugin, GlobalPlugin):
				try:
					plugin._player.set_eq_gain(band, gain_db)
				except Exception:
					pass
				break
		event.Skip()

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

	def _on_check_now(self, event):
		"""Trigger a manual update check from the settings panel."""
		self._check_now_btn.Disable()
		self._check_now_btn.SetLabel(_("Checking..."))
		def _run():
			for plugin in globalPluginHandler.runningPlugins:
				if isinstance(plugin, GlobalPlugin):
					plugin._check_for_updates(silent=False)
					break
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
		
		# Save disable_bass setting
		new_disable_bass = self._disable_bass.GetValue()
		old_disable_bass = config.conf["freeradio"].get("disable_bass", False)
		config.conf["freeradio"]["disable_bass"] = new_disable_bass

		_refresh_sel = self._audio_device_refresh_choice.GetSelection()
		new_audio_device_refresh_mode = (
			_AUDIO_DEVICE_REFRESH_MODE_KEYS[_refresh_sel]
			if 0 <= _refresh_sel < len(_AUDIO_DEVICE_REFRESH_MODE_KEYS)
			else "reliable"
		)
		config.conf["freeradio"]["audio_device_refresh_mode"] = new_audio_device_refresh_mode
		
		# Audio output device (only if BASS enabled)
		old_device_index = config.conf["freeradio"].get("audio_device", -1)
		old_device_name = config.conf["freeradio"].get("audio_device_name", "")
		if not new_disable_bass:
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
		else:
			new_device_index = -1
			new_device_name = ""
			config.conf["freeradio"]["audio_device_name"] = ""
		
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
		config.conf["freeradio"]["auto_check_updates"] = self._auto_check_updates.GetValue()
		config.conf["freeradio"]["disable_internet_check"] = self._disable_internet_check.GetValue()

		# Crossfade
		_cf_sel = self._crossfade_choice.GetSelection()
		_cf_val = self._cf_keys[_cf_sel] if 0 <= _cf_sel < len(self._cf_keys) else "off"
		config.conf["freeradio"]["crossfade"] = _cf_val

		# Time-shift buffer
		new_timeshift_enabled = self._timeshift_enabled.GetValue()
		config.conf["freeradio"]["timeshift_enabled"] = new_timeshift_enabled

		for plugin in globalPluginHandler.runningPlugins:
			if isinstance(plugin, GlobalPlugin):
				plugin._player.set_audio_device_refresh_mode(new_audio_device_refresh_mode)
				plugin._player.set_volume(vol)
				plugin._player.set_timeshift_enabled(new_timeshift_enabled)
				
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
					plugin._player.set_audio_device_refresh_mode(new_audio_device_refresh_mode)
					plugin._player.set_volume(vol)
					plugin._player.set_timeshift_enabled(new_timeshift_enabled)
					plugin._player.on_device_lost = plugin._on_audio_device_lost
					plugin._player.on_podcast_progress_saved = plugin._on_podcast_progress_saved
					if not new_disable_bass:
						try:
							actual_device_index = plugin._player.switch_output_device(new_device_index)
						except Exception:
							actual_device_index = getattr(plugin._player, "_output_device_index", new_device_index)
						if actual_device_index != new_device_index:
							config.conf["freeradio"]["audio_device"] = actual_device_index
							config.conf["freeradio"]["audio_device_name"] = self._audio_device_name_for_index(actual_device_index)
							new_device_index = actual_device_index
							new_device_name = config.conf["freeradio"].get("audio_device_name", "")
					
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
			# Use _notify so the message is suppressed when notifications are muted.
			wx.CallAfter(_notify, _("Sleep timer: radio stopped"))

	def _fade_and_stop(self):
		"""Gradually reduce volume to 0 over 60 seconds, then stop."""
		import time
		_FADE_DURATION  = 60
		_FADE_STEPS     = 20
		_STEP_INTERVAL  = _FADE_DURATION / _FADE_STEPS

		original_volume = self._player.get_volume()
		# Use _notify so both fade-out messages are suppressed when notifications are muted.
		wx.CallAfter(_notify, _("Sleep timer: fading out…"))

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
		# Use _notify so the stop message is suppressed when notifications are muted.
		wx.CallAfter(_notify, _("Sleep timer: radio stopped"))

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