import { describe, it, expect, afterEach, vi } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { useState } from "react"
import SegmentedControl from "./SegmentedControl"

vi.mock("../sound", () => ({ cue: vi.fn() }))
const { cue } = await import("../sound")

afterEach(() => {
  cleanup()
  vi.mocked(cue).mockClear()
})

const VIEWS = [
  { value: "solid", label: "Solid" },
  { value: "wire", label: "Wire" },
  { value: "ghost", label: "Ghost" },
]

function Harness({ onValueChange }: { onValueChange?: (v: string) => void } = {}) {
  const [view, setView] = useState("solid")
  return (
    <SegmentedControl
      label="View"
      options={VIEWS}
      value={view}
      onValueChange={(v) => {
        setView(v)
        onValueChange?.(v)
      }}
    />
  )
}

describe("SegmentedControl", () => {
  it("renders a radiogroup with the current segment checked", () => {
    render(<Harness />)
    expect(screen.getByRole("radiogroup", { name: "View" })).toBeTruthy()
    expect(screen.getByRole("radio", { name: "Solid" }).getAttribute("aria-checked")).toBe("true")
    expect(screen.getByRole("radio", { name: "Wire" }).getAttribute("tabindex")).toBe("-1")
  })

  it("moves the selection on a click and sounds the toggle once", () => {
    const seen: string[] = []
    render(<Harness onValueChange={(v) => seen.push(v)} />)
    fireEvent.click(screen.getByRole("radio", { name: "Ghost" }))
    expect(seen).toEqual(["ghost"])
    expect(cue).toHaveBeenCalledWith("toggle")

    // Re-picking what is already picked is not a change.
    fireEvent.click(screen.getByRole("radio", { name: "Ghost" }))
    expect(seen).toEqual(["ghost"])
    expect(vi.mocked(cue).mock.calls.length).toBe(1)
  })

  it("moves focus on the arrow keys without selecting, and commits on Enter", () => {
    const seen: string[] = []
    render(<Harness onValueChange={(v) => seen.push(v)} />)
    const solid = screen.getByRole("radio", { name: "Solid" })
    const wire = screen.getByRole("radio", { name: "Wire" })
    solid.focus()

    // Arrowing past an option must not commit it: one keypress here is one network write.
    fireEvent.keyDown(solid, { key: "ArrowRight" })
    expect(seen).toEqual([])
    expect(document.activeElement).toBe(wire)
    expect(solid.getAttribute("aria-checked")).toBe("true")
    expect(wire.getAttribute("aria-checked")).toBe("false")
    expect(cue).not.toHaveBeenCalled()

    fireEvent.keyDown(wire, { key: "Enter" })
    expect(seen).toEqual(["wire"])
    expect(wire.getAttribute("aria-checked")).toBe("true")
    expect(cue).toHaveBeenCalledWith("toggle")
  })

  it("jumps to the ends and commits on Space", () => {
    const seen: string[] = []
    render(<Harness onValueChange={(v) => seen.push(v)} />)
    const solid = screen.getByRole("radio", { name: "Solid" })
    solid.focus()
    fireEvent.keyDown(solid, { key: "End" })
    const ghost = screen.getByRole("radio", { name: "Ghost" })
    expect(document.activeElement).toBe(ghost)
    expect(seen).toEqual([])
    fireEvent.keyDown(ghost, { key: " " })
    expect(seen).toEqual(["ghost"])
  })
})
