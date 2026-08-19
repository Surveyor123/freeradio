# -*- coding: utf-8 -*-
# FreeRadio - Volume, EQ/bass-treble-vocal boost, crossfade, playback rate
#
# Extracted from GlobalPlugin in __init__.py. Mixed into GlobalPlugin, so
# `self` here is a GlobalPlugin instance - self._player and self._dialog
# (defined elsewhere on GlobalPlugin) are used as normal instance
# attributes via the class's MRO, no import needed for those.
#
# NOTE: every script here with a default gesture= must also be listed in
# GlobalPlugin's __gestures dict in __init__.py (see the __gestures
# comment there for why). Most scripts in this file have no default
# gesture, but volumeUp/volumeDown/playbackRateUp/playbackRateDown do.

import config
import ui
from scriptHandler import script

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr

from . import _notify


class AudioFxMixin:
	"""Volume, playback-rate, EQ band boosts, and crossfade/station-
	transition controls, plus the dialog-sync helpers they share."""

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

	@script(
		description=_("Increase podcast playback speed"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+shift+k",
	)
	def script_playbackRateUp(self, gesture):
		self._report_playback_rate(*self._player.increase_playback_rate())

	@script(
		description=_("Decrease podcast playback speed"),
		category=_("FreeRadio"),
		gesture="kb:control+windows+shift+j",
	)
	def script_playbackRateDown(self, gesture):
		self._report_playback_rate(*self._player.decrease_playback_rate())

	def _report_playback_rate(self, applied, rate, reason):
		if applied:
			if abs(rate - 1.0) < 0.05:
				_notify(_("Rate normal"))
			else:
				_notify(_("Rate %.1f") % rate)
			return
		if reason == "bass_fx_unavailable":
			_notify(_("Playback speed control needs the bass_fx add-on library — see the FreeRadio docs."))
		elif reason in ("not_tempo_stream", "wrong_backend"):
			_notify(_("Playback speed control is only available for podcasts."))
		else:
			_notify(_("Could not change playback speed."))

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

