import { describe, it, expect } from "vitest"
import { clock, elapsedLabel, formatBbox, initials, relativeTime } from "./format"

describe("elapsedLabel", () => {
  it("reads 0.0s at the start of a run", () => {
    expect(elapsedLabel(0)).toBe("0.0s")
  })

  it("keeps one decimal under a minute", () => {
    expect(elapsedLabel(4.2)).toBe("4.2s")
  })

  // The tenths would round to "60.0s" here, which is a minute spelled wrong.
  it("switches to m:ss before the tenths can read 60", () => {
    expect(elapsedLabel(59.96)).toBe("1:00")
  })

  it("reads m:ss over a minute", () => {
    expect(elapsedLabel(67)).toBe("1:07")
  })

  it("never goes negative", () => {
    expect(elapsedLabel(-3)).toBe("0.0s")
  })
})

describe("clock", () => {
  it("returns null with no figure", () => {
    expect(clock(null)).toBe(null)
    expect(clock(undefined)).toBe(null)
  })

  it("pads the seconds", () => {
    expect(clock(321)).toBe("5:21")
    expect(clock(9)).toBe("0:09")
  })

  it("rounds to the nearest second", () => {
    expect(clock(59.6)).toBe("1:00")
  })
})

describe("relativeTime", () => {
  const now = Date.parse("2026-09-16T12:00:00.000Z")

  it("says just now inside the first minute", () => {
    expect(relativeTime("2026-09-16T11:59:30.000Z", now)).toBe("just now")
  })

  it("climbs through minutes, hours, days and weeks", () => {
    expect(relativeTime("2026-09-16T11:20:00.000Z", now)).toBe("40m ago")
    expect(relativeTime("2026-09-16T05:00:00.000Z", now)).toBe("7h ago")
    expect(relativeTime("2026-09-14T12:00:00.000Z", now)).toBe("2d ago")
    expect(relativeTime("2026-08-26T12:00:00.000Z", now)).toBe("3w ago")
    expect(relativeTime("2026-06-16T12:00:00.000Z", now)).toBe("3mo ago")
  })

  it("has nothing to say about nothing", () => {
    expect(relativeTime(null)).toBe(null)
  })
})

describe("formatBbox", () => {
  it("rounds each axis to a tenth", () => {
    expect(formatBbox([80.04, 40, 19.96])).toBe("80 × 40 × 20")
  })

  it("refuses anything that is not three axes", () => {
    expect(formatBbox([80, 40])).toBe(null)
    expect(formatBbox(null)).toBe(null)
  })
})

describe("initials", () => {
  it("takes the first letter of two words", () => {
    expect(initials("Josh Pigford")).toBe("JP")
  })

  it("falls back to the email local part, then to a dot", () => {
    expect(initials("ada@example.com")).toBe("AD")
    expect(initials("Ada")).toBe("AD")
    expect(initials(null)).toBe("·")
  })
})
