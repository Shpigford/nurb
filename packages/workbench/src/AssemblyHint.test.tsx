import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import type { Finding } from "@nurb/ui"
import { describe, expect, it, vi } from "vitest"
import AssemblyHint, { redrawnSiblings } from "./AssemblyHint"
import { part } from "./fixtures"

const base = part("drive_base", "/a.glb")
const disk = part("drive_disk", "/b.glb")
const stand = part("drive_stand", "/c.glb")
const fit = part("drive_stand_fit_test", "/d.glb")
const parts = [base, disk, stand, fit]
const shared = [{ name: "drive_shapes", used_by: ["drive_base", "drive_disk", "drive_stand", "drive_stand_fit_test"] }]
const apart: Finding[] = [{ rule: "solids", severity: "fail", message: "not one piece" }]

describe("redrawnSiblings", () => {
  it("names the siblings a part in pieces shares its shapes with", () => {
    expect(redrawnSiblings(stand, parts, shared, apart)).toEqual(["drive_base", "drive_disk"])
  })

  it("stays quiet for a part in one piece, or one that is already an assembly", () => {
    expect(redrawnSiblings(stand, parts, shared, [])).toEqual([])
    expect(redrawnSiblings({ ...stand, uses: ["drive_base"] }, parts, shared, apart)).toEqual([])
    expect(redrawnSiblings(stand, parts, [], apart)).toEqual([])
  })
})

describe("AssemblyHint", () => {
  it("writes the request in the chat", async () => {
    const ask = vi.fn()
    render(<AssemblyHint siblings={["drive_base", "drive_disk"]} onAsk={ask} />)
    expect(screen.getByText(/shares its shapes with drive base and drive disk/)).toBeTruthy()
    await userEvent.click(screen.getByRole("button", { name: "Ask to make it an assembly" }))
    expect(ask).toHaveBeenCalledWith(expect.stringContaining("places the real drive_base and drive_disk parts"))
  })
})
