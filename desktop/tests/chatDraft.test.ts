import assert from "node:assert/strict";
import test from "node:test";
import {
  AttachmentDraft,
  restoreDraftFiles,
  restoreDraftText,
} from "../src/chatDraft.ts";

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

test("submission waits for every paste already being saved", async () => {
  let shown: string[] = [];
  let finishFirst!: (paths: string[]) => void;
  let finishSecond!: (paths: string[]) => void;
  const first = new Promise<string[]>((resolve) => {
    finishFirst = resolve;
  });
  const second = new Promise<string[]>((resolve) => {
    finishSecond = resolve;
  });
  const draft = new AttachmentDraft((files) => {
    shown = files;
  });

  draft.track(first);
  draft.track(second);
  const submitted = draft.take();
  finishSecond(["second.png"]);
  finishFirst(["first.png"]);

  assert.deepEqual(await submitted, ["first.png", "second.png"]);
  assert.deepEqual(shown, []);
});
