// API 客户端 — baseURL '/api'，dev/prod 都通过 nginx / vite proxy 转发到 backend :8082

const base = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(base + path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    const detail = body?.error?.message ?? r.statusText
    throw new Error(`${r.status} ${detail}`)
  }
  return r.json()
}

// ---- Types ----

export interface Project {
  id: number
  slug: string
  title: string
  genre: string | null
  platform: string | null
  status: string
  chapter_count: number
  created_at: string
  updated_at: string
}

export interface StageStatus {
  name: string
  status: 'pending' | 'running' | 'done' | 'skipped' | 'failed'
  started_at?: string
  finished_at?: string
  notes?: string
}

export interface WriteResponse {
  project_id: number
  chapter_no: number
  chapter_id: number | null
  state_revision: number
  final_wordcount: number | null
  stages: StageStatus[]
  chapter_hook: string | null
  summary_text: string | null
  errors: string[]
}

export type Scenario = 'auto' | 'write_long' | 'write_short' | 'scan'

export interface RouterRequest {
  project_id: number
  user_input: string
  explicit_scenario?: Scenario
}

export interface RouterResponse {
  intent: string
  graph_invoked: string
  supported: boolean
  state_revision: number | null
  final_wordcount: number | null
  stages: StageStatus[]
  payload: Record<string, unknown>
  errors: string[]
  notice: string | null
}

// ---- Endpoints ----

export const api = {
  healthz: () => request<{ ok: boolean; db: boolean }>('/healthz'),

  listProjects: () => request<Project[]>('/projects'),
  getProject: (id: number) => request<Project>(`/projects/${id}`),
  createProject: (body: { slug: string; title: string; genre?: string; platform?: string }) =>
    request<Project>('/projects', { method: 'POST', body: JSON.stringify(body) }),

  write: (body: {
    project_id: number
    chapter_no?: number
    user_input: string
    target_wordcount?: number
  }) => request<WriteResponse>('/write', { method: 'POST', body: JSON.stringify(body) }),
}