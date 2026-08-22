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
from . import getem
from . import podcast
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

	def _rebuild_getem_resume_url(self, detail_url, chapter_index):
		"""Re-registers the given GETEM chapter with a freshly (re)started
		local streaming proxy and returns (url, audio_profile), or
		(None, None) if that isn't possible.

		GETEM chapter audio is never played directly - it's relayed
		through a local proxy (see getem._ensure_proxy_server()) whose
		registered chapter tokens (getem._proxy_chapters) live only in
		memory and are lost every NVDA restart, so simply replaying
		config.conf["freeradio"]["last_station_url"] (a URL from the
		*previous* session) always 404s even though the proxy itself is
		listening on the same port again. This rebuilds a fresh, valid
		proxy URL for the saved chapter from the book's own library entry -
		looked up independently here since, on this NVDA-startup resume
		path, no RadioDialog exists yet to already have one loaded (see
		GlobalPlugin._download_current_getem_book() for the contrasting
		case where the dialog is guaranteed to exist). The book's own
		audio_profile (if any) is returned alongside the URL so
		_resume_last_station() can apply it too - see
		playbackCoreMixin._play_station().

		Returns (None, None) if the book isn't in the library (e.g. it was
		removed) or its chapter list was never resolved, in which case the
		caller should not attempt to resume playback."""
		if not detail_url:
			return None, None
		try:
			chapter_index = int(chapter_index)
		except (TypeError, ValueError):
			chapter_index = 0
		try:
			library = getem.GetemLibrary()
		except Exception:
			return None, None
		book = library.get_book_by_key(detail_url)
		if not book or not book.chapters:
			return None, None
		if not (0 <= chapter_index < len(book.chapters)):
			chapter_index = 0
		chapter_url = book.chapters[chapter_index].get("url")
		if not chapter_url:
			return None, None
		try:
			url = getem.get_stream_url(chapter_url, referer=book.detail_url)
		except Exception:
			return None, None
		return url, book.audio_profile

	def _advance_getem_chapter_headless(self, station):
		"""Auto-advance a GETEM audio book to its next part when the current
		part finishes on its own while the FreeRadio dialog isn't open (or
		isn't shown) to do it itself via
		RadioDialog._on_playback_finished()/_play_next_getem_chapter() -
		see GlobalPlugin._on_podcast_finished_ui() in __init__.py.

		Playback should keep moving forward the same way a podcast
		episode's resume position keeps saving in the background,
		regardless of whether the window happens to be open - so this
		mirrors RadioDialog._start_getem_chapter()'s playback and progress-
		tracking, but without touching any dialog UI (list selection/
		focus/"now playing" state), using only the finished station's own
		"getem_detail_url"/"getem_chapter_index" fields plus a fresh,
		dialog-independent GetemLibrary() lookup - the same pattern
		_rebuild_getem_resume_url() uses for the NVDA-startup-resume case.
		If the dialog is later opened while this is playing,
		RadioDialog._sync_getem_now_playing_from_player() picks its state
		back up from the player, same as it does after a startup resume."""
		if not station or "audiobook" not in station.get("tags", ""):
			return
		detail_url = station.get("getem_detail_url")
		if not detail_url:
			return
		try:
			chapter_index = int(station.get("getem_chapter_index", 0))
		except (TypeError, ValueError):
			chapter_index = 0
		try:
			library = getem.GetemLibrary()
		except Exception:
			return
		book = library.get_book_by_key(detail_url)
		if not book or not book.chapters:
			return
		next_index = chapter_index + 1
		if next_index >= len(book.chapters):
			# Reached the end of the book - nothing further to advance to.
			return
		chapter_url = book.chapters[next_index].get("url")
		if not chapter_url:
			return
		try:
			stream_url = getem.get_stream_url(chapter_url, referer=book.detail_url)
		except Exception:
			return

		library.mark_progress(book, next_index)

		station_dict = book.to_dict()
		if book.audio_profile:
			station_dict["station_audio"] = book.audio_profile
		station_dict["name"] = book.chapters[next_index].get("title", book.title)
		station_dict["url"] = stream_url
		station_dict["url_resolved"] = stream_url
		station_dict["getem_chapter_index"] = next_index
		self._play_station(station_dict)

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

		# GETEM audio books need their proxy URL rebuilt fresh every
		# session - see _rebuild_getem_resume_url(). Bail out rather than
		# handing the player a dead URL from the previous session, which
		# would just fail silently a moment later.
		if "audiobook" in tags:
			detail_url = config.conf["freeradio"].get("last_station_getem_detail_url", "").strip()
			chapter_index = config.conf["freeradio"].get("last_station_getem_chapter_index", 0)
			fresh_url, audio_profile = self._rebuild_getem_resume_url(detail_url, chapter_index)
			if not fresh_url:
				ui.message(_(
					"Could not resume the last audio book - it may have been "
					"removed from your library."
				))
				return
			station["url"] = fresh_url
			station["url_resolved"] = fresh_url
			station["getem_detail_url"] = detail_url
			if audio_profile:
				station["station_audio"] = audio_profile
		elif "podcast" in tags:
			# Likewise, re-apply the subscribed feed's saved audio profile
			# (if any) - see _on_episode_play()/_play_station(). Unlike the
			# audiobook case, the episode URL itself is still perfectly
			# playable on its own, so a missing/removed feed just means no
			# profile to apply rather than a reason to give up resuming.
			feed_url = config.conf["freeradio"].get("last_station_podcast_feed_url", "").strip()
			if feed_url:
				try:
					feed = podcast.PodcastManager().get_feed_by_url(feed_url)
				except Exception:
					feed = None
				if feed and feed.audio_profile:
					station["station_audio"] = feed.audio_profile
					station.setdefault("podcast_feed_url", feed_url)

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
			# GETEM audio books additionally need to know which book/part
			# this was, so _resume_last_station() can rebuild a fresh proxy
			# URL for it on the next NVDA startup (last_station_url's proxy
			# URL from *this* session is dead by then - see
			# _rebuild_getem_resume_url()). Cleared to blank/0 for anything
			# else so a stale audiobook resume hint never lingers once the
			# user moves on to a station or podcast.
			if "audiobook" in station.get("tags", ""):
				config.conf["freeradio"]["last_station_getem_detail_url"] = station.get("getem_detail_url", "") or ""
				config.conf["freeradio"]["last_station_getem_chapter_index"] = int(station.get("getem_chapter_index", 0) or 0)
			else:
				config.conf["freeradio"]["last_station_getem_detail_url"] = ""
				config.conf["freeradio"]["last_station_getem_chapter_index"] = 0
			# Same idea for a subscribed podcast feed's saved audio profile -
			# see _on_episode_play()/_resume_last_station(). A GETEM chapter
			# also carries "podcast" in its tags (see GetemBook.to_dict()),
			# so this is explicitly the non-audiobook case only.
			if "podcast" in station.get("tags", "") and "audiobook" not in station.get("tags", ""):
				config.conf["freeradio"]["last_station_podcast_feed_url"] = station.get("podcast_feed_url", "") or ""
			else:
				config.conf["freeradio"]["last_station_podcast_feed_url"] = ""
		except Exception:
			pass

		# Apply station-specific audio profile if one exists, else restore global settings
		station_audio = station.get("station_audio")
		disable_bass = config.conf["freeradio"].get("disable_bass", False)
		is_podcast_like = "podcast" in station.get("tags", "")
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

		# Playback speed - podcasts/audio books only (pitch-preserving
		# tempo change, see RadioPlayer.set_playback_rate_value). Handled
		# as its own step, independent of the volume/fx branch above, so
		# it follows the same "per-item, falls back to normal 1.0x when
		# nothing is saved" rule volume/fx already follow rather than
		# staying sticky: leaving a fast-profiled book for one with no
		# profile of its own must land back on normal speed, or the second
		# book plays at whatever rate the first one left behind.
		if is_podcast_like:
			speed = station_audio.get("speed") if station_audio else None
			try:
				self._player.set_playback_rate_value(speed if speed else 1.0)
			except Exception:
				pass

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
