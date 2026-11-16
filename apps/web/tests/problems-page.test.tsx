import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ProblemsPage from "../app/problems/page";
import { createAttempt } from "../lib/attempts";
import { fetchProblems, fetchTopics, updateProblem } from "../lib/problems";

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
  afterEach(cleanup);
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
        solution: null,
        priority: 3,
        total_attempts: 0,
        successful_revision_streak: 0,
        next_revision_date: null,
        calculated_next_revision_date: null,
        next_revision_overridden: false,
        current_mastery_state: "NEW",
        archived_at: null,
        topics: [],
      })),
      total: 26,
      page: 1,
      page_size: 5000,
    });

    render(<ProblemsPage />);
    const top = await screen.findByRole("navigation", {
      name: "Problem pagination (top)",
    });
    const bottom = screen.getByRole("navigation", {
      name: "Problem pagination (bottom)",
    });
    expect(within(top).getByText("Showing 1–25 of 26")).toBeVisible();
    expect(within(bottom).getByText("Page 1 of 2")).toBeVisible();
    expect(
      within(top).getByRole("button", { name: "Previous" }),
    ).toBeDisabled();
    expect(screen.queryByText("Problem 26")).not.toBeInTheDocument();
    fireEvent.click(
      screen.getAllByRole("button", { name: "Record attempt" })[0],
    );
    expect(
      await screen.findByRole("dialog", { name: "Record attempt" }),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    fireEvent.click(within(top).getByRole("button", { name: "Next" }));

    for (const navigation of [top, bottom]) {
      expect(within(navigation).getByText("Showing 26–26 of 26")).toBeVisible();
      expect(within(navigation).getByText("Page 2 of 2")).toBeVisible();
      expect(
        within(navigation).getByRole("button", { name: "Next" }),
      ).toBeDisabled();
    }
    expect(screen.getByText("Problem 26")).toBeVisible();
    fireEvent.click(within(bottom).getByRole("button", { name: "Previous" }));
    expect(within(top).getByText("Page 1 of 2")).toBeVisible();
    expect(screen.getByText("Problem 1")).toBeVisible();
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
          solution: "function twoSum() { return []; }",
          priority: 3,
          total_attempts: 0,
          successful_revision_streak: 0,
          next_revision_date: null,
          calculated_next_revision_date: null,
          next_revision_overridden: false,
          current_mastery_state: "NEW",
          archived_at: null,
          topics: [],
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
          solution: null,
          priority: 3,
          total_attempts: 0,
          successful_revision_streak: 0,
          next_revision_date: null,
          calculated_next_revision_date: null,
          next_revision_overridden: false,
          current_mastery_state: "NEW",
          archived_at: null,
          topics: [],
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

  it.each([
    [" Graphs, , Dynamic Programming ", ["Graphs", "Dynamic Programming"]],
    ["", []],
  ])("saves edited topics from %j", async (input, expectedTopics) => {
    vi.mocked(fetchProblems).mockResolvedValueOnce({
      items: [
        {
          id: "topic-edit",
          title: "Topic editing problem",
          url: null,
          platform: null,
          difficulty: "EASY",
          notes: null,
          solution: null,
          priority: 3,
          total_attempts: 0,
          successful_revision_streak: 0,
          next_revision_date: null,
          calculated_next_revision_date: null,
          next_revision_overridden: false,
          current_mastery_state: "NEW",
          archived_at: null,
          topics: [
            { id: "arrays", name: "Arrays" },
            { id: "hash-table", name: "Hash Table" },
          ],
        },
      ],
      total: 1,
      page: 1,
      page_size: 5000,
    });
    render(<ProblemsPage />);
    const card = (await screen.findByText("Topic editing problem")).closest(
      "li",
    );
    fireEvent.click(
      within(card as HTMLElement).getByRole("button", { name: "Edit" }),
    );
    const dialog = await screen.findByRole("dialog", { name: "Edit problem" });
    const topics = within(dialog).getByRole("textbox", { name: /Topics/ });
    expect(topics).toHaveValue("Arrays, Hash Table");
    fireEvent.change(topics, { target: { value: input } });
    const topicFetches = vi.mocked(fetchTopics).mock.calls.length;
    fireEvent.click(
      within(dialog).getByRole("button", { name: "Save changes" }),
    );
    await waitFor(() =>
      expect(updateProblem).toHaveBeenLastCalledWith(
        "topic-edit",
        expect.objectContaining({ topics: expectedTopics }),
      ),
    );
    await waitFor(() => expect(dialog).not.toBeInTheDocument());
    await waitFor(() =>
      expect(vi.mocked(fetchTopics).mock.calls.length).toBeGreaterThan(
        topicFetches,
      ),
    );
  });

  it("closes the attempt dialog after a successful submission", async () => {
    vi.mocked(fetchProblems)
      .mockReset()
      .mockResolvedValue({
        items: [
          {
            id: "reverse-integer",
            title: "Reverse Integer",
            url: null,
            platform: null,
            difficulty: "MEDIUM",
            notes: null,
            solution: "const reverse = (value) => value;",
            priority: 3,
            total_attempts: 0,
            successful_revision_streak: 0,
            next_revision_date: null,
            calculated_next_revision_date: null,
            next_revision_overridden: false,
            current_mastery_state: "NEW",
            archived_at: null,
            topics: [],
          },
        ],
        total: 1,
        page: 1,
        page_size: 5000,
      });
    vi.mocked(createAttempt).mockResolvedValueOnce({} as never);

    render(<ProblemsPage />);
    const problemCard = (await screen.findByText("Reverse Integer")).closest(
      "li",
    );
    expect(problemCard).not.toBeNull();
    fireEvent.click(
      within(problemCard as HTMLElement).getByRole("button", {
        name: "Record attempt",
      }),
    );
    const dialog = await screen.findByRole("dialog", {
      name: "Record attempt",
    });
    const timeSpent = within(dialog).getByRole("spinbutton", {
      name: "Time spent (minutes)",
    });
    expect(
      within(dialog).getByRole("textbox", { name: /Solution/ }),
    ).toHaveValue("const reverse = (value) => value;");
    expect(
      within(dialog).queryByRole("combobox", { name: "Hint usage" }),
    ).not.toBeInTheDocument();
    fireEvent.change(timeSpent, { target: { value: "5" } });
    fireEvent.click(
      within(dialog).getByRole("button", { name: "Record attempt" }),
    );

    await waitFor(() => expect(dialog).not.toBeInTheDocument());
    expect(createAttempt).toHaveBeenCalledWith(
      "reverse-integer",
      expect.objectContaining({
        time_spent_minutes: 5,
      }),
    );
  });
});
