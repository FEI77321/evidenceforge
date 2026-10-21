# EvidenceForge M1 演示手册

本演示使用仓库中的受控 Markdown Fixture，不访问真实网页，也不调用模型或外部搜索。它展示 M1 已实现的异步任务、Worker、追加式事件、来源快照和 SSE 工作台闭环。

## 演示前准备

在仓库根目录创建本地环境文件并启动 PostgreSQL 与 Redis：

~~~powershell
Copy-Item .env.example .env
docker compose up -d
Set-Location backend
uv sync
uv run alembic upgrade head
~~~

按需修改 .env 中的本地数据库密码。分别在三个终端启动服务：

~~~powershell
# 终端 1：API（backend 目录）
Set-Location backend
uv run uvicorn evidenceforge.main:app --host 127.0.0.1 --port 8000
~~~

~~~powershell
# 终端 2：Celery Worker（backend 目录）
Set-Location backend
uv run celery -A evidenceforge.infrastructure.worker_tasks:celery_app worker --loglevel=INFO -Q research --pool=solo
~~~

~~~powershell
# 终端 3：React 工作台（仓库根目录）
Set-Location frontend
npm install
npm run dev
~~~

打开 <http://localhost:5173>。

## 命令行演示

回到仓库根目录执行：

~~~powershell
.\scripts\run_fixture_demo.ps1
~~~

脚本会创建 Fixture 任务、等待 Worker 执行、读取事件和来源快照。任何依赖未就绪或任务未成功完成都会明确报错。预期可观察到：

- 任务状态：queued → running → completed
- 生命周期事件：created → running → completed
- Fixture 来源 URI、SHA-256 内容摘要和快照时间

## 浏览器演示

1. 创建一条研究任务，指出任务先进入 queued，然后由 SSE 自动更新状态。
2. 展示按 sequence 递增的事件时间线。前端会对历史回放或重连后收到的重复事件去重。
3. 任务完成后展开来源快照，查看来源 URI、快照时间、SHA-256 和 Fixture 原文。

### 可重复的取消演示

为避免 Fixture 任务完成太快导致点击取消的时机不稳定，可用以下步骤演示取消：

1. 在 Worker 终端按 Ctrl+C 暂停 Worker；不要停止 API、数据库、Redis 或前端。
2. 在工作台创建一条新任务。没有 Worker 消费队列，任务会保持 queued。
3. 点击“请求取消”，确认页面显示 cancel_requested。
4. 重新启动 Worker，使用上方的 Celery 命令。Worker 读取排队任务后会将其收敛到 canceled。
5. 在工作台确认 SSE 收到 canceled，并确认没有来源快照。

## 项目边界

当前是可验证异步调研工作台 M1，不会自动完成真实网络调研。网页/PDF 抓取、模型推理、RAG、结论校验和报告生成尚未实现。SSE 当前通过轮询持久化事件工作，不支持 Last-Event-ID 断线续接、心跳或多实例广播。
