import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import Lockup from "./Lockup"

afterEach(cleanup)

describe("Lockup", () => {
  it("is a plain image with nowhere to go", () => {
    render(<Lockup />)
    expect(screen.getByAltText("nurb").className).toContain("w-[65px]")
    expect(screen.queryByRole("button")).toBeNull()
  })

  it("becomes a button when it navigates", () => {
    const seen: string[] = []
    render(<Lockup size="panel" onNavigate={() => seen.push("home")} />)
    expect(screen.getByAltText("nurb").className).toContain("w-[87px]")
    fireEvent.click(screen.getByRole("button"))
    expect(seen).toEqual(["home"])
  })
})
