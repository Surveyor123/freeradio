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
from scriptHandler import script
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
		# Only meaningful when "audiobook" is in last_station_tags - see
		# GlobalPlugin._rebuild_getem_resume_url() in playbackCoreMixin.py.
		# GETEM chapters stream through a local proxy whose registered
		# tokens live only in memory (getem._proxy_chapters), so
		# last_station_url alone is a dead link by the next NVDA startup;
		# these let the resume path look the book back up in the library
		# and re-register a fresh proxy URL for the right chapter.
		"last_station_getem_detail_url":     "string(default='')",
		"last_station_getem_chapter_index":  "integer(default=0)",
		# Only meaningful when "podcast" is in last_station_tags and it's
		# NOT a GETEM audio book (those use the getem_* keys above instead) -
		# lets the resume path re-apply the subscribed feed's saved audio
		# profile (volume/effects/EQ/speed), same as _rebuild_getem_resume_url()
		# does for audio books. See GlobalPlugin._resume_last_station().
		"last_station_podcast_feed_url":     "string(default='')",
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
		"recording_format":       "string(default='original')",
		"recording_mp3_bitrate":  "integer(default=128, min=64, max=320)",
		"auto_check_updates":     "boolean(default=True)",
		"disable_internet_check": "boolean(default=False)",
		"crossfade":              "string(default='off')",  # off | short | normal | tuning
		"result_limit":           "integer(default=1000, min=100, max=10000)",
		"timeshift_enabled":      "boolean(default=False)",
		"timeshift_buffer_seconds": "integer(default=600, min=600, max=18000)",
	}

_init_config()


def _cleanup_orphaned_timeshift_buffers():
	"""Remove leftover freeradio_timeshift_*.buf files from previous
	sessions. TimeShiftBuffer.stop() normally deletes its own buffer file,
	but that only runs on a clean shutdown - an abrupt one (crash, power
	loss, Windows forcing NVDA closed) skips it, leaving the file behind in
	the temp folder. Safe to do unconditionally here: this runs during
	add-on startup, before any capture session of this run has begun, so
	every matching file at this point is necessarily orphaned.
	"""
	try:
		tmp_dir = tempfile.gettempdir()
		for name in os.listdir(tmp_dir):
			if name.startswith("freeradio_timeshift_") and name.endswith(".buf"):
				try:
					os.remove(os.path.join(tmp_dir, name))
				except OSError:
					pass
	except OSError:
		pass


from .settingsPanel import FreeRadioSettingsPanel
from .timerManager import TimerManager
from .audioDeviceMixin import AudioDeviceMixin
from .playbackCoreMixin import PlaybackCoreMixin
from .timeshiftMixin import TimeshiftMixin
from .audioFxMixin import AudioFxMixin
from .recordingMixin import RecordingMixin
from .trackInfoMixin import TrackInfoMixin
from .miscTogglesMixin import MiscTogglesMixin


class GlobalPlugin(MiscTogglesMixin, TrackInfoMixin, RecordingMixin, AudioFxMixin, TimeshiftMixin, PlaybackCoreMixin, AudioDeviceMixin, globalPluginHandler.GlobalPlugin):

	# Default gesture bindings for scripts defined on mixin base classes
	# (AudioDeviceMixin, PlaybackCoreMixin, TimeshiftMixin, AudioFxMixin,
	# RecordingMixin, TrackInfoMixin - MiscTogglesMixin has none, see its
	# module docstring) rather than directly in this class body.
	#
	# NVDA's @script(gesture=...) only auto-registers a default binding for
	# scripts found in the *literal* namespace of the class being built by
	# ScriptableType - it does not walk the MRO - so a gesture= kwarg on a
	# script inherited from a mixin is silently dropped. The __gestures
	# dict below is NVDA's documented alternative mechanism for binding
	# gestures (gesture id -> script name without the "script_" prefix)
	# and is read directly off this class, so it works regardless of which
	# base class actually defines the script. Every default gesture that
	# lives on a mixin must be listed here.
	__gestures = {
		"kb:control+windows+m": "mirrorAudio",
		"kb:control+windows+p": "pauseResume",
		"kb:control+windows+s": "stop",
		"kb:control+windows+rightArrow": "nextStation",
		"kb:control+windows+leftArrow": "prevStation",
		"kb:control+windows+j": "timeshiftRewind",
		"kb:control+windows+k": "timeshiftForward",
		"kb:control+windows+t": "toggleTimeshift",
		"kb:control+windows+upArrow": "volumeUp",
		"kb:control+windows+downArrow": "volumeDown",
		"kb:control+windows+shift+k": "playbackRateUp",
		"kb:control+windows+shift+j": "playbackRateDown",
		"kb:control+windows+e": "toggleRecord",
		"kb:control+windows+w": "openRecordingsFolder",
		"kb:control+windows+i": "whatsPlaying",
	}

	def __init__(self):
		super().__init__()
		_cleanup_orphaned_timeshift_buffers()
		disable_bass = config.conf["freeradio"].get("disable_bass", False)
		self._player  = radioPlayer.RadioPlayer(disable_bass=disable_bass)
		self._player.set_audio_device_refresh_mode(_audio_device_refresh_mode())
		self._player.set_volume(config.conf["freeradio"]["volume"])
		# Time-shift buffer (rewind/fast-forward live radio) - disabled by
		# default, opt-in via the settings panel or config.
		self._player.set_timeshift_enabled(
			config.conf["freeradio"].get("timeshift_enabled", False)
		)
		self._player.set_timeshift_capacity_seconds(
			config.conf["freeradio"].get("timeshift_buffer_seconds", 600)
		)
		self._player.set_timeshift_disk_full_callback(
			lambda: wx.CallAfter(
				_notify,
				_("Time-shift buffer: running low on disk space, the oldest audio is being dropped more aggressively."),
			)
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
		# Auto-advance to the next part when a GETEM audio book chapter
		# reaches its end on its own (regular podcast episodes are left as
		# manual advance - see RadioDialog._on_playback_finished()).
		self._player.on_podcast_finished = self._on_podcast_finished
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
			recording_format=config.conf["freeradio"].get("recording_format", "original"),
			mp3_bitrate=config.conf["freeradio"].get("recording_mp3_bitrate", 128),
			ffmpeg_path=config.conf["freeradio"].get("ffmpeg_path", ""),
		)
		self._recorder._notify_start  = lambda rec: wx.CallAfter(
			_notify, _("Recording started: %s") % rec.station.get("name", "")
		)
		self._recorder._notify_finish = lambda rec: wx.CallAfter(
			_notify, _("Recording finished: %s") % os.path.basename(rec.output_path or "")
		)
		self._recorder._notify_failed = lambda rec: wx.CallAfter(
			_notify,
			_("Recording failed: could not connect to %s") % rec.station.get("name", ""),
		)
		self._recorder._notify_conversion_error = lambda path, error: wx.CallAfter(
			_notify,
			_("Recording conversion failed. The original file was kept: %s")
			% os.path.basename(path or ""),
		)
		self._recorder._notify_folder_fallback = lambda rec, requested, reason: wx.CallAfter(
			_notify,
			_("Could not use the selected folder for '%(station)s' (%(reason)s). "
			  "Saved to the default recordings folder instead.")
			% {"station": rec.station.get("name", ""), "reason": reason},
		)
		self._stations      = []
		self._current_index = -1
		self._dialog        = None
		gui.NVDASettingsDialog.categoryClasses.append(FreeRadioSettingsPanel)
		_timers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timers.json")
		self._timer_manager = TimerManager(
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
		description=_("Open FreeRadio station browser"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+r",
	)
	def script_openDialog(self, gesture):
		wx.CallAfter(self._open_dialog)


	@script(
		description=_("Add currently playing station to favourites, download the whole audio book if one is playing, or download the episode if a podcast is playing"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+v",
	)
	def script_addToFavorites(self, gesture):
		station = self._player.get_current_station()
		if not station:
			ui.message(_("No station is playing"))
			return
		tags = station.get("tags", "")
		# Checked ahead of the plain "podcast" branch below: GETEM chapters
		# carry both tags (see getem.GetemBook.to_dict()), and a whole-book
		# download - into its own folder, all parts - is what's wanted here
		# rather than a single-episode-style download of just this part.
		if "audiobook" in tags:
			self._download_current_getem_book(station)
			return
		if "podcast" in tags:
			self._download_current_podcast_episode(station)
			return
		if self._manager.is_favorite(station):
			ui.message(_("Already in favourites: %s") % station.get("name", "").strip())
			return
		self._manager.add_favorite(station)
		ui.message(_("Added to favourites: %s") % station.get("name", "").strip())
		self._rebuild_station_scripts()

	def _download_current_getem_book(self, station):
		"""Downloads every part of the GETEM audio book currently playing
		into its own folder under the recordings directory - the
		audiobook branch of script_addToFavorites() above. The book
		object (with its already-resolved chapter list) lives on the
		dialog, not here, so this just hands off to it; the dialog
		instance persists (Hide(), not Destroy()) for as long as
		something it started is still playing, so it's expected to exist
		whenever this is reachable."""
		detail_url = station.get("getem_detail_url")
		if not detail_url or not self._dialog:
			ui.message(_("No audio book is playing"))
			return
		try:
			self._dialog.download_getem_book_by_detail_url(detail_url)
		except Exception:
			log.error("FreeRadio: could not start audio book download", exc_info=True)
			ui.message(_("Could not download this audio book."))


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

	def _on_podcast_finished(self, station):
		"""Called (possibly from a background thread - e.g. from
		radioPlayer's stall/finish detection) only when a podcast/GETEM item
		actually reaches its end, never on a plain pause - see
		radioPlayer.RadioPlayer.on_podcast_finished. Marshals onto the UI
		thread and asks the dialog, if open, to react (currently: auto-
		advance to the next GETEM chapter)."""
		wx.CallAfter(self._on_podcast_finished_ui, station)

	def _on_podcast_finished_ui(self, station):
		if self._dialog and self._dialog.IsShown():
			try:
				self._dialog._on_playback_finished(station)
			except Exception:
				pass
		else:
			# The dialog isn't open to react (e.g. auto-advance a GETEM
			# audio book to its next part) - but playback should keep
			# moving forward on its own regardless of whether the
			# FreeRadio window happens to be open, the same way a
			# podcast's resume position keeps saving in the background.
			# Do the advance ourselves, independent of any dialog UI.
			try:
				self._advance_getem_chapter_headless(station)
			except Exception:
				pass


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
		# A GETEM audio book may have kept auto-advancing chapters in the
		# background while this dialog was closed/hidden (see
		# _advance_getem_chapter_headless()) - resync its "now playing"
		# state from the player so F3/F4 book/chapter navigation and the
		# library list's "now playing" indicator reflect the actual
		# current chapter rather than whatever was showing when the
		# dialog was last open.
		try:
			self._dialog._sync_getem_now_playing_from_player()
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
