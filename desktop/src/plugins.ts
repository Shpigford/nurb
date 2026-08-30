// The engine plugin registry as reported by the dev server's /api/plugins.
// The engine owns loading; the app owns the Settings toggle, which flips the
// `enabled` flag by writing the same state file the engine reads.
export type PluginStatus = {
  id: string;
  name: string;
  version: string;
  description: string;
  state: "loaded" | "disabled" | "error" | "unloaded" | string;
  error: string;
  source: string;
  enabled: boolean;
  commands: string[];
  mcpTools: string[];
  checks: number;
};
