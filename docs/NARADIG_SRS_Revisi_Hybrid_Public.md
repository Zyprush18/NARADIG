# NARADIG --- SRS & Arsitektur Revisi

**Strategi pengumpulan:** Hybrid\
**Cakupan sumber:** Konten publik yang dapat diakses secara sah\
**Versi:** 1.1 --- Revisi arsitektur dan requirements\
**Tanggal:** 13 November 2026\
**Status:** Draft teknis untuk proyek kompetisi

## 1. Ringkasan keputusan

NARADIG menggunakan pendekatan **hybrid data acquisition** dengan tiga
jalur yang saling melengkapi:

1.  **Automated Monitoring:** pengambilan data terjadwal dari konektor
    sumber publik yang telah dikonfigurasi dan diizinkan.
2.  **On-Demand Topic Search:** pencarian berdasarkan topik/kata kunci
    yang diminta analis melalui konektor yang tersedia.
3.  **Dataset Import:** unggah CSV/JSON untuk riset, pengujian, data
    historis, atau sumber yang belum memiliki konektor.

Cakupan sumber adalah **konten publik**, bukan berarti semua konten
dapat diambil. Sistem hanya memproses data yang dapat diakses melalui
API resmi, RSS/feed yang diizinkan, portal terbuka, dataset berlisensi,
atau metode lain yang sesuai ketentuan sumber dan hukum yang berlaku.
Tidak ada pengambilan pesan privat, bypass login/paywall, circumvention
rate limit, atau scraping yang dilarang.

NARADIG menganalisis pola informasi, bukan menetapkan pelaku, niat, atau
kebenaran secara otomatis. Kemiripan konten bukan bukti koordinasi.

## 2. Tujuan dan ruang lingkup

### 2.1 Tujuan

-   Memantau perkembangan narasi publik dari berbagai sumber yang
    terhubung.
-   Menemukan konten yang memiliki kemiripan semantik lintas sumber.
-   Menampilkan kronologi dan kandidat perubahan klaim/narasi.
-   Menghubungkan temuan dengan sumber pemeriksaan fakta dan referensi
    resmi.
-   Membantu analis memprioritaskan pemeriksaan dengan alasan yang
    transparan.
-   Menyediakan jejak sumber, metodologi, dan review manusia.

### 2.2 Dalam ruang lingkup

-   Konektor data publik berbasis API resmi, RSS/feed yang diizinkan,
    dan sumber terbuka.
-   Monitoring terjadwal dengan topik, query, sumber, periode, dan
    frekuensi yang dikonfigurasi.
-   Pencarian topik sesuai permintaan.
-   Impor dataset CSV/JSON.
-   Validasi, normalisasi, deduplikasi, provenance.
-   NLP, embedding, clustering, timeline, graph relasi, mutation
    candidates.
-   Evidence matching, prioritas pemeriksaan, human review, alert, dan
    laporan.
-   Dashboard status konektor, status pengambilan, job analisis, dan
    kualitas data.

### 2.3 Di luar ruang lingkup

-   Mengakses konten privat atau akun tertutup.
-   Mengakali autentikasi, paywall, rate limit, atau mekanisme proteksi
    platform.
-   Menjamin cakupan seluruh unggahan dari suatu platform.
-   Mengidentifikasi individu sebagai pelaku atau menyimpulkan
    koordinasi hanya dari kemiripan.
-   Mengklasifikasikan konten sebagai hoaks secara otomatis tanpa bukti
    dan review.
-   Mengambil tindakan otomatis terhadap akun atau konten di platform.

## 3. Pengguna dan peran

  -----------------------------------------------------------------------
  Peran                               Hak dan tanggung jawab
  ----------------------------------- -----------------------------------
  Admin                               Mengelola pengguna, peran,
                                      konektor, kredensial, kebijakan,
                                      audit

  Analyst                             Membuat workspace, topik
                                      monitoring, pencarian, impor,
                                      menjalankan analisis

  Reviewer                            Menilai klaster/narasi, memeriksa
                                      bukti, memberi status dan catatan

  Viewer                              Melihat dashboard/laporan sesuai
                                      izin
  -----------------------------------------------------------------------

Semua akses menggunakan prinsip least privilege dan pemeriksaan izin di
backend.

## 4. Model akuisisi data hybrid

### 4.1 Automated Monitoring

Admin/analis mengatur sebuah monitoring job yang memuat: - Nama
pemantauan dan tujuan. - Topik/kata kunci atau query. - Konektor sumber
yang dipilih. - Rentang waktu dan jadwal. - Batas jumlah hasil dan batas
pemakaian API. - Bahasa, wilayah/topik opsional jika didukung sumber. -
Status aktif/nonaktif dan tanggal kedaluwarsa.

Scheduler menjalankan job sesuai jadwal. Connector adapter mengambil
hasil melalui antarmuka resmi/diizinkan, menormalisasi respons ke skema
internal, mencatat provenance, dan memasukkan item baru ke antrean
pemrosesan. Sistem harus menghormati quota, pagination, retry policy,
dan ketentuan sumber. Jika akses gagal atau quota habis, sistem mencatat
status dan tidak mencoba menghindari pembatasan.

### 4.2 On-Demand Topic Search

Analis memasukkan topik atau query, memilih sumber yang tersedia,
rentang waktu, dan batas hasil. Sistem menampilkan estimasi
cakupan/limit jika diketahui, menjalankan konektor, lalu menyimpan hasil
beserta query, waktu pencarian, dan sumbernya. Hasil pencarian bukan
representasi menyeluruh dari seluruh percakapan publik.

### 4.3 Dataset Import

Analis mengunggah CSV/JSON untuk data historis, eksperimen, atau sumber
yang belum terhubung. Sistem menyediakan preview, pemetaan kolom,
validasi, ringkasan kesalahan, dan pencatatan lisensi/provenance. Import
tidak boleh menghilangkan kewajiban dokumentasi asal data.

### 4.4 Konektor sumber awal

Prioritaskan konektor yang aksesnya realistis dan terdokumentasi: -
RSS/feed portal berita yang mengizinkan akses. - Portal pemeriksa fakta
dan situs resmi yang menyediakan feed/API/akses terbuka. - YouTube Data
API sesuai kebijakan dan kuota. - Reddit API sesuai persetujuan dan
ketentuan yang berlaku. - X API jika akses dan paket yang diperlukan
tersedia. - Dataset publik/berlisensi dari repositori penelitian.

Instagram/TikTok dan platform lain hanya ditambahkan jika ada API/akses
resmi yang sesuai untuk use case dan persyaratan platform. Jangan
menjanjikan integrasi sebelum aksesnya diverifikasi. Sediakan konektor
simulasi/mock untuk demo kompetisi bila akses API belum tersedia.

## 5. Alur sistem end-to-end

1.  Pengguna login dan backend memeriksa role.
2.  Pengguna membuat workspace.
3.  Pengguna memilih salah satu jalur: monitoring terjadwal, pencarian
    topik, atau impor dataset.
4.  Untuk monitoring, pengguna membuat konfigurasi topik, sumber,
    jadwal, dan batas pengambilan.
5.  Scheduler atau permintaan pengguna memicu connector orchestrator.
6.  Connector adapter memeriksa konfigurasi, kredensial, status sumber,
    quota, dan batas pengambilan.
7.  Data mentah disimpan sementara/terkendali dengan metadata
    provenance.
8.  Sistem memvalidasi skema, menghapus duplikasi, menormalkan
    teks/waktu/URL, dan mendeteksi bahasa.
9.  Item valid masuk ke antrean NLP; item invalid masuk ke laporan
    error.
10. NLP membuat embedding dan menyimpan versi model.
11. Clustering engine mengelompokkan konten; hasil memiliki parameter,
    waktu, dan metrik.
12. Narrative engine membuat kandidat ringkasan dan relasi antarversi.
13. Graph/timeline engine membangun hubungan bertipe dan kronologi.
14. Evidence service mencari referensi fact-check/sumber resmi.
15. Priority engine memberi skor prioritas pemeriksaan dengan faktor
    transparan.
16. Reviewer memeriksa hasil, bukti, konteks, dan ketidakpastian.
17. Dashboard menampilkan temuan dan alert; pengguna dapat membuat
    laporan.
18. Audit, retensi, penghapusan, dan pemantauan konektor berjalan sesuai
    kebijakan.

### 5.1 Diagram alur

``` mermaid
flowchart TD
  A[Login dan pilih workspace] --> B{Pilih jalur data}
  B --> C[Automated Monitoring]
  B --> D[On-Demand Topic Search]
  B --> E[Dataset Import]
  C --> F[Scheduler]
  D --> G[Connector Orchestrator]
  E --> H[File Validation dan Mapping]
  F --> G
  G --> I[API/RSS/Public Source Adapters]
  I --> J[Normalize Connector Response]
  H --> K[Canonical Data Schema]
  J --> K
  K --> L[Provenance, Deduplication, Validation]
  L --> M[Queue / Processing Jobs]
  M --> N[Embedding dan NLP]
  N --> O[Semantic Clustering]
  O --> P[Graph, Timeline, Mutation Candidates]
  P --> Q[Evidence Matching dan Priority]
  Q --> R[Human Review]
  R --> S[Dashboard, Alerts, Reports]
  S --> T[Audit, Retention, Monitoring]
```

## 6. Arsitektur teknis revisi

### 6.1 Komponen

  -----------------------------------------------------------------------
  Lapisan                 Teknologi usulan        Tanggung jawab
  ----------------------- ----------------------- -----------------------
  Frontend                Next.js, TypeScript,    Dashboard, konfigurasi
                          Tailwind                monitoring, pencarian,
                                                  import

  API Gateway / Backend   FastAPI, Pydantic       Auth, RBAC, workspace,
                                                  API, orkestrasi

  Connector Registry      Python adapters         Daftar konektor,
                                                  kapabilitas, status dan
                                                  versi

  Connector Workers       Python, HTTP clients    Pengambilan data sesuai
                          sesuai API              ketentuan sumber

  Scheduler               APScheduler untuk MVP;  Menjadwalkan monitoring
                          Celery Beat untuk skala 

  Queue                   Redis + Celery/RQ       Memisahkan job konektor
                                                  dan AI

  Raw/Artifact Storage    S3-compatible/local     Respons sumber yang
                          object storage          boleh disimpan, file
                                                  impor, laporan

  Processing              Python                  Normalisasi,
                                                  deduplikasi, bahasa,
                                                  provenance

  AI/NLP                  Sentence Transformers,  Embedding dan analisis
                          model multilingual      teks

  Clustering              HDBSCAN, scikit-learn   Pengelompokan dan
                                                  evaluasi

  Graph                   NetworkX; Cytoscape.js  Analisis dan
                          di UI                   visualisasi relasi

  Database                PostgreSQL + pgvector   Metadata, konten,
                                                  vektor, hasil analisis

  Observability           Structured logs +       Status job, error,
                          metrics                 latency, quota
  -----------------------------------------------------------------------

**Pilihan implementasi:** modular monolith dengan worker terpisah, bukan
microservices penuh. Pisahkan antrean `collection_jobs` dan
`analysis_jobs` agar konektor yang lambat tidak menghambat NLP.

### 6.2 Diagram arsitektur

``` mermaid
flowchart TB
  U[User] --> FE[Next.js Dashboard]
  FE --> API[FastAPI]
  API --> AUTH[Auth dan RBAC]
  API --> DB[(PostgreSQL + pgvector)]
  API --> REG[Connector Registry]
  API --> SCHED[Scheduler]
  SCHED --> CQ[Collection Queue]
  REG --> CQ
  CQ --> CW[Connector Workers]
  CW --> SRC[Official APIs / Allowed RSS / Open Sources]
  CW --> RAW[(Object Storage)]
  CW --> ING[Canonical Ingestion]
  API --> IQ[Import Queue]
  IQ --> ING
  ING --> DB
  ING --> AQ[Analysis Queue]
  AQ --> NLP[NLP and Embedding Workers]
  NLP --> CL[Clustering / Graph / Mutation]
  CL --> EV[Evidence and Priority Engine]
  EV --> DB
  API --> ALERT[Alerts and Reports]
  ALERT --> FE
```

### 6.3 Alasan pemisahan queue

-   Collection job dipengaruhi latency, quota, dan ketersediaan sumber.
-   Analysis job dapat memerlukan CPU/GPU dan waktu lebih lama.
-   Retry pengambilan tidak boleh mengulang analisis yang sudah selesai.
-   Status dan kegagalan tiap tahap harus dapat dilacak.

## 7. Requirements fungsional

Prioritas: **Must** = wajib MVP; **Should** = target setelah inti
stabil; **Could** = tambahan.

  -----------------------------------------------------------------------------------------------
  ID                Requirement       Prioritas         Kriteria penerimaan
  ----------------- ----------------- ----------------- -----------------------------------------
  FR-001            Login/logout dan  Must              Endpoint memverifikasi role dan workspace
                    RBAC                                access

  FR-002            Buat dan kelola   Must              Workspace menyimpan pemilik, deskripsi,
                    workspace                           waktu

  FR-003            Daftar dan status Must              UI menampilkan enabled/disabled,
                    konektor                            capability, last success/error

  FR-004            Konfigurasi       Must              Analis mengatur topik, sumber, jadwal,
                    automated                           periode, batas hasil
                    monitoring                          

  FR-005            Scheduler         Must              Job berjalan sesuai jadwal dan mencatat
                    menjalankan                         hasil/status
                    monitoring job                      

  FR-006            On-demand topic   Must              Pengguna mengirim query, memilih sumber
                    search                              dan batas hasil

  FR-007            Connector adapter Must              Tiap item menyimpan connector, source ID,
                    mengambil data                      waktu dan provenance
                    sesuai akses                        
                    resmi                               

  FR-008            Patuhi quota/rate Must              Sistem berhenti/menunda saat limit
                    limit/ketentuan                     tercapai; tidak melakukan bypass
                    sumber                              

  FR-009            Import CSV/JSON   Must              Preview, mapping, validasi, error report
                                                        tersedia

  FR-010            Canonical schema  Must              Hasil API/RSS/import menggunakan struktur
                    untuk semua jalur                   internal konsisten
                    data                                

  FR-011            Provenance dan    Must              Setiap item mencatat sumber, metode,
                    lisensi                             waktu, URL, lisensi/catatan

  FR-012            Validasi,         Must              Duplikat ditandai; invalid item tidak
                    normalisasi,                        masuk NLP
                    deduplikasi                         

  FR-013            Status collection Must              queued/running/succeeded/partial/failed
                    dan analysis job                    dapat dilihat

  FR-014            Embedding dan     Must              Item terkait model/version dan dimensi
                    versioning model                    vector

  FR-015            Semantic          Must              Klaster dapat ditelusuri ke item dan
                    clustering                          parameter

  FR-016            Detail klaster    Must              Menampilkan anggota, skor, sumber,
                    dan alasan                          rentang waktu
                    kemiripan                           

  FR-017            Timeline narasi   Must              Menampilkan urutan item/versi dengan zona
                                                        waktu

  FR-018            Kandidat mutation Should            Perubahan ditandai sebagai kandidat,
                    detection                           bukan kesimpulan final

  FR-019            Graph relasi      Should            Setiap edge memiliki relation_type dan
                    lintas sumber                       evidence

  FR-020            Evidence matching Should            Hasil menampilkan penerbit, tanggal, URL,
                                                        relevansi

  FR-021            Priority          Should            Faktor dan bobot dapat diperiksa; bukan
                    assessment                          truth score

  FR-022            Human review      Must              Reviewer memberi status, catatan, dan
                                                        koreksi

  FR-023            Alert berbasis    Should            Alert menyertakan alasan, sumber, waktu
                    aturan                              dan link ke temuan

  FR-024            Laporan PDF/CSV   Should            Laporan mencantumkan metode, tanggal,
                                                        sumber, batasan

  FR-025            Audit log         Must              Aksi penting dan perubahan konfigurasi
                                                        tercatat

  FR-026            Retensi dan       Must              Data dapat dihapus/di-retain sesuai
                    penghapusan                         kebijakan dan hak akses

  FR-027            Monitoring        Should            Menampilkan error rate, latency, quota
                    kesehatan                           jika disediakan API
                    konektor                            

  FR-028            Mock connector    Should            Demo dapat berjalan tanpa kredensial
                    untuk demo                          platform nyata
  -----------------------------------------------------------------------------------------------

## 8. Requirements nonfungsional

  ------------------------------------------------------------------------
  ID                      Area                    Requirement
  ----------------------- ----------------------- ------------------------
  NFR-001                 Security                Secret API disimpan di
                                                  secret
                                                  manager/environment,
                                                  tidak di repository

  NFR-002                 Privacy                 Minimalkan data pribadi;
                                                  jangan mengumpulkan
                                                  identifier yang tidak
                                                  dibutuhkan

  NFR-003                 Compliance              Ikuti ketentuan API,
                                                  lisensi, hak cipta, dan
                                                  hukum yang berlaku

  NFR-004                 Resilience              Retry terbatas dengan
                                                  exponential backoff;
                                                  hentikan saat
                                                  quota/limit

  NFR-005                 Observability           Semua job memiliki
                                                  correlation ID, status,
                                                  durasi dan error

  NFR-006                 Explainability          Hasil AI menyertakan
                                                  model, versi, parameter,
                                                  alasan dan batasan

  NFR-007                 Performance             Target demo: dashboard
                                                  umum \<3 detik pada
                                                  dataset uji yang
                                                  disepakati

  NFR-008                 Scalability             Collection worker dan
                                                  analysis worker dapat
                                                  diskalakan terpisah

  NFR-009                 Reliability             Job idempotent agar
                                                  retry tidak membuat
                                                  duplikasi

  NFR-010                 Accessibility           Navigasi keyboard, label
                                                  jelas, kontras cukup

  NFR-011                 Portability             Seluruh komponen MVP
                                                  dapat dijalankan via
                                                  Docker Compose

  NFR-012                 Localization            UI Bahasa Indonesia;
                                                  dukung teks informal dan
                                                  campuran bahasa

  NFR-013                 Auditability            Simpan versi dataset,
                                                  connector, query, model,
                                                  dan parameter

  NFR-014                 Ethical use             Tidak menyimpulkan
                                                  pelaku/koordinasi/niat
                                                  dari kemiripan konten
  ------------------------------------------------------------------------

## 9. Canonical data model

Semua sumber harus dinormalisasi ke bentuk internal yang sama. Field
minimum:

  ----------------------------------------------------------------------------------
  Field                   Tipe konseptual         Keterangan
  ----------------------- ----------------------- ----------------------------------
  id                      UUID                    ID internal

  workspace_id            UUID                    Workspace pemilik

  source_name             string                  Nama platform/penerbit

  connector_id            UUID                    Konektor yang digunakan

  source_item_id          string nullable         ID item pada sumber

  content_type            enum                    text/article/video_metadata/etc.

  text_content            text                    Teks yang boleh diproses

  title                   string nullable         Judul

  canonical_url           string nullable         URL sumber

  published_at            timestamp nullable      Waktu publikasi

  collected_at            timestamp               Waktu diperoleh

  language                string nullable         Bahasa

  content_hash            string                  Deduplikasi

  provenance_id           UUID                    Rujukan provenance

  license_note            string nullable         Lisensi/ketentuan

  collection_method       enum                    api/rss/open_dataset/import

  raw_payload_ref         string nullable         Referensi penyimpanan respons jika
                                                  diizinkan
  ----------------------------------------------------------------------------------

Simpan hanya field yang diizinkan dan dibutuhkan. Respons mentah tidak
otomatis harus disimpan; patuhi kebijakan sumber.

## 10. Rancangan database revisi

  -----------------------------------------------------------------------
  Tabel                               Fungsi dan kolom utama
  ----------------------------------- -----------------------------------
  users                               id, name, email, password_hash,
                                      role

  workspaces                          id, name, description, owner_id

  connectors                          id, name, connector_type, status,
                                      capability_json, version

  connector_credentials               id, connector_id, secret_ref,
                                      created_at

  monitoring_topics                   id, workspace_id, name,
                                      query_config_json, status

  monitoring_sources                  id, topic_id, connector_id,
                                      source_config_json

  schedules                           id, topic_id, cron_or_interval,
                                      timezone, next_run_at

  collection_jobs                     id, topic_id, connector_id, status,
                                      started_at, finished_at,
                                      metrics_json

  search_requests                     id, workspace_id, query,
                                      source_scope_json, requested_by,
                                      created_at

  imports                             id, workspace_id, file_ref,
                                      mapping_json, status,
                                      error_report_ref

  platforms                           id, name, source_type

  contents                            id, workspace_id, platform_id,
                                      connector_id, source_item_id,
                                      text_content, published_at,
                                      content_hash

  provenance                          id, content_id, canonical_url,
                                      collection_method, collected_at,
                                      license_note

  embeddings                          id, content_id, model_name,
                                      model_version, vector

  clusters                            id, workspace_id, title, summary,
                                      algorithm_version

  cluster_members                     id, cluster_id, content_id,
                                      membership_score

  narratives                          id, workspace_id, title, summary

  narrative_versions                  id, narrative_id, version_text,
                                      detected_at, parent_version_id

  content_relations                   id, source_content_id,
                                      target_content_id, relation_type,
                                      confidence, evidence_ref

  evidence_sources                    id, title, publisher, url,
                                      published_at, evidence_type

  narrative_evidence                  id, narrative_id, evidence_id,
                                      relevance_score

  risk_assessments                    id, cluster_id, score,
                                      factors_json, assessed_at

  reviews                             id, cluster_id, reviewer_id,
                                      status, notes, reviewed_at

  analysis_jobs                       id, workspace_id, job_type, status,
                                      parameters_json

  alerts                              id, cluster_id, severity, reason,
                                      created_at

  audit_logs                          id, user_id, action, entity_type,
                                      entity_id, created_at
  -----------------------------------------------------------------------

Catatan implementasi: - `connector_credentials.secret_ref` menunjuk ke
secret store; jangan simpan token plaintext di tabel biasa. - Tambahkan
unique constraint untuk `(connector_id, source_item_id)` bila source ID
tersedia. - Gunakan `content_hash` untuk deduplikasi lintas sumber
dengan kehati-hatian agar konten kutipan/konteks berbeda tidak otomatis
disatukan. - Tambahkan index pada `workspace_id`, `published_at`,
`platform_id`, `content_hash`, dan vector. - Jadwal simpan timezone
eksplisit. - Gunakan status job `queued`, `running`, `succeeded`,
`partial`, `failed`, `paused`, `rate_limited`.

## 11. Rancangan UI

### 11.1 Navigasi

-   Overview
-   Live Monitoring
-   Topic Search
-   Data Sources / Connectors
-   Data Imports
-   Collection Jobs
-   Cluster Intelligence
-   Network Graph
-   Narrative Timeline
-   Mutation Tracker
-   Evidence Workspace
-   Priority Radar
-   Alerts
-   Reports
-   Settings / Audit

### 11.2 Halaman Live Monitoring

-   Daftar topik aktif.
-   Sumber yang dipantau.
-   Jadwal dan status.
-   Terakhir berhasil mengambil data.
-   Jumlah item baru.
-   Quota/limit bila tersedia.
-   Error dan tombol pause/resume.

### 11.3 Halaman Topic Search

-   Input topik/query.
-   Pilih konektor/sumber.
-   Rentang waktu.
-   Batas hasil.
-   Catatan cakupan/limit.
-   Preview hasil dan tombol analisis.

### 11.4 Halaman Data Sources

-   Katalog konektor.
-   Status koneksi dan kapabilitas.
-   Panduan izin/kredensial.
-   Last sync, error, quota.
-   Tombol aktif/nonaktif.

### 11.5 Dashboard Intelligence

-   Tren konten teramati.
-   Klaster narasi.
-   Timeline perubahan.
-   Relasi antar-konten.
-   Evidence dan status review.
-   Peringatan beserta alasan.

## 12. Desain AI dan logika analisis

### 12.1 Clustering

1.  Normalisasi teks.
2.  Deteksi bahasa.
3.  Embedding multilingual yang dievaluasi untuk Bahasa Indonesia.
4.  Clustering (misalnya HDBSCAN).
5.  Evaluasi dengan subset berlabel manusia.
6.  Simpan model, versi, parameter, dan waktu analisis.

### 12.2 Mutation candidates

Bandingkan klaim, entitas, angka, waktu, modalitas, dan konteks.
Kategorikan perubahan sebagai penambahan, penghilangan, penguatan,
pelemahan, atau perubahan konteks. Semua hasil adalah kandidat yang
harus ditinjau.

### 12.3 Evidence matching

Cari sumber pemeriksaan fakta dan sumber resmi. Tampilkan penerbit,
tanggal, URL, relevansi, dan apakah sumber mendukung, membantah, memberi
konteks, atau belum cukup bukti. Jangan menyimpulkan hanya dari skor
semantic similarity.

### 12.4 Priority score

Skor hanya menentukan urutan pemeriksaan, bukan kebenaran. Faktor yang
dapat dipertimbangkan: urgensi, potensi dampak publik, cakupan sumber
teramati, dan ketidakpastian bukti. Tampilkan bobot dan alasan.

## 13. API utama

  Method   Endpoint                                  Fungsi
  -------- ----------------------------------------- ----------------------------
  GET      `/api/v1/connectors`                      Daftar konektor dan status
  POST     `/api/v1/monitoring-topics`               Buat topik monitoring
  GET      `/api/v1/monitoring-topics`               Daftar topik
  POST     `/api/v1/monitoring-topics/{id}/pause`    Pause monitoring
  POST     `/api/v1/monitoring-topics/{id}/resume`   Resume monitoring
  POST     `/api/v1/topic-search`                    Pencarian topik
  GET      `/api/v1/collection-jobs/{id}`            Status pengambilan
  POST     `/api/v1/imports`                         Upload dataset
  GET      `/api/v1/imports/{id}`                    Status import
  POST     `/api/v1/workspaces/{id}/analysis-jobs`   Jalankan analisis
  GET      `/api/v1/analysis-jobs/{id}`              Status analisis
  GET      `/api/v1/clusters`                        Daftar klaster
  GET      `/api/v1/clusters/{id}`                   Detail klaster
  GET      `/api/v1/narratives/{id}/timeline`        Timeline
  POST     `/api/v1/clusters/{id}/reviews`           Review
  GET      `/api/v1/alerts`                          Daftar alert
  POST     `/api/v1/reports`                         Buat laporan

## 14. Roadmap implementasi 12 minggu

  -----------------------------------------------------------------------
  Minggu                  Fokus                   Deliverable
  ----------------------- ----------------------- -----------------------
  1                       SRS, pemetaan sumber    SRS final, source
                          dan izin, definisi      register
                          skema                   

  2                       ERD, UI wireframe,      Fondasi
                          repository, Docker      

  3                       Auth, workspace,        Dasar backend
                          connector registry,     
                          mock connector          

  4                       RSS/portal terbuka      Akuisisi sumber pertama
                          connector + topic       
                          search                  

  5                       Scheduler, collection   Monitoring terjadwal
                          jobs,                   
                          status/quota/error      

  6                       CSV/JSON import,        Jalur hybrid lengkap
                          canonical schema,       
                          provenance              

  7                       Preprocessing,          Core AI
                          embedding, clustering   

  8                       Cluster detail,         Intelligence UI
                          timeline, graph         

  9                       Mutation candidates dan Analisis narasi
                          evidence matching       

  10                      Priority radar, alerts, Output analisis
                          report                  

  11                      Pengujian, keamanan,    Quality assurance
                          evaluasi model,         
                          usability               

  12                      Deployment, demo,       Release kompetisi
                          dokumentasi, pitch      
  -----------------------------------------------------------------------

## 15. Strategi pengujian

-   Connector tests: validasi pagination, quota handling, retry,
    parsing, duplicate handling.
-   Data tests: schema validation, timestamp normalization, provenance
    completeness.
-   AI tests: ARI/NMI/Silhouette untuk clustering; precision/recall/F1
    untuk mutation; Precision@K untuk retrieval.
-   System tests: scheduler, queue, idempotency, pause/resume, failed
    jobs.
-   Security tests: RBAC, secret handling, upload validation, audit.
-   Human evaluation: reviewer menilai false positive, false negative,
    dan kualitas ringkasan.
-   Data split: pisahkan berdasarkan waktu/sumber untuk mengurangi
    leakage.

## 16. Risiko dan mitigasi

  -----------------------------------------------------------------------
  Risiko                              Mitigasi
  ----------------------------------- -----------------------------------
  API tidak tersedia/mahal            Mulai dari RSS/open sources, mock
                                      connector, dan dataset legal

  Quota/rate limit                    Scheduler sadar quota, backoff,
                                      pause, observability

  Sumber tidak representatif          Tampilkan cakupan sumber dan
                                      keterbatasan

  Data berubah/dihapus di sumber      Simpan metadata/provenance sesuai
                                      izin dan kebijakan retensi

  Duplikasi lintas platform           Hash + canonicalization, tetap
                                      pertahankan sumber asal

  Bahasa informal/ironi               Evaluasi bahasa lokal dan human
                                      review

  Similarity disalahartikan sebagai   Label relasi eksplisit dan
  koordinasi                          peringatan interpretasi

  False alerts                        Threshold tervalidasi, feedback
                                      reviewer, audit
  -----------------------------------------------------------------------

## 17. Kriteria penerimaan MVP

MVP dianggap layak demo jika: 1. Pengguna dapat login dan membuat
workspace. 2. Pengguna dapat mengaktifkan satu konektor publik yang
benar-benar tersedia (misalnya RSS) dan membuat topik monitoring. 3.
Scheduler dapat menjalankan pengambilan terjadwal dan mencatat status.
4. Topic search dapat dijalankan pada konektor yang sama. 5. Dataset
CSV/JSON dapat diimpor. 6. Ketiga jalur menghasilkan canonical records
dengan provenance. 7. Data dapat dinormalisasi, di-embed, dan
dikelompokkan. 8. Dashboard menampilkan status konektor/job, klaster,
dan timeline. 9. Reviewer dapat memberi status dan catatan. 10. Laporan
menyertakan sumber, metode, rentang waktu, dan batasan.

## 18. Klaim inovasi dan batasan

Diferensiasi potensial NARADIG adalah menggabungkan monitoring
terjadwal, pencarian topik, dan impor dataset dalam satu pipeline
analisis narasi lintas sumber, dilengkapi pelacakan perubahan narasi,
provenance, evidence matching, serta review manusia.

Dokumen ini tidak mengklaim fitur tersebut belum pernah ada di dunia.
Klaim kebaruan harus dibuktikan melalui tinjauan literatur, pembandingan
produk, dan evaluasi prototipe.

## 19. Keputusan teknis yang harus dikunci

-   Konektor MVP pertama: rekomendasi RSS portal berita/sumber pemeriksa
    fakta.
-   Konektor kedua: pilih setelah memastikan akses API, biaya, dan
    ketentuan.
-   Model embedding multilingual: benchmark pada sampel Bahasa
    Indonesia.
-   Frekuensi polling: sesuai batas sumber, bukan interval agresif
    universal.
-   Retensi raw payload: hanya bila lisensi dan ketentuan mengizinkan.
-   Ukuran dataset demo: mulai kecil dan terukur, kemudian tingkatkan.
-   Definisi operasional narasi, mutation, dan evidence status.
-   Bobot priority score dan protokol review manusia.

**Rekomendasi implementasi:** bangun pipeline hybrid dengan RSS/mock
connector terlebih dahulu, lalu tambahkan konektor lain setelah akses
dan persyaratannya diverifikasi. Pastikan setiap jalur (monitoring,
pencarian, import) masuk ke canonical schema yang sama sebelum diproses
AI.
