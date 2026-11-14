'use client'
import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'

export interface AsyncState<T> {
  data: T | null
  error: Error | null
  loading: boolean
  refresh: () => void
}

/**
 * Fetch tunggal + polling opsional.
 * - path berubah / unmount -> request lama di-abort (F1: respons basi tidak menimpa).
 * - error disimpan, bukan ditelan (F2).
 * - polling berhenti saat tab tersembunyi (F6).
 */
export function useApi<T = any>(path: string | null, every = 0): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(!!path)
  const [tick, setTick] = useState(0)
  const refresh = useCallback(() => setTick((t) => t + 1), [])

  useEffect(() => {
    if (!path) {
      setData(null)
      setError(null)
      setLoading(false)
      return
    }
    let alive = true
    let ctrl: AbortController | null = null

    const load = async () => {
      ctrl?.abort()
      ctrl = new AbortController()
      setLoading(true)
      try {
        const d = await api<T>(path, { signal: ctrl.signal })
        if (!alive) return
        setData(d)
        setError(null)
      } catch (e) {
        if (!alive || (e as Error)?.name === 'AbortError') return
        setError(e as Error)
      } finally {
        if (alive) setLoading(false)
      }
    }

    load()
    const id = every
      ? setInterval(() => {
          if (!document.hidden) load()
        }, every)
      : undefined

    return () => {
      alive = false
      if (id) clearInterval(id)
      ctrl?.abort()
    }
  }, [path, every, tick])

  return { data, error, loading, refresh }
}