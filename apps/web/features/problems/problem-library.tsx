"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  createProblem,
  Difficulty,
  fetchProblems,
  findDuplicates,
  Problem,
  setProblemArchived,
  updateProblem,
} from "@/lib/problems";

export function ProblemLibrary() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [search, setSearch] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [difficulty, setDifficulty] = useState<Difficulty | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchProblems(
        search,
        showArchived,
        difficulty || undefined,
      );
      setProblems(result.items);
      setError(null);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Could not load problems.",
      );
    } finally {
      setLoading(false);
    }
  }, [difficulty, search, showArchived]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 200);
    return () => window.clearTimeout(timeout);
  }, [load]);

  async function addProblem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get("title") ?? "").trim();
    if (!title) return;
    setSubmitting(true);
    try {
      await createProblem({
        title,
        difficulty: String(form.get("difficulty")) as Difficulty,
        topics: String(form.get("topics") ?? "")
          .split(",")
          .map((topic) => topic.trim())
          .filter(Boolean),
      });
      event.currentTarget.reset();
      setDuplicateWarning(null);
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Could not add the problem.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function checkDuplicates(title: string) {
    if (title.trim().length < 2) return setDuplicateWarning(null);
    const matches = await findDuplicates(title);
    setDuplicateWarning(
      matches.length
        ? `Possible duplicate: ${matches[0].problem.title} (${matches[0].reason})`
        : null,
    );
  }

  async function toggleArchive(problem: Problem) {
    try {
      await setProblemArchived(problem.id, problem.archived_at === null);
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not update the problem.",
      );
    }
  }

  async function editProblem(problem: Problem) {
    const title = window.prompt("Problem title", problem.title)?.trim();
    if (!title || title === problem.title) return;
    try {
      await updateProblem(problem.id, { title });
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not edit the problem.",
      );
    }
  }

  return (
    <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_23rem]">
      <section>
        <div className="surface-card mb-6 flex flex-wrap items-center gap-3 p-3">
          <input
            type="search"
            aria-label="Search problems"
            className="min-h-11 min-w-64 flex-1 rounded-xl border-0 bg-slate-50 px-4 text-sm outline-none ring-1 ring-inset ring-slate-200 transition placeholder:text-slate-400 focus:bg-white focus:ring-2 focus:ring-emerald-600"
            placeholder="Search title or notes"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <select
            aria-label="Filter by difficulty"
            className="min-h-11 rounded-xl border-0 bg-slate-50 px-4 text-sm font-medium text-slate-700 outline-none ring-1 ring-inset ring-slate-200 focus:bg-white focus:ring-2 focus:ring-emerald-600"
            value={difficulty}
            onChange={(event) =>
              setDifficulty(event.target.value as Difficulty | "")
            }
          >
            <option value="">All difficulties</option>
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
          <label className="flex min-h-11 cursor-pointer items-center gap-2 rounded-xl px-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50">
            <input
              className="size-4 rounded border-slate-300 text-emerald-700 focus:ring-emerald-600"
              type="checkbox"
              checked={showArchived}
              onChange={(event) => setShowArchived(event.target.checked)}
            />
            Archived
          </label>
        </div>

        {error && (
          <p
            role="alert"
            className="mb-4 rounded-xl bg-red-50 p-4 text-red-800"
          >
            {error}
          </p>
        )}
        {loading ? (
          <p className="text-slate-500">Loading problems…</p>
        ) : problems.length === 0 ? (
          <div className="surface-card border-dashed p-12 text-center">
            <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-emerald-50 text-xl text-emerald-700">
              ＋
            </div>
            <h2 className="mt-4 text-xl font-semibold">No problems found</h2>
            <p className="mt-2 text-slate-500">
              Add your first problem or adjust the filters.
            </p>
          </div>
        ) : (
          <ul className="space-y-3">
            {problems.map((problem) => (
              <li
                key={problem.id}
                className="surface-card p-5 transition hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-[0_14px_32px_rgba(15,23,42,0.07)]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold tracking-tight text-slate-900">
                      {problem.title}
                    </h2>
                    <p className="mt-1 text-sm text-slate-500">
                      {problem.difficulty} · Priority {problem.priority}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="btn-quiet"
                      onClick={() => void editProblem(problem)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn-quiet"
                      onClick={() => void toggleArchive(problem)}
                    >
                      {problem.archived_at ? "Restore" : "Archive"}
                    </button>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {problem.topics.map((topic) => (
                    <span
                      key={topic.id}
                      className="rounded-full border border-emerald-100 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-800"
                    >
                      {topic.name}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <aside className="surface-card h-fit overflow-hidden lg:sticky lg:top-8">
        <div className="border-b border-slate-100 bg-gradient-to-br from-emerald-50 to-white px-6 py-5">
          <div className="flex size-10 items-center justify-center rounded-xl bg-emerald-700 text-xl text-white shadow-sm">
            ＋
          </div>
          <h2 className="mt-4 text-xl font-semibold tracking-tight">
            Add problem
          </h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Start with the essentials. You can add more detail later.
          </p>
        </div>
        <form
          className="space-y-5 p-6"
          onSubmit={(event) => void addProblem(event)}
        >
          <label className="field-label">
            Title
            <input
              required
              name="title"
              onBlur={(event) => void checkDuplicates(event.target.value)}
              placeholder="e.g. Merge Intervals"
              className="field-control"
            />
          </label>
          {duplicateWarning && (
            <p
              role="status"
              className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm leading-5 text-amber-900"
            >
              {duplicateWarning}. You can still keep both records.
            </p>
          )}
          <label className="field-label">
            Difficulty
            <select
              name="difficulty"
              defaultValue="UNKNOWN"
              className="field-control"
            >
              <option>UNKNOWN</option>
              <option>EASY</option>
              <option>MEDIUM</option>
              <option>HARD</option>
            </select>
          </label>
          <label className="field-label">
            Topics
            <input
              name="topics"
              placeholder="Arrays, Hash Table"
              className="field-control"
            />
            <span className="mt-2 block text-xs font-normal text-slate-400">
              Separate multiple topics with commas.
            </span>
          </label>
          <button disabled={submitting} className="btn-primary w-full">
            {submitting ? "Adding problem…" : "Add to library"}
          </button>
        </form>
      </aside>
    </div>
  );
}
