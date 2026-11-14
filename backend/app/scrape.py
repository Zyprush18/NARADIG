"""Scraper HTML portal berita nyata: halaman tag/pencarian -> teks artikel.

Tanpa dependency tambahan (html.parser stdlib), tanpa API key. Sopan: 1 domain
per konektor, jeda 0,4 s antar artikel, jumlah per run dibatasi SCRAPE_MAX.

ponytail: parser memakai kelas container + fallback semua <p>. Kalau markup situs
berubah, cukup ubah token `body` di SITES; kalau butuh selektor kompleks/JS,
naikkan ke Playwright di file terpisah.
"""
import logging
import re
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

from . import config

log = logging.getLogger("naradig.scrape")

# link: pola URL artikel di halaman daftar. body: token kelas container isi artikel.
SITES = {
    "antara": {
        "name": "ANTARA News",
        "list": "https://www.antaranews.com/tag/{q}",
        "link": r"antaranews\.com/berita/\d+/",
        "body": "post-content",
    },
    "cnbc": {
        "name": "CNBC Indonesia",
        "list": "https://www.cnbcindonesia.com/tag/{q}",
        "link": r"cnbcindonesia\.com/[a-z]+/\d{14}-\d+-\d+/",
        "body": "detail-text",
    },
    "detik": {
        "name": "detikcom",
        "list": "https://www.detik.com/tag/{q}",
        "link": r"detik\.com/.+/d-\d+/",
        "body": "detail__body-text",
    },
    "suara": {
        "name": "Suara.com",
        "list": "https://www.suara.com/tag/{q}",
        "link": r"suara\.com/[a-z]+/\d{4}/\d{2}/\d{2}/",
        "body": "article-content",
        "date_re": r"/(\d{4})/(\d{2})/(\d{2})/(\d{2})(\d{2})(\d{2})/",
    },
    "liputan6": {
        "name": "Liputan6",
        "list": "https://www.liputan6.com/tag/{q}",
        "link": r"liputan6\.com/[a-z]+/read/\d+/",
        "body": "article-content",
    },
}

BODY_MIN = 80        # buang halaman yang isinya cuma paywall/iklan
BODY_MAX = 6000      # cukup untuk clustering, hemat SQLite

# Urutan prioritas meta tanggal terbit (makin kecil makin dipercaya).
DATE_META = ("article:published_time", "datepublished", "pubdate", "publishdate", "dc.date.issued", "date")
WIB = timezone(timedelta(hours=7))  # situs ID tanpa zona waktu: pakai WIB


class _Links(HTMLParser):
    def __init__(self, pattern):
        super().__init__(convert_charrefs=True)
        self.pat = re.compile(pattern)
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        if self.pat.search(href):
            self.urls.append(href)


class _Article(HTMLParser):
    """Kumpulkan paragraf + kelas leluhurnya, judul og:title/h1, waktu terbit."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.paras = []
        self.title = ""
        self.published = ""
        self._rank = len(DATE_META)
        self._p = None
        self._h1 = None

    def _date(self, value, rank):
        if value and rank < self._rank:
            self.published = value.strip()
            self._rank = rank

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key == "og:title" and not self.title:
                self.title = (a.get("content") or "").strip()
            elif key in DATE_META:
                self._date(a.get("content"), DATE_META.index(key))
            return
        if tag == "time":
            self._date(a.get("datetime"), len(DATE_META))
            return
        self.stack.append((tag, a.get("class") or ""))
        if tag == "p" and self._p is None:
            self._p = []
        elif tag == "h1" and self._h1 is None:
            self._h1 = []

    def handle_endtag(self, tag):
        if tag == "p" and self._p is not None:
            text = " ".join("".join(self._p).split())
            if len(text) > 40:
                self.paras.append((self._classes(), text))
            self._p = None
        elif tag == "h1" and self._h1 is not None:
            text = " ".join("".join(self._h1).split())
            if text and not self.title:
                self.title = text
            self._h1 = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._p is not None:
            self._p.append(data)
        if self._h1 is not None:
            self._h1.append(data)

    def _classes(self):
        return " ".join(cls for _, cls in self.stack)


def _get(url):
    from .connectors import http_get  # impor lokal: hindari siklus modul
    return http_get(url).decode("utf-8", "replace")


def _body(art, token):
    hit = [t for cls, t in art.paras if token in cls]
    return " ".join(hit or [t for _, t in art.paras])[:BODY_MAX]


def _ms(s):
    if not s:
        return None
    s = re.sub(r"T(\d{2})-(\d{2})-(\d{2})", r"T\1:\2:\3", s.strip())
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return int(datetime.strptime(s, fmt).replace(tzinfo=WIB).timestamp() * 1000)
        except ValueError:
            continue
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=WIB)
    return int(d.timestamp() * 1000)


def _url_ms(url, pattern):
    """Tanggal terbit dari pola URL (mis. Suara: /2026/11/14/064000/), diasumsikan WIB."""
    if not pattern:
        return None
    m = re.search(pattern, url)
    if not m:
        return None
    try:
        d = datetime(*(int(x) for x in m.groups()), tzinfo=WIB)
    except ValueError:
        return None
    return int(d.timestamp() * 1000)


def fetch(query, limit=None, sites=None):
    """Ambil artikel nyata untuk query. Kembalikan record siap ingest."""
    names = sites or [s.strip() for s in config.SCRAPE_SITES.split(",") if s.strip()]
    limit = limit or config.SCRAPE_MAX
    q = urllib.parse.quote(query)
    out = []
    for sid in names:
        site = SITES.get(sid)
        if not site:
            continue
        try:
            links = list(dict.fromkeys(_links(site["list"].format(q=q), site["link"])))[:limit]
        except Exception as e:
            log.warning("daftar %s gagal: %s", sid, e)
            continue
        for url in links:
            try:
                art = _Article()
                art.feed(_get(url))
                text = _body(art, site["body"])
                if len(text) < BODY_MIN:
                    continue
                out.append({
                    "src_id": url,
                    "conn": "web-berita",
                    "source": site["name"],
                    "title": art.title or text[:60],
                    "text": text,
                    "url": url,
                    "pub": _ms(art.published) or _url_ms(url, site.get("date_re")),
                    "method": "web",
                    "license": "Halaman publik",
                    "origin": "live",
                })
                time.sleep(0.4)  # sopan: ~2 req/s maksimum per proses
            except Exception as e:
                log.info("artikel %s gagal: %s", url, e)
    return out


def _links(url, pattern):
    p = _Links(pattern)
    p.feed(_get(url))
    return p.urls
