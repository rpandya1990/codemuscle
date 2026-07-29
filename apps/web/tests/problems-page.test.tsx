import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ProblemsPage from "../app/problems/page";

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
    expect(screen.getByRole("textbox", { name: "Problem link" })).toBeRequired();
    expect(screen.getByRole("textbox", { name: /Notes/ })).toBeVisible();
    expect(screen.getByRole("textbox", { name: /Patterns/ })).toBeVisible();
    expect(
      screen.getByRole("searchbox", { name: "Search problems" }),
    ).toBeVisible();
  });
});
