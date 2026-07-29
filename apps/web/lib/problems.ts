export type Difficulty = "EASY" | "MEDIUM" | "HARD" | "UNKNOWN";

export interface NamedReference {
  id: string;
  name: string;
}

export interface Problem {
  id: string;
  title: string;
  url: string | null;
  platform: string | null;
  difficulty: Difficulty;
  notes: string | null;
  priority: number;
  total_attempts: number;
  successful_revision_streak: number;
  next_revision_date: string | null;
  calculated_next_revision_date: string | null;
  next_revision_overridden: boolean;
  current_mastery_state: string;
  archived_at: string | null;
  topics: NamedReference[];
  patterns: NamedReference[];
}

export interface ProblemList {
  items: Problem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DuplicateCandidate {
  problem: Problem;
  confidence: number;
  reason: string;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function fetchProblems(
  search: string,
  archived: boolean,
  difficulty?: Difficulty,
  topicId?: string,
): Promise<ProblemList> {
  const parameters = new URLSearchParams({
    archived: String(archived),
    page_size: "5000",
  });
  if (search) parameters.set("search", search);
  if (difficulty) parameters.set("difficulty", difficulty);
  if (topicId) parameters.set("topic_id", topicId);
  const response = await fetch(`${API_URL}/problems?${parameters}`);
  if (!response.ok) throw new Error("Could not load the problem library.");
  return response.json() as Promise<ProblemList>;
}

export async function fetchTopics(): Promise<NamedReference[]> {
  const response = await fetch(`${API_URL}/problems/topics`);
  if (!response.ok) throw new Error("Could not load topics.");
  return response.json() as Promise<NamedReference[]>;
}

export async function updateProblem(
  problemId: string,
  input: {
    title: string;
    url: string | null;
    difficulty: Difficulty;
    notes: string | null;
    patterns: string[];
  },
): Promise<Problem> {
  const response = await fetch(`${API_URL}/problems/${problemId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error("Could not edit the problem.");
  return response.json() as Promise<Problem>;
}

export async function createProblem(input: {
  title: string;
  url?: string;
  difficulty: Difficulty;
  notes?: string;
  topics: string[];
  patterns: string[];
}): Promise<Problem> {
  const response = await fetch(`${API_URL}/problems`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error("Could not add the problem.");
  return response.json() as Promise<Problem>;
}

export async function findDuplicates(
  title: string,
): Promise<DuplicateCandidate[]> {
  const response = await fetch(
    `${API_URL}/problems/duplicates?title=${encodeURIComponent(title)}`,
  );
  if (!response.ok) return [];
  return response.json() as Promise<DuplicateCandidate[]>;
}

export async function setProblemArchived(
  problemId: string,
  archived: boolean,
): Promise<void> {
  const action = archived ? "archive" : "restore";
  const response = await fetch(`${API_URL}/problems/${problemId}/${action}`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Could not ${action} the problem.`);
}

export async function setScheduleOverride(
  problemId: string,
  nextRevisionDate: string,
): Promise<Problem> {
  const response = await fetch(
    `${API_URL}/problems/${problemId}/schedule-override`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ next_revision_date: nextRevisionDate }),
    },
  );
  if (!response.ok) throw new Error("Could not override the revision date.");
  return response.json() as Promise<Problem>;
}

export async function clearScheduleOverride(
  problemId: string,
): Promise<Problem> {
  const response = await fetch(
    `${API_URL}/problems/${problemId}/schedule-override`,
    {
      method: "DELETE",
    },
  );
  if (!response.ok)
    throw new Error("Could not clear the revision-date override.");
  return response.json() as Promise<Problem>;
}
