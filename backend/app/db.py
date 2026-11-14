"""Akses database: SQLite (dev) atau PostgreSQL/Supabase (produksi)."""
import gzip, json, logging, os, re, shutil, sqlite3, threading, time
from datetime import datetime, timezone

from . import config

log = logging.getLogger("naradig.db")
IS_PG = bool(config.DATABASE_URL)

_lock = threading.RLock()
_conn = None
_pool = None

SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,pw TEXT,role TEXT);
CREATE TABLE IF NOT EXISTS workspaces(id INTEGER PRIMARY KEY,name TEXT,description TEXT,owner TEXT,created INT);
CREATE TABLE IF NOT EXISTS connectors(id TEXT PRIMARY KEY,enabled INT);
CREATE TABLE IF NOT EXISTS topics(id INTEGER PRIMARY KEY,ws INT,name TEXT,q TEXT,sources TEXT,every INT,max INT,exp TEXT,status TEXT,last INT,next INT,new_total INT DEFAULT 0,err TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY,ws INT,type TEXT,name TEXT,conn TEXT,status TEXT,started INT,finished INT,metrics TEXT);
CREATE TABLE IF NOT EXISTS contents(id INTEGER PRIMARY KEY,ws INT,conn TEXT,src_id TEXT,source TEXT,title TEXT,text TEXT,url TEXT,pub INT,collected INT,lang TEXT,hash TEXT,method TEXT,license TEXT,UNIQUE(ws,hash));
CREATE TABLE IF NOT EXISTS quota(conn TEXT,day TEXT,used INT,PRIMARY KEY(conn,day));
CREATE TABLE IF NOT EXISTS clusters(id TEXT PRIMARY KEY,ws INT,title TEXT,terms TEXT,items TEXT,scores TEXT,params TEXT);
CREATE TABLE IF NOT EXISTS reviews(cluster_id TEXT PRIMARY KEY,status TEXT,notes TEXT,by TEXT,at INT);
CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY,ws INT,cluster_id TEXT,sev TEXT,reason TEXT,at INT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,t INT,user TEXT,action TEXT,entity TEXT);
CREATE TABLE IF NOT EXISTS revoked_tokens(jti TEXT PRIMARY KEY,at INT);
CREATE TABLE IF NOT EXISTS login_attempts(id INTEGER PRIMARY KEY,akey TEXT,at INT);
CREATE TABLE IF NOT EXISTS connector_health(id INTEGER PRIMARY KEY,conn TEXT,ok INT,latency_ms INT,error TEXT,at INT);
CREATE INDEX IF NOT EXISTS ix_attempts_key ON login_attempts(akey);
CREATE INDEX IF NOT EXISTS ix_health_conn ON connector_health(conn);
CREATE INDEX IF NOT EXISTS ix_contents_ws ON contents(ws);
CREATE INDEX IF NOT EXISTS ix_clusters_ws ON clusters(ws);
CREATE INDEX IF NOT EXISTS ix_alerts_ws ON alerts(ws);
"""

PG_DDL = """
CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY,name TEXT,email TEXT UNIQUE,pw TEXT,role TEXT);
CREATE TABLE IF NOT EXISTS workspaces(id SERIAL PRIMARY KEY,name TEXT,description TEXT,owner TEXT,created BIGINT);
CREATE TABLE IF NOT EXISTS connectors(id TEXT PRIMARY KEY,enabled INT);
CREATE TABLE IF NOT EXISTS topics(id SERIAL PRIMARY KEY,ws INT,name TEXT,q TEXT,sources TEXT,every INT,max INT,exp TEXT,status TEXT,last BIGINT,next BIGINT,new_total INT DEFAULT 0,err TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS jobs(id SERIAL PRIMARY KEY,ws INT,type TEXT,name TEXT,conn TEXT,status TEXT,started BIGINT,finished BIGINT,metrics TEXT);
CREATE TABLE IF NOT EXISTS contents(id SERIAL PRIMARY KEY,ws INT,conn TEXT,src_id TEXT,source TEXT,title TEXT,text TEXT,url TEXT,pub BIGINT,collected BIGINT,lang TEXT,hash TEXT,method TEXT,license TEXT,UNIQUE(ws,hash));
CREATE TABLE IF NOT EXISTS quota(conn TEXT,day TEXT,used INT,PRIMARY KEY(conn,day));
CREATE TABLE IF NOT EXISTS clusters(id TEXT PRIMARY KEY,ws INT,title TEXT,terms TEXT,items TEXT,scores TEXT,params TEXT);
CREATE TABLE IF NOT EXISTS reviews(cluster_id TEXT PRIMARY KEY,status TEXT,notes TEXT,by TEXT,at BIGINT);
CREATE TABLE IF NOT EXISTS alerts(id SERIAL PRIMARY KEY,ws INT,cluster_id TEXT,sev TEXT,reason TEXT,at BIGINT);
CREATE TABLE IF NOT EXISTS audit(id SERIAL PRIMARY KEY,t BIGINT,user TEXT,action TEXT,entity TEXT);
CREATE TABLE IF NOT EXISTS revoked_tokens(jti TEXT PRIMARY KEY,at BIGINT);
CREATE TABLE IF NOT EXISTS login_attempts(id SERIAL PRIMARY KEY,akey TEXT,at BIGINT);
CREATE TABLE IF NOT EXISTS connector_health(id SERIAL PRIMARY KEY,conn TEXT,ok INT,latency_ms INT,error TEXT,at BIGINT);
CREATE INDEX IF NOT EXISTS ix_attempts_key ON login_attempts(akey);
CREATE INDEX IF NOT EXISTS ix_health_conn ON connector_health(conn);
CREATE INDEX IF NOT EXISTS ix_contents_ws ON contents(ws);
CREATE INDEX IF NOT EXISTS ix_clusters_ws ON clusters(ws);
CREATE INDEX IF NOT EXISTS ix_alerts_ws ON alerts(ws);
"""


def connect():
    global _conn, _pool
    if IS_PG:
        import psycopg_pool
        _pool = psycopg_pool.ConnectionPool(config.DATABASE_URL, min_size=1, max_size=10,
                                            kwargs={"autocommit": True}, open=True)
        _pool.wait()
    else:
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row


def _pg_sql(sql):
    return sql.replace("?", "%s")


def q(sql, a=(), one=False, write=False):
    """Query generik. Placeholder '?' untuk kedua dialek."""
    with _lock:
        if IS_PG:
            from psycopg.rows import dict_row
            with _pool.connection() as c, c.cursor(row_factory=dict_row) as cur:
                cur.execute(_pg_sql(sql), a)
                if write:
                    return cur.rowcount
                return (cur.fetchone() if one else cur.fetchall())
        cur = _conn.execute(sql, a)
        if write:
            _conn.commit()
            return cur.lastrowid
        r = [dict(x) for x in cur.fetchall()]
        return (r[0] if r else None) if one else r


def insert(sql, a=()):
    """INSERT yang mengembalikan id baru."""
    if IS_PG:
        row = q(sql + " RETURNING id", a, one=True)
        return row["id"] if row else None
    return q(sql, a, write=True)


def q_ignore(sql, a=()):
    """INSERT IGNORE lintas dialek."""
    if IS_PG:
        return q(sql.replace("INSERT OR IGNORE", "INSERT") + " ON CONFLICT DO NOTHING", a, write=True)
    return q(sql, a, write=True)


def upsert_review(cluster_id, status, notes, by, at):
    if IS_PG:
        return q("""INSERT INTO reviews(cluster_id,status,notes,by,at) VALUES(?,?,?,?,?)
                    ON CONFLICT (cluster_id) DO UPDATE SET status=EXCLUDED.status, notes=EXCLUDED.notes,
                    by=EXCLUDED.by, at=EXCLUDED.at""", (cluster_id, status, notes, by, at), write=True)
    return q("INSERT OR REPLACE INTO reviews VALUES(?,?,?,?,?)", (cluster_id, status, notes, by, at), write=True)


def init():
    from .security import pw_hash
    from . import config as C
    with _lock:
        if IS_PG:
            try:
                q("CREATE EXTENSION IF NOT EXISTS vector")  # siap untuk embedding (FR-014)
            except Exception as e:
                log.warning("pgvector tidak tersedia: %s", e)
            stmts = [s.strip() for s in PG_DDL.split(";") if s.strip()]
            for s in stmts:
                q(s)
        else:
            _conn.executescript(SQLITE_DDL)
            _conn.commit()
        if not q("SELECT 1 FROM users", one=True):
            for n, r in [("Admin Demo", "Admin"), ("Analyst Demo", "Analyst"),
                         ("Reviewer Demo", "Reviewer"), ("Viewer Demo", "Viewer")]:
                insert("INSERT INTO users(name,email,pw,role) VALUES(?,?,?,?)",
                       (n, r.lower() + "@naradig.local", pw_hash("naradig123"), r))
        for c in C.CONN:
            q_ignore("INSERT OR IGNORE INTO connectors VALUES(?,?)", (c["id"], 1 if c["available"] else 0))


def backup():
    """Backup harian. SQLite: gzip file. PG: pg_dump bila tersedia. Upload ke Supabase bila env diisi."""
    os.makedirs(config.BACKUP_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = None
    try:
        if IS_PG:
            import subprocess
            path = os.path.join(config.BACKUP_DIR, f"naradig_{ts}.sql.gz")
            with gzip.open(path, "wb") as f:
                subprocess.run(["pg_dump", "--no-owner", config.DATABASE_URL], stdout=f, check=True, timeout=300)
        else:
            path = os.path.join(config.BACKUP_DIR, f"naradig_{ts}.db.gz")
            tmp = os.path.join(config.BACKUP_DIR, f".naradig_{ts}.db")
            dst = sqlite3.connect(tmp)  # salinan konsisten walau ada penulisan berjalan
            try:
                with _lock:
                    _conn.backup(dst)
            finally:
                dst.close()
            with open(tmp, "rb") as fin, gzip.open(path, "wb") as fout:
                shutil.copyfileobj(fin, fout)
            os.remove(tmp)
        log.info("backup dibuat: %s", path)
    except Exception as e:
        log.error("backup gagal: %s", e)
        return None
    _upload_supabase(path)
    _prune()
    return path


def _upload_supabase(path):
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and key):
        return
    try:
        from supabase import create_client
        sb = create_client(url, key)
        with open(path, "rb") as f:
            sb.storage.from_(os.getenv("SUPABASE_BUCKET", "naradig-backups")).upload(os.path.basename(path), f,
                                                                                     {"content-type": "application/gzip"})
        log.info("backup diunggah ke Supabase: %s", os.path.basename(path))
    except Exception as e:
        log.warning("upload Supabase gagal (lokal tetap tersimpan): %s", e)


def _prune():
    cut = time.time() - config.BACKUP_KEEP_DAYS * 86400
    try:
        for f in os.listdir(config.BACKUP_DIR):
            p = os.path.join(config.BACKUP_DIR, f)
            if os.path.isfile(p) and os.path.getmtime(p) < cut:
                os.remove(p)
    except OSError:
        pass