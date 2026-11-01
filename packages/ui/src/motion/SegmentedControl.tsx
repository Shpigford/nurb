import { useId, useRef, useState } from "react"
import { motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import { cue } from "../sound"
import { duration, ease } from "./tokens"

// Ported from interior.dev's Segmented Control (MIT). One thumb, shared by layoutId, so
// a pick changed mid-slide resumes from where the thumb is instead of restarting.
//
// Roving tabindex with manual activation: arrows and Home/End move focus, Enter or Space
// commits it, a click commits straight away. The radio pattern usually selects on arrow,
// but a pick can be a write, and selection following focus would fire one write per
// keypress on the way past.

const OUT = ease.out as [number, number, number, number]

export interface SegmentedOption {
  value: string
  label: string
}

export default function SegmentedControl({
  options,
  label,
  value,
  onValueChange,
  className,
}: {
  options: SegmentedOption[]
  /** Accessible name. An unlabelled group of radios announces nothing about what it switches. */
  label: string
  value: string
  onValueChange: (value: string) => void
  className?: string
}) {
  const thumbId = useId()
  const reduced = useReducedMotion()
  const buttons = useRef<(HTMLButtonElement | null)[]>([])
  const [focused, setFocused] = useState<number | null>(null)
  const found = options.findIndex((option) => option.value === value)
  const index = found < 0 ? 0 : found
  // Tab re-enters the group on the selected option, never on wherever focus last wandered.
  const stop = focused ?? index

  const go = (next: number) => {
    const i = (next + options.length) % options.length
    buttons.current[i]?.focus()
  }

  const select = (next: string) => {
    if (next === value) return
    cue("toggle")
    onValueChange(next)
  }

  return (
    <div
      role="radiogroup"
      aria-label={label}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setFocused(null)
      }}
      className={clsx(
        "chrome grid auto-cols-fr grid-flow-col gap-px rounded-[3px] border border-line bg-raised p-[2px]",
        className,
      )}
    >
      {options.map((option, i) => (
        <button
          key={option.value}
          ref={(node) => {
            buttons.current[i] = node
          }}
          type="button"
          role="radio"
          aria-checked={i === index}
          tabIndex={i === stop ? 0 : -1}
          onFocus={() => setFocused(i)}
          onClick={() => select(option.value)}
          onKeyDown={(e) => {
            if (e.key === "ArrowRight" || e.key === "ArrowDown") go(i + 1)
            else if (e.key === "ArrowLeft" || e.key === "ArrowUp") go(i - 1)
            else if (e.key === "Home") go(0)
            else if (e.key === "End") go(options.length - 1)
            // Handled here rather than left to the button's own click, so the key that
            // commits is the same one in every browser and nothing fires twice.
            else if (e.key === "Enter" || e.key === " ") select(option.value)
            else return
            e.preventDefault()
          }}
          className={clsx(
            "mono-label relative flex h-6 items-center justify-center rounded-[3px] px-2.5 whitespace-nowrap transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
            i === index ? "text-ink" : "text-muted hover:text-ink-soft",
          )}
        >
          {i === index ? (
            <motion.span
              layoutId={thumbId}
              aria-hidden
              transition={{ duration: reduced ? 0 : duration.settle, ease: OUT }}
              className="absolute inset-0 rounded-[3px] bg-ground"
            />
          ) : null}
          <span className="relative">{option.label}</span>
        </button>
      ))}
    </div>
  )
}
