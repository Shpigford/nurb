import { useEffect, useState } from "react";
import {
  Button,
  FloatingHeader,
  HeaderCell,
  HeaderDivider,
  HeaderStack,
  Icon,
  Lockup,
  PanelStrip,
  ParamSlider,
  Stage,
} from "@nurb/ui";
import { useLive } from "@nurb/workbench/live";
import { getSystem, setMeasurement, setSetting, type ProjectSystem } from "@nurb/workbench/api";

// Sheet 31: a project read as a system. The numbers its shared files agree on, the
// measurements taken off the real thing, and the pieces its parts are built from.
// Changing a number here rewrites it where it lives and the family rebuilds.

const SHOWN_MEASUREMENTS = 8;

function SectionHead({ title, note }: { title: string; note: string }) {
  return (
    <div className="flex flex-col gap-1">
      <h2 className="font-display text-[17px] leading-[22px] tracking-tight text-ink">{title}</h2>
      <p className="text-[13.5px] leading-[18px] text-muted">{note}</p>
    </div>
  );
}

function partsLabel(count: number) {
  return count === 1 ? "1 part" : `${count} parts`;
}

export default function ProjectPanel({
  projectId,
  name,
  onClose,
}: {
  projectId: string;
  name: string;
  onClose: () => void;
}) {
  const [system, setSystem] = useState<ProjectSystem | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  // Dragged but not applied, keyed "file.NAME".
  const [draft, setDraft] = useState<Record<string, number>>({});
  const [applying, setApplying] = useState(false);
  const [allMeasurements, setAllMeasurements] = useState(false);

  const load = () =>
    getSystem(projectId)
      .then(setSystem)
      .catch((e) => setFailure(e instanceof Error ? e.message : String(e)));
  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);
  // An agent can change a shared file or a measurement while this is open.
  useLive((event) => {
    if (event.project_id === projectId && (event.kind === "part" || event.kind === "project")) void load();
  });

  const settled = (next: ProjectSystem) => {
    setSystem(next);
    setFailure(null);
  };
  const fail = (e: unknown) => setFailure(e instanceof Error ? e.message : String(e));

  const apply = async () => {
    setApplying(true);
    try {
      for (const [key, value] of Object.entries(draft)) {
        const [file, setting] = key.split(".");
        settled(await setSetting(projectId, file, setting, value));
      }
      setDraft({});
    } catch (e) {
      fail(e);
    } finally {
      setApplying(false);
    }
  };

  const files = system?.files ?? [];
  // What the most parts lean on comes first; a file no part imports moves nothing.
  const tunable = files
    .filter((file) => file.settings.length > 0 && file.used_by.length > 0)
    .sort((a, b) => b.used_by.length - a.used_by.length);
  const pieces = files
    .flatMap((file) => file.pieces.map((piece) => ({ ...piece, file: file.name })))
    .filter((piece) => piece.used_by.length > 0)
    .sort((a, b) => b.used_by.length - a.used_by.length);
  // A guess waiting for a caliper first, then what the most parts read.
  const measurements = [...(system?.measurements ?? [])].sort(
    (a, b) => Number(b.provisional) - Number(a.provisional) || b.used_by.length - a.used_by.length,
  );
  const shownMeasurements = allMeasurements ? measurements : measurements.slice(0, SHOWN_MEASUREMENTS);
  const dirty = Object.keys(draft).length;
  const rebuilding = new Set(
    Object.keys(draft).flatMap((key) => files.find((file) => file.name === key.split(".")[0])?.used_by ?? []),
  ).size;
  const partCount = new Set(files.flatMap((file) => file.used_by)).size;

  return (
    <Stage
      header={
        <FloatingHeader
          dragRegion
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
                Back
              </button>
              <HeaderDivider />
              <HeaderStack label="PROJECT" value={name} />
            </>
          }
        />
      }
    >
      <div className="flex min-h-0 flex-1">
        <div className="panel mx-auto flex max-h-full w-full max-w-[640px] flex-col overflow-hidden">
          <PanelStrip
            label="Project"
            trailing={
              system ? `${partsLabel(partCount)} · ${files.length === 1 ? "1 shared file" : `${files.length} shared files`}` : undefined
            }
          />
          <div className="min-h-0 flex-1 overflow-y-auto">
            {failure ? (
              <p className="mono-caption border-b border-line-soft bg-fail-wash px-7 py-2.5 text-fail" role="alert">
                {failure}
              </p>
            ) : null}

            <section className="flex flex-col gap-3.5 px-7 py-5.5">
              <SectionHead
                title="Settings"
                note={
                  tunable.length > 0
                    ? `Numbers every part in ${name} shares. Change one and every part that uses it rebuilds.`
                    : `${name} has no shared numbers yet. Ask the agent to lift what its parts repeat into a shared file, and they show up here.`
                }
              />
              {tunable.map((file) => (
                <div key={file.name} className="flex flex-col gap-2">
                  {tunable.length > 1 ? <p className="mono-caption uppercase text-faint">{file.name}</p> : null}
                  <div className="-mx-4 grid grid-cols-2 gap-x-2 gap-y-3">
                    {file.settings.map((setting) => {
                      const key = `${file.name}.${setting.name}`;
                      return (
                        <div key={key} className="flex flex-col gap-1">
                          <ParamSlider
                            id={`setting-${key}`}
                            param={{ name: setting.name, kind: setting.kind, default: setting.value }}
                            value={draft[key] ?? setting.value}
                            dirty={key in draft}
                            restLabel="saved"
                            onValue={(value) =>
                              setDraft((current) => {
                                const next = { ...current };
                                if (value === setting.value) delete next[key];
                                else next[key] = value;
                                return next;
                              })
                            }
                          />
                          <p className="px-4 text-xs leading-4 text-muted">
                            {[setting.note, partsLabel(file.used_by.length)].filter(Boolean).join(" · ")}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
              {dirty > 0 ? (
                // Pinned to the panel's foot: the change can be far above it in a long system.
                <div className="chrome sticky bottom-3 z-10 flex h-9 items-center gap-2 rounded-content bg-accent-wash px-3 shadow-[var(--shadow-panel)]">
                  <span className="size-1.5 shrink-0 rounded-full bg-accent" />
                  <span className="mono-id flex-1 uppercase text-accent-ink tabular-nums [letter-spacing:0.08em]">
                    {dirty} {dirty === 1 ? "change" : "changes"}
                  </span>
                  <button
                    type="button"
                    onClick={() => setDraft({})}
                    className="mono-label rounded-control px-2 py-1 text-ink-soft transition-colors hover:text-ink"
                  >
                    Reset
                  </button>
                  <Button size="md" variant="ink" className="px-3" disabled={applying} onClick={() => void apply()}>
                    {applying ? "Applying" : `Apply to ${partsLabel(rebuilding)}`}
                  </Button>
                </div>
              ) : null}
            </section>

            <div className="h-px bg-line-soft" />

            <section className="flex flex-col gap-3.5 px-7 py-5.5">
              <SectionHead
                title="Measurements"
                note={
                  measurements.length > 0
                    ? "Taken off the real thing. Correct one and the parts that read it rebuild."
                    : `${name} has no measurements yet. The agent records them as it learns the real thing's sizes.`
                }
              />
              {measurements.length > 0 ? (
                <div className="flex flex-col">
                  {shownMeasurements.map((m) => (
                    <MeasurementRow
                      key={m.name}
                      measurement={m}
                      onValue={(value) => setMeasurement(projectId, m.name, value).then(settled).catch(fail)}
                    />
                  ))}
                  {measurements.length > SHOWN_MEASUREMENTS ? (
                    <button
                      type="button"
                      onClick={() => setAllMeasurements((v) => !v)}
                      className="mono-label mt-3 self-start text-accent-ink transition-colors hover:text-accent"
                    >
                      {allMeasurements ? "Show fewer" : `Show all ${measurements.length}`}
                    </button>
                  ) : null}
                </div>
              ) : null}
            </section>

            {pieces.length > 0 ? (
              <>
                <div className="h-px bg-line-soft" />
                <section className="flex flex-col gap-3.5 px-7 py-5.5">
                  <SectionHead
                    title="Shared pieces"
                    note="Shapes the parts are built from. Ask the agent to change one and every part that uses it follows."
                  />
                  <div className="flex flex-col">
                    {pieces.map((piece, index) => (
                      <div
                        key={`${piece.file}.${piece.name}`}
                        className={`flex h-10 items-center gap-3.5 ${index < pieces.length - 1 ? "border-b border-line-soft" : ""}`}
                      >
                        <span className="mono-id min-w-0 flex-1 truncate text-ink">{piece.name}</span>
                        <span className="mono-caption w-20 shrink-0 uppercase text-faint">{piece.file}</span>
                        <span className="mono-caption w-16 shrink-0 text-right uppercase text-muted">
                          {partsLabel(piece.used_by.length)}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              </>
            ) : null}
          </div>
        </div>
      </div>
    </Stage>
  );
}

function MeasurementRow({
  measurement,
  onValue,
}: {
  measurement: ProjectSystem["measurements"][number];
  onValue: (value: number) => void;
}) {
  const [text, setText] = useState(String(measurement.value_mm));
  useEffect(() => setText(String(measurement.value_mm)), [measurement.value_mm]);
  const commit = () => {
    const value = Number(text);
    if (!text.trim() || !Number.isFinite(value) || value === measurement.value_mm) {
      setText(String(measurement.value_mm));
      return;
    }
    onValue(value);
  };
  return (
    <div className="flex h-[52px] items-center gap-3.5 border-b border-line-soft">
      <div className="flex min-w-0 flex-1 flex-col gap-[3px]">
        <span className="mono-id flex items-center gap-2 text-ink">
          {measurement.name}
          {measurement.provisional ? (
            <span className="mono-caption rounded-[2px] border border-line px-1 uppercase text-faint">Provisional</span>
          ) : null}
        </span>
        <span className="truncate text-xs leading-4 text-muted" title={measurement.how}>
          {measurement.how}
        </span>
      </div>
      <span className="mono-caption w-16 shrink-0 text-right uppercase text-faint">
        {partsLabel(measurement.used_by.length)}
      </span>
      <label className="flex h-7 w-[92px] shrink-0 items-center justify-end gap-1 rounded-[3px] border border-line bg-ground px-2 focus-within:border-accent">
        <input
          aria-label={`${measurement.name} in millimetres`}
          inputMode="decimal"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === "Enter") e.currentTarget.blur();
            else if (e.key === "Escape") {
              setText(String(measurement.value_mm));
              e.currentTarget.blur();
            }
          }}
          className="mono-value w-full min-w-0 bg-transparent text-right text-ink focus:outline-none"
        />
        <span className="mono-caption text-faint">mm</span>
      </label>
    </div>
  );
}
