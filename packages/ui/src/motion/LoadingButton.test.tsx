import { describe, it, expect, afterEach, vi } from "vitest"
import { cleanup, act, render, screen, fireEvent, waitFor } from "@testing-library/react"
import LoadingButton from "./LoadingButton"

vi.mock("../sound", () => ({ cue: vi.fn() }))

afterEach(cleanup)

function reduceMotion(reduce: boolean) {
  window.matchMedia = ((query: string) => ({
    matches: reduce && query.includes("reduce"),
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia
}

describe("LoadingButton", () => {
  it("reserves every label's width before the first click", () => {
    reduceMotion(false)
    render(<LoadingButton label="Save" successLabel="Saved" onAction={() => {}} />)
    expect(screen.getByRole("button", { name: "Save" })).toBeTruthy()
    // All four faces are on screen from the start, stacked in one cell.
    expect(screen.getByText("Saved")).toBeTruthy()
  })

  it("settles into success and announces it once", async () => {
    reduceMotion(false)
    render(<LoadingButton label="Save" successLabel="Saved" onAction={async () => {}} />)
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Save" }))
    })
    await waitFor(() => expect(screen.getByRole("button", { name: "Saved" })).toBeTruthy())
    expect(screen.getByRole("status").textContent).toBe("Saved")
  })

  it("still reaches the error state under reduced motion", async () => {
    reduceMotion(true)
    render(
      <LoadingButton
        label="Save"
        errorLabel="Retry"
        onAction={async () => {
          throw new Error("no")
        }}
      />
    )
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Save" }))
    })
    await waitFor(() => expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy())
  })
})
