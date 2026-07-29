import Link from "next/link";

import { ProblemLibrary } from "@/features/problems/problem-library";

export default function ProblemsPage() {
  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <div className="flex justify-between">
        <Link href="/" className="text-sm font-medium text-emerald-700">
          ← Dashboard
        </Link>
        <Link href="/import" className="text-sm font-medium text-emerald-700">
          Import CSV or Excel →
        </Link>
      </div>
      <div className="mb-10 mt-5">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Library
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">
          Coding problems
        </h1>
        <p className="mt-3 text-slate-600">
          Build and maintain the material your revision queue will use.
        </p>
      </div>
      <ProblemLibrary />
    </main>
  );
}
