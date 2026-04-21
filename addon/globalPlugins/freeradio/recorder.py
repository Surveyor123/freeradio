# -*- coding: utf-8 -*-
# FreeRadio - Recorder
#
# Recording strategy:
#   - For non-HLS streams: Python reads the stream directly over HTTP and writes it to disk.
#   - For HLS streams: resolves the master playlist, downloads segments sequentially.
#   - Output format: .m4a for AAC/MP4 streams, .ts for MPEG-TS streams, .aac for raw AAC.

import datetime
import logging
import os
import threading
import urllib.request

log = logging.getLogger(__name__)

_USER_AGENT = "FreeRadio-NVDA/1.0"
_CHUNK      = 65536   # 64 KB read chunk


def _recordings_dir():
	try:
		import config as _cfg
		custom = _cfg.conf["freeradio"].get("recordings_dir", "").strip()
		if custom and os.path.isabs(custom):
			os.makedirs(custom, exist_ok=True)
			return custom
	except Exception:
		pass
	docs = os.path.join(os.path.expanduser("~"), "Documents")
	path = os.path.join(docs, "FreeRadio Recordings")
	os.makedirs(path, exist_ok=True)
	return path


def _safe_filename(name):
	for ch in r'\/:*?"<>|':
		name = name.replace(ch, "_")
	return name.strip()


def _make_output_path(station_name, ext="mp3"):
	ts    = datetime.datetime.now().strftime("%Y-%m-%d %H-%M")
	name  = _safe_filename(station_name)
	fname = f"{name} - {ts}.{ext}"
	return os.path.join(_recordings_dir(), fname)


def _guess_ext(url, content_type=""):
	"""Guess file extension from URL or Content-Type."""
	ct = (content_type or "").lower()
	if "ogg" in ct:      return "ogg"
	if "mp4" in ct or "m4a" in ct: return "m4a"
	if "aac" in ct:      return "aac"
	if "mpeg" in ct or "mp3" in ct: return "mp3"
	url_lower = url.lower().split("?")[0]
	for ext in ("mp3", "aac", "ogg", "flac", "opus", "m4a", "mp4"):
		if url_lower.endswith("." + ext):
			return ext
	return "mp3"


def _detect_container_from_segment(segment_data):
	"""Detect container type from first few bytes of a segment."""
	if len(segment_data) < 8:
		return "unknown"
	# MPEG-TS starts with 0x47 (G) sync byte
	if segment_data[0] == 0x47:
		return "ts"
	# MP4/ISO base media: scan first 64 bytes for 'ftyp' box signature.
	# Some encoders prepend a styp or moof box before ftyp, so check beyond byte 4.
	for offset in range(0, min(64, len(segment_data) - 4)):
		if segment_data[offset:offset + 4] == b'ftyp':
			return "mp4"
		if segment_data[offset:offset + 4] == b'styp':
			return "mp4"
		if segment_data[offset:offset + 4] == b'moof':
			return "mp4"
	return "unknown"


def _resolve_hls(url):
	"""Parse HLS master manifest and return the best quality (highest bandwidth) stream URL.
	If a direct media URL is found, return it; otherwise return the original.
	"""
	from urllib.parse import urljoin
	import re
	try:
		req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
		with urllib.request.urlopen(req, timeout=10) as resp:
			text = resp.read(8192).decode("utf-8", errors="ignore")
		lines = text.splitlines()
		best_url = None
		best_bw  = -1
		for i, line in enumerate(lines):
			if line.startswith("#EXT-X-STREAM-INF"):
				m = re.search(r"BANDWIDTH=(\d+)", line, re.IGNORECASE)
				bw = int(m.group(1)) if m else 0
				if i + 1 < len(lines) and lines[i + 1].strip():
					child = urljoin(url, lines[i + 1].strip())
					if bw > best_bw:
						best_bw  = bw
						best_url = child
		if best_url:
			log.debug("FreeRadio Recorder: HLS best sub-stream (bw=%d) → %s", best_bw, best_url)
			if best_url.lower().split("?")[0].endswith(".m3u8"):
				return _resolve_hls(best_url)
			return best_url
	except Exception as e:
		log.warning("FreeRadio Recorder: HLS resolve failed: %s", e)
	return url


class _StreamWriter:
	"""Background thread that reads a URL and writes it to a file.
	Handles both direct streams and HLS playlists.
	"""

	def __init__(self, url, output_path):
		self.original_url = url
		self.output_path = output_path
		self._stop       = threading.Event()
		self._thread     = None
		self._error      = None
		self._container_detected = False
		self._container_type = "unknown"
		
		# Resolve HLS to final URL if possible
		resolved = url
		if url.lower().split("?")[0].endswith(".m3u8"):
			resolved = _resolve_hls(url)
		self._is_hls = resolved.lower().split("?")[0].endswith(".m3u8")
		self._effective_url = resolved if not self._is_hls else url
		log.debug("FreeRadio Recorder: effective URL for %s: %s, is_hls=%s",
		          url, self._effective_url, self._is_hls)

	def start(self):
		self._thread = threading.Thread(
			target=self._run_hls if self._is_hls else self._run,
			daemon=True,
		)
		self._thread.start()

	def stop(self):
		self._stop.set()
		if self._thread:
			self._thread.join(timeout=5)

	def _detect_and_fix_extension(self, first_chunk):
		"""Detect container from first chunk and adjust output extension."""
		container = _detect_container_from_segment(first_chunk)
		self._container_type = container
		base, current_ext = os.path.splitext(self.output_path)
		
		if container == "mp4" and current_ext not in (".mp4", ".m4a"):
			self.output_path = base + ".m4a"
			log.info("FreeRadio Recorder: detected MP4 container, saving as %s", self.output_path)
		elif container == "ts" and current_ext != ".ts":
			self.output_path = base + ".ts"
			log.info("FreeRadio Recorder: detected MPEG-TS container, saving as %s", self.output_path)
		elif container == "unknown" and self._is_hls:
			# For HLS, default to .m4a — most modern AAC/HLS streams use MP4 container.
			# .ts is legacy; defaulting to it causes "no audio" on AAC-in-MP4 segments.
			if current_ext not in (".m4a", ".mp4"):
				self.output_path = base + ".m4a"
				log.info("FreeRadio Recorder: unknown HLS container, defaulting to .m4a")

	def _run(self):
		import time
		first       = True
		fail_streak = 0

		while not self._stop.is_set():
			connected = False
			try:
				req = urllib.request.Request(
					self._effective_url,
					headers={"User-Agent": _USER_AGENT, "Icy-MetaData": "0"},
				)
				with urllib.request.urlopen(req, timeout=20) as resp:
					if first:
						ct  = resp.headers.get("Content-Type", "")
						ext = _guess_ext(self._effective_url, ct)
						base, _ = os.path.splitext(self.output_path)
						self.output_path = base + "." + ext
						log.info("FreeRadio Recorder: writing to %s (ct=%s)", self.output_path, ct)
						first = False

					connected   = True
					fail_streak = 0
					with open(self.output_path, "ab") as f:
						while not self._stop.is_set():
							chunk = resp.read(_CHUNK)
							if not chunk:
								break
							f.write(chunk)

			except Exception as e:
				if self._stop.is_set():
					return
				self._error = e
				if not connected:
					fail_streak += 1
				log.warning(
					"FreeRadio Recorder: connection error (streak=%d): %s",
					fail_streak, e,
				)

			if self._stop.is_set():
				return

			wait = min(2 ** fail_streak, 30)
			log.warning("FreeRadio Recorder: reconnecting in %ds...", wait)
			for _ in range(wait * 10):
				if self._stop.is_set():
					return
				time.sleep(0.1)

	def _run_hls(self):
		"""Download HLS segments sequentially and write to a single file."""
		import time
		from urllib.parse import urlparse

		log.info("FreeRadio Recorder: HLS recording started for %s", self._effective_url)

		def _abs(url, base_url):
			from urllib.parse import urljoin
			return urljoin(base_url, url)

		seen_segments = set()
		manifest_url  = self._effective_url
		manifest_errors = 0
		target_dur    = 5
		first_segment_written = False
		output_file = None
		last_map_url = None   # tracks #EXT-X-MAP initialization segment

		while not self._stop.is_set():
			try:
				base_url = manifest_url.rsplit("/", 1)[0] + "/"
				req = urllib.request.Request(manifest_url, headers={"User-Agent": _USER_AGENT})
				with urllib.request.urlopen(req, timeout=10) as resp:
					text = resp.read(32768).decode("utf-8", errors="ignore")
				lines = text.splitlines()
				manifest_errors = 0

				for line in lines:
					if line.startswith("#EXT-X-TARGETDURATION:"):
						try:
							target_dur = int(line.split(":")[1].strip())
						except Exception:
							pass

				# Check if it's a master playlist (contains #EXT-X-STREAM-INF)
				# Pick the sub-manifest with the highest BANDWIDTH value.
				switched = False
				best_manifest = None
				best_bw = -1
				import re as _re
				for i, line in enumerate(lines):
					if line.startswith("#EXT-X-STREAM-INF"):
						m = _re.search(r"BANDWIDTH=(\d+)", line, _re.IGNORECASE)
						bw = int(m.group(1)) if m else 0
						if i + 1 < len(lines):
							nl = lines[i + 1].strip()
							if nl and bw > best_bw:
								best_bw = bw
								best_manifest = _abs(nl, base_url)
				if best_manifest and best_manifest != manifest_url:
					log.info("FreeRadio Recorder: HLS → best sub-manifest (bw=%d): %s", best_bw, best_manifest)
					manifest_url = best_manifest
					switched = True
				if switched:
					continue

				# Parse #EXT-X-MAP initialization segment (fMP4 streams require this)
				current_map_url = None
				for line in lines:
					line_s = line.strip()
					if line_s.startswith("#EXT-X-MAP:"):
						# URI="..." — extract the URI value
						import re
						m = re.search(r'URI="([^"]+)"', line_s)
						if m:
							current_map_url = _abs(m.group(1), base_url)
						break

				# Otherwise it's a media playlist: collect new segment URLs
				segments = []
				for line in lines:
					line = line.strip()
					if line and not line.startswith("#"):
						seg_url = _abs(line, base_url)
						if seg_url not in seen_segments:
							segments.append(seg_url)

				log.debug("FreeRadio Recorder: HLS %d new segments (target_dur=%ds)",
				          len(segments), target_dur)

				seg_errors = 0
				for seg_url in segments:
					if self._stop.is_set():
						if output_file:
							output_file.close()
						return
					
					for seg_attempt in range(5):
						if self._stop.is_set():
							if output_file:
								output_file.close()
							return
						try:
							seg_req = urllib.request.Request(seg_url, headers={"User-Agent": _USER_AGENT})
							with urllib.request.urlopen(seg_req, timeout=15) as seg_resp:
								data = seg_resp.read()
							
							# First segment: detect container, write init segment if needed, open file
							if not first_segment_written:
								self._detect_and_fix_extension(data)
								output_file = open(self.output_path, "ab")
								first_segment_written = True
								log.info("FreeRadio Recorder: first segment written to %s", self.output_path)

								# fMP4 streams carry moov/init in a separate #EXT-X-MAP segment.
								# Without it, players see no audio/video tracks.
								if current_map_url and current_map_url != seg_url:
									try:
										map_req = urllib.request.Request(
											current_map_url, headers={"User-Agent": _USER_AGENT}
										)
										with urllib.request.urlopen(map_req, timeout=15) as map_resp:
											init_data = map_resp.read()
										output_file.write(init_data)
										output_file.flush()
										last_map_url = current_map_url
										log.info("FreeRadio Recorder: wrote fMP4 init segment from %s", current_map_url)
									except Exception as e:
										log.warning("FreeRadio Recorder: failed to fetch init segment: %s", e)
							else:
								# If the init segment changed mid-stream, write the new one
								if current_map_url and current_map_url != last_map_url:
									try:
										map_req = urllib.request.Request(
											current_map_url, headers={"User-Agent": _USER_AGENT}
										)
										with urllib.request.urlopen(map_req, timeout=15) as map_resp:
											init_data = map_resp.read()
										output_file.write(init_data)
										output_file.flush()
										last_map_url = current_map_url
										log.info("FreeRadio Recorder: wrote new fMP4 init segment from %s", current_map_url)
									except Exception as e:
										log.warning("FreeRadio Recorder: failed to fetch new init segment: %s", e)

							if output_file:
								output_file.write(data)
								output_file.flush()
							
							seen_segments.add(seg_url)
							seg_errors = 0
							break
						except Exception as e:
							log.warning(
								"FreeRadio Recorder: HLS segment error (attempt %d/5): %s",
								seg_attempt + 1, e,
							)
							seg_errors += 1
							if seg_attempt < 4:
								for _ in range(20):   # wait for 2 s
									if self._stop.is_set():
										if output_file:
											output_file.close()
										return
									time.sleep(0.1)

				# Wait for the duration of the next segment (target duration)
				for _ in range(max(target_dur, 2) * 10):
					if self._stop.is_set():
						if output_file:
							output_file.close()
						return
					time.sleep(0.1)

			except Exception as e:
				if self._stop.is_set():
					if output_file:
						output_file.close()
					return
				manifest_errors += 1
				wait = min(2 ** manifest_errors, 30)
				log.warning(
					"FreeRadio Recorder: HLS manifest error (streak=%d), retry in %ds: %s",
					manifest_errors, wait, e,
				)
				for _ in range(wait * 10):
					if self._stop.is_set():
						if output_file:
							output_file.close()
						return
					time.sleep(0.1)
		
		if output_file:
			output_file.close()


def _resolve_url(url):
	"""Resolve playlist/HLS URLs to the best direct stream URL."""
	low = url.lower().split("?")[0]
	if low.endswith(".m3u8"):
		return _resolve_hls(url)
	if low.endswith(".m3u") or low.endswith(".pls"):
		return _resolve_playlist(url)
	return url


def _resolve_playlist(url):
	"""Resolve .m3u or .pls playlist to first stream URL."""
	try:
		req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
		with urllib.request.urlopen(req, timeout=10) as resp:
			text = resp.read(4096).decode("utf-8", errors="ignore")
		for line in text.splitlines():
			line = line.strip()
			if line.startswith("http") and not line.startswith("#"):
				return line
			if line.startswith("File1="):
				return line[6:].strip()
	except Exception as e:
		log.warning("FreeRadio Recorder: playlist resolve failed: %s", e)
	return url


class ScheduledRecording:
	def __init__(self, station, start_time, duration_minutes,
	             player_paths=None, record_only=False):
		self.station          = station
		self.start_time       = start_time
		self.duration_minutes = duration_minutes
		self.player_paths     = player_paths or {}   # {vlc, potplayer, wmp}
		self.record_only      = record_only
		self.fired            = False
		self.output_path      = None

	def __str__(self):
		ts   = self.start_time.strftime("%d.%m.%Y %H:%M")
		mode = _("Record only") if self.record_only else _("Listen and record")
		return f"{self.station.get('name','?')} — {ts} ({self.duration_minutes} min, {mode})"


def _schedules_path():
	"""The path to the JSON file."""
	appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
	return os.path.join(appdata, "nvda", "freeradio_schedules.json")


def _save_schedules(schedules):
	import json
	data = []
	for rec in schedules:
		if rec.fired:
			continue
		try:
			data.append({
				"station":          rec.station,
				"start_time":       rec.start_time.isoformat(),
				"duration_minutes": rec.duration_minutes,
				"player_paths":     rec.player_paths,
				"record_only":      rec.record_only,
			})
		except Exception as e:
			log.warning("FreeRadio Recorder: could not serialize schedule: %s", e)
	try:
		path = _schedules_path()
		os.makedirs(os.path.dirname(path), exist_ok=True)
		with open(path, "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
	except Exception as e:
		log.warning("FreeRadio Recorder: could not save schedules: %s", e)


def _load_schedules():
	import json
	try:
		path = _schedules_path()
		if not os.path.isfile(path):
			return []
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
		now = datetime.datetime.now()
		result = []
		for item in data:
			try:
				start = datetime.datetime.fromisoformat(item["start_time"])
				if start <= now:
					continue
				rec = ScheduledRecording(
					station          = item["station"],
					start_time       = start,
					duration_minutes = item["duration_minutes"],
					player_paths     = item.get("player_paths", {}),
					record_only      = item.get("record_only", False),
				)
				result.append(rec)
			except Exception as e:
				log.warning("FreeRadio Recorder: skipping bad schedule entry: %s", e)
		return result
	except Exception as e:
		log.warning("FreeRadio Recorder: could not load schedules: %s", e)
		return []


class Recorder:
	"""Manages instant and scheduled recordings."""

	def __init__(self, dll_dir=None, player_paths=None, volume=100, main_player=None):
		"""
		dll_dir: Path to the directory containing bass_host.py and bass/ subfolder.
		player_paths: dict with optional keys 'vlc', 'potplayer', 'wmp' for fallback.
		volume: Default volume (0-100) for scheduled playback.
		main_player: Reference to the main RadioPlayer instance used for user playback.
		"""
		self._writer          = None
		self._output_path     = None
		self._station_name    = ""
		self._scheduled       = _load_schedules()
		self._scheduler_thread = None
		self._stop_scheduler  = threading.Event()
		self._dll_dir         = dll_dir
		self._player_paths    = player_paths or {}
		self._volume          = volume
		self._main_player     = main_player  # to avoid interrupting user
		self._active_scheduled = set()  # currently running scheduled recordings
		self._active_scheduled_lock = threading.Lock()
		if self._scheduled:
			self._ensure_scheduler()

	def _overlaps(self, start, duration_minutes):
		"""Return plans that overlap with the given range."""
		end = start + datetime.timedelta(minutes=duration_minutes)
		result = []
		for rec in self._scheduled:
			if rec.fired:
				continue
			rec_end = rec.start_time + datetime.timedelta(minutes=rec.duration_minutes)
			if start < rec_end and end > rec.start_time:
				result.append(rec)
		return result

	def start(self, player, station_name):
		"""Start instant recording. VLC keeps playing; Python writes the stream.
		Returns output file path.
		"""
		original_url = getattr(player, "_current_url_resolved", None) or player._current_url
		if not original_url:
			raise RuntimeError("No station playing")
		log.info("FreeRadio Recorder: instant recording URL = %s", original_url)
		if self._writer:
			self._writer.stop()

		out = _make_output_path(station_name)
		self._output_path  = out
		self._station_name = station_name
		self._writer = _StreamWriter(original_url, out)
		self._writer.start()
		log.info("FreeRadio Recorder: instant recording started → %s", out)
		return out

	def stop(self, player=None):
		"""Stop instant recording. Returns saved file path."""
		path = self._output_path
		if self._writer:
			self._writer.stop()
			path = self._writer.output_path
			self._writer = None
		self._output_path  = None
		self._station_name = ""
		log.info("FreeRadio Recorder: instant recording stopped, file=%s", path)
		return path

	def is_recording(self):
		return self._writer is not None

	def get_output_path(self):
		return self._output_path

	def get_station_name(self):
		return self._station_name

	def add_schedule(self, station, start_time, duration_minutes,
	                 player_paths=None, record_only=False):
		"""Schedule a recording.

		player_paths: dict with optional keys 'vlc', 'potplayer', 'wmp'.
		              Used only when record_only=False (listen + record mode)
		              to launch a player for audio output.  Recording itself
		              never requires a player.
		Returns (ScheduledRecording, conflict_names_str_or_None).
		"""
		conflict_names = None
		conflicts = self._overlaps(start_time, duration_minutes)
		if conflicts and not record_only:
			record_only = True
			conflict_names = ", ".join(
				r.station.get("name", "?") for r in conflicts
			)
		rec = ScheduledRecording(
			station, start_time, duration_minutes,
			player_paths=player_paths or {},
			record_only=record_only,
		)
		self._scheduled.append(rec)
		self._scheduled.sort(key=lambda r: r.start_time)
		_save_schedules(self._scheduled)
		self._ensure_scheduler()
		return rec, conflict_names

	def remove_schedule(self, rec):
		if rec in self._scheduled:
			self._scheduled.remove(rec)
			_save_schedules(self._scheduled)

	def get_schedules(self):
		return list(self._scheduled)

	def get_active_scheduled(self):
		"""Return a list of ScheduledRecording objects currently being recorded."""
		with self._active_scheduled_lock:
			return list(self._active_scheduled)

	def stop_active_scheduled(self):
		"""Force-stop all currently running scheduled recordings."""
		with self._active_scheduled_lock:
			active = list(self._active_scheduled)
		for rec in active:
			rec._force_stop = True
			writer = getattr(rec, "_writer", None)
			if writer:
				try:
					writer.stop()
				except Exception:
					pass

	def _ensure_scheduler(self):
		if self._scheduler_thread and self._scheduler_thread.is_alive():
			return
		self._stop_scheduler.clear()
		self._scheduler_thread = threading.Thread(
			target=self._scheduler_loop, daemon=True,
		)
		self._scheduler_thread.start()

	def _scheduler_loop(self):
		import time
		while not self._stop_scheduler.is_set():
			now = datetime.datetime.now()
			fired = []
			for rec in list(self._scheduled):
				if not rec.fired and now >= rec.start_time:
					rec.fired = True
					fired.append(rec)
					threading.Thread(
						target=self._run_scheduled,
						args=(rec,),
						daemon=True,
					).start()
			self._scheduled = [r for r in self._scheduled if not r.fired]
			if fired:
				_save_schedules(self._scheduled)
			time.sleep(1)

	def _run_scheduled(self, rec):
		"""Run a scheduled recording: Python writes the stream, optionally plays via main player."""
		import time

		url  = rec.station.get("url_resolved") or rec.station.get("url", "")
		name = rec.station.get("name", "Unknown").strip()
		out  = _make_output_path(name)

		writer = _StreamWriter(url, out)
		writer.start()
		rec.output_path = out
		rec._writer = writer  # reference for early external stop

		# --- Playback handling: use main player if available and idle ---
		started_on_main = False
		if not rec.record_only and self._main_player:
			main_playing = self._main_player.is_playing()
			main_station = self._main_player.get_current_station()
			if not main_playing:
				# Main player is idle → use it for scheduled playback
				try:
					self._main_player.play(url, name, url_resolved=url, station=rec.station)
					started_on_main = True
					log.info("FreeRadio Recorder: scheduled playback via main player")
				except Exception as e:
					log.warning("FreeRadio Recorder: failed to start scheduled playback on main player: %s", e)
			elif main_station and main_station.get("stationuuid") == rec.station.get("stationuuid"):
				log.info("FreeRadio Recorder: main player already playing %s; will only record", name)
			else:
				log.info("FreeRadio Recorder: main player playing another station; will only record (no playback)")
		# (If main_player is None or record_only=True, no playback is done)

		with self._active_scheduled_lock:
			self._active_scheduled.add(rec)

		log.info("FreeRadio Recorder: scheduled recording started — %s → %s", name, out)
		if hasattr(self, "_notify_start") and self._notify_start:
			self._notify_start(rec)

		deadline = time.time() + rec.duration_minutes * 60
		while time.time() < deadline:
			if getattr(rec, "_force_stop", False):
				break
			time.sleep(min(1.0, deadline - time.time()))

		writer.stop()
		rec.output_path = writer.output_path   # extension may have been updated
		rec._writer = None

		with self._active_scheduled_lock:
			self._active_scheduled.discard(rec)

		# --- Clean up playback ---
		if started_on_main:
			# Only stop if the main player is still playing the same station
			if self._main_player and self._main_player.is_playing():
				current = self._main_player.get_current_station()
				if current and current.get("stationuuid") == rec.station.get("stationuuid"):
					self._main_player.stop()
					log.info("FreeRadio Recorder: stopped scheduled playback on main player")
			# else: user changed station; keep playing what they chose

		log.info("FreeRadio Recorder: scheduled recording finished — %s", rec.output_path)
		if hasattr(self, "_notify_finish") and self._notify_finish:
			self._notify_finish(rec)

	def terminate(self):
		self._stop_scheduler.set()
		if self._writer:
			self._writer.stop()
			self._writer = None
		for rec in self._scheduled:
			if hasattr(rec, "_writer") and rec._writer:
				rec._writer.stop()