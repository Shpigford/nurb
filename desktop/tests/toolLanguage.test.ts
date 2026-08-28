import test from "node:test";
import assert from "node:assert/strict";
import { describe, orderOptions, permissionPrompt } from "../src/toolLanguage.ts";

test("a command dialog shows the command, not a paraphrase", () => {
  const prompt = permissionPrompt(
    { title: "nurb build lid", kind: "execute", detail: "uv run nurb build lid" },
    "Claude",
  );
  assert.equal(prompt.verbatim, true);
  assert.equal(prompt.detail, "uv run nurb build lid");
  // The regression this whole module exists for: describe() would have turned
  // the title into "build the part" and thrown the command away.
  assert.notEqual(prompt.headline, "Claude wants to build the part");
  assert.match(prompt.headline, /run this command/);
});

test("an edit dialog keeps the whole path", () => {
  const prompt = permissionPrompt(
    {
      title: "Edit /home/u/proj/parts/lid.py",
      kind: "edit",
      detail: "/home/u/proj/parts/lid.py",
    },
    "Claude",
  );
  assert.equal(prompt.verbatim, true);
  assert.equal(prompt.detail, "/home/u/proj/parts/lid.py");
  // FILE_TITLE would have reduced this to "lid".
  assert.ok(!prompt.headline.includes("lid"));
});

test("a kind the app cannot place is shown literally", () => {
  const prompt = permissionPrompt({ title: "mcp__weird__tool", detail: "rm -rf /" }, "Codex");
  assert.equal(prompt.verbatim, true);
  assert.equal(prompt.detail, "rm -rf /");
});

test("the agent's own fallback sentence is not echoed as its own detail", () => {
  const prompt = permissionPrompt({ title: "Claude wants to use a tool" }, "Claude");
  assert.equal(prompt.verbatim, true);
  assert.equal(prompt.detail, undefined);
});

test("a read dialog still speaks plainly", () => {
  const prompt = permissionPrompt(
    { title: "Read /home/u/proj/parts/lid.py", kind: "read" },
    "Claude",
  );
  assert.equal(prompt.verbatim, false);
  assert.equal(prompt.detail, undefined);
  assert.equal(prompt.headline, "Claude wants to look at lid");
});

test("deny comes first and the rest keep their order", () => {
  const ordered = orderOptions([
    { optionId: "a", name: "Allow", kind: "allow_once" },
    { optionId: "b", name: "Always", kind: "allow_always" },
    { optionId: "c", name: "Deny", kind: "reject_once" },
  ]);
  assert.deepEqual(
    ordered.map((o) => o.optionId),
    ["c", "a", "b"],
  );
});

test("describe translates what it recognizes and passes through what it does not", () => {
  assert.equal(describe("Edit /home/u/proj/parts/lid.py", undefined, 0), "editing lid");
  assert.equal(describe("nurb check", undefined, 1), "check printability");
  assert.equal(describe("uv run nurb build", undefined, 0), "building the part");
  assert.equal(describe("something else", "execute", 0), "running a command");
  assert.equal(describe("something else", undefined, 0), "something else");
});
