'use client'
import { useEffect, useState } from 'react'

const KEY = 'naradig-landing-seen'

export function LoadingScreen() {
  const [hidden, setHidden] = useState(false)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (sessionStorage.getItem(KEY)) {
      setHidden(true)
      return
    }
    let v = 0
    const tick = setInterval(() => {
      if (v >= 90) return
      v = v + (90 - v) * 0.08 + 0.4
      setProgress(v)
    }, 90)
    const finish = setTimeout(
      () => {
        clearInterval(tick)
        setProgress(100)
        sessionStorage.setItem(KEY, '1')
        setTimeout(() => setHidden(true), 350)
      },
      window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 300 : 1400,
    )
    return () => {
      clearInterval(tick)
      clearTimeout(finish)
    }
  }, [])

  if (hidden) return null

  return (
    <div className="l-pre" role="status" aria-live="polite" aria-label="Memuat NARADIG">
      <div className="l-pl">
        <svg className="l-nw" viewBox="0 0 120 60" aria-hidden="true">
          <path d="M20 40 60 14 100 38M60 14V50M20 40 60 50 100 38" />
          <circle cx="20" cy="40" r="5" />
          <circle cx="60" cy="14" r="7" />
          <circle cx="100" cy="38" r="5" />
          <circle cx="60" cy="50" r="4" />
        </svg>
        <div className="l-lg">
          <b />
          NARADIG
        </div>
        <div className="l-tr">
          <i style={{ width: progress + '%' }} />
        </div>
        <div className="l-ct2 l-m">
          <span>Memuat</span>
          <span>{Math.round(progress)}%</span>
        </div>
      </div>
    </div>
  )
}