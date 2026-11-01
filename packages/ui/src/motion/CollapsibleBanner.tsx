import { useCallback, useId, useRef, useState, type ReactNode } from "react"
import { motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import Icon from "../Icon"
import { IconButton } from "../Button"
import { duration, ease } from "./tokens"

// Ported from interior.dev (MIT) and restyled onto the nurb tokens. A notice has
// three resting places, not two: read, folded down to the line that names it, or
// let go. The fold is what lets a notice that is still true stay reachable, so
// `dismissible={false}` is the point of the component rather than a corner case.

const OUT = ease.out as [number, number, number, number]
const INSTANT = { duration: 0 } as const

export type BannerState = "open" | "folded" | "dismissed"
export type BannerTone = "warn" | "fail" | "neutral"

const TONE: Record<BannerTone, { surface: string; mark: string }> = {
  warn: { surface: "bg-warn-wash border-warn/25", mark: "text-warn" },
  fail: { surface: "bg-fail-wash border-fail/25", mark: "text-fail" },
  neutral: { surface: "bg-raised border-line", mark: "text-ink" },
}

export function useCollapsibleBanner({
  state: controlled,
  defaultState = "open",
  onStateChange,
  onDismiss,
}: {
  state?: BannerState
  defaultState?: BannerState
  onStateChange?: (state: BannerState) => void
  onDismiss?: () => void
} = {}) {
  const [uncontrolled, setUncontrolled] = useState<BannerState>(defaultState)
  const state = controlled ?? uncontrolled

  // Held in refs so a caller passing a fresh closure every render does not
  // re-create the callbacks it then depends on.
  const changed = useRef(onStateChange)
  changed.current = onStateChange
  const closed = useRef(onDismiss)
  closed.current = onDismiss

  const commit = useCallback((next: BannerState) => {
    setUncontrolled(next)
    changed.current?.(next)
  }, [])

  const fold = useCallback(() => commit("folded"), [commit])
  const expand = useCallback(() => commit("open"), [commit])
  const toggle = useCallback(() => commit(state === "open" ? "folded" : "open"), [commit, state])
  const dismiss = useCallback(() => {
    commit("dismissed")
    closed.current?.()
  }, [commit])

  return {
    state,
    open: state === "open",
    folded: state === "folded",
    dismissed: state === "dismissed",
    fold,
    expand,
    toggle,
    dismiss,
  }
}

export default function CollapsibleBanner({
  title,
  description,
  children,
  action,
  tone = "neutral",
  dismissible = true,
  state: controlled,
  defaultState = "open",
  onStateChange,
  onDismiss,
  dismissLabel = "Dismiss notice",
  className,
}: {
  title: ReactNode
  description?: ReactNode
  children?: ReactNode
  /** The control the notice is asking for, at the bottom of the fold. */
  action?: ReactNode
  tone?: BannerTone
  dismissible?: boolean
  state?: BannerState
  defaultState?: BannerState
  onStateChange?: (state: BannerState) => void
  onDismiss?: () => void
  dismissLabel?: string
  className?: string
}) {
  const reduced = useReducedMotion() === true
  const uid = useId()
  const bodyId = `${uid}-body`
  const titleId = `${uid}-title`

  const { state, open, dismissed, toggle, fold, dismiss } = useCollapsibleBanner({
    state: controlled,
    defaultState,
    onStateChange,
    onDismiss,
  })

  const hasBody = Boolean(description || children || action)
  const settle = { duration: reduced ? 0 : duration.settle, ease: OUT }

  return (
    <>
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: dismissed ? 0 : "auto", opacity: dismissed ? 0 : 1 }}
        transition={settle}
        style={{ overflow: "hidden" }}
      >
        <div
          role="region"
          aria-labelledby={titleId}
          className={clsx("rounded-[12px] border", TONE[tone].surface, className)}
        >
          <div className="flex items-center gap-2 p-2.5">
            <span aria-hidden="true" className={clsx("flex shrink-0", TONE[tone].mark)}>
              <Icon name={tone === "neutral" ? "box" : "warning"} />
            </span>

            {hasBody ? (
              <button
                type="button"
                onClick={toggle}
                onKeyDown={(e) => {
                  if (e.key !== "Escape" || !open) return
                  e.stopPropagation()
                  fold()
                }}
                aria-expanded={open}
                aria-controls={bodyId}
                className="chrome group flex min-w-0 flex-1 items-center gap-2 rounded-[3px] text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              >
                <span id={titleId} className="min-w-0 flex-1 truncate text-[13px] leading-5 font-medium text-ink">
                  {title}
                </span>
                <motion.span
                  aria-hidden="true"
                  className="flex shrink-0 text-muted group-hover:text-ink"
                  initial={false}
                  animate={{ rotate: open ? 180 : 0 }}
                  transition={reduced ? INSTANT : { duration: duration.tick, ease: OUT }}
                >
                  <Icon name="chevron-down" />
                </motion.span>
              </button>
            ) : (
              <span id={titleId} className="min-w-0 flex-1 truncate text-[13px] leading-5 font-medium text-ink">
                {title}
              </span>
            )}

            {dismissible ? <IconButton icon="xmark" label={dismissLabel} onClick={dismiss} /> : null}
          </div>

          {hasBody ? (
            <motion.div
              id={bodyId}
              inert={!open}
              initial={false}
              animate={{ height: open ? "auto" : 0, opacity: open ? 1 : 0 }}
              // Opacity leads on the way out and trails on the way in: finishing
              // first hides the reflow, starting late keeps text out of a box
              // that has not opened yet.
              transition={
                reduced
                  ? INSTANT
                  : { height: settle, opacity: { duration: duration.tick, ease: OUT, delay: open ? 0.05 : 0 } }
              }
              style={{ overflow: "hidden" }}
            >
              <div className="pr-2.5 pb-2.5 pl-[30px]">
                {description ? <p className="text-[12.5px] leading-relaxed text-muted">{description}</p> : null}
                {children}
                {action ? <div className="mt-2">{action}</div> : null}
              </div>
            </motion.div>
          ) : null}
        </div>
      </motion.div>
      {/* Outside the collapsing frame, so the confirmation is not clipped away with it. */}
      <span role="status" aria-live="polite" className="sr-only">
        {state === "dismissed" ? "Notice dismissed." : ""}
      </span>
    </>
  )
}
