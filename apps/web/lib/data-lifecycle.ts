export interface Backup {
  id: string;
  filename: string;
  manifest_version: number;
  application_version: string;
  status: string;
  created_at: string;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: { message?: string };
    } | null;
    throw new Error(
      body?.error?.message ??
        `Data operation failed (HTTP ${response.status}).`,
    );
  }
  return response.json() as Promise<T>;
}

export async function fetchBackups() {
  return json<Backup[]>(await fetch(`${API_URL}/backups`));
}

export async function createExport(format: "CSV" | "JSON" | "XLSX") {
  return json<{
    filename: string;
    problem_count: number;
    attempt_count: number;
  }>(
    await fetch(`${API_URL}/exports`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format, include_archived: true }),
    }),
  );
}

export async function createBackup(
  includeImports: boolean,
  includeExports: boolean,
) {
  return json<Backup>(
    await fetch(`${API_URL}/backups`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        include_imports: includeImports,
        include_exports: includeExports,
      }),
    }),
  );
}

export async function restoreBackup(backupId: string, confirmation: string) {
  return json<{ status: string; restored_rows: number }>(
    await fetch(`${API_URL}/backups/${backupId}/restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirmation }),
    }),
  );
}

export async function deleteAllData(input: {
  confirmation: string;
  delete_import_files: boolean;
  delete_export_files: boolean;
  delete_backup_files: boolean;
}) {
  return json<{
    status: string;
    deleted_rows: number;
    backups_preserved: boolean;
  }>(
    await fetch(`${API_URL}/data`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),
  );
}
