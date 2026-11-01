import Button from "./Button"
import type { IconName } from "./Icon"
import { brand } from "./brand"

// The shelf before anything is on it. The bracket is the ghost of a part.
export default function EmptyShelf({
  caption = "Describe a part and it builds here, live.",
  firstRun = false,
  primary,
  secondary,
}: {
  caption?: string
  /** The library has never held a part. Said once, and never again after the first one. */
  firstRun?: boolean
  primary?: { label: string; onClick: () => void; icon?: IconName }
  /** The quieter way in, under the primary: importing a folder you already have. */
  secondary?: { label: string; icon?: IconName; onClick: () => void; disabled?: boolean }
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-7 pb-16">
      <img src={brand.ghostBracket} alt="" aria-hidden="true" className="h-[300px] w-auto select-none" />
      <div className="flex flex-col items-center gap-2">
        <h2 className="font-display text-[20px] leading-[26px] tracking-[-0.022em] text-balance text-ink">
          Empty shelf. What’s rattling around your bench?
        </h2>
        <p className="mono-caption text-on-stage-muted [letter-spacing:0.11em]">{caption}</p>
        {firstRun ? (
          <p className="mt-1 max-w-[42ch] text-center text-[13px] leading-5 text-balance text-on-stage-muted">
            Nothing on the plate yet. Your first part goes here, and the first layer is the one that matters.
          </p>
        ) : null}
      </div>
      {primary || secondary ? (
        <div className="flex flex-col items-center gap-3">
          {primary ? (
            <Button variant="accent" size="lg" icon={primary.icon} onClick={primary.onClick}>
              {primary.label}
            </Button>
          ) : null}
          {secondary ? (
            <Button variant="outline" size="md" icon={secondary.icon} onClick={secondary.onClick} disabled={secondary.disabled}>
              {secondary.label}
            </Button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
