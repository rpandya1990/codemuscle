import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ProblemsPage from "../app/problems/page";
import { fetchProblems } from "../lib/problems";

vi.mock("../lib/problems", () => ({
  fetchProblems: vi
    .fn()
    .mockResolvedValue({ items: [], total: 0, page: 1, page_size: 25 }),
  createProblem: vi.fn(),
  findDuplicates: vi.fn().mockResolvedValue([]),
  setProblemArchived: vi.fn(),
  updateProblem: vi.fn(),
}));

describe("ProblemsPage", () => {
  it("renders library controls", async () => {
    render(<ProblemsPage />);
    expect(
      screen.getByRole("heading", { name: "Coding problems" }),
    ).toBeVisible();
    expect(screen.getByRole("heading", { name: "Add problem" })).toBeVisible();
    expect(
      screen.getByRole("textbox", { name: /Problem link/ }),
    ).not.toBeRequired();
    expect(screen.getByRole("textbox", { name: /Notes/ })).toBeVisible();
    expect(screen.getByRole("textbox", { name: /Patterns/ })).toBeVisible();
    expect(
      screen.getByRole("searchbox", { name: "Search problems" }),
    ).toBeVisible();
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

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(screen.getByText("Showing 26–26 of 26")).toBeVisible();
    expect(screen.getByText("Problem 26")).toBeVisible();
  });
});
