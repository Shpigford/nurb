import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import BuildCard from "./BuildCard"
import type { BuildEvent, ToolStep } from "./types"

afterEach(cleanup)

function step(id: string, over: Partial<ToolStep> = {}): ToolStep {
  return {
    id,
    verb: "build",
    object: `${id}.py`,
    status: "done",
    started_at: "2026-09-14T10:00:00.000Z",
    elapsed_s: 2.1,
    ...over,
  }
}

const passed: BuildEvent = {
  id: "b1",
  part_name: "bracket",
  status: "passed",
  started_at: "2026-09-14T10:00:00.000Z",
  elapsed_s: 321,
  revision: 24,
  steps: [step("a"), step("b"), step("c")],
  findings: [{ rule: "thin_wall", label: "THIN WALL", severity: "warn", message: "0.9 mm at the hook" }],
}

describe("BuildCard", () => {
  it("shows the render once the build has one", () => {
    render(<BuildCard build={{ ...passed, render_url: "/render/p/bracket.png?run=r1" }} />)
    const picture = screen.getByRole("img", { name: /bracket from four sides/i })
    expect(picture).toHaveAttribute("src", "/render/p/bracket.png?run=r1")
  })

  it("holds the picture back while the build runs", () => {
    render(<BuildCard build={{ ...passed, status: "running", render_url: "/render/p/bracket.png?run=r1" }} />)
    expect(screen.queryByRole("img")).toBeNull()
  })

  it("collapses the steps of a passed build behind one line", () => {
    const { container } = render(<BuildCard build={passed} />)
    expect(screen.getByText("Built")).toBeInTheDocument()
    expect(screen.getByText(/REV 24/)).toBeInTheDocument()
    const summary = screen.getByRole("button", { name: /3 steps/i })
    expect(screen.getAllByRole("button")).toHaveLength(1)
    fireEvent.click(summary)
    expect(screen.getAllByRole("button")).toHaveLength(4)
    expect(container.querySelector('[class*="animate-"]')).toBeNull()
  })

  it("stays expanded on a failure and names the count", () => {
    const failed: BuildEvent = {
      ...passed,
      status: "failed",
      steps: [step("a"), step("b", { status: "failed", output: "boom" })],
      findings: [
        { rule: "overhang", label: "OVERHANG", severity: "fail", message: "62 degrees on the shelf" },
        { rule: "sliver", label: "SLIVER", severity: "fail", message: "0.2 mm face" },
      ],
    }
    const { container } = render(<BuildCard build={failed} />)
    expect(screen.getByText("Failed")).toBeInTheDocument()
    expect(screen.getByText(/2 checks failed/i)).toBeInTheDocument()
    expect(screen.getByText("OVERHANG")).toBeInTheDocument()
    expect(screen.getAllByRole("button")).toHaveLength(2)
    expect(container.querySelector('[class*="animate-"]')).toBeNull()
  })

  it("honors collapsed={false} on a passed build", () => {
    render(<BuildCard build={passed} collapsed={false} />)
    expect(screen.getAllByRole("button")).toHaveLength(4)
  })

  it("shows the last line of the traceback on an engine error", () => {
    const error = "Traceback (most recent call last):\n  File \"parts/shelf.py\", line 4\nTypeError: bad wall\n"
    const errored: BuildEvent = { ...passed, status: "error", steps: [], findings: [], error }
    render(<BuildCard build={errored} />)
    expect(screen.getByText("TypeError: bad wall")).toBeInTheDocument()
  })
})
