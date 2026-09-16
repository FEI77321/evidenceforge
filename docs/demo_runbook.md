# EvidenceForge 三分钟演示脚本

本演示只使用已经纳入版本控制的 Fixture 来源，不调用真实网页、模型或外部搜索。它要证明的是任务状态机、异步 Worker、事件审计、来源快照与 SSE 工作台已经形成可追溯闭环。

## 演示前准备

在项目根目录完成一次本地服务准备：

```powershell
docker compose up -d
Set-Location backend
uv sync
uv run alembic upgrade head
```

分别启动 API、Worker 与前端：

```powershell
# 终端 1：API
Set-Location backend
uv run uvicorn evidenceforge.main:app --host 127.0.0.1 --port 8000

# 终端 2：Celery Worker
Set-Location backend
uv run celery -A evidenceforge.infrastructure.worker_tasks:celery_app worker --loglevel=INFO -Q research --pool=solo

# 终端 3：React 工作台
Set-Location frontend
npm install
npm run dev
```

## 90 秒命令行证据

运行下面命令；它会创建确定性 Fixture 任务、等待 Worker 处理、读取事件和来源快照。任何一个依赖未就绪都会明确失败，而不会伪装成演示成功。

```powershell
.\scripts\run_fixture_demo.ps1
```

预期可观察到：

```text
queued → running → completed
created → running → completed
fixture://fastapi_background_tasks.md
SHA-256 content hash
```

## 90 秒浏览器演示顺序

1. 打开 `http://localhost:5173`，输入一个调研问题并创建任务。
2. 指出页面先显示 `queued`，随后不点击“刷新事件”也会通过 SSE 变成 `running` 和 `completed`。
3. 展示按 `sequence` 追加的事件；说明页面在重连或历史回放时会去重。
4. 展开来源快照，展示 URI、快照时间、SHA-256 和受控纯文本原文。
5. 再创建一个任务，在 `queued` 或 `running` 状态点击“请求取消”；说明前端如实展示 `cancel_requested`，而 Worker 在安全检查点将其收敛为 `canceled`，且不会创建来源快照。

## 面试表达边界

当前系统是“可验证异步调研工作台 M1”，不是一个声称能自动完成真实网络调研的产品。真实网页抓取、模型推理、长任务恢复、多实例 SSE 广播、断线续接和报告生成均尚未实现。这个边界是刻意保留的：先验证任务生命周期与证据可追溯性，再扩展不确定性更高的 Agent 能力。
