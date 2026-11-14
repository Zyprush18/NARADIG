'use client'
import { api } from '../lib/api'
import { useApp } from '../lib/context/AppContext'
import { useApi } from '../lib/hooks/useApi'
import type { ClusterRow } from '../lib/types'
import { ErrorBox, Empty, Loading } from './ui/Async'
import { Card } from './ui/Card'
import { ClusterDetail } from './ClusterDetail'

export function Clusters() {
  const { ws, run, notify, sel, setSel } = useApp()
  const list = useApi<ClusterRow[]>(ws ? `/clusters?workspace_id=${ws}` : null)

  if (sel)
    return (
      <ClusterDetail
        id={sel}
        back={() => {
          setSel(null)
          list.refresh()
        }}
      />
    )

  return (
    <>
      <Card>
        <div className="row">
          <button
            className="btn"
            onClick={() =>
              run(async () => {
                const r = await api<{ clusters: number }>(`/workspaces/${ws}/analysis-jobs`, {
                  method: 'POST',
                })
                notify(`Analisis selesai: ${r.clusters} klaster.`)
                list.refresh()
              })
            }
          >
            Jalankan analisis
          </button>
          <span className="mut">Kemiripan konten bukan bukti koordinasi.</span>
        </div>
      </Card>
      <Card>
        {list.error ? (
          <ErrorBox error={list.error} retry={list.refresh} />
        ) : list.loading && !list.data ? (
          <Loading />
        ) : list.data?.length ? (
          list.data.map((c) => (
            <div className="li" key={c.id}>
              <div>
                <b>{c.title}</b>
                <span className="mut">
                  {c.items} item · {c.sources} sumber · {c.mutations} kandidat perubahan ·{' '}
                  {c.review}
                </span>
              </div>
              <span className="chip w">Prioritas {c.score}</span>
              <button className="btn sm g" onClick={() => setSel(c.id)}>
                Detail
              </button>
            </div>
          ))
        ) : (
          <Empty>Belum ada klaster. Kumpulkan data lalu jalankan analisis.</Empty>
        )}
      </Card>
    </>
  )
}