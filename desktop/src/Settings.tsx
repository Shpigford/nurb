import { useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open as pickFolder } from "@tauri-apps/plugin-dialog";
import { playChime, setSoundEnabled, soundEnabled } from "./chime";
import { AGENT_LABEL } from "./Chat";
import type { ExtensionStatus } from "./ExtensionsModal";
import type { PluginStatus } from "./plugins";

type SettingsAgent = {
  id: string;
  label: string;
  loggedIn: boolean | null;
  detail: string | null;
};

type Props = {
  folder: string;
  customized: boolean;
  onChange: (folder: string) => void | Promise<void>;
  onReset: () => void | Promise<void>;
  // The agents installed on this Mac, so signing in lives with the rest of the
  // setup rather than beside the parts.
  agents: SettingsAgent[];
  agentStatusState: "loading" | "ready" | "error";
  signingIn: string | null;
  onSignIn: (id: string) => Promise<boolean>;
  onMoreAgents: () => void;
  // Fork: developer extensions and engine plugins surface live here too.
  extensions: ExtensionStatus[];
  onExtensionsChanged: () => void;
  plugins: PluginStatus[];
  onPluginsChanged: () => void;
  projectPath: string;
  onClose: () => void;
};

export default function Settings({
  folder,
  customized,
  onChange,
  onReset,
  agents,
  agentStatusState,
  signingIn,
  onSignIn,
  onMoreAgents,
  extensions,
  onExtensionsChanged,
  plugins,
  onPluginsChanged,
  projectPath,
  onClose,
}: Props) {
  const [sound, setSound] = useState(soundEnabled);
  // The rail's error line is behind this modal, so a failed sign-in reports here.
  const [signInError, setSignInError] = useState<string | null>(null);

  const toggleSound = (on: boolean) => {
    setSoundEnabled(on);
    setSound(on);
    // Turning it on plays the chime once, so the choice is audible in place.
    if (on) playChime();
  };

  const [installing, setInstalling] = useState<string | null>(null);
  // Serialize writes per plugin. Two quick clicks otherwise race in the Rust
  // command and the earlier choice can overwrite the later one on disk.
  const pluginWrites = useRef<Record<string, Promise<void>>>({});

  const toggleExtension = (id: string, enabled: boolean) => {
    invoke("set_extension_enabled", { id, enabled })
      .then(onExtensionsChanged)
      .catch(() => {});
  };

  const installExtension = (id: string) => {
    setInstalling(id);
    invoke("install_extension", { id })
      .then(() => onExtensionsChanged())
      .catch(() => {})
      .finally(() => setInstalling(null));
  };

  // Engine plugins: the toggle writes the project's .nurb/plugins.toml, the
  // same file `nurb plugin enable|disable` writes, so both surfaces agree.
  const togglePlugin = (id: string, enabled: boolean) => {
    const previous = pluginWrites.current[id] ?? Promise.resolve();
    const write = previous
      .catch(() => {})
      .then(() => invoke("set_plugin_enabled", { path: projectPath, id, enabled }))
      .then(() => undefined);
    pluginWrites.current[id] = write;
    void write
      .then(() => {
        if (pluginWrites.current[id] === write) onPluginsChanged();
      })
      .catch(() => {})
      .finally(() => {
        if (pluginWrites.current[id] === write) delete pluginWrites.current[id];
      });
  };

  const changeFolder = async () => {
    // Before the backend resolves the default, the folder shown is the
    // literal "~/Documents/nurb" placeholder, which is not a path.
    const picked = await pickFolder({
      directory: true,
      defaultPath: folder.startsWith("~") ? undefined : folder,
      title: "Choose where new nurb projects are created",
    });
    if (typeof picked === "string") await onChange(picked);
  };

  // Non-dev-only extensions get a toggle in settings; dev-only ones stay
  // behind the "developer extensions" modal where they belong.
  const visibleExts = extensions.filter((e) => !e.devOnly);

  return (
    <div className="about" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div
        className="about-card settings"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
      >
        <button className="about-close" title="close" onClick={onClose}>
          ×
        </button>
        <div className="about-title" id="settings-title">
          Settings
        </div>
        <div className="about-body">
          <h3>Projects folder</h3>
          <p>New projects are created here. Changing it never moves existing files.</p>
          <div className="settings-folder" title={folder}>
            {folder}
          </div>
          <div className="settings-actions">
            <button className="settings-action" onClick={changeFolder}>
              Change folder
            </button>
            {customized && (
              <button className="settings-action secondary" onClick={onReset}>
                Use default
              </button>
            )}
          </div>
          <h3>Sound</h3>
          <label className="settings-toggle">
            <input
              type="checkbox"
              checked={sound}
              onChange={(e) => toggleSound(e.target.checked)}
            />
            Play a chime when the agent finishes a long task
          </label>
          {visibleExts.length > 0 && (
            <>
              <h3>Extensions</h3>
              {visibleExts.map((ext) => (
                <label className="settings-toggle" key={ext.id}>
                  <input
                    type="checkbox"
                    checked={ext.enabled}
                    onChange={(e) => toggleExtension(ext.id, e.target.checked)}
                  />
                  {ext.label}
                  {!ext.installed && (
                    <>
                      <span className="tag tag-off" style={{ marginLeft: 6 }}>
                        not installed
                      </span>
                      <button
                        className="rail-button"
                        style={{ marginLeft: 6, fontSize: '0.8em', padding: '2px 8px' }}
                        disabled={installing === ext.id}
                        onClick={(e) => {
                          e.preventDefault();
                          installExtension(ext.id);
                        }}
                      >
                        {installing === ext.id ? 'installing...' : 'install'}
                      </button>
                    </>
                  )}
                </label>
              ))}
            </>
          )}
          {plugins.length > 0 && (
            <>
              <h3>Plugins</h3>
              <p>Engine plugins for this project; a disabled plugin is never loaded.</p>
              {plugins.map((p) => (
                <label className="settings-toggle" key={p.id} title={p.description}>
                  <input
                    type="checkbox"
                    checked={p.enabled}
                    onChange={(e) => togglePlugin(p.id, e.target.checked)}
                  />
                  {p.name}
                  <span className="tag" style={{ marginLeft: 6 }}>
                    {p.version}
                  </span>
                  {p.state === "error" && (
                    <span className="tag tag-off" style={{ marginLeft: 6 }}>
                      error
                    </span>
                  )}
                </label>
              ))}
            </>
          )}
          <h3>Agents</h3>
          <p>Pick which one you chat with from the chat header.</p>
          {agentStatusState === "loading" && (
            <p className="settings-agent-state" role="status">checking agent status…</p>
          )}
          {agentStatusState === "error" && (
            <p className="settings-agent-error" role="alert">couldn’t check agent status</p>
          )}
          {agentStatusState === "ready" && (
            <>
              {agents.map((agent) => (
                <div className="settings-agent" key={agent.id}>
                  <span className="settings-agent-name">
                    {AGENT_LABEL[agent.id] ?? agent.label}
                  </span>
                  {agent.loggedIn === false ? (
                    <button
                      className="settings-action"
                      disabled={signingIn !== null}
                      onClick={() => {
                        setSignInError(null);
                        onSignIn(agent.id).catch((e) => setSignInError(String(e)));
                      }}
                    >
                      {signingIn === agent.id ? "signing in…" : "sign in"}
                    </button>
                  ) : (
                    <span className="settings-agent-state" title={agent.detail ?? undefined}>
                      {agent.loggedIn ? "signed in" : "status unknown"}
                    </span>
                  )}
                </div>
              ))}
              <button className="settings-agent-more" onClick={onMoreAgents}>
                need another agent?
              </button>
            </>
          )}
          {signInError && <p className="settings-agent-error" role="alert">{signInError}</p>}
        </div>
      </div>
    </div>
  );
}