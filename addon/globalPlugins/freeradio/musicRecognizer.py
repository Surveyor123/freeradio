# -*- coding: utf-8 -*-
# FreeRadio - Music Recognizer
# ffmpeg.exe ile PCM örnek alma + gerçek Shazam imza algoritması + tanıma.
# shazamio/algorithm.py + signature.py'den numpy'sız saf Python'a aktarıldı.
# numpy / aiohttp bağımlılığı yoktur.

import json
import logging
import math
import os
import struct
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid as _uuid_mod
import winsound
from binascii import crc32
from base64 import b64encode
from copy import copy
from io import BytesIO

import addonHandler
addonHandler.initTranslation()

log = logging.getLogger(__name__)

USER_AGENT        = "FreeRadio-NVDA/1.0 ( https://github.com/freeradio-nvda )"
_SAMPLE_DURATION  = 12          # saniye
_FFMPEG_TIMEOUT   = 30
_HTTP_TIMEOUT     = 10

_semaphore = threading.Semaphore(1)

DATA_URI_PREFIX = "data:audio/vnd.shazam.sig;base64,"

# ── Sonuç sınıfı ──────────────────────────────────────────────────────────────

class RecognitionResult:

    def __init__(self, success, artist="", title="", album="",
                 release_date="", score=0.0, error_msg=""):
        self.success      = success
        self.artist       = artist
        self.title        = title
        self.album        = album
        self.release_date = release_date
        self.score        = score
        self.error_msg    = error_msg

    def short_label(self):
        if not self.success:
            return self.error_msg or "Recognition failed"
        parts = []
        if self.title:
            parts.append(self.title)
        if self.artist:
            parts.append(self.artist)
        return u" \u2014 ".join(parts) if parts else "Unknown track"

    def full_label(self):
        if not self.success:
            return self.error_msg or "Recognition failed"
        parts = []
        if self.title:
            parts.append(self.title)
        if self.artist:
            parts.append(self.artist)
        if self.album:
            parts.append(self.album)
        if self.release_date:
            parts.append(self.release_date[:4])
        return u" \u2014 ".join(parts) if parts else "Unknown track"

    def __str__(self):
        return self.short_label()


# ── Stream URL çözümleme ──────────────────────────────────────────────────────

_AUDIO_CT = ("audio/", "application/ogg", "application/octet-stream")

def _is_audio_content_type(ct):
    ct = (ct or "").lower().split(";")[0].strip()
    return any(ct.startswith(t) for t in _AUDIO_CT)


def _make_absolute_url(base_url, relative_url):
    """Göreceli URL'yi base_url'e göre mutlak URL'ye çevirir."""
    if relative_url.startswith(("http://", "https://")):
        return relative_url
    return urllib.parse.urljoin(base_url, relative_url)


def _resolve_to_audio_url(url, timeout=10, _depth=0):
    """
    Verilen URL'yi gerçek ses akışı URL'sine çözümler.
    HLS master playlist (EXT-X-STREAM-INF) içeriyorsa en düşük bant genişlikli
    varyantı özyinelemeli olarak çözer. Göreceli URL'leri otomatik olarak
    mutlak URL'ye dönüştürür.
    """
    if _depth > 3:
        log.warning("FreeRadio Recognizer: HLS resolve depth limit reached")
        return None

    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Icy-MetaData": "1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final_url = resp.url if hasattr(resp, "url") else url
            ct = (resp.headers.get("content-type") or "").lower().split(";")[0].strip()
            data = resp.read(65536).decode("utf-8", errors="replace")
    except Exception as exc:
        log.warning("FreeRadio Recognizer: resolve failed: %s", exc)
        return None

    if _is_audio_content_type(ct):
        return final_url

    if ct in ("audio/x-mpegurl", "application/x-mpegurl", "audio/mpegurl") or \
            url.lower().endswith((".m3u", ".m3u8")):
        lines = data.splitlines()

        # HLS Master Playlist mi? (EXT-X-STREAM-INF veya EXT-X-MEDIA içeriyorsa)
        is_master = any(
            l.strip().startswith(("#EXT-X-STREAM-INF", "#EXT-X-MEDIA"))
            for l in lines
        )

        if is_master:
            # En düşük bant genişlikli varyantı seç
            best_url = None
            best_bw  = None
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith("#EXT-X-STREAM-INF"):
                    # BANDWIDTH=... değerini çıkar
                    bw = None
                    for part in line.split(","):
                        if part.strip().upper().startswith("BANDWIDTH="):
                            try:
                                bw = int(part.strip().split("=", 1)[1])
                            except ValueError:
                                pass
                    # Sonraki satır varyant URL'si
                    i += 1
                    while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith("#")):
                        i += 1
                    if i < len(lines):
                        candidate = lines[i].strip()
                        if candidate and not candidate.startswith("#"):
                            candidate = _make_absolute_url(final_url, candidate)
                            if best_bw is None or (bw is not None and bw < best_bw):
                                best_bw  = bw
                                best_url = candidate
                i += 1

            if best_url:
                log.info("FreeRadio Recognizer: HLS master → variant %s (bw=%s)", best_url, best_bw)
                return _resolve_to_audio_url(best_url, timeout=timeout, _depth=_depth + 1)

        # Normal M3U/M3U8 — ilk medya URL'sini döndür
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                return _make_absolute_url(final_url, line)

    if ct == "audio/x-scpls" or url.lower().endswith(".pls"):
        for line in data.splitlines():
            if line.lower().startswith("file1="):
                return line.split("=", 1)[1].strip()

    return None


# ── ffmpeg ile 16 kHz mono PCM ────────────────────────────────────────────────

def _decode_to_pcm(ffmpeg_path, stream_url, duration=_SAMPLE_DURATION):
    cmd = [
        ffmpeg_path,
        "-t", str(duration),
        "-i", stream_url,
        "-f", "s16le",
        "-ar", "16000",
        "-ac", "1",
        "-",
    ]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_FFMPEG_TIMEOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        raise ValueError("ffmpeg timed out after %ds" % _FFMPEG_TIMEOUT)

    if len(proc.stdout) < 4096:
        stderr_txt = proc.stderr.decode("utf-8", errors="replace")[-300:]
        raise ValueError("ffmpeg returned too little audio. stderr: %s" % stderr_txt)

    return proc.stdout  # s16le bytes, 16000 Hz, mono


# ── Shazam imza algoritması (shazamio'dan numpy'sız aktarıldı) ────────────────
#
# Kaynak: shazamio/algorithm.py + shazamio/signature.py (MIT lisansı)
# Tek değişiklik: numpy array işlemleri saf Python listelerine dönüştürüldü.

# FrequencyBand değerleri (shazamio/enums.py'den)
_BAND_250_520  = 0
_BAND_520_1450 = 1
_BAND_1450_3500 = 2
# hz_3500_5500 legacy modda kullanılmaz

# Hanning penceresi — 2048 örnek (shazamio: np.hanning(2050)[1:-1])
def _make_hanning_2048():
    n = 2050
    return [0.5 * (1.0 - math.cos(2.0 * math.pi * k / (n - 1)))
            for k in range(1, n - 1)]   # [1:-1] → 2048 eleman

_HANNING = _make_hanning_2048()


def _rfft_magnitudes_sq(samples_2048):
    """
    2048 örneklik Hanning pencereli rFFT sonuçlarını döndürür.
    Çıktı: 1025 float (|X[k]|² / 2^17), shazamio ile aynı ölçek.
    numpy.fft.rfft yerine Cooley-Tukey kullanılır.
    """
    n = 2048
    # Hanning uygulanmış
    windowed = [samples_2048[i] * _HANNING[i] for i in range(n)]

    # Iteratif Cooley-Tukey FFT
    bits = 11   # log2(2048)
    rev = list(range(n))
    for i in range(n):
        r = int('{:011b}'.format(i)[::-1], 2)
        if r > i:
            rev[i], rev[r] = rev[r], rev[i]
    xc = [complex(windowed[rev[i]], 0) for i in range(n)]

    length = 2
    while length <= n:
        ang = -2.0 * math.pi / length
        wr, wi = math.cos(ang), math.sin(ang)
        for i in range(0, n, length):
            re, im = 1.0, 0.0
            for j in range(length // 2):
                u = xc[i + j]
                v_re = xc[i + j + length // 2].real * re - xc[i + j + length // 2].imag * im
                v_im = xc[i + j + length // 2].real * im + xc[i + j + length // 2].imag * re
                xc[i + j]               = complex(u.real + v_re, u.imag + v_im)
                xc[i + j + length // 2] = complex(u.real - v_re, u.imag - v_im)
                new_re = re * wr - im * wi
                im     = re * wi + im * wr
                re     = new_re
        length <<= 1

    # rFFT → ilk 1025 bin, güç spektrumu / 2^17
    result = []
    denom = float(1 << 17)
    for k in range(1025):
        mag2 = (xc[k].real ** 2 + xc[k].imag ** 2) / denom
        result.append(max(mag2, 1e-10))
    return result


class _RingBuffer:
    """shazamio.RingBuffer'ın saf Python karşılığı."""
    def __init__(self, size, default):
        self._buf        = [copy(default) for _ in range(size)]
        self.position    = 0
        self.buffer_size = size
        self.num_written = 0

    def append(self, value):
        self._buf[self.position] = value
        self.position  = (self.position + 1) % self.buffer_size
        self.num_written += 1

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return self._buf[idx]
        return self._buf[idx % self.buffer_size]

    def __setitem__(self, idx, val):
        if isinstance(idx, slice):
            self._buf[idx] = val
        else:
            self._buf[idx % self.buffer_size] = val


class _FrequencyPeak:
    __slots__ = ("fft_pass_number", "peak_magnitude",
                 "corrected_peak_frequency_bin", "sample_rate_hz")

    def __init__(self, fft_pass, mag, corr_bin, sr):
        self.fft_pass_number            = fft_pass
        self.peak_magnitude             = mag
        self.corrected_peak_frequency_bin = corr_bin
        self.sample_rate_hz             = sr


class _SignatureGenerator:
    """
    shazamio.SignatureGenerator'ın numpy'sız Python portu.
    feed_input() ile s16 örnekler beslenir,
    get_next_signature() imza verisi döndürür.
    """
    SAMPLE_RATE  = 16000
    MAX_TIME_SEC = 3.1
    MAX_PEAKS    = 255

    def __init__(self):
        self._pending       = []
        self._processed     = 0

        self._ring          = _RingBuffer(2048, 0)
        self._fft_out       = _RingBuffer(256, [0.0] * 1025)
        self._spread        = _RingBuffer(256, [0.0] * 1025)

        self._peaks         = {}   # band_id → list of _FrequencyPeak
        self._num_samples   = 0

    def feed_input(self, s16_samples):
        self._pending.extend(s16_samples)

    def get_next_signature(self):
        if len(self._pending) - self._processed < 128:
            return None

        while len(self._pending) - self._processed >= 128:
            time_so_far = self._num_samples / self.SAMPLE_RATE
            peak_count  = sum(len(v) for v in self._peaks.values())
            if time_so_far >= self.MAX_TIME_SEC and peak_count >= self.MAX_PEAKS:
                break
            chunk = self._pending[self._processed: self._processed + 128]
            self._process_chunk(chunk)
            self._processed += 128

        # Reset ring buffers for next segment (matches shazamio behaviour)
        self._ring   = _RingBuffer(2048, 0)
        self._fft_out = _RingBuffer(256, [0.0] * 1025)
        self._spread  = _RingBuffer(256, [0.0] * 1025)

        return self._peaks, self._num_samples

    # ── internal ──────────────────────────────────────────────────────────────

    def _process_chunk(self, chunk128):
        self._num_samples += len(chunk128)
        pos = self._ring.position
        end = pos + len(chunk128)
        self._ring._buf[pos:end] = chunk128
        self._ring.position = end % 2048
        self._ring.num_written += len(chunk128)

        # Extract ordered ring buffer content (2048 samples)
        p   = self._ring.position
        buf = self._ring._buf[p:] + self._ring._buf[:p]

        fft_mags = _rfft_magnitudes_sq(buf)
        self._fft_out.append(fft_mags)
        self._do_spreading()
        if self._spread.num_written >= 46:
            self._do_peak_recognition()

    def _do_spreading(self):
        last = list(self._fft_out._buf[(self._fft_out.position - 1) % 256])  # 1025 floats

        # max across [k, k+1, k+2] in frequency axis
        spread_last = [0.0] * 1025
        for k in range(1025):
            spread_last[k] = max(last[k], last[k+1] if k+1 < 1025 else 0.0,
                                 last[k+2] if k+2 < 1025 else 0.0)

        i1 = (self._spread.position - 1) % 256
        i2 = (self._spread.position - 3) % 256
        i3 = (self._spread.position - 6) % 256

        # Time-domain spreading: propagate max to past frames
        s1 = self._spread._buf[i1]
        s2 = self._spread._buf[i2]
        s3 = self._spread._buf[i3]

        for k in range(1025):
            v  = spread_last[k]
            s1[k] = max(s1[k], v)
            s2[k] = max(s2[k], v)
            s3[k] = max(s3[k], v)

        self._spread._buf[i1] = s1
        self._spread._buf[i2] = s2
        self._spread._buf[i3] = s3
        self._spread.append(spread_last)

    def _do_peak_recognition(self):
        fft_m46  = self._fft_out._buf[(self._fft_out.position - 46) % 256]
        spread_m49 = self._spread._buf[(self._spread.position - 49) % 256]

        for bp in range(10, 1015):
            if fft_m46[bp] < 1.0 / 64:
                continue
            if fft_m46[bp] < spread_m49[bp - 1]:
                continue

            # frequency-domain local maximum check
            max_nbr = 0.0
            for off in [-10, -7, -4, -3, 1, 4, 7]:
                n = bp + off
                if 0 <= n < 1025:
                    if spread_m49[n] > max_nbr:
                        max_nbr = spread_m49[n]
            if fft_m46[bp] <= max_nbr:
                continue

            # time-domain local maximum check
            max_adj = max_nbr
            for toff in [-53, -45, 165, 172, 179, 186, 193, 200,
                         214, 221, 228, 235, 242, 249]:
                idx = (self._spread.position + toff) % 256
                n   = bp - 1
                if 0 <= n < 1025:
                    v = self._spread._buf[idx][n]
                    if v > max_adj:
                        max_adj = v
            if fft_m46[bp] <= max_adj:
                continue

            # Peak confirmed — calculate magnitude and corrected bin
            fft_num  = self._spread.num_written - 46

            def _log_mag(v):
                return math.log(max(1.0 / 64, v)) * 1477.3 + 6144

            mag      = _log_mag(fft_m46[bp])
            mag_prev = _log_mag(fft_m46[bp - 1]) if bp > 0    else mag
            mag_next = _log_mag(fft_m46[bp + 1]) if bp < 1024 else mag

            var1 = mag * 2 - mag_prev - mag_next
            if var1 <= 0:
                continue
            var2 = (mag_next - mag_prev) * 32.0 / var1

            corr_bin = bp * 64 + var2
            freq_hz  = corr_bin * (16000.0 / 2.0 / 1024.0 / 64.0)

            if   250 < freq_hz < 520:
                band = _BAND_250_520
            elif 520 < freq_hz < 1450:
                band = _BAND_520_1450
            elif 1450 < freq_hz < 3500:
                band = _BAND_1450_3500
            else:
                continue

            if band not in self._peaks:
                self._peaks[band] = []
            self._peaks[band].append(
                _FrequencyPeak(fft_num, int(mag), int(corr_bin), 16000))


# ── Shazam binary imza kodlaması (shazamio/signature.py'den) ─────────────────

_MAGIC1 = 0xCAFE2580
_MAGIC2 = 0x94119C00
_SAMPLE_RATE_ID_16K = 3   # SampleRate._16000

def _encode_signature_binary(peaks_by_band, num_samples):
    """
    peaks_by_band : {band_id: [_FrequencyPeak, ...]}
    num_samples   : toplam işlenen örnek sayısı
    Döner: bytes (Shazam binary imzası)
    """
    contents = BytesIO()

    for band_id in sorted(peaks_by_band.keys()):
        peaks = peaks_by_band[band_id]
        peaks_buf   = BytesIO()
        fft_pass    = 0

        for peak in peaks:
            assert peak.fft_pass_number >= fft_pass
            if peak.fft_pass_number - fft_pass >= 255:
                peaks_buf.write(b"\xff")
                peaks_buf.write(peak.fft_pass_number.to_bytes(4, "little"))
                fft_pass = peak.fft_pass_number
            peaks_buf.write(bytes([peak.fft_pass_number - fft_pass]))
            peaks_buf.write(peak.peak_magnitude.to_bytes(2, "little"))
            peaks_buf.write(peak.corrected_peak_frequency_bin.to_bytes(2, "little"))
            fft_pass = peak.fft_pass_number

        raw = peaks_buf.getvalue()
        contents.write((0x60030040 + band_id).to_bytes(4, "little"))
        contents.write(len(raw).to_bytes(4, "little"))
        contents.write(raw)
        contents.write(b"\x00" * (-len(raw) % 4))   # 4-byte alignment

    content_bytes = contents.getvalue()
    size_minus_header = len(content_bytes) + 8

    # Header (48 bytes fixed)
    # Fields (little-endian uint32 each):
    #   magic1, crc32, size_minus_header, magic2,
    #   void1[3], shifted_sample_rate_id,
    #   void2[2], number_samples_plus_divided_sample_rate, fixed_value
    shifted_sr = _SAMPLE_RATE_ID_16K << 27    # 0x18000000
    num_samp_field = int(num_samples + 16000 * 0.24)
    fixed_value = (15 << 19) + 0x40000        # 0x007C0000

    # Build buffer with placeholder CRC
    hdr = struct.pack("<IIIIIIIIIIII",
        _MAGIC1, 0,                # magic1, crc32 placeholder
        size_minus_header,
        _MAGIC2,
        0, 0, 0,                   # void1[3]
        shifted_sr,
        0, 0,                      # void2[2]
        num_samp_field,
        fixed_value,
    )
    # TLV fixed header
    tlv_hdr = struct.pack("<II", 0x40000000, size_minus_header)

    # Compute CRC over everything after first 8 bytes
    to_crc = hdr[8:] + tlv_hdr + content_bytes
    checksum = crc32(to_crc) & 0xFFFFFFFF

    # Rebuild header with real CRC
    hdr = struct.pack("<IIIIIIIIIIII",
        _MAGIC1, checksum,
        size_minus_header,
        _MAGIC2,
        0, 0, 0,
        shifted_sr,
        0, 0,
        num_samp_field,
        fixed_value,
    )
    return hdr + tlv_hdr + content_bytes


def _compute_signature_uri(pcm_bytes):
    """
    16 kHz mono s16le PCM → Shazam URI string + sample_ms.
    """
    sample_count = len(pcm_bytes) // 2
    if sample_count < 2048:
        raise ValueError("Not enough PCM samples")

    samples = list(struct.unpack("<%dh" % sample_count, pcm_bytes[:sample_count * 2]))

    gen = _SignatureGenerator()
    gen.feed_input(samples)
    result = gen.get_next_signature()
    if result is None:
        raise ValueError("Signature generator returned no data")

    peaks_by_band, num_samples = result
    if not peaks_by_band:
        raise ValueError(_("No frequency peaks found — audio may be silence"))

    binary  = _encode_signature_binary(peaks_by_band, num_samples)
    uri     = DATA_URI_PREFIX + b64encode(binary).decode("ascii")
    sample_ms = (num_samples * 1000) // 16000
    return uri, sample_ms


# ── Shazam HTTP isteği ────────────────────────────────────────────────────────

_SHAZAM_ENDPOINT = (
    "https://amp.shazam.com/discovery/v5/tr/TR/android/-/tag/{uuid1}/{uuid2}"
)
_SHAZAM_HEADERS = {
    "Content-Type":    "application/json",
    "Accept":          "application/json",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "User-Agent":      "Shazam/3.25.0-230206.1 CFNetwork/1220.1 Darwin/20.3.0",
}


def _query_shazam(signature_uri, sample_ms):
    url = _SHAZAM_ENDPOINT.format(
        uuid1=str(_uuid_mod.uuid4()).upper(),
        uuid2=str(_uuid_mod.uuid4()).upper(),
    )
    body = {
        "signature": {"uri": signature_uri, "samplems": sample_ms},
        "timestamp": int(time.time() * 1000),
        "timezone":  "Europe/Istanbul",
        "context":   {},
        "geolocation": {},
    }
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=_SHAZAM_HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            err_body = ""
        raise ValueError("Shazam HTTP %d: %s" % (exc.code, err_body))
    except Exception as exc:
        raise ValueError("Shazam request failed: %s" % exc)

    track = data.get("track")
    if not track:
        raise ValueError(_("Song not recognized"))

    title  = track.get("title", "")
    artist = track.get("subtitle", "")
    album  = ""
    rel    = ""
    for section in track.get("sections", []):
        if section.get("type") == "SONG":
            for meta in section.get("metadata", []):
                lbl = (meta.get("title") or "").lower()
                val = meta.get("text", "")
                if lbl == "album":
                    album = val
                elif lbl in ("released", "release", "year"):
                    rel = val

    return {"title": title, "artist": artist, "album": album, "release": rel}


# ── Ana tanıma fonksiyonu ─────────────────────────────────────────────────────

# Bip döngüsü için stop event
_beep_stop = threading.Event()

def _beep_loop():
    """Tanıma devam ederken 2 saniyede bir bip sesi çalar."""
    while not _beep_stop.wait(timeout=2.0):
        try:
            winsound.Beep(1000, 80)
        except Exception:
            pass


def recognize(stream_url, ffmpeg_path, _unused_api_key=""):
    acquired = _semaphore.acquire(blocking=False)
    if not acquired:
        return RecognitionResult(
            success=False, error_msg="Recognition already in progress, please wait")

    # Başlangıç sesi: iki yükselen ton
    try:
        winsound.Beep(800, 120)
        winsound.Beep(1200, 120)
    except Exception:
        pass

    # Bip döngüsünü başlat
    _beep_stop.clear()
    _beep_thread = threading.Thread(target=_beep_loop, daemon=True, name="FreeRadio-Beep")
    _beep_thread.start()

    try:
        # 1. ffmpeg kontrolü
        if not os.path.isfile(ffmpeg_path):
            return RecognitionResult(
                success=False,
                error_msg=(_(
                    "ffmpeg.exe not found. Download ffmpeg from "
                    "https://ffmpeg.org/download.html and place ffmpeg.exe "
                    "in the FreeRadio addon folder, or set the path in settings."
                )),
            )

        # 2. URL çözümle
        log.info("FreeRadio Recognizer: resolving %s", stream_url)
        resolved = _resolve_to_audio_url(stream_url)
        if resolved and resolved != stream_url:
            log.info("FreeRadio Recognizer: resolved → %s", resolved)
            stream_url = resolved
        elif not resolved:
            log.warning("FreeRadio Recognizer: could not resolve, trying original")

        # 3. ffmpeg ile PCM al
        log.info("FreeRadio Recognizer: decoding %ds PCM via ffmpeg", _SAMPLE_DURATION)
        try:
            pcm_bytes = _decode_to_pcm(ffmpeg_path, stream_url, _SAMPLE_DURATION)
        except Exception as exc:
            log.warning("FreeRadio Recognizer: ffmpeg error: %s", exc)
            return RecognitionResult(
                success=False, error_msg="Audio decode error: %s" % str(exc))

        log.info("FreeRadio Recognizer: %d PCM bytes received", len(pcm_bytes))

        # 4. Shazam imzası üret
        log.info("FreeRadio Recognizer: computing signature")
        try:
            sig_uri, sample_ms = _compute_signature_uri(pcm_bytes)
        except Exception as exc:
            log.warning("FreeRadio Recognizer: signature error: %s", exc)
            return RecognitionResult(
                success=False, error_msg="Signature error: %s" % str(exc))

        # 5. Shazam sorgusu
        log.info("FreeRadio Recognizer: querying Shazam (sample_ms=%d)", sample_ms)
        try:
            result = _query_shazam(sig_uri, sample_ms)
        except ValueError as exc:
            log.info("FreeRadio Recognizer: %s", exc)
            return RecognitionResult(success=False, error_msg=str(exc))
        except Exception as exc:
            log.warning("FreeRadio Recognizer: Shazam error: %s", exc)
            return RecognitionResult(
                success=False, error_msg="Shazam error: %s" % str(exc))

        title  = result.get("title",   "")
        artist = result.get("artist",  "")
        album  = result.get("album",   "")
        rel    = result.get("release", "")

        log.info("FreeRadio Recognizer: '%s' by '%s'", title, artist)
        return RecognitionResult(
            success=True, title=title, artist=artist,
            album=album, release_date=rel, score=1.0,
        )

    finally:
        # Bip döngüsünü durdur
        _beep_stop.set()
        # Bitiş sesi: iki alçalan ton
        try:
            winsound.Beep(1200, 120)
            winsound.Beep(800, 120)
        except Exception:
            pass
        _semaphore.release()


def recognize_async(stream_url, ffmpeg_path, api_key, callback):
    """api_key geriye dönük uyumluluk için korunmuştur (kullanılmaz)."""
    def _worker():
        result = recognize(stream_url, ffmpeg_path, api_key)
        try:
            callback(result)
        except Exception as exc:
            log.error("FreeRadio Recognizer callback error: %s", exc)
    t = threading.Thread(target=_worker, daemon=True, name="FreeRadio-Recognize")
    t.start()
    return t