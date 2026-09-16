param(
    [string]$ApiBase = "http://127.0.0.1:8000/api/v1",
    [int]$TimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"
$question = "演示：受控 Fixture 来源如何被事件审计、来源快照与 SSE 工作台共同追溯？"

Write-Host "[1/4] 创建确定性 Fixture 调研任务..." -ForegroundColor Cyan
$created = Invoke-RestMethod -Method Post -Uri "$ApiBase/research-tasks" `
    -ContentType "application/json" `
    -Body (@{ question = $question } | ConvertTo-Json)

$taskId = $created.task_id
Write-Host "Task ID: $taskId" -ForegroundColor Green

Write-Host "[2/4] 等待 Worker 将任务从 queued 推进到终态..." -ForegroundColor Cyan
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
do {
    Start-Sleep -Milliseconds 800
    $task = Invoke-RestMethod -Uri "$ApiBase/research-tasks/$taskId"
    Write-Host "  status = $($task.status)"
} while ($task.status -in @("queued", "running", "cancel_requested") -and (Get-Date) -lt $deadline)

if ($task.status -ne "completed") {
    throw "演示任务未在 $TimeoutSeconds 秒内完成，最终状态为 $($task.status)。请确认 API、Redis、Celery Worker 与 PostgreSQL 均已启动。"
}

Write-Host "[3/4] 读取追加式生命周期事件..." -ForegroundColor Cyan
$events = Invoke-RestMethod -Uri "$ApiBase/research-tasks/$taskId/events"
$events | Select-Object sequence, event_type, stage, occurred_at | Format-Table -AutoSize

Write-Host "[4/4] 读取可追溯来源快照..." -ForegroundColor Cyan
$sources = Invoke-RestMethod -Uri "$ApiBase/research-tasks/$taskId/sources"
$sources | Select-Object source_uri, source_kind, content_hash, captured_at | Format-List

Write-Host "Demo complete: queued → running → completed，并已持久化事件与 Fixture 来源快照。" -ForegroundColor Green
Write-Host "浏览器工作台可打开 http://localhost:5173，并输入同类问题观察 SSE 实时链路。" -ForegroundColor DarkGray
