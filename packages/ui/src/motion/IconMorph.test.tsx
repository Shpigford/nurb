import { describe, it, expect, afterEach } from "vitest"
import { cleanup, render, screen } from "@testing-library/react"
import IconMorph from "./IconMorph"

afterEach(cleanup)

function reduceMotion(reduce: boolean) {
  window.matchMedia = ((query: string) => ({
    matches: reduce && query.includes("reduce"),
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia
}

describe("IconMorph", () => {
  it("draws one path per slot, so the count never changes mid-morph", () => {
    reduceMotion(false)
    const { container, rerender } = render(<IconMorph preset="check-close" active={false} />)
    expect(container.querySelectorAll("path")).toHaveLength(2)
    rerender(<IconMorph preset="check-close" active={true} />)
    expect(container.querySelectorAll("path")).toHaveLength(2)
  })

  it("names itself only when nothing around it does", () => {
    reduceMotion(false)
    const { container } = render(<IconMorph preset="plus-minus" label="Add" />)
    expect(screen.getByRole("img", { name: "Add" })).toBeTruthy()
    expect(container.querySelector("svg")?.getAttribute("aria-hidden")).toBeNull()
  })

  it("lands on the second state under reduced motion", () => {
    reduceMotion(true)
    const { container } = render(<IconMorph preset="plus-minus" active={1} />)
    const paths = container.querySelectorAll("path")
    expect(paths).toHaveLength(2)
    // Minus is the same horizontal rule twice; the vertical stroke is gone.
    expect(paths[1].getAttribute("d")).toBe("M 5 12 L 19 12")
  })
})
