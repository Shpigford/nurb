import { describe, expect, it } from "vitest"
import { joinSpots, splitSpots, spotPlace, spotText } from "./spot"

describe("spotText", () => {
  it("names the spot in the part's mm and says which way its face points", () => {
    expect(spotText([12.04, -3.96, 42], [0, 0, 1])).toBe("This spot on the part: 12, -4, 42 mm, on a face pointing up.")
    expect(spotText([0, 5.25, 1], [-1, 0, 0])).toBe("This spot on the part: 0, 5.3, 1 mm, on a side face pointing -X.")
    expect(spotText([1, 2, 3], [0.6, 0, 0.8])).toBe("This spot on the part: 1, 2, 3 mm, on a sloped face.")
  })
})

describe("splitSpots", () => {
  const spot = spotText([12, -4, 42], [0, 0, 1])

  it("reads the place back out of a spot sentence", () => {
    expect(spotPlace(spot)).toBe("12, -4, 42")
    expect(spotPlace("make this wall thicker")).toBeNull()
  })

  it("round-trips the spots and the typed words", () => {
    const sent = joinSpots([spot], "make this wall thicker")
    expect(sent).toBe(`${spot}\nmake this wall thicker`)
    expect(splitSpots(sent)).toEqual({ spots: [spot], rest: "make this wall thicker" })
    expect(joinSpots([spot], "")).toBe(spot)
    expect(splitSpots("no spots here")).toEqual({ spots: [], rest: "no spots here" })
  })
})
