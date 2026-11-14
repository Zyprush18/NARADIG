'use client'
import { useState } from 'react'
import { api } from '../lib/api'
import { useApp } from '../lib/context/AppContext'
import { fmt } from '../lib/format'
import { useApi } from '../lib/hooks/useApi'
import type { AuditRow } from '../lib/types'
import { ErrorBox, TableWrap } from './ui/Async'
import { Card } from './ui/Card'
import { Field } from './ui/Field'

export function Settings() {
  const { wss, ws, can, run, notify, reloadWorkspaces } = useApp()
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const au = useApi<AuditRow[]>(can('audit') ? '/audit' : null)

  return (
    <>
      <Card t="Workspace">
        {can('create') ? (
          <div className="form">
            <Field label="Nama">
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </Field>
            <Field label="Deskripsi">
              <input value={desc} onChange={(e) => setDesc(e.target.value)} />
            </Field>
            <button
              className="btn"
              onClick={() =>
                run(async () => {
                  if (!name.trim()) throw new Error('Nama workspace wajib diisi.')
                  const r = await api<{ id: number }>('/workspaces', {
                    body: { name: name.trim(), description: desc.trim() },
                  })
                  notify('Workspace dibuat.')
                  setName('')
                  setDesc('')
                  reloadWorkspaces(r.id)
                })
              }
            >
              Buat workspace
            </button>
          </div>
        ) : (
          <p className="mut">Peran Anda tidak boleh membuat workspace.</p>
        )}
        {can('delete') && (
          <div className="row" style={{ marginTop: 10 }}>
            <button
              className="btn sm g"
              onClick={() =>
                run(async () => {
                  const r = await api<{ removed: number }>('/admin/purge-mock', {
                    method: 'POST',
                  })
                  notify(`${r.removed} item demo dihapus.`)
                  reloadWorkspaces()
                })
              }
            >
              Bersihkan data demo
            </button>
            <span className="mut">
              Hapus korpus demo + hasil analisisnya. Data feed nyata tidak disentuh.
            </span>
          </div>
        )}
        {wss.map((w) => (
          <div className="li" key={w.id}>
            <div>
              <b>{w.name}</b>
              <span className="mut">
                {w.description} · pemilik {w.owner} · {fmt(w.created)}
              </span>
            </div>
            {w.id === ws && <span className="chip ok">Aktif</span>}
          </div>
        ))}
      </Card>
      <Card t="Audit log">
        {can('audit') ? (
          au.error ? (
            <ErrorBox error={au.error} retry={au.refresh} />
          ) : (
            <TableWrap>
              <table>
                <thead>
                  <tr>
                    <th>Waktu</th>
                    <th>Pengguna</th>
                    <th>Aksi</th>
                    <th>Entitas</th>
                  </tr>
                </thead>
                <tbody>
                  {(au.data ?? []).map((a) => (
                    <tr key={a.id}>
                      <td>{fmt(a.t)}</td>
                      <td>{a.user}</td>
                      <td>{a.action}</td>
                      <td>{a.entity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableWrap>
          )
        ) : (
          <p className="mut">Audit log hanya untuk Admin.</p>
        )}
      </Card>
    </>
  )
}