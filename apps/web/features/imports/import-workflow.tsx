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
    <div className="space-y-8">
      <form
        onSubmit={(event) => void upload(event)}
        className="rounded-2xl border bg-white p-6"
      >
        <label className="block font-medium">
          CSV or Excel file
          <input
            className="mt-3 block w-full rounded-xl border p-3"
            name="file"
            type="file"
            accept=".csv,.xlsx"
            required
          />
        </label>
        <button
          disabled={busy}
          className="mt-4 rounded-xl bg-emerald-700 px-5 py-3 font-semibold text-white disabled:opacity-50"
        >
          Upload securely
        </button>
      </form>

      {error && (
        <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">
          {error}
        </p>
      )}

      {job && job.rows.length === 0 && (
        <section className="rounded-2xl border bg-white p-6">
          <h2 className="text-xl font-semibold">Map columns</h2>
          <p className="mt-2 text-sm text-slate-500">
            Review the suggested mapping. A title column is required.
          </p>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {fields.map(([field, label]) => (
              <label key={field} className="text-sm font-medium">
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
                  className="mt-1 w-full rounded-xl border p-3"
                >
                  <option value="">Not mapped</option>
                  {job.headers.map((header) => (
                    <option key={header}>{header}</option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          <button
            disabled={busy || !mapping.title}
            onClick={() => void preview()}
            className="mt-6 rounded-xl bg-emerald-700 px-5 py-3 font-semibold text-white disabled:opacity-50"
          >
            Validate and preview
          </button>
        </section>
      )}

      {job && job.rows.length > 0 && (
        <section className="rounded-2xl border bg-white p-6">
          <div className="flex flex-wrap gap-3 text-sm">
            <span className="rounded-full bg-slate-100 px-3 py-1">
              Total {job.total_rows}
            </span>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-800">
              Valid {job.valid_rows}
            </span>
            <span className="rounded-full bg-red-50 px-3 py-1 text-red-800">
              Invalid {job.invalid_rows}
            </span>
            <span className="rounded-full bg-amber-50 px-3 py-1 text-amber-800">
              Duplicates {job.duplicate_rows}
            </span>
          </div>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-3">Row</th>
                  <th className="p-3">Title</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Review</th>
                </tr>
              </thead>
              <tbody>
                {job.rows.map((row) => (
                  <tr key={row.id} className="border-b align-top">
                    <td className="p-3">{row.row_number}</td>
                    <td className="p-3">
                      {String(row.parsed_data?.title ?? "—")}
                    </td>
                    <td className="p-3 font-medium">{row.status}</td>
                    <td className="p-3">
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
                            className="mt-2 rounded-lg border p-2"
                          />
                        </div>
                      )}
                      {row.status === "DUPLICATE" && (
                        <label className="flex gap-2">
                          <input
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
          <div className="mt-6 flex gap-3">
            {job.invalid_rows > 0 && (
              <button
                disabled={busy}
                onClick={() => void retry()}
                className="rounded-xl border px-5 py-3 font-semibold"
              >
                Retry corrections
              </button>
            )}
            <button
              disabled={busy}
              onClick={() => void commit()}
              className="rounded-xl bg-emerald-700 px-5 py-3 font-semibold text-white"
            >
              Import valid rows
            </button>
          </div>
        </section>
      )}

      {result && (
        <p
          role="status"
          className="rounded-xl bg-emerald-50 p-5 text-emerald-900"
        >
          Imported {result.imported} problems. Skipped {result.skipped_invalid}{" "}
          invalid and {result.skipped_duplicates} possible duplicates.
        </p>
      )}
    </div>
  );
}
