import { useEffect, useRef } from "react"
import { apiBase, resolveBase } from "./api"

export interface LiveEvent {
  /** "workshop" is the bench itself: a printer added, removed or made the default. */
  kind: "project" | "part" | "build" | "message" | "workshop"
  id: string
  project_id: string
}

type Listener = (event: LiveEvent) => void

const listeners = new Set<Listener>()
let socket: WebSocket | null = null
let retry = 0
let timer: ReturnType<typeof setTimeout> | null = null

// A page served over http(s) reaches its own origin; any other origin (the desktop's
// `tauri://localhost`) has no serve of its own and waits for `configure`.
function url(): string | null {
  const base = apiBase()
  if (!base) {
    if (location.protocol !== "http:" && location.protocol !== "https:") return null
    const scheme = location.protocol === "https:" ? "wss:" : "ws:"
    return `${scheme}//${location.host}/ws`
  }
  const parsed = new URL(base)
  return `${parsed.protocol === "https:" ? "wss:" : "ws:"}//${parsed.host}/ws`
}

// The host that spawned the serve may have restarted it on another port, so it gets
// asked for the base again before every retry. A failed answer keeps the old one.
function reopen() {
  let pending: Promise<string> | null = null
  try {
    pending = resolveBase()
  } catch {
    // A host whose bridge is not up yet refuses synchronously. Letting that escape
    // the timer would end the retry chain, and the page would stay deaf until reload.
    return open()
  }
  if (!pending) return open()
  void pending.then(open, open)
}

function open() {
  if (socket) return
  const target = url()
  if (!target) return
  let ws: WebSocket
  try {
    ws = new WebSocket(target)
  } catch {
    // A secure context refuses an insecure socket synchronously (WKWebView says
    // "The operation is insecure" for `ws://localhost`); a throw here would unmount
    // the React tree that subscribed. Retry the way a dropped socket does.
    if (listeners.size === 0) return
    const wait = Math.min(1000 * 2 ** retry, 8000)
    retry += 1
    timer = setTimeout(reopen, wait)
    return
  }
  socket = ws
  ws.onopen = () => {
    if (retry > 0) {
      // A reconnect means events were missed, so every listener refetches.
      retry = 0
      for (const listener of listeners) listener({ kind: "project", id: "", project_id: "" })
    }
  }
  ws.onmessage = (event) => {
    let parsed: LiveEvent
    try {
      parsed = JSON.parse(String(event.data)) as LiveEvent
    } catch {
      return
    }
    for (const listener of listeners) listener(parsed)
  }
  ws.onclose = () => {
    socket = null
    if (listeners.size === 0) return
    const wait = Math.min(1000 * 2 ** retry, 8000)
    retry += 1
    timer = setTimeout(reopen, wait)
  }
}

// Refcounted, because React 19 StrictMode mounts every effect twice in dev and a
// second socket would double every refetch.
export function subscribe(listener: Listener): () => void {
  listeners.add(listener)
  if (listeners.size === 1) open()
  return () => {
    listeners.delete(listener)
    if (listeners.size > 0) return
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    const ws = socket
    socket = null
    retry = 0
    if (ws) {
      ws.onclose = null
      ws.close()
    }
  }
}

// A host that configures the base after the first subscriber mounted (the desktop
// learns its serve's port asynchronously) drops the socket it opened against the
// wrong address and opens one against the right one, with no backoff and no refetch.
export function reconnect() {
  const ws = socket
  socket = null
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
  retry = 0
  if (ws) {
    ws.onclose = null
    ws.close()
  }
  if (listeners.size > 0) open()
}

export function useLive(onEvent: (event: LiveEvent) => void) {
  const latest = useRef(onEvent)
  latest.current = onEvent
  useEffect(() => subscribe((event) => latest.current(event)), [])
}
