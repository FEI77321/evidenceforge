export type TaskStatus =
  | "queued"
  | "running"
  | "cancel_requested"
  | "completed"
  | "failed"
  | "canceled";

export type TaskEventType =
  | "created"
  | "running"
  | "completed"
  | "failed"
  | "cancel_requested"
  | "canceled";

export interface ResearchTask {
  task_id: string;
  question: string;
  status: TaskStatus;
}

export interface SourceSnapshot {
  snapshot_id: string;
  source_uri: string;
  source_kind: string;
  raw_content: string;
  content_hash: string;
  captured_at: string;
}

export interface TaskEvent {
  sequence: number;
  event_type: TaskEventType;
  stage: string | null;
  payload: Record<string, unknown>;
  occurred_at: string;
}