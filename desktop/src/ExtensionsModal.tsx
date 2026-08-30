import { invoke } from "@tauri-apps/api/core";

// The developer-only extension surface. Everything here is experimental and
// opt-in: extensions are disabled by default, each card says plainly what the
// extension is (and is not), and nothing here implies official affiliation
// with the extension's vendor.

export type ExtensionStatus = {
  id: string;
  label: string;
  version: string;
  host: "terminal" | "externalApp";
  devOnly: boolean;
  installed: boolean;
  enabled: boolean;
  install: string;
  note: string;
};

export default function ExtensionsModal({
  statuses,
  projectDir,
  onChanged,
  onOpenTerminal,
  onClose,
}: {
  statuses: ExtensionStatus[];
  projectDir: string | null;
  onChanged: () => void;
  onOpenTerminal: (extension: ExtensionStatus) => void;
  onClose: () => void;
}) {
  const setEnabled = (id: string, enabled: boolean) => {
    invoke("set_extension_enabled", { id, enabled })
      .then(onChanged)
      .catch(() => {});
  };

  return (
    <div className="about" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="about-card">
        <button className="about-close" title="close" onClick={onClose}>
          ×
        </button>
        <div className="about-title">Developer extensions</div>
        <div className="about-body">
          <p>
            Experimental integrations, off by default. Each extension runs the
            vendor's own software; nurb only hosts or launches it.
          </p>
          {statuses.map((ext) => (
            <div className="agents-help-agent" key={ext.id}>
              <p>
                <b>{ext.label}</b> {ext.note}
              </p>
              <p className="ext-chips">
                <span className={`tag ${ext.installed ? "" : "tag-off"}`}>
                  {ext.installed ? "installed" : "not found"}
                </span>
                <span className={`tag ${ext.enabled ? "" : "tag-off"}`}>
                  {ext.enabled ? "enabled" : "disabled"}
                </span>
              </p>
              {!ext.installed && <pre>{ext.install}</pre>}
              <div className="ext-actions">
                {ext.enabled ? (
                  <>
                    {ext.host === "terminal" ? (
                      <button
                        className="rail-button"
                        disabled={!projectDir}
                        title={
                          projectDir
                            ? `open ${ext.label} in a terminal here`
                            : "open a project first"
                        }
                        onClick={() => onOpenTerminal(ext)}
                      >
                        open in terminal
                      </button>
                    ) : (
                      <button
                        className="rail-button"
                        onClick={() =>
                          invoke("launch_external_extension", { id: ext.id }).catch(() => {})
                        }
                      >
                        launch
                      </button>
                    )}
                    <button className="rail-button" onClick={() => setEnabled(ext.id, false)}>
                      disable
                    </button>
                  </>
                ) : (
                  <button className="rail-button" onClick={() => setEnabled(ext.id, true)}>
                    enable
                  </button>
                )}
              </div>
            </div>
          ))}
          {statuses.length === 0 && <p>No extensions shipped in this build.</p>}
        </div>
      </div>
    </div>
  );
}
