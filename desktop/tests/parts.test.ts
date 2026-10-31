import assert from "node:assert/strict";
import test from "node:test";
import { folders, messagesForPart, moveTargets } from "../src/parts.ts";
import type { Message } from "@nurb/ui";
import type { LibraryPart, ProjectSummary } from "@nurb/workbench/api";

const project = (id: string, name: string, folder: boolean, parts = 1): ProjectSummary => ({
  id,
  name,
  created_at: "2026-09-18T00:00:00Z",
  parts,
  last_built: null,
  folder,
});

const held = (id: string, projectId: string): LibraryPart =>
  ({ id, name: id, project_id: projectId, project_name: projectId, folder: true }) as LibraryPart;

const line = (id: string, part: string | null): Message => ({
  id,
  role: "user",
  content: id,
  created_at: "2026-09-18T00:00:00Z",
  part,
});

test("the rail lists folders and hides the containers", () => {
  const list = [project("a", "Shelf", true, 3), project("b", "bracket", false)];
  assert.deepEqual(
    folders(list).map((p) => p.id),
    ["a"],
  );
});

test("a part cannot move into the folder it is already in", () => {
  const list = [project("a", "Shelf", true, 3), project("b", "Rack", true, 2), project("c", "x", false)];
  assert.deepEqual(moveTargets(list, held("p1", "a")), [{ id: "b", name: "Rack", parts: 2 }]);
});

test("a loose part can move into every folder", () => {
  const list = [project("a", "Shelf", true, 3), project("b", "x", false)];
  assert.deepEqual(moveTargets(list, held("p1", "b")), [{ id: "a", name: "Shelf", parts: 3 }]);
});

test("a folder keeps one conversation per part and its own", () => {
  const all = [line("1", null), line("2", "lip"), line("3", "base")];
  assert.deepEqual(
    messagesForPart(all, "lip", true).map((m) => m.id),
    ["2"],
  );
  assert.deepEqual(
    messagesForPart(all, null, true).map((m) => m.id),
    ["1"],
  );
});

test("a project holding one part shows every line", () => {
  const all = [line("1", null), line("2", "lip")];
  assert.deepEqual(
    messagesForPart(all, null, false).map((m) => m.id),
    ["1", "2"],
  );
});
