import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import QueuePage from "../app/queue/page";
import { generateQueue } from "../lib/queues";

vi.mock("../lib/problems", () => ({
  fetchTopics: vi.fn().mockResolvedValue([]),
  fetchProblems: vi.fn().mockResolvedValue({ items: [] }),
}));

vi.mock("../lib/queues", () => ({
  generateQueue: vi.fn().mockResolvedValue({
    id: "queue-1",
    available_minutes: 60,
    topic_focus_ids: [],
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
  updateQueueItem: vi.fn(),
}));

describe("QueuePage", () => {
  it("generates and explains a time-bounded queue", async () => {
    render(<QueuePage />);
    fireEvent.click(
      screen.getByRole("button", { name: "Generate daily queue" }),
    );
    await waitFor(() => expect(generateQueue).toHaveBeenCalled());
    expect(await screen.findByText("Course Schedule")).toBeVisible();
    expect(screen.getByText(/Overdue by 5 days/)).toBeVisible();
    expect(screen.getByText("1 problem · 35 of 60 minutes")).toBeVisible();
  });
});
