import type { ReactNode } from "react"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import Icon from "../Icon"
import { rev } from "../format"
import { duration, ease } from "../motion/tokens"

const OUT = ease.out as [number, number, number, number]

// The rail's banner when the newest revision did not build: the values on screen
// are the last ones that did, and the rail says so before the user drags anything.
// It slides down from the rail's top edge, so the numbers below are seen to stay put.
// It owns its own presence, so the caller mounts it either way and flips `open`.
// That keeps the slide back up here, where the motion already lives, instead of
// asking every host for an AnimatePresence of its own.
export function BuildFailedBanner({
  open = true,
  revision,
  shownRevision,
  error,
}: {
  /** False sends the banner back up the way it came. */
  open?: boolean
  revision: number
  shownRevision?: number | null
  /** The failure's own last line, so the reason sits under the headline whatever raised it. */
  error?: string | null
}) {
  const reduced = useReducedMotion()
  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: reduced ? 0 : duration.settle, ease: OUT }}
          className="flex items-start gap-2 bg-fail-wash px-4 py-2.5"
        >
          <span className="mt-0.5 shrink-0 text-fail">
            <Icon name="warning" />
          </span>
          <span className="flex flex-col gap-1">
            <span className="mono-label text-fail">{rev(revision)} failed at these values</span>
            {error ? <span className="text-chat text-ink">{error}</span> : null}
            {shownRevision != null ? (
              <span className="text-chat text-ink-soft">
                Showing {rev(shownRevision).toLowerCase()}, the last one that built.
              </span>
            ) : null}
          </span>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}

// The floating pill over the stage. The viewer column is not a panel, so the notice is.
export function StageNotice({ children }: { children: ReactNode }) {
  return (
    <div className="panel chrome absolute top-4 left-4 flex h-7 items-center gap-2 rounded-full px-3">
      <span className="size-1.5 shrink-0 rounded-full bg-fail" />
      <span className="mono-label text-ink">{children}</span>
    </div>
  )
}
