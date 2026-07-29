import Link from "next/link";

import { ImportWorkflow } from "@/features/imports/import-workflow";

export default function ImportPage() {
  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <Link href="/problems" className="text-sm font-medium text-emerald-700">
        ← Problem library
      </Link>
      <div className="mb-10 mt-5">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Data import
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">
          Import preparation history
        </h1>
        <p className="mt-3 text-slate-600">
          Preview and validate every row before anything enters your library.
        </p>
      </div>
      <ImportWorkflow />
    </main>
  );
}
