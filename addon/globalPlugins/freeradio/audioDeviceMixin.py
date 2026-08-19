# -*- coding: utf-8 -*-
# FreeRadio - Output device selection and audio mirroring
#
# Extracted from GlobalPlugin in __init__.py as the first slice of a
# broader script_* grouping. Mixed into GlobalPlugin, so `self` here is a
# GlobalPlugin instance - self._player, self._dialog, and
# self._sync_dialog_device (defined elsewhere on GlobalPlugin) are used
# as normal instance attributes/methods via the class's MRO, no import
# needed for those.

import threading
import config
import gui
import ui
import wx
from scriptHandler import script

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr


class AudioDeviceMixin:
	"""Output device selection, audio mirroring, and device-loss handling."""

	@script(
		description=_("Select the main FreeRadio output device"),
		category=_("FreeRadio"),
		# No gesture assigned by default; bind one via NVDA's Input Gestures dialog.
	)
	def script_selectOutputDevice(self, gesture):
		self._request_output_device_selection()

	def _request_output_device_selection(self):
		"""Open the main-output picker on demand when multiple devices exist."""
		if config.conf["freeradio"].get("disable_bass", False):
			ui.message(
				_("Audio device selection requires BASS backend. Enable it in FreeRadio settings.")
			)
			return
		if getattr(self, "_output_device_dialog_open", False):
			return
		self._output_device_dialog_open = True

		def _fetch_devices():
			try:
				devices = self._player.get_audio_devices()
			except Exception:
				devices = []
			wx.CallAfter(self._handle_output_device_list, devices)

		threading.Thread(target=_fetch_devices, daemon=True).start()

	def _handle_output_device_list(self, devices):
		"""Show the picker only when choosing between devices is useful."""
		if not devices:
			self._output_device_dialog_open = False
			ui.message(_("No audio output devices found"))
			return
		if len(devices) == 1:
			self._output_device_dialog_open = False
			ui.message(
				_("Only one physical audio output device is available. FreeRadio uses the system default output.")
			)
			return
		self._show_output_device_dialog(devices)

	def _show_output_device_dialog(self, devices):
		"""Show an accessible, preselected list of the available BASS outputs."""
		choices = [(-1, _("System default"))] + list(devices)
		saved_index = config.conf["freeradio"].get("audio_device", -1)
		saved_name = config.conf["freeradio"].get("audio_device_name", "")
		try:
			resolved_index, _resolved_name, match = self._player.resolve_audio_device(
				devices,
				saved_index,
				saved_name,
			)
		except Exception:
			resolved_index, match = saved_index, "missing"
		if match == "missing":
			resolved_index = getattr(self._player, "_output_device_index", -1)

		selection = 0
		for i, (device_index, _device_name) in enumerate(choices):
			if device_index == resolved_index:
				selection = i
				break

		try:
			gui.mainFrame.prePopup()
			dlg = wx.SingleChoiceDialog(
				gui.mainFrame,
				_("Select the main output device:"),
				_("FreeRadio Output Device"),
				[name for (_index, name) in choices],
			)
			dlg.SetSelection(selection)
			result = dlg.ShowModal()
			if result == wx.ID_OK:
				selected_index, selected_name = choices[dlg.GetSelection()]
				if selected_index == resolved_index:
					self._finish_output_device_selection(selected_index, selected_name, devices)
				else:
					self._apply_output_device_selection(selected_index, selected_name, devices)
			dlg.Destroy()
		finally:
			gui.mainFrame.postPopup()
			self._output_device_dialog_open = False

	def _apply_output_device_selection(self, requested_index, requested_name, devices):
		"""Switch output without blocking NVDA, then save and synchronize the UI."""
		def _switch():
			try:
				actual_index = self._player.switch_output_device(requested_index)
			except Exception:
				wx.CallAfter(
					ui.message,
					_("Could not switch to output device: %s") % requested_name,
				)
				return

			actual_name = ""
			if actual_index != -1:
				for device_index, device_name in devices:
					if device_index == actual_index:
						actual_name = device_name
						break
			wx.CallAfter(
				self._finish_output_device_selection,
				actual_index,
				actual_name,
				devices,
			)

		threading.Thread(target=_switch, daemon=True).start()

	def _finish_output_device_selection(self, device_index, device_name, devices):
		"""Persist the selected output and update any open FreeRadio controls."""
		config.conf["freeradio"]["audio_device"] = device_index
		config.conf["freeradio"]["audio_device_name"] = "" if device_index == -1 else device_name
		self._sync_dialog_device(device_index)
		if self._dialog and self._dialog.IsShown() and hasattr(self._dialog, "refresh_audio_devices"):
			self._dialog.refresh_audio_devices(force=True)
		try:
			for win in wx.GetTopLevelWindows():
				if isinstance(win, gui.NVDASettingsDialog):
					panel = win.FindWindowByName("FreeRadio")
					if panel and hasattr(panel, "_populate_devices"):
						panel._populate_devices(devices)
					break
		except Exception:
			pass
		display_name = _("System default") if device_index == -1 else device_name
		ui.message(_("Output device: %s") % display_name)

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
