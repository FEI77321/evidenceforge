# EvidenceForge

> 一个安全、可验证的网页调研 Agent。

> 演示入口：[`docs/demo_runbook.md`](docs/demo_runbook.md) 与 [`scripts/run_fixture_demo.ps1`](scripts/run_fixture_demo.ps1)。它们使用版本控制内的 Fixture，演示状态机、Celery Worker、追加式事件、来源快照和 SSE 闭环，不依赖真实网页或模型调用。

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
- 已完成来源读取的应用层与 API 契约测试；Day 9 收尾时完整测试套件为 **49 passed**，Ruff 静态检查通过。
- 已定义不可变 `TaskEvent` 领域模型与 `TaskEventType` 枚举，事件包含任务归属、按任务递增的 `sequence`、事件类型、可选阶段、结构化 Payload 与 UTC 发生时间；
- 已新增 PostgreSQL `task_events` 表及其 Alembic migration，建立 `task_id → research_tasks.id` 外键、`(task_id, sequence)` 唯一约束与事件类型约束；
- 已定义 `TaskEventRepository` Port，并提供测试用 `FakeTaskEventRepository` 和生产用 `PostgreSQLTaskEventRepository`；事件仓储以追加方式保存事件，并按单个任务分配连续序号；
- 已将任务事件写入接入应用层：`TaskService` 记录 `created`、`cancel_requested`，`ResearchTaskProcessor` 记录 `running`、`completed`、`failed`、`canceled`；
- 已将真实 PostgreSQL 事件仓储注入 Celery Worker，并完成真实端到端验证：正常任务产生 `created → running → completed`，取消任务产生 `created → cancel_requested → canceled`；取消任务不会执行 Fixture，也不会保存来源快照；
- 已覆盖任务事件领域规则、Fake 仓储顺序、应用层状态流转、PostgreSQL 持久化与 API 依赖装配；当前完整测试套件为 **55 passed**，Ruff 静态检查通过。
- 已新增 `TaskEventService`：先确认任务存在，再按任务读取生命周期事件；未知任务与“任务存在但暂无事件”在应用层分别表示为 `None` 与 `[]`；
- 已提供 `GET /api/v1/research-tasks/{task_id}/events`：未知任务返回 `404`，已存在但无事件返回 `200 []`，已有事件按 `sequence` 升序返回事件类型、阶段、Payload 与 UTC 时间；
- 已覆盖事件读取的 Fake 仓储、PostgreSQL 仓储、应用服务与 API 契约测试；Day 11 收尾时完整测试套件为 **55 passed**，Ruff 静态检查通过。
- 已新增 `TaskEventStreamService`：建流时回放已持久化的任务事件，之后以受控低频轮询读取事件历史，并通过 `sequence` 只推送尚未发送的新增事件；
- 已提供 `GET /api/v1/research-tasks/{task_id}/events/stream`：未知任务返回普通 JSON `404`；存在任务返回 `text/event-stream`，每条 SSE 消息使用 `id: <sequence>`、`event: task_event`、`data: <JSON>` 与空行结束；
- 已完成事件流回放、后续新增事件推送、sequence 去重、SSE 媒体类型与首帧格式的测试；Day 12 收尾时完整测试套件为 **60 passed**，Ruff 静态检查通过；真实 Uvicorn 联调已验证任务可收到 `created → running → completed`，随机未知任务返回 `404`。
- 已建立 `frontend/` React + TypeScript + Vite 最小工作台：可创建研究任务、展示任务 ID 与当前状态，并先读取 Day 11 历史事件；
- 前端通过浏览器原生 `EventSource` 订阅 Day 12 的 `/events/stream`。每次任务 ID 切换时关闭旧连接、建立新连接；历史回放或浏览器重连产生的重复事件按 `sequence` 去重；收到合法事件 Payload 中的 `status` 后同步更新任务状态标签；
- FastAPI 仅向本机 Vite 开发源 `http://localhost:5173` 与 `http://127.0.0.1:5173` 开放 CORS 的 `GET` / `POST` 与 `Content-Type`；自动化测试验证预检响应。Day 13 收尾时后端完整测试套件为 **61 passed**、Ruff 通过，前端 `npm run build` 通过；真实浏览器联调已验证不点击“刷新事件”时任务状态和时间线会随 SSE 自动更新。
- 前端已接入既有的取消 API：只在 `queued` / `running` 显示取消按钮，成功请求后如实显示 `cancel_requested`，随后由 SSE 自动收敛为 `canceled`；
- 前端会在 SSE 收到 `completed` 时自动读取 Day 9 来源快照，并展示 URI、类型、快照时间、SHA-256 与可展开的纯文本原文；取消任务不会展示来源快照。Day 14 收尾时后端完整测试仍为 **61 passed**、Ruff 通过，前端 ESLint 与 production build 通过，完成与取消两条真实浏览器链路均已验证。

### 尚未实现

- 真实网页调研执行逻辑，以及 Worker 运行中的细粒度取消中断；
- Worker 自动重试策略与可查询的执行日志；
- SSE 的 Last-Event-ID 断线续接、心跳、Redis Pub/Sub、多实例广播、背压与生产级连接治理；
- 真实网页 / PDF 摄入、真实 URL 抓取、来源版本比较与差异展示；
- RAG 检索、LangGraph 工作流、Tool Calling；
- Claim-Evidence 校验、安全门、红队评测；
- 完整 React 调研工作台：报告阅读、证据卡片、错误恢复和生产级可用性；当前已实现任务创建、取消、状态、事件时间线与受控 Fixture 来源快照的最小工作台；
- PostgreSQL 中的证据、结论与报告等后续数据表。

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

在项目根目录的另一个终端启动前端：

```powershell
Set-Location -LiteralPath .\frontend
npm install
npm run dev
```

随后打开：

```text
http://localhost:5173/
```

前端默认请求 `http://127.0.0.1:8000/api/v1`；可通过 `VITE_API_BASE_URL` 覆盖。开发期后端 CORS 仅允许本机 Vite 的 `localhost:5173` 和 `127.0.0.1:5173` 两个来源。

当前健康检查返回：

```json
{
  "status": "ok",
  "service": "evidenceforge"
}
```

> `GET /healthz` 当前只表示 API 进程存活；它不代表数据库、Redis、Worker、模型或外部来源已经就绪。

### 一键演示验证

在 API、Worker、PostgreSQL 和 Redis 都启动后，可在项目根目录执行：

```powershell
.\scripts\run_fixture_demo.ps1
```

脚本会创建一条受控 Fixture 任务，轮询直至任务到达终态，再打印生命周期事件与来源快照的 URI、SHA-256 和时间。预期成功链路是 `queued → running → completed` 与 `created → running → completed`；若依赖未启动或任务未成功完成，脚本会退出失败。这是面试/录屏用的可复现证据入口，完整口述顺序见 [`docs/demo_runbook.md`](docs/demo_runbook.md)。

## 当前 API

| 方法 | 路径 | 当前行为 |
|---|---|---|
| `POST` | `/api/v1/research-tasks` | 创建任务并投递到 Redis，返回 `202` 与初始 `queued` 状态。 |
| `GET` | `/api/v1/research-tasks/{task_id}` | 查询任务问题与当前状态；未知任务返回 `404`。 |
| `POST` | `/api/v1/research-tasks/{task_id}/cancel` | 请求取消任务；重复请求保持幂等。 |
| `GET` | `/api/v1/research-tasks/{task_id}/sources` | 读取该任务已保存的来源快照；未知任务为 `404`，尚无来源为 `200 []`。 |
| `GET` | `/api/v1/research-tasks/{task_id}/events` | 读取任务生命周期事件；未知任务为 `404`，已有任务按 `sequence` 升序返回事件，暂无事件为 `200 []`。 |
| `GET` | `/api/v1/research-tasks/{task_id}/events/stream` | 以 SSE 回放并持续推送任务事件；未知任务为 JSON `404`，存在任务返回 `text/event-stream`。 |

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

读取任务事件时间线：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/research-tasks/$taskId/events"
```

订阅任务事件流：

```powershell
curl.exe -N "http://127.0.0.1:8000/api/v1/research-tasks/$taskId/events/stream"
```

`-N` 会关闭 curl 的输出缓冲，使每一条 SSE 消息到达时立刻显示。当前流会先回放建连前已有的事件，再通过轮询推送后续新增事件；可按 `Ctrl + C` 主动关闭连接。

## 验证

在 `backend/` 目录运行：

```powershell
uv run pytest -q
uv run ruff check src tests migrations
```

截至 Day 11，完整测试套件的已验证结果为：

```text
55 passed
All checks passed!
```

Day 12 的事件流相关测试为 **8 passed**；Day 13 增加 CORS 预检契约测试后，后端完整测试套件为 **61 passed**，Ruff 静态检查通过；Day 14 前端 ESLint 与 `npm run build` 通过。除自动化测试外，还完成了真实 API → Redis → Celery Worker → PostgreSQL → SSE → React 浏览器联调：随机未知任务的 `/events/stream` 返回 JSON `404`，真实任务可接收到按序的 `created → running → completed` 事件；浏览器不点击“刷新事件”时，事件列表和任务状态标签会随 SSE 自动更新，任务完成后会自动展示来源快照。另已通过“停止 Worker → 请求取消 → 重启 Worker”的真实链路确认 `queued → cancel_requested → canceled`，取消任务不产生来源快照。创建完成任务后，可在 PostgreSQL 中按任务 ID 查询：

```sql
SELECT
    sequence,
    event_type,
    payload,
    occurred_at
FROM task_events
WHERE task_id = '<task_id>'
ORDER BY sequence;
```

正常完成任务应得到 `created → running → completed`；在 Worker 启动前请求取消的任务应得到 `created → cancel_requested → canceled`，且来源快照查询返回 `[]`。

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
- **Day 10 ✅**：完成追加式 `task_events` 领域模型、Port / Fake、PostgreSQL 表与 Repository、Alembic migration；创建与取消请求分别记录 `created`、`cancel_requested`，Worker 状态处理分别记录 `running`、`completed`、`failed`、`canceled`。已完成成功和取消两条真实 API → Redis → Celery Worker → PostgreSQL 事件链路验证；暂不提供事件查询 API 与 SSE；提交：`18d503b feat(events): persist task lifecycle events`。
- **Day 11 ✅**：完成 `TaskEventService`、事件读取响应契约、真实 PostgreSQL 事件查询、`GET /api/v1/research-tasks/{task_id}/events` 与 Fake / PostgreSQL / 应用服务 / API 契约测试；事件按 `sequence` 升序返回，未知任务为 `404`，已有但无事件的任务为 `200 []`；提交：`aa51709 feat(api): expose task lifecycle events`。
- **Day 12 ✅**：完成 `TaskEventStreamService`、`GET /api/v1/research-tasks/{task_id}/events/stream`、`StreamingResponse` 与标准 SSE 帧；实现历史事件回放、受控轮询观察新增事件和 `sequence` 去重。已通过自动化测试、真实任务事件流和未知任务 `404` 联调；当前不实现断线续接、心跳、多实例广播或生产级连接治理；提交：`0bad632 feat(stream): add task event SSE replay`。
- **Day 13 ✅**：建立 React + TypeScript + Vite 最小工作台，定义任务、事件与 API Client 类型；页面可创建任务、读取 Day 11 历史事件，并以浏览器 `EventSource` 消费 Day 12 SSE。前端按 `sequence` 合并并去重事件，同时由合法 `payload.status` 同步任务状态；后端只对本机 Vite 开放最小 CORS。自动化验证为后端 `61 passed`、Ruff 通过、前端 build 通过，真实浏览器联调确认不点击刷新也会自动出现后续事件与状态变化；提交：`381e2ed feat(frontend): add task event dashboard`。
- **Day 14 ✅**：在现有 React 工作台接入取消任务和来源快照展示。取消按钮只在允许取消的状态显示，页面忠实表达 `cancel_requested` 并经 SSE 接收 `canceled`；任务完成后自动读取并以纯文本展示 Day 9 的来源快照。已真实验证完成任务自动显示来源，以及停止 / 重启 Worker 的取消收敛路径；提交待收尾。
- **下一步**：完成 Day 14 Git 提交后，暂停新增产品能力，复盘 Day 11—14 的 M1 可演示闭环，并整理演示脚本与面试表达。

详细的项目架构、阶段路线、决策、真实状态和跨对话续接信息维护在个人知识库中：

```text
D:\MyKnowledgeBase\文件资料\项目追踪\EvidenceForge.md
```
