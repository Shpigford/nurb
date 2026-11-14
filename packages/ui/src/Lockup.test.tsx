import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import Lockup from "./Lockup"

afterEach(cleanup)

describe("Lockup", () => {
  it("is a plain image with nowhere to go", () => {
    render(<Lockup />)
    expect(screen.getByRole("img", { name: "nurb" }).className).toContain("w-[65px]")
    expect(screen.queryByRole("button")).toBeNull()
  })

  it("draws the wordmark in the ink colour so it turns over in dark", () => {
    render(<Lockup />)
    const lockup = screen.getByRole("img", { name: "nurb" })
    expect(lockup.innerHTML).toContain('fill="currentColor"')
    expect(lockup.innerHTML).not.toContain("#121821")
  })

  it("becomes a button when it navigates", () => {
    const seen: string[] = []
    render(<Lockup size="panel" onNavigate={() => seen.push("home")} />)
    expect(screen.getByRole("img", { name: "nurb" }).className).toContain("w-[87px]")
    fireEvent.click(screen.getByRole("button"))
    expect(seen).toEqual(["home"])
  })
})
