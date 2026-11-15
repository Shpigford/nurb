import clsx from "clsx"
import { useEffect, useRef, useState } from "react"
import { useIsDark } from "@nurb/ui"
import { absolute, type Part } from "./api"

/** The assembly a part belongs to, then the parts it places: what the strip shows. */
export function assemblyOf(part: Part | null, parts: Part[]): Part[] {
  if (!part) return []
  // The nearest assembly that places this part, so a nested part is on its own strip.
  const top = part.uses?.length ? part : parts.find((p) => p.uses?.includes(part.name))
  if (!top?.uses?.length) return []
  return [top, ...top.uses.flatMap((name) => parts.filter((p) => p.name === name))]
}

const named = (part: Part) => part.title ?? part.name.charAt(0).toUpperCase() + part.name.slice(1).replace(/_/g, " ")

// An assembly is the thing being made and its parts are what gets printed, so the
// strip keeps both one click apart: the assembled scene first, then each part.
export default function AssemblyStrip({
  group,
  selected,
  onSelect,
}: {
  group: Part[]
  selected: Part | null
  onSelect: (name: string) => void
}) {
  const dark = useIsDark()
  const row = useRef<HTMLDivElement | null>(null)
  // Which ends have more parts past them, so the edge fades instead of a scrollbar
  // drawing over the tiles.
  const [more, setMore] = useState({ left: false, right: false })
  const measure = () => {
    const el = row.current
    if (!el) return
    setMore({ left: el.scrollLeft > 1, right: el.scrollLeft + el.clientWidth < el.scrollWidth - 1 })
  }
  const selectedId = selected?.id
  useEffect(() => {
    const el = row.current
    if (!el) return
    el.querySelector<HTMLElement>("[aria-pressed=true]")?.scrollIntoView?.({ inline: "nearest", block: "nearest" })
    measure()
    if (typeof ResizeObserver === "undefined") return
    const observer = new ResizeObserver(measure)
    observer.observe(el)
    return () => observer.disconnect()
  }, [selectedId, group.length])
  if (group.length < 2) return null
  const [top, ...pieces] = group
  const tile = (part: Part, caption?: string) => {
    const url = part.build?.thumbnail_url ? absolute(part.build.thumbnail_url) : null
    const on = part.id === selected?.id
    return (
      <button
        key={part.id}
        type="button"
        aria-pressed={on}
        onClick={() => onSelect(part.name)}
        className={clsx(
          "flex shrink-0 items-center gap-2 rounded-[4px] py-1 pr-2.5 pl-1 text-left transition-colors",
          "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          on ? "bg-accent-wash" : "hover:bg-raised"
        )}
      >
        <span className="flex h-[34px] w-11 shrink-0 items-center justify-center overflow-hidden rounded-[3px] bg-raised">
          {url ? <img src={dark ? `${url}&theme=dark` : url} alt="" className="size-full object-contain p-0.5" /> : null}
        </span>
        <span className="flex min-w-0 flex-col">
          <span className={clsx("truncate text-[13px] leading-4 font-medium", on ? "text-ink" : "text-ink-soft")}>
            {named(part)}
          </span>
          {caption ? <span className="mono-caption text-muted">{caption}</span> : null}
        </span>
      </button>
    )
  }
  return (
    <nav
      aria-label={`Parts of ${named(top)}`}
      className="panel absolute top-4 left-1/2 z-10 flex max-w-[calc(100%-2rem)] -translate-x-1/2 items-stretch gap-1 rounded-[6px] p-1"
    >
      {/* The assembly stays put; only its parts scroll when they do not fit. */}
      {tile(top, `Assembly · ${pieces.length} ${pieces.length === 1 ? "part" : "parts"}`)}
      <span aria-hidden="true" className="my-1 w-px shrink-0 bg-line" />
      <div
        ref={row}
        onScroll={measure}
        // A mouse wheel only scrolls vertically, so it moves the row sideways here.
        onWheel={(e) => {
          if (row.current && Math.abs(e.deltaY) > Math.abs(e.deltaX)) row.current.scrollLeft += e.deltaY
        }}
        style={{
          maskImage: `linear-gradient(to right, ${more.left ? "transparent" : "black"}, black 32px, black calc(100% - 32px), ${more.right ? "transparent" : "black"})`,
        }}
        className="flex min-w-0 items-stretch gap-1 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {pieces.map((part) => tile(part))}
      </div>
    </nav>
  )
}
