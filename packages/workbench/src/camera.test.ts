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
    expect(loadCamera("p1", "lid")).toBeNull()
    expect(() => saveCamera("p1", "lid", { position: [1, 2, 3], target: [0, 0, 0] })).not.toThrow()
    vi.unstubAllGlobals()
  })

  it("refuses a stored view that is not three numbers", () => {
    const store = new Map([["nurb.camera.p1.lid", JSON.stringify({ position: ["x", "y", "z"], target: [0, 0, 0] })]])
    vi.stubGlobal("localStorage", { getItem: (k: string) => store.get(k) ?? null, setItem: () => {} })
    expect(loadCamera("p1", "lid")).toBeNull()
    vi.unstubAllGlobals()
  })

  it("round-trips a view", () => {
    const store = new Map<string, string>()
    vi.stubGlobal("localStorage", {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => store.set(k, v),
    })
    const state = { position: [1, 2, 3] as [number, number, number], target: [0, 0, 1] as [number, number, number] }
    saveCamera("p1", "lid", state)
    expect(loadCamera("p1", "lid")).toEqual(state)
    vi.unstubAllGlobals()
  })
})
