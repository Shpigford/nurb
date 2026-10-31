import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import Menu from "./Menu"

afterEach(cleanup)

describe("Menu", () => {
  it("opens on the trigger and selects an item", () => {
    const seen: string[] = []
    render(<Menu label="More" items={[{ label: "Rename", onSelect: () => seen.push("rename") }]} />)
    const trigger = screen.getByRole("button", { name: "More" })
    expect(screen.queryByRole("menu")).toBeNull()
    fireEvent.click(trigger)
    fireEvent.click(screen.getByRole("menuitem", { name: "Rename" }))
    expect(seen).toEqual(["rename"])
    expect(screen.queryByRole("menu")).toBeNull()
  })

  it("closes on Escape", () => {
    render(<Menu label="More" items={[{ label: "Delete", onSelect: () => {}, tone: "danger" }]} />)
    fireEvent.click(screen.getByRole("button", { name: "More" }))
    expect(screen.getByRole("menu")).toBeTruthy()
    fireEvent.keyDown(document, { key: "Escape" })
    expect(screen.queryByRole("menu")).toBeNull()
  })
})
