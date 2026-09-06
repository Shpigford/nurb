import assert from "node:assert/strict";
import test from "node:test";
import {
  groupSessions,
  sessionTitle,
  sessionWhen,
  type SessionInfo,
} from "../src/sessionHistory.ts";

const session = (over: Partial<SessionInfo>): SessionInfo => ({
  id: "s1",
  title: "a bracket",
  updatedAt: "2026-01-02T03:04:05Z",
  part: "bracket",
  attached: false,
  agent: "claude",
  ...over,
});

test("the attached session is what the part resumes", () => {
  const { resume } = groupSessions([
    session({ id: "new", attached: true }),
    session({ id: "old" }),
  ]);

  assert.deepEqual(resume.bracket, { id: "new", agent: "claude" });
});

test("history keeps every session for the part, newest first", () => {
  const { history } = groupSessions([
    session({ id: "new", attached: true }),
    session({ id: "old" }),
    session({ id: "other", part: "shelf" }),
    session({ id: "orphan", part: null }),
  ]);

  assert.deepEqual(
    history.bracket.map((entry) => entry.id),
    ["new", "old"],
  );
  assert.deepEqual(
    history.shelf.map((entry) => entry.id),
    ["other"],
  );
});

test("a part set aside with start fresh resumes nothing but keeps its history", () => {
  const { resume, history } = groupSessions([session({ id: "old" })]);

  assert.equal(resume.bracket, undefined);
  assert.equal(history.bracket.length, 1);
});

test("an untitled session still has something to click", () => {
  assert.equal(sessionTitle(session({ title: null })), "untitled chat");
  assert.equal(sessionTitle(session({ title: "  " })), "untitled chat");
  assert.equal(sessionTitle(session({ title: " a bracket " })), "a bracket");
});

test("timestamps read as how long ago", () => {
  const now = Date.parse("2026-01-10T12:00:00Z");
  const ago = (iso: string) => sessionWhen(iso, now);

  assert.equal(ago("2026-01-10T11:59:40Z"), "just now");
  assert.equal(ago("2026-01-10T11:45:00Z"), "15m ago");
  assert.equal(ago("2026-01-10T06:00:00Z"), "6h ago");
  assert.equal(ago("2026-01-08T12:00:00Z"), "2d ago");
  // Older than a week reads as a date, not a count.
  assert.ok(!ago("2025-11-02T12:00:00Z").endsWith("ago"));
  // A missing or unparseable timestamp leaves the row to its title.
  assert.equal(sessionWhen(null, now), "");
  assert.equal(sessionWhen("whenever", now), "");
});
