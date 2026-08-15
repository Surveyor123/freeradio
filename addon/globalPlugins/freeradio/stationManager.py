# -*- coding: utf-8 -*-
# FreeRadio - Station Manager
# Fetches stations from Radio Browser API and manages favorites.

import gzip
import json
import logging
import os
import socket
import time
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import globalVars

from . import externalSources

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
]  # fallback list — used only when DNS discovery fails
USER_AGENT = "FreeRadio-NVDA/1.0"
REQUEST_TIMEOUT = 10
COUNTRY_STATION_LIMIT = 1000
SEARCH_LIMIT = 1000

# --- Local station catalog cache ---------------------------------------
# Instead of hitting the Radio Browser API on every search, the full station
# catalog is periodically synced into a local gzip-compressed JSON cache
# (NVDA's bundled Python has no sqlite3 module, so a plain file is used
# instead of a DB). Once loaded, searches/filters run entirely in memory
# (no network round-trip), which keeps the UI responsive even on slow
# connections.
CACHE_FILENAME             = "freeradio_stations_cache.json.gz"
CACHE_SYNC_INTERVAL        = 12 * 60 * 60  # re-sync the catalog every 12h
CACHE_PAGE_SIZE            = 5000          # stations fetched per API page
CACHE_MAX_PAGES            = 30            # safety cap (~150k stations)

# Retry behaviour for HTTP 5xx responses (e.g. 503 Service Unavailable).
_HTTP_RETRY_STATUSES = {503, 502, 504}
_HTTP_RETRY_DELAY    = 2   # seconds to wait before retrying


def _discover_mirrors():
	"""Return a shuffled list of live Radio Browser server URLs via DNS lookup.

	Follows the approach recommended by the Radio Browser API docs:
	  1. Resolve 'all.api.radio-browser.info' to get all server IPs.
	  2. Reverse-lookup each IP to get the human-readable hostname.
	  3. Shuffle and return as https://<host>/json URLs.

	Falls back to the hardcoded RADIO_BROWSER_MIRRORS list on any error.
	"""
	import random
	try:
		ips = socket.getaddrinfo(
			"all.api.radio-browser.info", 80, 0, 0, socket.IPPROTO_TCP
		)
		hosts = []
		for entry in ips:
			ip = entry[4][0]
			try:
				host = socket.gethostbyaddr(ip)[0]
				url  = f"https://{host}/json"
				if url not in hosts:
					hosts.append(url)
			except Exception as exc:
				log.warning("FreeRadio: reverse lookup failed for %s: %s", ip, exc)
		if hosts:
			random.shuffle(hosts)
			log.info("FreeRadio: discovered mirrors via DNS: %s", hosts)
			return hosts
		log.warning("FreeRadio: DNS discovery returned no usable hosts")
	except Exception as exc:
		log.warning("FreeRadio: DNS discovery failed: %s — using fallback list", exc)
	return list(RADIO_BROWSER_MIRRORS)

# If a mirror gives this many consecutive errors, the cache is reset and
# The healthiest mirror is determined again on the next request.
_MIRROR_FAIL_THRESHOLD = 3


def _get_favorites_path():
	return os.path.join(globalVars.appArgs.configPath, "freeradio_favorites.json")


class StationManager:

	def __init__(self):
		self._favorites = []
		self._load_favorites()
		self._api_base          = None  # working mirror; determined on first request
		self._api_base_failures = 0     # consecutive failure count for cached mirror
		self._mirrors           = None  # discovered mirror list; None = not yet fetched
		self._catalog           = None  # in-memory station cache, sorted by votes desc
		self._sync_lock         = None
		import threading as _t
		self._sync_lock = _t.Lock()
		# Kick off DNS discovery and catalog cache loading in the background
		# so both are ready (or well underway) before the first request.
		_t.Thread(target=self._prefetch_mirrors, daemon=True).start()
		_t.Thread(target=self._init_cache, daemon=True).start()

	def _prefetch_mirrors(self):
		if self._mirrors is None:
			self._mirrors = _discover_mirrors()

	# -------------------------------------------------------------------
	# Local station catalog cache
	# -------------------------------------------------------------------

	def _cache_path(self):
		return os.path.join(globalVars.appArgs.configPath, CACHE_FILENAME)

	def _load_cache_file(self):
		"""Return (stations, last_sync) from the local cache file.
		Returns ([], None) if the file is missing, unreadable, or corrupt."""
		path = self._cache_path()
		if not os.path.exists(path):
			return [], None
		try:
			with gzip.open(path, "rt", encoding="utf-8") as fh:
				payload = json.load(fh)
			return payload.get("stations", []), payload.get("last_sync")
		except Exception as exc:
			log.warning("FreeRadio: failed to read station cache: %s", exc)
			return [], None

	def _write_cache_file(self, stations):
		"""Write the station catalog to the local cache file.
		Writes to a temp file first and swaps it in with os.replace(), so a
		crash mid-write can never leave a corrupt cache behind."""
		path     = self._cache_path()
		tmp_path = path + ".tmp"
		payload  = {"last_sync": time.time(), "stations": stations}
		with gzip.open(tmp_path, "wt", encoding="utf-8") as fh:
			json.dump(payload, fh, ensure_ascii=False)
		os.replace(tmp_path, path)

	def _init_cache(self):
		"""Load any existing cache into memory immediately (so searches can
		use it right away), then trigger a background sync if it's missing
		or stale. Runs on its own thread — never blocks the NVDA UI.
		"""
		catalog, last_sync = self._load_cache_file()
		if catalog:
			self._catalog = catalog
			log.info("FreeRadio: loaded %d stations from local cache", len(catalog))
		stale = (not last_sync) or (time.time() - float(last_sync) > CACHE_SYNC_INTERVAL)
		if stale:
			self._sync_catalog()

	def _sync_catalog(self):
		"""Fetch the full station catalog from the API and replace the local
		cache with it. Safe to call repeatedly/concurrently — a second call
		while one is already running is a no-op. On failure, the existing
		cache (if any) is left untouched so search keeps working.
		"""
		if not self._sync_lock.acquire(blocking=False):
			log.info("FreeRadio: catalog sync already in progress, skipping")
			return
		try:
			all_stations = []
			offset = 0
			for _page in range(CACHE_MAX_PAGES):
				params = (
					f"limit={CACHE_PAGE_SIZE}&offset={offset}"
					f"&order=votes&reverse=true&hidebroken=true"
				)
				try:
					page = self._request("/stations/search", params)
				except RadioBrowserError as exc:
					log.warning("FreeRadio: catalog sync failed at offset %d: %s", offset, exc)
					if not all_stations:
						return  # first page failed — keep the existing cache untouched
					break  # a partial refresh is still better than nothing
				if not page:
					break
				all_stations.extend(page)
				if len(page) < CACHE_PAGE_SIZE:
					break
				offset += CACHE_PAGE_SIZE

			if not all_stations:
				return

			try:
				self._write_cache_file(all_stations)
			except Exception:
				log.error("FreeRadio: failed to write station cache to disk", exc_info=True)

			# Already sorted by votes desc (the API query requested that order).
			self._catalog = all_stations
			log.info("FreeRadio: catalog sync complete — %d stations cached", len(all_stations))
		finally:
			self._sync_lock.release()

	def is_syncing(self):
		"""True while a catalog sync is in progress (e.g. to disable a
		'refresh now' button and avoid stacking requests)."""
		return self._sync_lock.locked()

	def refresh_catalog_async(self, on_done=None):
		"""Kick off an immediate background catalog re-sync (e.g. from a
		user-triggered 'refresh now' button). Callers should check
		is_syncing() first to avoid stacking requests. *on_done*, if given,
		is called with no arguments on this background thread once the
		attempt finishes — callers driving a GUI should marshal it back to
		the main thread themselves (e.g. wx.CallAfter)."""
		import threading as _t

		def _run():
			self._sync_catalog()
			if on_done:
				on_done()

		_t.Thread(target=_run, daemon=True).start()

	def catalog_ready(self):
		return bool(self._catalog)

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

	def _maybe_invalidate_mirror(self, mirror):
		"""Increment the consecutive failure counter for the cached mirror.
		If the counter reaches _MIRROR_FAIL_THRESHOLD, reset the cache so
		the next request re-evaluates all mirrors from scratch.
		Only has an effect when *mirror* is the currently cached mirror.
		"""
		if mirror != self._api_base:
			return
		self._api_base_failures += 1
		if self._api_base_failures >= _MIRROR_FAIL_THRESHOLD:
			log.warning(
				"FreeRadio: mirror %s failed %d times, resetting cache",
				mirror, self._api_base_failures,
			)
			self._api_base          = None
			self._api_base_failures = 0
			self._mirrors           = None  # re-discover via DNS on next request

	def _request(self, path, params=""):
		"""
		path  : e.g. "/stations/topvote/1000", with a leading slash
		params: query string without leading ? or &, e.g. "hidebroken=true"

		Tries every mirror in order. Returns parsed JSON data on success.
		Raises a RadioBrowserError subclass when all mirrors fail, so callers
		can distinguish network problems from API/data problems.

		Mirror cache: the first successful mirror is stored in _api_base and
		tried first on subsequent requests.  If that mirror fails
		_MIRROR_FAIL_THRESHOLD times in a row, _maybe_invalidate_mirror()
		resets the cache so all mirrors are re-evaluated on the next call.
		"""
		import urllib.error

		url_pattern = (
			("{mirror}{path}?{params}" if params else "{mirror}{path}")
		)

		last_error       = None
		had_timeout      = False
		had_connection   = False
		had_json_error   = False

		# Prioritise the known-good mirror; fall back to the rest in order.
		if self._mirrors is None:
			self._mirrors = _discover_mirrors()
		mirrors = self._mirrors

		if self._api_base and self._api_base in mirrors:
			ordered = [self._api_base] + [m for m in mirrors if m != self._api_base]
		else:
			ordered = list(mirrors)

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
					# Bad data from this mirror; increment failure counter / reset cache.
					self._maybe_invalidate_mirror(mirror)
					continue  # try next mirror
				# Success — update cache and reset failure counter.
				if mirror != self._api_base:
					log.info("FreeRadio: switching to mirror %s", mirror)
				self._api_base          = mirror
				self._api_base_failures = 0
				return data

			except urllib.error.HTTPError as exc:
				if exc.code in _HTTP_RETRY_STATUSES:
					log.warning(
						"FreeRadio: HTTP %d from %s — retrying in %ds",
						exc.code, mirror, _HTTP_RETRY_DELAY,
					)
					import time as _time
					_time.sleep(_HTTP_RETRY_DELAY)
					try:
						with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
							raw = resp.read().decode("utf-8")
						data = json.loads(raw)
						if mirror != self._api_base:
							log.info("FreeRadio: switching to mirror %s (after retry)", mirror)
						self._api_base          = mirror
						self._api_base_failures = 0
						return data
					except urllib.error.HTTPError as retry_exc:
						last_error = retry_exc
						log.warning(
							"FreeRadio: HTTP %d from %s after retry — moving on",
							retry_exc.code, mirror,
						)
						self._maybe_invalidate_mirror(mirror)
						continue  # try next mirror
					except (TimeoutError, socket.timeout) as retry_exc:
						had_timeout = True
						last_error  = retry_exc
						self._maybe_invalidate_mirror(mirror)
						continue
					except Exception as retry_exc:
						had_connection = True
						last_error     = retry_exc
						self._maybe_invalidate_mirror(mirror)
						continue
				last_error = exc
				log.warning(
					"FreeRadio: HTTP %d from %s — %s",
					exc.code, mirror, exc.reason,
				)
				self._maybe_invalidate_mirror(mirror)
			except (TimeoutError, socket.timeout) as exc:
				had_timeout = True
				last_error = exc
				log.warning("FreeRadio: timeout reaching %s", mirror)
				self._maybe_invalidate_mirror(mirror)
			except (ConnectionError, OSError, urllib.error.URLError) as exc:
				had_connection = True
				last_error = exc
				log.warning("FreeRadio: connection error (%s): %s", mirror, exc)
				self._maybe_invalidate_mirror(mirror)
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

	def search_stations(self, query, limit=SEARCH_LIMIT, countrycode=None):
		"""Search stations by name, country, and tag simultaneously.

		If the local catalog cache is populated, the search runs entirely
		in memory against it (no network round-trip, results in
		milliseconds). Otherwise — e.g. on the very first run, before the
		background sync has completed — this falls back to the older
		network-based multi-mirror search so the feature still works.

		If countrycode is provided, results are filtered to that country.
		Raises RadioBrowserError subclasses on network/API failure (only
		possible in the fallback path).
		"""
		catalog = self._catalog
		if catalog:
			return self._search_catalog(catalog, query, limit, countrycode)
		return self._search_stations_online(query, limit, countrycode)

	@staticmethod
	def _search_catalog(catalog, query, limit, countrycode):
		"""Filter the in-memory catalog for *query*, optionally scoped to
		*countrycode*. The catalog is already sorted by votes desc, so the
		filtered result preserves that order."""
		from .utils import matches_query as _mq

		query = query.strip()
		cc = countrycode.upper() if countrycode else None
		filtered = [
			s for s in catalog
			if (not cc or s.get("countrycode", "").upper() == cc) and _mq(s, query)
		]
		total_found = len(filtered)
		return filtered[:limit], total_found

	def _search_stations_online(self, query, limit=SEARCH_LIMIT, countrycode=None):
		"""Network fallback for search_stations() — used only while the local
		catalog cache has not been populated yet.

		Each token in the query is sent to the API separately (name/tag/country),
		results are unioned, then the full query is applied as a local post-filter
		so every token must appear in the station data.  This gives the widest
		possible API coverage while still enforcing AND semantics.
		"""
		from .utils import matches_query as _mq

		path = "/stations/search"
		# Use a higher internal limit to discover the real total result count;
		# the returned list is sliced to the user's limit by the caller.
		_DISCOVERY_LIMIT = max(limit, 10000)
		base_params = f"limit={_DISCOVERY_LIMIT}&order=votes&reverse=true"
		if countrycode:
			base_params += f"&countrycode={urllib.parse.quote(countrycode.upper())}"

		tokens = query.strip().split()
		if not tokens:
			tokens = [query.strip()]

		# Build one name+tag+country triple per token — union all results.
		sub_queries = []
		for token in tokens:
			encoded = urllib.parse.quote(token)
			sub_queries.append((f"name:{token}",    f"{base_params}&name={encoded}"))
			sub_queries.append((f"tag:{token}",     f"{base_params}&tag={encoded}"))
			sub_queries.append((f"country:{token}", f"{base_params}&country={encoded}"))

		seen        = {}
		last_exc    = None
		any_success = False

		def _fetch(label, params):
			return label, self._request(path, params)

		with ThreadPoolExecutor(max_workers=min(9, len(sub_queries))) as pool:
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

		# Post-filter: all tokens must appear somewhere in the station data.
		filtered = [s for s in seen.values() if _mq(s, query)]

		merged = sorted(filtered, key=lambda s: s.get("votes", 0), reverse=True)
		total_found = len(merged)
		return merged[:limit], total_found

	def search_tunein(self, query, limit=50):
		"""Search TuneIn for *query*. Best-effort — returns [] on any error,
		never raises. Thin wrapper so callers only ever talk to the manager,
		not to externalSources directly."""
		return externalSources.search_tunein((query or "").strip(), limit=limit)

	def search_iheart(self, query, limit=50):
		"""Search iHeartRadio for *query*. Best-effort — returns [] on any
		error, never raises. Thin wrapper so callers only ever talk to the
		manager, not to externalSources directly."""
		return externalSources.search_iheart((query or "").strip(), limit=limit)

	def search_external(self, query, limit=50):
		"""Search TuneIn and iHeartRadio (in parallel) for *query* and return
		a merged list of normalised station dicts.

		Best-effort by design: neither service has a stable public API, so a
		failure in either source is logged and simply contributes no results
		— this method never raises. NOTE: this waits for BOTH sources before
		returning, so a slow/unreachable one delays the other — callers that
		want each source's results as soon as they're ready (e.g. the search
		dialog) should call search_tunein()/search_iheart() independently
		instead. This combined method is kept for callers that just want one
		merged list and don't care about per-source latency.
		"""
		query = (query or "").strip()
		if not query:
			return []

		results = []
		sources = {
			"TuneIn": lambda: self.search_tunein(query, limit=limit),
			"iHeart": lambda: self.search_iheart(query, limit=limit),
		}
		with ThreadPoolExecutor(max_workers=len(sources)) as pool:
			futures = {pool.submit(fn): label for label, fn in sources.items()}
			for future in as_completed(futures):
				label = futures[future]
				try:
					results.extend(future.result())
				except Exception as exc:
					log.warning("FreeRadio: external search source %s failed: %s", label, exc)
		return results

	def get_top_stations(self, limit=1000):
		"""Return the top-voted stations. Raises RadioBrowserError on failure
		(only possible when falling back to the network — the catalog cache
		is already sorted by votes desc, so slicing it is instant)."""
		catalog = self._catalog
		if catalog:
			return catalog[:limit]
		return self._request(f"/stations/topvote/{limit}", "hidebroken=true")

	def get_stations_by_country(self, countrycode, limit=COUNTRY_STATION_LIMIT):
		"""Return stations for the given ISO 3166-1 alpha-2 country code.
		Returns (stations, total_found) where total_found is len(raw) — the
		caller (radioDialog) is responsible for substituting the cached
		stationcount from _fetch_countries when available.
		Raises RadioBrowserError on failure (only possible in the network
		fallback path).
		"""
		catalog = self._catalog
		if catalog:
			cc = countrycode.upper()
			matches = [s for s in catalog if s.get("countrycode", "").upper() == cc]
			return matches[:limit], len(matches)
		code = urllib.parse.quote(countrycode.upper())
		raw = self._request(
			f"/stations/bycountrycodeexact/{code}",
			f"limit={limit}&order=votes&reverse=true&hidebroken=true",
		)
		total_found = len(raw)
		return raw, total_found

	def get_stations_by_tag(self, tag, limit=500):
		"""Return stations matching the given tag. Raises RadioBrowserError on
		failure (only possible in the network fallback path)."""
		catalog = self._catalog
		if catalog:
			needle = tag.strip().lower()
			matches = [
				s for s in catalog
				if any(t.strip().lower() == needle for t in s.get("tags", "").split(","))
			]
			return matches[:limit]
		encoded = urllib.parse.quote(tag.lower())
		return self._request(
			f"/stations/bytag/{encoded}",
			f"limit={limit}&order=votes&reverse=true&hidebroken=true",
		)

	def get_countries(self):
		"""Return all countries with their station counts.
		Built from the local catalog cache when available; otherwise tries
		the /countries API endpoint, falling back to /countrycodes
		(/countrycodes uses name=code format instead of iso_3166_1).
		Raises RadioBrowserError only in the network fallback path, and only
		if both endpoints fail.
		"""
		catalog = self._catalog
		if catalog:
			counts = {}
			for s in catalog:
				code = s.get("countrycode", "").strip().upper()
				if code:
					counts[code] = counts.get(code, 0) + 1
			result = [{"iso_3166_1": code, "stationcount": count} for code, count in counts.items()]
			result.sort(key=lambda c: c["stationcount"], reverse=True)
			return result
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


	def export_favorites_json(self, path):
		"""Write all favourites to *path* as a UTF-8 JSON file.

		The file is a plain JSON array of station dicts — the same format
		used internally by freeradio_favorites.json — so it can be re-imported
		without any conversion.

		Raises OSError / IOError on write failure.
		"""
		with open(path, "w", encoding="utf-8") as fh:
			json.dump(self._favorites, fh, ensure_ascii=False, indent=2)

	def export_favorites_m3u(self, path):
		"""Write all favourites to *path* as an extended M3U playlist.

		Each entry uses the #EXTINF directive so media players display the
		station name.  The URL field is used; url_resolved is ignored so the
		playlist stays portable across network conditions.

		Raises OSError / IOError on write failure.
		"""
		lines = ["#EXTM3U"]
		for s in self._favorites:
			name = s.get("name", "").strip() or "Unknown"
			url  = s.get("url", "").strip()
			if url:
				lines.append(f"#EXTINF:-1,{name}")
				lines.append(url)
		with open(path, "w", encoding="utf-8") as fh:
			fh.write("\n".join(lines))

	def import_favorites(self, path, merge=True):
		"""Import favourites from a JSON or M3U file.

		Parameters
		----------
		path  : str   – path to the file to import
		merge : bool  – True  → add imported stations that are not already
								   present (matched by stationuuid or URL);
						False → replace the entire favourites list.

		Returns
		-------
		int  – number of stations actually added (0 when merge=False means
			   all existing entries were replaced, not that none were loaded).

		Raises
		------
		ValueError  – file format is unrecognised or contains no valid stations.
		OSError     – file cannot be read.
		"""
		ext = os.path.splitext(path)[1].lower()
		if ext == ".json":
			stations = self._parse_import_json(path)
		elif ext in (".m3u", ".m3u8"):
			stations = self._parse_import_m3u(path)
		else:
			raise ValueError(f"Unsupported file format: {ext!r}")

		if not stations:
			raise ValueError("No valid stations found in the selected file.")

		if not merge:
			self._favorites = stations
			self._save_favorites()
			return len(stations)

		# Merge: skip duplicates matched by stationuuid (preferred) or URL.
		existing_uuids = {s.get("stationuuid", "") for s in self._favorites}
		existing_urls  = {s.get("url", "").strip()  for s in self._favorites}
		added = 0
		for s in stations:
			uid = s.get("stationuuid", "")
			url = s.get("url", "").strip()
			if (uid and uid in existing_uuids) or (url and url in existing_urls):
				continue
			self._favorites.append(s)
			if uid:
				existing_uuids.add(uid)
			if url:
				existing_urls.add(url)
			added += 1
		if added:
			self._save_favorites()
		return added

	def _parse_import_json(self, path):
		"""Parse a JSON favourites file and return a list of station dicts.

		Missing fields are filled with safe defaults so partial exports from
		older add-on versions still import cleanly.
		"""
		with open(path, "r", encoding="utf-8-sig") as fh:
			data = json.load(fh)
		if not isinstance(data, list):
			raise ValueError("JSON file must contain a top-level array of stations.")
		stations = []
		for item in data:
			if not isinstance(item, dict):
				continue
			url = item.get("url", "").strip()
			if not url:
				continue  # skip entries without a playback URL
			# Start from a copy of the original item so that any extra fields
			# (e.g. homepage, language, bitrate, codec, country, favicon)
			# survive the import instead of being silently discarded.
			station = dict(item)
			# Ensure every required key exists so the rest of the add-on never
			# has to guard against KeyError, without clobbering values that
			# were already present in the imported file.
			station["stationuuid"]  = item.get("stationuuid", "custom-" + str(uuid.uuid4()))
			station["name"]         = item.get("name", url).strip()
			station["url"]          = url
			station["url_resolved"] = item.get("url_resolved", url)
			station["countrycode"]  = item.get("countrycode", "")
			station["tags"]         = item.get("tags", "")
			station["votes"]        = item.get("votes", 0)
			stations.append(station)
		return stations

	def _parse_import_m3u(self, path):
		"""Parse an extended M3U playlist and return a list of station dicts.

		Supports both #EXTINF name lines and bare URL-only playlists.
		"""
		with open(path, "r", encoding="utf-8-sig") as fh:
			lines = [l.rstrip("\n\r") for l in fh]

		stations = []
		pending_name = None
		for line in lines:
			if line.startswith("#EXTINF"):
				# #EXTINF:-1,Station Name
				if "," in line:
					pending_name = line.split(",", 1)[1].strip()
			elif line.startswith("#") or not line.strip():
				continue
			else:
				url  = line.strip()
				name = pending_name or url
				pending_name = None
				stations.append({
					"stationuuid":  "custom-" + str(uuid.uuid4()),
					"name":         name,
					"url":          url,
					"url_resolved": url,
					"countrycode":  "",
					"tags":         "",
					"votes":        0,
				})
		return stations
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