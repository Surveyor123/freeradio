# -*- coding: utf-8 -*-
# FreeRadio - Time-shift buffer

import collections
import logging
import os
import tempfile
import threading
import time
import urllib.request
import ssl
import socket
import re

from . import recorder as _recorder_mod

log = logging.getLogger()

_CHUNK = 65536

# Debug logging - disabled by default
# Set to True to enable detailed debug logs
_DEBUG_ENABLED = False

# Shared debug log
_DEBUG_LOG_PATH = os.path.join(tempfile.gettempdir(), "freeradio_timeshift_debug.log")


def _debug_log(msg):
	"""Write debug message to log file only if debugging is enabled."""
	if not _DEBUG_ENABLED:
		return
	log.info(msg)
	try:
		with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
			f.write("%s [timeshift.py] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
	except Exception:
		pass


def enable_debug_logging(enabled=True):
	"""Enable or disable debug logging for timeshift module."""
	global _DEBUG_ENABLED
	_DEBUG_ENABLED = bool(enabled)
	if _DEBUG_ENABLED:
		_debug_log("Debug logging enabled")
	else:
		_debug_log("Debug logging disabled")

class TimeShiftBuffer:
	"""Continuously captures the currently playing stream to a local file
	so it can be rewound and replayed.
	"""

	CAPACITY_SECONDS = 600		  # 10 minutes
	_TRIM_MARGIN_SECONDS = 120
	_TRIM_CHECK_INTERVAL = 30

	def __init__(self, tmp_dir=None):
		self._tmp_dir = tmp_dir or tempfile.gettempdir()
		self._thread = None
		self._stop_event = threading.Event()
		self._file_path = None
		self._file_lock = threading.Lock()
		self._file_handle = None
		self._session_start = None
		self._bytes_written = 0
		self._active = False
		self._suspend_trim = 0
		self._url = None
		self._is_hls = False
		self._hls_skipped = False
		self._reserved_prefix_len = 0
		self._flac_probe_done = True
		self._flac_probe_buf = b""
		self._generation = 0
		self._hls_captured_seconds = 0.0
		self._hls_segment_durations = collections.deque()
		# Real capture-time tracking for buffered_seconds()/trim/snippet math.
		# elapsed-since-session-start is NOT the same as actual captured
		# audio duration when the connection takes a while to establish (or
		# drops and reconnects) - _capture_leg_start/_capture_accum_seconds
		# track only the time a connection was actually open and writing.
		self._capture_leg_start = None
		self._capture_accum_seconds = 0.0
		# ICY metadata stripping state
		self._icy_metaint = 0
		self._icy_bytes_until_meta = 0
		self._icy_meta_remaining = 0

	# -- Public API ---------------------------------------------------------

	def start(self, url):
		"""Begin capturing *url* into a fresh buffer file."""
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
		self._flac_probe_done = self._is_hls
		self._flac_probe_buf = b""
		self._hls_captured_seconds = 0.0
		self._hls_segment_durations = collections.deque()
		self._capture_leg_start = None
		self._capture_accum_seconds = 0.0
		self._icy_metaint = 0
		self._icy_bytes_until_meta = 0
		self._icy_meta_remaining = 0

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
		return self._hls_skipped

	def get_file_path(self):
		return self._file_path

	def get_url(self):
		return self._url

	def get_reserved_prefix_len(self):
		return self._reserved_prefix_len

	def extract_recent_snippet(self, seconds, out_path):
		"""Write the most recently captured *seconds* of audio to *out_path*."""
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

			elapsed = self._captured_seconds()
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

	def _captured_seconds(self):
		"""Actual elapsed capture time - time a connection was open and
		writing, NOT wall-clock time since start() was called. The two
		diverge whenever the initial connection is slow, or a mid-session
		reconnect happens; using wall-clock time there overestimates how
		much audio is really in the buffer file, and rewind then seeks
		past what was actually written.

		HLS captures track their own duration separately (see
		_hls_captured_seconds, accumulated in _run_hls() from each
		segment's #EXTINF value) - _capture_leg_start/_capture_accum_seconds
		below are only ever updated by the non-HLS _run() connection loop.
		Without this branch, extract_recent_snippet() would always see 0.0
		elapsed for HLS stations (since leg/accum never move), compute a
		tail_bytes of 0, and fall back to reading from the very start of
		the buffer - which for stations that insert a fresh ad into every
		brand-new connection is exactly the ad, not the recent audio the
		snippet is supposed to capture.
		"""
		if self._is_hls:
			return self._hls_captured_seconds
		leg = self._capture_leg_start
		extra = (time.time() - leg) if leg else 0.0
		return self._capture_accum_seconds + extra

	def _shrink_captured_seconds(self, delta):
		"""Reduce the tracked capture duration by delta (used when trimming
		dropped audio off the front of the buffer)."""
		if self._capture_leg_start:
			self._capture_leg_start += delta
		else:
			self._capture_accum_seconds = max(0.0, self._capture_accum_seconds - delta)

	def buffered_seconds(self):
		"""Estimate how much audio is currently available in the buffer."""
		if not self._session_start:
			return 0.0
		if self._is_hls and self._hls_captured_seconds > 0:
			return max(0.0, min(self._hls_captured_seconds,
								self.CAPACITY_SECONDS + self._TRIM_MARGIN_SECONDS))
		if not self._is_hls and self._bytes_written <= 0:
			return 0.0
		elapsed = self._captured_seconds()
		return max(0.0, min(elapsed, self.CAPACITY_SECONDS + self._TRIM_MARGIN_SECONDS))

	def get_container_hint(self):
		"""Sniff the container type from the true start of the buffer file."""
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
		"""True if this buffer can be safely tailed."""
		if self._reserved_prefix_len > 0:
			return True
		return self.get_container_hint() in self._TAIL_SAFE_CONTAINERS

	def enter_playback(self):
		"""Called when something starts reading the buffer file directly."""
		self._suspend_trim += 1

	def exit_playback(self):
		"""Matches a prior enter_playback() call."""
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
		"""True if a newer start() call has superseded this session."""
		return my_gen != self._generation

	_FLAC_PROBE_CAP = 2 * 1024 * 1024

	def _maybe_capture_flac_header(self, chunk):
		"""Watch the first bytes for a native FLAC stream marker."""
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
				return
			header = buf[pos:pos + 4]
			is_last = bool(header[0] & 0x80)
			block_len = (header[1] << 16) | (header[2] << 8) | header[3]
			pos += 4 + block_len
			if is_last:
				self._reserved_prefix_len = pos
				self._flac_probe_done = True
				self._flac_probe_buf = b""
				log.info("FreeRadio TimeShift: detected native FLAC stream, "
						 "preserving %d-byte header as reserved prefix", pos)
				return

	def _strip_icy_metadata(self, data):
		"""Strip ICY metadata from a data chunk and return clean audio data.

		State (self._icy_bytes_until_meta / self._icy_meta_remaining) is
		carried across calls. A metadata block that happens to span two
		separate network reads - common with small/irregular recv() sizes
		on a raw socket - must keep being skipped in the next chunk;
		previously that leftover was silently dropped, so the next chunk's
		first byte(s) got misread as a bogus metadata length and the
		stream stayed desynced (and audibly corrupted) for the rest of
		the connection.
		"""
		if self._icy_metaint == 0:
			return data

		clean_chunks = []
		remaining = data
		while remaining:
			if self._icy_meta_remaining > 0:
				take = min(len(remaining), self._icy_meta_remaining)
				remaining = remaining[take:]
				self._icy_meta_remaining -= take
				if self._icy_meta_remaining > 0:
					break  # metadata block still incomplete - wait for more
				self._icy_bytes_until_meta = self._icy_metaint
				continue

			if self._icy_bytes_until_meta == 0:
				if len(remaining) < 1:
					break
				meta_len = remaining[0] * 16
				remaining = remaining[1:]
				if meta_len > 0:
					take = min(len(remaining), meta_len)
					remaining = remaining[take:]
					self._icy_meta_remaining = meta_len - take
					if self._icy_meta_remaining > 0:
						break  # metadata block continues in the next chunk
				self._icy_bytes_until_meta = self._icy_metaint
				continue

			take = min(len(remaining), self._icy_bytes_until_meta)
			clean_chunks.append(remaining[:take])
			remaining = remaining[take:]
			self._icy_bytes_until_meta -= take

		return b"".join(clean_chunks)

	def _run(self, my_gen):
		"""Capture loop entry point with reconnection support."""
		fail_streak = 0
		backoff = 2
		max_backoff = 30

		try:
			while not self._stop_event.is_set() and not self._is_stale(my_gen):
				try:
					self._run_once(my_gen)
					fail_streak = 0
					backoff = 2
				except Exception as e:
					_debug_log("capture loop failed for %s: %r" % (self._url, e))
					fail_streak += 1

				if self._stop_event.is_set() or self._is_stale(my_gen):
					return

				wait = min(backoff, max_backoff)
				backoff = min(backoff * 2, max_backoff)
				_debug_log("reconnecting capture in %ds... (%s)" % (wait, self._url))
				if self._stop_event.wait(wait) or self._is_stale(my_gen):
					return
		finally:
			if not self._is_stale(my_gen):
				self._close_file_handle()

	def _connect_https_icy_socket(self, url):
		"""Connect to HTTPS stream using raw socket + TLS + ICY protocol.
		This bypasses urllib completely and mimics how _open_icy works but with SSL.
		"""
		try:
			from urllib.parse import urlparse
			
			parsed = urlparse(url)
			host = parsed.hostname
			port = parsed.port or 443
			path = parsed.path or "/"
			if parsed.query:
				path += "?" + parsed.query

			_debug_log("HTTPS socket connecting to %s:%d" % (host, port))

			# Create socket and wrap with TLS
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.settimeout(20)
			sock.connect((host, port))

			# Wrap with SSL
			ssl_context = ssl.create_default_context()
			ssl_context.check_hostname = False
			ssl_context.verify_mode = ssl.CERT_NONE
			ssl_sock = ssl_context.wrap_socket(sock, server_hostname=host)

			# Send ICY request
			request = (
				"GET %s HTTP/1.0\r\n"
				"Host: %s\r\n"
				"User-Agent: Winamp/5.9.1.1002\r\n"
				"Icy-MetaData: 1\r\n"
				"Accept: */*\r\n"
				"Connection: close\r\n"
				"\r\n"
			) % (path, host)
			
			ssl_sock.sendall(request.encode())

			# Read response headers
			response = b""
			while True:
				chunk = ssl_sock.recv(4096)
				if not chunk:
					raise Exception("No response from server")
				response += chunk
				if b"\r\n\r\n" in response or b"\n\n" in response:
					break

			# Parse headers
			headers = {}
			header_part = response.split(b"\r\n\r\n", 1)[0] if b"\r\n\r\n" in response else response.split(b"\n\n", 1)[0]
			for line in header_part.split(b"\r\n"):
				if b":" in line:
					key, value = line.split(b":", 1)
					headers[key.decode().strip().lower()] = value.decode().strip()

			# Extract ICY metadata interval
			metaint_str = headers.get("icy-metaint", "")
			if metaint_str:
				try:
					self._icy_metaint = int(metaint_str)
					self._icy_bytes_until_meta = self._icy_metaint
					_debug_log("ICY metaint detected: %d bytes between metadata" % self._icy_metaint)
				except ValueError:
					pass

			# Extract prefix (audio data before first metadata)
			prefix = response.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in response else response.split(b"\n\n", 1)[1]

			_debug_log("HTTPS socket connected successfully to %s" % url)
			return ssl_sock, headers, prefix

		except Exception as e:
			_debug_log("HTTPS socket connection failed: %s" % e)
			raise

	def _run_once(self, my_gen):
		"""Capture loop: connects to the stream and appends raw bytes to the buffer."""
		url = self._url
		if self._is_stale(my_gen):
			return

		reader = None
		is_socket = False
		prefix = b""

		# Reset ICY state for each connection attempt
		self._icy_metaint = 0
		self._icy_bytes_until_meta = 0
		self._icy_meta_remaining = 0

		try:
			# Check if this is an HTTPS stream (like Soma FM)
			is_https = url.lower().startswith("https://")
			
			if is_https:
				# Use raw socket + TLS + ICY protocol (bypasses urllib)
				try:
					ssl_sock, headers, prefix = self._connect_https_icy_socket(url)
					reader = ssl_sock
					is_socket = True
					_debug_log("HTTPS socket connection successful for %s" % url)
				except Exception as e:
					_debug_log("HTTPS socket connection failed: %s, falling back to urllib" % e)
					# Fall through to urllib method
					pass

			if reader is None:
				# Standard HTTP/ICY connection via urllib
				req = urllib.request.Request(
					url,
					headers={"User-Agent": _recorder_mod._USER_AGENT, "Icy-MetaData": "1"},
				)
				reader = _recorder_mod._urlopen(req, 20)

				# Check for ICY metadata interval from HTTP headers
				metaint_str = reader.headers.get("icy-metaint", "")
				if metaint_str:
					try:
						self._icy_metaint = int(metaint_str)
						self._icy_bytes_until_meta = self._icy_metaint
						_debug_log("ICY metaint detected: %d bytes between metadata" % self._icy_metaint)
					except ValueError:
						pass

		except Exception as e:
			if not _recorder_mod._is_icy_error(e):
				raise
			_debug_log("ICY fallback triggered for %s (urllib error: %s)" % (url, e))
			sock, headers, prefix = _recorder_mod._open_icy(url, timeout=20)
			reader = sock
			is_socket = True

			# Parse ICY metadata interval from headers
			if headers:
				metaint_str = headers.get("icy-metaint", "")
				if metaint_str:
					try:
						self._icy_metaint = int(metaint_str)
						self._icy_bytes_until_meta = self._icy_metaint
						_debug_log("ICY metaint detected from socket: %d bytes between metadata" % self._icy_metaint)
					except ValueError:
						pass

		if self._is_stale(my_gen):
			try:
				reader.close()
			except Exception:
				pass
			return

		# Write any prefix audio bytes that arrived together with the
		# response headers - this applies to all three connection paths
		# above (direct HTTPS socket, ICY-fallback socket, and in practice
		# never urllib, which doesn't pre-read a prefix). It must run
		# through _strip_icy_metadata() like every other chunk so the
		# metaint counters stay in sync with the real stream position -
		# silently discarding it (as before) or writing it unstripped
		# would desync ICY tracking for the rest of the connection.
		if prefix and not self._is_stale(my_gen):
			clean_prefix = self._strip_icy_metadata(prefix)
			if clean_prefix:
				self._maybe_capture_flac_header(clean_prefix)
				self._write_chunk(clean_prefix, my_gen)

		if is_socket:
			_debug_log("capture connected via raw socket for %s" % url)
		else:
			_debug_log("capture connected via HTTP for %s" % url)

		# Real audio capture begins here - mark the start of this connected
		# "leg" so buffered_seconds() doesn't count the (possibly long)
		# connection setup time above as buffered audio.
		self._capture_leg_start = time.time()

		last_trim_check = time.time()
		chunk_count = 0

		try:
			while not self._stop_event.is_set() and not self._is_stale(my_gen):
				try:
					chunk = reader.recv(_CHUNK) if is_socket else reader.read(_CHUNK)
				except Exception as e:
					log.info("FreeRadio TimeShift: capture read failed after %d chunk(s): %s",
							 chunk_count, e)
					# This will trigger a reconnect in _run()
					raise
				if not chunk:
					log.info("FreeRadio TimeShift: capture stream ended (server closed connection) "
							 "after %d chunk(s)", chunk_count)
					# End of stream - reconnect
					return

				chunk_count += 1

				# Strip ICY metadata from this chunk
				clean_chunk = self._strip_icy_metadata(chunk)

				# Only write if there's clean audio data
				if clean_chunk:
					self._maybe_capture_flac_header(clean_chunk)
					self._write_chunk(clean_chunk, my_gen)

				now = time.time()
				if now - last_trim_check >= self._TRIM_CHECK_INTERVAL:
					last_trim_check = now
					if not self._suspend_trim:
						self._maybe_trim(my_gen)

			log.info("FreeRadio TimeShift: capture loop exiting, wrote %d chunk(s), "
					 "%d byte(s) total", chunk_count, self._bytes_written)
		finally:
			if self._capture_leg_start:
				self._capture_accum_seconds += time.time() - self._capture_leg_start
				self._capture_leg_start = None
			try:
				reader.close()
			except Exception:
				pass

	def _run_hls(self, my_gen):
		"""Capture loop for HLS (.m3u8) stations."""
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
				pending_duration = 0.0
				for line in lines:
					line = line.strip()
					if line.startswith("#EXTINF"):
						m = _re.search(r'#EXTINF:\s*([\d.]+)', line)
						if m:
							try:
								pending_duration = float(m.group(1))
							except ValueError:
								pending_duration = 0.0
						continue
					if line and not line.startswith("#"):
						seg_url = _abs(line, base_url)
						if seg_url not in seen_segments:
							new_segments.append((seg_url, pending_duration))
						pending_duration = 0.0

				for seg_url, seg_duration in new_segments:
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
					with self._file_lock:
						self._hls_segment_durations.append((len(data), seg_duration))
						self._hls_captured_seconds += seg_duration

					now = time.time()
					if now - last_trim_check >= self._TRIM_CHECK_INTERVAL:
						last_trim_check = now
						if not self._suspend_trim:
							self._maybe_trim(my_gen)

				if len(seen_segments) > 500:
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
		"""Drop the oldest portion of the buffer file once it exceeds capacity."""
		if self._is_stale(my_gen):
			return
		if not self._session_start:
			return
		if self._is_hls:
			self._maybe_trim_hls(my_gen)
			return
		elapsed = self._captured_seconds()
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
				self._shrink_captured_seconds(drop_bytes / bytes_per_second)
				self._bytes_written = len(prefix) + len(remainder)
				self._file_handle = open(path, "ab", buffering=0)
			except OSError as e:
				log.info("FreeRadio TimeShift: trim failed: %s", e)
				try:
					self._file_handle = open(path, "ab", buffering=0)
				except OSError:
					self._file_handle = None

	def _maybe_trim_hls(self, my_gen):
		"""HLS version of _maybe_trim(): drops the oldest whole segments."""
		if self._hls_captured_seconds <= self.CAPACITY_SECONDS + self._TRIM_MARGIN_SECONDS:
			return
		if not self._hls_segment_durations:
			return

		path = self._file_path
		if not path:
			return

		with self._file_lock:
			if self._is_stale(my_gen):
				return
			try:
				if self._file_handle:
					try:
						self._file_handle.close()
					except Exception:
						pass
					self._file_handle = None

				target_drop_duration = self._hls_captured_seconds - self.CAPACITY_SECONDS
				drop_bytes = 0
				drop_duration = 0.0
				while (len(self._hls_segment_durations) > 1
					   and drop_duration < target_drop_duration):
					seg_bytes, seg_dur = self._hls_segment_durations.popleft()
					drop_bytes += seg_bytes
					drop_duration += seg_dur

				if drop_bytes <= 0:
					self._file_handle = open(path, "ab", buffering=0)
					return

				size = os.path.getsize(path)
				prefix_len = min(self._reserved_prefix_len, size)
				drop_bytes = min(drop_bytes, max(0, size - prefix_len))
				if drop_bytes <= 0:
					self._file_handle = open(path, "ab", buffering=0)
					return

				with open(path, "rb") as f:
					prefix = f.read(prefix_len) if prefix_len else b""
					f.seek(prefix_len + drop_bytes)
					remainder = f.read()
				with open(path, "wb") as f:
					if prefix:
						f.write(prefix)
					f.write(remainder)

				self._hls_captured_seconds = max(0.0, self._hls_captured_seconds - drop_duration)
				self._bytes_written = len(prefix) + len(remainder)
				self._file_handle = open(path, "ab", buffering=0)
			except OSError as e:
				log.info("FreeRadio TimeShift: HLS trim failed: %s", e)
				try:
					self._file_handle = open(path, "ab", buffering=0)
				except OSError:
					self._file_handle = None