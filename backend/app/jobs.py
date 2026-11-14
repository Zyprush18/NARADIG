"""Job monitoring: eksekusi topik, scheduler tick, dispatch opsional ke Celery."""
import json
import logging

from . import config, connectors, db, ingest

log = logging.getLogger("naradig.jobs")


def add_job(ws, typ, name, conn, status, metrics):
    return db.insert("INSERT INTO jobs(ws,type,name,conn,status,started,finished,metrics) VALUES(?,?,?,?,?,?,?,?)",
                     (ws, typ, name, conn, status, _now(), _now(), json.dumps(metrics)))


def run_topic(t):
    total, status, msgs = 0, "succeeded", []
    for c in json.loads(t["sources"]):
        if not connectors.enabled(c):
            status = "partial"
            msgs.append(f"{c}: konektor nonaktif")
            continue
        if connectors.quota(c) >= config.LIM:
            status = "rate_limited"
            msgs.append(f"{c}: kuota habis, ditunda (tanpa bypass)")
            continue
        connectors.use_quota(c)
        recs = connectors.fetch_conn(c, t["q"], t["max"], 0, t["ws"], True)
        total += ingest.ingest(t["ws"], recs, "rss", "Feed publik")["added"]

    add_job(t["ws"], "monitoring", t["name"], t["sources"], status,
            {"baru": total, "catatan": "; ".join(msgs)})
    from datetime import datetime
    expired = bool(t["exp"]) and _now() > int(datetime.fromisoformat(t["exp"]).timestamp() * 1000) + config.DAY
    db.q("UPDATE topics SET last=?,next=?,new_total=new_total+?,err=?,status=? WHERE id=?",
         (_now(), _now() + t["every"] * 60000, total, "; ".join(msgs),
          "expired" if expired else t["status"], t["id"]), write=True)
    return total


def tick():
    for t in db.q("SELECT * FROM topics WHERE status='active' AND next<=?", (_now(),)):
        try:
            run_topic(t)
        except Exception as e:
            log.exception("topik %s gagal", t["id"])
            add_job(t["ws"], "monitoring", t["name"], t["sources"], "failed", {"error": str(e)})


def _now():
    import time
    return int(time.time() * 1000)