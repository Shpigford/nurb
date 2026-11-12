import assert from "node:assert/strict";
import test from "node:test";
import {
  markChatSeen,
  renameChatColumn,
  renameChatKey,
  retainChatColumns,
  updateChatActivity,
  chatKey,
  type ChatColumn,
} from "../src/chatColumns.ts";

const fresh = (path = "/projects/alpha"): ChatColumn => ({
  id: 1,
  path,
  part: "bracket",
  agent: null,
  resume: null,
  gen: 0,
  unseen: false,
});

test("starting a turn pins the resolved agent", () => {
  const [column] = updateChatActivity(
    [fresh()],
    "/projects/alpha",
    "bracket",
    "claude",
    true,
    true,
    false,
  );

  assert.equal(column.agent, "claude");
});

test("a hidden completed turn survives unrelated project switches until shown", () => {
  const running = updateChatActivity(
    [fresh()],
    "/projects/alpha",
    "bracket",
    "claude",
    true,
    true,
    false,
  );
  const completed = updateChatActivity(
    running,
    "/projects/alpha",
    "bracket",
    "claude",
    false,
    false,
    true,
  );

  assert.equal(completed[0].unseen, true);
  assert.equal(retainChatColumns(completed, "/projects/beta", {}).length, 1);
  assert.equal(retainChatColumns(completed, "/projects/gamma", {}).length, 1);

  const seen = markChatSeen(completed, "/projects/alpha", "bracket");
  assert.equal(seen[0].unseen, false);
  assert.equal(retainChatColumns(seen, "/projects/beta", {}).length, 0);
});

test("an initial idle report does not invent unseen work", () => {
  const columns = [fresh()];
  const next = updateChatActivity(
    columns,
    "/projects/alpha",
    "bracket",
    "claude",
    false,
    false,
    false,
  );

  assert.equal(next, columns);
  assert.equal(next[0].unseen, false);
});

test("a renamed column keeps its identity, and replaces a leftover under the new name", () => {
  const old = { ...fresh(), id: 7 };
  const leftover = { ...fresh(), id: 8, part: "shelf" };
  const elsewhere = { ...fresh("/projects/beta"), id: 9 };
  const next = renameChatColumn([old, leftover, elsewhere], "/projects/alpha", "bracket", "shelf");
  assert.deepEqual(
    next.map((column) => [column.id, column.part]),
    [
      [7, "shelf"],
      [9, "bracket"],
    ],
  );
});

test("a running turn's busy flag follows the rename", () => {
  const was = chatKey("/projects/alpha", "bracket");
  const name = chatKey("/projects/alpha", "shelf");
  assert.deepEqual(renameChatKey({ [was]: true }, was, name), { [name]: true });
  const idle = {};
  assert.equal(renameChatKey(idle, was, name), idle);
});
