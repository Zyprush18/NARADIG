"""Konfigurasi dan konstanta NARADIG."""
import os

ENV = os.getenv("NARADIG_ENV", "development").lower()
SECRET = os.getenv("NARADIG_SECRET", "dev-secret-ganti-di-produksi")
DB_PATH = os.getenv("NARADIG_DB", "naradig.db")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
BACKUP_DIR = os.getenv("NARADIG_BACKUP_DIR", "backups")
BACKUP_KEEP_DAYS = int(os.getenv("NARADIG_BACKUP_KEEP_DAYS", "7"))
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
).split(",")
REDIS_URL = os.getenv("REDIS_URL", "").strip()
DISPLAY_TZ = os.getenv("NARADIG_TZ", "UTC")
# false = jangan pakai korpus demo saat feed nyata gagal/kosong
ALLOW_MOCK = os.getenv("NARADIG_ALLOW_MOCK", "true").lower() in ("1", "true", "yes")
# Ambang cosine clustering. Deskripsi RSS pendek -> 0.25 lebih realistis dari 0.3.
SIM_THRESHOLD = float(os.getenv("NARADIG_SIM_THRESHOLD", "0.25"))

LIM, DAY = 25, 86400000

ROLES = {
    "Admin": {"create", "run", "import", "review", "conn", "audit", "delete"},
    "Analyst": {"create", "run", "import"},
    "Reviewer": {"review"},
    "Viewer": set(),
}
STOP = set("yang dan di ke dari untuk pada dengan ini itu atau juga akan telah sudah adalah dalam oleh bagi para serta bukan tidak meski hingga bulan pekan the and for are was with".split())
REVIEW_STATUS = ["Belum ditinjau", "Perlu pemeriksaan lanjut", "Bukti cukup sebagai konteks", "Bukti membantah klaim", "Tidak relevan (false positive)"]


def validate():
    """Gagal cepat di produksi bila secret masih default (NFR-001)."""
    if ENV == "production" and SECRET.startswith("dev-secret"):
        raise RuntimeError("NARADIG_SECRET wajib di-set di produksi (jangan pakai nilai default)")
    if ENV == "production" and not DATABASE_URL:
        raise RuntimeError("DATABASE_URL wajib di-set di produksi (SQLite tidak untuk produksi)")


CONN = [
    {"id": "rss-berita", "name": "RSS Portal Berita", "cap": "RSS/feed, query kata kunci", "available": True,
     "note": "Feed publik nyata (NARADIG_RSS_FEEDS). Fallback ke korpus demo bila jaringan gagal."},
    {"id": "rss-cekfakta", "name": "RSS Pemeriksa Fakta", "cap": "RSS/feed, bukti pembanding", "available": True,
     "note": "Feed pemeriksa fakta (NARADIG_FACTCHECK_FEEDS). Fallback ke korpus demo."},
    {"id": "web-berita", "name": "Scraping Portal Berita", "cap": "HTML halaman tag/pencarian", "available": True,
     "note": "ANTARA, CNBC Indonesia, detikcom, Suara, Liputan6 (NARADIG_SCRAPE_SITES). Teks artikel penuh, tanpa API key."},
    {"id": "yt", "name": "YouTube Data API", "cap": "Metadata video, kuota harian", "available": False,
     "note": "Butuh kunci API dan kuota resmi; belum diverifikasi."},
    {"id": "reddit", "name": "Reddit API", "cap": "Pos publik", "available": False,
     "note": "Menunggu persetujuan akses dan ketentuan API."},
]

# Korpus demo: dipakai sebagai fallback mock saat feed nyata tidak tersedia.
CORP = [
    ("a1", "rss-berita", "Portal Sultra Kini", 6, "Pemerintah salurkan bantuan banjir Konawe", "Pemerintah menyalurkan 500 paket bantuan untuk korban banjir di Konawe, Sulawesi Tenggara pada Senin."),
    ("a2", "rss-berita", "Kabar Nusantara", 4, "Bantuan banjir Konawe dikabarkan 5000 paket", "Dikabarkan 5000 paket bantuan banjir Konawe disalurkan, korban banjir di Sulawesi Tenggara disebut sudah menerima bantuan."),
    ("a3", "rss-berita", "Harian Kendari", 2, "Semua korban banjir Konawe pasti sudah menerima bantuan", "Dipastikan seluruh korban banjir di Konawe sudah menerima 5000 paket bantuan pemerintah."),
    ("a4", "rss-cekfakta", "Cek Fakta Demo", 1, "Cek fakta jumlah paket bantuan banjir Konawe", "Pemeriksaan menemukan jumlah paket bantuan banjir Konawe yang tercatat 500 paket, bukan 5000; sebagian korban banjir belum menerima bantuan."),
    ("b1", "rss-berita", "Portal Sultra Kini", 5, "Harga beras naik di pasar Kendari", "Harga beras medium naik menjadi Rp14.000 per kilogram di pasar Kendari pekan ini."),
    ("b2", "rss-berita", "Kabar Nusantara", 3, "Harga beras melonjak Rp20.000, stok menipis", "Harga beras melonjak hingga Rp20.000 per kilogram di Kendari, stok beras diduga menipis di seluruh Sulawesi Tenggara."),
    ("b4", "rss-berita", "Harian Kendari", 2, "Stok beras Bulog Sultra aman", "Bulog menyatakan stok beras Sulawesi Tenggara aman hingga tiga bulan meski harga beras naik di Kendari."),
    ("b3", "rss-cekfakta", "Cek Fakta Demo", 1, "Cek fakta harga beras Rp20.000 per kilogram", "Data Bulog menunjukkan harga beras medium Rp14.000 per kilogram di Kendari; klaim harga beras Rp20.000 tidak sesuai data resmi dan stok beras aman."),
    ("c1", "rss-berita", "Warta Bahari", 4, "Tarif listrik naik bulan depan?", "Beredar kabar tarif listrik naik 20 persen bulan depan untuk pelanggan rumah tangga."),
    ("c2", "rss-berita", "Kabar Nusantara", 2, "Tarif listrik pasti naik 20 persen", "Dipastikan tarif listrik naik 20 persen bulan depan, pelanggan rumah tangga diminta bersiap."),
    ("c3", "rss-cekfakta", "Cek Fakta Demo", 1, "Cek fakta tarif listrik naik 20 persen", "PLN memastikan tarif listrik tidak naik bulan depan; kabar kenaikan tarif listrik 20 persen tidak benar."),
    ("d1", "rss-berita", "Warta Bahari", 3, "Festival Bahari Wakatobi dibuka", "Festival Bahari Wakatobi resmi dibuka dengan lomba perahu tradisional dan pameran kuliner laut."),
    ("d2", "rss-berita", "Harian Kendari", 5, "Perbaikan jalan Trans Sulawesi dimulai", "Pekerjaan perbaikan ruas jalan Trans Sulawesi di Kolaka dimulai dan ditargetkan selesai akhir tahun."),
]
EVID = [
    ("BNPB (demo)", "Laporan penyaluran bantuan banjir Konawe", 3, "Laporan penyaluran bantuan banjir Konawe mencatat 500 paket bantuan untuk korban banjir, penyaluran masih berlangsung.", "Data resmi", "konteks"),
    ("Bulog (demo)", "Informasi harga dan stok beras", 2, "Harga beras medium Rp14.000 per kilogram di Kendari, stok beras Sulawesi Tenggara aman, harga beras Rp20.000 tidak sesuai data.", "Data resmi", "membantah"),
    ("PLN (demo)", "Siaran pers tarif listrik", 2, "Tarif listrik tidak naik bulan depan, kenaikan tarif listrik 20 persen tidak benar bagi pelanggan rumah tangga.", "Data resmi", "membantah"),
]

DEFAULT_RSS = "https://www.antaranews.com/rss/terkini.xml,https://www.cnnindonesia.com/rss"
DEFAULT_FACTCHECK = "https://turnbackhoax.id/feed/,https://cekfakta.com/feed/"
RSS_FEEDS = [u for u in os.getenv("NARADIG_RSS_FEEDS", DEFAULT_RSS).split(",") if u.strip()]
FACTCHECK_FEEDS = [u for u in os.getenv("NARADIG_FACTCHECK_FEEDS", DEFAULT_FACTCHECK).split(",") if u.strip()]
# Scraper HTML: sumber nyata tanpa API key. Kosongkan untuk menonaktifkan.
SCRAPE_SITES = os.getenv("NARADIG_SCRAPE_SITES", "antara,cnbc,detik,suara,liputan6")
SCRAPE_MAX = int(os.getenv("NARADIG_SCRAPE_MAX", "6"))