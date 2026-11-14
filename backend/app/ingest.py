"""Canonical ingestion: validasi, normalisasi waktu, deteksi bahasa, deduplikasi."""
from datetime import datetime

from . import db, textutil


def _ts(v):
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).replace("Z", "+00:00")
    d = datetime.fromisoformat(s)
    if d.tzinfo is None:
        from datetime import timezone
        d = d.replace(tzinfo=timezone.utc)
    return int(d.timestamp() * 1000)


def ingest(ws, recs, method, lic):
    added = dup = 0
    bad = []
    for n, r in enumerate(recs, 1):
        t = str(r.get("text") or "").strip()
        if len(t) < 15:
            bad.append(f"Baris {n}: teks kosong atau terlalu pendek")
            continue
        pub = None
        if r.get("pub"):
            try:
                pub = _ts(r["pub"])
            except Exception:
                bad.append(f"Baris {n}: tanggal tidak valid")
                continue
        h = textutil.hsh(t)
        conn = r.get("conn", "import")
        src_id = r.get("src_id")
        if db.q("SELECT 1 FROM contents WHERE ws=? AND (hash=? OR (conn=? AND src_id=? AND src_id IS NOT NULL))",
                (ws, h, conn, src_id), one=True):
            dup += 1
            continue
        db.insert("INSERT INTO contents(ws,conn,src_id,source,title,text,url,pub,collected,lang,hash,method,license) "
                  "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (ws, conn, src_id, r.get("source") or "Impor", r.get("title") or t[:60], t,
                   r.get("url") or None, pub, _now(), textutil.lang(t), h, r.get("method") or method,
                   r.get("license") or lic))
        added += 1
    return dict(added=added, duplicates=dup, invalid=bad)


def _now():
    import time
    return int(time.time() * 1000)