// Router 端点 — 统一意图识别入口

import { request, type RouterRequest, type RouterResponse } from './client'

export const routerApi = {
  invoke: (body: RouterRequest) =>
    request<RouterResponse>('/router', { method: 'POST', body: JSON.stringify(body) }),
}