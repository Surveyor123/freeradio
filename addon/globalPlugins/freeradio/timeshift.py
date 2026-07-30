# -*- coding: utf-8 -*-
# FreeRadio - Time-shift buffer
#
# Captures the currently playing live stream into a local rolling buffer
# file so the user can rewind and re-listen to the last few minutes, like a
# cassette tape / DVR. Capture runs over an independent HTTP/ICY connection,
# completely separate from the BASS playback engine used for normal live
# listening - it never touches bass_host.py's audio pipeline.
#
# Design notes (see the design document for the full rationale):
#   - Plain HTTP(S) streams AND HLS (.m3u8) streams are both supported, and
#     both write into the exact same rolling buffer file mechanism below
#     (_write_chunk / _maybe_trim / generation counter / suspend-trim).
#     Only how bytes are *acquired* differs:
#       * Plain HTTP/ICY: raw bytes are read straight off the socket (_run).
#       * HLS: the master playlist is resolved to the best media playlist,
#         then new segments are downloaded in order over plain HTTP and
#         their raw bytes are appended to the buffer exactly like a plain
#         stream would be (_run_hls). This mirrors what recorder.py already
#         does for HLS recordings - concatenating segment bytes into a
#         single playable file - so the same BASS_StreamCreateFile() call
#         used for the plain-HTTP buffer in bass_host.py also works
#         unchanged for the HLS buffer; no separate HLS playback path is
#         needed.
#   - The buffer stores the raw encoded bytes exactly as received (MP3/AAC/
#     OGG/MPEG-TS/fMP4/etc.), matching what recorder.py already does for
#     recordings.
#   - fMP4-packaged HLS streams carry required initialization data (a moov
#     box) in a separate #EXT-X-MAP segment. Native FLAC streams (plain
#     HTTP/ICY, e.g. lossless internet radio) carry required initialization
#     data too - the "fLaC" marker plus STREAMINFO/metadata block chain -
#     but as part of the ordinary byte stream rather than a separate
#     request. Either way, that data is written once, at the very start of
#     the buffer file, and its length is recorded in _reserved_prefix_len so
#     _maybe_trim() can never trim it away - trimming into it would make the
#     whole buffer file undecodable, and a snippet built from later in the
#     buffer (see extract_recent_snippet) would be missing information no
#     individual frame carries on its own.
#     _reserved_prefix_len is 0 for plain non-FLAC HTTP and TS-packaged HLS
#     streams, so trimming behaves exactly as before for those.
#   - The buffer is trimmed to CAPACITY_SECONDS only while nothing is
#     currently reading it for time-shifted playback (see enter_playback/
#     exit_playback). This avoids rewriting a file out from under an
#     actively open BASS file stream. While a time-shift session is active,
#     the buffer may temporarily grow past the configured capacity; trimming
#     resumes as soon as the user returns to live.
#   - Trim uses an average bytes-per-second estimate for the session. This
#     is approximate for variable-bitrate streams but adequate for a rolling
#     "last N minutes" window. Trim only ever drops bytes that come after
#     _reserved_prefix_len, so a preserved fMP4 init segment (see above) is
#     never touched.
#   - Generation counter: every start() call bumps a generation number, and
#     the capture thread checks it belongs to the current generation before
#     every write and on every loop iteration. This guarantees a stale
#     thread from a previous station can never keep writing into (or being
#     read back from) the buffer, even if stop() was skipped or delayed for
#     any reason - the thread notices on its own and exits.
#   - The buffer file is kept open for the whole capture session instead of
#     being reopened for every chunk, to minimize disk I/O overhead (many
#     open/close syscalls per second can contribute to audio stutter on the
#     live stream, since capture competes for system resources).

import logging
import os
import tempfile
import threading
import time
import urllib.request

from . import recorder as _recorder_mod

log = logging.getLogger()

_CHUNK = 65536


class TimeShiftBuffer:
	"""Continuously captures the currently playing stream to a local file
	so it can be rewound and replayed. Only one capture session is active
	at a time, matching the single "now playing" station of the main
	player.
	"""

	CAPACITY_SECONDS = 600          # 10 minutes
	_TRIM_MARGIN_SECONDS = 120       # trim only once ~2 minutes over capacity
	_TRIM_CHECK_INTERVAL = 30        # seconds between trim checks

	def __init__(self, tmp_dir=None):
		self._tmp_dir = tmp_dir or tempfile.gettempdir()
		self._thread = None
		self._stop_event = threading.Event()
		self._file_path = None
		self._file_lock = threading.Lock()   # guards the persistent file handle
		self._file_handle = None             # persistent handle, opened for the whole session
		self._session_start = None
		self._bytes_written = 0
		self._active = False
		self._suspend_trim = 0        # reference count: >0 while one or more external
		                               # readers (time-shift playback, recorder tail,
		                               # recognizer snippet extraction) have the file open
		self._url = None
		self._is_hls = False         # True if the current session is capturing via HLS segments
		self._hls_skipped = False    # True only if the HLS manifest itself could not be read at all
		self._reserved_prefix_len = 0  # bytes at the head of the buffer that _maybe_trim must never drop
		self._flac_probe_done = True   # False while probing early bytes for a native-FLAC header
		self._flac_probe_buf  = b""
		self._generation = 0         # bumped on every start(); stale threads self-terminate

	# -- Public API ---------------------------------------------------------

	def start(self, url):
		"""Begin capturing *url* into a fresh buffer file. Any previous
		session is stopped and its temp file removed first.

		Both plain HTTP(S) streams and HLS (.m3u8) streams are captured
		into the same kind of rolling buffer file - see the module design
		notes above. is_hls_skipped() only reports True if the HLS
		manifest itself could not be read at all (see _run_hls).
		"""
		self.stop()

		self._generation += 1
		my_gen = self._generation

		self._stop_event = threading.Event()
		self._url = url
		self._is_hls = url.lower().split("?")[0].endswith(".m3u8")
		self._hls_skipped = False
		self._session_start = time.time()
		self._bytes_written = 0
		self._suspend_trim = 0
		self._reserved_prefix_len = 0
		self._flac_probe_done = self._is_hls   # only plain HTTP/ICY streams can be native FLAC
		self._flac_probe_buf  = b""

		try:
			fd, path = tempfile.mkstemp(prefix="freeradio_timeshift_", suffix=".buf", dir=self._tmp_dir)
			os.close(fd)
		except OSError as e:
			log.info("FreeRadio TimeShift: could not create buffer file: %s", e)
			return

		self._file_path = path
		self._active = True
		target = self._run_hls if self._is_hls else self._run
		thread_name = "FreeRadio-TimeShiftCaptureHLS" if self._is_hls else "FreeRadio-TimeShiftCapture"
		self._thread = threading.Thread(
			target=target, args=(my_gen,), name=thread_name, daemon=True,
		)
		self._thread.start()

	def stop(self):
		"""Stop capturing and remove the buffer file."""
		self._stop_event.set()
		thread = self._thread
		if thread and thread.is_alive():
			thread.join(timeout=5)
		self._thread = None
		self._active = False
		self._close_file_handle()
		path = self._file_path
		self._file_path = None
		if path:
			try:
				os.remove(path)
			except OSError:
				pass

	def is_active(self):
		return self._active

	def is_hls_skipped(self):
		"""True only if the current/last station is an HLS (.m3u8) stream
		whose manifest could not be read at all on the very first attempt
		(bad URL, DNS/network failure, etc.) - i.e. capture never managed
		to buffer a single byte. HLS streams that read fine are captured
		normally and this returns False for them, same as plain HTTP."""
		return self._hls_skipped

	def get_file_path(self):
		return self._file_path

	def get_url(self):
		return self._url

	def get_reserved_prefix_len(self):
		"""Size in bytes of the container-header prefix (fMP4 init segment)
		that must be kept at the front of any standalone copy taken from
		this buffer. 0 for plain HTTP/ICY and MPEG-TS-packaged streams."""
		return self._reserved_prefix_len

	def extract_recent_snippet(self, seconds, out_path):
		"""Write the most recently captured *seconds* of audio - plus the
		preserved container header, if this stream needs one - to
		*out_path* as a standalone file an external decoder (ffmpeg) can
		open directly from byte 0.

		This exists so callers (music recognition, in particular) can grab
		"whatever is airing right now" without opening a second connection
		to the stream: a fresh connection looks like a brand-new listener
		to some CDNs, which serve it a freshly-inserted ad instead of the
		track actually playing, even though the main playback connection
		is already well past that ad.

		Returns True on success, False if the buffer has nothing usable
		yet. Safe to call while capture is running - trimming is briefly
		suspended via enter_playback()/exit_playback() for the read.
		"""
		path = self._file_path
		if not path:
			return False

		self.enter_playback()
		try:
			try:
				size = os.path.getsize(path)
			except OSError:
				return False
			if size <= 0:
				return False

			prefix_len = min(self._reserved_prefix_len, size)

			elapsed = time.time() - (self._session_start or time.time())
			bytes_per_second = (self._bytes_written / elapsed) if elapsed > 0 and self._bytes_written > 0 else 0
			tail_bytes = int(bytes_per_second * seconds) if bytes_per_second else 0

			try:
				with open(path, "rb") as f:
					prefix = f.read(prefix_len) if prefix_len else b""
					tail_start = max(prefix_len, size - tail_bytes) if tail_bytes else prefix_len
					f.seek(tail_start)
					tail = f.read()
			except OSError as e:
				log.info("FreeRadio TimeShift: snippet read failed: %s", e)
				return False

			if not prefix and not tail:
				return False

			try:
				with open(out_path, "wb") as out_f:
					if prefix:
						out_f.write(prefix)
					out_f.write(tail)
			except OSError as e:
				log.info("FreeRadio TimeShift: snippet write failed: %s", e)
				return False

			return True
		finally:
			self.exit_playback()

	def buffered_seconds(self):
		"""Rough estimate of how much audio is currently available in the
		buffer, i.e. how far back the user can rewind."""
		if not self._session_start:
			return 0.0
		elapsed = time.time() - self._session_start
		return max(0.0, min(elapsed, self.CAPACITY_SECONDS + self._TRIM_MARGIN_SECONDS))

	def get_container_hint(self):
		"""Sniff the container type from the true start of the buffer file
		(byte 0, as originally captured when this session's connection was
		opened) - NOT from whatever bytes happen to be arriving live right
		now. Returns one of recorder.py's _detect_container_from_segment
		results ("mp3", "flac", "ogg", "ts", "mp4", "unknown")."""
		path = self._file_path
		if not path:
			return "unknown"
		try:
			with open(path, "rb") as f:
				head = f.read(64)
		except OSError:
			return "unknown"
		return _recorder_mod._detect_container_from_segment(head)

	_TAIL_SAFE_CONTAINERS = frozenset({"mp3", "ts"})

	def is_tail_safe(self):
		"""True if recorder.py/musicRecognizer.py can safely tail this
		buffer (or snippet from it) instead of opening a fresh connection.

		Two cases qualify:
		  - _reserved_prefix_len > 0: a required setup header (fMP4 init
		    segment, or a native-FLAC STREAMINFO chain) was detected and is
		    being preserved, so a snippet/tail built from later in the file
		    is still decodable.
		  - The container is one where ANY excerpt decodes independently,
		    with no setup data needed at all (MP3 frame sync repeats every
		    frame; MPEG-TS packets are self-describing).

		Everything else - most importantly Ogg (Vorbis/Opus/FLAC-in-Ogg),
		whose required identification/setup packets we don't parse - is
		NOT tail-safe: tailing it would produce a file with correct bytes
		but no audio, since those formats need their own opening packets to
		make sense of anything that comes later. Callers should fall back
		to a fresh connection for those, same as before this buffer-tailing
		feature existed.
		"""
		if self._reserved_prefix_len > 0:
			return True
		return self.get_container_hint() in self._TAIL_SAFE_CONTAINERS

	def enter_playback(self):
		"""Called when something starts reading the buffer file directly -
		a time-shift playback session, a recording tail-copy, or a
		recognition snippet extraction. Suspends trimming until a matching
		exit_playback() call so the file is not rewritten out from under
		an open reader. Reference-counted: safe to call from more than one
		reader at a time.
		"""
		self._suspend_trim += 1

	def exit_playback(self):
		"""Matches a prior enter_playback() call. Trimming resumes once
		every registered reader has called this."""
		self._suspend_trim = max(0, self._suspend_trim - 1)

	# -- Internal -------------------------------------------------------

	def _close_file_handle(self):
		with self._file_lock:
			if self._file_handle:
				try:
					self._file_handle.close()
				except Exception:
					pass
				self._file_handle = None

	def _is_stale(self, my_gen):
		"""True if a newer start() call has superseded the session this
		capture thread was launched for - it should exit immediately."""
		return my_gen != self._generation

	_FLAC_PROBE_CAP = 2 * 1024 * 1024  # generous cap in case of large embedded cover art

	def _maybe_capture_flac_header(self, chunk):
		"""Watch the first bytes of a plain HTTP/ICY session for a native
		FLAC stream marker ("fLaC"). Unlike MP3 or ADTS-AAC, a raw FLAC
		frame is not independently decodable - the decoder needs the
		STREAMINFO metadata block (sample rate, channels, bit depth) that
		only appears once, right at the start of the stream. Without it, a
		snippet built from later in the buffer (extract_recent_snippet) or
		a recording tailed from "now" onward (recorder.py's
		_TimeshiftTailWriter) would be silent/undecodable even though the
		bytes themselves are intact - the same problem fMP4's moov box
		solves via #EXT-X-MAP, just arriving inline instead of as a
		separate request.

		Accumulates chunks until the full metadata block chain is found (or
		the probe cap is hit), then records its length in
		_reserved_prefix_len so it is preserved the same way an fMP4 init
		segment is. Streams that don't start with "fLaC" are recognised as
		such immediately and never probed again this session.
		"""
		if self._flac_probe_done:
			return
		self._flac_probe_buf += chunk
		buf = self._flac_probe_buf
		if len(buf) < 4:
			return
		if buf[:4] != b"fLaC":
			self._flac_probe_done = True
			self._flac_probe_buf = b""
			return

		pos = 4
		while True:
			if len(buf) < pos + 4:
				if len(buf) > self._FLAC_PROBE_CAP:
					log.info("FreeRadio TimeShift: FLAC metadata chain exceeded "
								 "%d-byte probe cap, giving up on header preservation",
								 self._FLAC_PROBE_CAP)
					self._flac_probe_done = True
					self._flac_probe_buf = b""
				return  # wait for more bytes on the next chunk
			header    = buf[pos:pos + 4]
			is_last   = bool(header[0] & 0x80)
			block_len = (header[1] << 16) | (header[2] << 8) | header[3]
			pos += 4 + block_len
			if is_last:
				self._reserved_prefix_len = pos
				self._flac_probe_done = True
				self._flac_probe_buf = b""
				log.info("FreeRadio TimeShift: detected native FLAC stream, "
						  "preserving %d-byte header as reserved prefix", pos)
				return

	def _run(self, my_gen):
		"""Capture loop entry point: keeps (re)connecting with exponential
		backoff so a transient network hiccup (a read timeout, a dropped
		socket) doesn't permanently kill the buffer for the rest of the
		session. Previously a single failure just ended the thread for
		good; that was tolerable when the buffer only backed the optional
		rewind feature, but recognition and recording now depend on this
		same connection staying alive for as long as the station is
		playing - a "never reconnects" buffer silently pushes those
		features back onto opening a fresh connection, which is exactly
		what re-triggers per-session ad insertion on some stations.
		"""
		fail_streak = 0
		try:
			while not self._stop_event.is_set() and not self._is_stale(my_gen):
				try:
					self._run_once(my_gen)
					fail_streak = 0   # reached at least a successful connect
				except Exception as e:
					log.info("FreeRadio TimeShift: capture loop failed: %s", e, exc_info=True)
					fail_streak += 1

				if self._stop_event.is_set() or self._is_stale(my_gen):
					return

				wait = min(2 ** fail_streak, 30)
				log.info("FreeRadio TimeShift: reconnecting capture in %ds...", wait)
				if self._stop_event.wait(wait) or self._is_stale(my_gen):
					return
		finally:
			if not self._is_stale(my_gen):
				self._close_file_handle()

	def _run_once(self, my_gen):
		"""Capture loop: connects to the stream (plain HTTP, falling back to
		a raw-socket ICY connection for Shoutcast-style servers - the same
		approach recorder.py uses), appends raw bytes to the buffer file,
		and periodically trims the front of the file to respect
		CAPACITY_SECONDS while no external reader has the file open.

		Raises on failure to connect at all, so the caller's backoff loop
		retries; returns normally once the read loop ends for any other
		reason (clean EOF, a read error, stop requested, or a newer
		station superseding this one).
		"""
		url = self._url
		if self._is_stale(my_gen):
			return

		reader = None
		is_socket = False
		try:
			req = urllib.request.Request(
				url,
				headers={"User-Agent": _recorder_mod._USER_AGENT, "Icy-MetaData": "0"},
			)
			reader = _recorder_mod._urlopen(req, 20)
		except Exception as e:
			if not _recorder_mod._is_icy_error(e):
				raise
			sock, _headers, prefix = _recorder_mod._open_icy(url, timeout=20)
			reader = sock
			is_socket = True
			if prefix and not self._is_stale(my_gen):
				self._maybe_capture_flac_header(prefix)
				self._write_chunk(prefix, my_gen)

		if self._is_stale(my_gen):
			try:
				reader.close()
			except Exception:
				pass
			return

		if is_socket:
			log.info("FreeRadio TimeShift: capture connected via raw ICY socket for %s", url)
		else:
			log.info("FreeRadio TimeShift: capture connected via HTTP for %s", url)

		last_trim_check = time.time()
		chunk_count = 0
		try:
			while not self._stop_event.is_set() and not self._is_stale(my_gen):
				try:
					chunk = reader.recv(_CHUNK) if is_socket else reader.read(_CHUNK)
				except Exception as e:
					log.info("FreeRadio TimeShift: capture read failed after %d chunk(s): %s",
								 chunk_count, e)
					break
				if not chunk:
					log.info("FreeRadio TimeShift: capture stream ended (server closed connection) "
							  "after %d chunk(s)", chunk_count)
					break
				chunk_count += 1
				self._maybe_capture_flac_header(chunk)
				self._write_chunk(chunk, my_gen)

				now = time.time()
				if now - last_trim_check >= self._TRIM_CHECK_INTERVAL:
					last_trim_check = now
					if not self._suspend_trim:
						self._maybe_trim(my_gen)

			log.info("FreeRadio TimeShift: capture loop exiting, wrote %d chunk(s), "
					  "%d byte(s) total", chunk_count, self._bytes_written)
		finally:
			try:
				reader.close()
			except Exception:
				pass

	def _run_hls(self, my_gen):
		"""Capture loop for HLS (.m3u8) stations.

		Resolves the master playlist down to the highest-bandwidth media
		playlist (same approach as recorder.py's HLS recording path),
		then polls it for new segments and downloads them in order,
		appending each segment's raw bytes to the buffer file via
		_write_chunk() - the exact same mechanism the plain-HTTP path
		uses. From bass_host.py's point of view the resulting buffer file
		is indistinguishable from a plain-HTTP capture.

		fMP4-packaged streams additionally carry a one-time #EXT-X-MAP
		initialization segment; it is written once, right at the start of
		the buffer, and its length is recorded in _reserved_prefix_len so
		_maybe_trim() never trims it away.

		*my_gen* is checked throughout exactly as in _run() - a newer
		station superseding this one makes the loop exit immediately.
		"""
		import re as _re
		from urllib.parse import urljoin

		def _abs(u, base_url):
			return urljoin(base_url, u)

		manifest_url = self._url
		seen_segments = set()
		manifest_attempts = 0
		first_segment_written = False
		last_map_url = None
		last_trim_check = time.time()
		chunk_count = 0

		log.info("FreeRadio TimeShift: HLS capture started for %s", manifest_url)

		try:
			while not self._stop_event.is_set() and not self._is_stale(my_gen):
				try:
					base_url = manifest_url.rsplit("/", 1)[0] + "/"
					req = urllib.request.Request(
						manifest_url, headers={"User-Agent": _recorder_mod._USER_AGENT},
					)
					with _recorder_mod._urlopen(req, 10) as resp:
						text = resp.read(32768).decode("utf-8", errors="ignore")
					lines = text.splitlines()
					manifest_attempts = 0
				except Exception as e:
					manifest_attempts += 1
					log.info("FreeRadio TimeShift: HLS manifest fetch failed (attempt=%d): %s",
								 manifest_attempts, e)
					if not first_segment_written:
						# Never managed to read the manifest at all - treat
						# this station as genuinely unsupported rather than
						# retrying forever with nothing ever buffered.
						self._hls_skipped = True
						return
					if self._is_stale(my_gen) or self._stop_event.wait(4):
						return
					continue

				if self._is_stale(my_gen):
					return

				# Master playlist? Switch to the highest-bandwidth sub-manifest.
				best_manifest, best_bw = None, -1
				for i, line in enumerate(lines):
					if line.startswith("#EXT-X-STREAM-INF"):
						m = _re.search(r"BANDWIDTH=(\d+)", line, _re.IGNORECASE)
						bw = int(m.group(1)) if m else 0
						if i + 1 < len(lines):
							nxt = lines[i + 1].strip()
							if nxt and bw > best_bw:
								best_bw, best_manifest = bw, _abs(nxt, base_url)
				if best_manifest and best_manifest != manifest_url:
					log.info("FreeRadio TimeShift: HLS -> best sub-manifest (bw=%d): %s",
							  best_bw, best_manifest)
					manifest_url = best_manifest
					continue

				# #EXT-X-MAP initialization segment (required for fMP4 streams).
				current_map_url = None
				for line in lines:
					line_s = line.strip()
					if line_s.startswith("#EXT-X-MAP:"):
						m = _re.search(r'URI="([^"]+)"', line_s)
						if m:
							current_map_url = _abs(m.group(1), base_url)
						break

				new_segments = []
				for line in lines:
					line = line.strip()
					if line and not line.startswith("#"):
						seg_url = _abs(line, base_url)
						if seg_url not in seen_segments:
							new_segments.append(seg_url)

				for seg_url in new_segments:
					if self._stop_event.is_set() or self._is_stale(my_gen):
						return
					seen_segments.add(seg_url)

					if current_map_url and current_map_url != last_map_url:
						try:
							map_req = urllib.request.Request(
								current_map_url, headers={"User-Agent": _recorder_mod._USER_AGENT},
							)
							with _recorder_mod._urlopen(map_req, 15) as map_resp:
								init_data = map_resp.read()
							self._write_chunk(init_data, my_gen)
							with self._file_lock:
								self._reserved_prefix_len += len(init_data)
							last_map_url = current_map_url
							log.info("FreeRadio TimeShift: wrote fMP4 init segment (%d bytes)",
									  len(init_data))
						except Exception as e:
							log.info("FreeRadio TimeShift: failed to fetch init segment: %s", e)

					try:
						seg_req = urllib.request.Request(
							seg_url, headers={"User-Agent": _recorder_mod._USER_AGENT},
						)
						with _recorder_mod._urlopen(seg_req, 15) as seg_resp:
							data = seg_resp.read()
					except Exception as e:
						log.info("FreeRadio TimeShift: segment download failed: %s", e)
						continue

					if self._is_stale(my_gen):
						return
					self._write_chunk(data, my_gen)
					first_segment_written = True
					chunk_count += 1

					now = time.time()
					if now - last_trim_check >= self._TRIM_CHECK_INTERVAL:
						last_trim_check = now
						if not self._suspend_trim:
							self._maybe_trim(my_gen)

				if len(seen_segments) > 500:
					# Bound memory on long-running sessions; the live edge
					# has long since moved past these, so they're safe to drop.
					seen_segments = set(list(seen_segments)[-200:])

				if self._stop_event.wait(4):
					return

			log.info("FreeRadio TimeShift: HLS capture loop exiting, wrote %d segment(s), "
					  "%d byte(s) total", chunk_count, self._bytes_written)
		except Exception as e:
			log.info("FreeRadio TimeShift: HLS capture loop failed: %s", e, exc_info=True)
		finally:
			if not self._is_stale(my_gen):
				self._close_file_handle()

	def _write_chunk(self, data, my_gen):
		if not data or self._is_stale(my_gen):
			return
		path = self._file_path
		if not path:
			return
		with self._file_lock:
			if self._is_stale(my_gen):
				return
			try:
				if self._file_handle is None:
					self._file_handle = open(path, "ab", buffering=0)
				self._file_handle.write(data)
				self._bytes_written += len(data)
			except OSError as e:
				log.info("FreeRadio TimeShift: write failed: %s", e)

	def _maybe_trim(self, my_gen):
		"""Drop the oldest portion of the buffer file once it exceeds
		CAPACITY_SECONDS + margin, estimated from the average byte rate
		observed so far in this session."""
		if self._is_stale(my_gen):
			return
		if not self._session_start:
			return
		elapsed = time.time() - self._session_start
		if elapsed <= self.CAPACITY_SECONDS + self._TRIM_MARGIN_SECONDS:
			return
		if self._bytes_written <= 0 or elapsed <= 0:
			return

		bytes_per_second = self._bytes_written / elapsed
		keep_bytes = int(bytes_per_second * self.CAPACITY_SECONDS)

		path = self._file_path
		if not path:
			return

		with self._file_lock:
			if self._is_stale(my_gen):
				return
			try:
				# Close the persistent handle before rewriting the file, and
				# reopen it afterwards - trimming is infrequent (every ~2
				# min over capacity) so this brief close/reopen is cheap
				# compared to reopening on every chunk.
				if self._file_handle:
					try:
						self._file_handle.close()
					except Exception:
						pass
					self._file_handle = None

				size = os.path.getsize(path)
				prefix_len = min(self._reserved_prefix_len, size)
				trimmable = size - prefix_len
				if trimmable <= keep_bytes:
					self._file_handle = open(path, "ab", buffering=0)
					return
				drop_bytes = trimmable - keep_bytes
				with open(path, "rb") as f:
					prefix = f.read(prefix_len) if prefix_len else b""
					f.seek(prefix_len + drop_bytes)
					remainder = f.read()
				with open(path, "wb") as f:
					if prefix:
						f.write(prefix)
					f.write(remainder)
				# Nudge the session start forward so buffered_seconds() stays
				# roughly accurate after trimming. Only the trimmed (non-
				# reserved) portion represents elapsed playback time.
				self._session_start += drop_bytes / bytes_per_second
				self._bytes_written = len(prefix) + len(remainder)
				self._file_handle = open(path, "ab", buffering=0)
			except OSError as e:
				log.info("FreeRadio TimeShift: trim failed: %s", e)
				try:
					self._file_handle = open(path, "ab", buffering=0)
				except OSError:
					self._file_handle = None
