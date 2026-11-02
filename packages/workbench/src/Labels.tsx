import { useState, type FormEvent } from "react"
import { Button } from "@nurb/ui"
import type { PartLabel } from "./api"

/** A saved label on the part: a ring on the spot and its name beside it. Dashed once the part moved away. */
export function LabelTag({ label, onOpen }: { label: PartLabel; onOpen: () => void }) {
  const off = label.on_part === false
  return (
    <button
      type="button"
      onClick={onOpen}
      title={off ? `${label.name} is no longer on the part. Click to rename or remove it.` : `Rename or remove ${label.name}`}
      className="-translate-x-[5px] -translate-y-[11px] flex items-center gap-1.5 group-data-[flip]:translate-x-[5px] group-data-[flip]:flex-row-reverse"
    >
      <span
        className={`size-2.5 shrink-0 rounded-full border-2 ${off ? "border-dashed border-muted" : "border-ink bg-ground"}`}
      />
      <span
        className={`mono-caption flex h-[22px] items-center gap-1.5 whitespace-nowrap rounded-[3px] border bg-ground px-2 ${
          off ? "border-dashed border-muted text-muted" : "border-ink text-ink"
        }`}
      >
        {label.name}
        {off ? <span className="text-ink-soft">· not on the part</span> : null}
      </span>
    </button>
  )
}

/** Names a new spot, or renames or removes a label. Sits beside the spot it is about. */
export function LabelEditor({
  was,
  onSave,
  onRemove,
  onMove,
  onCancel,
}: {
  /** The label's current name, or undefined for a spot that has none yet. */
  was?: string
  onSave: (name: string) => Promise<void>
  onRemove?: () => Promise<void>
  /** Puts the stage back in label mode, so the next click is this label's new spot. */
  onMove?: () => void
  onCancel: () => void
}) {
  const [name, setName] = useState(was ?? "")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async (work: () => Promise<void>) => {
    setBusy(true)
    setError(null)
    try {
      await work()
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "That did not save.")
      setBusy(false)
    }
  }
  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (name.trim()) void run(() => onSave(name.trim()))
  }

  return (
    <div className="-translate-x-[6px] -translate-y-[6px] flex items-start gap-2.5 group-data-[flip]:translate-x-[6px] group-data-[flip]:flex-row-reverse">
      <span className="size-3 shrink-0 rounded-full border-[3px] border-ink bg-ground" />
      <form
        onSubmit={submit}
        onKeyDown={(e) => e.key === "Escape" && onCancel()}
        className="flex w-72 flex-col gap-2.5 rounded-[6px] border border-panel-edge bg-ground p-3 shadow-[0_8px_24px_rgba(18,24,33,0.12)]"
      >
        <div className="flex h-7 items-center gap-1">
          <label htmlFor="label-name" className="mono-caption flex-1 whitespace-nowrap text-muted">
            {was ? "Rename this spot" : "Name this spot"}
          </label>
          {onMove ? (
            <Button variant="ghost" className="px-2" disabled={busy} onClick={onMove}>
              Move
            </Button>
          ) : null}
          {onRemove ? (
            <Button variant="ghost" className="px-2" disabled={busy} onClick={() => void run(onRemove)}>
              Remove
            </Button>
          ) : null}
        </div>
        <input
          id="label-name"
          autoFocus
          maxLength={100}
          value={name}
          placeholder="Lip, hook, back wall…"
          onChange={(e) => setName(e.target.value)}
          className="h-[34px] rounded-[4px] border border-ink px-2.5 text-[15px] text-ink outline-none placeholder:text-faint"
        />
        {error ? <p className="text-[13px] leading-[18px] text-fail">{error}</p> : null}
        <div className="flex items-center justify-end gap-2">
          <Button variant="outline" disabled={busy} onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" variant="ink" disabled={busy || !name.trim()}>
            Save label
          </Button>
        </div>
      </form>
    </div>
  )
}
