# auto_novels · demo

> 多 agent 网文写作系统 — **FastAPI + LangGraph + PostgreSQL + Vue 3 + nginx**.
>
> 设计文档在 [`docs/`](./docs/)；实现细节分别见 [`backend/README.md`](./backend/README.md) 与 [`frontend/README.md`](./frontend/README.md)。

---

## 1. 架构（系统级 3 层）

```
浏览器 → nginx(:80)
           ├─ /          → frontend(Vue 3 SPA, 静态资源)
           ├─ /api/*     → backend(FastAPI+LangGraph, :8082)
           └─ /docs      → backend FastAPI Swagger
                          │
                          ▼
                       postgres(:5432)
```

内部网络隔离：PG / backend / frontend 都不直接对外，只 nginx 暴露 80。

## 2. 应用内 5 层（后端）

```
Layer 0 · schemas (Pydantic DTO)         ← API 边界
Layer 1 · api    (FastAPI routes)        ← HTTP 边界
Layer 2 · service (业务用例 / 事务边界)    ← Agent 唯一允许调用的层
Layer 3 · repository (纯 CRUD)            ← 唯一 import ORM 的层
Layer 4 · models (SQLAlchemy 2.0 async)   ← 持久化

横向：agents (LLM 节点)  /  graphs (LangGraph 拓扑)
```

**依赖铁律**（由 `tests/test_smoke.py::test_iron_rule_*` 守住）：
- agent ❌ 不能 import `repository` / `models`
- graph ❌ 不能 import `repository` / `models`
- 事务边界只在 service（`TrackingService.commit`）

## 3. 启动方式（两种）

### 方式 A · docker-compose 一键起（推荐 demo）

```bash
# 在仓库根目录
docker compose up -d --build
# 等待 ~30s（首次要 build + 装依赖）

# 浏览器
open http://localhost         # 前端
open http://localhost/docs    # FastAPI Swagger

# 日志
docker compose logs -f nginx backend frontend

# 关停
docker compose down           # 保留数据
docker compose down -v        # 删数据
```

### 方式 B · 本地开发模式（保留 `uvicorn` + `vite dev`）

```bash
# 终端 1 · 起 PG（仅）
docker compose -f backend/docker-compose.yml up -d postgres

# 终端 2 · 后端
cd backend
cp .env.example .env
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload

# 终端 3 · 前端（自带 /api → :8082 代理）
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

开发模式下 **不需要 nginx** — vite dev 自带 proxy pass，浏览器依然只看到 `http://localhost:5173`。

## 4. demo 流程（curl）

```bash
# 1. 健康检查
curl -s http://localhost/api/healthz
# {"ok":true,"db":true}

# 2. 建项目
curl -s -X POST http://localhost/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"slug":"wugang-demo","title":"雾港来客","genre":"都市悬疑","platform":"fanqie"}'

# 3. 触发写第 1 章（mock LLM 返回预置正文）
curl -s -X POST http://localhost/api/write \
  -H 'Content-Type: application/json' \
  -d '{"project_id":1,"user_input":"回到雾港的夜晚","target_wordcount":1500}'
```

返回包含 `stages[]`（节点进度）/ `final_wordcount` / `chapter_hook` / `summary_text`。

## 5. 切换到真实 LLM

`backend/.env`（方式 B）或根 `docker-compose.yml` `backend.environment`：

```env
LLM_PROVIDER=anthropic          # 或 openai
ANTHROPIC_API_KEY=sk-ant-...
LLM_WRITER_MODEL=claude-sonnet-4-5
```

## 6. 目录结构

```
auto_novels/
├── docs/                # 设计文档（schema / LangGraph 拆解 / 拓扑）
├── backend/             # FastAPI + LangGraph + async PG（5 层骨架）
├── frontend/            # Vue 3 + Vite SPA
├── nginx/               # 反向代理网关配置
└── docker-compose.yml   # 4 服务一键起
```

## 7. 已实现 vs 设计差距

| 项 | 状态 |
|---|---|
| FastAPI + async PG + LangGraph 端到端 demo | ✓ |
| 5 层分层 + 铁律 + 测试守住 | ✓ |
| nginx 反代网关 | ✓ |
| Vue 3 SPA（建项目 + 写章节 + 看 stages）| ✓ |
| docker-compose 一键起 + 本地开发模式 | ✓ |
| Mock LLM（无需 API key）| ✓ |
| 真实 LLM 切换（Anthropic / OpenAI）| ✓ |
| 完整 19 张表 ORM 映射 | △（demo 只 3 张核心表）|
| Alembic 迁移 | △（当前用 docker initdb 自动应用 SQL）|
| RouterGraph / AnalyzeGraph / ReviewGraph | ✗（demo 只 WriteGraph 4 节点）|
| Reference Gate / QualityService | ✗（demo 跳过）|
| Checkpointer / Redis 热层 | ✗ |

详见 [`docs/langgraph-status-v0.1.md`](./docs/langgraph-status-v0.1.md)。