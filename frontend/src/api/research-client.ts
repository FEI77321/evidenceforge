import type {
  ResearchTask,
  SourceSnapshot,
  TaskEvent,
} from "../types/research";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  public readonly status: number;

  constructor(
    status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => null) as { detail?: string } | null;

    throw new ApiError(
      response.status,
      body?.detail ?? response.statusText,
    );
  }

  return response.json() as Promise<T>;
}

export function createResearchTask(
  question: string,
): Promise<ResearchTask> {
  return request<ResearchTask>("/research-tasks", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export function cancelResearchTask(
  taskId: string,
): Promise<ResearchTask> {
  return request<ResearchTask>(
    `/research-tasks/${taskId}/cancel`,
    {
      method: "POST",
    },
  );
}

export function getResearchTask(
  taskId: string,
): Promise<ResearchTask> {
  return request<ResearchTask>(
    `/research-tasks/${taskId}`,
  );
}

export function getTaskEvents(
  taskId: string,
): Promise<TaskEvent[]> {
  return request<TaskEvent[]>(
    `/research-tasks/${taskId}/events`,
  );
}

export function getTaskSources(
  taskId: string,
): Promise<SourceSnapshot[]> {
  return request<SourceSnapshot[]>(
    `/research-tasks/${taskId}/sources`,
  );
}
export interface TaskEventStreamHandlers {
  onOpen: () => void;
  onEvent: (event: TaskEvent) => void;
  onError: () => void;
}

export function subscribeToTaskEvents(
  taskId: string,
  handlers: TaskEventStreamHandlers,
): () => void {
  const eventSource = new EventSource(
    `${API_BASE_URL}/research-tasks/${taskId}/events/stream`,
  );

  eventSource.onopen = handlers.onOpen;

  eventSource.addEventListener("task_event", (event) => {
    const message = event as MessageEvent<string>;

    handlers.onEvent(
      JSON.parse(message.data) as TaskEvent,
    );
  });

  eventSource.onerror = handlers.onError;

  return () => {
    eventSource.close();
  };
}
