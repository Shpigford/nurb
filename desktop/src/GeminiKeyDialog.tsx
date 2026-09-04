import { FormEvent, useState } from "react";
import { openUrl } from "@tauri-apps/plugin-opener";
import { isWindows } from "./platform";

type Props = {
  onSubmit: (key: string) => void;
  onClose: () => void;
};

export default function GeminiKeyDialog({ onSubmit, onClose }: Props) {
  const [key, setKey] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const value = key.trim();
    if (value) onSubmit(value);
  };

  return (
    <div
      className="about"
      onClick={(event) =>
        event.target === event.currentTarget ? onClose() : null
      }
    >
      <form
        className="about-card api-key-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gemini-key-title"
        onSubmit={submit}
      >
        <button
          type="button"
          className="about-close"
          title="close"
          onClick={onClose}
        >
          ×
        </button>
        <div className="about-title" id="gemini-key-title">
          Connect Gemini
        </div>
        <div className="about-body">
          <label className="api-key-label" htmlFor="gemini-api-key">
            Gemini API key
          </label>
          <input
            id="gemini-api-key"
            className="api-key-input"
            type="password"
            value={key}
            onChange={(event) => setKey(event.target.value)}
            autoComplete="off"
            autoFocus
          />
          <div className="api-key-meta">
            <button
              type="button"
              className="about-copy"
              onClick={() => openUrl("https://aistudio.google.com/apikey")}
            >
              Create a key in Google AI Studio
            </button>
            <span>{isWindows ? "Stored in Windows Credential Manager." : "Stored in macOS Keychain."}</span>
          </div>
          <div className="settings-actions">
            <button
              className="settings-action"
              type="submit"
              disabled={!key.trim()}
            >
              Connect
            </button>
            <button
              className="settings-action secondary"
              type="button"
              onClick={onClose}
            >
              Cancel
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
