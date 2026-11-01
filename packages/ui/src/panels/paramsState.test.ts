import { describe, it, expect } from "vitest"
import { adjustable, decimals, detentsFor, dirtyValues, rangeFor, sliderRange, tidy } from "./paramsState"
import type { Param } from "../types"

const width: Param = { name: "width", kind: "float", default: 40.0 }
const count: Param = { name: "count", kind: "int", default: 4, description: "how many" }
const flag: Param = { name: "flag", kind: "bool", default: false }
const name: Param = { name: "label", kind: "str", default: "x" }

describe("paramsState", () => {
  it("spans half to double and never starts a positive int at zero", () => {
    expect(sliderRange(40, false)).toEqual({ lo: 20, hi: 80, step: 1 })
    expect(sliderRange(4, true)).toEqual({ lo: 2, hi: 8, step: 1 })
    expect(sliderRange(1, true).lo).toBe(1)
    const zero = sliderRange(0, false)
    expect(zero.lo).toBe(0)
    expect(zero.hi).toBe(1)
  })

  it("keeps a negative default inside its range", () => {
    const range = sliderRange(-3, false)
    expect(range.lo).toBeLessThanOrEqual(-3)
    expect(range.hi).toBeGreaterThanOrEqual(-3)
  })

  it("never gives an int slider fewer than four stops", () => {
    const range = sliderRange(1, true)
    expect(range.hi - range.lo).toBeGreaterThanOrEqual(4)
  })

  it("keeps a fractional default on the step grid", () => {
    expect(sliderRange(9.5, false)).toEqual({ lo: 4.7, hi: 19, step: 0.1 })
    expect(sliderRange(92.5, false)).toEqual({ lo: 46.2, hi: 185, step: 0.1 })
    expect(sliderRange(0.25, false).step).toBe(0.01)
  })

  it("tidies to a number someone would write", () => {
    expect(tidy(0.30000000000000004, 0.1)).toBe(0.3)
    expect(tidy(42.00000001, 1)).toBe(42)
  })

  it("counts written decimal places and caps runaway fractions", () => {
    expect(decimals(12)).toBe(0)
    expect(decimals(9.5)).toBe(1)
    expect(decimals(1 / 3)).toBe(4)
    expect(decimals(1e-7)).toBe(0)
  })

  it("gives controls to bool, int, and float only", () => {
    expect(adjustable(width) && adjustable(count) && adjustable(flag)).toBe(true)
    expect(adjustable(name)).toBe(false)
  })

  it("keeps only what differs from the declared default", () => {
    const params = [width, count, flag, name]
    expect(dirtyValues(params, {})).toEqual({})
    expect(dirtyValues(params, { width: 40.0, count: 4 })).toEqual({})
    expect(dirtyValues(params, { width: 55, flag: true })).toEqual({ width: 55, flag: true })
  })
})

const wall: Param = { name: "wall", kind: "float", default: 2.0 }

describe("detentsFor", () => {
  it("gives an int slider nothing, because every stop is already a detent", () => {
    expect(detentsFor(count, [{ value_mm: 4 }])).toEqual([])
  })

  it("gives a bool and a string nothing either", () => {
    expect(detentsFor(flag, undefined)).toEqual([])
    expect(detentsFor(name, undefined)).toEqual([])
  })

  it("always marks the declared default", () => {
    expect(detentsFor(width, undefined)).toEqual([{ value: 40, label: "default" }])
  })

  it("marks a measurement inside the range and drops one outside it", () => {
    // width 40 spans 20 to 80.
    const out = detentsFor(width, [{ value_mm: 25.16 }, { value_mm: 4 }, { value_mm: 900 }])
    expect(out).toEqual([
      { value: 25.16, label: "measured" },
      { value: 40, label: "default" },
    ])
  })

  it("reads the range the slider reads, so a declared min and max hold the stops", () => {
    // Without the param's own range this would guess 20 to 80 and keep the 25.16.
    const narrow: Param = { ...width, min: 35, max: 45 }
    expect(rangeFor(narrow, false)).toEqual({ lo: 35, hi: 45, step: 1 })
    expect(detentsFor(narrow, [{ value_mm: 25.16 }, { value_mm: 42 }])).toEqual([
      { value: 40, label: "default" },
      { value: 42, label: "measured" },
    ])
  })

  it("keeps a measurement at its measured precision", () => {
    const out = detentsFor(width, [{ value_mm: 25.16 }])
    expect(out[0].value).toBe(25.16)
  })

  it("marks whole extrusion lines on a wall, from two lines up", () => {
    // wall 2.0 spans 1.0 to 4.0 on a 0.4 mm nozzle.
    const out = detentsFor(wall, undefined)
    expect(out.map((d) => d.value)).toEqual([1.2, 1.6, 2, 2.4, 2.8, 3.2, 3.6, 4])
    expect(out.map((d) => d.label)).toEqual([
      "3 lines",
      "4 lines",
      "default",
      "6 lines",
      "7 lines",
      "8 lines",
      "9 lines",
      "10 lines",
    ])
  })

  it("never offers a single line, which prints but does not hold", () => {
    const thin: Param = { name: "wall", kind: "float", default: 0.8 }
    const out = detentsFor(thin, undefined)
    expect(out.every((d) => d.value >= 0.8)).toBe(true)
    expect(out.map((d) => d.label)).not.toContain("1 lines")
  })

  it("reads the nozzle it is given", () => {
    const out = detentsFor(wall, undefined, 0.6)
    expect(out.map((d) => d.value)).toEqual([1.2, 1.8, 2, 2.4, 3, 3.6])
    expect(out[0].label).toBe("2 lines")
  })

  it("names a wall by wall, thickness, lip, rim or shell and nothing else", () => {
    for (const name of ["wall", "base_thickness", "lip_height", "rim", "shell_mm", "WALL"]) {
      expect(detentsFor({ name, kind: "float", default: 2.0 }, undefined).length).toBeGreaterThan(1)
    }
    expect(detentsFor({ name: "gap", kind: "float", default: 2.0 }, undefined)).toHaveLength(1)
  })

  it("keeps one label per value: default beats measured beats lines", () => {
    const out = detentsFor(wall, [{ value_mm: 2.0 }, { value_mm: 1.6 }])
    const at = (v: number) => out.find((d) => d.value === v)
    expect(at(2)?.label).toBe("default")
    expect(at(1.6)?.label).toBe("measured")
    expect(at(1.2)?.label).toBe("3 lines")
    expect(out.filter((d) => d.value === 2)).toHaveLength(1)
  })

  it("returns one ascending list", () => {
    const out = detentsFor(wall, [{ value_mm: 3.7 }, { value_mm: 1.1 }])
    const values = out.map((d) => d.value)
    expect([...values].sort((a, b) => a - b)).toEqual(values)
  })
})
