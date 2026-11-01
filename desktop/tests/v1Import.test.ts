import assert from "node:assert/strict";
import test from "node:test";
import { broughtOver, importV1Folders, notBroughtOver } from "../src/v1Import.ts";

test("a folder that refuses does not stop the others", async () => {
  const tried: string[] = [];
  const reported: string[] = [];
  const count = await importV1Folders(
    ["/a", "/bad", "/c"],
    async (path) => {
      tried.push(path);
      if (path === "/bad") throw new Error("Bracket.py: a part name is lowercase snake_case");
    },
    (text) => reported.push(text),
  );

  assert.equal(count, 2);
  assert.deepEqual(tried, ["/a", "/bad", "/c"]);
  assert.equal(reported.length, 1);
  assert.match(reported[0], /\/bad: Bracket\.py/);
});

test("the notice counts projects in plain words", () => {
  assert.equal(broughtOver(1), "Brought over 1 project from nurb 0.x");
  assert.equal(broughtOver(3), "Brought over 3 projects from nurb 0.x");
  assert.equal(notBroughtOver(1), "1 project from nurb 0.x didn't come over. Use Import folder to try again.");
});
