import { useCallback, useEffect, useId, useRef, useState } from "react"
import { animate, motion, useMotionValue, useReducedMotion, useTransform } from "motion/react"
import Button from "../Button"
import { cue } from "../sound"
import { duration as motionDuration, ease } from "./tokens"

// A guard rail in front of anything with no undo. Ported from interior.dev (MIT).
// A click never confirms: only a continuous hold does, and letting go drains the
// meter rather than snapping it to zero, so a slip costs a moment and not the part.

const OUT = ease.out as [number, number, number, number]
// Progress drains this many times faster than it fills.
const RELEASE_RATE = 2.5
// The hold is sampled this many times, so a 1.2 second press costs twenty renders instead of eighty.
const STEPS = 20
const MOVE_TOLERANCE = 10

export type HoldPhase = "idle" | "holding" | "releasing" | "committed"

/** The hold itself, with no surface: pointer and key bindings in, a phase and a 0..1 progress out. */
export function useHoldToConfirm({
  onConfirm,
  holdMs = 1800,
  disabled = false,
}: {
  onConfirm: () => void
  holdMs?: number
  disabled?: boolean
}) {
  const [step, setStep] = useState(0)
  const [phase, setPhase] = useState<HoldPhase>("idle")
  const phaseRef = useRef<HoldPhase>("idle")
  const down = useRef(false)
  const elapsed = useRef(0)
  const last = useRef(0)
  const raf = useRef(0)
  const origin = useRef<{ x: number; y: number } | null>(null)
  const confirm = useRef(onConfirm)
  confirm.current = onConfirm

  const move = useCallback((next: HoldPhase) => {
    phaseRef.current = next
    setPhase(next)
  }, [])

  const reset = useCallback(() => {
    cancelAnimationFrame(raf.current)
    raf.current = 0
    down.current = false
    elapsed.current = 0
    origin.current = null
    setStep(0)
    move("idle")
  }, [move])

  const begin = useCallback(
    (point?: { x: number; y: number }) => {
      if (disabled) return
      if (phaseRef.current === "committed" || phaseRef.current === "holding") return

      origin.current = point ?? null
      down.current = true
      move("holding")
      cue("press")
      if (raf.current) return

      last.current = performance.now()
      const loop = (now: number) => {
        const dt = Math.min(64, now - last.current)
        last.current = now
        elapsed.current += down.current ? dt : -dt * RELEASE_RATE

        if (elapsed.current >= holdMs) {
          raf.current = 0
          elapsed.current = holdMs
          down.current = false
          origin.current = null
          setStep(STEPS)
          move("committed")
          confirm.current()
          return
        }
        if (elapsed.current <= 0) {
          raf.current = 0
          elapsed.current = 0
          origin.current = null
          setStep(0)
          move("idle")
          return
        }

        const s = Math.min(STEPS, Math.floor((elapsed.current / holdMs) * STEPS))
        setStep((prev) => (prev === s ? prev : s))
        raf.current = requestAnimationFrame(loop)
      }
      raf.current = requestAnimationFrame(loop)
    },
    [disabled, holdMs, move],
  )

  const release = useCallback(() => {
    if (phaseRef.current !== "holding") return
    down.current = false
    origin.current = null
    move("releasing")
  }, [move])

  useEffect(() => {
    // A hold must never survive into the background and fire when nobody is watching.
    const bail = () => release()
    const onVisibility = () => {
      if (document.hidden) release()
    }
    window.addEventListener("blur", bail)
    document.addEventListener("visibilitychange", onVisibility)
    return () => {
      window.removeEventListener("blur", bail)
      document.removeEventListener("visibilitychange", onVisibility)
      cancelAnimationFrame(raf.current)
      raf.current = 0
    }
  }, [release])

  const bind = {
    onPointerDown: (e: React.PointerEvent) => {
      if (e.pointerType === "mouse" && e.button !== 0) return
      e.currentTarget.setPointerCapture?.(e.pointerId)
      begin({ x: e.clientX, y: e.clientY })
    },
    onPointerMove: (e: React.PointerEvent) => {
      const from = origin.current
      if (phaseRef.current !== "holding" || !from) return
      if (Math.hypot(e.clientX - from.x, e.clientY - from.y) > MOVE_TOLERANCE) release()
    },
    onPointerUp: release,
    onPointerCancel: release,
    onPointerLeave: release,
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        if (phaseRef.current === "holding" || phaseRef.current === "releasing") {
          e.preventDefault()
          reset()
        }
        return
      }
      if (e.repeat) return
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault()
        begin()
      }
    },
    onKeyUp: (e: React.KeyboardEvent) => {
      if (e.key === " " || e.key === "Enter") release()
    },
    onBlur: release,
    onClick: (e: React.MouseEvent) => e.preventDefault(),
    onContextMenu: (e: React.MouseEvent) => e.preventDefault(),
  }

  return { bind, phase, progress: step / STEPS, reset }
}

export default function HoldToConfirm({
  label,
  confirmLabel = "Confirmed",
  holdMs = 1800,
  onConfirm,
  variant = "danger",
  disabled = false,
  className,
}: {
  label: string
  confirmLabel?: string
  holdMs?: number
  onConfirm: () => void
  variant?: "accent" | "ink" | "outline" | "ghost" | "danger"
  disabled?: boolean
  className?: string
}) {
  const { bind, phase, reset } = useHoldToConfirm({ onConfirm, holdMs, disabled })
  const reduced = useReducedMotion()
  const hintId = useId()
  const committed = phase === "committed"
  const seconds = Math.round(holdMs / 100) / 10

  const swept = useMotionValue(0)
  const clipPath = useTransform(swept, (v) => `inset(0 ${(1 - v) * 100}% 0 0)`)

  useEffect(() => {
    if (!committed) return
    const back = setTimeout(reset, 1600)
    return () => clearTimeout(back)
  }, [committed, reset])

  useEffect(() => {
    // Reduced motion drops the sweep, never the hold: the delay is the guard rail, not decoration.
    if (reduced) {
      swept.set(phase === "holding" || phase === "committed" ? 1 : 0)
      return
    }
    if (phase === "committed") {
      const controls = animate(swept, 1, { duration: motionDuration.tick, ease: "linear" })
      return () => controls.stop()
    }
    const from = swept.get()
    if (phase === "holding") {
      const controls = animate(swept, 1, { duration: (holdMs * (1 - from)) / 1000, ease: "linear" })
      return () => controls.stop()
    }
    const controls = animate(swept, 0, { duration: (holdMs * from) / RELEASE_RATE / 1000, ease: OUT })
    return () => controls.stop()
  }, [phase, holdMs, reduced, swept])

  return (
    <Button
      variant={variant}
      // Named explicitly: the visible faces are decoration and the hint is a description, not the name.
      aria-label={label}
      aria-disabled={disabled || committed}
      aria-describedby={hintId}
      className={`relative isolate select-none overflow-hidden ${className ?? ""}`}
      {...bind}
    >
      <Faces committed={committed} label={label} confirmLabel={confirmLabel} />
      <motion.span
        aria-hidden="true"
        style={{ clipPath }}
        className="absolute inset-0 grid place-items-center bg-ink text-ground"
      >
        <Faces committed={committed} label={label} confirmLabel={confirmLabel} />
      </motion.span>
      <span id={hintId} className="sr-only">
        Press and hold for {seconds} seconds to confirm. Let go early and nothing happens.
      </span>
      <span role="status" aria-live="polite" className="sr-only">
        {committed ? confirmLabel : ""}
      </span>
    </Button>
  )
}

// Both labels share one grid cell, so committing cannot change the button's width.
function Faces({ committed, label, confirmLabel }: { committed: boolean; label: string; confirmLabel: string }) {
  const transition = { duration: motionDuration.settle, ease: OUT }
  return (
    <span aria-hidden="true" className="col-start-1 row-start-1 grid">
      <motion.span
        initial={false}
        animate={{ opacity: committed ? 0 : 1 }}
        transition={transition}
        className="col-start-1 row-start-1 flex items-center justify-center whitespace-nowrap"
      >
        {label}
      </motion.span>
      <motion.span
        initial={false}
        animate={{ opacity: committed ? 1 : 0 }}
        transition={transition}
        className="col-start-1 row-start-1 flex items-center justify-center gap-1.5 whitespace-nowrap"
      >
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
        >
          <path d="M2.5 6.4 4.7 8.6 9.5 3.5" />
        </svg>
        {confirmLabel}
      </motion.span>
    </span>
  )
}
