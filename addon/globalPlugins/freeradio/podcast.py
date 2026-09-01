# -*- coding: utf-8 -*-
# FreeRadio - Podcast Manager
# RSS/Atom podcast feed parser, subscription manager, and iTunes search.

import json
import logging
import os
import time
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime

import addonHandler
addonHandler.initTranslation()
import globalVars

log = logging.getLogger(__name__)

USER_AGENT = "FreeRadio-NVDA/1.0"
REQUEST_TIMEOUT = 15


def _parse_duration_seconds(duration):
	"""Parse an itunes:duration string into whole seconds.

	Accepts "HH:MM:SS", "MM:SS", or a plain seconds value like "754".
	Returns 0 if *duration* is empty or can't be parsed.
	"""
	if not duration:
		return 0
	duration = duration.strip()
	if not duration:
		return 0
	if ":" in duration:
		parts = duration.split(":")
		try:
			parts = [int(p) for p in parts]
		except ValueError:
			return 0
		seconds = 0
		for p in parts:
			seconds = seconds * 60 + p
		return seconds
	try:
		return int(float(duration))
	except ValueError:
		return 0


def episode_download_target(title, url):
	"""Compute the destination path and filename a podcast episode would be
	downloaded to. Cheap and synchronous - safe to call directly from the
	UI/main thread to decide whether a download is even necessary (e.g. the
	file already exists) before spinning up a background thread.
	Returns (out_path, filename).
	"""
	from . import recorder
	out_dir = recorder._recordings_dir()
	safe_title = "".join(c for c in title if c.isalnum() or c in " .-_")[:80]
	url_path = urllib.parse.urlparse(url).path
	ext = os.path.splitext(url_path)[1] or ".mp3"
	if not ext.startswith("."):
		ext = "." + ext
	filename = f"{safe_title}{ext}"
	out_path = os.path.join(out_dir, filename)
	return out_path, filename


def download_episode_file(url, out_path):
	"""Download *url* to *out_path*. Blocking network/disk I/O - always call
	this from a background thread, never the UI thread. On failure, cleans
	up any partial file and re-raises so the caller can report it.
	"""
	req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
	try:
		with urllib.request.urlopen(req, timeout=60) as resp:
			with open(out_path, "wb") as f:
				while True:
					chunk = resp.read(65536)
					if not chunk:
						break
					f.write(chunk)
	except Exception:
		try:
			if os.path.exists(out_path):
				os.remove(out_path)
		except Exception:
			pass
		raise


class PodcastEpisode:
	"""Represents a single podcast episode."""

	def __init__(self, title, url, published, duration="", description=""):
		self.title = title
		self.url = url          # enclosure or link URL
		self.published = published  # datetime object
		self.duration = duration    # string like "12:34" or "123"
		self.duration_seconds = _parse_duration_seconds(duration)
		self.description = description
		# Sequence number within the feed (1 = oldest episode), assigned
		# after the whole feed is parsed and sorted - see
		# PodcastManager._assign_episode_numbers(). None until then.
		self.number = None

	def to_dict(self):
		"""Convert to a dictionary compatible with radioPlayer station format.

		Includes "description" so the station-details dialog
		(trackInfoMixin._build_podcast_details()) can show the same
		episode description text the Podcasts tab's episode-details box
		shows (via RadioDialog._format_episode_details()) for whichever
		episode is actually playing."""
		return {
			"name": self.title,
			"url": self.url,
			"url_resolved": self.url,
			"stationuuid": "podcast-" + str(uuid.uuid4()),
			"countrycode": "",
			"tags": "podcast",
			# Dedicated marker used by radioPlayer.py/timeshiftMixin.py/
			# radioDialog.py/__init__.py to decide whether this is a
			# seekable local-media item (podcast/audio book) that gets
			# resume/seek/speed handling. Deliberately NOT the same thing
			# as "tags" above: "tags" is free-text and, for real Radio
			# Browser stations elsewhere in the app, can legitimately
			# contain the substring "podcast" as a community-assigned
			# genre on a live stream (e.g. talk-radio stations mirrored
			# from podcast-hosting platforms like Zeno.fm or Qingting.fm).
			# Checking that free-text field for "podcast"/"audiobook" used
			# to be how this was detected, which meant any live station
			# tagged that way by Radio Browser got treated as a
			# downloadable, seekable podcast episode - opened as
			# seekable=True, resumed to a stale/impossible saved position
			# on an actually-infinite stream, and left silently stuck
			# behind the casette.mp3 resume-wait effect. "media_kind" is
			# only ever set here, in getem.GetemBook.to_dict(), and in
			# librivox.LibriVoxBook.to_dict() - never derived from
			# external data - so it can't collide with a real station's
			# genre tags.
			"media_kind": "podcast",
			"episode_published": self.published.isoformat() if self.published else "",
			"episode_duration": self.duration,
			"description": self.description,
		}

	def _progress_prefix_and_suffix(self, position, listened):
		"""Build the "[Listened]" prefix and duration suffix for a given
		position (seconds; -1.0 means fully listened) and listened flag.

		- Listened: "[Listened]" prefix, no suffix.
		- Partially played (position > 0): " (elapsed / total)", or just
		  " (elapsed)" if the episode's total duration isn't known.
		- Never played: " (total)" if the total duration is known,
		  otherwise nothing.
		"""
		from .__init__ import _format_duration
		total = self.duration_seconds

		if listened or position == -1.0:
			return _("[Listened]"), ""
		if position and position > 0.0:
			if total > 0:
				return "", f" ({_format_duration(position)} / {_format_duration(total)})"
			return "", f" ({_format_duration(position)})"
		if total > 0:
			return "", f" ({_format_duration(total)})"
		return "", ""

	def display_label(self, player=None):
		"""Return string for listbox display: episode number, "[Listened]"
		prefix if completed, elapsed/total duration if partially played, or
		just the total duration for episodes that have never been played."""
		label = self.title
		if self.published:
			label = f"{self.published} - {label}"
		if self.number is not None:
			label = f"{self.number}. {label}"

		if player:
			pos = player.get_podcast_position(self.url)
			with player._podcast_positions_lock:
				entry = player._podcast_positions.get(self.url, {})
			listened = bool(entry.get("listened"))
			prefix, suffix = self._progress_prefix_and_suffix(pos, listened)
			if prefix:
				label = f"{prefix} {label}"
			label += suffix

		return label

	def live_display_label(self, position, listened):
		"""Same as display_label(), but built from a live (not-yet-persisted
		to disk) position/listened pair - e.g. from
		RadioPlayer.get_live_podcast_progress(). Used for per-second episode
		list updates during playback, since the disk-backed position is only
		saved periodically."""
		label = self.title
		if self.published:
			label = f"{self.published} - {label}"
		if self.number is not None:
			label = f"{self.number}. {label}"

		prefix, suffix = self._progress_prefix_and_suffix(position, listened)
		if prefix:
			label = f"{prefix} {label}"
		label += suffix

		return label


class PodcastFeed:
	"""Represents a subscribed podcast feed."""

	def __init__(self, url, title="", image="", author="", description=""):
		self.url = url
		self.title = title or url
		self.image = image
		self.author = author
		self.description = description
		self.episodes = []          # list of PodcastEpisode
		self.last_refresh = 0.0     # timestamp
		self._etag = ""
		self._modified = ""
		# Optional dict of {"volume": int, "fx": str, "eq_gains": {...},
		# "speed": float} applied to every episode of this feed when it
		# starts playing - see playbackCoreMixin._play_station() and
		# RadioDialog._on_episode_play(). None if the user hasn't saved one.
		self.audio_profile = None

	def to_dict(self):
		return {
			"url": self.url,
			"title": self.title,
			"image": self.image,
			"author": self.author,
			"description": self.description,
			"last_refresh": self.last_refresh,
			"_etag": self._etag,
			"_modified": self._modified,
			"audio_profile": self.audio_profile,
		}

	@classmethod
	def from_dict(cls, data):
		feed = cls(
			url=data["url"],
			title=data.get("title", data["url"]),
			image=data.get("image", ""),
			author=data.get("author", ""),
			description=data.get("description", ""),
		)
		feed.last_refresh = data.get("last_refresh", 0.0)
		feed._etag = data.get("_etag", "")
		feed._modified = data.get("_modified", "")
		feed.audio_profile = data.get("audio_profile") or None
		return feed


class PodcastManager:
	"""Manages podcast subscriptions and feed parsing."""

	def __init__(self):
		self._feeds = []  # list of PodcastFeed
		self._load()

	def _get_path(self):
		return os.path.join(globalVars.appArgs.configPath, "freeradio_podcasts.json")

	def _load(self):
		path = self._get_path()
		if not os.path.exists(path):
			return
		try:
			with open(path, "r", encoding="utf-8") as f:
				data = json.load(f)
			self._feeds = [PodcastFeed.from_dict(item) for item in data]
			# Episodes are not persisted, fetched on refresh.
			for feed in self._feeds:
				feed.episodes = []
		except Exception as e:
			log.warning("FreeRadio Podcast: failed to load subscriptions: %s", e)
			self._feeds = []

	def _save(self):
		path = self._get_path()
		data = [f.to_dict() for f in self._feeds]
		try:
			with open(path, "w", encoding="utf-8") as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception as e:
			log.warning("FreeRadio Podcast: failed to save subscriptions: %s", e)

	def get_feeds(self):
		"""Return a list of subscribed feeds (metadata only, episodes may be empty)."""
		return list(self._feeds)

	def get_feed_by_url(self, url):
		for feed in self._feeds:
			if feed.url == url:
				return feed
		return None

	def add_feed(self, url):
		"""Fetch and parse the feed, add it to subscriptions if valid.
		Returns (feed, error_message) where error_message is None on success.
		"""
		feed = self.get_feed_by_url(url)
		if feed:
			return feed, _("Already subscribed.")

		try:
			feed, error = self._fetch_and_parse(url)
			if error:
				return None, error
			if not feed.episodes:
				return None, _("No episodes found in this feed.")
			self._feeds.append(feed)
			self._save()
			return feed, None
		except Exception as e:
			log.warning("FreeRadio Podcast: add feed failed: %s", e)
			return None, str(e)

	def fetch_preview(self, url):
		"""Fetch and parse a feed for preview purposes only (e.g. so the user
		can browse its episodes before deciding to subscribe). Does not add
		to, remove from, or otherwise modify the subscription list.
		Returns (PodcastFeed, error_message) where error_message is None on
		success.
		"""
		try:
			return self._fetch_and_parse(url)
		except Exception as e:
			log.warning("FreeRadio Podcast: preview fetch failed: %s", e)
			return None, str(e)

	def remove_feed(self, url):
		feed = self.get_feed_by_url(url)
		if feed:
			self._feeds.remove(feed)
			self._save()
			return True
		return False

	def refresh_feed(self, url):
		"""Re-fetch and update episodes for a given feed URL."""
		feed = self.get_feed_by_url(url)
		if not feed:
			return None, _("Feed not found.")

		try:
			new_feed, error = self._fetch_and_parse(url, feed)
			if error:
				return feed, error
			feed.episodes = new_feed.episodes
			feed.title = new_feed.title or feed.title
			feed.image = new_feed.image or feed.image
			feed.author = new_feed.author or feed.author
			feed.description = new_feed.description or feed.description
			feed.last_refresh = time.time()
			self._save()
			return feed, None
		except Exception as e:
			log.warning("FreeRadio Podcast: refresh feed failed: %s", e)
			return feed, str(e)

	def _fetch_and_parse(self, url, existing_feed=None):
		"""Low-level fetch and parse. Returns (PodcastFeed, error_string)."""
		headers = {"User-Agent": USER_AGENT}
		if existing_feed and existing_feed._etag:
			headers["If-None-Match"] = existing_feed._etag
		if existing_feed and existing_feed._modified:
			headers["If-Modified-Since"] = existing_feed._modified

		req = urllib.request.Request(url, headers=headers)
		try:
			with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
				if resp.status == 304:
					if existing_feed:
						existing_feed.last_refresh = time.time()
						self._save()
						return existing_feed, None
					return None, _("No new episodes (304).")

				raw = resp.read()
				encoding = resp.headers.get_content_charset() or "utf-8"
				try:
					text = raw.decode(encoding)
				except UnicodeDecodeError:
					text = raw.decode("utf-8", errors="replace")

				root = ET.fromstring(text)
				if root.tag.endswith("rss"):
					return self._parse_rss(root, url), None
				elif root.tag.endswith("feed"):
					return self._parse_atom(root, url), None
				else:
					return None, _("Unrecognized feed format (not RSS or Atom).")
		except urllib.error.HTTPError as e:
			if e.code == 304:
				if existing_feed:
					existing_feed.last_refresh = time.time()
					self._save()
					return existing_feed, None
				return None, _("No new episodes (304).")
			return None, f"HTTP {e.code}: {e.reason}"
		except Exception as e:
			return None, str(e)

	def _parse_rss(self, root, url):
		"""Parse RSS 2.0 feed with iTunes extensions."""
		channel = root.find("channel")
		if channel is None:
			return None

		title = channel.findtext("title") or url
		image = ""
		img_elem = channel.find("image/url")
		if img_elem is not None:
			image = img_elem.text or ""
		itunes_img = channel.find("itunes:image", namespaces={"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"})
		if itunes_img is not None and itunes_img.get("href"):
			image = itunes_img.get("href")
		author = channel.findtext("itunes:author", namespaces={"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}) or ""
		description = channel.findtext("description") or channel.findtext(
			"itunes:summary", namespaces={"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
		) or ""

		feed = PodcastFeed(url, title=title, image=image, author=author, description=description)

		for item in channel.findall("item"):
			title = item.findtext("title") or _("Untitled")
			enclosure = item.find("enclosure")
			if enclosure is not None and enclosure.get("url"):
				ep_url = enclosure.get("url")
			else:
				link = item.find("link")
				ep_url = link.text if link is not None else None
				if not ep_url:
					continue

			pub_date = item.findtext("pubDate")
			published = None
			if pub_date:
				try:
					published = parsedate_to_datetime(pub_date)
				except Exception:
					pass

			duration = item.findtext("itunes:duration", namespaces={"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}) or ""
			desc = item.findtext("description") or ""

			episode = PodcastEpisode(title, ep_url, published, duration, desc)
			feed.episodes.append(episode)

		feed.episodes.sort(key=lambda e: e.published or datetime.min, reverse=True)
		# feed.episodes is newest-first after the sort above, so the oldest
		# episode (last in the list) gets number 1, matching how podcasts
		# are conventionally numbered.
		total = len(feed.episodes)
		for i, ep in enumerate(feed.episodes):
			ep.number = total - i
		return feed

	def _parse_atom(self, root, url):
		"""Parse Atom feed."""
		ns = {"atom": "http://www.w3.org/2005/Atom"}
		title = root.findtext("atom:title", namespaces=ns) or url
		image = ""
		icon = root.find("atom:icon", namespaces=ns)
		if icon is not None:
			image = icon.text or ""
		logo = root.find("atom:logo", namespaces=ns)
		if logo is not None and not image:
			image = logo.text or ""
		author = root.findtext("atom:author/atom:name", namespaces=ns) or ""
		description = root.findtext("atom:subtitle", namespaces=ns) or ""

		feed = PodcastFeed(url, title=title, image=image, author=author, description=description)

		for entry in root.findall("atom:entry", namespaces=ns):
			title = entry.findtext("atom:title", namespaces=ns) or _("Untitled")
			ep_url = None
			for link in entry.findall("atom:link", namespaces=ns):
				rel = link.get("rel")
				typ = link.get("type") or ""
				if rel == "enclosure" or (rel == "alternate" and "audio" in typ) or (rel is None and "audio" in typ):
					ep_url = link.get("href")
					break
			if not ep_url:
				link = entry.find("atom:link", namespaces=ns)
				if link is not None:
					ep_url = link.get("href")
			if not ep_url:
				continue

			ep_url = urllib.parse.urljoin(url, ep_url)

			published = None
			pub_elem = entry.find("atom:published", namespaces=ns) or entry.find("atom:updated", namespaces=ns)
			if pub_elem is not None:
				try:
					published = parsedate_to_datetime(pub_elem.text)
				except Exception:
					pass

			duration = ""
			desc = entry.findtext("atom:summary", namespaces=ns) or ""

			episode = PodcastEpisode(title, ep_url, published, duration, desc)
			feed.episodes.append(episode)

		feed.episodes.sort(key=lambda e: e.published or datetime.min, reverse=True)
		# feed.episodes is newest-first after the sort above, so the oldest
		# episode (last in the list) gets number 1, matching how podcasts
		# are conventionally numbered.
		total = len(feed.episodes)
		for i, ep in enumerate(feed.episodes):
			ep.number = total - i
		return feed


def search_podcasts(query, limit=50):
	"""Search for podcasts using iTunes API. Returns list of dicts with title, feedUrl, artistName, image."""
	import urllib.parse
	import urllib.request
	import json

	url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&media=podcast&entity=podcast&limit={limit}"
	req = urllib.request.Request(url, headers={"User-Agent": "FreeRadio-NVDA/1.0"})
	try:
		with urllib.request.urlopen(req, timeout=10) as resp:
			data = json.loads(resp.read().decode('utf-8'))
		results = []
		for item in data.get('results', []):
			results.append({
				'title': item.get('trackName', '').strip(),
				'feedUrl': item.get('feedUrl', '').strip(),
				'artist': item.get('artistName', '').strip(),
				'image': item.get('artworkUrl100', ''),
				'description': item.get('description', '').strip(),
			})
		return results
	except Exception as e:
		log.warning("FreeRadio Podcast: iTunes search failed: %s", e)
		return []