# -*- coding: utf-8 -*-
# FreeRadio - Recorder
#
# Recording strategy:
#   - For non-HLS streams: Python reads the stream directly over HTTP and writes it to disk.
#   - For HLS streams: resolves the master playlist, downloads segments sequentially.
#   - Output format: .m4a for AAC/MP4 streams, .ts for MPEG-TS streams, .aac for raw AAC.

import collections
import datetime
import hashlib
import logging
import os
import ssl
import subprocess
import threading
import urllib.request
import uuid

log = logging.getLogger(__name__)

_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001


def _set_scheduled_recording_power_request(active):
	"""Prevent idle sleep while a scheduled recording worker is active.

	The request belongs to the calling thread, so the same worker that enables
	it must clear it in a ``finally`` block.  This deliberately prevents only
	automatic idle sleep; it does not override an explicit Sleep command or a
	lid-close action chosen by the user.
	"""
	if os.name != "nt":
		return False
	try:
		import ctypes
		flags = _ES_CONTINUOUS | (_ES_SYSTEM_REQUIRED if active else 0)
		result = ctypes.windll.kernel32.SetThreadExecutionState(flags)
		if not result:
			log.warning(
				"FreeRadio Recorder: Windows rejected the scheduled-recording power request"
			)
		return bool(result)
	except Exception as e:
		log.warning("FreeRadio Recorder: could not update the Windows power request: %s", e)
		return False

# Primary User-Agent (works with ICY and most stations)
_USER_AGENT_PRIMARY = "FreeRadio-NVDA/1.0"
# Fallback User-Agent (used for servers like SomaFM that expect a browser-like UA)
_USER_AGENT_FALLBACK = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# Default to primary
_USER_AGENT = _USER_AGENT_PRIMARY
_CHUNK      = 65536   # 64 KB read chunk

# Some stream servers present expired or otherwise invalid TLS certificates
# yet still serve audio perfectly fine over HTTPS - BASS's own HTTP engine
# does not validate certificates as strictly as Python's default-verifying
# urlopen does, which is why live playback works on these stations while a
# plain urlopen() call raises SSL: CERTIFICATE_VERIFY_FAILED. Since this is
# just audio content (not sensitive data), _urlopen() below tries a normal,
# fully-verified connection first and only relaxes verification for a
# request that specifically failed on its certificate - not for one that
# failed for any other reason (timeout, connection refused, DNS, etc.),
# where relaxing verification wouldn't help anyway. This keeps every other,
# properly-configured server protected against a man-in-the-middle
# substituting the stream, while still letting these particular stations
# work. Used in recorder.py and in timeshift.py, which reuses this helper.
# This only takes effect for https:// requests; it has no effect on plain
# http:// connections.
_VERIFIED_SSL_CONTEXT  = ssl.create_default_context()
_INSECURE_SSL_CONTEXT  = ssl.create_default_context()
_INSECURE_SSL_CONTEXT.check_hostname = False
_INSECURE_SSL_CONTEXT.verify_mode    = ssl.CERT_NONE

# Hosts observed to fail with a certificate verification error at least
# once this session. A recording re-fetches from the same host constantly
# (once per HLS segment, or every reconnect on a dropped ICY connection),
# so without this, EVERY one of those requests would pay for a doomed
# verified attempt before falling back - on a host already known to need
# it, that's pure added latency on every single segment, which is exactly
# the kind of delay that turns into buffering/dropped segments on a
# recording. Once a host has shown it needs the fallback, later requests
# to it go straight to _INSECURE_SSL_CONTEXT; only the first request to
# a given host per session pays the verified-then-retry cost. This is
# purely a "skip the redundant probe" cache, not a trust decision - every
# other host is still verified, always, and a host only lands here after
# actually failing verification for real.
_ssl_verify_bypass_hosts = set()
_ssl_verify_bypass_lock  = threading.Lock()


def _is_cert_verify_error(exc):
	"""True if *exc* (or anything chained onto it via __cause__/__context__,
	e.g. a urllib.error.URLError wrapping an ssl.SSLCertVerificationError)
	is specifically a TLS certificate verification failure, as opposed to
	any other kind of connection failure. Used to decide whether retrying
	without certificate verification is actually appropriate - it isn't,
	for a plain timeout or refused connection, and retrying in that case
	would just delay an unavoidable failure."""
	seen = set()
	while exc is not None and id(exc) not in seen:
		seen.add(id(exc))
		if isinstance(exc, ssl.SSLCertVerificationError):
			return True
		if isinstance(exc, ssl.SSLError) and "CERTIFICATE_VERIFY_FAILED" in str(exc):
			return True
		exc = exc.__cause__ or exc.__context__
	return False


def _request_host(req):
	"""Best-effort hostname extraction from whatever _urlopen() was given
	(a urllib.request.Request or a plain URL string) - used only as a
	cache key for _ssl_verify_bypass_hosts, so a failure to extract one
	just means no caching for that call, not an error."""
	try:
		url = req.full_url
	except AttributeError:
		url = req
	try:
		from urllib.parse import urlparse
		return urlparse(url).hostname
	except Exception:
		return None


def _urlopen(req, timeout):
	"""urllib.request.urlopen() that verifies TLS certificates by default,
	and only falls back to relaxed verification for a request that
	specifically failed with a certificate error - see the comment above
	_VERIFIED_SSL_CONTEXT for why some stream servers need that at all.
	Use this instead of calling urllib.request.urlopen() directly anywhere
	a stream, playlist, or segment is fetched."""
	host = _request_host(req)
	if host is not None:
		with _ssl_verify_bypass_lock:
			already_bypassed = host in _ssl_verify_bypass_hosts
		if already_bypassed:
			return urllib.request.urlopen(req, timeout=timeout, context=_INSECURE_SSL_CONTEXT)

	try:
		return urllib.request.urlopen(req, timeout=timeout, context=_VERIFIED_SSL_CONTEXT)
	except Exception as e:
		if not _is_cert_verify_error(e):
			raise
		if host is not None:
			with _ssl_verify_bypass_lock:
				_ssl_verify_bypass_hosts.add(host)
		log.info(
			"FreeRadio: %s presented an invalid/untrusted TLS certificate; "
			"retrying without certificate verification (host will be "
			"remembered for the rest of this session)", host or req,
		)
		return urllib.request.urlopen(req, timeout=timeout, context=_INSECURE_SSL_CONTEXT)


def _parse_hls_media_segments(lines, base_url):
	"""Return ``(media_sequence, segments)`` for an HLS media playlist.

	Each segment is returned as ``(identity, absolute_url, duration)``. When
	``#EXT-X-MEDIA-SEQUENCE`` is present, the identity is the protocol-level
	media sequence number rather than the complete URL. This matters for HLS
	servers that add a fresh session token to every playlist response: the URL
	changes even though the segment is still exactly the same one.
	"""
	from urllib.parse import urljoin
	import re

	media_sequence = None
	skipped_segments = 0
	for raw_line in lines:
		line = raw_line.strip()
		if line.startswith("#EXT-X-MEDIA-SEQUENCE:"):
			try:
				media_sequence = int(line.split(":", 1)[1].strip())
			except (TypeError, ValueError):
				media_sequence = None
		elif line.startswith("#EXT-X-SKIP:"):
			attributes = line.split(":", 1)[1]
			match = re.search(
				r"(?:^|,)SKIPPED-SEGMENTS=(\d+)(?:,|$)",
				attributes,
				re.IGNORECASE,
			)
			if match:
				skipped_segments = int(match.group(1))

	segments = []
	pending_duration = 0.0
	pending_byterange = ""
	ordinal = skipped_segments
	for raw_line in lines:
		line = raw_line.strip()
		if line.startswith("#EXTINF"):
			match = re.search(r"#EXTINF:\s*([\d.]+)", line)
			if match:
				try:
					pending_duration = float(match.group(1))
				except ValueError:
					pending_duration = 0.0
			continue
		if line.startswith("#EXT-X-BYTERANGE:"):
			pending_byterange = line.split(":", 1)[1].strip()
			continue
		if not line or line.startswith("#"):
			continue

		segment_url = urljoin(base_url, line)
		if media_sequence is not None:
			identity = ("sequence", media_sequence + ordinal)
		else:
			# Preserve URL-based behaviour for playlists that do not expose
			# media sequence numbers. Include BYTERANGE because several logical
			# segments may intentionally share one resource URL.
			identity = ("url", segment_url, pending_byterange)
		segments.append((identity, segment_url, pending_duration))
		ordinal += 1
		pending_duration = 0.0
		pending_byterange = ""

	return media_sequence, segments


class _HlsSegmentTracker:
	"""Ordered, bounded set of successfully written HLS segment identities."""

	def __init__(self, max_entries=10000):
		self._max_entries = max(100, int(max_entries))
		self._seen = set()
		self._order = collections.deque()
		self._highest_sequence = None

	def prepare_playlist(self, segments):
		"""Notice a genuine server sequence reset without reacting to stale CDN data."""
		sequence_numbers = [
			identity[1] for identity, _url, _duration in segments
			if identity and identity[0] == "sequence"
		]
		if not sequence_numbers:
			return False
		current_highest = max(sequence_numbers)
		# A small backwards step can be a stale CDN response. A large one is
		# almost certainly an encoder/server restart and starts a new epoch.
		if self._highest_sequence is not None and current_highest + 128 < self._highest_sequence:
			self.clear()
			self._highest_sequence = current_highest
			return True
		if self._highest_sequence is None or current_highest > self._highest_sequence:
			self._highest_sequence = current_highest
		return False

	def contains(self, identity):
		return identity in self._seen

	def mark_written(self, identity):
		if identity in self._seen:
			return
		self._seen.add(identity)
		self._order.append(identity)
		while len(self._order) > self._max_entries:
			oldest = self._order.popleft()
			self._seen.discard(oldest)

	def clear(self):
		self._seen.clear()
		self._order.clear()


def _hls_content_signature(data):
	"""Return a stable signature for HLS initialization data."""
	return hashlib.sha256(data).digest()


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
	# Always use the primary UA for ICY servers; they often reject browser-like UAs.
	request = (
		f"GET {raw_path} HTTP/1.0\r\n"
		f"Host: {host}:{port}\r\n"
		f"User-Agent: {_USER_AGENT_PRIMARY}\r\n"
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
		# Use primary UA for manifest resolution; fallback is handled inside _run_hls.
		req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT_PRIMARY})
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
		# Set the first time a connection actually succeeds and data starts
		# being written — lets callers (e.g. scheduled recordings) tell a
		# real recording apart from one that spent its whole window failing
		# to connect (see _run_once / _run_icy / _run_hls).
		self._connected = threading.Event()
		
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

	def is_connected(self):
		"""True once a connection has succeeded and data has started writing
		at least once (not necessarily still connected right now)."""
		return self._connected.is_set()

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

	def _run_once(self, first, use_fallback=False):
		"""Single connection attempt via urllib.  Raises _IcyProtocolError when
		the server replies with 'ICY 200 OK' so the caller can switch modes.
		If use_fallback is True, the fallback browser-like UA is used instead
		of the primary UA. This helps with stations that filter by User-Agent.
		"""
		ua = _USER_AGENT_FALLBACK if use_fallback else _USER_AGENT_PRIMARY
		req = urllib.request.Request(
			self._effective_url,
			headers={"User-Agent": ua, "Icy-MetaData": "0"},
		)
		try:
			resp_cm = _urlopen(req, 20)
		except Exception as e:
			# urllib raises a ValueError/http.client.BadStatusLine for ICY responses.
			# The message reliably contains "ICY" in that case.
			if _is_icy_error(e):
				raise _IcyProtocolError() from e
			# If the connection was closed without response and we haven't tried
			# the fallback UA yet, retry with the fallback UA.
			if not use_fallback and "Remote end closed" in str(e):
				return self._run_once(first, use_fallback=True)
			raise

		with resp_cm as resp:
			if first:
				ct  = resp.headers.get("Content-Type", "")
				ext = _guess_ext(self._effective_url, ct)
				base, _ = os.path.splitext(self.output_path)
				self.output_path = base + "." + ext
				log.info("FreeRadio Recorder: writing to %s (ct=%s)", self.output_path, ct)

			with open(self.output_path, "ab") as f:
				self._connected.set()
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
				self._connected.set()
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

	def _fetch_manifest_with_fallback(self, manifest_url):
		"""Fetch an HLS manifest, trying primary then fallback User-Agent."""
		for ua in (_USER_AGENT_PRIMARY, _USER_AGENT_FALLBACK):
			try:
				req = urllib.request.Request(manifest_url, headers={"User-Agent": ua})
				with _urlopen(req, 10) as resp:
					return resp.read(32768).decode("utf-8", errors="ignore")
			except Exception:
				continue
		raise RuntimeError("Could not fetch HLS manifest: %s" % manifest_url)

	def _fetch_segment_with_fallback(self, seg_url):
		"""Fetch an HLS segment, trying primary then fallback User-Agent."""
		for ua in (_USER_AGENT_PRIMARY, _USER_AGENT_FALLBACK):
			try:
				req = urllib.request.Request(seg_url, headers={"User-Agent": ua})
				with _urlopen(req, 15) as resp:
					return resp.read()
			except Exception:
				continue
		raise RuntimeError("Could not fetch segment: %s" % seg_url)

	def _run_hls(self):
		"""Download HLS segments sequentially and write to a single file."""
		import time
		from urllib.parse import urlparse

		log.info("FreeRadio Recorder: HLS recording started for %s", self._effective_url)

		def _abs(url, base_url):
			from urllib.parse import urljoin
			return urljoin(base_url, url)

		seen_segments = _HlsSegmentTracker()
		manifest_url  = self._effective_url
		manifest_errors = 0
		target_dur    = 5
		first_segment_written = False
		output_file = None
		last_map_url = None   # tracks #EXT-X-MAP initialization segment URL
		last_map_signature = None

		while not self._stop.is_set():
			try:
				base_url = manifest_url.rsplit("/", 1)[0] + "/"
				# Use the helper that tries primary then fallback UA
				text = self._fetch_manifest_with_fallback(manifest_url)
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

				# Otherwise it's a media playlist. Use protocol-level media sequence
				# numbers as identities: signed/session query parameters may change
				# between two responses while still pointing to the same segment.
				media_sequence, parsed_segments = _parse_hls_media_segments(lines, base_url)
				if seen_segments.prepare_playlist(parsed_segments):
					log.info(
						"FreeRadio Recorder: HLS media sequence reset detected; "
						"starting a new segment epoch"
					)
				segments = [
					entry for entry in parsed_segments
					if not seen_segments.contains(entry[0])
				]

				log.debug(
					"FreeRadio Recorder: HLS %d new segments "
					"(target_dur=%ds, media_sequence=%s)",
					len(segments), target_dur, media_sequence,
				)

				seg_errors = 0
				for segment_identity, seg_url, _segment_duration in segments:
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
							# Use the helper that tries primary then fallback UA
							data = self._fetch_segment_with_fallback(seg_url)
							
							# First segment: detect container, write init segment if needed, open file
							if not first_segment_written:
								self._detect_and_fix_extension(data)
								output_file = open(self.output_path, "ab")
								first_segment_written = True
								self._connected.set()
								log.info("FreeRadio Recorder: first segment written to %s", self.output_path)

								# fMP4 streams carry moov/init in a separate #EXT-X-MAP segment.
								# Without it, players see no audio/video tracks.
								if current_map_url and current_map_url != seg_url:
									try:
										# Use fallback for init segment too
										init_data = self._fetch_segment_with_fallback(current_map_url)
										map_signature = _hls_content_signature(init_data)
										if map_signature != last_map_signature:
											output_file.write(init_data)
											output_file.flush()
											last_map_signature = map_signature
											log.info(
												"FreeRadio Recorder: wrote fMP4 init segment from %s",
												current_map_url,
											)
										else:
											log.debug(
												"FreeRadio Recorder: ignored unchanged fMP4 init "
												"segment with refreshed URL"
											)
										last_map_url = current_map_url
									except Exception as e:
										log.warning("FreeRadio Recorder: failed to fetch init segment: %s", e)
							else:
								# If the init segment changed mid-stream, write the new one
								if current_map_url and current_map_url != last_map_url:
									try:
										init_data = self._fetch_segment_with_fallback(current_map_url)
										map_signature = _hls_content_signature(init_data)
										if map_signature != last_map_signature:
											output_file.write(init_data)
											output_file.flush()
											last_map_signature = map_signature
											log.info(
												"FreeRadio Recorder: wrote new fMP4 init segment from %s",
												current_map_url,
											)
										else:
											log.debug(
												"FreeRadio Recorder: ignored unchanged fMP4 init "
												"segment with refreshed URL"
											)
										last_map_url = current_map_url
									except Exception as e:
										log.warning("FreeRadio Recorder: failed to fetch new init segment: %s", e)

							if output_file:
								output_file.write(data)
								output_file.flush()
							
							seen_segments.mark_written(segment_identity)
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
		# Use primary UA for playlist resolution.
		req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT_PRIMARY})
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


def _is_active_schedule_day(value, active_days):
	"""Return whether *value* falls on one of the configured weekdays."""
	return not active_days or value.weekday() in active_days


def _next_active_start(start, active_days):
	"""Return the first matching wall-clock occurrence after *start*."""
	candidate = start + datetime.timedelta(days=1)
	for _ in range(7):
		if _is_active_schedule_day(candidate, active_days):
			return candidate
		candidate += datetime.timedelta(days=1)
	return None


def _normalise_recurring_occurrence(start, duration_minutes, active_days, now, max_days=3660):
	"""Return the occurrence that should be pending at *now*.

	The returned start is either the currently active occurrence or the first
	future occurrence on an allowed weekday.  It is derived from the schedule's
	wall-clock time rather than its persisted date, which also repairs dates
	that older FreeRadio versions incorrectly moved a full week ahead.

	The second return value counts fully missed occurrences between the stored
	start and the returned start.  Legacy fixed-count schedules use that value
	to preserve their occurrence limit.
	"""
	active_days = active_days or []
	valid_days = {day for day in active_days if isinstance(day, int) and 0 <= day <= 6}
	if active_days and not valid_days:
		return None, 0
	days = valid_days if active_days else set()
	duration = datetime.timedelta(minutes=duration_minutes)
	candidate = now.replace(
		hour=start.hour,
		minute=start.minute,
		second=start.second,
		microsecond=start.microsecond,
	)
	if not _is_active_schedule_day(candidate, days) or now >= candidate + duration:
		if candidate <= now:
			candidate += datetime.timedelta(days=1)
		for _ in range(7):
			if _is_active_schedule_day(candidate, days):
				break
			candidate += datetime.timedelta(days=1)
		else:
			return None, 0

	skipped = 0
	cursor = start
	for _ in range(max_days):
		if cursor >= candidate:
			break
		if _is_active_schedule_day(cursor, days) and cursor + duration <= now:
			skipped += 1
		cursor += datetime.timedelta(days=1)
	else:
		return None, skipped
	return candidate, skipped


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
	             record_only=False,
	             recurrence="once", active_days=None,
	             max_occurrences=0, occurrences_done=0,
	             output_folder=None):
		self.station           = station
		self.start_time        = start_time
		self.duration_minutes  = duration_minutes
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
		# Transient crash/sleep-recovery field — never persisted.  When set,
		# the scheduler records only until the original end of this occurrence
		# instead of starting the full duration late.
		self.catchup_duration_seconds = None

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

		Walks forward day-by-day starting from the day right after
		start_time, stopping at the first day that is in active_days.
		An empty/None active_days means every day is active, per this
		class's docstring, so it stops at the very next calendar day.

		This must NOT jump a full week ahead before checking active_days:
		doing so meant an entry with every weekday marked active (meant
		to record daily) only ever re-fired once a week, on the original
		weekday, because "start_time + 1 week" always already satisfies
		"any day is active" - every day in between (e.g. every day but
		the original weekday) was silently skipped.

		Returns a new datetime or None when no valid day is found within
		the next 7 days.
		"""
		return _next_active_start(self.start_time, self.active_days)

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
		temp_path = "%s.%s.tmp" % (path, uuid.uuid4().hex)
		try:
			with open(temp_path, "w", encoding="utf-8") as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
			os.replace(temp_path, path)
		finally:
			if os.path.exists(temp_path):
				os.remove(temp_path)
	except Exception as e:
		log.warning("FreeRadio Recorder: could not save schedules: %s", e)


def _roll_forward_occurrence(start, active_days, now, max_steps=520):
	"""Advance *start* occurrence-by-occurrence until it is after *now*.

	Kept as a small compatibility helper for callers that only care about
	start times.  Schedule recovery itself uses
	``_normalise_recurring_occurrence`` so an occurrence whose window is
	currently open can be resumed rather than skipped.
	"""
	candidate = start
	steps = 0
	while candidate <= now and steps < max_steps:
		candidate = _next_active_start(candidate, active_days)
		if candidate is None:
			return None, steps
		steps += 1
	if candidate <= now:
		return None, steps
	return candidate, steps


def _load_schedules(now=None):
	"""Load, recover and migrate scheduled recordings from JSON.

	Recurring entries are normalised to the currently active occurrence or
	the first future occurrence on an allowed weekday.  This repairs dates
	persisted by older builds that jumped a full week ahead.  If NVDA starts
	inside a recording window, only the remaining seconds are recorded.
	"""
	import json
	try:
		path = _schedules_path()
		if not os.path.isfile(path):
			return []
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
		now = now or datetime.datetime.now()
		result = []
		needs_save = False
		for item in data:
			try:
				start            = datetime.datetime.fromisoformat(item["start_time"])
				duration_minutes = item["duration_minutes"]
				recurrence       = item.get("recurrence", "once")
				active_days      = item.get("active_days", []) or []
				max_occurrences  = item.get("max_occurrences", 0)
				occurrences_done = item.get("occurrences_done", 0)
				output_folder    = item.get("output_folder", "")
				is_recurring     = recurrence in ("weekly", "indefinite")

				catchup_seconds = None
				original_start = start
				if is_recurring:
					start, skipped = _normalise_recurring_occurrence(
						start, duration_minutes, active_days, now,
					)
					if start is None:
						log.warning(
							"FreeRadio Recorder: could not find a valid occurrence for '%s'; dropping entry",
							item.get("station", {}).get("name", "?"),
						)
						needs_save = True
						continue
					if recurrence == "weekly":
						occurrences_done += skipped
						if max_occurrences > 0 and occurrences_done >= max_occurrences:
							needs_save = True
							continue
					if start != original_start:
						needs_save = True
						log.info(
							"FreeRadio Recorder: normalised recurring schedule '%s' to %s",
							item.get("station", {}).get("name", "?"),
							start.strftime("%d.%m.%Y %H:%M"),
						)
				elif start + datetime.timedelta(minutes=duration_minutes) <= now:
					# A one-shot entry whose complete window elapsed cannot be
					# recovered and should not remain in the persisted list.
					needs_save = True
					continue

				deadline = start + datetime.timedelta(minutes=duration_minutes)
				if start <= now < deadline:
					catchup_seconds = (deadline - now).total_seconds()
					log.info(
						"FreeRadio Recorder: recovering '%s' with %.1f seconds remaining",
						item.get("station", {}).get("name", "?"),
						catchup_seconds,
					)

				rec = ScheduledRecording(
					station          = item["station"],
					start_time       = start,
					duration_minutes = duration_minutes,
					record_only      = item.get("record_only", False),
					recurrence       = recurrence,
					active_days      = active_days,
					max_occurrences  = max_occurrences,
					occurrences_done = occurrences_done,
					output_folder    = output_folder,
				)
				rec.catchup_duration_seconds = catchup_seconds
				result.append(rec)
			except Exception as e:
				log.warning("FreeRadio Recorder: skipping bad schedule entry: %s", e)
		if needs_save:
			_save_schedules(result)
		return result
	except Exception as e:
		log.warning("FreeRadio Recorder: could not load schedules: %s", e)
		return []


class Recorder:
	"""Manages instant and scheduled recordings."""

	def __init__(self, dll_dir=None, volume=100, main_player=None,
	             recording_format="original", mp3_bitrate=128, ffmpeg_path=""):
		"""
		dll_dir: Path to the directory containing bass_host.py and bass/ subfolder.
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
		self._volume          = volume
		self._main_player     = main_player  # to avoid interrupting user
		self._recording_format = _normalise_recording_format(recording_format)
		self._mp3_bitrate      = _normalise_mp3_bitrate(mp3_bitrate)
		self._ffmpeg_path      = ffmpeg_path or _default_ffmpeg_path(dll_dir)
		self._active_scheduled = set()  # currently running scheduled recordings
		self._active_scheduled_lock = threading.Lock()
		# Guards every read-then-write of self._scheduled (list membership,
		# reassignment, append/sort). Without this, the scheduler loop's
		# once-a-second "self._scheduled = [r for r in self._scheduled if
		# not r.fired]" reassignment can race with _run_scheduled()'s
		# recurrence requeue append: if the reassignment's snapshot is taken
		# before the requeue's append lands on the (about to be orphaned)
		# old list object, the newly chained occurrence silently vanishes -
		# the first firing works, but the re-queued next one never gets a
		# chance to fire.
		self._scheduled_lock = threading.RLock()
		# Serialises complete snapshot-and-save operations.  Without this,
		# overlapping recordings can write the same JSON file concurrently.
		self._schedule_persist_lock = threading.Lock()
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
		with self._schedule_persist_lock:
			with self._active_scheduled_lock:
				active = list(self._active_scheduled)
			if extra_active:
				seen = {id(r) for r in active}
				for r in extra_active:
					if id(r) not in seen:
						active.append(r)
						seen.add(id(r))
			with self._scheduled_lock:
				pending = list(self._scheduled)
			_save_schedules(pending + active)

	def _overlaps(self, start, duration_minutes):
		"""Return plans that overlap with the given range."""
		end = start + datetime.timedelta(minutes=duration_minutes)
		result = []
		with self._scheduled_lock:
			schedules = list(self._scheduled)
		for rec in schedules:
			if rec.fired:
				continue
			rec_end = rec.start_time + datetime.timedelta(minutes=rec.duration_minutes)
			if start < rec_end and end > rec.start_time:
				result.append(rec)
		return result

	def start(self, player, station_name, timeshift_buffer=None):
		"""Start instant recording. Playback keeps going; Python writes the stream
		via its own independent connection.

		timeshift_buffer is no longer used to tail the main player's capture
		(see history below) - kept as a parameter for call-site compatibility
		only, so a recording is never affected by anything that happens to
		the main player afterwards (station switch, pause/resume, stop).

		Previously, when the buffer was actively capturing this exact URL,
		the recording tailed it instead of opening a fresh connection - some
		stations serve a new ad to every brand-new connection, which a
		second connection made just for this recording would otherwise
		capture instead of the track actually airing. That optimisation
		tied the recording's lifetime to RadioPlayer's single shared
		_timeshift_buffer: switching station (or a long-pause resume) stops
		and restarts that same buffer object for the new URL, silently
		cutting off a recording that was tailing it. Recordings must
		survive playback changes, so this now always opens its own
		connection instead.

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

		timeshift_buffer: see start() - no longer used to tail the buffer,
		kept only for call-site compatibility.

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
	                 record_only=False,
	                 recurrence="once", active_days=None,
	                 max_occurrences=0, output_folder=None):
		"""Schedule a recording.

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
			record_only=record_only,
			recurrence=recurrence,
			active_days=active_days or [],
			max_occurrences=max_occurrences,
			output_folder=output_folder,
		)
		with self._scheduled_lock:
			self._scheduled.append(rec)
			self._scheduled.sort(key=lambda r: r.start_time)
		self._persist_schedules()
		self._ensure_scheduler()
		return rec, conflict_names

	def remove_schedule(self, rec):
		removed = False
		with self._scheduled_lock:
			if rec in self._scheduled:
				self._scheduled.remove(rec)
				removed = True
		if removed:
			self._persist_schedules()

	def get_schedules(self):
		with self._scheduled_lock:
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
		while not self._stop_scheduler.is_set():
			self._scheduler_tick()
			self._stop_scheduler.wait(1.0)

	def _start_scheduled_worker(self, rec):
		threading.Thread(
			target=self._run_scheduled,
			args=(rec,),
			daemon=True,
		).start()

	def _scheduler_tick(self, now=None):
		"""Dispatch due entries and roll fully missed entries forward.

		A delayed tick can happen after Modern Standby.  If the original
		recording window is still open, the worker receives only the remaining
		seconds.  If the complete window elapsed, no misleading full-length
		recording is started late; recurring entries move to their next valid
		day and one-shot entries are removed.
		"""
		now = now or datetime.datetime.now()
		fired = []
		changed = False
		with self._scheduled_lock:
			pending = []
			for rec in self._scheduled:
				if rec.fired:
					changed = True
					continue
				if now < rec.start_time:
					pending.append(rec)
					continue

				remaining_seconds = (
					rec.start_time
					+ datetime.timedelta(minutes=rec.duration_minutes)
					- now
				).total_seconds()
				if remaining_seconds > 0:
					rec.fired = True
					rec.catchup_duration_seconds = remaining_seconds
					fired.append(rec)
					changed = True
					continue

				changed = True
				if not rec.is_recurring():
					log.warning(
						"FreeRadio Recorder: one-shot schedule for '%s' was missed while NVDA was suspended",
						rec.station.get("name", "?"),
					)
					continue

				new_start, skipped = _normalise_recurring_occurrence(
					rec.start_time,
					rec.duration_minutes,
					rec.active_days,
					now,
				)
				if rec.recurrence == "weekly":
					rec.occurrences_done += skipped
				if new_start is None or not rec.has_more_occurrences():
					log.warning(
						"FreeRadio Recorder: missed recurring schedule for '%s' has no future occurrence",
						rec.station.get("name", "?"),
					)
					continue
				rec.start_time = new_start
				rec.catchup_duration_seconds = None
				pending.append(rec)
				log.warning(
					"FreeRadio Recorder: missed occurrence for '%s'; next at %s",
					rec.station.get("name", "?"),
					new_start.strftime("%d.%m.%Y %H:%M"),
				)
			self._scheduled = pending

		if changed:
			self._persist_schedules(extra_active=fired)
		for rec in fired:
			self._start_scheduled_worker(rec)
		return fired

	def _run_scheduled(self, rec):
		power_request = _set_scheduled_recording_power_request(True)
		try:
			self._run_scheduled_body(rec)
		finally:
			if power_request:
				_set_scheduled_recording_power_request(False)

	def _run_scheduled_body(self, rec):
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

		run_seconds = rec.catchup_duration_seconds
		if run_seconds is None:
			run_seconds = rec.duration_minutes * 60
		deadline = time.time() + run_seconds
		while time.time() < deadline:
			if getattr(rec, "_force_stop", False):
				break
			time.sleep(min(1.0, deadline - time.time()))

		# Capture before _finalize_writer() stops the writer, so we know
		# whether it ever actually connected during the whole scheduled
		# window - a stream that only ever failed to connect (see
		# _StreamWriter._run's reconnect loop) produces no output file, and
		# without this check the recording is silently reported as
		# "finished" with nothing actually captured.
		ever_connected = writer.is_connected()
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

		if not ever_connected:
			log.error(
				"FreeRadio Recorder: scheduled recording never connected — %s (no file was written)",
				name,
			)
			if hasattr(self, "_notify_failed") and self._notify_failed:
				self._notify_failed(rec)
		else:
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
					record_only      = rec.record_only,
					recurrence       = rec.recurrence,
					active_days      = rec.active_days,
					max_occurrences  = rec.max_occurrences,
					occurrences_done = rec.occurrences_done,
					output_folder    = rec.output_folder,
				)
				# Locked so this append/sort/persist can never interleave
				# with the scheduler loop's per-second self._scheduled
				# reassignment (that race is what was silently dropping
				# the requeued next occurrence - see _scheduled_lock
				# comment in __init__).
				with self._scheduled_lock:
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
		with self._scheduled_lock:
			schedules = list(self._scheduled)
		for rec in schedules:
			if hasattr(rec, "_writer") and rec._writer:
				rec._writer.stop()
