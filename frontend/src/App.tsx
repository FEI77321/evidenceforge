import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  ApiError,
  createResearchTask,
  getTaskEvents,
  subscribeToTaskEvents,
} from "./api/research-client";
import type {
  ResearchTask,
  TaskEvent,
  TaskStatus,
} from "./types/research";
import "./App.css";

type EventStreamState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting";

function isTaskStatus(value: unknown): value is TaskStatus {
  return (
    typeof value === "string"
    && [
      "queued",
      "running",
      "cancel_requested",
      "completed",
      "failed",
      "canceled",
    ].includes(value)
  );
}

function formatOccurredAt(occurredAt: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(new Date(occurredAt));
}

function getStreamStateLabel(
  streamState: EventStreamState,
): string {
  const labels: Record<EventStreamState, string> = {
    disconnected: "未连接事件流",
    connecting: "正在连接事件流",
    connected: "实时事件流已连接",
    reconnecting: "事件流重连中",
  };

  return labels[streamState];
}

function mergeTaskEvent(
  currentEvents: TaskEvent[],
  incomingEvent: TaskEvent,
): TaskEvent[] {
  const eventAlreadyExists = currentEvents.some(
    (event) => event.sequence === incomingEvent.sequence,
  );

  if (eventAlreadyExists) {
    return currentEvents;
  }

  return [...currentEvents, incomingEvent].sort(
    (left, right) => left.sequence - right.sequence,
  );
}

function App() {
  const [question, setQuestion] = useState("");
  const [task, setTask] = useState<ResearchTask | null>(null);
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [streamState, setStreamState] = useState<EventStreamState>(
    "disconnected",
  );
  const taskId = task?.task_id;

  useEffect(() => {
    if (!taskId) {
      return;
    }

    const unsubscribe = subscribeToTaskEvents(
      taskId,
      {
        onOpen: () => {
          setStreamState("connected");
        },
        onEvent: (incomingEvent) => {
          setEvents((currentEvents) =>
            mergeTaskEvent(currentEvents, incomingEvent),
          );

          const nextStatus = incomingEvent.payload["status"];

          if (isTaskStatus(nextStatus)) {
            setTask((currentTask) => {
              if (
                !currentTask
                || currentTask.task_id !== taskId
              ) {
                return currentTask;
              }

              return {
                ...currentTask,
                status: nextStatus,
              };
            });
          }
        },
        onError: () => {
          setStreamState("reconnecting");
        },
      },
    );

    return () => {
      unsubscribe();
    };
  }, [taskId]);

  async function loadTaskEvents(taskId: string): Promise<void> {
    setIsLoadingEvents(true);

    try {
      const taskEvents = await getTaskEvents(taskId);
      setEvents(taskEvents);
    } finally {
      setIsLoadingEvents(false);
    }
  }

  async function handleCreateTask(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    const normalizedQuestion = question.trim();
    if (!normalizedQuestion) {
      setErrorMessage("请输入一个需要调研的问题。");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setStreamState("disconnected");

    try {
      const createdTask = await createResearchTask(normalizedQuestion);

      setStreamState("connecting");
      setTask(createdTask);
      setQuestion("");
      await loadTaskEvents(createdTask.task_id);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(
          `请求失败（${error.status}）：${error.message}`,
        );
      } else {
        setErrorMessage("请求失败，请确认后端服务正在运行。");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRefreshEvents(): Promise<void> {
    if (!task) {
      return;
    }

    setErrorMessage(null);

    try {
      await loadTaskEvents(task.task_id);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(
          `读取事件失败（${error.status}）：${error.message}`,
        );
      } else {
        setErrorMessage("读取事件失败，请确认后端服务正在运行。");
      }
    }
  }

  return (
    <main className="app-shell">
      <section className="panel">
        <p className="eyebrow">EvidenceForge · Day 13</p>
        <h1>证据驱动的研究任务</h1>
        <p className="intro">
          创建任务后，页面会读取历史事件，并实时接收后端推送。
        </p>

        <form className="task-form" onSubmit={handleCreateTask}>
          <label htmlFor="research-question">
            你想研究什么问题？
          </label>
          <textarea
            id="research-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="例如：比较 RAG 与 GraphRAG 在可追溯证据上的差异"
            rows={4}
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "正在创建……" : "创建研究任务"}
          </button>
        </form>

        {errorMessage ? (
          <p className="error-message" role="alert">
            {errorMessage}
          </p>
        ) : null}
      </section>

      {task ? (
        <section className="panel task-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">当前任务</p>
              <h2>{task.question}</h2>
            </div>
            <span className={`status status--${task.status}`}>
              {task.status}
            </span>
          </div>

          <p className="task-id">
            Task ID：<code>{task.task_id}</code>
          </p>

          <div className="section-heading event-heading">
            <div>
              <h2>生命周期事件</h2>
              <p
                className={`stream-state stream-state--${streamState}`}
              >
                {getStreamStateLabel(streamState)}
              </p>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={handleRefreshEvents}
              disabled={isLoadingEvents}
            >
              {isLoadingEvents ? "读取中……" : "刷新事件"}
            </button>
          </div>

          {events.length === 0 ? (
            <p className="empty-state">该任务暂时还没有事件。</p>
          ) : (
            <ol className="event-list">
              {events.map((taskEvent) => (
                <li key={taskEvent.sequence} className="event-item">
                  <div className="event-meta">
                    <strong>#{taskEvent.sequence}</strong>
                    <span>{taskEvent.event_type}</span>
                    <time dateTime={taskEvent.occurred_at}>
                      {formatOccurredAt(taskEvent.occurred_at)}
                    </time>
                  </div>
                  <pre>
                    {JSON.stringify(taskEvent.payload, null, 2)}
                  </pre>
                </li>
              ))}
            </ol>
          )}
        </section>
      ) : null}
    </main>
  );
}

export default App;
