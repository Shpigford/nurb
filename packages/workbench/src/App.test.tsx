import { render, screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import App from "./App"
import { messages, part, project, summaries } from "./fixtures"
import { FakeSocket, installSocket } from "./socket-stub"

// The real island needs WebGL; the stage's data attribute is what the tests read.
vi.mock("@nurb/ui", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@nurb/ui")>()
  return { ...actual, ViewerIsland: () => <div data-testid="viewer" /> }
})

let glb = "/glb/p2/lid.glb?run=1"
let listed = summaries

function stubFetch() {
  vi.stubGlobal("fetch", async (url: string) => {
    if (url === "/api/projects") return new Response(JSON.stringify({ projects: listed }))
    if (url === "/api/projects/p2") {
      return new Response(JSON.stringify(project("p2", "Second", [part("body", "/glb/p2/body.glb?run=1"), part("lid", glb)], messages)))
    }
    return new Response("{}", { status: 404 })
  })
}

beforeEach(() => {
  glb = "/glb/p2/lid.glb?run=1"
  listed = summaries
  installSocket()
  stubFetch()
  history.replaceState(null, "", "/?project=p2&part=lid")
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("workbench", () => {
  it("selects the project and part named in the query string", async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByLabelText("Project")).toHaveValue("p2"))
    // Parts are the floating header's tabs now, not a list of buttons in a panel.
    const lid = await screen.findByRole("tab", { name: "lid" })
    expect(lid).toHaveAttribute("aria-selected", "true")
    expect(screen.getByTestId("stage")).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=1")
  })

  it("refetches on a build event and hands the viewer the new url", async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByTestId("stage")).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=1"))

    glb = "/glb/p2/lid.glb?run=2"
    FakeSocket.instances[0].emit({ kind: "build", id: "b2", project_id: "p2" })
    await waitFor(() => expect(screen.getByTestId("stage")).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=2"))
  })

  it("renders every payload kind in the transcript", async () => {
    render(<App />)
    expect(await screen.findByText("Built the bracket.")).toBeInTheDocument()
    // build, spec, measurement, step: one recognizable line each.
    expect(screen.getAllByText(/bracket/i).length).toBeGreaterThan(1)
    expect(screen.getByText("A bracket")).toBeInTheDocument()
    expect(screen.getAllByText(/rail_width/).length).toBeGreaterThan(0)
  })

  // A delete names a project the list already holds, which is the whole point of it.
  it("drops a deleted project from the picker", async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByLabelText("Project")).toHaveValue("p2"))
    expect(screen.getByRole("option", { name: "First" })).toBeInTheDocument()

    listed = summaries.filter((p) => p.id !== "p1")
    FakeSocket.instances[0].emit({ kind: "project", id: "p1", project_id: "p1" })
    await waitFor(() => expect(screen.queryByRole("option", { name: "First" })).toBeNull())
  })

  it("keeps the selection in the url", async () => {
    render(<App />)
    await screen.findByTestId("stage")
    await waitFor(() => expect(location.search).toBe("?project=p2&part=lid"))
  })
})
