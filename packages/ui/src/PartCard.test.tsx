import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import PartCard, { type PartCardPart } from "./PartCard"

afterEach(cleanup)

const built: PartCardPart = {
  id: "p1",
  name: "Shelf bracket",
  bbox: [80, 40, 20],
  status: "built",
  revision: 4,
  builtAt: new Date(Date.now() - 2 * 86_400_000).toISOString(),
}

describe("PartCard", () => {
  it("shows the revision, the dimensions and opens on click", () => {
    const seen: string[] = []
    render(<PartCard part={built} onOpen={() => seen.push("open")} />)
    expect(screen.getByText("REV 04")).toBeTruthy()
    expect(screen.getByText("80 × 40 × 20 mm")).toBeTruthy()
    expect(screen.getByText("Built 2d ago")).toBeTruthy()
    fireEvent.click(screen.getByRole("button", { name: "Open Shelf bracket" }))
    expect(seen).toEqual(["open"])
  })

  it("names the project only when it differs from the part", () => {
    render(<PartCard part={{ ...built, folder: "Shelf bracket" }} onOpen={() => {}} />)
    expect(screen.getByText("REV 04")).toBeTruthy()
    cleanup()
    render(<PartCard part={{ ...built, folder: "Garage wall" }} onOpen={() => {}} />)
    expect(screen.getByText("Garage wall")).toBeTruthy()
  })

  it("says Failed instead of a revision", () => {
    render(<PartCard part={{ ...built, status: "failed" }} onOpen={() => {}} />)
    expect(screen.getByText("Failed").className).toContain("text-warn")
  })

  it("stops pulsing once a build has run for 30 seconds", () => {
    const fresh = render(
      <PartCard
        part={{ ...built, status: "building", buildingSince: new Date(Date.now() - 5_000).toISOString() }}
        onOpen={() => {}}
      />
    )
    expect(fresh.container.querySelector('[data-build="running"]')).toBeTruthy()
    cleanup()
    const stalled = render(
      <PartCard
        part={{ ...built, status: "building", buildingSince: new Date(Date.now() - 45_000).toISOString() }}
        onOpen={() => {}}
      />
    )
    expect(stalled.container.querySelector('[data-build="running"]')).toBeNull()
    expect(stalled.container.querySelector('[data-build="stalled"]')).toBeTruthy()
  })

  it("says a draft is being designed while its agent works, and never shows a revision", () => {
    const draft: PartCardPart = { id: "d1", name: "A door stopper for the back door", status: "draft" }
    render(<PartCard part={{ ...draft, designing: true }} onOpen={() => {}} />)
    expect(screen.getByText("Being designed")).toBeTruthy()
    expect(screen.queryByText(/REV/)).toBeNull()
    cleanup()
    render(<PartCard part={draft} onOpen={() => {}} />)
    expect(screen.getByText("No design yet")).toBeTruthy()
  })

  it("renders the menu when it has items", () => {
    render(<PartCard part={built} onOpen={() => {}} menu={[{ label: "Delete", onSelect: () => {} }]} />)
    expect(screen.getByRole("button", { name: "More for Shelf bracket" })).toBeTruthy()
  })
})
