import { describe, it, expect, afterEach } from "vitest"
import { render, screen, cleanup, waitFor } from "@testing-library/react"
import { BuildFailedBanner, StageNotice } from "./BuildFailed"

afterEach(cleanup)

describe("BuildFailed", () => {
  it("names the revision that failed and the one on screen", () => {
    const { container } = render(<BuildFailedBanner revision={5} shownRevision={4} />)
    expect(screen.getByText("REV 05 failed at these values")).toBeTruthy()
    expect(screen.getByText("Showing rev 04, the last one that built.")).toBeTruthy()
    expect((container.firstElementChild as HTMLElement).className).toContain("bg-fail-wash")
    // A failed build is the one place the tone has to carry, so the banner says what it cost.
    expect(screen.getByText("That one didn't survive the checks. It didn't cost you a part either.")).toBeTruthy()
  })

  it("goes back up on its own when the error clears", async () => {
    const { rerender } = render(<BuildFailedBanner open revision={5} shownRevision={4} />)
    expect(screen.getByText("REV 05 failed at these values")).toBeTruthy()
    // The caller keeps it mounted and flips the flag, so the banner owns its exit.
    rerender(<BuildFailedBanner open={false} revision={5} shownRevision={4} />)
    await waitFor(() => expect(screen.queryByText("REV 05 failed at these values")).toBeNull())
  })

  it("floats the stage notice over the viewer column", () => {
    const { container } = render(<StageNotice>Showing rev 04 · rev 05 did not build</StageNotice>)
    const pill = container.firstElementChild as HTMLElement
    expect(pill.className).toContain("panel")
    expect(pill.className).toContain("rounded-full")
    expect(pill.className).toContain("top-4")
    expect(pill.className).toContain("left-4")
  })
})
