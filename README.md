# NARADIG v1.2 (Next.js + FastAPI)

## Menjalankan (lokal, SQLite)
Backend (Python 3.10+):
    cd backend
    python -m venv .venv
    .venv\Scripts\activate          # Windows
    pip install -r requirements.txt
    copy .env.example .env          # opsional; default sudah jalan
    uvicorn main:app --reload --port 8000      # dok: http://localhost:8000/docs

Frontend (Node 18+):
    cd frontend
    npm install && npm run dev                 # http://localhost:3000
    # opsional: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 di .env.local
    # /      = landing page publik (login lewat modal di halaman ini)
    # /app   = aplikasi (tanpa sesi otomatis kembali ke /)

## Menjalankan (Docker Compose, PostgreSQL + Redis + Celery)
    docker compose up --build
    # frontend :3000, backend :8000, postgres :5432, redis :6379

## Akun demo
Kata sandi `naradig123`: admin@, analyst@, reviewer@, viewer@naradig.local

## Struktur backend
    backend/app/config.py       konstanta + env
    backend/app/db.py           SQLite/PostgreSQL, backup, migrasi skema
    backend/app/security.py     hash password, token, rate limit, pencabutan
    backend/app/connectors.py   RSS nyata + fallback korpus demo, kuota, kesehatan
    backend/app/ingest.py       canonical ingestion, dedupe, bahasa
    backend/app/analysis.py     TF-IDF clustering, mutasi, evidence, prioritas, graph
    backend/app/jobs.py         job monitoring + scheduler
    backend/app/queue.py        dispatch Celery (fallback inline)
    backend/app/api.py          endpoint /api/v1
    backend/app/main.py         assembly FastAPI
    backend/worker.py           worker Celery

## Data nyata (bukan dummy)
- Feed default: `NARADIG_RSS_FEEDS` (ANTARA, CNN Indonesia) dan `NARADIG_FACTCHECK_FEEDS` (TurnBackHoax, CekFakta).
- `GET /api/v1/feed-test` — cek semua feed (status, jumlah item, latensi, error) tanpa menyimpan.
- `POST /api/v1/admin/purge-mock` — hapus korpus demo + hasil analisisnya (Admin).
- `NARADIG_ALLOW_MOCK=false` — matikan fallback demo, hanya data feed nyata.
- `NARADIG_SIM_THRESHOLD` (default 0.25) — ambang cosine; deskripsi RSS pendek butuh ambang lebih longgar dari 0.3.
- Tombol "Tes feed nyata" ada di halaman Data Sources; badge "Feed nyata"/"Korpus demo" di hasil pencarian & timeline.
- CA root: urllib memakai `certifi` bila tersedia (memperbaiki `CERTIFICATE_VERIFY_FAILED` di Windows).

## Variabel lingkungan
Lihat `backend/.env.example`. Inti: `NARADIG_SECRET` (wajib di produksi),
`NARADIG_DB` (SQLite), `DATABASE_URL` (PostgreSQL/Supabase), `REDIS_URL`,
`SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (upload backup, opsional),
`NARADIG_RSS_FEEDS` / `NARADIG_FACTCHECK_FEEDS`, `CORS_ORIGINS`.

Produksi wajib: `NARADIG_ENV=production`, secret non-default, `DATABASE_URL` diisi —
startup akan menolak jalan bila belum.

## Perbaikan keamanan v1.2
- Password: PBKDF2-SHA256 120k putaran + salt acak per user (hash lama otomatis dimigrasi saat login).
- Login: rate limit 5 percobaan / 15 menit per IP+email (HTTP 429).
- Logout: `POST /api/v1/auth/logout` mencabut token (tabel `revoked_tokens`).
- Re-analisis tidak lagi menyisakan review lama (review dihapus bersama klaster).
- Startup menolak secret default di produksi.

## Backup
- Harian 03:00 ke `backups/` (gzip SQLite atau `pg_dump` untuk PostgreSQL), retensi 7 hari.
- Upload ke Supabase Storage bila `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` diisi.

## Catatan
- Konektor RSS memakai feed nyata; bila jaringan gagal dipakai korpus demo (mock).
- YouTube/Reddit tetap ditandai belum tersedia sampai akses API diverifikasi.
- Pengelompokan memakai TF-IDF cosine (pengganti embedding multilingual + HDBSCAN).
- Empat jalur tetap: monitoring, topic search, import, analisis — semua ke skema kanonik.
- Test: `cd backend && pytest -q`. Dependensi test butuh jaringan saat `pip install`.

## Isu tersisa
Lihat `FATAL_ISSUES.md` dan `FATAL_ISSUES_CHECKLIST.md`.