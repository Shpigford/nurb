import type { CameraState } from "@nurb/ui"

// A webview can refuse storage outright, so every access is guarded.
function key(projectId: string, partName: string): string {
  return `nurb.camera.${projectId}.${partName}`
}

function vector(value: unknown): boolean {
  return Array.isArray(value) && value.length === 3 && value.every((n) => typeof n === "number" && Number.isFinite(n))
}

export function loadCamera(projectId: string, partName: string): CameraState | null {
  try {
    const raw = localStorage.getItem(key(projectId, partName))
    if (!raw) return null
    const parsed = JSON.parse(raw) as CameraState
    // A half-written or hand-edited value would otherwise reach the readout and
    // take the page down with it.
    if (!parsed || !vector(parsed.position) || !vector(parsed.target)) return null
    return parsed
  } catch {
    return null
  }
}

export function saveCamera(projectId: string, partName: string, state: CameraState): void {
  try {
    localStorage.setItem(key(projectId, partName), JSON.stringify(state))
  } catch {
    // A view that cannot be remembered is not worth failing the page over.
  }
}
