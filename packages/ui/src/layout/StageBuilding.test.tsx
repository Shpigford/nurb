import { describe, it, expect, afterEach } from "vitest"
import { render, screen, cleanup, waitFor } from "@testing-library/react"
import { StageBuilding } from "./StageBuilding"

describe("StageBuilding", () => {
  afterEach(cleanup)

  it("says the model is rebuilding while open, and leaves when the build lands", async () => {
    const { rerender } = render(<StageBuilding open expected={2} />)
    expect(screen.getByRole("status")).toHaveTextContent("Rebuilding")

    rerender(<StageBuilding open={false} expected={2} />)
    await waitFor(() => expect(screen.queryByText("Rebuilding")).toBeNull())
  })
})
