import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import DataPage from "../app/data/page";
import { createExport, deleteAllData } from "../lib/data-lifecycle";

vi.mock("../lib/data-lifecycle", () => ({
  fetchBackups: vi.fn().mockResolvedValue([]),
  createExport: vi
    .fn()
    .mockResolvedValue({ filename: "export.json", problem_count: 3 }),
  createBackup: vi.fn(),
  restoreBackup: vi.fn(),
  deleteAllData: vi.fn().mockResolvedValue({ deleted_rows: 10 }),
}));

describe("DataPage", () => {
  it("exports data and requires typed deletion confirmation", async () => {
    render(<DataPage />);
    fireEvent.click(screen.getByRole("button", { name: "Export JSON" }));
    await waitFor(() => expect(createExport).toHaveBeenCalledWith("JSON"));
    expect(await screen.findByText(/Created export.json/)).toBeVisible();

    fireEvent.change(
      screen.getByRole("textbox", { name: "Type DELETE ALL DATA" }),
      {
        target: { value: "DELETE ALL DATA" },
      },
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Delete selected data" }),
    );
    await waitFor(() =>
      expect(deleteAllData).toHaveBeenCalledWith(
        expect.objectContaining({ confirmation: "DELETE ALL DATA" }),
      ),
    );
  });
});
