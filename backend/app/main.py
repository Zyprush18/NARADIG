"""Assembly FastAPI: lifespan, scheduler, CORS, logging terstruktur."""
import json, logging, secrets, time
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import api, config, db, queue

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("naradig")


@asynccontextmanager
async def life(_):
    config.validate()
    db.connect()
    db.init()
    s = BackgroundScheduler()
    s.add_job(queue.scheduled_tick, "interval", seconds=20)
    s.add_job(db.backup, "cron", hour=3, minute=0)  # backup harian
    s.start()
    log.info(json.dumps({"event": "startup", "db": "postgres" if db.IS_PG else "sqlite",
                         "queue": queue.celery_ready()}))
    try:
        yield
    finally:
        s.shutdown()


app = FastAPI(title="NARADIG API", version="1.2", lifespan=life)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def access_log(request: Request, call_next):
    rid = request.headers.get("x-request-id") or secrets.token_hex(8)
    t0 = time.time()
    resp = await call_next(request)
    resp.headers["x-request-id"] = rid
    log.info(json.dumps({"event": "request", "rid": rid, "method": request.method,
                         "path": request.url.path, "status": resp.status_code,
                         "dur_ms": round((time.time() - t0) * 1000)}))
    return resp


app.include_router(api.r)