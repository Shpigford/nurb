import assert from "node:assert/strict";
import test from "node:test";
import {
  AttachmentDraft,
  foldDrafts,
  restoreDraftFiles,
  restoreDraftText,
  stashDraft,
  unstashDraft,
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

test("a stashed draft outlives its column and comes back once", () => {
  stashDraft("loose\u0000bin", { text: "make it taller", files: ["/tmp/a.png"] });
  assert.deepEqual(unstashDraft("other\u0000bin"), { text: "", files: [] });
  assert.deepEqual(unstashDraft("loose\u0000bin"), { text: "make it taller", files: ["/tmp/a.png"] });
  assert.deepEqual(unstashDraft("loose\u0000bin"), { text: "", files: [] });
  stashDraft("loose\u0000bin", { text: "kept", files: [] });
  stashDraft("loose\u0000bin", { text: "  ", files: [] });
  assert.deepEqual(unstashDraft("loose\u0000bin"), { text: "", files: [] });
});

test("queued messages fold back in the order they were written", () => {
  assert.deepEqual(
    foldDrafts([
      { text: "Stopped turn", files: ["a.png"] },
      { text: "First queued", files: [] },
      { text: "Second queued", files: ["b.stl", "a.png"] },
    ]),
    { text: "Stopped turn\n\nFirst queued\n\nSecond queued", files: ["a.png", "b.stl"] },
  );
  assert.deepEqual(foldDrafts([{ text: "", files: ["photo.png"] }, { text: "Only words", files: [] }]), {
    text: "Only words",
    files: ["photo.png"],
  });
  assert.deepEqual(foldDrafts([]), { text: "", files: [] });
});
