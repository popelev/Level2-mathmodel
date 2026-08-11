import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ImportPage } from "./ImportPage";

describe("ImportPage", () => {
  it("renders import controls and catalog/bindings sections in English", () => {
    const html = renderToStaticMarkup(<ImportPage />);
    expect(html).toContain("Import from Level2");
    expect(html).toContain("Tag catalog");
    expect(html).toContain("Bindings");
    expect(html).toContain("tag_id");
    expect(html).toContain("device_id");
    expect(html).toContain("datatype");
    expect(html).toContain("path");
    expect(html).toContain("logical_name");
    expect(html).toContain("Add / update binding");
  });
});
