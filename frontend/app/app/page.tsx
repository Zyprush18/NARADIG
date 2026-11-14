'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { AppProvider } from '../../lib/context/AppContext'
import { useSession } from '../../lib/hooks/useSession'
import { Shell } from '../../components/Shell'
import { ErrorBoundary } from '../../components/ui/ErrorBoundary'

export default function App() {
  const { user, ready, logout } = useSession()
  const router = useRouter()

  // Login hanya lewat modal di landing; tanpa sesi, kembali ke sana.
  useEffect(() => {
    if (ready && !user) router.replace('/')
  }, [ready, user, router])

  if (!ready || !user) return null
  return (
    <ErrorBoundary>
      <AppProvider user={user}>
        <Shell onLogout={logout} />
      </AppProvider>
    </ErrorBoundary>
  )
}