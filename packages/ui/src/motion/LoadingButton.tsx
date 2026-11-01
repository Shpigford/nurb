import { useCallback, useEffect, useRef, useState } from "react"
import { motion, useReducedMotion } from "motion/react"
import Button from "../Button"
import { cue } from "../sound"
import { duration, ease } from "./tokens"

// A button that carries the result of its own action. Ported from interior.dev
// (MIT). Every label lives in one grid cell, so the widest of them reserves the
// width before the first click and "Sign in" becoming "Signing in" cannot shove
// the controls beside it.

// motion's types want a tuple; ease.out is a plain number[].
const OUT = ease.out as [number, number, number, number]
const FADE = { duration: duration.settle, ease: OUT }
const INSTANT = { duration: 0 }

export type AsyncStatus = "idle" | "pending" | "success" | "error"

/** The state machine on its own: run once, settle, fall back to idle after resetAfter ms. */
export function useAsyncAction({
  action,
  resetAfter = 1400,
}: {
  action: () => unknown
  resetAfter?: number
}) {
  const [status, setStatus] = useState<AsyncStatus>("idle")
  const phase = useRef<AsyncStatus>("idle")
  const runId = useRef(0)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const alive = useRef(true)
  const act = useRef(action)
  act.current = action

  const clear = useCallback(() => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = null
  }, [])

  const run = useCallback(() => {
    if (phase.current === "pending") return
    clear()
    // Every run carries an id, so a slow first response cannot overwrite the run that replaced it.
    const id = ++runId.current
    phase.current = "pending"
    setStatus("pending")

    const settle = (next: "success" | "error") => {
      if (!alive.current || id !== runId.current) return
      phase.current = next
      setStatus(next)
      timer.current = setTimeout(() => {
        if (!alive.current || id !== runId.current) return
        phase.current = "idle"
        setStatus("idle")
      }, resetAfter)
    }

    Promise.resolve()
      .then(() => act.current())
      .then(
        () => settle("success"),
        () => settle("error"),
      )
  }, [clear, resetAfter])

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
      clear()
    }
  }, [clear])

  return { status, run, pending: status === "pending" }
}

function Spinner({ still }: { still: boolean }) {
  return (
    <motion.svg
      width="11"
      height="11"
      viewBox="0 0 12 12"
      fill="none"
      aria-hidden="true"
      className="shrink-0"
      animate={still ? undefined : { rotate: 360 }}
      transition={still ? undefined : { duration: duration.coast * 0.6, repeat: Infinity, ease: "linear" }}
    >
      <circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.22" />
      <path d="M10.5 6A4.5 4.5 0 0 0 6 1.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </motion.svg>
  )
}

function Mark({ d, extra }: { d: string; extra?: string }) {
  return (
    <svg
      width="11"
      height="11"
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0"
    >
      <path d={d} />
      {extra ? <path d={extra} /> : null}
    </svg>
  )
}

export default function LoadingButton({
  label,
  pendingLabel = label,
  successLabel = "Done",
  errorLabel = "Try again",
  onAction,
  resetAfter = 1400,
  variant = "outline",
  disabled = false,
  className,
}: {
  label: string
  pendingLabel?: string
  successLabel?: string
  errorLabel?: string
  onAction: () => unknown
  resetAfter?: number
  variant?: "accent" | "ink" | "outline" | "ghost" | "danger"
  disabled?: boolean
  className?: string
}) {
  const reduced = useReducedMotion()
  const { status, run, pending } = useAsyncAction({ action: onAction, resetAfter })
  const fade = reduced ? INSTANT : FADE

  const faces = [
    { key: "idle", text: label, color: undefined, icon: null },
    {
      key: "pending",
      text: pendingLabel,
      color: "var(--color-muted)",
      icon: <Spinner still={reduced === true || status !== "pending"} />,
    },
    {
      key: "success",
      text: successLabel,
      color: "var(--color-pass)",
      icon: <Mark d="M2.6 6.3 4.9 8.6 9.4 3.6" />,
    },
    {
      key: "error",
      text: errorLabel,
      color: "var(--color-fail)",
      icon: <Mark d="M6 2.9v3.5" extra="M6 9.05h.01" />,
    },
  ]

  const current = faces.find((face) => face.key === status) ?? faces[0]

  return (
    <>
      <Button
        variant={variant}
        disabled={disabled}
        // Never natively disabled mid-flight, or a keyboard user's focus drops to the body the moment they press Enter.
        aria-label={current.text}
        aria-busy={pending || undefined}
        aria-disabled={pending || undefined}
        className={className}
        onClick={() => {
          if (pending) return
          cue("press")
          run()
        }}
      >
        <span aria-hidden="true" className="relative grid place-items-center">
          {faces.map((face) => (
            <motion.span
              key={face.key}
              initial={false}
              animate={face.key === status ? { opacity: 1, y: 0 } : { opacity: 0, y: 2 }}
              transition={fade}
              style={{ color: face.color }}
              className="col-start-1 row-start-1 flex items-center justify-center gap-1.5 whitespace-nowrap"
            >
              {face.icon}
              {face.text}
            </motion.span>
          ))}
        </span>
      </Button>
      <span role="status" aria-live="polite" className="sr-only">
        {status === "success" ? successLabel : status === "error" ? errorLabel : ""}
      </span>
    </>
  )
}
