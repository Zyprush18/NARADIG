'use client'
import { useApp } from '../lib/context/AppContext'
import { shortDate, fmt } from '../lib/format'
import { useApi } from '../lib/hooks/useApi'
import type { Job, OverviewData } from '../lib/types'
import { ErrorBox, Loading } from './ui/Async'
import { Card } from './ui/Card'
import { Chip } from './ui/Chip'

export function Overview() {
  const { ws, setPage } = useApp()
  const o = useApi<OverviewData>(ws ? `/overview?workspace_id=${ws}` : null, 10000)
  const jobs = useApi<Job[]>(ws ? `/collection-jobs?workspace_id=${ws}` : null, 10000)

  if (o.error) return <ErrorBox error={o.error} retry={o.refresh} />
  if (!o.data) return <Loading />

  const data = o.data
  const mx = Math.max(1, ...data.days)
  const labels = data.days.map((_, i) => shortDate(Date.now() - (6 - i) * 864e5))

  return (
    <div className="cols">
      <div className="stack">
        <div className="g3">
          {[
            ['Item terkumpul', data.items],
            ['Klaster narasi', data.clusters],
            ['Alert terbuka', data.alerts],
          ].map(([l, n]) => (
            <Card key={l as string}>
              <div className="n">{n}</div>
              <b>{l}</b>
            </Card>
          ))}
        </div>
        <Card t="Tren konten teramati (7 hari)">
          <div className="bars">
            {data.days.map((d, i) => (
              <div key={i}>
                <i
                  className={d === mx && d ? 'hi' : ''}
                  style={{ height: (d / mx) * 85 + '%' }}
                  title={d + ' item'}
                />
                {labels[i]}
              </div>
            ))}
          </div>
          <p className="mut">Bukan representasi seluruh percakapan publik.</p>
        </Card>
      </div>
      <div className="stack">
        <Card dark>
          <h2>Mulai dari jalur data</h2>
          <div className="row">
            <button className="btn sm" onClick={() => setPage('mon')}>
              Monitoring
            </button>
            <button className="btn sm g" onClick={() => setPage('search')}>
              Pencarian
            </button>
            <button className="btn sm g" onClick={() => setPage('imp')}>
              Impor
            </button>
          </div>
        </Card>
        <Card t="Prioritas pemeriksaan">
          {data.top.length ? (
            data.top.map((c) => (
              <div className="li" key={c.id}>
                <div>
                  <b>{c.title}</b>
                  <span className="mut">{c.items} item</span>
                </div>
                <span className="chip w">{c.score}</span>
              </div>
            ))
          ) : (
            <div className="note">Belum ada klaster.</div>
          )}
          <p className="mut">Skor hanya mengurutkan pemeriksaan, bukan kebenaran.</p>
        </Card>
        <Card t="Job terbaru">
          {(jobs.data ?? []).slice(0, 4).map((j) => (
            <div className="li" key={j.id}>
              <div>
                <b>{j.name}</b>
                <span className="mut">
                  {j.type} · {fmt(j.finished)}
                </span>
              </div>
              <Chip s={j.status} />
            </div>
          ))}
        </Card>
      </div>
    </div>
  )
}