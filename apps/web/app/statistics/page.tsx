import Link from "next/link";

import { StatisticsView } from "@/features/statistics/statistics-view";

export default function StatisticsPage() {
  return (
    <main className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
      <Link href="/" className="btn-quiet -ml-3">
        ← Dashboard
      </Link>
      <div className="mb-10 mt-8">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Insights
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight sm:text-5xl">
          Practice statistics
        </h1>
        <p className="mt-4 text-lg text-slate-600">
          Understand progress and identify weak or neglected areas.
        </p>
      </div>
      <StatisticsView />
    </main>
  );
}
