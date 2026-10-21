# EvidenceForge

> 可追溯的异步调研任务工作台：记录任务过程、事件和来源快照，再逐步扩展真实调研能力。

[演示手册](docs/demo_runbook.md) · [Fixture 演示脚本](scripts/run_fixture_demo.ps1)

## 项目状态

EvidenceForge 的 M1 已完成并冻结。当前版本演示异步任务工作流，不会访问真实网页，也不会调用大模型。Worker 使用仓库内受控的 Markdown Fixture，因此演示结果可重复验证。

### 当前已实现

- FastAPI 提供任务创建、查询和取消接口。
- PostgreSQL 持久化任务、生命周期事件和来源快照；Alembic 管理迁移。
- Redis 作为 Celery Broker；API 投递任务 ID，由独立 Worker 执行。
- Fixture 执行器读取本地 Markdown，并保存来源 URI、原文、SHA-256 摘要和 UTC 快照时间。
- 事件接口按序读取历史记录，并通过 SSE 回放和推送新事件。
- React + TypeScript 工作台支持创建、查看、取消任务，展示事件时间线与来源快照。

### 当前不包含

真实网页或 PDF 抓取、外部搜索、大模型推理、RAG、Agent 工作流、结论验证、报告生成、自动重试、Worker 强制中断，以及生产级 SSE 断线续接和多实例广播。

## 架构

~~~mermaid
flowchart LR
    UI[React 工作台] -->|HTTP / SSE| API[FastAPI]
    API -->|任务 ID| Redis[(Redis / Celery)]
    Redis --> Worker[Celery Worker]
    API --> DB[(PostgreSQL)]
    Worker -->|状态、事件、快照| DB
    Worker --> Fixture[Markdown Fixture]
    API -->|轮询事件并发送 SSE| UI
~~~

事件按任务的 sequence 递增保存。SSE 先回放已有事件，再通过轮询发送新事件；前端按 sequence 去重。此实现用于 M1 演示，不支持多实例事件广播或断线游标续接。

## 技术栈

Python 3.13、FastAPI、SQLAlchemy、asyncpg、Alembic、PostgreSQL 17、Celery、Redis 7、React、TypeScript、Vite、Docker Compose、pytest、Ruff、ESLint。

## 本地运行

### 环境要求

Python 3.13+、uv、Node.js/npm、Docker Compose。

### 启动依赖

在仓库根目录复制环境文件，并按需修改本地数据库密码：

~~~powershell
Copy-Item .env.example .env
docker compose up -d
~~~

.env 仅用于本地开发，请勿提交密码或其他密钥。

### 安装后端并迁移数据库

~~~powershell
Set-Location backend
uv sync
uv run alembic upgrade head
~~~

在 backend 目录的两个终端分别启动 API 和 Worker：

~~~powershell
uv run uvicorn evidenceforge.main:app --reload --host 127.0.0.1 --port 8000
~~~

~~~powershell
uv run celery -A evidenceforge.infrastructure.worker_tasks:celery_app worker --loglevel=INFO -Q research --pool=solo
~~~

API 文档：<http://127.0.0.1:8000/docs>。GET /healthz 只表示 API 进程存活，不代表数据库、Redis 或 Worker 已就绪。

### 启动前端

在仓库根目录的新终端运行：

~~~powershell
Set-Location frontend
npm install
npm run dev
~~~

打开 <http://localhost:5173>。前端默认请求 http://127.0.0.1:8000/api/v1，可通过 VITE_API_BASE_URL 覆盖。开发期 CORS 仅允许本机 Vite 的 localhost:5173 和 127.0.0.1:5173。

## Fixture 演示

确保 Docker 服务、API 和 Worker 正在运行，然后在仓库根目录执行：

~~~powershell
.\scripts\run_fixture_demo.ps1
~~~

成功时脚本会创建任务、等待 Worker 完成，并输出状态、生命周期事件和来源快照摘要。预期状态为 queued → running → completed，事件为 created → running → completed。完整演示步骤见[演示手册](docs/demo_runbook.md)。

## API 概览

完整请求与响应 Schema 请查看 <http://127.0.0.1:8000/docs>。

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| GET | /healthz | API 进程健康检查 |
| POST | /api/v1/research-tasks | 创建任务，返回 202 和 queued 状态 |
| GET | /api/v1/research-tasks/{task_id} | 查询任务；未知任务返回 404 |
| POST | /api/v1/research-tasks/{task_id}/cancel | 请求取消；重复请求具备幂等语义 |
| GET | /api/v1/research-tasks/{task_id}/sources | 读取来源快照；暂无来源时返回空数组 |
| GET | /api/v1/research-tasks/{task_id}/events | 按 sequence 升序读取事件 |
| GET | /api/v1/research-tasks/{task_id}/events/stream | 通过 SSE 回放并推送事件 |

## 验证

在 backend 目录运行：

~~~powershell
uv run pytest -q
uv run ruff check src tests migrations
~~~

在 frontend 目录运行：

~~~powershell
npm run lint
npm run build
~~~

Fixture/Fake 测试、数据库集成测试和真实浏览器联调依赖不同，应分别说明，不要混称为离线单元测试。
