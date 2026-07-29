import Link from "next/link";

import { ProblemLibrary } from "@/features/problems/problem-library";

export default function ProblemsPage() {
  return (
    <main className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
      <div className="flex items-center">
        <Link href="/" className="btn-quiet -ml-3">
          ← Dashboard
        </Link>
      </div>
      <div className="mb-10 mt-8 max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Library
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-[-0.035em] text-slate-950 sm:text-5xl">
          Coding problems
        </h1>
        <p className="mt-4 text-lg leading-8 text-slate-600">
          Build and maintain the material your revision queue will use.
        </p>
      </div>
      <ProblemLibrary />
    </main>
  );
}
