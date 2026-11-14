'use client'
import { useCallback, useEffect, useState } from 'react'
import { api, setUnauthorizedHandler } from '../api'
import type { User } from '../types'

const K_TOKEN = 'naradig-token'
const K_USER = 'naradig-user'

/** Hapus hanya key milik aplikasi ini (F8: jangan localStorage.clear()). */
export const clearSession = () => {
  localStorage.removeItem(K_TOKEN)
  localStorage.removeItem(K_USER)
}

/** Login ke backend + simpan sesi. Dipakai useSession dan modal di landing. */
export async function loginRequest(email: string, password: string): Promise<User> {
  const r = await api<{ token: string; user: User }>('/auth/login', {
    body: { email, password },
  })
  localStorage.setItem(K_TOKEN, r.token)
  localStorage.setItem(K_USER, JSON.stringify(r.user))
  return r.user
}

export function useSession() {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  const logout = useCallback(async () => {
    await api('/auth/logout', { method: 'POST' }).catch(() => {})
    clearSession()
    setUser(null)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const u = await loginRequest(email, password)
    setUser(u)
    return u
  }, [])

  useEffect(() => {
    // 401 di mana pun -> sesi dibersihkan, kembali ke Login (F3).
    setUnauthorizedHandler(() => {
      clearSession()
      setUser(null)
    })
    const raw = localStorage.getItem(K_USER)
    if (raw && localStorage.getItem(K_TOKEN)) {
      try {
        setUser(JSON.parse(raw))
      } catch {
        clearSession()
      }
    }
    setReady(true)
    return () => setUnauthorizedHandler(null)
  }, [])

  return { user, ready, login, logout }
}