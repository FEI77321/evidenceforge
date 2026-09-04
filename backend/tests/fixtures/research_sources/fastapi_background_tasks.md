# FastAPI BackgroundTasks and independent task queues

fixture_kind: synthetic_local_development_input
source_policy: official_tech_docs
topic: FastAPI BackgroundTasks and Celery

## Content

FastAPI BackgroundTasks are suitable for small jobs that can run after an HTTP response is returned.

For heavy background computation, long-running jobs, or work that should run in a separate process,
an independent task queue can be more suitable. Celery is one example of a distributed task queue.

A durable research system should persist task state outside the web process so that a task can be
queried after the API process restarts.

## Expected facts

- BackgroundTasks are appropriate for lightweight post-response work.
- A separate task queue is more appropriate for long-running or heavy background work.
- Celery workers can run outside the FastAPI web process.
- Task state should be persisted instead of existing only in API process memory.