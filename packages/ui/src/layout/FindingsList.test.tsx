import { describe, it, expect, afterEach, vi } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import FindingsList from "./FindingsList"
import type { Finding } from "../types"

afterEach(cleanup)

const findings: Finding[] = [
  { rule: "thin_wall", label: "Thin wall", severity: "warn", message: "The back wall is 0.8 mm, under two extrusions." },
  { rule: "overhang", severity: "fail", message: "The hook overhangs 62 degrees and needs support." },
]

describe("FindingsList", () => {
  it("lists a row per finding, previews on hover and keeps a clicked one", async () => {
    const onHighlight = vi.fn()
    render(<FindingsList findings={findings} verdict="fail" highlight={1} onHighlight={onHighlight} />)
    expect(screen.getByText("Thin wall")).toBeTruthy()
    expect(screen.getByText("overhang")).toBeTruthy()

    const rows = screen.getAllByRole("button")
    expect(rows[1].className).toContain("bg-raised")
    expect(rows[1].getAttribute("aria-pressed")).toBe("true")
    await userEvent.hover(rows[0])
    expect(onHighlight).toHaveBeenCalledWith(0)
    // Leaving the row must not drop the pick: the user looks at the part next.
    await userEvent.unhover(rows[0])
    expect(onHighlight).not.toHaveBeenCalledWith(null)
    await userEvent.click(rows[0])
    expect(onHighlight).toHaveBeenLastCalledWith(0)
    await userEvent.click(rows[1])
    expect(onHighlight).toHaveBeenLastCalledWith(null)
  })

  it("counts the findings above the rows, and says so in the singular", () => {
    const { rerender } = render(<FindingsList findings={findings} verdict="fail" />)
    expect(screen.getByText("2 findings to fix.")).toBeTruthy()
    rerender(<FindingsList findings={findings.slice(0, 1)} verdict="warn" />)
    expect(screen.getByText("1 finding to fix.")).toBeTruthy()
  })

  it("says what an empty list means for each verdict", () => {
    const { rerender } = render(<FindingsList findings={[]} verdict="none" />)
    expect(screen.getByText("Nothing checked yet")).toBeTruthy()
    rerender(<FindingsList findings={[]} verdict="fail" />)
    expect(screen.getByText("The build stopped before the checks ran")).toBeTruthy()
    rerender(<FindingsList findings={[]} verdict="pass" />)
    expect(screen.getByText("Nothing to fix. Checks pass at these numbers.")).toBeTruthy()
  })
})
