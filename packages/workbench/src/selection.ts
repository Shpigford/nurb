export interface Selection {
  project: string | null
  part: string | null
}

export function readSelection(): Selection {
  const params = new URLSearchParams(location.search)
  return { project: params.get("project"), part: params.get("part") }
}

export function writeSelection(selection: Selection): void {
  const params = new URLSearchParams(location.search)
  if (selection.project) params.set("project", selection.project)
  else params.delete("project")
  if (selection.part) params.set("part", selection.part)
  else params.delete("part")
  const query = params.toString()
  history.replaceState(null, "", query ? `${location.pathname}?${query}` : location.pathname)
}
