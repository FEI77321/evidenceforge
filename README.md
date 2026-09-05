# EvidenceForge

> 一个安全、可验证的网页调研 Agent。

EvidenceForge 面向公开网页与 PDF 调研场景。系统的目标不是只生成一段看似合理的答案，而是让每条结论都能关联到可追溯的来源、证据片段和验证状态。

## 当前实现状态

> 项目正在开发中。以下内容严格区分已完成与计划能力。

### 已完成

- 已初始化独立 Git 仓库；
- 已建立 Python 3.13 + `uv` 后端工程；
- 已接入 FastAPI 与 Uvicorn；
- 已实现并在浏览器验证 `GET /healthz`；
- 已配置 `.gitignore`，不会提交本地 IDE 配置、虚拟环境或真实密钥。
- 已完成纯 Python 的 `ResearchTask` 领域模型与任务状态机：`queued`、`running`、`cancel_requested`、`completed`、`failed`、`canceled`；
- 已固化成功、失败、取消、终态不可回退与取消幂等等生命周期规则；
- 已定义 `TaskRepository` / `TaskQueue` 抽象 Port，并提供仅用于测试的内存 Fake 实现；
- 已建立 14 条离线单元测试，并通过 pytest 与 Ruff 格式 / 静态检查验证。
- 已完成 `TaskService`、Pydantic 请求 / 响应模型，以及任务创建、查询、取消的 FastAPI API；
- 已建立 API 契约测试；测试通过依赖覆盖使用 Fake，保持快速且不依赖数据库；
- 已通过 Docker Compose 启动 PostgreSQL，并将 Docker 运行数据配置在本机 D 盘；
- 已接入 SQLAlchemy、asyncpg 与 Alembic，建立并执行 `research_tasks` 初始迁移；
- 已实现 `PostgreSQLTaskRepository`，并验证任务创建、读取、状态更新可持久化；
- 已验证真实 API 创建任务后，可通过后续 API 查询和 PostgreSQL 直接 SQL 查询读回同一条记录；
- 已建立 PostgreSQL 连通性与 Repository 集成测试；当前完整测试套件通过，Ruff 检查通过。
- 已通过 Docker Compose 启动 Redis 7，并将其作为 Celery 的任务 Broker 与结果 Backend；
- 已实现 `CeleryTaskQueue` 与 `worker_tasks.py`：API 仅投递任务 ID，独立 Worker 从 Redis 消费任务并更新 PostgreSQL 状态；
- 已完成真实端到端验证：创建任务后状态从 `queued` 自动推进为 `running`、最终为 `completed`。
- 已将 Worker 的状态流转规则提炼为可独立测试的 `ResearchTaskProcessor`，避免业务规则与 Celery、Redis、SQLAlchemy 基础设施耦合；
- 已定义 `ResearchExecutor` 抽象，并提供生产环境的 `StubResearchExecutor` 与测试环境的 `FakeResearchExecutor`；
- 已覆盖任务完成、取消、重复消息、未知任务和执行失败五类状态处理场景；执行器异常会使任务从 `running` 明确转为 `failed`。
- 已实现 `FixtureResearchExecutor`：Worker 可以读取受控的本地 Markdown Fixture，而不再只是空 Stub 成功；
- 已通过统一 `Settings` 配置 Fixture 来源路径，并验证默认路径真实指向已纳入版本控制的资料文件；
- 已建立 Fixture 读取成功与文件缺失两类测试，并完成真实链路验证：Worker 成功读取 `fastapi_background_tasks.md` 后将任务推进为 `completed`。
- 已定义不可变 `SourceSnapshot` 领域模型，包含任务归属、来源 URI、来源类型、原文、UTF-8 SHA-256 内容 Hash 与 UTC 快照时间；
- 已新增 PostgreSQL `source_snapshots` 表及其 Alembic migration，并建立 `task_id → research_tasks.id` 外键和按任务查询索引；
- 已实现 `PostgreSQLSourceSnapshotRepository`，支持追加保存来源快照，并按任务、抓取时间升序查询；
- 已将真实快照 Repository 注入 Celery Worker：Fixture 执行器读取本地 Markdown 后会创建并持久化快照；
- 已完成真实端到端验证：API 创建任务后，Celery Worker 将任务推进为 `completed`，且 PostgreSQL 中可按 `task_id` 查询到 `fixture://fastapi_background_tasks.md` 的原文长度、Hash 与 UTC 快照时间。
- 已新增 `SourceSnapshotService`，以“先确认任务存在、再查询来源快照”的方式组织来源读取用例；应用层不直接依赖 FastAPI 或 PostgreSQL。
- 已提供 `GET /api/v1/research-tasks/{task_id}/sources`：未知任务返回 `404`，已存在但尚无来源的任务返回 `200 []`，已有来源时返回快照 ID、URI、类型、原文、SHA-256 Hash 与 UTC 快照时间。
- 已完成来源读取的应用层与 API 契约测试；当前完整测试套件为 **49 passed**，Ruff 静态检查通过。

### 尚未实现

- 真实网页调研执行逻辑，以及 Worker 运行中的细粒度取消中断；
- Worker 自动重试策略、任务事件记录与可查询的执行日志；
- SSE 任务进度流；
- 真实网页 / PDF 摄入、真实 URL 抓取、来源版本比较与差异展示；
- RAG 检索、LangGraph 工作流、Tool Calling；
- Claim-Evidence 校验、安全门、红队评测；
- React 前端；
- PostgreSQL 中的证据、结论、报告与任务事件等后续数据表。

## 项目目标

用户提交调研问题后，系统将逐步完成：

```text
Plan
  → Search / Select Sources
  → Fetch
  → Security Gate
  → Evidence Index
  → Draft Claims
  → Verify Claims
  → Publish Report
```

最终报告中的每条结论都应标记为以下状态之一：

- `supported`：现有证据支持该结论；
- `insufficient`：证据不足，不能把结论说成事实；
- `conflict`：来源之间存在冲突，系统不强行裁决。

## 当前技术基线

- Python 3.13
- FastAPI
- Uvicorn
- uv
- Git
- pytest
- Ruff
- Docker Compose
- PostgreSQL 17
- SQLAlchemy
- asyncpg
- Alembic
- Pydantic Settings
- Redis 7
- Celery

后续计划接入：

- React + TypeScript + Vite
- RAG、LangGraph、Tool Calling、MCP、安全与评测模块

## 本地运行

先在项目根目录准备 PostgreSQL 与 Redis（首次运行前需基于 `.env.example` 创建本地、且不提交 Git 的 `.env`）：

```powershell
docker compose up -d
```

进入后端目录：

```powershell
Set-Location -LiteralPath .\backend
```

安装并同步依赖：

```powershell
uv sync
```

执行数据库迁移：

```powershell
uv run alembic upgrade head
```

在一个终端启动 API：

```powershell
uv run uvicorn evidenceforge.main:app --reload --host 127.0.0.1 --port 8000
```

在另一个终端启动 Worker：

```powershell
uv run celery -A evidenceforge.infrastructure.worker_tasks:celery_app worker --loglevel=INFO -Q research --pool=solo
```

浏览器验证：

```text
http://127.0.0.1:8000/healthz
http://127.0.0.1:8000/docs
```

当前健康检查返回：

```json
{
  "status": "ok",
  "service": "evidenceforge"
}
```

> `GET /healthz` 当前只表示 API 进程存活；它不代表数据库、Redis、Worker、模型或外部来源已经就绪。

## 当前 API

| 方法 | 路径 | 当前行为 |
|---|---|---|
| `POST` | `/api/v1/research-tasks` | 创建任务并投递到 Redis，返回 `202` 与初始 `queued` 状态。 |
| `GET` | `/api/v1/research-tasks/{task_id}` | 查询任务问题与当前状态；未知任务返回 `404`。 |
| `POST` | `/api/v1/research-tasks/{task_id}/cancel` | 请求取消任务；重复请求保持幂等。 |
| `GET` | `/api/v1/research-tasks/{task_id}/sources` | 读取该任务已保存的来源快照；未知任务为 `404`，尚无来源为 `200 []`。 |

创建任务后，Worker 会读取当前受控 Fixture，并将一个来源快照写入 PostgreSQL。任务变为 `completed` 后，可以读取来源：

```powershell
$taskId = '<创建接口返回的 task_id>'
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/research-tasks/$taskId/sources"
```

当前 Fixture 场景下，返回数组中的每一项具有如下形态：

```json
{
  "snapshot_id": "UUID",
  "source_uri": "fixture://fastapi_background_tasks.md",
  "source_kind": "fixture",
  "raw_content": "...",
  "content_hash": "SHA-256 hex digest",
  "captured_at": "UTC ISO-8601 timestamp"
}
```

## 验证

在 `backend/` 目录运行：

```powershell
uv run pytest -q
uv run ruff check src tests migrations
```

截至 Day 9，预期结果为：

```text
49 passed
All checks passed!
```

## 开发原则

- 外部网页、PDF 与工具输出均视为不可信数据，而不是系统指令；
- 先保存和检索可追溯证据，再生成报告；
- 引用存在不等于结论被证据支持；
- 默认测试使用 Stub / Fixture，不把真实模型、真实网页和 Docker 联调混称为普通单元测试；
- 复杂能力必须有评测收益和失败案例，不能只为堆叠技术名词而接入。

## 项目进度

- **Day 1 ✅**：完成独立仓库、Python / uv 后端工程、FastAPI / Uvicorn 与 `GET /healthz`；提交：`19592ce feat(api): bootstrap FastAPI health endpoint`；
- **Day 2 ✅**：完成任务状态机、Repository / Queue Port、内存 Fake、14 条离线单元测试与代码质量检查；提交：`ff6c7be feat(tasks): add task lifecycle foundation`；
- **Day 3 ✅**：完成 `TaskService`、Pydantic 契约、任务创建 / 查询 / 取消 API、API 契约测试；提交：`9711202 feat(api): add task management API`；
- **Day 4 ✅**：完成 Docker PostgreSQL、SQLAlchemy / asyncpg、Alembic 初始迁移、`PostgreSQLTaskRepository`、真实数据库集成测试，以及 API 默认使用真实 Repository；提交：`c8bcce3 feat(storage): persist research tasks in PostgreSQL`；
- **Day 5 ✅**：完成 Redis 7、Celery 配置、`CeleryTaskQueue`、Worker Stub，并验证真实任务可从 `queued` 自动推进至 `completed`；提交：`1a4fdde feat(worker): process research tasks with Celery`；
- **Day 6 ✅**：完成可测试的 `ResearchTaskProcessor`、`ResearchExecutor` 抽象、Stub / Fake 执行器，以及 Worker 执行失败时的 `running → failed` 状态记录与单元测试；提交：`ac98d23 feat(worker): handle task execution failures`；
- **Day 7 ✅**：完成受控 Markdown Fixture、`FixtureResearchExecutor`、Fixture 路径配置及其测试；已验证真实 Celery Worker 成功读取本地资料并将任务推进至 `completed`；提交：`4052b22 feat(research): load controlled fixture source`；
- **Day 8 ✅**：完成 `SourceSnapshot` 领域模型、`SourceSnapshotRepository` Port / Fake、`source_snapshots` Alembic 迁移、PostgreSQL Repository、Fixture 执行器写入与 Worker 真实依赖装配；已验证真实任务从 `queued` 进入 `completed` 后，PostgreSQL 中存在关联的 Fixture 来源快照、SHA-256 Hash 和 UTC `captured_at`；提交：`0265dea feat(research): persist fixture source snapshots`；
- **Day 9 ✅**：完成 `SourceSnapshotService`、来源快照响应契约和 `GET /api/v1/research-tasks/{task_id}/sources`；已覆盖已有来源、空来源和未知任务三种语义，并真实验证 API → Redis → Worker → PostgreSQL → HTTP 读取闭环；提交：`17a22a9 feat(api): expose task source snapshots`；
- **下一步 Day 10**：建立追加式 `task_events` 持久化与事件发布边界，记录任务状态变化；暂不接 SSE。

详细的项目架构、阶段路线、决策、真实状态和跨对话续接信息维护在个人知识库中：

```text
D:\MyKnowledgeBase\文件资料\项目追踪\EvidenceForge.md
```
