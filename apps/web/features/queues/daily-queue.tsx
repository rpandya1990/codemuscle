"use client";

import { FormEvent, useEffect, useState } from "react";

import { AttemptOutcome, createAttempt, HintUsage } from "@/lib/attempts";
import {
  Difficulty,
  fetchProblems,
  fetchTopics,
  NamedReference,
  Problem,
} from "@/lib/problems";
import {
  addQueueItem,
  DailyQueue as Queue,
  generateQueue,
  QueueItem,
  removeQueueItem,
  replaceQueueItem,
  updateQueueItem,
} from "@/lib/queues";

export function DailyQueue() {
  const [queue, setQueue] = useState<Queue | null>(null);
  const [topics, setTopics] = useState<NamedReference[]>([]);
  const [problems, setProblems] = useState<Problem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [completingItem, setCompletingItem] = useState<QueueItem | null>(null);
  const [attemptRecordedForItemId, setAttemptRecordedForItemId] = useState<
    string | null
  >(null);

  useEffect(() => {
    void Promise.all([fetchTopics(), fetchProblems("", false)]).then(
      ([topicList, problemList]) => {
        setTopics(topicList);
        setProblems(problemList.items);
      },
    );
  }, []);

  async function generate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setWorking(true);
    try {
      setQueue(
        await generateQueue({
          available_minutes: Number(form.get("available_minutes")),
          topic_focus_ids: form.get("topic_id")
            ? [String(form.get("topic_id"))]
            : [],
          difficulty_focus: form
            .getAll("difficulty")
            .map((value) => String(value) as Difficulty),
          requested_problem_count: form.get("problem_count")
            ? Number(form.get("problem_count"))
            : null,
        }),
      );
      setError(null);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not generate the queue.",
      );
    } finally {
      setWorking(false);
    }
  }

  async function mutate(action: () => Promise<Queue>) {
    setWorking(true);
    try {
      setQueue(await action());
      setError(null);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not update the queue.",
      );
    } finally {
      setWorking(false);
    }
  }

  async function completeWithAttempt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!queue || !completingItem) return;
    const form = new FormData(event.currentTarget);
    const complexityUnderstood = String(
      form.get("complexity_understood") ?? "",
    );
    setWorking(true);
    try {
      if (attemptRecordedForItemId !== completingItem.id) {
        await createAttempt(completingItem.problem.id, {
          outcome: String(form.get("outcome")) as AttemptOutcome,
          hint_usage: String(form.get("hint_usage")) as HintUsage,
          time_spent_minutes: form.get("time_spent_minutes")
            ? Number(form.get("time_spent_minutes"))
            : null,
          confidence: form.get("confidence")
            ? Number(form.get("confidence"))
            : null,
          notes: String(form.get("notes") ?? "").trim() || null,
          complexity_understood: complexityUnderstood
            ? complexityUnderstood === "yes"
            : null,
        });
        setAttemptRecordedForItemId(completingItem.id);
      }
      setQueue(
        await updateQueueItem(queue.id, completingItem.id, "COMPLETED"),
      );
      setCompletingItem(null);
      setAttemptRecordedForItemId(null);
      setError(null);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not record the attempt and complete the problem.",
      );
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="grid items-start gap-8 lg:grid-cols-[20rem_minmax(0,1fr)]">
      <form
        className="surface-card space-y-5 p-6 lg:sticky lg:top-8"
        onSubmit={(event) => void generate(event)}
      >
        <h2 className="text-xl font-semibold">Plan a session</h2>
        <label className="field-label">
          Available minutes
          <input
            required
            type="number"
            min="5"
            max="720"
            name="available_minutes"
            defaultValue="60"
            className="field-control"
          />
        </label>
        <fieldset>
          <legend className="field-label">Problem difficulty</legend>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {(["EASY", "MEDIUM", "HARD", "UNKNOWN"] as Difficulty[]).map(
              (value) => (
                <label
                  key={value}
                  className="flex cursor-pointer items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 ring-1 ring-inset ring-slate-200"
                >
                  <input
                    type="checkbox"
                    name="difficulty"
                    value={value}
                    className="size-4 rounded border-slate-300 text-emerald-700 focus:ring-emerald-600"
                  />
                  {value.charAt(0) + value.slice(1).toLowerCase()}
                </label>
              ),
            )}
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Select any combination, or leave all unchecked to include every
            difficulty.
          </p>
        </fieldset>
        <label className="field-label">
          Topic focus{" "}
          <span className="font-normal text-slate-400">(optional)</span>
          <select name="topic_id" className="field-control" defaultValue="">
            <option value="">Balanced topics</option>
            {topics.map((topic) => (
              <option key={topic.id} value={topic.id}>
                {topic.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field-label">
          Problem count{" "}
          <span className="font-normal text-slate-400">(optional)</span>
          <input
            type="number"
            min="1"
            max="100"
            name="problem_count"
            className="field-control"
          />
        </label>
        <button className="btn-primary w-full" disabled={working}>
          {working ? "Building queue…" : "Generate daily queue"}
        </button>
      </form>

      <section>
        {error && (
          <p
            role="alert"
            className="mb-4 rounded-xl bg-red-50 p-4 text-red-800"
          >
            {error}
          </p>
        )}
        {!queue ? (
          <div className="surface-card border-dashed p-12 text-center text-slate-500">
            Choose your available time to create a deterministic revision plan.
          </div>
        ) : (
          <>
            <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="text-2xl font-semibold">Today’s queue</h2>
                <p className="mt-1 text-slate-500">
                  {queue.items.length}{" "}
                  {queue.items.length === 1 ? "problem" : "problems"} ·{" "}
                  {queue.total_estimated_minutes} of {queue.available_minutes}{" "}
                  minutes
                </p>
              </div>
              <form
                className="flex gap-2"
                onSubmit={(event) => {
                  event.preventDefault();
                  const problemId = String(
                    new FormData(event.currentTarget).get("problem_id"),
                  );
                  if (problemId)
                    void mutate(() => addQueueItem(queue.id, problemId));
                }}
              >
                <select
                  name="problem_id"
                  aria-label="Problem to add"
                  className="field-control mt-0"
                  defaultValue=""
                >
                  <option value="">Add a problem…</option>
                  {problems.map((problem) => (
                    <option key={problem.id} value={problem.id}>
                      {problem.title}
                    </option>
                  ))}
                </select>
                <button className="btn-secondary">Add</button>
              </form>
            </div>
            <ol className="space-y-4">
              {queue.items.map((item) => (
                <li
                  key={item.id}
                  className={`surface-card p-5 ${item.status === "COMPLETED" ? "opacity-60" : ""}`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                        #{item.position} · {item.estimated_duration_minutes} min
                      </p>
                      <h3 className="mt-1 text-lg font-semibold">
                        {item.problem.title}
                      </h3>
                      <p className="mt-1 text-sm text-slate-500">
                        {item.problem.difficulty} ·{" "}
                        {item.problem.current_mastery_state}
                      </p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold">
                      {item.status}
                    </span>
                  </div>
                  <ul className="mt-4 space-y-1 text-sm text-slate-600">
                    {item.recommendation_reasons.map((reason) => (
                      <li key={reason}>• {reason}</li>
                    ))}
                  </ul>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={working || item.status === "COMPLETED"}
                      onClick={() => {
                        setAttemptRecordedForItemId(null);
                        setCompletingItem(item);
                      }}
                    >
                      Complete
                    </button>
                    <button
                      type="button"
                      className="btn-quiet"
                      disabled={working}
                      onClick={() =>
                        void mutate(() =>
                          updateQueueItem(queue.id, item.id, "POSTPONED"),
                        )
                      }
                    >
                      Postpone
                    </button>
                    <button
                      type="button"
                      className="btn-quiet"
                      disabled={working}
                      onClick={() =>
                        void mutate(() => replaceQueueItem(queue.id, item.id))
                      }
                    >
                      Replace
                    </button>
                    <button
                      type="button"
                      className="btn-quiet text-red-700"
                      disabled={working}
                      onClick={() =>
                        void mutate(() => removeQueueItem(queue.id, item.id))
                      }
                    >
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ol>
          </>
        )}
      </section>

      {completingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="queue-attempt-title"
            className="surface-card max-h-[92vh] w-full max-w-3xl overflow-y-auto p-6 shadow-2xl"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2
                  id="queue-attempt-title"
                  className="text-xl font-semibold"
                >
                  Record attempt
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {completingItem.problem.title}
                </p>
              </div>
              <button
                type="button"
                className="btn-quiet"
                disabled={working}
                onClick={() => {
                  setCompletingItem(null);
                  setAttemptRecordedForItemId(null);
                }}
              >
                Close
              </button>
            </div>
            <form
              className="mt-6 grid gap-5 sm:grid-cols-2"
              onSubmit={(event) => void completeWithAttempt(event)}
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
                Hint usage
                <select
                  name="hint_usage"
                  className="field-control"
                  defaultValue="NONE"
                >
                  <option value="NONE">None</option>
                  <option value="SMALL">Small</option>
                  <option value="SIGNIFICANT">Significant</option>
                  <option value="SOLUTION_VIEWED">Solution viewed</option>
                  <option value="NOT_APPLICABLE">Not applicable</option>
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
              <label className="field-label">
                Confidence (1–5)
                <input
                  type="number"
                  min="1"
                  max="5"
                  name="confidence"
                  className="field-control"
                />
              </label>
              <label className="field-label">
                Complexity understood
                <select
                  name="complexity_understood"
                  className="field-control"
                  defaultValue=""
                >
                  <option value="">Not recorded</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
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
                disabled={working}
                className="btn-primary sm:col-span-2"
              >
                {working ? "Recording…" : "Record attempt and complete"}
              </button>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
