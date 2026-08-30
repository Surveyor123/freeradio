# -*- coding: utf-8 -*-
# FreeRadio - "What's playing" announcements, station details dialog,
# track-info clipboard/recognition, and the ICY metadata polling loop
#
# Extracted from GlobalPlugin in __init__.py. Mixed into GlobalPlugin, so
# `self` here is a GlobalPlugin instance - self._player, self._recorder,
# self._icy_poll_stop, and helper methods defined elsewhere on GlobalPlugin
# (e.g. self._check_internet, self._open_dialog) are used as normal
# instance attributes/methods via the class's MRO, no import needed for
# those.
#
# _stop_from_dialog lives here too even though it duplicates script_stop's
# logic (PlaybackCoreMixin) - it sits right next to _whats_playing_from_dialog
# and _announce_now in the original file because all three are F2/F8
# dialog-key callbacks (radioDialog.py calls them via self._plugin.<name>),
# and moving it elsewhere would just split one contiguous, cohesive unit for
# no benefit - self resolves it the same regardless of which mixin holds it.
#
# NOTE: every script here with a default gesture= must also be listed in
# GlobalPlugin's __gestures dict in __init__.py (see the __gestures
# comment there for why). Only script_whatsPlaying has one; the others in
# this file are deliberately unbound (see their descriptions).

import logging
import os
import tempfile
import threading
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

from . import _notify, _speak_on_demand, _format_duration, _sapi5_speak

log = logging.getLogger(__name__)


class TrackInfoMixin:
	"""'What's playing' announcements (Ctrl+Win+I, 1x/2x/3x/4x press),
	station-details dialog and clipboard/recognition actions, their F2/F8
	dialog-callback equivalents, and the background ICY metadata poll loop
	that drives track-change announcements and song-capture auto-stop."""

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

	def _build_station_details(self):
		"""Return information about whatever is currently playing as a list
		of (label, value) rows, tailored to what kind of source it is:
		a plain radio station (radio-browser fields - country, bitrate,
		stream URL, ...), a podcast episode, or an audiobook chapter (GETEM
		or LibriVox). Podcasts and audiobooks carry none of the
		radio-browser fields (country/language/bitrate/codec/homepage/
		votes) and showing "Stream URL" for them is actively misleading -
		for a podcast it's just the one episode's file, and for an
		audiobook (GETEM especially) it can be a temporary local streaming
		proxy address that won't mean anything to the user or work once
		copied elsewhere - so each kind gets its own field set instead of
		reusing the radio-station rows with the inapplicable ones dropped."""
		s = self._player.get_current_station()
		if not s:
			return []

		tags = s.get("tags", "").strip()
		tag_set = {t.strip() for t in tags.split(",") if t.strip()}

		if "audiobook" in tag_set:
			return self._build_audiobook_details(s)
		if "podcast" in tag_set:
			return self._build_podcast_details(s)
		return self._build_radio_station_details(s)

	def _build_radio_station_details(self, s):
		"""Details rows for a plain radio-browser station."""
		from .utils import country_name as _country_name

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

	def _build_podcast_details(self, s):
		"""Details rows for a podcast episode. Replaces the radio-station
		fields with ones that actually apply: the podcast (feed) it's
		from, plus an "Episode details" block that reuses the exact same
		By/Published/Duration/description text and strings the Podcasts
		tab's episode-details box shows (via
		RadioDialog._format_episode_details()) - see
		radioDialog._format_podcast_episode_lines() - rather than
		re-inventing separate, newly-translated fields for the same
		information. Also shows the episode's own audio URL (labelled as
		such rather than the generic "Stream URL", since there's only
		ever the one URL here, not a resolved-vs-fallback pair the way a
		radio station can have)."""
		from .radioDialog import _format_podcast_episode_lines

		rows = []

		name = s.get("name", "").strip()
		if name:
			rows.append((_("Episode"), name))

		feed_url = s.get("podcast_feed_url", "").strip()
		if feed_url:
			rows.append((_("Podcast"), feed_url))

		published = s.get("episode_published", "").strip()
		lines = _format_podcast_episode_lines(
			author=s.get("podcast_author", "").strip(),
			published=self._format_episode_date(published) if published else "",
			duration=s.get("episode_duration", "").strip(),
			description=s.get("description", "").strip(),
		)
		if lines:
			rows.append((_("Episode details"), "\n".join(lines)))

		episode_url = s.get("url_resolved", "").strip() or s.get("url", "").strip()
		if episode_url:
			rows.append((_("Episode URL"), episode_url))

		return rows

	def _build_audiobook_details(self, s):
		"""Details rows for a GETEM/LibriVox audiobook chapter. Shows
		which chapter this is, then an "Audio book details" block that
		reuses the exact same Source/Author/Narrator/Publisher/Type/
		description text and strings the Audio Books tab's details box
		shows (via RadioDialog._format_getem_details()) - see
		radioDialog._format_audiobook_lines() - rather than re-inventing
		separate, newly-translated fields for the same information.
		Crucially, the "link" shown here is the book's own detail page
		(getem_detail_url) rather than the chapter's audio URL: for GETEM
		that URL is a temporary local streaming-proxy address (see
		getem.get_stream_url()) that's meaningless once copied out of the
		dialog, and even for LibriVox (a plain public archive.org file
		link) it points at one chapter, not the book the user actually
		thinks of themselves as listening to."""
		from .radioDialog import _format_audiobook_lines

		rows = []

		name = s.get("name", "").strip()
		if name:
			rows.append((_("Book"), name))

		chapter_title = s.get("audiobook_chapter_title", "").strip()
		chapter_index = s.get("getem_chapter_index")
		chapter_count = s.get("audiobook_chapter_count") or 0
		if chapter_title:
			if isinstance(chapter_index, int) and chapter_count:
				rows.append((
					_("Chapter"),
					"%s (%d/%d)" % (chapter_title, chapter_index + 1, chapter_count),
				))
			else:
				rows.append((_("Chapter"), chapter_title))

		lines = _format_audiobook_lines(
			source_label=s.get("audiobook_source", "").strip(),
			author=s.get("author", "").strip(),
			narrator=s.get("narrator", "").strip(),
			publisher=s.get("publisher", "").strip(),
			format_label=s.get("audiobook_format", "").strip(),
			chapter_count=chapter_count,
			description=s.get("description", "").strip(),
		)
		if lines:
			rows.append((_("Audio book details"), "\n".join(lines)))

		book_url = s.get("getem_detail_url", "").strip()
		if book_url:
			rows.append((_("Book link"), book_url))

		return rows

	@staticmethod
	def _format_episode_date(iso_string):
		"""Best-effort human-readable rendering of a
		PodcastEpisode.to_dict() "episode_published" ISO timestamp,
		matching the plain str(datetime) formatting
		RadioDialog._format_episode_details() already uses for the same
		value (via PodcastEpisode.published, a datetime there rather than
		the isoformat() string station_dict carries) so both dialogs show
		the date the same way. Falls back to the raw string if it can't
		be parsed, since showing something is better than dropping the
		row."""
		import datetime
		try:
			return str(datetime.datetime.fromisoformat(iso_string))
		except ValueError:
			return iso_string

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

		# If track info is not yet available, fetch it in the background and
		# insert into dialog. Only applies to plain radio stations - ICY
		# metadata (and the "Station"/"Now playing" rows this inserts
		# next to) doesn't exist for podcasts or audiobooks, and probing
		# for it there would just be a wasted background fetch against a
		# podcast episode URL or a temporary GETEM streaming-proxy address.
		current_station = self._player.get_current_station() or {}
		current_tags = {t.strip() for t in current_station.get("tags", "").split(",") if t.strip()}
		now_playing_label = _("Now playing")
		if not (current_tags & {"podcast", "audiobook"}) and now_playing_label not in field_ctrls:
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

