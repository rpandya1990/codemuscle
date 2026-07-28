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
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Could not add the problem.",
      );
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
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <section>
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <input
            type="search"
            aria-label="Search problems"
            className="min-w-64 flex-1 rounded-xl border border-slate-300 px-4 py-3"
            placeholder="Search title or notes"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <select
            aria-label="Filter by difficulty"
            className="rounded-xl border border-slate-300 px-4 py-3"
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
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
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
          <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center">
            <h2 className="text-xl font-semibold">No problems found</h2>
            <p className="mt-2 text-slate-500">
              Add your first problem or adjust the filters.
            </p>
          </div>
        ) : (
          <ul className="space-y-3">
            {problems.map((problem) => (
              <li
                key={problem.id}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold">{problem.title}</h2>
                    <p className="mt-1 text-sm text-slate-500">
                      {problem.difficulty} · Priority {problem.priority}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      className="rounded-lg border px-3 py-2 text-sm"
                      onClick={() => void editProblem(problem)}
                    >
                      Edit
                    </button>
                    <button
                      className="rounded-lg border px-3 py-2 text-sm"
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
                      className="rounded-full bg-emerald-50 px-3 py-1 text-xs text-emerald-800"
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

      <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold">Add problem</h2>
        <form
          className="mt-5 space-y-4"
          onSubmit={(event) => void addProblem(event)}
        >
          <label className="block text-sm font-medium">
            Title
            <input
              required
              name="title"
              onBlur={(event) => void checkDuplicates(event.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2"
            />
          </label>
          {duplicateWarning && (
            <p
              role="status"
              className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900"
            >
              {duplicateWarning}. You can still keep both records.
            </p>
          )}
          <label className="block text-sm font-medium">
            Difficulty
            <select
              name="difficulty"
              defaultValue="UNKNOWN"
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2"
            >
              <option>UNKNOWN</option>
              <option>EASY</option>
              <option>MEDIUM</option>
              <option>HARD</option>
            </select>
          </label>
          <label className="block text-sm font-medium">
            Topics
            <input
              name="topics"
              placeholder="Arrays, Hash Table"
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2"
            />
          </label>
          <button className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white">
            Add to library
          </button>
        </form>
      </aside>
    </div>
  );
}
