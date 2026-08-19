# -*- coding: utf-8 -*-
# FreeRadio - Core playback: pause/resume, stop, next/prev station
#
# Extracted from GlobalPlugin in __init__.py. Mixed into GlobalPlugin, so
# `self` here is a GlobalPlugin instance - self._player, self._recorder,
# self._manager, and helper methods defined elsewhere on GlobalPlugin
# (e.g. self._sync_dialog_audio, self._check_internet, self._stop_from_dialog,
# self._open_dialog_on_favorites/_search/_tab, self._announce_now) are used
# as normal instance attributes/methods via the class's MRO, no import
# needed for those.
#
# NOTE: every script here with a default gesture= must also be listed in
# GlobalPlugin's __gestures dict in __init__.py (NVDA's @script(gesture=...)
# auto-registration only sees the literal class a script is defined in, not
# the MRO - see the __gestures comment in __init__.py for details).

import config
import gui
import ui
import wx
from scriptHandler import script, getLastScriptRepeatCount

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr

from . import _notify, _notifications_muted
from .settingsPanel import FreeRadioSettingsPanel


class PlaybackCoreMixin:
	"""Pause/resume, stop, next/prev station, and the shared station-playing
	pipeline (_play_station / _start_playing / _on_station_selected /
	_resume_last_station) that other scripts and dialogs call into."""

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

	def _on_station_selected(self, station, stations, index, announce=True):
		self._stations      = stations
		self._current_index = index
		self._play_station(station, announce)

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
