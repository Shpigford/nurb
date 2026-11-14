import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { openUrl } from "@tauri-apps/plugin-opener";
import { Button, IconButton, PanelStrip } from "@nurb/ui";
import { AGENT_LABEL } from "./Chat";

type MissingAgent = {
  id: string;
  label: string;
  note: string;
  install: string | null;
};

type Props = {
  // The supported agents that are not on this Mac, each with its vendor's installer.
  missing: MissingAgent[];
  // Present when the app is waiting on a Gemini key; the key section is shown then.
  onSubmitGeminiKey?: (key: string) => void;
  onClose: () => void;
};

// The raised 56px row every agent in this dialog opens with.
function AgentRow({
  name,
  status,
  action,
}: {
  name: string;
  status: string;
  action: ReactNode;
}) {
  return (
    <div className="flex h-14 shrink-0 items-center justify-between rounded-[6px] bg-raised px-4">
      <div className="flex flex-col gap-[3px]">
        <div className="font-mono text-[12px] leading-4 text-ink">{name}</div>
        <div className="mono-caption text-muted">{status}</div>
      </div>
      {action}
    </div>
  );
}

/// One door for every way of adding an agent: the ones missing from this Mac,
/// with their vendor's install line, and the key Gemini needs before it runs.
export default function AddAgent({ missing, onSubmitGeminiKey, onClose }: Props) {
  const [shown, setShown] = useState<string | null>(null);
  const [key, setKey] = useState("");

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const value = key.trim();
    if (value && onSubmitGeminiKey) onSubmitGeminiKey(value);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-scrim/30 p-6"
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <form
        className="panel flex max-h-full w-[520px] flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Add an agent"
        onSubmit={submit}
      >
        <PanelStrip
          label="Add an agent"
          inset={16}
          trailing={<IconButton icon="xmark" label="Close" onClick={onClose} className="-mr-2" />}
        />
        <div className="flex flex-col gap-4 overflow-y-auto px-5 pt-5 pb-1">
          <p className="text-[14px] leading-5 text-ink-soft">
            nurb talks to the coding agent you already use. Pick one.
          </p>

          {missing.map((agent) => (
            <div className="flex flex-col gap-2.5" key={agent.id}>
              <AgentRow
                name={AGENT_LABEL[agent.id] ?? agent.label}
                status={agent.note}
                action={
                  agent.install ? (
                    <Button onClick={() => setShown(shown === agent.id ? null : agent.id)}>
                      {shown === agent.id ? "Hide" : "Show how"}
                    </Button>
                  ) : null
                }
              />
              {agent.install && shown === agent.id ? (
                <div className="flex flex-col gap-2 px-4">
                  <p className="text-[12px] leading-4 text-muted">
                    Install it from the terminal, then come back here and sign in.
                  </p>
                  <code className="rounded-[6px] bg-raised px-3.5 py-2.5 font-mono text-[11px] leading-4 break-all text-ink-soft">
                    {agent.install}
                  </code>
                </div>
              ) : null}
            </div>
          ))}

          {onSubmitGeminiKey ? (
            <div className="flex flex-col gap-2.5">
              <AgentRow name="Gemini" status="Needs an API key" action={null} />
              <div className="flex flex-col gap-2 px-4">
                <input
                  id="gemini-api-key"
                  aria-label="Gemini API key"
                  placeholder="Paste your API key"
                  className="h-8 shrink-0 rounded-[3px] border border-line bg-ground px-3 font-mono text-[11px] text-ink placeholder:text-faint focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
                  type="password"
                  value={key}
                  onChange={(event) => setKey(event.target.value)}
                  autoComplete="off"
                  autoFocus
                />
                <div className="flex items-center justify-between gap-4">
                  <span className="mono-caption text-muted">Stored in your Mac's keychain</span>
                  <button
                    type="button"
                    className="chrome mono-caption shrink-0 font-medium text-accent-ink transition-colors hover:text-accent"
                    onClick={() => openUrl("https://aistudio.google.com/apikey").catch(() => {})}
                  >
                    Create a key in Google AI Studio
                  </button>
                </div>
              </div>
            </div>
          ) : null}

          {missing.length === 0 && !onSubmitGeminiKey ? (
            <p className="text-[13.5px] leading-[18px] text-muted">
              Every agent nurb works with is already on this Mac.
            </p>
          ) : null}

          <p className="text-[13.5px] leading-[18px] text-muted">
            Using one that isn't here?{" "}
            <button
              type="button"
              className="text-accent-ink underline underline-offset-2 transition-colors hover:text-accent"
              onClick={() => openUrl("https://github.com/Shpigford/nurb/issues/new?template=feature_request.yml").catch(() => {})}
            >
              Ask us for it.
            </button>
          </p>
        </div>
        <div className="flex shrink-0 items-center justify-end gap-2 px-5 pt-4 pb-5">
          <Button size="md" className="px-3.5" onClick={onClose}>
            Cancel
          </Button>
          {onSubmitGeminiKey ? (
            <Button variant="accent" size="md" className="px-3.5" type="submit" disabled={!key.trim()}>
              Connect
            </Button>
          ) : null}
        </div>
      </form>
    </div>
  );
}
