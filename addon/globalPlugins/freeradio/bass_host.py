# -*- coding: utf-8 -*-
"""
bass_host.py — FreeRadio BASS subprocess host.

Runs as a standalone process so that BASS audio appears as a separate
entry in the Windows volume mixer (independent from nvda.exe).

Protocol: newline-delimited JSON on stdin/stdout.
  stdin  ← commands from parent  {"cmd": "play", "url": "...", "volume": 0.8}
  stdout → responses to parent   {"ok": true} / {"ok": false, "error": "..."}
                                  {"event": "meta", "title": "..."}

Supported commands:
  play       {"cmd":"play",       "url":"...", "volume":0.0-1.0, "seekable":false}
             "seekable":true opens the URL without BASS_STREAM_BLOCK so the
             stream supports BASS_ChannelSetPosition (e.g. podcast episodes).
             Live radio should leave this false (default) for robustness.
  stop       {"cmd":"stop"}
  pause      {"cmd":"pause"}
  resume     {"cmd":"resume"}
  volume     {"cmd":"volume",     "value":0.0-2.0}
  bass_boost {"cmd":"bass_boost", "value":0.0-1.0}
  set_playback_rate {"cmd":"set_playback_rate", "rate":0.5-3.0}  # pitch-preserving, podcasts only (needs bass_fx.dll)
  ping       {"cmd":"ping"}
  quit       {"cmd":"quit"}

Time-shift (local buffer file) commands:
  timeshift_play     {"cmd":"timeshift_play", "path":"...", "volume":0.0-1.0, "start_seconds":0.0}
  timeshift_seek     {"cmd":"timeshift_seek", "delta_seconds":-15.0}
  timeshift_status   {"cmd":"timeshift_status"}
"""

import ctypes
import json
import os
import sys
import tempfile
import threading
import time
import re
import urllib.request
import socket
import atexit

# Standalone process, no access to NVDA's `log` — appends to the same shared
# debug file timeshift.py and radioPlayer.py use, so one time-shift failure
# can be traced across all three in chronological order.
_DEBUG_LOG_PATH = os.path.join(tempfile.gettempdir(), "freeradio_timeshift_debug.log")

# Off by default, matching timeshift.py's own _DEBUG_ENABLED — this file
# previously had no gate at all and wrote unconditionally, so disabling
# debug logging in timeshift.py had no effect on it.
_DEBUG_ENABLED = True


def _debug_log(msg):
    if not _DEBUG_ENABLED:
        return
    try:
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write("%s [bass_host.py] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass

# Constants (mirrors radioPlayer.py)
_BASS_ATTRIB_VOL          = 2
_BASS_TAG_META            = 5
_BASS_CONFIG_NET_TIMEOUT  = 11
_BASS_CONFIG_NET_HTTPS_FLAG = 71
_BASS_CONFIG_NET_SSL      = 73
_BASS_CONFIG_NET_SSL_VERIFY = 74
_BASS_CONFIG_NET_PLAYLIST = 21
_BASS_CONFIG_NET_PREBUF   = 15
_BASS_CONFIG_NET_READTIMEOUT = 37
_BASS_ERROR_ALREADY       = 8
_BASS_ERROR_FILEFORM      = 40
_BASS_ERROR_NOTAVAIL      = 37
_BASS_ERROR_SSL           = 41
_BASS_STREAM_BLOCK        = 0x100000
_BASS_STREAM_DECODE       = 0x200000  # source-only stream, feeds into BASS_FX_TempoCreate
_BASS_FX_FREESOURCE       = 0x10000   # BASS_FX_TempoCreate: free the source stream when the tempo one is freed
_BASS_ATTRIB_TEMPO        = 0x10000   # BASS_FX attribute id: tempo change in % (-95..+5000, 0 = normal)
_BASS_ACTIVE_STOPPED      = 0
_BASS_ACTIVE_PLAYING      = 1
_BASS_ACTIVE_STALLED      = 2
_BASS_ACTIVE_PAUSED       = 3
_BASS_DATA_AVAILABLE      = 0   # flag for BASS_ChannelGetData — returns buffered bytes
_BASS_POS_BYTE            = 0   # mode for BASS_ChannelGetPosition — byte position
_BASS_UNICODE             = 0x80000000  # flag for BASS_StreamCreateFile — file path is a wide string

# Keep timeshift_seek() forward seeks this many seconds short of the
# time-shift buffer file's growing tail (see timeshift_seek() below).
_TIMESHIFT_TAIL_SAFETY_SECONDS = 2.0

# basshls.dll config constants
_BASS_CONFIG_HLS_BANDWIDTH = 0x10400  # master playlist'te bitrate selection
_BASS_CONFIG_HLS_DELAY     = 0x10401  # live stream delay (seconds); default 30

# FX constants (DirectX 8 effects — bass.dll built-in, no additional DLL required)
# Official BASS rankings (from bass.h):
# 0=CHORUS, 1=COMPRESSOR, 2=DISTORTION, 3=ECHO, 4=FLANGER,
# 5=GARGLE, 6=I3DL2REVERB(*), 7=PARAMEQ, 8=REVERB
# (*) I3DL2REVERB has been removed in Windows 11 24H2 — obsolete.
_BASS_FX_DX8_CHORUS     = 0
_BASS_FX_DX8_COMPRESSOR = 1
_BASS_FX_DX8_DISTORTION = 2
_BASS_FX_DX8_ECHO       = 3
_BASS_FX_DX8_FLANGER    = 4
_BASS_FX_DX8_GARGLE     = 5
#6 = I3DL2REVERB — Removed in Windows 11 24H2, not added to the list
_BASS_FX_DX8_PARAMEQ    = 7
_BASS_FX_DX8_REVERB     = 8

_FX_NAME_TO_TYPE = {
    "none":         None,
    "chorus":       _BASS_FX_DX8_CHORUS,
    "compressor":   _BASS_FX_DX8_COMPRESSOR,
    "distortion":   _BASS_FX_DX8_DISTORTION,
    "echo":         _BASS_FX_DX8_ECHO,
    "flanger":      _BASS_FX_DX8_FLANGER,
    "gargle":       _BASS_FX_DX8_GARGLE,
    "reverb":       _BASS_FX_DX8_REVERB,
    # ParamEQ presets — each with gain applied via BASS_FXSetParameters
    "eq_bass":      _BASS_FX_DX8_PARAMEQ,   # Bass Boost  (~100 Hz +9 dB)
    "eq_treble":    _BASS_FX_DX8_PARAMEQ,   # Treble Boost (~8000 Hz +9 dB)
    "eq_vocal":     _BASS_FX_DX8_PARAMEQ,   # Vocal Boost  (~2500 Hz +6 dB)
}

# ParamEQ preset parameters: {fCenter_Hz, fBandwidth_semitones, fGain_dB}
# fBandwidth: 1–36 semitones — 18 ≈ 1.5 octaves according to DirectX documentation
# fGain_dB: default gain; can be overridden at runtime via set_eq_gain command.
_PARAMEQ_PRESETS = {
    "eq_bass":    (100.0,  18.0,  9.0),
    "eq_treble":  (8000.0, 18.0,  9.0),
    "eq_vocal":   (2500.0, 12.0,  6.0),
}

# Runtime gain overrides — populated by set_eq_gain command.
# Keys: "eq_bass" | "eq_treble" | "eq_vocal"  Values: dB (float, -15..+15)
_PARAMEQ_GAIN_OVERRIDE: dict = {}

# Stdout helpers — all communication goes through stdout as JSON lines.
# stderr is used only for fatal startup errors.
_stdout_lock = threading.Lock()


def _send(obj):
    line = json.dumps(obj, ensure_ascii=False)
    with _stdout_lock:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()


def _ok(**kwargs):
    _send({"ok": True, **kwargs})


def _err(msg):
    _send({"ok": False, "error": str(msg)})


def _event(**kwargs):
    _send({"event": True, **kwargs})


# Playlist resolver (same logic as radioPlayer.py)
def _resolve_playlist_url(url, timeout=8):
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "FreeRadio-NVDA/1.0", "Icy-MetaData": "1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final_url = resp.url if hasattr(resp, "url") else url
            ct = (resp.headers.get("content-type") or "").lower().split(";")[0].strip()
            data = resp.read(8192).decode("utf-8", "ignore")

        # Calculate base URL to convert relative URL to absolute URL
        from urllib.parse import urljoin
        base_url = final_url

        audio_types = ("audio/", "application/ogg", "video/")
        if any(ct.startswith(t) for t in audio_types):
            return final_url

        if ct in ("audio/x-mpegurl", "application/x-mpegurl",
                  "audio/mpegurl", "application/vnd.apple.mpegurl") \
                or url.lower().endswith((".m3u", ".m3u8")):
            for line in data.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    return urljoin(base_url, line)

        if ct == "audio/x-scpls" or url.lower().endswith(".pls"):
            for line in data.splitlines():
                if line.lower().startswith("file1="):
                    return urljoin(base_url, line.split("=", 1)[1].strip())

        if ct in ("video/x-ms-asf", "audio/x-ms-wax", "audio/x-ms-wmx") or \
                any(url.lower().endswith(e) for e in (".asx", ".wmx", ".wax")):
            m = re.search(r"href\s*=\s*[\"']([^\"']+)[\"']", data, re.IGNORECASE)
            if m:
                return urljoin(base_url, m.group(1))
    except Exception:
        pass
    return url


# BASS engine
class BassHost:
    def __init__(self, dll_dir, device_index=-1):
        self._dll_dir     = dll_dir
        self._device_index = device_index  # -1 = system default
        self._dll      = None
        self._dll_hls  = None
        self._bass_fx_dll = None  # bass_fx.dll - optional, only used for
                                  # pitch-preserving podcast playback speed
        self._tempo_active = False  # True while self._handle is a BASS_FX
                                     # tempo-wrapped stream (podcasts only)
        self._playback_rate = 1.0   # persists across episodes, like volume
        self._handle   = 0
        self._lock     = threading.RLock()
        self._meta_stop   = threading.Event()
        self._meta_thread = None
        self._current_play_thread = None
        self._current_play_seq = None
        self._pending_response = None
        # Cache successful resolve chains: original_url → (employee_url, timestamp)
        # Segment URLs (like TRT) are ephemeral — they are not cached.
        self._resolve_cache = {}
        self._CACHE_TTL = 300  # seconds — Resolve after 5 minutes
        # Amplification (>1.0): Applied with DSP callback.
        self._gain = 1.0          # current gain multiplier (1.0 = normal)
        self._dsp_handle = 0      # handle from BASS_ChannelSetDSP
        self._dsp_proc_ref = None # Reference to protect DSP callback from GC
        # Bass boost: 0.0 = off, 1.0 = maximum (+12 dB low-shelf @ ~150 Hz)
        self._bass_boost = 0.0
        # Separate handle/ref for bass boost DSP
        self._bass_dsp_handle = 0
        self._bass_dsp_proc_ref = None
        # Low-shelf IIR filter status (separate for left/right channel)
        self._bass_x1 = [0.0, 0.0]  # previous entry examples
        self._bass_y1 = [0.0, 0.0]  # previous output examples
        # FX: set of active effect names and handles returned from BASS_ChannelSetFX
        self._fx_names   = set()   # active effect names
        self._fx_handles = {}      # {fx_name: handle}


    @staticmethod
    def enumerate_devices(dll):
        """Return list of (index, name) for all available BASS output devices."""
        devices = []

        _BASS_DEVICE_ENABLED = 1

        # Try the Unicode build first (BASS_GetDeviceInfoW — available in some versions)
        class _BASS_DEVICE_INFO_W(ctypes.Structure):
            _fields_ = [
                ("name",   ctypes.c_wchar_p),
                ("driver", ctypes.c_wchar_p),
                ("flags",  ctypes.c_uint32),
            ]

        class _BASS_DEVICE_INFO_A(ctypes.Structure):
            _fields_ = [
                ("name",   ctypes.c_char_p),
                ("driver", ctypes.c_char_p),
                ("flags",  ctypes.c_uint32),
            ]

        use_unicode = hasattr(dll, "BASS_GetDeviceInfoW")

        i = 1  # BASS device indices start at 1; 0 = no sound
        while True:
            try:
                if use_unicode:
                    info = _BASS_DEVICE_INFO_W()
                    ok = dll.BASS_GetDeviceInfoW(i, ctypes.byref(info))
                    if not ok:
                        break
                    if info.flags & _BASS_DEVICE_ENABLED:
                        name = info.name or f"Device {i}"
                        devices.append((i, name))
                else:
                    info = _BASS_DEVICE_INFO_A()
                    ok = dll.BASS_GetDeviceInfo(i, ctypes.byref(info))
                    if not ok:
                        break
                    if info.flags & _BASS_DEVICE_ENABLED:
                        raw = info.name
                        if raw:
                            # Decode with system code page (mbcs);
                            # if that fails latin-1, last resort utf-8.
                            name = None
                            for enc in ("mbcs", "latin-1", "utf-8"):
                                try:
                                    name = raw.decode(enc)
                                    break
                                except (UnicodeDecodeError, LookupError):
                                    continue
                            if name is None:
                                name = raw.decode("utf-8", errors="replace")
                        else:
                            name = f"Device {i}"
                        devices.append((i, name))
            except Exception:
                break
            i += 1
        return devices

    def load(self):
        is64 = ctypes.sizeof(ctypes.c_voidp) == 8
        bass_subdir = "bass/x64" if is64 else "bass"
        base_dll_dir = os.path.join(self._dll_dir, bass_subdir)
        bass_path = os.path.join(base_dll_dir, "bass.dll")

        if not os.path.isfile(bass_path):
            return False, f"DLL not found: {bass_path}"

        try:
            dll = ctypes.WinDLL(bass_path)
        except Exception as e:
            return False, f"Could not load DLL: {e}"

        if not dll.BASS_Init(self._device_index, 44100, 0, None, None):
            err = dll.BASS_ErrorGetCode()
            if err != _BASS_ERROR_ALREADY:
                return False, f"BASS_Init failed (err={err})"

        dll.BASS_SetConfig(_BASS_CONFIG_NET_HTTPS_FLAG, 1)
        dll.BASS_SetConfig(_BASS_CONFIG_NET_TIMEOUT, 12000)     # ms — 12s; Increased for slow servers (qingting.fm etc.)
        dll.BASS_SetConfig(_BASS_CONFIG_NET_READTIMEOUT, 12000) # ms
        dll.BASS_SetConfig(_BASS_CONFIG_NET_PREBUF, 0)
        dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL, 1)
        dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL_VERIFY, 0)
        dll.BASS_SetConfig(_BASS_CONFIG_NET_PLAYLIST, 1)

        # Plugin list: only existing ones are loaded
        for plugin in ['bass_aac', 'basshls', 'bassopus', 'bassflac', 'basswma']:
            plugin_file = f"{plugin}.dll"
            plugin_path = os.path.join(base_dll_dir, plugin_file)
            if os.path.isfile(plugin_path):
                try:
                    result = dll.BASS_PluginLoad(plugin_path.encode("mbcs"), 0)
                except Exception:
                    pass
                if plugin == 'basshls':
                    try:
                        # BASS_PluginLoad completed successfully — basshls.dll
# loaded into process. Now use the BASS_HLS_StreamCreateURL function
                        #find. Three strategies are tried in order:
                        # 1. Via bass.dll (accessible after installing the plugin)
                        # 2. With ctypes.cdll (different calling convention attempt than WinDLL)
                        #3. Manual search with kernel32.GetProcAddress
                        _fn = None

                        # Strategy 1: via bass.dll
                        try:
                            _fn = dll.BASS_HLS_StreamCreateURL
                            _fn.restype  = ctypes.c_ulong
                            _fn.argtypes = [
                                ctypes.c_char_p,
                                ctypes.c_uint32,
                                ctypes.c_void_p,
                                ctypes.c_void_p,
                            ]
                        except AttributeError:
                            _fn = None

                        # Strategy 2: WinDLL — add_dll_directory
                        if _fn is None:
                            _cookie = None
                            try:
                                if hasattr(os, "add_dll_directory"):
                                    _cookie = os.add_dll_directory(base_dll_dir)
                                _hls_dll = ctypes.WinDLL(plugin_path)
                                _fn = _hls_dll.BASS_HLS_StreamCreateURL
                                _fn.restype  = ctypes.c_ulong
                                _fn.argtypes = [
                                    ctypes.c_char_p,
                                    ctypes.c_uint32,
                                    ctypes.c_void_p,
                                    ctypes.c_void_p,
                                ]
                                self._dll_hls = _hls_dll
                            except Exception:
                                _fn = None
                            finally:
                                if _cookie is not None:
                                    try: _cookie.close()
                                    except Exception: pass

                        # Strategy 3: GetProcAddress
                        if _fn is None:
                            try:
                                _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
                                _k32.GetModuleHandleW.restype  = ctypes.c_void_p
                                _k32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
                                _k32.GetProcAddress.restype    = ctypes.c_void_p
                                _k32.GetProcAddress.argtypes   = [ctypes.c_void_p, ctypes.c_char_p]
                                _hmod = _k32.GetModuleHandleW(plugin_path)
                                if _hmod:
                                    _addr = _k32.GetProcAddress(_hmod, b"BASS_HLS_StreamCreateURL")
                                    if _addr:
                                        _fn = ctypes.CFUNCTYPE(
                                            ctypes.c_ulong,
                                            ctypes.c_char_p,
                                            ctypes.c_uint32,
                                            ctypes.c_void_p,
                                            ctypes.c_void_p,
                                        )(_addr)
                            except Exception:
                                pass

                        if _fn is not None:
                            if self._dll_hls is None:
                                class _HlsProxy:
                                    def __init__(self, fn):
                                        self.BASS_HLS_StreamCreateURL = fn
                                self._dll_hls = _HlsProxy(_fn)
                            # 3s live delay: Provides sufficient buffer for smartstream.ne.jp,
                            # It also reduces the startup delay to 5s→3s.
                            # Live delay: 8s provides enough buffer for CDN-backed HLS streams
                            # (e.g. TRT) that produce segments every 6-8s.
                            # 3s was too aggressive and caused underruns on slow CDN responses.
                            dll.BASS_SetConfig(_BASS_CONFIG_HLS_DELAY, 3)
                    except Exception:
                        self._dll_hls = None

        # bass_fx.dll (optional, separate add-on library from un4seen.com) -
        # enables pitch-preserving playback speed control for podcasts.
        # Not a BASS_PluginLoad-style plugin; it's loaded directly and its
        # BASS_ATTRIB_TEMPO/etc. attributes are then used through the
        # normal BASS_ChannelSetAttribute on streams it has wrapped.
        # Absent entirely if the user hasn't downloaded/placed the DLL -
        # every caller must check self._bass_fx_dll before relying on it.
        bass_fx_path = os.path.join(base_dll_dir, "bass_fx.dll")
        if os.path.isfile(bass_fx_path):
            try:
                fx_dll = ctypes.WinDLL(bass_fx_path)
                fx_dll.BASS_FX_TempoCreate.restype = ctypes.c_ulong
                fx_dll.BASS_FX_TempoCreate.argtypes = [
                    ctypes.c_ulong, ctypes.c_uint32,
                ]
                self._bass_fx_dll = fx_dll
            except Exception:
                self._bass_fx_dll = None

        self._dll = dll
        dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL_VERIFY, 0)
        dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL, 1)
        # BASS_ChannelGetPosition returns a QWORD; ctypes defaults unconfigured
        # functions to a 32-bit c_int return, which would silently truncate
        # the byte position on long-running streams. Used by the position-
        # based stall check in _monitor_loop (see _BASS_POS_BYTE).
        try:
            dll.BASS_ChannelGetPosition.restype  = ctypes.c_int64
            dll.BASS_ChannelGetPosition.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        except Exception:
            pass

        # Additional prototypes needed for time-shift (local file) playback:
        # seeking and length/position queries all use 64-bit byte offsets or
        # double-precision seconds, which ctypes would otherwise truncate to
        # a 32-bit int if left unconfigured.
        try:
            dll.BASS_StreamCreateFile.restype  = ctypes.c_uint32
            dll.BASS_StreamCreateFile.argtypes = [
                ctypes.c_int32, ctypes.c_wchar_p,
                ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint32,
            ]
            dll.BASS_ChannelGetLength.restype  = ctypes.c_int64
            dll.BASS_ChannelGetLength.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
            dll.BASS_ChannelBytes2Seconds.restype  = ctypes.c_double
            dll.BASS_ChannelBytes2Seconds.argtypes = [ctypes.c_uint32, ctypes.c_int64]
            dll.BASS_ChannelSeconds2Bytes.restype  = ctypes.c_int64
            dll.BASS_ChannelSeconds2Bytes.argtypes = [ctypes.c_uint32, ctypes.c_double]
            dll.BASS_ChannelSetPosition.restype  = ctypes.c_int32
            dll.BASS_ChannelSetPosition.argtypes = [ctypes.c_uint32, ctypes.c_int64, ctypes.c_uint32]
        except Exception:
            pass
        return True, "ok"

    def _cancel_pending_play(self):
        """Cancel any pending play operation and stop current stream."""
        with self._lock:
            if self._current_play_thread and self._current_play_thread.is_alive():
                # Thread will check self._current_play_seq mismatch and abort
                pass
            self._current_play_seq = None
            
            # Immediately stop any playing stream
            if self._handle and self._dll:
                try:
                    self._dll.BASS_ChannelStop(self._handle)
                    self._dll.BASS_StreamFree(self._handle)
                except Exception:
                    pass
                self._handle = 0
                # FX handles belong to the freed stream — clear so _apply_fx
                # re-registers them on the next stream instead of skipping.
                self._fx_handles = {}
            
            # Notify waiting caller that this operation is cancelled
            if self._pending_response:
                seq, evt, result_slot = self._pending_response
                result_slot[0] = False
                evt.set()
                self._pending_response = None

    def _try_download_and_play(self, url):
        """Download URL to a temp file and play it via BASS_StreamCreateFile.
        Returns stream handle or 0 on failure. Does NOT cache the file.
        """
        import tempfile
        import urllib.request

        try:
            fd, path = tempfile.mkstemp(prefix="freeradio_podcast_", suffix=".mp3")
            os.close(fd)
        except Exception as e:
            _debug_log("download temp file creation failed: %s" % e)
            return 0

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FreeRadio-NVDA/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                with open(path, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
        except Exception as e:
            _debug_log("download failed: %s" % e)
            try:
                os.remove(path)
            except OSError:
                pass
            return 0

        try:
            stream = self._dll.BASS_StreamCreateFile(
                ctypes.c_int32(0),
                ctypes.c_wchar_p(path),
                ctypes.c_uint64(0),
                ctypes.c_uint64(0),
                ctypes.c_uint32(_BASS_UNICODE),
            )
            if stream:
                # Store the path for cleanup, but don't cache it
                self._downloaded_file_path = path
                _debug_log("download OK, playing from %s" % path)
                return stream
            else:
                err = self._dll.BASS_ErrorGetCode()
                _debug_log("BASS_StreamCreateFile failed, err=%d" % err)
                try:
                    os.remove(path)
                except OSError:
                    pass
                return 0
        except Exception as e:
            _debug_log("BASS_StreamCreateFile exception: %s" % e)
            try:
                os.remove(path)
            except OSError:
                pass
            return 0

    def _try_create_local_file(self, path, seekable=False):
        """Opens a local audio file via BASS_StreamCreateFile - the
        counterpart to _try_create_url() for content that's already on
        disk (currently: a GETEM audio-book chapter downloaded ahead of
        playback, see getem.download_chapter()). Deliberately not routed
        through BASS_StreamCreateURL: passing it a plain filesystem path
        can happen to open something playable, but the resulting stream
        isn't reliably seekable afterwards (BASS_ChannelSetPosition fails
        on it) - the same class of BASS_ERROR_NOTAVAIL quirk already
        worked around for the live-radio time-shift buffer file (see
        play_timeshift_file()). BASS_StreamCreateFile doesn't have that
        problem, so local files go straight to it instead.

        Mirrors the seekable branch of _try_create_url()'s DECODE +
        BASS_FX tempo-wrap logic, so local-file playback (GETEM chapters)
        gets the same pitch-preserving playback-rate support podcasts do."""
        use_tempo = seekable and bool(self._bass_fx_dll)
        stream = self._dll.BASS_StreamCreateFile(
            ctypes.c_int32(0), ctypes.c_wchar_p(path),
            ctypes.c_uint64(0), ctypes.c_uint64(0),
            ctypes.c_uint32((_BASS_STREAM_DECODE if use_tempo else 0) | _BASS_UNICODE),
        )
        if stream and use_tempo:
            tempo_stream = self._bass_fx_dll.BASS_FX_TempoCreate(
                stream, ctypes.c_uint32(_BASS_FX_FREESOURCE)
            )
            if tempo_stream:
                stream = tempo_stream
                self._tempo_active = True
                if self._playback_rate != 1.0:
                    try:
                        self._dll.BASS_ChannelSetAttribute(
                            stream, _BASS_ATTRIB_TEMPO,
                            ctypes.c_float((self._playback_rate - 1.0) * 100.0),
                        )
                    except Exception:
                        pass
            else:
                # Wrap failed - the decode-only stream is unplayable on
                # its own; drop it and get a normal (non-decode) file
                # stream so playback still works, just without rate
                # control for this file.
                try:
                    self._dll.BASS_StreamFree(stream)
                except Exception:
                    pass
                self._tempo_active = False
                stream = self._dll.BASS_StreamCreateFile(
                    ctypes.c_int32(0), ctypes.c_wchar_p(path),
                    ctypes.c_uint64(0), ctypes.c_uint64(0),
                    ctypes.c_uint32(_BASS_UNICODE),
                )
        if stream:
            _debug_log("local file stream opened: %s" % path)
        else:
            try:
                err = self._dll.BASS_ErrorGetCode()
            except Exception:
                err = -1
            _debug_log("BASS_StreamCreateFile failed for local file, err=%d: %s" % (err, path))
        return stream

    def _try_create_url(self, url, seekable=False):
        # Reset up front — only the seekable/tempo-wrap path below sets this
        # back to True, so a stale value from a previous podcast session
        # never lingers onto an unrelated live-radio stream.
        if not seekable:
            self._tempo_active = False

        # A plain local filesystem path (not an http/https URL) - route to
        # BASS_StreamCreateFile instead of treating it as a network URL;
        # see _try_create_local_file() for why.
        if not url.lower().startswith(("http://", "https://")) and os.path.isfile(url):
            return self._try_create_local_file(url, seekable=seekable)

        url_lower = url.split("?")[0].lower()
        is_hls = url_lower.endswith(".m3u8")
        is_aac_ext = url_lower.endswith(".aac")
        looks_like_aac = is_aac_ext or "aac" in url_lower

        # HLS
        if is_hls and self._dll_hls:
            stream = self._dll_hls.BASS_HLS_StreamCreateURL(
                url.encode("utf-8"),
                ctypes.c_uint32(_BASS_STREAM_BLOCK),
                ctypes.c_void_p(0),
                ctypes.c_void_p(0),
            )
            if stream:
                return stream
            # Akamai CDN HLS stream's (mediaserviceslive.akamaized.net vb.)
            # Can play intermittently with BASS_HLS; Try with BASS_StreamCreateURL.
            _akamai_hosts = ("akamaized.net", "akamaihd.net", "akamai.net")
            if any(h in url_lower for h in _akamai_hosts):
                stream = self._dll.BASS_StreamCreateURL(
                    url.encode("utf-8"),
                    ctypes.c_uint32(0), ctypes.c_uint32(_BASS_STREAM_BLOCK),
                    ctypes.c_void_p(0), ctypes.c_void_p(0),
                )
                if stream:
                    return stream
            if is_hls and not self._dll_hls and url_lower.startswith("https"):
                return 0

        is_https = url_lower.startswith("https://")
        is_http  = url_lower.startswith("http://")

        # HTTPS Icecast workaround — bypass BASS's SSL layer entirely.
        if is_https and not seekable:
            stream = self._try_https_local_proxy(url, seekable=seekable)
            if stream:
                return stream

        # For HTTP, disable SSL completely and also try with custom headers via a small hack
        # Some Shoutcast servers require "Icy-MetaData: 1" header.
        # BASS doesn't send it by default, but we can set BASS_CONFIG_NET_META=1 already.
        ssl_saved = None
        if is_http:
            try:
                ssl_saved = self._dll.BASS_GetConfig(_BASS_CONFIG_NET_SSL)
                self._dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL, 0)
            except:
                pass

        try:
            if seekable:
                # Try without BLOCK first — request a plain decode-only
                # stream when bass_fx is available so it can be wrapped for
                # pitch-preserving playback-rate control (podcasts only;
                # "seekable" is only ever True for podcast playback). A
                # decode-only stream can't be played directly, so if the
                # wrap step fails for any reason, fall back to a normal
                # (non-decode) stream instead of leaving playback broken.
                use_tempo = bool(self._bass_fx_dll)
                stream = self._dll.BASS_StreamCreateURL(
                    url.encode("utf-8"),
                    ctypes.c_uint32(0),
                    ctypes.c_uint32(_BASS_STREAM_DECODE if use_tempo else 0),
                    ctypes.c_void_p(0),
                    ctypes.c_void_p(0),
                )
                if stream and use_tempo:
                    tempo_stream = self._bass_fx_dll.BASS_FX_TempoCreate(
                        stream, ctypes.c_uint32(_BASS_FX_FREESOURCE)
                    )
                    if tempo_stream:
                        stream = tempo_stream
                        self._tempo_active = True
                        if self._playback_rate != 1.0:
                            try:
                                self._dll.BASS_ChannelSetAttribute(
                                    stream, _BASS_ATTRIB_TEMPO,
                                    ctypes.c_float((self._playback_rate - 1.0) * 100.0),
                                )
                            except Exception:
                                pass
                    else:
                        # Wrap failed — the decode-only stream is unplayable
                        # on its own; drop it and get a normal stream so
                        # podcast playback still works, just without rate
                        # control for this episode.
                        try:
                            self._dll.BASS_StreamFree(stream)
                        except Exception:
                            pass
                        self._tempo_active = False
                        stream = self._dll.BASS_StreamCreateURL(
                            url.encode("utf-8"), ctypes.c_uint32(0), ctypes.c_uint32(0),
                            ctypes.c_void_p(0), ctypes.c_void_p(0),
                        )
                else:
                    self._tempo_active = False
                if stream:
                    # Do NOT check length; just return and hope it's seekable.
                    # If it's not seekable, timeshift_seek will fail.
                    _debug_log("seekable stream opened without length check: %s" % url)
                    return stream
                else:
                    # If opening fails, fall back to download
                    self._tempo_active = False
                    _debug_log("seekable stream failed, trying download: %s" % url)
                    return self._try_download_and_play(url)
            else:
                # Live radio: try BLOCK first, then 0 as fallback
                for _flags in (_BASS_STREAM_BLOCK, 0):
                    stream = self._dll.BASS_StreamCreateURL(
                        url.encode("utf-8"),
                        ctypes.c_uint32(0), ctypes.c_uint32(_flags),
                        ctypes.c_void_p(0), ctypes.c_void_p(0),
                    )
                    if stream:
                        return stream

                # Last resort: use urllib to get the real stream URL (might be redirected)
                if is_http:
                    try:
                        import urllib.request
                        req = urllib.request.Request(url, headers={"User-Agent": "Winamp/5.8", "Icy-MetaData": "1"})
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            final_url = resp.geturl()
                            if final_url != url:
                                stream = self._dll.BASS_StreamCreateURL(
                                    final_url.encode("utf-8"),
                                    ctypes.c_uint32(0), ctypes.c_uint32(0 if seekable else _BASS_STREAM_BLOCK),
                                    ctypes.c_void_p(0), ctypes.c_void_p(0),
                                )
                                if stream:
                                    return stream
                    except:
                        pass
                return 0
        finally:
            if ssl_saved is not None:
                try:
                    self._dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL, ssl_saved)
                except:
                    pass

    def _connect_https_ipv4(self, url_parts, headers, ssl_ctx, timeout):
        """Connect directly over IPv4 (bypassing urllib's default dual-stack
        address resolution) and return an http.client.HTTPResponse.

        Some hosts (icecast.walmradio.com observed) have a slow/unreachable
        IPv6 address that Python's standard connection logic tries FIRST and
        waits out the full timeout on before falling back to a fast IPv4
        address — there is no Happy-Eyeballs-style racing in the stdlib for
        plain urllib.request. Restricting resolution to AF_INET up front
        skips that wasted wait entirely on hosts where it applies.

        Raises on any failure (including hosts with no IPv4 address at all)
        — callers should catch and fall back to the standard urllib path.
        """
        import socket as _socket
        import http.client

        host = url_parts.hostname
        port = url_parts.port or 443
        path = url_parts.path or "/"
        if url_parts.query:
            path += "?" + url_parts.query

        infos = _socket.getaddrinfo(host, port, _socket.AF_INET, _socket.SOCK_STREAM)
        if not infos:
            raise OSError(f"no IPv4 address found for {host}")

        last_exc = None
        for family, socktype, proto, _canon, sockaddr in infos:
            raw = None
            try:
                raw = _socket.socket(family, socktype, proto)
                raw.settimeout(timeout)
                raw.connect(sockaddr)
                ssl_sock = ssl_ctx.wrap_socket(raw, server_hostname=host)
                ssl_sock.settimeout(timeout)

                req_lines = [f"GET {path} HTTP/1.1", f"Host: {host}"]
                for k, v in headers.items():
                    req_lines.append(f"{k}: {v}")
                req_lines.append("Connection: close")
                req_lines.append("")
                req_lines.append("")
                ssl_sock.sendall("\r\n".join(req_lines).encode("ascii"))

                resp = http.client.HTTPResponse(ssl_sock, method="GET")
                resp.begin()
                return resp
            except Exception as e:
                last_exc = e
                try:
                    if raw:
                        raw.close()
                except Exception:
                    pass
                continue

        raise last_exc or OSError(f"could not connect to any IPv4 address for {host}")

    def _try_https_local_proxy(self, url, seekable=False):
        """Proxy an HTTPS Icecast stream through a local TCP socket for BASS.

        BASS fails with BASS_ERROR_FILEFORM (err=40) on HTTPS Icecast streams
        that send ICY headers immediately after the TLS handshake (e.g.
        icecast.walmradio.com). This method works around the issue by:

          1. Opening the HTTPS connection first — trying a direct IPv4-only
             connection (fast path, see _connect_https_ipv4) before falling
             back to standard urllib (slower, dual-stack) if that fails.
          2. Only AFTER the remote is ready: opening a local loopback TCP
             server and pointing BASS at http://127.0.0.1:<port>.
          3. Running a background thread that immediately answers BASS's HTTP
             request (headers are already known) and then forwards audio bytes.

        Connecting remote first (sequential, not parallel) means BASS always
        gets an instant HTTP response from the proxy — its own NET_READTIMEOUT
        never triggers, so we never need to touch BASS_SetConfig globally.
        The cost is that the caller blocks until the remote connects, but this
        method is always called from a background play thread so it does not
        stall NVDA's UI, and the user was already going to wait for the
        remote to connect anyway.
        """
        import socket as _socket
        import ssl as _ssl
        import urllib.request
        import urllib.parse

        # icecast.walmradio.com's connect time has been observed at both
        # 20.5s and 42.5s across separate test runs — i.e. genuinely slow
        # and variable, not a fixed quantity. 30s is the ceiling for the
        # (rarely-needed) dual-stack fallback path; the IPv4 fast path below
        # uses its own short 8s timeout since it should either connect
        # quickly or not at all.
        CONNECT_TIMEOUT = 30   # seconds — fallback-path urllib timeout
        CHUNK           = 8192 # bytes per forwarding iteration

        ssl_ctx = _ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode    = _ssl.CERT_NONE

        # --- Step 1: establish the remote HTTPS connection first ---
        # We block here (in the background play thread) until the server
        # responds. Only then do we set up the local proxy, so BASS never
        # has to wait for a slow TLS handshake on the loopback side.
        #
        # walmradio's connect times have been observed at 20.5s and 42.5s
        # across two test runs, both suspiciously close to (CONNECT_TIMEOUT
        # + a few seconds) — the signature of Python trying an unreachable/
        # slow IPv6 address first (no Happy-Eyeballs / RFC 8305 racing in
        # urllib), burning the full timeout, before falling back to a IPv4
        # address that connects quickly. We try a direct IPv4-only connection
        # FIRST with a short timeout; if that fails for any reason (including
        # the host genuinely having no IPv4 address), we fall back to the
        # original urllib path, which handles redirects/odd encodings more
        # robustly but may hit the slow dual-stack behaviour again.
        t_remote_start = time.time()
        url_parts  = urllib.parse.urlsplit(url)
        req_headers = {
            "User-Agent": "VLC/3.0.21 LibVLC/3.0.21",
            "Icy-MetaData": "1",
            "Accept":      "*/*",
        }
        remote_resp = None

        try:
            remote_resp = self._connect_https_ipv4(
                url_parts, req_headers, ssl_ctx, timeout=8)
        except Exception as e:
            pass

        if remote_resp is None:
            t_fallback_start = time.time()
            try:
                req = urllib.request.Request(url, headers=req_headers)
                remote_resp = urllib.request.urlopen(
                    req, timeout=CONNECT_TIMEOUT, context=ssl_ctx)
            except Exception as e:
                return 0

        ct = (remote_resp.headers.get("content-type") or "").lower()
        if not ("audio/" in ct or "application/ogg" in ct or "video/" in ct):
            try:
                remote_resp.close()
            except Exception:
                pass
            return 0

        # Collect ICY/audio headers to pass through to BASS.
        # icy-metaint must be forwarded accurately — sending 0 or omitting it
        # causes BASS to misparse the byte stream (garbled audio / glitches).
        #
        # content-length is forwarded too when the remote sent one. Live
        # Icecast radio streams normally don't send it (indefinite stream),
        # so this is a no-op for those - existing radio behaviour is
        # unchanged. Finite files (podcast episodes) usually DO send it,
        # and without it BASS has no way to know the stream's total length,
        # so BASS_ChannelGetLength()/BASS_ChannelSetPosition() can't work
        # even though the stream was opened without BASS_STREAM_BLOCK -
        # this is why podcast episodes served over https (and therefore
        # routed through this local proxy) previously played fine but
        # could never seek or resume from a saved position.
        passthrough_headers = []
        for hdr in ("content-type", "content-length", "icy-name", "icy-genre",
                    "icy-br", "icy-sr", "icy-metaint", "icy-pub", "icy-url"):
            val = remote_resp.headers.get(hdr)
            if val:
                passthrough_headers.append(f"{hdr}: {val}".encode())

        # --- Step 2: bind a local loopback server socket ---
        # The remote is already connected, so BASS will get an immediate
        # HTTP response the moment it sends its GET request.
        try:
            srv = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            srv.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            srv.settimeout(15)   # BASS must connect within 15 s
            port = srv.getsockname()[1]
        except Exception as e:
            try:
                remote_resp.close()
            except Exception:
                pass
            return 0


        # Pre-build the HTTP response to send to BASS (all headers are known).
        http_response = b"\r\n".join(
            [b"HTTP/1.0 200 OK"] + passthrough_headers + [b"", b""])

        # --- Step 3: proxy thread — waits for BASS then forwards ---
        proxy_ready = threading.Event()

        def _proxy():
            proxy_ready.set()

            try:
                client, _ = srv.accept()
            except Exception as e:
                try:
                    remote_resp.close()
                except Exception:
                    pass
                return
            finally:
                srv.close()

            # Drain BASS's HTTP GET request
            try:
                client.settimeout(5)
                buf = b""
                while b"\r\n\r\n" not in buf:
                    chunk = client.recv(512)
                    if not chunk:
                        break
                    buf += chunk
            except Exception:
                pass

            # Send HTTP response with forwarded ICY headers
            try:
                client.sendall(http_response)
            except Exception as e:
                try:
                    client.close()
                    remote_resp.close()
                except Exception:
                    pass
                return


            # Forward remote audio bytes → BASS.
            # A generous timeout (30 s) prevents spurious disconnects during
            # brief network pauses without blocking indefinitely on dead streams.
            client.settimeout(30)
            read_fn = remote_resp.read
            total_bytes  = 0
            t_fwd_start  = time.time()
            t_last_log   = t_fwd_start
            stop_reason  = "eof"
            try:
                while True:
                    data = read_fn(CHUNK)
                    if not data:
                        break
                    client.sendall(data)
                    total_bytes += len(data)
                    now = time.time()
                    if now - t_last_log >= 20:
                        t_last_log = now
            except Exception as e:
                stop_reason = repr(e)
            finally:
                elapsed = time.time() - t_fwd_start
                try:
                    client.close()
                except Exception:
                    pass
                try:
                    remote_resp.close()
                except Exception:
                    pass

        t = threading.Thread(target=_proxy, daemon=True, name="bass-https-proxy")
        t.start()

        # Wait until the proxy thread has called proxy_ready.set() (i.e. it is
        # in srv.accept()) before pointing BASS at the local address.
        proxy_ready.wait(timeout=2)

        # --- Step 4: point BASS at the local proxy ---
        local_url = f"http://127.0.0.1:{port}/"
        # For seekable (podcast) we try without BLOCK first, then fallback to BLOCK
        # only if that fails. However, if we used the proxy for a podcast and it
        # falls back to BLOCK, seeking will fail. But the proxy is only used for
        # HTTPS streams that fail with BASS directly; if seekable is True, we might
        # still want to try BLOCK as last resort. But for podcasts, we want seeking
        # to work, so we avoid BLOCK entirely. So we should not use BLOCK for seekable.
        if seekable:
            stream = self._dll.BASS_StreamCreateURL(
                local_url.encode("utf-8"),
                ctypes.c_uint32(0), ctypes.c_uint32(0),
                ctypes.c_void_p(0), ctypes.c_void_p(0),
            )
            if stream:
                return stream
            else:
                return self._try_download_and_play(url)
        else:
            for _flags in (_BASS_STREAM_BLOCK, 0):
                stream = self._dll.BASS_StreamCreateURL(
                    local_url.encode("utf-8"),
                    ctypes.c_uint32(0), ctypes.c_uint32(_flags),
                    ctypes.c_void_p(0), ctypes.c_void_p(0),
                )
                if stream:
                    return stream

        # Both attempts failed; close the server socket so the proxy thread exits
        try:
            srv.close()
        except Exception:
            pass
        try:
            remote_resp.close()
        except Exception:
            pass
        return 0

    def play(self, url, volume_0_1=1.0, seq=None, seekable=False):
        # Cancel any existing play operation first
        self._cancel_pending_play()

        if not self._dll:
            return False, "BASS not loaded"

        # Store seq for this play attempt
        with self._lock:
            self._current_play_seq = seq

        time.sleep(0.05)  # Small delay to ensure previous stream is freed

        # Try directly the previously successfully resolved URL (TTL: 5 min)
        _cache_entry = self._resolve_cache.get(url)
        cached_url = None
        if _cache_entry:
            _cached_url_val, _cached_ts = _cache_entry
            if time.time() - _cached_ts < self._CACHE_TTL:
                cached_url = _cached_url_val
            else:
                self._resolve_cache.pop(url, None)
        if cached_url and cached_url != url:
            stream = self._try_create_url(cached_url, seekable=seekable)
            if stream:
                with self._lock:
                    if self._current_play_seq != seq:
                        try:
                            self._dll.BASS_StreamFree(stream)
                        except Exception:
                            pass
                        return False, "play cancelled"
                    self._handle = stream
                try:
                    self._gain = max(0.0, min(2.0, volume_0_1))
                    bass_vol = min(1.0, self._gain)
                    self._dll.BASS_ChannelSetAttribute(
                        stream, _BASS_ATTRIB_VOL, ctypes.c_float(bass_vol))
                    self._apply_gain_dsp(stream)
                    self._apply_fx(stream)
                except Exception:
                    pass
                if not self._dll.BASS_ChannelPlay(stream, 0):
                    # Cache hit but ChannelPlay failed — invalidate cache and fall
                    # through to the full resolve chain below.
                    err = self._dll.BASS_ErrorGetCode()
                    try:
                        self._dll.BASS_StreamFree(stream)
                    except Exception:
                        pass
                    with self._lock:
                        self._handle = 0
                    self._resolve_cache.pop(url, None)
                    # fall through to resolve chain
                else:
                    # Cache hit and playback started successfully.
                    # CRITICAL: must return here — without this the code falls
                    # through to the resolve loop and opens a second stream,
                    # causing simultaneous double-playback.
                    with self._lock:
                        if self._current_play_seq == seq:
                            self._current_play_seq = None
                        self._handle = stream
                    self._restart_meta_thread()
                    return True, "ok"

        # Resolve chain: True with playlist resolve if URL fails
        # Try to access the stream URL. Stations like TRT 2 levels
        # Uses HLS playlist chain: master.m3u8 → master_128.m3u8 → .aac
        # That's why we make a maximum of 3 levels of resolve.
        _MAX_RESOLVE_DEPTH = 3
        current_url = url
        visited = {url}
        stream = 0  # reset — cache branch may have left a stale value

        for depth in range(_MAX_RESOLVE_DEPTH + 1):
            stream = self._try_create_url(current_url, seekable=seekable)
            if stream:
                break
            if depth == _MAX_RESOLVE_DEPTH:
                break
            resolved = _resolve_playlist_url(current_url)
            if not resolved or resolved == current_url or resolved in visited:
                break
            visited.add(resolved)
            current_url = resolved
        if not stream:
            err = self._dll.BASS_ErrorGetCode()
            with self._lock:
                if self._current_play_seq == seq:
                    self._current_play_seq = None
            return False, f"StreamCreateURL failed (err={err})"

        # Check if this play was cancelled while creating stream
        with self._lock:
            if self._current_play_seq != seq:
                # Play was cancelled, clean up stream
                try:
                    self._dll.BASS_StreamFree(stream)
                except Exception:
                    pass
                return False, "play cancelled"
            self._handle = stream

        try:
            self._gain = max(0.0, min(2.0, volume_0_1))
            bass_vol = min(1.0, self._gain)
            self._dll.BASS_ChannelSetAttribute(
                stream, _BASS_ATTRIB_VOL, ctypes.c_float(bass_vol))
            self._apply_gain_dsp(stream)
            self._apply_fx(stream)
        except Exception as e:
            try:
                self._dll.BASS_StreamFree(stream)
            except Exception:
                pass
            with self._lock:
                if self._current_play_seq == seq:
                    self._current_play_seq = None
                self._handle = 0
            return False, f"set volume failed: {e}"

        # Check again if cancelled
        with self._lock:
            if self._current_play_seq != seq:
                try:
                    self._dll.BASS_StreamFree(stream)
                except Exception:
                    pass
                self._handle = 0
                return False, "play cancelled"

        if not self._dll.BASS_ChannelPlay(stream, 0):
            err = self._dll.BASS_ErrorGetCode()
            try:
                self._dll.BASS_StreamFree(stream)
            except Exception:
                pass
            with self._lock:
                if self._current_play_seq == seq:
                    self._current_play_seq = None
                self._handle = 0
            return False, f"ChannelPlay failed (err={err})"

        with self._lock:
            if self._current_play_seq == seq:
                self._current_play_seq = None
            self._handle = stream

        # Cache the successful resolve chain — excluding segment URLs.
        # Segment URLs (TRT: master_128_primary_XXXXXX.aac) are ephemeral;
        # Caching these will cause a silencing issue after a few minutes.
        if current_url != url:
            import re as _re
            _is_segment = bool(_re.search(r'_\d{6,}\.', current_url))
            if not _is_segment:
                self._resolve_cache[url] = (current_url, time.time())
        self._restart_meta_thread()
        return True, "ok"

    def stop(self):
        # Cancel any pending play when stopping
        self._cancel_pending_play()
        self._stop_meta_thread()
        with self._lock:
            if self._handle and self._dll:
                try:
                    self._dll.BASS_ChannelStop(self._handle)
                    self._dll.BASS_StreamFree(self._handle)
                except Exception:
                    pass
                self._handle = 0
                # FX handles belong to the freed stream — must be cleared so
                # _apply_fx() re-registers them on the next stream.
                self._fx_handles = {}
            # Clean up any downloaded temp file (if any)
            if hasattr(self, '_downloaded_file_path') and self._downloaded_file_path:
                try:
                    os.remove(self._downloaded_file_path)
                except OSError:
                    pass
                self._downloaded_file_path = None

    def pause(self):
        with self._lock:
            if self._handle and self._dll:
                try:
                    self._dll.BASS_ChannelPause(self._handle)
                except Exception:
                    pass

    def resume(self):
        with self._lock:
            if self._handle and self._dll:
                try:
                    self._dll.BASS_ChannelPlay(self._handle, 0)
                except Exception:
                    pass

    # -- Time-shift (local buffer file) playback -------------------------
    #
    # These methods are independent of the live-URL play() path above: they
    # open a local file created by timeshift.py via BASS_StreamCreateFile
    # instead of BASS_StreamCreateURL, which is what makes real seeking
    # (rewind/fast-forward) possible. Returning to live playback is just a
    # normal play(live_url, ...) call - no special handling needed there.

    def play_timeshift_file(self, path, volume_0_1=1.0, start_seconds=0.0):
        """Open a local time-shift buffer file for seekable playback.

        Any currently playing stream (live or time-shift) is stopped first.
        Returns (ok, message).
        """
        try:
            size = os.path.getsize(path)
        except Exception as e:
            size = -1
        _debug_log("play_timeshift_file: path=%r size=%d volume=%.2f start_seconds=%.2f"
                   % (path, size, volume_0_1, start_seconds))

        self._cancel_pending_play()
        self._stop_meta_thread()
        if not self._dll:
            _debug_log("play_timeshift_file: FAILED - BASS not loaded")
            return False, "BASS not loaded"

        with self._lock:
            if self._handle:
                try:
                    self._dll.BASS_ChannelStop(self._handle)
                    self._dll.BASS_StreamFree(self._handle)
                except Exception:
                    pass
                self._handle = 0
                self._fx_handles = {}

        try:
            stream = self._dll.BASS_StreamCreateFile(
                ctypes.c_int32(0),          # mem = False - read from disk
                ctypes.c_wchar_p(path),
                ctypes.c_uint64(0),         # offset
                ctypes.c_uint64(0),         # length - 0 means "to end of file"
                ctypes.c_uint32(_BASS_UNICODE),
            )
        except Exception as e:
            _debug_log("play_timeshift_file: FAILED - BASS_StreamCreateFile exception: %s" % e)
            return False, f"BASS_StreamCreateFile exception: {e}"

        if not stream:
            err = self._dll.BASS_ErrorGetCode()
            _debug_log("play_timeshift_file: FAILED - BASS_StreamCreateFile err=%d "
                       "(41=FILEFORM/unrecognized format, 2=FILEOPEN, 32=timeout)" % err)
            return False, f"BASS_StreamCreateFile failed (err={err})"

        _debug_log("play_timeshift_file: BASS_StreamCreateFile OK, handle=%d" % stream)
        with self._lock:
            self._handle = stream

        try:
            gain = max(0.0, min(2.0, volume_0_1))
            bass_vol = min(1.0, gain)
            self._dll.BASS_ChannelSetAttribute(
                stream, _BASS_ATTRIB_VOL, ctypes.c_float(bass_vol))
            self._apply_gain_dsp(stream)
            self._apply_fx(stream)
        except Exception:
            pass

        if start_seconds > 0:
            try:
                pos_bytes = self._dll.BASS_ChannelSeconds2Bytes(
                    stream, ctypes.c_double(start_seconds))
                if not self._dll.BASS_ChannelSetPosition(stream, pos_bytes, _BASS_POS_BYTE):
                    err = self._dll.BASS_ErrorGetCode()
                    _debug_log("play_timeshift_file: initial BASS_ChannelSetPosition "
                               "failed, err=%d (started from position 0 instead)" % err)
            except Exception as e:
                _debug_log("play_timeshift_file: initial seek exception: %s" % e)

        if not self._dll.BASS_ChannelPlay(stream, 0):
            err = self._dll.BASS_ErrorGetCode()
            try:
                self._dll.BASS_StreamFree(stream)
            except Exception:
                pass
            with self._lock:
                self._handle = 0
            _debug_log("play_timeshift_file: FAILED - BASS_ChannelPlay err=%d" % err)
            return False, f"ChannelPlay failed (err={err})"

        _debug_log("play_timeshift_file: OK, playing handle=%d" % stream)
        return True, "ok"

    def timeshift_seek(self, delta_seconds):
        """Seek by a relative number of seconds within the currently open
        time-shift file stream, clamped to [0, stream length].

        Forward seeks (delta_seconds > 0) are additionally kept
        _TIMESHIFT_TAIL_SAFETY_SECONDS short of the file's current tail:
        the buffer file is being written to live while this reads from
        it, so BASS_ChannelGetLength can still lag a moment behind what
        has actually been flushed to disk. Targeting a position right at
        (or past) that reported length makes BASS_ChannelSetPosition
        fail intermittently near the live edge.

        Returns (ok, position_seconds, length_seconds).
        """
        with self._lock:
            handle, dll = self._handle, self._dll
        if not handle or not dll:
            return False, 0.0, 0.0
        try:
            # Get current position
            pos_bytes = dll.BASS_ChannelGetPosition(handle, _BASS_POS_BYTE)
            pos_secs = dll.BASS_ChannelBytes2Seconds(handle, pos_bytes)
            new_pos = max(0.0, pos_secs + delta_seconds)
            if delta_seconds > 0:
                try:
                    tail_length_bytes = dll.BASS_ChannelGetLength(handle, _BASS_POS_BYTE)
                    tail_length_secs  = dll.BASS_ChannelBytes2Seconds(handle, tail_length_bytes)
                except Exception:
                    tail_length_secs = 0.0
                if tail_length_secs > 0:
                    new_pos = min(new_pos, max(0.0, tail_length_secs - _TIMESHIFT_TAIL_SAFETY_SECONDS))
            new_pos_bytes = dll.BASS_ChannelSeconds2Bytes(handle, ctypes.c_double(new_pos))
            if dll.BASS_ChannelSetPosition(handle, new_pos_bytes, _BASS_POS_BYTE):
                # Try to get length for caller's info (optional)
                try:
                    length_bytes = dll.BASS_ChannelGetLength(handle, _BASS_POS_BYTE)
                    length_secs = dll.BASS_ChannelBytes2Seconds(handle, length_bytes)
                except:
                    length_secs = 0.0
                return True, new_pos, length_secs
            else:
                err = dll.BASS_ErrorGetCode()
                _debug_log("timeshift_seek: BASS_ChannelSetPosition failed, err=%d "
                           "(target=%.2fs, was at %.2fs)" % (err, new_pos, pos_secs))
                return False, pos_secs, 0.0
        except Exception as e:
            _debug_log("timeshift_seek exception: %s" % e)
            return False, 0.0, 0.0

    def timeshift_status(self):
        """Return (position_seconds, length_seconds) for the currently open
        time-shift file stream, or (0.0, 0.0) if none is open."""
        with self._lock:
            handle, dll = self._handle, self._dll
        if not handle or not dll:
            return 0.0, 0.0
        try:
            length_bytes = dll.BASS_ChannelGetLength(handle, _BASS_POS_BYTE)
            length_secs  = dll.BASS_ChannelBytes2Seconds(handle, length_bytes)
            pos_bytes    = dll.BASS_ChannelGetPosition(handle, _BASS_POS_BYTE)
            pos_secs     = dll.BASS_ChannelBytes2Seconds(handle, pos_bytes)
            return pos_secs, length_secs
        except Exception:
            return 0.0, 0.0

    def _apply_gain_dsp(self, handle):
        """Install or remove DSP gain + bass boost callback for stream.

        Amplification curve (VLC-like):
          The volume_0_1 value scales exponentially, not linearly.
          volume=1.0 → gain=1.0 (no change)
          volume=1.5 → gain≈2.8  (+8.5 dB)
          volume=2.0 → gain≈8.0  (+18 dB)
          Formule: gain = EXP_BASE ^ (for volume - 1.0)  (volume > 1.0)

        Bass boost (low-shelf IIR, first degree):
          Cutoff frequency ~150 Hz, 44100 Hz sampling rate assumed.
          bass_boost=0.0 → no additional gain
          bass_boost=1.0 → approximately +12 dB at low frequencies

        Performance: Array module and ctypes memoryview instead of Python loop
        is used — Processing time per sample is reduced by ~10x.
        """
        import math
        import array as _array

        DSPPROC = ctypes.CFUNCTYPE(
            None,
            ctypes.c_ulong,   # handle
            ctypes.c_ulong,   # channel
            ctypes.c_void_p,  # buffer
            ctypes.c_ulong,   # length
            ctypes.c_void_p,  # user
        )

        # 1. Gain DSP
        if self._dsp_handle and self._dll:
            try:
                self._dll.BASS_ChannelRemoveDSP(handle, self._dsp_handle)
            except Exception:
                pass
            self._dsp_handle = 0
            self._dsp_proc_ref = None

        if self._gain > 1.0:
            # Exponential scaling: Reflects VLC's 100%+ behavior.
            # EXP_BASE=8 → volume=2.0 gain≈8x (+18 dB), volume=1.5'de ≈2.8x
            EXP_BASE = 8.0
            gain = EXP_BASE ** (self._gain - 1.0)
            # Precalculated LUT (Lookup Table): 65536 values, 16-bit integer range.
            # The DSP callback performs a single table lookup instead of multiplication each time it is called.
            _lut = _array.array('h', (
                max(-32768, min(32767, int(s * gain)))
                for s in range(-32768, 32768)
            ))

            def _dsp_gain(dsp_h, channel, buf, length, user):
                if not buf or not length:
                    return
                n_samples = length // 2
                # Display buffer memory directly as ctypes array
                arr = (ctypes.c_int16 * n_samples).from_address(buf)
                for i in range(n_samples):
                    # LUT search: arr[i] unsigned → convert to positive index with offset +32768
                    arr[i] = _lut[arr[i] + 32768]

            proc_gain = DSPPROC(_dsp_gain)
            self._dsp_proc_ref = proc_gain
            try:
                dsp_h = self._dll.BASS_ChannelSetDSP(handle, proc_gain, None, 1)
                self._dsp_handle = dsp_h
            except Exception:
                self._dsp_proc_ref = None

        # 2. Bass Boost DSP (Low-shelf IIR)
        if self._bass_dsp_handle and self._dll:
            try:
                self._dll.BASS_ChannelRemoveDSP(handle, self._bass_dsp_handle)
            except Exception:
                pass
            self._bass_dsp_handle = 0
            self._bass_dsp_proc_ref = None
            self._bass_x1 = [0.0, 0.0]
            self._bass_y1 = [0.0, 0.0]

        if self._bass_boost > 0.0:
            # First order low-shelf IIR filter.
            # Cutoff ~150 Hz @ 44100 Hz; boost: between 0..+12 dB.
            # Reference: Audio EQ Cookbook (Zölzer) in simplified form.
            fc      = 150.0   # cut-off frequency (Hz)
            fs      = 44100.0 # sample rate
            max_db  = 12.0    # maximum bass boost (dB)
            boost_db  = self._bass_boost * max_db
            boost_lin = 10.0 ** (boost_db / 20.0)
            K  = math.tan(math.pi * fc / fs)
            b0 = (1.0 + boost_lin * K) / (1.0 + K)
            b1 = (boost_lin * K - 1.0) / (1.0 + K)
            a1 = (K - 1.0)             / (1.0 + K)
            # Filter state: [left_x1, right_x1], [left_y1, right_y1]
            x1_ref = self._bass_x1
            y1_ref = self._bass_y1

            def _dsp_bass(dsp_h, channel, buf, length, user):
                if not buf or not length:
                    return
                n_samples = length // 2
                arr = (ctypes.c_int16 * n_samples).from_address(buf)
                # IIR filter: stereo interleaved — even=left (0), odd=right (1)
                # The two channels are tracked with separate state vectors.
                x1L = x1_ref[0]; y1L = y1_ref[0]
                x1R = x1_ref[1]; y1R = y1_ref[1]
                i = 0
                while i < n_samples - 1:
                    # left example
                    x0 = arr[i]
                    y0 = b0 * x0 + b1 * x1L - a1 * y1L
                    x1L = x0; y1L = y0
                    v = int(y0)
                    arr[i] = 32767 if v > 32767 else (-32768 if v < -32768 else v)
                    i += 1
                    # Right example
                    x0 = arr[i]
                    y0 = b0 * x0 + b1 * x1R - a1 * y1R
                    x1R = x0; y1R = y0
                    v = int(y0)
                    arr[i] = 32767 if v > 32767 else (-32768 if v < -32768 else v)
                    i += 1
                # Mono or single remaining sample
                if i < n_samples:
                    x0 = arr[i]
                    y0 = b0 * x0 + b1 * x1L - a1 * y1L
                    x1L = x0; y1L = y0
                    v = int(y0)
                    arr[i] = 32767 if v > 32767 else (-32768 if v < -32768 else v)
                # Write back state vectors
                x1_ref[0] = x1L; x1_ref[1] = x1R
                y1_ref[0] = y1L; y1_ref[1] = y1R

            proc_bass = DSPPROC(_dsp_bass)
            self._bass_dsp_proc_ref = proc_bass
            try:
                # priority=0 → gain works before DSP (bass before boost,
                # then overall gain — more accurate signal chain)
                bass_dsp_h = self._dll.BASS_ChannelSetDSP(handle, proc_bass, None, 0)
                self._bass_dsp_handle = bass_dsp_h
            except Exception:
                self._bass_dsp_proc_ref = None

    def set_volume(self, volume_0_1):
        with self._lock:
            volume_0_1 = max(0.0, min(2.0, volume_0_1))
            self._gain = volume_0_1
            if self._handle and self._dll:
                try:
                    # BASS_ATTRIB_VOL only works between 0.0–1.0.
                    # For amplification (>1.0) apply gain with BASS_ChannelSetDSP.
                    bass_vol = min(1.0, volume_0_1)
                    self._dll.BASS_ChannelSetAttribute(
                        self._handle, _BASS_ATTRIB_VOL,
                        ctypes.c_float(bass_vol))
                    self._apply_gain_dsp(self._handle)
                except Exception:
                    pass

    def set_fx(self, fx_names):
        """Replace active DirectX 8 effects.

        fx_names: A comma-separated string or list of effect names.
                  Example: "chorus,reverb" or ["chorus", "reverb"]
                  To close all: "none" or empty string or []
        The change is applied immediately; no reboot required.
        """
        if isinstance(fx_names, str):
            parts = [x.strip().lower() for x in fx_names.split(",") if x.strip()]
            new_names = set(parts) - {"none"}
        else:
            new_names = {x.strip().lower() for x in fx_names if x.strip().lower() != "none"}

        with self._lock:
            if new_names == self._fx_names:
                return
            self._fx_names = new_names
            if self._handle and self._dll:
                self._apply_fx(self._handle)

    def _apply_fx(self, handle):
        """Remove old FX on handle and apply new ones."""
        dll = self._dll
        if not dll:
            return

        # Remove effects that are no longer active
        for name, h in list(self._fx_handles.items()):
            if name not in self._fx_names:
                try:
                    dll.BASS_ChannelRemoveFX(handle, h)
                except Exception:
                    pass
                del self._fx_handles[name]

        # Apply newly added effects
        for name in self._fx_names:
            if name in self._fx_handles:
                continue  # already active
            fx_type = _FX_NAME_TO_TYPE.get(name)
            if fx_type is None:
                continue
            try:
                h = dll.BASS_ChannelSetFX(handle, fx_type, 0)
                if h:
                    self._fx_handles[name] = h
                else:
                    continue
            except Exception:
                continue

            # Set parameters for ParamEQ presets
            if name in _PARAMEQ_PRESETS:
                fCenter, fBandwidth, fGain = _PARAMEQ_PRESETS[name]
                # Apply runtime gain override if set
                fGain = _PARAMEQ_GAIN_OVERRIDE.get(name, fGain)
                class _PARAMEQ(ctypes.Structure):
                    _fields_ = [
                        ("fCenter",    ctypes.c_float),
                        ("fBandwidth", ctypes.c_float),
                        ("fGain",      ctypes.c_float),
                    ]
                params = _PARAMEQ(fCenter, fBandwidth, fGain)
                try:
                    dll.BASS_FXSetParameters(self._fx_handles[name], ctypes.byref(params))
                except Exception:
                    pass

    def set_eq_gain(self, band, gain_db):
        """Set the gain (dB) for one ParamEQ band and re-apply it immediately.

        band:    "eq_bass" | "eq_treble" | "eq_vocal"
        gain_db: float, clamped to -15..+15 dB
        """
        if band not in _PARAMEQ_PRESETS:
            return
        gain_db = max(-15.0, min(15.0, float(gain_db)))
        _PARAMEQ_GAIN_OVERRIDE[band] = gain_db

        with self._lock:
            h = self._handle
            dll = self._dll
            fx_h = self._fx_handles.get(band)
        if not h or not dll or not fx_h:
            return

        fCenter, fBandwidth, _ = _PARAMEQ_PRESETS[band]

        class _PARAMEQ(ctypes.Structure):
            _fields_ = [
                ("fCenter",    ctypes.c_float),
                ("fBandwidth", ctypes.c_float),
                ("fGain",      ctypes.c_float),
            ]
        params = _PARAMEQ(fCenter, fBandwidth, float(gain_db))
        try:
            dll.BASS_FXSetParameters(fx_h, ctypes.byref(params))
        except Exception:
            pass

    def set_bass_boost(self, boost_0_1):
        """Adjust the bass boost level.

        boost_0_1: 0.0 = off, 1.0 = maximum (+12 dB low-shelf ~150 Hz).
        The change is applied immediately (without the need for a reboot).
        """
        with self._lock:
            self._bass_boost = max(0.0, min(1.0, float(boost_0_1)))
            # Reset filter state — preventing popping during sharp transitions
            self._bass_x1 = [0.0, 0.0]
            self._bass_y1 = [0.0, 0.0]
            if self._handle and self._dll:
                try:
                    self._apply_gain_dsp(self._handle)
                except Exception:
                    pass

    def set_playback_rate(self, rate):
        """Set pitch-preserving playback speed for the current stream
        (podcasts only). rate: 1.0 = normal, 1.1 = 10% faster, 0.9 = 10%
        slower. Persists across episodes (like volume) so it applies again
        automatically the next time a tempo-capable stream is opened.

        Returns (ok, actual_rate, reason). ok is False when either
        bass_fx.dll isn't available at all, or the current stream isn't a
        tempo-wrapped one (e.g. it fell back to a plain stream because
        wrapping failed for this particular episode) — in both cases the
        rate is remembered for next time but has no effect right now.
        """
        rate = max(0.5, min(3.0, float(rate)))
        with self._lock:
            self._playback_rate = rate
            if not self._bass_fx_dll:
                return False, rate, "bass_fx_unavailable"
            if not (self._tempo_active and self._handle and self._dll):
                return False, rate, "not_tempo_stream"
            try:
                ok = self._dll.BASS_ChannelSetAttribute(
                    self._handle, _BASS_ATTRIB_TEMPO,
                    ctypes.c_float((rate - 1.0) * 100.0),
                )
            except Exception:
                ok = False
            if not ok:
                return False, rate, "set_attribute_failed"
            return True, rate, ""

    def get_playback_rate(self):
        return self._playback_rate

    def unload(self):
        self._cancel_pending_play()
        self._stop_meta_thread()
        self.stop()
        if self._dll:
            try:
                self._dll.BASS_Free()
            except Exception:
                pass
            self._dll = None

    # -- ICY meta + stream health monitor -----------------------------------
    # Stall detection: ~3s each cycle, threshold=6 → stall event after ~18s.
    # Raised from 4 to reduce false positives on slow Japanese HLS streams
    # (smartstream.ne.jp) that buffer slowly but are not actually broken.
    # 3 × 3s = ~9s — fast enough to catch Icecast dropouts without
    # false positives on slow-but-healthy HLS streams.
    _STALL_THRESHOLD = 3

    def _restart_meta_thread(self):
        self._stop_meta_thread()
        self._meta_stop.clear()
        self._meta_thread = threading.Thread(
            target=self._monitor_loop, daemon=True)
        self._meta_thread.start()

    def _stop_meta_thread(self):
        self._meta_stop.set()
        t = self._meta_thread
        self._meta_thread = None
        if t and t.is_alive():
            t.join(timeout=2)
        self._meta_stop.clear()

    def _monitor_loop(self):
        """ICY metadata polling + stall/stop/buffer-drain detection.

        Three failure modes are detected:
          1. BASS_ACTIVE_STALLED / STOPPED  — classic network dropout
          2. Buffer drain while PLAYING     — AAC+ SBR decoder drift;
             BASS reports PLAYING but internal decode buffer empties silently.
             Detected via BASS_ChannelGetData(BASS_DATA_AVAILABLE).
          3. Position stuck while PLAYING and buffer non-empty — covers the
             case where BASS keeps reporting PLAYING and keeps accepting/
             buffering bytes (so ICY metadata can keep updating normally),
             but the playback cursor itself never advances, i.e. nothing is
             actually being heard. This is the scenario reported as "title
             keeps changing but there's no sound" on icecast.walmradio.com.
             Detected via BASS_ChannelGetPosition(BASS_POS_BYTE) not moving
             across consecutive polls.
        Either condition increments its own counter; after _STALL_THRESHOLD
        consecutive hits a stall event is sent to the parent process.
        """
        last_title      = ""
        stall_count     = 0
        buf_empty_count = 0
        pos_stuck_count = 0
        last_pos        = None
        _BUF_EMPTY_THRESHOLD = 2   # consecutive near-empty reads before stall

        while not self._meta_stop.is_set():
            for _ in range(6):   # 3-second hold, cancellable in 0.5s steps
                if self._meta_stop.is_set():
                    return
                time.sleep(0.5)

            try:
                with self._lock:
                    h, dll = self._handle, self._dll

                if not h or not dll:
                    stall_count     = 0
                    buf_empty_count = 0
                    pos_stuck_count = 0
                    last_pos        = None
                    continue

                # 1. ICY metadata
                try:
                    raw = dll.BASS_ChannelGetTags(h, _BASS_TAG_META)
                    if raw and b"StreamTitle='" in raw:
                        decoded = raw.decode("utf-8", "ignore")
                        title = decoded.split("StreamTitle='")[1].split("';")[0]
                        if title and title != last_title:
                            last_title = title
                            _event(type="meta", title=title)
                except Exception:
                    pass

                # 2. Channel status
                try:
                    state = dll.BASS_ChannelIsActive(h)
                except Exception:
                    state = _BASS_ACTIVE_PLAYING

                if state in (_BASS_ACTIVE_STALLED, _BASS_ACTIVE_STOPPED):
                    stall_count += 1
                    buf_empty_count = 0
                    pos_stuck_count = 0
                    last_pos        = None
                    if stall_count >= self._STALL_THRESHOLD:
                        if not self._meta_stop.is_set():
                            _event(type="stall", state=state)
                        stall_count = 0

                elif state == _BASS_ACTIVE_PLAYING:
                    stall_count = 0
                    # 3. Buffer-drain check — catches AAC+ SBR decoder drift.
                    # BASS_ChannelGetData with BASS_DATA_AVAILABLE returns
                    # buffered decoded bytes without consuming them.
                    # Returning 0 while PLAYING means the decoder has stalled
                    # internally even though the channel is nominally active.
                    available = None
                    try:
                        available = dll.BASS_ChannelGetData(h, None, _BASS_DATA_AVAILABLE)
                        if available == 0:
                            buf_empty_count += 1
                            if buf_empty_count >= _BUF_EMPTY_THRESHOLD:
                                if not self._meta_stop.is_set():
                                    _event(type="stall", state=state)
                                buf_empty_count = 0
                        else:
                            buf_empty_count = 0
                    except Exception:
                        buf_empty_count = 0

                    # 4. Position-stuck check — channel says PLAYING and the
                    # buffer isn't empty, but the actual playback cursor has
                    # frozen, so no audio is reaching the output. This is
                    # invisible to checks 1-3, which is why it kept being
                    # reported as "title updates but no sound".
                    try:
                        pos = dll.BASS_ChannelGetPosition(h, _BASS_POS_BYTE)
                        if pos is not None and pos >= 0:
                            if last_pos is not None and pos == last_pos:
                                pos_stuck_count += 1
                                if pos_stuck_count >= self._STALL_THRESHOLD:
                                    if not self._meta_stop.is_set():
                                        _event(type="stall", state=state)
                                    pos_stuck_count = 0
                            else:
                                pos_stuck_count = 0
                            last_pos = pos
                    except Exception:
                        pos_stuck_count = 0
                # PAUSED: leave counters unchanged

            except Exception:
                pass


# Main command loop
def main():
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--device", type=int, default=-1,
                        help="BASS output device index (-1 = system default)")
    args, _ = parser.parse_known_args()

    dll_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        os.chdir(dll_dir)
    except Exception:
        pass
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(dll_dir)
        except Exception:
            pass

    host = BassHost(dll_dir, device_index=args.device)
    ok, msg = host.load()
    if not ok:
        _err(f"BASS load failed: {msg}")
        sys.exit(1)
    _ok(ready=True)

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            cmd_obj = json.loads(raw_line)
        except json.JSONDecodeError as e:
            _err(f"JSON parse error: {e}")
            continue

        cmd = cmd_obj.get("cmd", "")

        if cmd == "ping":
            _ok(pong=True)

        elif cmd == "list_devices":
            try:
                devices = BassHost.enumerate_devices(host._dll)
                _ok(devices=devices)
            except Exception as e:
                _err(f"list_devices failed: {e}")

        elif cmd == "status":
            with host._lock:
                h   = host._handle
                dll = host._dll
            if h and dll:
                try:
                    state = dll.BASS_ChannelIsActive(h)
                except Exception:
                    state = -1
            else:
                state = -1
            # state: 0=stopped, 1=playing, 2=stalled, 3=paused, -1=no handle
            _ok(state=state)

        elif cmd == "play":
            url = cmd_obj.get("url", "")
            vol = float(cmd_obj.get("volume", 1.0))
            seq = cmd_obj.get("seq", None)
            seekable = bool(cmd_obj.get("seekable", False))
            host._cancel_pending_play()
            prev = host._current_play_thread
            if prev and prev.is_alive():
                prev.join(timeout=1.0)
            def _do_play(u=url, v=vol, s=seq, sk=seekable):
                ok, reason = host.play(u, v, seq=s, seekable=sk)
                _send({"ok": ok, "error": reason if not ok else None, "seq": s})
            t = threading.Thread(target=_do_play, daemon=True, name="bass-play")
            host._current_play_thread = t
            t.start()

        elif cmd == "stop":
            host._cancel_pending_play()
            host.stop()
            _ok()

        elif cmd == "pause":
            host.pause()
            _ok()

        elif cmd == "resume":
            host.resume()
            _ok()

        elif cmd == "volume":
            val = float(cmd_obj.get("value", 1.0))
            host.set_volume(val)
            _ok()

        elif cmd == "bass_boost":
            val = float(cmd_obj.get("value", 0.0))
            host.set_bass_boost(val)
            _ok()

        elif cmd == "set_playback_rate":
            rate = float(cmd_obj.get("rate", 1.0))
            ok, actual_rate, reason = host.set_playback_rate(rate)
            _ok(cmd="set_playback_rate", rate_applied=ok,
                rate=actual_rate, reason=reason)

        elif cmd == "set_fx":
            fx = cmd_obj.get("fx", "none")
            host.set_fx(fx)
            _ok()

        elif cmd == "set_eq_gain":
            band    = cmd_obj.get("band", "")
            gain_db = float(cmd_obj.get("gain_db", 9.0))
            host.set_eq_gain(band, gain_db)
            _ok()

        elif cmd == "timeshift_play":
            path          = cmd_obj.get("path", "")
            vol           = float(cmd_obj.get("volume", 1.0))
            start_seconds = float(cmd_obj.get("start_seconds", 0.0))
            ok, reason = host.play_timeshift_file(path, vol, start_seconds)
            if ok:
                _ok(cmd="timeshift_play")
            else:
                _send({"ok": False, "cmd": "timeshift_play", "error": reason})

        elif cmd == "timeshift_seek":
            delta = float(cmd_obj.get("delta_seconds", 0.0))
            seeked, position_seconds, length_seconds = host.timeshift_seek(delta)
            _ok(cmd="timeshift_seek", seeked=seeked,
                position_seconds=position_seconds, length_seconds=length_seconds)

        elif cmd == "timeshift_status":
            position_seconds, length_seconds = host.timeshift_status()
            _ok(cmd="timeshift_status",
                position_seconds=position_seconds, length_seconds=length_seconds)

        elif cmd == "quit":
            _ok()
            break

        else:
            _err(f"Unknown command: {cmd!r}")

    host.unload()


if __name__ == "__main__":
    # Use line-buffered stdout so JSON lines flush immediately
    sys.stdout = open(sys.stdout.fileno(), mode="w", buffering=1,
                      encoding="utf-8", errors="replace", closefd=False)
    main()