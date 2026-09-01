# -*- coding: utf-8 -*-
# FreeRadio - Audio Books (LibriVox) integration
#
# Searches and resolves playable media from LibriVox
# (https://librivox.org/), the volunteer-read public-domain audiobook
# project. Every LibriVox recording is permanently hosted on archive.org
# (https://wiki.librivox.org - "The Librivox audio files are hosted at
# Archive.org permanently"), and archive.org exposes its own fast,
# well-documented, unauthenticated JSON APIs for both search
# (advancedsearch.php) and per-item file listings (metadata/<identifier>).
# BOTH search AND chapter resolution go through archive.org directly
# rather than through librivox.org's own /api/feed endpoint - see
# search_librivox() and _resolve_via_archive_org() below for why.
#
# Unlike GETEM (see getem.py), LibriVox requires NO account/login at all -
# its whole catalog, including the audio files themselves, is public domain
# and openly reachable. This makes this module considerably simpler than
# getem.py: there is no credential storage, no authenticated session, and
# no local streaming proxy - a chapter's audio URL is an ordinary public
# https:// link (hosted on archive.org) that the BASS backend can open
# directly, exactly like a normal podcast episode's URL.
#
# LibrivoxBook is deliberately attribute- and method-compatible with
# getem.GetemBook (same field names, identity_key()/to_dict()/
# to_library_dict()/from_dict() shape), and LibrivoxLibrary is compatible
# with getem.GetemLibrary, so radioDialog.py's Audio Books tab can drive
# either source through the same generic UI code - see
# RadioDialog._current_audiobook_module()/_current_audiobook_library().
#
# WHY ARCHIVE.ORG INSTEAD OF LIBRIVOX.ORG'S OWN API:
# librivox.org's own /api/feed/audiobooks/<field>/<term> endpoint was the
# original search path used here, but was repeatedly observed timing out
# or being rate-limited on a real, live install - for search terms that
# librivox.org's own human-facing search page (https://librivox.org/search/)
# returns results for instantly. This points to librivox.org's API
# infrastructure specifically being slow/unreliable, not the query itself
# being wrong. Since archive.org already hosts every LibriVox file (and is
# what librivox.org's own RSS feeds ultimately point to anyway), searching
# and resolving chapters directly against archive.org's own API removes
# the flaky dependency on librivox.org entirely instead of just retrying
# around it. archive.org's metadata API for a LibriVox item consistently
# exposes a "64Kbps MP3" file group, one file per chapter in track order -
# see _resolve_via_archive_org() below.
#
# Library entries saved by older versions of this module (before this
# change) only have a LibriVox url_rss and no archive_id - resolve_media()
# still supports those via _resolve_via_librivox_rss() as a fallback so
# existing saved books keep working, but new searches no longer go through
# librivox.org at all.
#
# NOTE: this module was written and updated without being able to make a
# live request to either librivox.org or archive.org from the environment
# it was authored in - if archive.org searches or chapter listings still
# fail, check the *actual* HTTP status and response body in FreeRadio's
# log (see _fetch()'s error handling) rather than assuming this note is
# still the full picture.


import html
import json
import logging
import os
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr
ngettext = globals().get("ngettext", lambda s, p, n: s if n == 1 else p)

import globalVars

log = logging.getLogger(__name__)

LIBRIVOX_API_URL = "https://librivox.org/api/feed/audiobooks/"
ARCHIVE_ADVANCED_SEARCH_URL = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA_URL = "https://archive.org/metadata/"
ARCHIVE_DOWNLOAD_BASE = "https://archive.org/download/"
ARCHIVE_DETAILS_BASE = "https://archive.org/details/"
# Matches an archive.org book "details" page URL pasted into the Audio
# Books search field - see looks_like_book_url()/get_book_by_url().
ARCHIVE_DETAILS_URL_RE = re.compile(
	r"^https?://(?:www\.)?archive\.org/details/([A-Za-z0-9._-]+)", re.IGNORECASE)
USER_AGENT = "FreeRadio-NVDA/1.0"
REQUEST_TIMEOUT = 15
SEARCH_TIMEOUT = 20
RESULTS_PER_QUERY = 100


# --------------------------------------------------------------------- #
# Search
# --------------------------------------------------------------------- #

def _fetch(url, timeout=REQUEST_TIMEOUT):
	headers = {
		"User-Agent": USER_AGENT,
		"Accept": "application/json, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5",
	}
	req = urllib.request.Request(url, headers=headers)
	try:
		with urllib.request.urlopen(req, timeout=timeout) as resp:
			raw = resp.read()
			charset = resp.headers.get_content_charset() or "utf-8"
			return raw.decode(charset, errors="replace")
	except urllib.error.HTTPError as e:
		# Surface the server's own response body, not just the bare status
		# code - a WAF/CDN block page or the API's own error response is
		# usually far more specific about what it actually objected to,
		# and this couldn't be reached for a scripted request from the
		# environment this module was authored/fixed in, so this detail is
		# needed in FreeRadio's log to diagnose it for real next time
		# rather than guessing again.
		try:
			body = e.read().decode("utf-8", errors="replace")[:300].strip()
		except Exception:
			body = ""
		detail = (" | response body: %s" % body) if body else " | (no response body)"
		raise RuntimeError("HTTP %s for %s%s" % (e.code, url, detail)) from e


def _first_str(value):
	"""archive.org's advancedsearch.php returns a field as either a bare
	string or a list of strings (e.g. multiple creators) depending on the
	item - this normalizes either shape to a single string, taking the
	first entry for a list."""
	if isinstance(value, list):
		return str(value[0]) if value else ""
	return str(value) if value is not None else ""


def _strip_html(text):
	# archive.org item descriptions are frequently plain HTML (<p>, <br>,
	# etc.) rather than plain text.
	return re.sub(r"<[^>]+>", "", text or "").strip()


def _parse_archive_doc(doc):
	"""Turns one 'doc' entry from archive.org's advancedsearch.php search
	response into a LibrivoxBook, with book.archive_id set so
	resolve_media() knows to fetch its chapters from archive.org's
	metadata API (see _resolve_via_archive_org())."""
	identifier = _first_str(doc.get("identifier")).strip()
	title = _first_str(doc.get("title")).strip() or _("Unknown")

	creators = doc.get("creator")
	if isinstance(creators, list):
		author = ", ".join(c.strip() for c in (str(x) for x in creators) if c.strip())
	else:
		author = _first_str(creators).strip()

	language = _first_str(doc.get("language")).strip()
	description = _strip_html(_first_str(doc.get("description")))
	runtime = _first_str(doc.get("runtime")).strip()

	detail_url = ARCHIVE_DETAILS_BASE + identifier
	book = LibrivoxBook(
		title=title, detail_url=detail_url, author=author,
		description=description, language=language,
	)
	book.archive_id = identifier
	if runtime and language:
		book.format_label = "%s, %s" % (language, runtime)
	elif runtime:
		book.format_label = runtime
	elif language:
		book.format_label = language
	return book


def search_librivox(query, limit=RESULTS_PER_QUERY):
	"""Searches for LibriVox audiobooks matching *query*, directly against
	archive.org's 'librivoxaudio' collection rather than librivox.org's
	own API - see the module docstring for why. Matches against title OR
	creator (author) in a single request, unlike the old librivox.org-API
	approach which needed a separate author fallback request. Returns
	(list_of_LibrivoxBook, error_message)."""
	query = (query or "").strip()
	if not query:
		return [], _("Please enter a search term.")

	# A quoted phrase match against title/creator approximates what
	# someone typing these words into librivox.org's own search box would
	# expect - unlike the old API's anchored-prefix-only title/^query
	# matching, this also matches the term appearing anywhere in the
	# title or author name.
	phrase = query.replace('"', "")
	search_q = 'collection:(librivoxaudio) AND (title:("%s") OR creator:("%s"))' % (phrase, phrase)
	params = [
		("q", search_q),
		("fl[]", "identifier"),
		("fl[]", "title"),
		("fl[]", "creator"),
		("fl[]", "language"),
		("fl[]", "description"),
		("fl[]", "runtime"),
		("rows", str(limit)),
		("page", "1"),
		("output", "json"),
	]
	url = "%s?%s" % (ARCHIVE_ADVANCED_SEARCH_URL, urllib.parse.urlencode(params))
	try:
		response_text = _fetch(url, timeout=SEARCH_TIMEOUT)
	except Exception as e:
		log.warning("FreeRadio LibriVox: archive.org search failed: %s", e)
		return [], str(e)

	try:
		data = json.loads(response_text)
	except ValueError as e:
		log.warning("FreeRadio LibriVox: could not parse archive.org search response: %s", e)
		return [], str(e)

	docs = (((data or {}).get("response") or {}).get("docs")) or []
	books = []
	for doc in docs:
		try:
			books.append(_parse_archive_doc(doc))
		except Exception as e:
			log.warning("FreeRadio LibriVox: could not parse one archive.org result: %s", e)

	return books, None



# --------------------------------------------------------------------- #
# Book model - see the module docstring for why this mirrors GetemBook.
# --------------------------------------------------------------------- #

class LibrivoxBook:
	"""A single LibriVox audiobook. Attribute- and method-compatible with
	getem.GetemBook so radioDialog.py's generic Audio Books tab code (result
	formatting, library persistence, playback, audio profiles, downloads)
	works unmodified against either source - see
	RadioDialog._current_audiobook_module()/_current_audiobook_library()."""

	def __init__(self, title, detail_url, author="", narrator="", format_label="",
			description="", publisher="", language="", url_rss="", archive_id=""):
		self.title = title or _("Unknown")
		self.detail_url = detail_url
		self.author = author
		# LibriVox credits readers per-chapter rather than one narrator per
		# book, so there's no single value to put here - kept for
		# attribute-compatibility with GetemBook (used by
		# _format_getem_details()) and always empty.
		self.narrator = narrator
		self.format_label = format_label
		self.description = description
		# LibriVox has no publisher concept; kept empty for the same reason
		# as narrator above.
		self.publisher = publisher
		self.language = language
		# Kept for backward compatibility with library entries saved by
		# older versions of this module, which resolved chapters through
		# LibriVox's own RSS feed - see _resolve_via_librivox_rss(). New
		# books found through search_librivox() leave this empty and set
		# archive_id instead - see resolve_media().
		self.url_rss = url_rss
		# archive.org item identifier (e.g. "the_conquest_of_happiness_librivox").
		# Set for books found via the current, archive.org-based
		# search_librivox() - resolve_media() uses this to fetch chapters
		# from archive.org's metadata API. Empty for older library entries
		# that predate this, which fall back to url_rss instead.
		self.archive_id = archive_id
		# Populated lazily by resolve_media(): [{"title": str, "url": str}, ...]
		self.chapters = []
		self.last_chapter_index = 0
		self.audio_profile = None

	def identity_key(self):
		return self.detail_url

	def to_dict(self):
		"""Same station-like dict shape as getem.GetemBook.to_dict() (see
		its docstring for the full rationale) - including reusing the
		"getem_detail_url"/tag names verbatim rather than LibriVox-specific
		ones. Several places outside this tab (radioPlayer.py's
		resume/seek/speed handling, and __init__.py's own-session "resume
		last station" rebuild) key off those exact field names regardless
		of which audiobook source the book actually came from, so reusing
		them here - rather than inventing "librivox_detail_url" - is what
        lets a LibriVox book get the same resume/seek/speed treatment a
		GETEM book or podcast episode gets, without those other files
		needing to learn a second field name.

		Also includes author/narrator/publisher/format_label, the book's
		total part count, its description, and a fixed
		"audiobook_source" label - same rationale as GetemBook.to_dict(),
		so the station-details dialog
		(trackInfoMixin._build_audiobook_details()) can show these
		audiobook-specific fields regardless of which source the book
		came from. narrator/publisher are always empty for LibriVox (see
		__init__ above) and simply won't be shown. "audiobook_source" is
		the exact same bare "LibriVox" string
		RadioDialog._audiobook_source_label_for() already produces, kept
		in sync manually since librivox.py has no reason to import
		radioDialog.py."""
		return {
			"name": self.title,
			"url": "",
			"url_resolved": "",
			"stationuuid": "librivox-" + str(uuid.uuid5(uuid.NAMESPACE_URL, self.detail_url)),
			"countrycode": "",
			"tags": "podcast,audiobook",
			# See podcast.PodcastEpisode.to_dict()'s comment on "media_kind"
			# for why this exists as a separate field from "tags" above:
			# "tags" is kept as-is (unused for detection now, harmless to
			# leave) purely for backward compatibility with anything still
			# reading it; all resume/seek/speed/download logic should key
			# off "media_kind" instead, which can never collide with a
			# real Radio Browser station's own genre tags.
			"media_kind": "audiobook",
			"getem_detail_url": self.detail_url,
			"author": self.author,
			"narrator": self.narrator,
			"publisher": self.publisher,
			"audiobook_format": self.format_label,
			"audiobook_chapter_count": len(self.chapters),
			"description": self.description,
			"audiobook_source": _("LibriVox"),
		}

	def to_library_dict(self):
		return {
			"title": self.title,
			"author": self.author,
			"narrator": self.narrator,
			"format_label": self.format_label,
			"description": self.description,
			"publisher": self.publisher,
			"language": self.language,
			"url_rss": self.url_rss,
			"archive_id": self.archive_id,
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
			language=data.get("language", ""),
			url_rss=data.get("url_rss", ""),
			archive_id=data.get("archive_id", ""),
		)
		book.chapters = data.get("chapters", []) or []
		book.last_chapter_index = data.get("last_chapter_index", 0) or 0
		book.audio_profile = data.get("audio_profile") or None
		return book


# --------------------------------------------------------------------- #
# Media resolution
# --------------------------------------------------------------------- #

def resolve_media(book, session=None):
	"""Fills in *book*.chapters with every part/chapter found for it, in
	listening order. *session* is accepted but unused - kept only so
	radioDialog.py can call this the same way it calls
	getem.resolve_media(book, session=...), with no source-specific
	branching. Returns (book, error_message), matching
	getem.resolve_media()'s contract.

	Dispatches to whichever of archive.org or LibriVox's own RSS feed
	*book* actually has enough information to use - see the module
	docstring for why archive.org is the path used for books found
	through the current search_librivox()."""
	if book.archive_id:
		return _resolve_via_archive_org(book)
	return _resolve_via_librivox_rss(book)


def looks_like_book_url(text):
	"""Whether *text* (typically whatever was typed into the Audio Books
	search field) looks like an archive.org book link rather than a
	keyword search - see get_book_by_url()/RadioDialog._on_getem_search()."""
	return bool(ARCHIVE_DETAILS_URL_RE.match((text or "").strip()))


def get_book_by_url(url):
	"""Resolves a book directly from an archive.org "details" URL - e.g.
	one pasted from a browser's address bar, or copied via this tab's own
	"Copy the URL" context menu action (see RadioDialog._copy_to_clipboard()) -
	instead of having to search for it by title/author again. Fetches the
	book's metadata AND its chapter list in the same request, since
	archive.org's metadata API already returns both - see
	_book_from_metadata(). Returns (book_or_None, error_message)."""
	match = ARCHIVE_DETAILS_URL_RE.match((url or "").strip())
	if not match:
		return None, _("This doesn't look like an archive.org book link.")
	return _resolve_book_by_identifier(match.group(1))


def _resolve_book_by_identifier(identifier):
	url = ARCHIVE_METADATA_URL + urllib.parse.quote(identifier, safe="")
	try:
		response_text = _fetch(url, timeout=REQUEST_TIMEOUT)
	except Exception as e:
		return None, str(e)

	try:
		data = json.loads(response_text)
	except ValueError as e:
		return None, str(e)

	meta = data.get("metadata") or {}
	if not meta or not meta.get("identifier"):
		return None, _("Could not find a book at this address on archive.org.")

	book = _parse_archive_doc({
		"identifier": identifier,
		"title": meta.get("title"),
		"creator": meta.get("creator"),
		"language": meta.get("language"),
		"description": meta.get("description"),
		"runtime": meta.get("runtime"),
	})
	return _chapters_from_metadata(book, data)


def _chapters_from_metadata(book, data):
	"""Fills in *book*.chapters from an already-fetched archive.org
	metadata *data* response, using the "64Kbps MP3" file group that
	every LibriVox item on archive.org exposes - one file per chapter,
	already in track order (see the module docstring). Shared by
	_resolve_via_archive_org() (which fetches *data* itself, for a book
	found through search_librivox()) and _resolve_book_by_identifier()
	(which already has *data* on hand from resolving a pasted book URL -
	see get_book_by_url()), so the chapter-picking logic only lives in
	one place. Returns (book, error_message)."""
	files = data.get("files") or []
	server = data.get("server") or data.get("d1") or ""
	item_dir = data.get("dir") or ""

	def _file_url(name):
		# Prefer the item's own assigned server/dir from the metadata
		# response when present (matches what the site itself links to);
		# fall back to the generic /download/ URL, which archive.org
		# transparently redirects to the right server either way.
		if server and item_dir:
			return "https://%s%s/%s" % (server, item_dir, urllib.parse.quote(name))
		return ARCHIVE_DOWNLOAD_BASE + urllib.parse.quote(book.archive_id, safe="") + "/" + urllib.parse.quote(name)

	def _track_key(f):
		track = (f.get("track") or "").split("/")[0].strip()
		try:
			return (0, int(track))
		except (TypeError, ValueError):
			return (1, f.get("name") or "")

	mp3_files = [f for f in files if isinstance(f, dict) and (f.get("format") or "") == "64Kbps MP3"]
	if not mp3_files:
		# A handful of very old items only have a variable-bitrate
		# derivative instead of a fixed 64Kbps one - fall back to that
		# rather than showing no chapters at all.
		mp3_files = [f for f in files if isinstance(f, dict) and (f.get("format") or "") == "VBR MP3"]
	mp3_files.sort(key=_track_key)

	chapters = []
	for f in mp3_files:
		name = f.get("name") or ""
		if not name:
			continue
		title = (f.get("title") or "").strip() or os.path.splitext(os.path.basename(name))[0]
		chapters.append({"title": title, "url": _file_url(name)})

	if not chapters:
		return book, _("No playable audio file was found for this book on archive.org.")

	book.chapters = chapters
	return book, None


def _resolve_via_archive_org(book):
	"""Fetches *book*'s chapter list from archive.org's metadata API
	(https://archive.org/metadata/<identifier>) - see
	_chapters_from_metadata() for the actual file-picking logic, shared
	with the direct book-URL lookup path (get_book_by_url()). No login is
	required; these are ordinary public files."""
	url = ARCHIVE_METADATA_URL + urllib.parse.quote(book.archive_id, safe="")
	try:
		response_text = _fetch(url, timeout=REQUEST_TIMEOUT)
	except Exception as e:
		return book, str(e)

	try:
		data = json.loads(response_text)
	except ValueError as e:
		return book, str(e)

	return _chapters_from_metadata(book, data)



def _resolve_via_librivox_rss(book):
	"""Fetches *book*'s LibriVox RSS feed (book.url_rss) and fills in its
	.chapters with every part found there, in feed order. Used only as a
	fallback for library entries saved by older versions of this module
	(before search moved to archive.org - see the module docstring),
	which have a url_rss but no archive_id.

	No login is required - LibriVox's RSS feeds and the audio files they
	link to (almost always hosted on archive.org) are public."""
	if not book.url_rss:
		return book, _("This book has no LibriVox RSS feed to read chapters from.")

	try:
		feed_text = _fetch(book.url_rss, timeout=REQUEST_TIMEOUT)
	except Exception as e:
		return book, str(e)

	try:
		root = ET.fromstring(feed_text)
	except ET.ParseError as e:
		return book, str(e)

	channel = root.find("channel")
	if channel is None:
		return book, _("Could not read this book's chapter list.")

	chapters = []
	for item in channel.findall("item"):
		title = (item.findtext("title") or "").strip() or _("Untitled")
		enclosure = item.find("enclosure")
		url = enclosure.get("url") if enclosure is not None else None
		if not url:
			continue
		chapters.append({"title": title, "url": url})

	if not chapters:
		return book, _("No playable audio file was found in this book's LibriVox feed.")

	# LibriVox RSS feeds list chapters oldest-first already (matching
	# listening order), unlike a typical podcast feed - no re-sort needed.
	book.chapters = chapters
	return book, None


# --------------------------------------------------------------------- #
# Streaming - no proxy needed (see module docstring): a LibriVox chapter
# URL is already a plain public https:// link the player can open
# directly, so this is a trivial pass-through kept only so
# radioDialog.py's playback code can call module.get_stream_url(...)
# identically for either audiobook source - see _start_getem_chapter().
# --------------------------------------------------------------------- #

def get_stream_url(chapter_url, referer=None):
	return chapter_url


# --------------------------------------------------------------------- #
# Downloads - same shapes as the corresponding getem.py functions, so
# radioDialog.py's download code (_download_getem_book() and friends)
# works unmodified against either source.
# --------------------------------------------------------------------- #

def _fetch_audio_file(chapter_url, dest_path, referer=None, session=None, progress_callback=None):
	headers = {"User-Agent": USER_AGENT, "Accept": "audio/mpeg, audio/*;q=0.9, */*;q=0.5"}
	req = urllib.request.Request(chapter_url, headers=headers)
	tmp_path = dest_path + ".part"
	with urllib.request.urlopen(req, timeout=60) as resp:
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
		raise RuntimeError(_("The downloaded file was empty."))

	os.replace(tmp_path, dest_path)
	return dest_path


def download_chapter_to(chapter_url, out_path, referer=None, session=None, progress_callback=None):
	if os.path.exists(out_path):
		raise FileExistsError(out_path)
	return _fetch_audio_file(chapter_url, out_path, referer=referer, session=session, progress_callback=progress_callback)


def _chapter_file_extension(chapter_url):
	url_path = urllib.parse.urlparse(chapter_url).path
	ext = os.path.splitext(url_path)[1]
	return ext if ext else ".mp3"


def safe_book_title(book):
	return "".join(c for c in book.title if c.isalnum() or c in " .-_")[:60].strip()


def download_target(book, chapter):
	from . import recorder
	out_dir = recorder._recordings_dir()
	safe_book = safe_book_title(book)
	chapter_title = chapter.get("title") or ""
	safe_chapter = "".join(c for c in chapter_title if c.isalnum() or c in " .-_")[:60].strip()
	ext = _chapter_file_extension(chapter["url"])
	if safe_chapter and safe_chapter != safe_book:
		filename = f"{safe_book} - {safe_chapter}{ext}"
	else:
		filename = f"{safe_book}{ext}"
	return os.path.join(out_dir, filename), filename


def book_download_dir(book):
	from . import recorder
	out_dir = recorder._recordings_dir()
	return os.path.join(out_dir, safe_book_title(book) or _("Untitled"))


def download_book_chapter_target(book, chapter, chapter_index):
	out_dir = book_download_dir(book)
	chapter_title = (chapter.get("title") or "").strip()
	safe_chapter = "".join(c for c in chapter_title if c.isalnum() or c in " .-_")[:60].strip()
	ext = _chapter_file_extension(chapter["url"])
	width = len(str(len(book.chapters)))
	number = str(chapter_index + 1).zfill(width)
	safe_book = safe_book_title(book)
	if safe_chapter and safe_chapter != safe_book:
		filename = f"{number} - {safe_chapter}{ext}"
	else:
		filename = f"{number}{ext}"
	return os.path.join(out_dir, filename)


# --------------------------------------------------------------------- #
# Library persistence - same shape as getem.GetemLibrary.
# --------------------------------------------------------------------- #

class LibrivoxLibrary:
	"""The user's saved LibriVox audio books. Persisted separately from
	GETEM's library (its own JSON file) - see radioDialog.py's Audio Books
	tab "Source" dropdown, which switches which of the two libraries is
	shown/searched/played, rather than merging them into one list."""

	def __init__(self):
		self._books = []
		self._load()

	def _get_path(self):
		return os.path.join(globalVars.appArgs.configPath, "freeradio_librivox_library.json")

	def _load(self):
		path = self._get_path()
		if not os.path.exists(path):
			return
		try:
			with open(path, "r", encoding="utf-8") as f:
				data = json.load(f)
			self._books = [LibrivoxBook.from_dict(item) for item in data if isinstance(item, dict)]
		except Exception as e:
			log.warning("FreeRadio LibriVox: failed to load library: %s", e)

	def save(self):
		try:
			path = self._get_path()
			tmp_path = path + ".tmp"
			with open(tmp_path, "w", encoding="utf-8") as f:
				json.dump([b.to_library_dict() for b in self._books], f, ensure_ascii=False, indent=4)
			os.replace(tmp_path, path)
		except Exception as e:
			log.warning("FreeRadio LibriVox: failed to save library: %s", e)

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
		existing = self.get_book_by_key(book.identity_key())
		if not existing:
			return
		existing.last_chapter_index = chapter_index
		self.save()