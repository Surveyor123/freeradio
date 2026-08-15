# -*- coding: utf-8 -*-
# FreeRadio - External station sources
#
# Best-effort search providers for TuneIn and iHeartRadio. Neither service
# has a stable, officially supported public API — both endpoints below are
# reverse-engineered from their own apps/websites and are undocumented, so
# they can change or go away without notice. Every function here is
# defensive: on any failure it logs a warning and returns an empty list
# rather than raising, so a broken/blocked source never breaks search.
#
# Every returned station dict is normalised to the same shape used
# throughout the add-on for Radio Browser stations (stationuuid, name, url,
# url_resolved, countrycode, tags, votes, favicon) so it can flow through
# the existing favourites/playback code unchanged. stationuuid is prefixed
# ("tunein-" / "iheart-") so it can never collide with a Radio Browser UUID.
# tags is set to the source name ("TuneIn" / "iHeart") purely so it shows up
# via the existing first-tag display in station_label() — a lightweight way
# to mark provenance in the station list without touching the UI code.

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

USER_AGENT = "FreeRadio-NVDA/1.0"
REQUEST_TIMEOUT = 6

TUNEIN_SEARCH_URL = "https://opml.radiotime.com/Search.ashx"
TUNEIN_TUNE_URL   = "https://opml.radiotime.com/Tune.ashx"

IHEART_SEARCH_URL = "https://api.iheart.com/api/v3/search/all"

# Preferred iHeart stream keys, best quality/most compatible first.
_IHEART_STREAM_KEY_PRIORITY = (
	"secure_shoutcast", "shoutcast", "secure_hls", "hls", "pls",
)


def _get_json(url, timeout=REQUEST_TIMEOUT):
	req = urllib.request.Request(
		url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
	)
	with urllib.request.urlopen(req, timeout=timeout) as resp:
		raw = resp.read().decode("utf-8", "ignore")
	return json.loads(raw)


def search_tunein(query, limit=50, timeout=REQUEST_TIMEOUT):
	"""Search TuneIn stations by name. Returns a list of normalised station
	dicts, or [] on any error. Uses TuneIn's own (undocumented) JSON search
	endpoint — no API key required.

	The station "url" is TuneIn's Tune.ashx tuning URL rather than a raw
	stream URL: fetching it returns a PLS playlist pointing at the real
	stream, which the existing playback code (_resolve_playlist_url) already
	knows how to unwrap, so no special-casing is needed at playback time.
	"""
	query = (query or "").strip()
	if not query:
		return []

	url = "%s?query=%s&render=json" % (TUNEIN_SEARCH_URL, urllib.parse.quote(query))
	try:
		data = _get_json(url, timeout=timeout)
	except (urllib.error.URLError, TimeoutError, OSError) as exc:
		log.warning("FreeRadio: TuneIn search unreachable: %s", exc)
		return []
	except (ValueError, json.JSONDecodeError) as exc:
		log.warning("FreeRadio: TuneIn search returned invalid JSON: %s", exc)
		return []
	except Exception as exc:
		log.warning("FreeRadio: TuneIn search failed: %s", exc)
		return []

	stations = []

	def _walk(items):
		if len(stations) >= limit:
			return
		for item in items or []:
			if not isinstance(item, dict):
				continue
			if item.get("type") == "audio" and item.get("item") == "station":
				guide_id = str(item.get("guide_id", "")).strip()
				name = str(item.get("text", "")).strip()
				# TuneIn's own catalog marks discontinued/unplayable streams
				# this way while still listing them in search results — skip
				# them outright rather than adding dead stations to the list.
				is_dead = name and "not supported" in name.lower()
				if guide_id and name and not is_dead:
					tune_url = "%s?id=%s" % (TUNEIN_TUNE_URL, urllib.parse.quote(guide_id))
					stations.append({
						"stationuuid":  "tunein-" + guide_id,
						"name":         name,
						"url":          tune_url,
						"url_resolved": tune_url,
						"countrycode":  "",
						"tags":         "TuneIn",
						"votes":        0,
						"favicon":      item.get("image", "") or "",
						"homepage":     "",
					})
					if len(stations) >= limit:
						return
			# Some result shapes nest station outlines under "children".
			children = item.get("children")
			if children:
				_walk(children)

	body = data.get("body", data) if isinstance(data, dict) else data
	_walk(body if isinstance(body, list) else [])

	return stations[:limit]


def search_iheart(query, limit=50, timeout=REQUEST_TIMEOUT):
	"""Search iHeartRadio live stations by name. Returns a list of
	normalised station dicts, or [] on any error. Uses iHeart's own
	(undocumented, key-less) catalog search endpoint.

	iHeart's search response shape is not formally documented; parsing here
	is deliberately defensive (missing/renamed fields are skipped rather
	than raising) since the endpoint could change without notice.
	"""
	query = (query or "").strip()
	if not query:
		return []

	params = urllib.parse.urlencode({
		"keywords":   query,
		"bestMatch":  "true",
		"depth":      str(min(max(limit, 1), 50)),
		"startIndex": "0",
	})
	url = "%s?%s" % (IHEART_SEARCH_URL, params)
	try:
		data = _get_json(url, timeout=timeout)
	except (urllib.error.URLError, TimeoutError, OSError) as exc:
		log.warning("FreeRadio: iHeart search unreachable: %s", exc)
		return []
	except (ValueError, json.JSONDecodeError) as exc:
		log.warning("FreeRadio: iHeart search returned invalid JSON: %s", exc)
		return []
	except Exception as exc:
		log.warning("FreeRadio: iHeart search failed: %s", exc)
		return []

	try:
		raw_stations = (data.get("results") or {}).get("stations") or []
	except AttributeError:
		raw_stations = []

	stations = []
	for s in raw_stations:
		if not isinstance(s, dict):
			continue
		station_id = s.get("id")
		name = str(s.get("name", "")).strip()
		if not station_id or not name:
			continue

		streams = s.get("streams") or {}
		stream_url = None
		for key in _IHEART_STREAM_KEY_PRIORITY:
			candidate = streams.get(key)
			if candidate:
				stream_url = candidate
				break
		if not stream_url and streams:
			# Unknown/renamed key — fall back to whatever stream URL exists.
			stream_url = next(iter(streams.values()), None)
		if not stream_url:
			continue

		stations.append({
			"stationuuid":  "iheart-" + str(station_id),
			"name":         name,
			"url":          stream_url,
			"url_resolved": stream_url,
			# iHeart is a US-focused service; not exposed reliably per station.
			"countrycode":  "US",
			"tags":         "iHeart",
			"votes":        0,
			"favicon":      s.get("logo", "") or "",
			"homepage":     "",
		})
		if len(stations) >= limit:
			break

	return stations
