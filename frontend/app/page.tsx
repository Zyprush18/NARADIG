import './landing.css'
import { Hero } from '../components/landing/Hero'
import { LoadingScreen } from '../components/landing/LoadingScreen'
import { LoginModal, LoginTrigger } from '../components/landing/LoginModal'
import { ScoreLab } from '../components/landing/ScoreLab'

export const metadata = {
  title: 'NARADIG | Satu Klaim, Seribu Versi',
  description:
    'NARADIG melacak bagaimana klaim menyebar dan berubah lintas sumber publik, dengan jejak data dan review manusia.',
}

const STEPS = [
  { t: 'Kumpulkan', d: 'Monitoring terjadwal, pencarian topik, atau impor CSV/JSON.' },
  { t: 'Normalisasi', d: 'Satu skema, deduplikasi, dan catatan asal serta lisensi.' },
  { t: 'Kelompokkan', d: 'Konten yang mirip dijadikan klaster dengan timeline.' },
  { t: 'Tandai', d: 'Kandidat perubahan klaim dan bukti pembanding dicocokkan.' },
  { t: 'Tinjau', d: 'Reviewer menetapkan status. Laporan memuat batasannya.' },
]

const PRINCIPLES = [
  {
    n: '01',
    t: 'Jejak sumber',
    d: 'Asal, waktu kumpul, metode, dan lisensi tercatat di setiap item.',
  },
  {
    n: '02',
    t: 'Skor terbuka',
    d: 'Faktor dan bobot terlihat. Skor bukan penilaian kebenaran.',
  },
  {
    n: '03',
    t: 'Manusia memutuskan',
    d: 'Sistem hanya mengusulkan kandidat. Status ditetapkan reviewer.',
  },
  {
    n: '04',
    t: 'Sumber yang sah',
    d: 'API resmi, RSS, dan dataset berlisensi. Bukan representasi seluruh percakapan publik.',
  },
]

const WORDS = [
  'RSS / Feed',
  'CSV',
  'JSON',
  'Klaster narasi',
  'Timeline',
  'Kandidat perubahan',
  'Bukti pembanding',
  'Skor prioritas',
  'Review manusia',
  'Audit log',
  'Laporan',
]
const TOKENS = WORDS.flatMap((w) => [w, '/'])
const MARQUEE = [...TOKENS, ...TOKENS]

const SPARK = [30, 55, 40, 70, 100, 60, 45]

export default function LandingPage() {
  return (
    <div className="lp">
      <LoadingScreen />
      <LoginModal />
      <header className="l-nav">
        <a className="l-logo" href="#top" aria-label="NARADIG beranda">
          <b />
          NARADIG
        </a>
        <nav aria-label="Menu utama">
          <a href="#alur">Alur</a>
          <a href="#fitur">Fitur</a>
          <a href="#skor">Skor</a>
          <a href="#prinsip">Prinsip</a>
        </nav>
        <LoginTrigger className="l-btn l-sm">Masuk</LoginTrigger>
      </header>

      <main id="top">
        <Hero />

        <div className="l-mq l-m" aria-hidden="true">
          <div>
            {MARQUEE.map((w, i) => (
              <span key={i} className={i % 3 === 2 ? 'l-hi' : undefined}>
                {w}
              </span>
            ))}
          </div>
        </div>

        <section className="l-paper" id="alur">
          <div className="l-wrap">
            <p className="l-m" style={{ color: '#5c5c68', marginBottom: 18 }}>
              Cara kerja
            </p>
            <h2 className="l-d">Dari data mentah ke temuan yang bisa diperiksa</h2>
            <div className="l-steps">
              {STEPS.map((s) => (
                <div className="l-st" key={s.t}>
                  <h3>{s.t}</h3>
                  <p>{s.d}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="fitur">
          <div className="l-wrap">
            <p className="l-m" style={{ color: 'var(--lime)', marginBottom: 18 }}>
              Fitur
            </p>
            <h2 className="l-d">Semua yang dibutuhkan tim verifikasi, tanpa klaim berlebihan</h2>
            <div className="l-bento">
              <div className="l-tile l-t1">
                <h3>Live Monitoring</h3>
                <p>
                  Topik dipantau terjadwal. Kuota konektor dihormati, dan job ditunda saat batas
                  tercapai, tanpa upaya melewatinya.
                </p>
                <div className="l-spark" aria-hidden="true">
                  {SPARK.map((h, i) => (
                    <i key={i} style={{ height: h + '%' }} />
                  ))}
                </div>
              </div>
              <div className="l-tile l-t2">
                <h3>Topic Search</h3>
                <p>Cari sesuai permintaan. Query dan waktu pencarian tersimpan.</p>
                <div className="l-mock" aria-hidden="true">
                  <div>
                    <span>query</span>
                    <b>banjir bantuan</b>
                  </div>
                  <div>
                    <span>rentang</span>
                    <b>7 hari</b>
                  </div>
                </div>
              </div>
              <div className="l-tile l-t3">
                <h3>Impor Dataset</h3>
                <p>Petakan kolom, validasi, catat lisensi.</p>
                <div className="l-mock" aria-hidden="true">
                  <div>
                    <span>isi</span>
                    <b>→ teks</b>
                  </div>
                  <div>
                    <span>tanggal</span>
                    <b>→ terbit</b>
                  </div>
                </div>
              </div>
              <div className="l-tile l-t4">
                <h3>Klaster &amp; Timeline</h3>
                <p>Versi klaim disusun menurut waktu terbit.</p>
                <div className="l-dotl" aria-hidden="true">
                  <i />
                  <s />
                  <i />
                  <s />
                  <i />
                  <s />
                  <i />
                </div>
              </div>
              <div className="l-tile l-t5">
                <h3>Review &amp; Audit</h3>
                <p>Status, catatan, dan riwayat aksi tercatat per pengguna.</p>
                <div className="l-mock" aria-hidden="true">
                  <div>
                    <span>Reviewer</span>
                    <b>Bukti membantah</b>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="skor" style={{ background: 'var(--ink2)' }}>
          <div className="l-wrap l-lab">
            <div>
              <p className="l-m" style={{ color: 'var(--lime)', marginBottom: 18 }}>
                Skor transparan
              </p>
              <h2 className="l-d" style={{ fontSize: 'clamp(34px,4.4vw,60px)' }}>
                Bongkar sendiri cara skornya dihitung
              </h2>
              <p className="l-lede">
                Prioritas pemeriksaan adalah jumlah empat faktor berbobot. Geser nilainya dan lihat
                hasilnya. Skor ini hanya mengurutkan apa yang diperiksa lebih dulu, bukan menilai
                benar atau salah.
              </p>
            </div>
            <ScoreLab />
          </div>
        </section>

        <section className="l-lime" id="prinsip">
          <div className="l-wrap">
            <p className="l-m" style={{ marginBottom: 18 }}>
              Prinsip
            </p>
            <h2 className="l-d">Kemiripan konten bukan bukti koordinasi.</h2>
            <div className="l-pg">
              {PRINCIPLES.map((p) => (
                <div key={p.n}>
                  <span className="l-m">{p.n}</span>
                  <h3>{p.t}</h3>
                  <p>{p.d}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="masuk" className="l-cta">
          <div className="l-wrap">
            <h2 className="l-d" style={{ margin: '0 auto' }}>
              Mulai dari satu topik.
            </h2>
            <p className="l-lede" style={{ margin: '20px auto 34px' }}>
              Masuk, buat workspace, lalu pantau isu pertama Anda.
            </p>
            <LoginTrigger className="l-btn">Masuk ke aplikasi →</LoginTrigger>
          </div>
        </section>
      </main>

      <footer>
        <div className="l-wrap">
          <span>
            © 2026 NARADIG. Data hanya dari sumber terhubung dan bukan representasi seluruh
            percakapan publik.
          </span>
          <nav aria-label="Menu footer">
            <a href="#alur">Alur</a>
            <a href="#fitur">Fitur</a>
            <a href="#prinsip">Prinsip</a>
            <LoginTrigger>Masuk</LoginTrigger>
          </nav>
        </div>
      </footer>
    </div>
  )
}