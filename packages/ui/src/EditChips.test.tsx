import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import EditChips, { changedLines, diffDefaults, keywordDefaults } from "./EditChips"

afterEach(cleanup)

const before = `from nurb import *

@part
def dispenser(width=80.0, wall=2.0, lip=3.0):
    return Box(width, wall, lip)
`
const after = `from nurb import *

@part
def dispenser(width=80.0, wall=2.4, chamfer_size=1.0):
    return Box(width, wall, chamfer_size)
`

describe("diffDefaults", () => {
  it("reads the keyword defaults of the part function", () => {
    expect([...keywordDefaults(before)]).toEqual([
      ["width", "80.0"],
      ["wall", "2.0"],
      ["lip", "3.0"],
    ])
  })

  it("names what moved, what arrived and what went away", () => {
    expect(diffDefaults(before, after)).toEqual(["wall 2.0 to 2.4", "added chamfer_size", "removed lip"])
  })

  it("ignores anything that is not a keyword default", () => {
    const plain = "def dispenser(width, *, wall=2.0, count: int = 4):\n    pass"
    expect([...keywordDefaults(plain)]).toEqual([
      ["wall", "2.0"],
      ["count", "4"],
    ])
  })

  it("splits on the commas between parameters, not the ones inside a call", () => {
    const nested = "def rail(at=Vector(1, 2), wall=2.0):\n    pass"
    expect([...keywordDefaults(nested)]).toEqual([
      ["at", "Vector(1, 2)"],
      ["wall", "2.0"],
    ])
  })

  it("says nothing when no signature is in the text", () => {
    expect(diffDefaults("keep = body", "keep = shell")).toEqual([])
  })
})

describe("changedLines", () => {
  it("trims the matching head and tail", () => {
    expect(changedLines("a\nb\nc", "a\nB\nc")).toEqual([
      { sign: "-", text: "b" },
      { sign: "+", text: "B" },
    ])
  })
})

describe("EditChips", () => {
  it("renders one chip per changed default and opens a diff", () => {
    render(<EditChips input={{ part_name: "dispenser", old_string: before, new_string: after }} />)
    const chip = screen.getByRole("button", { name: "wall 2.0 to 2.4" })
    expect(screen.getByRole("button", { name: "added chamfer_size" })).toBeInTheDocument()
    expect(chip).toHaveAttribute("aria-expanded", "false")
    fireEvent.click(chip)
    expect(chip).toHaveAttribute("aria-expanded", "true")
    expect(screen.getByText(/def dispenser\(width=80.0, wall=2.4/)).toBeInTheDocument()
  })

  it("falls back to the part when only the new source is there", () => {
    render(<EditChips input={{ part_name: "dispenser", source: after }} />)
    expect(screen.getByRole("button", { name: "edited dispenser" })).toBeInTheDocument()
  })

  it("renders nothing for a call that is not a part edit", () => {
    const { container } = render(<EditChips input={{ command: "ls" }} />)
    expect(container).toBeEmptyDOMElement()
  })
})
