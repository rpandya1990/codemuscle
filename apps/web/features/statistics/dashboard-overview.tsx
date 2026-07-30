"use client";

import { useEffect, useState } from "react";

import {
  DashboardStatistics,
  fetchDashboard,
  fetchWeakAreas,
  AreaStatistics,
} from "@/lib/statistics";

export function DashboardOverview() {
  const [dashboard, setDashboard] = useState<DashboardStatistics | null>(null);
  const [weakAreas, setWeakAreas] = useState<AreaStatistics[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all([fetchDashboard(), fetchWeakAreas()])
      .then(([summary, areas]) => {
        setDashboard(summary);
        setWeakAreas(areas.slice(0, 5));
      })
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error
            ? reason.message
            : "Could not load dashboard statistics.",
        ),
      );
  }, []);

  if (error)
    return (
      <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">
        {error}
      </p>
    );
  if (!dashboard) return <p className="text-slate-500">Loading dashboard…</p>;

  const cards = [
    ["Due today", dashboard.due_today],
    ["Overdue", dashboard.overdue],
    ["Practiced this week", dashboard.practiced_this_week],
    ["Mastered", dashboard.mastered],
    ["Needs relearning", dashboard.needs_relearning],
    ["Active problems", dashboard.total_active_problems],
  ] as const;
  return (
    <div className="space-y-8">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map(([label, value]) => (
          <div key={label} className="surface-card p-5">
            <p className="text-sm font-medium text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-950">
              {value}
            </p>
          </div>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="surface-card p-6">
          <h2 className="text-lg font-semibold">Weak and neglected topics</h2>
          {weakAreas.length ? (
            <ul className="mt-4 space-y-3">
              {weakAreas.map((area) => (
                <li key={area.id} className="flex justify-between gap-4">
                  <span>{area.name}</span>
                  <span className="text-sm font-semibold text-amber-700">
                    {area.status}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-slate-500">
              No weak areas detected.
            </p>
          )}
        </section>
        <section className="surface-card p-6">
          <h2 className="text-lg font-semibold">Recent activity</h2>
          {dashboard.recent_activity.length ? (
            <ul className="mt-4 space-y-3">
              {dashboard.recent_activity.slice(0, 5).map((activity) => (
                <li key={activity.attempt_id}>
                  <p className="font-medium">{activity.problem_title}</p>
                  <p className="text-sm text-slate-500">
                    {activity.outcome.replaceAll("_", " ").toLowerCase()} ·{" "}
                    {new Date(activity.attempted_at).toLocaleDateString()}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-slate-500">
              No attempts recorded yet.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
