import { useEffect, useState } from "react"
import Icon from "./Icon"
import IsoBox from "./IsoBox"
import Menu, { type MenuItem } from "./Menu"
import BlurUpImage from "./motion/BlurUpImage"
import { formatBbox, relativeTime, rev } from "./format"

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
  identifier?: string
  bbox?: number[] | null
  status: "built" | "failed" | "building" | "unbuilt"
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
}: {
  part: PartCardPart
  onOpen: () => void
  menu?: MenuItem[]
}) {
  const dims = formatBbox(part.bbox)
  const built = relativeTime(part.builtAt)
  const failed = part.status === "failed"
  const building = part.status === "building"
  const pulse = usePulse(building, part.buildingSince)
  return (
    <div className="group relative flex flex-col rounded-[6px] border border-panel-edge bg-ground transition-shadow focus-within:shadow-[var(--shadow-panel)] hover:shadow-[var(--shadow-panel)]">
      <button
        type="button"
        onClick={onOpen}
        aria-label={`Open ${part.name}`}
        className="absolute inset-0 z-10 rounded-[6px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      />
      <div className="relative h-[148px] overflow-hidden rounded-t-[6px] border-b border-line-soft bg-ground">
        {part.thumbnailUrl ? (
          // The card owns the box, so the frame fills it instead of its own ratio,
          // and the whole part stays in frame rather than being cropped to it.
          <BlurUpImage
            src={part.thumbnailUrl}
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
          <h2 className="min-w-0 flex-1 truncate text-[13.5px] leading-[18px] font-semibold tracking-[-0.01em] text-ink">
            {part.name}
          </h2>
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
        <p className="mono-caption truncate text-muted normal-case [letter-spacing:0.08em]">
          {part.identifier ?? ""}
          {part.identifier && dims ? " · " : ""}
          {dims ? `${dims} mm` : ""}
        </p>
      </div>
      <div className="mono-caption flex items-center justify-between border-t border-line-soft px-[13px] py-2 text-muted [letter-spacing:0.08em]">
        <span>{built ? `Built ${built}` : "Not built yet"}</span>
        <span className={failed ? "text-warn" : undefined}>
          {failed ? "Failed" : (part.folder ?? rev(part.revision))}
        </span>
      </div>
    </div>
  )
}
