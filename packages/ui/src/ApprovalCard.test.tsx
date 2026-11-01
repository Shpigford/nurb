import { describe, it, expect, afterEach } from "vitest"
import { useState } from "react"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import ApprovalCard, { type ApprovalQuestion } from "./ApprovalCard"

afterEach(cleanup)

const ask = (id: string, title: string): ApprovalQuestion => ({
  id,
  title,
  actions: [
    { id: "allow", label: "allow", variant: "accent" },
    { id: "deny", label: "not now", variant: "ghost" },
  ],
})

/** The owner drops an answered question, which is what advances the card. */
function Queue() {
  const [questions, setQuestions] = useState([ask("a", "Claude wants to build the part"), ask("b", "Claude wants to export print files")])
  return (
    <ApprovalCard
      questions={questions}
      onAnswer={(id) => setQuestions((list) => list.filter((q) => q.id !== id))}
    />
  )
}

describe("ApprovalCard", () => {
  it("shows one question at a time and advances the counter", async () => {
    render(<Queue />)
    expect(screen.getByText("Question 1 of 2")).toBeInTheDocument()
    expect(screen.getByText("Claude wants to build the part")).toBeInTheDocument()
    expect(screen.queryByText("Claude wants to export print files")).toBeNull()

    fireEvent.click(screen.getByRole("button", { name: "allow" }))

    expect(screen.getByText("Question 2 of 2")).toBeInTheDocument()
    expect(screen.getByText("Claude wants to export print files")).toBeInTheDocument()
    // The answered question leaves on its exit animation, so it is gone a beat later.
    await waitFor(() => expect(screen.queryByText("Claude wants to build the part")).toBeNull())
  })

  it("counts a later batch from one again", () => {
    const { rerender } = render(<ApprovalCard questions={[ask("a", "one"), ask("b", "two")]} onAnswer={() => {}} />)
    expect(screen.getByText("Question 1 of 2")).toBeInTheDocument()
    rerender(<ApprovalCard questions={[]} onAnswer={() => {}} />)
    rerender(<ApprovalCard questions={[ask("c", "three"), ask("d", "four")]} onAnswer={() => {}} />)
    expect(screen.getByText("Question 1 of 2")).toBeInTheDocument()
  })

  it("hides the counter for a single question and renders nothing when the queue drains", () => {
    const { rerender } = render(<ApprovalCard questions={[ask("a", "Claude wants to build the part")]} onAnswer={() => {}} />)
    expect(screen.queryByText(/Question/)).toBeNull()
    rerender(<ApprovalCard questions={[]} onAnswer={() => {}} />)
    expect(screen.queryByText("Claude wants to build the part")).toBeNull()
  })
})
