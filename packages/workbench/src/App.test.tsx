import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import App from "./App"
import PartView from "./PartView"
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
    // The project's parts live behind one switcher in the header, the open one checked.
    fireEvent.click(await screen.findByRole("button", { name: "Parts in Second" }))
    expect(await screen.findByRole("menuitemradio", { name: "lid" })).toHaveAttribute("aria-checked", "true")
    expect(screen.getByRole("menuitemradio", { name: "body" })).toHaveAttribute("aria-checked", "false")
    expect(screen.getByTestId("stage")).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=1")
  })

  it("keeps the renamed part on stage while the host and the project disagree on its name", async () => {
    const lid = part("lid", "/glb/p2/lid.glb?run=1")
    const before = project("p2", "Second", [part("body", "/glb/p2/body.glb?run=1"), lid], messages)
    const stage = () => screen.getByTestId("stage")
    const { rerender } = render(<PartView project={before} partName="lid" />)
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=1"))

    // The host has moved its selection; the refetched project has not landed.
    rerender(<PartView project={before} partName="cap" />)
    expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=1")

    const after = { ...before, parts: [before.parts[0], { ...lid, name: "cap", build: lid.build }] }
    rerender(<PartView project={after} partName="cap" />)
    expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=1")
  })

  it("says the part is opening while a running build holds the project's read", async () => {
    vi.stubGlobal("fetch", (url: string) =>
      url === "/api/projects"
        ? Promise.resolve(new Response(JSON.stringify({ projects: listed })))
        : new Promise<Response>(() => {})
    )
    render(<App />)
    expect(await screen.findAllByText("Opening part")).not.toHaveLength(0)
    expect(screen.queryByText("No part yet")).not.toBeInTheDocument()
    expect(screen.queryByText("NOT BUILT")).not.toBeInTheDocument()
  })

  it("refetches on a build event and hands the viewer the new url", async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByTestId("stage")).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=1"))

    glb = "/glb/p2/lid.glb?run=2"
    FakeSocket.instances[0].emit({ kind: "build", id: "b2", project_id: "p2" })
    await waitFor(() => expect(screen.getByTestId("stage")).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=2"))
  })

  it("shows what was said and the plan, not the tool calls or a first measurement", async () => {
    render(<App />)
    expect(await screen.findByText("Built the bracket.")).toBeInTheDocument()
    expect(screen.getByText("A bracket")).toBeInTheDocument()
    // The plan lists sizes; a size first written down is not news in the transcript.
    expect(screen.queryByText("Measurement recorded")).toBeNull()
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
