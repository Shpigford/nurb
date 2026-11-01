import { renderHook, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { configure } from "./api"
import { part, project } from "./fixtures"
import { installSocket } from "./socket-stub"
import { useProject } from "./useProject"

const first = project("p1", "First", [part("bracket", "/glb/p1/bracket.glb")])

beforeEach(() => {
  installSocket()
})

afterEach(() => {
  configure({ base: "" })
  vi.unstubAllGlobals()
})

// Each answer in turn: the first fetch lands the project, the second is the failure
// under test.
function stubFetch(answers: (() => Response | Promise<Response>)[]) {
  let i = 0
  vi.stubGlobal("fetch", async () => {
    const answer = answers[Math.min(i, answers.length - 1)]
    i += 1
    return answer()
  })
}

describe("useProject", () => {
  it("reports missing when the project is gone", async () => {
    stubFetch([() => new Response(JSON.stringify({ error: "No project p1." }), { status: 404 })])
    const { result } = renderHook(() => useProject("p1"))
    await waitFor(() => expect(result.current.missing).toBe(true))
    expect(result.current.project).toBeNull()
  })

  it("stops reporting missing once another project is asked for", async () => {
    stubFetch([
      () => new Response(JSON.stringify({ error: "No project p1." }), { status: 404 }),
      () => new Promise<Response>(() => {}),
    ])
    const { result, rerender } = renderHook(({ id }) => useProject(id), {
      initialProps: { id: "p1" },
    })
    await waitFor(() => expect(result.current.missing).toBe(true))

    // p2 has not answered yet, so nothing is known to be gone.
    rerender({ id: "p2" })
    await waitFor(() => expect(result.current.missing).toBe(false))
  })

  it("keeps the project on screen when the connection drops", async () => {
    stubFetch([
      () => new Response(JSON.stringify(first)),
      () => Promise.reject(new TypeError("Failed to fetch")),
    ])
    const { result } = renderHook(() => useProject("p1"))
    await waitFor(() => expect(result.current.project?.id).toBe("p1"))

    result.current.reload()
    await waitFor(() => expect(result.current.project?.id).toBe("p1"))
    expect(result.current.missing).toBe(false)
  })

  it("keeps the project on screen when the engine answers 503", async () => {
    stubFetch([
      () => new Response(JSON.stringify(first)),
      () => new Response("restarting", { status: 503 }),
    ])
    const { result } = renderHook(() => useProject("p1"))
    await waitFor(() => expect(result.current.project?.id).toBe("p1"))

    result.current.reload()
    await waitFor(() => expect(result.current.project?.id).toBe("p1"))
    expect(result.current.missing).toBe(false)
  })
})
