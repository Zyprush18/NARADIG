export const NAV: [string, string][] = [
  ['ov', 'Overview'],
  ['mon', 'Live Monitoring'],
  ['search', 'Topic Search'],
  ['src', 'Data Sources'],
  ['imp', 'Data Imports'],
  ['cl', 'Cluster Intelligence'],
  ['al', 'Alerts'],
  ['rep', 'Reports'],
  ['set', 'Settings / Audit'],
]

export const PAGE_TITLES: Record<string, string> = Object.fromEntries(NAV)

export const REVIEW_STATUS = [
  'Belum ditinjau',
  'Perlu pemeriksaan lanjut',
  'Bukti cukup sebagai konteks',
  'Bukti membantah klaim',
  'Tidak relevan (false positive)',
]

// Batas file impor di klien; server tetap punya batas sendiri.
export const MAX_IMPORT_BYTES = 2 * 1024 * 1024