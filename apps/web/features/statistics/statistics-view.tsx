"use client";

import { useEffect, useState } from "react";

import {
  AreaStatistics,
  fetchTopicTotals,
  fetchTopicStatistics,
  fetchTrends,
  TrendPoint,
  TrendInterval,
} from "@/lib/statistics";

export function StatisticsView() {
  const [topics, setTopics] = useState<AreaStatistics[]>([]);
  const [total, setTotal] = useState<AreaStatistics | null>(null);
  const [interval, setInterval] = useState<TrendInterval>("week");
  const [count, setCount] = useState("8");
  const [allTime, setAllTime] = useState(false);
  const [loading, setLoading] = useState(false);
  const validCount =
    /^\d+$/.test(count) && Number(count) >= 1 && Number(count) <= 1000;
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    if (!allTime && !validCount) {
      setLoading(false);
      return;
    }
    setError(null);
    setLoading(true);
    void Promise.all([
      fetchTopicStatistics(),
      fetchTopicTotals(),
      fetchTrends(interval, allTime ? 0 : Number(count)),
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
      )
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [interval, count, allTime, validCount]);
  const maxAttempts = Math.max(1, ...trends.map((point) => point.attempts));
  return (
    <div className="space-y-8">
      <section className="surface-card p-6">
        <h2 className="text-xl font-semibold">Practice trend</h2>
        <div className="mt-3 flex flex-wrap items-end gap-4">
          <label className="block text-sm">
            Group by
            <select
              className="field-control mt-1"
              value={interval}
              onChange={(event) =>
                setInterval(event.target.value as TrendInterval)
              }
            >
              <option value="day">Day</option>
              <option value="week">Week</option>
              <option value="month">Month</option>
              <option value="year">Year</option>
            </select>
          </label>
          <label className="block text-sm">
            Number of {interval}s
            <input
              className="field-control mt-1"
              type="number"
              min={1}
              max={1000}
              step={1}
              value={count}
              disabled={allTime}
              aria-invalid={!allTime && !validCount}
              aria-describedby={
                !allTime && !validCount ? "trend-count-error" : undefined
              }
              onChange={(event) => setCount(event.target.value)}
            />
          </label>
          <label className="flex items-center gap-2 py-2 text-sm">
            <input
              type="checkbox"
              checked={allTime}
              onChange={(event) => setAllTime(event.target.checked)}
            />
            All time
          </label>
        </div>
        {!allTime && !validCount && (
          <p
            id="trend-count-error"
            role="alert"
            className="mt-2 text-sm text-red-800"
          >
            Enter a whole number from 1 to 1,000.
          </p>
        )}
        {error && (
          <p role="alert" className="mt-3 text-red-800">
            {error}
          </p>
        )}
        <p className="mt-3 text-sm text-slate-500">
          {allTime ? "All recorded history" : `Last ${count} ${interval}s`}.
          Each bar shows attempts for one {interval}. Includes the current
          partial {interval}.
          {interval === "week" ? " Weeks start on Monday." : ""}
        </p>
        {loading && (
          <p role="status" className="mt-3 text-sm text-slate-500">
            Loading trend…
          </p>
        )}
        <div
          aria-label="Practice trend bars"
          aria-busy={loading}
          className="mt-5 flex h-52 items-end gap-3 overflow-x-auto"
        >
          {!loading &&
            (allTime || validCount) &&
            !error &&
            trends.map((point) => (
              <div
                key={point.period_start}
                className="flex min-w-16 flex-1 flex-col items-center gap-2"
                title={`${point.period_start}: ${point.attempts} attempts, ${point.independent_successes} independent, ${point.failures} failed`}
              >
                <span className="text-xs font-semibold">{point.attempts}</span>
                <div
                  className="w-full rounded-t bg-emerald-600"
                  style={{
                    height: `${Math.max(4, (point.attempts / maxAttempts) * 140)}px`,
                  }}
                />
                <span className="text-[10px] text-slate-500">
                  {interval === "year"
                    ? point.period_start.slice(0, 4)
                    : interval === "month"
                      ? point.period_start.slice(0, 7)
                      : point.period_start}
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
        <p className="mt-2 text-sm text-slate-500">
          Health is the percentage of active problems solved independently at
          least once. Unattempted problems are included.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="p-4">Topic</th>
              <th className="p-4">Status</th>
              <th className="p-4">Problems</th>
              <th className="p-4">Attempts</th>
              <th className="p-4">Health</th>
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
                  {Math.round(area.health_rate * 100)}%
                  <span className="block text-xs font-normal text-slate-500">
                    {area.independently_solved_problems} of{" "}
                    {area.total_problems} problems
                  </span>
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
