import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { FakeSocket, installSocket } from "./socket-stub"

beforeEach(() => {
  vi.resetModules()
  installSocket()
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe("live store", () => {
  it("opens one socket for two subscribers and reconnects after a close", async () => {
    const { subscribe } = await import("./live")
    const seen: string[] = []
    const off1 = subscribe((e) => seen.push(`a:${e.kind}`))
    const off2 = subscribe((e) => seen.push(`b:${e.kind}`))
    expect(FakeSocket.instances).toHaveLength(1)

    FakeSocket.instances[0].emit({ kind: "build", id: "b1", project_id: "p1" })
    expect(seen).toEqual(["a:build", "b:build"])

    FakeSocket.instances[0].drop()
    vi.advanceTimersByTime(1000)
    expect(FakeSocket.instances).toHaveLength(2)

    // A reconnect tells every listener to refetch, since events were missed.
    seen.length = 0
    FakeSocket.instances[1].onopen?.()
    expect(seen).toEqual(["a:project", "b:project"])

    off1()
    off2()
  })

  it("reconnects to the newly configured base without a backoff", async () => {
    const { configure } = await import("./api")
    const { subscribe, reconnect } = await import("./live")
    const seen: string[] = []
    const off = subscribe((e) => seen.push(e.kind))
    expect(FakeSocket.instances[0].url).toBe("ws://localhost:3000/ws")

    configure({ base: "http://127.0.0.1:7391" })
    reconnect()
    expect(FakeSocket.instances[0].closed).toBe(true)
    expect(FakeSocket.instances).toHaveLength(2)
    expect(FakeSocket.instances[1].url).toBe("ws://127.0.0.1:7391/ws")

    // A fresh socket, not a retry: no synthetic refetch on open.
    FakeSocket.instances[1].onopen?.()
    expect(seen).toEqual([])
    off()
  })

  it("waits for a base on a page that is not served over http", async () => {
    const { configure } = await import("./api")
    const { subscribe, reconnect } = await import("./live")
    const original = window.location
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...original, protocol: "tauri:", host: "localhost" },
    })
    try {
      const off = subscribe(() => {})
      expect(FakeSocket.instances).toHaveLength(0)
      configure({ base: "http://127.0.0.1:7391" })
      reconnect()
      expect(FakeSocket.instances).toHaveLength(1)
      expect(FakeSocket.instances[0].url).toBe("ws://127.0.0.1:7391/ws")
      off()
    } finally {
      Object.defineProperty(window, "location", { configurable: true, value: original })
    }
  })

  it("retries instead of throwing when the constructor refuses the socket", async () => {
    const { subscribe } = await import("./live")
    const Refusing = class {
      constructor() {
        throw new DOMException("The operation is insecure.", "SecurityError")
      }
    }
    ;(globalThis as unknown as { WebSocket: unknown }).WebSocket = Refusing
    const off = subscribe(() => {})
    installSocket()
    vi.advanceTimersByTime(1000)
    expect(FakeSocket.instances).toHaveLength(1)
    off()
  })

  it("opens anyway when the host refuses to resolve a base", async () => {
    const { configure } = await import("./api")
    const { subscribe } = await import("./live")
    configure({
      base: "http://127.0.0.1:7391",
      resolve: () => {
        throw new Error("no bridge yet")
      },
    })
    const off = subscribe(() => {})
    FakeSocket.instances[0].drop()
    vi.advanceTimersByTime(1000)
    expect(FakeSocket.instances).toHaveLength(2)
    off()
    configure({ base: "" })
  })

  it("closes the socket when the last subscriber leaves", async () => {
    const { subscribe } = await import("./live")
    const off = subscribe(() => {})
    off()
    expect(FakeSocket.instances[0].closed).toBe(true)
  })
})
