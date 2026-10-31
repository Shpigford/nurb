import { describe, it, expect, afterEach } from "vitest"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import BlurUpImage from "./BlurUpImage"

afterEach(cleanup)

const shot = { src: "https://example.test/shelf.png", alt: "The shelf on the bed", width: 1200, height: 800 }

describe("BlurUpImage", () => {
  it("holds the alt text and the box before the bytes arrive", () => {
    const { container } = render(<BlurUpImage {...shot} />)
    const img = screen.getByAltText("The shelf on the bed") as HTMLImageElement
    expect(img.getAttribute("src")).toBe(shot.src)
    const frame = container.firstElementChild as HTMLElement
    expect(frame.getAttribute("aria-busy")).toBe("true")
    expect(frame.style.aspectRatio).toBe("1200 / 800")
    expect(frame.style.backgroundColor).toBe("var(--color-accent-wash)")
  })

  it("resolves when the image loads", () => {
    let ready = 0
    const { container } = render(<BlurUpImage {...shot} onReady={() => (ready += 1)} />)
    fireEvent.load(screen.getByAltText("The shelf on the bed"))
    expect(ready).toBe(1)
    expect((container.firstElementChild as HTMLElement).dataset.status).toBe("ready")
  })

  it("degrades to a drawn state on a dead URL", () => {
    const { container } = render(<BlurUpImage {...shot} />)
    fireEvent.error(screen.getByAltText("The shelf on the bed"))
    const frame = container.firstElementChild as HTMLElement
    expect(frame.dataset.status).toBe("error")
    expect(frame.getAttribute("aria-busy")).toBe("false")
  })
})
