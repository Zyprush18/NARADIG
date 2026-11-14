"""Analisis: TF-IDF cosine clustering, kandidat perubahan klaim, evidence, prioritas."""
import json, math, re

from fastapi import HTTPException

from . import config, db, textutil

TH = config.SIM_THRESHOLD
ABS = r"\b(pasti|dipastikan|seluruh|semua)\b"
HEDGE = r"\b(diduga|dikabarkan|disebut|beredar|kemungkinan)\b"
CORR = r"\b(bukan|tidak benar|tidak sesuai|tidak naik)\b"


def analyze(ws):
    its = db.q("SELECT * FROM contents WHERE ws=?", (ws,))
    docs = [textutil.tok(i["title"] + " " + i["text"]) for i in its]
    N = len(its)
    df = {}
    for d in docs:
        for w in set(d):
            df[w] = df.get(w, 0) + 1
    vec = []
    for d in docs:
        v = {}
        for w in d:
            v[w] = v.get(w, 0) + 1
        for w in v:
            v[w] *= math.log(1 + N / df[w])
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        vec.append({w: x / norm for w, x in v.items()})
    cos = lambda a, b: sum(x * b[w] for w, x in a.items() if w in b)

    parent = list(range(N))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(N):
        for j in range(i + 1, N):
            if cos(vec[i], vec[j]) >= TH:
                parent[find(i)] = find(j)

    groups = {}
    for i in range(N):
        groups.setdefault(find(i), []).append(i)

    # Urutan hapus penting: review dulu selama cluster lama masih ada (cegah review orphan).
    db.q("DELETE FROM reviews WHERE cluster_id IN (SELECT id FROM clusters WHERE ws=?)", (ws,), write=True)
    db.q("DELETE FROM alerts WHERE ws=?", (ws,), write=True)
    db.q("DELETE FROM clusters WHERE ws=?", (ws,), write=True)

    made = 0
    for g in groups.values():
        if len(g) < 2:
            continue
        m = sorted(g, key=lambda i: its[i]["pub"] or 0)
        sm = {}
        for i in g:
            for w, x in vec[i].items():
                sm[w] = sm.get(w, 0) + x
        sc = {its[i]["id"]: round(sum(cos(vec[i], vec[j]) for j in g if j != i) / (len(g) - 1), 2) for i in g}
        cid = "C-" + str(its[m[0]]["id"])
        row = (cid, ws, its[m[0]]["title"], json.dumps(sorted(sm, key=sm.get, reverse=True)[:8]),
               json.dumps([its[i]["id"] for i in m]), json.dumps(sc),
               json.dumps({"algoritma": "TF-IDF cosine + single-linkage", "ambang": TH,
                           "model": "tfidf-v1 (pengganti embedding multilingual)", "waktu": _now()}))
        db.q("INSERT INTO clusters VALUES(?,?,?,?,?,?,?)", row, write=True)
        made += 1
        core = _core({"id": cid, "ws": ws, "title": row[2], "terms": row[3], "items": row[4],
                      "scores": row[5], "params": row[6]}, [its[i] for i in m], None)
        if core["priority"]["score"] >= 55:
            db.q("INSERT INTO alerts(ws,cluster_id,sev,reason,at) VALUES(?,?,?,?,?)",
                 (ws, cid, "Tinggi", f'Skor prioritas {core["priority"]["score"]}/100 '
                  '(urgensi, dampak, cakupan, ketidakpastian bukti).', _now()), write=True)
        if len(core["mutations"]) >= 2:
            db.q("INSERT INTO alerts(ws,cluster_id,sev,reason,at) VALUES(?,?,?,?,?)",
                 (ws, cid, "Sedang", f'{len(core["mutations"])} kandidat perubahan klaim antarversi; '
                  'perlu ditinjau manusia.', _now()), write=True)

    from .jobs import add_job
    add_job(ws, "analysis", "Analisis klaster", "tfidf-v1", "succeeded", {"item": N, "klaster": made})
    return made


def list_clusters(ws):
    """Loop klaster tanpa N+1: 3 query total untuk semua klaster (bukan 2 query x N)."""
    cl = db.q("SELECT * FROM clusters WHERE ws=? ORDER BY id", (ws,))
    if not cl:
        return []
    its = {i["id"]: i for i in db.q("SELECT * FROM contents WHERE ws=?", (ws,))}
    ids = [c["id"] for c in cl]
    rv = {r["cluster_id"]: r for r in db.q(
        f"SELECT * FROM reviews WHERE cluster_id IN ({','.join('?' * len(ids))})", ids)} if ids else {}
    out = []
    for c in cl:
        items = [its[i] for i in json.loads(c["items"]) if i in its]
        d = _core(c, items, rv.get(c["id"]))
        out.append({"id": c["id"], "title": c["title"], "items": len(items),
                    "sources": len({i["source"] for i in items}),
                    "mutations": len(d["mutations"]), "score": d["priority"]["score"],
                    "review": (d["review"] or {}).get("status", config.REVIEW_STATUS[0])})
    return sorted(out, key=lambda x: -x["score"])


def derive(cid):
    c = db.q("SELECT * FROM clusters WHERE id=?", (cid,), one=True)
    if not c:
        raise HTTPException(404, "Klaster tidak ditemukan")
    ids = json.loads(c["items"])
    rows = {r["id"]: r for r in db.q(
        f"SELECT * FROM contents WHERE id IN ({','.join('?' * len(ids))})", ids)} if ids else {}
    items = [rows[i] for i in ids if i in rows]
    rv = db.q("SELECT * FROM reviews WHERE cluster_id=?", (cid,), one=True)
    return _core(c, items, rv)


def _core(c, items, review):
    mut = []
    for a, b in zip(items, items[1:]):
        A, B = a["title"] + " " + a["text"], b["title"] + " " + b["text"]
        na, nb = textutil.nums(A), textutil.nums(B)
        ta, tb = set(textutil.tok(A)), set(textutil.tok(B))
        add = lambda k, d: mut.append({"from": a["source"], "to": b["source"], "kind": k, "detail": d})
        if na and any(n not in na for n in nb):
            add("Perubahan angka", f'{", ".join(dict.fromkeys(na))} → {", ".join(dict.fromkeys(nb))}')
        if re.search(ABS, B, re.I) and not re.search(ABS, A, re.I):
            add("Penguatan klaim", "Muncul kata kepastian atau generalisasi")
        if re.search(HEDGE, B, re.I) and not re.search(HEDGE, A, re.I):
            add("Pelemahan klaim", "Muncul kata keraguan atau atribusi tidak pasti")
        if re.search(CORR, B, re.I) and not re.search(CORR, A, re.I):
            add("Perubahan konteks", "Muncul bantahan atau koreksi eksplisit")
        if len(tb - ta) >= 4:
            add("Penambahan", "Istilah baru: " + ", ".join(list(tb - ta)[:5]))
        if len(ta - tb) >= 4:
            add("Penghilangan", "Istilah hilang: " + ", ".join(list(ta - tb)[:5]))

    T = set(json.loads(c["terms"]))
    ev = []
    for e in config.EVID:
        r = len(T & set(textutil.tok(e[1] + " " + e[3]))) / max(1, len(T))
        if r >= .25:
            ev.append({"publisher": e[0], "title": e[1], "date": _now() - e[2] * config.DAY,
                       "type": e[4], "stance": e[5], "relevance": round(r, 2)})
    ev.sort(key=lambda x: -x["relevance"])

    n = len(items)
    srcs = len({x["source"] for x in items})
    recent = sum(1 for x in items if x["pub"] and _now() - x["pub"] <= 3 * config.DAY) / max(1, n)
    best = ev[0]["relevance"] if ev else 0
    fac = [{"name": "Urgensi (aktivitas 3 hari terakhir)", "value": round(recent, 2), "weight": .3},
           {"name": "Potensi dampak (jumlah item)", "value": round(min(1, n / 6), 2), "weight": .3},
           {"name": "Cakupan sumber teramati", "value": round(min(1, srcs / 4), 2), "weight": .2},
           {"name": "Ketidakpastian bukti", "value": round(1 - min(1, best * 1.6), 2), "weight": .2}]
    cluster = dict(c)
    cluster.update(terms=sorted(T), items=items, scores=json.loads(c["scores"]),
                   params=json.loads(c["params"]))
    return {"cluster": cluster, "items": items, "mutations": mut, "evidence": ev,
            "priority": {"score": round(100 * sum(f["value"] * f["weight"] for f in fac)), "factors": fac,
                         "note": "Skor hanya mengurutkan pemeriksaan, bukan menilai kebenaran."},
            "review": review}


def graph(cid):
    """Graph relasi bertipe (FR-019), tanpa dependensi NetworkX: edge = kemiripan teramati."""
    d = derive(cid)
    sc = d["cluster"]["scores"]
    nodes = [{"id": i["id"], "label": i["source"], "title": i["title"]} for i in d["items"]]
    edges = []
    for a in d["items"]:
        for b in d["items"]:
            if a["id"] >= b["id"]:
                continue
            w = round((sc.get(a["id"], 0) + sc.get(b["id"], 0)) / 2, 2)
            edges.append({"source": a["id"], "target": b["id"], "relation_type": "narasi_mirip",
                          "weight": w, "evidence_ref": cid})
    return {"nodes": nodes, "edges": edges,
            "note": "Relasi hanya kemiripan teks teramati, bukan bukti koordinasi."}


def _now():
    import time
    return int(time.time() * 1000)