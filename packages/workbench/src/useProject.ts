import { useCallback, useEffect, useRef, useState } from "react"
import { ApiError, fetchProject, type Project } from "./api"
import { useLive } from "./live"

/**
 * One project, kept current. A build lands as a part, a build and a message in the
 * same breath, so the fetches overlap and an older answer can arrive last; only the
 * newest wins. Only a 404 reports `missing`, because the caller treats that as gone
 * and lands somewhere else; a dropped connection during an engine restart keeps what
 * is on screen, and the reconnect's refetch tries again.
 */
export function useProject(projectId: string | null): {
  project: Project | null
  missing: boolean
  reload: () => void
} {
  const [project, setProject] = useState<Project | null>(null)
  const [missing, setMissing] = useState(false)
  const seq = useRef(0)
  const asked = useRef<string | null>(null)

  const reload = useCallback(() => {
    const seen = ++seq.current
    // `missing` is about one project. Another one has not been answered for yet, so
    // it starts out present; a refetch of the same one keeps the verdict it earned.
    if (asked.current !== projectId) setMissing(false)
    asked.current = projectId
    if (!projectId) {
      setProject(null)
      return
    }
    // A switch shows nothing rather than the project before it; a refetch of the
    // same project keeps what is on screen until the answer lands.
    setProject((current) => (current?.id === projectId ? current : null))
    void fetchProject(projectId).then(
      (data) => {
        if (seen !== seq.current) return
        setProject(data)
        setMissing(false)
      },
      (error: unknown) => {
        if (seen !== seq.current) return
        if (!(error instanceof ApiError) || error.status !== 404) return
        setProject(null)
        setMissing(true)
      }
    )
  }, [projectId])

  useEffect(reload, [reload])

  useLive((event) => {
    // A reconnect arrives with no project, so it refetches too. So does a bench
    // change, because it can move the printer this project prices against.
    if (!event.project_id || event.kind === "workshop" || event.project_id === projectId) reload()
  })

  return { project, missing, reload }
}
