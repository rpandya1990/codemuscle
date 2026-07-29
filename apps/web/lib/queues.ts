import type { Problem } from "./problems";

export interface QueueItem {
  id: string;
  position: number;
  estimated_duration_minutes: number;
  recommendation_score: number;
  recommendation_reasons: string[];
  status: "PENDING" | "POSTPONED" | "COMPLETED";
  problem: Problem;
}

export interface DailyQueue {
  id: string;
  available_minutes: number;
  topic_focus_ids: string[];
  requested_problem_count: number | null;
  status: string;
  created_at: string;
  total_estimated_minutes: number;
  items: QueueItem[];
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function json(response: Response): Promise<DailyQueue> {
  if (!response.ok)
    throw new Error(`Queue request failed (HTTP ${response.status}).`);
  return response.json() as Promise<DailyQueue>;
}

export async function generateQueue(input: {
  available_minutes: number;
  topic_focus_ids: string[];
  requested_problem_count: number | null;
}): Promise<DailyQueue> {
  return json(
    await fetch(`${API_URL}/queues`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),
  );
}

export async function updateQueueItem(
  queueId: string,
  itemId: string,
  status: "POSTPONED" | "COMPLETED",
): Promise<DailyQueue> {
  return json(
    await fetch(`${API_URL}/queues/${queueId}/items/${itemId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),
  );
}

export async function removeQueueItem(
  queueId: string,
  itemId: string,
): Promise<DailyQueue> {
  return json(
    await fetch(`${API_URL}/queues/${queueId}/items/${itemId}`, {
      method: "DELETE",
    }),
  );
}

export async function replaceQueueItem(
  queueId: string,
  itemId: string,
): Promise<DailyQueue> {
  return json(
    await fetch(`${API_URL}/queues/${queueId}/items/${itemId}/replace`, {
      method: "POST",
    }),
  );
}

export async function addQueueItem(
  queueId: string,
  problemId: string,
): Promise<DailyQueue> {
  return json(
    await fetch(`${API_URL}/queues/${queueId}/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem_id: problemId }),
    }),
  );
}
