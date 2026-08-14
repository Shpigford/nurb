import assert from "node:assert/strict";
import test from "node:test";
import { shouldPlayCompletionChime } from "../src/chime.ts";

test("only successful long turns earn a completion chime", () => {
  assert.equal(shouldPlayCompletionChime(false, 9000), false);
  assert.equal(shouldPlayCompletionChime(true, 8000), false);
  assert.equal(shouldPlayCompletionChime(true, 8001), true);
});
