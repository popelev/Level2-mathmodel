import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("renders brand and English navigation", () => {
    const html = renderToStaticMarkup(<App />);
    expect(html).toContain("Level2 Mathmodel");
    expect(html).toContain("Status");
    expect(html).toContain("Live inputs");
    expect(html).toContain("Local variables");
    expect(html).toContain("Plan");
  });
});
