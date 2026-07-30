export interface RecentActivity {
  attempt_id: string;
  problem_id: string;
  problem_title: string;
  outcome: string;
  attempted_at: string;
}

export interface DashboardStatistics {
  total_active_problems: number;
  due_today: number;
  overdue: number;
  practiced_this_week: number;
  mastered: number;
  needs_relearning: number;
  recent_activity: RecentActivity[];
}

export interface AreaStatistics {
  id: string;
  name: string;
  total_problems: number;
  total_attempts: number;
  independent_success_rate: number;
  hint_assisted_success_rate: number;
  failed_attempt_rate: number;
  problems_due: number;
  problems_overdue: number;
  mastery_distribution: Record<string, number>;
  last_practiced_date: string | null;
  recent_trend: string;
  status: "WEAK" | "NEGLECTED" | "IMPROVING" | "STABLE";
  status_reasons: string[];
}

export interface TrendPoint {
  week_start: string;
  attempts: number;
  independent_successes: number;
  failures: number;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok)
    throw new Error(`Statistics request failed (HTTP ${response.status}).`);
  return response.json() as Promise<T>;
}

export const fetchDashboard = () =>
  get<DashboardStatistics>("/statistics/dashboard");
export const fetchTopicStatistics = () =>
  get<AreaStatistics[]>("/statistics/topics");
export const fetchPatternStatistics = () =>
  get<AreaStatistics[]>("/statistics/patterns");
export const fetchWeakAreas = () =>
  get<AreaStatistics[]>("/statistics/weak-areas");
export const fetchTrends = (weeks = 8) =>
  get<{ points: TrendPoint[] }>(`/statistics/trends?weeks=${weeks}`);
