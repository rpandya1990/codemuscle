"use client";

import { useEffect, useState } from "react";

import {
  AreaStatistics,
  fetchTopicTotals,
  fetchTopicStatistics,
  fetchTrends,
  TrendPoint,
} from "@/lib/statistics";

export function StatisticsView() {
  const [topics, setTopics] = useState<AreaStatistics[]>([]);
  const [total, setTotal] = useState<AreaStatistics | null>(null);
  const [weeks, setWeeks] = useState(8);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    setError(null);
    void Promise.all([
      fetchTopicStatistics(),
      fetchTopicTotals(),
      fetchTrends(weeks),
    ])
      .then(([topicData, totalData, trendData]) => {
        if (!active) return;
        setTopics(topicData);
        setTotal(totalData);
        setTrends(trendData.points);
      })
      .catch(
        (reason: unknown) =>
          active &&
          setError(
            reason instanceof Error
              ? reason.message
              : "Could not load statistics.",
          ),
      );
    return () => {
      active = false;
    };
  }, [weeks]);
  const maxAttempts = Math.max(1, ...trends.map((point) => point.attempts));
  if (error)
    return (
      <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">
        {error}
      </p>
    );
  return (
    <div className="space-y-8">
      <section className="surface-card p-6">
        <h2 className="text-xl font-semibold">Practice trend</h2>
        <label className="mt-3 block text-sm">
          Time range
          <select
            className="field-control mt-1"
            value={weeks}
            onChange={(event) => setWeeks(Number(event.target.value))}
          >
            {[2, 4, 8, 12, 26, 52, 0].map((value) => (
              <option key={value} value={value}>
                {value ? `Last ${value} weeks` : "All time"}
              </option>
            ))}
          </select>
        </label>
        <p className="mt-3 text-sm text-slate-500">
          Attempts per week (week starting date). Includes the current week.
        </p>
        <div className="mt-5 flex h-52 items-end gap-3 overflow-x-auto">
          {trends.map((point) => (
            <div
              key={point.week_start}
              className="flex min-w-16 flex-1 flex-col items-center gap-2"
              title={`${point.week_start}: ${point.attempts} attempts, ${point.independent_successes} independent, ${point.failures} failed`}
            >
              <span className="text-xs font-semibold">{point.attempts}</span>
              <div
                className="w-full rounded-t bg-emerald-600"
                style={{
                  height: `${Math.max(4, (point.attempts / maxAttempts) * 140)}px`,
                }}
              />
              <span className="text-[10px] text-slate-500">
                {point.week_start}
              </span>
            </div>
          ))}
        </div>
      </section>
      <AreaTable title="Topic statistics" areas={topics} total={total} />
    </div>
  );
}

function AreaTable({
  title,
  areas,
  total,
}: {
  title: string;
  areas: AreaStatistics[];
  total: AreaStatistics | null;
}) {
  return (
    <section className="surface-card overflow-hidden">
      <div className="border-b border-slate-100 p-6">
        <h2 className="text-xl font-semibold">{title}</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="p-4">Topic</th>
              <th className="p-4">Status</th>
              <th className="p-4">Problems</th>
              <th className="p-4">Attempts</th>
              <th className="p-4">Independent</th>
              <th className="p-4">Failed</th>
              <th className="p-4">Reason</th>
            </tr>
          </thead>
          <tbody>
            {[...areas, ...(total ? [total] : [])].map((area) => (
              <tr
                key={area.id}
                className={
                  area === total
                    ? "border-t-2 border-slate-200 bg-slate-50 font-semibold"
                    : "border-t border-slate-100"
                }
              >
                <td className="p-4 font-medium">{area.name}</td>
                <td className="p-4">{area === total ? "—" : area.status}</td>
                <td className="p-4">{area.total_problems}</td>
                <td className="p-4">{area.total_attempts}</td>
                <td className="p-4">
                  {Math.round(area.independent_success_rate * 100)}%
                </td>
                <td className="p-4">
                  {Math.round(area.failed_attempt_rate * 100)}%
                </td>
                <td className="max-w-xs p-4 text-slate-500">
                  {area === total
                    ? "Each active problem counted once, including problems without topics."
                    : area.status_reasons.join("; ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
