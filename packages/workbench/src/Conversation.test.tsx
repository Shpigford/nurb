import { useEffect } from "react"
import { fireEvent, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import PartView from "./PartView"
import { part, project } from "./fixtures"

vi.mock("@nurb/ui", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@nurb/ui")>()
  return {
    ...actual,
    ViewerIsland: ({ onPick }: { onPick?: (spot: unknown) => void }) => (
      <button onClick={() => onPick?.({ point: [1, 2, 3], normal: [0, 0, 1] })}>Pick a spot</button>
    ),
  }
})

const bracket = project("p1", "Bracket", [part("bracket", "/glb/p1/bracket.glb")], [])

beforeEach(() => {
  const values = new Map<string, string>()
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
  })
})
afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe("conversation visibility", () => {
  it("hides and restores the panel from the header with the keyboard", async () => {
    render(<PartView project={bracket} partName="bracket" chat={<p>Conversation text</p>} />)
    const button = screen.getByRole("button", { name: "Hide conversation" })
    const panel = document.getElementById(button.getAttribute("aria-controls")!)!
    expect(button).toHaveAttribute("aria-expanded", "true")
    expect(panel).toBeVisible()

    button.focus()
    await userEvent.keyboard("{Enter}")
    expect(screen.getByRole("button", { name: "Show conversation" })).toHaveFocus()
    expect(button).toHaveAttribute("aria-expanded", "false")
    expect(panel).not.toBeVisible()

    await userEvent.keyboard(" ")
    expect(screen.getByRole("button", { name: "Hide conversation" })).toHaveAttribute("aria-expanded", "true")
    expect(panel).toBeVisible()
  })

  it("keeps the conversation and draft mounted, and tells the host when it is hidden", () => {
    const stopped = vi.fn()
    function Conversation({ hidden }: { hidden: boolean }) {
      useEffect(() => stopped, [])
      return <input aria-label="Draft" data-hidden={hidden} defaultValue="" />
    }
    render(
      <PartView project={bracket} partName="bracket" chat={(hidden) => <Conversation hidden={hidden} />} />
    )
    const draft = screen.getByRole("textbox", { name: "Draft" })
    fireEvent.change(draft, { target: { value: "Make the arm shorter" } })
    fireEvent.click(screen.getByRole("button", { name: "Hide conversation" }))
    expect(draft).toHaveAttribute("data-hidden", "true")
    expect(draft).toBeInTheDocument()
    expect(stopped).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole("button", { name: "Show conversation" }))
    expect(screen.getByRole("textbox", { name: "Draft" })).toBe(draft)
    expect(draft).toHaveValue("Make the arm shorter")
    expect(draft).toHaveAttribute("data-hidden", "false")
    expect(stopped).not.toHaveBeenCalled()
  })

  it("remembers the choice when the workspace is reopened", () => {
    const view = () => <PartView project={bracket} partName="bracket" chat={<p>Conversation text</p>} />
    const first = render(view())
    fireEvent.click(screen.getByRole("button", { name: "Hide conversation" }))
    first.unmount()

    const second = render(view())
    expect(screen.getByRole("button", { name: "Show conversation" })).toHaveAttribute("aria-expanded", "false")
    expect(screen.getByText("Conversation text")).not.toBeVisible()
    fireEvent.click(screen.getByRole("button", { name: "Show conversation" }))
    second.unmount()

    render(view())
    expect(screen.getByRole("button", { name: "Hide conversation" })).toHaveAttribute("aria-expanded", "true")
  })

  it("still toggles when storage is unavailable", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => { throw new Error("Storage blocked") },
      setItem: () => { throw new Error("Storage blocked") },
    })
    render(<PartView project={bracket} partName="bracket" chat={<p>Conversation text</p>} />)
    fireEvent.click(screen.getByRole("button", { name: "Hide conversation" }))
    expect(screen.getByText("Conversation text")).not.toBeVisible()
    fireEvent.click(screen.getByRole("button", { name: "Show conversation" }))
    expect(screen.getByText("Conversation text")).toBeVisible()
  })

  it("reveals the conversation when a picked spot is sent to the composer", () => {
    localStorage.setItem("nurb.conversation-hidden", "true")
    const onPointAt = vi.fn()
    render(
      <PartView project={bracket} partName="bracket" chat={<p>Conversation text</p>} onPointAt={onPointAt} />
    )
    fireEvent.click(screen.getByRole("button", { name: "Point at the part" }))
    fireEvent.click(screen.getByRole("button", { name: "Pick a spot" }))
    expect(onPointAt).toHaveBeenCalledOnce()
    expect(screen.getByText("Conversation text")).toBeVisible()
    expect(screen.getByRole("button", { name: "Hide conversation" })).toHaveAttribute("aria-expanded", "true")
  })

  it("does not offer the control when there is no conversation", () => {
    render(<PartView project={bracket} partName="bracket" />)
    expect(screen.queryByRole("button", { name: /conversation/i })).not.toBeInTheDocument()
  })
})
