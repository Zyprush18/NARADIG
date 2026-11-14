'use client'
import { useState } from 'react'

const FACTORS = [
  { label: 'Urgensi, aktivitas 3 hari terakhir (bobot 0,3)', weight: 0.3, init: 80 },
  { label: 'Potensi dampak, jumlah item (bobot 0,3)', weight: 0.3, init: 70 },
  { label: 'Cakupan sumber teramati (bobot 0,2)', weight: 0.2, init: 50 },
  { label: 'Ketidakpastian bukti (bobot 0,2)', weight: 0.2, init: 40 },
]

export function ScoreLab() {
  const [values, setValues] = useState(FACTORS.map((f) => f.init))
  const score = Math.round(
    values.reduce((sum, v, i) => sum + (v / 100) * FACTORS[i].weight, 0) * 100,
  )

  return (
    <div className="l-sl">
      {FACTORS.map((f, i) => (
        <label key={f.label}>
          {f.label}
          <span>
            <input
              type="range"
              min="0"
              max="100"
              value={values[i]}
              onChange={(e) =>
                setValues((prev) => prev.map((v, j) => (j === i ? +e.target.value : v)))
              }
            />
            <b>{(values[i] / 100).toFixed(2)}</b>
          </span>
        </label>
      ))}
      <div className="l-score">
        <b>{score}</b>
        <span>/ 100 skor prioritas</span>
      </div>
    </div>
  )
}