'use client'
import { Fragment, useEffect, useRef, useState } from 'react'
import { LoginTrigger } from './LoginModal'

interface Version {
  source: string
  text: string
  tag: string
}

interface Cluster {
  name: string
  score: number
  versions: Version[]
}

const CLUSTERS: Cluster[] = [
  {
    name: 'Bantuan banjir',
    score: 55,
    versions: [
      { source: 'Portal Sultra Kini', text: 'Bantuan [500] paket disalurkan', tag: 'Awal' },
      {
        source: 'Kabar Nusantara',
        text: 'Dikabarkan [5000] paket disalurkan',
        tag: 'Angka berubah',
      },
      {
        source: 'Harian Kendari',
        text: '[Dipastikan] seluruh korban menerima bantuan',
        tag: 'Klaim menguat',
      },
    ],
  },
  {
    name: 'Harga beras',
    score: 55,
    versions: [
      { source: 'Portal Sultra Kini', text: 'Harga beras naik jadi Rp[14.000] per kg', tag: 'Awal' },
      {
        source: 'Kabar Nusantara',
        text: 'Melonjak hingga Rp[20.000], stok [diduga] menipis',
        tag: 'Angka berubah',
      },
      {
        source: 'Cek Fakta Demo',
        text: 'Data resmi Rp14.000, klaim Rp20.000 [tidak sesuai]',
        tag: 'Koreksi muncul',
      },
    ],
  },
  {
    name: 'Tarif listrik',
    score: 50,
    versions: [
      { source: 'Warta Bahari', text: '[Beredar kabar] tarif naik 20 persen', tag: 'Awal' },
      { source: 'Kabar Nusantara', text: '[Dipastikan] tarif naik 20 persen', tag: 'Klaim menguat' },
      {
        source: 'Cek Fakta Demo',
        text: 'PLN: tarif [tidak naik] bulan depan',
        tag: 'Koreksi muncul',
      },
    ],
  },
]

/** Bagian bertanda [..] ditampilkan sebagai <mark>. */
const highlight = (text: string) =>
  text.split(/\[(.*?)\]/g).map((part, i) =>
    i % 2 === 1 ? <mark key={i}>{part}</mark> : <Fragment key={i}>{part}</Fragment>,
  )

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  r: number
}

export function Hero() {
  const [ci, setCi] = useState(0)
  const [vi, setVi] = useState(1)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const hostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const host = hostRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !host || !ctx) return

    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let w = 0
    let h = 0
    let raf = 0
    let mx = -999
    let my = -999
    let pts: Particle[] = []

    const size = () => {
      const rect = canvas.getBoundingClientRect()
      const dpr = window.devicePixelRatio || 1
      w = rect.width
      h = rect.height
      canvas.width = w * dpr
      canvas.height = h * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      const n = Math.min(70, Math.round((w * h) / 16000))
      pts = Array.from({ length: n }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 2 + 1,
      }))
    }

    const tick = () => {
      ctx.clearRect(0, 0, w, h)
      for (const p of pts) {
        if (!reduce) {
          p.x += p.vx
          p.y += p.vy
          if (p.x < 0 || p.x > w) p.vx *= -1
          if (p.y < 0 || p.y > h) p.vy *= -1
        }
      }
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i]
        for (let j = i + 1; j < pts.length; j++) {
          const b = pts[j]
          const d = Math.hypot(a.x - b.x, a.y - b.y)
          if (d < 140) {
            ctx.strokeStyle = `rgba(217,242,122,${0.22 * (1 - d / 140)})`
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.stroke()
          }
        }
        const m = Math.hypot(a.x - mx, a.y - my)
        if (m < 170) {
          ctx.strokeStyle = `rgba(138,99,238,${0.5 * (1 - m / 170)})`
          ctx.beginPath()
          ctx.moveTo(a.x, a.y)
          ctx.lineTo(mx, my)
          ctx.stroke()
        }
        ctx.fillStyle = m < 170 ? '#8a63ee' : 'rgba(217,242,122,.7)'
        ctx.beginPath()
        ctx.arc(a.x, a.y, a.r, 0, 7)
        ctx.fill()
      }
      if (!reduce) raf = requestAnimationFrame(tick)
    }

    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      mx = e.clientX - rect.left
      my = e.clientY - rect.top
    }
    const onResize = () => {
      size()
      if (reduce) tick()
    }

    size()
    tick()
    window.addEventListener('resize', onResize)
    host.addEventListener('mousemove', onMove)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', onResize)
      host.removeEventListener('mousemove', onMove)
    }
  }, [])

  const cluster = CLUSTERS[ci]

  return (
    <div className="l-hero" ref={hostRef}>
      <canvas ref={canvasRef} className="l-cv" aria-hidden="true" />
      <div className="l-wrap">
        <div>
          <h1 className="l-d">
            Satu klaim.
            <br />
            Seribu versi.
            <br />
            <em>Lacak jejaknya.</em>
          </h1>
          <p className="l-sub">
            NARADIG mengumpulkan konten dari sumber publik yang sah, mengelompokkan yang mirip, dan
            menandai perubahan klaim. Setiap temuan punya jejak data dan melewati review manusia.
          </p>
          <div className="l-row">
            <LoginTrigger className="l-btn">Masuk ke aplikasi →</LoginTrigger>
            <a className="l-btn l-ghost" href="#alur">
              Lihat alurnya
            </a>
          </div>
        </div>
        <div className="l-ex" aria-label="Contoh penjelajah klaster">
          <div className="l-tabs l-m" role="tablist" aria-label="Pilih contoh klaster">
            {CLUSTERS.map((c, i) => (
              <button
                key={c.name}
                role="tab"
                aria-selected={i === ci}
                className={i === ci ? 'on' : ''}
                onClick={() => {
                  setCi(i)
                  setVi(1)
                }}
              >
                {c.name}
              </button>
            ))}
          </div>
          <div>
            {cluster.versions.map((v, i) => (
              <button
                key={v.source}
                className={'l-ver' + (i === vi ? ' on' : '')}
                onClick={() => setVi(i)}
                aria-pressed={i === vi}
              >
                <span className="l-n">V{i + 1}</span>
                <span>
                  <small>{v.source}</small>
                  {highlight(v.text)}
                </span>
                <span className={'l-flag' + (i ? '' : ' o')}>{v.tag}</span>
              </button>
            ))}
          </div>
          <div className="l-pr">
            <span>Prioritas pemeriksaan</span>
            <div className="l-bar">
              <i style={{ width: cluster.score + '%' }} />
            </div>
            <b>{cluster.score}</b>
          </div>
          <p style={{ fontSize: 12, color: 'var(--mut)', marginTop: 12 }}>
            Data demo. Klik versi untuk melihat apa yang berubah.
          </p>
        </div>
      </div>
    </div>
  )
}