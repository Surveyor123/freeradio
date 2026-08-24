import datetime
import importlib.util
import json
import pathlib
import sys
import tempfile
import threading
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "addon" / "globalPlugins" / "freeradio"
PACKAGE_NAME = "freeradio_scheduler_under_test"
package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PACKAGE_DIR)]
sys.modules[PACKAGE_NAME] = package

RECORDER_SPEC = importlib.util.spec_from_file_location(
	PACKAGE_NAME + ".recorder", PACKAGE_DIR / "recorder.py",
)
recorder = importlib.util.module_from_spec(RECORDER_SPEC)
sys.modules[RECORDER_SPEC.name] = recorder
RECORDER_SPEC.loader.exec_module(recorder)


def make_recording(start, duration=60, recurrence="indefinite", active_days=None):
	return recorder.ScheduledRecording(
		station={"name": "Test station", "url": "https://stream.example/live"},
		start_time=start,
		duration_minutes=duration,
		record_only=True,
		recurrence=recurrence,
		active_days=[] if active_days is None else active_days,
	)


def make_recorder(schedules):
	instance = recorder.Recorder.__new__(recorder.Recorder)
	instance._scheduled = list(schedules)
	instance._scheduled_lock = threading.RLock()
	instance._active_scheduled = set()
	instance._active_scheduled_lock = threading.Lock()
	instance._persist_schedules = mock.Mock()
	instance._start_scheduled_worker = mock.Mock()
	return instance


class RecurrenceCalculationTests(unittest.TestCase):
	def test_next_occurrence_uses_next_selected_day_not_next_week(self):
		monday = datetime.datetime(2026, 8, 24, 10, 0)
		recording = make_recording(monday, active_days=[0, 1, 2, 3, 4])

		self.assertEqual(
			datetime.datetime(2026, 8, 25, 10, 0),
			recording.next_occurrence(),
		)

	def test_stale_future_date_is_repaired_to_earliest_selected_day(self):
		# Older versions could persist Friday although Tuesday is also active.
		stored = datetime.datetime(2026, 8, 28, 10, 0)
		now = datetime.datetime(2026, 8, 24, 12, 0)

		start, skipped = recorder._normalise_recurring_occurrence(
			stored, 60, [0, 1, 2, 3, 4], now,
		)

		self.assertEqual(datetime.datetime(2026, 8, 25, 10, 0), start)
		self.assertEqual(0, skipped)

	def test_current_occurrence_is_kept_when_its_window_is_open(self):
		stored = datetime.datetime(2026, 8, 17, 10, 0)
		now = datetime.datetime(2026, 8, 24, 10, 15)

		start, _skipped = recorder._normalise_recurring_occurrence(
			stored, 60, [0], now,
		)

		self.assertEqual(datetime.datetime(2026, 8, 24, 10, 0), start)


class ScheduleLoadTests(unittest.TestCase):
	def test_load_migrates_stale_recurring_date_and_saves_it(self):
		now = datetime.datetime(2026, 8, 24, 12, 0)
		with tempfile.TemporaryDirectory() as temp_dir:
			path = pathlib.Path(temp_dir) / "freeradio_schedules.json"
			path.write_text(json.dumps([{
				"station": {"name": "Test station", "url": "https://stream.example/live"},
				"start_time": "2026-08-28T10:00:00",
				"duration_minutes": 60,
				"recurrence": "indefinite",
				"active_days": [0, 1, 2, 3, 4],
			}]), encoding="utf-8")

			with mock.patch.object(recorder, "_schedules_path", return_value=str(path)):
				loaded = recorder._load_schedules(now=now)

			self.assertEqual(1, len(loaded))
			self.assertEqual(datetime.datetime(2026, 8, 25, 10, 0), loaded[0].start_time)
			persisted = json.loads(path.read_text(encoding="utf-8"))
			self.assertEqual("2026-08-25T10:00:00", persisted[0]["start_time"])

	def test_load_recovers_to_the_exact_remaining_seconds(self):
		now = datetime.datetime(2026, 8, 24, 10, 59, 45)
		with tempfile.TemporaryDirectory() as temp_dir:
			path = pathlib.Path(temp_dir) / "freeradio_schedules.json"
			path.write_text(json.dumps([{
				"station": {"name": "Test station", "url": "https://stream.example/live"},
				"start_time": "2026-08-24T10:00:00",
				"duration_minutes": 60,
				"recurrence": "indefinite",
				"active_days": [0],
			}]), encoding="utf-8")

			with mock.patch.object(recorder, "_schedules_path", return_value=str(path)):
				loaded = recorder._load_schedules(now=now)

			self.assertEqual(15, loaded[0].catchup_duration_seconds)


class SchedulerTickTests(unittest.TestCase):
	def test_late_tick_inside_window_records_only_remaining_seconds(self):
		start = datetime.datetime(2026, 8, 24, 10, 0)
		now = datetime.datetime(2026, 8, 24, 10, 59, 45)
		recording = make_recording(start)
		instance = make_recorder([recording])

		fired = instance._scheduler_tick(now=now)

		self.assertEqual([recording], fired)
		self.assertEqual(15, recording.catchup_duration_seconds)
		self.assertEqual([], instance._scheduled)
		instance._persist_schedules.assert_called_once_with(extra_active=[recording])
		instance._start_scheduled_worker.assert_called_once_with(recording)

	def test_fully_missed_recurring_entry_rolls_to_next_selected_day(self):
		start = datetime.datetime(2026, 8, 24, 10, 0)
		now = datetime.datetime(2026, 8, 24, 12, 0)
		recording = make_recording(start, active_days=[0, 1, 2, 3, 4])
		instance = make_recorder([recording])

		fired = instance._scheduler_tick(now=now)

		self.assertEqual([], fired)
		self.assertEqual(datetime.datetime(2026, 8, 25, 10, 0), recording.start_time)
		self.assertEqual([recording], instance._scheduled)
		instance._persist_schedules.assert_called_once_with(extra_active=[])
		instance._start_scheduled_worker.assert_not_called()

	def test_fully_missed_one_shot_is_removed_instead_of_started_late(self):
		start = datetime.datetime(2026, 8, 24, 10, 0)
		now = datetime.datetime(2026, 8, 24, 12, 0)
		recording = make_recording(start, recurrence="once")
		instance = make_recorder([recording])

		fired = instance._scheduler_tick(now=now)

		self.assertEqual([], fired)
		self.assertEqual([], instance._scheduled)
		instance._persist_schedules.assert_called_once_with(extra_active=[])
		instance._start_scheduled_worker.assert_not_called()


class PowerRequestTests(unittest.TestCase):
	def test_power_request_is_cleared_after_recording(self):
		instance = recorder.Recorder.__new__(recorder.Recorder)
		instance._run_scheduled_body = mock.Mock()
		recording = object()

		with mock.patch.object(
			recorder,
			"_set_scheduled_recording_power_request",
			side_effect=[True, True],
		) as power_request:
			instance._run_scheduled(recording)

		instance._run_scheduled_body.assert_called_once_with(recording)
		self.assertEqual([mock.call(True), mock.call(False)], power_request.call_args_list)

	def test_power_request_is_cleared_if_recording_raises(self):
		instance = recorder.Recorder.__new__(recorder.Recorder)
		instance._run_scheduled_body = mock.Mock(side_effect=RuntimeError("test failure"))

		with mock.patch.object(
			recorder,
			"_set_scheduled_recording_power_request",
			side_effect=[True, True],
		) as power_request:
			with self.assertRaisesRegex(RuntimeError, "test failure"):
				instance._run_scheduled(object())

		self.assertEqual([mock.call(True), mock.call(False)], power_request.call_args_list)


if __name__ == "__main__":
	unittest.main()
