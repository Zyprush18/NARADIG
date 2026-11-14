export interface User {
  name: string
  role: string
  permissions: string[]
}

export interface Workspace {
  id: number
  name: string
  description?: string
  owner?: string
  created?: number
}

export interface Connector {
  id: string
  name: string
  cap: string
  note: string
  available: boolean
  enabled: boolean
  quota_used: number
  quota_limit: number
  last_ok?: boolean | null
  latency_ms?: number | null
  last_error?: string | null
}

export interface MonitoringTopic {
  id: number
  name: string
  q: string
  sources: string[]
  every: number
  status: string
  next?: number | null
  last?: number | null
  err?: string
  new_total: number
}

export interface Job {
  id: string
  name: string
  type: string
  finished?: number | null
  status: string
  metrics: Record<string, number | string>
}

export interface ClusterRow {
  id: string
  title: string
  items: number
  sources: number
  mutations: number
  score: number
  review: string
}

export interface Review {
  status: string
  notes?: string
  by?: string
  at?: number
}

export interface PriorityFactor {
  name: string
  weight: number
  value: number
}

export interface ClusterDetail {
  cluster: {
    id: string
    title: string
    terms: string[]
    params: { algoritma: string; ambang: number; model: string; waktu: number }
    scores: Record<string, number>
  }
  items: { id: string }[]
  mutations: { kind: string; from: string; to: string; detail?: string }[]
  priority: { score: number; note: string; factors: PriorityFactor[] }
  evidence: {
    title: string
    publisher: string
    type: string
    date: number
    relevance: number
    stance: string
  }[]
  review: Review | null
}

export interface TimelineItem {
  id: string
  at: number
  title: string
  source: string
  text: string
  provenance: { method: string; collected_at: number; license: string; url?: string }
}

export interface Alert {
  id: number
  title: string
  reason: string
  at: number
  sev: string
  cluster_id: string
}

export interface OverviewData {
  items: number
  clusters: number
  alerts: number
  days: number[]
  top: ClusterRow[]
}

export interface SearchHit {
  src_id: string
  title: string
  source: string
  pub: number
  text: string
  origin: string
}

export interface SearchResult {
  query: string
  searched_at: number
  found: number
  added: number
  duplicates: number
  note: string
  results: SearchHit[]
}

export interface Report {
  title: string
  created_at: number
  method: string
  range?: [number, number] | null
  sources: string[]
  rows: (string | number)[][]
  limitations: string
  csv: string
}

export interface FeedProbe {
  url: string
  ok?: boolean
  items?: number
  ms?: number
  error?: string
}

export interface FeedTest {
  allow_mock: boolean
  connectors: Record<string, FeedProbe[]>
}

export interface ImportPreview {
  rows: number
  columns: string[]
  sample: Record<string, unknown>[]
}

export interface ImportResult {
  added: number
  duplicates: number
  invalid: string[]
}

export interface AuditRow {
  id: number
  t: number
  user: string
  action: string
  entity: string
}