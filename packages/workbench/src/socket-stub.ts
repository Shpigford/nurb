// A WebSocket jsdom does not have. Tests drive it by hand.
export class FakeSocket {
  static instances: FakeSocket[] = []
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  closed = false

  constructor(public url: string) {
    FakeSocket.instances.push(this)
  }

  emit(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) })
  }

  drop() {
    this.closed = true
    this.onclose?.()
  }

  close() {
    this.closed = true
  }
}

export function installSocket() {
  FakeSocket.instances = []
  ;(globalThis as unknown as { WebSocket: unknown }).WebSocket = FakeSocket
  return FakeSocket
}
