import { useCallback, useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { Terminal } from "xterm";
import { FitAddon } from "@xterm/addon-fit";
import "xterm/css/xterm.css";

// The terminal host surface for a developer extension:
// an xterm.js panel fed byte-for-byte by the ConPTY session in terminal.rs.
// The panel only transports bytes - keystrokes go to the child, output comes
// back - so what the user sees is the official CLI exactly as it would run in
// any terminal emulator.

type OutputEvent = { id: string; data: string }; // data is base64: not UTF-8
type ExitEvent = { id: string; code: number | null };

function base64ToBytes(data: string): Uint8Array {
  const bin = atob(data);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

export default function TerminalPanel({
  id,
  label,
  projectDir,
  onClose,
}: {
  id: string;
  label: string;
  projectDir: string;
  onClose: () => void;
}) {
  // The panel's own session handle, distinct from the extension id: the Rust
  // host keys live sessions by this, so two panels of the same extension stay
  // separate sessions instead of colliding in one map entry. Fixed per mount;
  // reopening the panel gets a fresh id.
  const [sessionId] = useState(() => `${id}-${Math.random().toString(36).slice(2, 10)}`);
  const hostRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [exited, setExited] = useState<number | null>(null);

  const resize = useCallback(
    (term: Terminal) => {
      invoke("terminal_resize", {
        id: sessionId,
        cols: term.cols,
        rows: term.rows,
      }).catch(() => {});
    },
    [sessionId],
  );

  useEffect(() => {
    const term = new Terminal({
      convertEol: true,
      cursorBlink: true,
      fontSize: 13,
      fontFamily:
        'Consolas, "Cascadia Mono", "Courier New", monospace',
      theme: { background: "#141414", foreground: "#e8e8e8" },
    });
    const fit = new FitAddon();
    term.loadAddon(fit);
    termRef.current = term;
    if (hostRef.current) term.open(hostRef.current);
    fit.fit();

    // Keystrokes go straight to the child; nothing else ever writes input.
    term.onData((data) => {
      invoke("terminal_input", { id: sessionId, data }).catch((e) =>
        setError(String(e)),
      );
    });
    term.onResize(() => resize(term));

    invoke("open_terminal_extension", {
      session: sessionId,
      extension: id,
      projectDir,
      cols: term.cols,
      rows: term.rows,
    }).catch((e) => setError(String(e)));

    const ro = new ResizeObserver(() => {
      fit.fit();
      resize(term);
    });
    if (hostRef.current) ro.observe(hostRef.current);

    let unlistenOutput: (() => void) | undefined;
    let unlistenExit: (() => void) | undefined;
    listen<OutputEvent>("terminal-output", (event) => {
      if (event.payload.id === sessionId) {
        term.write(base64ToBytes(event.payload.data));
      }
    }).then((fn) => (unlistenOutput = fn));
    listen<ExitEvent>("terminal-exit", (event) => {
      if (event.payload.id === sessionId) setExited(event.payload.code ?? 0);
    }).then((fn) => (unlistenExit = fn));

    return () => {
      ro.disconnect();
      unlistenOutput?.();
      unlistenExit?.();
      invoke("terminal_close", { id: sessionId }).catch(() => {});
      term.dispose();
      termRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, id, projectDir]);

  return (
    <div className="about" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="about-card terminal-card">
        <div className="terminal-head">
          <span className="terminal-title">{label}</span>
          <button className="about-close" title="close" onClick={onClose}>
            ×
          </button>
        </div>
        {error && <div className="terminal-error">{error}</div>}
        {exited !== null && (
          <div className="terminal-error">
            session ended (exit {exited})
          </div>
        )}
        <div className="terminal-host" ref={hostRef} />
      </div>
    </div>
  );
}
