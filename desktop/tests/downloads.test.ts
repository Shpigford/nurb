import assert from "node:assert/strict";
import test from "node:test";
import { numbered } from "../src/downloads.ts";

test("a second copy is named the way Finder names one", () => {
  assert.equal(numbered("drill_bits.3mf", 2), "drill_bits 2.3mf");
  assert.equal(numbered("Notch v2.step", 3), "Notch v2 3.step");
  assert.equal(numbered("README", 2), "README 2");
});
