import { describe, it, expect, afterEach } from "vitest"
import { cleanup, render, screen } from "@testing-library/react"
import PanelStrip from "./PanelStrip"

afterEach(cleanup)

describe("PanelStrip", () => {
  it("renders the label and the trailing count", () => {
    render(<PanelStrip label="Parameters" trailing="6" />)
    expect(screen.getByText("Parameters")).toBeTruthy()
    expect(screen.getByText("6")).toBeTruthy()
  })

  it("drops the trailing slot when there is nothing to say, and takes the 16 inset", () => {
    const { container } = render(<PanelStrip label="Findings" inset={16} />)
    const strip = container.firstElementChild as HTMLElement
    expect(strip.className).toContain("px-4")
    expect(strip.className).toContain("h-[30px]")
    expect(strip.children.length).toBe(1)
  })
})
