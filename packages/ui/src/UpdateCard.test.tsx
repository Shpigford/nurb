import { it, expect, vi, afterEach } from "vitest"
import { render, screen, fireEvent, cleanup } from "@testing-library/react"

afterEach(cleanup)
import UpdateCard from "./UpdateCard"

it("offers Later and Restart now, and calls each", () => {
  const onLater = vi.fn()
  const onInstall = vi.fn()
  render(<UpdateCard version="1.1.0" onLater={onLater} onInstall={onInstall} />)
  expect(screen.getByText("nurb 1.1.0 is ready")).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "Later" }))
  fireEvent.click(screen.getByRole("button", { name: "Restart now" }))
  expect(onLater).toHaveBeenCalledTimes(1)
  expect(onInstall).toHaveBeenCalledTimes(1)
})

it("drops Later and disables the button while installing", () => {
  render(<UpdateCard version="1.1.0" installing onLater={() => {}} onInstall={() => {}} />)
  expect(screen.queryByRole("button", { name: "Later" })).toBeNull()
  const restart = screen.getByRole("button", { name: "Restarting…" }) as HTMLButtonElement
  expect(restart.disabled).toBe(true)
  expect(screen.getByText("Closing and reopening nurb.")).toBeTruthy()
})
