export type AttemptOutcome =
  | "SOLVED_INDEPENDENTLY"
  | "SOLVED_SMALL_HINT"
  | "SOLVED_SIGNIFICANT_HELP"
  | "UNDERSTOOD_AFTER_SOLUTION"
  | "FAILED"
  | "SKIPPED";

export type HintUsage =
  "NONE" | "SMALL" | "SIGNIFICANT" | "SOLUTION_VIEWED" | "NOT_APPLICABLE";

export interface Attempt {
  id: string;
  problem_id: string;
  attempted_at: string;
  outcome: AttemptOutcome;
  hint_usage: HintUsage;
  time_spent_minutes: number | null;
  notes: string | null;
  previous_mastery_state: string;
  calculated_mastery_state: string;
  calculated_next_revision_date: string;
  schedule_explanation: string;
  created_at: string;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function fetchAttempts(problemId: string): Promise<Attempt[]> {
  const response = await fetch(`${API_URL}/problems/${problemId}/attempts`);
  if (!response.ok) throw new Error("Could not load attempt history.");
  return response.json() as Promise<Attempt[]>;
}

export async function createAttempt(
  problemId: string,
  input: {
    outcome: AttemptOutcome;
    hint_usage: HintUsage;
    time_spent_minutes: number | null;
    notes: string | null;
  },
): Promise<Attempt> {
  const response = await fetch(`${API_URL}/problems/${problemId}/attempts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error("Could not record the attempt.");
  return response.json() as Promise<Attempt>;
}
