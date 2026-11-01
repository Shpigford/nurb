import { strict as assert } from "node:assert";
import test from "node:test";
import { connectCommands, maskToken, mcpUrl } from "../src/connect.ts";

const info = { port: 7373, token: "abc123XYZ" };

test("the address carries the port", () => {
  assert.equal(mcpUrl(7373), "http://127.0.0.1:7373/mcp");
});

test("every command carries the address and the token", () => {
  const c = connectCommands(info);
  assert.ok(c.claudeCode.includes(c.mcpUrl));
  assert.ok(c.claudeCode.includes("Bearer abc123XYZ"));
  assert.ok(c.codexCli.includes(c.mcpUrl));
  assert.ok(c.codexCli.includes("Bearer abc123XYZ"));
});

test("the Codex command appends a server block to its config", () => {
  const c = connectCommands(info);
  assert.ok(c.codexCli.startsWith("printf '"));
  assert.ok(c.codexCli.includes("[mcp_servers.nurb]"));
  assert.ok(c.codexCli.endsWith(">> ~/.codex/config.toml"));
});

test("the Cursor link decodes to the server object", () => {
  const c = connectCommands(info);
  const config = new URL(c.cursorLink).searchParams.get("config") ?? "";
  assert.equal(
    atob(config),
    '{"url":"http://127.0.0.1:7373/mcp","headers":{"Authorization":"Bearer abc123XYZ"}}',
  );
  assert.ok(c.cursorLink.startsWith("cursor://anysphere.cursor-deeplink/mcp/install?name=nurb&"));
  assert.equal(atob(config), c.cursorConfig);
});

test("masking keeps six characters of the token", () => {
  assert.equal(maskToken("abc123XYZ"), "abc123••••••••");
  assert.ok(!maskToken("abc123XYZ").includes("XYZ"));
});
