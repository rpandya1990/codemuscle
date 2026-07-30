import Link from "next/link";

import { DashboardOverview } from "@/features/statistics/dashboard-overview";

export default function HomePage() {
  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-16">
      <section className="mb-10 rounded-3xl border border-emerald-950/10 bg-white p-10 shadow-sm">
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          CodeMuscle
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">
          Know what to revise today.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
          Your private, deterministic coding-interview revision tracker is
          taking shape.
        </p>
        <div className="mt-10 rounded-2xl bg-emerald-50 p-5 text-emerald-950">
          <Link
            href="/problems"
            className="font-semibold underline underline-offset-4"
          >
            Open your problem library →
          </Link>
          <span className="mx-3 text-emerald-300">|</span>
          <Link
            href="/queue"
            className="font-semibold underline underline-offset-4"
          >
            Build today’s queue →
          </Link>
          <span className="mx-3 text-emerald-300">|</span>
          <Link
            href="/statistics"
            className="font-semibold underline underline-offset-4"
          >
            View statistics →
          </Link>
        </div>
      </section>
      <DashboardOverview />
    </main>
  );
}
