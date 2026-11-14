# Rencana Refactor Frontend NARADIG

Status: **sudah dieksekusi** (F1-F14). Lihat bagian 7 untuk hasil verifikasi.

Sumber audit: `frontend/app/page.tsx` (dulu monolit ±1319 baris, semua halaman + state + fetch di satu file).

---

## 1. Temuan fatal

### State & effect

| ID | Lokasi | Masalah | Dampak |
|----|--------|---------|--------|
| F1 | `useData` (`page.tsx` ~45-59) | Fetch tanpa `AbortController` / guard | Ganti workspace cepat → respons lama menimpa data baru |
| F2 | `useData` `.catch(() => setD(null))` | Error 401/404/timeout semuanya jadi `null` | UI "Memuat…" selamanya, error tak terlihat |
| F3 | `lib/api.ts` | Tidak ada penanganan 401 global | Token kedaluwarsa → semua tombol gagal diam-diam, user tetap di shell |
| F4 | `val()`, `checked()` (~62-67) | Form membaca DOM langsung (`getElementById`, `querySelector`) | Nilai tak terkontrol, bocor antar workspace, ID bentrok (`ms`, `lic`, `rs`, `rn`, `csv`), rawan StrictMode |
| F5 | `Search.r`, `Imports.pv/txt/res`, `Sources.ft`, form Monitoring | State lokal tidak direset saat `ws` berubah | Hasil pencarian/import workspace lama masih tampil |
| F6 | Overview 10s, Alerts 15s, Monitoring 8s | Polling tetap jalan saat tab disembunyikan | Boros; `/overview` recompute klaster tiap 10 detik |
| F7 | `loadWs` dipakai di effect `[]` | Closure menutup `ws` basi (ESLint warning nyata) | Workspace salah terpilih setelah penghapusan |
| F8 | `localStorage.clear()` (~96, ~150) | Menghapus semua key origin | Data aplikasi lain di origin sama ikut hilang |
| F9 | Root app | Tidak ada error boundary | Satu field undefined (`o.days`, `d.priority`) → layar putih |
| F10 | `ClusterDetail` | `c.scores[d.items[i]?.id]` mengandalkan urutan dua request berbeda | Skor bisa tertempel ke item yang salah |

### Lain-lain

| ID | Masalah | Dampak |
|----|---------|--------|
| F11 | `GET /clusters/{cid}`, `/narratives/{cid}/timeline`, `/graph`, `POST /clusters/{cid}/reviews` tidak scope `workspace_id` | IDOR: klaster workspace lain bisa dibaca/direview |
| F12 | `api()` mengirim `Content-Type` di GET | Preflight CORS sia-sia tiap request |
| F13 | Impor file tanpa batas ukuran (`f.text()`) | File 50 MB membekukan tab |
| F14 | `navigator.clipboard` tanpa fallback | Gagal di non-HTTPS/non-localhost |

Catatan: F11 ada di backend, ditemukan saat audit alur state frontend.

---

## 2. Struktur file target

```
frontend/app/page.tsx                 → tipis: <AppProvider><Shell/></AppProvider>
frontend/components/
  Shell.tsx              nav, pemilih workspace, flash, routing halaman
  Login.tsx
  Overview.tsx
  Monitoring.tsx
  TopicSearch.tsx
  Sources.tsx
  Imports.tsx
  Clusters.tsx           daftar + pemilihan
  ClusterDetail.tsx      timeline, mutasi, prioritas, evidence, review
  Alerts.tsx
  Reports.tsx
  Settings.tsx
  ui/Card.tsx            Card, Section
  ui/Chip.tsx            StatusChip (job, review, origin)
  ui/Table.tsx           wrapper tabel responsif
  ui/Field.tsx           label + input terkontrol
  ui/Async.tsx           Loading / Error / Empty
  ui/ErrorBoundary.tsx
frontend/lib/
  api.ts                 fetch + AbortController + interceptor 401 + batas body
  types.ts               User, Workspace, Connector, Topic, Job, Cluster, Detail, Alert, Report
  constants.ts           NAV, REVIEW_STATUS, PAGE_TITLES
  format.ts              fmt, tzLabel, pct
  hooks/useApi.ts        { data, error, loading, refresh } + abort + polling + visibility
  hooks/useSession.ts    login/logout/expire, key spesifik `naradig-*`
  hooks/useWorkspace.ts
  context/AppContext.tsx session + workspace + notify (hilangkan prop drilling `P`)
```

Aturan:
- Satu komponen = satu file, satu tanggung jawab.
- Semua fetching lewat `useApi`.
- Tidak ada `document.getElementById` setelah migrasi; form pakai `useState`.
- Tidak ada library baru.

---

## 3. Urutan kerja

Setiap langkah harus tetap lolos `npm run build`.

1. **Fondasi, UI belum berubah** — `lib/types.ts`, `lib/constants.ts`, `lib/format.ts`, `api.ts` (abort + 401 + batas body), `hooks/useApi.ts`, `ui/*` (Card, Chip, Table, Field, Async, ErrorBoundary). Perbaiki F12, F14 dasar.
2. **Shell + Login** — pecah ke file, sesi pindah ke `useSession`/`AppContext`. Perbaiki F3, F7, F8, F9.
3. **Overview, Alerts, Sources** (state paling sedikit) — terapkan F1, F2, F6.
4. **Monitoring, TopicSearch, Imports** — ganti `val()/checked()` ke state terkontrol (F4), reset saat `ws` berubah (F5), batas ukuran impor (F13).
5. **Clusters + ClusterDetail** — skor diambil dari `items`, bukan indeks (F10).
6. **Reports, Settings** — clipboard fallback (F14).
7. **Backend kecil** — scope `workspace_id` pada endpoint klaster/timeline/graph/review + test IDOR (F11).
8. **Verifikasi** — build, matriks manual, pytest.

Perkiraan hasil: 13 komponen + 8 file lib/ui; `page.tsx` dari ±900 baris jadi ±20 baris.

---

## 4. Matriks verifikasi

| Skenario | Harapan | Menutup |
|----------|---------|---------|
| Ganti workspace cepat berulang | Data selalu milik workspace aktif | F1, F5 |
| Matikan backend, buka halaman | Pesan error + tombol coba lagi, bukan "Memuat…" | F2 |
| Set token rusak di localStorage lalu klik menu | Kembali ke Login, sesi dibersihkan | F3 |
| Key lain di localStorage (mis. `foo`) | Tidak terhapus saat logout | F8 |
| Komponen dipaksa `undefined` | Error boundary tampil, bukan layar putih | F9 |
| Tab disembunyikan 1 menit | Request berhenti | F6 |
| Impor file 50 MB | Ditolak dengan pesan jelas | F13 |
| Login user A, akses `/clusters/{cid}?workspace_id=B` | 403/404 | F11 |
| `npm run build` | 0 error | semua |
| `pytest -q` | 7+ passed | F11 |

---

## 5. Keputusan yang diambil

1. Cakupan: **penuh 1-8**.
2. `ClusterDetail` tetap satu file; form review dipisah jadi `ReviewForm` (state terkontrol).
3. Perbaikan backend F11 **ikut** batch ini + test IDOR.
4. CSS: **tetap satu** `globals.css` (tidak ada CSS module).

---

## 6. Di luar cakupan

- Embedding multilingual + HDBSCAN (kualitas klaster).
- Visualisasi graph di UI.
- PDF report, konektor YouTube/Reddit.
- Full-text fetch artikel.

---

## 7. Hasil eksekusi

`app/page.tsx`: 1319 → 22 baris. 14 komponen + 9 modul lib.

| Temuan | Perbaikan |
|--------|-----------|
| F1 | `useApi` abort + flag `alive` sebelum `setData` |
| F2 | state `error` terpisah; `ErrorBox` + tombol coba lagi |
| F3 | `setUnauthorizedHandler` di `useSession`; 401 → hapus sesi → Login |
| F4 | semua form pakai `useState`; `val()`/`checked()` dihapus |
| F5 | konten halaman diberi `key={page-ws}` → remount saat workspace berganti |
| F6 | interval polling tidak memanggil saat `document.hidden` |
| F7 | `reloadWorkspaces` pakai `setWs(prev => ...)` |
| F8 | `removeItem('naradig-token')`, `removeItem('naradig-user')` |
| F9 | `ErrorBoundary` di root |
| F10 | timeline mengembalikan `id`; skor `c.scores[x.id]` |
| F11 | `_cluster(cid, workspace_id)` di detail/timeline/graph/review; `workspace_id` wajib |
| F12 | `Content-Type` hanya dikirim bila ada body |
| F13 | batas `MAX_IMPORT_BYTES` 2 MB, ditolak sebelum `f.text()` |
| F14 | `copyText()` dengan fallback `textarea` + `execCommand` |

Verifikasi:
- `npx tsc --noEmit`: 0 error.
- `npm run build`: sukses; 2 warning `react-hooks/exhaustive-deps` hilang, sisa warning font lama di `layout.tsx`.
- `pytest -q`: 8 passed (termasuk `test_cluster_endpoints_scoped_to_workspace`).
- Live: `GET /clusters/{cid}?workspace_id=1` → 200; `workspace_id=2` → 404; tanpa param → 422.