import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import EmptyShelf from "./EmptyShelf"

afterEach(cleanup)

describe("EmptyShelf", () => {
  it("asks the question and offers nothing by default", () => {
    render(<EmptyShelf />)
    expect(screen.getByText(/Empty shelf/)).toBeTruthy()
    expect(screen.queryByRole("button")).toBeNull()
  })

  it("runs the primary action and offers the quieter way in under it", () => {
    const seen: string[] = []
    render(
      <EmptyShelf
        primary={{ label: "New part", onClick: () => seen.push("new") }}
        secondary={{ label: "Open a folder", onClick: () => seen.push("open") }}
      />
    )
    fireEvent.click(screen.getByRole("button", { name: /New part/ }))
    fireEvent.click(screen.getByRole("button", { name: "Open a folder" }))
    expect(seen).toEqual(["new", "open"])
  })

  it("disables the secondary action when the host says so", () => {
    render(<EmptyShelf secondary={{ label: "Open a folder", onClick: () => {}, disabled: true }} />)
    expect(screen.getByRole("button", { name: "Open a folder" })).toHaveProperty("disabled", true)
  })
})
