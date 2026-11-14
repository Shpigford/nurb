import { useEffect, useMemo, useState } from "react"
import clsx from "clsx"
import Button, { IconButton } from "./Button"
import Icon from "./Icon"
import PanelStrip from "./PanelStrip"

/** A shipped profile, as the catalogue lists it. */
export interface PrinterCatalogueEntry {
  name: string
  label: string
  brand: string
  bed: number[]
}

export interface AddPrinterDialogProps {
  catalogue: PrinterCatalogueEntry[]
  /** Names already on the bench: they show, dimmed, so the list stays the same shape. */
  owned: string[]
  busy?: boolean
  error?: string | null
  onAdd: (name: string) => void
  onClose: () => void
}

export const bedLine = (bed: number[] | null | undefined) =>
  bed && bed.length === 3 ? bed.map((n) => Math.round(n)).join(" × ") : ""

// Picking the machine on the bench. The bed size is the only number the checks
// read, so it is the one fact every row carries.
export default function AddPrinterDialog({
  catalogue,
  owned,
  busy,
  error,
  onAdd,
  onClose,
}: AddPrinterDialogProps) {
  const [query, setQuery] = useState("")
  const [picked, setPicked] = useState<string | null>(null)
  const have = useMemo(() => new Set(owned), [owned])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [onClose])

  const groups = useMemo(() => {
    const needle = query.trim().toLowerCase()
    const matched = needle
      ? catalogue.filter((entry) => entry.label.toLowerCase().includes(needle))
      : catalogue
    const order: string[] = []
    const byBrand = new Map<string, PrinterCatalogueEntry[]>()
    for (const entry of matched) {
      if (!byBrand.has(entry.brand)) {
        byBrand.set(entry.brand, [])
        order.push(entry.brand)
      }
      byBrand.get(entry.brand)!.push(entry)
    }
    return order.map((brand) => ({ brand, rows: byBrand.get(brand)! }))
  }, [catalogue, query])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-scrim/30 p-6"
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        className="panel flex max-h-full w-[520px] flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Add a printer"
      >
        <PanelStrip
          label="Add a printer"
          inset={16}
          trailing={<IconButton icon="xmark" label="Close" onClick={onClose} className="-mr-2" />}
        />

        <div className="flex shrink-0 flex-col gap-3 px-5 pt-4">
          <p className="text-[13.5px] leading-[18px] text-ink-soft">
            Pick the machine on your bench. Checks use its bed size; the slicer brings its own profile.
          </p>
          <div className="flex h-8 shrink-0 items-center gap-2 rounded-[3px] border border-line bg-ground px-2.5">
            <span className="shrink-0 text-faint">
              <Icon name="search" />
            </span>
            <input
              name="printer-search"
              aria-label="Search printers"
              placeholder="SEARCH PRINTERS"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              autoFocus
              className="min-w-0 flex-1 bg-transparent font-mono text-[10.5px] tracking-[0.08em] text-ink uppercase placeholder:text-faint focus:outline-none"
            />
          </div>
        </div>

        <div className="mt-3 min-h-0 flex-1 overflow-y-auto border-t border-line-soft">
          {groups.length === 0 ? (
            <p className="px-5 py-4 text-[13px] leading-[18px] text-muted">No printer matches that.</p>
          ) : (
            groups.map((group) => (
              <div key={group.brand} className="flex flex-col">
                <div className="flex h-6 items-center bg-raised px-5 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase">
                  {group.brand}
                </div>
                {group.rows.map((entry) => {
                  const already = have.has(entry.name)
                  const selected = picked === entry.name
                  return (
                    <button
                      key={entry.name}
                      type="button"
                      disabled={already}
                      aria-pressed={selected}
                      onClick={() => setPicked(entry.name)}
                      className={clsx(
                        "chrome flex h-[30px] w-full items-center gap-2 px-5 text-left transition-colors focus-visible:outline-none",
                        already
                          ? "cursor-default text-faint"
                          : selected
                            ? "bg-accent-wash text-ink"
                            : "text-ink-soft hover:bg-raised hover:text-ink"
                      )}
                    >
                      <span className="flex size-3 shrink-0 items-center justify-center">
                        {selected ? <Icon name="check" /> : null}
                      </span>
                      <span className="min-w-0 flex-1 truncate font-mono text-[11px] leading-4">
                        {entry.label}
                      </span>
                      <span className="shrink-0 font-mono text-[10px] leading-4 tracking-[0.08em] text-muted tabular-nums">
                        {already ? "On your bench" : bedLine(entry.bed)}
                      </span>
                    </button>
                  )
                })}
              </div>
            ))
          )}
        </div>

        {error ? (
          <p className="shrink-0 bg-fail-wash px-5 py-2 text-[12px] leading-4 text-fail" role="alert">
            {error}
          </p>
        ) : null}

        <div className="flex shrink-0 items-center gap-4 border-t border-line-soft px-5 py-4">
          <p className="min-w-0 flex-1 text-[12px] leading-4 text-muted">
            Not listed? Pick the one with the closest bed size. That is all the checks use.
          </p>
          <Button size="md" className="px-3.5" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="accent"
            size="md"
            className="px-3.5"
            disabled={!picked || busy}
            onClick={() => picked && onAdd(picked)}
          >
            {busy ? "Adding" : "Add printer"}
          </Button>
        </div>
      </div>
    </div>
  )
}
