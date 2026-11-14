export const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export interface ApiError extends Error {
  status?: number
}

let onUnauthorized: (() => void) | null = null

/** Dipanggil sekali di useSession: 401 dari endpoint mana pun = sesi habis. */
export const setUnauthorizedHandler = (fn: (() => void) | null) => {
  onUnauthorized = fn
}

export async function api<T = any>(
  path: string,
  o: { method?: string; body?: unknown; signal?: AbortSignal } = {},
): Promise<T> {
  const method = o.method || (o.body !== undefined ? 'POST' : 'GET')
  const token = typeof window !== 'undefined' ? localStorage.getItem('naradig-token') : null
  const headers: Record<string, string> = {}
  if (token) headers.Authorization = 'Bearer ' + token
  // Content-Type hanya saat ada body (F12: hindari preflight CORS di GET).
  if (o.body !== undefined) headers['Content-Type'] = 'application/json'

  let r: Response
  try {
    r = await fetch(API + path, {
      method,
      headers,
      body: o.body !== undefined ? JSON.stringify(o.body) : undefined,
      signal: o.signal,
    })
  } catch (e) {
    if ((e as Error)?.name === 'AbortError') throw e
    throw new Error('Backend tidak dapat dihubungi. Pastikan FastAPI berjalan di ' + API)
  }

  if (r.status === 401 && token) onUnauthorized?.()

  const j = await r.json().catch(() => ({}))
  if (!r.ok) {
    const err = new Error(
      typeof j.detail === 'string' ? j.detail : 'Permintaan gagal (' + r.status + ')',
    ) as ApiError
    err.status = r.status
    throw err
  }
  return j as T
}