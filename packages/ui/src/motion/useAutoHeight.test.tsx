import { describe, it, expect, afterEach, vi } from "vitest"
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"
import { useState } from "react"
import { useAutoHeight } from "./useAutoHeight"

afterEach(cleanup)

// jsdom lays nothing out, so the measurement is stubbed to a real number.
function measured(height: number) {
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({ height } as DOMRect)
}

function Harness({ startOpen = false }: { startOpen?: boolean }) {
  const [open, setOpen] = useState(startOpen)
  const panel = useAutoHeight(open)
  return (
    <div>
      <button type="button" onClick={() => setOpen((v) => !v)}>
        toggle
      </button>
      <div data-testid="panel" data-height={String(panel.animate.height)} data-duration={panel.transition.duration} style={panel.style}>
        <div ref={panel.ref}>content</div>
      </div>
      <button type="button" onClick={panel.onAnimationComplete}>
        finish
      </button>
    </div>
  )
}

describe("useAutoHeight", () => {
  it("starts a closed panel at zero and hides its overflow", () => {
    measured(120)
    render(<Harness />)
    const panel = screen.getByTestId("panel")
    expect(panel.dataset.height).toBe("0")
    expect(panel.style.overflow).toBe("hidden")
  })

  it("travels to the measured height, then settles on auto", () => {
    measured(120)
    render(<Harness />)
    act(() => {
      fireEvent.click(screen.getByText("toggle"))
    })
    expect(screen.getByTestId("panel").dataset.height).toBe("120")
    act(() => {
      fireEvent.click(screen.getByText("finish"))
    })
    expect(screen.getByTestId("panel").dataset.height).toBe("auto")
  })

  it("renders an already-open panel at auto, so nothing flashes shut on mount", () => {
    measured(80)
    render(<Harness startOpen />)
    expect(screen.getByTestId("panel").dataset.height).toBe("auto")
  })
})
