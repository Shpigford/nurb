import { describe, it, expect, afterEach } from "vitest"
import { cleanup, render, screen } from "@testing-library/react"
import ProgressBar from "./ProgressBar"

afterEach(cleanup)

describe("ProgressBar", () => {
  it("reports no value while the total is unknown", () => {
    render(<ProgressBar value={null} label="Building" pendingLabel="Sizing" />)
    const bar = screen.getByRole("progressbar")
    expect(bar.hasAttribute("aria-valuenow")).toBe(false)
    expect(bar.getAttribute("aria-valuemax")).toBe("100")
    // Once in the readout, once in the live region.
    expect(screen.getAllByText("Sizing")).toHaveLength(2)
  })

  it("hands over to the measured value", () => {
    const { rerender } = render(<ProgressBar value={null} label="Building" />)
    rerender(<ProgressBar value={62} label="Building" />)
    const bar = screen.getByRole("progressbar")
    expect(bar.getAttribute("aria-valuenow")).toBe("62")
    expect(screen.getByText("62%")).toBeTruthy()
  })

  it("quantizes to whole cells and announces the finish", () => {
    const { container } = render(<ProgressBar value={100} segments={4} completeLabel="Build complete" />)
    expect(container.querySelectorAll("[data-lit]")).toHaveLength(4)
    expect(screen.getByText("Build complete")).toBeTruthy()
  })
})
