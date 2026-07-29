export interface ImportRow {
  id: string;
  row_number: number;
  raw_data: Record<string, unknown>;
  parsed_data: Record<string, unknown> | null;
  errors: Record<string, string[]>;
  duplicate_problem_ids: string[];
  status: "VALID" | "INVALID" | "DUPLICATE" | "IMPORTED";
  created_problem_id: string | null;
}

export interface ImportJob {
  id: string;
  original_filename: string;
  status: string;
  headers: string[];
  mapping: Record<string, string>;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  rows: ImportRow[];
}

export interface ImportCommitResult {
  imported: number;
  skipped_invalid: number;
  skipped_duplicates: number;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: { message?: string };
    } | null;
    throw new Error(body?.error?.message ?? "The import request failed.");
  }
  return response.json() as Promise<T>;
}

export async function uploadImport(file: File): Promise<ImportJob> {
  const form = new FormData();
  form.append("file", file);
  return json<ImportJob>(
    await fetch(`${API_URL}/imports`, { method: "POST", body: form }),
  );
}

export async function previewImport(
  jobId: string,
  mapping: Record<string, string>,
): Promise<ImportJob> {
  await json<ImportJob>(
    await fetch(`${API_URL}/imports/${jobId}/mapping`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mapping }),
    }),
  );
  return json<ImportJob>(
    await fetch(`${API_URL}/imports/${jobId}/preview`, { method: "POST" }),
  );
}

export async function retryImport(
  jobId: string,
  corrections: Record<string, Record<string, unknown>>,
): Promise<ImportJob> {
  return json<ImportJob>(
    await fetch(`${API_URL}/imports/${jobId}/retry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ corrections }),
    }),
  );
}

export async function commitImport(
  jobId: string,
  includeDuplicateRowIds: string[],
): Promise<ImportCommitResult> {
  return json<ImportCommitResult>(
    await fetch(`${API_URL}/imports/${jobId}/commit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        include_duplicate_row_ids: includeDuplicateRowIds,
      }),
    }),
  );
}
