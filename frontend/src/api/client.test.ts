import { describe, expect, it } from "vitest";
import { formatApiError } from "./client";

describe("formatApiError", () => {
  it("returns string detail as-is", () => {
    expect(formatApiError("Not found", "fallback")).toBe("Not found");
  });

  it("joins validation error array", () => {
    expect(
      formatApiError([{ msg: "field required" }, { msg: "invalid type" }], "fallback")
    ).toBe("field required; invalid type");
  });

  it("uses fallback for unknown shapes", () => {
    expect(formatApiError(null, "Server error")).toBe("Server error");
  });
});
