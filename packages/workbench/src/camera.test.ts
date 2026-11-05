import { describe, expect, it, vi } from "vitest"
import { loadCamera, saveCamera } from "./camera"

describe("camera store", () => {
  it("survives a storage that throws", () => {
    const thrower = {
      getItem: () => {
        throw new Error("denied")
      },
      setItem: () => {
        throw new Error("denied")
      },
    }
    vi.stubGlobal("localStorage", thrower)
    expect(loadCamera("part-1", "p1", "lid")).toBeNull()
    expect(() => saveCamera("part-1", { position: [1, 2, 3], target: [0, 0, 0] })).not.toThrow()
    vi.unstubAllGlobals()
  })

  it("refuses a stored view that is not three numbers", () => {
    const store = new Map([["nurb.camera.part-1", JSON.stringify({ position: ["x", "y", "z"], target: [0, 0, 0] })]])
    vi.stubGlobal("localStorage", { getItem: (k: string) => store.get(k) ?? null, setItem: () => {} })
    expect(loadCamera("part-1", "p1", "lid")).toBeNull()
    vi.unstubAllGlobals()
  })

  it("moves a view saved under the old name-based key over to the part's id", () => {
    const view = JSON.stringify({ position: [1, 2, 3], target: [0, 0, 0] })
    const store = new Map([["nurb.camera.p1.lid", view]])
    vi.stubGlobal("localStorage", {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => store.set(k, v),
    })
    expect(loadCamera("part-1", "p1", "lid")).toEqual(JSON.parse(view))
    expect(loadCamera("part-1", "p1", "renamed")).toEqual(JSON.parse(view))
    vi.unstubAllGlobals()
  })

  it("round-trips a view", () => {
    const store = new Map<string, string>()
    vi.stubGlobal("localStorage", {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => store.set(k, v),
    })
    const state = { position: [1, 2, 3] as [number, number, number], target: [0, 0, 1] as [number, number, number] }
    saveCamera("part-1", state)
    expect(loadCamera("part-1", "p1", "lid")).toEqual(state)
    vi.unstubAllGlobals()
  })
})
