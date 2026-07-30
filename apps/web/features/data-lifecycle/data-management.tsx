"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  Backup,
  createBackup,
  createExport,
  deleteAllData,
  fetchBackups,
  restoreBackup,
} from "@/lib/data-lifecycle";

export function DataManagement() {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);

  async function loadBackups() {
    try {
      setBackups(await fetchBackups());
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Could not load backups.",
      );
    }
  }
  useEffect(() => {
    void loadBackups();
  }, []);

  async function run(action: () => Promise<string>) {
    setWorking(true);
    setError(null);
    setMessage(null);
    try {
      setMessage(await action());
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Data operation failed.",
      );
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="space-y-8">
      {message && (
        <p
          role="status"
          className="rounded-xl bg-emerald-50 p-4 text-emerald-900"
        >
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">
          {error}
        </p>
      )}
      <section className="surface-card p-6">
        <h2 className="text-xl font-semibold">Export your data</h2>
        <p className="mt-2 text-sm text-slate-500">
          Exports are written to your private workspace exports directory.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          {(["CSV", "JSON", "XLSX"] as const).map((format) => (
            <button
              key={format}
              disabled={working}
              className="btn-secondary"
              onClick={() =>
                void run(async () => {
                  const result = await createExport(format);
                  return `Created ${result.filename} with ${result.problem_count} problems.`;
                })
              }
            >
              Export {format}
            </button>
          ))}
        </div>
      </section>
      <section className="surface-card p-6">
        <h2 className="text-xl font-semibold">Backups</h2>
        <p className="mt-2 text-sm text-slate-500">
          Create a versioned ZIP containing a database export and manifest.
        </p>
        <form
          className="mt-5 flex flex-wrap items-center gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            const form = new FormData(event.currentTarget);
            void run(async () => {
              const result = await createBackup(
                form.get("imports") === "on",
                form.get("exports") === "on",
              );
              await loadBackups();
              return `Created ${result.filename}.`;
            });
          }}
        >
          <label className="flex gap-2">
            <input type="checkbox" name="imports" /> Include imports
          </label>
          <label className="flex gap-2">
            <input type="checkbox" name="exports" /> Include exports
          </label>
          <button disabled={working} className="btn-primary">
            Create backup
          </button>
        </form>
        <ul className="mt-6 space-y-3">
          {backups.map((backup) => (
            <li
              key={backup.id}
              className="rounded-xl border border-slate-200 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium">{backup.filename}</p>
                  <p className="text-sm text-slate-500">
                    {new Date(backup.created_at).toLocaleString()} ·{" "}
                    {backup.status}
                  </p>
                </div>
                <button
                  disabled={working}
                  className="btn-secondary"
                  onClick={() => {
                    const confirmation = window.prompt(
                      "Type RESTORE to replace current data",
                    );
                    if (confirmation)
                      void run(async () => {
                        const result = await restoreBackup(
                          backup.id,
                          confirmation,
                        );
                        window.location.reload();
                        return `Restored ${result.restored_rows} rows.`;
                      });
                  }}
                >
                  Restore
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>
      <section className="surface-card border-red-200 p-6">
        <h2 className="text-xl font-semibold text-red-900">
          Delete personal data
        </h2>
        <p className="mt-2 text-sm text-red-700">
          This permanently deletes application records and selected workspace
          files. Create a backup first.
        </p>
        <form
          className="mt-5 space-y-4"
          onSubmit={(event: FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            const form = new FormData(event.currentTarget);
            void run(async () => {
              const result = await deleteAllData({
                confirmation: String(form.get("confirmation")),
                delete_import_files: form.get("imports") === "on",
                delete_export_files: form.get("exports") === "on",
                delete_backup_files: form.get("backups") === "on",
              });
              setBackups(result.backups_preserved ? backups : []);
              return `Deleted ${result.deleted_rows} database rows.`;
            });
          }}
        >
          <label className="field-label">
            Type DELETE ALL DATA
            <input
              name="confirmation"
              required
              className="field-control"
              autoComplete="off"
            />
          </label>
          <div className="flex flex-wrap gap-4">
            <label>
              <input type="checkbox" name="imports" defaultChecked /> Delete
              import files
            </label>
            <label>
              <input type="checkbox" name="exports" defaultChecked /> Delete
              export files
            </label>
            <label>
              <input type="checkbox" name="backups" /> Delete backups too
            </label>
          </div>
          <button
            disabled={working}
            className="btn bg-red-700 text-white hover:bg-red-800"
          >
            Delete selected data
          </button>
        </form>
      </section>
    </div>
  );
}
