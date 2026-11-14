'use client'
import { useState } from 'react'
import { api } from '../lib/api'
import { copyText } from '../lib/clipboard'
import { useApp } from '../lib/context/AppContext'
import { fmt } from '../lib/format'
import type { Report } from '../lib/types'
import { TableWrap } from './ui/Async'
import { Card } from './ui/Card'

export function Reports() {
  const { ws, run, notify } = useApp()
  const [r, setR] = useState<Report | null>(null)

  return (
    <>
      <Card t="Laporan">
        <p>Laporan memuat sumber, metode, rentang waktu, dan batasan.</p>
        <button
          className="btn"
          onClick={() =>
            run(async () => setR(await api<Report>('/reports', { body: { workspace_id: ws } })))
          }
        >
          Buat laporan
        </button>
      </Card>
      {r && (
        <Card t={r.title}>
          <p className="mut">Dibuat {fmt(r.created_at)}</p>
          <h2>Metode</h2>
          <p>{r.method}</p>
          <h2>Rentang waktu dan sumber</h2>
          <p>
            {r.range
              ? `${fmt(r.range[0])} sampai ${fmt(r.range[1])}`
              : 'Tidak ada data'}
            . Sumber: {r.sources.join(', ') || '—'}.
          </p>
          <h2>Temuan ({r.rows.length} klaster)</h2>
          <TableWrap>
            <table>
              <thead>
                <tr>
                  <th>Klaster</th>
                  <th>Item</th>
                  <th>Prioritas</th>
                  <th>Kandidat</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {r.rows.map((x, i) => (
                  <tr key={i}>
                    {x.map((v, j) => (
                      <td key={j}>{v}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </TableWrap>
          <h2>Batasan</h2>
          <p>{r.limitations}</p>
          <label>
            CSV
            <textarea readOnly value={r.csv} />
          </label>
          <div className="row" style={{ marginTop: 10 }}>
            <button
              className="btn g"
              onClick={async () => {
                const ok = await copyText(r.csv)
                notify(ok ? 'CSV disalin.' : 'Gagal menyalin; salin manual.', !ok)
              }}
            >
              Salin CSV
            </button>
            <button className="btn g" onClick={() => window.print()}>
              Cetak / simpan PDF
            </button>
          </div>
        </Card>
      )}
    </>
  )
}