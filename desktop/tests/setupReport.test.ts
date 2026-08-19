import assert from "node:assert/strict";
import test from "node:test";
import { REPORT_URL_MAX_LENGTH, setupReportUrl } from "../src/setupReport.ts";

test("setup reports preserve ordinary errors", () => {
  const url = new URL(setupReportUrl("app 0.22.1", "Claude CLI failed"));

  assert.equal(url.searchParams.get("template"), "bug_report.yml");
  assert.equal(url.searchParams.get("version"), "app 0.22.1");
  assert.equal(url.searchParams.get("output"), "Claude CLI failed");
});

test("setup reports fit GitHub's URL limit after encoding", () => {
  const error = "dyld: <missing> & % 😀 ".repeat(1_000);
  const url = setupReportUrl("app 0.22.1", error);
  const output = new URL(url).searchParams.get("output") ?? "";
  const prefix = output.replace(/\n\n\[error truncated\]$/, "");

  assert.ok(url.length <= REPORT_URL_MAX_LENGTH);
  assert.ok(output.endsWith("\n\n[error truncated]"));
  assert.ok(error.startsWith(prefix));
  assert.ok(!prefix.endsWith("\ud83d"));
});
