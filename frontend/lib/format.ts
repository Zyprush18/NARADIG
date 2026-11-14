// Format tampilan. Zona waktu mengikuti perangkat pengguna, bukan hardcode WITA.
export const fmt = (t?: number | null) =>
  t
    ? new Date(t).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' })
    : '—'

export const tzLabel = () => Intl.DateTimeFormat().resolvedOptions().timeZone

export const pct = (v: number) => Math.round(v * 100) + '%'

export const shortDate = (t: number) =>
  new Date(t).toLocaleDateString('id-ID', { weekday: 'short' })