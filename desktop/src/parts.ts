import type { Message } from "@nurb/ui";
import type { ProjectSummary } from "@nurb/workbench/api";

// The part is the unit and the project is a folder. A project the person never
// named is invisible: it holds one part, and the library shows the part alone.

/** rail_bracket is Rail bracket wherever a part is spoken of: on a card, in the activity pod. */
export function titleCase(name: string): string {
  const spoken = name.replace(/_/g, " ");
  return spoken.charAt(0).toUpperCase() + spoken.slice(1);
}

/** The rail's Projects section: the folders, in the order the library listed them. */
export function folders(projects: ProjectSummary[]): ProjectSummary[] {
  return projects.filter((project) => project.folder);
}

export type MoveTarget = { id: string; name: string; parts: number };

/** Where a part can go: every folder except the one already holding it. */
export function moveTargets(
  projects: ProjectSummary[],
  part: { project_id: string } | null,
): MoveTarget[] {
  return folders(projects)
    .filter((project) => project.id !== part?.project_id)
    .map((project) => ({ id: project.id, name: project.name, parts: project.parts }));
}

/**
 * The lines one chat column owns. A folder keeps a conversation per part plus
 * its own, so the rows are filtered; a project holding a single part has one
 * conversation, and every line in it belongs to that part.
 */
export function messagesForPart(
  messages: Message[],
  part: string | null,
  folder: boolean,
): Message[] {
  if (!folder) return messages;
  return messages.filter((message) => (message.part ?? null) === part);
}
