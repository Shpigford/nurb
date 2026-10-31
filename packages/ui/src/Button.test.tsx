import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import Button, { IconButton } from "./Button"

afterEach(cleanup)

describe("Button", () => {
  it("renders a label and fires onClick", () => {
    const seen: string[] = []
    render(
      <Button variant="accent" icon="plus" onClick={() => seen.push("hit")}>
        New part
      </Button>
    )
    const button = screen.getByRole("button", { name: /New part/ })
    expect(button.className).toContain("bg-accent")
    fireEvent.click(button)
    expect(seen).toEqual(["hit"])
  })

  it("IconButton labels itself for assistive tech", () => {
    render(<IconButton icon="trash" label="Delete part" active />)
    expect(screen.getByRole("button", { name: "Delete part" }).className).toContain("bg-accent-wash")
  })
})
