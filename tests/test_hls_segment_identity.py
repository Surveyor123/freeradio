import importlib.util
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "addon" / "globalPlugins" / "freeradio"
PACKAGE_NAME = "freeradio_under_test"
package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PACKAGE_DIR)]
sys.modules[PACKAGE_NAME] = package

RECORDER_SPEC = importlib.util.spec_from_file_location(
	PACKAGE_NAME + ".recorder", PACKAGE_DIR / "recorder.py",
)
recorder = importlib.util.module_from_spec(RECORDER_SPEC)
sys.modules[RECORDER_SPEC.name] = recorder
RECORDER_SPEC.loader.exec_module(recorder)

TIMESHIFT_SPEC = importlib.util.spec_from_file_location(
	PACKAGE_NAME + ".timeshift", PACKAGE_DIR / "timeshift.py",
)
timeshift = importlib.util.module_from_spec(TIMESHIFT_SPEC)
sys.modules[TIMESHIFT_SPEC.name] = timeshift
TIMESHIFT_SPEC.loader.exec_module(timeshift)


def playlist(first_sequence, session_id, count=6):
	lines = [
		"#EXTM3U",
		"#EXT-X-TARGETDURATION:7",
		"#EXT-X-MEDIA-SEQUENCE:%d" % first_sequence,
	]
	for sequence in range(first_sequence, first_sequence + count):
		lines.extend([
			"#EXTINF:6.0,",
			"audio_%d.ts?nimblesessionid=%s" % (sequence, session_id),
		])
	return lines


class HlsSegmentIdentityTests(unittest.TestCase):
	def test_refreshed_session_token_does_not_duplicate_same_segments(self):
		base_url = "https://stream.example/live/"
		tracker = recorder._HlsSegmentTracker()

		_sequence, first = recorder._parse_hls_media_segments(
			playlist(2327, "31155323"), base_url,
		)
		tracker.prepare_playlist(first)
		for identity, _url, _duration in first:
			tracker.mark_written(identity)

		_sequence, refreshed = recorder._parse_hls_media_segments(
			playlist(2327, "31155330"), base_url,
		)
		tracker.prepare_playlist(refreshed)
		unseen = [entry for entry in refreshed if not tracker.contains(entry[0])]

		self.assertEqual([], unseen)
		self.assertNotEqual(first[0][1], refreshed[0][1])
		self.assertEqual(first[0][0], refreshed[0][0])

	def test_sliding_window_keeps_only_the_genuinely_new_sequence(self):
		base_url = "https://stream.example/live/"
		tracker = recorder._HlsSegmentTracker()
		_sequence, first = recorder._parse_hls_media_segments(
			playlist(2327, "old-token"), base_url,
		)
		tracker.prepare_playlist(first)
		for identity, _url, _duration in first:
			tracker.mark_written(identity)

		_sequence, next_window = recorder._parse_hls_media_segments(
			playlist(2328, "new-token"), base_url,
		)
		tracker.prepare_playlist(next_window)
		unseen = [entry for entry in next_window if not tracker.contains(entry[0])]

		self.assertEqual([("sequence", 2333)], [entry[0] for entry in unseen])

	def test_failed_segment_can_be_retried_until_marked_written(self):
		tracker = recorder._HlsSegmentTracker()
		_sequence, entries = recorder._parse_hls_media_segments(
			playlist(10, "first", count=1), "https://stream.example/live/",
		)
		identity = entries[0][0]
		self.assertFalse(tracker.contains(identity))
		self.assertFalse(tracker.contains(identity))
		tracker.mark_written(identity)
		self.assertTrue(tracker.contains(identity))

	def test_large_sequence_rollback_starts_a_new_epoch(self):
		tracker = recorder._HlsSegmentTracker()
		_sequence, old_entries = recorder._parse_hls_media_segments(
			playlist(5000, "before-restart"), "https://stream.example/live/",
		)
		tracker.prepare_playlist(old_entries)
		for identity, _url, _duration in old_entries:
			tracker.mark_written(identity)

		_sequence, restarted = recorder._parse_hls_media_segments(
			playlist(1, "after-restart"), "https://stream.example/live/",
		)
		self.assertTrue(tracker.prepare_playlist(restarted))
		self.assertFalse(tracker.contains(restarted[0][0]))

	def test_delta_playlist_skip_offsets_first_segment_number(self):
		lines = [
			"#EXTM3U",
			"#EXT-X-MEDIA-SEQUENCE:100",
			"#EXT-X-SKIP:SKIPPED-SEGMENTS=3",
			"#EXTINF:6.0,",
			"audio.ts?token=changed",
		]
		sequence, entries = recorder._parse_hls_media_segments(
			lines, "https://stream.example/live/",
		)
		self.assertEqual(100, sequence)
		self.assertEqual(("sequence", 103), entries[0][0])

	def test_init_segment_signature_ignores_url_token_changes(self):
		first = recorder._hls_content_signature(b"same init bytes")
		second = recorder._hls_content_signature(b"same init bytes")
		changed = recorder._hls_content_signature(b"new init bytes")
		self.assertEqual(first, second)
		self.assertNotEqual(first, changed)

	def test_stream_writer_does_not_download_refreshed_urls_twice(self):
		manifest_url = "https://stream.example/live/chunks.m3u8"
		media = {
			"https://stream.example/live/audio_100.ts?nimblesessionid=first": b"\x47" + b"A" * 187,
			"https://stream.example/live/audio_101.ts?nimblesessionid=first": b"\x47" + b"B" * 187,
			"https://stream.example/live/audio_100.ts?nimblesessionid=second": b"\x47" + b"A" * 187,
			"https://stream.example/live/audio_101.ts?nimblesessionid=second": b"\x47" + b"B" * 187,
		}
		first_manifest = "\n".join(playlist(100, "first", count=2)).encode("utf-8")
		second_manifest = "\n".join(playlist(100, "second", count=2)).encode("utf-8")

		class Response:
			def __init__(self, data):
				self.data = data

			def __enter__(self):
				return self

			def __exit__(self, exc_type, exc_value, traceback):
				return False

			def read(self, _size=-1):
				return self.data

		with tempfile.TemporaryDirectory() as temp_dir:
			initial_path = str(pathlib.Path(temp_dir) / "capture.mp3")
			writer = recorder._StreamWriter("https://stream.example/live/direct.bin", initial_path)
			writer._is_hls = True
			writer._effective_url = manifest_url
			manifest_calls = []
			segment_fetches = []

			def fake_urlopen(request, _timeout):
				url = request.full_url
				if url == manifest_url:
					manifest_calls.append(url)
					if len(manifest_calls) == 1:
						return Response(first_manifest)
					if len(manifest_calls) == 2:
						return Response(second_manifest)
					writer._stop.set()
					return Response(second_manifest)
				segment_fetches.append(url)
				return Response(media[url])

			with mock.patch.object(recorder, "_urlopen", side_effect=fake_urlopen), mock.patch(
				"time.sleep", return_value=None,
			):
				writer._run_hls()

			self.assertEqual(3, len(manifest_calls))
			self.assertEqual(
				[
					"https://stream.example/live/audio_100.ts?nimblesessionid=first",
					"https://stream.example/live/audio_101.ts?nimblesessionid=first",
				],
				segment_fetches,
			)
			self.assertEqual(
				b"\x47" + b"A" * 187 + b"\x47" + b"B" * 187,
				pathlib.Path(writer.output_path).read_bytes(),
			)

	def test_timeshift_does_not_download_refreshed_urls_twice(self):
		manifest_url = "https://stream.example/live/chunks.m3u8"
		first_manifest = "\n".join(playlist(100, "first", count=2)).encode("utf-8")
		second_manifest = "\n".join(playlist(100, "second", count=2)).encode("utf-8")
		media = {
			"https://stream.example/live/audio_100.ts?nimblesessionid=first": b"\x47" + b"A" * 187,
			"https://stream.example/live/audio_101.ts?nimblesessionid=first": b"\x47" + b"B" * 187,
			"https://stream.example/live/audio_100.ts?nimblesessionid=second": b"\x47" + b"A" * 187,
			"https://stream.example/live/audio_101.ts?nimblesessionid=second": b"\x47" + b"B" * 187,
		}

		class FastEvent:
			def __init__(self):
				self.value = False

			def is_set(self):
				return self.value

			def set(self):
				self.value = True

			def wait(self, _timeout=None):
				return self.value

		class Response:
			def __init__(self, data):
				self.data = data

			def __enter__(self):
				return self

			def __exit__(self, exc_type, exc_value, traceback):
				return False

			def read(self, _size=-1):
				return self.data

		with tempfile.TemporaryDirectory() as temp_dir:
			buffer = timeshift.TimeShiftBuffer(tmp_dir=temp_dir)
			buffer._generation = 1
			buffer._url = manifest_url
			buffer._is_hls = True
			buffer._file_path = str(pathlib.Path(temp_dir) / "timeshift.ts")
			buffer._active = True
			buffer._stop_event = FastEvent()
			manifest_calls = []
			segment_fetches = []

			def fake_urlopen(request, _timeout):
				url = request.full_url
				if url == manifest_url:
					manifest_calls.append(url)
					if len(manifest_calls) == 1:
						return Response(first_manifest)
					if len(manifest_calls) == 2:
						return Response(second_manifest)
					buffer._stop_event.set()
					return Response(second_manifest)
				segment_fetches.append(url)
				return Response(media[url])

			with mock.patch.object(recorder, "_urlopen", side_effect=fake_urlopen):
				buffer._run_hls(1)

			self.assertEqual(3, len(manifest_calls))
			self.assertEqual(
				[
					"https://stream.example/live/audio_100.ts?nimblesessionid=first",
					"https://stream.example/live/audio_101.ts?nimblesessionid=first",
				],
				segment_fetches,
			)
			self.assertEqual(
				b"\x47" + b"A" * 187 + b"\x47" + b"B" * 187,
				pathlib.Path(buffer._file_path).read_bytes(),
			)


if __name__ == "__main__":
	unittest.main()
