import assert from "node:assert/strict";
import test from "node:test";
import { scrub } from "../src/crashReports.ts";

test("a crash report never carries the account name", () => {
  const event = JSON.stringify({ message: "could not open /Users/ada/Library/nurb/parts/x.py" });
  const scrubbed = scrub(event);
  assert.ok(!scrubbed.includes("ada"));
  assert.ok(scrubbed.includes("~/Library/nurb/parts/x.py"));
});
