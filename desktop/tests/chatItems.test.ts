import assert from "node:assert/strict";
import test from "node:test";
import {
  activity,
  applyChatEvent,
  claudeNote,
  pruneLanded,
  toolWords,
  withNote,
  type ChatEvent,
  type Item,
} from "../src/chatItems.ts";

const fold = (events: [ChatEvent, number][]): Item[] =>
  events.reduce<Item[]>((items, [event, at]) => applyChatEvent(items, event, at), []);

const START = Date.parse("2026-09-15T12:00:00Z");

test("a Claude turn leaves the finished step and the streaming text", () => {
  const items = fold([
    [{ type: "agent_text", text: "Making " }, START],
    [{ type: "agent_text", text: "the clip." }, START + 100],
    [
      {
        type: "tool_call",
        id: "t1",
        title: "write_part_source",
        kind: "nurb",
        status: "in_progress",
        input: '{"project_id":"p1","part_name":"cable_clip","source":"..."}',
      },
      START + 200,
    ],
  ]);

  assert.equal(items.length, 2);
  assert.deepEqual(items[0], { kind: "agent", text: "Making the clip." });
  const step = items[1];
  assert.equal(step.kind, "step");
  if (step.kind !== "step") return;
  assert.equal(step.toolKind, "nurb");
  assert.equal(step.step.verb, "write");
  assert.equal(step.step.object, "cable_clip");
  assert.equal(step.step.status, "running");
});

test("a nurb step leaves the overlay once its own transcript row lands", () => {
  const call: ChatEvent = {
    type: "tool_call",
    id: "t1",
    title: "write_part_source",
    kind: "nurb",
    status: "in_progress",
    input: '{"project_id":"p1","part_name":"cable_clip","source":"..."}',
  };
  const done: ChatEvent = {
    type: "tool_call_update",
    id: "t1",
    status: "completed",
    output: "wrote cable_clip",
  };
  const items = fold([
    [call, START],
    [done, START + 2500],
  ]);
  assert.equal(items.length, 1, "the step waits for its row");

  // An older row for the same tool is not this call's row.
  const older = [{ sequence_number: 0, payload: { type: "step", tool: "write_part_source" } }];
  assert.equal(pruneLanded(items, older).length, 1);
  const landed = [{ sequence_number: 1, payload: { type: "build", tool: "write_part_source" } }];
  assert.deepEqual(pruneLanded(items, landed), []);
});

test("a nurb call that never reached the serve keeps its failure on screen", () => {
  const items = fold([
    [
      { type: "tool_call", id: "t1", title: "run_build", kind: "nurb", status: "in_progress" },
      START,
    ],
    [
      { type: "tool_call_update", id: "t1", status: "failed", output: "MCP server nurb failed" },
      START + 100,
    ],
  ]);
  const later = [{ sequence_number: 5, payload: { type: "step", tool: "get_project" } }];
  assert.equal(pruneLanded(items, later).length, 1);
  assert.equal(items[0].kind === "step" && items[0].step.status, "failed");
});

test("an ACP step stays put and records how long it took", () => {
  const items = fold([
    [
      {
        type: "tool_call",
        id: "t1",
        title: "Edit parts/cable_clip.py",
        kind: "edit",
        status: "in_progress",
      },
      START,
    ],
    [{ type: "tool_call_update", id: "t1", status: "completed", output: "ok" }, START + 1500],
  ]);

  assert.equal(items.length, 1);
  const step = items[0];
  assert.equal(step.kind, "step");
  if (step.kind !== "step") return;
  assert.equal(step.step.verb, "edit");
  assert.equal(step.step.object, "cable_clip");
  assert.equal(step.step.status, "done");
  assert.ok(step.step.elapsed_s !== undefined && step.step.elapsed_s >= 0);
  assert.equal(step.step.output, "ok");
});

test("a nurb tool with no named part reads as its own words", () => {
  assert.deepEqual(toolWords("list_project_parts", "nurb", undefined), ["list", "project parts"]);
});

test("the words landing clear the finished steps before them, not the failures", () => {
  const items = fold([
    [{ type: "tool_call", id: "t1", title: "Read", kind: "read", status: "in_progress" }, START],
    [{ type: "tool_call_update", id: "t1", status: "completed" }, START + 10],
    [{ type: "tool_call", id: "t2", title: "run_build", kind: "nurb", status: "in_progress" }, START + 20],
    [{ type: "tool_call_update", id: "t2", status: "failed", output: "MCP server nurb failed" }, START + 30],
    [{ type: "agent_text", text: "That did not build." }, START + 40],
    [{ type: "prose", text: "That did not build." }, START + 50],
  ]);
  assert.equal(items.length, 1);
  assert.equal(items[0].kind === "step" && items[0].step.id, "t2");
});

test("prose only drops the block it replaces", () => {
  const items = fold([
    [{ type: "note", text: "starting" }, START],
    [{ type: "prose", text: "Done." }, START + 10],
  ]);

  assert.deepEqual(items, [{ kind: "note", text: "starting" }]);
});

test("each Claude Code failure says what to do about it", () => {
  assert.match(String(claudeNote("claude_missing")), /^Install Claude Code first/);
  assert.match(String(claudeNote("claude_outdated: 2.1.100")), /you have 2\.1\.100/);
  assert.match(String(claudeNote("auth_required")), /^Sign in to Claude Code first/);
  assert.equal(claudeNote("something else broke"), null);
});

test("the same trouble reported twice in a turn leaves one note", () => {
  const once = withNote([], "Sign in first.");
  const twice = withNote(once, "Sign in first.");
  assert.equal(twice.length, 1);
  const other = withNote(twice, "Update Claude Code.");
  assert.equal(other.length, 2);
});

test("the working line names the running call in plain words", () => {
  const running = fold([
    [{ type: "tool_call", id: "t1", title: "get_project", kind: "nurb", status: "in_progress" }, START],
    [{ type: "tool_call_update", id: "t1", status: "completed" }, START + 10],
    [{ type: "tool_call", id: "t2", title: "edit_part_source", kind: "nurb", status: "in_progress" }, START + 20],
  ]);
  assert.equal(activity(running), "building the part");
  assert.equal(activity([]), "working");
});
