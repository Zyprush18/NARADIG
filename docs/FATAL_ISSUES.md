# NARADIG — Isu Fatal (Prioritas Perbaikan)

Dibuat dari analisis kode vs SRS Revisi 1.1. Urut dari **paling fatal** (bisa bocor data, aman, produksi gagal) ke **arsitektur fundamental**.

> **Status 13 Nov 2026:** 13/13 isu sudah diimplementasikan pada refactor modular `backend/app/`.
> Lokasi baru + bukti verifikasi ada di `FATAL_ISSUES_CHECKLIST.md`. Catatan: `pytest`, `npm run build`,
> dan `docker compose up` belum dijalankan karena sandbox tanpa jaringan/dependensi.

---

## 🔴 KRITIS — Keamanan & Integritas Data (Perbaiki Dulu)

### 1. Salt Statis di Hash Password (CVE-level)
**File:** `backend/main.py:52`
```python
def pw(p): return hashlib.pbkdf2_hmac("sha256", p.encode(), b"naradig", 60000).hex()
```
- Salt `b"naradig"` sama untuk **semua user** → rainbow table trivial.
- **Fix:** Generate salt per user (16 byte), simpan `salt:hash` di kolom `pw`, verify dengan salt yang disimpan.

### 2. Review Orphan — Data Corruption Silent
**File:** `backend/main.py:163`
```python
q("DELETE FROM clusters WHERE ws=?", (ws,), write=True)
q("DELETE FROM alerts WHERE ws=?", (ws,), write=True)
# TIDAK hapus reviews!
```
- `cluster_id = "C-" + str(its[m[0]]["id"])` — content ID bisa dipakai ulang setelah re-analisis.
- Review lama menempel ke klaster baru yang beda narasi → **kesimpulan reviewer salah**.
- **Fix:** `DELETE FROM reviews WHERE cluster_id IN (SELECT id FROM clusters WHERE ws=?)` sebelum hapus clusters.

### 3. Token Tidak Bisa Dicabut (No Revocation)
**File:** `backend/main.py:74-81`
- Token = `base64(payload) + "." + HMAC(payload)`, exp 8 jam.
- Logout hanya hapus `localStorage` — token tetap valid sampai exp.
- **Fix:** Tambah tabel `revoked_tokens(token_hash, revoked_at)`, cek di `auth()`, atau pakai short expiry + refresh token.

### 4. Tidak Ada Rate Limit Login
**File:** `backend/main.py:221-226`
- Endpoint `/auth/login` tanpa throttling → brute force dictionary attack.
- **Fix:** Tambah `login_attempts` tabel / in-memory bucket per IP/email, lock 15 menit setelah 5 gagal.

---

## 🟠 TINGGI — Arsitektur & Skalabilitas (Blokir Produksi)

### 5. Konektor Hanya Mock (Pipeline Palsu)
**File:** `backend/main.py:19-37, 100-107`
- `CORP` = 13 artikel hardcoded, `fetch_conn()` filter lokal.
- RSS/YouTube/Reddit **tidak pernah dipanggil** → demo tidak mewakili real pipeline.
- **Fix:** Ganti 1 konektor (RSS portal berita yg izinkan akses) jadi nyata dulu.

### 6. SQLite + Single File — Bukan Produksi
**File:** `backend/main.py:14, 44`
- `DBP = os.getenv("NARADIG_DB", "naradig.db")`
- `sqlite3.connect(..., check_same_thread=False)` — race condition di multi-worker.
- Tidak ada migrasi skema (SRS Bab 10 butuh 22+ tabel).
- **Fix:** PostgreSQL + pgvector + Alembic migrations.

### 6b. SQLite Backup Otomatis — Belum Ada (Risk Data Loss)
**File:** `backend/main.py:44`
- File `naradig.db` single point of failure — tidak ada backup otomatis.
- Crash disk / corruption / hapus tidak sengaja = hilang semua data workspace, contents, reviews, audit.
- **Fix (MVP):** Tambah fungsi backup berkala ke Supabase Storage / S3-compatible:
  ```python
  # main.py - tambah di init() atau lifespan
  import shutil, gzip
  from datetime import datetime
  
  def backup_sqlite():
      ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
      dst = f"backups/naradig_{ts}.db.gz"
      with open(DBP, "rb") as f_in, gzip.open(dst, "wb") as f_out:
          shutil.copyfileobj(f_in, f_out)
      # upload ke Supabase Storage bucket "naradig-backups"
      # supabase.storage.from_("naradig-backups").upload(dst, open(dst, "rb"))
      # hapus backup > 7 hari
  ```
- **Jadwal:** APScheduler harian jam 03:00 UTC (di luar jam kerja).
- **Restore:** Download `.db.gz` → gunzip → replace `naradig.db` → restart backend.
- **Supabase Storage:** Gratis 1GB, cukup untuk SQLite < 100MB compressed.

### 6c. Supabase Sebagai Alternatif PostgreSQL + pgvector
**File:** (tidak ada — baru)
- Supabase = PostgreSQL managed + pgvector extension built-in + Auth + Realtime + Storage + Edge Functions.
- **Kelebihan untuk NARADIG:**
  - pgvector sudah terinstall (aktifkan via dashboard: `CREATE EXTENSION vector;`)
  - Connection pooling (PgBouncer) siap pakai
  - Storage bucket untuk backup SQLite + raw payload (FR-011, NFR-011)
  - Row Level Security (RLS) untuk multi-tenant workspace (SRS Bab 10)
  - Realtime subscription untuk UI live update (cluster baru, alert)
  - Edge Functions untuk connector workers (FR-007) tanpa server terpisah
- **Migrasi dari SQLite → Supabase:**
  1. Buat project Supabase, catat `DATABASE_URL` (postgres://...)
  2. Jalankan skema SRS Bab 10 via SQL Editor / migrasi Alembic
  3. Export data SQLite: `sqlite3 naradig.db .dump > dump.sql` → edit kompatibilitas → import ke Supabase
  4. Update `NARADIG_DB` → `DATABASE_URL` env var, ganti driver `sqlite3` → `psycopg`/`asyncpg`
  5. Aktifkan RLS policies per tabel `workspace_id`

### 7. Tidak Ada Queue — Synchronous Blocking
**File:** `backend/main.py:126-139, 176, 247, 294`
- `run_topic()`, `analyze()`, `ingest()` jalan di thread request / APScheduler.
- Job besar → timeout HTTP, blokir scheduler, tidak ada retry/backoff.
- SRS butuh: `collection_queue` + `analysis_queue` (Redis/Celery).
- **Fix:** Pisah worker, pakai Celery/RQ, idempotency key per job.

### 8. N+1 Query di `clusters()` & `overview()` — Timeout Data Nyata
**File:** `backend/main.py:295-300, 311-314`
```python
for c in q("SELECT id FROM clusters WHERE ws=?", (workspace_id,)):
    d = derive(c["id"])  # ← query berulang per klaster
```
- 100 klaster = 100× `derive()` = 100× (SELECT contents + evidence + review).
- **Fix:** Batch query — ambil semua contents + reviews + evidence sekali, join di Python.

### 9. Tidak Ada Docker Compose — Tidak Bisa Deploy Kompetisi
**File:** (tidak ada)
- SRS NFR-011: "Seluruh komponen MVP dapat dijalankan via Docker Compose".
- **Fix:** Buat `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml` dengan PostgreSQL, Redis.

---

## 🟡 SEDANG — Kualitas Kode & Observability

### 10. TypeScript & ESLint Dimatikan (No Type Safety)
**File:** `frontend/next.config.js:1`, `frontend/tsconfig.json:1`
```js
typescript: { ignoreBuildErrors: true }, eslint: { ignoreDuringBuilds: true }
```
```json
"strict": false
```
- Error tipe tidak terdeteksi saat build → bug ke produksi.
- **Fix:** Hapus ignore, set `strict: true`, perbaiki error satu-satu.

### 11. Observability Minimal (NFR-005)
**File:** `backend/main.py:124, 139`
- Hanya `jobs.metrics` JSON manual.
- Tidak ada: correlation ID, structured logging, latency, error rate per konektor.
- **Fix:** Pakai `structlog` + middleware request ID, emit metrics ke Prometheus/OTel.

### 12. Secret Management (NFR-001)
**File:** `backend/main.py:13-14`
```python
SECRET = os.getenv("NARADIG_SECRET", "dev-secret-ganti-di-produksi")
DBP = os.getenv("NARADIG_DB", "naradig.db")
```
- Default value aman untuk dev, tapi **tidak ada validasi** wajib di produksi.
- **Fix:** Startup check: `if not os.getenv("NARADIG_SECRET") or SECRET == "dev-secret...": raise RuntimeError`.

### 13. Timezone Hardcoded ke WITA (Asia/Makassar)
**File:** `backend/main.py:304`, `frontend/lib/api.ts:12`, `frontend/app/globals.css:20`
- Backend simpan epoch ms UTC (benar).
- Frontend paksa format `Asia/Makassar` → salah untuk user di zona lain.
- **Fix:** Simpan `user_timezone` di preferensi, atau gunakan `Intl.DateTimeFormat` browser default.

---

## 🟢 RENDAH — Fitur SRS Belum Ada (Backlog)

| ID SRS | Fitur | Status |
|--------|-------|--------|
| FR-014 | Embedding versioning & pgvector | ❌ TF-IDF only |
| FR-019 | Graph relasi (NetworkX + Cytoscape) | ❌ |
| FR-024 | PDF Report | ⚠️ CSV only |
| FR-026 | Retensi & penghapusan data | ❌ |
| FR-027 | Kesehatan konektor (latency, error rate) | ⚠️ Quota only |
| NFR-004 | Retry + exponential backoff | ❌ |
| NFR-009 | Idempotency key per job | ⚠️ Hash dedupe only |
| NFR-010 | Accessibility audit | ❌ |

---

## 📋 Rencana Perbaikan 1 Minggu (Critical Path)

| Hari | Fokus | Deliverable |
|------|-------|-------------|
| 1 | **Salt per user + review cleanup + login rate limit** | `main.py` patched, test login brute force |
| 2 | **Token revocation (revoked_tokens table)** | Logout server-side works |
| 3 | **Konektor RSS nyata (1 sumber)** | `fetch_conn` panggil HTTP real, parse XML |
| 4 | **Batch query `derive()` + SQLite backup otomatis** | `clusters()` < 500ms, backup harian ke Supabase Storage |
| 5 | **Supabase (PostgreSQL + pgvector) + Docker Compose** | `docker-compose up` jalan full stack ke Supabase |
| 6 | **TypeScript strict + ESLint** | `npm run build` zero error |
| 7 | **Observability + secret validation** | Structured logs, startup guard |

---

## 🚫 Jangan Dilakukan Dulu (YAGNI)

- Embedding multilingual + HDBSCAN (butuh GPU, dataset evaluasi, minggu 7-8 SRS)
- Graph relasi & Narrative versions (butuh skema DB baru, minggu 8-9)
- PDF report (bisa pakai print-to-PDF browser dulu)
- Konektor YouTube/Reddit (tunggu akses API diverifikasi, SRS 4.1)
- Self-hosted PostgreSQL + PgBouncer + pgvector (Supabase handle ini)
- Custom object storage (Supabase Storage sudah ada)

---

## Catatan Implementasi Khusus

### Perbaikan #1: Salt Per User (Contoh)
```python
# main.py
def pw_hash(p: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", p.encode(), salt, 60000)
    return salt.hex() + ":" + h.hex()

def pw_verify(p: str, stored: str) -> bool:
    salt_hex, h_hex = stored.split(":")
    h = hashlib.pbkdf2_hmac("sha256", p.encode(), bytes.fromhex(salt_hex), 60000)
    return hmac.compare_digest(h.hex(), h_hex)
```
- Migrasi: `UPDATE users SET pw = ? WHERE pw NOT LIKE '%:%'` (hash lama tidak punya `:`).

### Perbaikan #2: Review Cleanup (Satu Baris)
```python
# main.py:163 tambahkan sebelum DELETE clusters
q("DELETE FROM reviews WHERE cluster_id IN (SELECT id FROM clusters WHERE ws=?)", (ws,), write=True)
```

### Perbaikan #4: Login Rate Limit (Minimal)
```python
# main.py tambahkan di atas login()
login_bucket = {}
def check_rate(ip_email: str) -> bool:
    now = time.time()
    bucket = login_bucket.get(ip_email, [])
    bucket = [t for t in bucket if now - t < 900]  # 15 menit
    if len(bucket) >= 5: return False
    bucket.append(now)
    login_bucket[ip_email] = bucket
    return True

@app.post(P + "/auth/login")
def login(b: Login, request: Request):
    ip = request.client.host
    key = f"{ip}:{b.email.lower().strip()}"
    if not check_rate(key): raise HTTPException(429, "Terlalu banyak percobaan, coba lagi 15 menit")
    ...
```

---

### Perbaikan #6b: SQLite Backup ke Supabase Storage (Contoh)
```python
# main.py - tambah import
from supabase import create_client, Client
import gzip, shutil

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # service role untuk backend
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def backup_sqlite():
    if not supabase: return
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    local_gz = f"/tmp/naradig_{ts}.db.gz"
    with open(DBP, "rb") as f_in, gzip.open(local_gz, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    # upload
    with open(local_gz, "rb") as f:
        supabase.storage.from_("naradig-backups").upload(f"naradig_{ts}.db.gz", f, {"content-type": "application/gzip"})
    # hapus lokal
    os.remove(local_gz)
    # hapus backup lama > 7 hari (list + filter by name/date)
    # supabase.storage.from_("naradig-backups").list()...
    print(f"[backup] uploaded naradig_{ts}.db.gz")

# di lifespan startup:
scheduler.add_job(backup_sqlite, "cron", hour=3, minute=0, timezone="UTC")
```

---

### Perbaikan #6c: Koneksi ke Supabase (PostgreSQL + pgvector)
```python
# requirements.txt tambah:
# psycopg[binary,pool]>=3.1
# supabase>=2.0

# main.py - ganti sqlite3 connection
import psycopg_pool

DB_URL = os.getenv("DATABASE_URL")  # postgresql://user:pass@host:5432/db?sslmode=require
pool = psycopg_pool.ConnectionPool(DB_URL, min_size=1, max_size=10, kwargs={"autocommit": True})

def q(sql, a=(), one=False, write=False):
    with pool.connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(sql, a)
            if write: return cur.lastrowid
            r = cur.fetchall()
            return (r[0] if r else None) if one else r

# Aktifkan pgvector di Supabase SQL Editor:
# CREATE EXTENSION IF NOT EXISTS vector;
# ALTER TABLE embeddings ADD COLUMN vector vector(384);  -- atau 768/1024/1536 sesuai model
```

---

**File ini sebagai checklist.** Tandai ✅ saat selesai. Mulai dari nomor 1.