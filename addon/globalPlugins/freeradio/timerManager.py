# -*- coding: utf-8 -*-
# FreeRadio - Sleep/alarm timer manager
#
# Extracted from __init__.py: schedules and persists sleep (stop) and
# alarm (start playback) timers, running them on a background thread.

import logging
import threading
import wx

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr

from . import _notify

log = logging.getLogger(__name__)


class TimerManager:
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
