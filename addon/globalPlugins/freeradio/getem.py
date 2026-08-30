# -*- coding: utf-8 -*-
# FreeRadio - Audio Books (GETEM e-library) integration
#
# Searches, authenticates against, and resolves playable media from the
# GETEM e-library (https://getem.boun.edu.tr/), the digital library run by
# Bogazici University's Center for the Visually Impaired.
#
# GETEM's search page is a public Drupal "Views" exposed-filter form - the
# catalog itself can be browsed without logging in, but actually streaming
# a work's audio requires being a registered GETEM member. This module
# logs in with the member's own credentials (stored encrypted on disk, see
# save_credentials()/load_credentials()) and keeps an authenticated
# session (cookies) for both searching and resolving the audio file(s) of
# a selected work.
#
# A single free-text term is matched against several of GETEM's own filter
# fields (title, author, narrator, subject, publisher) independently and
# the results are merged/de-duplicated - see search_getem() - since the
# site's own form only supports narrowing by all of those fields at once
# (AND), not a single search across all of them (OR).

import ctypes
import hashlib
import html
import http.cookiejar
import http.server
import json
import logging
import os
import re
import socketserver
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr
# ngettext is injected by initTranslation alongside _; capture it the same way.
ngettext = globals().get("ngettext", lambda s, p, n: s if n == 1 else p)

import globalVars

log = logging.getLogger(__name__)

GETEM_BASE_URL = "https://getem.boun.edu.tr"
GETEM_CATALOG_URL = GETEM_BASE_URL + "/?q=katalog"
GETEM_LOGIN_URL = GETEM_BASE_URL + "/user/login"
USER_AGENT = "FreeRadio-NVDA/1.0"
REQUEST_TIMEOUT = 15
SEARCH_TIMEOUT = 20
RESULTS_PER_QUERY = 100

# Every field the free-text search term is independently matched against;
# results from all of them are merged - see search_getem(). Field names
# are GETEM's own exposed-filter parameter names.
SEARCHED_FIELDS = (
	"title",
	"field_yazar_value",       # author
	"field_seslendiren_value", # narrator
	"body_value",              # subject / description
	"field_yayinevi_value",    # publisher
)

# Keywords (case-insensitive, Turkish) used to recognize which of GETEM's
# own "Eser bicimi" (format) options represent audio sources - human
# narration, computer/TTS narration, audio description, radio drama, etc.
# - as opposed to braille, large print, e-text and other non-audio formats
# also catalogued on the site. Matched against option labels fetched live
# from the site (get_audio_format_options()), so this keeps working even
# if GETEM renames or adds formats.
AUDIO_FORMAT_KEYWORDS = (
	"ses",        # covers "sesli kitap", "ses kaydi", etc.
	"konusan",    # "konusan kitap" (talking book)
	"betimleme",  # audio description
	"tiyatro",    # radio theatre / radio drama
	"daisy",      # DAISY talking-book format
	"mp3",
)

# File extensions treated as playable audio when scanning a work's detail
# page - see resolve_media().
AUDIO_FILE_EXTENSIONS = (".mp3", ".m4a", ".m4b", ".wav", ".ogg", ".oga", ".aac", ".wma")


# --------------------------------------------------------------------- #
# Turkish text normalization (site labels use Turkish characters that
# AUDIO_FORMAT_KEYWORDS above is deliberately written without, so both
# sides are folded through this before comparison).
# --------------------------------------------------------------------- #

_TR_FOLD_MAP = str.maketrans({
	"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
	"ç": "c", "Ç": "c", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u",
})


def _fold(text):
	return (text or "").translate(_TR_FOLD_MAP).casefold()


# --------------------------------------------------------------------- #
# Credential storage - encrypted with the Windows Data Protection API
# (DPAPI), which ties the encrypted bytes to the current Windows user
# without FreeRadio having to manage a key of its own. Stored as its own
# file under the NVDA user config folder, never in config.conf/the addon's
# settings ini (which is plain text).
# --------------------------------------------------------------------- #

class _DataBlob(ctypes.Structure):
	_fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _make_blob(data):
	buf = ctypes.create_string_buffer(data, len(data))
	blob = _DataBlob()
	blob.cbData = len(data)
	blob.pbData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
	return blob, buf  # buf must stay alive as long as blob is used


def _dpapi_protect(data):
	in_blob, _keep_alive = _make_blob(data)
	out_blob = _DataBlob()
	ok = ctypes.windll.crypt32.CryptProtectData(
		ctypes.byref(in_blob), "FreeRadio GETEM credentials", None, None, None, 0, ctypes.byref(out_blob)
	)
	if not ok:
		raise OSError("CryptProtectData failed")
	try:
		return ctypes.string_at(out_blob.pbData, out_blob.cbData)
	finally:
		ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(data):
	in_blob, _keep_alive = _make_blob(data)
	out_blob = _DataBlob()
	ok = ctypes.windll.crypt32.CryptUnprotectData(
		ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
	)
	if not ok:
		raise OSError("CryptUnprotectData failed")
	try:
		return ctypes.string_at(out_blob.pbData, out_blob.cbData)
	finally:
		ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _credentials_path():
	return os.path.join(globalVars.appArgs.configPath, "freeradio_getem_credentials.bin")


def has_credentials():
	return os.path.exists(_credentials_path())


def save_credentials(username, password):
	"""Encrypt and store *username*/*password* for the current Windows
	user. Passing empty strings for both is equivalent to clear_credentials()."""
	if not username and not password:
		return clear_credentials()
	payload = json.dumps({"username": username, "password": password}).encode("utf-8")
	try:
		encrypted = _dpapi_protect(payload)
	except Exception as e:
		log.error("FreeRadio GETEM: could not encrypt credentials: %s", e)
		return False
	path = _credentials_path()
	tmp_path = path + ".tmp"
	try:
		with open(tmp_path, "wb") as f:
			f.write(encrypted)
		os.replace(tmp_path, path)
		return True
	except Exception as e:
		log.error("FreeRadio GETEM: could not save credentials: %s", e)
		return False


def load_credentials():
	"""Returns (username, password), both "" if nothing is stored or it
	could not be decrypted (e.g. NVDA is running under a different Windows
	user than the one that saved it)."""
	path = _credentials_path()
	if not os.path.exists(path):
		return "", ""
	try:
		with open(path, "rb") as f:
			encrypted = f.read()
		payload = _dpapi_unprotect(encrypted)
		data = json.loads(payload.decode("utf-8"))
		return data.get("username", ""), data.get("password", "")
	except Exception as e:
		log.warning("FreeRadio GETEM: could not decrypt stored credentials: %s", e)
		return "", ""


def clear_credentials():
	path = _credentials_path()
	try:
		if os.path.exists(path):
			os.remove(path)
		return True
	except Exception as e:
		log.warning("FreeRadio GETEM: could not remove stored credentials: %s", e)
		return False


# --------------------------------------------------------------------- #
# HTML helpers
#
# The parsing approach in this section (_clean_html_text, _absolute_url,
# _extract_select_options, and the catalog-row splitting/field extraction
# in _parse_catalog_results below) was developed with reference to Mehmet
# Aykurt's GETEM E-Kutuphane NVDA add-on, which parses the same site:
# https://github.com/MehmetAykurt/getem
# --------------------------------------------------------------------- #

def _clean_html_text(text):
	if text is None:
		return ""
	text = str(text)
	text = text.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
	text = re.sub(r"<[^>]+>", "", text)
	text = html.unescape(text)
	text = re.sub(r"\s+", " ", text)
	return text.strip()


def _absolute_url(link):
	link = (link or "").strip()
	if not link:
		return ""
	if link.startswith("http://") or link.startswith("https://"):
		return link
	if link.startswith("/"):
		return GETEM_BASE_URL + link
	return GETEM_BASE_URL + "/" + link


def _extract_select_options(html_text, select_id):
	"""Returns [(label, value), ...] for the <option>s of the <select
	id="select_id"> found in *html_text* (GETEM's own search form uses
	this to publish its current filter choices - see get_audio_format_options()).
	Extraction approach (locate by id, slice to </select>, regex the
	<option> tags) follows Mehmet Aykurt's GETEM add-on - see the module
	header above."""
	options = []
	marker = 'id="' + select_id + '"'
	start = html_text.find(marker)
	if start == -1:
		return options
	end = html_text.find("</select>", start)
	if end == -1:
		return options
	block = html_text[start:end]
	for value, label in re.findall(
		r'<option\s+[^>]*value=["\']([^"\']*)["\'][^>]*>(.*?)</option>',
		block, re.DOTALL | re.IGNORECASE,
	):
		options.append((_clean_html_text(label), html.unescape(value)))
	return options


def _extract_hidden_field(html_text, field_name):
	match = re.search(
		r'name=["\']' + re.escape(field_name) + r'["\']\s+[^>]*value=["\']([^"\']*)["\']',
		html_text, re.IGNORECASE,
	)
	return html.unescape(match.group(1)) if match else None


def _extract_field_text(row_html, field_class):
	"""Pulls the visible text out of one of GETEM's "views-field-..." result
	columns within a single search-result row's HTML."""
	match = re.search(
		r'class="[^"]*' + re.escape(field_class) + r'[^"]*"[^>]*>\s*'
		r'<[^>]+class="field-content"[^>]*>(.*?)</(?:div|span)>',
		row_html, re.DOTALL | re.IGNORECASE,
	)
	if not match:
		return ""
	return _clean_html_text(match.group(1))


def _parse_catalog_results(html_text):
	"""Parses GETEM's catalog search-results HTML (a Drupal Views listing)
	into a list of GetemBook, same general shape as one search-result "row"
	on the site. Row-splitting/field-extraction approach, and the
	"Seslendiren:" prefix cleanup below, follow Mehmet Aykurt's GETEM
	add-on - see the module header above."""
	books = []
	rows = html_text.split('<div class="views-row')
	for row in rows[1:]:
		link_match = re.search(
			r'<div class="views-field views-field-title">\s*'
			r'<span class="field-content"><a href="([^"]*)">(.*?)</a>',
			row, re.DOTALL | re.IGNORECASE,
		)
		if not link_match:
			continue

		detail_url = _absolute_url(link_match.group(1))
		title = _clean_html_text(link_match.group(2)) or _("Unknown")

		narrator = _extract_field_text(row, "views-field-field-seslendiren")
		narrator = re.sub(r"^(?:Seslendiren:\s*)+", "", narrator, flags=re.IGNORECASE).strip()

		books.append(GetemBook(
			title=title,
			detail_url=detail_url,
			author=_extract_field_text(row, "views-field-field-yazar"),
			narrator=narrator,
			format_label=_extract_field_text(row, "views-field-field-formati"),
			description=_extract_field_text(row, "views-field-body"),
			publisher=_extract_field_text(row, "views-field-field-yayinevi"),
		))
	return books


# --------------------------------------------------------------------- #
# Book model
# --------------------------------------------------------------------- #

class GetemBook:
	"""A single work in the GETEM catalog, regardless of how many audio
	parts it's split into on the site - see resolve_media(). There is
	deliberately only ever one GetemBook per work, in search results as
	much as in the library; chapters never get their own row anywhere."""

	def __init__(self, title, detail_url, author="", narrator="", format_label="", description="", publisher=""):
		self.title = title or _("Unknown")
		self.detail_url = detail_url
		self.author = author
		self.narrator = narrator
		self.format_label = format_label
		self.description = description
		self.publisher = publisher
		# Populated lazily by resolve_media(): [{"title": str, "url": str}, ...]
		self.chapters = []
		# Which part was last played - see GetemLibrary.mark_progress().
		# A book is a single source even though it's split into parts (an
		# implementation detail of how GETEM hosts the audio, not
		# something the listener thinks in terms of), so "where did I
		# leave off" is book-level: which part, and radioPlayer.py's own
		# per-part position store (keyed on that part's stream URL - see
		# getem.get_stream_url()) already tracks the exact second within
		# it. Together the two give a full book-level resume.
		self.last_chapter_index = 0
		# Optional dict of {"volume": int, "fx": str, "eq_gains": {...},
		# "speed": float} applied to every part/chapter of this book when
		# it starts playing - see playbackCoreMixin._play_station() and
		# RadioDialog._start_getem_chapter(). None if the user hasn't
		# saved one.
		self.audio_profile = None

	def identity_key(self):
		"""Stable key used for de-duplication and library membership - the
		detail page URL is the closest thing GETEM gives us to a unique id."""
		return self.detail_url

	def to_dict(self):
		"""Convert to the same station-like dict shape podcast episodes use
		(podcast.PodcastEpisode.to_dict()), so it can be handed to the
		existing player/_play_callback machinery unchanged - that's what
		gives audio books the same resume/seek/speed handling podcasts
		already have. The caller fills in which chapter's url/name to use;
		see radioDialog.RadioDialog._start_getem_chapter().

		The "podcast" tag is deliberately included (not just "audiobook"):
		radioPlayer.py's seek/playback-rate/resume-position/finish-detection
		code all gate on `"podcast" in station.get("tags", "")`, and GETEM
		chapters are always played from a local downloaded file (see
		download_chapter()), so they qualify for that handling exactly like
		a podcast episode does. "audiobook" is kept alongside it so callers
		that need to tell a GETEM chapter apart from a real podcast episode
		still can (radioDialog._on_playback_finished() does this).

		Deliberately does NOT include "station_audio" (the saved
		audio_profile, if any) - the caller attaches that itself right
		before playing (see _start_getem_chapter()), same as
		PodcastEpisode.to_dict()/RadioDialog._on_episode_play() do for
		podcast feed profiles.

		Includes author/narrator/publisher/format_label, the book's total
		part count, its description, and a fixed "audiobook_source" label
		so the station-details dialog
		(trackInfoMixin._build_audiobook_details()) can show the same
		Source/Author/Narrator/Publisher/Type/description fields the
		Audio Books tab shows via RadioDialog._format_getem_details() -
		and the book's own detail_url as its "link" - instead of the
		generic radio-station fields that don't apply here.
		"audiobook_source" is the exact same bare "GETEM" string
		RadioDialog._audiobook_source_label_for() already produces (kept
		in sync manually since getem.py has no reason to import
		radioDialog.py), so no new translatable string is introduced for
		it. _start_getem_chapter() is the sole caller and always runs
		after chapters are resolved, so len(self.chapters) is accurate
		at this point."""
		return {
			"name": self.title,
			"url": "",
			"url_resolved": "",
			"stationuuid": "getem-" + str(uuid.uuid5(uuid.NAMESPACE_URL, self.detail_url)),
			"countrycode": "",
			"tags": "podcast,audiobook",
			"getem_detail_url": self.detail_url,
			"author": self.author,
			"narrator": self.narrator,
			"publisher": self.publisher,
			"audiobook_format": self.format_label,
			"audiobook_chapter_count": len(self.chapters),
			"description": self.description,
			"audiobook_source": _("GETEM"),
		}

	def to_library_dict(self):
		return {
			"title": self.title,
			"author": self.author,
			"narrator": self.narrator,
			"format_label": self.format_label,
			"description": self.description,
			"publisher": self.publisher,
			"detail_url": self.detail_url,
			"chapters": self.chapters,
			"last_chapter_index": self.last_chapter_index,
			"audio_profile": self.audio_profile,
		}

	@classmethod
	def from_dict(cls, data):
		book = cls(
			title=data.get("title", ""),
			detail_url=data.get("detail_url", ""),
			author=data.get("author", ""),
			narrator=data.get("narrator", ""),
			format_label=data.get("format_label", ""),
			description=data.get("description", ""),
			publisher=data.get("publisher", ""),
		)
		book.chapters = data.get("chapters", []) or []
		book.last_chapter_index = data.get("last_chapter_index", 0) or 0
		book.audio_profile = data.get("audio_profile") or None
		return book


# --------------------------------------------------------------------- #
# Authenticated session
# --------------------------------------------------------------------- #

class GetemSession:
	"""Holds an (optionally authenticated) connection to GETEM. Searching
	works without logging in - the catalog itself is public - but
	resolve_media() requires a successful login() first, since actually
	streaming a work's audio is member-only on the site."""

	def __init__(self):
		self._cookie_jar = http.cookiejar.CookieJar()
		self._opener = urllib.request.build_opener(
			urllib.request.HTTPCookieProcessor(self._cookie_jar),
			urllib.request.ProxyHandler({}),
		)
		self.logged_in = False

	def fetch(self, url, data=None, timeout=REQUEST_TIMEOUT):
		req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
		with self._opener.open(req, timeout=timeout) as resp:
			raw = resp.read()
			charset = resp.headers.get_content_charset() or "utf-8"
			return raw.decode(charset, errors="replace")

	def login(self, username, password):
		"""Logs in with a Drupal-style login form. Returns (success, error_message)."""
		if not username or not password:
			return False, _("Please enter your GETEM username and password in FreeRadio's settings.")

		try:
			login_page = self.fetch(GETEM_LOGIN_URL)
		except Exception as e:
			return False, str(e)

		fields = {
			"name": username,
			"pass": password,
			"form_id": _extract_hidden_field(login_page, "form_id") or "user_login",
			"op": "Log in",
		}
		form_build_id = _extract_hidden_field(login_page, "form_build_id")
		if form_build_id:
			fields["form_build_id"] = form_build_id

		try:
			response_html = self.fetch(
				GETEM_LOGIN_URL, data=urllib.parse.urlencode(fields).encode("utf-8"),
			)
		except Exception as e:
			return False, str(e)

		# A rejected login re-shows the login form (with an error message);
		# a successful one shows a "Merhaba <username> / Cikis" (logged in
		# as .../Log out) toolbar link instead - that's the reliable tell,
		# confirmed against a real logged-in GETEM page.
		if "?q=user/logout" in response_html or ">Çıkış<" in response_html or ">Cikis<" in response_html:
			self.logged_in = True
			return True, None

		if 'id="edit-name"' in response_html and 'name="form_id" value="user_login"' in response_html:
			return False, _("GETEM login failed. Please check your username and password.")

		# Ambiguous response (e.g. a theme without the expected markup) -
		# assume success rather than blocking the user on a false negative;
		# resolve_media() will surface a clear error if it turns out we
		# weren't actually logged in.
		self.logged_in = True
		return True, None


_session_lock = threading.Lock()
_shared_session = None


def get_session():
	"""Shared GetemSession used by the search UI and by playback, so a
	login made from one doesn't have to be repeated for the other."""
	global _shared_session
	with _session_lock:
		if _shared_session is None:
			_shared_session = GetemSession()
		return _shared_session


def ensure_logged_in(session=None):
	"""Logs *session* (or the shared session) in with the stored
	credentials if it isn't already authenticated. Returns (success,
	error_message). Safe to call from a background thread."""
	session = session or get_session()
	if session.logged_in:
		return True, None
	username, password = load_credentials()
	if not username or not password:
		return False, _("Please enter your GETEM username and password in FreeRadio's settings first.")
	return session.login(username, password)


# --------------------------------------------------------------------- #
# Search
# --------------------------------------------------------------------- #

def get_audio_format_options(session=None):
	"""Fetches GETEM's own "Eser bicimi" (format) filter options from the
	catalog page and returns only the ones that look like audio sources,
	as [(label, value), ...]. Values are opaque site-internal ids, just
	passed back into the search query."""
	session = session or get_session()
	try:
		catalog_html = session.fetch(GETEM_CATALOG_URL, timeout=REQUEST_TIMEOUT)
	except Exception as e:
		log.warning("FreeRadio GETEM: could not fetch catalog page for format options: %s", e)
		return []

	options = _extract_select_options(catalog_html, "edit-field-formati-value")
	return [
		(label, value) for label, value in options
		if value and any(keyword in _fold(label) for keyword in AUDIO_FORMAT_KEYWORDS)
	]


def search_getem(query, session=None, limit=RESULTS_PER_QUERY):
	"""Searches GETEM for audio works matching *query* across title,
	author, narrator, subject and publisher at once, merged and
	de-duplicated, restricted to audio formats. Returns (list_of_GetemBook,
	error_message) - error_message is None on success (an empty list with
	no error just means nothing matched)."""
	query = (query or "").strip()
	if not query:
		return [], _("Please enter a search term.")

	session = session or get_session()

	audio_formats = get_audio_format_options(session)
	if not audio_formats:
		return [], _("Could not reach GETEM's catalog. Please check your internet connection.")
	audio_labels = {_fold(label) for label, _value in audio_formats}

	merged = {}
	last_error = None
	for field in SEARCHED_FIELDS:
		params = [("items_per_page", str(limit)), ("page", "0"), (field, query)]
		for _label, value in audio_formats:
			# Best-effort narrowing on GETEM's side; the format label is
			# re-checked client-side below regardless of whether the site
			# actually honours this multi-value filter parameter.
			params.append(("field_formati_value[]", value))

		url = GETEM_CATALOG_URL + "&" + urllib.parse.urlencode(params)
		try:
			results_html = session.fetch(url, timeout=SEARCH_TIMEOUT)
		except Exception as e:
			log.warning("FreeRadio GETEM: search request failed for field %s: %s", field, e)
			last_error = str(e)
			continue

		for book in _parse_catalog_results(results_html):
			if _fold(book.format_label) not in audio_labels and not any(
				keyword in _fold(book.format_label) for keyword in AUDIO_FORMAT_KEYWORDS
			):
				continue
			merged.setdefault(book.identity_key(), book)

	if not merged and last_error and not merged:
		return [], last_error
	return list(merged.values()), None


# --------------------------------------------------------------------- #
# Media resolution
# --------------------------------------------------------------------- #

# GETEM's own detail-page template lists each part of a work under an
# "Eser Ayrimlari" (work's parts) heading as a pair of links: a plain
# download.php link (title text = part name) immediately followed by a
# "Dinle" (Listen) link. The "Dinle" link's own href is "#" (its click is
# handled entirely in JS) and its data-file attribute points at
# getemPlayerYeni/getemplayer.php - but that endpoint turns out to return
# an HTML page embedding GETEM's own jPlayer widget, not the raw audio
# (confirmed against a real response - it starts with a <script src=".../
# jquery.jplayer.min.js"> tag). The download.php link right next to it is
# the actual raw file endpoint, so that's what's captured here.
_CHAPTER_ROW_RE = re.compile(
	r'<h3>\s*<a\s+href=["\']([^"\']+)["\']>(.*?)</a>\s*</h3>',
	re.IGNORECASE | re.DOTALL,
)


def _parse_chapters_from_detail_html(detail_html):
	"""The actual chapter-extraction logic for a GETEM work's detail page
	HTML - shared between resolve_media() (which fetches the page itself
	for a book already known from search results) and get_book_by_url()
	(which already has the page fetched, since scraping title/author for
	a book found via a pasted URL needs that same page - see the note
	there). Returns [(title_or_empty, url), ...] in page order; the
	caller is responsible for the final "unnamed part" numbering - see
	_label_chapters()."""
	chapters = []
	seen = set()

	# Primary: GETEM's own per-part download.php links - see
	# _CHAPTER_ROW_RE above.
	for href, title in _CHAPTER_ROW_RE.findall(detail_html):
		if not any(ext in href.lower() for ext in AUDIO_FILE_EXTENSIONS):
			continue
		url = _absolute_url(html.unescape(href))
		if url and url not in seen:
			seen.add(url)
			chapters.append((_clean_html_text(title), url))

	# Fallback: a plain <audio>/<source> element, or a link whose URL
	# (path OR query string - GETEM's own download.php links only carry
	# the extension in their query string, e.g. "download.php?...&file=
	# 001-Name.mp3") ends in a known audio extension. Covers content types
	# whose page doesn't use the "Dinle" player links above.
	if not chapters:
		for src in re.findall(r'<(?:audio|source)\s+[^>]*src=["\']([^"\']+)["\']', detail_html, re.IGNORECASE):
			url = _absolute_url(html.unescape(src))
			if url and url not in seen:
				seen.add(url)
				chapters.append(("", url))

		for href, link_text in re.findall(
			r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', detail_html, re.IGNORECASE | re.DOTALL
		):
			if not any(ext in href.lower() for ext in AUDIO_FILE_EXTENSIONS):
				continue
			url = _absolute_url(html.unescape(href))
			if url and url not in seen:
				seen.add(url)
				chapters.append((_clean_html_text(link_text), url))

	return chapters


def _label_chapters(book, chapters):
	"""Turns [(title_or_empty, url), ...] (as returned by
	_parse_chapters_from_detail_html()) into the final
	[{"title": ..., "url": ...}, ...] shape stored on book.chapters,
	numbering unnamed parts against *book*.title - shared by
	resolve_media()/get_book_by_url()."""
	total = len(chapters)
	return [
		{
			"title": title or (book.title if total == 1 else _("{0} - Part {1}").format(book.title, i + 1)),
			"url": url,
		}
		for i, (title, url) in enumerate(chapters)
	]


def resolve_media(book, session=None):
	"""Fetches *book*'s GETEM detail page (logging in first if needed) and
	fills in its .chapters with every playable audio part found there, in
	page order. Multi-part works simply end up with several chapters on
	the same GetemBook - there is deliberately no separate UI concept of a
	chapter list beyond this. Returns (book, error_message)."""
	session = session or get_session()
	ok, error = ensure_logged_in(session)
	if not ok:
		return book, error

	try:
		detail_html = session.fetch(book.detail_url, timeout=REQUEST_TIMEOUT)
	except Exception as e:
		return book, str(e)

	chapters = _parse_chapters_from_detail_html(detail_html)
	if not chapters:
		return book, _(
			"No playable audio file was found on this work's GETEM page. "
			"It may require manual download from the site."
		)

	book.chapters = _label_chapters(book, chapters)
	return book, None


# --------------------------------------------------------------------- #
# Direct book-URL lookup (paste a GETEM work link instead of searching)
# --------------------------------------------------------------------- #

GETEM_NODE_URL_RE = re.compile(
	r"^https?://(?:www\.)?getem\.boun\.edu\.tr/(?:\?q=)?node/(\d+)", re.IGNORECASE)


def looks_like_book_url(text):
	"""Whether *text* (typically whatever was typed into the Audio Books
	search field) looks like a GETEM work URL rather than a keyword
	search - see get_book_by_url()/RadioDialog._on_getem_search()."""
	return bool(GETEM_NODE_URL_RE.match((text or "").strip()))


def _normalize_detail_url(url):
	match = GETEM_NODE_URL_RE.match((url or "").strip())
	if not match:
		return None
	# Always the canonical "?q=node/<id>" form regardless of how the link
	# was written (e.g. a path-alias-style "/node/<id>" URL also matches
	# GETEM_NODE_URL_RE above) - detail_url doubles as the library's
	# identity key (see GetemBook.identity_key()), so this keeps the same
	# work from ending up under two different keys depending on which
	# form of its URL happened to get pasted.
	return GETEM_BASE_URL + "/?q=node/" + match.group(1)


def _extract_node_title(html_text):
	"""Best-effort extraction of a GETEM node/detail page's own title -
	tried against the page's first <h1> heading (Drupal's default node
	template wraps the title in <h1 id="page-title" class="title">...</h1>
	or similar), falling back to the <title> tag (keeping only the part
	before a common " | SiteName" suffix, if the theme adds one) since
	every page has one even if the heading markup differs. See the note
	in get_book_by_url() about this not being verified against a live
	GETEM detail page."""
	h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, re.IGNORECASE | re.DOTALL)
	if h1_match:
		title = _clean_html_text(h1_match.group(1))
		if title:
			return title
	title_match = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
	if title_match:
		title = re.split(r"\s*\|\s*", _clean_html_text(title_match.group(1)))[0].strip()
		if title:
			return title
	return ""


def _extract_node_field_text(html_text, field_class):
	"""Pulls the visible text out of one of GETEM's node/detail page
	"field-name-..." field wrappers (Drupal's default field-display
	markup) - the detail-page equivalent of _extract_field_text() above,
	which is written for catalog *listing* rows instead (different
	markup - "views-field-..." wrappers - so it can't be reused here
	as-is). Strips the field's own label (e.g. "Yazar:"), if the theme
	renders one inside the same wrapper. See the note in
	get_book_by_url() about this not being verified against a live GETEM
	detail page - if a field comes back empty here, the book is still
	fully usable (its chapters resolve through the separately-verified
	_parse_chapters_from_detail_html()); only that one detail is missing
	from what would otherwise come from a catalog search result."""
	match = re.search(
		r'class="[^"]*' + re.escape(field_class) + r'[^"]*"[^>]*>(.*?)</div>\s*</div>',
		html_text, re.DOTALL | re.IGNORECASE,
	)
	if not match:
		return ""
	text = re.sub(
		r'<div[^>]*class="[^"]*field-label[^"]*"[^>]*>.*?</div>',
		"", match.group(1), flags=re.DOTALL | re.IGNORECASE,
	)
	return _clean_html_text(text)


def get_book_by_url(url, session=None):
	"""Resolves a book directly from a GETEM work URL - e.g. one pasted
	from a browser's address bar, or copied via this tab's own "Copy the
	URL" context menu action - instead of having to search for it by
	title/author/etc. again. Requires being logged in, same as
	resolve_media() (see the note above _CHAPTER_ROW_RE on why even
	viewing a work's detail page needs it); title/author/narrator/
	publisher/description are scraped from that very same page fetch, so
	this needs no extra request beyond what resolve_media() would already
	make to play this book. Its chapters are extracted with the exact
	same, already-verified code resolve_media() uses
	(_parse_chapters_from_detail_html()/_label_chapters()) - only the
	metadata scraping below (_extract_node_title()/
	_extract_node_field_text()) is new, and unverified against a live
	GETEM detail page (see the note on those two). Returns
	(book_or_None, error_message)."""
	detail_url = _normalize_detail_url(url)
	if not detail_url:
		return None, _("This doesn't look like a GETEM work link.")

	session = session or get_session()
	ok, error = ensure_logged_in(session)
	if not ok:
		return None, error

	try:
		detail_html = session.fetch(detail_url, timeout=REQUEST_TIMEOUT)
	except Exception as e:
		return None, str(e)

	narrator = _extract_node_field_text(detail_html, "field-name-field-seslendiren")
	narrator = re.sub(r"^(?:Seslendiren:\s*)+", "", narrator, flags=re.IGNORECASE).strip()

	book = GetemBook(
		title=_extract_node_title(detail_html) or _("Unknown"),
		detail_url=detail_url,
		author=_extract_node_field_text(detail_html, "field-name-field-yazar"),
		narrator=narrator,
		format_label=_extract_node_field_text(detail_html, "field-name-field-formati"),
		description=_extract_node_field_text(detail_html, "field-name-body"),
		publisher=_extract_node_field_text(detail_html, "field-name-field-yayinevi"),
	)

	chapters = _parse_chapters_from_detail_html(detail_html)
	if not chapters:
		return book, _(
			"No playable audio file was found on this work's GETEM page. "
			"It may require manual download from the site."
		)
	book.chapters = _label_chapters(book, chapters)
	return book, None




def _chapter_cache_dir():
	path = os.path.join(globalVars.appArgs.configPath, "freeradio_getem_cache")
	os.makedirs(path, exist_ok=True)
	return path


def _looks_like_audio(path):
	"""Cheap sanity check on a downloaded file: real mp3s either start
	with an ID3 tag or an MPEG frame-sync byte; anything that looks like
	HTML/text (an error or login page GETEM returned instead of audio)
	does not. Used to avoid caching (and silently "playing") a bogus file."""
	try:
		with open(path, "rb") as f:
			head = f.read(512)
	except OSError:
		return False
	if not head:
		return False
	if head.lstrip()[:1] in (b"<", b"{"):
		return False
	if head[:3] == b"ID3" or head[:2] == b"\xff\xfb" or head[:2] == b"\xff\xf3":
		return True
	# Not a recognized mp3 header, but also not obviously HTML/JSON -
	# accept it; GETEM also serves other audio containers (m4a/wav) whose
	# signatures aren't checked for here.
	return True


def get_local_path_for_chapter(chapter_url):
	"""Deterministic local cache filename for a chapter's streaming URL,
	so re-playing an already-downloaded part doesn't re-download it."""
	digest = hashlib.sha1(chapter_url.encode("utf-8")).hexdigest()[:16]
	return os.path.join(_chapter_cache_dir(), digest + ".mp3")


def _fetch_audio_file(chapter_url, dest_path, referer=None, session=None, progress_callback=None):
	"""Shared download core for download_chapter()/download_chapter_to():
	fetches *chapter_url* through the authenticated *session* and writes it
	to *dest_path* (atomically, via a ".part" temp file next to it).

	*referer*, if given, is sent as the Referer header (the "Dinle" link
	is triggered by GETEM's own JavaScript rather than being a plain
	link, so the endpoint may expect to see the book's own page as the
	referring page rather than no Referer at all).

	*progress_callback*, if given, is called as (bytes_written, total_bytes)
	while downloading (total_bytes may be 0 if the server didn't send a
	Content-Length header).

	Raises RuntimeError with a message quoting what the server actually
	sent back if it wasn't recognizable audio (e.g. an access-denied or
	session-expired page), rather than silently saving a bogus file."""
	session = session or get_session()
	ok, error = ensure_logged_in(session)
	if not ok:
		raise RuntimeError(error)

	headers = {
		"User-Agent": USER_AGENT,
		"Accept": "audio/mpeg, audio/*;q=0.9, */*;q=0.5",
	}
	if referer:
		headers["Referer"] = referer

	req = urllib.request.Request(chapter_url, headers=headers)
	tmp_path = dest_path + ".part"
	with session._opener.open(req, timeout=60) as resp:
		content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
		try:
			total = int(resp.headers.get("Content-Length") or 0)
		except (TypeError, ValueError):
			total = 0
		written = 0
		with open(tmp_path, "wb") as f:
			while True:
				chunk = resp.read(65536)
				if not chunk:
					break
				f.write(chunk)
				written += len(chunk)
				if progress_callback:
					progress_callback(written, total)

	if written == 0:
		try:
			os.remove(tmp_path)
		except OSError:
			pass
		raise RuntimeError(_("The downloaded file was empty. Please check your GETEM login."))

	if content_type.startswith("text/") or content_type == "application/json" or not _looks_like_audio(tmp_path):
		# GETEM sent something other than audio back - most likely an
		# access-denied/login-expired/error page. Surface a snippet of it
		# (rather than just failing silently) so the actual reason is
		# visible instead of a file that "plays" with no sound.
		try:
			with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
				snippet = _clean_html_text(f.read(500))
		except OSError:
			snippet = ""
		try:
			os.remove(tmp_path)
		except OSError:
			pass
		if snippet:
			raise RuntimeError(_("GETEM did not return audio for this part: %s") % snippet[:200])
		raise RuntimeError(_("GETEM did not return a playable audio file for this part."))

	os.replace(tmp_path, dest_path)
	return dest_path


# --------------------------------------------------------------------- #
# Local streaming proxy
# --------------------------------------------------------------------- #
#
# GETEM's chapter audio URLs are only reachable with our Python session's
# login cookie - the NVDA audio backend (BASS, which runs in its own
# subprocess - see bass_host.py) has no way to present that cookie itself
# when it opens a URL on its own, so handing it the raw remote URL would
# just get an access-denied page back instead of audio, and downloading
# the whole chapter to a local file before playback can even start is
# slow and a poor match for how podcasts already stream instantly.
#
# Instead, a small local HTTP relay runs in this process: BASS is pointed
# at http://127.0.0.1:<port>/<token> (an ordinary http:// URL, so it goes
# through the exact same streaming/seek code path bass_host.py already
# uses for podcasts), and each request is served by fetching the real
# GETEM URL through the authenticated session and forwarding the
# response straight through, chunk by chunk, as it arrives - so playback
# starts as soon as the first bytes come back rather than waiting for
# the whole chapter to download.

_proxy_server = None
_proxy_lock = threading.Lock()
_proxy_chapters = {}  # token -> (chapter_url, referer)
_PROXY_PREFERRED_PORT = 47823  # arbitrary, in the dynamic/private range


class _GetemProxyHandler(http.server.BaseHTTPRequestHandler):
	protocol_version = "HTTP/1.1"

	def log_message(self, format, *args):
		pass  # Silence BaseHTTPRequestHandler's default stderr access log.

	def do_GET(self):
		token = self.path.lstrip("/").split("?")[0]
		entry = _proxy_chapters.get(token)
		if not entry:
			self.send_error(404, "Unknown chapter")
			return
		chapter_url, referer = entry

		try:
			session = get_session()
			ok, error = ensure_logged_in(session)
			if not ok:
				self.send_error(502, "GETEM login failed")
				return

			headers = {
				"User-Agent": USER_AGENT,
				"Accept": "audio/mpeg, audio/*;q=0.9, */*;q=0.5",
			}
			if referer:
				headers["Referer"] = referer
			# Forward BASS's own Range request as-is, so seeking within
			# the stream works if GETEM's server honours it (exactly how
			# seeking already works for a normal remote podcast episode).
			range_header = self.headers.get("Range")
			if range_header:
				headers["Range"] = range_header

			req = urllib.request.Request(chapter_url, headers=headers)
			with session._opener.open(req, timeout=60) as resp:
				status = getattr(resp, "status", None) or resp.getcode() or 200
				content_type = resp.headers.get("Content-Type") or "audio/mpeg"
				content_length = resp.headers.get("Content-Length")
				content_range = resp.headers.get("Content-Range")

				self.send_response(status)
				self.send_header("Content-Type", content_type)
				if content_length is not None:
					self.send_header("Content-Length", content_length)
				if content_range is not None:
					self.send_header("Content-Range", content_range)
				self.send_header("Accept-Ranges", "bytes")
				# This relay doesn't implement chunked transfer-encoding on
				# its own response, so if the upstream didn't give us a
				# Content-Length either, there'd be no way for the client
				# to know where the body ends on a kept-alive connection -
				# always close after one response to keep that unambiguous.
				self.send_header("Connection", "close")
				self.close_connection = True
				self.end_headers()

				while True:
					chunk = resp.read(65536)
					if not chunk:
						break
					try:
						self.wfile.write(chunk)
					except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
						# BASS closed the connection early (stopped/seeked
						# away) - not an error, just stop forwarding.
						return
		except Exception as e:
			try:
				self.send_error(502, ("GETEM fetch failed: %s" % str(e))[:150])
			except Exception:
				pass


class _ThreadingProxyServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
	daemon_threads = True
	allow_reuse_address = True


def _ensure_proxy_server():
	"""Starts the local streaming proxy (once per NVDA session, lazily on
	first use) and returns the port it's listening on.

	Binds a fixed, preferred port rather than letting the OS assign a
	random one: get_stream_url() builds a deterministic URL per chapter
	(same chapter -> same URL every time), and that URL doubles as the
	resume-position lookup key in radioPlayer.py's podcast position
	store (podcast_positions.json) exactly like a real podcast episode's
	URL does - a random per-launch port would silently break "kaldığı
	yerden devam etme" across NVDA restarts, since the saved position
	would be keyed to a URL that no longer matches anything. Falls back
	to an OS-assigned port only if the preferred one is unavailable
	(e.g. something else is using it) - resume still works within that
	single NVDA session, just not across a restart."""
	global _proxy_server
	with _proxy_lock:
		if _proxy_server is None:
			try:
				_proxy_server = _ThreadingProxyServer(("127.0.0.1", _PROXY_PREFERRED_PORT), _GetemProxyHandler)
			except OSError:
				_proxy_server = _ThreadingProxyServer(("127.0.0.1", 0), _GetemProxyHandler)
			t = threading.Thread(
				target=_proxy_server.serve_forever,
				daemon=True, name="FreeRadio-getem-proxy",
			)
			t.start()
		return _proxy_server.server_address[1]


def get_stream_url(chapter_url, referer=None):
	"""Registers *chapter_url* with the local streaming proxy (starting
	it first if needed) and returns a http://127.0.0.1:<port>/<token>
	URL that can be handed straight to the player - see the module
	docstring above. Playback can start as soon as the proxy relays the
	first bytes back; there's no upfront download to wait for.

	The token is a deterministic hash of *chapter_url*, not a fresh
	random one per call: the same chapter always maps to the same proxy
	URL, which is what lets resume-position tracking (keyed on this URL,
	same as for a real podcast episode) work across replays - see
	_ensure_proxy_server()."""
	port = _ensure_proxy_server()
	token = hashlib.sha1(chapter_url.encode("utf-8")).hexdigest()
	_proxy_chapters[token] = (chapter_url, referer)
	return "http://127.0.0.1:%d/%s" % (port, token)


def download_chapter(chapter_url, referer=None, session=None, progress_callback=None):
	"""Downloads *chapter_url* to a local cache file and returns its path.
	NOT used for normal playback any more - see get_stream_url(), which
	streams a chapter through the local proxy so playback can start
	immediately instead of waiting for a full download. This is kept for
	anything that genuinely wants a complete local copy up front (offline
	playback fallback, etc); the explicit "Download Part" menu action
	uses download_chapter_to() instead, which saves to a permanent,
	user-visible path rather than this hidden cache location.

	See _fetch_audio_file() for *referer*/*progress_callback* and the
	errors this can raise. Skips re-downloading if a valid cached copy
	already exists at get_local_path_for_chapter()."""
	local_path = get_local_path_for_chapter(chapter_url)
	if os.path.exists(local_path) and os.path.getsize(local_path) > 0 and _looks_like_audio(local_path):
		return local_path
	return _fetch_audio_file(chapter_url, local_path, referer=referer, session=session, progress_callback=progress_callback)


def _chapter_file_extension(chapter_url):
	"""Filename extension to use for a saved copy of *chapter_url*.

	GETEM's chapter "url" is actually a PHP endpoint that streams back the
	real audio bytes (e.g. .../oku.php?...) - the URL's own path extension
	is therefore ".php" (or sometimes missing/query-only), not the audio
	format it actually serves. Trusting os.path.splitext() on that path
	blindly is what previously produced ".php"-named downloads that were
	genuinely mp3 data underneath - see download_target()/
	download_book_chapter_target(). Only trust the URL's extension if it's
	one of the audio extensions we recognize (AUDIO_FILE_EXTENSIONS);
	otherwise fall back to ".mp3", which is what GETEM actually sends in
	practice."""
	url_path = urllib.parse.urlparse(chapter_url).path
	ext = os.path.splitext(url_path)[1]
	if ext and not ext.startswith("."):
		ext = "." + ext
	if ext.lower() not in AUDIO_FILE_EXTENSIONS:
		ext = ".mp3"
	return ext


def download_target(book, chapter):
	"""Compute the destination path and filename a GETEM chapter would be
	saved to as an explicit, user-visible download - mirroring
	podcast.episode_download_target(). Distinct from the hashed cache path
	download_chapter() uses for on-the-fly playback: this is a copy meant
	for the user to keep, named after the book (and chapter, for
	multi-part works) rather than a hash. Returns (out_path, filename)."""
	from . import recorder
	out_dir = recorder._recordings_dir()
	safe_book = "".join(c for c in book.title if c.isalnum() or c in " .-_")[:60].strip()
	chapter_title = chapter.get("title") or ""
	safe_chapter = "".join(c for c in chapter_title if c.isalnum() or c in " .-_")[:60].strip()
	ext = _chapter_file_extension(chapter["url"])
	if safe_chapter and safe_chapter != safe_book:
		filename = f"{safe_book} - {safe_chapter}{ext}"
	else:
		filename = f"{safe_book}{ext}"
	out_path = os.path.join(out_dir, filename)
	return out_path, filename


def download_chapter_to(chapter_url, out_path, referer=None, session=None, progress_callback=None):
	"""Downloads *chapter_url* to the explicit destination *out_path* (see
	download_target()), for the user's own keeping - as opposed to
	download_chapter()'s hidden playback cache. Returns *out_path*.
	Raises RuntimeError the same way download_chapter()/_fetch_audio_file()
	do; raises FileExistsError if *out_path* already exists, so callers can
	decide whether to warn instead of silently overwriting."""
	if os.path.exists(out_path):
		raise FileExistsError(out_path)
	return _fetch_audio_file(chapter_url, out_path, referer=referer, session=session, progress_callback=progress_callback)


def safe_book_title(book):
	"""Filesystem-safe version of a book's title - shared by
	book_download_dir() (the whole-book download folder name) and
	download_target() (the single-part download filename) so both use
	the same sanitizing rule."""
	return "".join(c for c in book.title if c.isalnum() or c in " .-_")[:60].strip()


def book_download_dir(book):
	"""Destination folder a GETEM book's parts are saved to when the whole
	book is downloaded at once ("Download Book" / Ctrl+Win+V) - a
	subfolder of the recordings directory named after the book."""
	from . import recorder
	out_dir = recorder._recordings_dir()
	return os.path.join(out_dir, safe_book_title(book) or _("Untitled"))


def download_book_chapter_target(book, chapter, chapter_index):
	"""Destination path for one part of *book* when downloading the whole
	book into book_download_dir(book). Filenames are numbered by their
	position in book.chapters (rather than named after each part's own
	title, as download_target() does for a single-part download) so the
	parts always sort back into listening order in the folder, regardless
	of what GETEM itself calls them."""
	out_dir = book_download_dir(book)
	chapter_title = (chapter.get("title") or "").strip()
	safe_chapter = "".join(c for c in chapter_title if c.isalnum() or c in " .-_")[:60].strip()
	ext = _chapter_file_extension(chapter["url"])
	width = len(str(len(book.chapters)))
	number = str(chapter_index + 1).zfill(width)
	if safe_chapter and safe_chapter != safe_book_title(book):
		filename = f"{number} - {safe_chapter}{ext}"
	else:
		filename = f"{number}{ext}"
	return os.path.join(out_dir, filename)


# --------------------------------------------------------------------- #
# Library persistence
# --------------------------------------------------------------------- #

class GetemLibrary:
	"""The user's saved GETEM audio books - the ones added from search
	results via the "Add to Library" context menu. Persisted the same way
	podcast.PodcastManager persists feed subscriptions."""

	def __init__(self):
		self._books = []
		self._load()

	def _get_path(self):
		return os.path.join(globalVars.appArgs.configPath, "freeradio_getem_library.json")

	def _load(self):
		path = self._get_path()
		if not os.path.exists(path):
			return
		try:
			with open(path, "r", encoding="utf-8") as f:
				data = json.load(f)
			self._books = [GetemBook.from_dict(item) for item in data if isinstance(item, dict)]
		except Exception as e:
			log.warning("FreeRadio GETEM: failed to load library: %s", e)

	def save(self):
		"""Persists the current library to disk. Also used after
		resolve_media() fills in a library book's chapters in place, so
		they don't need re-resolving on the next play."""
		try:
			path = self._get_path()
			tmp_path = path + ".tmp"
			with open(tmp_path, "w", encoding="utf-8") as f:
				json.dump([b.to_library_dict() for b in self._books], f, ensure_ascii=False, indent=4)
			os.replace(tmp_path, path)
		except Exception as e:
			log.warning("FreeRadio GETEM: failed to save library: %s", e)

	def get_books(self):
		return list(self._books)

	def get_book_by_key(self, key):
		for book in self._books:
			if book.identity_key() == key:
				return book
		return None

	def is_in_library(self, book):
		return self.get_book_by_key(book.identity_key()) is not None

	def add_book(self, book):
		if self.is_in_library(book):
			return False
		self._books.append(book)
		self.save()
		return True

	def remove_book(self, book):
		existing = self.get_book_by_key(book.identity_key())
		if not existing:
			return False
		self._books.remove(existing)
		self.save()
		return True

	def mark_progress(self, book, chapter_index):
		"""Records which part of *book* was most recently played and
		persists it, so _play_getem_book() can resume there next time -
		even across an NVDA restart. No-ops if *book* isn't actually in
		the library (e.g. played once from search results without being
		added) - there'd be nowhere to persist the progress to."""
		existing = self.get_book_by_key(book.identity_key())
		if not existing:
			return
		existing.last_chapter_index = chapter_index
		self.save()