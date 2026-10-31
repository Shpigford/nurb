import { useMemo } from "react"
import { motion, useReducedMotion } from "motion/react"
import { duration, ease } from "./tokens"

// One path list whose coordinates interpolate, rather than two icons crossfaded
// over each other. Ported from interior.dev (MIT). Crossfading draws both shapes
// at once through the middle, and a copy button that briefly shows a check laid
// over an X is worse than no animation at all.
//
// It renders the glyph and nothing else, so it sits inside a Button that already
// owns the press, the label and the accessible name.

const OUT = ease.out as [number, number, number, number]
const NUMBER = /-?\d*\.?\d+/g
const CENTER = "12"

export type IconMorphPreset = "check-close" | "plus-minus"

const PRESETS: Record<IconMorphPreset, readonly (readonly string[])[]> = {
  "check-close": [
    ["M 5 12.5 L 10 17.5 L 19.5 7", "M 12 12 L 12 12 L 12 12"],
    ["M 6.5 6.5 L 12 12 L 17.5 17.5", "M 17.5 6.5 L 12 12 L 6.5 17.5"],
  ],
  "plus-minus": [
    ["M 5 12 L 19 12", "M 12 5 L 12 19"],
    ["M 5 12 L 19 12", "M 5 12 L 19 12"],
  ],
}

// A path whose points all collapse onto one coordinate draws nothing, so it fades
// instead. That keeps the number of paths fixed and stops a stroke popping into being.
function isCollapsed(d: string): boolean {
  const nums = d.match(NUMBER)
  if (!nums || nums.length < 4) return false
  return nums.every((n, i) => n === nums[i % 2])
}

function slotsFor(states: readonly (readonly string[])[], index: number) {
  const count = states.reduce((most, s) => Math.max(most, s.length), 0)
  const state = states[index] ?? states[0]
  return Array.from({ length: count }, (_, i) => {
    const own = state[i]
    const sibling = states.find((s) => s[i] !== undefined)?.[i] ?? ""
    const d = own ?? sibling.replace(NUMBER, CENTER)
    return { key: i, d, visible: !isCollapsed(d) }
  })
}

export default function IconMorph({
  preset = "check-close",
  active = 0,
  size = 12,
  strokeWidth = 1.75,
  label,
  className,
}: {
  preset?: IconMorphPreset
  /** Which state to show. A boolean maps to 0 and 1. */
  active?: number | boolean
  size?: number
  strokeWidth?: number
  /** Give the glyph its own accessible name when nothing around it carries one. */
  label?: string
  className?: string
}) {
  const states = PRESETS[preset]
  const index = typeof active === "boolean" ? (active ? 1 : 0) : Math.min(Math.max(Math.trunc(active), 0), 1)
  const slots = useMemo(() => slotsFor(states, index), [states, index])
  const reduced = useReducedMotion()
  const transition = reduced ? { duration: 0 } : { duration: duration.settle, ease: OUT }

  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      focusable="false"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={{ display: "block" }}
    >
      {slots.map((slot) => (
        <motion.path
          key={slot.key}
          initial={false}
          animate={{ d: slot.d, opacity: slot.visible ? 1 : 0 }}
          transition={transition}
        />
      ))}
    </svg>
  )
}
