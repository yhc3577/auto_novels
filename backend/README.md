# auto_novels backend

> FastAPI + LangGraph + async PostgreSQL demo.
> 系统架构、5 层分层说明见根 [README.md](../README.md) 与 [docs/](../docs/)。

---

## 1. 启动（独立模式，无需前端）

```bash
# 起 PG
docker compose up -d postgres

# 装依赖 + 启 API
cp .env.example .env
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

访问：

- Swagger: <http://localhost:8082/docs>
- Healthz: <http://localhost:8082/api/healthz>

## 2. 目录速查（5 层）

```
backend/app/
├── main.py            # FastAPI 入口 + lifespan
├── config.py          # pydantic-settings
├── db.py              # async engine + session_scope
├── deps.py            # get_session（Depends）
├── errors.py          # DomainError + handlers
├── logging_setup.py
│
├── models/            # Layer 4 — ORM
├── repositories/      # Layer 3 — CRUD（唯一 import ORM 的层）
├── services/          # Layer 2 — 业务用例（事务边界）
├── schemas/           # Layer 0 — Pydantic DTO
├── agents/            # 横向 — LLM agent（只能调 service）
├── graphs/            # 横向 — LangGraph 拓扑（节点调 service）
└── api/               # Layer 1 — FastAPI 路由
```

## 3. LangGraph 节点（demo 最薄实现）

```
route_scenario → write_prose → wordcount_checkpoint → tracking_commit → END
```

每个节点都 `async def`；通过 deps dict 注入 `session` + `llm_factory`：
- `route_scenario` — 推算 `chapter_no = last_committed + 1`
- `write_prose` — 调 `narrative_writer` agent
- `wordcount_checkpoint` — `WordcountService.checkpoint`（CJK ±20%）
- `tracking_commit` — `TrackingService.commit`（**单事务写 chapters + chapter_records**）

## 4. 测试

```bash
pytest -q
```

覆盖：
- `WordcountService`（CJK / ASCII / 混合 / checkpoint 通过/失败）
- **铁律**：agent / graphs 不能 import `repository` / `models`（AST 扫描守）

## 5. 切换真实 LLM

三选一，改 `.env` 即可（代码路径完全写好）：

```bash
# ── A. 直连 Anthropic ─────────────────────────────
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_WRITER_MODEL=claude-sonnet-4-5

# ── B. 直连 OpenAI ────────────────────────────────
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_WRITER_MODEL=gpt-4o-mini

# ── C. NewAPI 网关（OpenAI 兼容协议，推荐）─────────
LLM_PROVIDER=newapi
NEWAPI_BASE_URL=https://your-newapi-domain/v1
NEWAPI_API_KEY=sk-xxxxxxxxxxxxxx          # NewAPI 网关签发的 key，不是上游 provider 的
LLM_WRITER_MODEL=anthropic/claude-sonnet-4-5   # NewAPI 下模型名格式：<provider>/<model>
```

### NewAPI 部署说明

- NewAPI 是 OpenAI Chat Completions 兼容网关，后端可用任何 provider（Claude / GPT / Gemini / 国产）
- 本项目通过 `langchain-openai.ChatOpenAI(base_url=…, api_key=…)` 接入，与 NewAPI 走同一协议
- 鉴权使用 NewAPI 网关发的 `sk-…` key，**不是**上游 provider 的 key
- 模型名按 NewAPI 约定：`<provider>/<model>`（例如 `anthropic/claude-sonnet-4-5`、`openai/gpt-4o`）
- 切换失败时会报 `ValueError("LLM_PROVIDER=newapi 时必须设置 NEWAPI_BASE_URL")`

## 6. 已知 demo 限制

| 项 | demo 行为 | 生产应做 |
|---|---|---|
| 字数不足 | 仅在 stages.notes 标注，不过滤 | `QualityService` 重新写 |
| 缺 reference_materials | 不报错 | `Reference Gate` 拦下 |
| 并发写同章 | last write wins（`ON CONFLICT` upsert） | Redis lock:chapter:* |
| 长会话 | 不压缩 context | 召回 + budget 切片 |
| Checkpoint | 不持久化 | 接 `langgraph-checkpoint-postgres` |