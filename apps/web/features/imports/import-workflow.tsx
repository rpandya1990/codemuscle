"use client";

import { FormEvent, useState } from "react";

import {
  commitImport,
  ImportCommitResult,
  ImportJob,
  previewImport,
  retryImport,
  uploadImport,
} from "@/lib/imports";

const fields = [
  ["title", "Problem title"],
  ["url", "Problem link"],
  ["difficulty", "Difficulty"],
  ["notes", "Notes"],
  ["topic", "Topic"],
  ["pattern", "Pattern"],
  ["last_revised_date", "Last revised date"],
  ["revision_count", "Revision count"],
  ["successful_streak", "Successful streak"],
  ["next_revision_date", "Next revision date"],
] as const;

const statusStyles: Record<string, string> = {
  VALID: "border-emerald-200 bg-emerald-50 text-emerald-800",
  INVALID: "border-red-200 bg-red-50 text-red-800",
  DUPLICATE: "border-amber-200 bg-amber-50 text-amber-800",
  IMPORTED: "border-sky-200 bg-sky-50 text-sky-800",
};

export function ImportWorkflow() {
  const [job, setJob] = useState<ImportJob | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [acceptedDuplicates, setAcceptedDuplicates] = useState<string[]>([]);
  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const [result, setResult] = useState<ImportCommitResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = new FormData(event.currentTarget).get("file");
    if (!(file instanceof File) || !file.name) return;
    await run(async () => {
      const uploaded = await uploadImport(file);
      setJob(uploaded);
      setMapping(uploaded.mapping);
    });
  }

  async function preview() {
    if (!job) return;
    await run(async () => setJob(await previewImport(job.id, mapping)));
  }

  async function retry() {
    if (!job) return;
    const payload = Object.fromEntries(
      Object.entries(corrections)
        .filter(([, title]) => title.trim())
        .map(([rowId, title]) => [rowId, { title: title.trim() }]),
    );
    await run(async () => setJob(await retryImport(job.id, payload)));
  }

  async function commit() {
    if (!job) return;
    await run(async () =>
      setResult(await commitImport(job.id, acceptedDuplicates)),
    );
  }

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "The import request failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <form
        onSubmit={(event) => void upload(event)}
        className="surface-card overflow-hidden"
      >
        <div className="border-b border-slate-100 px-6 py-5">
          <div className="flex items-center gap-3">
            <span className="flex size-8 items-center justify-center rounded-full bg-emerald-700 text-sm font-bold text-white">
              1
            </span>
            <div>
              <h2 className="font-semibold text-slate-900">
                Choose your source file
              </h2>
              <p className="mt-0.5 text-sm text-slate-500">
                Your original file stays in your private workspace.
              </p>
            </div>
          </div>
        </div>
        <div className="p-6">
          <label className="group flex cursor-pointer flex-col items-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/70 px-6 py-10 text-center transition hover:border-emerald-400 hover:bg-emerald-50/40">
            <span className="flex size-12 items-center justify-center rounded-2xl bg-white text-2xl text-emerald-700 shadow-sm ring-1 ring-slate-200">
              ↑
            </span>
            <span className="mt-4 font-semibold text-slate-800">
              Select a CSV or Excel file
            </span>
            <span className="mt-1 text-sm text-slate-500">
              .csv or .xlsx · maximum 10 MB
            </span>
            <input
              aria-label="CSV or Excel file"
              className="mt-5 block max-w-full text-sm text-slate-500 file:mr-4 file:rounded-lg file:border-0 file:bg-emerald-100 file:px-4 file:py-2 file:font-semibold file:text-emerald-800 hover:file:bg-emerald-200"
              name="file"
              type="file"
              accept=".csv,.xlsx"
              required
            />
          </label>
          <div className="mt-5 flex justify-end">
            <button disabled={busy} className="btn-primary">
              {busy ? "Uploading…" : "Upload securely"}
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      </form>

      {error && (
        <p
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
        >
          {error}
        </p>
      )}

      {job && job.rows.length === 0 && (
        <section className="surface-card overflow-hidden">
          <div className="border-b border-slate-100 px-6 py-5">
            <div className="flex items-center gap-3">
              <span className="flex size-8 items-center justify-center rounded-full bg-emerald-700 text-sm font-bold text-white">
                2
              </span>
              <div>
                <h2 className="font-semibold text-slate-900">Map columns</h2>
                <p className="mt-0.5 text-sm text-slate-500">
                  Review the suggestions. Only problem title is required.
                </p>
              </div>
            </div>
          </div>
          <div className="grid gap-x-6 gap-y-5 p-6 sm:grid-cols-2">
            {fields.map(([field, label]) => (
              <label key={field} className="field-label">
                {label}
                {field === "title" ? " *" : ""}
                <select
                  value={mapping[field] ?? ""}
                  onChange={(event) =>
                    setMapping((current) => ({
                      ...current,
                      [field]: event.target.value,
                    }))
                  }
                  className="field-control"
                >
                  <option value="">Not mapped</option>
                  {job.headers.map((header) => (
                    <option key={header}>{header}</option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          <div className="flex justify-end border-t border-slate-100 bg-slate-50/60 px-6 py-4">
            <button
              type="button"
              disabled={busy || !mapping.title}
              onClick={() => void preview()}
              className="btn-primary"
            >
              {busy ? "Validating…" : "Validate and preview"}
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </section>
      )}

      {job && job.rows.length > 0 && (
        <section className="surface-card overflow-hidden">
          <div className="border-b border-slate-100 px-6 py-5">
            <div className="flex items-center gap-3">
              <span className="flex size-8 items-center justify-center rounded-full bg-emerald-700 text-sm font-bold text-white">
                3
              </span>
              <div>
                <h2 className="font-semibold text-slate-900">Review import</h2>
                <p className="mt-0.5 text-sm text-slate-500">
                  Fix invalid rows and decide whether to keep possible
                  duplicates.
                </p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 p-6 sm:grid-cols-4">
            <div className="rounded-xl bg-slate-50 p-3">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Total
              </p>
              <p className="mt-1 text-2xl font-semibold text-slate-800">
                {job.total_rows}
              </p>
            </div>
            <div className="rounded-xl bg-emerald-50 p-3">
              <p className="text-xs font-medium uppercase tracking-wide text-emerald-600">
                Valid
              </p>
              <p className="mt-1 text-2xl font-semibold text-emerald-800">
                {job.valid_rows}
              </p>
            </div>
            <div className="rounded-xl bg-red-50 p-3">
              <p className="text-xs font-medium uppercase tracking-wide text-red-500">
                Invalid
              </p>
              <p className="mt-1 text-2xl font-semibold text-red-800">
                {job.invalid_rows}
              </p>
            </div>
            <div className="rounded-xl bg-amber-50 p-3">
              <p className="text-xs font-medium uppercase tracking-wide text-amber-600">
                Duplicates
              </p>
              <p className="mt-1 text-2xl font-semibold text-amber-800">
                {job.duplicate_rows}
              </p>
            </div>
          </div>
          <div className="overflow-x-auto border-y border-slate-200">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-5 py-3 font-semibold">Row</th>
                  <th className="px-5 py-3 font-semibold">Title</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Review</th>
                </tr>
              </thead>
              <tbody>
                {job.rows.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-slate-100 align-top last:border-0 hover:bg-slate-50/70"
                  >
                    <td className="px-5 py-4 font-mono text-xs text-slate-400">
                      {row.row_number}
                    </td>
                    <td className="px-5 py-4 font-medium text-slate-800">
                      {String(row.parsed_data?.title ?? "—")}
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${statusStyles[row.status] ?? "border-slate-200 bg-slate-50 text-slate-700"}`}
                      >
                        {row.status}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      {row.status === "INVALID" && (
                        <div>
                          <p className="text-red-700">
                            {Object.values(row.errors).flat().join(", ")}
                          </p>
                          <input
                            aria-label={`Correct title for row ${row.row_number}`}
                            placeholder="Corrected title"
                            value={corrections[row.id] ?? ""}
                            onChange={(event) =>
                              setCorrections((current) => ({
                                ...current,
                                [row.id]: event.target.value,
                              }))
                            }
                            className="field-control mt-2 max-w-xs"
                          />
                        </div>
                      )}
                      {row.status === "DUPLICATE" && (
                        <label className="flex cursor-pointer items-center gap-2 font-medium text-slate-700">
                          <input
                            className="size-4 rounded border-slate-300 text-emerald-700 focus:ring-emerald-600"
                            type="checkbox"
                            checked={acceptedDuplicates.includes(row.id)}
                            onChange={(event) =>
                              setAcceptedDuplicates((current) =>
                                event.target.checked
                                  ? [...current, row.id]
                                  : current.filter((id) => id !== row.id),
                              )
                            }
                          />
                          Keep both
                        </label>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap justify-end gap-3 bg-slate-50/60 px-6 py-4">
            {job.invalid_rows > 0 && (
              <button
                disabled={busy}
                onClick={() => void retry()}
                className="btn-secondary"
              >
                Retry corrections
              </button>
            )}
            <button
              disabled={busy}
              onClick={() => void commit()}
              className="btn-primary"
            >
              Import valid rows
            </button>
          </div>
        </section>
      )}

      {result && (
        <p
          role="status"
          className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 font-medium text-emerald-900 shadow-sm"
        >
          Imported {result.imported} problems. Skipped {result.skipped_invalid}{" "}
          invalid and {result.skipped_duplicates} possible duplicates.
        </p>
      )}
    </div>
  );
}
