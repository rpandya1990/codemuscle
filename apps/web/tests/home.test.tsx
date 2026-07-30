import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import HomePage from "../app/page";

vi.mock("../lib/statistics", () => ({
  fetchDashboard: vi.fn().mockResolvedValue({
    total_active_problems: 10,
    due_today: 2,
    overdue: 1,
    practiced_this_week: 3,
    mastered: 4,
    needs_relearning: 1,
    recent_activity: [],
  }),
  fetchWeakAreas: vi.fn().mockResolvedValue([]),
}));

describe("HomePage", () => {
  it("states the primary product promise and loads dashboard statistics", async () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: /know what to revise today/i }),
    ).toBeVisible();
    expect(await screen.findByText("Due today")).toBeVisible();
    expect(screen.getByText("2")).toBeVisible();
  });
});
