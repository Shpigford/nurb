import assert from "node:assert/strict";
import test from "node:test";
import { createPartRecovery } from "../src/partRecovery.ts";

test("one recovery remains pending until it settles, then another can start", async () => {
  const settlements: Array<{
    resolve: () => void;
    reject: (error: Error) => void;
  }> = [];
  let attempts = 0;
  const recovery = createPartRecovery(
    () => new Promise<void>((resolve, reject) => {
      attempts += 1;
      settlements.push({ resolve, reject });
    }),
  );

  recovery.failure();
  recovery.failure();
  recovery.failure();
  for (let failure = 0; failure < 6; failure += 1) recovery.failure();
  assert.equal(attempts, 1);

  settlements[0].resolve();
  await Promise.resolve();
  recovery.failure();
  recovery.failure();
  recovery.failure();
  assert.equal(attempts, 2);

  settlements[1].reject(new Error("restart failed"));
  await Promise.resolve();
  recovery.failure();
  recovery.failure();
  recovery.failure();
  assert.equal(attempts, 3);
});

test("a stopped recovery ignores stale failures and settlement", async () => {
  let release: (() => void) | undefined;
  let attempts = 0;
  const recovery = createPartRecovery(
    () => new Promise<void>((resolve) => {
      attempts += 1;
      release = resolve;
    }),
  );

  recovery.failure();
  recovery.failure();
  recovery.failure();
  recovery.stop();
  release?.();
  await Promise.resolve();
  recovery.failure();
  recovery.failure();
  recovery.failure();

  assert.equal(attempts, 1);
});
