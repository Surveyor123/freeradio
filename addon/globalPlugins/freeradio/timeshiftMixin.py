# -*- coding: utf-8 -*-
# FreeRadio - Time-shift (rewind/fast-forward) controls
#
# Extracted from GlobalPlugin in __init__.py. Mixed into GlobalPlugin, so
# `self` here is a GlobalPlugin instance - self._player and self._dialog
# (defined elsewhere on GlobalPlugin) are used as normal instance
# attributes via the class's MRO, no import needed for those.
#
# NOTE: every script here with a default gesture= must also be listed in
# GlobalPlugin's __gestures dict in __init__.py (see the __gestures
# comment there for why).

import logging
import config
import ui
from scriptHandler import script

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr

from . import _notify

log = logging.getLogger(__name__)


class TimeshiftMixin:
	"""Rewind/fast-forward the time-shift buffer (or seek within a podcast
	file), and toggle the time-shift buffer on/off."""

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
				"hls_unsupported": _("Time-shift is not supported for this station's stream (no seekable audio could be extracted)."),
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

