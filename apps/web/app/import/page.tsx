import Link from "next/link";

import { ImportWorkflow } from "@/features/imports/import-workflow";

export default function ImportPage() {
  return (
    <main className="mx-auto min-h-screen max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
      <Link href="/problems" className="btn-quiet -ml-3">
        ← Problem library
      </Link>
      <div className="mb-10 mt-8 max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Data import
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-[-0.035em] text-slate-950 sm:text-5xl">
          Import preparation history
        </h1>
        <p className="mt-4 text-lg leading-8 text-slate-600">
          Preview and validate every row before anything enters your library.
        </p>
      </div>
      <ImportWorkflow />
    </main>
  );
}
