"""Konektor: RSS nyata dengan fallback korpus demo, kuota, kesehatan konektor."""
import logging, time, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from . import config, db, scrape, textutil

log = logging.getLogger("naradig.connectors")
UA = "NARADIG/1.2 (+riset narasi publik; hanya feed yang diizinkan)"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def _ssl_ctx():
    """Pakai CA bundle certifi bila ada (Windows sering tidak punya root CA untuk urllib)."""
    try:
        import ssl, certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def http_get(url: str, tries: int = 2, timeout: int = 10) -> bytes:
    """GET dengan retry terbatas + exponential backoff (NFR-004). Tidak mengakali rate limit."""
    last = None
    ctx = _ssl_ctx()
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            kw = {"timeout": timeout}
            if ctx is not None:
                kw["context"] = ctx
            with urllib.request.urlopen(req, **kw) as r:
                return r.read()
        except Exception as e:  # transien saja; tidak retry pada 4xx
            last = e
            if i + 1 < tries:
                time.sleep(0.5 * (2 ** i))
    raise last


def parse_feed(raw: bytes):
    """Dukung RSS 2.0 dan Atom. Kembalikan list dict ternormalisasi."""
    root = ET.fromstring(raw)
    out = []
    for it in root.iter("item"):
        out.append({
            "title": (it.findtext("title") or "").strip(),
            "text": (it.findtext("description") or "").strip(),
            "url": (it.findtext("link") or "").strip(),
            "pub": _pub(it.findtext("pubDate") or it.findtext("date")),
            "source": _source(root),
        })
    for e in root.findall(".//atom:entry", NS):
        link = e.find("atom:link", NS)
        out.append({
            "title": (e.findtext("atom:title", "", NS) or "").strip(),
            "text": (e.findtext("atom:summary", "", NS) or e.findtext("atom:content", "", NS) or "").strip(),
            "url": link.get("href") if link is not None else "",
            "pub": _pub(e.findtext("atom:updated", "", NS) or e.findtext("atom:published", "", NS)),
            "source": _source(root),
        })
    return [x for x in out if x["title"] or x["text"]]


def _source(root):
    return (root.findtext("channel/title") or root.findtext("atom:title", "", NS) or "RSS").strip()


def _pub(s):
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except Exception:
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return int(d.timestamp() * 1000)


def quota(c):
    d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db.q_ignore("INSERT OR IGNORE INTO quota VALUES(?,?,0)", (c, d))
    return db.q("SELECT used FROM quota WHERE conn=? AND day=?", (c, d), one=True)["used"]


def use_quota(c):
    d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db.q("UPDATE quota SET used=used+1 WHERE conn=? AND day=?", (c, d), write=True)


def enabled(c):
    r = db.q("SELECT enabled FROM connectors WHERE id=?", (c,), one=True)
    return bool(r and r["enabled"])


def health(c):
    return db.q("SELECT ok,latency_ms,error,at FROM connector_health WHERE conn=? ORDER BY id DESC LIMIT 1", (c,), one=True)


def _record(c, ok, ms, err=""):
    db.q("INSERT INTO connector_health(conn,ok,latency_ms,error,at) VALUES(?,?,?,?,?)",
         (c, int(ok), ms, err[:300], int(time.time() * 1000)), write=True)


def fetch_conn(c, query, limit, days, ws, skip_seen):
    """Ambil item dari konektor. RSS/scraper nyata -> fallback mock. Konektor lain: mock."""
    qt = set(textutil.tok(query))
    if not qt:
        return []
    feeds = {"rss-berita": config.RSS_FEEDS, "rss-cekfakta": config.FACTCHECK_FEEDS}.get(c, [])
    items = []
    if c == "web-berita":
        t0 = time.time()
        try:
            items = [it for it in scrape.fetch(query, min(limit, config.SCRAPE_MAX))
                     if _match(qt, it["title"] + " " + it["text"])]
            _record(c, bool(items), int((time.time() - t0) * 1000), "" if items else "tidak ada artikel cocok")
        except Exception as e:
            log.warning("scrape %s gagal: %s", c, e)
            _record(c, False, int((time.time() - t0) * 1000), str(e))
    if feeds:
        t0 = time.time()
        err = ""
        try:
            for url in feeds:
                for it in parse_feed(http_get(url)):
                    if _match(qt, it["title"] + " " + it["text"]):
                        items.append(_rec(c, it))
        except Exception as e:
            err = str(e)
            log.warning("feed %s gagal: %s", c, e)
        if items:
            _record(c, True, int((time.time() - t0) * 1000))
        elif err:
            _record(c, False, int((time.time() - t0) * 1000), err)
    if not items and config.ALLOW_MOCK:  # fallback korpus demo (FR-028)
        items = []
        for sid, cid, src, d, title, text in sorted(config.CORP, key=lambda x: x[3]):
            if cid != c or (days and d > days) or not _match(qt, title + " " + text):
                continue
            items.append({"src_id": sid, "conn": c, "source": src, "title": title, "text": text,
                          "url": f"https://contoh.demo/{c}/{sid}", "pub": _now() - d * config.DAY,
                          "method": "open_dataset", "license": "Korpus demo", "origin": "mock"})
    out = []
    for it in items:
        it.setdefault("method", "rss")
        it.setdefault("license", "RSS publik")
        if skip_seen and it.get("src_id") and db.q(
                "SELECT 1 FROM contents WHERE ws=? AND conn=? AND src_id=?", (ws, c, it["src_id"]), one=True):
            continue
        out.append(it)
    return out[:limit]


def _rec(c, it):
    return {"src_id": it["url"] or None, "conn": c, "source": it["source"] or "RSS",
            "title": it["title"] or it["text"][:60], "text": it["text"] or it["title"],
            "url": it["url"] or None, "pub": it["pub"], "method": "rss", "license": "RSS publik",
            "origin": "live"}


def probe(c, limit=3):
    """Diagnostik feed: dipakai GET /feed-test. Tidak menyimpan data."""
    feeds = {"rss-berita": config.RSS_FEEDS, "rss-cekfakta": config.FACTCHECK_FEEDS}.get(c, [])
    out = []
    for url in feeds:
        t0 = time.time()
        row = {"url": url}
        try:
            items = parse_feed(http_get(url))
            row.update(ok=True, items=len(items), ms=int((time.time() - t0) * 1000),
                       sample=[i["title"] for i in items[:limit]])
        except Exception as e:
            row.update(ok=False, error=str(e), ms=int((time.time() - t0) * 1000))
        out.append(row)
    return out


def _match(qt, blob):
    return bool(qt & set(textutil.tok(blob)))


def _now():
    return int(time.time() * 1000)