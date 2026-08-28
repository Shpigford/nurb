import assert from "node:assert/strict";
import test from "node:test";
import { createLatestRequestGate } from "../src/latestRequest.ts";

test("only the latest request remains current", () => {
  const gate = createLatestRequestGate();
  const first = gate.begin();

  assert.equal(first(), true);

  const second = gate.begin();

  assert.equal(first(), false);
  assert.equal(second(), true);
});
