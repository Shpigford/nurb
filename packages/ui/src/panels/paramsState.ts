// Pure logic for the parameter panel: slider ranges inferred from defaults and
// the dirty-value diff. Free of React and the DOM so a plain runner can drive it.

import type { Detent } from "../motion/useSliderDetents"
import type { Param, Params } from "../types"

// No part annotates a range, so one is guessed the way the OSS viewer does:
// half the default to double it, never a 0-based range (item_depth=0 is an
// error, not a design), soft (typing outside widens it). `int` must be told,
// never inferred: Python's 1.0 arrives in JS as 1.
export function sliderRange(defaultValue: number, int: boolean) {
  let lo: number
  let hi: number
  if (defaultValue === 0) {
    lo = 0
    hi = int ? 8 : 1
  } else if (defaultValue < 0) {
    lo = defaultValue * 2
    hi = defaultValue / 2
  } else {
    lo = defaultValue / 2
    hi = defaultValue * 2
  }
  if (int) {
    lo = Math.floor(lo)
    hi = Math.ceil(hi)
    if (defaultValue >= 1) lo = Math.max(1, lo)
    if (hi - lo < 4) hi = lo + 4 // never a slider with two stops on it
    return { lo, hi, step: 1 }
  }
  // The default must sit on the step grid, or the thumb snaps to a neighbour
  // while the fill and the number show the real value (9.5 on a step of 1).
  const step = Math.min(10 ** (Math.floor(Math.log10(hi - lo)) - 1), 10 ** -decimals(defaultValue))
  return { lo: tidy(Math.floor(lo / step) * step, step), hi: tidy(Math.ceil(hi / step) * step, step), step }
}

// A param may annotate its own range; otherwise it is guessed from the default.
// One helper, so the slider and its stops never resolve the range differently.
export function rangeFor(param: Param, int: boolean) {
  const guess = sliderRange(param.default as number, int)
  return {
    lo: param.min ?? guess.lo,
    hi: param.max ?? guess.hi,
    step: param.step ?? guess.step,
  }
}

// Decimal places a number is written with, capped so 1/3 never asks for a
// step of 1e-16. 9.5 -> 1, 12 -> 0.
export function decimals(value: number): number {
  const text = String(value)
  const dot = text.indexOf(".")
  return dot === -1 || text.includes("e") ? 0 : Math.min(text.length - dot - 1, 4)
}

// A slider lands on 0.30000000000000004, which is not a dimension anyone chose.
export function tidy(value: number, step: number): number {
  const places = Math.max(0, -Math.floor(Math.log10(step)))
  return +value.toFixed(places)
}

export function adjustable(param: Param): boolean {
  return param.kind === "bool" || param.kind === "int" || param.kind === "float"
}

// The values that differ from the part's declared defaults: exactly what Apply
// writes back. Sending only the diff means an untouched panel sends {}.
export function dirtyValues(params: Param[], values: Params): Params {
  const out: Params = {}
  for (const param of params) {
    if (!adjustable(param)) continue
    const held = values[param.name]
    if (held === undefined || held === param.default) continue
    out[param.name] = held
  }
  return out
}

// A project measurement, narrowed to what a detent needs. Structural on purpose:
// the workbench's ProjectMeasurement carries more fields and assigns without a cast.
export interface Measurement {
  value_mm: number
}

// Names that describe a printed wall. A wall is printed in whole extrusion lines,
// so 1.2 mm on a 0.4 mm nozzle is three lines and 1.3 mm is three lines plus a gap.
const WALLISH = /wall|thickness|lip|rim|shell/

// The stops a float slider hands the pointer: the declared default, anything the
// project measured, and, on a wall, every whole number of extrusion lines.
// An int slider gets none. Its every stop is already a detent.
export function detentsFor(param: Param, measurements: Measurement[] | undefined, nozzle = 0.4): Detent[] {
  if (param.kind !== "float" || typeof param.default !== "number") return []
  const { lo, hi, step } = rangeFor(param, false)
  const inside = (value: number) => Number.isFinite(value) && value >= lo && value <= hi

  // Pushed in priority order, so the first label on a value is the one that wins.
  const found: Detent[] = [{ value: param.default, label: "default" }]
  for (const m of measurements ?? []) {
    if (inside(m.value_mm)) found.push({ value: m.value_mm, label: "measured" })
  }
  if (WALLISH.test(param.name.toLowerCase()) && nozzle > 0) {
    // From two lines up. One line is a skin: it prints, it just does not hold,
    // so offering it as a stop would be offering a wall that snaps.
    for (let n = 2; n * nozzle <= hi; n += 1) {
      const value = tidy(n * nozzle, 0.001)
      if (inside(value)) found.push({ value, label: `${n} lines` })
    }
  }

  // Two stops a step apart are one stop. The key is tidied to the slider's grid,
  // the kept detent keeps its own value, so a measured 25.16 stays 25.16.
  const byValue = new Map<number, Detent>()
  for (const detent of found) {
    const key = tidy(detent.value, step)
    if (!byValue.has(key)) byValue.set(key, detent)
  }
  return [...byValue.values()].sort((a, b) => a.value - b.value)
}
