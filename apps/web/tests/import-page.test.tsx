import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ImportPage from "../app/import/page";

describe("ImportPage", () => {
  it("starts with a constrained file picker", () => {
    render(<ImportPage />);
    expect(
      screen.getByRole("heading", { name: "Import preparation history" }),
    ).toBeVisible();
    const input = screen.getByLabelText("CSV or Excel file");
    expect(input).toHaveAttribute("accept", ".csv,.xlsx");
  });
});
