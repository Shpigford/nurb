import { describe, it, expect, afterEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import Stage, { StageColumn, StageEmpty } from "./Stage"

afterEach(cleanup)

describe("Stage", () => {
  it("lays the header over a single row of columns on the stage ground", () => {
    const { container } = render(
      <Stage header={<header>HEADER</header>}>
        <StageColumn>VIEWER</StageColumn>
      </Stage>
    )
    const frame = container.firstElementChild as HTMLElement
    expect(frame.className).toContain("h-dvh")
    expect(frame.className).toContain("bg-stage")
    expect(frame.className).toContain("p-4")
    expect(screen.getByText("HEADER")).toBeTruthy()
    expect(screen.getByText("VIEWER").className).toContain("flex-1")
  })

  it("pads the top for a titlebar when asked", () => {
    const { container } = render(
      <Stage topInset={36}>
        <StageColumn>VIEWER</StageColumn>
      </Stage>
    )
    expect((container.firstElementChild as HTMLElement).style.paddingTop).toBe("36px")
  })

  it("centres an empty stage", () => {
    render(
      <Stage>
        <StageEmpty>NOTHING YET</StageEmpty>
      </Stage>
    )
    expect(screen.getByText("NOTHING YET").className).toContain("justify-center")
  })
})
