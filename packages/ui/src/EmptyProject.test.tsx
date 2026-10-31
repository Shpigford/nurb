import { describe, it, expect, afterEach } from "vitest"
import { cleanup, render, screen } from "@testing-library/react"
import EmptyProject from "./EmptyProject"

afterEach(cleanup)

describe("EmptyProject", () => {
  it("stands the outline mark on the plate", () => {
    render(<EmptyProject />)
    expect(screen.getByText("No part yet")).toBeTruthy()
    expect(screen.getByText(/It builds here, live/)).toBeTruthy()
  })

  it("takes overrides", () => {
    render(<EmptyProject title="Nothing here" caption="Say what to make." />)
    expect(screen.getByText("Nothing here")).toBeTruthy()
    expect(screen.getByText("Say what to make.")).toBeTruthy()
  })
})
