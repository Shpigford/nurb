// The commands that hand this Mac's local nurb endpoint to a coding assistant.
// Pure string building so the Settings section stays a render and the shapes
// can be tested without a window.

export type ConnectInfo = { port: number; token: string };

export type ConnectCommands = {
  mcpUrl: string;
  claudeCode: string;
  codexCli: string;
  cursorConfig: string;
  cursorLink: string;
};

export function mcpUrl(port: number): string {
  return `http://127.0.0.1:${port}/mcp`;
}

/// The server object Cursor keeps under mcpServers.nurb in its mcp.json.
export function cursorConfig(url: string, token: string): string {
  return JSON.stringify({ url, headers: { Authorization: `Bearer ${token}` } });
}

/// Cursor installs from a deeplink carrying that object as base64; the padding
/// and any + or / in it have to survive the query string.
export function cursorLink(url: string, token: string): string {
  return `cursor://anysphere.cursor-deeplink/mcp/install?name=nurb&config=${encodeURIComponent(btoa(cursorConfig(url, token)))}`;
}

export function connectCommands({ port, token }: ConnectInfo): ConnectCommands {
  const url = mcpUrl(port);
  return {
    mcpUrl: url,
    claudeCode: `claude mcp add --transport http --scope user nurb ${url} --header "Authorization: Bearer ${token}"`,
    // The Codex CLI has no header flag, so the server goes into its config file.
    codexCli: `printf '\\n[mcp_servers.nurb]\\nurl = "${url}"\\nhttp_headers = { Authorization = "Bearer ${token}" }\\n' >> ~/.codex/config.toml`,
    cursorConfig: cursorConfig(url, token),
    cursorLink: cursorLink(url, token),
  };
}

/// Enough of the token to recognise it, never enough to use it.
export function maskToken(token: string): string {
  return `${token.slice(0, 6)}••••••••`;
}
