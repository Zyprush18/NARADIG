'use client'
import { useState } from 'react'
import { api } from '../lib/api'
import { useApp } from '../lib/context/AppContext'
import { useApi } from '../lib/hooks/useApi'
import type { Connector, FeedTest } from '../lib/types'
import { ErrorBox, Loading } from './ui/Async'
import { Card } from './ui/Card'
import { Chip } from './ui/Chip'

export function Sources() {
  const { can, run, notify } = useApp()
  const conns = useApi<Connector[]>('/connectors')
  const [ft, setFt] = useState<FeedTest | null>(null)

  return (
    <Card t="Katalog konektor">
      <div className="row" style={{ marginBottom: 8 }}>
        <button
          className="btn sm g"
          onClick={() => run(async () => setFt(await api<FeedTest>('/feed-test')))}
        >
          Tes feed nyata
        </button>
        <span className="mut">Cek langsung tanpa menyimpan data.</span>
      </div>
      {ft && (
        <div className="note">
          {Object.entries(ft.connectors).map(([k, v]) => (
            <div key={k}>
              {k}:{' '}
              {v
                .map(
                  (f) =>
                    `${f.ok ? 'OK' : 'GAGAL'} ${f.items ?? 0} item ${f.ms}ms ${f.error || ''}`,
                )
                .join(' | ')}
            </div>
          ))}
          <span className="mut">Mode mock: {ft.allow_mock ? 'aktif' : 'nonaktif'}</span>
        </div>
      )}
      {conns.error ? (
        <ErrorBox error={conns.error} retry={conns.refresh} />
      ) : conns.loading && !conns.data ? (
        <Loading />
      ) : (
        (conns.data ?? []).map((x) => (
          <div className="li" key={x.id}>
            <div>
              <b>{x.name}</b>
              <span className="mut">
                {x.cap}. {x.note}
              </span>
              {x.available && (
                <>
                  <span className="mut">
                    Kuota hari ini: {x.quota_used}/{x.quota_limit}
                  </span>
                  {x.last_ok != null && (
                    <span className="mut">
                      Kesehatan: {x.last_ok ? 'OK' : 'gagal'} · {x.latency_ms ?? '—'} ms{' '}
                      {x.last_error ? '· ' + x.last_error : ''}
                    </span>
                  )}
                  <div className="bar2" style={{ maxWidth: 240 }}>
                    <i style={{ width: (x.quota_used / x.quota_limit) * 100 + '%' }} />
                  </div>
                </>
              )}
            </div>
            {x.available ? (
              <>
                <Chip s={x.enabled ? 'Aktif' : 'Nonaktif'} />
                {can('conn') && (
                  <button
                    className="btn sm g"
                    onClick={() =>
                      run(async () => {
                        await api('/connectors/' + x.id, {
                          method: 'PATCH',
                          body: { enabled: !x.enabled },
                        })
                        notify('Konektor diperbarui.')
                        conns.refresh()
                      })
                    }
                  >
                    {x.enabled ? 'Nonaktifkan' : 'Aktifkan'}
                  </button>
                )}
              </>
            ) : (
              <span className="chip e">Belum tersedia</span>
            )}
          </div>
        ))
      )}
      <p className="mut">
        Hanya konten publik yang diakses secara sah. Hanya Admin yang dapat mengubah konektor.
      </p>
    </Card>
  )
}