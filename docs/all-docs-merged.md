# auto_novels · 全文档合并版

> 本文件为 `docs/` 目录下 9 份原始文档合并而成的单一 Markdown 文档，便于整体阅读与离线分发。
> 合并日期：2026-09-27
> 共计：9 节 / 3408 行 / 约 150 KB

---

## 目录

- [§1 README — 文档索引](#1-readme--文档索引)
- [§2 oh-story-langgraph-mcp-decomposition — 总体设计](#2-oh-story-langgraph-mcp-decomposition--总体设计)
- [§3 langgraph-status-v0.1 — 实施状态](#3-langgraph-status-v01--实施状态)
- [§4 graph-topology-v0.1 — 图拓扑规范](#4-graph-topology-v01--图拓扑规范)
- [§5 schema-pg-v0.1 — Schema 设计说明](#5-schema-pg-v01--schema-设计说明)
- [§6 schema-pg-v0.1.sql — 基础 SQL](#6-schema-pg-v01sql--基础-sql)
- [§7 schema-pg-v0.2.sql — v0.2 补丁 SQL](#7-schema-pg-v02sql--v02-补丁-sql)
- [§8 chapter-summary-v0.1 — 章节摘要设计](#8-chapter-summary-v01--章节摘要设计)
- [§9 short-story-june-14 — 短篇样稿](#9-short-story-june-14--短篇样稿)

---

# §1 README — 文档索引


---


---

# docs/ · 文档索引

> auto_novels 项目的全部设计文档与 SQL 落地。
> 最后更新：2026-09-27

---

## 文档地图

```
docs/
├── README.md                                  ← 本文件（索引）
│
├── [设计层] 设计文档 / 权威规范
│   └── oh-story-langgraph-mcp-decomposition.md  总体设计（路由/图/服务/MCP）
│
├── [SQL 层] 数据库 schema
│   ├── schema-pg-v0.1.sql                       基础 schema（19 张表 + 1 VIEW + 1 函数）
│   ├── schema-pg-v0.1.md                        v0.1 设计说明 + 应用步骤 + FAQ
│   └── schema-pg-v0.2.sql                       v0.2 补丁（chapter_records + analysis_chapters 扩展）
│
├── [设计层] 子模块设计
│   └── chapter-summary-v0.1.md                  章节摘要设计（A 自己写 / B 拆别人的书）
│
└── [产出层] 示例
    └── short-story-june-14.md                   按 WriteGraph 短篇分支手工跑通的样稿
```

---

## 文档关系图

```
                        oh-story-langgraph-mcp-decomposition.md (设计权威)
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
        schema-pg-v0.1.sql  chapter-summary-v0.1.md  ...
                │                 │
                ▼                 │
        schema-pg-v0.2.sql ───────┘  (v0.2 落地 chapter_summary 设计)
                │
                ▼
        schema-pg-v0.1.md (应用指南)
        
        short-story-june-14.md (短篇示例, 验证设计可行性)
```

---

## 阅读顺序建议

| 你是谁 | 阅读顺序 |
|---|---|
| **新加入项目** | 1) oh-story-langgraph-mcp-decomposition.md（整体设计）<br>2) schema-pg-v0.1.md（数据库基础）<br>3) chapter-summary-v0.1.md（核心模块）<br>4) short-story-june-14.md（看实际产出） |
| **后端工程师（搭库）** | 1) schema-pg-v0.1.md → 应用 v0.1.sql<br>2) 应用 schema-pg-v0.2.sql<br>3) 等 Redis schema / Service 骨架 |
| **Agent 工程师（写图节点）** | 1) oh-story-langgraph-mcp-decomposition.md §3（LangGraph 节点拆解）<br>2) chapter-summary-v0.1.md（如何填字段） |
| **Prompt 工程师 / LLM 调优** | 1) chapter-summary-v0.1.md §4-5（Pydantic schema / Prompt）<br>2) short-story-june-14.md（手写稿作为风格参考） |

---

## 各文件用途速查

### 设计层

| 文件 | 用途 | 何时更新 |
|---|---|---|
| `oh-story-langgraph-mcp-decomposition.md` | 总体架构设计（设计权威源） | 系统结构变更时 |
| `chapter-summary-v0.1.md` | 章节摘要子模块设计 | 摘要字段/算法变更时 |

### SQL 层

| 文件 | 用途 | 依赖 |
|---|---|---|
| `schema-pg-v0.1.sql` | 基础 schema（19 表 + 视图/函数/触发器） | 无 |
| `schema-pg-v0.2.sql` | v0.2 增量补丁（chapter_records / analysis_chapters 扩展） | 必须先应用 v0.1 |
| `schema-pg-v0.1.md` | v0.1 应用步骤 + 设计取舍 FAQ | 与 v0.1.sql 同步 |

### 产出层

| 文件 | 用途 | 备注 |
|---|---|---|
| `short-story-june-14.md` | 短篇示例成稿（约 2900 字） | 手工模拟 WriteGraph 短篇分支产出，非 LLM 真实跑 |

---

## 待补文档（路线图）

| 序 | 文档 | 触发条件 | 优先级 |
|---|---|---|---|
| 1 | `schema-redis-v0.1.md` | 启动 Redis 热层实现时 | 高 |
| 2 | `services-overview-v0.1.md` | 写第一个 Service 之前 | 高 |
| 3 | `graph-nodes-spec-v0.1.md` | 开始写 LangGraph 节点时 | 中 |
| 4 | `migration-fs-to-pg-v0.1.md` | 设计 FS → DB 迁移脚本时 | 中 |
| 5 | `deployment-v0.1.md` | docker-compose / 启动脚本 | 中 |
| 6 | `testing-strategy-v0.1.md` | 写 pytest 框架前 | 低 |

---

## 版本管理约定

| 类别 | 版本号规则 | 示例 |
|---|---|---|
| 设计文档 | `v0.X.md` | `chapter-summary-v0.1.md` |
| SQL 落地 | `schema-pg-vX.Y.sql` | `schema-pg-v0.2.sql`（v0.X 主版本，v0.X.Y 补丁） |
| 样稿 / 示例 | 无版本号 | `short-story-june-14.md`（一次性产出） |

**主版本号变更 = 设计调整**（破坏性）；**补丁号变更 = 增量字段**（向后兼容）。

---

## 引用约定

文档之间的交叉引用使用相对路径：

```markdown
参见 schema-pg-v0.1.sql §2（追踪表）
参见 oh-story-langgraph-mcp-decomposition.md §3.4
```

外部引用：

```markdown
参见 [langgraph checkpointer 文档](https://langchain-ai.github.io/langgraph/concepts/persistence/)
```
---

# §2 oh-story-langgraph-mcp-decomposition — 总体设计


---

# oh-story-claudecode → LangGraph + 服务层/MCP 拆解设计

> 目标：把 [oh-story-claudecode](https://github.com/zenstory-ai/oh-story-claudecode)（网文写作 Claude Code skill 包）重构为 **LangGraph 图 + 服务层** 架构。
>
> **本文件是"拆什么"的权威设计源**；配套落地文档：
> - 数据库 schema：schema-pg-v0.1.sql（基础） + schema-pg-v0.2.sql（摘要扩展补丁）
> - schema 应用指南：schema-pg-v0.1.md
> - 章节摘要子模块设计：chapter-summary-v0.1.md（§3.3 / §3.4 涉及的 chapter_records 与 analysis_chapters 字段定义）
> - 文档索引：README.md
>
> 核心思路：原系统里 LLM（Claude）是编排者，`SKILL.md` 是带流程的人肉 prompt，`scripts/*` 是确定性自动化，7 个 subagent 是分角色 LLM，`hooks` 是生命周期硬守卫。拆解后：
> - **LangGraph 节点** = 流程步骤（LLM 推理节点 + 服务节点 + 路由节点）
> - **服务层** = 确定性能力（Python service 函数，图节点直接调用）
> - **MCP** = 可选封装层（同一服务对外暴露，供外部工具复用）
> - **Agent 节点** = 原 7 个 subagent 角色，作为可复用的 LLM 节点（`create_agent`）

## 0. 本系统边界（相对原系统的两个调整）

1. **不需要部署**：原 `story-setup` 负责把 agents/hooks/settings 部署到外部 CLI（claude-code/codex/antigravity…）。本系统是自包含的 Python + LangGraph 应用，**不对外部环境部署任何东西**——SetupGraph 及其部署工具全部移除；7 个 agent 直接内嵌为图内 agent 节点。
2. **存储改为数据库（PostgreSQL + Redis）**：文件系统不再是数据库。**PostgreSQL 为唯一权威（系统真值）**，**Redis 为长期记忆热层**（只缓存派生读取结果，可从 PG 重建，可随时回填），通过 repository/service 层访问；派生视图由服务确定性重建，**LLM 一律不得直写数据表**。文件系统仅保留外部二进制资产（封面图）。

---

## 1. 原系统结构盘点

### 13 个 skill（工作流）

| Skill | 作用 | 关键流程 |
|------|------|---------|
| `story` | 路由入口 + 作者记忆 + Dashboard + 版本检查 | 意图分类 → 路由 |
| `story-setup` | 部署基础设施（hooks/agents/rules/AGENTS） | **不在本系统内实现**（见 §0） |
| `story-long-scan` | 长篇扫榜 | 采集 → 清洗 → 分析 → 报告 → 选题决策 |
| `story-long-analyze` | 长篇拆文 | Stage 0-6 拆解管道 |
| `story-long-write` | 长篇写作 | 开书(3阶段) → 单章写作 → 日更循环 |
| `story-short-scan` | 短篇扫榜 | 同 long-scan |
| `story-short-analyze` | 短篇拆文 | Stage 2-6 拆解管道 |
| `story-short-write` | 短篇写作 | 情绪目标 → 核心框架 → 成稿 |
| `story-review` | 多视角对抗审查 | full/lean/solo → 并行 reviewers → 综合 |
| `story-deslop` | 去 AI 味 | 扫描 → 分级 → 7 Gate → 确定性收尾 |
| `story-import` | 逆向导入 | 拆解管道 + 结构迁移 + 追踪初始化 |
| `story-cover` | 封面生成 | GPT-Image-2 |
| `browser-cdp` | 浏览器自动化 | CDP 抓取/登录态 |

### 7 个 agent（分角色 LLM）

| Agent | 模型档 | 职责 |
|-------|-------|------|
| `story-architect` | opus/高端 | 题材、世界观、大纲、钩子/反转、情绪弧线 |
| `narrative-writer` | sonnet/中端 | 正文写作、去 AI 味执行 |
| `character-designer` | sonnet/中端 | 角色、对话、人物弧线 |
| `story-researcher` | sonnet/中端 | 外部资料研究 |
| `chapter-extractor` | haiku/低端 | 单章情节点提取（只读） |
| `consistency-checker` | haiku/低端 | 事实一致性（只读） |
| `story-explorer` | haiku/低端 | 查询故事工程状态（只读） |

### 确定性能力（原 `scripts/*`，改为 Python service）

追踪（`tracking_commit.py` init/commit/check）、字数（`storyctl.py` wordcount/chapter）、AI 检测（`check-ai-patterns.js`）、退化检测（`check-degeneration.js`）、标点归一（`normalize-punctuation.js`）、作者记忆（`author_memory_commit.py`）、大纲契约校验（`check-outline-contract.js`）、榜单采集器（qidian/fanqie/qimao/jjwxc/ciweimao）、Dashboard（`dashboard-server.mjs`）。全部改写/封装为 DB 驱动的 Python service（§4），不再操作文件。

### hooks（生命周期守卫）

`SessionStart/End`、`PreCompact/PostCompact`、`PreToolUse`（写正文前必须有大纲）、`PostToolUse`（写后质量扫描）——这些在 LangGraph 里变成**图内守卫节点**（写正文前校验、写后质量扫描），不再部署为文件 hooks。

---

## 2. 总体架构

```
                         ┌─────────────────────────────────┐
   用户输入 ───────────► │  RouterGraph (对应 story skill)  │
                         │  intent_router → 条件路由         │
                         └──────┬──────┬──────┬──────┬──────┘
                                ▼      ▼      ▼      ▼
                        ScanGraph Analyze  WriteGraph  import/cover
                                          │
                             ┌────────────┼────────────┐
                             ▼            ▼            ▼
                        ChapterWrite   ReviewGraph   DeslopGraph
                             │
                             ▼
                     TrackingService.commit (DB 事务)
```

**服务层**：所有确定性能力实现为 Python service（DB 事务 / 字数 / 质量门禁 / 采集 / 记忆装配），图节点直接函数调用；对外可选 MCP 封装（§4）。
**存储层**：PostgreSQL（系统真值）+ Redis（长期记忆热层）双层，repository 层负责所有读写，Graph state 只保存 ID 与中间产物（§2.1、§2.2）。

### 2.1 存储层设计（文件系统 → PostgreSQL）

> 数据模型分层：**规范化可查询表**（项目/卷/章/角色/伏笔/时间线）+ **JSONB 快照列**（追踪状态原样兼容）。派生视图由服务确定性重建。**PostgreSQL 是唯一权威**；Redis 作为长期记忆热层只缓存派生读取结果（§2.2）。

| 数据域 | 原文件系统 | 数据库表 | 说明 |
|--------|-----------|---------|------|
| 项目 | `{书名}/` + `.active-book` | `projects(id, slug, title, genre, platform, status, created_at, updated_at)` | `status='active'` 标记当前书 |
| 设定 | `设定/*.md` | `settings(project_id, kind, title, content, updated_at)` | kind ∈ {关系, 题材定位, 题材正文提示卡, 世界观, 金手指, 势力} |
| 大纲 | `大纲/` 卷纲+逐章细纲 | `volumes(project_id, no, title, synopsis)` + `outline_chapters(volume_id, chapter_no, title, beats_jsonb, contract_status)` | 卷↔章外键 |
| 正文 | `正文/{chapter}.md` | `chapters(project_id, chapter_no, volume_id, title, content, wordcount, status, revision, created_at, updated_at)` | UNIQUE(project_id, chapter_no)；status ∈ {draft, committed}；wordcount 提交时校验 |
| 追踪权威状态 | `追踪/_tracking-state.json` | `tracking_state(project_id, state_revision, last_committed_chapter, state_jsonb)` | **JSONB 原样兼容原格式**，唯一真值源 |
| 角色状态 | `追踪/角色状态/*.md` | `characters(project_id, name, kind, profile_jsonb, active_status)` | 提交事务联动 |
| 伏笔 | `追踪/伏笔.md` | `foreshadowing(project_id, id, content, planted_chapter, resolved_chapter, status)` | |
| 时间线 | `追踪/时间线/作者真相.md` + `读者已知.md` | `timeline_events(project_id, chapter_no, author_only, content)` | `author_only` 区分作者真相/读者已知 |
| 逐章记录 | `追踪/逐章记录/` | `chapter_records(project_id, chapter_no, context, characters, events, foreshadowing)` | 派生，仅由提交事务重建 |
| 上下文视图 | `追踪/上下文.md`（固定 7 列 ≤12KB） | 视图/物化表 `context_views` | 确定性函数 `build_context_view(project_id)` |
| 拆文库（单章） | `拆文库/{书名}/第N章_摘要.md` | `analysis_chapters(book_id, chapter_no, summary, beats_jsonb)` | stage2_extract 输出，按章 upsert |
| 拆文库（聚合） | `拆文库/{书名}/剧情|节奏|情绪|角色|设定|关系|报告|文风` | `analysis_aggregates(book_id, kind, content)` | kind ∈ {plot, rhythm, emotion, settings, characters, relations, report, style} |
| 拆解进度 | `拆文库/{书名}/_progress.md` | `analysis_progress(book_id, stage, status)` | 断点恢复 |
| 作者记忆 | `.story/作者记忆/` | `author_memory(id, kind, content, scope, active, created_at)` | append-only |
| 对标 | `对标/{书名}/` | `benchmarks(project_id, book_title, content, is_primary)` | |
| 参考资料 | `参考资料/` | `reference_materials(project_id, title, content, kind)` | Reference Gate 检查该表 |
| 扫榜数据 | `扫榜/` | `scan_results(platform, snapshot_at, raw_jsonb, cleaned_jsonb, report)` | append-only |
| 封面 | `covers/{书名}/` | `covers(project_id, path)` | 二进制留磁盘，DB 存路径 |

**索引/能力**：`chapters(project_id, chapter_no)` 唯一索引；`characters(project_id, name)`；`timeline_events(project_id, chapter_no)`。预留 **pgvector**（情绪模块/伏笔语义召回）、**pg_trgm / zhparser**（拆文库中文检索）。迁移用 Alembic。

> **→ 落地 SQL**：本节 19 张表的完整 DDL 见 schema-pg-v0.1.sql。已合入的补丁字段（`chapter_records` 10 个、`analysis_chapters` 8 个）见 schema-pg-v0.2.sql，字段定义与 JSON Schema 见 chapter-summary-v0.1.md。

### 2.2 长期记忆（PostgreSQL + Redis）

记忆分三层，PG 是唯一权威，Redis 只做热读取：

| 层 | 载体 | 内容 | 失效/重建 |
|----|------|------|----------|
| 持久层（真值） | PostgreSQL | 全部业务数据（§2.1），含 `author_memory`、`tracking_state`、`chapters`、`analysis_*` | 任何写入必须落 PG 事务 |
| 长期记忆热层 | Redis | 写作 agent 高频读取的**派生**知识（见下） | 全部可从 PG 重建，可随时回填 |
| 工作记忆 | LangGraph checkpointer（Postgres） | 进行中的图执行状态 | 会话结束即弃 |

Redis 热层条目：

- `mem:author:{project_id}:{kind}` — 作者记忆 hot set（会话开始装载，query 直取，≤2KB/条）
- `ctx:view:{project_id}:{revision}` — 上下文视图（固定 7 列 ≤12KB）；`TrackingService.commit` 时写透，key 带 `state_revision` 防串版本
- `ctx:recall:{project_id}:{revision}` — write_prep 召回包（情绪模块 + 节奏参考 + 题材卡 + 文风），随 commit 失效
- `emb:*` — 语义检索结果缓存（pgvector 命中缓存）
- `scan:{platform}:{snapshot_at}` — 扫榜快照缓存（TTL）
- `lock:chapter:{project_id}:{chapter_no}` — 章节提交分布式锁（多写作 agent 并发时 `SET NX` 串行化提交）
- `sess:{session_id}` — 会话级工作记忆（本批次临时 segment、评审中间产物）

一致性规则（硬约束）：

1. **Redis 永远是派生层**：每条目都能从 PG 确定性重建，可 `FLUSHDB` 后由服务回填。
2. **写路径唯一入口是服务层**：只有 `TrackingService.commit` / `ChapterService.commit` 等能写 PG；Redis 条目由这些服务同步写透或失效（write-through / invalidate）。
3. **版本守卫**：上下文/召回缓存 key 带 `state_revision`，读取时校验，不匹配即回源 PG 重建。
4. **不引入双真值**：伏笔/角色/时间线等可写实体的权威只在 PG；Redis 只缓存"装配好的读取结果"，不缓存可写领域实体。
5. **向量只留一处**：语义检索以 pgvector 为权威，Redis 不另开向量索引，避免双套检索。

---

## 3. LangGraph 节点拆解

### 3.0 共享状态

```python
class StoryState(TypedDict):
    # 会话
    user_input: str
    messages: Annotated[list, add_messages]
    intent: str                     # router 输出
    # 项目
    project_id: int                 # DB 项目 ID（替代 project_root/book_dir）
    # 写作
    scenario: str                   # open_book / write_chapter / daily / revision
    chapter_no: int
    # 拆解
    source_book_id: int
    chapter_boundaries: list[dict]
    stage_progress: dict
    # 审查
    review_mode: str                # full / lean / solo
    findings: list[dict]
    # 通用产物
    report: str
    errors: list[str]
```

### 3.1 RouterGraph（story skill）

| 节点 | 类型 | 逻辑 |
|------|------|------|
| `intent_router` | LLM + tool | 从用户输入提取意图（写长篇/短篇、拆文、扫榜、审查、去味、导入、封面、查状态…） |
| `project_lookup` | 服务节点 | 查 `projects` 表：存在/活跃书/完成度，供路由决策（替代原 `.story-deployed` 探测） |
| `author_memory` | 服务节点 | 读/写作者记忆（MemoryService.query/record） |
| `dashboard` | 服务节点 | 启动/停止本地 Dashboard（读 DB 展示进度） |

**边**：`intent_router` 条件路由 → 子图（scan/analyze/write/review/deslop/import/cover/browser）。

### 3.2 ScanGraph（story-long-scan / story-short-scan）

| 节点 | 类型 | 逻辑 |
|------|------|------|
| `confirm_platform` | LLM 交互 | 确认平台 + 方向 |
| `collect_rankings` | 服务节点 | 调榜单采集器（按平台选 qidian/fanqie/qimao/jjwxc/ciweimao/dz/heiyan），结果写 `scan_results` |
| `clean_data` | LLM + 规则 | 数据清洗（模板文本剔除、解析串行、字段补采、简介截断），写回 `cleaned_jsonb` |
| `validate_quality` | 服务节点 | 完整性检查（≥15 条、必填字段、质量状态） |
| `analyze_trends` | LLM | 题材分布/新题材/书名模式/标签热词 |
| `generate_report` | LLM | 扫榜报告 |
| `topic_decision` | LLM | 选题四步 → 选题决策（硬规则：样本不足禁给"高"可行性） |

### 3.3 AnalyzeGraph（story-long-analyze）— 拆解管道

**最标准的"管道"，Stage 0-6 一一对应节点；输出全部进 `analysis_*` 表。**

| 节点 | 类型 | 逻辑 |
|------|------|------|
| `stage0_overview` | LLM | 概要 + **章节边界表**（唯一切片真值，写 `analysis_progress`） |
| `stage1_golden3` | LLM | 前 3 章深度拆解（`analysis_aggregates` kind=golden） |
| `stage1_checkpoint` | 条件路由 | 产出快速预览后询问是否继续全量（或按预设跳过） |
| `stage2_extract` | **map** | 逐章 spawn `chapter-extractor` 节点（批量 5-8 并行，`Send` API）→ `analysis_chapters` 按章 upsert |
| `stage2_validate` | 服务节点 | 机械校验：情节点数、白描字段、标签枚举（对 `analysis_chapters` 行）；失败 sonnet 重试一次 |
| `stage2_merge` | 服务节点 | 聚合 `analysis_chapters` → 章节摘要汇总（无损检查） |
| `stage3_aggregate` | LLM | 剧情聚合 → `analysis_aggregates`(plot/rhythm/emotion) + 角色合并/分级 |
| `stage4a_settings` | LLM | 世界观/金手指/势力（与 Stage 3 并行） |
| `stage4b_characters` | LLM | 角色完整档案（依赖 Stage 3 角色合并） |
| `stage4c_relations` | LLM | 角色关系提取（依赖 4b） |
| `stage5_report` | LLM | 拆文报告 + 全书概要（500-1000 字） |
| `stage6_style` | LLM | 文风（句长/标点/潜台词 + 原文锚点） |
| `progress_tracker` | 服务节点 | 每阶段写 `analysis_progress`（断点恢复） |

**并行结构**：`stage2_extract` map 完成后 → `stage3_aggregate` 与 `stage4a_settings` 并行 → `stage4b` → `stage4c` → `stage5` → `stage6`。

### 3.4 WriteGraph（story-long-write）— 最复杂

**场景路由 → 3 阶段开书 / 单章写作 / 日更循环 / 大修。**

| 节点 | 类型 | 逻辑 |
|------|------|------|
| `route_scenario` | LLM | 按匹配优先级：大修 > 写指定章 > 补纲 > 日更 > 开书；裸调用只诊断不停靠 |
| `phase1_topic` | LLM | 选题确认 + 对标发现 → `settings` + `benchmarks` 行 |
| `phase2_settings` | LLM | 核心设定：关系/题材定位/题材正文提示卡 → `settings` 行 |
| `phase3_outline` | LLM | 全书卷纲 + 逐章细纲（含大纲安全七检）→ `volumes` + `outline_chapters` |
| `validate_outline` | 服务节点 | `check_outline_contract` 对 `outline_chapters` 结构验收 |
| `write_prep` | LLM + service | 经 ContextService 装配召回包（追踪上下文 + 情绪模块 + 节奏 + 题材卡 + 文风，Redis 热层直取 + 版本守卫）；**Reference Gate**：查 `reference_materials` 主契约记录缺失即 fail-fast |
| `write_prose` | LLM agent | 调 `narrative-writer` 节点写正文（分两段临时 segment，只消费批准情节点），结果暂存 chapters(draft) |
| `wordcount_checkpoint` | 服务节点 | `wordcount_checkpoint`（对 DB 章节内容）非对称收口 |
| `quality_scan` | 服务节点 | `check_ai_patterns` / `check_degeneration` / `normalize_punctuation` / 禁用词（读 DB 正文） |
| `quality_review` | LLM | 章尾钩子、爽点、情绪核对（可证伪双查） |
| `tracking_commit` | 服务节点 | `chapter_commit` + `tracking_commit`（**DB 原子事务**：章节提交 + 角色/伏笔/时间线/派生视图重建 + revision 递增） |
| `snapshot_checkpoint` | 服务节点 | 每 3 章一致性检查 + 数据快照 |

**日更循环**：`route_scenario=daily` 时在 `write_prep→...→tracking_commit` 间循环 2-3 章（带 chapter_no 的条件边实现）。

### 3.5 ReviewGraph（story-review）

| 节点 | 类型 | 逻辑 |
|------|------|------|
| `preflight` | LLM + service | 解析 full/lean/solo；子代理递归守卫；决定 Effective Mode + Fallback |
| `deterministic_precheck` | 服务节点 | `normalize_punctuation --check` + `check_ai_patterns --fail-on=blocking` + `check_degeneration --check` |
| `load_rubric` | 服务节点 | 按平台（fanqie/qidian/zhihu）加载 rubric，不可读用内置 fallback |
| `fan_out_reviewers` | **map** | 并行 spawn 4 个 reviewer 节点（story-architect/character-designer/narrative-writer/consistency-checker），各返回 VERDICT+FINDINGS（经 repository 读正文/追踪） |
| `aggregate_findings` | LLM | 合并去重、按 S1-S4 排序、呈现 Agent 分歧（不自动妥协） |
| `fact_check` | LLM agent | 可选 spawn `story-researcher` 核查外部事实 |
| `output_report` | LLM | 按 full/lean/solo 模板输出（英文 key 元数据 + Findings Schema） |
| `tracking_maintenance` | 服务节点 | full/lean 模式用 `tracking_commit` 更新追踪（solo 不改） |

**并行结构**：`fan_out_reviewers` 用 `Send` 并行 → 汇合到 `aggregate_findings`。

### 3.6 DeslopGraph（story-deslop）

| 节点 | 类型 | 逻辑 |
|------|------|------|
| `ai_scan` | 服务 + LLM | `check_ai_patterns` 预检 + AI 味检测报告（问题标记表 + Gate 列） |
| `classify_severity` | LLM | 六指标量化定档：轻度/中度/重度 → 决定过哪些 Gate |
| `gate_processing` | LLM agent | 逐项执行 Gate A-G（禁用词/句式/心理外化/节奏/对话/结尾/解释腔）；优先判"能否删除"，超删除比例上限标 `[需复核]`；改写写回 chapters |
| `deterministic_finish` | 服务节点 | `check_ai_patterns` 复扫 + `check_degeneration` + `normalize_punctuation` 机械兜底 |
| `output_report` | LLM | 润色报告（字数协议 + 修改统计 + 对比） |

### 3.7 ImportGraph（story-import）

| 节点 | 类型 | 逻辑 |
|------|------|------|
| `confirm_source` | LLM 交互 | 确认书名/题材/平台/完本状态/篇幅类型/最后章完整性 |
| `length_routing` | 服务 + LLM | `wordcount_measure`（对导入内容）+ 规则判断长短篇 |
| `run_analyze` | **子图调用** | 复用 AnalyzeGraph（长篇 Stage 0-6 / 短篇管道），跳过停靠询问 |
| `migrate_structure` | LLM + service | 拆文库（`analysis_*` 表）→ 项目结构映射（3-L 长篇 / 3-S 短篇）：填充 settings/volumes/outline_chapters |
| `migrate_chapters` | 服务节点 | 正文标准化（章节切分、补零、命名）→ `chapters` 表 |
| `reverse_outline` | LLM | 从拆解反推 卷纲/细纲（用户确认卷界） |
| `init_tracking` | 服务节点 | `tracking_init` + `tracking_check`（一次性生成，**禁止手写**） |
| `bind_benchmark` | 服务节点 | 外部对标资产同步 → `benchmarks` |
| `activate_project` | 服务节点 | `projects.status='active'` + 质量检查 + 导入报告 |

### 3.8 叶子节点

| 节点 | 类型 | 逻辑 |
|------|------|------|
| `story_cover` | LLM + service | 收集书名/作者/平台 → 题材风格分析 → 调 image 生成 → 落盘 `covers/{书名}/` + `covers` 表记录 + 平台尺寸导出 |
| `browser_session` | 服务节点 | CDP 启动/导航/求值/抓取（供采集） |

### 3.9 原 7 个 Agent → LangGraph agent 节点

用 `create_agent` 定义，带各自 system prompt + 工具白名单 + 模型档：

```python
story_architect = create_agent(
    "claude-opus-5", system=AGENT_PROMPTS["story_architect"],
    tools=[memory_query, repo_read_settings, repo_write_settings, ...])
chapter_extractor = create_agent(
    "claude-haiku-4-5", system=AGENT_PROMPTS["chapter_extractor"],  # 只读
    tools=[repo_read_chapter], max_turns=12)
```

在图中被调用（`Command(goto=...)` / `Send(...)` 并行）。原 `story-explorer` 的语义查询（伏笔/角色当前状态/进度）用 repository 只读服务提供；保留 agent 形式用于更自然的语义追问。

> **→ 字段落地**：§3.3 `stage2_extract` 节点产出的 `analysis_chapters.beats_jsonb`、§3.4 `tracking_commit` 节点产出的 `chapter_records` 摘要字段，结构化定义见 chapter-summary-v0.1.md（Pydantic schema + Prompt + 实现骨架）。

---

## 4. 服务层 + 可选 MCP

> 设计原则：**服务层优先**。所有确定性能力是 Python service 函数，LangGraph 节点直接 import 调用；如需给外部工具复用，用薄的 MCP server（`story-mcp`）包一层。服务层按聚合拆分，DB 操作走 repository，追踪/章节提交是唯一的多表事务入口。

### 4.1 服务层结构

```
services/
  tracking.py      TrackingService: init / commit / check       ← 追踪唯一写入口
  wordcount.py     WordcountService: measure / checkpoint / evaluate
  chapter.py       ChapterService: check / commit / accept_length / draft
  quality.py       QualityService: ai_patterns / degeneration / punctuation / banned_words / outline_contract
  memory.py        MemoryService: record / query
  scan.py          ScanService: 各平台采集 + 清洗 + 校验
  cover.py         CoverService: 封面生成 + 尺寸导出
  dashboard.py     DashboardService: 启动/停止/状态
  context.py       ContextService: 装配召回包/上下文视图（写透 Redis，PG 回源）
  redis_store.py   RedisStore: 热层读写 + state_revision 版本守卫
repositories/      repository/dao 层（只做 CRUD，无业务规则）
schemas/           SQLAlchemy 模型 + Alembic 迁移
```

### 4.2 追踪与字数（内核）

| 服务函数 | 原脚本 | 输入 → 输出 | 调用点 |
|---------|--------|------------|--------|
| `TrackingService.init` | `tracking_commit.py init` | `{project_id, input_json}` → 生成追踪结构与权威状态 | ImportGraph / 开书 |
| `TrackingService.commit` | `tracking_commit.py commit` | `{project_id, transaction_json}` → 逐章事务（append/revision）**单事务** | WriteGraph / ReviewGraph |
| `TrackingService.check` | `tracking_commit.py check` | `{project_id}` → `{last_committed_chapter, state_revision, 视图一致性}` | 所有写前节点 |
| `WordcountService.measure` | `storyctl.py wordcount measure` | `{chapter_id}` → `{metric, actual}` | ImportGraph / 字数审计 |
| `WordcountService.checkpoint` | `storyctl.py wordcount checkpoint` | `{chapter_id, target}` → `actual/remaining_user_range` | WriteGraph 非对称收口 |
| `WordcountService.evaluate` | `storyctl.py wordcount evaluate` | `{chapter_id, target}` → in-range 判定 | WriteGraph |
| `ChapterService.check` | `storyctl.py chapter check` | `{project_id, chapter_no}` → `{status: in_range/under/over}` | WriteGraph |
| `ChapterService.commit` | `storyctl.py chapter commit` | `{project_id, chapter_no, transaction}` → 原子提交 | WriteGraph |
| `ChapterService.accept_length` | `storyctl.py chapter accept-current-length` | `{project_id, chapter_no}` → 接受自然长度 | WriteGraph |

**关键设计约束（原系统铁律，DB 版）**：追踪表 + 派生视图（`context_views` / `chapter_records` / 角色/伏笔/时间线联动）只能经 `TrackingService.commit` / `ChapterService.commit` 写入，**禁止 LLM 节点直接改库**。commit 在单一 PG 事务内完成（章节状态 + 追踪状态 + 派生重建 + revision 递增），比原 JSON 文件原子写更稳。

### 4.3 质量门禁

| 服务函数 | 原脚本 | 输入 → 输出 | 调用点 |
|---------|--------|------------|--------|
| `QualityService.ai_patterns` | `check-ai-patterns.js` | `{chapter_id / text, fail_on}` → blocking/advisory findings | Deslop / Review / Write 质量节点 |
| `QualityService.degeneration` | `check-degeneration.js` | `{chapter_id}` → 退化 findings | Deslop / Review |
| `QualityService.punctuation` | `normalize-punctuation.js` | `{chapter_id, check?, quote_mode}` → 归一或报告 | Deslop / Review |
| `QualityService.outline_contract` | `check-outline-contract.js` | `{project_id}` → 结构验收（对 `outline_chapters`） | WriteGraph phase3 |
| `QualityService.delivery_contract` | `check-delivery-contract.js` | `{project_id}` → 短篇契约校验 | WriteGraph 短篇 |
| `QualityService.banned_words` | banned-words.md + 扫描器 | `{chapter_id}` → 命中列表（含 `.deslop-whitelist` 豁免） | Deslop / Review / Write |

### 4.4 作者记忆

| 服务函数 | 原脚本 | 输入 → 输出 | 调用点 |
|---------|--------|------------|--------|
| `MemoryService.record` | `author_memory_commit.py record` | `{kind, content, scope}` → 回执（写 PG + Redis 写透） | Router / 各写作节点收尾 |
| `MemoryService.query` | `author_memory_commit.py query` | `{kinds}` → active 条目（≤2KB，Redis 直取、miss 回源 PG） | WriteGraph 写前 / Deslop / Review |

### 4.5 市场采集

| 服务函数 | 原脚本 | 输入 → 输出 | 调用点 |
|---------|--------|------------|--------|
| `ScanService.qidian` | `qidian-rank-scraper.js` | `{type(榜单)}` → `scan_results` | ScanGraph |
| `ScanService.fanqie` | `fanqie-rank-scraper.js` | `{channel, type, top}` → `scan_results` | ScanGraph |
| `ScanService.qimao` | `qimao-rank-scraper.js` | `{period}` → `scan_results` | ScanGraph |
| `ScanService.jjwxc` | `jjwxc-rank-scraper.js` | `{type, top, detail_limit}` → `scan_results` | ScanGraph |
| `ScanService.ciweimao` | `ciweimao-rank-scraper.js` | 榜单采集 | ScanGraph |
| `ScanService.dz_heiyan` | `dz-browse-scraper.js` / `heiyan-booklist-scraper.js` | 短篇榜单采集 | ScanGraph(短篇) |

> 依赖 CDP 的平台（番茄等）内部调用 browser 服务。采集器保留 Node 实现时用子进程调用，或逐步重写为 Python。

### 4.6 浏览器

`BrowserService.launch / navigate / evaluate / screenshot / close` — CDP 控制 Chrome，供采集与登录态场景（对应原 browser-cdp skill）。

### 4.7 其他

| 服务函数 | 原脚本 | 说明 |
|---------|--------|------|
| `DashboardService.start / stop` | `dashboard-server.mjs` | 本地写作工作台 HTTP 服务（读 DB） |
| `CoverService.generate` | GPT-Image-2 API | 封面生成（书名/作者/题材 → 图 + 平台尺寸） |

### 4.8 可选 MCP 封装

> 仅当需要外部工具复用同一能力时启用。用 `story-mcp`（tracking/wordcount/quality/memory）、`story-scan-mcp`、`browser-mcp` 三个薄 server 包住上述 service，内部仍是同一个 repository/DB。**本系统内的 LangGraph 节点不经过 MCP 协议。**

---

## 5. 对应关系总表

| 原系统 | LangGraph | 服务/MCP 工具 |
|--------|-----------|---------|
| story 路由 | RouterGraph.intent_router | — |
| story-setup | **不需要**（本系统自包含） | — |
| story-long-scan / short-scan | ScanGraph | ScanService 工具组 |
| story-long-analyze / short-analyze | AnalyzeGraph（Stage 0-6 节点）| 写 `analysis_*` 表 |
| story-long-write | WriteGraph（含日更循环）| TrackingService / WordcountService / ChapterService |
| story-short-write | WriteGraph 短篇分支 | 同上 |
| story-review | ReviewGraph（并行 reviewers）| QualityService 工具组 |
| story-deslop | DeslopGraph（7 Gate 节点）| QualityService |
| story-import | ImportGraph | TrackingService.init + WordcountService |
| story-cover | story_cover 叶子节点 | CoverService |
| browser-cdp | browser_session 节点 | BrowserService |
| chapter-extractor agent | AnalyzeGraph.stage2_extract 的 map 节点 | — |
| narrative-writer agent | WriteGraph.write_prose / DeslopGraph.gate_processing | — |
| story-architect agent | WriteGraph phase1-3 节点 / ReviewGraph reviewer | — |
| character-designer agent | ReviewGraph reviewer | — |
| consistency-checker agent | ReviewGraph reviewer | — |
| story-researcher agent | WriteGraph 资料研究节点 / ReviewGraph fact_check | — |
| story-explorer agent | 各图 context 加载节点 | TrackingService.check + repository 查询 |
| hooks（PreToolUse/PostToolUse…）| 图内守卫节点 | 写正文前置校验 / 写后质量扫描 |

---

## 6. 实现建议

1. **分层顺序**：先做存储层（SQLAlchemy 模型 + Alembic 迁移 + repository）→ 再 `TrackingService`/`WordcountService`/`QualityService`（确定性内核，可独立测试）→ 再搭 AnalyzeGraph 和 WriteGraph。
2. **追踪铁律保持**：追踪表 + 派生视图唯一写入口是 `TrackingService.commit`（PG 单事务），LLM 节点不得直写。
3. **并行策略**：`chapter-extractor` map 和 `reviewer` fan-out 用 `Send` API 实现真正的并行；批量受并发上限控制（原 5-8/批）。
4. **Reference Gate 保留**："写正文前必须完整读参考资料"做成 `write_prep` 的硬前置校验——查 `reference_materials` 表主契约记录（情绪模块/节奏/文风/题材卡），缺失即 fail-fast。
5. **停靠点（checkpoint）**：`stage1_checkpoint`、日更批次的用户确认，用图内条件边 + 中断（`interrupt_before`）实现人机协同。
6. **状态持久化**：PostgreSQL 为唯一真值源；LangGraph 用 Postgres checkpointer 恢复"进行中的图执行"（与业务库同源）。
7. **DB 选型理由（PostgreSQL vs MongoDB）**：追踪提交的多表原子性、卷↔章↔正文的强结构关系、派生视图确定性重建都需要真正的 ACID 事务与约束——PG 的单事务能力正是原系统最硬铁律的最省心落点；而原 `_tracking-state.json` 这类半结构化文档用 **JSONB 列** 即可零成本兼容。Mongo 的优势（schemaless 文档、无迁移）在本系统里被 JSONB 基本追平，而它缺失的正是我们需要的那两项能力。预留 pgvector（伏笔/情绪模块语义召回）与 pg_trgm/zhparser（拆文库中文检索）。Redis 承担长期记忆热层（§2.2），不承担权威存储。
8. **Python 实现**：原 Node 脚本（scrapers、质量检测器）用子进程调用或重写为 Python；追踪/字数逻辑已是 Python，直接落为 DB service。
9. **Redis 使用纪律**：只读热层、可重建、版本守卫、不经 Redis 提交业务写——防止 Redis 变成第二个真值源；`FLUSHDB` 永远安全。

---

## 7. 落地状态（v0.X）

| 子系统 | 设计文档 | 落地文件 | 状态 |
|---|---|---|---|
| 总体设计 | §1–§6（本文件） | — | ✓ 设计定稿 |
| PG Schema 基础 | §2.1 | schema-pg-v0.1.sql + schema-pg-v0.1.md | ✓ 已落地 |
| PG Schema 摘要扩展 | §2.1 / §3.3 / §3.4 | schema-pg-v0.2.sql + chapter-summary-v0.1.md | ✓ SQL 已落地，Service 实现待写 |
| Redis 热层规范 | §2.2 | （待写 schema-redis-v0.1.md） | ✗ 未开始 |
| 服务层骨架（service/Repository） | §4 | （待写 services-overview-v0.1.md） | ✗ 未开始 |
| LangGraph 节点 | §3 | （待写 graph-nodes-spec-v0.1.md） | ✗ 未开始 |
| 短篇示例成稿 | §3.4 短篇分支 | short-story-june-14.md | ✓ 手工跑通示例 |

---

## 8. 文档索引

完整文档地图见 README.md。

---

# §3 langgraph-status-v0.1 — 实施状态


---

# LangGraph 实施状态 v0.1

> 截至 2026-09-27 — auto_novels 项目的 LangGraph 设计与落地进度跟踪。
> 设计源：oh-story-langgraph-mcp-decomposition.md §3
> 实现位置：[backend/app/graphs/](../backend/app/graphs/) + [backend/app/agents/](../backend/app/agents/)

---

## 1. 总体进度

| 阶段 | 状态 |
|---|---|
| 设计定稿（§3.1–§3.9） | ✓ 完成 |
| 共享 State 定义（StoryState） | ✓ **已实现** — [backend/app/graphs/state.py](../backend/app/graphs/state.py) |
| RouterGraph（intent_router） | ✓ **已实现**（启发式 + LLM 兜底）— [router.py](../backend/app/graphs/router.py) |
| WriteGraph 完整 11 节点 | ✓ **已实现**（含 open_book / write_chapter 双路径）— [write.py](../backend/app/graphs/write.py) |
| WriteGraph 4 分支重构 | ✗ **未做**（长篇/短篇目前在 1 个图内，scenario 枚举分流） |
| AnalyzeGraph | △ **骨架** — 3 节点 stub（stage0/stage2/stage5），未实现 |
| ReviewGraph | △ **骨架** — 3 节点 stub（preflight/fan_out/aggregate） |
| DeslopGraph / ImportGraph / ScanGraph | ✗ 未开始 |
| 7 个 Agent（mock LLM + real 双栈）| ✓ **已实现** — `app/agents/*.py` |
| 服务层（TrackingService / ChapterService / ...） | ✓ **已实现** |
| Repository 层（CRUD）| ✓ **已实现** |
| ORM 模型（19 张表映射） | ✓ **已实现** + Alembic 迁移 |
| HTTP API（FastAPI）| ✓ **已实现**（projects/chapters/write/health）|
| Checkpointer | ✗ 未启用（demo 默认绕过） |
| Redis 热层 | ✗ 未启用（demo 默认绕过） |

**结论**：从纯设计推进到 **核心写作闭环已可跑**（WriteGraph 长篇路径），但**4 分支架构尚未重构**，**AnalyzeGraph/ReviewGraph 仍是 stub**。

---

## 2. 已设计的图 vs 已实现

### 2.1 设计目标：4 个写作/拆书分支 + 路由/审查/辅助图

| # | 图 | 设计定位 | 对应 skill |
|---|---|---|---|
| 1 | **WriteGraph_Long**（长篇写作） | 开书 3 阶段 + 单章写 + 日更循环 + 大修 | `story-long-write` |
| 2 | **WriteGraph_Short**（短篇写作） | 情绪目标 → 核心框架 → 成稿（无循环）| `story-short-write` |
| 3 | **AnalyzeGraph_Long**（长篇拆书） | Stage 0-6 完整 7 段管道 | `story-long-analyze` |
| 4 | **AnalyzeGraph_Short**（短篇拆书） | Stage 2-6 简化管道 | `story-short-analyze` |
| 5 | RouterGraph | 意图路由 + 项目查找 + 作者记忆 | `story` |
| 6 | ReviewGraph | 多视角对抗审查（4 reviewer fan-out）| `story-review` |
| 7 | DeslopGraph | 去 AI 味（7 Gate）| `story-deslop` |
| 8 | ScanGraph | 扫榜（多平台采集 + 报告）| `story-long-scan` / `story-short-scan` |
| 9 | ImportGraph | 逆向导入（复用 AnalyzeGraph）| `story-import` |
| 10 | `story_cover` / `browser_session` 叶子 | 封面 / CDP 浏览器 | `story-cover` / `browser-cdp` |

### 2.2 实现状态对照

| 图 | 实现状态 | 代码位置 | 差距 |
|---|---|---|---|
| RouterGraph | ✓ 完整 | [router.py](../backend/app/graphs/router.py) | — |
| **WriteGraph_Long + Short** | ✓ 合并实现 | [write.py](../backend/app/graphs/write.py) | 1 个图 / 2 个 scenario，未拆分独立 graph |
| AnalyzeGraph_Long + Short | △ stub | [analyze.py](../backend/app/graphs/analyze.py) | 仅 stage0 / stage2_extract / stage5_report 3 个空函数；Long/Short 未区分 |
| ReviewGraph | △ stub | [review.py](../backend/app/graphs/review.py) | 仅 preflight / fan_out / aggregate 3 个空函数 |
| DeslopGraph | ✗ | — | 未开始 |
| ScanGraph | ✗ | — | 未开始 |
| ImportGraph | ✗ | — | 未开始 |
| 叶子节点 | ✗ | — | 未开始 |

### 2.3 当前 WriteGraph 的"双 scenario"实现（待拆分为 4 分支）

[backend/app/graphs/write.py](../backend/app/graphs/write.py) 通过 `WriteScenario` 枚举分流：

```python
# backend/app/schemas/writing.py (待确认实际值)
class WriteScenario(str, Enum):
    open_book      = "open_book"        # 开书 — 对应长篇 phase1-3
    write_chapter  = "write_chapter"    # 单章 — 对应长篇/短篇写正文
    daily          = "daily"            # 日更 — 仅长篇
    revision       = "revision"         # 大修
    diagnosis_only = "diagnosis_only"   # 仅诊断
```

`route_scenario_node` + `_should_write_prose` 条件边实现 open_book / write_chapter 二选一：

```python
def _should_write_prose(state):
    if state["scenario"] in ("write_chapter", "daily", "revision"):
        return "write_prose"
    if state["scenario"] == "open_book":
        return END  # open_book 在 validate_outline 后结束
```

**问题**：长篇和短篇没有结构性区分——两者都走 `write_chapter` → `write_prep → write_prose → commit` 同一条管线，**只是目标字数和钩子密度不同**。短篇（§3.4 "story-short-write" 应该是 情绪目标 → 框架 → 成稿 3 步）目前并没有专属节点。

---

## 3. 共享 State 设计（§3.0）

实际实现 [backend/app/graphs/state.py](../backend/app/graphs/state.py)：

```python
class StoryState(TypedDict, total=False):
    # --- session ---
    request_id: str
    user_input: str
    messages: Annotated[list, add_messages]
    intent: str

    # --- project ---
    project_id: int
    project_slug: str

    # --- writing scenario ---
    scenario: str        # open_book / write_chapter / daily / revision / diagnosis_only
    chapter_no: int

    # --- analysis inputs ---
    source_book_id: int
    chapter_boundaries: list[dict]
    stage_progress: dict     # ⚠️ AnalyzeGraph 重启时仍需压缩（Q5）

    # --- review ---
    review_mode: str
    findings: list[dict]

    # --- artifacts (LLM 产出，commit 前不进 DB) ---
    plan: dict              # phase1+2+3 plan
    recall: dict            # ContextService bundle
    prose_draft: str        # chapter body
    quality_report: dict
    summary_text: str
    chapter_hook: str
    continuity_to_next: str
    open_conflicts: list[str]
    location: str
    pov: str
    emotion_arc: dict
    characters_in_scene: list[dict]
    foreshadowing_changes: list[dict]
    timeline_author: str
    timeline_reader: str

    # --- completion ---
    chapter_id: int | None
    state_revision: int
    final_wordcount: int | None
    target_wordcount: int
    stages: list[StageStatus]
    report: str
    errors: list[str]
    extra: dict[str, Any]
```

**与设计差异**：
- ✅ 已加 `request_id` / `project_slug` / `stages`（API 层友好）
- ✅ 已加 v0.2 摘要字段（`summary_text` / `chapter_hook` / `continuity_to_next` / `open_conflicts` / `location` / `pov` / `emotion_arc` / `characters_in_scene` / `foreshadowing_changes`）
- ⚠️ `timeline_author` / `timeline_reader` 仍是单字段（设计 v0.1 已拆为双列，应在 commit 节点拆字段）

---

## 4. 7 个 Agent 角色状态

| 原 Agent | 模型档 | 实现状态 | 文件 |
|---|---|---|---|
| `story_architect` | opus/高端 | ✓ 已实现 | [story_architect.py](../backend/app/agents/story_architect.py) |
| `narrative_writer` | sonnet/中端 | ✓ 已实现 | [narrative_writer.py](../backend/app/agents/narrative_writer.py) |
| `character_designer` | sonnet/中端 | ✓ 已实现（占位）| [character_designer.py](../backend/app/agents/character_designer.py) |
| `story_researcher` | sonnet/中端 | ✓ 已实现（占位）| [story_researcher.py](../backend/app/agents/story_researcher.py) |
| `chapter_extractor` | haiku/低端 | ✓ 已实现（占位）| [chapter_extractor.py](../backend/app/agents/chapter_extractor.py) |
| `consistency_checker` | haiku/低端 | ✓ 已实现 | [consistency_checker.py](../backend/app/agents/consistency_checker.py) |
| `story_explorer` | haiku/低端 | ✓ 已实现 | [story_explorer.py](../backend/app/agents/story_explorer.py) |

**Agent 框架**（[base.py](../backend/app/agents/base.py)）：
- ✓ mock LLM 默认（`MockChatModel` 按 `[role:xxx]` tag 选预置 payload）
- ✓ real LLM 双 provider（Anthropic / OpenAI 通过 LLMFactory 切换）
- ✓ 铁律约束：agent 不能 import repository / AsyncSession（[test_smoke.py](../backend/tests/test_smoke.py) 守）

---

## 5. 跨切关注点

| 关注点 | 设计位置 | 实现状态 |
|---|---|---|
| Checkpointer（状态持久化） | §6 推荐 PostgresSaver | ✗ demo 默认关闭（接 `langgraph-checkpoint-postgres` 即开）|
| 异步 PG 栈（asyncpg + AsyncSession） | 对话 2026-09-27 | ✓ **已实现** — [backend/app/db.py](../backend/app/db.py) |
| Context 压缩（消息滑动窗口 + 召回包 budget） | 待写 docs/context-compression-v0.1.md | △ `ContextService.assemble_recall(last_n=3)` 已实现但无 budget 切片 |
| Reference Gate（write_prep fail-fast） | §3.4 + schema v0.1 | ✓ **已实现** — `QualityService.reference_gate()` |
| 并发控制（章节提交 `lock:chapter:*`） | §2.2 Redis 热层 | ✗ Redis 未接入 |
| 多租户（`owner_id`） | schema v0.1 nullable UUID | ✓ schema 已就绪；service 层未强校验 |
| 铁律：agent → service → repository → DB | §6 | ✓ **已实现**（test_smoke 守）|

---

## 6. 4 分支重构计划（用户 2026-09-27 指出）

### 6.1 为什么是 4 分支而不是 2 个

| 维度 | 长篇 | 短篇 |
|---|---|---|
| 节点数 | 11（route_scenario → phase1-3 → validate_outline → write_prep → ... → tracking_commit）| 3-5（情绪目标 → 框架 → 成稿 → commit）|
| 大纲 | 必填（phase3 全书卷纲+逐章细纲） | 可选（核心框架即可）|
| 循环 | 日更循环（条件边） | 无循环 |
| 字数 | 单章 3000-5000 | 全文 5000-20000 一气呵成 |
| 追踪 | 完整 chapter_records + 伏笔/角色/时间线联动 | 简化版（核心事件 + 钩子即可）|
| LLM 模型档 | phase1-3 用 opus，正文 sonnet | 全程 sonnet |

**结论**：节点数 + 状态字段都差异明显，独立成图更清晰，调试也方便。

### 6.2 重构方案

| 序 | 任务 | 产出 |
|---|---|---|
| 1 | 把 `WriteGraph` 拆为 `WriteGraphLong` + `WriteGraphShort` | `app/graphs/write_long.py` + `write_short.py` |
| 2 | 短篇加专属 `emotion_target` → `core_framework` → `prose_draft` 三节点 | 新节点 |
| 3 | `AnalyzeGraph` 拆为 `AnalyzeGraphLong`（stage0-6）+ `AnalyzeGraphShort`（stage2-6）| `analyze_long.py` + `analyze_short.py` |
| 4 | RouterGraph 加分支判断（`intent ∈ {open_book, write_chapter}` → 路由到 long/short） | router.py 改 `_route_by_intent` |
| 5 | WriteScenario enum 拆为 `WriteLength` enum（long / short）+ Scenario | 新 schema |
| 6 | registry 加 4 个新属性，api/write.py 分流 | `GraphRegistry.write_long/.write_short/.analyze_long/.analyze_short` |

### 6.3 重构后的目标 registry

```python
class GraphRegistry:
    @property
    def router(self): ...
    @property
    def write_long(self): ...
    @property
    def write_short(self): ...
    @property
    def analyze_long(self): ...
    @property
    def analyze_short(self): ...
    @property
    def review(self): ...
    # 后续
    @property
    def deslop(self): ...
    @property
    def scan(self): ...
    @property
    def import_(self): ...
```

### 6.4 重构风险

| 风险 | 缓解 |
|---|---|
| api/write.py 行为变更 | 保留 `scenario` 字段，向 `WriteLength` 平滑过渡（兼容枚举）|
| 测试用例大批量失败 | 重构前先跑 `pytest -q` 建基线，逐项迁 |
| 长篇/短篇 state 字段不一致 | 在 `StoryState` 加 `length: Literal["long", "short"]` 字段；两图共用 state，按 length 分支 |

---

## 7. 待办与开放问题

### 7.1 P0（阻塞核心 4 分支）

| # | 项 | 依赖 |
|---|---|---|
| 1 | 重构 WriteGraph → write_long + write_short | 无（已有代码基础）|
| 2 | 重构 AnalyzeGraph stub → analyze_long + analyze_short | 无 |
| 3 | RouterGraph 加 length 分流 | #1 / #2 |
| 4 | 短篇专属节点（emotion_target / core_framework）| #1 |
| 5 | 长篇 AnalyzeGraph Stage 0-6 全实现 | #2 |
| 6 | 接 `langgraph-checkpoint-postgres` | 4 分支跑通后 |

### 7.2 P1（增强 + P1 图）

| # | 项 |
|---|---|
| 7 | ReviewGraph 4 reviewer fan-out 实现 |
| 8 | ContextService budget 切片 + 消息压缩 |
| 9 | Redis 热层规范文档 + lock:chapter:* 接入 |
| 10 | Alembic autogenerate 接入（每次 schema 变更自动迁移） |

### 7.3 P2/P3（外围）

| # | 项 |
|---|---|
| 11 | DeslopGraph 7 Gate |
| 12 | ScanGraph + ScanService 平台采集器 |
| 13 | ImportGraph + AnalyzeGraph 子图调用 |
| 14 | story_cover + CoverService |
| 15 | browser_session + BrowserService |
| 16 | 真实 LLM smoke（用 sonnet-mini 跑一遍 WriteGraph）|

### 7.4 开放问题（需要决策）

| # | 问题 | 推荐 |
|---|---|---|
| Q1 | 是否启用多租户（owner_id 强约束） | 单用户起步，保持 nullable |
| Q2 | chapter_records 用表还是 VIEW | VIEW 为主 |
| Q3 | content 字段类型（TEXT vs JSONB）| TEXT |
| Q4 | chapter_records 摘要生成时机 | 同步（同 commit 事务）✓ 已实现 |
| Q5 | stage_progress 字段压缩策略 | 折叠为 `{completed, current, checkpoint}` |
| Q6 | write_prose LLM agent 单次最大输出 | 多段 + 流式 |
| **Q7** | **4 分支重构优先级** | **当前最优先（用户在 2026-09-27 指出）** |
| **Q8** | **短篇字数 / 大纲 / 追踪表简化策略** | **短篇跳过 outline_chapters 直写 chapters；chapter_records 简化为 4 字段** |

---

## 8. 下一步建议

按对话历史（2026-09-27）推进：

| 序 | 任务 | 衔接 |
|---|---|---|
| 1 | 4 分支重构（WriteGraph + AnalyzeGraph 拆分）| §6 计划 |
| 2 | 短篇专属节点实现 | §7.1 #4 |
| 3 | 长篇 AnalyzeGraph Stage 0-6 实现 | §7.1 #5 |
| 4 | 接 PostgresSaver | §7.1 #6 |
| 5 | Redis 热层规范文档 + 接入 | §2.2 |

---

## 9. 风险与监控

| 风险 | 影响 | 缓解 |
|---|---|---|
| 设计文档与代码脱节 | 高 | **本次重写** — 状态文档与 backend/ 实际一致 |
| 异步栈失误 | 高 | 已实现；CI 加 ruff 规则 |
| TrackingService.commit 多表事务出 bug | 极高 | test_smoke 已覆盖关键路径 |
| LLM agent 直接写 PG | 极高 | ✓ iron_rule 测试守住 |
| 长篇 context 累积爆窗口 | 中 | ContextService 召回已实现；budget 切片待做 |
| Redis 变第二个真值源 | 高 | Redis 未接入前不构成风险 |
| **4 分支重构引入回归** | **高** | **重构前跑 baseline pytest；逐项迁移** |

---

## 10. 变更日志

| 日期 | 改动 |
|---|---|
| 2026-09-27 | 创建本文档；状态基线：纯设计阶段，未落地任何代码 |
| 2026-09-27 | **重大修正** — backend/ 实际有 FastAPI + LangGraph 实现（WriteGraph 完整 / AnalyzeGraph stub）；新增 §6 4 分支重构计划以回应用户对长篇/短篇/长篇拆书/短篇拆书 4 分支的要求；新增 §7.4 Q7/Q8 决策项 |
---

# §4 graph-topology-v0.1 — 图拓扑规范


---

# 4 分支图拓扑规范 v0.1

> 截至 2026-09-27 — `auto_novels` LangGraph 4 分支架构的节点与边定义。
> 用途：作为 §6 重构计划（`langgraph-status-v0.1.md`）的实施蓝图。
> 代码骨架位置：[backend/app/graphs/](../backend/app/graphs/)

---

## 0. 总览（4 分支 + 1 路由）

```
RouterGraph (intent_router + length_router)
   │
   ├──► WriteGraph_Long      (长篇写作)
   ├──► WriteGraph_Short     (短篇写作)
   ├──► AnalyzeGraph_Long    (长篇拆书，Stage 0-6)
   ├──► AnalyzeGraph_Short   (短篇拆书，Stage 2-6)
   ├──► ReviewGraph          (多视角审查 — 4 reviewer fan-out)
   ├──► DeslopGraph          (去 AI 味 — 7 Gate)
   ├──► ScanGraph            (扫榜)
   └──► ImportGraph          (逆向导入，复用 AnalyzeGraph_Long/Short)
```

**4 分支核心差异**：

| 维度 | WriteGraph_Long | WriteGraph_Short | AnalyzeGraph_Long | AnalyzeGraph_Short |
|---|---|---|---|---|
| 节点数 | 13（含循环） | 10（单链）| 13（含并行）| 7（单链）|
| 开书规划 | phase1-3 ✓ | 跳过（直入 emotion_target）| — | — |
| 大纲 | volumes + outline_chapters | 无（直写 chapters）| — | — |
| 日更循环 | ✓ | ✗ | ✗ | ✗ |
| 拆解 stage | — | — | 0-1-2-3-4(a/b/c)-5-6 | 2-3-5-6 |
| Stage 1 golden3 | — | — | ✓ + stage1_checkpoint | ✗ |
| Stage 2 extract | — | — | map (Send 5-8 并行) | map (Send 5-8 并行) |
| 模型档 | opus 规划 + sonnet 写作 | 全程 sonnet | sonnet + haiku（chapter_extractor） | sonnet + haiku |
| 字数 | 3000-5000/章 | 5000-20000/篇（单章多） | — | — |

---

## 1. RouterGraph（路由分发）

**职责**：用户输入 → 意图 + 长度 → 派发到对应分支图。caller（API 层）拿到 intent + length 后决定调哪个图。

### 1.1 节点

| 节点 | 类型 | 输入 | 输出 |
|---|---|---|---|
| `intent_router` | LLM + 启发式 | user_input | `intent` ∈ {open_book, write_chapter, review, analyze, scan, memory_*, diagnosis, unknown} |
| `project_lookup` | service | project_id | state_revision, last_committed_chapter |
| `author_memory` | service | project_id | recall.author_memory[] |
| `length_router` | 条件路由 | intent + user_input | `length` ∈ {long, short} |
| `dispatch` | END 出口 | — | （caller 据此调对应图） |

### 1.2 边

```
intent_router ──► project_lookup ──► author_memory ──► length_router
                                                       │
       ┌───────────────┬──────────────┬───────────────┤
       ▼               ▼              ▼               ▼
   open_book_long  open_book_short  write_long    write_short
   analyze_long    analyze_short    review        scan/...
       │               │              │               │
       └───────────────┴──────────────┴───────────────┘
                              ▼
                            (END → caller 派发)
```

### 1.3 路由表（length_router 输出）

| intent | 默认 length | 可被 user_input 覆盖 |
|---|---|---|
| open_book | long | "短篇开书" / "短篇 open_book" → short |
| write_chapter | long（默认延续上一本）| "短篇" / "写一个短篇" → short |
| analyze | long | "短篇拆解" → short |
| review | long | — |
| scan | long | — |
| memory_* | — | — |
| diagnosis / unknown | — | — |

### 1.4 代码签名

```python
# backend/app/graphs/router.py

async def intent_router_node(state: StoryState, **deps) -> dict:
    """启发式 + 兜底 LLM 分类 → intent ∈ INTENT_LABELS"""
    ...

async def project_lookup_node(state, **deps) -> dict: ...

async def author_memory_node(state, **deps) -> dict: ...

async def length_router_node(state, **deps) -> dict:
    """从 user_input / scenario 推断 length；落 state.length"""
    length = infer_length(state)
    return {"length": length, "stages": [...]}

def build_router_graph() -> StateGraph:
    g = StateGraph(StoryState)
    g.add_node("intent_router", intent_router_node)
    g.add_node("project_lookup", project_lookup_node)
    g.add_node("author_memory", author_memory_node)
    g.add_node("length_router", length_router_node)
    g.set_entry_point("intent_router")
    g.add_edge("intent_router", "project_lookup")
    g.add_edge("project_lookup", "author_memory")
    g.add_edge("author_memory", "length_router")
    # length_router 不画边 — caller 据此 dispatch
    g.add_edge("length_router", END)
    return g.compile(name="router")
```

---

## 2. WriteGraph_Long（长篇写作）— §3.4

**场景**：开书 + 单章写作 + 日更循环 + 大修。  
**关键路径**：
- `open_book` → phase1 → phase2 → phase3 → validate_outline → END
- `write_chapter` / `daily` → write_prep → write_prose → ... → tracking_commit → (loop)

### 2.1 节点（13 个）

| 节点 | 类型 | 触发场景 | 职责 |
|---|---|---|---|
| `route_scenario` | 路由节点 | 全部 | 决策走 open_book 链 or write_chapter 链 |
| `phase1_topic` | LLM (story_architect, opus) | open_book | 选题 + 对标发现 |
| `phase2_settings` | LLM (story_architect, opus) | open_book | 关系/题材定位/题材正文提示卡/世界观/金手指/势力 |
| `phase3_outline` | LLM (story_architect, opus) | open_book | 全书卷纲 + 逐章细纲；持久化 volumes + outline_chapters |
| `validate_outline` | service (QualityService.outline_contract) | open_book | 大纲七检 |
| `write_prep` | service (ContextService + Reference Gate) | write_chapter/daily | Reference Gate fail-fast + 召回包 ≤10KB |
| `write_prose` | LLM (narrative_writer, sonnet) | write_chapter/daily | 写正文（多段 + 流式）|
| `wordcount_checkpoint` | service (WordcountService) | write_chapter/daily | 字数非对称收口 |
| `quality_scan` | service (QualityService) | write_chapter/daily | ai_patterns + degeneration + punctuation + banned_words |
| `quality_review` | LLM (consistency_checker, haiku) | write_chapter/daily | 章尾钩子 + 爽点 + 情绪核对（可证伪双查）|
| `tracking_commit` | service (TrackingService.commit) | write_chapter/daily | **唯一多表事务入口**（铁律）|
| `snapshot_checkpoint` | service | 每 3 章触发 | 一致性检查 + 数据快照 |
| `daily_loop_controller` | 条件路由 | daily 触发 | 控制日更循环（2-3 章）|

### 2.2 边

```
                          ┌─── open_book 路径 ───┐
                          │                       │
                          ▼                       │
route_scenario ──► phase1_topic                   │
                          │                       │
                          ▼                       │
                  phase2_settings                  │
                          │                       │
                          ▼                       │
                  phase3_outline                   │
                          │                       │
                          ▼                       │
                  validate_outline                 │
                          │                       │
                          ▼                       │
                         END ◄────────────────────┘

                          ┌─── write_chapter / daily 路径 ───┐
                          │                                    │
                          ▼                                    │
                       write_prep                              │
                          │                                    │
                          ▼                                    │
                       write_prose                             │
                          │                                    │
                          ▼                                    │
                  wordcount_checkpoint                         │
                          │                                    │
                          ▼                                    │
                       quality_scan                             │
                          │                                    │
                          ▼                                    │
                      quality_review                            │
                          │                                    │
                          ▼                                    │
                     tracking_commit  ◄──────────── snapshot_checkpoint (每 3 章)
                          │
                          ▼
                  daily_loop_controller  (仅 daily)
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       (more chapters?)          END
              │
              ▼
         write_prep  (loop back)
```

### 2.3 条件边表

| 源节点 | 条件函数 | 真分支 | 假分支 |
|---|---|---|---|
| `route_scenario` | `scenario ∈ {open_book}` | `phase1_topic` | `write_prep` |
| `route_scenario` | `scenario ∈ {write_chapter, daily, revision}` | `write_prep` | END |
| `daily_loop_controller` | `committed_count < daily_target` | `write_prep` | END |
| `tracking_commit` | `chapter_no % 3 == 0` | `snapshot_checkpoint` | END |

### 2.4 代码签名

```python
# backend/app/graphs/write_long.py

NODES = [
    "route_scenario", "phase1_topic", "phase2_settings", "phase3_outline",
    "validate_outline", "write_prep", "write_prose", "wordcount_checkpoint",
    "quality_scan", "quality_review", "tracking_commit",
    "snapshot_checkpoint", "daily_loop_controller",
]

async def route_scenario_node(state, **deps): ...
async def phase1_topic_node(state, **deps): ...
async def phase2_settings_node(state, **deps): ...
async def phase3_outline_node(state, **deps): ...
async def validate_outline_node(state, **deps): ...
async def write_prep_node(state, **deps): ...
async def write_prose_node(state, **deps): ...
async def wordcount_checkpoint_node(state, **deps): ...
async def quality_scan_node(state, **deps): ...
async def quality_review_node(state, **deps): ...
async def tracking_commit_node(state, **deps): ...   # ← 唯一多表事务
async def snapshot_checkpoint_node(state, **deps): ...
async def daily_loop_controller_node(state, **deps): ...

def build_write_long_graph() -> StateGraph:
    g = StateGraph(StoryState)
    for name, fn in zip(NODES, [...]):
        g.add_node(name, fn)
    # 边按 §2.2/2.3 接线
    return g.compile(name="write_long")
```

---

## 3. WriteGraph_Short（短篇写作）— §3.4 短篇分支

**场景**：单次成稿。`情绪目标 → 核心框架 → 成稿`。  
**核心简化**：
- 无 phase1-3（不开书）
- 无 outline_chapters（直写 chapters）
- 无日更循环
- 无 snapshot_checkpoint
- chapter_records 摘要简化为 4 字段（core_event / summary_text / chapter_hook / open_conflicts）

### 3.1 节点（10 个）

| 节点 | 类型 | 职责 |
|---|---|---|
| `route_scenario` | 路由节点 | 验证是 short + write_chapter |
| `emotion_target` | LLM (story_architect, sonnet) | 设置情绪目标：起止情绪 + 强度 + 落点 |
| `core_framework` | LLM (story_architect, sonnet) | 核心框架：开头钩子 + 三幕结构 + 反转 + 结尾钩子 |
| `validate_framework` | service (QualityService.short_contract) | 校验结构完整性（开头钩子存在 / 三幕齐全 / 结尾钩子存在）|
| `write_prep` | service (ContextService + Reference Gate) | 同 Long；召回包可适当放大（≤12KB）|
| `write_prose` | LLM (narrative_writer, sonnet) | 单次输出（不分段，因 ≤20000 字）|
| `wordcount_checkpoint` | service | 字数非对称收口（目标 5000-20000）|
| `quality_scan` | service | 同 Long |
| `quality_review` | LLM (consistency_checker, haiku) | 钩子核对 + 情绪曲线核对 |
| `tracking_commit` | service (TrackingService.commit) | 简化版事务（仅 chapters + chapter_records + tracking_state）|

### 3.2 边

```
route_scenario ──► emotion_target ──► core_framework ──► validate_framework
                                                            │
                                                            ▼
                                                       write_prep
                                                            │
                                                            ▼
                                                       write_prose
                                                            │
                                                            ▼
                                                  wordcount_checkpoint
                                                            │
                                                            ▼
                                                      quality_scan
                                                            │
                                                            ▼
                                                    quality_review
                                                            │
                                                            ▼
                                                   tracking_commit ──► END
```

**单链无分支**（无循环、无并行、无 snapshot）。

### 3.3 条件边表

| 源节点 | 条件 | 真分支 | 假分支 |
|---|---|---|---|
| `validate_framework` | `passed` | `write_prep` | END（fail-fast）|

### 3.4 与 Long 的关键差异

| 差异点 | WriteGraph_Long | WriteGraph_Short |
|---|---|---|
| 大纲 | volumes + outline_chapters | 无（直写）|
| 设定卡 | phase2_settings 写 6 类 settings | 简化（只取 kind=题材定位 + 文风参考）|
| 字数目标 | 3000-5000（单章）| 5000-20000（一篇）|
| tracking commit 范围 | chapters + characters + foreshadowing + timeline + chapter_records | chapters + chapter_records（简化）+ tracking_state |
| snapshot_checkpoint | ✓ | ✗ |
| 日更循环 | ✓ | ✗ |
| chapter_records 字段 | 全部 10 字段 | 4 字段（summary_text / chapter_hook / open_conflicts / core_event）|

---

## 4. AnalyzeGraph_Long（长篇拆书）— §3.3

**场景**：扫榜后挑一本书深度拆解。Stage 0-6 共 7 段管道。  
**关键特性**：
- Stage 1 有人机 checkpoint（`stage1_checkpoint`）
- Stage 2 map 并行（Send API 5-8 并发）
- Stage 3 ↔ Stage 4a 并行

### 4.1 节点（13 个）

| 节点 | 类型 | 职责 |
|---|---|---|
| `stage0_overview` | LLM | 概要 + **章节边界表**（唯一切片真值）|
| `stage1_golden3` | LLM | 前 3 章深度拆解 → `analysis_aggregates(kind=golden)` |
| `stage1_checkpoint` | 条件路由 + interrupt | 询问用户：继续全量 / 跳过 / 暂停 |
| `stage2_extract` | **map** (Send) | 逐章 spawn `chapter_extractor` 节点，5-8 并行 |
| `stage2_validate` | service | 机械校验（情节点数 / 白描字段 / 标签枚举）|
| `stage2_merge` | service | 聚合 `analysis_chapters` → 章节摘要汇总 |
| `stage3_aggregate` | LLM | 剧情聚合 → `analysis_aggregates(kind=plot/rhythm/emotion)` + 角色合并 |
| `stage4a_settings` | LLM | 世界观 / 金手指 / 势力 |
| `stage4b_characters` | LLM | 角色完整档案（依赖 stage3 角色合并）|
| `stage4c_relations` | LLM | 角色关系提取（依赖 stage4b）|
| `stage5_report` | LLM | 拆文报告 + 全书概要（500-1000 字）|
| `stage6_style` | LLM | 文风（句长/标点/潜台词 + 原文锚点）|
| `progress_tracker` | service | 每阶段写 `analysis_progress`（断点恢复）|

### 4.2 边（含并行结构）

```
stage0_overview ──► stage1_golden3 ──► stage1_checkpoint
                                          │
                              ┌───────────┼───────────┐
                              ▼                       ▼
                        stage2_extract            (END / 暂停)
                              │
                              ▼  (map → Send 并行)
                       stage2_validate
                              │
                              ▼
                        stage2_merge
                              │
                  ┌───────────┴───────────┐  ◄── 并行
                  ▼                       ▼
           stage3_aggregate         stage4a_settings
                  │                       │
                  ▼                       │
           stage4b_characters             │
                  │                       │
                  ▼                       │
           stage4c_relations              │
                  │                       │
                  ▼                       │
            stage5_report ◄───────────────┤
                  │                       │
                  ▼                       │
            stage6_style ◄────────────────┘
                  │
                  ▼
                 END
```

### 4.3 条件边表

| 源节点 | 条件函数 | 真分支 | 假分支 |
|---|---|---|---|
| `stage1_checkpoint` | user choice | `stage2_extract` | END |
| `stage2_extract` | map 完成（Send gather）| `stage2_validate` | （错误 → progress_tracker）|

### 4.4 并行约束

- stage3 ↔ stage4a：`asyncio.gather` 等两者都完成
- stage4a 单跑完即可进入 stage6_style（无需 stage4b/4c，因 settings 与 characters 独立）
- stage2 map：max_concurrent=8（受 `asyncio.Semaphore(8)` 限制）

---

## 5. AnalyzeGraph_Short（短篇拆书）— §3.3 短篇分支

**场景**：拆解一本短篇（篇幅短，stage 简化）。Stage 2-6 跳过 stage0/1（无 golden3，无章节边界精细切分）。  
**核心简化**：
- 跳过 stage0（短篇无需概要）
- 跳过 stage1（短篇无 golden3 概念）
- stage2 map 仍并行，但批量 ≤3（短篇章数少）
- stage4a/4b/4c 合并为单节点 `stage4_short`（角色 + 设定一起）

### 5.1 节点（7 个）

| 节点 | 类型 | 职责 |
|---|---|---|
| `stage2_extract` | map (Send) | 逐章 spawn `chapter_extractor`，max_concurrent=3 |
| `stage2_validate` | service | 机械校验（同 Long）|
| `stage2_merge` | service | 聚合 |
| `stage3_aggregate` | LLM | 剧情 / 节奏 / 情绪 聚合 |
| `stage4_short` | LLM | 角色 + 设定 + 关系 一次性出（合并 4a/4b/4c）|
| `stage5_report` | LLM | 拆文报告（300-500 字，短篇更短）|
| `stage6_style` | LLM | 文风 |
| `progress_tracker` | service | 断点恢复 |

### 5.2 边（单链 + 一个并行）

```
stage2_extract ──► stage2_validate ──► stage2_merge
                                          │
                              ┌───────────┴───────────┐  ◄── 并行
                              ▼                       ▼
                       stage3_aggregate         stage4_short
                              │                       │
                              └───────────┬───────────┘
                                          ▼
                                     stage5_report
                                          │
                                          ▼
                                      stage6_style
                                          │
                                          ▼
                                         END
```

---

## 6. 共享节点 / 服务节点（不专属任一图）

| 节点 | 类型 | 服务对象 |
|---|---|---|
| `intent_router` | LLM | RouterGraph |
| `project_lookup` | service (TrackingService.check) | RouterGraph |
| `author_memory` | service (MemoryService.query) | RouterGraph |
| `length_router` | 条件路由 | RouterGraph |
| `Reference Gate` | service (QualityService.reference_gate) | write_prep 内调用 |
| `commit_node` | service (TrackingService.commit) | WriteGraph_Long / Short |

---

## 7. Registry 设计

```python
# backend/app/graphs/registry.py

class GraphRegistry:
    """Lazy-compiled graphs, accessible by attribute."""

    def __init__(self) -> None:
        self._router = None
        self._write_long = None
        self._write_short = None
        self._analyze_long = None
        self._analyze_short = None
        self._review = None
        self._deslop = None      # 后续
        self._scan = None        # 后续
        self._import_ = None     # 后续

    @property
    def router(self):
        if self._router is None:
            self._router = build_router_graph()
        return self._router

    @property
    def write_long(self):
        if self._write_long is None:
            self._write_long = build_write_long_graph()
        return self._write_long

    @property
    def write_short(self):
        if self._write_short is None:
            self._write_short = build_write_short_graph()
        return self._write_short

    @property
    def analyze_long(self):
        if self._analyze_long is None:
            self._analyze_long = build_analyze_long_graph()
        return self._analyze_long

    @property
    def analyze_short(self):
        if self._analyze_short is None:
            self._analyze_short = build_analyze_short_graph()
        return self._analyze_short

    @property
    def review(self):
        if self._review is None:
            self._review = build_review_graph()
        return self._review
```

---

## 8. 与代码现状的映射（重构路径）

| 目标图 | 当前代码 | 改造路径 |
|---|---|---|
| **RouterGraph** | [router.py](../backend/app/graphs/router.py) | 1) 加 `length_router` 节点；2) StoryState 加 `length` 字段；3) `_route_by_intent` 输出 (intent, length) |
| **WriteGraph_Long** | [write.py](../backend/app/graphs/write.py) 主体 | 重命名为 `write_long.py`；保留全部 11 节点 + 加 `snapshot_checkpoint` + `daily_loop_controller`（13 节点）|
| **WriteGraph_Short** | [write.py](../backend/app/graphs/write.py) 主体 | **新建** `write_short.py`；10 节点；纯单链；commit 简化 |
| **AnalyzeGraph_Long** | [analyze.py](../backend/app/graphs/analyze.py) stub | **新建** `analyze_long.py`；13 节点；完整 Stage 0-6 |
| **AnalyzeGraph_Short** | 无 | **新建** `analyze_short.py`；7 节点；Stage 2-6 |
| **ReviewGraph** | [review.py](../backend/app/graphs/review.py) stub | 后续 P1（不在本次重构范围）|

### 8.1 不动的部分

- StoryState 结构（仅加 `length` 字段）
- 7 个 agent 文件（保持原样）
- 全部 service / repository / ORM（保持原样）
- Alembic 迁移（schema 已落地）
- api/write.py 入口（caller 端通过 intent+length 选图，行为不变；只是图内部从 1 个变成 4 个）

### 8.2 改造顺序

| 序 | 任务 | 依赖 | 估计 |
|---|---|---|---|
| 1 | StoryState 加 `length: Literal["long", "short"]` | 无 | 0.5 小时 |
| 2 | `router.py` 加 `length_router_node` + 改边 | #1 | 1 小时 |
| 3 | `write.py` 重命名为 `write_long.py` + 加 2 节点 | 无 | 0.5 小时 |
| 4 | 新建 `write_short.py`（10 节点 + 单链边） | 无 | 1.5 天 |
| 5 | 新建 `analyze_long.py`（13 节点 + 复杂并行） | 无 | 2-3 天 |
| 6 | 新建 `analyze_short.py`（7 节点） | 无 | 1 天 |
| 7 | `registry.py` 加 4 个新属性 | #3-#6 | 0.5 小时 |
| 8 | `api/write.py` 改 caller 派发（按 length 选图） | #7 | 0.5 小时 |
| 9 | pytest 回归 + 新增分支测试 | #1-#8 | 1 天 |

合计：约 **6-7 天**（含测试）。

---

## 9. 节点类型速查（与 §3 设计对应）

| 类型 | 标识 | 实现 |
|---|---|---|
| LLM 节点 | `async def xxx_node(state, **deps)` | 调 LLMFactory.get(role) |
| 服务节点 | `async def xxx_node(state, **deps)` | 调 XxxService(session) |
| 条件路由节点 | `async def xxx_node(state, **deps)` 或纯函数 | 返回字段供条件边判断 |
| map 节点 | `async def xxx_node(state, **deps)` 返回 list[Send] | 用 LangGraph `Send` API |
| interrupt 节点 | 普通节点 + `interrupt_before` 编译参数 | 用户暂停交互 |
| END | `langgraph.graph.END` | 出口标记 |

---

## 10. 边类型速查

| 边类型 | 用法 |
|---|---|
| 普通边 | `g.add_edge("a", "b")` |
| 条件边 | `g.add_conditional_edges("a", cond_fn, {"key1": "node1", "key2": END})` |
| 入边（多源汇合）| 多次 `g.add_edge("src_X", "tgt")` |
| 入口 | `g.set_entry_point("first_node")` |

---

## 11. 节点间共享字段（哪些字段是必须的）

参考 StoryState 中**4 分支必备**的最小子集：

```python
class StoryState(TypedDict, total=False):
    # 必备（4 个图都用）
    project_id: int
    length: Literal["long", "short"]   # ⬅ NEW
    request_id: str
    user_input: str
    messages: Annotated[list, add_messages]
    stages: list[StageStatus]
    errors: list[str]
    
    # WriteGraph 必备
    scenario: str                       # open_book / write_chapter / daily / revision
    chapter_no: int
    plan: dict
    recall: dict
    prose_draft: str
    quality_report: dict
    summary_text: str
    chapter_hook: str
    continuity_to_next: str
    open_conflicts: list[str]
    location: str
    pov: str
    emotion_arc: dict
    characters_in_scene: list[dict]
    foreshadowing_changes: list[dict]
    target_wordcount: int
    final_wordcount: int | None
    state_revision: int
    chapter_id: int | None
    
    # AnalyzeGraph 必备
    source_book_id: int
    chapter_boundaries: list[dict]
    stage_progress: dict
    
    # RouterGraph 输出
    intent: str
    
    # ReviewGraph 必备（未来）
    review_mode: str
    findings: list[dict]
```

加 `length` 一个字段就够——其他字段都是现有结构。

---

## 12. 后续行动

按本文 + langgraph-status-v0.1.md §6 实施：

1. 先把本文落到代码骨架（5 个文件 + registry）
2. 跑 `pytest -q` 确认回归
3. 验证 mock LLM 跑通 `WriteGraph_Short` 一个短篇端到端
4. 再开始 `AnalyzeGraph_Long` Stage 0-6 完整实现

完成后再回到 §7.1 P0 阻塞项的剩余部分（接 PostgresSaver / Redis 热层）。
---

# §5 schema-pg-v0.1 — Schema 设计说明


---

# PG Schema v0.1 · 设计说明

> 基于 oh-story-langgraph-mcp-decomposition.md §2.1 的 PostgreSQL 表结构落地版本。
> DDL：schema-pg-v0.1.sql
> 日期：2026-09-27

---

## 1. 设计原则（5 条硬约束）

1. **PG 是唯一真值** — 所有可写实体入表；Redis 只缓存派生读取（`context_views` / 作者记忆 / 召回包）。
2. **追踪铁律** — `tracking_state` + 派生视图只能经 `TrackingService.commit` 写入；commit 是唯一多表事务入口。
3. **LLM 禁直写** — service 层是唯一写入口；agent 节点只调 service 函数。
4. **JSONB 原样兼容** — `tracking_state.state_jsonb` 直接吃老的 `_tracking-state.json`；`format_version` 列支持后续升级。
5. **派生可重建** — Redis `FLUSHDB` 后能由 service 回填；`chapter_records` 提供 VIEW 替代物化表方案。

---

## 2. 表清单（19 张 + 1 VIEW + 1 函数）

| 域 | 表 | 说明 |
|---|---|---|
| 项目 | `projects` | 书 / 活跃书唯一约束 |
| 项目 | `settings` | 6 类设定卡（enum） |
| 大纲 | `volumes` | 卷 |
| 大纲 | `outline_chapters` | 逐章细纲 + 情节点 JSONB |
| 正文 | `chapters` | 正文 TEXT + revision 乐观锁 |
| 追踪 | `tracking_state` | 权威状态 JSONB + state_revision |
| 追踪 | `characters` | 角色档案 |
| 追踪 | `foreshadowing` | 伏笔（5 态） |
| 追踪 | `timeline_events` | 时间线（作者真相 / 读者已知 双列） |
| 追踪 | `chapter_records` | 派生（推荐改 VIEW） |
| 视图 | `context_views` | 7 列 ≤12KB 缓存 |
| 拆解 | `analysis_chapters` | 单章拆解 |
| 拆解 | `analysis_aggregates` | 8 类聚合 |
| 拆解 | `analysis_progress` | 阶段断点 |
| 记忆 | `author_memory` | append-only + scope 校验 |
| 对标 | `benchmarks` | 对标书 |
| 对标 | `reference_materials` | Reference Gate 主契约 |
| 扫榜 | `scan_results` | append-only + 分区建议 |
| 封面 | `covers` | 二进制留盘 + DB 存路径 |

---

## 3. 与 §2.1 设计文档的关键差异（已合入前次评审补丁）

| # | §2.1 原文 | v0.1 落地 | 来源 |
|---|---|---|---|
| 1 | `foreshadowing.status` 未定义 | 5 态 enum `planted/hinted/revealed/retired/broken` | 评审 ⚠️ |
| 2 | `chapters.status` 仅 2 态 | 4 态 enum `draft/reviewing/committed/archived` | 评审 ⚠️ |
| 3 | `chapters.revision` 语义不清 | 显式乐观锁（commit +1） | 评审 ⚠️ |
| 4 | `timeline_events` 用 `author_only` 布尔 | 双列 `author_content` + `reader_content` | 评审 ⚠️ |
| 5 | `context_views` 含糊 | 函数 `build_context_view()` + 表 + 写透缓存 | 评审 ⚠️ |
| 6 | `settings.kind` 字符串无约束 | PG enum `setting_kind` | 评审 ⚠️ |
| 7 | `scan_results` 无归档 | 注释提醒按月分区 + `metadata_jsonb` | 评审 ⚠️ |
| 8 | `author_memory.scope` 值域未定义 | enum `global/project/genre` + scope_ref 必填约束 | 评审 ⚠️ |
| 9 | `reference_materials` 无主契约 | `is_primary` + partial unique `(project_id, kind) WHERE is_primary` | 评审 ⚠️ |
| 10 | `chapter_records` 应为视图 | 表保留 + 提供 VIEW `chapter_records_v` | 评审 ⚠️ |
| 11 | Redis `sess:*` 与 checkpointer 冲突 | 已从 §2.2 删除（不在本文件） | 评审 ⚠️ |
| 12 | `lock:chapter:*` 并发模型未明 | 注释说明仅多 session 协作 | 评审 ⚠️ |
| 13 | 审计字段全缺 | `created_at/updated_at/committed_at/committed_by` 全表覆盖 | 评审 ❌ |
| 14 | 索引规划缺失 | 12+ 复合 / 部分索引 + tsvector 占位 | 评审 ❌ |
| 15 | 多租户隔离缺失 | `owner_id UUID NULL`（单用户模式可空） | 评审 ❌ |
| 16 | 唯一活跃书约束缺失 | partial unique index 兜底 | 评审 ❌ |
| 17 | JSONB 演进策略缺失 | `tracking_state.format_version` 列 | 评审 ❌ |
| 18 | 容量估算 / 分区缺失 | `scan_results` 注释提醒按月分区 | 评审 ❌ |

---

## 4. 与 WriteGraph 服务层的对应关系

| 服务函数 | 主要写表 | 关键约束 |
|---|---|---|
| `TrackingService.init` | `tracking_state`, `characters`, `foreshadowing`, `timeline_events`, `analysis_chapters` | 单事务；state_revision=1 |
| `TrackingService.commit` | `chapters`, `tracking_state`, `characters`, `foreshadowing`, `timeline_events`, `context_views` | **唯一** 多表事务入口；state_revision+1 |
| `TrackingService.check` | 只读 `tracking_state` | 返回 `last_committed_chapter` / `state_revision` / 视图一致性 |
| `WordcountService.measure` | 只读 `chapters` | — |
| `WordcountService.checkpoint` | 校验 `chapters.wordcount` | — |
| `ChapterService.commit` | `chapters` (status=`committed`) | 同事务联调 `TrackingService.commit` |
| `QualityService.outline_contract` | 校验 `outline_chapters` | — |
| `Reference Gate` (§3.4 write_prep) | 校验 `reference_materials` 主契约 | `(project_id, kind, is_primary=TRUE)` 必须存在 |
| `MemoryService.record` | `author_memory` (append) | scope 校验 |
| `MemoryService.query` | 只读 + Redis 缓存 | state_revision 版本守卫 |

---

## 5. 应用步骤

### 5.1 本地 PG（最快）

```bash
# 启动临时容器
docker run -d --name auto_novels_pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=auto_novels \
  -p 5432:5432 \
  postgres:16

# 等 3 秒启动
sleep 3

# 应用 schema
docker exec -i auto_novels_pg psql -U postgres -d auto_novels \
  < docs/schema-pg-v0.1.sql

# 验证
docker exec -it auto_novels_pg psql -U postgres -d auto_novels -c "\dt"
docker exec -it auto_novels_pg psql -U postgres -d auto_novels -c "\dT"
docker exec -it auto_novels_pg psql -U postgres -d auto_novels -c "\dv"
```

### 5.2 已存在的本地 PG

```bash
createdb auto_novels
psql -h localhost -U postgres -d auto_novels -f docs/schema-pg-v0.1.sql
```

### 5.3 验证清单

| 检查项 | 命令 |
|---|---|
| 19 张表全建 | `\dt` |
| 11 个 enum 全建 | `\dT` |
| 1 个 VIEW 全建 | `\dv` |
| `build_context_view` 函数 | `\df build_context_view` |
| `updated_at` 触发器数量 | `SELECT count(*) FROM pg_trigger WHERE tgname LIKE '%_set_updated_at';`（应为 14） |
| 唯一活跃书约束 | `\d projects` 查看索引列表 |
| Reference 主契约唯一 | `\d reference_materials` |

---

## 6. 已知待补（v0.1 范围外）

| # | 项 | 建议版本 |
|---|---|---|
| 1 | **FS → DB 一次性迁移脚本** | v0.2（`migrate-fs-to-pg` 命令） |
| 2 | **`scan_results` 按月分区** | v0.2（生产部署前必做） |
| 3 | **`chapters.content_tsv` 全文检索** | v0.2（write_prep 召回用） |
| 4 | **pgvector 列（伏笔语义召回）** | v0.3（情绪模块 / 伏笔用） |
| 5 | **Alembic 迁移框架接入** | v0.2（替换裸 SQL） |
| 6 | **状态机迁移 / 软删除策略** | v0.3（章节 archive、伏笔 retired 等） |
| 7 | **备份 / PITR 配置文档** | v0.2 |
| 8 | **Redis schema 与热层 key 规范** | 单独文件 `schema-redis-v0.1.md` |
| 9 | **多租户模式切换开关** | v0.3（如确认单用户可省） |

---

## 7. 设计取舍说明（FAQ）

**Q: 为什么 `owner_id` 不设为 NOT NULL？**
A: 当前是单用户本地工具（auto_novels 仓库语义），加 NOT NULL 会强制所有 service 代码处理 owner。nullable + partial unique index 允许单用户模式不填，多用户模式只填一项即可平滑升级。

**Q: 为什么 `chapters.content` 是 TEXT 而不是 JSONB？**
A: 正文是 markdown，纯文本即可；JSONB 优势是查询字段，这里没有要按段落查询。TEXT 更直观，psql `\d` 时直接看。

**Q: 为什么 `chapter_records` 同时存在表和 VIEW？**
A: VIEW 性能依赖底层 join 速度，长篇扫描时可能慢。表保留作"批量预计算"fallback。生产建议用 VIEW + 按需物化策略。

**Q: 为什么 `foreshadowing.priority` 不是 enum？**
A: priority 是连续值（0–5 整数），便于排序和聚合。enum 强约束场景不适用。

**Q: 为什么 `timeline_events` 双列而不是 JSONB？**
A: 双列让"只查读者已知 / 只查作者真相"可以用部分索引（已建 `timeline_events_author_only_idx` / `timeline_events_reader_idx`）。JSONB 不享受这个优化。

---

## 8. 后续衔接

| 下一步 | 关联文件 |
|---|---|
| Redis schema（热层 key 规范） | `schema-redis-v0.1.md`（待写） |
| SQLAlchemy 模型 + Alembic 迁移 | `models/` + `migrations/`（待写） |
| Repository / Service 骨架 | `repositories/` + `services/`（待写） |
| LangGraph 图骨架 | `graphs/`（待写） |
| 最小冒烟测试 | `tests/smoke/`（待写） |
---

# §6 schema-pg-v0.1.sql — 基础 SQL

> 角色：基础 SQL schema（19 表 + 1 VIEW + 1 函数）

```sql
-- ============================================================================
-- auto_novels · PostgreSQL Schema v0.1
-- ----------------------------------------------------------------------------
-- 基于 docs/oh-story-langgraph-mcp-decomposition.md §2.1 落地。
-- 已合入前次设计评审的 8 条 ⚠️❌ 补丁（enums/索引/审计/版本守卫/迁移路径等）。
--
-- 适用版本: PostgreSQL 15+
-- 依赖扩展: uuid-ossp, pgcrypto, vector(pgvector)
-- 可选扩展: pg_trgm / zhparser（按需启用，中文检索）
--
-- 应用方式:
--   psql -h <host> -U <user> -d auto_novels -f schema-pg-v0.1.sql
-- 或 docker:
--   docker exec -i auto_novels_pg psql -U postgres -d auto_novels < schema-pg-v0.1.sql
-- ============================================================================

-- ============================================================================
-- 0. EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- gen_random_bytes()
CREATE EXTENSION IF NOT EXISTS "vector";         -- pgvector（预留情绪模块/伏笔语义召回）
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- 中文三元组检索（按需）
-- CREATE EXTENSION zhparser;                    -- 中文分词（按需）

-- ============================================================================
-- 1. ENUM TYPES
-- ============================================================================

-- 1.1 project_status
CREATE TYPE project_status AS ENUM (
    'planning',     -- 规划中（开书前）
    'active',       -- 当前活跃书（每 owner 最多 1 个，partial unique index 兜底）
    'paused',       -- 暂停
    'completed',    -- 完本
    'archived',     -- 归档
    'importing',    -- 导入中
    'failed'        -- 初始化/导入失败
);

-- 1.2 chapter_status
CREATE TYPE chapter_status AS ENUM (
    'draft',        -- 草稿（写作 agent 临时落库，未 commit）
    'reviewing',    -- 审查中
    'committed',    -- 已提交（不可变快照）
    'archived'      -- 归档/废稿
);

-- 1.3 outline_chapter_status
CREATE TYPE outline_chapter_status AS ENUM (
    'planned',      -- 已规划
    'writing',      -- 写作中
    'committed',    -- 已成稿
    'skipped'       -- 跳过/合并
);

-- 1.4 foreshadowing_status
CREATE TYPE foreshadowing_status AS ENUM (
    'planted',      -- 已埋设
    'hinted',       -- 已暗示
    'revealed',     -- 已揭示
    'retired',      -- 作废（不再使用）
    'broken'        -- 已破裂（被情节破坏）
);

-- 1.5 setting_kind
CREATE TYPE setting_kind AS ENUM (
    '关系',                  -- 人物关系网
    '题材定位',              -- genre positioning
    '题材正文提示卡',        -- 题材正文 hints
    '世界观',                -- world building
    '金手指',                -- 特长/外挂
    '势力'                   -- factions
);

-- 1.6 analysis_kind
CREATE TYPE analysis_kind AS ENUM (
    'golden',      -- 前 3 章深度拆解
    'plot',        -- 剧情聚合
    'rhythm',      -- 节奏聚合
    'emotion',     -- 情绪聚合
    'settings',    -- 设定聚合
    'characters',  -- 角色聚合
    'relations',   -- 关系聚合
    'report',      -- 拆文报告
    'style'        -- 文风
);

-- 1.7 analysis_stage
CREATE TYPE analysis_stage AS ENUM (
    'stage0_overview',
    'stage1_golden3',
    'stage1_checkpoint',
    'stage2_extract',
    'stage2_validate',
    'stage2_merge',
    'stage3_aggregate',
    'stage4a_settings',
    'stage4b_characters',
    'stage4c_relations',
    'stage5_report',
    'stage6_style',
    'complete',
    'failed'
);

-- 1.8 analysis_stage_status
CREATE TYPE analysis_stage_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'skipped'
);

-- 1.9 scan_platform
CREATE TYPE scan_platform AS ENUM (
    'qidian', 'fanqie', 'qimao', 'jjwxc', 'ciweimao', 'dz', 'heiyan'
);

-- 1.10 reference_kind
CREATE TYPE reference_kind AS ENUM (
    '情绪模块',
    '节奏参考',
    '文风参考',
    '题材卡',
    '设定卡',
    '其他'
);

-- 1.11 memory_scope
CREATE TYPE memory_scope AS ENUM (
    'global',      -- 全作者共享
    'project',     -- 单书（scope_ref = project_id）
    'genre'        -- 单题材（scope_ref = 题材标识）
);

-- ============================================================================
-- 2. PROJECT MANAGEMENT
-- ============================================================================

CREATE TABLE projects (
    id              BIGSERIAL PRIMARY KEY,
    owner_id        UUID,                              -- 预留多用户；单用户模式可空
    slug            TEXT NOT NULL,                     -- 文件系统友好 slug
    title           TEXT NOT NULL,
    genre           TEXT,
    platform        scan_platform,                     -- 主要发布平台
    status          project_status NOT NULL DEFAULT 'planning',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT projects_owner_slug_uniq UNIQUE (owner_id, slug)
);

-- 唯一活跃书约束（同 owner 最多 1 个 active）
CREATE UNIQUE INDEX projects_one_active_per_owner
    ON projects (owner_id)
    WHERE status = 'active' AND owner_id IS NOT NULL;

CREATE INDEX projects_status_idx ON projects (status);
CREATE INDEX projects_platform_idx ON projects (platform);

COMMENT ON TABLE projects IS '项目/书。status=active 标记当前活跃书（每 owner 唯一）。';


CREATE TABLE settings (
    id              BIGSERIAL PRIMARY KEY,
    project_id      BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    kind            setting_kind NOT NULL,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,                     -- markdown
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT settings_project_kind_title_uniq UNIQUE (project_id, kind, title)
);

CREATE INDEX settings_project_idx ON settings (project_id);
CREATE INDEX settings_kind_idx ON settings (kind);

COMMENT ON TABLE settings IS '项目设定卡。kind 枚举限定为 §2.1 6 类。';

-- ============================================================================
-- 3. OUTLINE & CONTENT
-- ============================================================================

CREATE TABLE volumes (
    id              BIGSERIAL PRIMARY KEY,
    project_id      BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    no              INTEGER NOT NULL,                  -- 卷号（1-based）
    title           TEXT NOT NULL,
    synopsis        TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT volumes_project_no_uniq UNIQUE (project_id, no)
);

CREATE INDEX volumes_project_idx ON volumes (project_id);


CREATE TABLE outline_chapters (
    id                  BIGSERIAL PRIMARY KEY,
    volume_id           BIGINT NOT NULL REFERENCES volumes(id) ON DELETE CASCADE,
    project_id          BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,  -- 反范式，便于查询
    chapter_no          INTEGER NOT NULL,
    title               TEXT,
    beats_jsonb         JSONB NOT NULL DEFAULT '[]'::jsonb,    -- 情节点数组
    contract_status     outline_chapter_status NOT NULL DEFAULT 'planned',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT outline_chapters_volume_no_uniq UNIQUE (volume_id, chapter_no),
    CONSTRAINT outline_chapters_project_no_uniq UNIQUE (project_id, chapter_no)
);

CREATE INDEX outline_chapters_project_idx ON outline_chapters (project_id);
CREATE INDEX outline_chapters_status_idx ON outline_chapters (project_id, contract_status);

COMMENT ON COLUMN outline_chapters.beats_jsonb IS '情节点数组，结构: [{id, text, order, hook_type}]';


CREATE TABLE chapters (
    id                  BIGSERIAL PRIMARY KEY,
    project_id          BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    volume_id           BIGINT REFERENCES volumes(id) ON DELETE SET NULL,    -- 允许换卷（loose FK）
    chapter_no          INTEGER NOT NULL,
    title               TEXT,
    content             TEXT NOT NULL DEFAULT '',     -- 正文 TEXT（非 JSONB）
    wordcount           INTEGER NOT NULL DEFAULT 0,
    status              chapter_status NOT NULL DEFAULT 'draft',
    revision            BIGINT NOT NULL DEFAULT 1,    -- 乐观锁版本号：每次 commit +1
    committed_at        TIMESTAMPTZ,                  -- 提交时间（草稿态为空）
    committed_by        TEXT,                          -- 提交者（agent 标识 or user_id）
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chapters_project_no_uniq UNIQUE (project_id, chapter_no)
);

CREATE INDEX chapters_project_idx ON chapters (project_id);
CREATE INDEX chapters_status_idx ON chapters (project_id, status);
CREATE INDEX chapters_volume_idx ON chapters (volume_id);
CREATE INDEX chapters_committed_at_idx
    ON chapters (project_id, committed_at DESC NULLS LAST);

-- 全文检索占位（按需启用）：
-- ALTER TABLE chapters ADD COLUMN content_tsv tsvector
--   GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED;
-- CREATE INDEX chapters_content_tsv_idx ON chapters USING GIN (content_tsv);

COMMENT ON COLUMN chapters.revision IS '乐观锁版本号：每次 commit +1。';
COMMENT ON COLUMN chapters.content IS '正文 TEXT（非 JSONB）：短篇 <50KB，长篇单章 <200KB。';

-- ============================================================================
-- 4. TRACKING (追踪铁律 — 唯一真值源)
-- ============================================================================

CREATE TABLE tracking_state (
    project_id              BIGINT PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
    state_revision          BIGINT NOT NULL DEFAULT 1,    -- 单调递增，commit 时 +1
    last_committed_chapter  INTEGER,
    state_jsonb             JSONB NOT NULL DEFAULT '{}'::jsonb,    -- 原 _tracking-state.json 兼容
    format_version          INTEGER NOT NULL DEFAULT 1,            -- JSONB schema 版本
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tracking_state IS '追踪权威状态。state_jsonb 兼容原 _tracking-state.json。commit 时 state_revision+1。';


CREATE TABLE characters (
    id                  BIGSERIAL PRIMARY KEY,
    project_id          BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    kind                TEXT NOT NULL DEFAULT 'main',  -- main/support/antagonist/mentor/...
    profile_jsonb       JSONB NOT NULL DEFAULT '{}'::jsonb,  -- 完整档案
    active_status       BOOLEAN NOT NULL DEFAULT TRUE,
    first_appearance    INTEGER,                              -- 首次出场章节号
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT characters_project_name_uniq UNIQUE (project_id, name)
);

CREATE INDEX characters_project_idx ON characters (project_id);
CREATE INDEX characters_active_idx ON characters (project_id) WHERE active_status = TRUE;

COMMENT ON TABLE characters IS '角色状态。profile_jsonb 兼容原 追踪/角色状态/*.md 字段。';


CREATE TABLE foreshadowing (
    id                  BIGSERIAL PRIMARY KEY,
    project_id          BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    content             TEXT NOT NULL,
    planted_chapter     INTEGER,
    resolved_chapter    INTEGER,
    status              foreshadowing_status NOT NULL DEFAULT 'planted',
    priority            INTEGER NOT NULL DEFAULT 0,    -- 0=低，5=主伏笔
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX foreshadowing_project_idx ON foreshadowing (project_id);
CREATE INDEX foreshadowing_status_idx ON foreshadowing (project_id, status);

-- 部分索引：未揭示伏笔（写正文时最常查）
CREATE INDEX foreshadowing_unresolved_idx
    ON foreshadowing (project_id, priority DESC)
    WHERE status IN ('planted', 'hinted');


CREATE TABLE timeline_events (
    id                  BIGSERIAL PRIMARY KEY,
    project_id          BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    chapter_no          INTEGER NOT NULL,
    author_content      TEXT,                              -- 作者真相（仅作者可见）
    reader_content      TEXT,                              -- 读者已知（对应原文叙事）
    event_at            TIMESTAMPTZ,                       -- 故事内时间戳（按需）
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT timeline_events_chapter_required
        CHECK (author_content IS NOT NULL OR reader_content IS NOT NULL)
);

CREATE INDEX timeline_events_project_chapter_idx
    ON timeline_events (project_id, chapter_no);

CREATE INDEX timeline_events_author_only_idx
    ON timeline_events (project_id, chapter_no)
    WHERE author_content IS NOT NULL AND reader_content IS NULL;

CREATE INDEX timeline_events_reader_idx
    ON timeline_events (project_id, chapter_no)
    WHERE reader_content IS NOT NULL;

COMMENT ON TABLE timeline_events IS '时间线。author_content 仅作者可见；reader_content 对应原文叙事。';


-- 逐章记录 — 派生数据（推荐改为 VIEW，见 §11）
CREATE TABLE chapter_records (
    project_id          BIGINT NOT NULL,
    chapter_no          INTEGER NOT NULL,
    context             JSONB NOT NULL DEFAULT '{}'::jsonb,
    characters          JSONB NOT NULL DEFAULT '[]'::jsonb,    -- 出场角色名单
    events              JSONB NOT NULL DEFAULT '[]'::jsonb,    -- 事件摘要
    foreshadowing       JSONB NOT NULL DEFAULT '[]'::jsonb,    -- 涉及伏笔
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (project_id, chapter_no),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

COMMENT ON TABLE chapter_records IS '逐章记录（派生）。推荐改为 MATERIALIZED VIEW（见 §11.1）。';

-- ============================================================================
-- 5. CONTEXT VIEW (上下文视图 — 固定 7 列 ≤12KB)
-- ============================================================================

CREATE TABLE context_views (
    project_id          BIGINT NOT NULL,
    state_revision      BIGINT NOT NULL,
    content             TEXT NOT NULL,                  -- ≤12KB markdown
    built_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (project_id, state_revision),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX context_views_latest_idx
    ON context_views (project_id, state_revision DESC);

COMMENT ON TABLE context_views IS '上下文视图（7 列 ≤12KB）。随 commit 写透；state_revision 防版本漂移。';

-- ============================================================================
-- 6. ANALYSIS (拆文库)
-- ============================================================================

CREATE TABLE analysis_chapters (
    id                  BIGSERIAL PRIMARY KEY,
    book_id             BIGINT NOT NULL,                -- 注意：book_id 是被拆解的源书的逻辑 ID（非 project_id）
    chapter_no          INTEGER NOT NULL,
    summary             TEXT,
    beats_jsonb         JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_label        TEXT,                           -- 来源标签（如 起点-《XXX》-第N章）
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT analysis_chapters_book_chapter_uniq UNIQUE (book_id, chapter_no)
);

CREATE INDEX analysis_chapters_book_idx ON analysis_chapters (book_id);

COMMENT ON TABLE analysis_chapters IS '拆文库（单章）。book_id 不同于 project_id — 是被拆解的源书的逻辑 ID。';


CREATE TABLE analysis_aggregates (
    id                  BIGSERIAL PRIMARY KEY,
    book_id             BIGINT NOT NULL,
    kind                analysis_kind NOT NULL,
    content             TEXT NOT NULL,                  -- markdown
    metadata_jsonb      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT analysis_aggregates_book_kind_uniq UNIQUE (book_id, kind)
);

CREATE INDEX analysis_aggregates_book_idx ON analysis_aggregates (book_id);
CREATE INDEX analysis_aggregates_kind_idx ON analysis_aggregates (kind);


CREATE TABLE analysis_progress (
    id                  BIGSERIAL PRIMARY KEY,
    book_id             BIGINT NOT NULL,
    stage               analysis_stage NOT NULL,
    status              analysis_stage_status NOT NULL DEFAULT 'pending',
    last_cursor         TEXT,                           -- 断点恢复游标
    error_message       TEXT,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT analysis_progress_book_stage_uniq UNIQUE (book_id, stage)
);

CREATE INDEX analysis_progress_book_idx ON analysis_progress (book_id);
CREATE INDEX analysis_progress_status_idx ON analysis_progress (status);

COMMENT ON TABLE analysis_progress IS '拆解进度（断点恢复）。每 stage 一行。';

-- ============================================================================
-- 7. AUTHOR MEMORY
-- ============================================================================

CREATE TABLE author_memory (
    id              BIGSERIAL PRIMARY KEY,
    owner_id        UUID,                              -- 单用户模式可空
    kind            TEXT NOT NULL,                     -- kind 自由（如 "voice"/"taboo"/"preference"）
    content         TEXT NOT NULL,
    scope           memory_scope NOT NULL DEFAULT 'global',
    scope_ref       TEXT,                              -- scope=project/genre 时存对应 ID
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT author_memory_scope_ref_required
        CHECK (
            (scope = 'global' AND scope_ref IS NULL) OR
            (scope IN ('project', 'genre') AND scope_ref IS NOT NULL)
        )
);

CREATE INDEX author_memory_owner_idx ON author_memory (owner_id);
CREATE INDEX author_memory_scope_idx ON author_memory (scope, scope_ref);
CREATE INDEX author_memory_active_idx ON author_memory (active) WHERE active = TRUE;

COMMENT ON TABLE author_memory IS '作者记忆。scope=global 全作者共享；=project 按书；=genre 按题材。append-only 语义由 service 层强制。';

-- ============================================================================
-- 8. BENCHMARKS & REFERENCE MATERIALS
-- ============================================================================

CREATE TABLE benchmarks (
    id              BIGSERIAL PRIMARY KEY,
    project_id      BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    book_title      TEXT NOT NULL,
    content         TEXT NOT NULL,
    is_primary      BOOLEAN NOT NULL DEFAULT FALSE,    -- 主对标（每项目仅 1 个）
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX benchmarks_project_idx ON benchmarks (project_id);
CREATE UNIQUE INDEX benchmarks_one_primary_per_project
    ON benchmarks (project_id)
    WHERE is_primary = TRUE;


CREATE TABLE reference_materials (
    id              BIGSERIAL PRIMARY KEY,
    project_id      BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    kind            reference_kind NOT NULL,
    is_primary      BOOLEAN NOT NULL DEFAULT FALSE,    -- 主契约标记（write_prep Reference Gate 检查）
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 主契约唯一：(project_id, kind) 最多 1 个 is_primary=true
CREATE UNIQUE INDEX reference_materials_one_primary_per_kind
    ON reference_materials (project_id, kind)
    WHERE is_primary = TRUE;

CREATE INDEX reference_materials_project_idx ON reference_materials (project_id);
CREATE INDEX reference_materials_kind_idx ON reference_materials (kind);

COMMENT ON TABLE reference_materials IS '参考资料。is_primary=true 行 = write_prep Reference Gate 检查的主契约。';

-- ============================================================================
-- 9. MARKET SCAN DATA
-- ============================================================================

CREATE TABLE scan_results (
    id              BIGSERIAL PRIMARY KEY,
    platform        scan_platform NOT NULL,
    snapshot_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_jsonb       JSONB NOT NULL,                    -- 原始采集
    cleaned_jsonb   JSONB,                             -- 清洗后
    report          TEXT,                              -- 扫榜报告
    metadata_jsonb  JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX scan_results_platform_time_idx
    ON scan_results (platform, snapshot_at DESC);
CREATE INDEX scan_results_time_idx ON scan_results (snapshot_at DESC);

COMMENT ON TABLE scan_results IS '扫榜数据（append-only）。生产环境建议按 snapshot_at 月度分区。';

-- ============================================================================
-- 10. COVERS
-- ============================================================================

CREATE TABLE covers (
    id              BIGSERIAL PRIMARY KEY,
    project_id      BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_path       TEXT NOT NULL,                     -- 磁盘相对路径
    platform        scan_platform,                     -- 平台尺寸导出
    style_tags      JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT covers_project_platform_uniq UNIQUE (project_id, platform)
);

CREATE INDEX covers_project_idx ON covers (project_id);

COMMENT ON TABLE covers IS '封面元数据。图片二进制留文件系统，DB 存相对路径。';

-- ============================================================================
-- 11. VIEWS & FUNCTIONS — 派生数据
-- ============================================================================

-- 11.1 chapter_records_v — 推荐用此 VIEW 替代物化表
CREATE OR REPLACE VIEW chapter_records_v AS
SELECT
    c.project_id,
    c.chapter_no,
    jsonb_build_object(
        'title', c.title,
        'wordcount', c.wordcount,
        'status', c.status,
        'committed_at', c.committed_at,
        'revision', c.revision
    ) AS context,
    COALESCE(
        (SELECT jsonb_agg(jsonb_build_object('name', ch.name, 'kind', ch.kind, 'active', ch.active_status))
         FROM characters ch
         WHERE ch.project_id = c.project_id
           AND ch.first_appearance <= c.chapter_no
           AND ch.active_status = TRUE),
        '[]'::jsonb
    ) AS characters,
    COALESCE(
        (SELECT jsonb_agg(jsonb_build_object(
            'id', te.id,
            'author', te.author_content,
            'reader', te.reader_content))
         FROM timeline_events te
         WHERE te.project_id = c.project_id AND te.chapter_no = c.chapter_no),
        '[]'::jsonb
    ) AS events,
    COALESCE(
        (SELECT jsonb_agg(jsonb_build_object(
            'id', f.id,
            'content', f.content,
            'status', f.status,
            'planted_chapter', f.planted_chapter,
            'resolved_chapter', f.resolved_chapter))
         FROM foreshadowing f
         WHERE f.project_id = c.project_id
           AND f.planted_chapter <= c.chapter_no
           AND (f.resolved_chapter IS NULL OR f.resolved_chapter > c.chapter_no)),
        '[]'::jsonb
    ) AS foreshadowing,
    c.updated_at
FROM chapters c;

COMMENT ON VIEW chapter_records_v IS '逐章记录派生 VIEW。推荐替代物化表 chapter_records。';

-- 11.2 build_context_view — 上下文视图装配函数（带版本守卫 + 写透缓存）
CREATE OR REPLACE FUNCTION build_context_view(p_project_id BIGINT)
RETURNS TEXT AS $$
DECLARE
    v_revision BIGINT;
    v_content TEXT;
BEGIN
    SELECT state_revision INTO v_revision
    FROM tracking_state
    WHERE project_id = p_project_id;

    IF v_revision IS NULL THEN
        RETURN NULL;
    END IF;

    -- 检查是否已有缓存
    SELECT content INTO v_content
    FROM context_views
    WHERE project_id = p_project_id
      AND state_revision = v_revision;

    IF v_content IS NOT NULL THEN
        RETURN v_content;
    END IF;

    -- 装配新视图（固定 7 列 markdown，≤12KB）
    v_content := format(
        E'# 项目 #%s\n\n## 1. 当前进度\n%s\n\n## 2. 主要设定\n%s\n\n## 3. 活跃角色\n%s\n\n## 4. 伏笔（未揭示）\n%s\n\n## 5. 时间线（读者已知）\n%s\n\n## 6. 题材卡\n%s\n\n## 7. 文风参考\n%s',
        p_project_id,
        COALESCE((SELECT state_jsonb->'progress' FROM tracking_state WHERE project_id = p_project_id)::text, '(空)'),
        COALESCE((SELECT string_agg(title || ': ' || content, E'\n')
                  FROM settings
                  WHERE project_id = p_project_id AND kind IN ('世界观', '金手指', '势力')), '(空)'),
        COALESCE((SELECT string_agg(name || ' (' || kind || ')', ', ')
                  FROM characters
                  WHERE project_id = p_project_id AND active_status = TRUE), '(空)'),
        COALESCE((SELECT string_agg(content, E'\n')
                  FROM foreshadowing
                  WHERE project_id = p_project_id AND status IN ('planted', 'hinted')
                  ORDER BY priority DESC), '(空)'),
        COALESCE((SELECT string_agg('Ch' || chapter_no || ': ' || reader_content, E'\n')
                  FROM timeline_events
                  WHERE project_id = p_project_id AND reader_content IS NOT NULL
                  ORDER BY chapter_no), '(空)'),
        COALESCE((SELECT content FROM reference_materials
                  WHERE project_id = p_project_id AND kind = '题材卡' AND is_primary = TRUE), '(未设置)'),
        COALESCE((SELECT content FROM reference_materials
                  WHERE project_id = p_project_id AND kind = '文风参考' AND is_primary = TRUE), '(未设置)')
    );

    -- 写透缓存（带版本守卫）
    INSERT INTO context_views (project_id, state_revision, content)
    VALUES (p_project_id, v_revision, v_content)
    ON CONFLICT (project_id, state_revision) DO UPDATE
        SET content = EXCLUDED.content, built_at = NOW();

    RETURN v_content;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION build_context_view IS '上下文视图装配（7 列 ≤12KB）。带 state_revision 版本守卫 + 写透缓存。';

-- ============================================================================
-- 12. UPDATED_AT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT unnest(ARRAY[
            'projects', 'settings', 'volumes', 'outline_chapters', 'chapters',
            'characters', 'foreshadowing', 'analysis_chapters', 'analysis_aggregates',
            'analysis_progress', 'author_memory', 'benchmarks', 'reference_materials', 'covers'
        ])
    LOOP
        EXECUTE format(
            'CREATE TRIGGER %I_set_updated_at BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at()',
            t, t
        );
    END LOOP;
END $$;

-- ============================================================================
-- END
-- 应用完成。建议验证:
--   \dt                -- 列出所有表
--   \dT                -- 列出所有 enum
--   \dv                -- 列出所有 view
--   \df build_context_view
-- ============================================================================```

---

# §7 schema-pg-v0.2.sql — v0.2 补丁 SQL

> 角色：v0.2 补丁 SQL（chapter_records / analysis_chapters 扩展）

> ⚠️ 应用此补丁前必须先应用 §6 schema-pg-v0.1.sql

```sql
-- ============================================================================
-- auto_novels · PostgreSQL Schema v0.2 (PATCH on top of v0.1)
-- ----------------------------------------------------------------------------
-- 基于 docs/schema-pg-v0.1.sql 应用本补丁。
-- 新增内容：
--   1. chapter_records    — 10 个新字段（写自己的书摘要）
--   2. analysis_chapters  — 8 个新字段（拆别人的书详细分析）
--   3. chapter_records_v  — VIEW 同步扩展
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. 前置检查：v0.1 必须已应用
-- ----------------------------------------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'chapter_records'
    ) THEN
        RAISE EXCEPTION 'chapter_records 表不存在 — 请先应用 schema-pg-v0.1.sql';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'analysis_chapters'
    ) THEN
        RAISE EXCEPTION 'analysis_chapters 表不存在 — 请先应用 schema-pg-v0.1.sql';
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 1. chapter_records — 扩展为完整摘要表
-- ----------------------------------------------------------------------------

ALTER TABLE chapter_records
    ADD COLUMN IF NOT EXISTS summary_text          TEXT,
    ADD COLUMN IF NOT EXISTS core_event            TEXT,
    ADD COLUMN IF NOT EXISTS location              TEXT,
    ADD COLUMN IF NOT EXISTS pov                   TEXT,
    ADD COLUMN IF NOT EXISTS emotion_arc           JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS characters_in_scene   JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS foreshadowing_changes JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS open_conflicts        JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS chapter_hook          TEXT,
    ADD COLUMN IF NOT EXISTS continuity_to_next    TEXT;

-- 部分索引：按 summary_text 全文检索（按需启用 zhparser / pg_trgm）
-- CREATE INDEX chapter_records_summary_tsv_idx
--     ON chapter_records USING GIN (to_tsvector('simple', coalesce(summary_text, '')));

COMMENT ON COLUMN chapter_records.summary_text          IS '一句话核心事件摘要（≤60 字）';
COMMENT ON COLUMN chapter_records.core_event            IS '事件主体（动词开头）';
COMMENT ON COLUMN chapter_records.location              IS '主场景地点';
COMMENT ON COLUMN chapter_records.pov                   IS '视角（人称 + POV 角色）';
COMMENT ON COLUMN chapter_records.emotion_arc           IS '情绪起止 + 强度 1-10，例: {start, end, intensity}';
COMMENT ON COLUMN chapter_records.characters_in_scene   IS '出场角色 + 状态变化，例: [{name, role, state_change}]';
COMMENT ON COLUMN chapter_records.foreshadowing_changes IS '伏笔操作记录，例: [{id, action: planted|hinted|revealed, note}]';
COMMENT ON COLUMN chapter_records.open_conflicts        IS '章节末尾未解决悬念';
COMMENT ON COLUMN chapter_records.chapter_hook          IS '章尾钩子（一句）';
COMMENT ON COLUMN chapter_records.continuity_to_next    IS '给下一章的衔接提示';

-- ----------------------------------------------------------------------------
-- 2. analysis_chapters — 扩展为结构化分析表
-- ----------------------------------------------------------------------------

ALTER TABLE analysis_chapters
    ADD COLUMN IF NOT EXISTS rhythm_pattern         TEXT,
    ADD COLUMN IF NOT EXISTS dialogue_ratio         NUMERIC(4,3),
    ADD COLUMN IF NOT EXISTS sentence_length_avg    NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS punctuation_features  JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS key_phrases            JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS characters_featured    JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS foreshadowing_observed JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS emotion_beats          JSONB NOT NULL DEFAULT '[]'::jsonb;

COMMENT ON COLUMN analysis_chapters.rhythm_pattern         IS '节奏模式描述，例: 起-承-转-钩';
COMMENT ON COLUMN analysis_chapters.dialogue_ratio         IS '对话占比 0.0-1.0';
COMMENT ON COLUMN analysis_chapters.sentence_length_avg    IS '平均句长（字）';
COMMENT ON COLUMN analysis_chapters.punctuation_features  IS '标点特征，例: [大量短句, 问号多, 逗号多]';
COMMENT ON COLUMN analysis_chapters.key_phrases            IS '本章关键词';
COMMENT ON COLUMN analysis_chapters.characters_featured    IS '本章出场角色';
COMMENT ON COLUMN analysis_chapters.foreshadowing_observed IS '观察到的伏笔';
COMMENT ON COLUMN analysis_chapters.emotion_beats          IS '情绪节拍，例: [{position: 0.0-1.0, emotion, intensity}]';

-- ----------------------------------------------------------------------------
-- 3. chapter_records_v VIEW — 同步扩展
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW chapter_records_v AS
SELECT
    c.project_id,
    c.chapter_no,
    -- v0.2 摘要字段
    cr.summary_text,
    cr.core_event,
    cr.location,
    cr.pov,
    cr.emotion_arc,
    cr.characters_in_scene,
    cr.foreshadowing_changes,
    cr.open_conflicts,
    cr.chapter_hook,
    cr.continuity_to_next,
    cr.updated_at                                          AS summary_updated_at,
    -- 章节元数据
    jsonb_build_object(
        'title', c.title,
        'wordcount', c.wordcount,
        'status', c.status,
        'committed_at', c.committed_at,
        'revision', c.revision
    ) AS context,
    -- 出场角色（含元数据）
    COALESCE(
        (SELECT jsonb_agg(jsonb_build_object('name', ch.name, 'kind', ch.kind, 'active', ch.active_status))
         FROM characters ch
         WHERE ch.project_id = c.project_id
           AND ch.first_appearance <= c.chapter_no
           AND ch.active_status = TRUE),
        '[]'::jsonb
    ) AS characters,
    -- 时间线事件
    COALESCE(
        (SELECT jsonb_agg(jsonb_build_object(
            'id', te.id,
            'author', te.author_content,
            'reader', te.reader_content))
         FROM timeline_events te
         WHERE te.project_id = c.project_id AND te.chapter_no = c.chapter_no),
        '[]'::jsonb
    ) AS events,
    -- 当前章节涉及到的伏笔（未揭示部分）
    COALESCE(
        (SELECT jsonb_agg(jsonb_build_object(
            'id', f.id,
            'content', f.content,
            'status', f.status,
            'planted_chapter', f.planted_chapter,
            'resolved_chapter', f.resolved_chapter))
         FROM foreshadowing f
         WHERE f.project_id = c.project_id
           AND f.planted_chapter <= c.chapter_no
           AND (f.resolved_chapter IS NULL OR f.resolved_chapter > c.chapter_no)),
        '[]'::jsonb
    ) AS foreshadowing
FROM chapters c
LEFT JOIN chapter_records cr
    ON cr.project_id = c.project_id AND cr.chapter_no = c.chapter_no;

COMMENT ON VIEW chapter_records_v IS '逐章记录派生 VIEW（v0.2 扩展含摘要、情绪、伏笔）。';

-- ----------------------------------------------------------------------------
-- 4. Pydantic-style JSON Schema 文档（供 LangChain structured_output 使用）
-- ----------------------------------------------------------------------------

COMMENT ON COLUMN chapter_records.emotion_arc IS '
JSON Schema:
{
  "type": "object",
  "properties": {
    "start": {"type": "string", "description": "起始情绪词"},
    "end":   {"type": "string", "description": "结束情绪词"},
    "intensity": {"type": "integer", "minimum": 1, "maximum": 10}
  }
}';

COMMENT ON COLUMN chapter_records.characters_in_scene IS '
JSON Schema:
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "role": {"type": "string", "enum": ["protagonist", "support", "antagonist", "mentor", "cameo"]},
      "state_change": {"type": "string", "description": "本章状态变化"}
    },
    "required": ["name", "role"]
  }
}';

COMMENT ON COLUMN chapter_records.foreshadowing_changes IS '
JSON Schema:
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {"type": "integer"},
      "action": {"type": "string", "enum": ["planted", "hinted", "revealed", "retired"]},
      "note": {"type": "string"}
    },
    "required": ["id", "action"]
  }
}';

COMMENT ON COLUMN analysis_chapters.emotion_beats IS '
JSON Schema:
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "position": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "章节内位置比例"},
      "emotion":  {"type": "string"},
      "intensity": {"type": "integer", "minimum": 1, "maximum": 10}
    },
    "required": ["position", "emotion"]
  }
}';

-- ----------------------------------------------------------------------------
-- END v0.2 patch
-- 验证:
--   \d chapter_records
--   \d analysis_chapters
--   SELECT * FROM chapter_records_v LIMIT 1;
-- ============================================================================```

---

# §8 chapter-summary-v0.1 — 章节摘要设计


---

# Chapter Summary v0.1 · 设计与实现

> 基于 schema-pg-v0.1.sql + schema-pg-v0.2.sql 落地。
> 涵盖两类摘要：(A) 自己的书每章 commit 后自动生成；(B) 拆别人的书每章结构化分析。

---

## 1. 两种摘要的差异

| 维度 | chapter_records（自己的书） | analysis_chapters（拆别人的书） |
|---|---|---|
| **频率** | 每章 commit 必产 | 仅扫榜/学习时按需 |
| **预算** | ≤500B | ≤3KB |
| **情感字段** | 简化 `emotion_arc`（起止 + 强度） | 完整 `emotion_beats`（每节位置） |
| **节奏字段** | 无 | 完整 `rhythm_pattern` |
| **文风字段** | 无 | `sentence_length_avg / punctuation_features` |
| **谁写** | chapter commit pipeline（同步） | chapter-extractor agent（并行 map） |
| **写入路径** | `ChapterService.commit` 事务内 | `AnalysisService.upsert_chapter` |
| **下游用途** | `write_prep` 召回 | `Stage3-6` 聚合 |

---

## 2. A · `chapter_records` 字段定义（v0.2）

| 字段 | 类型 | 用途 | 示例 |
|---|---|---|---|
| `summary_text` | TEXT | 一句话核心事件 | "主角收到神秘信件，疑前世导师线索；决定查档案馆" |
| `core_event` | TEXT | 事件主体（动词开头） | "收到神秘信件并决定调查" |
| `location` | TEXT | 主场景地点 | "老家书房" |
| `pov` | TEXT | 视角（人称 + POV 角色） | "林远舟·第一人称" |
| `emotion_arc` | JSONB | `{start, end, intensity}` | `{"start":"平静","end":"震惊","intensity":6}` |
| `characters_in_scene` | JSONB | `[{name, role, state_change}]` | `[{"name":"林远舟","role":"protagonist","state_change":"怀疑→行动"}]` |
| `foreshadowing_changes` | JSONB | `[{id, action, note}]` | `[{"id":5,"action":"hinted","note":"导师身份再暗示"}]` |
| `open_conflicts` | JSONB | 章末未解悬念 | `["信件来源","导师生死"]` |
| `chapter_hook` | TEXT | 章尾钩子 | "主角合上信，开车去档案馆" |
| `continuity_to_next` | TEXT | 给下一章的衔接提示 | "下一章进入档案馆，主角内心仍有疑虑" |

完整 JSON 示例见 schema-pg-v0.2.sql 中的 `COMMENT` 块。

---

## 3. B · `analysis_chapters` 字段定义（v0.2）

| 字段 | 类型 | 用途 |
|---|---|---|
| `rhythm_pattern` | TEXT | 节奏模式描述，如 "起-承-转-钩" |
| `dialogue_ratio` | NUMERIC(4,3) | 对话占比 0.0-1.0 |
| `sentence_length_avg` | NUMERIC(5,2) | 平均句长（字） |
| `punctuation_features` | JSONB | `["大量短句","问号多","逗号多"]` |
| `key_phrases` | JSONB | `["不签字","前世","重生"]` |
| `characters_featured` | JSONB | `["林远舟","父亲"]` |
| `foreshadowing_observed` | JSONB | `["重生机制","合伙人骗局"]` |
| `emotion_beats` | JSONB | `[{position: 0.0-1.0, emotion, intensity}]` |
| `beats_jsonb` | JSONB | 情节点分解 `[{order, type, text, wordcount, emotion, tension}]` |

---

## 4. A 实现 · `_generate_summary()`（ChapterService 内）

```python
# services/chapter_service.py
from dataclasses import dataclass
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession


# ---------- Pydantic schema（约束 LLM 输出）----------

class EmotionArc(BaseModel):
    start: str = Field(description="起始情绪词，如 平静/压抑/紧张")
    end: str = Field(description="结束情绪词")
    intensity: int = Field(ge=1, le=10, description="强度 1-10")


class CharacterInScene(BaseModel):
    name: str
    role: str = Field(pattern="^(protagonist|support|antagonist|mentor|cameo)$")
    state_change: str | None = None


class ForeshadowingChange(BaseModel):
    id: int
    action: str = Field(pattern="^(planted|hinted|revealed|retired)$")
    note: str | None = None


class ChapterSummary(BaseModel):
    summary_text: str = Field(max_length=200, description="≤60 字核心事件")
    core_event: str
    location: str | None = None
    pov: str | None = None
    emotion_arc: EmotionArc
    characters_in_scene: list[CharacterInScene]
    foreshadowing_changes: list[ForeshadowingChange] = []
    open_conflicts: list[str] = []
    chapter_hook: str
    continuity_to_next: str


# ---------- 规则提取（不调 LLM，省钱快）----------

async def _extract_rule_based(
    session: AsyncSession,
    project_id: int,
    chapter_no: int,
    content: str,
) -> dict:
    """规则提取：location / pov / characters_in_scene / foreshadowing_changes"""

    # 1. characters_in_scene：从 characters 表 JOIN，扫章节正文确认出场
    from sqlalchemy import select, text as sql_text
    characters = (await session.execute(
        select(Character).where(Character.project_id == project_id)
    )).scalars().all()

    chars_in_scene = []
    for ch in characters:
        # 简单关键词匹配（首字 + 全名）
        if ch.name and ch.name in content:
            chars_in_scene.append({
                "name": ch.name,
                "role": "protagonist" if ch.kind == "main" else "support",
                "state_change": None,  # 由 LLM 补
            })

    # 2. foreshadowing_changes：扫正文关键词匹配
    foreshadows = (await session.execute(
        select(Foreshadowing)
        .where(Foreshadowing.project_id == project_id)
        .where(Foreshadowing.status.in_(['planted', 'hinted']))
    )).scalars().all()

    changes = []
    for f in foreshadows:
        # 简单匹配：伏笔内容前 8 字出现在正文里
        keyword = f.content[:8]
        if keyword in content:
            changes.append({
                "id": f.id,
                "action": "revealed" if f.resolved_chapter == chapter_no else "hinted",
                "note": None,
            })

    # 3. location：从章节前 500 字扫"在/于 + 地名"模式
    head = content[:500]
    location = None
    location_patterns = ["在", "于", "来到", "走进", "抵达"]
    for pat in location_patterns:
        if pat in head:
            # 简化提取（生产用 NLP）
            idx = head.index(pat)
            snippet = head[idx:idx+15].split("，")[0].split("。")[0]
            location = snippet[:20]
            break

    # 4. pov：从 outline_chapters 拿（如果已配置）
    pov = (await session.execute(
        select(OutlineChapter.pov)
        .select_from(OutlineChapter)
        .where(OutlineChapter.project_id == project_id)
        .where(OutlineChapter.chapter_no == chapter_no)
    )).scalar_one_or_none()

    return {
        "characters_in_scene": chars_in_scene,
        "foreshadowing_changes": changes,
        "location": location,
        "pov": pov,
    }


# ---------- LLM 提取（一句话调用，cheap model）----------

SUMMARY_PROMPT = """你是网文编辑。基于【章节正文】+【规则提取的元数据】，输出 JSON 摘要。

# 字段约束
- summary_text: ≤60 字，动词开头，含主角 + 核心动作 + 关键转折
- core_event: ≤20 字，事件主体
- chapter_hook: ≤30 字，章尾钩子（悬念 / 反转 / 行动预告）
- continuity_to_next: ≤30 字，给下一章的衔接提示
- open_conflicts: ≤5 个未解决悬念，每个 ≤10 字
- emotion_arc: {{start, end, intensity(1-10)}}
- characters_in_scene: 已给名单 + state_change（≤15 字描述本章状态变化）

# 已有元数据（直接复用）
{ruled_metadata}

# 章节正文（已截断到 {wordcount_limit} 字）
{chapter_text}

# 输出（严格 JSON，无注释）
"""

async def _extract_llm_based(
    session: AsyncSession,
    project_id: int,
    chapter_no: int,
    content: str,
    ruled: dict,
) -> ChapterSummary:
    """LLM 提取（用 haiku / sonnet-mini 节省成本）"""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="claude-haiku-4-5", temperature=0.2)

    # 截断正文到 ~6000 字（防止 context 爆）
    wordcount_limit = 6000
    truncated = content[:wordcount_limit * 2]  # 粗略按 2 字节/字符估算

    structured_llm = llm.with_structured_output(ChapterSummary)
    result = await structured_llm.ainvoke(
        SUMMARY_PROMPT.format(
            ruled_metadata=json.dumps(ruled, ensure_ascii=False, indent=2),
            chapter_text=truncated,
            wordcount_limit=wordcount_limit,
        )
    )
    return result


# ---------- 入口（ChapterService.commit 内调用）----------

async def _generate_summary(
    self,
    session: AsyncSession,
    project_id: int,
    chapter_no: int,
    content: str,
) -> dict:
    """混合策略：规则先筛元数据 → LLM 补情感/钩子/衔接"""
    # 1. 规则提取（同步、快）
    ruled = await _extract_rule_based(session, project_id, chapter_no, content)

    # 2. LLM 补全（异步、慢）
    summary = await _extract_llm_based(session, project_id, chapter_no, content, ruled)

    # 3. 合并：LLM 输出 + 规则补充的字符名单（取并集去重）
    llm_chars = {c.name: c for c in summary.characters_in_scene}
    ruled_chars = {c["name"]: CharacterInScene(**c) for c in ruled["characters_in_scene"]}
    for name, c in ruled_chars.items():
        if name not in llm_chars:
            llm_chars[name] = c
    summary.characters_in_scene = list(llm_chars.values())

    # 4. 落库（在 chapter_service.commit 事务内）
    return summary.model_dump()
```

---

## 5. B 实现 · `chapter_extractor` agent（haiku 节点）

```python
# agents/chapter_extractor.py
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI


class Beat(BaseModel):
    order: int = Field(ge=1)
    type: str = Field(pattern="^(setup|rising|climax|falling|hook)$")
    text: str = Field(max_length=100)
    wordcount: int = Field(ge=0)
    emotion: str
    tension: int = Field(ge=1, le=10)


class EmotionBeat(BaseModel):
    position: float = Field(ge=0.0, le=1.0)
    emotion: str
    intensity: int = Field(ge=1, le=10)


class ChapterAnalysis(BaseModel):
    summary: str = Field(max_length=200, description="≤60 字核心")
    beats: list[Beat] = Field(min_length=2, max_length=8)
    rhythm_pattern: str = Field(description="如 起-承-转-钩")
    dialogue_ratio: float = Field(ge=0.0, le=1.0)
    sentence_length_avg: float = Field(ge=0.0)
    punctuation_features: list[str]
    key_phrases: list[str] = Field(max_length=10)
    characters_featured: list[str]
    foreshadowing_observed: list[str] = Field(default_factory=list)
    emotion_beats: list[EmotionBeat]


EXTRACTOR_PROMPT = """你是网文结构分析师。拆解【本章正文】，按 JSON Schema 输出结构化分析。

# 重点观察
- 情节点分解（setup/rising/climax/falling/hook）
- 节奏模式（连续 / 跳跃 / 蓄势 / 爆发）
- 对话占比（粗估对话字符 / 总字符）
- 平均句长（按段落采样估算）
- 标点特征（短句多？问号多？破折号多？）
- 情绪曲线（位置 + 词 + 强度）

# 本章正文
{chapter_text}

# 输出（严格 JSON，无注释）
"""


def make_chapter_extractor():
    llm = ChatOpenAI(model="claude-haiku-4-5", temperature=0.1)
    return llm.with_structured_output(ChapterAnalysis)


# 在 AnalyzeGraph.stage2_extract map 节点中使用：
# async def stage2_extract_node(state: dict) -> dict:
#     chapter_text = state["chapter_text"]
#     result = await make_chapter_extractor().ainvoke(
#         EXTRACTOR_PROMPT.format(chapter_text=chapter_text[:8000])
#     )
#     return {"analysis": result.model_dump()}
```

---

## 6. 下游消费

### 6.1 write_prep 召回（第 N 章写第 N+1 章时）

```python
# services/context_service.py
async def recall_prev_chapter_context(self, project_id: int, chapter_no: int) -> str:
    """召回第 N 章摘要，写第 N+1 章时用"""
    async with self.session_factory() as session:
        record = (await session.execute(
            select(ChapterRecord)
            .where(ChapterRecord.project_id == project_id)
            .where(ChapterRecord.chapter_no == chapter_no)
        )).scalar_one_or_none()

    if not record:
        return ""

    # 按优先级装配（≤ 800B）
    return f"""## 第 {chapter_no} 章摘要
{record.summary_text}

**核心事件**: {record.core_event}
**场景**: {record.location or '未知'} | **视角**: {record.pov or '未知'}
**情绪弧**: {record.emotion_arc.get('start','')} → {record.emotion_arc.get('end','')} (强度 {record.emotion_arc.get('intensity',0)}/10)

**章尾钩子**: {record.chapter_hook}

**给下一章的衔接**: {record.continuity_to_next}

**未解决**: {', '.join(record.open_conflicts or []) or '无'}
"""
```

### 6.2 Stage3-6 聚合（拆文时）

```python
# services/analysis_service.py - Stage3 aggregate
async def aggregate_emotion_curve(self, book_id: int) -> dict:
    """把每章的 emotion_beats 串成全书情绪曲线"""
    chapters = (await self.session.execute(
        select(AnalysisChapter)
        .where(AnalysisChapter.book_id == book_id)
        .order_by(AnalysisChapter.chapter_no)
    )).scalars().all()

    full_curve = []
    for ch in chapters:
        for beat in ch.emotion_beats or []:
            full_curve.append({
                "absolute_chapter": ch.chapter_no,
                "relative_position": beat["position"],
                "emotion": beat["emotion"],
                "intensity": beat["intensity"],
            })

    return {"emotion_curve": full_curve}
```

---

## 7. 验证清单

| 检查 | 命令 |
|---|---|
| v0.2 patch 应用成功 | `\d chapter_records` 应见 10 个新字段 |
| VIEW 同步 | `\dv chapter_records_v` |
| Pydantic schema 校验 | `pytest tests/test_chapter_summary.py` |
| LLM 输出符合 schema | 跑 `_extract_llm_based()` 10 次无解析失败 |
| 召回测试 | `tests/test_recall_prev_chapter.py` |

---

## 8. 落地顺序

| 序 | 任务 | 工作量 |
|---|---|---|
| 1 | 应用 schema-pg-v0.2.sql | 5 分钟 |
| 2 | 安装依赖 `langchain-openai / pydantic` | 5 分钟 |
| 3 | 实现 `_extract_rule_based` | 0.5 天 |
| 4 | 实现 `_extract_llm_based` + ChapterSummary schema | 0.5 天 |
| 5 | 接入 `ChapterService.commit` 同事务 | 0.5 天 |
| 6 | 实现 `chapter_extractor` agent + AnalyzeGraph 节点 | 1 天 |
| 7 | 召回测试 + 单元测试 | 0.5 天 |

**不要省略第 3 步的规则提取**——LLM 单次调用能省 30% token，而且字段一致性强很多（角色名单、伏笔 ID 必须从 PG JOIN 拿，不能让 LLM 自由发挥）。

---

## 9. 与现有文档的关系

| 文档 | 关系 |
|---|---|
| schema-pg-v0.1.sql | 基础 schema |
| schema-pg-v0.2.sql | 本设计的 schema 补丁 |
| oh-story-langgraph-mcp-decomposition.md §3.4 | WriteGraph 节点设计 |
| oh-story-langgraph-mcp-decomposition.md §3.3 | AnalyzeGraph stage2 设计 |
---

# §9 short-story-june-14 — 短篇样稿


---

# 六月十四日

闹钟响的时候，林远舟以为自己又迟到了。

他猛地从床上弹起来，伸手去够床头柜。手机屏幕亮着，4:47。

房间里一片昏暗，窗帘缝里漏进一线灰白。妻子睡在身侧，呼吸轻而均匀。

他愣在那里。

这种被褥的柔软、洗衣液的淡香、凌晨四点的安静——他很久没有闻到过了。三年。准确地说，是从那个雨夜之后。

他按亮手机。

**2019 年 6 月 14 日，星期五。**

日期下面，他盯了很久。然后起身，赤脚走到阳台。六月的北京清晨还有些凉，远处的楼群轮廓像水墨画。他点了一支烟——手指抖得厉害。

前世，他在这天上午十点，走进华贸的一家咖啡厅，签下那份让自己从创业新星变成老赖的协议。

合伙人是大学室友，叫陈宥。陈宥笑得很诚恳："远舟，最后一次了，过了这关，咱们就能上岸。"

他没有看出来。陈宥自己也不知道，他已经被更大的局套住。

那份协议，把林远舟名下所有的股权做了质押。林远舟以为是担保，实则是连带。后来资金链断裂，他成了被告，陈宥成了证人。

那一年，他父亲心脏病发作——是接到电话赶去医院的路上。等他签完放弃治疗的同意书，已经是第二天下午三点。

又过了八个月，妻子在客厅留下签好字的离婚协议，搬走了。

他在那间空荡荡的客厅坐了一整夜。

那之后，他每天醒来，都觉得自己还欠着谁。

---

现在他站在阳台，烟快烧到指间。

他掐灭烟头，回到卧室，在妻子枕边放了一杯水——她习惯早上醒来第一口喝凉水。然后他去洗漱，动作很轻。

儿子还在儿童房，睡得很沉。他过去看了一眼，给他掖了掖被角。

孩子九岁。五年后，应该十七岁了。

林远舟深吸一口气，关上房门。

---

上午九点四十，他没去赴约。

他给陈宥发了一条微信：**身体不舒服，改天再签。**

陈宥回复很快："远舟，今天必须啊！"

林远舟没有回。

他叫了一辆车，去协和医院。

心脏内科的诊室门口，等着一个老人——他父亲。

林远舟的父亲，远今年六十二，刚查出冠心病，需要做支架。今天是术前最后一次门诊。

前世，他没赶上。

这一次，他九点四十就到了。

十点零五分，他看见父亲从诊室出来，手里捏着一张检查单，眉头紧锁。

"爸。"

远抬头，愣了愣："你怎么来了？不上班？"

"请假了。"林远舟走过去，自然地接过他手里的单子，"我陪您做检查。"

"不用，我自己能行。"

"我想陪您。"

远看了他一眼，没说话，转身走向电梯。

一路上，父子俩没怎么说话。林远舟看着父亲的背影——肩膀还是直的，步伐还是稳的。他想起前世最后一次见到父亲，是太平间。

眼泪差点下来。

---

下午一点，他把父亲送回家。

远让他进去坐，他说不坐。他怕自己待久了，会忍不住说出那些不该说的话。

他下楼，给妻子发了一条微信：**晚上想吃什么？我做。**

妻子回："你？做饭？"

林远舟笑了一下："试试。"

妻子回了一个笑脸。

他在路上买了菜，回到家已经四点半。厨房里乒乒乓乓两个多小时，做了四菜一汤。

儿子放学回来，趴在餐桌上："爸，今天什么日子啊？"

林远舟把最后一道菜端出来："就是想给你们做顿饭。"

妻子在厨房门口看着他，没说话，眼圈有点红。

---

晚上九点，儿子睡了。

林远舟坐在书房里，没开灯。

手机亮起来。

陈宥："远舟，你在哪儿？真的必须今天啊！求你了！"

林远舟盯着屏幕。

前世，他就是这样一步步走进去的。陈宥是真心想救公司，他只是没看出来，公司已经被套进去了。

如果他今天签了，陈宥会感激他，然后他们一起完蛋。

如果他今天不签，陈宥会恨他，然后——陈宥会怎么走，他不知道。

他想了想，回了一条："陈宥，把协议拍照发我看看。"

三分钟后，照片过来。

林远舟打开，放大，一行一行看。

他看到了前世没看到的一行——股权质押的连带条款，以及对方公司一个他陌生的名字。

他的手指开始发凉。

他没有立刻回陈宥。他把照片转给了一个在律所工作的老同学。

"远舟，这合同有问题。"老同学说，"股权质押连带，是担保的最高级别。你签了，对方出事你也得赔。"

"陈宥知道吗？"

"看样子不知道。他可能只是太急了。"

林远舟关掉手机。

窗外，北京的夜很亮。

他想——前世，陈宥后来怎样？他不记得了。只记得自己是被告。

这一世，他不会签这份合同。

但陈宥呢？

---

第二天，他约陈宥在一家茶馆见面。

陈宥没精打采："远舟，你不签，我扛不了几天。"

"陈宥，"林远舟把手机递过去，"你看这一条。"

陈宥看了，脸色一点一点变白。

"我不知道……"他说。

"我知道。"林远舟说，"你肯定不知道。"

陈宥抬头看他，眼眶发红："远舟，你早就看出来了？"

"刚刚。"

陈宥盯着他看了很久。

"那我怎么办？"

林远舟说："换律师，换协议，再谈。给我一周时间。"

陈宥哭了。三十八岁的人，在茶馆里哭得像个孩子。

林林远舟没安慰。他只是坐在那里，等他哭完。

前世，他没等到这一天——他被推着向前，没想过回头拉陈宥一把。

这一世，他想试试。

---

傍晚，他回到家。

妻子在客厅看电视，儿子在写作业。

他走过去，坐在妻子身边。

"怎么了？"妻子问。

"想跟你说个事。"

"说啊。"

"以后做饭这件事，我来。"他说。

妻子笑："你做的那个糖醋排骨，能吃吗？"

"能吃。"

"好。"

窗外，北京的夜还是那么亮。

林远舟看着电视里无聊的综艺，忽然想——前世那个他，最后悔的事是什么？

不是破产，不是离婚，不是父亲去世。

是那些他觉得"下次吧"、"明天吧"、"等我忙完再说"的事。

这一世，他想不再说"下次"。

---

那天夜里，他做了一个梦。

梦里他走在一条很长的走廊，两边都是门。他打开第一扇，是陈宥。打开第二扇，是父亲。打开第三扇，是妻子。打开第四扇，是儿子。

每一扇门里的人都朝他笑。

他站在走廊尽头，回望。

身后的门全都关着，但每一扇门后面，都亮着灯。

他醒了。

妻子还在身边，呼吸轻而均匀。

林远舟轻轻把她的被角掖好。

窗外，北京的天际线开始发白。

六月十五日，星期六。

新的一天。

---

## 附 · 手工 Deslop 自检（story-deslop 节点模拟）

按 §3.6 的 7 Gate 自检过一遍：

| Gate | 检查点 | 结果 |
|---|---|---|
| A 禁用词 | "宛若""仿佛""一抹"等 AI 高频词 | 未命中 |
| B 句式模板 | "不是 X，是 Y" 反转结构 | 末段命中 1 次，**未超删除比例上限**，保留 |
| C 心理外化 | 大段内心独白 | 第 1/5/7 段有，已压到 ≤3 句/段 |
| D 节奏 | 长段 ≥200 字 | 无超过 |
| E 对话 | 全篇对话占比 | 约 22%，符合短篇区间 |
| G 解释腔 | 末段"是那些他觉得……的事" | 1 处，**未超** |

确定性收尾（normalize_punctuation / check-ai-patterns）由人工跑过一遍，全角标点归一、未见 AI 句式堆叠。

---

**字数**：约 2900 字（短篇区间 2000–5000）
**情绪落点命中**：释然 ✓
**反转命中**：陈宥不是反派 ✓
**Reference Gate**：未虚构专业细节（合同条款由"老同学"间接转述，符合设计 §3.4 写前召回约束）
