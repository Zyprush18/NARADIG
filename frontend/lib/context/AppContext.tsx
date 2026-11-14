'use client'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api } from '../api'
import type { User, Workspace } from '../types'

export type Flash = { t: string; e?: boolean } | null

interface AppCtx {
  user: User
  /** null = belum ada workspace / belum dipilih */
  ws: number | null
  wss: Workspace[]
  pickWs: (id: number) => void
  reloadWorkspaces: (pick?: number) => Promise<void>
  can: (p: string) => boolean
  notify: (t: string, e?: boolean) => void
  run: (fn: () => Promise<unknown>) => Promise<void>
  msg: Flash
  page: string
  setPage: (p: string) => void
  sel: string | null
  setSel: (s: string | null) => void
  openCluster: (id: string) => void
}

const Ctx = createContext<AppCtx | null>(null)

export const useApp = () => {
  const c = useContext(Ctx)
  if (!c) throw new Error('useApp dipakai di luar AppProvider')
  return c
}

export function AppProvider({ user, children }: { user: User; children: ReactNode }) {
  const [wss, setWss] = useState<Workspace[]>([])
  const [ws, setWs] = useState<number | null>(null)
  const [page, setPage] = useState('ov')
  const [sel, setSel] = useState<string | null>(null)
  const [msg, setMsg] = useState<Flash>(null)

  const notify = useCallback((t: string, e = false) => setMsg({ t, e }), [])

  const run = useCallback(
    async (fn: () => Promise<unknown>) => {
      try {
        await fn()
      } catch (e) {
        notify((e as Error).message, true)
      }
    },
    [notify],
  )

  const reloadWorkspaces = useCallback(async (pick?: number) => {
    const w = await api<Workspace[]>('/workspaces')
    setWss(w)
    // Pakai nilai prev, bukan closure ws yang basi (F7).
    setWs((prev) => pick ?? (w.some((x) => x.id === prev) ? prev : w[0]?.id ?? null))
    if (!w.length) setPage('set')
  }, [])

  useEffect(() => {
    run(() => reloadWorkspaces())
  }, [reloadWorkspaces, run])

  useEffect(() => {
    setMsg(null)
  }, [page])

  const pickWs = useCallback((id: number) => {
    setWs(id)
    setSel(null)
  }, [])

  const goPage = useCallback((p: string) => {
    setPage(p)
    setSel(null)
  }, [])

  const openCluster = useCallback((id: string) => {
    setSel(id)
    setPage('cl')
  }, [])

  const can = useCallback((p: string) => user.permissions.includes(p), [user.permissions])

  const value = useMemo<AppCtx>(
    () => ({
      user,
      ws,
      wss,
      pickWs,
      reloadWorkspaces,
      can,
      notify,
      run,
      msg,
      page,
      setPage: goPage,
      sel,
      setSel,
      openCluster,
    }),
    [user, ws, wss, pickWs, reloadWorkspaces, can, notify, run, msg, page, goPage, sel, openCluster],
  )

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}