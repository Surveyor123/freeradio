# -*- coding: utf-8 -*-
# FreeRadio - Sleep/alarm timer manager
#
# Extracted from __init__.py: schedules and persists sleep (stop) and
# alarm (start playback) timers, running them on a background thread.

import os
import logging
import threading
import wx

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr

from . import _notify
from .recorder import _next_active_start

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

	def add_sleep(self, stop_dt, notify_callback=None, recurrence="once", active_days=None):
		"""Schedule a stop at stop_dt (datetime). Returns entry id.

		recurrence: "once" (default) fires once and is done; "weekly"
		re-fires every week on active_days (same convention as
		recorder.ScheduledRecording - a weekday-int list, 0=Monday..6=Sunday,
		empty/None means every day) until removed.
		"""
		_stop = self._action_stop
		def _sleep_action():
			_stop()
		# Translators: Fallback display label for a sleep timer in the pending-timers list, used when no station name applies (unlike an alarm timer, which is labelled with the station name instead).
		return self._add(stop_dt, _sleep_action, _("Sleep timer"), notify_callback,
						kind="sleep", station=None,
						recurrence=recurrence, active_days=active_days)

	def add_alarm(self, start_dt, station, play_callback, notify_callback=None,
	              recurrence="once", active_days=None):
		"""Schedule playback of station at start_dt. Returns entry id.

		recurrence/active_days: see add_sleep() above.
		"""
		def action():
			play_callback(station, [station], 0)
		return self._add(start_dt, action, station.get("name", "?"), notify_callback,
						kind="alarm", station=station,
						recurrence=recurrence, active_days=active_days)

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
					"id":           entry_id,
					"dt":           dt.isoformat(),
					"label":        label,
					"kind":         meta["kind"],
					"station":      meta.get("station"),
					"recurrence":   meta.get("recurrence", "once"),
					"active_days":  meta.get("active_days", []),
				})
		tmp_path = self._save_path + ".tmp"
		try:
			with open(tmp_path, "w", encoding="utf-8") as fh:
				_json.dump(records, fh, ensure_ascii=False, indent=2)
			os.replace(tmp_path, self._save_path)
		except Exception as exc:
			log.error("FreeRadio: failed to save timers: %s", exc)
			try:
				os.remove(tmp_path)
			except OSError:
				pass

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
			kind        = rec.get("kind", "sleep")
			label       = rec.get("label", "")
			station     = rec.get("station")
			entry_id    = rec.get("id")
			recurrence  = rec.get("recurrence", "once")
			active_days = rec.get("active_days") or []
			if dt <= now:
				if recurrence != "weekly":
					continue  # past, one-off — skip
				# Past-due recurring entry (e.g. NVDA was off past its fire
				# time) — roll forward to the next valid occurrence instead
				# of silently dropping it, same idea as
				# recorder._normalise_recurring_occurrence() for scheduled
				# recordings.
				for _ in range(7):
					dt = _next_active_start(dt, active_days)
					if dt is None or dt > now:
						break
				if dt is None or dt <= now:
					continue
			if not entry_id:
				import uuid as _uuid
				entry_id = str(_uuid.uuid4())

			if kind == "sleep":
				_stop = self._action_stop
				def _sleep_action():
					_stop()
				_sleep_action._timer_meta = {
					"kind": "sleep", "station": None,
					"recurrence": recurrence, "active_days": active_days,
				}
				action = _sleep_action
			elif kind == "alarm" and station and self._play_callback:
				_st = station
				_cb = self._play_callback
				def _make_alarm_action(s, cb, rec_, days_):
					def _action():
						cb(s, [s], 0)
					_action._timer_meta = {
						"kind": "alarm", "station": s,
						"recurrence": rec_, "active_days": days_,
					}
					return _action
				action = _make_alarm_action(_st, _cb, recurrence, active_days)
			else:
				continue

			with self._lock:
				self._timers.append((entry_id, dt, action, label, None))

		with self._lock:
			self._timers.sort(key=lambda t: t[1])

	def _add(self, dt, action, label, notify_callback, kind="sleep", station=None,
	         recurrence="once", active_days=None):
		import uuid as _uuid
		entry_id = str(_uuid.uuid4())
		# Attach metadata to the callable for serialisation
		action._timer_meta = {
			"kind": kind, "station": station,
			"recurrence": recurrence, "active_days": list(active_days or []),
		}
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
			# Translators: Spoken when a sleep timer fires and stops playback instantly (nothing was playing to fade out).
			wx.CallAfter(_notify, _("Sleep timer: radio stopped"))

	def _fade_and_stop(self):
		"""Gradually reduce volume to 0 over 60 seconds, then stop."""
		import time
		_FADE_DURATION  = 60
		_FADE_STEPS     = 20
		_STEP_INTERVAL  = _FADE_DURATION / _FADE_STEPS

		original_volume = self._player.get_volume()
		# Use _notify so both fade-out messages are suppressed when notifications are muted.
		# Translators: Spoken when a sleep timer fires while something is playing, before the 60-second volume fade-out begins.
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
		# Translators: Spoken at the end of the fade-out, once volume has reached 0 and playback actually stops.
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
				requeued = []
				for entry in self._timers:
					entry_id, dt, action, label, notify_cb = entry
					if now >= dt:
						fired.append(entry)
						meta = getattr(action, "_timer_meta", None) or {}
						if meta.get("recurrence") == "weekly":
							next_dt = _next_active_start(dt, meta.get("active_days") or [])
							if next_dt is not None:
								requeued.append((entry_id, next_dt, action, label, notify_cb))
					else:
						remaining.append(entry)
				remaining.extend(requeued)
				remaining.sort(key=lambda t: t[1])
				self._timers = remaining

			if fired:
				self._save()  # timer list changed (removed and/or requeued) — update disk
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

			# Clear the wakeup flag BEFORE computing the wait time, so a
			# timer added between the clear() and the wait() below can't
			# have its _wakeup.set() wiped out by our clear() and get
			# skipped past by our full timeout - which for the "no timers
			# left" case can be up to a minute.
			self._wakeup.clear()
			with self._lock:
				if self._timers:
					next_dt = self._timers[0][1]
					wait = max(0.1, (next_dt - _dt.datetime.now()).total_seconds())
					wait = min(wait, _MAX_SLEEP)
				else:
					wait = _MAX_SLEEP

			self._wakeup.wait(timeout=wait)