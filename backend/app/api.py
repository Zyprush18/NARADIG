"""API HTTP v1."""
import csv, io, json, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from . import analysis, config, connectors, db, ingest, jobs, security, textutil

P = "/api/v1"
r = APIRouter(prefix=P)


class Login(BaseModel):
    email: str
    password: str


class WS(BaseModel):
    name: str
    description: str = ""


class Topic(BaseModel):
    workspace_id: int
    name: str
    query: str
    sources: list[str]
    every_minutes: int = 60
    max_results: int = 3
    expires: Optional[str] = None


class Search(BaseModel):
    workspace_id: int
    query: str
    sources: list[str]
    days: int = 7
    limit: int = 10


class Preview(BaseModel):
    content: str


class Imp(BaseModel):
    workspace_id: int
    filename: str
    content: str
    mapping: dict
    license: str


class Rev(BaseModel):
    status: str
    notes: str = ""


class Rep(BaseModel):
    workspace_id: int


class Tog(BaseModel):
    enabled: bool


def audit(u, action, entity=""):
    db.insert("INSERT INTO audit(t,user,action,entity) VALUES(?,?,?,?)",
              (_now(), f'{u["name"]} ({u["role"]})' if u else "sistem", action, entity))


def _ws(ws_id: int):
    if not db.q("SELECT 1 FROM workspaces WHERE id=?", (ws_id,), one=True):
        raise HTTPException(404, "Workspace tidak ditemukan")


def _cluster(cid: str, workspace_id: int):
    """Klaster harus milik workspace yang diminta (anti-IDOR)."""
    if not db.q("SELECT 1 FROM clusters WHERE id=? AND ws=?", (cid, workspace_id), one=True):
        raise HTTPException(404, "Klaster tidak ditemukan")


# ---------- auth ----------
@r.post("/auth/login")
def login(b: Login, request: Request):
    key = f'{request.client.host if request.client else "?"}:{b.email.lower().strip()}'
    if not security.rate_ok(key):
        raise HTTPException(429, "Terlalu banyak percobaan login. Coba lagi 15 menit.")
    u = db.q("SELECT * FROM users WHERE email=?", (b.email.lower().strip(),), one=True)
    if not u or not security.pw_verify(b.password, u["pw"]):
        security.rate_hit(key)
        raise HTTPException(401, "Email atau kata sandi salah")
    security.rate_clear(key)
    if ":" not in (u["pw"] or ""):  # migrasi hash lama -> salt per user
        db.q("UPDATE users SET pw=? WHERE id=?", (security.pw_hash(b.password), u["id"]), write=True)
    audit(u, "Login")
    return {"token": security.make_token(u),
            "user": {"name": u["name"], "role": u["role"],
                     "permissions": sorted(config.ROLES[u["role"]])}}


@r.post("/auth/logout")
def logout(u=Depends(security.auth)):
    security.revoke(u)
    return {"ok": True}


# ---------- workspace ----------
@r.get("/workspaces")
def wss(u=Depends(security.auth)):
    return db.q("SELECT * FROM workspaces ORDER BY id")


@r.post("/workspaces")
def mkws(b: WS, u=Depends(security.need("create"))):
    if not b.name.strip():
        raise HTTPException(422, "Nama workspace wajib diisi")
    i = db.insert("INSERT INTO workspaces(name,description,owner,created) VALUES(?,?,?,?)",
                  (b.name.strip(), b.description, u["name"], _now()))
    audit(u, "Buat workspace", b.name)
    return {"id": i}


@r.delete("/workspaces/{wid}")
def rmws(wid: int, u=Depends(security.need("delete"))):
    _ws(wid)
    db.q("DELETE FROM reviews WHERE cluster_id IN (SELECT id FROM clusters WHERE ws=?)", (wid,), write=True)
    for t in ("alerts", "clusters", "contents", "jobs", "topics"):
        db.q(f"DELETE FROM {t} WHERE ws=?", (wid,), write=True)
    db.q("DELETE FROM workspaces WHERE id=?", (wid,), write=True)
    audit(u, "Hapus workspace (retensi)", f"ws {wid}")
    return {"ok": True}


# ---------- connectors ----------
@r.get("/connectors")
def conns(u=Depends(security.auth)):
    out = []
    for c in config.CONN:
        h = connectors.health(c["id"]) or {}
        out.append({**c, "enabled": connectors.enabled(c["id"]),
                    "quota_used": connectors.quota(c["id"]) if c["available"] else 0,
                    "quota_limit": config.LIM, "last_ok": h.get("ok"), "latency_ms": h.get("latency_ms"),
                    "last_error": h.get("error")})
    return out


@r.patch("/connectors/{cid}")
def tconn(cid: str, b: Tog, u=Depends(security.need("conn"))):
    c = next((x for x in config.CONN if x["id"] == cid), None)
    if not c:
        raise HTTPException(404, "Konektor tidak ditemukan")
    if not c["available"]:
        raise HTTPException(409, "Konektor belum tersedia: akses API belum diverifikasi")
    db.q("UPDATE connectors SET enabled=? WHERE id=?", (int(b.enabled), cid), write=True)
    audit(u, "Ubah konektor", f"{cid} → {b.enabled}")
    return {"ok": True}


@r.get("/feed-test")
def feed_test(u=Depends(security.auth)):
    """Cek feed nyata tanpa menyimpan data. Dipakai tombol 'Tes feed' di Data Sources."""
    return {"allow_mock": config.ALLOW_MOCK,
            "connectors": {c["id"]: connectors.probe(c["id"]) for c in config.CONN if c["available"]}}


MOCK = "(license LIKE '%Korpus demo%' OR license LIKE '%simulasi%' OR url LIKE 'https://contoh.demo/%')"


@r.post("/admin/purge-mock")
def purge_mock(u=Depends(security.need("delete"))):
    """Hapus konten korpus demo (termasuk data demo versi lama) + hasil analisis terkait."""
    wss = [x["ws"] for x in db.q(f"SELECT DISTINCT ws FROM contents WHERE {MOCK}")]
    for ws in wss:
        db.q("DELETE FROM reviews WHERE cluster_id IN (SELECT id FROM clusters WHERE ws=?)", (ws,), write=True)
        db.q("DELETE FROM alerts WHERE ws=?", (ws,), write=True)
        db.q("DELETE FROM clusters WHERE ws=?", (ws,), write=True)
    n = db.q(f"SELECT COUNT(*) AS n FROM contents WHERE {MOCK}", one=True)["n"]
    db.q(f"DELETE FROM contents WHERE {MOCK}", write=True)
    audit(u, "Bersihkan data demo", f"{len(wss)} workspace, {n} item")
    return {"removed": n, "workspaces": wss}


# ---------- monitoring ----------
@r.get("/monitoring-topics")
def topics(workspace_id: int, u=Depends(security.auth)):
    _ws(workspace_id)
    return [{**t, "sources": json.loads(t["sources"])} for t in
            db.q("SELECT * FROM topics WHERE ws=? ORDER BY id DESC", (workspace_id,))]


@r.post("/monitoring-topics")
def mktopic(b: Topic, u=Depends(security.need("create"))):
    _ws(b.workspace_id)
    if not b.name.strip() or not textutil.tok(b.query) or not b.sources:
        raise HTTPException(422, "Nama, query bermakna, dan minimal satu sumber wajib diisi")
    i = db.insert("INSERT INTO topics(ws,name,q,sources,every,max,exp,status,next) VALUES(?,?,?,?,?,?,?,?,?)",
                  (b.workspace_id, b.name, b.query, json.dumps(b.sources), b.every_minutes,
                   b.max_results, b.expires, "active", _now()))
    n = jobs.run_topic(db.q("SELECT * FROM topics WHERE id=?", (i,), one=True))
    audit(u, "Buat topik monitoring", b.name)
    return {"id": i, "new_items": n}


@r.post("/monitoring-topics/{tid}/{act}")
def topic_act(tid: int, act: str, u=Depends(security.need("run"))):
    t = db.q("SELECT * FROM topics WHERE id=?", (tid,), one=True)
    if not t:
        raise HTTPException(404, "Topik tidak ditemukan")
    if act == "pause":
        db.q("UPDATE topics SET status='paused' WHERE id=?", (tid,), write=True)
    elif act == "resume":
        db.q("UPDATE topics SET status='active',next=? WHERE id=?", (_now() + t["every"] * 60000, tid), write=True)
    elif act == "run":
        audit(u, "Jalankan topik", t["name"])
        return {"new_items": jobs.run_topic(t)}
    else:
        raise HTTPException(404, "Aksi tidak dikenal")
    audit(u, act + " topik", t["name"])
    return {"ok": True}


@r.delete("/monitoring-topics/{tid}")
def rm_topic(tid: int, u=Depends(security.need("run"))):
    t = db.q("SELECT * FROM topics WHERE id=?", (tid,), one=True)
    if not t:
        raise HTTPException(404, "Topik tidak ditemukan")
    db.q("DELETE FROM topics WHERE id=?", (tid,), write=True)
    audit(u, "Hapus topik", t["name"])
    return {"ok": True}


@r.post("/topic-search")
def tsearch(b: Search, u=Depends(security.need("run"))):
    _ws(b.workspace_id)
    if not textutil.tok(b.query) or not b.sources:
        raise HTTPException(422, "Isi query yang bermakna dan pilih sumber")
    lst = []
    for c in b.sources:
        if not connectors.enabled(c) or connectors.quota(c) >= config.LIM:
            continue
        connectors.use_quota(c)
        lst += connectors.fetch_conn(c, b.query, b.limit, b.days, b.workspace_id, False)
    lst = sorted(lst, key=lambda x: -(x["pub"] or 0))[:b.limit]
    res = ingest.ingest(b.workspace_id, lst, "rss", "Feed publik")
    jobs.add_job(b.workspace_id, "search", "Cari: " + b.query, ",".join(b.sources), "succeeded",
                 {"ditemukan": len(lst), "baru": res["added"]})
    audit(u, "Topic search", b.query)
    return {"query": b.query, "searched_at": _now(), "found": len(lst), **res, "results": lst,
            "note": "Hasil bukan representasi seluruh percakapan publik."}


@r.get("/collection-jobs")
def job_list(workspace_id: int, u=Depends(security.auth)):
    _ws(workspace_id)
    return [{**j, "metrics": json.loads(j["metrics"])} for j in
            db.q("SELECT * FROM jobs WHERE ws=? ORDER BY id DESC LIMIT 40", (workspace_id,))]


@r.get("/collection-jobs/{jid}")
def job(jid: int, u=Depends(security.auth)):
    j = db.q("SELECT * FROM jobs WHERE id=?", (jid,), one=True)
    if not j:
        raise HTTPException(404, "Job tidak ditemukan")
    return {**j, "metrics": json.loads(j["metrics"])}


# ---------- imports ----------
def _parse(content):
    c = content.strip()
    try:
        rows = json.loads(c) if c[:1] in "[{" else list(csv.DictReader(io.StringIO(c)))
    except Exception as e:
        raise HTTPException(422, "Format tidak dapat dibaca: " + str(e))
    if isinstance(rows, dict):
        rows = rows.get("items") or rows.get("data") or [rows]
    if not rows or not isinstance(rows[0], dict):
        raise HTTPException(422, "Berkas tidak berisi baris data")
    return rows


@r.post("/imports/preview")
def ipreview(b: Preview, u=Depends(security.need("import"))):
    rows = _parse(b.content)
    return {"columns": list(rows[0].keys()), "rows": len(rows), "sample": rows[:4]}


@r.post("/imports")
def imports(b: Imp, u=Depends(security.need("import"))):
    _ws(b.workspace_id)
    if not b.license.strip():
        raise HTTPException(422, "Lisensi/asal data wajib dicatat (FR-011)")
    m = b.mapping
    if not m.get("text"):
        raise HTTPException(422, "Pilih kolom teks konten")
    recs = [{"text": row.get(m["text"]), "title": row.get(m.get("title") or "", ""),
             "pub": row.get(m.get("pub") or ""), "url": row.get(m.get("url") or ""),
             "source": row.get(m.get("source") or "") or b.filename, "conn": "import"}
            for row in _parse(b.content)]
    res = ingest.ingest(b.workspace_id, recs, "import", b.license)
    jid = jobs.add_job(b.workspace_id, "import", b.filename, "import",
                       "failed" if res["invalid"] and not res["added"] else "partial" if res["invalid"] else "succeeded",
                       {"diimpor": res["added"], "duplikat": res["duplicates"], "error": len(res["invalid"])})
    audit(u, "Impor dataset", b.filename)
    return {"job_id": jid, **res}


# ---------- analysis ----------
@r.post("/workspaces/{wid}/analysis-jobs")
def run_analysis(wid: int, u=Depends(security.need("run"))):
    _ws(wid)
    n = analysis.analyze(wid)
    audit(u, "Jalankan analisis", f"ws {wid}: {n} klaster")
    return {"clusters": n}


@r.get("/clusters")
def clusters(workspace_id: int, u=Depends(security.auth)):
    _ws(workspace_id)
    return analysis.list_clusters(workspace_id)


@r.get("/clusters/{cid}")
def cluster(cid: str, workspace_id: int, u=Depends(security.auth)):
    _cluster(cid, workspace_id)
    return analysis.derive(cid)


@r.get("/narratives/{cid}/timeline")
def timeline(cid: str, workspace_id: int, u=Depends(security.auth)):
    _cluster(cid, workspace_id)
    return [{"id": i["id"], "at": i["pub"], "timezone": config.DISPLAY_TZ, "title": i["title"],
             "source": i["source"], "text": i["text"],
             "provenance": {"method": i["method"], "collected_at": i["collected"],
                            "license": i["license"], "url": i["url"]}}
            for i in analysis.derive(cid)["items"]]


@r.get("/narratives/{cid}/graph")
def narrative_graph(cid: str, workspace_id: int, u=Depends(security.auth)):
    _cluster(cid, workspace_id)
    return analysis.graph(cid)


@r.post("/clusters/{cid}/reviews")
def review(cid: str, workspace_id: int, b: Rev, u=Depends(security.need("review"))):
    _cluster(cid, workspace_id)
    if b.status not in config.REVIEW_STATUS:
        raise HTTPException(422, "Status review tidak valid")
    analysis.derive(cid)
    db.upsert_review(cid, b.status, b.notes, u["name"], _now())
    audit(u, "Review klaster", f"{cid}: {b.status}")
    return {"ok": True}


@r.get("/alerts")
def alerts(workspace_id: int, u=Depends(security.auth)):
    _ws(workspace_id)
    return db.q("SELECT a.*,c.title FROM alerts a LEFT JOIN clusters c ON c.id=a.cluster_id "
                "WHERE a.ws=? ORDER BY a.id DESC", (workspace_id,))


@r.get("/overview")
def overview(workspace_id: int, u=Depends(security.auth)):
    _ws(workspace_id)
    its = db.q("SELECT pub FROM contents WHERE ws=?", (workspace_id,))
    days = [sum(1 for i in its if i["pub"] and (_now() - i["pub"]) // config.DAY == 6 - k) for k in range(7)]
    cl = analysis.list_clusters(workspace_id)
    al = db.q("SELECT COUNT(*) AS n FROM alerts WHERE ws=?", (workspace_id,), one=True)["n"]
    return {"items": len(its), "clusters": len(cl), "alerts": al, "days": days, "top": cl[:4]}


@r.post("/reports")
def report(b: Rep, u=Depends(security.auth)):
    _ws(b.workspace_id)
    cl = analysis.list_clusters(b.workspace_id)
    its = db.q("SELECT pub,source FROM contents WHERE ws=?", (b.workspace_id,))
    ds = [i["pub"] for i in its if i["pub"]]
    rows = [[c["title"], c["items"], c["score"], c["mutations"], c["review"]] for c in cl]
    csvt = "klaster,item,prioritas,kandidat_perubahan,status_review\n" + "\n".join(
        ",".join('"' + str(v).replace('"', '""') + '"' for v in row) for row in rows)
    audit(u, "Buat laporan", f"ws {b.workspace_id}")
    return {"title": "Laporan analisis narasi", "created_at": _now(),
            "range": [min(ds), max(ds)] if ds else None,
            "sources": sorted({i["source"] for i in its}), "rows": rows, "csv": csvt,
            "method": "Pengumpulan hybrid ke skema kanonik, deduplikasi hash, TF-IDF cosine (ambang "
                      f"{config.SIM_THRESHOLD}), kandidat perubahan dan skor prioritas berbasis aturan transparan.",
            "limitations": "Data hanya dari sumber terhubung, bukan representasi seluruh percakapan publik. "
                           "Kemiripan bukan bukti koordinasi. Skor prioritas bukan skor kebenaran. "
                           "Semua temuan butuh review manusia."}


@r.get("/audit")
def audit_log(u=Depends(security.need("audit"))):
    return db.q("SELECT * FROM audit ORDER BY id DESC LIMIT 40")


def _now():
    return int(time.time() * 1000)