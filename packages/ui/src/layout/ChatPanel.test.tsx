import { describe, it, expect, afterEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import ChatPanel from "./ChatPanel"

afterEach(cleanup)

describe("ChatPanel", () => {
  it("is 372 wide, with the strip, a scrolling transcript and a pinned composer", () => {
    const { container } = render(
      <ChatPanel strip={{ label: "Conversation", trailing: "4 turns · rev 04" }} composer={<div>COMPOSER</div>}>
        <div>TRANSCRIPT</div>
      </ChatPanel>
    )
    const panel = container.querySelector("section") as HTMLElement
    expect(panel.className).toContain("w-[372px]")
    expect(panel.className).toContain("panel")
    expect(screen.getByText("Conversation")).toBeTruthy()
    expect(screen.getByText("4 turns · rev 04")).toBeTruthy()
    expect(screen.getByText("TRANSCRIPT").parentElement?.className).toContain("overflow-y-auto")
    expect(screen.getByText("COMPOSER").parentElement?.className).toContain("pt-0")
  })

  it("renders the picker in the strip's trailing area", () => {
    render(
      <ChatPanel strip={{ label: "Conversation" }} picker={<button type="button">PICKER</button>} composer={null}>
        {null}
      </ChatPanel>
    )
    expect(screen.getByText("PICKER")).toBeTruthy()
  })

  it("stays mounted when hidden, so a background conversation keeps running", () => {
    const { container } = render(
      <ChatPanel hidden strip={{ label: "Conversation" }} composer={null}>
        <div>TRANSCRIPT</div>
      </ChatPanel>
    )
    expect((container.querySelector("section") as HTMLElement).hidden).toBe(true)
    expect(screen.getByText("TRANSCRIPT", { ignore: "" })).toBeTruthy()
  })

  it("marks the strip as the window drag region when asked", () => {
    const { container } = render(
      <ChatPanel dragRegion strip={{ label: "Conversation" }} composer={null}>
        {null}
      </ChatPanel>
    )
    expect(container.querySelector("[data-tauri-drag-region]")).toBeTruthy()
  })
})
