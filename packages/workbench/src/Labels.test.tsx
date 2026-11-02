import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { LabelEditor, LabelTag } from "./Labels"

describe("LabelEditor", () => {
  it("names a new spot with what was typed, trimmed", async () => {
    const onSave = vi.fn(async () => {})
    render(<LabelEditor onSave={onSave} onCancel={() => {}} />)
    expect(screen.queryByRole("button", { name: "Remove" })).toBeNull()
    expect(screen.getByRole("button", { name: "Save label" })).toBeDisabled()
    await userEvent.type(screen.getByLabelText("Name this spot"), "  Hook tip {Enter}")
    expect(onSave).toHaveBeenCalledWith("Hook tip")
  })

  it("keeps a refusal on screen instead of closing", async () => {
    const onSave = vi.fn(async () => {
      throw new Error("this part already has a label called Lip")
    })
    render(<LabelEditor was="Hook" onSave={onSave} onRemove={async () => {}} onMove={() => {}} onCancel={() => {}} />)
    const field = screen.getByLabelText("Rename this spot")
    await userEvent.clear(field)
    await userEvent.type(field, "Lip{Enter}")
    await waitFor(() => expect(screen.getByText("this part already has a label called Lip")).toBeInTheDocument())
    expect(screen.getByRole("button", { name: "Remove" })).toBeEnabled()
  })
})

describe("LabelTag", () => {
  it("says when the part moved away from the spot", () => {
    render(
      <LabelTag
        label={{ name: "Lip", point: [0, 0, 0], normal: [0, 0, 1], facing: "up", off_mm: 3, on_part: false }}
        onOpen={() => {}}
      />
    )
    expect(screen.getByRole("button")).toHaveTextContent("Lip· not on the part")
  })
})
