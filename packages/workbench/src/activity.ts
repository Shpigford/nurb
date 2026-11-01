// Work the workbench starts, said out loud for whoever is listening. The desktop
// shell puts it in the pod; a browser has nothing on the other end and the event
// simply goes nowhere, which is why this never asks whether the shell is there.

export type ActivityTone = "working" | "done" | "fail"

export interface Activity {
  /** The same id for the start and its answer, so one line is patched rather than stacked. */
  id: string
  title: string
  detail?: string
  tone: ActivityTone
}

export function activity(said: Activity): void {
  if (typeof window === "undefined") return
  window.dispatchEvent(new CustomEvent<Activity>("nurb:activity", { detail: said }))
}
