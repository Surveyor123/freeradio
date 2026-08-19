# -*- coding: utf-8 -*-
# FreeRadio - Instant/song-capture recording toggle, recordings folder,
# and podcast episode download
#
# Extracted from GlobalPlugin in __init__.py. Mixed into GlobalPlugin, so
# `self` here is a GlobalPlugin instance - self._player and self._recorder
# (defined elsewhere on GlobalPlugin) are used as normal instance
# attributes via the class's MRO, no import needed for those.
#
# NOTE: every script here with a default gesture= must also be listed in
# GlobalPlugin's __gestures dict in __init__.py (see the __gestures
# comment there for why).

import logging
import os
import threading
import config
import ui
import wx
from scriptHandler import script, getLastScriptRepeatCount

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr

from . import _notify

log = logging.getLogger(__name__)


class RecordingMixin:
	"""Instant/song-capture recording toggle (Ctrl+Win+E), the recordings
	folder shortcut, and podcast episode download (used by
	script_addToFavorites when a podcast episode is playing)."""

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
				def _stop_song_capture():
					path = self._recorder.stop_song_capture()
					if path:
						wx.CallAfter(
							_notify,
							_("Song recording stopped: %s") % os.path.basename(path),
						)
					else:
						wx.CallAfter(_notify, _("Song recording stopped"))
				threading.Thread(
					target=_stop_song_capture,
					daemon=True,
					name="FreeRadio-SongRecordingFinalize",
				).start()
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
				def _stop_recording():
					path = self._recorder.stop(self._player)
					if path:
						wx.CallAfter(_notify, _("Recording stopped: %s") % os.path.basename(path))
					else:
						wx.CallAfter(_notify, _("Recording stopped"))
				threading.Thread(
					target=_stop_recording,
					daemon=True,
					name="FreeRadio-RecordingFinalize",
				).start()
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

