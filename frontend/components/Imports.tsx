'use client'
import { useState } from 'react'
import { api } from '../lib/api'
import { MAX_IMPORT_BYTES } from '../lib/constants'
import { useApp } from '../lib/context/AppContext'
import type { ImportPreview, ImportResult } from '../lib/types'
import { Card } from './ui/Card'
import { Field } from './ui/Field'
import { TableWrap } from './ui/Async'

interface Mapping {
  text: string
  title: string
  pub: string
  url: string
  source: string
}

const EMPTY_MAP: Mapping = { text: '', title: '', pub: '', url: '', source: '' }

export function Imports() {
  const { ws, can, run, notify } = useApp()
  const [txt, setTxt] = useState('')
  const [name, setName] = useState('tempelan')
  const [pv, setPv] = useState<ImportPreview | null>(null)
  const [res, setRes] = useState<ImportResult | null>(null)
  const [map, setMap] = useState<Mapping>(EMPTY_MAP)
  const [license, setLicense] = useState('')

  const guess = (cols: string[], re: RegExp) => cols.find((c) => re.test(c)) || ''

  const preview = (content: string, filename: string) =>
    run(async () => {
      const p = await api<ImportPreview>('/imports/preview', { body: { content } })
      setTxt(content)
      setName(filename)
      setRes(null)
      setPv(p)
      setMap({
        text: guess(p.columns, /isi|text|content|body/i),
        title: guess(p.columns, /judul|title/i),
        pub: guess(p.columns, /date|tanggal|waktu/i),
        url: guess(p.columns, /url|link/i),
        source: guess(p.columns, /source|sumber/i),
      })
    })

  const pickFile = (f: File) => {
    // F13: jangan muat file besar ke memori.
    if (f.size > MAX_IMPORT_BYTES) {
      notify(
        `Berkas ${(f.size / 1024 / 1024).toFixed(1)} MB melebihi batas ${MAX_IMPORT_BYTES / 1024 / 1024} MB.`,
        true,
      )
      return
    }
    f.text().then((c) => preview(c, f.name))
  }

  const imp = () =>
    run(async () => {
      if (!map.text) throw new Error('Kolom teks konten wajib dipetakan.')
      if (!license.trim()) throw new Error('Lisensi / asal data wajib diisi.')
      const r = await api<ImportResult>('/imports', {
        body: {
          workspace_id: ws,
          filename: name,
          content: txt,
          license: license.trim(),
          mapping: map,
        },
      })
      setRes(r)
      notify('Impor selesai.')
    })

  const sel = (key: keyof Mapping, label: string) => (
    <Field label={label}>
      <select
        value={map[key]}
        onChange={(e) => setMap((m) => ({ ...m, [key]: e.target.value }))}
      >
        <option value="">(tidak dipakai)</option>
        {(pv?.columns ?? []).map((c) => (
          <option key={c}>{c}</option>
        ))}
      </select>
    </Field>
  )

  if (!can('import'))
    return (
      <Card>
        <div className="note">Peran Anda tidak boleh mengimpor.</div>
      </Card>
    )

  return (
    <>
      <Card t="Impor dataset CSV/JSON">
        <label>
          Berkas
          <input
            type="file"
            accept=".csv,.json,.txt"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) pickFile(f)
            }}
          />
        </label>
        <label style={{ marginTop: 12 }}>
          Atau tempel isi
          <textarea value={txt} onChange={(e) => setTxt(e.target.value)} />
        </label>
        <div className="row" style={{ marginTop: 10 }}>
          <button className="btn g" onClick={() => preview(txt, 'tempelan')}>
            Pratinjau
          </button>
        </div>
      </Card>
      {pv && (
        <Card t={`Pratinjau ${name} (${pv.rows} baris)`}>
          <TableWrap>
            <table>
              <thead>
                <tr>
                  {pv.columns.map((c) => (
                    <th key={c}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pv.sample.map((r, i) => (
                  <tr key={i}>
                    {pv.columns.map((c) => (
                      <td key={c}>{String(r[c]).slice(0, 70)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </TableWrap>
          <h2 style={{ marginTop: 16 }}>Pemetaan kolom</h2>
          <div className="form">
            {sel('text', 'Teks konten *')}
            {sel('title', 'Judul')}
            {sel('pub', 'Tanggal')}
            {sel('url', 'URL')}
            {sel('source', 'Sumber')}
            <Field label="Lisensi / asal data *">
              <input value={license} onChange={(e) => setLicense(e.target.value)} />
            </Field>
          </div>
          <button className="btn" style={{ marginTop: 12 }} onClick={imp}>
            Validasi dan impor
          </button>
          {res && (
            <div className="note" style={{ marginTop: 12 }}>
              <b>{res.added} diimpor</b>, {res.duplicates} duplikat, {res.invalid.length} tidak
              valid.
              {res.invalid.map((b) => (
                <div key={b}>{b}</div>
              ))}
            </div>
          )}
        </Card>
      )}
    </>
  )
}