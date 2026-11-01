import { useCallback, useEffect, useRef, useState } from "react"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import Icon from "../Icon"
import { IconButton } from "../Button"
import { duration, ease } from "./tokens"

// Ported from interior.dev (MIT) and restyled onto the nurb tokens. One pod, not
// a stack: the latest work replaces the last, because a system genuinely doing
// four things deserves a page rather than a pile of chips.

const OUT = ease.out as [number, number, number, number]
const INSTANT = { duration: 0 } as const
const SPIN = { duration: duration.coast, ease: "linear", repeat: Infinity } as const

export type ActivityTone = "working" | "done" | "fail"

export type Activity = {
  id: string
  title: string
  detail?: string
  tone?: ActivityTone
}

export function useLiveActivity({ linger = 2000 }: { linger?: number } = {}) {
  const [activity, setActivity] = useState<Activity | null>(null)
  const seq = useRef(0)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clear = useCallback(() => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = null
  }, [])

  const start = useCallback(
    (input: Omit<Activity, "id" | "tone">) => {
      clear()
      seq.current += 1
      const id = `activity-${seq.current}`
      setActivity({ ...input, id, tone: "working" })
      return id
    },
    [clear]
  )

  const update = useCallback((patch: Partial<Omit<Activity, "id">>) => {
    setActivity((prev) => (prev ? { ...prev, ...patch } : prev))
  }, [])

  const dismiss = useCallback(() => {
    clear()
    setActivity(null)
  }, [clear])

  const succeed = useCallback(
    (patch?: Partial<Omit<Activity, "id" | "tone">>) => {
      setActivity((prev) => (prev ? { ...prev, ...patch, tone: "done" } : prev))
      clear()
      timer.current = setTimeout(() => {
        timer.current = null
        setActivity(null)
      }, linger)
    },
    [clear, linger]
  )

  // Failure stays: the pod never auto-dismisses bad news.
  const fail = useCallback(
    (patch?: Partial<Omit<Activity, "id" | "tone">>) => {
      clear()
      setActivity((prev) => (prev ? { ...prev, ...patch, tone: "fail" } : prev))
    },
    [clear]
  )

  useEffect(() => clear, [clear])

  return { activity, start, update, succeed, fail, dismiss }
}

export default function LiveActivity({
  activity,
  onDismiss,
  label = "Activity",
  className,
}: {
  activity: Activity | null
  /** Wired to the close affordance, once the work has resolved. */
  onDismiss?: () => void
  label?: string
  className?: string
}) {
  const reduced = useReducedMotion() === true
  const [spoken, setSpoken] = useState("")
  const said = useRef<Set<string>>(new Set())
  const tone = activity?.tone ?? "working"

  // One announcement per phase per activity: readers hear started, finished,
  // failed, never a stream.
  useEffect(() => {
    if (!activity) return
    const key = `${activity.id}:${tone}`
    if (said.current.has(key)) return
    said.current.add(key)
    setSpoken(
      tone === "working"
        ? `${activity.title} started.`
        : tone === "done"
          ? `${activity.title} finished.`
          : `${activity.title} failed.`
    )
  }, [activity, tone])

  return (
    <div role="region" aria-label={label} className={clsx("pointer-events-none flex justify-center", className)}>
      <AnimatePresence initial={false} mode="wait">
        {activity ? (
          <motion.div
            key={activity.id}
            initial={reduced ? { opacity: 0 } : { opacity: 0, y: -10, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduced ? { opacity: 0, transition: INSTANT } : { opacity: 0, y: -8, scale: 0.97 }}
            transition={reduced ? INSTANT : { duration: duration.settle, ease: OUT }}
            style={{ transformOrigin: "50% 0%" }}
            className="pointer-events-auto flex max-w-[320px] items-center gap-2 rounded-[12px] border border-line bg-ground px-3 py-2 shadow-[var(--shadow-panel)]"
          >
            <ToneGlyph tone={tone} reduced={reduced} />
            <span className="min-w-0 flex-1">
              <span className="block truncate text-[13px] leading-5 font-medium text-ink">{activity.title}</span>
              {activity.detail ? <span className="mono-caption block truncate text-muted">{activity.detail}</span> : null}
            </span>
            {onDismiss && tone !== "working" ? (
              <IconButton icon="xmark" label="Dismiss activity" onClick={onDismiss} />
            ) : null}
          </motion.div>
        ) : null}
      </AnimatePresence>
      <span role="status" aria-live="polite" className="sr-only">
        {spoken}
      </span>
    </div>
  )
}

function ToneGlyph({ tone, reduced }: { tone: ActivityTone; reduced: boolean }) {
  if (tone === "done") {
    return (
      <span className="flex shrink-0 text-pass" data-tone="done">
        <Icon name="check" />
      </span>
    )
  }
  if (tone === "fail") {
    return (
      <span className="flex shrink-0 text-fail" data-tone="fail">
        <Icon name="warning" />
      </span>
    )
  }
  return (
    <motion.span
      className="flex shrink-0 text-accent"
      data-tone="working"
      style={{ transformOrigin: "50% 50%" }}
      animate={reduced ? undefined : { rotate: 360 }}
      transition={reduced ? INSTANT : SPIN}
    >
      <Icon name="loader" />
    </motion.span>
  )
}
