import { useEffect, useState } from "react"
import { fireEvent, render, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import type { Finding } from "@nurb/ui"
import PartView, { conversationHidden } from "./PartView"
import { part, project } from "./fixtures"

// The viewer reports what it was handed, so a test can read what is drawn on the part.
vi.mock("@nurb/ui", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@nurb/ui")>()
  return {
    ...actual,
    ViewerIsland: ({
      onPick,
      anchors,
      findings,
      highlight,
    }: {
      onPick?: ((spot: unknown) => void) | null
      anchors?: unknown[]
      findings?: Finding[]
      highlight?: number | null
    }) => (
      <div data-testid="viewer" data-anchors={anchors?.length ?? 0} data-findings={findings?.length ?? 0} data-highlight={highlight ?? ""}>
        <button onClick={() => onPick?.({ point: [1, 2, 3], normal: [0, 0, 1] })}>Pick a spot</button>
      </div>
    ),
  }
})

const findings: Finding[] = [
  { rule: "overhang", severity: "warn", message: "Overhang", where: [0, 0, 0] },
  { rule: "wall", severity: "fail", message: "Thin wall", where: [1, 0, 0] },
]
const bracketPart = {
  ...part("bracket", "/glb/p1/bracket.glb"),
  labels: [{ name: "hook", point: [0, 0, 5] as [number, number, number], normal: [0, 0, 1] as [number, number, number], facing: "top" }],
}
bracketPart.build = { ...bracketPart.build!, findings, passed: false }
const bracket = project("p1", "Bracket", [bracketPart], [])

// The menu stays open after a pick, so only open it when it is closed.
function toggle(name: string) {
  if (!screen.queryByRole("menu")) fireEvent.click(screen.getByRole("button", { name: "View" }))
  fireEvent.click(screen.getByRole("menuitemcheckbox", { name }))
}

function item(name: string) {
  if (!screen.queryByRole("menu")) fireEvent.click(screen.getByRole("button", { name: "View" }))
  return screen.getByRole("menuitemcheckbox", { name })
}

const viewer = () => screen.getByTestId("viewer")

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

describe("the View menu", () => {
  it("hides and restores the conversation without unmounting it", () => {
    const stopped = vi.fn()
    function Conversation() {
      useEffect(() => stopped, [])
      return <input aria-label="Draft" defaultValue="" />
    }
    render(<PartView project={bracket} partName="bracket" chat={<Conversation />} />)
    const draft = screen.getByRole("textbox", { name: "Draft" })
    fireEvent.change(draft, { target: { value: "Make the arm shorter" } })

    expect(item("Conversation")).toHaveAttribute("aria-checked", "true")
    toggle("Conversation")
    expect(item("Conversation")).toHaveAttribute("aria-checked", "false")
    expect(draft).not.toBeVisible()
    expect(stopped).not.toHaveBeenCalled()

    toggle("Conversation")
    expect(screen.getByRole("textbox", { name: "Draft" })).toBe(draft)
    expect(draft).toBeVisible()
    expect(draft).toHaveValue("Make the arm shorter")
  })

  it("hides spot labels and check markers on the part", () => {
    render(<PartView project={bracket} partName="bracket" />)
    expect(viewer()).toHaveAttribute("data-anchors", "1")
    expect(viewer()).toHaveAttribute("data-findings", "2")

    toggle("Spot labels")
    toggle("Check markers")
    expect(viewer()).toHaveAttribute("data-anchors", "0")
    expect(viewer()).toHaveAttribute("data-findings", "0")

    toggle("Spot labels")
    toggle("Check markers")
    expect(viewer()).toHaveAttribute("data-anchors", "1")
    expect(viewer()).toHaveAttribute("data-findings", "2")
  })

  it("shows labels again when the person starts labelling a spot", () => {
    render(<PartView project={bracket} partName="bracket" />)
    toggle("Spot labels")
    fireEvent.keyDown(document, { key: "Escape" })
    fireEvent.click(screen.getByRole("button", { name: "Label a spot" }))
    expect(viewer()).toHaveAttribute("data-anchors", "1")
  })

  it("remembers each choice when the workspace is reopened", () => {
    const view = () => <PartView project={bracket} partName="bracket" chat={<p>Conversation text</p>} />
    const first = render(view())
    toggle("Conversation")
    toggle("Check markers")
    first.unmount()

    render(view())
    expect(screen.getByText("Conversation text")).not.toBeVisible()
    expect(viewer()).toHaveAttribute("data-findings", "0")
    expect(viewer()).toHaveAttribute("data-anchors", "1")
  })

  it("still toggles when storage is unavailable", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => {
        throw new Error("Storage blocked")
      },
      setItem: () => {
        throw new Error("Storage blocked")
      },
    })
    render(<PartView project={bracket} partName="bracket" chat={<p>Conversation text</p>} />)
    toggle("Conversation")
    expect(screen.getByText("Conversation text")).not.toBeVisible()
    toggle("Conversation")
    expect(screen.getByText("Conversation text")).toBeVisible()
  })

  it("lets the host reveal a prepared prompt and keeps the menu in sync", () => {
    localStorage.setItem("nurb.conversation-hidden", "true")
    function Host() {
      const [hidden, setHidden] = useState(conversationHidden)
      return (
        <>
          <button onClick={() => setHidden(false)}>Ask the agent</button>
          <PartView
            project={bracket}
            partName="bracket"
            chatHidden={hidden}
            onChatHiddenChange={setHidden}
            chat={<p>Prepared prompt</p>}
          />
        </>
      )
    }
    render(<Host />)
    expect(screen.getByText("Prepared prompt")).not.toBeVisible()
    fireEvent.click(screen.getByRole("button", { name: "Ask the agent" }))
    expect(screen.getByText("Prepared prompt")).toBeVisible()
    expect(localStorage.getItem("nurb.conversation-hidden")).toBe("false")
    expect(item("Conversation")).toHaveAttribute("aria-checked", "true")
  })

  it("reveals the conversation when a picked spot is sent to the composer", () => {
    localStorage.setItem("nurb.conversation-hidden", "true")
    const onPointAt = vi.fn()
    render(<PartView project={bracket} partName="bracket" chat={<p>Conversation text</p>} onPointAt={onPointAt} />)
    fireEvent.click(screen.getByRole("button", { name: "Point at the part" }))
    fireEvent.click(screen.getByRole("button", { name: "Pick a spot" }))
    expect(onPointAt).toHaveBeenCalledOnce()
    expect(screen.getByText("Conversation text")).toBeVisible()
  })

  it("does not offer the conversation when there is none", () => {
    render(<PartView project={bracket} partName="bracket" />)
    item("Spot labels")
    expect(screen.queryByRole("menuitemcheckbox", { name: "Conversation" })).not.toBeInTheDocument()
  })
})

describe("the stage keys", () => {
  const press = (key: string, init: KeyboardEventInit = {}) => fireEvent.keyDown(window, { key, ...init })

  it("starts and stops labelling with L and Escape", () => {
    render(<PartView project={bracket} partName="bracket" />)
    press("l")
    expect(screen.getByRole("button", { name: "Click a spot to name it" })).toBeInTheDocument()
    press("Escape")
    expect(screen.getByRole("button", { name: "Label a spot" })).toBeInTheDocument()
  })

  it("points at the part with P when the host can take the question", () => {
    render(<PartView project={bracket} partName="bracket" onPointAt={() => {}} />)
    press("p")
    expect(screen.getByRole("button", { name: "Click a spot on the part" })).toBeInTheDocument()
    press("p")
    expect(screen.getByRole("button", { name: "Point at the part" })).toBeInTheDocument()
  })

  it("hides the conversation with Cmd+Backslash", () => {
    render(<PartView project={bracket} partName="bracket" chat={<p>Conversation text</p>} />)
    press("\\", { metaKey: true })
    expect(screen.getByText("Conversation text")).not.toBeVisible()
    press("\\", { ctrlKey: true })
    expect(screen.getByText("Conversation text")).toBeVisible()
  })

  it("leaves keys typed in a field, with a modifier, or on a hidden stage alone", () => {
    const { container } = render(
      <div>
        <input aria-label="Draft" />
        <PartView project={bracket} partName="bracket" />
      </div>,
    )
    fireEvent.keyDown(screen.getByRole("textbox", { name: "Draft" }), { key: "l" })
    press("l", { metaKey: true })
    expect(screen.getByRole("button", { name: "Label a spot" })).toBeInTheDocument()

    container.firstElementChild!.setAttribute("hidden", "")
    press("l")
    expect(screen.getByRole("button", { name: "Label a spot", hidden: true })).toBeInTheDocument()
  })
})
