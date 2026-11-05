import type { CameraState } from "@nurb/ui"

// By part id, which a rename or a move into a folder leaves alone. A webview can
// refuse storage outright, so every access is guarded.
function key(partId: string): string {
  return `nurb.camera.${partId}`
}

function vector(value: unknown): boolean {
  return Array.isArray(value) && value.length === 3 && value.every((n) => typeof n === "number" && Number.isFinite(n))
}

export function loadCamera(partId: string, projectId: string, partName: string): CameraState | null {
  try {
    let raw = localStorage.getItem(key(partId))
    if (!raw) {
      // A view saved before views were kept by id moves over the first time the part opens.
      raw = localStorage.getItem(`nurb.camera.${projectId}.${partName}`)
      if (!raw) return null
      localStorage.setItem(key(partId), raw)
    }
    const parsed = JSON.parse(raw) as CameraState
    // A half-written or hand-edited value would otherwise reach the readout and
    // take the page down with it.
    if (!parsed || !vector(parsed.position) || !vector(parsed.target)) return null
    return parsed
  } catch {
    return null
  }
}

export function saveCamera(partId: string, state: CameraState): void {
  try {
    localStorage.setItem(key(partId), JSON.stringify(state))
  } catch {
    // A view that cannot be remembered is not worth failing the page over.
  }
}
