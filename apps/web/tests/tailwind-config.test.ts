import { describe, expect, it } from "vitest";

import tailwindConfig from "../tailwind.config";

describe("Tailwind content configuration", () => {
  it("includes feature modules where interactive page styling lives", () => {
    expect(tailwindConfig.content).toContain(
      "./features/**/*.{js,ts,jsx,tsx,mdx}",
    );
  });
});
