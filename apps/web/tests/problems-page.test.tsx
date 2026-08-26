import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ProblemsPage from "../app/problems/page";
import { fetchProblems } from "../lib/problems";

vi.mock("../lib/problems", () => ({
  fetchProblems: vi
    .fn()
    .mockResolvedValue({ items: [], total: 0, page: 1, page_size: 25 }),
  createProblem: vi.fn(),
  clearScheduleOverride: vi.fn(),
  fetchTopics: vi.fn().mockResolvedValue([
    { id: "arrays", name: "Arrays" },
    { id: "graphs", name: "Graphs" },
  ]),
  findDuplicates: vi.fn().mockResolvedValue([]),
  setProblemArchived: vi.fn(),
  setScheduleOverride: vi.fn(),
  updateProblem: vi.fn(),
}));

vi.mock("../lib/attempts", () => ({
  createAttempt: vi.fn(),
  fetchAttempts: vi.fn().mockResolvedValue([]),
}));

describe("ProblemsPage", () => {
  it("renders library controls", async () => {
    render(<ProblemsPage />);
    expect(
      screen.getByRole("heading", { name: "Coding problems" }),
    ).toBeVisible();
    expect(screen.getByRole("heading", { name: "Add problem" })).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Add to library" }),
    ).toBeVisible();
    expect(
      screen.getByRole("textbox", { name: /Problem link/ }),
    ).not.toBeRequired();
    expect(screen.getByRole("textbox", { name: /Notes/ })).toBeVisible();
    expect(screen.getByRole("textbox", { name: /Patterns/ })).toBeVisible();
    expect(
      screen.getByRole("combobox", { name: "Filter by topic" }),
    ).toBeVisible();
    expect(
      screen.getByRole("searchbox", { name: "Search problems" }),
    ).toBeVisible();

    fireEvent.change(
      await screen.findByRole("combobox", { name: "Filter by topic" }),
      { target: { value: "arrays" } },
    );
    await waitFor(() =>
      expect(fetchProblems).toHaveBeenLastCalledWith(
        "",
        false,
        undefined,
        "arrays",
      ),
    );
  });

  it("paginates the complete problem list in the browser", async () => {
    vi.mocked(fetchProblems).mockResolvedValueOnce({
      items: Array.from({ length: 26 }, (_, index) => ({
        id: String(index + 1),
        title: `Problem ${index + 1}`,
        url: null,
        platform: null,
        difficulty: "UNKNOWN" as const,
        notes: null,
        priority: 3,
        total_attempts: 0,
        successful_revision_streak: 0,
        next_revision_date: null,
        calculated_next_revision_date: null,
        next_revision_overridden: false,
        current_mastery_state: "NEW",
        archived_at: null,
        topics: [],
        patterns: [],
      })),
      total: 26,
      page: 1,
      page_size: 5000,
    });

    render(<ProblemsPage />);
    expect(await screen.findByText("Showing 1–25 of 26")).toBeVisible();
    expect(screen.queryByText("Problem 26")).not.toBeInTheDocument();
    fireEvent.click(
      screen.getAllByRole("button", { name: "Record attempt" })[0],
    );
    expect(
      await screen.findByRole("dialog", { name: "Record attempt" }),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(screen.getByText("Showing 26–26 of 26")).toBeVisible();
    expect(screen.getByText("Problem 26")).toBeVisible();
  });

  it("shows a problem's link when one is available", async () => {
    vi.mocked(fetchProblems).mockResolvedValueOnce({
      items: [
        {
          id: "two-sum",
          title: "Two Sum",
          url: "https://leetcode.com/problems/two-sum/",
          platform: "LeetCode",
          difficulty: "EASY",
          notes: null,
          priority: 3,
          total_attempts: 0,
          successful_revision_streak: 0,
          next_revision_date: null,
          calculated_next_revision_date: null,
          next_revision_overridden: false,
          current_mastery_state: "NEW",
          archived_at: null,
          topics: [],
          patterns: [],
        },
      ],
      total: 1,
      page: 1,
      page_size: 5000,
    });

    render(<ProblemsPage />);

    const problemLink = await screen.findByRole("link", {
      name: "Open Two Sum problem link (opens in a new tab)",
    });
    expect(problemLink).toBeVisible();
    expect(problemLink).toHaveAttribute(
      "href",
      "https://leetcode.com/problems/two-sum/",
    );
    expect(problemLink).toHaveAttribute("target", "_blank");
  });

  it("shows a muted link icon when a problem has no link", async () => {
    vi.mocked(fetchProblems).mockResolvedValueOnce({
      items: [
        {
          id: "no-link",
          title: "Problem without link",
          url: null,
          platform: null,
          difficulty: "UNKNOWN",
          notes: null,
          priority: 3,
          total_attempts: 0,
          successful_revision_streak: 0,
          next_revision_date: null,
          calculated_next_revision_date: null,
          next_revision_overridden: false,
          current_mastery_state: "NEW",
          archived_at: null,
          topics: [],
          patterns: [],
        },
      ],
      total: 1,
      page: 1,
      page_size: 5000,
    });

    render(<ProblemsPage />);

    expect(
      await screen.findByRole("img", {
        name: "No problem link available for Problem without link",
      }),
    ).toHaveClass("text-slate-300");
  });
});
