"use client";

import { useEffect, useState } from "react";

import {
  AreaStatistics,
  fetchPatternStatistics,
  fetchTopicStatistics,
  fetchTrends,
  TrendPoint,
} from "@/lib/statistics";

export function StatisticsView() {
  const [topics, setTopics] = useState<AreaStatistics[]>([]);
  const [patterns, setPatterns] = useState<AreaStatistics[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    void Promise.all([
      fetchTopicStatistics(),
      fetchPatternStatistics(),
      fetchTrends(),
    ])
      .then(([topicData, patternData, trendData]) => {
        setTopics(topicData);
        setPatterns(patternData);
        setTrends(trendData.points);
      })
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error
            ? reason.message
            : "Could not load statistics.",
        ),
      );
  }, []);
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
        <div className="mt-5 flex h-44 items-end gap-3">
          {trends.map((point) => (
            <div
              key={point.week_start}
              className="flex flex-1 flex-col items-center gap-2"
            >
              <span className="text-xs font-semibold">{point.attempts}</span>
              <div
                className="w-full rounded-t bg-emerald-600"
                style={{ height: `${Math.max(4, point.attempts * 12)}px` }}
              />
              <span className="text-[10px] text-slate-500">
                {point.week_start.slice(5)}
              </span>
            </div>
          ))}
        </div>
      </section>
      <AreaTable title="Topic statistics" areas={topics} />
      <AreaTable title="Pattern statistics" areas={patterns} />
    </div>
  );
}

function AreaTable({
  title,
  areas,
}: {
  title: string;
  areas: AreaStatistics[];
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
              <th className="p-4">Area</th>
              <th className="p-4">Status</th>
              <th className="p-4">Problems</th>
              <th className="p-4">Attempts</th>
              <th className="p-4">Independent</th>
              <th className="p-4">Failed</th>
              <th className="p-4">Reason</th>
            </tr>
          </thead>
          <tbody>
            {areas.map((area) => (
              <tr key={area.id} className="border-t border-slate-100">
                <td className="p-4 font-medium">{area.name}</td>
                <td className="p-4">{area.status}</td>
                <td className="p-4">{area.total_problems}</td>
                <td className="p-4">{area.total_attempts}</td>
                <td className="p-4">
                  {Math.round(area.independent_success_rate * 100)}%
                </td>
                <td className="p-4">
                  {Math.round(area.failed_attempt_rate * 100)}%
                </td>
                <td className="max-w-xs p-4 text-slate-500">
                  {area.status_reasons.join("; ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
