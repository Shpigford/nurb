import { describe, it, expect, afterEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import ParamRail from "./ParamRail"

afterEach(cleanup)

describe("ParamRail", () => {
  it("is 288 wide and counts the parameters in its strip", () => {
    const { container } = render(<ParamRail count={14} params={<div>SLIDERS</div>} actions={<button type="button">DOWNLOAD</button>} />)
    const rail = container.querySelector("aside") as HTMLElement
    expect(rail.className).toContain("w-[288px]")
    expect(rail.className).toContain("panel")
    expect(screen.getByText("Parameters")).toBeTruthy()
    expect(screen.getByText("14")).toBeTruthy()
    expect(screen.getByText("SLIDERS")).toBeTruthy()
    expect(screen.getByText("DOWNLOAD")).toBeTruthy()
  })

  it("scrolls an oversized footer so its actions remain reachable", () => {
    const { container } = render(
      <ParamRail
        count={1}
        params={<div>SLIDERS</div>}
        disclosures={<div>LOTS OF OPEN DISCLOSURES</div>}
        actions={<button type="button">REBUILD</button>}
      />
    )

    const footer = screen.getByText("LOTS OF OPEN DISCLOSURES").parentElement as HTMLElement
    expect(footer.className).toContain("min-h-0")
    expect(footer.className).toContain("overflow-y-auto")
    expect(footer.className).not.toContain("shrink-0")
    expect(screen.getByRole("button", { name: "REBUILD" })).toBeTruthy()
    expect(container.querySelector("aside")?.className).toContain("overflow-hidden")
  })

  it("puts what the spec pinned above what the user may drag", () => {
    render(
      <ParamRail
        count={2}
        pinned={[{ name: "block_width", value: "25.16 mm" }]}
        params={<div>SLIDERS</div>}
        actions={null}
      />
    )
    expect(screen.getByText("Pinned by spec")).toBeTruthy()
    expect(screen.getByText("block_width")).toBeTruthy()
    expect(screen.getByText("25.16 mm")).toBeTruthy()
    // The "Yours to drag" rule belongs to ParamsPanel, so the rail never draws it twice.
    expect(screen.queryByText("Yours to drag")).toBeNull()
  })

  it("reads mass, print time and height, and dashes what it does not know", () => {
    const { rerender } = render(
      <ParamRail count={1} params={null} actions={null} readouts={{ grams: 42, seconds: 4320, heightMm: 110 }} />
    )
    expect(screen.getByText("42")).toBeTruthy()
    expect(screen.getByText("1:12")).toBeTruthy()
    expect(screen.getByText("110")).toBeTruthy()
    expect(screen.getByText("g")).toBeTruthy()
    expect(screen.getByText("hr")).toBeTruthy()
    expect(screen.getByText("mm")).toBeTruthy()

    rerender(<ParamRail count={1} params={null} actions={null} readouts={{}} />)
    expect(screen.getAllByText("-").length).toBe(3)
  })

  it("surfaces only the warning count, never the passing checks", () => {
    const { rerender } = render(<ParamRail count={1} params={null} actions={null} warnCount={0} />)
    expect(screen.queryByText(/warn/i)).toBeNull()
    rerender(<ParamRail count={1} params={null} actions={null} warnCount={1} />)
    expect(screen.getByText("1 warn")).toBeTruthy()
    rerender(<ParamRail count={1} params={null} actions={null} warnCount={1} failCount={2} />)
    expect(screen.getByText("2 fails")).toBeTruthy()
  })
})
