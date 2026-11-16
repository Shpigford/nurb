import { act, render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import App from "./App"
import { part, project, summaries } from "./fixtures"
import type { Part, Project, RevisionEntry, RevisionView } from "./api"
import { FakeSocket, installSocket } from "./socket-stub"

const heard = vi.hoisted(() => [] as string[])
vi.mock("@nurb/ui", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@nurb/ui")>()
  return { ...actual, ViewerIsland: () => <div data-testid="viewer" />, cue: (name: string) => heard.push(name) }
})

interface Call {
  url: string
  method: string
  body: Record<string, unknown> | null
}

let calls: Call[] = []
let state: Project

const base = part("lid", "/glb/p2/lid.glb?run=b1")

function withPart(over: Partial<Part>): Project {
  return project("p2", "Second", [{ ...base, ...over }])
}

const rows: RevisionEntry[] = [
  { id: "r1", revision: 3, created_at: "2026-09-01T00:00:00Z", note: null, current: true, status: "ok", prompt: null, group: "r1", thumbnail_url: null },
  { id: "r0", revision: 2, created_at: "2026-08-31T00:00:00Z", note: null, current: false, status: "unbuilt", prompt: null, group: "r0", thumbnail_url: null },
  { id: "rA", revision: 1, created_at: "2026-08-30T00:00:00Z", note: "Applied wall from the sliders", current: false, status: "ok", prompt: null, group: "rA", thumbnail_url: null },
]

const rev1: RevisionView = {
  id: "rA",
  revision: 1,
  created_at: "2026-08-30T00:00:00Z",
  note: "Applied wall from the sliders",
  current: false,
  status: "ok",
  error: null,
  source: "",
  build: {
    id: "old-run",
    status: "ok",
    passed: true,
    started_at: "2026-08-30T00:00:00Z",
    finished_at: "2026-08-30T00:00:02Z",
    error: null,
    findings: [],
    stats: { bbox: [10, 10, 10] },
    slice: null,
    glb_url: "/glb/p2/lid.glb?run=old-run",
    render_url: "/render/p2/lid.png?run=old-run",
    thumbnail_url: "/thumbnail/p2/lid.png?run=old-run",
    shown_revision: 1,
    stale: false,
  },
  params: [{ name: "wall", kind: "float", value: 1.5, default: 1.5 }],
}

const rev2: RevisionView = { ...rev1, id: "r0", revision: 2, note: null, status: "unbuilt", build: null, params: [] }

function install(routes: Record<string, (body: Record<string, unknown> | null) => unknown> = {}) {
  vi.stubGlobal("fetch", async (url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET"
    const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null
    calls.push({ url, method, body })
    if (url === "/api/projects") return new Response(JSON.stringify({ projects: summaries }))
    if (url === "/api/projects/p2" && method === "GET") return new Response(JSON.stringify(state))
    const handler = routes[`${method} ${url}`]
    if (!handler) return new Response("nothing here", { status: 404 })
    const answer = await handler(body)
    return answer instanceof Response ? answer : new Response(JSON.stringify(answer))
  })
}

const history = {
  "GET /api/parts/part-lid/revisions": () => ({ revisions: rows }),
  "GET /api/parts/part-lid/revisions/rA": () => rev1,
  "GET /api/parts/part-lid/revisions/r0": () => rev2,
}

const stage = () => screen.getByTestId("stage")
const banner = () => screen.getByRole("status", { name: "Earlier revision on stage" })

async function openRevision(name: RegExp) {
  await userEvent.click(await screen.findByRole("button", { name: /history/i }))
  const panel = await screen.findByRole("dialog", { name: "Part history" })
  await userEvent.click(await within(panel).findByRole("button", { name }))
}

beforeEach(() => {
  calls = []
  heard.length = 0
  state = withPart({})
  installSocket()
  window.history.replaceState(null, "", "/?project=p2&part=lid")
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("history", { timeout: 15000 }, () => {
  it("folds the edits made for one message into one row, opened at its newest build", async () => {
    const asked = "add a lip at the front"
    const grouped: RevisionEntry[] = [
      { ...rows[1], revision: 3, prompt: asked, group: "rA" },
      { ...rows[2], revision: 2, note: null, prompt: asked, group: "rA", current: false },
      { ...rows[2], id: "rB", revision: 1, prompt: asked, group: "rA" },
    ]
    install({ ...history, "GET /api/parts/part-lid/revisions": () => ({ revisions: grouped }) })
    render(<App />)
    await userEvent.click(await screen.findByRole("button", { name: /history/i }))
    const panel = await screen.findByRole("dialog", { name: "Part history" })
    expect(await within(panel).findByText(asked)).toBeInTheDocument()
    expect(within(panel).getByText(/3 edits/)).toBeInTheDocument()
    expect(within(panel).queryByText("REV 01")).not.toBeInTheDocument()

    await userEvent.click(within(panel).getByRole("button", { name: "Show each of the 3 edits" }))
    expect(within(panel).getByText("Never built")).toBeInTheDocument()
    expect(within(panel).getByText("REV 01")).toBeInTheDocument()

    // The row itself opens rev 2, the newest edit that built, not rev 3 which never did.
    await userEvent.click(within(panel).getByRole("button", { name: new RegExp(asked) }))
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=old-run"))
    expect(calls.some((c) => c.url.endsWith("/revisions/rA"))).toBe(true)
  })

  it("puts an earlier revision's own geometry on stage, read-only, and comes back", async () => {
    install(history)
    render(<App />)
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=b1"))
    expect(screen.getByLabelText("wall")).toBeInTheDocument()

    await openRevision(/REV 01/)
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=old-run"))
    expect(banner()).toHaveTextContent(/Viewing rev 01/)
    expect(banner()).toHaveTextContent("Applied wall from the sliders")
    // The values it was built at, and nothing to drag, label or download.
    expect(screen.queryByLabelText("wall")).not.toBeInTheDocument()
    expect(screen.getByText("1.5")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /label a spot/i })).not.toBeInTheDocument()

    await userEvent.click(within(banner()).getByRole("button", { name: "Back to rev 03" }))
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=b1"))
    expect(screen.getByLabelText("wall")).toBeInTheDocument()
    // Looking builds nothing and writes nothing.
    const posts = () => calls.filter((c) => c.method === "POST" && !c.url.endsWith("/slice"))
    expect(posts()).toHaveLength(0)
    // Coming back is not a reason to price the part again.
    expect(calls.filter((c) => c.url.endsWith("/slice"))).toHaveLength(1)
  })

  it("restores as a new revision, naming the one it saw as current", async () => {
    install({
      ...history,
      "POST /api/parts/part-lid/revisions/rA/restore": () => ({ revision_id: "r4", revision: 4, build: base.build }),
    })
    render(<App />)
    await openRevision(/REV 01/)
    await userEvent.click(within(await screen.findByRole("status", { name: "Earlier revision on stage" })).getByRole("button", { name: "Restore rev 01" }))
    await waitFor(() => expect(screen.queryByRole("status", { name: "Earlier revision on stage" })).not.toBeInTheDocument())
    const [restore] = calls.filter((c) => c.url.endsWith("/restore"))
    expect(restore.body).toEqual({ expected_revision_id: "r1" })
    expect(await screen.findByText("Restored rev 01 as rev 04.")).toBeInTheDocument()
  })

  it("says why a refused restore was refused and stays on the old revision", async () => {
    install({
      ...history,
      "POST /api/parts/part-lid/revisions/rA/restore": () =>
        new Response(JSON.stringify({ error: "lid changed while you were looking." }), { status: 409 }),
    })
    render(<App />)
    await openRevision(/REV 01/)
    await userEvent.click(within(await screen.findByRole("status", { name: "Earlier revision on stage" })).getByRole("button", { name: "Restore rev 01" }))
    expect(await screen.findByText("lid changed while you were looking.")).toBeInTheDocument()
    expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=old-run")
  })

  it("shows nothing in place of a revision that was never built", async () => {
    install(history)
    render(<App />)
    await openRevision(/REV 02/)
    expect(await screen.findByText("REV 02 was never built")).toBeInTheDocument()
    expect(stage()).toHaveAttribute("data-glb-url", "")
  })

  it("leaves the old revision when a new one lands", async () => {
    install(history)
    render(<App />)
    await openRevision(/REV 01/)
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=old-run"))
    state = withPart({
      revision_id: "r5",
      revision: 5,
      build: { ...base.build!, id: "b5", glb_url: "/glb/p2/lid.glb?run=b5" },
    })
    act(() => FakeSocket.instances[0].emit({ kind: "part", id: "part-lid", project_id: "p2" }))
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=b5"))
    expect(screen.queryByRole("status", { name: "Earlier revision on stage" })).not.toBeInTheDocument()
  })

  it("leaves a revision that never built with Escape, though it has no stage tools", async () => {
    install(history)
    render(<App />)
    await openRevision(/REV 02/)
    await screen.findByText("REV 02 was never built")
    await userEvent.keyboard("{Escape}")
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=b1"))
  })

  it("keeps the old revision up until the restore's build answers", async () => {
    let answer: (value: unknown) => void = () => {}
    install({
      ...history,
      "POST /api/parts/part-lid/revisions/rA/restore": () => new Promise((resolve) => (answer = resolve)),
    })
    render(<App />)
    await openRevision(/REV 01/)
    await userEvent.click(within(await screen.findByRole("status", { name: "Earlier revision on stage" })).getByRole("button", { name: "Restore rev 01" }))
    // The revision commits and the page hears about it before the build is done.
    state = withPart({ revision_id: "r4", revision: 4 })
    act(() => FakeSocket.instances[0].emit({ kind: "part", id: "part-lid", project_id: "p2" }))
    await waitFor(() => expect(screen.getByText("BUILDING")).toBeInTheDocument())
    expect(banner()).toHaveTextContent("Restoring")
    state = withPart({ revision_id: "r4", revision: 4, build: { ...base.build!, id: "b4", glb_url: "/glb/p2/lid.glb?run=b4" } })
    act(() => answer({ revision_id: "r4", revision: 4, build: state.parts[0].build }))
    act(() => FakeSocket.instances[0].emit({ kind: "build", id: "b4", project_id: "p2" }))
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=b4"))
    expect(screen.queryByRole("status", { name: "Earlier revision on stage" })).not.toBeInTheDocument()
  })

  it("plays nothing for a restore that was refused", async () => {
    install({
      ...history,
      "POST /api/parts/part-lid/revisions/rA/restore": () =>
        new Response(JSON.stringify({ error: "lid changed while you were looking." }), { status: 409 }),
    })
    render(<App />)
    await openRevision(/REV 01/)
    await userEvent.click(within(await screen.findByRole("status", { name: "Earlier revision on stage" })).getByRole("button", { name: "Restore rev 01" }))
    await screen.findByText("lid changed while you were looking.")
    expect(heard).not.toContain("ready")
  })

  it("drops a restore's answer that arrives after another part is on stage", async () => {
    let answer: (value: unknown) => void = () => {}
    const cap = { ...part("cap", "/glb/p2/cap.glb?run=c1"), overrides: { wall: 3 } }
    state = project("p2", "Second", [base, cap])
    install({
      ...history,
      "POST /api/parts/part-lid/revisions/rA/restore": () => new Promise((resolve) => (answer = resolve)),
    })
    render(<App />)
    await openRevision(/REV 01/)
    await userEvent.click(within(await screen.findByRole("status", { name: "Earlier revision on stage" })).getByRole("button", { name: "Restore rev 01" }))
    await userEvent.click(screen.getByRole("button", { name: "Parts in Second" }))
    await userEvent.click(await screen.findByRole("menuitemradio", { name: "cap" }))
    await waitFor(() => expect(stage()).toHaveAttribute("data-glb-url", "/glb/p2/cap.glb?run=c1"))
    act(() => answer({ revision_id: "r4", revision: 4, build: base.build }))
    await act(async () => {})
    // Nothing about lid's restore lands on cap: its values and its rail stay its own.
    expect(screen.queryByText("Restored rev 01 as rev 04.")).not.toBeInTheDocument()
    expect(screen.getByLabelText("wall value")).toHaveValue("3")
  })
})
