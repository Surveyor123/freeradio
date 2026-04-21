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
import urllib.request
import socket
import atexit

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

_BASS_ERROR_SSL      = 41
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
            m = re.search(r"StreamTitle='([^']*)'", meta_raw)
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
        self._proc     = None
        self._lock     = threading.RLock()
        self._ready    = False
        self._icy_title = None
        # The outer layer can assign a connect notification callback.
        self.on_slow_connect = None
        self.on_meta       = None
        # Called if there is no response within 5 seconds; UI may show 'connecting'.
        self.on_connecting = None
        # Called when bass_host sends a stall event.
        self.on_stall      = None
        self._reader_thread = None
        self._stop_reader   = threading.Event()
        self._play_seq     = 0
        self._pending_play = None   # (seq, event, [result])
        self._current_play_seq = None  # Track currently active play request
        atexit.register(self._cleanup)

    def _find_python(self):
        """
        Find a non-elevated pythonw.exe to run bass_host.py as a normal
        (non-admin) subprocess so Windows does not trigger UAC elevation.

        Search order:
        1. Bundled embed Python (eklentinin python/ klasörü) — mimariyle eşleşen
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
        evt    = threading.Event()
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

    def play(self, url, volume_0_1=1.0):
        """Send play command and block until the host confirms success/failure.
        
        If a previous play is still pending, it is cancelled first.
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

        self._send({"cmd": "play", "url": url, "volume": volume_0_1, "seq": seq})

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

    def set_bass_boost(self, boost_0_1):
        """Adjust the bass boost level (0.0 = off, 1.0 = max +12 dB)."""
        self._send({"cmd": "bass_boost", "value": max(0.0, min(1.0, float(boost_0_1)))})

    def set_fx(self, fx_name):
        """Adjust DirectX 8 effect.

        fx_name: "none" | "chorus" | "compressor" | "distortion" |
                 "echo" | "flanger" | "gargle" | "reverb" |
                 "eq_bass" | "eq_treble" | "eq_vocal"
        It is applied instantly on the active stream.
        """
        self._send({"cmd": "set_fx", "fx": fx_name or "none"})

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

    BACKEND_BASS      = "bass"
    BACKEND_VLC       = "vlc"
    BACKEND_POTPLAYER = "potplayer"
    BACKEND_WMP       = "wmp"
    BACKEND_NONE      = "none"

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
        self._audio_fx   = "none"  # active DirectX 8 effect name
        self._intentional_stop = False
        self._play_lock = threading.RLock()  # Prevent concurrent play operations
        self._play_gen  = 0          # Incremented on every play(); bg threads check this

        self._vlc_path        = vlc_path if vlc_path and os.path.isfile(vlc_path) else _find_vlc()
        self._wmp_path        = wmp_path if wmp_path and os.path.isfile(wmp_path) else None
        self._potplayer_path  = potplayer_path if potplayer_path and os.path.isfile(potplayer_path) else _find_potplayer()

        self._backend = self.BACKEND_NONE
        self._proc = None
        self._vbs_path = None

        self._disable_bass = disable_bass

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

        self._watchdog_stop = threading.Event()
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

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
        """Called when bass_host.py sends a stall event.

        Stream is disconnected or frozen—retrying to reconnect
        starts in the background. In case of intentional stop() on_stall is already
        is not called (bass_host checks _meta_stop).
        """
        if self._disable_bass:
            return
        if not self._is_playing or self._intentional_stop:
            return
        url = self._current_url
        vol = self._volume
        if not url:
            return
        log.warning("FreeRadio: BASS stall detected, reconnecting: %s", url)

        # Capture generation at the moment of stall so reconnect thread
        # can detect if a newer play() has already taken over.
        stall_gen = self._play_gen

        def _reconnect(captured_gen=stall_gen):
            if not self._is_playing or self._intentional_stop:
                return
            # Backoff: fast for the first few tries, then slow down
            for wait in (3, 5, 10, 20, 30):
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
                        return
                except Exception:
                    pass
            log.warning("FreeRadio: BASS stall reconnect exhausted")

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


    def update_paths(self, vlc_path=None, wmp_path=None, potplayer_path=None):
        self._vlc_path       = vlc_path if vlc_path and os.path.isfile(vlc_path) else _find_vlc()
        self._wmp_path       = wmp_path if wmp_path and os.path.isfile(wmp_path) else None
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

        # Skip if BASS is disabled
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
        success = self._bass_engine.play(url, volume / 100.0)
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
            return True
        return False

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


    def play(self, url, name="", url_resolved=None, station=None):
        with self._play_lock:
            # Bump generation — any in-flight _bg_launch with an older gen will
            # notice the mismatch and abort before starting audio output.
            self._play_gen += 1
            my_gen = self._play_gen

            # Stop whatever is currently playing / being launched.
            self._stop_current()
            self._stop_icy_thread()

            self._current_url          = url
            self._current_url_resolved = url_resolved or url
            self._current_name         = name
            self._current_station      = station or {}
            self._intentional_stop     = False
            self._is_playing           = True

            vol        = self._volume
            stream_url = url_resolved or url

        def _bg_launch(gen=my_gen):
            # Each blocking step is guarded: if a newer play() arrived while we
            # were busy, our generation is stale — bail out immediately.
            if self._play_gen != gen:
                return
            try:
                self._launch(stream_url, vol, gen=gen)
            except Exception:
                if self._play_gen == gen:
                    self._is_playing = False
                return
            if self._play_gen != gen:
                # A newer play() started while _launch was running; it has
                # already called _stop_current(), so just exit.
                return
            if self._backend != self.BACKEND_BASS:
                self._start_icy_thread(stream_url)
            # Mirror aktifse aynı URL'yi yeni istasyonla güncelle
            if not self._disable_bass:
                mirror = getattr(self, "_mirror_engine", None)
                mirror_dev = getattr(self, "_mirror_device_index", None)
                if mirror is not None and mirror_dev is not None:
                    try:
                        mirror.stop()
                        mirror.play(stream_url, vol / 100.0)
                    except Exception:
                        pass

        threading.Thread(target=_bg_launch, daemon=True, name="FreeRadio-launch").start()

    def pause(self):
        with self._play_lock:
            if not self._is_playing:
                return
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

            if not self._disable_bass and self._backend == self.BACKEND_BASS and self._bass_engine:
                if paused_duration <= _BASS_RESUME_THRESHOLD:
                    self._bass_engine.resume()
                    # Wake up Mirror with a short resume
                    mirror = getattr(self, "_mirror_engine", None)
                    if mirror and mirror.ready():
                        try:
                            mirror.resume()
                        except Exception:
                            pass
                    return
                # Long pause — restart BASS
                self._bass_engine.stop()
                self._backend = self.BACKEND_NONE

            vol = self._volume
            stream_url = self._current_url_resolved or self._current_url

        def _bg_resume(gen=my_gen):
            if self._play_gen != gen:
                return
            try:
                self._launch(stream_url, vol, gen=gen)
            except Exception:
                if self._play_gen == gen:
                    self._is_playing = False
                return
            if self._play_gen != gen:
                return
            if self._backend != self.BACKEND_BASS:
                self._start_icy_thread(stream_url)
            # Restart the mirror after a long pause
            if not self._disable_bass:
                mirror = getattr(self, "_mirror_engine", None)
                if mirror and mirror.ready():
                    try:
                        mirror.stop()
                        mirror.play(stream_url, vol / 100.0)
                    except Exception:
                        pass

        threading.Thread(target=_bg_resume, daemon=True, name="FreeRadio-resume").start()

    def stop(self):
        with self._play_lock:
            self._play_gen += 1
            self._intentional_stop = True
            self._stop_icy_thread()

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

    def get_fx(self):
        return getattr(self, "_audio_fx", "none")

    def get_volume(self):
        return self._volume

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

    def get_audio_devices(self):
        """Return list of (index, name) for all available BASS output devices.
        Uses the primary bass engine's host process. Returns [] if unavailable.
        """
        if self._disable_bass:
            return []
        if self._bass_engine and self._bass_engine.ready():
            return self._bass_engine.list_devices()
        return []

    def start_mirror(self, device_index):
        """Start mirroring the current stream to an additional output device.
        Launches a second bass_host process on device_index and plays the same URL.
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
        url = self._current_url_resolved or self._current_url
        vol = self._volume / 100.0
        ok  = mirror_engine.play(url, vol)
        time.sleep(1.0)
        if not ok:
            mirror_engine.unload()
            return False
        self._mirror_engine       = mirror_engine
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
        self._mirror_engine       = None
        self._mirror_device_index = None

    def get_mirror_device(self):
        """Return the device index of the active mirror, or None."""
        if self._disable_bass:
            return None
        return getattr(self, "_mirror_device_index", None)

    def switch_output_device(self, device_index):
        """Instantly switch audio output device.

        The current playback status is preserved: if the radio is playing, it is on the new device.
        restarts with the same URL.  If it doesn't work, only engine
        reloads; The new device is used on the next playback.

        device_index: BASS device index; -1 = system default.
        """
        if self._disable_bass:
            return
            
        with self._play_lock:
            was_playing  = self._is_playing
            current_url  = self._current_url_resolved or self._current_url
            current_vol  = self._volume

            # Stop and shut down the current engine
            if self._bass_engine:
                try:
                    self._bass_engine.stop()
                    self._bass_engine.unload()
                except Exception:
                    pass

            # Create engine on new device
            dll_dir = os.path.dirname(os.path.abspath(__file__))
            self._bass_engine = _BassEngine(dll_dir, output_device=device_index)
            self._bass_engine.load()

            # Revert to system default if device is not powered on (BASS failed to initialize)
            if not self._bass_engine.ready() and device_index != -1:
                log.warning(
                    "FreeRadio: Device %d unavailable, falling back to system default.",
                    device_index,
                )
                self._bass_engine.unload()
                device_index = -1
                self._bass_engine = _BassEngine(dll_dir, output_device=-1)
                self._bass_engine.load()
                # Trigger callback from here instead of background thread
                _notify_lost = True
            else:
                _notify_lost = False

            if self._bass_engine.ready():
                self._bass_engine.on_meta       = self._on_bass_meta
                self._bass_engine.on_connecting  = self._on_bass_connecting
                self._bass_engine.on_stall       = self._on_bass_stall

            self._backend      = self.BACKEND_NONE
            self._is_playing   = False
            self._intentional_stop = False
            self._play_gen    += 1

        # Update selected device index (-1 if reverted)
        self._output_device_index = device_index

        # Device was not on — trigger on_device_lost callback outside
        if _notify_lost:
            cb = self.on_device_lost
            if cb:
                try:
                    cb(device_index)
                except Exception:
                    pass

        # If it was playing, restart (outside lock — no risk of deadlock)
        if was_playing and current_url:
            self.play(self._current_url, current_vol)

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
        self.stop_mirror()
        self.stop()
        if not self._disable_bass and self._bass_engine:
            self._bass_engine.unload()