import { useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";
import { openUrl } from "@tauri-apps/plugin-opener";
import {
  Button,
  FloatingHeader,
  HeaderCell,
  HeaderDivider,
  HeaderStack,
  Icon,
  LoadingButton,
  Lockup,
  PanelStrip,
  Stage,
  AddPrinterDialog,
  bedLine,
  cue,
  readSoundPrefs,
  setSoundEnabled,
  setSoundVolume,
} from "@nurb/ui";
import {
  addPrinter,
  fetchPrinters,
  removePrinter,
  setDefaultPrinter,
  type Workshop,
} from "@nurb/workbench/api";
import { connectCommands, maskToken } from "./connect";
import About from "./About";
import { AGENT_LABEL } from "./Chat";

type SettingsAgent = {
  id: string;
  label: string;
  loggedIn: boolean | null;
  detail: string | null;
};

export type SettingsSection = "agents" | "printers" | "connect" | "general" | "about";

// The nav at the left, in the order a new user meets them.
const SECTIONS: { id: SettingsSection; label: string }[] = [
  { id: "agents", label: "Agents" },
  { id: "printers", label: "Printers" },
  { id: "connect", label: "Connect" },
  { id: "general", label: "General" },
  { id: "about", label: "About" },
];

export type AboutInfo = {
  appVersion: string;
  nurbVersion: string;
  occtVersion: string | null;
  osVersion: string;
  arch: string;
};

type Props = {
  // The agents installed on this Mac, so signing in lives with the rest of the
  // setup rather than beside the parts.
  agents: SettingsAgent[];
  agentStatusState: "loading" | "ready" | "error";
  signingIn: string | null;
  // The local endpoint an assistant on this Mac connects to, once it is up.
  serve: { url: string; port: number; token: string } | null;
  // Versions for the panel strip and the About section. Null until the shell has them.
  about: AboutInfo | null;
  // Optional, so the button only appears once the shell hands it the updater.
  onCheckUpdates?: () => void;
  // Which section opens first, so the printer row in the rail lands on Printers.
  initialSection?: SettingsSection;
  onSignIn: (id: string) => Promise<boolean>;
  onMoreAgents: () => void;
  onClose: () => void;
};

// The slicer's path is a path; the person recognises the folder it sits in.
function folderOf(path: string): string {
  const parts = path.split("/").filter(Boolean);
  return parts.length > 1 ? parts[parts.length - 2] : path;
}

// A section title and the line under it, the pair every block on this screen opens with.
function SectionHead({ title, note }: { title: string; note?: string }) {
  return (
    <div className="flex flex-col gap-1">
      <h2 className="font-display text-[17px] leading-[22px] tracking-tight text-ink">{title}</h2>
      {note ? <p className="text-[13.5px] leading-[18px] text-muted">{note}</p> : null}
    </div>
  );
}

export default function Settings({
  agents,
  agentStatusState,
  signingIn,
  serve,
  about,
  onCheckUpdates,
  initialSection = "agents",
  onSignIn,
  onMoreAgents,
  onClose,
}: Props) {
  const [section, setSection] = useState<SettingsSection>(initialSection);
  const [soundPrefs, setSoundPrefs] = useState(readSoundPrefs);
  // The rail's error line is on another screen, so a failed sign-in reports here.
  const [signInError, setSignInError] = useState<string | null>(null);
  // One key per copyable row, so only the row you pressed says so.
  const [copied, setCopied] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);
  // The bench. Every mutation answers with the whole list, so the rows update in place.
  const [workshop, setWorkshop] = useState<Workshop | null>(null);
  const [addingPrinter, setAddingPrinter] = useState(false);
  const [printerBusy, setPrinterBusy] = useState(false);
  const [printerError, setPrinterError] = useState<string | null>(null);
  // One object so the rows read from a single non-null value.
  const connect = serve ? { ...connectCommands(serve), token: serve.token } : null;
  // The nav's trailing captions, present only once there is an answer to show.
  const signedIn = agents.filter((agent) => agent.loggedIn).length;
  const counts: Partial<Record<SettingsSection, string>> = {
    agents: agentStatusState === "ready" ? `${signedIn}/${agents.length}` : undefined,
    printers: workshop ? String(workshop.printers.length) : undefined,
  };

  useEffect(() => {
    let live = true;
    fetchPrinters()
      .then((said) => live && setWorkshop(said))
      .catch((e) => live && setPrinterError(e instanceof Error ? e.message : String(e)));
    return () => {
      live = false;
    };
  }, []);

  const printerAction = async (run: () => Promise<Workshop>) => {
    setPrinterBusy(true);
    setPrinterError(null);
    try {
      setWorkshop(await run());
      setAddingPrinter(false);
    } catch (e) {
      setPrinterError(e instanceof Error ? e.message : String(e));
    } finally {
      setPrinterBusy(false);
    }
  };

  const copy = (key: string, text: string) => {
    writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied((current) => (current === key ? null : current)), 1500);
    });
  };

  // A call rather than a component, so pressing it does not remount the button.
  const copyButton = (name: string, text: string) => (
    <Button aria-live="polite" onClick={() => copy(name, text)}>
      {copied === name ? "Copied" : "Copy"}
    </Button>
  );

  // Both controls preview a cue, so the choice is audible where it is made.
  const toggleSound = (on: boolean) => {
    setSoundEnabled(on);
    setSoundPrefs((prefs) => ({ ...prefs, enabled: on }));
    if (on) cue("ready");
  };

  const changeVolume = (volume: number) => {
    setSoundVolume(volume);
    setSoundPrefs((prefs) => ({ ...prefs, volume }));
    if (soundPrefs.enabled) cue("ready");
  };

  // A command and the button that copies it: label, raised block, action.
  const commandRow = (label: string, command: string, action?: ReactNode) => (
    <div className="flex flex-col gap-1.5">
      <div className="mono-label text-muted">{label}</div>
      <div className="flex items-center gap-2.5">
        <code className="grow overflow-hidden rounded-[6px] bg-raised px-3 py-2 font-mono text-[11px] leading-4 break-all text-ink-soft">
          {command}
        </code>
        {action}
        {copyButton(label, command)}
      </div>
    </div>
  );

  return (
    <Stage
      header={
        <FloatingHeader
          cells={
            <>
              <div className="h-full w-[92px] shrink-0" data-tauri-drag-region />
              <HeaderDivider />
              <HeaderCell>
                <Lockup />
              </HeaderCell>
              <HeaderDivider />
              <button
                type="button"
                onClick={onClose}
                className="chrome mono-label flex h-full items-center gap-2 px-4 text-muted transition-colors hover:text-ink"
              >
                <Icon name="chevron-left" />
                Library
              </button>
              <HeaderDivider />
              <HeaderStack label="NURB" value="Settings" />
            </>
          }
        />
      }
    >
      <div className="flex min-h-0 flex-1">
        <div className="panel mx-auto flex h-[620px] max-h-full w-full max-w-[920px] flex-col overflow-hidden">
          <PanelStrip label="Settings" trailing={about ? `nurb ${about.appVersion}` : undefined} />

          <div className="flex min-h-0 flex-1">
            <nav
              aria-label="Settings sections"
              className="flex w-[212px] shrink-0 flex-col gap-0.5 border-r border-line-soft px-2.5 py-3.5"
            >
              {SECTIONS.map((entry) => {
                const selected = entry.id === section;
                return (
                  <button
                    type="button"
                    key={entry.id}
                    aria-current={selected ? "page" : undefined}
                    onClick={() => setSection(entry.id)}
                    className={`flex h-[30px] w-full shrink-0 cursor-default items-center gap-2 rounded-[3px] px-2.5 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent ${
                      selected ? "bg-raised" : "hover:bg-raised/60"
                    } ${entry.id === "about" ? "mt-auto" : ""}`}
                  >
                    <span className="mono-value min-w-0 flex-1 truncate text-left text-ink uppercase">
                      {entry.label}
                    </span>
                    {counts[entry.id] ? (
                      <span className="mono-caption shrink-0 text-muted">{counts[entry.id]}</span>
                    ) : null}
                  </button>
                );
              })}
            </nav>

            <div className="min-w-0 flex-1 overflow-y-auto">
              {section === "agents" ? (
                <section className="flex flex-col gap-3.5 px-7 py-5.5">
                  <SectionHead
                    title="Agents"
                    note="The agent does the modelling. Sign in once; it stays signed in."
                  />
                  {agentStatusState === "loading" && (
                    <p className="mono-label text-muted" role="status">
                      Checking agents
                    </p>
                  )}
                  {agentStatusState === "error" && (
                    <p className="mono-label text-fail" role="alert">
                      Could not check the agents
                    </p>
                  )}
                  {agentStatusState === "ready" && (
                    <>
                      <div className="flex flex-col">
                        {agents.map((agent, index) => (
                          <div
                            className={`flex h-10 shrink-0 items-center justify-between ${
                              index === agents.length - 1 ? "" : "border-b border-line-soft"
                            }`}
                            key={agent.id}
                          >
                            <span className="font-mono text-[11px] text-ink">
                              {AGENT_LABEL[agent.id] ?? agent.label}
                            </span>
                            {agent.loggedIn === false ? (
                              <LoadingButton
                                label={agent.id === "gemini" ? "Add key" : "Sign in"}
                                pendingLabel="Signing in"
                                successLabel="Signed in"
                                errorLabel="Try again"
                                disabled={signingIn !== null && signingIn !== agent.id}
                                onAction={async () => {
                                  setSignInError(null);
                                  let signed: boolean;
                                  try {
                                    signed = await onSignIn(agent.id);
                                  } catch (e) {
                                    setSignInError(String(e));
                                    throw e;
                                  }
                                  // The key prompt was closed without a key, so
                                  // nothing was signed in and the button says so.
                                  if (!signed) throw new Error("No key");
                                  cue("success");
                                }}
                              />
                            ) : agent.loggedIn ? (
                              <span className="btn-label flex items-center gap-1.5 text-pass" title={agent.detail ?? undefined}>
                                <Icon name="check" />
                                Signed in
                              </span>
                            ) : (
                              <span className="btn-label text-muted" title={agent.detail ?? undefined}>
                                Status unknown
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                      <button
                        type="button"
                        className="chrome mono-label self-start text-accent-ink transition-colors hover:text-accent"
                        onClick={onMoreAgents}
                      >
                        + Add an agent
                      </button>
                    </>
                  )}
                  {signInError && (
                    <p className="mono-label text-fail" role="alert">
                      {signInError}
                    </p>
                  )}
                </section>
              ) : null}

              {section === "printers" ? (
                <section className="flex flex-col gap-3.5 px-7 py-5.5">
                  <SectionHead
                    title="Printers"
                    note="The machines on your bench. Checks use the bed size; slicing uses the slicer's own profile for it."
                  />
                  <div className="flex flex-col">
                    {(workshop?.printers ?? []).map((printer, index) => (
                      <div
                        className={`flex h-12 shrink-0 items-center gap-3 ${
                          index === (workshop?.printers.length ?? 0) - 1 ? "" : "border-b border-line-soft"
                        }`}
                        key={printer.name}
                      >
                        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                          <span className="truncate font-mono text-[11px] leading-4 text-ink">{printer.label}</span>
                          <span className="truncate font-mono text-[10px] leading-4 tracking-[0.08em] text-muted uppercase">
                            {bedLine(printer.bed)} MM · 0.4 nozzle
                          </span>
                        </div>
                        <div className="flex w-28 shrink-0 justify-end">
                          {printer.default ? (
                            <span className="flex items-center gap-1 rounded-[2px] border border-line px-1.5 py-0.5 font-mono text-[9px] leading-3 tracking-[0.08em] text-muted uppercase">
                              <Icon name="check" />
                              Default
                            </span>
                          ) : (
                            <button
                              type="button"
                              disabled={printerBusy}
                              onClick={() => void printerAction(() => setDefaultPrinter(printer.name))}
                              className="chrome font-mono text-[10px] leading-4 tracking-[0.08em] text-muted uppercase transition-colors hover:text-ink disabled:opacity-50"
                            >
                              Make default
                            </button>
                          )}
                        </div>
                        <div className="flex w-14 shrink-0 justify-end">
                          <button
                            type="button"
                            disabled={printerBusy}
                            onClick={() => void printerAction(() => removePrinter(printer.name))}
                            className="chrome font-mono text-[10px] leading-4 tracking-[0.08em] text-faint uppercase transition-colors hover:text-fail disabled:opacity-50"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    ))}
                    {workshop && workshop.printers.length === 0 ? (
                      <p className="text-[13.5px] leading-[18px] text-muted">No printers yet.</p>
                    ) : null}
                  </div>
                  <button
                    type="button"
                    className="chrome mono-label self-start text-accent-ink transition-colors hover:text-accent"
                    onClick={() => setAddingPrinter(true)}
                  >
                    + Add a printer
                  </button>
                  {printerError ? (
                    <p className="mono-label text-fail" role="alert">
                      {printerError}
                    </p>
                  ) : null}

                  <div className="h-px bg-line-soft" />

                  <div className="flex items-start justify-between gap-6">
                    <div className="flex min-w-0 flex-col gap-1">
                      <span className="font-mono text-[10px] leading-4 tracking-[0.08em] text-muted uppercase">
                        Slicer
                      </span>
                      {workshop?.slicer ? (
                        <span className="flex items-center gap-1.5 font-mono text-[11px] leading-4 text-ink">
                          <span className="text-pass">
                            <Icon name="check" />
                          </span>
                          {workshop.slicer.name} · in {folderOf(workshop.slicer.path)}
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 font-mono text-[11px] leading-4 text-ink">
                          <span className="text-warn">
                            <Icon name="warning" />
                          </span>
                          No slicer found
                        </span>
                      )}
                    </div>
                    {workshop?.slicer ? (
                      <p className="w-[240px] shrink-0 text-right text-[12px] leading-4 text-muted">
                        Weight and print time come from here. Without it, downloads still work.
                      </p>
                    ) : (
                      <button
                        type="button"
                        onClick={() =>
                          openUrl("https://github.com/SoftFever/OrcaSlicer/releases").catch(() => {})
                        }
                        className="chrome w-[240px] shrink-0 text-right text-[12px] leading-4 text-muted underline underline-offset-2 transition-colors hover:text-ink"
                      >
                        Install OrcaSlicer and weight and print time appear. Downloads work either way.
                      </button>
                    )}
                  </div>
                </section>
              ) : null}

              {section === "about" && about ? <About {...about} onCheckUpdates={onCheckUpdates} /> : null}

              {section === "general" ? (
                <section className="flex flex-col gap-3.5 px-7 py-5.5">
                  <SectionHead title="General" note="How nurb behaves on this Mac." />
                  <div className="flex flex-col gap-2.5 border-y border-line-soft py-2.5">
                    <div className="flex items-center justify-between gap-6">
                      <div className="flex min-w-0 flex-col gap-0.5">
                        <span className="font-mono text-[11px] text-ink">Sounds</span>
                        <span className="text-[13.5px] leading-[18px] text-muted">
                          Short cues when a build finishes, a link is copied, or something needs you.
                        </span>
                      </div>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={soundPrefs.enabled}
                        aria-label="Play sounds"
                        onClick={() => toggleSound(!soundPrefs.enabled)}
                        className={`flex h-[18px] w-8 shrink-0 items-center rounded-full px-0.5 transition-colors ${
                          soundPrefs.enabled ? "justify-end bg-accent" : "justify-start bg-line"
                        }`}
                      >
                        <span className="size-3.5 shrink-0 rounded-full bg-white" />
                      </button>
                    </div>
                    {soundPrefs.enabled ? (
                      <div className="flex items-center gap-3">
                        <span className="mono-label w-12 shrink-0 text-muted">Volume</span>
                        <input
                          type="range"
                          min={0}
                          max={1}
                          step={0.05}
                          value={soundPrefs.volume}
                          aria-label="Volume"
                          onChange={(event) => changeVolume(Number(event.target.value))}
                          style={{ "--pct": soundPrefs.volume } as CSSProperties}
                          className="param-slider grow"
                        />
                      </div>
                    ) : null}
                  </div>
                </section>
              ) : null}

              {section === "connect" ? (
                <section className="flex flex-col gap-4 px-7 py-5.5">
                  <SectionHead
                    title="Connect another agent"
                    note="An agent outside nurb can open and build your parts at this address. Keep nurb open while you use it."
                  />
                  {!connect ? (
                    <p className="mono-label text-muted">Starting the engine</p>
                  ) : (
                    <>
                      <div className="flex flex-col gap-3">
                        <div className="flex items-end justify-between gap-4">
                          <div className="flex flex-col gap-[5px] overflow-hidden">
                            <div className="mono-label text-muted">Address</div>
                            <div className="truncate font-mono text-[12px] leading-4 text-ink">
                              {connect.mcpUrl}
                            </div>
                          </div>
                          {copyButton("address", connect.mcpUrl)}
                        </div>
                        <div className="flex items-end justify-between gap-4">
                          <div className="flex flex-col gap-[5px] overflow-hidden">
                            <div className="mono-label text-muted">Token</div>
                            <div className="truncate font-mono text-[12px] leading-4 text-ink">
                              {revealed ? connect.token : maskToken(connect.token)}
                            </div>
                          </div>
                          <div className="flex shrink-0 items-center gap-2">
                            <Button onClick={() => setRevealed(!revealed)}>
                              {revealed ? "Hide" : "Reveal"}
                            </Button>
                            {copyButton("token", connect.token)}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col gap-2.5">
                        {commandRow("Claude Code", connect.claudeCode)}
                        {commandRow("Codex CLI", connect.codexCli)}
                        {commandRow(
                          "Cursor",
                          connect.cursorConfig,
                          <Button
                            variant="accent"
                            onClick={() => openUrl(connect.cursorLink).catch(() => {})}
                          >
                            Add to Cursor
                          </Button>
                        )}
                      </div>
                    </>
                  )}
                </section>
              ) : null}

            </div>
          </div>
        </div>
      </div>
      {addingPrinter && workshop ? (
        <AddPrinterDialog
          catalogue={workshop.catalogue}
          owned={workshop.printers.map((printer) => printer.name)}
          busy={printerBusy}
          error={printerError}
          onAdd={(name) => void printerAction(() => addPrinter(name))}
          onClose={() => {
            setAddingPrinter(false);
            setPrinterError(null);
          }}
        />
      ) : null}
    </Stage>
  );
}
