import Link from "next/link";

import { DailyQueue } from "@/features/queues/daily-queue";

export default function QueuePage() {
  return (
    <main className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
      <Link href="/" className="btn-quiet -ml-3">
        ← Dashboard
      </Link>
      <div className="mb-10 mt-8 max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Daily revision
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-[-0.035em] text-slate-950 sm:text-5xl">
          Your focused queue
        </h1>
        <p className="mt-4 text-lg leading-8 text-slate-600">
          Fit the highest-value revision work into the time you have today.
        </p>
      </div>
      <DailyQueue />
    </main>
  );
}
