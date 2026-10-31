import { describe, it, expect, afterEach, beforeEach, vi } from "vitest"
import { act, cleanup, render, screen } from "@testing-library/react"
import ValueFlash from "./ValueFlash"

afterEach(cleanup)
beforeEach(() => {
  vi.useRealTimers()
})

describe("ValueFlash", () => {
  it("renders the formatted figure and announces it once it settles", () => {
    vi.useFakeTimers()
    render(<ValueFlash value={12.5} format={(v) => `${v.toFixed(1)} mm`} label="Width" />)
    expect(screen.getByText("12.5 mm")).toBeTruthy()
    act(() => {
      vi.advanceTimersByTime(700)
    })
    expect(screen.getByText("Width: 12.5 mm")).toBeTruthy()
  })

  it("flashes pass on a rise and fail on a fall, then clears after the hold", () => {
    vi.useFakeTimers()
    const { rerender, container } = render(<ValueFlash value={10} hold={500} />)
    const cell = container.firstElementChild as HTMLElement
    expect(cell.dataset.direction).toBeUndefined()

    rerender(<ValueFlash value={14} hold={500} />)
    expect(cell.dataset.direction).toBe("up")

    rerender(<ValueFlash value={9} hold={500} />)
    expect(cell.dataset.direction).toBe("down")

    act(() => {
      vi.advanceTimersByTime(500)
    })
    expect(cell.dataset.direction).toBeUndefined()
  })

  it("ignores a re-render that leaves the number where it was", () => {
    const { rerender, container } = render(<ValueFlash value={7} />)
    rerender(<ValueFlash value={7} />)
    expect((container.firstElementChild as HTMLElement).dataset.direction).toBeUndefined()
  })
})
