import { describe, it, expect, vi, afterEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import MeasurementCard from "./MeasurementCard"
import type { Measurement } from "./types"

const recorded: Measurement = {
  name: "shelf_depth",
  value_mm: 180,
  how: "the user said 180",
  provisional: false,
}

const changed: Measurement = {
  name: "shelf_depth",
  value_mm: 184,
  how: "caliper on the rail",
  provisional: true,
  previous_value_mm: 180,
  stale_parts: ["bracket", "end_cap"],
}

describe("MeasurementCard", () => {
  // vitest runs with globals off, so Testing Library never registers its own cleanup.
  afterEach(cleanup)

  it("reads 'recorded' when the value never moved", () => {
    render(<MeasurementCard measurement={recorded} />)
    expect(screen.getByText("Measurement recorded")).toBeInTheDocument()
    expect(screen.getByText("180 mm")).toBeInTheDocument()
  })

  it("reads 'changed' and strikes the old value", () => {
    render(<MeasurementCard measurement={changed} />)
    expect(screen.getByText("Measurement changed")).toBeInTheDocument()
    const previous = screen.getByText("180 mm")
    expect(previous).toHaveClass("line-through")
    expect(screen.getByText("184 mm")).toBeInTheDocument()
  })

  it("calls onAccept with the measurement name", async () => {
    const onAccept = vi.fn()
    render(<MeasurementCard measurement={changed} onAccept={onAccept} />)
    await userEvent.click(screen.getByRole("button", { name: "Accept" }))
    expect(onAccept).toHaveBeenCalledWith("shelf_depth")
  })

  it("hides Accept when the measurement is not provisional", () => {
    render(<MeasurementCard measurement={recorded} onAccept={vi.fn()} />)
    expect(screen.queryByRole("button", { name: "Accept" })).toBeNull()
  })

  it("calls onEdit with the measurement name", async () => {
    const onEdit = vi.fn()
    render(<MeasurementCard measurement={changed} onEdit={onEdit} />)
    await userEvent.click(screen.getByRole("button", { name: "Edit" }))
    expect(onEdit).toHaveBeenCalledWith("shelf_depth")
  })

  it("rebuilds only the parts still stale", async () => {
    const onRebuild = vi.fn()
    render(<MeasurementCard measurement={changed} staleParts={["end_cap", "lid"]} onRebuild={onRebuild} />)
    expect(screen.getByText("end_cap is stale")).toBeInTheDocument()
    await userEvent.click(screen.getByRole("button", { name: "Rebuild" }))
    expect(onRebuild).toHaveBeenCalledWith(["end_cap"])
  })

  it("shows no Rebuild button without the handler", () => {
    render(<MeasurementCard measurement={changed} staleParts={["end_cap"]} />)
    expect(screen.getByText("end_cap is stale")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Rebuild" })).toBeNull()
  })

  it("says Rebuilding while a rebuild runs", () => {
    render(<MeasurementCard measurement={changed} onRebuild={vi.fn()} rebuilding />)
    expect(screen.getByRole("button", { name: "Rebuilding…" })).toBeDisabled()
  })

  it("drops the stale strip once nothing is stale", () => {
    render(<MeasurementCard measurement={changed} staleParts={["lid"]} onRebuild={vi.fn()} />)
    expect(screen.queryByText(/stale/)).toBeNull()
    expect(screen.queryByRole("button", { name: "Rebuild" })).toBeNull()
  })
})
