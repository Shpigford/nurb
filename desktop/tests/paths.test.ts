import assert from "node:assert/strict";
import test from "node:test";
import { pathName, pathParentName } from "../src/paths.ts";

// A path reaches the page from the Rust side with the operating system's own
// separator. Splitting on "/" alone made a project's folder name double as its
// id, so on Windows the "id" was the whole path and every request came back
// "no project".

test("a Windows path gives its last segment, not itself", () => {
  const dir = "C:\\Users\\someone\\AppData\\Roaming\\dev.nurb.desktop\\projects\\5f61bfca";
  assert.equal(pathName(dir), "5f61bfca");
  assert.equal(pathParentName(dir), "projects");
});

test("a Mac path behaves as it always did", () => {
  const dir = "/Users/someone/.nurb/projects/5f61bfca";
  assert.equal(pathName(dir), "5f61bfca");
  assert.equal(pathParentName(dir), "projects");
});

test("a trailing separator does not invent a segment", () => {
  assert.equal(pathName("C:\\projects\\alpha\\"), "alpha");
  assert.equal(pathName("/projects/alpha/"), "alpha");
});

test("a path with no separator is its own name", () => {
  assert.equal(pathName("bracket"), "bracket");
  assert.equal(pathParentName("bracket"), "bracket");
});

test("an empty path stays empty rather than becoming undefined", () => {
  assert.equal(pathName(""), "");
});

test("a mixed path splits on whichever separator it uses", () => {
  // A value pasted from a slicer's settings can carry either, and a Windows path
  // can hold a forward slash, so neither side may assume the other's.
  assert.equal(pathName("C:/Program Files/OrcaSlicer/orca-slicer.exe"), "orca-slicer.exe");
  assert.equal(pathName("C:\\Program Files\\OrcaSlicer/orca-slicer.exe"), "orca-slicer.exe");
});
