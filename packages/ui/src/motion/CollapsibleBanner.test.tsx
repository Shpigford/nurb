import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import CollapsibleBanner from "./CollapsibleBanner"

afterEach(cleanup)

describe("CollapsibleBanner", () => {
  it("renders the title and its description", () => {
    render(<CollapsibleBanner title="Your card was declined" description="We retry on the 14th." tone="warn" />)
    expect(screen.getByText("Your card was declined")).toBeTruthy()
    expect(screen.getByText("We retry on the 14th.")).toBeTruthy()
    expect(screen.getByRole("button", { name: /Your card was declined/ }).getAttribute("aria-expanded")).toBe("true")
  })

  it("folds on the title and keeps the notice reachable", () => {
    const seen: string[] = []
    render(
      <CollapsibleBanner
        title="Payments are degraded"
        description="Charges settle once the provider recovers."
        dismissible={false}
        onStateChange={(s) => seen.push(s)}
      />
    )
    fireEvent.click(screen.getByRole("button", { name: /Payments are degraded/ }))
    expect(seen).toEqual(["folded"])
    expect(screen.getByRole("button", { name: /Payments are degraded/ }).getAttribute("aria-expanded")).toBe("false")
    expect(screen.queryByRole("button", { name: "Dismiss notice" })).toBeNull()
  })

  it("dismisses once and announces it", () => {
    let gone = 0
    render(<CollapsibleBanner title="All done" description="Nothing left to do." onDismiss={() => (gone += 1)} />)
    fireEvent.click(screen.getByRole("button", { name: "Dismiss notice" }))
    expect(gone).toBe(1)
    expect(screen.getByRole("status").textContent).toBe("Notice dismissed.")
  })
})
