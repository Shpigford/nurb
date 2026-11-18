import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"
import { ShareMenu } from "./Share"

const share = { url: "https://nurb.app/s/SckGVebnAF", shared_at: "2026-11-17T00:00:00Z", current: true }

function answering(body: unknown, status = 200) {
  const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status }))
  vi.stubGlobal("fetch", fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe("ShareMenu", () => {
  it("makes a link at the values on the sliders", async () => {
    const fetchMock = answering({ share })
    render(<ShareMenu partId="p1" share={null} values={{ width: 30 }} />)
    await userEvent.click(screen.getByRole("button", { name: "Share" }))
    await userEvent.click(screen.getByRole("button", { name: "Create link" }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toMatch(/\/api\/parts\/p1\/share$/)
    expect(JSON.parse(String(init.body))).toEqual({ values: { width: 30 } })
  })

  it("copies the link through the host when it has one", async () => {
    const copy = vi.fn(async () => {})
    render(<ShareMenu partId="p1" share={share} values={{}} onCopy={copy} />)
    await userEvent.click(screen.getByRole("button", { name: "Shared" }))
    expect(screen.getByRole("textbox", { name: "Link to this part" })).toHaveProperty("value", share.url)
    await userEvent.click(screen.getByRole("button", { name: "Copy link" }))
    expect(copy).toHaveBeenCalledWith(share.url)
    expect(await screen.findByRole("button", { name: "Copied" })).toBeTruthy()
  })

  it("offers to bring a link up to date once the part has moved on", async () => {
    answering({ share })
    render(<ShareMenu partId="p1" share={{ ...share, current: false }} values={{}} />)
    await userEvent.click(screen.getByRole("button", { name: "Shared" }))
    expect(screen.getByText("Changed since you shared it.")).toBeTruthy()
    expect(screen.getByRole("button", { name: "Update link" })).toBeTruthy()
  })

  it("asks before taking the link down, and says why it could not", async () => {
    const fetchMock = answering({ error: "could not reach nurb.app. Check the internet connection and try again." }, 502)
    render(<ShareMenu partId="p1" share={share} values={{}} />)
    await userEvent.click(screen.getByRole("button", { name: "Shared" }))
    await userEvent.click(screen.getByRole("button", { name: "Stop sharing" }))
    expect(fetchMock).not.toHaveBeenCalled()
    expect(screen.getByText("Turn the link off?")).toBeTruthy()
    await userEvent.click(screen.getByRole("button", { name: "Stop sharing" }))
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(init.method).toBe("DELETE")
    expect(await screen.findByText(/could not reach nurb.app/)).toBeTruthy()
  })
})
