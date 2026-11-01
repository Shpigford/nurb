import { describe, it, expect } from "vitest"
import { render } from "@testing-library/react"
import AssistantMarkdown from "./AssistantMarkdown"

describe("AssistantMarkdown", () => {
  it("never emits remote image resources", () => {
    const { container } = render(
      <AssistantMarkdown content={"**Safe text**\n\n![tracker](https://tracker.test/pixel.gif)\n\n1. List still renders"} />
    )
    const html = container.innerHTML

    expect(html).not.toMatch(/<img|preload|tracker\.test/)
    expect(html).toMatch(/<strong[^>]*>Safe text<\/strong>/)
    expect(html).toMatch(/<ol/)
  })

  // react-markdown puts the fence's language on the code element; the package
  // styling has to merge with it rather than replace it.
  it("keeps both the package class and react-markdown's language class", () => {
    const { container } = render(<AssistantMarkdown content={"```js\nconst a = 1\n```"} />)
    const code = container.querySelector("code")

    expect(code).not.toBeNull()
    expect(code).toHaveClass("bg-raised")
    expect(code).toHaveClass("language-js")
  })

  it("marks the streaming variant so the caret can ride the last node", () => {
    const { container } = render(<AssistantMarkdown content="Thinking" streaming />)
    expect(container.firstElementChild).toHaveClass("md-streaming")
  })
})
