'use client'
import { NAV, PAGE_TITLES } from '../lib/constants'
import { useApp } from '../lib/context/AppContext'
import { useApi } from '../lib/hooks/useApi'
import type { Alert } from '../lib/types'
import { Card } from './ui/Card'
import { Overview } from './Overview'
import { Monitoring } from './Monitoring'
import { TopicSearch } from './TopicSearch'
import { Sources } from './Sources'
import { Imports } from './Imports'
import { Clusters } from './Clusters'
import { Alerts } from './Alerts'
import { Reports } from './Reports'
import { Settings } from './Settings'

function Page() {
  const { page } = useApp()
  switch (page) {
    case 'ov':
      return <Overview />
    case 'mon':
      return <Monitoring />
    case 'search':
      return <TopicSearch />
    case 'src':
      return <Sources />
    case 'imp':
      return <Imports />
    case 'cl':
      return <Clusters />
    case 'al':
      return <Alerts />
    case 'rep':
      return <Reports />
    case 'set':
      return <Settings />
    default:
      return null
  }
}

export function Shell({ onLogout }: { onLogout: () => Promise<void> }) {
  const { user, ws, wss, pickWs, page, setPage, msg } = useApp()
  const { data: alerts } = useApi<Alert[]>(ws ? `/alerts?workspace_id=${ws}` : null, 15000)
  const title = page === 'ov' ? `Selamat datang kembali, ${user.name}` : PAGE_TITLES[page] ?? ''

  return (
    <div className="shell">
      <aside>
        <div className="logo">
          <i>N</i>NARADIG
        </div>
        <nav aria-label="Navigasi utama">
          {NAV.map(([k, l]) => (
            <button key={k} className={page === k ? 'on' : ''} onClick={() => setPage(k)}>
              {l}
              {k === 'al' && alerts?.length ? <b>{alerts.length}</b> : null}
            </button>
          ))}
        </nav>
        <p className="mut" style={{ margin: '18px 8px 8px', color: '#c8c8d8' }}>
          {user.name} ({user.role})
        </p>
        <button className="btn sm" onClick={() => void onLogout()}>
          Keluar
        </button>
      </aside>
      <main>
        <div className="top">
          <h1>{title}</h1>
          <select
            className="pill"
            aria-label="Workspace"
            value={ws ?? ''}
            onChange={(e) => pickWs(+e.target.value)}
            style={{ width: 'auto' }}
          >
            {wss.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </div>
        {msg && (
          <div className={'flash ' + (msg.e ? 'err' : '')} role="status">
            {msg.t}
          </div>
        )}
        {!ws && page !== 'set' ? (
          <Card>
            <div className="note">Buat workspace dulu di Settings.</div>
          </Card>
        ) : (
          // key: state lokal halaman ikut direset saat workspace berganti (F5).
          <Page key={`${page}-${ws ?? 'none'}`} />
        )}
      </main>
    </div>
  )
}