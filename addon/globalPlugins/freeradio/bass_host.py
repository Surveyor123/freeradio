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
  play       {"cmd":"play",       "url":"...", "volume":0.0-1.0}
  stop       {"cmd":"stop"}
  pause      {"cmd":"pause"}
  resume     {"cmd":"resume"}
  volume     {"cmd":"volume",     "value":0.0-2.0}
  bass_boost {"cmd":"bass_boost", "value":0.0-1.0}
  ping       {"cmd":"ping"}
  quit       {"cmd":"quit"}
"""

import ctypes
import json
import os
import sys
import threading
import time
import re
import urllib.request

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
_BASS_ACTIVE_STOPPED      = 0
_BASS_ACTIVE_PLAYING      = 1
_BASS_ACTIVE_STALLED      = 2
_BASS_ACTIVE_PAUSED       = 3
_BASS_DATA_AVAILABLE      = 0   # flag for BASS_ChannelGetData — returns buffered bytes

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
_PARAMEQ_PRESETS = {
    "eq_bass":    (100.0,  18.0,  9.0),
    "eq_treble":  (8000.0, 18.0,  9.0),
    "eq_vocal":   (2500.0, 12.0,  6.0),
}

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
        dll.BASS_SetConfig(_BASS_CONFIG_NET_TIMEOUT, 12000)     # ms — 12s; slow servers (qingting.fm etc.) için artırıldı
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

        self._dll = dll
        dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL_VERIFY, 0)
        dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL, 1)
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

    def play(self, url, volume_0_1=1.0, seq=None):
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
            stream = self._try_create_url(cached_url)
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
            stream = self._try_create_url(current_url)
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

    def _try_create_url(self, url):
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
                    ctypes.c_uint32(_BASS_STREAM_BLOCK), ctypes.c_uint32(0),
                    ctypes.c_void_p(0), ctypes.c_void_p(0),
                )
                if stream:
                    return stream
            if is_hls and not self._dll_hls and url_lower.startswith("https"):
                return 0

        # For HTTP, disable SSL completely and also try with custom headers via a small hack
        # Some Shoutcast servers require "Icy-MetaData: 1" header.
        # BASS doesn't send it by default, but we can set BASS_CONFIG_NET_META=1 already.
        ssl_saved = None
        is_http = url_lower.startswith("http://")
        if is_http:
            try:
                ssl_saved = self._dll.BASS_GetConfig(_BASS_CONFIG_NET_SSL)
                self._dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL, 0)
            except:
                pass

        try:
            # Try with BLOCK flag first
            stream = self._dll.BASS_StreamCreateURL(
                url.encode("utf-8"),
                ctypes.c_uint32(_BASS_STREAM_BLOCK), ctypes.c_uint32(0),
                ctypes.c_void_p(0), ctypes.c_void_p(0),
            )
            if stream:
                return stream

            # Try without BLOCK
            stream = self._dll.BASS_StreamCreateURL(
                url.encode("utf-8"),
                ctypes.c_uint32(0), ctypes.c_uint32(0),
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
                            # Try again with final URL
                            stream = self._dll.BASS_StreamCreateURL(
                                final_url.encode("utf-8"),
                                ctypes.c_uint32(_BASS_STREAM_BLOCK), ctypes.c_uint32(0),
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

    def _apply_gain_dsp(self, handle):
        """Install or remove DSP gain + bass boost callback for stream.

        Amplification curve (VLC-like):
          The volume_0_1 value scales exponentially, not linearly.
          volume=1.0 → gain=1.0 (no change)
          volume=1.5 → gain≈2.8  (+8.5 dB)
          volume=2.0 → gain≈8.0  (+18 dB)
          Formule: gain = EXP_BASE ^ (volume - 1.0)  (volume > 1.0 için)

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
        Either condition increments stall_count; after _STALL_THRESHOLD
        consecutive hits a stall event is sent to the parent process.
        """
        last_title      = ""
        stall_count     = 0
        buf_empty_count = 0
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
            host._cancel_pending_play()
            prev = host._current_play_thread
            if prev and prev.is_alive():
                prev.join(timeout=1.0)
            def _do_play(u=url, v=vol, s=seq):
                ok, reason = host.play(u, v, seq=s)
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

        elif cmd == "set_fx":
            fx = cmd_obj.get("fx", "none")
            host.set_fx(fx)
            _ok()

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