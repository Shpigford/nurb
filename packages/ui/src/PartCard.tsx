import { useEffect, useRef, useState } from "react"
import Icon from "./Icon"
import IsoBox from "./IsoBox"
import Menu, { useContextMenu, type MenuItem } from "./Menu"
import BlurUpImage from "./motion/BlurUpImage"
import { formatBbox, relativeTime, rev } from "./format"
import { useIsDark } from "./theme"

// A build that has been running longer than this has stalled, and a dot still
// pulsing would say it is fine.
const FRESH_MS = 30_000

// The pulse is a claim that work is happening. It stops on its own at the 30 s
// mark, so a stalled build reads as stalled without waiting for another event.
function usePulse(building: boolean, since?: string | null): boolean {
  const started = since ? Date.parse(since) : NaN
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!building || Number.isNaN(started)) return
    const left = started + FRESH_MS - Date.now()
    if (left <= 0) return
    const timer = setTimeout(() => setNow(Date.now()), left)
    return () => clearTimeout(timer)
  }, [building, started])
  if (!building) return false
  if (Number.isNaN(started)) return true
  return now - started < FRESH_MS
}

export interface PartCardPart {
  id: string
  name: string
  bbox?: number[] | null
  /** A draft is described and not written yet, so there is nothing to build. */
  status: "built" | "failed" | "building" | "unbuilt" | "draft"
  /** A draft whose agent turn is running right now. */
  designing?: boolean
  revision?: number | null
  builtAt?: string | null
  thumbnailUrl?: string | null
  /** The folder the part sits in. The footer says that instead of the revision. */
  folder?: string | null
  /** When the running build started, so a stalled one stops claiming to be alive. */
  buildingSince?: string | null
}

// Every part stays alive and parametric: the card opens it at the last build.
// The footer says when it built and which revision that was.
export default function PartCard({
  part,
  onOpen,
  menu,
  renaming,
  onRename,
}: {
  part: PartCardPart
  onOpen: () => void
  menu?: MenuItem[]
  /** The title is a field: Enter or leaving it hands back the name, Escape hands back null. */
  renaming?: boolean
  onRename?: (name: string | null) => void
}) {
  const dims = formatBbox(part.bbox)
  // A project named after its first part would repeat the title, so the revision shows instead.
  const folder = part.folder && part.folder.toLowerCase() !== part.name.toLowerCase() ? part.folder : null
  const built = relativeTime(part.builtAt)
  const failed = part.status === "failed"
  const building = part.status === "building"
  const draft = part.status === "draft"
  const pulse = usePulse(building, part.buildingSince)
  const context = useContextMenu()
  // The picture carries its own floor shadow, drawn for the card's ground.
  const dark = useIsDark()
  const thumbnail = part.thumbnailUrl && dark ? `${part.thumbnailUrl}&theme=dark` : (part.thumbnailUrl ?? undefined)
  return (
    <div
      onContextMenu={(e) => context.open(e, renaming ? undefined : menu)}
      className="group relative flex flex-col rounded-[6px] border border-panel-edge bg-ground transition-shadow focus-within:shadow-[var(--shadow-panel)] hover:shadow-[var(--shadow-panel)]"
    >
      {context.menu}
      <button
        type="button"
        onClick={onOpen}
        aria-label={`Open ${part.name}`}
        className="absolute inset-0 z-10 rounded-[6px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      />
      {/* A draft has no geometry yet, so its picture is a plain panel rather than a box. */}
      <div
        className={`relative h-[148px] overflow-hidden rounded-t-[6px] border-b border-line-soft ${draft ? "bg-raised/60" : "bg-ground"}`}
      >
        {draft ? null : part.thumbnailUrl ? (
          // The card owns the box, so the frame fills it instead of its own ratio,
          // and the whole part stays in frame rather than being cropped to it.
          <BlurUpImage
            src={thumbnail}
            alt=""
            width={4}
            height={3}
            // The picture has no ground of its own, so the card's shows through it.
            placeholder="transparent"
            className="h-full rounded-none! [&_img]:object-contain [&_img]:p-2"
          />
        ) : (
          <IsoBox bbox={part.bbox} ghost={!part.bbox} className="size-full" />
        )}
      </div>
      {/* Outside the clipped thumbnail so the menu can open past its edge. */}
      {menu && menu.length > 0 ? (
        <div className="absolute top-2 right-2 z-20 flex items-center gap-1 transition-opacity lg:opacity-0 lg:group-focus-within:opacity-100 lg:group-hover:opacity-100 lg:has-[[aria-expanded=true]]:opacity-100">
          <Menu
            label={`More for ${part.name}`}
            className="[&>button]:size-7 [&>button]:rounded-[4px] [&>button]:border [&>button]:border-panel-edge [&>button]:bg-ground [&>button]:shadow-[var(--shadow-control)]"
            items={menu}
          />
        </div>
      ) : null}
      <div className="flex flex-col gap-1.5 px-[13px] py-[11px]">
        <div className="flex items-center gap-2">
          {renaming ? (
            <RenameField name={part.name} onDone={(name) => onRename?.(name)} />
          ) : (
            <h2 className="min-w-0 flex-1 truncate text-[13.5px] leading-[18px] font-semibold tracking-[-0.01em] text-ink">
              {part.name}
            </h2>
          )}
          {failed ? (
            <span className="text-warn"><Icon name="warning" /></span>
          ) : building ? (
            <span
              data-build={pulse ? "running" : "stalled"}
              className={`size-1.5 rounded-full bg-accent${pulse ? " motion-safe:animate-pulse" : ""}`}
            />
          ) : part.status === "built" ? (
            <span className="text-pass"><Icon name="check" /></span>
          ) : null}
        </div>
        {/* The name is the title above, so this line is the size alone. A space keeps the height when there is none. */}
        <p className="mono-caption truncate text-muted normal-case [letter-spacing:0.08em]">
          {dims ? `${dims} mm` : "\u00a0"}
        </p>
      </div>
      <div className="mono-caption flex items-center justify-between border-t border-line-soft px-[13px] py-2 text-muted [letter-spacing:0.08em]">
        {draft ? (
          <span className="flex items-center gap-2">
            {part.designing ? (
              <span aria-hidden="true" className="size-1.5 rounded-full bg-accent motion-safe:animate-pulse" />
            ) : null}
            {part.designing ? "Being designed" : "No design yet"}
          </span>
        ) : (
          <span>{built ? `Built ${built}` : "Not built yet"}</span>
        )}
        <span className={failed ? "text-warn" : undefined}>
          {failed ? "Failed" : (folder ?? (draft ? "" : rev(part.revision)))}
        </span>
      </div>
    </div>
  )
}

// Above the card's open button, so a click in the field edits instead of opening.
function RenameField({ name, onDone }: { name: string; onDone: (name: string | null) => void }) {
  const [draft, setDraft] = useState(name)
  const done = useRef(false)
  const finish = (value: string | null) => {
    if (done.current) return
    done.current = true
    onDone(value && value.trim() && value.trim() !== name ? value.trim() : null)
  }
  return (
    <input
      autoFocus
      aria-label={`Rename ${name}`}
      value={draft}
      onFocus={(e) => e.currentTarget.select()}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => finish(draft)}
      onKeyDown={(e) => {
        if (e.key === "Enter") finish(draft)
        else if (e.key === "Escape") finish(null)
      }}
      className="relative z-20 h-[22px] min-w-0 flex-1 rounded-[2px] border border-accent bg-ground px-1 text-[13.5px] leading-[18px] font-semibold tracking-[-0.01em] text-ink focus:outline-none"
    />
  )
}
