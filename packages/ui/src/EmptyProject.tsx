import { brand } from "./brand"

// A project with nothing in it yet. The outline mark stands on the plate where
// the part will.
export default function EmptyProject({
  title = "No part yet",
  caption = "It builds here, live, the moment the spec is pinned.",
}: {
  title?: string
  caption?: string
}) {
  return (
    <div className="relative flex min-h-[320px] flex-1 flex-col items-center justify-center gap-5 text-center">
      <img src={brand.markOutline} alt="" aria-hidden="true" className="size-14 select-none" />
      <div className="flex flex-col items-center gap-2">
        <p className="mono-label text-on-stage-muted">{title}</p>
        <p className="max-w-[34ch] text-[15px] leading-[22px] text-balance text-ink-soft">{caption}</p>
      </div>
    </div>
  )
}
