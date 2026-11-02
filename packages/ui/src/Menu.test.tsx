import { describe, it, expect, afterEach, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import Menu, { useContextMenu, type MenuItem } from "./Menu"

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

  it("filters a long list by name and takes the first match on Enter", () => {
    const pick = vi.fn()
    render(
      <Menu
        label="Parts"
        filter="Find a part"
        items={["bin", "hook", "hinge"].map((name) => ({ label: name, checked: name === "bin", onSelect: () => pick(name) }))}
      />
    )
    fireEvent.click(screen.getByRole("button", { name: "Parts" }))
    const find = screen.getByRole("textbox", { name: "Find a part" })
    fireEvent.change(find, { target: { value: "h" } })
    expect(screen.queryByRole("menuitemradio", { name: "bin" })).toBeNull()
    expect(screen.getAllByRole("menuitemradio")).toHaveLength(2)
    fireEvent.change(find, { target: { value: "zzz" } })
    expect(screen.getByText("Nothing matches")).toBeTruthy()
    fireEvent.change(find, { target: { value: "hin" } })
    fireEvent.keyDown(find, { key: "Enter" })
    expect(pick).toHaveBeenCalledWith("hinge")
  })

  it("leaves the page once it has closed, so nothing invisible catches clicks", async () => {
    render(<Menu label="More" items={[{ label: "Rename", onSelect: () => {} }]} />)
    fireEvent.click(screen.getByRole("button", { name: "More" }))
    fireEvent.click(screen.getByRole("menuitem", { name: "Rename" }))
    await waitFor(() => expect(screen.queryByText("Rename")).toBeNull())
  })

  it("opens the same rows on a right-click, and leaves the native menu alone with nothing to offer", () => {
    const seen: string[] = []
    function Row({ items }: { items?: MenuItem[] }) {
      const context = useContextMenu()
      return (
        <div data-testid="row" onContextMenu={(e) => context.open(e, items)}>
          {context.menu}
        </div>
      )
    }
    const { rerender } = render(<Row items={[{ label: "Rename", onSelect: () => seen.push("rename") }]} />)
    expect(fireEvent.contextMenu(screen.getByTestId("row"))).toBe(false)
    fireEvent.click(screen.getByRole("menuitem", { name: "Rename" }))
    expect(seen).toEqual(["rename"])
    expect(screen.queryByRole("menu")).toBeNull()

    fireEvent.contextMenu(screen.getByTestId("row"))
    fireEvent.keyDown(document, { key: "Escape" })
    expect(screen.queryByRole("menu")).toBeNull()

    rerender(<Row />)
    expect(fireEvent.contextMenu(screen.getByTestId("row"))).toBe(true)
    expect(screen.queryByRole("menu")).toBeNull()
  })
})
