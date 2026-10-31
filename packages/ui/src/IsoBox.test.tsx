import { describe, it, expect, afterEach } from "vitest"
import { cleanup, render } from "@testing-library/react"
import IsoBox from "./IsoBox"

afterEach(cleanup)

describe("IsoBox", () => {
  it("fills the three faces from a real bounding box", () => {
    const { container } = render(<IsoBox bbox={[80, 40, 20]} />)
    const filled = container.querySelectorAll("polygon[fill]")
    expect(filled.length).toBe(3)
  })

  it("falls back to a dashed ghost with no box", () => {
    const { container } = render(<IsoBox bbox={null} />)
    expect(container.querySelector("g")?.getAttribute("stroke-dasharray")).toBe("5 4")
  })
})
