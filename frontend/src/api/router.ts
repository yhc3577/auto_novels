// Router 端点 — 统一意图识别入口

import type { RouterRequest, RouterResponse } from '../api/client'

// 共享 client.ts 里的 base / request
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

export const routerApi = {
  invoke: (body: RouterRequest) =>
    request<RouterResponse>('/router', { method: 'POST', body: JSON.stringify(body) }),
}