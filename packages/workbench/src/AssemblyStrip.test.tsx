import { afterEach, describe, expect, it } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import AssemblyStrip, { assemblyOf } from "./AssemblyStrip"
import { part } from "./fixtures"

afterEach(cleanup)

const holder = { ...part("holder", "/g/h"), uses: ["arm", "roller"] }
const arm = { ...part("arm", "/g/a"), assembly: "holder" }
const roller = { ...part("roller", "/g/r"), assembly: "holder" }
const loose = part("loose", "/g/l")
const parts = [arm, holder, loose, roller]

describe("AssemblyStrip", () => {
  it("is the assembly and its parts, from either end", () => {
    expect(assemblyOf(holder, parts).map((p) => p.name)).toEqual(["holder", "arm", "roller"])
    expect(assemblyOf(roller, parts).map((p) => p.name)).toEqual(["holder", "arm", "roller"])
    expect(assemblyOf(loose, parts)).toEqual([])
    // A part inside a nested assembly gets the strip of the assembly that places it.
    const top = { ...part("top", "/g/t"), uses: ["sub"] }
    const sub = { ...part("sub", "/g/s"), uses: ["leaf"], assembly: "top" }
    const leaf = { ...part("leaf", "/g/f"), assembly: "top" }
    expect(assemblyOf(leaf, [top, sub, leaf]).map((p) => p.name)).toEqual(["sub", "leaf"])
  })

  it("moves between the assembly and a part", () => {
    const seen: string[] = []
    render(<AssemblyStrip group={assemblyOf(arm, parts)} selected={arm} onSelect={(n) => seen.push(n)} />)
    expect(screen.getByText("Assembly · 2 parts")).toBeTruthy()
    expect(screen.getByRole("button", { name: /Arm/ }).getAttribute("aria-pressed")).toBe("true")
    fireEvent.click(screen.getByRole("button", { name: /Holder/ }))
    expect(seen).toEqual(["holder"])
  })

  it("draws nothing for a plain part", () => {
    const { container } = render(<AssemblyStrip group={[]} selected={loose} onSelect={() => {}} />)
    expect(container.innerHTML).toBe("")
  })
})
