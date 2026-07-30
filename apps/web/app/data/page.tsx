import Link from "next/link";

import { DataManagement } from "@/features/data-lifecycle/data-management";

export default function DataPage() {
  return (
    <main className="mx-auto min-h-screen max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
      <Link href="/" className="btn-quiet -ml-3">
        ← Dashboard
      </Link>
      <div className="mb-10 mt-8">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Settings and data
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight sm:text-5xl">
          Manage your data
        </h1>
        <p className="mt-4 text-lg text-slate-600">
          Export, back up, restore, or permanently remove your private data.
        </p>
      </div>
      <DataManagement />
    </main>
  );
}
