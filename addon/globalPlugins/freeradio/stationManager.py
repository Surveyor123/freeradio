# -*- coding: utf-8 -*-
# FreeRadio - Station Manager
# Fetches stations from Radio Browser API and manages favorites.

import json
import logging
import os
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import globalVars

log = logging.getLogger(__name__)


class RadioBrowserError(Exception):
	"""Base exception for all Radio Browser API errors."""

class RadioBrowserConnectionError(RadioBrowserError):
	"""Raised when no mirror is reachable (network/firewall issue)."""

class RadioBrowserTimeoutError(RadioBrowserError):
	"""Raised when all mirrors time out."""

class RadioBrowserAPIError(RadioBrowserError):
	"""Raised when a mirror responds but returns invalid/unexpected data."""


RADIO_BROWSER_MIRRORS = [
	"https://de1.api.radio-browser.info/json",
	"https://nl1.api.radio-browser.info/json",
	"https://at1.api.radio-browser.info/json",
]
USER_AGENT = "FreeRadio-NVDA/1.0"
REQUEST_TIMEOUT = 10
COUNTRY_STATION_LIMIT = 500
SEARCH_LIMIT = 500

# Bir mirror bu kadar ardışık hata verirse cache sıfırlanır ve
# bir sonraki istekte en sağlıklı mirror yeniden belirlenir.
_MIRROR_FAIL_THRESHOLD = 3


def _get_favorites_path():
	return os.path.join(globalVars.appArgs.configPath, "freeradio_favorites.json")


class StationManager:

	def __init__(self):
		self._favorites = []
		self._load_favorites()
		self._api_base          = None  # working mirror; determined on first request
		self._api_base_failures = 0     # consecutive failure count for cached mirror

	def _get_api_base(self):
		"""Return the first reachable mirror, caching the result."""
		if self._api_base:
			return self._api_base
		for mirror in RADIO_BROWSER_MIRRORS:
			try:
				req = urllib.request.Request(
					mirror + "/stats",
					headers={"User-Agent": USER_AGENT},
				)
				with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT):
					self._api_base = mirror
					log.info("FreeRadio: using mirror %s", mirror)
					return mirror
			except Exception:
				log.warning("FreeRadio: mirror unreachable: %s", mirror)
		self._api_base = RADIO_BROWSER_MIRRORS[0]
		return self._api_base

	def _request(self, path, params=""):
		"""
		path  : e.g. "/stations/topvote/1000", with a leading slash
		params: query string without leading ? or &, e.g. "hidebroken=true"

		Tries every mirror in order. Returns parsed JSON data on success.
		Raises a RadioBrowserError subclass when all mirrors fail, so callers
		can distinguish network problems from API/data problems.

		Mirror cache: ilk başarılı mirror _api_base'e yazılır ve sonraki
		isteklerde önce o denenir. Aynı mirror art arda _MIRROR_FAIL_THRESHOLD
		kez hata verirse cache sıfırlanır; bir sonraki istekte tüm mirror'lar
		yeniden değerlendirilir.
		"""
		import socket
		import urllib.error

		url_pattern = (
			("{mirror}{path}?{params}" if params else "{mirror}{path}")
		)

		last_error       = None
		had_timeout      = False
		had_connection   = False
		had_json_error   = False

		# Bilinen çalışan mirror'ı listeye öne al; diğerleri yedek sırasında.
		if self._api_base and self._api_base in RADIO_BROWSER_MIRRORS:
			ordered = [self._api_base] + [m for m in RADIO_BROWSER_MIRRORS if m != self._api_base]
		else:
			ordered = list(RADIO_BROWSER_MIRRORS)

		for mirror in ordered:
			url = url_pattern.format(mirror=mirror, path=path, params=params)
			try:
				req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
				with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
					raw = resp.read().decode("utf-8")
				try:
					data = json.loads(raw)
				except json.JSONDecodeError as exc:
					had_json_error = True
					last_error = exc
					log.warning(
						"FreeRadio: JSON decode error from %s (%s): %.120s…",
						mirror, exc, raw,
					)
					# Bu mirror'dan kötü veri geldi; sayacı artır / cache'i sıfırla.
					if mirror == self._api_base:
						self._api_base_failures += 1
						if self._api_base_failures >= _MIRROR_FAIL_THRESHOLD:
							log.warning(
								"FreeRadio: mirror %s failed %d times, resetting cache",
								mirror, self._api_base_failures,
							)
							self._api_base          = None
							self._api_base_failures = 0
					continue  # try next mirror
				# Başarılı — cache'i güncelle, hata sayacını sıfırla.
				if mirror != self._api_base:
					log.info("FreeRadio: switching to mirror %s", mirror)
				self._api_base          = mirror
				self._api_base_failures = 0
				return data

			except urllib.error.HTTPError as exc:
				last_error = exc
				log.warning(
					"FreeRadio: HTTP %d from %s — %s",
					exc.code, mirror, exc.reason,
				)
				if mirror == self._api_base:
					self._api_base_failures += 1
					if self._api_base_failures >= _MIRROR_FAIL_THRESHOLD:
						log.warning(
							"FreeRadio: mirror %s failed %d times, resetting cache",
							mirror, self._api_base_failures,
						)
						self._api_base          = None
						self._api_base_failures = 0
			except (TimeoutError, socket.timeout) as exc:
				had_timeout = True
				last_error = exc
				log.warning("FreeRadio: timeout reaching %s", mirror)
				if mirror == self._api_base:
					self._api_base_failures += 1
					if self._api_base_failures >= _MIRROR_FAIL_THRESHOLD:
						log.warning(
							"FreeRadio: mirror %s failed %d times, resetting cache",
							mirror, self._api_base_failures,
						)
						self._api_base          = None
						self._api_base_failures = 0
			except (ConnectionError, OSError, urllib.error.URLError) as exc:
				had_connection = True
				last_error = exc
				log.warning("FreeRadio: connection error (%s): %s", mirror, exc)
				if mirror == self._api_base:
					self._api_base_failures += 1
					if self._api_base_failures >= _MIRROR_FAIL_THRESHOLD:
						log.warning(
							"FreeRadio: mirror %s failed %d times, resetting cache",
							mirror, self._api_base_failures,
						)
						self._api_base          = None
						self._api_base_failures = 0
			except Exception as exc:
				last_error = exc
				log.warning("FreeRadio: unexpected error (%s): %s", mirror, exc)

		if had_json_error and not had_connection and not had_timeout:
			raise RadioBrowserAPIError(
				"All mirrors returned invalid JSON. "
				"The Radio Browser API may be temporarily broken."
			) from last_error
		if had_timeout and not had_connection:
			raise RadioBrowserTimeoutError(
				"All Radio Browser mirrors timed out. "
				"Your internet connection may be slow or the service is overloaded."
			) from last_error
		raise RadioBrowserConnectionError(
			"Could not reach any Radio Browser mirror. "
			"Please check your internet connection."
		) from last_error

	def search_stations(self, query, limit=SEARCH_LIMIT):
		"""Search stations by name, country, and tag simultaneously.

		Üç alt sorgu (isim, ülke, etiket) ThreadPoolExecutor ile paralel
		çalıştırılır; sonuçlar birleştirilip vote sırasına göre döner.
		Raises RadioBrowserError subclasses on network/API failure.
		"""
		encoded = urllib.parse.quote(query)
		path = "/stations/search"
		base_params = f"limit={limit}&order=votes&reverse=true"

		sub_queries = [
			("name",    f"{base_params}&name={encoded}"),
			("country", f"{base_params}&country={encoded}"),
			("tag",     f"{base_params}&tag={encoded}"),
		]

		seen        = {}
		last_exc    = None
		any_success = False

		def _fetch(label, params):
			return label, self._request(path, params)

		with ThreadPoolExecutor(max_workers=3) as pool:
			futures = {
				pool.submit(_fetch, label, params): label
				for label, params in sub_queries
			}
			for future in as_completed(futures):
				label = futures[future]
				try:
					_, results = future.result()
					any_success = True
					for s in results:
						uid = s.get("stationuuid", "")
						if uid and uid not in seen:
							seen[uid] = s
				except RadioBrowserError as exc:
					if last_exc is None:
						last_exc = exc
					log.warning("FreeRadio: search sub-query failed (%s): %s", label, exc)

		if not any_success:
			raise last_exc or RadioBrowserConnectionError(
				"Search failed: could not reach Radio Browser."
			)

		merged = sorted(seen.values(), key=lambda s: s.get("votes", 0), reverse=True)
		return merged[:limit]

	def get_top_stations(self, limit=1000):
		"""Return the top-voted stations. Raises RadioBrowserError on failure."""
		return self._request(f"/stations/topvote/{limit}", "hidebroken=true")

	def get_stations_by_country(self, countrycode, limit=COUNTRY_STATION_LIMIT):
		"""Return stations for the given ISO 3166-1 alpha-2 country code.
		Raises RadioBrowserError on failure.
		"""
		code = urllib.parse.quote(countrycode.upper())
		return self._request(
			f"/stations/bycountrycodeexact/{code}",
			f"limit={limit}&order=votes&reverse=true&hidebroken=true",
		)

	def get_stations_by_tag(self, tag, limit=500):
		"""Return stations matching the given tag. Raises RadioBrowserError on failure."""
		encoded = urllib.parse.quote(tag.lower())
		return self._request(
			f"/stations/bytag/{encoded}",
			f"limit={limit}&order=votes&reverse=true&hidebroken=true",
		)

	def get_countries(self):
		"""Return all countries from the API.
		Tries /countries first; falls back to /countrycodes (/countrycodes uses
		name=code format instead of iso_3166_1).
		Raises RadioBrowserError only if both endpoints fail.
		"""
		try:
			data = self._request("/countries", "order=stationcount&reverse=true&hidebroken=true")
			if data:
				return data
		except RadioBrowserError:
			log.warning("FreeRadio: /countries failed, trying /countrycodes")
		return self._request("/countrycodes", "order=stationcount&reverse=true")

	@staticmethod
	def get_user_countrycode():
		"""Return the two-letter ISO country code, trying multiple methods."""
		# 1. Windows: user geographic location (GetUserGeoID + GetGeoInfoW)
		try:
			import ctypes
			import ctypes.wintypes
			kernel32 = ctypes.windll.kernel32
			geo_id = kernel32.GetUserGeoID(16)  # GEOCLASS_NATION = 16
			if geo_id and geo_id != 0x7FFFFFFF:  # GEOID_NOT_AVAILABLE
				buf = ctypes.create_unicode_buffer(10)
				# GEO_ISO2 = 4
				if kernel32.GetGeoInfoW(geo_id, 4, buf, 10, 0):
					code = buf.value.strip()
					if len(code) == 2:
						log.info("FreeRadio: country from GeoID: %s", code)
						return code.upper()
		except Exception:
			pass

		# 2. Windows: system locale (GetUserDefaultLCID)
		try:
			import ctypes
			kernel32 = ctypes.windll.kernel32
			lcid = kernel32.GetUserDefaultLCID()
			buf = ctypes.create_unicode_buffer(10)
			# LOCALE_SISO3166CTRYNAME = 0x5A
			if kernel32.GetLocaleInfoW(lcid, 0x5A, buf, 10):
				code = buf.value.strip()
				if len(code) == 2:
					log.info("FreeRadio: country from LCID: %s", code)
					return code.upper()
		except Exception:
			pass

		# 3. Python locale (platform-independent fallback)
		try:
			import locale
			lang, _enc = locale.getlocale()
			if lang and "_" in lang:
				return lang.split("_")[1].upper()
		except Exception:
			pass

		return None


	def _load_favorites(self):
		path = _get_favorites_path()
		try:
			if os.path.exists(path):
				with open(path, "r", encoding="utf-8") as f:
					self._favorites = json.load(f)
		except Exception:
			self._favorites = []

	def _save_favorites(self):
		path = _get_favorites_path()
		try:
			with open(path, "w", encoding="utf-8") as f:
				json.dump(self._favorites, f, ensure_ascii=False, indent=2)
		except Exception:
			log.error("FreeRadio: failed to save favorites", exc_info=True)

	def get_favorites(self):
		return list(self._favorites)

	def is_favorite(self, station):
		uid = station.get("stationuuid", "")
		return bool(uid and any(s.get("stationuuid") == uid for s in self._favorites))

	def add_favorite(self, station):
		if not self.is_favorite(station):
			self._favorites.append(station)
			self._save_favorites()

	def remove_favorite(self, station):
		uid = station.get("stationuuid", "")
		self._favorites = [s for s in self._favorites if s.get("stationuuid") != uid]
		self._save_favorites()

	def move_favorite_up(self, station):
		uid = station.get("stationuuid", "")
		idx = next((i for i, s in enumerate(self._favorites) if s.get("stationuuid") == uid), -1)
		if idx > 0:
			self._favorites[idx - 1], self._favorites[idx] = self._favorites[idx], self._favorites[idx - 1]
			self._save_favorites()
			return idx - 1
		return idx

	def move_favorite_down(self, station):
		uid = station.get("stationuuid", "")
		idx = next((i for i, s in enumerate(self._favorites) if s.get("stationuuid") == uid), -1)
		if 0 <= idx < len(self._favorites) - 1:
			self._favorites[idx], self._favorites[idx + 1] = self._favorites[idx + 1], self._favorites[idx]
			self._save_favorites()
			return idx + 1
		return idx

	def add_custom_station(self, name, url):
		station = {
			"stationuuid": "custom-" + str(uuid.uuid4()),
			"name": name.strip(),
			"url": url.strip(),
			"url_resolved": url.strip(),
			"countrycode": "",
			"tags": "",
			"votes": 0,
		}
		self.add_favorite(station)
		return station