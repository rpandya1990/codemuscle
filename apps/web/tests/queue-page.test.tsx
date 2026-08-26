import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import QueuePage from "../app/queue/page";
import { createAttempt } from "../lib/attempts";
import { generateQueue, updateQueueItem } from "../lib/queues";

vi.mock("../lib/attempts", () => ({
  createAttempt: vi.fn().mockResolvedValue({}),
}));

vi.mock("../lib/problems", () => ({
  fetchTopics: vi.fn().mockResolvedValue([]),
  fetchProblems: vi.fn().mockResolvedValue({ items: [] }),
}));

vi.mock("../lib/queues", () => ({
  generateQueue: vi.fn().mockResolvedValue({
    id: "queue-1",
    available_minutes: 60,
    topic_focus_ids: [],
    difficulty_focus: [],
    requested_problem_count: null,
    status: "ACTIVE",
    created_at: "2026-07-28T12:00:00Z",
    total_estimated_minutes: 35,
    items: [
      {
        id: "item-1",
        position: 1,
        estimated_duration_minutes: 35,
        recommendation_score: 100,
        recommendation_reasons: ["Overdue by 5 days"],
        status: "PENDING",
        problem: {
          id: "problem-1",
          title: "Course Schedule",
          difficulty: "MEDIUM",
          current_mastery_state: "FRAGILE",
        },
      },
    ],
  }),
  addQueueItem: vi.fn(),
  removeQueueItem: vi.fn(),
  replaceQueueItem: vi.fn(),
  updateQueueItem: vi.fn().mockResolvedValue({
    id: "queue-1",
    available_minutes: 60,
    topic_focus_ids: [],
    difficulty_focus: [],
    requested_problem_count: null,
    status: "ACTIVE",
    created_at: "2026-07-28T12:00:00Z",
    total_estimated_minutes: 35,
    items: [],
  }),
}));

describe("QueuePage", () => {
  it("generates and explains a time-bounded queue", async () => {
    render(<QueuePage />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Easy" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Hard" }));
    fireEvent.click(
      screen.getByRole("button", { name: "Generate daily queue" }),
    );
    await waitFor(() =>
      expect(generateQueue).toHaveBeenCalledWith({
        available_minutes: 60,
        topic_focus_ids: [],
        difficulty_focus: ["EASY", "HARD"],
        requested_problem_count: null,
      }),
    );
    expect(await screen.findByText("Course Schedule")).toBeVisible();
    expect(screen.getByText(/Overdue by 5 days/)).toBeVisible();
    expect(screen.getByText("1 problem · 35 of 60 minutes")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Complete" }));
    expect(
      await screen.findByRole("dialog", { name: "Record attempt" }),
    ).toBeVisible();
    fireEvent.change(screen.getByRole("combobox", { name: "Outcome" }), {
      target: { value: "SOLVED_SMALL_HINT" },
    });
    fireEvent.change(screen.getByRole("combobox", { name: "Hint usage" }), {
      target: { value: "SMALL" },
    });
    fireEvent.change(
      screen.getByRole("spinbutton", { name: "Confidence (1–5)" }),
      { target: { value: "4" } },
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Record attempt and complete" }),
    );

    await waitFor(() =>
      expect(createAttempt).toHaveBeenCalledWith("problem-1", {
        outcome: "SOLVED_SMALL_HINT",
        hint_usage: "SMALL",
        time_spent_minutes: null,
        confidence: 4,
        notes: null,
        complexity_understood: null,
      }),
    );
    expect(updateQueueItem).toHaveBeenCalledWith(
      "queue-1",
      "item-1",
      "COMPLETED",
    );
  });
});
