import { useState } from "react";
import { open as pickFolder } from "@tauri-apps/plugin-dialog";
import { playChime, setSoundEnabled, soundEnabled } from "./chime";
import { AGENT_LABEL } from "./Chat";

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
  // The agents installed on this machine, so signing in lives with the rest of
  // the setup rather than beside the parts.
  agents: SettingsAgent[];
  agentStatusState: "loading" | "ready" | "error";
  signingIn: string | null;
  onSignIn: (id: string) => Promise<boolean>;
  onMoreAgents: () => void;
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
