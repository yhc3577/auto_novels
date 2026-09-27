# auto_novels frontend

> Vue 3 + Vite + TypeScript SPA.
> 通过 nginx（或 vite proxy）反代 `/api` 到 backend.

## 启动（开发模式）

```bash
npm install
npm run dev
# → http://localhost:5173
```

`/api/*` 自动代理到 `http://localhost:8082`（见 `vite.config.ts`）。

## 生产构建

```bash
npm run build       # 产出 dist/
npm run preview     # 本地预览（:8080）

# 或直接交给 docker-compose（根目录）：
docker compose up -d --build frontend
```

## 目录

```
frontend/
├── package.json
├── vite.config.ts      # 含 /api 代理
├── tsconfig.json
├── index.html
├── Dockerfile          # 多阶段：node build → nginx 托管
└── src/
    ├── main.ts
    ├── App.vue
    ├── router.ts
    ├── api/client.ts   # 类型化的 fetch wrapper
    ├── pages/
    │   ├── ProjectsPage.vue   # 建项目 + 列表
    │   └── WritePage.vue      # 触发写章节 + 看 stages
    └── components/
        └── StageList.vue
```

## 路径约定

| URL | 组件 | 数据来源 |
|---|---|---|
| `/` | `ProjectsPage` | `GET /api/projects` |
| `/projects/:id/write` | `WritePage` | `POST /api/write` |
| API 根 | — | `/api`（nginx / vite proxy → backend:8082） |