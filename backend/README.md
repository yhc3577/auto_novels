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

# 一次性初始化 DB schema (创建 projects / chapters / chapter_records / users 表)
PYTHONPATH=. .venv/bin/python -m scripts.init_db

# 启 API
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

JWT 密钥（默认 dev 占位）：生产环境务必设 `JWT_SECRET=<strong-random>` env 变量覆盖。

访问：

- Swagger: <http://localhost:8082/docs>
- Healthz: <http://localhost:8082/api/healthz>

## 1.1 Auth 端点

| 端点 | 方法 | 需要鉴权 | 说明 |
|------|------|---------|------|
| `/api/auth/register` | POST | ❌ | 用户名 + 密码注册，返 JWT token (HS256, 7 天过期) |
| `/api/auth/login` | POST | ❌ | 用户名 + 密码登录，返 JWT token |
| `/api/auth/me` | GET | ✅ | 验证 token 还有效，返当前 user |
| `/api/healthz` | GET | ❌ | 健康检查（监控系统用）|
| `/api/projects` | * | ✅ | 项目 CRUD（list / get / create）|
| `/api/write` | POST | ✅ | 触发 write_long 图 |
| `/api/router` | POST | ✅ | 统一意图识别入口 |

请求体：`{"username": "...", "password": "..."}`
响应：`{"token": "eyJ...", "user_id": 1, "username": "...", "created_at": "..."}`

存储：bcrypt 哈希（cost=12），密码限 72 字节。

鉴权方式：所有需鉴权的端点要带 `Authorization: Bearer <token>` header。前端 axios 已在 `services/api.ts` 拦截器里自动注入；401 自动清理 localStorage 并跳 `/login`。

## 2. 目录速查（5 层 + 横向）

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
├── services/          # Layer 2 — 业务用例（事务边界）+ 纯规则工具
├── schemas/           # Layer 0 — Pydantic DTO
├── agents/            # 横向 — LLM agent（只能调 service）
├── graphs/            # 横向 — LangGraph 拓扑（节点调 service）
└── api/               # Layer 1 — FastAPI 路由
```

### `agents/` — 三个真 LLM agent

| Agent | 文件 | 角色 |
|------|------|------|
| `NarrativeWriter` | `narrative_writer.py` | 章节正文生成（write_long / write_short） |
| `ChapterDesigner` | `chapter_designer.py` | 章节细纲设计（结构化 JSON） |
| `ProseConsistencyChecker` | `prose_consistency.py` | LLM 轻校验：剧情一致性审查 |
| `IntentRouter` | `intent_router.py` | 意图识别（启发式 + LLM 兜底） |
| `ScanExplorer` | `scan_explorer.py` | 扫榜报告摘要 |

### `services/` — 纯规则工具 + 业务用例

| Service | 文件 | 性质 |
|------|------|------|
| `WordcountService` | `wordcount.py` | 工具 — CJK/ASCII 字数测量 |
| `OutlineValidator` | `outline_validator.py` | 工具 — 细纲钩子+节拍覆盖规则校验 |
| `OutlinePreValidator` | `outline_pre_validator.py` | 工具 — 写前细纲完整性/卷契约/ReferenceGate |
| `ProsePostChecker` | `prose_post_checker.py` | 工具 — 写后 6 项确定性门禁 |
| `ContextService` | `context.py` | 业务 — 上下文召回（last_n 章 + 参考材料 + 作者记忆） |
| `TrackingService` | `tracking.py` | 业务 — 原子事务落库（chapters + chapter_records） |
| `ChapterService` | `chapter.py` | 业务 — 章节读侧 |

## 3. write_long 图（4 节点 精简设计-写作-校验闭环）

```
chapter_design (LLM)
       ↓
pre_write_validate (服务，路由点)
       ├─ pass ──────────────────────────→ write_prose
       └─ fail + retry<MAX → chapter_design (loop)
       └─ fail + retry≥MAX → write_prose (best-effort)
       ↓
write_prose (LLM)
       ↓
validate_prose (合并节点：post_write_check + prose_consistency + tracking_commit + interrupt_human)
       ├─ post_write fail + iter<MAX ────→ write_prose (loop，无 commit)
       ├─ post_write fail + iter≥MAX ────→ commit (best-effort) → END
       ├─ post_write pass + consistency low/medium ──→ commit → END
       ├─ post_write pass + consistency high + iter<MAX ──→ chapter_design (loop)
       └─ post_write pass + consistency high + iter≥MAX:
           ├─ LLM 推荐 human_review → commit + interrupt_pending → END
           └─ 其他推荐 → commit (best-effort) → END
```

### 节点性质分类

| 性质 | 节点 |
|------|------|
| **LLM agent**（2） | `chapter_design`, `write_prose` |
| **服务节点**（2） | `pre_write_validate`, `validate_prose`（合并节点） |

> **简化动机**：7 节点图中 `post_write_check` / `prose_consistency` / `tracking_commit` / `interrupt_human` 4 个节点被合并为 `validate_prose`。路由决策点全部内化到节点函数内，不再依赖多组条件边。

### validate_prose 决策矩阵

| post_write | consistency | iter | action |
|-----------|-------------|------|--------|
| fail | (skipped) | <MAX | loop to `write_prose`（无 commit）|
| fail | (skipped) | ≥MAX | commit（best-effort）|
| pass | low / medium | any | commit（clean pass）|
| pass | high | <MAX | loop to `chapter_design`（无 commit）|
| pass | high + `human_review` | ≥MAX | commit + `interrupt_pending` |
| pass | high + other | ≥MAX | commit (best-effort) |

### 闭环控制参数

```python
MAX_PRE_WRITE_RETRIES = 1   # pre_write_validate 失败时 chapter_design 最多重做 1 次
MAX_DESIGN_ITERATIONS = 1   # prose_consistency 严重偏离时 chapter_design 最多重做 1 次
```

### post_write_check 的 6 项门禁

1. **字数** — 与目标 ±20% 区间
2. **标点归一** — 全角→半角（副作用：归一化后正文回写到 `state.prose_draft`）
3. **AI 词模式** — substring 扫描 `综上所述` / `值得注意的是` / `不难发现` / `总而言之`
4. **退化检测** — 句子级 4-gram 重复率 ≥ 0.3 视为退化
5. **禁用词** — 黑名单 substring 扫描
6. **长度下限** — < 100 字视为不合格

### pre_write_validate 的 3 项检查

1. **beats 完整性** — 数量 ≥ 3，每条 4~120 字
2. **卷大纲契约** — 细纲是否呼应卷大纲 `objectives` 的关键词
3. **ReferenceGate** — `characters_in_scene` ⊆ `character_roster`，`location` ∈ `known_locations`

### prose_consistency 的三路分支

LLM 返回 `deviation_score` + `severity` + `recommendation`，路由决策（在 `validate_prose` 节点内部）：

| severity | iter | recommendation | → |
|---------|------|----------------|---|
| low / medium | 任意 | 任意 | `commit`（放行）|
| high | < MAX | 任意 | `chapter_design` (full redo) |
| high | ≥ MAX | `human_review` | `commit` + `interrupt_pending`（人在环）|
| high | ≥ MAX | 其他 | `commit` (best-effort) |

## 4. write_short 图（4 节点，最薄版）

```
route_scenario → write_prose → wordcount_checkpoint → tracking_commit → END
```

短篇不触发 design / validate 环节，直接调用 `NarrativeWriter`。

## 5. 测试

```bash
# 在 backend/ 下
pytest -q
```

测试覆盖（80+ 用例）：
- `WordcountService`（CJK / ASCII / 混合 / checkpoint 通过/失败）
- `OutlineValidator` / `OutlinePreValidator` / `ProsePostChecker`（规则工具）
- `ChapterDesigner` / `ProseConsistencyChecker`（LLM agent 的 JSON 解析 + fallback）
- **write_long 图**：节点存在性、2 组条件边、2 组 routing 决策 + validate_prose 6 路分支端到端
- **铁律**：agent / graphs 不能 import `repository` / `models`（AST 扫描守）

## 6. 切换真实 LLM

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

`LLM_PROVIDER=mock`（默认）：返回每个 role 的预置 payload，**无需任何 API key**。

### 各 role 在 mock 模式下的行为

| role | 预置输出 |
|------|------|
| `intent_router` | `write_long` |
| `narrative_writer` | 雾港题材第 1 章预置正文 |
| `chapter_designer` | 雾港细纲 JSON（opening_hook / 3 beats / characters 等） |
| `prose_consistency` | `severity=low, recommendation=pass` |
| `scan_explorer` | 雾港题材扫榜 mock 报告 |

## 7. API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/healthz` | GET | 健康检查 |
| `/api/projects` | POST | 建项目 |
| `/api/write` | POST | **直接调 `write_long` 图**（保留旧入口） |
| `/api/router` | POST | **统一入口** — 自动意图识别 + 分发 |

### 端到端 demo（curl）

```bash
# 1. 健康检查
curl -s http://localhost:8082/api/healthz

# 2. 建项目
curl -s -X POST http://localhost:8082/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"slug":"wugang-demo","title":"雾港来客","genre":"都市悬疑","platform":"fanqie"}'

# 3. 写第 1 章（自动识别意图为 write_long）
curl -s -X POST http://localhost:8082/api/router \
  -H 'Content-Type: application/json' \
  -d '{"project_id":1,"user_input":"回到雾港的夜晚","explicit_scenario":"auto"}'
```

返回包含：

- `intent` / `graph_invoked` — 实际命中的图
- `state_revision` — 项目状态版本号（每次落库 +1）
- `final_wordcount` — 最终字数
- `stages[]` — 节点进度数组（含子节点折叠事件）
- `notice` — 如果校验失败但已 best-effort 落库，会有提示

## 8. 已知 demo 限制

| 项 | demo 行为 | 生产应做 |
|---|---|---|
| 字数不足 | 6 项门禁拦下，触发重写 | 已实现 (`ProsePostChecker`) |
| 剧情偏离 | LLM 轻校验，触发重做或人工审核 | 已实现 (`ProseConsistencyChecker`) |
| Reference Gate | 仅校验出场人物/地点，未校验引用内容 | `OutlinePreValidator` 已支持 `character_roster` / `known_locations`，需 DB schema 落地 |
| 并发写同章 | last write wins | Redis lock:chapter:* |
| 长会话 | 不压缩 context | 召回 + budget 切片 |
| Checkpoint | 不持久化 | 接 `langgraph-checkpoint-postgres` |
| interrupt_human | demo 用 `interrupt_pending` flag，API 层可检测 | 接 LangGraph `interrupt_before` 真暂停 |