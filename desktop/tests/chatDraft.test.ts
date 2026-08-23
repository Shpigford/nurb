import assert from "node:assert/strict";
import test from "node:test";
import { restoreDraftFiles, restoreDraftText } from "../src/chatDraft.ts";

test("an auth failure preserves work composed during the failed turn", () => {
  assert.equal(
    restoreDraftText("Original message", "Next draft"),
    "Original message\n\nNext draft",
  );
  assert.equal(restoreDraftText("", "Next draft"), "Next draft");
  assert.equal(restoreDraftText("Original message", ""), "Original message");
  assert.deepEqual(
    restoreDraftFiles(["original.stl"], ["next.png", "original.stl"]),
    ["original.stl", "next.png"],
  );
});
