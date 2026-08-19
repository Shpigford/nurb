import assert from "node:assert/strict";
import test from "node:test";
import { partMessage } from "../src/partMessages.ts";

test("passive part synchronization cannot change its configuration", () => {
  const { message, consumed } = partMessage("/one", "shelf", null);

  assert.deepEqual(message, { type: "nurb:part", name: "shelf" });
  assert.equal(Object.hasOwn(message, "variant"), false);
  assert.equal(consumed, false);
});

test("an explicit defaults or variant click is delivered once to its part", () => {
  const defaults = partMessage("/one", "shelf", {
    path: "/one",
    part: "shelf",
    variant: null,
  });
  const variant = partMessage("/one", "shelf", {
    path: "/one",
    part: "shelf",
    variant: "tall",
  });

  assert.deepEqual(defaults, {
    message: { type: "nurb:part", name: "shelf", variant: null },
    consumed: true,
  });
  assert.deepEqual(variant, {
    message: { type: "nurb:part", name: "shelf", variant: "tall" },
    consumed: true,
  });
});

test("a configuration click cannot leak into another project", () => {
  const result = partMessage("/two", "shelf", {
    path: "/one",
    part: "shelf",
    variant: "tall",
  });

  assert.deepEqual(result, {
    message: { type: "nurb:part", name: "shelf" },
    consumed: false,
  });
});
