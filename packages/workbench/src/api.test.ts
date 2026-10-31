import { afterEach, describe, expect, it, vi } from "vitest"
import {
  absolute,
  configure,
  createProject,
  deleteProject,
  fetchProjects,
  importFolder,
} from "./api"

interface Call {
  url: string
  method: string
  body: unknown
}

function stubFetch(answer: unknown = {}): Call[] {
  const calls: Call[] = []
  vi.stubGlobal("fetch", async (url: string, init?: RequestInit) => {
    calls.push({
      url,
      method: init?.method ?? "GET",
      body: init?.body ? JSON.parse(String(init.body)) : null,
    })
    return new Response(JSON.stringify(answer))
  })
  return calls
}

afterEach(() => {
  configure({ base: "" })
  vi.unstubAllGlobals()
})

describe("api", () => {
  it("stays on the same origin until it is pointed somewhere", async () => {
    const calls = stubFetch({ projects: [] })
    await fetchProjects()
    expect(calls[0].url).toBe("/api/projects")
    expect(absolute("/glb/p1/lid.glb?run=1")).toBe("/glb/p1/lid.glb?run=1")
  })

  it("prefixes every request and every asset url with the configured base", async () => {
    configure({ base: "http://127.0.0.1:7391" })
    const calls = stubFetch({ projects: [] })
    await fetchProjects()
    expect(calls[0].url).toBe("http://127.0.0.1:7391/api/projects")
    expect(absolute("/glb/p1/lid.glb?run=1")).toBe("http://127.0.0.1:7391/glb/p1/lid.glb?run=1")
    expect(absolute("blob:nothing")).toBe("blob:nothing")
  })

  it("posts a project and an import, and deletes by id", async () => {
    const calls = stubFetch({ id: "p1", name: "First" })
    await createProject()
    await createProject("Second", true)
    await importFolder("/Users/someone/parts")
    await deleteProject("p 1")
    expect(calls).toEqual([
      { url: "/api/projects", method: "POST", body: { folder: false } },
      { url: "/api/projects", method: "POST", body: { name: "Second", folder: true } },
      { url: "/api/import", method: "POST", body: { path: "/Users/someone/parts" } },
      { url: "/api/projects/p%201", method: "DELETE", body: null },
    ])
  })

  it("passes the server's sentence through a refusal", async () => {
    vi.stubGlobal("fetch", async () => new Response(JSON.stringify({ error: "That folder has no parts." }), { status: 400 }))
    await expect(importFolder("/tmp/empty")).rejects.toThrow("That folder has no parts.")
  })
})
