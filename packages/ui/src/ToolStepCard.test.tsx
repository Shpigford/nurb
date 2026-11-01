import { describe, it, expect, vi, afterEach } from "vitest"
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"
import { ToolStepCard, ToolStepGroup } from "./ToolStepCard"
import type { ToolStep } from "./types"

afterEach(cleanup)

function step(over: Partial<ToolStep> = {}): ToolStep {
  return {
    id: over.id ?? "s1",
    verb: "build",
    object: "bracket.py",
    status: "done",
    started_at: "2026-09-14T10:00:00.000Z",
    elapsed_s: 4.2,
    ...over,
  }
}

describe("ToolStepCard", () => {
  it("renders the verb, the object and the elapsed", () => {
    render(<ToolStepCard step={step()} />)
    expect(screen.getByText("BUILD")).toBeInTheDocument()
    expect(screen.getByText("bracket.py")).toBeInTheDocument()
    expect(screen.getByText("4.2s")).toBeInTheDocument()
  })

  it("puts the elapsed in tabular figures and never animates", () => {
    const { container } = render(<ToolStepCard step={step()} />)
    expect(screen.getByText("4.2s").className).toContain("tabular-nums")
    expect(container.querySelector('[class*="animate-"]')).toBeNull()
  })

  it("counts a running step up", () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date("2026-09-14T10:00:00.000Z"))
    const running = step({ status: "running", elapsed_s: undefined })
    const { container } = render(<ToolStepCard step={running} />)
    expect(screen.getByText("0.0s")).toBeInTheDocument()
    act(() => vi.advanceTimersByTime(1500))
    expect(screen.getByText("1.5s")).toBeInTheDocument()
    expect(container.querySelector('[class*="animate-"]')).toBeNull()
    vi.useRealTimers()
  })

  it("toggles the input and output blocks", () => {
    render(<ToolStepCard step={step({ input: { part: "bracket" }, output: "ok\n2 faces" })} />)
    const button = screen.getByRole("button")
    expect(button).toHaveAttribute("aria-expanded", "false")
    expect(screen.queryByText("INPUT")).toBeNull()
    fireEvent.click(button)
    expect(button).toHaveAttribute("aria-expanded", "true")
    expect(screen.getByText("INPUT")).toBeInTheDocument()
    expect(screen.getByText("OUTPUT")).toBeInTheDocument()
    expect(document.querySelectorAll("pre")).toHaveLength(2)
  })

  it("starts a failed step open", () => {
    render(<ToolStepCard step={step({ status: "failed", output: "BRep_API: command not done" })} />)
    expect(screen.getByRole("button")).toHaveAttribute("aria-expanded", "true")
    expect(screen.getByText("OUTPUT")).toBeInTheDocument()
  })

  it("opens when a mounted running step fails", () => {
    const { rerender } = render(<ToolStepCard step={step({ status: "running", elapsed_s: undefined })} />)
    rerender(<ToolStepCard step={step({ status: "failed", elapsed_s: 2.5, output: "BRep_API: command not done" })} />)
    expect(screen.getByRole("button")).toHaveAttribute("aria-expanded", "true")
    expect(screen.getByText("OUTPUT")).toBeInTheDocument()
  })

  it("reads 0.0s for a landed step with no recorded time", () => {
    const started = new Date(Date.now() - 86_400_000).toISOString()
    render(<ToolStepCard step={step({ status: "done", elapsed_s: undefined, started_at: started })} />)
    expect(screen.getByText("0.0s")).toBeInTheDocument()
  })
})

describe("ToolStepGroup", () => {
  const done = (n: number) => Array.from({ length: n }, (_, i) => step({ id: `s${i}`, object: `part-${i}.py` }))

  it("collapses three consecutive done steps into one summary", () => {
    render(<ToolStepGroup steps={done(3)} />)
    const summary = screen.getByRole("button", { name: /3 steps/i })
    expect(screen.getAllByRole("button")).toHaveLength(1)
    fireEvent.click(summary)
    expect(screen.getAllByRole("button")).toHaveLength(4)
  })

  it("leaves two steps as two rows", () => {
    render(<ToolStepGroup steps={done(2)} />)
    expect(screen.queryByRole("button", { name: /2 steps/i })).toBeNull()
    expect(screen.getAllByRole("button")).toHaveLength(2)
  })

  it("splits a group around a failed step, which stands alone open", () => {
    const steps = done(5)
    steps[2] = step({ id: "s2", object: "part-2.py", status: "failed", output: "boom" })
    render(<ToolStepGroup steps={steps} />)
    expect(screen.queryByRole("button", { name: /steps/i })).toBeNull()
    expect(screen.getAllByRole("button")).toHaveLength(5)
    expect(screen.getByRole("button", { name: /part-2\.py/i })).toHaveAttribute("aria-expanded", "true")
  })

  it("never groups a running step at the end", () => {
    const steps = [...done(3), step({ id: "live", object: "checking", status: "running", elapsed_s: undefined })]
    render(<ToolStepGroup steps={steps} />)
    expect(screen.getByRole("button", { name: /3 steps/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /checking/i })).toBeInTheDocument()
    expect(screen.getAllByRole("button")).toHaveLength(2)
  })
})
