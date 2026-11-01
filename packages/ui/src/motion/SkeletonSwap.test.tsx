import { describe, it, expect, afterEach, vi } from "vitest"
import { act, cleanup, render } from "@testing-library/react"
import SkeletonSwap from "./SkeletonSwap"

afterEach(() => {
  cleanup()
  vi.useRealTimers()
})

describe("SkeletonSwap", () => {
  it("reserves the box and shows the content", () => {
    const { container, getByText } = render(
      <SkeletonSwap loading={false} lines={3} lineHeight={20}>
        <p>Measured</p>
      </SkeletonSwap>,
    )
    const shell = container.firstElementChild as HTMLElement
    expect(shell.style.height).toBe("60px")
    expect(shell.getAttribute("aria-busy")).toBe("false")
    expect(getByText("Measured")).toBeTruthy()
  })

  it("paints the skeleton only once the delay passes", () => {
    vi.useFakeTimers()
    const { container } = render(
      <SkeletonSwap loading delay={120}>
        <p>Measured</p>
      </SkeletonSwap>,
    )
    expect(container.querySelector("[data-skeleton]")).toBeNull()
    act(() => void vi.advanceTimersByTime(120))
    expect(container.querySelector("[data-skeleton]")).not.toBeNull()
  })

  it("keeps the skeleton off for an answer faster than the delay", () => {
    vi.useFakeTimers()
    const { container, rerender } = render(
      <SkeletonSwap loading delay={120}>
        <p>Measured</p>
      </SkeletonSwap>,
    )
    act(() => void vi.advanceTimersByTime(40))
    rerender(
      <SkeletonSwap loading={false} delay={120}>
        <p>Measured</p>
      </SkeletonSwap>,
    )
    act(() => void vi.advanceTimersByTime(400))
    expect(container.querySelector("[data-skeleton]")).toBeNull()
    expect((container.firstElementChild as HTMLElement).getAttribute("aria-busy")).toBe("false")
  })
})
