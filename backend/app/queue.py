"""Dispatch job: Celery+Redis bila tersedia, jika tidak eksekusi inline (fallback aman)."""
import logging

from . import config, db, jobs

log = logging.getLogger("naradig.queue")


def celery_ready():
    if not config.REDIS_URL:
        return False
    try:
        import celery  # noqa: F401
        import redis  # noqa: F401
        return True
    except Exception:
        return False


def dispatch_topic(topic):
    """Kirim job pengumpulan ke worker. Return True bila masuk queue."""
    if celery_ready():
        try:
            from worker import app as cel
            cel.send_task("naradig.collect_topic", args=[topic["id"]])
            return True
        except Exception as e:
            log.warning("queue gagal, fallback inline: %s", e)
    jobs.run_topic(topic)
    return False


def scheduled_tick():
    for t in db.q("SELECT * FROM topics WHERE status='active' AND next<=?", (jobs._now(),)):
        try:
            dispatch_topic(t)
        except Exception as e:
            log.exception("topik %s gagal", t["id"])
            jobs.add_job(t["ws"], "monitoring", t["name"], t["sources"], "failed", {"error": str(e)})