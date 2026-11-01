import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import ConfirmDialog from "./ConfirmDialog"

// jsdom has no top layer, so showModal is a stub. It still has to set `open`,
// or the dialog's contents stay out of the accessibility tree.
HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
  this.open = true
}

afterEach(cleanup)

describe("ConfirmDialog", () => {
  it("names the thing and confirms it", () => {
    const seen: string[] = []
    render(
      <ConfirmDialog title="Delete bracket?" onConfirm={() => seen.push("yes")} onCancel={() => seen.push("no")}>
        No undo.
      </ConfirmDialog>
    )
    expect(screen.getByText("Delete bracket?")).toBeTruthy()
    fireEvent.click(screen.getByRole("button", { name: "Delete" }))
    expect(seen).toEqual(["yes"])
  })

  it("cancels", () => {
    const seen: string[] = []
    render(
      <ConfirmDialog title="Delete bracket?" confirmLabel="Remove" onConfirm={() => {}} onCancel={() => seen.push("no")}>
        No undo.
      </ConfirmDialog>
    )
    expect(screen.getByRole("button", { name: "Remove" })).toBeTruthy()
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }))
    expect(seen).toEqual(["no"])
  })

  it("puts a hold in front of the confirm when there is no undo", () => {
    const seen: string[] = []
    render(
      <ConfirmDialog title="Delete bracket?" hold onConfirm={() => seen.push("yes")} onCancel={() => {}}>
        No undo.
      </ConfirmDialog>
    )
    const confirm = screen.getByRole("button", { name: "Delete" })
    fireEvent.click(confirm)
    expect(seen).toEqual([])
    expect(screen.getByText(/Press and hold/)).toBeTruthy()
  })
})
