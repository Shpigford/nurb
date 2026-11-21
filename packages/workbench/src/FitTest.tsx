import { useState, type ReactNode } from "react"
import { Button, Icon, words } from "@nurb/ui"
import { confirmFit, type Part, type ProjectMeasurement } from "./api"
import { fitTestFor, isFitTest, LONG_PRINT_S, parentOf, untested } from "./fits"

function hours(seconds: number): string {
  const minutes = Math.round(seconds / 60)
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h === 0 ? `${m} min` : m === 0 ? `${h} h` : `${h} h ${m} min`
}

function list(names: string[]): string {
  const said = names.map((name) => words(name).toLowerCase())
  return said.length < 2 ? said.join("") : `${said.slice(0, -1).join(", ")} and ${said[said.length - 1]}`
}

const title = (part: Part) => part.title ?? words(part.name)

// Sits above Download. A long print that fits a real object gets a fit test first,
// because finding out a fit is loose after five hours of printing is the expensive way.
export default function FitTest({
  part,
  parts,
  measurements,
  seconds,
  atSavedValues = true,
  onSelectPart,
  onAsk,
}: {
  part: Part
  parts: Part[]
  measurements: ProjectMeasurement[]
  /** The sliced print time, null until there is one. */
  seconds: number | null
  atSavedValues?: boolean
  onSelectPart?: (name: string) => void
  /** Writes a request in the chat for the person to send. */
  onAsk?: (text: string) => void
}) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const owed = untested(part, measurements)

  if (isFitTest(part.name)) {
    const parent = parentOf(part, parts)
    if (owed.length === 0) {
      if (!parent || !onSelectPart) return null
      return (
        <Card icon="check" heading="Fit confirmed">
          <p className="text-xs leading-4 text-muted">
            {untested(parent, measurements).length === 0
              ? `${title(parent)} has no untested fits.`
              : `${title(parent)} still has fits nobody has printed.`}
          </p>
          <div className="mt-1 flex">
            <Button size="sm" onClick={() => onSelectPart(parent.name)}>
              Open {title(parent)}
            </Button>
          </div>
        </Card>
      )
    }
    const exportId = atSavedValues ? part.fit_export_id : null
    const confirm = async () => {
      if (!exportId) return
      setSaving(true)
      setError(null)
      try {
        await confirmFit(part.id, exportId)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setSaving(false)
      }
    }
    return (
      <Card icon="ruler" heading="Did it fit?">
        <p className="text-xs leading-4 text-muted">
          {exportId
            ? `Print the latest download and try it on the real thing. It tests ${list(owed)}.`
            : `Download an STL or 3MF at the saved dimensions, then print it to test ${list(owed)}.`}
        </p>
        <div className="mt-1 grid grid-cols-2 gap-1.5">
          <Button size="sm" variant="ink" className="col-span-2" disabled={saving || !exportId} onClick={() => void confirm()}>
            {saving ? "Saving…" : "It fits"}
          </Button>
          {onAsk ? (
            <>
              <Button size="sm" title="Writes it in the chat for you to send" onClick={() => onAsk(LOOSE)}>
                Too loose
              </Button>
              <Button size="sm" title="Writes it in the chat for you to send" onClick={() => onAsk(TIGHT)}>
                Too tight
              </Button>
            </>
          ) : null}
        </div>
        {error ? <p className="text-xs leading-4 text-fail">{error}</p> : null}
        {parent && onSelectPart ? (
          <button
            type="button"
            onClick={() => onSelectPart(parent.name)}
            className="mono-caption flex items-center gap-1 self-start text-muted transition-colors hover:text-ink"
          >
            <Icon name="chevron-left" />
            Back to {title(parent)}
          </button>
        ) : null}
      </Card>
    )
  }

  if (owed.length === 0 || (seconds !== null && seconds < LONG_PRINT_S)) return null
  const test = fitTestFor(part, parts, owed)
  const open = test && onSelectPart ? () => onSelectPart(test.name) : null
  const ask = seconds !== null && onAsk ? () => onAsk(askFor(owed)) : null
  return (
    <Card icon="warning" heading="Fit not tested">
      <p className="text-xs leading-4 text-muted">
        {words(list(owed))} {owed.length === 1 ? "has" : "have"} not been printed yet.{" "}
        {seconds !== null
          ? `Print a small fit test before committing to a ${hours(seconds)} print.`
          : "Slice this part to estimate its print time."}
      </p>
      <div className="mt-1 flex">
        {open ? (
          <Button size="sm" variant="ink" onClick={open}>
            Open fit test
          </Button>
        ) : ask ? (
          <Button
            size="sm"
            variant="ink"
            icon="chat"
            title="Writes the request in the chat for you to send"
            onClick={ask}
          >
            Ask for a fit test
          </Button>
        ) : null}
      </div>
    </Card>
  )
}

const LOOSE = "The fit test came out too loose. "
const TIGHT = "The fit test came out too tight. "
const askFor = (owed: string[]) =>
  `Make a fit test for this part before I print it. It should test ${list(owed)} and take a few minutes of filament.`

export function Card({ icon, heading, children }: { icon: "ruler" | "warning" | "check" | "box"; heading: string; children: ReactNode }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-[6px] border border-line">
      <div className="chrome flex h-[30px] items-center border-b border-line-soft bg-raised px-3">
        <span className="mono-label flex items-center gap-2 text-ink">
          <Icon name={icon} />
          {heading}
        </span>
      </div>
      <div className="flex flex-col gap-1.5 px-3 pt-[9px] pb-2.5">{children}</div>
    </div>
  )
}
