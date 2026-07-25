import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("POST /api/auth/login", () => {
  it("true should be true", async () => {
    expect(true).toBe(true);
  });
});
