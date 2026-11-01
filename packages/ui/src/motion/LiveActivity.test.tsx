import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import LiveActivity, { type Activity } from "./LiveActivity"

afterEach(cleanup)

const working: Activity = { id: "a1", title: "Building shelf", detail: "notch/shelf", tone: "working" }

describe("LiveActivity", () => {
  it("wears the running work and announces that it started", () => {
    render(<LiveActivity activity={working} onDismiss={() => {}} />)
    expect(screen.getByText("Building shelf")).toBeTruthy()
    expect(screen.getByText("notch/shelf")).toBeTruthy()
    expect(screen.getByRole("status").textContent).toBe("Building shelf started.")
    // Running work has nothing to dismiss yet.
    expect(screen.queryByRole("button", { name: "Dismiss activity" })).toBeNull()
  })

  it("offers the close once the work has resolved", () => {
    let gone = 0
    const { rerender } = render(<LiveActivity activity={working} onDismiss={() => (gone += 1)} />)
    rerender(<LiveActivity activity={{ ...working, tone: "done" }} onDismiss={() => (gone += 1)} />)
    expect(screen.getByRole("status").textContent).toBe("Building shelf finished.")
    fireEvent.click(screen.getByRole("button", { name: "Dismiss activity" }))
    expect(gone).toBe(1)
  })

  it("is gone, not hidden, on a null activity", () => {
    render(<LiveActivity activity={null} />)
    expect(screen.queryByText("Building shelf")).toBeNull()
    expect(screen.getByRole("region", { name: "Activity" })).toBeTruthy()
  })
})
