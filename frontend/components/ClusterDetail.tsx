'use client'
import { useState } from 'react'
import { api } from '../lib/api'
import { REVIEW_STATUS } from '../lib/constants'
import { useApp } from '../lib/context/AppContext'
import { fmt, pct } from '../lib/format'
import { useApi } from '../lib/hooks/useApi'
import type { ClusterDetail as DetailData, Review, TimelineItem } from '../lib/types'
import { ErrorBox, Loading } from './ui/Async'
import { Card } from './ui/Card'

function ReviewForm({
  id,
  q,
  initial,
  onSaved,
}: {
  id: string
  q: string
  initial: Review | null
  onSaved: () => void
}) {
  const { run, notify } = useApp()
  const [status, setStatus] = useState(initial?.status ?? REVIEW_STATUS[0])
  const [notes, setNotes] = useState(initial?.notes ?? '')

  return (
    <>
      <label>
        Status
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          {REVIEW_STATUS.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </label>
      <label style={{ marginTop: 8 }}>
        Catatan
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
      </label>
      <button
        className="btn"
        style={{ marginTop: 10 }}
        onClick={() =>
          run(async () => {
            await api(`/clusters/${id}/reviews${q}`, { body: { status, notes } })
            notify('Review disimpan.')
            onSaved()
          })
        }
      >
        Simpan review
      </button>
    </>
  )
}

export function ClusterDetail({ id, back }: { id: string; back: () => void }) {
  const { ws, can } = useApp()
  const q = `?workspace_id=${ws}`
  const d = useApi<DetailData>(`/clusters/${id}${q}`)
  const tl = useApi<TimelineItem[]>(`/narratives/${id}/timeline${q}`)

  if (d.error) return <ErrorBox error={d.error} retry={d.refresh} />
  if (!d.data) return <Loading />

  const c = d.data.cluster
  const rv = d.data.review

  return (
    <>
      <div>
        <button className="btn sm g" onClick={back}>
          ← Kembali
        </button>
      </div>
      <Card t={c.title}>
        <p className="mut">
          Istilah dominan: {c.terms.join(', ')}. Parameter: {c.params.algoritma}, ambang{' '}
          {c.params.ambang}, model {c.params.model}, {fmt(c.params.waktu)}.
        </p>
      </Card>
      <div className="cols">
        <div className="stack">
          <Card t="Timeline narasi">
            {tl.error ? (
              <ErrorBox error={tl.error} retry={tl.refresh} />
            ) : (
              <div className="tl">
                {(tl.data ?? []).map((x) => (
                  <div key={x.id}>
                    <b>{x.title}</b>
                    <br />
                    <span className="mut">
                      {fmt(x.at)} · {x.source} · skor {c.scores[x.id] ?? '—'}{' '}
                      <span
                        className={
                          'chip ' + (/demo/i.test(x.provenance.license) ? 'w' : 'ok')
                        }
                      >
                        {/demo/i.test(x.provenance.license) ? 'Korpus demo' : 'Feed nyata'}
                      </span>
                    </span>
                    <br />
                    {x.text}
                    <br />
                    <span className="mut">
                      Asal: {x.provenance.method}, dikumpulkan {fmt(x.provenance.collected_at)},{' '}
                      {x.provenance.license}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>
          <Card t="Kandidat perubahan klaim">
            {d.data.mutations.length ? (
              d.data.mutations.map((m, i) => (
                <div className="li" key={i}>
                  <div>
                    <b>{m.kind}</b>
                    <span className="mut">
                      {m.from} → {m.to}
                    </span>
                    {m.detail}
                  </div>
                  <span className="chip w">Kandidat</span>
                </div>
              ))
            ) : (
              <p className="mut">Tidak ada perubahan terdeteksi.</p>
            )}
            <p className="mut">
              Kandidat otomatis, bukan kesimpulan; wajib ditinjau manusia.
            </p>
          </Card>
        </div>
        <div className="stack">
          <Card t="Prioritas pemeriksaan">
            <div className="n">
              {d.data.priority.score}
              <span className="mut">/100</span>
            </div>
            {d.data.priority.factors.map((f) => (
              <div key={f.name} style={{ margin: '8px 0' }}>
                <div className="row">
                  <span>{f.name}</span>
                  <span className="sp mut">
                    bobot {f.weight} · nilai {f.value}
                  </span>
                </div>
                <div className="bar2">
                  <i style={{ width: f.value * 100 + '%' }} />
                </div>
              </div>
            ))}
            <p className="mut">{d.data.priority.note}</p>
          </Card>
          <Card t="Evidence workspace">
            {d.data.evidence.length ? (
              d.data.evidence.map((e) => (
                <div className="li" key={e.title}>
                  <div>
                    <b>{e.title}</b>
                    <span className="mut">
                      {e.publisher} · {e.type} · {fmt(e.date)}
                      <br />
                      Relevansi {pct(e.relevance)}, status: {e.stance}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <span className="chip">Belum cukup bukti</span>
            )}
          </Card>
          <Card t="Human review">
            {can('review') ? (
              <ReviewForm
                key={`${id}-${rv?.at ?? 'none'}`}
                id={id}
                q={q}
                initial={rv}
                onSaved={() => d.refresh()}
              />
            ) : (
              <p>
                {rv?.status || REVIEW_STATUS[0]}
                <br />
                <span className="mut">
                  Hanya Reviewer atau Admin yang dapat memberi status.
                </span>
              </p>
            )}
            {rv && (
              <p className="mut">
                Terakhir: {rv.by}, {fmt(rv.at)}
              </p>
            )}
          </Card>
        </div>
      </div>
    </>
  )
}