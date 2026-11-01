import { describe, it, expect, afterEach, vi } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import RailDisclosure from "./RailDisclosure"

afterEach(cleanup)

describe("RailDisclosure", () => {
  it("keeps the body closed until it is opened", async () => {
    const onToggle = vi.fn()
    const { rerender } = render(
      <RailDisclosure label="Spec and checks" summary="1 warn" tone="warn" open={false} onToggle={onToggle}>
        <div>DETAIL</div>
      </RailDisclosure>
    )
    const button = screen.getByRole("button")
    expect(button.getAttribute("aria-expanded")).toBe("false")
    // Mounted but hidden, so a slice still running survives the collapse.
    expect((screen.getByText("DETAIL").parentElement as HTMLElement).hidden).toBe(true)
    expect(screen.getByText("1 warn")).toBeTruthy()

    await userEvent.click(button)
    expect(onToggle).toHaveBeenCalledOnce()

    rerender(
      <RailDisclosure label="Spec and checks" summary="1 warn" tone="warn" open onToggle={onToggle}>
        <div>DETAIL</div>
      </RailDisclosure>
    )
    expect(screen.getByRole("button").getAttribute("aria-expanded")).toBe("true")
    expect(screen.getByText("DETAIL").parentElement?.className).toContain("max-h-48")
    expect((screen.getByText("DETAIL").parentElement as HTMLElement).hidden).toBe(false)
  })

  it("carries no glyph when there is nothing to flag", () => {
    const { container } = render(
      <RailDisclosure label="Print time" open={false} onToggle={() => {}}>
        <div>DETAIL</div>
      </RailDisclosure>
    )
    expect(container.querySelectorAll("svg").length).toBe(1)
  })
})
