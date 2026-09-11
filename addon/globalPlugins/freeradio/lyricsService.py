# -*- coding: utf-8 -*-
"""Lyrics fetcher for FreeRadio using lrclib.net (free, no API key required).

Endpoints:
  GET https://lrclib.net/api/get?artist_name=…&track_name=…  (exact match)
  GET https://lrclib.net/api/search?q=…					   (fuzzy fallback)

plain_lyrics is preferred; synced_lyrics timestamps are stripped when
plain_lyrics is absent.
"""

import json
import logging
import re
import threading
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

_BASE	= "https://lrclib.net/api"
_TIMEOUT = 12
_UA	  = "FreeRadio-NVDA-addon/1.0"

# Station suffix appended by some ICY streams: " - Show Name on domain.tld"
# Matched and removed from the raw string before any other parsing.
_STATION_SUFFIX_RE = re.compile(
	r' - \S.+ on [^ .]+\.[a-z]{2,}$',
	re.IGNORECASE,
)

# Noise suffixes stripped from the title portion before querying.
_NOISE_PATTERNS = [
	# Parenthesised/bracketed suffixes containing known noise keywords or a bare year.
	re.compile(
		r'[\(\[]\s*(?:[^)\]]*\b(?:'
		r'remaster(?:ed)?|reissue|anniversary|edition|version|'
		r'live|acoustic|demo|instrumental|radio\s*edit|single\s*version|'
		r'extended|explicit|clean|bonus|deluxe|original\s*mix|'
		r'official(?:\s*(?:audio|video|lyric|music\s*video))?|'
		r'hd|hq|4k|audio|video|clip|mv|'
		r'\d{4}'
		r')\b[^)\]]*)\s*[\)\]]',
		re.IGNORECASE,
	),
	# Pipe-separated suffixes: | Greatest Hits | Official Audio
	re.compile(r'\s*\|.*$', re.IGNORECASE),
	# "feat." / "ft." / "featuring" credits
	re.compile(r'\s*[\(\[]?\s*(?:feat\.?|ft\.?|featuring|with)\s+[^\)\]]+[\)\]]?', re.IGNORECASE),
	# Trailing dash + label: - Official Video, - Audio, - HD
	re.compile(
		r'\s*[-/]\s*(?:official|lyrics?|audio|video|hd|hq|4k|clip|mv)\b.*$',
		re.IGNORECASE,
	),
]

_EM_DASH  = "\u2014"   # —
_HYPHEN   = " - "
_BY_RE	= re.compile(r'^(.+?)\s+by\s+(.+)$', re.IGNORECASE)
_YEAR_RE  = re.compile(r'^\d{4}$')


def fetch_lyrics(song_string, callback):
	"""Fetch lyrics for *song_string* asynchronously.

	song_string : str  — as stored in likedSongs.txt
	callback(lyrics: str | None, error: str | None) — called from a background
	thread; use wx.CallAfter when updating UI.
	"""
	def _run():
		artist, title = _parse_song(song_string)
		lyrics, error = _get_lyrics(artist, title, song_string)
		callback(lyrics, error)

	threading.Thread(target=_run, daemon=True).start()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_song(song_string):
	"""Return (artist, title) from a raw likedSongs.txt line.

	Handles three separator styles found in ICY metadata:
	  "Artist - Title"			(hyphen  -> artist first)
	  "Title — Artist[— Album — Year]" (em dash -> title first)
	  "Title by Artist"
	  "Title"					 (no separator -> title only)

	Station suffixes such as "- Classic Vinyl on walmradio.comm" are stripped
	before parsing so they do not pollute the artist or title fields.
	"""
	s = _STATION_SUFFIX_RE.sub("", song_string.strip()).strip()

	# --- "Title by Artist" ---
	m = _BY_RE.match(s)
	if m:
		return m.group(2).strip(), m.group(1).strip()

	# --- Em dash separator: Title — Artist [— Album — Year] ---
	if _EM_DASH in s:
		parts = [p.strip() for p in s.split(_EM_DASH)]
		title  = parts[0]
		# parts[1] is the artist; parts[2+] are album / year — discard them
		artist = parts[1] if len(parts) > 1 else ""
		return artist, title

	# --- Hyphen separator: Artist - Title ---
	if _HYPHEN in s:
		# Split on first occurrence only; title may itself contain " - "
		artist, title = s.split(_HYPHEN, 1)
		# If there are more hyphen parts (e.g. "A - B - C"), the third part is
		# likely an album name on this separator style too — drop it.
		if _HYPHEN in title:
			title = title.split(_HYPHEN, 1)[0]
		return artist.strip(), title.strip()

	# --- No separator ---
	return "", s


def _clean_title(title):
	"""Strip noise suffixes (remaster, live, year, …) from a track title."""
	cleaned = title
	for pattern in _NOISE_PATTERNS:
		cleaned = pattern.sub("", cleaned)
	return cleaned.strip(" -|/")


# ---------------------------------------------------------------------------
# Lookup logic
# ---------------------------------------------------------------------------

def _first_artist(artist):
	"""Return only the first name from a multi-artist string.

	'Miles Davis, Billie Holiday & Dave Brubeck' -> 'Miles Davis'
	'Sarah Brightman & Andrea Bocelli'		   -> 'Sarah Brightman'
	"""
	first = re.split(r'\s*[,&]\s*', artist, maxsplit=1)[0].strip()
	return first if first else artist


def _get_lyrics(artist, title, raw_query):
	"""Try progressively looser queries until lyrics are found.

	Steps:
	  1. Exact /get  - full artist,  cleaned title.
	  2. Exact /get  - full artist,  original title  (only if cleaning changed it).
	  3. Exact /get  - first artist, cleaned title   (only if artist was multi-value).
	  4. Fuzzy /search - "first_artist cleaned_title".
	  5. Fuzzy /search - raw_query as a last resort.
	"""
	clean_title   = _clean_title(title) if title else title
	title_changed = clean_title != title
	first_art	 = _first_artist(artist) if artist else artist
	artist_multi  = first_art != artist

	# --- 1. exact: full artist + cleaned title ---
	if artist and clean_title:
		data, _ = _api_get(artist, clean_title)
		if data:
			lyrics = _extract_lyrics(data)
			if lyrics:
				return lyrics, None

	# --- 2. exact: full artist + original title ---
	if artist and title and title_changed:
		data, _ = _api_get(artist, title)
		if data:
			lyrics = _extract_lyrics(data)
			if lyrics:
				return lyrics, None

	# --- 3. exact: first artist + cleaned title ---
	if artist_multi and first_art and clean_title:
		data, _ = _api_get(first_art, clean_title)
		if data:
			lyrics = _extract_lyrics(data)
			if lyrics:
				return lyrics, None

	# --- 4. fuzzy search: first artist + cleaned title ---
	search_query = ("%s %s" % (first_art, clean_title)).strip() if first_art else clean_title
	if search_query:
		results, _ = _api_search(search_query)
		if results:
			for item in results:
				lyrics = _extract_lyrics(item)
				if lyrics:
					return lyrics, None

	# --- 5. fuzzy search: raw string as last resort ---
	if raw_query != search_query:
		results, _ = _api_search(raw_query)
		if results:
			for item in results:
				lyrics = _extract_lyrics(item)
				if lyrics:
					return lyrics, None

	return None, "Lyrics not found for: %s" % raw_query


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def _api_get(artist, title):
	params = urllib.parse.urlencode({
		"artist_name": artist,
		"track_name":  title,
	})
	return _fetch_json("%s/get?%s" % (_BASE, params))


def _api_search(query):
	params = urllib.parse.urlencode({"q": query})
	data, err = _fetch_json("%s/search?%s" % (_BASE, params))
	if err:
		return None, err
	if isinstance(data, list):
		return data, None
	return None, "Unexpected search response format"


def _fetch_json(url):
	try:
		req = urllib.request.Request(
			url,
			headers={"User-Agent": _UA, "Accept": "application/json"},
		)
		with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
			if resp.status == 404:
				return None, "404 Not Found"
			raw = resp.read().decode("utf-8")
		return json.loads(raw), None
	except urllib.error.HTTPError as e:
		return None, "HTTP %d" % e.code
	except Exception as e:
		log.warning("FreeRadio lyricsService: %s", e)
		return None, str(e)


# ---------------------------------------------------------------------------
# Lyrics extraction
# ---------------------------------------------------------------------------

def _extract_lyrics(data):
	"""Return plain_lyrics, or timestamp-stripped synced_lyrics. None if instrumental."""
	if not isinstance(data, dict):
		return None
	if data.get("instrumental"):
		return None
	plain = (data.get("plainLyrics") or data.get("plain_lyrics") or "").strip()
	if plain:
		return plain
	synced = (data.get("syncedLyrics") or data.get("synced_lyrics") or "").strip()
	if synced:
		return _strip_lrc_timestamps(synced)
	return None


def _strip_lrc_timestamps(lrc_text):
	"""Remove [mm:ss.xx] timestamp tags from LRC lyrics lines."""
	lines = []
	for line in lrc_text.splitlines():
		clean = re.sub(r"(\[\d+:\d+(?:\.\d+)?\])+", "", line).strip()
		if clean:
			lines.append(clean)
	return "\n".join(lines)