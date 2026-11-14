'use client'
import { useState } from 'react'
import { api } from '../lib/api'
import { useApp } from '../lib/context/AppContext'
import { fmt } from '../lib/format'
import { useApi } from '../lib/hooks/useApi'
import type { Connector, SearchResult } from '../lib/types'
import { Card } from './ui/Card'
import { Field } from './ui/Field'
import { Origin } from './ui/Chip'
import { availableSources, SourcePicker } from './ui/SourcePicker'

export function TopicSearch() {
  const { ws, can, run, setPage } = useApp()
  const conns = useApi<Connector[]>('/connectors')
  const [query, setQuery] = useState('')
  const [days, setDays] = useState('7')
  const [limit, setLimit] = useState('10')
  const [sources, setSources] = useState<string[] | null>(null)
  const [r, setR] = useState<SearchResult | null>(null)
  const effSources = sources ?? availableSources(conns.data)

  const search = () =>
    run(async () => {
      if (!query.trim()) throw new Error('Query wajib diisi.')
      setR(
        await api<SearchResult>('/topic-search', {
          body: {
            workspace_id: ws,
            query: query.trim(),
            sources: effSources,
            days: +days,
            limit: +limit || 10,
          },
        }),
      )
    })

  return (
    <>
      <Card t="Pencarian topik sesuai permintaan">
        {can('run') ? (
          <>
            <div className="form">
              <Field label="Query">
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="beras harga"
                />
              </Field>
              <Field label="Rentang">
                <select value={days} onChange={(e) => setDays(e.target.value)}>
                  <option value="3">3 hari</option>
                  <option value="7">7 hari</option>
                  <option value="30">30 hari</option>
                </select>
              </Field>
              <Field label="Batas hasil">
                <input type="number" value={limit} onChange={(e) => setLimit(e.target.value)} />
              </Field>
            </div>
            <SourcePicker list={conns.data} value={effSources} onChange={setSources} />
            <button className="btn" onClick={search}>
              Cari
            </button>
          </>
        ) : (
          <div className="note">Peran Anda tidak boleh menjalankan pencarian.</div>
        )}
      </Card>
      {r && (
        <Card t={`Hasil: “${r.query}”`}>
          <p className="mut">
            {fmt(r.searched_at)} · {r.found} ditemukan, {r.added} baru, {r.duplicates} duplikat.{' '}
            {r.note}
          </p>
          {r.found ? (
            r.results.map((x) => (
              <div className="li" key={x.src_id}>
                <div>
                  <b>{x.title}</b>
                  <span className="mut">
                    {x.source} · {fmt(x.pub)} <Origin origin={x.origin} />
                  </span>
                  {x.text}
                </div>
              </div>
            ))
          ) : (
            <div className="note">Tidak ada hasil. Coba kata kunci lain.</div>
          )}
          <button
            className="btn"
            onClick={() =>
              run(async () => {
                await api(`/workspaces/${ws}/analysis-jobs`, { method: 'POST' })
                setPage('cl')
              })
            }
          >
            Jalankan analisis
          </button>
        </Card>
      )}
    </>
  )
}