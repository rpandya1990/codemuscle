"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  fetchProblems,
  fetchTopics,
  NamedReference,
  Problem,
} from "@/lib/problems";
import {
  addQueueItem,
  DailyQueue as Queue,
  generateQueue,
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
                      onClick={() =>
                        void mutate(() =>
                          updateQueueItem(queue.id, item.id, "COMPLETED"),
                        )
                      }
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
    </div>
  );
}
