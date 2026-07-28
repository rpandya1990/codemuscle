import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "../app/page";

describe("HomePage", () => {
  it("states the primary product promise", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: /know what to revise today/i }),
    ).toBeVisible();
  });
});
