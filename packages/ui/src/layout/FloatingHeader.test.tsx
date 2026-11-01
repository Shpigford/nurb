import { describe, it, expect, afterEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import FloatingHeader, { HeaderCell, HeaderDivider, HeaderStack, HeaderStatus } from "./FloatingHeader"

afterEach(cleanup)

describe("FloatingHeader", () => {
  it("is a 52px floating panel", () => {
    const { container } = render(<FloatingHeader start={<HeaderCell>LOCKUP</HeaderCell>} />)
    const header = container.querySelector("header") as HTMLElement
    expect(header.className).toContain("h-[52px]")
    expect(header.className).toContain("panel")
    expect(screen.getByText("LOCKUP")).toBeTruthy()
  })

  it("stacks a label over its value and divides cells with a hairline", () => {
    const { container } = render(
      <FloatingHeader cells={<><HeaderDivider /><HeaderStack label="Project" value="Bench shelf" /></>} />
    )
    expect(container.querySelector(".w-px.bg-line")).toBeTruthy()
    expect(screen.getByText("Project")).toBeTruthy()
    expect(screen.getByText("Bench shelf")).toBeTruthy()
  })

  it("tints the status dot by tone", () => {
    const { container } = render(<FloatingHeader cells={<HeaderStatus tone="pass" label="Built rev 04" detail="0:47" />} />)
    expect(container.querySelector(".bg-pass")).toBeTruthy()
    expect(screen.getByText("0:47")).toBeTruthy()
  })
})
