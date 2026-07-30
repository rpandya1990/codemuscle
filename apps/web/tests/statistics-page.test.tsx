import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import StatisticsPage from "../app/statistics/page";

vi.mock("../lib/statistics", () => ({
  fetchTopicStatistics: vi.fn().mockResolvedValue([
    {
      id: "graphs",
      name: "Graphs",
      status: "WEAK",
      total_problems: 4,
      total_attempts: 5,
      independent_success_rate: 0.4,
      failed_attempt_rate: 0.4,
      status_reasons: ["Independent success rate is below 50%"],
    },
  ]),
  fetchPatternStatistics: vi.fn().mockResolvedValue([]),
  fetchTrends: vi.fn().mockResolvedValue({
    points: [
      {
        week_start: "2026-07-27",
        attempts: 3,
        independent_successes: 2,
        failures: 1,
      },
    ],
  }),
}));

describe("StatisticsPage", () => {
  it("shows deterministic area classifications and trends", async () => {
    render(<StatisticsPage />);
    expect(await screen.findByText("Graphs")).toBeVisible();
    expect(screen.getByText("WEAK")).toBeVisible();
    expect(
      screen.getByText("Independent success rate is below 50%"),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Practice trend" }),
    ).toBeVisible();
  });
});
