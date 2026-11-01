import { describe, it, expect, afterEach, vi } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { DetentMarks, useSliderDetents, type Detent } from "./useSliderDetents"

vi.mock("../sound", () => ({ cue: vi.fn() }))
const { cue } = await import("../sound")

afterEach(() => {
  cleanup()
  vi.mocked(cue).mockClear()
})

const DETENTS: Detent[] = [{ value: 0, label: "flat" }, { value: 50 }, { value: 100, label: "full" }]

function Harness({ value, onValueChange }: { value: number; onValueChange: (v: number) => void }) {
  const slider = useSliderDetents({ value, onValueChange, min: 0, max: 100, step: 1, detents: DETENTS })
  return (
    <div className="relative">
      <input
        type="range"
        aria-label="width"
        min={0}
        max={100}
        step={1}
        value={value}
        onChange={slider.onChange}
        onKeyDown={slider.onKeyDown}
      />
      <span data-testid="active">{slider.activeDetent}</span>
      <span data-testid="label">{slider.activeLabel ?? ""}</span>
      <DetentMarks detents={slider.detents} min={0} max={100} activeDetent={slider.activeDetent} />
    </div>
  )
}

describe("useSliderDetents", () => {
  it("renders a mark per detent, positioned by percentage", () => {
    render(<Harness value={20} onValueChange={() => {}} />)
    const marks = document.querySelectorAll("span[style]")
    expect(Array.from(marks).map((m) => (m as HTMLElement).style.left)).toEqual(["0%", "50%", "100%"])
  })

  it("snaps a pointer value inside the pull radius and ticks once", () => {
    const seen: number[] = []
    render(<Harness value={20} onValueChange={(v) => seen.push(v)} />)
    fireEvent.change(screen.getByLabelText("width"), { target: { value: "48" } })
    expect(seen).toEqual([50])
    expect(cue).toHaveBeenCalledWith("tick")
  })

  it("reports the parked detent and lets the keyboard step off it", () => {
    const seen: number[] = []
    const { rerender } = render(<Harness value={50} onValueChange={(v) => seen.push(v)} />)
    expect(screen.getByTestId("active").textContent).toBe("1")
    expect(screen.getByTestId("label").textContent).toBe("")

    const input = screen.getByLabelText("width")
    fireEvent.keyDown(input, { key: "ArrowRight" })
    fireEvent.change(input, { target: { value: "51" } })
    expect(seen).toEqual([51])
    expect(cue).not.toHaveBeenCalled()

    rerender(<Harness value={0} onValueChange={(v) => seen.push(v)} />)
    expect(screen.getByTestId("label").textContent).toBe("flat")
  })
})
