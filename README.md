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

### 尚未实现

- PostgreSQL、Redis、Celery Worker；
- 任务创建、查询、取消与 SSE 进度；
- 网页 / PDF 摄入、来源快照与版本管理；
- RAG 检索、LangGraph 工作流、Tool Calling；
- Claim-Evidence 校验、安全门、红队评测；
- React 前端与 Docker Compose。

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

后续计划接入：

- PostgreSQL + Alembic
- Redis + Celery
- React + TypeScript + Vite
- Docker Compose
- RAG、LangGraph、Tool Calling、MCP、安全与评测模块

## 本地运行

进入后端目录：

```powershell
Set-Location -LiteralPath .\backend
```

安装并同步依赖：

```powershell
uv sync
```

启动开发服务器：

```powershell
uv run uvicorn evidenceforge.main:app --reload --host 127.0.0.1 --port 8000
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

## 开发原则

- 外部网页、PDF 与工具输出均视为不可信数据，而不是系统指令；
- 先保存和检索可追溯证据，再生成报告；
- 引用存在不等于结论被证据支持；
- 默认测试使用 Stub / Fixture，不把真实模型、真实网页和 Docker 联调混称为普通单元测试；
- 复杂能力必须有评测收益和失败案例，不能只为堆叠技术名词而接入。

## 项目进度

详细的项目架构、阶段路线、决策、真实状态和跨对话续接信息维护在个人知识库中：

```text
D:\MyKnowledgeBase\文件资料\项目追踪\EvidenceForge.md
```