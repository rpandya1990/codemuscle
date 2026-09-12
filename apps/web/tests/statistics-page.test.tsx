import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { fetchTrends } from "../lib/statistics";

import StatisticsPage from "../app/statistics/page";

vi.mock("../lib/statistics", () => ({
  fetchTopicStatistics: vi.fn().mockResolvedValue([
    {
      id: "graphs",
      name: "Graphs",
      status: "WEAK",
      total_problems: 4,
      independently_solved_problems: 1,
      health_rate: 0.25,
      total_attempts: 5,
      independent_success_rate: 0.4,
      failed_attempt_rate: 0.4,
      status_reasons: ["Independent success rate is below 50%"],
    },
  ]),
  fetchTopicTotals: vi.fn().mockResolvedValue({
    id: "total",
    name: "All topics",
    total_problems: 6,
    independently_solved_problems: 3,
    health_rate: 0.5,
    total_attempts: 10,
    independent_successes: 7,
    independent_success_rate: 0.7,
    failed_attempt_rate: 0.2,
    status_reasons: [],
  }),
  fetchTrends: vi.fn().mockResolvedValue({
    points: [
      {
        period_start: "2026-07-27",
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
    expect(screen.getByText("All topics")).toBeVisible();
    const totalRow = screen.getByText("All topics").closest("tr");
    expect(totalRow).not.toBeNull();
    expect(within(totalRow!).getByText("50%")).toBeVisible();
    expect(within(totalRow!).getByText("3 of 6 problems")).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "Health" })).toBeVisible();
    const topicRow = screen.getByText("Graphs").closest("tr")!;
    expect(within(topicRow).getByText("25%")).toBeVisible();
    expect(within(topicRow).getByText("1 of 4 problems")).toBeVisible();
    fireEvent.change(screen.getByLabelText("Number of weeks"), {
      target: { value: "5" },
    });
    await waitFor(() =>
      expect(fetchTrends).toHaveBeenLastCalledWith("week", 5),
    );
    for (const interval of ["day", "month", "year"]) {
      fireEvent.change(screen.getByLabelText("Group by"), {
        target: { value: interval },
      });
      await waitFor(() =>
        expect(fetchTrends).toHaveBeenLastCalledWith(interval, 5),
      );
      expect(screen.getByLabelText(`Number of ${interval}s`)).toHaveValue(5);
    }
    const calls = vi.mocked(fetchTrends).mock.calls.length;
    fireEvent.change(screen.getByLabelText("Number of years"), {
      target: { value: "" },
    });
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a whole number");
    expect(vi.mocked(fetchTrends).mock.calls).toHaveLength(calls);
    fireEvent.click(screen.getByLabelText("All time"));
    await waitFor(() =>
      expect(fetchTrends).toHaveBeenLastCalledWith("year", 0),
    );
    expect(screen.getByText("WEAK")).toBeVisible();
    expect(
      screen.getByText("Independent success rate is below 50%"),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Practice trend" }),
    ).toBeVisible();
  });
});
