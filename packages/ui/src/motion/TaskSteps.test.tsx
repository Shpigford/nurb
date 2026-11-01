import { describe, it, expect, afterEach } from "vitest"
import { cleanup, render, screen } from "@testing-library/react"
import TaskSteps, { useTaskSteps, type TaskStep } from "./TaskSteps"

afterEach(cleanup)

const STEPS: TaskStep[] = [
  { id: "load", label: "Loading part" },
  { id: "build", label: "Building", meta: "0.6s" },
  { id: "mesh", label: "Tessellating" },
]

describe("TaskSteps", () => {
  it("mounts the whole plan and marks the running step", () => {
    const { container } = render(<TaskSteps steps={STEPS} current={1} />)
    expect(screen.getByText("Tessellating")).toBeTruthy()
    const rows = container.querySelectorAll("li")
    expect([...rows].map((row) => row.dataset.status)).toEqual(["done", "active", "pending"])
    expect(rows[1].getAttribute("aria-current")).toBe("step")
  })

  it("draws a check as each step completes", () => {
    const { container, rerender } = render(<TaskSteps steps={STEPS} current={1} />)
    expect(container.querySelectorAll("polyline")).toHaveLength(1)
    rerender(<TaskSteps steps={STEPS} current={3} />)
    expect(container.querySelectorAll("polyline")).toHaveLength(3)
    expect(container.querySelector("li[data-status='active']")).toBeNull()
  })

  it("stops at the failure and leaves the rest unrun", () => {
    const { rows, sentence } = useTaskSteps({ steps: STEPS, current: 1, failed: true })
    expect(rows.map((row) => row.status)).toEqual(["done", "failed", "pending"])
    expect(sentence).toBe("Failed at Building")
    render(<TaskSteps steps={STEPS} current={1} failed />)
    expect(screen.getByText("Run failed")).toBeTruthy()
  })
})
