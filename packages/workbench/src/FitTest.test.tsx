import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"
import type { ProjectMeasurement } from "./api"
import FitTest from "./FitTest"
import { part } from "./fixtures"

const guess = (name: string, provisional = true): ProjectMeasurement => ({
  name,
  value_mm: 56.2,
  unit: "mm",
  how: "snug, fit table",
  provisional,
  value_changed_at: null,
})
const stand = { ...part("phone_stand", "/a.glb"), measures: ["puck_fit"] }
const test = { ...part("phone_stand_fit_test", "/b.glb"), measures: ["puck_fit"] }

afterEach(() => vi.unstubAllGlobals())

describe("FitTest", () => {
  it("asks for a fit test before a long print with an untested fit", async () => {
    const ask = vi.fn()
    render(<FitTest part={stand} parts={[stand]} measurements={[guess("puck_fit")]} seconds={12600} onAsk={ask} />)
    expect(screen.getByText(/a 3 h 30 min print/)).toBeTruthy()
    await userEvent.click(screen.getByRole("button", { name: "Ask for a fit test" }))
    expect(ask).toHaveBeenCalledWith(expect.stringContaining("It should test puck fit and"))
  })

  it("opens the fit test once there is one", async () => {
    const open = vi.fn()
    render(<FitTest part={stand} parts={[stand, test]} measurements={[guess("puck_fit")]} seconds={null} onSelectPart={open} />)
    await userEvent.click(screen.getByRole("button", { name: "Open fit test" }))
    expect(open).toHaveBeenCalledWith("phone_stand_fit_test")
  })

  it("stays quiet for a short print or a fit already confirmed", () => {
    const { container, rerender } = render(
      <FitTest part={stand} parts={[stand]} measurements={[guess("puck_fit")]} seconds={1800} onAsk={vi.fn()} />,
    )
    expect(container.textContent).toBe("")
    rerender(<FitTest part={stand} parts={[stand]} measurements={[guess("puck_fit", false)]} seconds={12600} onAsk={vi.fn()} />)
    expect(container.textContent).toBe("")
  })

  it("opens the coupon that covers the fit still owed", async () => {
    const open = vi.fn()
    const parent = { ...stand, measures: ["puck_fit", "pocket_fit"] }
    const pocket = { ...part("pocket_fit_test", "/c.glb"), measures: ["pocket_fit"] }
    render(<FitTest part={parent} parts={[parent, test, pocket]} measurements={[guess("puck_fit", false), guess("pocket_fit")]} seconds={12600} onSelectPart={open} />)
    await userEvent.click(screen.getByRole("button", { name: "Open fit test" }))
    expect(open).toHaveBeenCalledWith(pocket.name)
  })

  it("warns without chat and waits for a long estimate before offering to request a coupon", () => {
    const ask = vi.fn()
    const props = { part: stand, parts: [stand], measurements: [guess("puck_fit")] }
    const { rerender } = render(<FitTest {...props} seconds={12600} />)
    expect(screen.getByText("Fit not tested")).toBeVisible()
    rerender(<FitTest {...props} seconds={null} onAsk={ask} />)
    expect(screen.getByText(/estimate its print time/)).toBeVisible()
    expect(screen.queryByRole("button", { name: "Ask for a fit test" })).toBeNull()
  })

  it("confirms the eligible print export and disables stale or modified settings", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ confirmed: true })))
    vi.stubGlobal("fetch", fetchMock)
    const props = { parts: [stand, test], measurements: [guess("puck_fit")], seconds: 600 }
    const { rerender } = render(<FitTest {...props} part={test} />)
    expect(screen.getByRole("button", { name: "It fits" })).toBeDisabled()
    const exported = { ...test, fit_export_id: "printed" }
    rerender(<FitTest {...props} part={exported} atSavedValues={false} />)
    expect(screen.getByRole("button", { name: "It fits" })).toBeDisabled()
    rerender(<FitTest {...props} part={exported} />)
    await userEvent.click(screen.getByRole("button", { name: "It fits" }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toMatch(/\/api\/parts\/part-phone_stand_fit_test\/confirm-fit$/)
    expect(JSON.parse(String(init.body))).toEqual({ export_id: "printed" })
  })

})
