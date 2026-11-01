import { describe, it, expect, afterEach, vi } from "vitest"
import { cleanup, act, render, screen, fireEvent } from "@testing-library/react"
import HoldToConfirm from "./HoldToConfirm"
import { cue } from "../sound"

vi.mock("../sound", () => ({ cue: vi.fn() }))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe("HoldToConfirm", () => {
  it("renders the label and a hint naming the hold", () => {
    render(<HoldToConfirm label="Delete part" holdMs={1200} onConfirm={() => {}} />)
    expect(screen.getByRole("button", { name: "Delete part" })).toBeTruthy()
    expect(screen.getByText(/Press and hold for 1.2 seconds/)).toBeTruthy()
  })

  it("a click alone confirms nothing", () => {
    const seen: string[] = []
    render(<HoldToConfirm label="Delete part" onConfirm={() => seen.push("gone")} />)
    fireEvent.click(screen.getByRole("button", { name: "Delete part" }))
    expect(seen).toEqual([])
  })

  it("starts the hold on press and sounds it", () => {
    render(<HoldToConfirm label="Delete part" onConfirm={() => {}} />)
    fireEvent.pointerDown(screen.getByRole("button", { name: "Delete part" }), { pointerType: "mouse", button: 0 })
    expect(cue).toHaveBeenCalledWith("press")
  })

  it("commits when the hold runs to full duration", () => {
    vi.useFakeTimers()
    const seen: string[] = []
    let now = 0
    const frames: FrameRequestCallback[] = []
    vi.spyOn(performance, "now").mockImplementation(() => now)
    vi.stubGlobal("requestAnimationFrame", (fn: FrameRequestCallback) => {
      frames.push(fn)
      return frames.length
    })
    vi.stubGlobal("cancelAnimationFrame", () => {})

    render(<HoldToConfirm label="Delete part" confirmLabel="Deleted" holdMs={120} onConfirm={() => seen.push("gone")} />)
    fireEvent.pointerDown(screen.getByRole("button", { name: "Delete part" }), { pointerType: "mouse", button: 0 })

    // Three 64ms frames clear the 120ms hold.
    for (let i = 0; i < 3 && frames.length; i++) {
      const next = frames.shift()!
      now += 64
      act(() => next(now))
    }
    expect(seen).toEqual(["gone"])
    expect(screen.getByRole("status").textContent).toBe("Deleted")

    vi.unstubAllGlobals()
    vi.useRealTimers()
    vi.restoreAllMocks()
  })
})
