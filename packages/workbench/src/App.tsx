import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { ChatPanel, EmptyShelf, HeaderStack, Stage, StageEmpty } from "@nurb/ui"
import { fetchProjects, type ProjectSummary } from "./api"
import { useLive } from "./live"
import { readSelection, writeSelection } from "./selection"
import PartView from "./PartView"
import Transcript from "./Transcript"
import { useProject } from "./useProject"

export default function App() {
  const initial = useMemo(readSelection, [])
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [projectId, setProjectId] = useState<string | null>(initial.project)
  const [partName, setPartName] = useState<string | null>(initial.part)
  const [loadedProjects, setLoadedProjects] = useState(false)

  // Two lists land at once after a build, so an older answer can arrive last.
  const listSeq = useRef(0)

  const loadProjects = useCallback(async () => {
    const seq = ++listSeq.current
    const data = await fetchProjects().catch(() => null)
    if (!data || seq !== listSeq.current) return
    setProjects(data.projects)
    setLoadedProjects(true)
    setProjectId((current) => current ?? data.projects[0]?.id ?? null)
  }, [])

  const { project, missing } = useProject(projectId)

  useEffect(() => {
    void loadProjects()
  }, [loadProjects])

  // The link named a project that is gone, so fall back to one that is here.
  useEffect(() => {
    if (!missing) return
    setProjectId(null)
    void loadProjects()
  }, [missing, loadProjects])

  useLive((event) => {
    // A reconnect arrives with no project, so the list refetches too. Every project
    // event refetches, because one is how a project arrives and how it goes, and
    // "already in the list" is exactly the case a delete leaves behind.
    if (!event.project_id || event.kind === "project") void loadProjects()
  })

  const parts = project?.parts ?? []
  const part = parts.find((p) => p.name === partName) ?? parts[0] ?? null
  const messages = project?.messages ?? []

  useEffect(() => {
    // Until the project has loaded there is no resolved part, and writing then
    // would strip the part the deep link asked for.
    if (projectId && project?.id !== projectId) return
    writeSelection({ project: projectId, part: part?.name ?? null })
  }, [projectId, project?.id, part?.name])

  if (loadedProjects && projects.length === 0) {
    return (
      <Stage>
        <StageEmpty>
          <EmptyShelf />
          <p className="mono-caption max-w-[40ch] text-center text-on-stage-muted">
            Add the nurb connection to your agent, then ask it for a part.
          </p>
        </StageEmpty>
      </Stage>
    )
  }

  return (
    <PartView
      project={project}
      partName={partName}
      onSelectPart={setPartName}
      onPartRenamed={(_, name) => setPartName(name)}
      header={{
        start: (
          <HeaderStack
            label="PROJECT"
            value={
              <select
                aria-label="Project"
                value={projectId ?? ""}
                onChange={(e) => {
                  setProjectId(e.target.value)
                  setPartName(null)
                }}
                className="mono-value -mx-1 max-w-[180px] rounded-control bg-transparent px-1 text-ink hover:bg-raised"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            }
          />
        ),
      }}
      chat={
        <ChatPanel
          strip={{ label: "Conversation", trailing: `${messages.length} turns` }}
          composer={
            <p className="mono-caption text-muted">The agent talks here through the nurb connection.</p>
          }
        >
          <Transcript messages={messages} />
        </ChatPanel>
      }
    />
  )
}
