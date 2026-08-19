# -*- coding: utf-8 -*-
# FreeRadio - Small independent config toggles: mute notifications,
# BASS backend, track-change announcements/voice, save-liked-songs
#
# Extracted from GlobalPlugin in __init__.py. Mixed into GlobalPlugin, so
# `self` here is a GlobalPlugin instance - self._dialog (defined elsewhere
# on GlobalPlugin) is used as a normal instance attribute via the class's
# MRO, no import needed for it.
#
# None of these scripts has a default gesture (all are bound manually via
# NVDA's Input Gestures dialog), so - unlike every other mixin extracted
# so far - nothing needs to be added to GlobalPlugin's __gestures dict.

import config
import ui
from scriptHandler import script

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr


class MiscTogglesMixin:
	"""Standalone on/off config toggles that don't fit any other mixin:
	mute notifications, BASS backend, auto-announce track changes (and its
	voice), and saving liked songs to a text file."""

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

