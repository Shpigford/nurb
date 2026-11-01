import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { AddPrinterDialog, Button, ProgressBar, PrinterMenu, ValueFlash, cue, type ExportStatus } from "@nurb/ui"
import {
  addPrinter,
  fetchPrinters,
  setPrinter,
  slicePart,
  type SliceResult,
  type Workshop,
} from "./api"
import { useLive } from "./live"

// "42g" is how the engine writes a weight; a row reads it with the unit off the number.
const spacedGrams = (weight?: string | null) => weight?.replace(/g$/, " g") ?? null

// The layer height belongs to the server's preset chain, so it is read back out of the
// chain rather than guessed: "prusa_mk4 / 0.20mm Standard @MK4 / PLA Basic" reads 0.2 mm.
function layerOf(settings?: string): string | null {
  const found = settings?.match(/(\d*\.\d+)\s*mm/i)
  return found ? `${Number(found[1])} mm` : null
}

// What the plate costs, from the slicer the user already has. It is the one fact about
// a part that the geometry cannot answer, so it is asked for rather than measured on
// every rebuild: a slice is seconds of a real slicer.
export default function Slice({
  partId,
  projectId,
  printer,
  runId,
  seed,
  onStatus,
  onManagePrinters,
}: {
  partId: string
  projectId: string
  /** The machine this part prices against: the project's, or the bench's default. */
  printer: string | null
  runId: string | null
  seed: SliceResult | null
  onStatus: (status: ExportStatus | null) => void
  /** Only the app has a Settings screen, so the menu's footer is only there. */
  onManagePrinters?: () => void
}) {
  const [result, setResult] = useState<SliceResult | null>(seed)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stale, setStale] = useState(false)
  const [picking, setPicking] = useState(false)
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [workshop, setWorkshop] = useState<Workshop | null>(null)
  const [benchError, setBenchError] = useState<string | null>(null)
  const shownFor = useRef(runId)
  const askedFor = useRef<string | null>(seed ? runId : null)
  // One trigger is on screen at a time: the menu is placed from it, and a press on
  // it must not count as a press outside the menu.
  const triggerRef = useRef<HTMLButtonElement>(null)

  // The bench, for the labels and for the catalogue the dialog offers. A bench that
  // did not load is the state that hides every way in, so it is kept and shown.
  const loadBench = useCallback(async () => {
    try {
      setWorkshop(await fetchPrinters())
      setBenchError(null)
    } catch (failure) {
      setBenchError(failure instanceof Error ? failure.message : "Your printers did not load.")
    }
  }, [])

  useEffect(() => {
    void loadBench()
  }, [loadBench])

  // Adding, removing or re-defaulting a printer happens in Settings, so this row
  // hears about it rather than waiting for the next build.
  useLive((event) => {
    if (event.kind === "workshop") void loadBench()
  })

  useEffect(() => {
    if (runId === shownFor.current) return
    shownFor.current = runId
    setError(null)
    setPicking(false)
    if (seed) {
      setResult(seed)
      setStale(false)
      return
    }
    if (!result) return
    setResult(null)
    setStale(true)
  }, [runId])

  // The download menu's estimate line is this tile's answer, seen from the other side.
  // An unchosen printer and a missing slicer are not failures, so they say nothing there.
  useEffect(() => {
    if (running) {
      onStatus({ state: "queued" })
    } else if (error) {
      onStatus({ state: "failed", error })
    } else if (result?.kind === "slice") {
      onStatus({ state: "succeeded", grams: result.grams, seconds: result.seconds })
    } else if (result && result.kind !== "choose" && result.kind !== "slicer") {
      onStatus({ state: "failed", error: result.error ?? "the slicer did not answer" })
    } else {
      onStatus(null)
    }
  }, [running, error, result, onStatus])

  const ask = useCallback(async () => {
    setRunning(true)
    setError(null)
    setStale(false)
    setPicking(false)
    cue("loading")
    try {
      const said = await slicePart(partId)
      setResult(said)
      shownFor.current = runId
      // A slice that came back without numbers is a refusal, not an answer.
      cue(said.kind === "slice" ? "ready" : "error")
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "The slicer did not answer.")
      cue("error")
    } finally {
      setRunning(false)
    }
  }, [partId, runId])

  // A bench with a printer on it has already answered the only question the slice
  // needs, so the row carries the number rather than a button that fetches it.
  useEffect(() => {
    if (!printer || !runId || result || running || error) return
    if (askedFor.current === runId) return
    askedFor.current = runId
    void ask()
  }, [printer, runId, result, running, error])

  const pick = async (profile: string) => {
    setPicking(false)
    try {
      await setPrinter(projectId, profile)
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "That printer did not stick.")
      return
    }
    await ask()
  }

  // The dialog owns the add itself and keeps its own refusal. Everything after the
  // add belongs to the row, because by then the dialog is gone.
  const add = async (profile: string) => {
    setBusy(true)
    setAddError(null)
    let added: Workshop
    try {
      added = await addPrinter(profile)
    } catch (failure) {
      setAddError(failure instanceof Error ? failure.message : "That printer did not save.")
      setBusy(false)
      return
    }
    setWorkshop(added)
    setBenchError(null)
    setBusy(false)
    setAdding(false)
    try {
      await setPrinter(projectId, profile)
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "That printer did not stick.")
      return
    }
    await ask()
  }

  const bench = workshop?.printers ?? []
  const labelOf = useCallback(
    (name: string) =>
      bench.find((p) => p.name === name)?.label ??
      workshop?.catalogue.find((p) => p.name === name)?.label ??
      name,
    [bench, workshop]
  )
  const options = useMemo(() => bench.map((p) => ({ name: p.name, label: p.label })), [bench])
  const fallbackDefault = bench.find((p) => p.default)?.name ?? null

  const kind = running ? null : result?.kind
  const sliced = kind === "slice" && result ? result : null
  const chosen = sliced?.profile ?? printer ?? null
  const layer = layerOf(sliced?.settings ?? undefined)
  // Nothing on the bench is the one state that has an answer the person can act on.
  // A part that already names a printer is not in it, whatever the bench list says.
  const empty = workshop !== null && bench.length === 0 && !printer

  // Whatever else the row is saying, the machine it is saying it about stays named
  // and stays changeable. An error with no way back out of it is a dead end.
  const printerLine = chosen ? (
    <div className="flex items-center justify-between gap-2" title={sliced?.settings}>
      <span className="mono-value uppercase text-ink">
        {[labelOf(chosen), layer].filter(Boolean).join(" · ")}
      </span>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setPicking((v) => !v)}
        aria-expanded={picking}
        className="btn-label shrink-0 text-accent-ink transition-opacity hover:opacity-70 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
      >
        change
      </button>
    </div>
  ) : null

  const dialog = adding && workshop ? (
    <AddPrinterDialog
      catalogue={workshop.catalogue}
      owned={bench.map((p) => p.name)}
      busy={busy}
      error={addError}
      onAdd={(name) => void add(name)}
      onClose={() => {
        setAdding(false)
        setAddError(null)
      }}
    />
  ) : null

  return (
    <div className="relative flex flex-col gap-1.5">
      {/* Always mounted: a live region only announces text that changes inside it. */}
      <div role="status" className="flex flex-col gap-1.5">
        {running ? (
          // The slicer never says how far along it is, so the bar crawls rather than lying.
          <ProgressBar value={null} label="Slicing" pendingLabel="working" />
        ) : error ? (
          <>
            {printerLine}
            <span className="text-[12px] leading-[17px] text-fail">{error}</span>
          </>
        ) : sliced ? (
          <>
            {printerLine}
            {/* Both figures move on their own after every rebuild, so both say which way. */}
            <span className="mono-value flex items-center gap-1 uppercase text-ink-soft">
              {sliced.grams ? (
                <ValueFlash value={sliced.grams} label="Weight" format={(g) => spacedGrams(sliced.weight) ?? `${g} g`} />
              ) : null}
              {sliced.grams && sliced.seconds ? <span aria-hidden>·</span> : null}
              {sliced.seconds ? (
                <ValueFlash value={sliced.seconds} label="Print time" format={() => sliced.spoken ?? ""} />
              ) : sliced.spoken ? (
                <span>{sliced.spoken}</span>
              ) : null}
            </span>
          </>
        ) : benchError ? (
          <div className="flex items-center justify-between gap-2">
            <span className="min-w-0 text-[12px] leading-[17px] text-fail">{benchError}</span>
            <button
              type="button"
              onClick={() => void loadBench()}
              className="btn-label shrink-0 text-accent-ink transition-opacity hover:opacity-70 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
            >
              try again
            </button>
          </div>
        ) : empty ? (
          <>
            <span className="text-[12px] leading-[17px] text-ink-soft">
              No printer yet. Add the one on your bench and the weight and print time show up here after
              every build.
            </span>
            <div className="flex items-center gap-2">
              <Button className="h-7" onClick={() => setAdding(true)}>
                Add a printer
              </Button>
              <span className="shrink-0 font-mono text-[10px] leading-4 tracking-[0.08em] text-faint uppercase">
                For every part
              </span>
            </div>
          </>
        ) : kind === "choose" ? (
          <>
            <span className="text-[12px] leading-[17px] text-ink-soft">Which printer is this part for?</span>
            {/* The server says nothing is decided yet, so this is the ask, not a swap. */}
            <button
              ref={triggerRef}
              type="button"
              onClick={() => setPicking((v) => !v)}
              aria-expanded={picking}
              className="btn-label self-start text-accent-ink transition-opacity hover:opacity-70 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
            >
              choose a printer
            </button>
          </>
        ) : kind === "slicer" ? (
          <>
            {printerLine}
            <span className="mono-value uppercase text-muted">no slicer found</span>
            <span className="text-[12px] leading-[17px] text-ink-soft">
              the 3mf download still works, for whatever you do slice with
            </span>
          </>
        ) : result ? (
          <>
            {printerLine}
            <span className="text-[12px] leading-[17px] text-fail">{result.error}</span>
          </>
        ) : stale ? (
          <>
            {printerLine}
            <div className="flex items-center justify-between gap-2">
              <span className="text-[12px] leading-[17px] text-ink-soft">The shape changed.</span>
              <button
                type="button"
                onClick={() => void ask()}
                className="btn-label shrink-0 text-accent-ink transition-opacity hover:opacity-70 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
              >
                price again
              </button>
            </div>
          </>
        ) : !runId ? (
          <span className="text-[12px] leading-[17px] text-ink-soft">Build the part first.</span>
        ) : null}
      </div>

      {picking ? (
        <PrinterMenu
          printers={options}
          current={chosen}
          defaultName={fallbackDefault}
          triggerRef={triggerRef}
          onPick={(name) => void pick(name)}
          onAdd={() => {
            setPicking(false)
            setAdding(true)
          }}
          onManage={
            onManagePrinters
              ? () => {
                  setPicking(false)
                  onManagePrinters()
                }
              : undefined
          }
          onClose={() => setPicking(false)}
        />
      ) : null}
      {dialog}
    </div>
  )
}
