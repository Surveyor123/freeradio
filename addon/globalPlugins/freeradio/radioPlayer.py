# -*- coding: utf-8 -*-
# FreeRadio - Radio Player
# Backend priority: BASS (subprocess) → VLC → WMP.

import ctypes
import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
import re
import random
import urllib.request
import socket
import atexit

from . import timeshift as _timeshift_mod

log = logging.getLogger()

_WATCHDOG_INTERVAL = 5
_WATCHDOG_BACKOFF = [5, 10, 20, 30, 30, 30]

_ICY_INTERVAL = 30
_ICY_TIMEOUT = 10

_BASS_ATTRIB_VOL = 2
_BASS_TAG_META = 5
_BASS_CONFIG_NET_TIMEOUT = 11
_BASS_CONFIG_NET_HTTPS_FLAG = 71
_BASS_CONFIG_NET_SSL = 73
_BASS_CONFIG_NET_SSL_VERIFY = 74
_BASS_CONFIG_NET_PLAYLIST = 21
_BASS_CONFIG_NET_PREBUF = 15
_BASS_CONFIG_NET_READTIMEOUT = 37

# Device / output routing
_BASS_DEVICE_DEFAULT  = -1   # system default output

# Seconds of rolling capture kept when the user has NOT enabled the
# user-facing rewind feature. The time-shift buffer's capture connection is
# now kept running at all times (not just when rewind is enabled) because
# music recognition and recording both tail it instead of opening their own
# fresh connection - some stations serve a new ad to every brand-new
# connection, and reusing this already-open one avoids re-triggering that.
# When rewind IS enabled, TimeShiftBuffer.CAPACITY_SECONDS (10 min) is used
# instead so the existing rewind window is unaffected.
_LIGHT_BUFFER_SECONDS = 45

# Station tuning transition effect — plays a short local sound effect
# (tuner.mp3, bundled alongside this file) while connecting to a new
# station, instead of a numeric crossfade. BASS backend only; see
# RadioPlayer.set_tuning_effect_enabled().
_TUNER_MP3_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tuner.mp3")
_TUNER_POLL_INTERVAL = 0.25  # seconds between end-of-clip checks while looping

# Cached duration of tuner.mp3, in seconds, discovered the first time it is
# played (via timeshift_status() right after opening). Used on subsequent
# tuning transitions to start playback from a random position instead of
# always from the beginning. None until first discovered.
_TUNER_LENGTH_SECONDS = None

_BASS_ERROR_SSL	  = 41
_BASS_ERROR_FILEFORM = 40
_BASS_ERROR_TIMEOUT  = 38
_BASS_ERROR_NOTAVAIL = 37
_BASS_ERROR_ALREADY  = 8


_VLC_PATHS = [
	r"C:\Program Files\VideoLAN\VLC\vlc.exe",
	r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
]

_POTPLAYER_PATHS = [
	r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
	r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini.exe",
	r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini.exe",
	r"C:\Program Files\PotPlayer\PotPlayerMini64.exe",
	r"C:\Program Files\PotPlayer\PotPlayerMini.exe",
]


def _find_vlc():
	for path in _VLC_PATHS:
		if os.path.isfile(path):
			return path
	userprofile = os.environ.get("USERPROFILE", "")
	if userprofile:
		for candidate in [
			os.path.join(userprofile, "vlc", "vlc.exe"),
			os.path.join(userprofile, "AppData", "Local", "Programs", "VLC", "vlc.exe"),
			os.path.join(userprofile, "AppData", "Local", "VLC", "vlc.exe"),
		]:
			if os.path.isfile(candidate):
				return candidate
	try:
		result = subprocess.run(
			["where", "vlc.exe"],
			capture_output=True, text=True,
			creationflags=subprocess.CREATE_NO_WINDOW,
		)
		if result.returncode == 0:
			first = result.stdout.strip().splitlines()[0].strip()
			if os.path.isfile(first):
				return first
	except Exception:
		pass
	return None


def _find_potplayer():
	for path in _POTPLAYER_PATHS:
		if os.path.isfile(path):
			return path
	userprofile = os.environ.get("USERPROFILE", "")
	if userprofile:
		for candidate in [
			os.path.join(userprofile, "AppData", "Local", "DAUM", "PotPlayer", "PotPlayerMini64.exe"),
			os.path.join(userprofile, "AppData", "Local", "DAUM", "PotPlayer", "PotPlayerMini.exe"),
		]:
			if os.path.isfile(candidate):
				return candidate
	try:
		result = subprocess.run(
			["where", "PotPlayerMini64.exe"],
			capture_output=True, text=True,
			creationflags=subprocess.CREATE_NO_WINDOW,
		)
		if result.returncode == 0:
			first = result.stdout.strip().splitlines()[0].strip()
			if os.path.isfile(first):
				return first
	except Exception:
		pass
	return None



def _read_icy_title(url):
	try:
		req = urllib.request.Request(
			url,
			headers={"User-Agent": "FreeRadio-NVDA/1.0", "Icy-MetaData": "1"},
		)
		with urllib.request.urlopen(req, timeout=_ICY_TIMEOUT) as resp:
			metaint_str = resp.headers.get("icy-metaint", "")
			if not metaint_str:
				return None
			metaint = int(metaint_str)
			resp.read(metaint)
			meta_len_byte = resp.read(1)
			if not meta_len_byte:
				return None
			meta_len = meta_len_byte[0] * 16
			if meta_len == 0:
				return None
			meta_raw = resp.read(meta_len).decode("utf-8", errors="ignore")
			# NOTE: match up to the closing "';" (not just the next "'"),
			# since the title itself may contain an apostrophe (e.g.
			# "Don't Stop Believin'"). ICY metadata always terminates each
			# key='value' pair with "';", so this is a safe delimiter.
			m = re.search(r"StreamTitle='(.*?)';", meta_raw)
			if m:
				title = m.group(1).strip()
				return title if title else None
	except Exception:
		pass
	return None



_VBS = """\
On Error Resume Next
Dim wmp
Set wmp = CreateObject("WMPlayer.OCX")
If Err.Number <> 0 Then
	WScript.Quit 1
End If
On Error GoTo 0
wmp.settings.volume = {volume}
wmp.settings.autoStart = True
wmp.URL = "{url}"
wmp.controls.play()

Dim stoppedCount
stoppedCount = 0

Do While True
	WScript.Sleep 3000
	Dim state
	state = wmp.playState
	If state = 1 Or state = 10 Then
		stoppedCount = stoppedCount + 1
		If stoppedCount >= 2 Then
			wmp.controls.stop
			WScript.Sleep 1000
			wmp.URL = "{url}"
			wmp.controls.play
			stoppedCount = 0
		End If
	Else
		stoppedCount = 0
	End If
Loop
"""





def _resolve_playlist_url(url, timeout=8):
	"""
	If url points to a playlist (M3U, PLS, XSPF, ASX) or returns a redirect,
	return the first actual stream URL found inside it.
	Returns the original url if nothing better is found.
	"""
	try:
		import urllib.request as _req
		req = _req.Request(
			url,
			headers={"User-Agent": "FreeRadio-NVDA/1.0",
					 "Icy-MetaData": "1"},
		)
		with _req.urlopen(req, timeout=timeout) as resp:
			final_url = resp.url if hasattr(resp, "url") else url
			ct = (resp.headers.get("content-type") or "").lower().split(";")[0].strip()
			data = resp.read(8192).decode("utf-8", "ignore")

		audio_types = ("audio/", "application/ogg", "video/")
		if any(ct.startswith(t) for t in audio_types):
			return final_url if final_url != url else url

		from urllib.parse import urljoin as _urljoin
		base_url = final_url

		if ct in ("audio/x-mpegurl", "application/x-mpegurl",
				  "audio/mpegurl", "application/vnd.apple.mpegurl") or \
				url.lower().endswith((".m3u", ".m3u8")):
			for line in data.splitlines():
				line = line.strip()
				if line and not line.startswith("#"):
					return _urljoin(base_url, line)

		if ct == "audio/x-scpls" or url.lower().endswith(".pls"):
			for line in data.splitlines():
				if line.lower().startswith("file1="):
					return _urljoin(base_url, line.split("=", 1)[1].strip())

		if ct in ("video/x-ms-asf", "audio/x-ms-wax", "audio/x-ms-wmx") or \
				any(url.lower().endswith(e) for e in (".asx", ".wmx", ".wax")):
			import re as _re
			m = _re.search(r"href\s*=\s*[\"']([^\"']+)[\"']", data, _re.IGNORECASE)
			if m:
				return _urljoin(base_url, m.group(1))

	except Exception:
		pass

	return url



class _BassSubprocessEngine:
	"""
	Runs bass_host.py as a child process so that BASS audio appears as a
	separate entry in the Windows volume mixer — independent from nvda.exe.

	Communication: newline-delimited JSON on stdin/stdout.
	"""

	def __init__(self, dll_dir, device_index=-1):
		self._dll_dir  = dll_dir
		self._device_index = device_index  # -1 = system default
		self._proc	 = None
		self._lock	 = threading.RLock()
		self._ready	= False
		self._icy_title = None
		# The outer layer can assign a connect notification callback.
		self.on_slow_connect = None
		self.on_meta	   = None
		# Called if there is no response within 5 seconds; UI may show 'connecting'.
		self.on_connecting = None
		# Called when bass_host sends a stall event.
		self.on_stall	  = None
		self._reader_thread = None
		self._stop_reader   = threading.Event()
		self._play_seq	 = 0
		self._pending_play = None   # (seq, event, [result])
		self._current_play_seq = None  # Track currently active play request
		atexit.register(self._cleanup)

	def _find_python(self):
		"""
		Find a non-elevated pythonw.exe to run bass_host.py as a normal
		(non-admin) subprocess so Windows does not trigger UAC elevation.

		Search order:
		1. Bundled embed Python (python/ folder of the plugin) — matching the architecture
		2. pythonw.exe / python.exe next to bass_host.py
		3. pythonw.exe / python.exe next to sys.executable
		4. sys.executable itself if it is literally python/pythonw
		5. PATH fallback
		"""
		candidates = []

		# 1. Embed Python embedded in the plugin — folder matching the architecture
		is64 = ctypes.sizeof(ctypes.c_voidp) == 8
		arch_dir = "x64" if is64 else "x86"
		bundled_dir = os.path.join(self._dll_dir, "python", arch_dir)
		for name in ("pythonw.exe", "python.exe"):
			candidates.append(os.path.join(bundled_dir, name))

		# 2. Alongside the script itself
		for name in ("pythonw.exe", "python.exe"):
			candidates.append(os.path.join(self._dll_dir, name))

		# 3. Alongside whatever interpreter is running NVDA
		exe_dir = os.path.dirname(sys.executable)
		for name in ("pythonw.exe", "python.exe"):
			candidates.append(os.path.join(exe_dir, name))

		# 4. sys.executable itself if it is literally python/pythonw
		base = os.path.basename(sys.executable).lower()
		if base in ("python.exe", "pythonw.exe"):
			candidates.append(sys.executable)

		for path in candidates:
			if os.path.isfile(path):
				return path

		# 5. PATH fallback
		for name in ("pythonw", "python"):
			try:
				result = subprocess.run(
					["where", name],
					capture_output=True, text=True,
					creationflags=subprocess.CREATE_NO_WINDOW,
				)
				if result.returncode == 0:
					first = result.stdout.strip().splitlines()[0].strip()
					if os.path.isfile(first):
						return first
			except Exception:
				pass

		return None

	def load(self):
		host_script = os.path.join(self._dll_dir, "bass_host.py")
		if not os.path.isfile(host_script):
			return False

		python = self._find_python()
		if not python:
			return False

		si = subprocess.STARTUPINFO()
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		si.wShowWindow = 0

		try:
			cmd = [python, host_script]
			if self._device_index != -1:
				cmd += ["--device", str(self._device_index)]
			proc = subprocess.Popen(
				cmd,
				stdin=subprocess.PIPE,
				stdout=subprocess.PIPE,
				stderr=subprocess.DEVNULL,
				startupinfo=si,
				creationflags=subprocess.CREATE_NO_WINDOW,
				encoding="utf-8",
				bufsize=1,
			)
		except Exception:
			return False

		with self._lock:
			self._proc = proc

		try:
			line = proc.stdout.readline()
			resp = json.loads(line)
			if not resp.get("ok"):
				self._kill()
				return False
		except Exception:
			self._kill()
			return False

		self._ready = True
		self._stop_reader.clear()
		self._reader_thread = threading.Thread(
			target=self._read_loop, daemon=True, name="FreeRadio-BassReader")
		self._reader_thread.start()

		return True

	def ready(self):
		return self._ready and self._proc is not None and self._proc.poll() is None

	def unload(self):
		self._stop_reader.set()
		self._send({"cmd": "quit"})
		time.sleep(0.3)
		self._kill()
		self._ready = False

	def _kill(self):
		with self._lock:
			proc = self._proc
			self._proc = None
		if proc:
			try:
				proc.terminate()
				proc.wait(timeout=2)
			except Exception:
				try:
					proc.kill()
				except Exception:
					pass

	def _cleanup(self):
		self.unload()

	def _send(self, obj):
		with self._lock:
			proc = self._proc
		if proc and proc.poll() is None:
			try:
				proc.stdin.write(json.dumps(obj) + "\n")
				proc.stdin.flush()
			except Exception:
				pass

	def list_devices(self, timeout=5.0):
		"""Return list of (index, name) tuples for all BASS output devices.
		Sends list_devices command to the host process and waits for reply.
		Returns [] on failure.
		"""
		if not self.ready():
			return []
		evt	= threading.Event()
		result = [None]

		def _wait_for_reply():
			# Temporarily hook the read loop result via a one-shot flag
			deadline = time.time() + timeout
			self._send({"cmd": "list_devices"})
			while time.time() < deadline:
				time.sleep(0.05)
				if result[0] is not None:
					break

		# We piggyback on the existing _read_loop; add a side-channel listener
		old_on_devices = getattr(self, "_on_devices_reply", None)

		def _on_reply(devices):
			result[0] = devices
			evt.set()

		self._on_devices_reply = _on_reply
		self._send({"cmd": "list_devices"})
		evt.wait(timeout=timeout)
		self._on_devices_reply = old_on_devices
		return result[0] if result[0] is not None else []

	def _cancel_current_play(self):
		"""Cancel any ongoing play request and send stop to host."""
		with self._lock:
			if self._current_play_seq is not None:
				# Send stop to host to ensure any pending stream is cancelled
				self._send({"cmd": "stop"})
				self._current_play_seq = None
			
			# Also clear any pending response
			if self._pending_play:
				seq, evt, result_slot = self._pending_play
				result_slot[0] = False
				evt.set()
				self._pending_play = None

	def play(self, url, volume_0_1=1.0, seekable=False):
		"""Send play command and block until the host confirms success/failure.
		
		If a previous play is still pending, it is cancelled first.
		seekable=True asks the host to open the URL without BASS_STREAM_BLOCK
		so seek_relative() actually works (podcasts); live radio should
		leave this False.
		"""
		if not self.ready():
			return False

		# Cancel any ongoing play request
		self._cancel_current_play()

		# Assign a sequence number so _read_loop can route the reply back.
		with self._lock:
			self._play_seq += 1
			seq = self._play_seq
			self._current_play_seq = seq
			evt = threading.Event()
			self._pending_play = (seq, evt, [None])   # [result_slot]
			result_slot = self._pending_play[2]

		self._send({"cmd": "play", "url": url, "volume": volume_0_1, "seq": seq, "seekable": seekable})

		# If there is no response in the first 5 seconds, give the "connecting" signal, then wait another 25 seconds.
		got_reply = evt.wait(timeout=5)
		if not got_reply:
			if self.on_connecting:
				try:
					self.on_connecting(url)
				except Exception:
					pass
			got_reply = evt.wait(timeout=25)

		with self._lock:
			# Clear pending regardless
			if self._pending_play and self._pending_play[0] == seq:
				self._pending_play = None
			if self._current_play_seq == seq:
				self._current_play_seq = None

		if not got_reply:
			# The host may still be in BASS_StreamCreateURL.
			# If we do not send stop, it will start sound when completed.
			self._send({"cmd": "stop"})
			return False

		success = result_slot[0]
		return bool(success)

	def stop(self):
		self._cancel_current_play()
		self._send({"cmd": "stop"})

	def pause(self):
		self._send({"cmd": "pause"})

	def resume(self):
		self._send({"cmd": "resume"})

	def set_volume(self, volume_0_1):
		# 2.0 upper limit matches bass_host.py; negative values are not allowed.
		self._send({"cmd": "volume", "value": max(0.0, min(2.0, volume_0_1))})

	# -- Time-shift (local buffer file) playback -------------------------

	def play_timeshift_file(self, path, volume_0_1=1.0, start_seconds=0.0, timeout=5.0):
		"""Open a local time-shift buffer file for seekable playback.
		Blocks until the host confirms success/failure. Returns True/False.
		"""
		if not self.ready():
			return False
		evt	= threading.Event()
		result = [False]

		old_on_reply = getattr(self, "_on_generic_reply", None)

		def _on_reply(ok):
			result[0] = ok
			evt.set()

		self._on_generic_reply = _on_reply
		self._send({
			"cmd": "timeshift_play",
			"path": path,
			"volume": volume_0_1,
			"start_seconds": start_seconds,
		})
		evt.wait(timeout=timeout)
		self._on_generic_reply = old_on_reply
		return result[0]

	def timeshift_seek(self, delta_seconds, timeout=3.0):
		"""Seek relative to the current position in the open time-shift
		file stream. Returns (ok, position_seconds, length_seconds)."""
		if not self.ready():
			return False, 0.0, 0.0
		evt	= threading.Event()
		result = [(False, 0.0, 0.0)]

		old_on_reply = getattr(self, "_on_timeshift_reply", None)

		def _on_reply(ok, position_seconds, length_seconds):
			result[0] = (ok, position_seconds, length_seconds)
			evt.set()

		self._on_timeshift_reply = _on_reply
		self._send({"cmd": "timeshift_seek", "delta_seconds": delta_seconds})
		evt.wait(timeout=timeout)
		self._on_timeshift_reply = old_on_reply
		return result[0]

	def timeshift_status(self, timeout=3.0):
		"""Return (position_seconds, length_seconds) for the currently open
		time-shift file stream, or (0.0, 0.0) on timeout/failure."""
		if not self.ready():
			return 0.0, 0.0
		evt	= threading.Event()
		result = [(0.0, 0.0)]

		old_on_reply = getattr(self, "_on_timeshift_status_reply", None)

		def _on_reply(position_seconds, length_seconds):
			result[0] = (position_seconds, length_seconds)
			evt.set()

		self._on_timeshift_status_reply = _on_reply
		self._send({"cmd": "timeshift_status"})
		evt.wait(timeout=timeout)
		self._on_timeshift_status_reply = old_on_reply
		return result[0]

	def set_bass_boost(self, boost_0_1):
		"""Adjust the bass boost level (0.0 = off, 1.0 = max +12 dB)."""
		self._send({"cmd": "bass_boost", "value": max(0.0, min(1.0, float(boost_0_1)))})

	def set_playback_rate(self, rate, timeout=3.0):
		"""Set pitch-preserving playback speed (podcasts only).

		rate: 1.0 = normal, 1.1 = 10% faster, 0.9 = 10% slower (clamped to
		0.5-3.0 on the host side). Returns (applied, actual_rate, reason) —
		applied is False when bass_fx.dll isn't available or the current
		stream can't be tempo-adjusted; the rate is still remembered on the
		host for the next tempo-capable stream either way.
		"""
		if not self.ready():
			return False, rate, "not_ready"
		evt = threading.Event()
		result = [(False, rate, "timeout")]

		old_on_reply = getattr(self, "_on_playback_rate_reply", None)

		def _on_reply(applied, actual_rate, reason):
			result[0] = (applied, actual_rate, reason)
			evt.set()

		self._on_playback_rate_reply = _on_reply
		self._send({"cmd": "set_playback_rate", "rate": float(rate)})
		evt.wait(timeout=timeout)
		self._on_playback_rate_reply = old_on_reply
		return result[0]

	def set_fx(self, fx_name):
		"""Adjust DirectX 8 effect.

		fx_name: "none" | "chorus" | "compressor" | "distortion" |
				 "echo" | "flanger" | "gargle" | "reverb" |
				 "eq_bass" | "eq_treble" | "eq_vocal"
		It is applied instantly on the active stream.
		"""
		self._send({"cmd": "set_fx", "fx": fx_name or "none"})

	def set_eq_gain(self, band, gain_db):
		"""Set the ParamEQ gain for one EQ band in dB (-15..+15).

		band:	"eq_bass" | "eq_treble" | "eq_vocal"
		gain_db: dB value; applied immediately if the band effect is active.
		"""
		self._send({"cmd": "set_eq_gain", "band": band,
					"gain_db": max(-15.0, min(15.0, float(gain_db)))})

	def get_icy_title(self):
		return self._icy_title

	def _read_loop(self):
		with self._lock:
			proc = self._proc
		if not proc:
			return
		try:
			for raw in proc.stdout:
				if self._stop_reader.is_set():
					break
				raw = raw.strip()
				if not raw:
					continue
				try:
					msg = json.loads(raw)
				except Exception:
					continue

				# ICY metadata event
				if msg.get("event") and msg.get("type") == "meta":
					title = msg.get("title", "")
					if title:
						self._icy_title = title
						if self.on_meta:
							try:
								self.on_meta(title)
							except Exception:
								pass
					continue

				# Stall event — BASS stream interrupted, reconnect
				if msg.get("event") and msg.get("type") == "stall":
					cb = getattr(self, "on_stall", None)
					if cb:
						try:
							cb()
						except Exception:
							pass
					continue

				# list_devices reply
				if msg.get("ok") and "devices" in msg:
					cb = getattr(self, "_on_devices_reply", None)
					if cb:
						try:
							cb(msg["devices"])
						except Exception:
							pass
					continue

				# Time-shift replies — routed unambiguously via the "cmd" echo
				# field the host attaches to these specific responses.
				reply_cmd = msg.get("cmd")
				if reply_cmd == "timeshift_play":
					cb = getattr(self, "_on_generic_reply", None)
					if cb:
						try:
							cb(bool(msg.get("ok")))
						except Exception:
							pass
					continue
				if reply_cmd == "timeshift_seek":
					cb = getattr(self, "_on_timeshift_reply", None)
					if cb:
						try:
							cb(msg.get("seeked", False),
							   msg.get("position_seconds", 0.0),
							   msg.get("length_seconds", 0.0))
						except Exception:
							pass
					continue
				if reply_cmd == "timeshift_status":
					cb = getattr(self, "_on_timeshift_status_reply", None)
					if cb:
						try:
							cb(msg.get("position_seconds", 0.0), msg.get("length_seconds", 0.0))
						except Exception:
							pass
					continue
				if reply_cmd == "set_playback_rate":
					cb = getattr(self, "_on_playback_rate_reply", None)
					if cb:
						try:
							cb(bool(msg.get("rate_applied", False)),
							   msg.get("rate", 1.0), msg.get("reason", ""))
						except Exception:
							pass
					continue

				# Play result — route to waiting play() call
				seq = msg.get("seq")
				if seq is not None:
					with self._lock:
						pending = self._pending_play
						current_seq = self._current_play_seq
					# Only accept response if it matches the current active play
					if pending and pending[0] == seq and current_seq == seq:
						pending[2][0] = msg.get("ok", False)
						pending[1].set()
					continue

		except Exception:
			pass
		finally:
			# Unblock any waiting play() call if the process died
			with self._lock:
				pending = self._pending_play
				self._pending_play = None
				self._current_play_seq = None
			if pending:
				pending[1].set()


# _BassEngine is the old in-process class — we keep the name but now it
# delegates to the subprocess engine.  RadioPlayer only uses the public API
# (load, ready, play, stop, pause, resume, set_volume, get_icy_title, unload,
# on_meta), which _BassSubprocessEngine fully satisfies.
class _BassEngine(_BassSubprocessEngine):
	"""Subprocess-based BASS engine (previously in-process)."""

	def __init__(self, dll_dir, output_device=_BASS_DEVICE_DEFAULT):
		# output_device: -1 = system default, positive int = specific device index
		super().__init__(dll_dir, device_index=output_device)



class RadioPlayer:
	"""
	Unified radio player.
	Backend priority: BASS (in-process ctypes) → VLC → WMP.
	BASS is used for ALL streams by default, only falls back on failure.
	"""

	BACKEND_BASS	  = "bass"
	BACKEND_VLC	   = "vlc"
	BACKEND_POTPLAYER = "potplayer"
	BACKEND_WMP	   = "wmp"
	BACKEND_NONE	  = "none"

	def __init__(self, vlc_path=None, wmp_path=None, potplayer_path=None,
				 output_device=_BASS_DEVICE_DEFAULT, config_path=None,
				 disable_bass=False):
		self._current_url = None
		self._current_url_resolved = None
		self._current_name = ""
		self._current_station = {}
		self._is_playing = False
		self._volume = 100
		self._bass_boost = 0.0   # bass boost level: 0.0–1.0
		self._playback_rate = 1.0  # pitch-preserving speed for podcasts: 1.0 = normal
		self._audio_fx   = "none"  # active DirectX 8 effect name
		self._intentional_stop = False
		self._play_lock = threading.RLock()  # Prevent concurrent play operations
		self._play_gen  = 0		  # Incremented on every play(); bg threads check this

		self._vlc_path		= vlc_path if vlc_path and os.path.isfile(vlc_path) else _find_vlc()
		self._wmp_path		= wmp_path if wmp_path and os.path.isfile(wmp_path) else None
		self._potplayer_path  = potplayer_path if potplayer_path and os.path.isfile(potplayer_path) else _find_potplayer()

		self._backend = self.BACKEND_NONE
		self._proc = None
		self._vbs_path = None

		self._disable_bass = disable_bass
		self._audio_device_refresh_mode = "reliable"

		if not disable_bass:
			dll_dir = os.path.dirname(os.path.abspath(__file__))
			self._bass_engine = _BassEngine(dll_dir, output_device=output_device)
			self._bass_engine.load()
			if self._bass_engine.ready():
				self._bass_engine.on_meta = self._on_bass_meta
				self._bass_engine.on_connecting = self._on_bass_connecting
				self._bass_engine.on_stall = self._on_bass_stall
		else:
			self._bass_engine = None

		self._icy_title = None
		self._icy_stop = threading.Event()
		self._icy_thread = None

		self._output_device_index = output_device  # User-selected device index
		self.on_device_lost = None  # Callback: called when the device is lost (device_index)
		# Callback: called with (url) right after a podcast's position is
		# saved due to a pause or the episode finishing - NOT the periodic
		# 15s autosave. Lets the UI refresh that one episode row's
		# [Listened]/duration display without a continuously-ticking timer.
		# May run on a background thread (called from _on_bass_stall).
		self.on_podcast_progress_saved = None
		# Callback: called with (station) only when a podcast/GETEM item
		# actually reaches its end (never on a plain pause) - see the
		# is_podcast branch of _on_bass_stall(). Lets the UI auto-advance to
		# the next episode/chapter. Deliberately separate from
		# on_podcast_progress_saved, which also fires on pause and only
		# gets a bare url, not enough to tell "finished" from "paused".
		# May run on a background thread (called from _on_bass_stall); the
		# handler is responsible for marshalling onto the UI thread.
		self.on_podcast_finished = None

		# Crossfade
		self._crossfade_duration = 0.0   # seconds; 0.0 = disabled
		self._crossfade_engine   = None  # old _BassEngine being faded out

		# Station tuning transition effect (alternative to numeric crossfade,
		# mutually exclusive with it — see set_tuning_effect_enabled()).
		self._tuning_effect_enabled = False
		self._tuning_engine = None  # old _BassEngine currently playing tuner.mp3
		self._tuning_stop   = None  # threading.Event signalling the loop-watcher to stop

		self._watchdog_stop = threading.Event()
		self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
		self._watchdog_thread.start()

		# Podcast resume positions: {url: {"position": secs, "name": str,
		# "updated": iso timestamp}}, persisted to disk so an episode
		# picks up where it left off next time it's played (podcasts are
		# always seekable - see the "seekable" play() flag - so resuming
		# is just a seek after playback starts).
		# Stored under the NVDA user config directory rather than next to
		# this file - the addon folder gets wiped and replaced on every
		# update, which would silently lose all saved positions.
		self._podcast_positions_path = self._get_podcast_positions_path()
		self._podcast_positions_lock = threading.Lock()
		self._podcast_positions = self._load_podcast_positions()
		self._podcast_autosave_stop = threading.Event()
		self._podcast_autosave_thread = threading.Thread(
			target=self._podcast_autosave_loop, daemon=True,
			name="FreeRadio-podcast-autosave")
		self._podcast_autosave_thread.start()

		# Time-shift buffer (rewind/fast-forward for live radio). Disabled by
		# default — the caller enables it via set_timeshift_enabled(True)
		# once the user opts in from the settings panel. Only supported on
		# the BASS backend.
		self._timeshift_enabled = False
		self._timeshift_active  = False   # True while time-shifted (buffered) playback is active
		# User-configurable rewind buffer capacity in seconds (default 10
		# min; up to 5 hours via Settings). Only applies once the
		# time-shift feature itself is enabled — the always-on lightweight
		# buffer stays fixed at _LIGHT_BUFFER_SECONDS regardless.
		self._timeshift_capacity_seconds = 600
		self._timeshift_buffer  = _timeshift_mod.TimeShiftBuffer()
		# _play_gen value for which _timeshift_buffer currently holds the
		# right station's capture session. _timeshift_active is reset to
		# False as soon as _bg_launch starts (see below), well before the
		# buffer itself is actually stopped/restarted for the new stream -
		# so without this, a rewind press landing in that gap would treat
		# the *previous* station's still-live buffer file as "ready" and
		# start time-shift playback from it instead of correctly reporting
		# "not buffered yet". None until the first station has ever fully
		# swapped the buffer over.
		self._timeshift_buffer_gen = None
		# Serializes every "stop old capture / start new capture / assign
		# _timeshift_buffer_gen" sequence across the different code paths
		# that can trigger one (_bg_launch on station switch, the BASS
		# stall reconnect, and set_timeshift_enabled's _bg_start_capture).
		# Without this, two such sequences racing (e.g. a fast station
		# switch landing while set_timeshift_enabled's background thread is
		# still resolving the previous station's URL) could interleave
		# their stop()/start() calls and finish with the buffer capturing
		# one station while _timeshift_buffer_gen claims it belongs to a
		# different one - rewind_timeshift() would then refuse forever with
		# "no_buffer_yet" until something (station switch, feature toggle)
		# happened to reset it back into sync.
		self._timeshift_launch_lock = threading.Lock()

		if not disable_bass:
			self._device_monitor_thread = threading.Thread(target=self._device_monitor_loop, daemon=True)
			self._device_monitor_thread.start()



	def _on_bass_meta(self, title):
		self._icy_title = title

	def _on_bass_connecting(self, url):
		"""Called if BASS connection could not be established within 5s."""
		if self.on_slow_connect:
			try:
				self.on_slow_connect(url)
			except Exception:
				pass

	def _on_bass_stall(self):
		"""Called when bass_host.py sends a stall event."""
		if self._disable_bass:
			return
		if not self._is_playing or self._intentional_stop:
			return

		station = self._current_station
		is_podcast = bool(station and "podcast" in station.get("tags", ""))

		# If it's a podcast, reaching stall means the episode has ended.
		# Mark as listened and stop player instead of reconnecting/restarting.
		if is_podcast:
			log.info("FreeRadio: Podcast episode finished playing.")
			self._save_podcast_position_now(station, -1.0, -1.0)
			cb = self.on_podcast_progress_saved
			if cb:
				try:
					cb(station.get("url") or self._current_url)
				except Exception:
					pass
			finished_cb = self.on_podcast_finished
			if finished_cb:
				try:
					finished_cb(station)
				except Exception:
					pass
			self.stop()
			return

		# bass_host's stall watcher monitors whatever is on the single BASS
		# channel, live URL or the local time-shift .buf file alike, and
		# can't tell us which one stalled. A still-growing .buf file is
		# especially prone to tripping its buffer-empty/position-stuck
		# checks spuriously. If we're currently time-shifted, treat this
		# as that (not a dead live connection) and just fall back to live
		# the same clean way exit_timeshift_to_live() always does -
		# running the live-URL reconnect/backoff loop below instead would
		# silently tear down time-shift mode via _bg_launch's own reset,
		# then immediately race back into a fresh, still-too-small buffer
		# on the next rewind press, repeating indefinitely.
		if self._timeshift_active:
			log.warning("FreeRadio: BASS stall detected during time-shifted "
						"playback, returning to live")
			self.exit_timeshift_to_live()
			return

		url = self._current_url
		vol = self._volume
		if not url:
			return
		log.warning("FreeRadio: BASS stall detected, reconnecting: %s", url)
		# ... (rest of the method stays same)

		# Capture generation at the moment of stall so reconnect thread
		# can detect if a newer play() has already taken over.
		stall_gen = self._play_gen

		def _reconnect(captured_gen=stall_gen):
			if not self._is_playing or self._intentional_stop:
				return
			# First attempt is immediate — Icecast dropouts should reconnect
			# without delay. Subsequent retries back off progressively.
			for wait in (0, 5, 10, 20, 30):
				if not self._is_playing or self._intentional_stop:
					return
				# Abort if a newer play() already started
				if self._play_gen != captured_gen:
					return
				time.sleep(wait)
				if not self._is_playing or self._intentional_stop:
					return
				if self._play_gen != captured_gen:
					return  # User selected a different station
				if self._current_url != url:
					return
				log.info("FreeRadio: BASS stall reconnect attempt: %s", url)
				with self._play_lock:
					# Double-check generation under lock before bumping
					if self._play_gen != captured_gen:
						return
					self._play_gen += 1
					captured_gen = self._play_gen
				try:
					if self._launch_bass(url, vol):
						log.info("FreeRadio: BASS stall reconnect OK")
						# The time-shift capture connection is independent of
						# BASS playback and was never interrupted by this
						# stall, so the buffer is still valid for the current
						# station - only _play_gen advanced here, not the
						# buffer's own generation. Sync them so rewind_timeshift()
						# doesn't mistake this still-good buffer for a stale
						# one and refuse to rewind (see its gen check).
						if self._backend == self.BACKEND_BASS:
							with self._timeshift_launch_lock:
								if self._play_gen == captured_gen:
									self._timeshift_buffer_gen = captured_gen
						return
				except Exception as e:
					pass
			log.warning("FreeRadio: BASS stall reconnect exhausted")

			# BASS could not recover after repeated attempts. Previously this
			# just gave up here, leaving _is_playing True with no audio
			# actually playing (and possibly stale ICY metadata still
			# displayed). Fall back to the VLC/PotPlayer/WMP chain instead,
			# same as a normal BASS-unavailable startup would.
			if not self._is_playing or self._intentional_stop:
				return
			if self._play_gen != captured_gen:
				return
			with self._play_lock:
				if self._play_gen != captured_gen:
					return
				self._play_gen += 1
				fallback_gen = self._play_gen
			log.warning(
				"FreeRadio: falling back to VLC/PotPlayer/WMP after BASS "
				"exhaustion: %s", url)
			try:
				self._launch_non_bass_fallback(url, vol, fallback_gen)
			except Exception:
				log.warning(
					"FreeRadio: non-BASS fallback also failed", exc_info=True)

		threading.Thread(target=_reconnect, daemon=True,
						 name="FreeRadio-BassReconnect").start()


	def _watchdog_loop(self):
		attempt = 0
		last_check = time.time()
		while not self._watchdog_stop.is_set():
			for _ in range(_WATCHDOG_INTERVAL * 2):
				if self._watchdog_stop.is_set():
					return
				time.sleep(0.5)

			if not self._is_playing or self._intentional_stop:
				attempt = 0
				continue

			# The BASS backend is self-managing, the watchdog does not intervene.
			if self._backend in (self.BACKEND_BASS, self.BACKEND_NONE):
				attempt = 0
				continue

			proc = self._proc
			if proc is None:
				continue
				
			is_dead = proc.poll() is not None
			
			if not is_dead:
				attempt = 0
				last_check = time.time()
				continue
				
			# Waiting time for newly started process
			if time.time() - last_check < 5:
				continue

			wait = _WATCHDOG_BACKOFF[min(attempt, len(_WATCHDOG_BACKOFF) - 1)]
			for _ in range(wait * 2):
				if self._watchdog_stop.is_set() or self._intentional_stop:
					return
				time.sleep(0.5)

			if self._watchdog_stop.is_set() or self._intentional_stop:
				return

			if self._is_playing and self._current_url and not self._intentional_stop:
				with self._play_lock:
					self._play_gen += 1
					wdog_gen = self._play_gen
				try:
					self._launch(self._current_url, self._volume, gen=wdog_gen)
					last_check = time.time()
				except Exception:
					pass
				attempt += 1


	def _start_icy_thread(self, url):
		self._stop_icy_thread()
		self._icy_title = None
		self._icy_stop.clear()
		self._icy_thread = threading.Thread(target=self._icy_loop, args=(url,), daemon=True)
		self._icy_thread.start()

	def _stop_icy_thread(self):
		self._icy_stop.set()
		t = self._icy_thread
		self._icy_thread = None
		if t and t.is_alive():
			t.join(timeout=2)
		self._icy_stop.clear()

	def _icy_loop(self, url):
		while not self._icy_stop.is_set():
			title = _read_icy_title(url)
			if title and title != self._icy_title:
				self._icy_title = title
			for _ in range(_ICY_INTERVAL * 2):
				if self._icy_stop.is_set():
					return
				time.sleep(0.5)

	def get_icy_title(self):
		if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
			return self._bass_engine.get_icy_title()
		return self._icy_title

	def set_audio_device_refresh_mode(self, mode):
		"""Ustaw tryb odświeżania listy urządzeń BASS."""
		self._audio_device_refresh_mode = "fast" if mode == "fast" else "reliable"

	def use_fresh_audio_device_probe(self):
		return getattr(self, "_audio_device_refresh_mode", "reliable") != "fast"


	def update_paths(self, vlc_path=None, wmp_path=None, potplayer_path=None):
		self._vlc_path	   = vlc_path if vlc_path and os.path.isfile(vlc_path) else _find_vlc()
		self._wmp_path	   = wmp_path if wmp_path and os.path.isfile(wmp_path) else None
		self._potplayer_path = potplayer_path if potplayer_path and os.path.isfile(potplayer_path) else _find_potplayer()

	def _stop_current(self):
		if not self._disable_bass and self._backend == self.BACKEND_BASS:
			if self._bass_engine:
				self._bass_engine.stop()
		else:
			self._stop_process()
		self._backend = self.BACKEND_NONE

	def _stop_process(self):
		proc = self._proc
		self._proc = None
		if proc:
			try:
				proc.terminate()
				proc.wait(timeout=2)
			except:
				try:
					proc.kill()
				except:
					pass

		vbs = self._vbs_path
		self._vbs_path = None
		if vbs:
			try:
				os.unlink(vbs)
			except:
				pass

	def _launch_non_bass_fallback(self, url, volume, gen):
		"""VLC -> PotPlayer -> WMP only — used when BASS has already been
		retried and exhausted (see _on_bass_stall's _reconnect()). Mirrors
		the tail of _launch() but deliberately skips the BASS step, since
		BASS just failed repeatedly for this URL.
		"""
		def _stale():
			return gen is not None and self._play_gen != gen

		self._stop_current()

		if _stale():
			return

		if self._vlc_path:
			try:
				self._launch_vlc(url, volume)
				if _stale():
					self._stop_process()
				return
			except Exception:
				pass

		if _stale():
			return

		if self._potplayer_path:
			try:
				self._launch_potplayer(url, volume)
				if _stale():
					self._stop_process()
				return
			except Exception:
				pass

		if _stale():
			return

		self._launch_wmp(url, volume)
		if _stale():
			self._stop_process()

	def _launch(self, url, volume, gen=None):
		"""Launch playback: BASS → VLC → PotPlayer → WMP.
		Always called from a background thread.
		gen: the _play_gen value captured when this launch was requested.
			 If self._play_gen no longer matches, a newer play() has arrived
			 and we must stop immediately without starting any audio output.
		"""
		def _stale():
			return gen is not None and self._play_gen != gen

		self._stop_current()

		if _stale():
			return

		if not self._disable_bass and self._bass_engine and self._bass_engine.ready():
			try:
				if self._launch_bass(url, volume):
					if _stale():
						self._bass_engine.stop()
						return
					return
			except Exception:
				pass

		if _stale():
			return

		if self._vlc_path:
			try:
				self._launch_vlc(url, volume)
				if _stale():
					self._stop_process()
					return
				return
			except Exception:
				pass

		if _stale():
			return

		if self._potplayer_path:
			try:
				self._launch_potplayer(url, volume)
				if _stale():
					self._stop_process()
					return
				return
			except Exception:
				pass

		if _stale():
			return

		self._launch_wmp(url, volume)
		if _stale():
			self._stop_process()
			return

	def _launch_bass(self, url, volume):
		"""Start BASS playback — single attempt, no retry."""
		# Ensure any previously playing stream is stopped before starting a new one.
		if self._bass_engine:
			self._bass_engine.stop()
		station = self._current_station
		is_podcast = bool(station and "podcast" in station.get("tags", ""))
		saved_pos = 0.0
		if is_podcast:
			saved_pos = self.get_podcast_position(station.get("url") or url)

		# If we're about to try resuming a podcast, open the real stream
		# muted and play tuner.mp3 (looped) on a small separate engine
		# meanwhile, instead of letting the episode's own audio play
		# audibly from 0:00 while we wait for BASS to accept the seek back
		# to saved_pos. Same tuner.mp3/loop-watcher used for station tuning
		# transitions; see set_tuning_effect_enabled().
		resume_wait_engine = None
		resume_wait_stop   = None
		if is_podcast and saved_pos > 1.0 and not self._disable_bass:
			try:
				dll_dir = os.path.dirname(os.path.abspath(__file__))
				candidate = _BassEngine(dll_dir, output_device=self._output_device_index)
				if candidate.load():
					candidate.play_timeshift_file(_TUNER_MP3_PATH, self._volume / 100.0)
					resume_wait_engine = candidate
					resume_wait_stop   = threading.Event()
					threading.Thread(
						target=self._tuning_loop_watcher,
						args=(resume_wait_engine, resume_wait_stop, self._play_gen),
						daemon=True, name="FreeRadio-podcast-resume-tuner"
					).start()
			except Exception:
				resume_wait_engine = None
				resume_wait_stop   = None

		play_volume = 0.0 if resume_wait_engine else (volume / 100.0)
		success = self._bass_engine.play(url, play_volume, seekable=is_podcast)

		def _stop_resume_wait():
			if resume_wait_stop:
				resume_wait_stop.set()
			if resume_wait_engine:
				try:
					resume_wait_engine.stop()
					resume_wait_engine.unload()
				except Exception:
					pass

		if success:
			self._backend = self.BACKEND_BASS
			# Reapply bass boost setting (DSP resets when stream restarts)
			boost = getattr(self, "_bass_boost", 0.0)
			if boost > 0.0:
				try:
					self._bass_engine.set_bass_boost(boost)
				except Exception:
					pass
			# Reapply FX setting — _apply_fx() in bass_host already runs during
			# play(), but we send set_fx again as a safety net for edge cases
			# (e.g. subprocess state divergence after device switch).
			fx = getattr(self, "_audio_fx", "none")
			if fx and fx != "none":
				try:
					self._bass_engine.set_fx(fx)
				except Exception:
					pass
			# Reapply playback rate (podcasts only) — bass_host.py's Host
			# remembers the rate on its own and reapplies it automatically
			# the next time a tempo-capable stream is opened *within the
			# same subprocess* (see _try_create_url). But whenever a fresh
			# _BassEngine is created instead of reusing the existing one —
			# crossfade/tuning transitions (play()), or switch_output_device()
			# — the new subprocess's Host starts at the default rate (1.0)
			# and never learns about self._playback_rate, so the previously
			# chosen speed silently reverts to normal on the next episode or
			# resume. Resending it here (same safety-net pattern as bass
			# boost/FX above) keeps it in sync regardless of which engine
			# instance ended up serving this stream.
			if is_podcast and self._playback_rate != 1.0:
				try:
					self._bass_engine.set_playback_rate(self._playback_rate)
				except Exception:
					pass
			# Resume podcasts from where they were left off - podcasts are
			# always opened seekable (see the "seekable" flag above), so
			# this is just a relative seek from the fresh position (0).
			if is_podcast and saved_pos > 1.0:
				self._resume_podcast_position_on_engine(self._bass_engine, saved_pos)
			if resume_wait_engine:
				_stop_resume_wait()
				# Reveal the episode at its real volume now that it's
				# positioned correctly (or we gave up waiting for the seek).
				try:
					self._bass_engine.set_volume(volume / 100.0)
				except Exception:
					pass
			return True
		_stop_resume_wait()
		return False

	def _resume_podcast_position(self, saved_pos):
		"""Seek to saved_pos right after a podcast starts playing.

		A seek attempted in the first instant after play() returns can
		silently fail (or land at 0) - BASS may not have finished reading
		the stream's Content-Length yet, so the seek target gets clamped
		against a not-yet-populated length. The previous version fired a
		single seek and ignored its result entirely, so this failure was
		invisible and the episode just kept playing from the start. Retry
		briefly instead of giving up after one silent attempt.
		"""
		self._resume_podcast_position_on_engine(self._bass_engine, saved_pos)

	def _resume_podcast_position_on_engine(self, engine, saved_pos):
		"""Seek *engine* to saved_pos right after it starts playing a
		seekable (podcast) stream. Shared by the main playback path
		(_resume_podcast_position) and by start_mirror(), which needs the
		same retry behaviour to pick up the mirror output at the position
		the main output is already at.

		Podcasts are opened as progressive network streams, not fully
		pre-buffered (see _BassEngine.play()'s "seekable" docstring), so a
		seek attempted the instant play() reports success can legitimately
		fail: BASS may not yet have downloaded/parsed enough of the stream
		to know its length or accept a position change. The previous retry
		window here (6 attempts, 0.25s apart - under 2 seconds total) was
		too short on an ordinary connection, so a slow-to-buffer episode
		would consistently exhaust every attempt and silently keep playing
		from 0:00 with no visible error. Retry for up to ~15 seconds with
		a growing delay between attempts to give normal buffering time to
		catch up before giving up.
		"""
		deadline = time.time() + 15.0
		delay = 0.3
		attempt = 0
		while time.time() < deadline:
			attempt += 1
			try:
				ok, _pos, _length = engine.timeshift_seek(saved_pos)
			except Exception:
				ok = False
			if ok:
				return
			time.sleep(delay)
			delay = min(delay * 1.5, 1.5)
		log.info("FreeRadio: could not resume podcast at %.1fs after %d attempts over ~15s",
				  saved_pos, attempt)

	def _launch_vlc(self, url, volume):
		self._stop_process()

		vlc_volume = str(int(min(volume, 200) / 100.0 * 256))  # VLC scale: 256=100%, 512=200%
		cmd = [
			self._vlc_path,
			"--intf", "dummy",
			"--aout", "directsound",
			"--no-video",
			"--quiet",
			"--http-reconnect",
			"--network-caching", "6000",
			"--live-caching", "6000",
			"--volume", vlc_volume,
			"--extraintf", "rc",
			"--rc-host", "127.0.0.1:19155",
			url,
		]

		si = subprocess.STARTUPINFO()
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		si.wShowWindow = 0

		self._proc = subprocess.Popen(
			cmd,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
			startupinfo=si,
			creationflags=subprocess.CREATE_NO_WINDOW,
		)
		self._backend = self.BACKEND_VLC

		# VLC ignores --volume on startup and resets to its default (~128/256).
		# Re-apply the correct volume via the RC interface once VLC is ready.
		_target_vol = int(min(volume, 200) / 100.0 * 256)

		def _apply_vlc_volume():
			for _attempt in range(8):
				time.sleep(0.4)
				try:
					with socket.create_connection(("127.0.0.1", 19155), timeout=1.0) as s:
						s.sendall(("volume %d\r\nquit\r\n" % _target_vol).encode())
					return
				except Exception:
					pass

		threading.Thread(target=_apply_vlc_volume, daemon=True,
						 name="FreeRadio-VLCVol").start()

	def _launch_potplayer(self, url, volume):
		"""Launch PotPlayer for stream playback."""
		self._stop_process()
		cmd = [
			self._potplayer_path,
			url,
			"/new",
			f"/volume={min(volume, 200)}",
			"/autoplay",
			"/cache=6000",
			"/network_retry=3",
			"/network_retry_delay=2000",
		]
		si = subprocess.STARTUPINFO()
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		si.wShowWindow = 0
		self._proc = subprocess.Popen(
			cmd,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
			startupinfo=si,
			creationflags=subprocess.CREATE_NO_WINDOW,
		)
		self._backend = self.BACKEND_POTPLAYER

	def _launch_wmp(self, url, volume):
		self._stop_process()

		safe_url = url.replace('"', "")
		fd, path = tempfile.mkstemp(suffix=".vbs", prefix="freeradio_")
		try:
			with os.fdopen(fd, "w", encoding="utf-8") as f:
				f.write(_VBS.format(volume=min(volume, 100), url=safe_url))
		except:
			try:
				os.unlink(path)
			except:
				pass
			raise
		self._vbs_path = path

		cmd = ["wscript", "/nologo", path]

		si = subprocess.STARTUPINFO()
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		si.wShowWindow = 0

		self._proc = subprocess.Popen(
			cmd,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
			startupinfo=si,
			creationflags=subprocess.CREATE_NO_WINDOW,
		)
		self._backend = self.BACKEND_WMP


	def set_crossfade_duration(self, seconds):
		"""Set the crossfade duration in seconds when switching stations.

		seconds: 0.0 disables crossfade (instant cut); recommended range 1.0–4.0.
		Only effective with the BASS backend.
		"""
		self._crossfade_duration = max(0.0, float(seconds))

	def get_crossfade_duration(self):
		return self._crossfade_duration

	def _abort_crossfade(self):
		"""Immediately stop any in-progress fade-out engine.  Must be called
		from a context where it is safe to unload a _BassEngine."""
		engine = self._crossfade_engine
		self._crossfade_engine = None
		if engine:
			try:
				engine.stop()
				engine.unload()
			except Exception:
				pass

	def set_tuning_effect_enabled(self, enabled):
		"""Enable/disable the 'station tuning' transition effect.

		When enabled, switching stations plays tuner.mp3 (looped for as long
		as needed) while the new station connects in the background; as soon
		as the new stream is confirmed playing, the effect is cut over
		instantly. Only effective with the BASS backend. Mutually exclusive
		with a numeric crossfade — callers should set that duration to 0.0
		when enabling this.
		"""
		self._tuning_effect_enabled = bool(enabled)

	def get_tuning_effect_enabled(self):
		return self._tuning_effect_enabled

	def _play_tuner_clip(self, engine):
		"""Open tuner.mp3 on engine for the tuning transition effect.

		Starts from a random position once the clip's duration is known, so
		each station switch (and each loop restart while waiting) sounds
		different instead of always starting from the same spot. The first
		time it's ever played, the duration isn't known yet, so it starts
		from 0.0 and the discovered length is cached in _TUNER_LENGTH_SECONDS
		for all later calls.
		"""
		global _TUNER_LENGTH_SECONDS
		start = 0.0
		if _TUNER_LENGTH_SECONDS and _TUNER_LENGTH_SECONDS > 1.0:
			start = random.uniform(0.0, max(0.0, _TUNER_LENGTH_SECONDS - 1.0))
		ok = engine.play_timeshift_file(_TUNER_MP3_PATH, self._volume / 100.0, start_seconds=start)
		if ok and not _TUNER_LENGTH_SECONDS:
			try:
				_pos, length = engine.timeshift_status()
				if length > 0:
					_TUNER_LENGTH_SECONDS = length
			except Exception:
				pass
		return ok

	def _abort_tuning_transition(self):
		"""Immediately stop any in-progress tuning-effect engine and its
		loop-watcher thread. Must be called from a context where it is safe
		to unload a _BassEngine."""
		stop_evt = self._tuning_stop
		self._tuning_stop = None
		if stop_evt:
			stop_evt.set()
		engine = self._tuning_engine
		self._tuning_engine = None
		if engine:
			try:
				engine.stop()
				engine.unload()
			except Exception:
				pass

	def _tuning_loop_watcher(self, engine, stop_evt, gen):
		"""While a tuning transition is in progress, replay tuner.mp3 from
		the start whenever it reaches its end, so the effect keeps playing
		for as long as the new station takes to connect."""
		while not stop_evt.is_set() and self._play_gen == gen:
			time.sleep(_TUNER_POLL_INTERVAL)
			if stop_evt.is_set() or self._play_gen != gen:
				return
			try:
				pos, length = engine.timeshift_status()
			except Exception:
				return
			if length > 0 and pos >= length - 0.15:
				if stop_evt.is_set() or self._play_gen != gen:
					return
				try:
					self._play_tuner_clip(engine)
				except Exception:
					return

	def play(self, url, name="", url_resolved=None, station=None):
		with self._play_lock:
			# Save the resume position of whatever podcast is currently
			# playing before we switch away from it - _current_station is
			# about to be overwritten below.
			if self._is_playing:
				try:
					self._save_current_podcast_position_if_playing()
				except Exception:
					pass

			# Bump generation — any in-flight _bg_launch with an older gen will
			# notice the mismatch and abort before starting audio output.
			self._play_gen += 1
			my_gen = self._play_gen

			# --- Crossfade logic (BASS backend only) ---
			# If a stream is currently playing on BASS and crossfade is enabled,
			# keep the old engine alive as a temporary fade-out engine and spin up
			# a brand-new _BassEngine for the new station.  The old engine will
			# continue playing until the new stream is confirmed started, then it
			# is gradually faded to silence in a background thread.
			xfade_engine = None
			tuner_engine = None
			do_crossfade = (
				not self._disable_bass
				and self._crossfade_duration > 0.0
				and not self._tuning_effect_enabled
				and self._backend == self.BACKEND_BASS
				and self._bass_engine is not None
				and self._bass_engine.ready()
				and self._is_playing
			)
			do_tuning = (
				not do_crossfade
				and not self._disable_bass
				and self._tuning_effect_enabled
				and self._backend == self.BACKEND_BASS
				and self._bass_engine is not None
				and self._bass_engine.ready()
				and self._is_playing
			)

			if do_crossfade:
				# Abort any previous (still running) fade-out/tuning first.
				self._abort_crossfade()
				self._abort_tuning_transition()

				# Save old engine — it keeps playing untouched.
				xfade_engine = self._bass_engine

				# Create a fresh engine for the new station.
				# load() is called in the background thread (blocking I/O outside lock).
				dll_dir = os.path.dirname(os.path.abspath(__file__))
				self._bass_engine = _BassEngine(dll_dir, output_device=self._output_device_index)
				# backend is NONE until _launch_bass() succeeds below.
				self._backend = self.BACKEND_NONE
			elif do_tuning:
				# Abort any previous (still running) fade-out/tuning first.
				self._abort_crossfade()
				self._abort_tuning_transition()

				# Old engine switches over to the tuning sound effect right
				# away, instead of continuing to play the old station.
				tuner_engine = self._bass_engine
				try:
					self._play_tuner_clip(tuner_engine)
				except Exception:
					pass

				stop_evt = threading.Event()
				self._tuning_stop   = stop_evt
				self._tuning_engine = tuner_engine
				threading.Thread(
					target=self._tuning_loop_watcher,
					args=(tuner_engine, stop_evt, my_gen),
					daemon=True, name="FreeRadio-tuning-loop"
				).start()

				# Create a fresh engine for the new station — it connects in
				# the background while the tuning effect is heard.
				dll_dir = os.path.dirname(os.path.abspath(__file__))
				self._bass_engine = _BassEngine(dll_dir, output_device=self._output_device_index)
				self._backend = self.BACKEND_NONE
			else:
				# Normal path: stop whatever is currently playing.
				self._abort_crossfade()
				self._abort_tuning_transition()
				self._stop_current()

			self._stop_icy_thread()

			self._current_url		  = url
			self._current_url_resolved = url_resolved or url
			self._current_name		 = name
			self._current_station	  = station or {}
			self._intentional_stop	 = False
			self._is_playing		   = True

			vol		= self._volume
			stream_url = url_resolved or url

		def _bg_launch(gen=my_gen, xfade=xfade_engine, tuner=tuner_engine):
			# Each blocking step is guarded: if a newer play() arrived while we
			# were busy, our generation is stale — bail out immediately.
			if self._play_gen != gen:
				if xfade:
					try:
						xfade.stop()
						xfade.unload()
					except Exception:
						pass
				if tuner:
					self._abort_tuning_transition()
				return

			# A fresh launch (new station, reconnect, or crossfade) always
			# starts in live mode. Reset any stale time-shift state from a
			# previous station now, before anything else - otherwise a
			# leftover "active" flag would cause the next rewind/forward
			# press to try to seek within the (unseekable) live URL stream
			# instead of correctly starting a new time-shift session.
			if self._timeshift_active:
				self._timeshift_active = False
				try:
					self._timeshift_buffer.exit_playback()
				except Exception:
					pass

			# If crossfade or tuning mode: load the brand-new engine now (blocking).
			if xfade is not None or tuner is not None:
				loaded = self._bass_engine.load()
				if not loaded or not self._bass_engine.ready():
					# New engine failed to initialise — restore old engine and
					# fall back to a regular (non-crossfade/non-tuning) launch.
					log.warning("FreeRadio: crossfade/tuning engine failed to load, falling back.")
					try:
						self._bass_engine.unload()
					except Exception:
						pass
					self._bass_engine = xfade if xfade is not None else tuner
					xfade = None
					if tuner is not None:
						# Reusing the tuner engine as the live engine now —
						# just stop its loop-watcher and clear tracking,
						# without stopping/unloading the engine itself (that
						# happens via self._bass_engine.stop() just below).
						stop_evt = self._tuning_stop
						self._tuning_stop = None
						if stop_evt:
							stop_evt.set()
						self._tuning_engine = None
						tuner = None
					try:
						self._bass_engine.stop()
					except Exception:
						pass
				else:
					self._bass_engine.on_meta	   = self._on_bass_meta
					self._bass_engine.on_connecting  = self._on_bass_connecting
					self._bass_engine.on_stall	   = self._on_bass_stall

				if self._play_gen != gen:
					if xfade:
						try:
							xfade.stop()
							xfade.unload()
						except Exception:
							pass
					if tuner:
						self._abort_tuning_transition()
					return

			# If a mirror output is active, kick off its (re)connect on a
			# separate thread at the same time as the main stream below,
			# instead of waiting for the main connect to finish first.
			# Each connect is a separate network round-trip through its own
			# bass_host subprocess, so starting them together — rather than
			# one after the other — keeps the two outputs much closer to
			# in sync instead of the mirror trailing behind by however long
			# the main connect took.
			mirror_thread = None
			if not self._disable_bass:
				mirror = getattr(self, "_mirror_engine", None)
				mirror_dev = getattr(self, "_mirror_device_index", None)
				if mirror is not None and mirror_dev is not None:
					station = self._current_station
					is_podcast = bool(station and "podcast" in station.get("tags", ""))
					saved_pos = 0.0
					if is_podcast:
						saved_pos = self.get_podcast_position(station.get("url") or stream_url)
					rate = self._playback_rate

					def _sync_mirror(m=mirror, u=stream_url, v=vol, g=gen,
									  podcast=is_podcast, pos=saved_pos, r=rate):
						if self._play_gen != g:
							return
						try:
							m.stop()
							# Podcasts/audio books must open seekable, same as
							# the main engine, or the resume-position and
							# rewind/forward seeks below silently no-op on
							# the mirror.
							m.play(u, v / 100.0, seekable=podcast)
						except Exception:
							return
						if self._play_gen != g:
							return
						if podcast and r != 1.0:
							try:
								m.set_playback_rate(r)
							except Exception:
								pass
						if podcast and pos > 1.0:
							self._resume_podcast_position_on_engine(m, pos)

					mirror_thread = threading.Thread(
						target=_sync_mirror, daemon=True,
						name="FreeRadio-mirror-sync")
					mirror_thread.start()

			try:
				self._launch(stream_url, vol, gen=gen)
			except Exception:
				if self._play_gen == gen:
					self._is_playing = False
				if xfade:
					try:
						xfade.stop()
						xfade.unload()
					except Exception:
						pass
				if tuner:
					self._abort_tuning_transition()
				return

			if self._play_gen != gen:
				# A newer play() started while _launch was running; it has
				# already called _stop_current(), so just exit.
				if xfade:
					try:
						xfade.stop()
						xfade.unload()
					except Exception:
						pass
				if tuner:
					self._abort_tuning_transition()
				return

			# New stream is confirmed playing — for the tuning effect this is
			# an instant hard cut (not a fade): stop the tuner sound right away.
			if tuner:
				self._abort_tuning_transition()

			# New stream is confirmed playing — begin fade-out of the old engine.
			if xfade:
				self._crossfade_engine = xfade
				xfade_vol = vol / 100.0

				def _fade_out(engine=xfade, start_vol=xfade_vol):
					duration = self._crossfade_duration
					steps	= max(10, int(duration * 20))  # ~50 ms per step
					interval = duration / steps
					for i in range(steps):
						# Stop early if a newer crossfade has already taken over.
						if self._crossfade_engine is not engine:
							break
						frac = 1.0 - (i + 1) / steps
						try:
							engine.set_volume(frac * start_vol)
						except Exception:
							break
						time.sleep(interval)
					# Clean up — only if still ours.
					if self._crossfade_engine is engine:
						self._crossfade_engine = None
					try:
						engine.stop()
						engine.unload()
					except Exception:
						pass

				threading.Thread(
					target=_fade_out, daemon=True, name="FreeRadio-fadeout"
				).start()

			if self._backend != self.BACKEND_BASS:
				self._start_icy_thread(stream_url)

			# Time-shift buffer: restart capture for the new station. Always
			# running on the BASS backend now (see _LIGHT_BUFFER_SECONDS above)
			# so recognition/recording have an already-open connection to tail
			# instead of opening their own; capacity is only smaller when the
			# user-facing rewind feature itself is off. Only supported on the
			# BASS backend.
			#
			# IMPORTANT: the previous station's capture session is always
			# torn down first, unconditionally - even if resolving/starting
			# the new one fails or the new stream is unsupported (HLS).
			# Otherwise a stale buffer from the *previous* station would
			# keep capturing in the background and could get played back
			# by rewind, even though a different station is now selected.
			if self._backend == self.BACKEND_BASS:
				with self._timeshift_launch_lock:
					# Re-check under the lock, not just before it: another
					# thread (e.g. set_timeshift_enabled's own capture-start,
					# or a stall reconnect) may have been holding the lock
					# for a newer generation while we were waiting for it.
					# If so, our station has already been superseded - bail
					# out without touching the buffer so we can't clobber
					# the newer, correct capture session.
					if self._play_gen == gen:
						is_podcast = "podcast" in self._current_station.get("tags", "")
						if is_podcast:
							# Podcasts and GETEM audio books are on-demand,
							# already-seekable files (via seek_relative()/
							# timeshift_seek() directly on the BASS engine -
							# see script_timeshiftRewind's podcast branch),
							# not a live ad-inserted stream - none of the
							# reasons this buffer exists for live radio
							# (a rewind window, letting recognition/recording
							# tail an already-open connection past a
							# per-connection ad) apply to them. Capturing one
							# anyway was ballooning the .buf file far past
							# CAPACITY_SECONDS for file-based streams - just
							# stop whatever capture was left running from a
							# previous (live) station instead of starting or
							# keeping one for this one.
							try:
								self._timeshift_buffer.stop()
							except Exception:
								pass
							self._timeshift_buffer_gen = None
						else:
							self._timeshift_buffer.CAPACITY_SECONDS = (
								self._timeshift_capacity_seconds if self._timeshift_enabled else _LIGHT_BUFFER_SECONDS
							)
							# HLS master playlists are not simple "one line = one
							# audio URL" playlists - resolving them the way
							# _resolve_playlist_url() resolves .pls/.m3u files
							# could pick the wrong sub-stream. TimeShiftBuffer
							# does its own HLS master/media playlist resolution
							# internally (see timeshift.py's _run_hls), so the
							# raw .m3u8 URL is passed through unresolved here.
							is_hls = stream_url.lower().split("?")[0].endswith(".m3u8")
							capture_url = stream_url if is_hls else _resolve_playlist_url(stream_url)

							# If the buffer is already actively capturing this exact
							# URL, this _bg_launch is a *reconnect* of the same
							# station - e.g. resume() falling back to a full relaunch
							# after a long pause, not the user picking a different
							# station. Tearing the capture down and restarting it
							# here would throw away a connection that has already
							# played past whatever per-connection ad the station
							# serves brand-new listeners; a fresh start() would just
							# get served that ad again, reintroducing the exact bug
							# this buffer exists to avoid for recognition/recording.
							# Only stop()+start() when the station actually changed.
							if self._timeshift_buffer.is_active() and self._timeshift_buffer.get_url() == capture_url:
								log.info("FreeRadio TimeShift: reusing existing capture for %s (same station, "
										  "not a switch)", capture_url)
							else:
								try:
									self._timeshift_buffer.stop()
								except Exception:
									pass
								try:
									if is_hls:
										log.info("FreeRadio TimeShift: starting HLS capture for %s", capture_url)
									else:
										log.info("FreeRadio TimeShift: starting capture for %s (resolved from %s)",
												  capture_url, stream_url)
									self._timeshift_buffer.start(capture_url)
								except Exception as e:
									log.info("FreeRadio TimeShift: could not start capture: %s", e, exc_info=True)
							# Whether reused or freshly started, this buffer instance
							# now genuinely belongs to *this* launch's station.
							self._timeshift_buffer_gen = gen

			# The mirror (re)connect was already started concurrently above;
			# just make sure it has finished before this launch is done.
			if mirror_thread is not None:
				mirror_thread.join(timeout=30.0)

		threading.Thread(target=_bg_launch, daemon=True, name="FreeRadio-launch").start()

	def pause(self):
		with self._play_lock:
			if not self._is_playing:
				return
			station = self._current_station
			try:
				self._save_current_podcast_position_if_playing()
			except Exception:
				pass
			self._play_gen += 1
			self._intentional_stop = True
			self._paused_at = time.time()
			if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
				self._bass_engine.pause()
			else:
				self._stop_icy_thread()
				self._stop_process()
			self._is_playing = False
		# Also pause Mirror
		if not self._disable_bass:
			mirror = getattr(self, "_mirror_engine", None)
			if mirror and mirror.ready():
				try:
					mirror.pause()
				except Exception:
					pass
		if station and "podcast" in station.get("tags", ""):
			cb = self.on_podcast_progress_saved
			if cb:
				try:
					cb(station.get("url") or self._current_url)
				except Exception:
					pass

	def resume(self):
		_BASS_RESUME_THRESHOLD = 10  # seconds — reconnect if this time has passed

		with self._play_lock:
			if self._is_playing or not self._current_url:
				return
			self._play_gen += 1
			my_gen = self._play_gen
			self._intentional_stop = False
			self._is_playing = True

			paused_duration = time.time() - getattr(self, "_paused_at", 0)

			# Podcasts always take the reconnect-and-seek path below, never
			# the quick in-place BASS resume. The in-place resume trusts the
			# BASS host to keep its own position on a paused, still-
			# downloading network stream, which is not reliable for
			# podcasts in practice - it can come back at (or near) 0
			# instead of where playback was paused. The reconnect path is
			# the same one a fresh play() uses, seeking to the position
			# saved in podcast_positions.json (updated right before pause),
			# so it is the one path proven to land at the right spot.
			station = self._current_station
			is_podcast = bool(station and "podcast" in station.get("tags", ""))

			if (
				not is_podcast
				and not self._disable_bass
				and self._backend == self.BACKEND_BASS
				and self._bass_engine
				and paused_duration <= _BASS_RESUME_THRESHOLD
			):
				self._bass_engine.resume()
				# Wake up Mirror with a short resume
				mirror = getattr(self, "_mirror_engine", None)
				if mirror and mirror.ready():
					try:
						mirror.resume()
					except Exception:
						pass
				# The time-shift capture connection was never touched by
				# pause() (it keeps recording the live edge the whole
				# time - see timeshift.py's design notes), so the buffer
				# itself is still valid for this station. Only _play_gen
				# advanced here (twice: once on pause(), once here) -
				# sync _timeshift_buffer_gen to match so rewind_timeshift()
				# doesn't mistake this still-good buffer for a stale one
				# left over from a station switch and refuse to rewind.
				self._timeshift_buffer_gen = my_gen
				return

			if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
				# Long pause (or a podcast, which always lands here) —
				# restart BASS. This always reconnects to the *live* URL
				# below (see _bg_resume), never back into time-shifted
				# playback, so any active time-shift session must be torn
				# down here - the same reset _bg_launch does on every fresh
				# launch. Skipping this (as before) left _timeshift_active
				# stuck True while BASS was actually playing the live
				# stream again: rewind/forward would then call
				# timeshift_seek() against a plain live stream that
				# was never opened via play_timeshift_file(), which does
				# nothing, making navigation silently stop working until
				# the buffer was toggled off/on or the station changed. It
				# also left _suspend_trim permanently incremented (its
				# matching exit_playback() was never called), which quietly
				# let the capture file grow past its capacity forever.
				if self._timeshift_active:
					self._timeshift_active = False
					try:
						self._timeshift_buffer.exit_playback()
					except Exception:
						pass
				self._bass_engine.stop()
				self._backend = self.BACKEND_NONE

			vol = self._volume
			stream_url = self._current_url_resolved or self._current_url

		def _bg_resume(gen=my_gen):
			if self._play_gen != gen:
				return

			# Restart the mirror concurrently with the main stream below,
			# instead of after it finishes, so both outputs reconnect at
			# roughly the same moment after a long pause.
			mirror_thread = None
			if not self._disable_bass:
				mirror = getattr(self, "_mirror_engine", None)
				if mirror and mirror.ready():
					station = self._current_station
					podcast = bool(station and "podcast" in station.get("tags", ""))
					pos = self.get_podcast_position(station.get("url") or stream_url) if podcast else 0.0
					rate = self._playback_rate

					def _sync_mirror(m=mirror, u=stream_url, v=vol, g=gen,
									  podcast=podcast, pos=pos, r=rate):
						if self._play_gen != g:
							return
						try:
							m.stop()
							# Podcasts/audio books must reopen seekable, same
							# as the main engine, or the resume-position and
							# rewind/forward seeks below silently no-op on
							# the mirror.
							m.play(u, v / 100.0, seekable=podcast)
						except Exception:
							return
						if self._play_gen != g:
							return
						if podcast and r != 1.0:
							try:
								m.set_playback_rate(r)
							except Exception:
								pass
						if podcast and pos > 1.0:
							self._resume_podcast_position_on_engine(m, pos)

					mirror_thread = threading.Thread(
						target=_sync_mirror, daemon=True,
						name="FreeRadio-mirror-sync")
					mirror_thread.start()

			try:
				self._launch(stream_url, vol, gen=gen)
			except Exception:
				if self._play_gen == gen:
					self._is_playing = False
				if mirror_thread is not None:
					mirror_thread.join(timeout=30.0)
				return
			if self._play_gen != gen:
				if mirror_thread is not None:
					mirror_thread.join(timeout=30.0)
				return
			if self._backend != self.BACKEND_BASS:
				self._start_icy_thread(stream_url)
			elif self._timeshift_buffer_gen is not None:
				# Same reasoning as the short-pause path above: this is a
				# reconnect of the SAME station after a long pause, not a
				# station switch, so the capture buffer was never stopped or
				# restarted and is still valid - only re-sync the generation
				# counter so rewind_timeshift() doesn't treat it as stale.
				self._timeshift_buffer_gen = gen
			if mirror_thread is not None:
				mirror_thread.join(timeout=30.0)

		threading.Thread(target=_bg_resume, daemon=True, name="FreeRadio-resume").start()

	def stop(self):
		with self._play_lock:
			if self._is_playing:
				try:
					self._save_current_podcast_position_if_playing()
				except Exception:
					pass
			self._play_gen += 1
			self._intentional_stop = True
			self._stop_icy_thread()
			self._abort_crossfade()
			self._abort_tuning_transition()

			if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
				self._bass_engine.stop()
			else:
				self._stop_process()

			self._current_url = None
			self._current_name = ""
			self._current_station = {}
			self._is_playing = False
			self._backend = self.BACKEND_NONE

		# Also stop Mirror (except lock - no risk of deadlock)
		self.stop_mirror()

		# Stop time-shift capture (outside lock — no risk of deadlock).
		# This always runs now regardless of the rewind toggle - see
		# _LIGHT_BUFFER_SECONDS above.
		try:
			self._timeshift_buffer.stop()
		except Exception:
			pass
		self._timeshift_active = False

	def set_volume(self, volume):
		with self._play_lock:
			# Allow amplification beyond 100 % up to 200 % (maps to 0.0–2.0 in BASS).
			self._volume = max(0, min(200, int(volume)))
			# Sync mirror volume too (only if BASS enabled)
			if not self._disable_bass:
				mirror = getattr(self, "_mirror_engine", None)
				if mirror and mirror.ready():
					try:
						mirror.set_volume(self._volume / 100.0)
					except Exception:
						pass
			if not self._is_playing:
				return

			if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
				self._bass_engine.set_volume(self._volume / 100.0)
				return

			if self._backend == self.BACKEND_VLC and self._proc and self._proc.poll() is None:
				try:
					vlc_vol = int(min(self._volume, 200) / 100.0 * 256)
					with socket.create_connection(("127.0.0.1", 19155), timeout=1.0) as s:
						s.sendall(("volume %d\r\n" % vlc_vol).encode())
					return
				except Exception:
					# Don't restrat, just log in
					return

			# do not restart for PotPlayer
			if self._backend == self.BACKEND_POTPLAYER:
				# PotPlayer does not support volume adjustment directly
				return

	def set_bass_boost(self, boost_0_1):
		"""Adjust the bass boost level.

		boost_0_1: 0.0 = off, 1.0 = maximum (+12 dB low-shelf ~150 Hz).
		It only works on the BASS backend.
		"""
		self._bass_boost = max(0.0, min(1.0, float(boost_0_1)))
		if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
			try:
				self._bass_engine.set_bass_boost(self._bass_boost)
			except Exception:
				pass

	_PLAYBACK_RATE_STEP = 0.1
	_PLAYBACK_RATE_MIN  = 0.5
	_PLAYBACK_RATE_MAX  = 2.0

	def _step_playback_rate(self, delta):
		"""Increase/decrease the pitch-preserving podcast playback rate by
		*delta* (rounded to 1 decimal place so repeated steps land cleanly
		on 0.9/1.0/1.1 etc. instead of drifting from float addition).

		Returns (applied, actual_rate, reason): see set_playback_rate_value().
		"""
		return self.set_playback_rate_value(self._playback_rate + delta)

	def set_playback_rate_value(self, rate):
		"""Set the pitch-preserving podcast playback rate to an absolute
		value - the counterpart to _step_playback_rate()'s delta-based
		stepping, used to apply a saved per-feed/per-book playback speed
		(see PodcastFeed.audio_profile / GetemBook.audio_profile and
		playbackCoreMixin._play_station()) the moment an episode/chapter
		from it starts playing, rather than nudging up from whatever rate
		happened to be in effect already.

		Returns (applied, actual_rate, reason):
		- applied=True  -> the rate is actually in effect right now.
		- applied=False -> not currently possible (wrong backend, bass_fx.dll
		  not installed, or the current stream isn't tempo-wrapped e.g. a
		  live station or a podcast episode that fell back to a plain
		  stream) - the requested rate is still remembered and will apply
		  automatically to the next tempo-capable stream that opens.
		"""
		new_rate = round(float(rate), 1)
		new_rate = max(self._PLAYBACK_RATE_MIN, min(self._PLAYBACK_RATE_MAX, new_rate))
		if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
			try:
				applied, actual_rate, reason = self._bass_engine.set_playback_rate(new_rate)
			except Exception:
				applied, actual_rate, reason = False, new_rate, "engine_error"
			self._playback_rate = actual_rate if applied else new_rate
			if applied:
				self._sync_mirror_playback_rate(self._playback_rate)
			return applied, self._playback_rate, reason
		self._playback_rate = new_rate
		return False, new_rate, "wrong_backend"

	def increase_playback_rate(self):
		return self._step_playback_rate(self._PLAYBACK_RATE_STEP)

	def decrease_playback_rate(self):
		return self._step_playback_rate(-self._PLAYBACK_RATE_STEP)

	def get_playback_rate(self):
		return self._playback_rate

	def get_bass_boost(self):
		return getattr(self, "_bass_boost", 0.0)

	def set_fx(self, fx_name):
		"""Adjust and save DirectX 8 effect.

		fx_name: "none" | "chorus" | "compressor" | "distortion" |
				 "echo" | "flanger" | "gargle" | "reverb" |
				 "eq_bass" | "eq_treble" | "eq_vocal"
		It only works on the BASS backend; is applied immediately to the active stream.
		"""
		self._audio_fx = fx_name or "none"
		if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
			try:
				self._bass_engine.set_fx(self._audio_fx)
			except Exception:
				pass

	def set_eq_gain(self, band, gain_db):
		"""Set the ParamEQ gain for one EQ band in dB (-15..+15).

		band:	"eq_bass" | "eq_treble" | "eq_vocal"
		gain_db: dB value applied immediately; ignored unless BASS backend is active.
		"""
		# Store so it can be restored after reconnect / device switch
		if not hasattr(self, "_eq_gains"):
			self._eq_gains = {}
		self._eq_gains[band] = max(-15.0, min(15.0, float(gain_db)))
		if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
			try:
				self._bass_engine.set_eq_gain(band, gain_db)
			except Exception:
				pass

	def get_eq_gain(self, band):
		"""Return the stored EQ gain for *band*, or the default if not set."""
		_defaults = {"eq_bass": 9.0, "eq_treble": 9.0, "eq_vocal": 6.0}
		return getattr(self, "_eq_gains", {}).get(band, _defaults.get(band, 9.0))

	def get_fx(self):
		return getattr(self, "_audio_fx", "none")

	def get_volume(self):
		return self._volume

	def seek_relative(self, seconds):
		"""Seek relative to current position (for file-based playback like podcasts).
		Only works with BASS backend. Returns (ok, new_position_seconds).
		"""
		if self._disable_bass or self._backend != self.BACKEND_BASS or not self._bass_engine:
			return False, 0.0
		try:
			ok, pos, length = self._bass_engine.timeshift_seek(seconds)
			if ok:
				station = self._current_station
				if station and "podcast" in station.get("tags", ""):
					self._save_podcast_position_now(station, pos, length)
				self._sync_mirror_timeshift_seek(seconds)
			return ok, pos
		except Exception:
			return False, 0.0

	# -- Podcast resume position ---------------------------------------------

	def _get_podcast_positions_path(self):
		"""Path for podcast_positions.json directly under the NVDA user config directory."""
		try:
			import globalVars
			base_dir = globalVars.appArgs.configPath
		except Exception:
			# Fallback for standalone/test use outside NVDA.
			base_dir = os.path.dirname(os.path.abspath(__file__))

		return os.path.join(base_dir, "podcast_positions.json")

	def _load_podcast_positions(self):
		try:
			with open(self._podcast_positions_path, "r", encoding="utf-8") as fh:
				data = json.load(fh)
			if isinstance(data, dict):
				return data
		except FileNotFoundError:
			pass
		except Exception as e:
			log.error("FreeRadio: failed to load podcast positions: %s", e)
		return {}

	def _write_podcast_positions(self):
		try:
			with self._podcast_positions_lock:
				data = dict(self._podcast_positions)
			with open(self._podcast_positions_path, "w", encoding="utf-8") as fh:
				json.dump(data, fh, ensure_ascii=False, indent=2)
		except Exception as e:
			log.error("FreeRadio: failed to save podcast positions: %s", e)

	def get_podcast_position(self, url):
		"""Return the saved resume position (seconds) for *url*, or 0.0."""
		if not url:
			return 0.0
		with self._podcast_positions_lock:
			entry = self._podcast_positions.get(url)
		return float(entry.get("position", 0.0)) if entry else 0.0

	def clear_podcast_position(self, url):
		"""Remove the saved resume position for *url*, if any - used when
		the episode's podcast feed is unsubscribed
		(RadioDialog._on_podcast_remove()) or a GETEM audio book is removed
		from the library (RadioDialog._on_getem_remove_from_library()), so
		stale progress doesn't linger for content the user can no longer
		see or resume."""
		if not url:
			return
		with self._podcast_positions_lock:
			removed = self._podcast_positions.pop(url, None) is not None
		if removed:
			self._write_podcast_positions()

	def clear_podcast_positions(self, urls):
		"""Bulk version of clear_podcast_position() for a whole feed's worth
		of episode URLs, or a whole book's worth of chapter stream URLs, at
		once - a single disk write instead of one per URL."""
		if not urls:
			return
		changed = False
		with self._podcast_positions_lock:
			for url in urls:
				if url and self._podcast_positions.pop(url, None) is not None:
					changed = True
		if changed:
			self._write_podcast_positions()

	def has_podcast_position_entry(self, url):
		"""Whether *url* has ever had a podcast resume position recorded.
		A reliable way to tell a podcast episode URL from a plain radio
		stream URL when tag info isn't available - e.g. resuming the last
		station on NVDA startup from a config saved before the
		"last_station_tags" field existed, where the reconstructed station
		dict has no "tags" to check."""
		if not url:
			return False
		with self._podcast_positions_lock:
			return url in self._podcast_positions

	def _save_current_podcast_position_if_playing(self):
		"""Query and persist the live playback position of the current
		station, if it's a podcast that's actually playing right now.
		Called before switching stations, on pause/stop, and on
		termination, so the resume point is never far behind."""
		station = self._current_station
		if not station or "podcast" not in station.get("tags", ""):
			return
		if self._disable_bass or self._backend != self.BACKEND_BASS or not self._bass_engine:
			return
		try:
			pos, length = self._bass_engine.timeshift_status()
		except Exception:
			return
			
		# If position returned 0.0 but stream was playing, check if it reached the end
		if pos <= 0.0 and length <= 0.0:
			return

		self._save_podcast_position_now(station, pos, length)

	def _save_podcast_position_now(self, station, position, length=0.0):
		"""Persist *position* for the given podcast station.
		If position is within 3 seconds of the end, mark as listened (position = -1)."""
		url = station.get("url") or self._current_url
		if not url:
			return

		is_finished = False
		if length > 0:
			if length - position <= 3.0:
				is_finished = True
		elif position == -1.0:
			is_finished = True

		with self._podcast_positions_lock:
			if is_finished:
				self._podcast_positions[url] = {
					"position": -1.0,
					"listened": True,
					"name": station.get("name", "").strip(),
					"updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
				}
			else:
				self._podcast_positions[url] = {
					"position": round(float(position), 1),
					"listened": False,
					"name": station.get("name", "").strip(),
					"updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
				}
		self._write_podcast_positions()

	def _podcast_autosave_loop(self):
		"""Periodically save the resume position of a playing podcast, so a
		crash or unexpected NVDA restart doesn't lose much progress.

		The dialog no longer shows a live-ticking elapsed/total duration on
		the episode list (that caused NVDA to re-announce the focused row
		every second), so this no longer refreshes the in-memory
		live-progress cache each tick - it only does the periodic disk save,
		every _AUTOSAVE_INTERVAL seconds."""
		_AUTOSAVE_INTERVAL = 15
		while not self._podcast_autosave_stop.is_set():
			if self._podcast_autosave_stop.wait(timeout=_AUTOSAVE_INTERVAL):
				return
			try:
				if self._is_playing:
					self._save_current_podcast_position_if_playing()
			except Exception:
				pass

	def get_playback_position(self):
		"""Return (ok, position_seconds, length_seconds) for whatever is
		currently open on the BASS backend (live station, timeshift buffer
		file, or a seekable podcast stream all share the same handle)."""
		if self._disable_bass or self._backend != self.BACKEND_BASS or not self._bass_engine:
			return False, 0.0, 0.0
		try:
			pos, length = self._bass_engine.timeshift_status()
		except Exception:
			return False, 0.0, 0.0
		if pos <= 0.0 and length <= 0.0:
			return False, 0.0, 0.0
		return True, pos, length

	def is_playing(self):
		return self._is_playing

	def has_media(self):
		return self._current_url is not None

	def get_current_name(self):
		return self._current_name

	def get_current_station(self):
		return self._current_station

	def get_backend(self):
		return self._backend

	# -- Time-shift (rewind / fast-forward live radio) -------------------
	#
	# Only supported on the BASS backend. The capture buffer (timeshift.py)
	# runs continuously in the background whenever the feature is enabled
	# and something is playing; entering/exiting time-shift mode only
	# switches which BASS stream (live URL vs. local buffer file) is
	# actually feeding the audio output - the capture itself is untouched,
	# so returning to live never loses buffered audio.

	def set_timeshift_capacity_seconds(self, seconds):
		"""Set how much rewind-buffer audio to retain once the time-shift
		feature is enabled (clamped to 10 minutes .. 5 hours). Takes effect
		immediately — including on a capture that's already running, no
		restart or reconnect needed — since the buffer just reads this
		value back on its next periodic trim check.
		"""
		try:
			seconds = int(seconds)
		except (TypeError, ValueError):
			seconds = 600
		seconds = max(600, min(seconds, 18000))
		self._timeshift_capacity_seconds = seconds
		if self._timeshift_enabled:
			self._timeshift_buffer.CAPACITY_SECONDS = seconds

	def set_timeshift_disk_full_callback(self, callback):
		"""Register a callback invoked (at most once per capture session)
		if the time-shift buffer can't keep writing because the disk is
		full. Purely informational — capture keeps running with whatever
		space is available, live playback is never affected."""
		self._timeshift_buffer._notify_disk_full = callback

	def set_timeshift_enabled(self, enabled):
		"""Enable or disable the time-shift buffer feature.

		Disabling immediately returns to live playback (if time-shifted)
		and stops capturing. Enabling while already playing starts
		capturing right away, without interrupting playback.
		"""
		self._timeshift_enabled = bool(enabled)
		if not self._timeshift_enabled:
			if self._timeshift_active:
				self.exit_timeshift_to_live()
			# NOTE: capture itself is deliberately NOT stopped here anymore -
			# recognition and recording tail this same connection to avoid
			# re-triggering per-session ad insertion on stations that serve
			# one to every brand-new connection. Just shrink the retention
			# window back down to the lightweight default; the existing
			# connection (and its "past the ad" position in the stream) is
			# left untouched.
			self._timeshift_buffer.CAPACITY_SECONDS = _LIGHT_BUFFER_SECONDS
		elif (
			self._is_playing
			and self._backend == self.BACKEND_BASS
			# Podcasts/GETEM audio books never get a capture started for
			# them in the first place (see _bg_launch above) - they're
			# already seekable files, so there's nothing here to widen the
			# retention window on.
			and "podcast" not in self._current_station.get("tags", "")
		):
			self._timeshift_buffer.CAPACITY_SECONDS = self._timeshift_capacity_seconds
			stream_url = self._current_url_resolved or self._current_url
			captured_gen = self._play_gen
			if stream_url:
				def _bg_start_capture(url=stream_url, gen=captured_gen):
					# Share _timeshift_launch_lock with _bg_launch's own
					# stop/start/gen-assign sequence. Without this, a fast
					# station switch landing while this thread is still
					# resolving the *previous* station's URL could finish
					# its stop()/start() call after _bg_launch's, silently
					# overwriting the new (correct) capture session with a
					# stale one - after which the gen check below would
					# still (wrongly) look consistent from this thread's
					# point of view, leaving the buffer captured for the
					# wrong station indefinitely.
					with self._timeshift_launch_lock:
						if self._play_gen != gen:
							return
						is_hls = url.lower().split("?")[0].endswith(".m3u8")
						resolved_for_capture = url if is_hls else _resolve_playlist_url(url)
						# The light (45s) buffer is already running continuously
						# in the background for every playing station (see
						# _LIGHT_BUFFER_SECONDS above) - turning the rewind
						# feature on here just needs to widen its capacity to
						# 10 minutes, not open a brand-new connection. If it's
						# already capturing this exact URL, calling start()
						# anyway would (TimeShiftBuffer.start() always stops
						# itself first) throw away a connection that's already
						# past whatever per-connection ad the station serves
						# brand-new listeners, and get served a fresh one on
						# reconnect - the same bug _bg_launch's reuse guard
						# avoids for station switches/resumes.
						if self._timeshift_buffer.is_active() and self._timeshift_buffer.get_url() == resolved_for_capture:
							log.info("FreeRadio TimeShift: reusing existing capture for %s (rewind enabled, "
									  "not a switch)", resolved_for_capture)
						else:
							try:
								log.info("FreeRadio TimeShift: starting capture for %s (resolved from %s)",
										  resolved_for_capture, url)
								self._timeshift_buffer.start(resolved_for_capture)
							except Exception as e:
								log.info("FreeRadio TimeShift: could not start capture: %s", e, exc_info=True)
						# Whether reused or freshly started, sync the buffer
						# generation the same way _bg_launch's own start()
						# does - otherwise a prior play_gen bump elsewhere (e.g. a
						# BASS stall reconnect) that never got mirrored into
						# _timeshift_buffer_gen would keep rewind_timeshift()
						# permanently refusing with "no_buffer_yet", and toggling
						# this setting off/on would never be able to fix it since
						# this was the one start-capture path that skipped the
						# sync. Only skip it if a newer play() has since
						# superseded this station.
						if self._play_gen == gen:
							self._timeshift_buffer_gen = gen
				threading.Thread(
					target=_bg_start_capture, daemon=True,
					name="FreeRadio-TimeShiftResolve",
				).start()

	def is_timeshift_enabled(self):
		return self._timeshift_enabled

	def get_timeshift_buffer(self):
		"""Return the TimeShiftBuffer instance backing this player. Used by
		the recorder and music recognizer to tail the already-open capture
		connection instead of opening a fresh one."""
		return self._timeshift_buffer

	def get_timeshift_buffered_seconds(self):
		"""How many seconds of audio are currently available to rewind."""
		try:
			return self._timeshift_buffer.buffered_seconds()
		except Exception:
			return 0.0

	def is_timeshifted(self):
		"""True while time-shifted (buffered, seekable) playback is active,
		as opposed to normal live playback."""
		return self._timeshift_active

	def rewind_timeshift(self, seconds=15):
		"""Rewind by *seconds*.

		If not already time-shifted, this enters time-shift mode starting
		*seconds* before the live edge. Returns
		(ok, position_seconds, buffered_seconds, reason) where reason is a
		short code identifying why it failed ("ok" on success):
		"bass_disabled", "feature_disabled", "wrong_backend",
		"hls_unsupported", "no_buffer_yet", "no_buffer_file", "engine_error".
		"""
		if self._disable_bass:
			return False, 0.0, 0.0, "bass_disabled"
		if not self._timeshift_enabled:
			return False, 0.0, 0.0, "feature_disabled"
		if self._backend != self.BACKEND_BASS or not self._bass_engine:
			return False, 0.0, 0.0, "wrong_backend"
		if self._timeshift_buffer.is_hls_skipped():
			return False, 0.0, 0.0, "hls_unsupported"

		# The buffer object is reused across stations and only actually
		# torn down/restarted partway through _bg_launch - well after
		# _timeshift_active is reset for the new station. A rewind that
		# lands in that gap must not be allowed to treat the *previous*
		# station's still-open buffer file as ready.
		if self._timeshift_buffer_gen != self._play_gen:
			return False, 0.0, 0.0, "no_buffer_yet"

		buffered = self._timeshift_buffer.buffered_seconds()
		if buffered <= 0:
			return False, 0.0, 0.0, "no_buffer_yet"

		if not self._timeshift_active:
			path = self._timeshift_buffer.get_file_path()
			if not path:
				return False, 0.0, buffered, "no_buffer_file"
			start_pos = max(0.0, buffered - abs(seconds))
			vol = self._volume / 100.0
			self._timeshift_buffer.enter_playback()
			ok = self._bass_engine.play_timeshift_file(path, vol, start_pos)
			if not ok:
				self._timeshift_buffer.exit_playback()
				return False, 0.0, buffered, "engine_error"
			self._timeshift_active = True
			self._sync_mirror_timeshift_enter(path, start_pos)
			return True, start_pos, buffered, "ok"

		ok, position, _length = self._bass_engine.timeshift_seek(-abs(seconds))
		if ok:
			self._sync_mirror_timeshift_seek(-abs(seconds))
		return ok, position, buffered, ("ok" if ok else "engine_error")

	def forward_timeshift(self, seconds=15):
		"""Fast-forward by *seconds* while time-shifted.

		If this reaches the live edge, playback automatically returns to
		the live stream. Returns (ok, position_seconds_or_none, at_live_edge).
		"""
		if not self._timeshift_active or not self._bass_engine:
			return False, 0.0, False

		ok, position, length = self._bass_engine.timeshift_seek(abs(seconds))
		if not ok:
			# Once time-shifted, a forward seek can only fail because the
			# requested position is beyond what has actually been captured
			# so far - i.e. we're already at (or asking past) the live
			# edge. BASS_ChannelSetPosition usually errors out here rather
			# than landing close to the end, so the normal "within
			# _EDGE_MARGIN_SECONDS of length" check below never gets a
			# chance to fire. Treat the failure itself as having reached
			# live instead of surfacing a raw seek error to the user.
			self.exit_timeshift_to_live()
			return True, None, True

		self._sync_mirror_timeshift_seek(abs(seconds))

		_EDGE_MARGIN_SECONDS = 2.0
		if length - position <= _EDGE_MARGIN_SECONDS:
			self.exit_timeshift_to_live()
			return True, None, True

		return True, position, False

	def exit_timeshift_to_live(self):
		"""Return from time-shifted playback to the live stream immediately.
		Capture continues uninterrupted - only the playback source switches.
		"""
		if not self._timeshift_active:
			return
		self._timeshift_active = False
		self._timeshift_buffer.exit_playback()
		if self._backend == self.BACKEND_BASS and self._bass_engine:
			stream_url = self._current_url_resolved or self._current_url
			if stream_url:
				vol = self._volume / 100.0
				try:
					self._bass_engine.play(stream_url, vol)
				except Exception:
					pass
		self._sync_mirror_exit_to_live()

	# -- Mirror sync helpers for time-shift and playback rate ------------
	#
	# The mirror output is a second, independent bass_host subprocess (see
	# start_mirror()), so nothing that happens on the main engine reaches
	# it automatically. Without these, entering/seeking/exiting time-shift
	# or changing podcast playback speed would only ever affect the main
	# output, leaving the mirrored device stuck on live audio at normal
	# speed. Each helper is fire-and-forget on a background thread so a
	# slow mirror round-trip never delays the main output's response.

	def _get_ready_mirror(self):
		mirror = getattr(self, "_mirror_engine", None)
		if mirror is not None and mirror.ready():
			return mirror
		return None

	def _sync_mirror_timeshift_enter(self, path, start_pos):
		"""Open the same time-shift buffer file, at the same position, on
		the mirror engine right after the main engine enters time-shift."""
		mirror = self._get_ready_mirror()
		if mirror is None:
			return
		vol = self._volume / 100.0

		def _do(m=mirror, p=path, pos=start_pos, v=vol):
			try:
				m.play_timeshift_file(p, v, pos)
			except Exception:
				pass

		threading.Thread(target=_do, daemon=True, name="FreeRadio-mirror-timeshift").start()

	def _sync_mirror_timeshift_seek(self, delta_seconds):
		"""Apply the same rewind/forward seek to the mirror engine's
		already-open time-shift file, so it tracks the main output."""
		mirror = self._get_ready_mirror()
		if mirror is None:
			return

		def _do(m=mirror, d=delta_seconds):
			try:
				m.timeshift_seek(d)
			except Exception:
				pass

		threading.Thread(target=_do, daemon=True, name="FreeRadio-mirror-timeshift").start()

	def _sync_mirror_exit_to_live(self):
		"""Switch the mirror engine back to the live URL right after the
		main engine does, so it doesn't stay stuck on the time-shift file."""
		mirror = self._get_ready_mirror()
		if mirror is None:
			return
		stream_url = self._current_url_resolved or self._current_url
		if not stream_url:
			return
		vol = self._volume / 100.0

		def _do(m=mirror, u=stream_url, v=vol):
			try:
				m.play(u, v)
			except Exception:
				pass

		threading.Thread(target=_do, daemon=True, name="FreeRadio-mirror-timeshift").start()

	def _sync_mirror_playback_rate(self, rate):
		"""Reapply a just-changed podcast playback rate on the mirror
		engine too, so both outputs stay at the same speed."""
		mirror = self._get_ready_mirror()
		if mirror is None:
			return

		def _do(m=mirror, r=rate):
			try:
				m.set_playback_rate(r)
			except Exception:
				pass

		threading.Thread(target=_do, daemon=True, name="FreeRadio-mirror-rate").start()

	def get_audio_devices(self, fresh=None):
		"""Zwróć listę (indeks, nazwa) dostępnych urządzeń wyjściowych BASS.

		Gdy fresh=True, lista jest pobierana z krótkotrwałego procesu hosta
		BASS. To wymusza aktualne indeksy urządzeń po podłączeniu lub
		odłączeniu wyjścia audio bez restartu NVDA.
		"""
		if self._disable_bass:
			return []
		if fresh is None:
			fresh = self.use_fresh_audio_device_probe()
		if fresh:
			dll_dir = os.path.dirname(os.path.abspath(__file__))
			probe_engine = _BassEngine(dll_dir, output_device=_BASS_DEVICE_DEFAULT)
			try:
				if probe_engine.load() and probe_engine.ready():
					devices = probe_engine.list_devices()
					if devices:
						return devices
			except Exception:
				pass
			finally:
				try:
					probe_engine.unload()
				except Exception:
					pass
		if self._bass_engine and self._bass_engine.ready():
			return self._bass_engine.list_devices()
		return []

	@staticmethod
	def _normalize_audio_device_name(name):
		return " ".join(str(name or "").split()).casefold()

	def resolve_audio_device(self, devices, saved_index=-1, saved_name=""):
		"""Dopasuj zapisane urządzenie do aktualnej listy BASS.

		Zwraca (indeks, nazwa, sposób), gdzie sposób to: "default",
		"name", "index" albo "missing".
		"""
		try:
			saved_index = int(saved_index)
		except Exception:
			saved_index = -1
		if saved_index == -1 and not saved_name:
			return -1, "", "default"

		wanted_name = self._normalize_audio_device_name(saved_name)
		if wanted_name:
			for idx, name in devices:
				if self._normalize_audio_device_name(name) == wanted_name:
					return idx, name, "name"

		for idx, name in devices:
			try:
				if int(idx) == saved_index:
					return idx, name, "index"
			except Exception:
				pass

		return saved_index, saved_name or "", "missing"

	def start_mirror(self, device_index):
		"""Start mirroring the current stream to an additional output device.
		Launches a second bass_host process on device_index and plays the
		same source the main output is already on, so switching on audio
		mirroring continues from where playback already was rather than
		starting over. Three cases:
		- Time-shifted live radio: the mirror opens the same time-shift
		  buffer file, seeked to the main output's current time-shift
		  position, instead of jumping to the live edge.
		- Podcasts: the mirror is opened seekable and seeked to the main
		  output's current position, same as before.
		- Live (non-time-shifted) radio: the mirror just opens the live URL.
		If a podcast playback-rate adjustment is active, it's reapplied on
		the mirror engine too - it's a brand-new subprocess (unlike the
		mirror-resync paths in _bg_launch/_bg_resume, which reuse the
		already-running mirror subprocess and so don't need this), so it
		would otherwise silently come up at normal speed. See the matching
		safety-net comment in _launch().
		Returns True on success, False otherwise.
		"""
		if self._disable_bass:
			return False
		if not self._current_url:
			return False
		self.stop_mirror()
		dll_dir = os.path.dirname(os.path.abspath(__file__))
		mirror_engine = _BassEngine(dll_dir, output_device=device_index)
		if not mirror_engine.load():
			return False
		vol = self._volume / 100.0
		station = self._current_station
		is_podcast = bool(station and "podcast" in station.get("tags", ""))
		timeshifted = self._timeshift_active

		current_pos = 0.0
		if timeshifted:
			pos_ok, current_pos, _length = self.get_playback_position()
			if not pos_ok:
				current_pos = 0.0
			path = self._timeshift_buffer.get_file_path()
			ok = bool(path) and mirror_engine.play_timeshift_file(path, vol, current_pos)
		else:
			url = self._current_url_resolved or self._current_url
			if is_podcast:
				pos_ok, current_pos, _length = self.get_playback_position()
				if not pos_ok:
					current_pos = 0.0
			ok = mirror_engine.play(url, vol, seekable=is_podcast)

		time.sleep(1.0)
		if not ok:
			mirror_engine.unload()
			return False
		if is_podcast and self._playback_rate != 1.0:
			try:
				mirror_engine.set_playback_rate(self._playback_rate)
			except Exception:
				pass
		if not timeshifted and is_podcast and current_pos > 1.0:
			self._resume_podcast_position_on_engine(mirror_engine, current_pos)
		self._mirror_engine	   = mirror_engine
		self._mirror_device_index = device_index
		return True

	def stop_mirror(self):
		"""Stop the mirror output if one is running."""
		engine = getattr(self, "_mirror_engine", None)
		if engine:
			try:
				engine.stop()
				engine.unload()
			except Exception:
				pass
		self._mirror_engine	   = None
		self._mirror_device_index = None

	def get_mirror_device(self):
		"""Return the device index of the active mirror, or None."""
		if self._disable_bass:
			return None
		return getattr(self, "_mirror_device_index", None)

	def switch_output_device(self, device_index):
		"""Przełącz wyjście BASS i zachowaj bieżące odtwarzanie.

		BASS przypina strumień do urządzenia użytego przez proces hosta, więc
		aktywny strumień jest uruchamiany ponownie na świeżo załadowanym hoście
		dla nowego urządzenia. Nazwa stacji, jej dane i głośność zostają
		zachowane.

		device_index: indeks urządzenia BASS; -1 = domyślne systemowe.
		Zwraca indeks urządzenia, które faktycznie zostało wybrane.
		"""
		if self._disable_bass:
			return self._output_device_index

		requested_device_index = device_index
		with self._play_lock:
			was_playing = self._is_playing
			current_url = self._current_url
			current_url_resolved = self._current_url_resolved
			current_name = self._current_name
			current_station = dict(self._current_station or {})

			self._abort_crossfade()
			self._abort_tuning_transition()
			self._stop_icy_thread()

			if self._timeshift_active:
				self._timeshift_active = False
				try:
					self._timeshift_buffer.exit_playback()
				except Exception:
					pass

			if self._bass_engine:
				try:
					self._bass_engine.stop()
					self._bass_engine.unload()
				except Exception:
					pass

			dll_dir = os.path.dirname(os.path.abspath(__file__))
			self._bass_engine = _BassEngine(dll_dir, output_device=device_index)
			self._bass_engine.load()

			if not self._bass_engine.ready() and device_index != -1:
				log.warning(
					"FreeRadio: Device %d unavailable, falling back to system default.",
					device_index,
				)
				try:
					self._bass_engine.unload()
				except Exception:
					pass
				device_index = -1
				self._bass_engine = _BassEngine(dll_dir, output_device=device_index)
				self._bass_engine.load()
				notify_lost = True
			else:
				notify_lost = False

			if self._bass_engine.ready():
				self._bass_engine.on_meta		= self._on_bass_meta
				self._bass_engine.on_connecting  = self._on_bass_connecting
				self._bass_engine.on_stall	   = self._on_bass_stall

			self._output_device_index = device_index
			self._backend			 = self.BACKEND_NONE
			self._is_playing		  = False
			self._intentional_stop	= False
			self._play_gen		   += 1

		if notify_lost:
			cb = self.on_device_lost
			if cb:
				try:
					cb(requested_device_index)
				except Exception:
					pass

		if was_playing and current_url:
			self.play(
				current_url,
				current_name,
				url_resolved=current_url_resolved,
				station=current_station,
			)
		return device_index

	def _device_monitor_loop(self):
		"""Periodically checks for the presence of the selected audio device.

		If it is not in the device list or is disabled, it will return to the system default.
		(index -1) automatically passes and triggers the on_device_lost callback.
		Since BASS can always access the system default (-1), the default
		There is no tracking for the device.
		"""
		_CHECK_INTERVAL = 10   # second
		_BASS_DEVICE_ENABLED = 1

		while not self._watchdog_stop.is_set():
			# 10-second hold — with cancellation control in 0.5s steps
			for _ in range(_CHECK_INTERVAL * 2):
				if self._watchdog_stop.is_set():
					return
				time.sleep(0.5)

			target = self._output_device_index
			if target == -1:
				# System default — no need to monitor
				continue

			try:
				devices = self.get_audio_devices()  # [(index, name), ...]
			except Exception:
				continue

			if not devices:
				# BASS not ready yet or list could not be retrieved — skip
				continue

			# Is the selected device still available?
			found = any(idx == target for idx, _name in devices)
			if found:
				continue

			# Device lost — switch to system default
			lost_index = target
			log.warning(
				"FreeRadio: Audio device %d disappeared, falling back to system default.",
				lost_index,
			)
			try:
				self.switch_output_device(-1)
			except Exception:
				pass

			cb = self.on_device_lost
			if cb:
				try:
					cb(lost_index)
				except Exception:
					pass

	def terminate(self):
		self._watchdog_stop.set()
		self._podcast_autosave_stop.set()
		self.stop_mirror()
		self._abort_crossfade()
		self._abort_tuning_transition()
		self.stop()
		if not self._disable_bass and self._bass_engine:
			self._bass_engine.unload()