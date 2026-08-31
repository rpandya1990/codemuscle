"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  Attempt,
  AttemptOutcome,
  createAttempt,
  fetchAttempts,
} from "@/lib/attempts";

import {
  createProblem,
  clearScheduleOverride,
  Difficulty,
  fetchProblems,
  fetchTopics,
  findDuplicates,
  Problem,
  NamedReference,
  setProblemArchived,
  setScheduleOverride,
  updateProblem,
} from "@/lib/problems";

const PROBLEMS_PER_PAGE = 25;

export function ProblemLibrary() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [search, setSearch] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [difficulty, setDifficulty] = useState<Difficulty | "">("");
  const [topicId, setTopicId] = useState("");
  const [topics, setTopics] = useState<NamedReference[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [editing, setEditing] = useState<Problem | null>(null);
  const [attemptProblem, setAttemptProblem] = useState<Problem | null>(null);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [page, setPage] = useState(1);
  const totalPages = Math.max(
    1,
    Math.ceil(problems.length / PROBLEMS_PER_PAGE),
  );
  const visibleProblems = problems.slice(
    (page - 1) * PROBLEMS_PER_PAGE,
    page * PROBLEMS_PER_PAGE,
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchProblems(
        search,
        showArchived,
        difficulty || undefined,
        topicId || undefined,
      );
      setProblems(result.items);
      setPage((current) =>
        Math.min(
          current,
          Math.max(1, Math.ceil(result.items.length / PROBLEMS_PER_PAGE)),
        ),
      );
      setError(null);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Could not load problems.",
      );
    } finally {
      setLoading(false);
    }
  }, [difficulty, search, showArchived, topicId]);

  useEffect(() => {
    void fetchTopics()
      .then(setTopics)
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error ? reason.message : "Could not load topics.",
        ),
      );
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 200);
    return () => window.clearTimeout(timeout);
  }, [load]);

  async function addProblem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const title = String(form.get("title") ?? "").trim();
    if (!title) return;
    setSubmitting(true);
    try {
      await createProblem({
        title,
        url: String(form.get("url") ?? "").trim() || undefined,
        difficulty: String(form.get("difficulty")) as Difficulty,
        notes: String(form.get("notes") ?? "").trim() || undefined,
        topics: String(form.get("topics") ?? "")
          .split(",")
          .map((topic) => topic.trim())
          .filter(Boolean),
        patterns: String(form.get("patterns") ?? "")
          .split(",")
          .map((pattern) => pattern.trim())
          .filter(Boolean),
      });
      formElement.reset();
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

  async function editProblem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const form = new FormData(event.currentTarget);
    setSubmitting(true);
    try {
      await updateProblem(editing.id, {
        title: String(form.get("title") ?? "").trim(),
        url: String(form.get("url") ?? "").trim() || null,
        difficulty: String(form.get("difficulty")) as Difficulty,
        notes: String(form.get("notes") ?? "").trim() || null,
        patterns: String(form.get("patterns") ?? "")
          .split(",")
          .map((pattern) => pattern.trim())
          .filter(Boolean),
      });
      const revisionDate = String(form.get("next_revision_date") ?? "");
      if (revisionDate && revisionDate !== editing.next_revision_date) {
        await setScheduleOverride(editing.id, revisionDate);
      }
      setEditing(null);
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not edit the problem.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function removeScheduleOverride(problem: Problem) {
    try {
      await clearScheduleOverride(problem.id);
      setEditing(null);
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not clear the override.",
      );
    }
  }

  async function openAttempts(problem: Problem) {
    setAttemptProblem(problem);
    try {
      setAttempts(await fetchAttempts(problem.id));
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not load attempt history.",
      );
    }
  }

  async function recordAttempt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!attemptProblem) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setSubmitting(true);
    try {
      const outcome = String(form.get("outcome")) as AttemptOutcome;
      await createAttempt(attemptProblem.id, {
        outcome,
        time_spent_minutes: form.get("time_spent_minutes")
          ? Number(form.get("time_spent_minutes"))
          : null,
        notes: String(form.get("notes") ?? "").trim() || null,
      });
      setAttemptProblem(null);
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not record the attempt.",
      );
    } finally {
      setSubmitting(false);
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
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
          <select
            aria-label="Filter by difficulty"
            className="min-h-11 rounded-xl border-0 bg-slate-50 px-4 text-sm font-medium text-slate-700 outline-none ring-1 ring-inset ring-slate-200 focus:bg-white focus:ring-2 focus:ring-emerald-600"
            value={difficulty}
            onChange={(event) => {
              setDifficulty(event.target.value as Difficulty | "");
              setPage(1);
            }}
          >
            <option value="">All difficulties</option>
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
          <select
            aria-label="Filter by topic"
            className="min-h-11 rounded-xl border-0 bg-slate-50 px-4 text-sm font-medium text-slate-700 outline-none ring-1 ring-inset ring-slate-200 focus:bg-white focus:ring-2 focus:ring-emerald-600"
            value={topicId}
            onChange={(event) => {
              setTopicId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All topics</option>
            {topics.map((topic) => (
              <option key={topic.id} value={topic.id}>
                {topic.name}
              </option>
            ))}
          </select>
          <label className="flex min-h-11 cursor-pointer items-center gap-2 rounded-xl px-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50">
            <input
              className="size-4 rounded border-slate-300 text-emerald-700 focus:ring-emerald-600"
              type="checkbox"
              checked={showArchived}
              onChange={(event) => {
                setShowArchived(event.target.checked);
                setPage(1);
              }}
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
          <div>
            <ul className="space-y-3">
              {visibleProblems.map((problem) => (
                <li
                  key={problem.id}
                  className="surface-card p-5 transition hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-[0_14px_32px_rgba(15,23,42,0.07)]"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h2 className="text-lg font-semibold tracking-tight text-slate-900">
                        {problem.title}
                      </h2>
                      {problem.url ? (
                        <a
                          href={problem.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`Open ${problem.title} problem link (opens in a new tab)`}
                          title="Open problem link"
                          className="mt-1 inline-flex size-8 items-center justify-center rounded-lg text-emerald-700 transition hover:bg-emerald-50 hover:text-emerald-900 focus:outline-none focus:ring-2 focus:ring-emerald-600"
                        >
                          <LinkIcon />
                        </a>
                      ) : (
                        <span
                          role="img"
                          aria-label={`No problem link available for ${problem.title}`}
                          title="No problem link available"
                          className="mt-1 inline-flex size-8 items-center justify-center rounded-lg text-slate-300"
                        >
                          <LinkIcon />
                        </span>
                      )}
                      <p className="mt-1 text-sm text-slate-500">
                        {problem.difficulty} · {problem.current_mastery_state} ·{" "}
                        {problem.total_attempts} attempts
                      </p>
                      {problem.next_revision_date && (
                        <p className="mt-1 text-sm text-slate-500">
                          Next revision: {problem.next_revision_date}
                          {problem.next_revision_overridden
                            ? " · Manually set"
                            : " · Calculated"}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => void openAttempts(problem)}
                      >
                        Record attempt
                      </button>
                      <button
                        type="button"
                        className="btn-quiet"
                        onClick={() => setEditing(problem)}
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
            <nav
              className="mt-6 flex flex-wrap items-center justify-between gap-3"
              aria-label="Problem pagination"
            >
              <p className="text-sm text-slate-500">
                Showing {(page - 1) * PROBLEMS_PER_PAGE + 1}–
                {Math.min(page * PROBLEMS_PER_PAGE, problems.length)} of{" "}
                {problems.length}
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="btn-quiet"
                  disabled={page === 1}
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                >
                  Previous
                </button>
                <span className="px-2 text-sm font-medium text-slate-600">
                  Page {page} of {totalPages}
                </span>
                <button
                  type="button"
                  className="btn-quiet"
                  disabled={page === totalPages}
                  onClick={() =>
                    setPage((current) => Math.min(totalPages, current + 1))
                  }
                >
                  Next
                </button>
              </div>
            </nav>
          </div>
        )}
      </section>

      <aside className="surface-card h-fit overflow-hidden lg:sticky lg:top-8 lg:flex lg:max-h-[calc(100vh-4rem)] lg:flex-col">
        <div className="shrink-0 border-b border-slate-100 bg-gradient-to-br from-emerald-50 to-white px-6 py-5">
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
          className="lg:flex lg:min-h-0 lg:flex-1 lg:flex-col"
          onSubmit={(event) => void addProblem(event)}
        >
          <div className="space-y-5 p-6 lg:min-h-0 lg:flex-1 lg:overflow-y-auto">
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
              Problem link{" "}
              <span className="font-normal text-slate-400">(optional)</span>
              <input
                type="url"
                name="url"
                placeholder="https://leetcode.com/problems/merge-intervals"
                className="field-control"
              />
            </label>
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
              Notes{" "}
              <span className="font-normal text-slate-400">(optional)</span>
              <textarea
                name="notes"
                rows={4}
                placeholder="Key insight, edge cases, or reminders"
                className="field-control resize-y"
              />
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
            <label className="field-label">
              Patterns{" "}
              <span className="font-normal text-slate-400">(optional)</span>
              <input
                name="patterns"
                placeholder="Sliding Window, Two Pointers"
                className="field-control"
              />
              <span className="mt-2 block text-xs font-normal text-slate-400">
                Separate multiple patterns with commas.
              </span>
            </label>
          </div>
          <div className="shrink-0 border-t border-slate-100 bg-white p-4">
            <button disabled={submitting} className="btn-primary w-full">
              {submitting ? "Adding problem…" : "Add to library"}
            </button>
          </div>
        </form>
      </aside>

      {editing && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setEditing(null);
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="edit-problem-title"
            className="surface-card max-h-[90vh] w-full max-w-xl overflow-y-auto p-6 shadow-2xl"
          >
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <h2 id="edit-problem-title" className="text-xl font-semibold">
                  Edit problem
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Update the problem details used in your library.
                </p>
              </div>
              <button
                className="btn-quiet"
                type="button"
                onClick={() => setEditing(null)}
              >
                Close
              </button>
            </div>
            <form
              className="space-y-5"
              onSubmit={(event) => void editProblem(event)}
            >
              <label className="field-label">
                Title
                <input
                  required
                  name="title"
                  defaultValue={editing.title}
                  className="field-control"
                />
              </label>
              <label className="field-label">
                Problem link
                <input
                  type="url"
                  name="url"
                  defaultValue={editing.url ?? ""}
                  className="field-control"
                />
              </label>
              <label className="field-label">
                Difficulty
                <select
                  name="difficulty"
                  defaultValue={editing.difficulty}
                  className="field-control"
                >
                  <option value="UNKNOWN">Unknown</option>
                  <option value="EASY">Easy</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HARD">Hard</option>
                </select>
              </label>
              <label className="field-label">
                Notes{" "}
                <span className="font-normal text-slate-400">(optional)</span>
                <textarea
                  name="notes"
                  rows={5}
                  defaultValue={editing.notes ?? ""}
                  className="field-control resize-y"
                />
              </label>
              <label className="field-label">
                Patterns{" "}
                <span className="font-normal text-slate-400">(optional)</span>
                <input
                  name="patterns"
                  defaultValue={editing.patterns
                    .map((pattern) => pattern.name)
                    .join(", ")}
                  className="field-control"
                />
              </label>
              <label className="field-label">
                Next revision date
                <input
                  type="date"
                  name="next_revision_date"
                  defaultValue={editing.next_revision_date ?? ""}
                  className="field-control"
                />
                <span className="mt-2 block text-xs font-normal text-slate-400">
                  Changing this creates a visible manual override.
                </span>
              </label>
              {editing.next_revision_overridden && (
                <button
                  type="button"
                  className="btn-secondary w-full"
                  onClick={() => void removeScheduleOverride(editing)}
                >
                  Use calculated date
                </button>
              )}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  className="btn-quiet"
                  onClick={() => setEditing(null)}
                >
                  Cancel
                </button>
                <button disabled={submitting} className="btn-primary">
                  {submitting ? "Saving…" : "Save changes"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}

      {attemptProblem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="attempt-title"
            className="surface-card max-h-[92vh] w-full max-w-3xl overflow-y-auto p-6 shadow-2xl"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="attempt-title" className="text-xl font-semibold">
                  Record attempt
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {attemptProblem.title}
                </p>
              </div>
              <button
                type="button"
                className="btn-quiet"
                onClick={() => setAttemptProblem(null)}
              >
                Close
              </button>
            </div>
            <form
              className="mt-6 grid gap-5 sm:grid-cols-2"
              onSubmit={(event) => void recordAttempt(event)}
            >
              <label className="field-label">
                Outcome
                <select
                  name="outcome"
                  className="field-control"
                  defaultValue="SOLVED_INDEPENDENTLY"
                >
                  <option value="SOLVED_INDEPENDENTLY">
                    Solved independently
                  </option>
                  <option value="SOLVED_SMALL_HINT">
                    Solved with small hint
                  </option>
                  <option value="SOLVED_SIGNIFICANT_HELP">
                    Solved with significant help
                  </option>
                  <option value="UNDERSTOOD_AFTER_SOLUTION">
                    Understood after solution
                  </option>
                  <option value="FAILED">Failed</option>
                  <option value="SKIPPED">Skipped</option>
                </select>
              </label>
              <label className="field-label">
                Time spent (minutes)
                <input
                  type="number"
                  min="0"
                  max="1440"
                  name="time_spent_minutes"
                  className="field-control"
                />
              </label>
              <label className="field-label sm:col-span-2">
                Notes
                <textarea
                  name="notes"
                  rows={3}
                  className="field-control resize-y"
                />
              </label>
              <button
                disabled={submitting}
                className="btn-primary sm:col-span-2"
              >
                {submitting ? "Recording…" : "Record attempt"}
              </button>
            </form>
            <div className="mt-8 border-t border-slate-200 pt-6">
              <h3 className="font-semibold">Attempt history</h3>
              {attempts.length === 0 ? (
                <p className="mt-3 text-sm text-slate-500">
                  No attempts recorded yet.
                </p>
              ) : (
                <ol className="mt-3 space-y-3">
                  {attempts.map((attempt) => (
                    <li
                      key={attempt.id}
                      className="rounded-xl border border-slate-200 p-4"
                    >
                      <div className="flex flex-wrap justify-between gap-2 text-sm">
                        <strong>{attempt.outcome.replaceAll("_", " ")}</strong>
                        <time className="text-slate-500">
                          {new Date(attempt.attempted_at).toLocaleString()}
                        </time>
                      </div>
                      <p className="mt-2 text-sm text-slate-600">
                        {attempt.previous_mastery_state} →{" "}
                        {attempt.calculated_mastery_state}
                      </p>
                      <p className="mt-2 text-sm text-slate-500">
                        {attempt.schedule_explanation}
                      </p>
                      {attempt.notes && (
                        <p className="mt-2 text-sm text-slate-700">
                          {attempt.notes}
                        </p>
                      )}
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function LinkIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="size-4"
    >
      <path d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1" />
      <path d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.1-1.1" />
    </svg>
  );
}
