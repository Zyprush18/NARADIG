'use client'
import { useApp } from '../lib/context/AppContext'
import { fmt } from '../lib/format'
import { useApi } from '../lib/hooks/useApi'
import type { Alert } from '../lib/types'
import { ErrorBox, Loading } from './ui/Async'
import { Card } from './ui/Card'

export function Alerts() {
  const { ws, openCluster } = useApp()
  const a = useApi<Alert[]>(ws ? `/alerts?workspace_id=${ws}` : null, 10000)

  return (
    <Card t="Alert berbasis aturan">
      {a.error ? (
        <ErrorBox error={a.error} retry={a.refresh} />
      ) : a.loading && !a.data ? (
        <Loading />
      ) : a.data?.length ? (
        a.data.map((x) => (
          <div className="li" key={x.id}>
            <div>
              <b>{x.title}</b>
              <span className="mut">
                {x.reason} {fmt(x.at)}
              </span>
            </div>
            <span className={'chip ' + (x.sev === 'Tinggi' ? 'w' : '')}>{x.sev}</span>
            <button className="btn sm g" onClick={() => openCluster(x.cluster_id)}>
              Lihat temuan
            </button>
          </div>
        ))
      ) : (
        <div className="note">
          Belum ada alert. Alert dibuat setelah analisis jika skor tinggi atau banyak kandidat
          perubahan.
        </div>
      )}
    </Card>
  )
}