"""Worker Celery (opsional). Jalankan: celery -A worker worker -l info"""
from celery import Celery

from app import config, db, jobs

app = Celery("naradig", broker=config.REDIS_URL, backend=config.REDIS_URL)
app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")


@app.task(name="naradig.collect_topic")
def collect_topic(topic_id: int):
    db.connect()
    db.init()
    t = db.q("SELECT * FROM topics WHERE id=?", (topic_id,), one=True)
    if t:
        return jobs.run_topic(t)
    return 0


@app.task(name="naradig.backup")
def backup():
    db.connect()
    return db.backup()