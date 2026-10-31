import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import NewItemsPill from "./NewItemsPill"

afterEach(cleanup)

describe("NewItemsPill", () => {
  it("is absent at zero", () => {
    render(<NewItemsPill count={0} onClick={() => {}} />)
    expect(screen.queryByRole("button")).toBeNull()
  })

  it("states the count it was given and reports the click", () => {
    let jumped = 0
    render(<NewItemsPill count={3} onClick={() => (jumped += 1)} label={(n) => `${n} new parts`} />)
    fireEvent.click(screen.getByRole("button", { name: "3 new parts" }))
    expect(jumped).toBe(1)
  })
})
