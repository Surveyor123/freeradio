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
import ssl
import subprocess
import threading
import urllib.request
import uuid

log = logging.getLogger(__name__)

_USER_AGENT = "FreeRadio-NVDA/1.0"
_CHUNK      = 65536   # 64 KB read chunk

# Some stream servers present expired or otherwise invalid TLS certificates
# yet still serve audio perfectly fine over HTTPS - BASS's own HTTP engine
# does not validate certificates as strictly as Python's default-verifying
# urlopen does, which is why live playback works on these stations while a
# plain urlopen() call raises SSL: CERTIFICATE_VERIFY_FAILED. Since this is
# just audio content (not sensitive data), certificate verification is
# relaxed for every stream/playlist/segment fetch below - in recorder.py and
# in timeshift.py, which reuses this helper. This context only takes effect
# for https:// requests; it has no effect on plain http:// connections.
_INSECURE_SSL_CONTEXT = ssl.create_default_context()
_INSECURE_SSL_CONTEXT.check_hostname = False
_INSECURE_SSL_CONTEXT.verify_mode = ssl.CERT_NONE


def _urlopen(req, timeout):
	"""urllib.request.urlopen() with relaxed TLS certificate verification.
	Use this instead of calling urllib.request.urlopen() directly anywhere
	a stream, playlist, or segment is fetched."""
	return urllib.request.urlopen(req, timeout=timeout, context=_INSECURE_SSL_CONTEXT)


class _IcyProtocolError(Exception):
	"""Raised when a server replies with ICY 200 OK instead of HTTP."""


def _is_icy_error(exc):
	"""Return True when *exc* was caused by an ICY 200 OK status line."""
	msg = str(exc).upper()
	# http.client.BadStatusLine, ValueError, etc. all embed the bad line in str(exc)
	return "ICY" in msg


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


def _make_output_path(station_name, ext="mp3", folder=None):
	ts    = datetime.datetime.now().strftime("%Y-%m-%d %H-%M")
	name  = _safe_filename(station_name)
	fname = f"{name} - {ts}.{ext}"
	return os.path.join(folder or _recordings_dir(), fname)


def _resolve_output_folder(custom_folder):
	"""Resolve the folder a scheduled recording should be written to.

	Returns (folder_path, fallback_reason). fallback_reason is None when
	*custom_folder* is empty/unset (global default used, as before) or was
	used successfully as-is. When the requested folder cannot be created or
	written to, the global default is returned instead and fallback_reason
	holds a short, user-facing explanation so the caller can notify the
	user that their chosen folder was not used for this recording.
	"""
	custom_folder = (custom_folder or "").strip()
	if not custom_folder:
		return _recordings_dir(), None
	try:
		os.makedirs(custom_folder, exist_ok=True)
		# os.makedirs succeeding doesn't guarantee the folder is writable
		# (e.g. a read-only network share) — verify with an actual write.
		# The probe name must be unique per call: multiple scheduled
		# recordings can resolve the same folder at the same moment (e.g.
		# several entries firing together), and a fixed filename would have
		# one thread's write collide with another's on Windows.
		probe = os.path.join(custom_folder, ".freeradio_write_test_%s" % uuid.uuid4().hex)
		with open(probe, "w") as f:
			f.write("")
		os.remove(probe)
		return custom_folder, None
	except Exception as e:
		log.warning(
			"FreeRadio Recorder: configured folder '%s' is unavailable (%s); "
			"falling back to the default recordings folder",
			custom_folder, e,
		)
		return _recordings_dir(), str(e)


_RECORDING_FORMATS = ("original", "audio_only", "mp3")


def _normalise_recording_format(value):
	"""Return a supported recording output mode, defaulting safely to original."""
	return value if value in _RECORDING_FORMATS else "original"


def _normalise_mp3_bitrate(value):
	"""Clamp the configured MP3 bitrate to a sensible encoder range."""
	try:
		value = int(value)
	except (TypeError, ValueError):
		value = 128
	return min(320, max(64, value))


def _default_ffmpeg_path(dll_dir=None):
	"""Return the configured or bundled ffmpeg executable path."""
	try:
		import config as _cfg
		configured = _cfg.conf["freeradio"].get("ffmpeg_path", "").strip()
		if configured:
			return configured
	except Exception:
		pass
	if dll_dir:
		return os.path.join(dll_dir, "ffmpeg.exe")
	return "ffmpeg.exe"


def _run_ffmpeg(args):
	"""Run ffmpeg without opening a console window and return success."""
	try:
		result = subprocess.run(
			args,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.PIPE,
			creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
			check=False,
		)
		if result.returncode == 0:
			return True, ""
		error = result.stderr.decode("utf-8", errors="replace")[-2000:]
		return False, error
	except Exception as e:
		return False, str(e)


def _replace_converted_file(source_path, temporary_path, destination_path):
	"""Publish a completed conversion, removing the source only on success."""
	if not os.path.isfile(temporary_path) or os.path.getsize(temporary_path) == 0:
		return False
	if os.path.abspath(source_path) != os.path.abspath(destination_path):
		try:
			os.remove(destination_path)
		except FileNotFoundError:
			pass
		os.replace(temporary_path, destination_path)
		try:
			os.remove(source_path)
		except OSError:
			pass
	else:
		os.replace(temporary_path, destination_path)
	return True


def convert_recording(source_path, mode="original", ffmpeg_path="ffmpeg.exe", mp3_bitrate=128):
	"""Convert a finished recording according to the selected output mode.

	Returns ``(output_path, error_message)``. The original file is retained
	whenever conversion fails. ``audio_only`` remuxes video containers without
	re-encoding; it first tries M4A (ideal for the common HLS AAC case) and falls
	back to MKA when the source audio codec cannot be stored in MP4.
	"""
	mode = _normalise_recording_format(mode)
	if mode == "original" or not source_path or not os.path.isfile(source_path):
		return source_path, ""

	base, ext = os.path.splitext(source_path)
	ext = ext.lower()
	ffmpeg_path = ffmpeg_path or "ffmpeg.exe"

	if not os.path.isfile(ffmpeg_path) and os.path.dirname(ffmpeg_path):
		return source_path, "ffmpeg.exe not found: %s" % ffmpeg_path

	if mode == "audio_only":
		# Ordinary radio recordings are already audio-only and should remain
		# byte-for-byte original. Only multimedia containers need remuxing.
		if ext not in (".ts", ".m2ts", ".mts", ".mp4", ".m4v", ".mov", ".mkv", ".webm"):
			return source_path, ""

		attempts = (
			(base + ".m4a", ["-c:a", "copy", "-movflags", "+faststart"]),
			(base + ".mka", ["-c:a", "copy"]),
		)
		last_error = ""
		for destination, codec_args in attempts:
			temporary = destination + ".converting"
			try:
				os.remove(temporary)
			except FileNotFoundError:
				pass
			args = [
				ffmpeg_path, "-hide_banner", "-loglevel", "error", "-y",
				"-i", source_path, "-map", "0:a:0", "-vn",
			] + codec_args + [temporary]
			# The temporary suffix is intentionally non-standard, so explicitly
			# select the matching container instead of relying on its extension.
			args[-1:-1] = ["-f", "mp4" if destination.endswith(".m4a") else "matroska"]
			ok, last_error = _run_ffmpeg(args)
			if ok and _replace_converted_file(source_path, temporary, destination):
				return destination, ""
			try:
				os.remove(temporary)
			except OSError:
				pass
		return source_path, last_error or "Could not extract the audio track"

	# MP3 input is already in the requested format; avoid a lossy second encode.
	if ext == ".mp3":
		return source_path, ""

	destination = base + ".mp3"
	temporary = destination + ".converting"
	try:
		os.remove(temporary)
	except FileNotFoundError:
		pass
	bitrate = _normalise_mp3_bitrate(mp3_bitrate)
	args = [
		ffmpeg_path, "-hide_banner", "-loglevel", "error", "-y",
		"-i", source_path, "-map", "0:a:0", "-vn",
		"-c:a", "libmp3lame", "-b:a", "%dk" % bitrate,
		"-id3v2_version", "3", "-f", "mp3", temporary,
	]
	ok, error = _run_ffmpeg(args)
	if ok and _replace_converted_file(source_path, temporary, destination):
		return destination, ""
	try:
		os.remove(temporary)
	except OSError:
		pass
	return source_path, error or "Could not convert the recording to MP3"


def _open_icy(url, timeout=20):
	"""Open a Shoutcast/Icecast stream that responds with 'ICY 200 OK'.

	urllib cannot parse the non-standard ICY status line, so we connect via a
	raw socket, send a minimal HTTP/1.0 GET request, and consume the response
	headers ourselves.  Returns a tuple (socket, headers_dict, body_prefix)
	where body_prefix is any data already read past the header boundary.
	Raises OSError / socket.error on failure.
	"""
	import socket
	import re
	from urllib.parse import urlparse

	parsed   = urlparse(url)
	host     = parsed.hostname
	port     = parsed.port or 80
	path     = (parsed.path or "/") + (";" if url.rstrip().endswith(";") else "")
	# keep the trailing semicolon if the original URL had it
	if url.rstrip().endswith(";") and not path.endswith(";"):
		path += ";"
	# Use the raw path+query from the original URL to avoid mangling
	raw_path = parsed.path
	if parsed.query:
		raw_path += "?" + parsed.query
	if not raw_path:
		raw_path = "/"

	sock = socket.create_connection((host, port), timeout=timeout)
	request = (
		f"GET {raw_path} HTTP/1.0\r\n"
		f"Host: {host}:{port}\r\n"
		f"User-Agent: {_USER_AGENT}\r\n"
		f"Icy-MetaData: 0\r\n"
		f"Connection: close\r\n"
		f"\r\n"
	)
	sock.sendall(request.encode())

	# Read until we find the blank line that ends the headers.
	buf = b""
	while b"\r\n\r\n" not in buf and b"\n\n" not in buf:
		data = sock.recv(4096)
		if not data:
			break
		buf += data
		if len(buf) > 65536:   # safety limit
			break

	# Split at the first blank line
	if b"\r\n\r\n" in buf:
		header_raw, body_prefix = buf.split(b"\r\n\r\n", 1)
	elif b"\n\n" in buf:
		header_raw, body_prefix = buf.split(b"\n\n", 1)
	else:
		header_raw, body_prefix = buf, b""

	lines   = header_raw.decode("utf-8", errors="ignore").splitlines()
	status  = lines[0] if lines else ""
	headers = {}
	for line in lines[1:]:
		if ":" in line:
			k, _, v = line.partition(":")
			headers[k.strip().lower()] = v.strip()

	# Accept ICY 200 OK  or  HTTP/1.x 200
	if not re.match(r"(ICY|HTTP/\S+)\s+200", status, re.IGNORECASE):
		sock.close()
		raise OSError(f"Unexpected status from ICY server: {status!r}")

	return sock, headers, body_prefix


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
	# Native FLAC stream marker
	if segment_data[:4] == b"fLaC":
		return "flac"
	# Ogg container (Ogg Vorbis / Ogg Opus / Ogg FLAC)
	if segment_data[:4] == b"OggS":
		return "ogg"
	# MP3: either an ID3v2 tag at the very start, or an MPEG audio frame
	# sync word (11 set bits: 0xFF followed by 0xE0-0xFF).
	if segment_data[:3] == b"ID3":
		return "mp3"
	if segment_data[0] == 0xFF and (segment_data[1] & 0xE0) == 0xE0:
		return "mp3"
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
		with _urlopen(req, 10) as resp:
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
				self._run_once(first)
				# _run_once returns normally only when the stream ends cleanly
				# or stop is requested; reset first flag after first successful connect
				first = False
				fail_streak = 0
				connected   = True

			except _IcyProtocolError:
				# Server returned ICY 200 OK — retry with raw socket path
				log.info("FreeRadio Recorder: ICY protocol detected, switching to raw socket mode")
				try:
					self._run_icy(first)
					first = False
					fail_streak = 0
					connected   = True
				except Exception as e2:
					if self._stop.is_set():
						return
					self._error = e2
					fail_streak += 1
					log.warning(
						"FreeRadio Recorder: ICY connection error (streak=%d): %s",
						fail_streak, e2,
					)

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

	def _run_once(self, first):
		"""Single connection attempt via urllib.  Raises _IcyProtocolError when
		the server replies with 'ICY 200 OK' so the caller can switch modes."""
		req = urllib.request.Request(
			self._effective_url,
			headers={"User-Agent": _USER_AGENT, "Icy-MetaData": "0"},
		)
		try:
			resp_cm = _urlopen(req, 20)
		except Exception as e:
			# urllib raises a ValueError/http.client.BadStatusLine for ICY responses.
			# The message reliably contains "ICY" in that case.
			if _is_icy_error(e):
				raise _IcyProtocolError() from e
			raise

		with resp_cm as resp:
			if first:
				ct  = resp.headers.get("Content-Type", "")
				ext = _guess_ext(self._effective_url, ct)
				base, _ = os.path.splitext(self.output_path)
				self.output_path = base + "." + ext
				log.info("FreeRadio Recorder: writing to %s (ct=%s)", self.output_path, ct)

			with open(self.output_path, "ab") as f:
				while not self._stop.is_set():
					chunk = resp.read(_CHUNK)
					if not chunk:
						break
					f.write(chunk)

	def _run_icy(self, first):
		"""Connect via raw socket to handle Shoutcast/Icecast ICY 200 OK servers."""
		sock, headers, body_prefix = _open_icy(self._effective_url, timeout=20)
		try:
			if first:
				ct  = headers.get("content-type", "")
				ext = _guess_ext(self._effective_url, ct)
				base, _ = os.path.splitext(self.output_path)
				self.output_path = base + "." + ext
				log.info("FreeRadio Recorder: ICY writing to %s (ct=%s)", self.output_path, ct)

			with open(self.output_path, "ab") as f:
				if body_prefix:
					f.write(body_prefix)
				while not self._stop.is_set():
					chunk = sock.recv(_CHUNK)
					if not chunk:
						break
					f.write(chunk)
		finally:
			try:
				sock.close()
			except Exception:
				pass

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
				with _urlopen(req, 10) as resp:
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
							with _urlopen(seg_req, 15) as seg_resp:
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
										with _urlopen(map_req, 15) as map_resp:
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
										with _urlopen(map_req, 15) as map_resp:
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
		with _urlopen(req, 10) as resp:
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


_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class ScheduledRecording:
	"""Represents one scheduled (possibly recurring) recording entry.

	recurrence values:
	  "once"       – fire exactly once (default / legacy behaviour)
	  "weekly"     – repeat every week on the specified active_days
	  "indefinite" – repeat every week on active_days with no end limit

	active_days: list of weekday integers 0–6 (0=Monday … 6=Sunday).
	  An empty list or None means all days are active.

	max_occurrences: how many times to fire before auto-removing.
	  Ignored when recurrence is "indefinite" or "once".

	occurrences_done: counter incremented after each successful fire.
	"""

	def __init__(self, station, start_time, duration_minutes,
	             player_paths=None, record_only=False,
	             recurrence="once", active_days=None,
	             max_occurrences=0, occurrences_done=0,
	             output_folder=None):
		self.station           = station
		self.start_time        = start_time
		self.duration_minutes  = duration_minutes
		self.player_paths      = player_paths or {}   # {vlc, potplayer, wmp}
		self.record_only       = record_only
		self.fired             = False
		self.output_path       = None
		# Per-entry destination folder. Empty string/None means "use the
		# global default recordings folder" (config.conf["freeradio"]["recordings_dir"]).
		self.output_folder     = (output_folder or "").strip()
		# Recurrence fields
		self.recurrence        = recurrence       # "once" | "weekly" | "indefinite"
		self.active_days       = active_days or []  # [] means all days
		self.max_occurrences   = max_occurrences  # 0 = unlimited (for "indefinite")
		self.occurrences_done  = occurrences_done
		# Transient crash-recovery field — never persisted.  When set, the
		# scheduler should record for this many minutes instead of
		# duration_minutes, without altering the canonical start_time /
		# duration_minutes the user entered (see _load_schedules).
		self.catchup_duration_minutes = None

	# ------------------------------------------------------------------
	# Recurrence helpers
	# ------------------------------------------------------------------

	def is_recurring(self):
		"""Return True when this entry should be re-scheduled after firing."""
		return self.recurrence in ("weekly", "indefinite")

	def has_more_occurrences(self):
		"""Return True when there are still firings left for this entry."""
		if self.recurrence == "once":
			return False
		if self.recurrence == "indefinite":
			return True
		# "weekly" with a fixed count
		if self.max_occurrences > 0:
			return self.occurrences_done < self.max_occurrences
		return True  # weekly with no cap → treat as indefinite

	def next_occurrence(self):
		"""Compute and return the next start_time for a recurring entry.

		Advances from the current start_time by one week, then keeps
		stepping forward one day at a time until a day that is in
		active_days (if any restriction is set).

		Returns a new datetime or None when no valid day is found within
		the next 7 days.
		"""
		candidate = self.start_time + datetime.timedelta(weeks=1)
		if not self.active_days:
			return candidate
		# Walk forward up to 7 days to find an allowed weekday.
		for _ in range(7):
			if candidate.weekday() in self.active_days:
				return candidate
			candidate += datetime.timedelta(days=1)
		return None

	def __str__(self):
		ts   = self.start_time.strftime("%d.%m.%Y %H:%M")
		mode = _("Record only") if self.record_only else _("Listen and record")
		base = f"{self.station.get('name','?')} — {ts} ({self.duration_minutes} min, {mode})"

		if self.recurrence == "weekly":
			day_labels = (
				", ".join(_DAY_NAMES[d] for d in sorted(self.active_days))
				if self.active_days else "every day"
			)
			remaining = ""
			if self.max_occurrences > 0:
				left = max(0, self.max_occurrences - self.occurrences_done)
				remaining = f", {left} left"
			base += f" [weekly: {day_labels}{remaining}]"
		elif self.recurrence == "indefinite":
			day_labels = (
				", ".join(_DAY_NAMES[d] for d in sorted(self.active_days))
				if self.active_days else "every day"
			)
			base += f" [indefinite: {day_labels}]"

		return base


def _schedules_path():
	"""The path to the JSON file."""
	appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
	return os.path.join(appdata, "nvda", "freeradio_schedules.json")


def _save_schedules(schedules):
	"""Persist the given schedule entries to JSON.

	`schedules` must already be the exact set the caller wants written —
	both still-pending entries AND any currently-active (already fired,
	still recording) entries.  Active entries are written with their
	canonical/original start_time and duration_minutes (never the
	crash-recovery-adjusted values), so that if NVDA is closed and
	restarted while a recording is still in progress, _load_schedules()
	can find it on disk and start a catch-up recording for the time that
	remains — without this, a recording that started normally would
	vanish from disk the moment it began, leaving nothing to resume from
	if NVDA restarted mid-recording.
	"""
	import json
	data = []
	for rec in schedules:
		try:
			data.append({
				"station":           rec.station,
				"start_time":        rec.start_time.isoformat(),
				"duration_minutes":  rec.duration_minutes,
				"player_paths":      rec.player_paths,
				"record_only":       rec.record_only,
				# Recurrence fields (absent in legacy files → defaults apply on load)
				"recurrence":        rec.recurrence,
				"active_days":       rec.active_days,
				"max_occurrences":   rec.max_occurrences,
				"occurrences_done":  rec.occurrences_done,
				# Absent in legacy files → "" on load, meaning "use default".
				"output_folder":     rec.output_folder,
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


def _roll_forward_occurrence(start, active_days, now, max_steps=520):
	"""Advance `start` week-by-week (respecting active_days) until it is
	strictly in the future relative to `now`.

	Used when a recurring entry was missed entirely (NVDA was not running
	for the whole scheduled window), so the original entry is not lost —
	it is simply moved on to its next valid future occurrence, exactly as
	if each missed firing had happened and re-queued normally.

	Returns (new_start, steps_skipped) or (None, steps_skipped) if no
	valid day could be found (e.g. nonsensical active_days).
	"""
	candidate = start
	steps = 0
	while candidate <= now and steps < max_steps:
		candidate = candidate + datetime.timedelta(weeks=1)
		if active_days:
			found = False
			for _ in range(7):
				if candidate.weekday() in active_days:
					found = True
					break
				candidate += datetime.timedelta(days=1)
			if not found:
				return None, steps
		steps += 1
	if candidate <= now:
		return None, steps
	return candidate, steps


def _load_schedules():
	"""Load scheduled recordings from JSON.

	Two special cases compared to the original implementation:

	1. Crash recovery — if a recurring or one-shot entry should currently
	   be active (its start_time has passed but the deadline has not yet
	   been reached), a *catch-up* recording is started immediately for
	   the remaining duration.  Crucially, the entry's canonical
	   start_time and duration_minutes — the values the user originally
	   entered — are left untouched.  Only the transient
	   catchup_duration_minutes field is set, which the scheduler uses
	   solely to decide how long to actually record this one time.  This
	   means:
	     - The schedule list keeps showing the original entry (e.g.
	       20:00, 10 min) rather than a value rewritten to match the late
	       start (e.g. 20:04, 6 min).
	     - When a recurring entry is caught up this way, the normal
	       requeue logic in the scheduler computes the *next* occurrence
	       from the original, unmodified start_time, so the weekly
	       schedule itself is never shifted and no extra entry is added.

	2. Entirely-missed recurring entries — if the whole scheduled window
	   has already passed (NVDA wasn't running at all during it), a
	   recurring entry is rolled forward to its next valid future
	   occurrence instead of being silently dropped.  Indefinitely
	   repeating entries are therefore only ever removed when the user
	   deletes them.  One-off ("once") entries that were missed entirely
	   are still dropped, since there is nothing left to catch up.

	3. Recurrence fields — "recurrence", "active_days", "max_occurrences",
	   and "occurrences_done" are read back from the JSON.  Missing keys
	   (legacy files) fall back to "once" / [] / 0 / 0.
	"""
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
				start            = datetime.datetime.fromisoformat(item["start_time"])
				duration_minutes = item["duration_minutes"]
				recurrence       = item.get("recurrence", "once")
				active_days      = item.get("active_days", [])
				max_occurrences  = item.get("max_occurrences", 0)
				occurrences_done = item.get("occurrences_done", 0)
				output_folder    = item.get("output_folder", "")
				is_recurring     = recurrence in ("weekly", "indefinite")

				catchup_minutes = None
				deadline = start + datetime.timedelta(minutes=duration_minutes)

				if start <= now:
					remaining_minutes = None
					if now < deadline:
						remaining_minutes = int((deadline - now).total_seconds() / 60)

					if remaining_minutes and remaining_minutes >= 1:
						# --- Crash recovery: still within the recording window ---
						# Leave start_time/duration_minutes exactly as the user
						# entered them; only flag how long the catch-up
						# recording should actually run for.
						catchup_minutes = remaining_minutes
						log.info(
							"FreeRadio Recorder: crash recovery — resuming '%s' "
							"with %d minutes remaining (original schedule kept)",
							item.get("station", {}).get("name", "?"),
							remaining_minutes,
						)
					elif is_recurring:
						# --- Entirely missed (or <1 min left) ---
						# Roll the recurring entry forward to its next valid
						# future occurrence rather than losing it.
						new_start, steps = _roll_forward_occurrence(start, active_days, now)
						if new_start is None:
							log.warning(
								"FreeRadio Recorder: could not find a future "
								"occurrence for '%s'; dropping entry",
								item.get("station", {}).get("name", "?"),
							)
							continue
						occurrences_done += steps
						if recurrence == "weekly" and max_occurrences > 0 and occurrences_done >= max_occurrences:
							# All fixed occurrences already elapsed while NVDA
							# wasn't running.
							continue
						start = new_start
						log.info(
							"FreeRadio Recorder: '%s' was missed entirely while "
							"NVDA was not running; rolled forward to %s",
							item.get("station", {}).get("name", "?"),
							start.strftime("%d.%m.%Y %H:%M"),
						)
					else:
						# One-off ("once") entry that is now entirely in the
						# past, or has less than a minute left — nothing
						# worth catching up; drop it.
						continue

				rec = ScheduledRecording(
					station          = item["station"],
					start_time       = start,
					duration_minutes = duration_minutes,
					player_paths     = item.get("player_paths", {}),
					record_only      = item.get("record_only", False),
					recurrence       = recurrence,
					active_days      = active_days,
					max_occurrences  = max_occurrences,
					occurrences_done = occurrences_done,
					output_folder    = output_folder,
				)
				rec.catchup_duration_minutes = catchup_minutes
				result.append(rec)
			except Exception as e:
				log.warning("FreeRadio Recorder: skipping bad schedule entry: %s", e)
		return result
	except Exception as e:
		log.warning("FreeRadio Recorder: could not load schedules: %s", e)
		return []




class _TimeshiftTailWriter:
	"""Writes a recording by tailing FreeRadio's already-running time-shift
	capture buffer instead of opening a brand-new connection to the stream.

	Why: some stations serve a fresh, per-connection ad to every new
	listener session (server-side ad insertion). The main player's own
	connection has already passed that ad by the time the user presses
	record, but a second, independent connection made at that moment (the
	old _StreamWriter behaviour) looks like a brand-new listener to the ad
	server and gets served a new ad instead of whatever track is actually
	airing. The time-shift buffer already has its own long-running
	connection open (started when the station began playing) - tailing it,
	rather than reconnecting, captures what is actually playing right now.
	"""

	_POLL_INTERVAL = 1.0

	def __init__(self, timeshift_buffer, output_path):
		self._buffer     = timeshift_buffer
		self.output_path = output_path
		self._stop       = threading.Event()
		self._thread     = None
		self._error      = None

	def start(self):
		# Suspend the buffer's trimming for as long as we're reading it,
		# same guard the rewind feature uses for the same reason.
		try:
			self._buffer.enter_playback()
		except Exception:
			pass
		self._thread = threading.Thread(
			target=self._run, daemon=True, name="FreeRadio-RecorderTail",
		)
		self._thread.start()

	def stop(self):
		self._stop.set()
		if self._thread:
			self._thread.join(timeout=5)
		try:
			self._buffer.exit_playback()
		except Exception:
			pass

	def _run(self):
		path = self._buffer.get_file_path()
		if not path:
			self._error = RuntimeError("Time-shift buffer has no active file")
			return

		# If this stream needs a container header to be decodable (fMP4-
		# packaged HLS), it lives in the first prefix_len bytes of the
		# buffer and must be prepended to our own output file too, or the
		# finished recording won't be playable on its own.
		prefix_len = 0
		try:
			prefix_len = self._buffer.get_reserved_prefix_len()
		except Exception:
			pass
		prefix_bytes = b""
		if prefix_len:
			try:
				with open(path, "rb") as f:
					prefix_bytes = f.read(prefix_len)
			except OSError:
				prefix_bytes = b""

		try:
			pos = os.path.getsize(path)
		except OSError:
			pos = 0

		out_f = None
		try:
			while not self._stop.is_set():
				try:
					size = os.path.getsize(path)
				except OSError:
					size = pos
				if size > pos:
					try:
						with open(path, "rb") as buf_f:
							buf_f.seek(pos)
							chunk = buf_f.read(size - pos)
					except OSError as e:
						log.warning("FreeRadio Recorder: tail read failed: %s", e)
						chunk = b""
					if chunk:
						if out_f is None:
							self._detect_and_fix_extension(prefix_bytes[:64] or chunk[:64])
							out_f = open(self.output_path, "ab")
							if prefix_bytes:
								out_f.write(prefix_bytes)
						out_f.write(chunk)
						pos += len(chunk)
				self._stop.wait(self._POLL_INTERVAL)
		finally:
			if out_f:
				try:
					out_f.close()
				except Exception:
					pass

	_CONTAINER_EXT = {
		"mp4":  ".m4a",
		"ts":   ".ts",
		"flac": ".flac",
		"ogg":  ".ogg",
		"mp3":  ".mp3",
	}

	def _detect_and_fix_extension(self, first_bytes):
		container = _detect_container_from_segment(first_bytes)
		base, current_ext = os.path.splitext(self.output_path)
		ext = self._CONTAINER_EXT.get(container)
		if ext:
			if current_ext != ext:
				self.output_path = base + ext
				log.warning("FreeRadio Recorder: detected %s container, saving as %s",
						  container, self.output_path)
			return
		# Byte sniffing came back inconclusive. For HLS (.m3u8) stations,
		# most AAC content is MP4-boxed even when the sniffed first bytes
		# didn't show it (e.g. mid-fragment), so keep the old .m4a default
		# for those. Otherwise guess from the station's own URL rather than
		# assuming every buffer-tailed recording is HLS/AAC.
		try:
			url = self._buffer.get_url() or ""
		except Exception:
			url = ""
		if url.lower().split("?")[0].endswith(".m3u8"):
			guessed = ".m4a"
		else:
			guessed = "." + _guess_ext(url)
		if current_ext != guessed:
			self.output_path = base + guessed
			log.warning("FreeRadio Recorder: unknown container from buffer, "
					  "guessed %s from station URL", guessed)


class Recorder:
	"""Manages instant and scheduled recordings."""

	def __init__(self, dll_dir=None, player_paths=None, volume=100, main_player=None,
	             recording_format="original", mp3_bitrate=128, ffmpeg_path=""):
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
		self._recording_format = _normalise_recording_format(recording_format)
		self._mp3_bitrate      = _normalise_mp3_bitrate(mp3_bitrate)
		self._ffmpeg_path      = ffmpeg_path or _default_ffmpeg_path(dll_dir)
		self._active_scheduled = set()  # currently running scheduled recordings
		self._active_scheduled_lock = threading.Lock()
		if self._scheduled:
			self._ensure_scheduler()

	def set_output_format(self, recording_format, mp3_bitrate=128, ffmpeg_path=""):
		"""Update output conversion settings for subsequent recordings."""
		self._recording_format = _normalise_recording_format(recording_format)
		self._mp3_bitrate = _normalise_mp3_bitrate(mp3_bitrate)
		self._ffmpeg_path = ffmpeg_path or _default_ffmpeg_path(self._dll_dir)

	def _finalize_writer(self, writer):
		"""Stop a writer and apply the selected output conversion.

		This method may invoke ffmpeg and must not run on NVDA's UI thread for
		interactive recordings. Scheduled recordings already call it from their
		worker thread.
		"""
		writer.stop()
		path = writer.output_path
		converted_path, error = convert_recording(
			path,
			mode=self._recording_format,
			ffmpeg_path=self._ffmpeg_path,
			mp3_bitrate=self._mp3_bitrate,
		)
		if error:
			log.error(
				"FreeRadio Recorder: output conversion failed; original retained: %s",
				error,
			)
			if hasattr(self, "_notify_conversion_error") and self._notify_conversion_error:
				self._notify_conversion_error(path, error)
		else:
			log.info("FreeRadio Recorder: finalized recording → %s", converted_path)
		return converted_path

	def _persist_schedules(self, extra_active=None):
		"""Save pending schedules together with whatever is currently
		recording.  Without including active recordings here, an entry
		would vanish from disk the instant it fires — leaving nothing to
		recover from if NVDA is closed and restarted while that recording
		is still in progress.

		extra_active: optional list of ScheduledRecording objects that
		have just been dispatched to a worker thread but may not yet have
		registered themselves in self._active_scheduled (avoids a race
		between the scheduler loop and _run_scheduled).
		"""
		with self._active_scheduled_lock:
			active = list(self._active_scheduled)
		if extra_active:
			seen = {id(r) for r in active}
			for r in extra_active:
				if id(r) not in seen:
					active.append(r)
					seen.add(id(r))
		_save_schedules(self._scheduled + active)

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

	def start(self, player, station_name, timeshift_buffer=None):
		"""Start instant recording. VLC keeps playing; Python writes the stream.

		timeshift_buffer: the RadioPlayer's TimeShiftBuffer, if available. When
		it is actively capturing, the recording tails that already-open
		connection instead of opening a fresh one - some stations serve a new
		ad to every brand-new connection, which a second connection made
		just for this recording would otherwise capture instead of the
		track actually airing.

		Returns output file path.
		"""
		original_url = getattr(player, "_current_url_resolved", None) or player._current_url
		if not original_url:
			raise RuntimeError("No station playing")
		log.warning("FreeRadio Recorder: instant recording URL = %s", original_url)
		if self._writer:
			self._writer.stop()

		out = _make_output_path(station_name)
		self._output_path  = out
		self._station_name = station_name
		if timeshift_buffer is not None and timeshift_buffer.is_active() and timeshift_buffer.is_tail_safe():
			self._writer = _TimeshiftTailWriter(timeshift_buffer, out)
			log.warning("FreeRadio Recorder: instant recording via time-shift buffer tail (no new connection)")
		else:
			self._writer = _StreamWriter(original_url, out)
		self._writer.start()
		log.warning("FreeRadio Recorder: instant recording started → %s", out)
		return out

	def start_song_capture(self, player, song_title, timeshift_buffer=None):
		"""Start a song-capture recording named after the current ICY track title.

		This mode is intended for stations that broadcast ICY metadata.  The file
		is named after the song rather than the station so recordings are easy to
		identify later.  The caller is responsible for stopping the recording when
		the track changes (see Recorder.stop_song_capture).

		timeshift_buffer: see start().

		Returns the output file path.
		"""
		original_url = getattr(player, "_current_url_resolved", None) or player._current_url
		if not original_url:
			raise RuntimeError("No station playing")

		# Stop any ongoing instant or song-capture recording before starting a new one.
		if self._writer:
			self._writer.stop()

		out = _make_output_path(song_title)
		self._output_path  = out
		self._station_name = song_title   # store the song title in the station-name slot
		self._song_capture = True         # flag: this recording was started in song-capture mode
		if timeshift_buffer is not None and timeshift_buffer.is_active() and timeshift_buffer.is_tail_safe():
			self._writer = _TimeshiftTailWriter(timeshift_buffer, out)
			log.warning("FreeRadio Recorder: song-capture recording via time-shift buffer tail (no new connection)")
		else:
			self._writer = _StreamWriter(original_url, out)
		self._writer.start()
		log.warning("FreeRadio Recorder: song-capture recording started → %s", out)
		return out

	def stop_song_capture(self):
		"""Stop an active song-capture recording.

		Clears the song-capture flag regardless of whether a writer was active so
		the recorder always returns to normal state after this call.
		Returns the saved file path, or None if no recording was active.
		"""
		path = self._output_path
		writer = self._writer
		self._writer = None
		self._output_path  = None
		self._station_name = ""
		self._song_capture = False
		if writer:
			path = self._finalize_writer(writer)
		log.info("FreeRadio Recorder: song-capture recording stopped, file=%s", path)
		return path

	def is_song_capture(self):
		"""Return True when the current recording was started in song-capture mode."""
		return bool(getattr(self, "_song_capture", False)) and self._writer is not None

	def get_song_title(self):
		"""Return the song title used for the active song-capture recording, or empty string."""
		if self.is_song_capture():
			return self._station_name
		return ""

	def stop(self, player=None):
		"""Stop instant recording. Returns saved file path."""
		path = self._output_path
		writer = self._writer
		self._writer = None
		self._output_path  = None
		self._station_name = ""
		# Also clear song-capture flag if stop() is called generically.
		self._song_capture = False
		if writer:
			path = self._finalize_writer(writer)
		log.info("FreeRadio Recorder: instant recording stopped, file=%s", path)
		return path

	def is_recording(self):
		return self._writer is not None

	def get_output_path(self):
		return self._output_path

	def get_station_name(self):
		return self._station_name

	def add_schedule(self, station, start_time, duration_minutes,
	                 player_paths=None, record_only=False,
	                 recurrence="once", active_days=None,
	                 max_occurrences=0, output_folder=None):
		"""Schedule a recording.

		player_paths: dict with optional keys 'vlc', 'potplayer', 'wmp'.
		              Used only when record_only=False (listen + record mode)
		              to launch a player for audio output.  Recording itself
		              never requires a player.
		recurrence:   "once" | "weekly" | "indefinite"
		active_days:  list of weekday ints 0–6 (0=Mon). [] means all days.
		max_occurrences: for "weekly" mode — 0 means no cap.
		output_folder: optional per-entry destination folder. Empty/None
		              means use the global default recordings folder.
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
			recurrence=recurrence,
			active_days=active_days or [],
			max_occurrences=max_occurrences,
			output_folder=output_folder,
		)
		self._scheduled.append(rec)
		self._scheduled.sort(key=lambda r: r.start_time)
		self._persist_schedules()
		self._ensure_scheduler()
		return rec, conflict_names

	def remove_schedule(self, rec):
		if rec in self._scheduled:
			self._scheduled.remove(rec)
			self._persist_schedules()

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

			# Remove fired entries from the pending list.
			self._scheduled = [r for r in self._scheduled if not r.fired]

			if fired:
				self._persist_schedules(extra_active=fired)
			time.sleep(1)

	def _run_scheduled(self, rec):
		"""Run a scheduled recording: Python writes the stream, optionally plays via main player."""
		import time

		url  = rec.station.get("url_resolved") or rec.station.get("url", "")
		name = rec.station.get("name", "Unknown").strip()
		folder, fallback_reason = _resolve_output_folder(rec.output_folder)
		if fallback_reason and hasattr(self, "_notify_folder_fallback") and self._notify_folder_fallback:
			self._notify_folder_fallback(rec, rec.output_folder, fallback_reason)
		out  = _make_output_path(name, folder=folder)

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
		self._persist_schedules()

		log.info("FreeRadio Recorder: scheduled recording started — %s → %s", name, out)
		if hasattr(self, "_notify_start") and self._notify_start:
			self._notify_start(rec)

		deadline = time.time() + (rec.catchup_duration_minutes or rec.duration_minutes) * 60
		while time.time() < deadline:
			if getattr(rec, "_force_stop", False):
				break
			time.sleep(min(1.0, deadline - time.time()))

		rec.output_path = self._finalize_writer(writer)
		rec._writer = None

		with self._active_scheduled_lock:
			self._active_scheduled.discard(rec)
		self._persist_schedules()

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

		# Re-queue recurring entries after the recording has fully completed.
		# Doing this here (rather than in _scheduler_loop) prevents a duplicate
		# entry from appearing in the schedule list when NVDA is restarted while
		# a recording is still in progress: if next_rec were created in the loop,
		# a restart would find both the still-active entry (causing a catch-up)
		# AND next_rec (a separate pending entry) in the JSON file.
		rec.occurrences_done += 1
		if rec.is_recurring() and rec.has_more_occurrences():
			next_start = rec.next_occurrence()
			if next_start is not None:
				next_rec = ScheduledRecording(
					station          = rec.station,
					start_time       = next_start,
					duration_minutes = rec.duration_minutes,
					player_paths     = rec.player_paths,
					record_only      = rec.record_only,
					recurrence       = rec.recurrence,
					active_days      = rec.active_days,
					max_occurrences  = rec.max_occurrences,
					occurrences_done = rec.occurrences_done,
					output_folder    = rec.output_folder,
				)
				self._scheduled.append(next_rec)
				self._scheduled.sort(key=lambda r: r.start_time)
				self._persist_schedules()
				log.info(
					"FreeRadio Recorder: recurring entry re-queued — "
					"'%s' next at %s",
					rec.station.get("name", "?"),
					next_start.strftime("%d.%m.%Y %H:%M"),
				)
			else:
				log.warning(
					"FreeRadio Recorder: could not find next valid day "
					"for '%s'; stopping recurrence",
					rec.station.get("name", "?"),
				)

	def terminate(self):
		self._stop_scheduler.set()
		if self._writer:
			self._writer.stop()
			self._writer = None
		for rec in self._scheduled:
			if hasattr(rec, "_writer") and rec._writer:
				rec._writer.stop()
