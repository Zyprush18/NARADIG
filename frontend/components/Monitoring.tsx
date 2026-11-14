'use client'
import { useState } from 'react'
import { api } from '../lib/api'
import { useApp } from '../lib/context/AppContext'
import { fmt } from '../lib/format'
import { useApi } from '../lib/hooks/useApi'
import type { Connector, Job, MonitoringTopic } from '../lib/types'
import { ErrorBox, Empty, Loading, TableWrap } from './ui/Async'
import { Card } from './ui/Card'
import { Chip } from './ui/Chip'
import { Field } from './ui/Field'
import { availableSources, SourcePicker } from './ui/SourcePicker'

function JobTable({ jobs }: { jobs?: Job[] | null }) {
  return (
    <TableWrap>
      <table>
        <thead>
          <tr>
            <th>Job</th>
            <th>Jenis</th>
            <th>Selesai</th>
            <th>Hasil</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {(jobs ?? []).map((j) => (
            <tr key={j.id}>
              <td>{j.name}</td>
              <td>{j.type}</td>
              <td>{fmt(j.finished)}</td>
              <td>
                {Object.entries(j.metrics)
                  .filter((e) => e[1] !== '')
                  .map((e) => e[0] + ': ' + e[1])
                  .join('; ')}
              </td>
              <td>
                <Chip s={j.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableWrap>
  )
}

export function Monitoring() {
  const { ws, can, run, notify } = useApp()
  const topics = useApi<MonitoringTopic[]>(ws ? `/monitoring-topics?workspace_id=${ws}` : null, 8000)
  const jobs = useApi<Job[]>(ws ? `/collection-jobs?workspace_id=${ws}` : null, 8000)
  const conns = useApi<Connector[]>('/connectors')

  const [name, setName] = useState('')
  const [query, setQuery] = useState('')
  const [every, setEvery] = useState('60')
  const [max, setMax] = useState('3')
  const [expires, setExpires] = useState('')
  const [sources, setSources] = useState<string[] | null>(null)
  const effSources = sources ?? availableSources(conns.data)

  const act = (id: number, a: string) =>
    run(async () => {
      const r = await api<{ new_items: number }>(`/monitoring-topics/${id}/${a}`, {
        method: 'POST',
      })
      notify(a === 'run' ? `${r.new_items} item baru.` : 'Status diperbarui.')
      topics.refresh()
      jobs.refresh()
    })

  const save = () =>
    run(async () => {
      if (!name.trim() || !query.trim()) throw new Error('Nama dan query wajib diisi.')
      const r = await api<{ new_items: number }>('/monitoring-topics', {
        body: {
          workspace_id: ws,
          name: name.trim(),
          query: query.trim(),
          sources: effSources,
          every_minutes: +every,
          max_results: +max || 3,
          expires: expires || null,
        },
      })
      notify(`Topik disimpan: ${r.new_items} item baru.`)
      setName('')
      setQuery('')
      topics.refresh()
      jobs.refresh()
    })

  return (
    <>
      {can('create') && (
        <Card t="Topik monitoring baru">
          <div className="form">
            <Field label="Nama">
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </Field>
            <Field label="Query">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="banjir bantuan"
              />
            </Field>
            <Field label="Frekuensi">
              <select value={every} onChange={(e) => setEvery(e.target.value)}>
                <option value="1">Tiap 1 menit (demo)</option>
                <option value="15">Tiap 15 menit</option>
                <option value="60">Tiap 1 jam</option>
              </select>
            </Field>
            <Field label="Batas hasil">
              <input type="number" value={max} onChange={(e) => setMax(e.target.value)} />
            </Field>
            <Field label="Kedaluwarsa">
              <input type="date" value={expires} onChange={(e) => setExpires(e.target.value)} />
            </Field>
          </div>
          <SourcePicker list={conns.data} value={effSources} onChange={setSources} />
          <button className="btn" onClick={save}>
            Simpan dan jalankan
          </button>
          <p className="mut">
            Scheduler APScheduler di backend mengecek jadwal tiap 20 detik. Kuota 25 per konektor
            per hari; bila habis, job ditunda tanpa bypass.
          </p>
        </Card>
      )}
      <Card t="Topik aktif">
        {topics.error ? (
          <ErrorBox error={topics.error} retry={topics.refresh} />
        ) : topics.loading && !topics.data ? (
          <Loading />
        ) : topics.data?.length ? (
          <TableWrap>
            <table>
              <thead>
                <tr>
                  <th>Topik</th>
                  <th>Jadwal</th>
                  <th>Terakhir</th>
                  <th>Baru</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {topics.data.map((x) => (
                  <tr key={x.id}>
                    <td>
                      <b>{x.name}</b>
                      <br />
                      <span className="mut">
                        {x.q} · {x.sources.join(', ')}
                      </span>
                    </td>
                    <td>
                      Tiap {x.every} mnt
                      <br />
                      <span className="mut">
                        {x.status === 'active' ? 'Berikut ' + fmt(x.next) : ''}
                      </span>
                    </td>
                    <td>
                      {fmt(x.last)}
                      <br />
                      <span className="mut">{x.err}</span>
                    </td>
                    <td>{x.new_total}</td>
                    <td>
                      <Chip s={x.status} />
                    </td>
                    <td>
                      {can('run') && (
                        <>
                          <button className="btn sm g" onClick={() => act(x.id, 'run')}>
                            Jalankan
                          </button>{' '}
                          <button
                            className="btn sm g"
                            onClick={() => act(x.id, x.status === 'paused' ? 'resume' : 'pause')}
                          >
                            {x.status === 'paused' ? 'Resume' : 'Pause'}
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableWrap>
        ) : (
          <Empty>Belum ada topik.</Empty>
        )}
      </Card>
      <Card t="Collection jobs">
        <JobTable jobs={jobs.data} />
      </Card>
    </>
  )
}