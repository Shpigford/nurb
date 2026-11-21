import { Button, words } from "@nurb/ui"
import type { Finding } from "@nurb/ui"
import type { Part } from "./api"
import { Card } from "./FitTest"
import { isFitTest } from "./fits"

/** The sibling parts this one seems to redraw, or nothing when it is not that case. */
export function redrawnSiblings(
  part: Part,
  parts: Part[],
  shared: { name: string; used_by: string[] }[],
  findings: Finding[],
): string[] {
  // A part that comes out in pieces and shares its shapes with siblings is usually a
  // picture of those siblings together, which use() would place as the real parts.
  if (part.uses?.length || part.assembly) return []
  if (!findings.some((f) => f.rule === "solids" && f.severity === "fail")) return []
  const near = new Set(shared.filter((file) => file.used_by.includes(part.name)).flatMap((file) => file.used_by))
  return parts.filter((p) => p.name !== part.name && near.has(p.name) && !isFitTest(p.name)).map((p) => p.name)
}

const list = (names: string[]) =>
  names.length < 2 ? names.join("") : `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`

export default function AssemblyHint({ siblings, onAsk }: { siblings: string[]; onAsk?: (text: string) => void }) {
  if (siblings.length === 0) return null
  const named = list(siblings.map((name) => words(name).toLowerCase()))
  return (
    <Card icon="box" heading="Make it an assembly?">
      <p className="text-xs leading-4 text-muted">
        This part comes out in separate pieces and shares its shapes with {named}. If it shows them together, an assembly places the real parts, so each one is checked and printed on its own.
      </p>
      {onAsk ? (
        <div className="mt-1 flex">
          <Button size="sm" variant="ink" icon="chat" title="Writes the request in the chat for you to send" onClick={() => onAsk(askFor(siblings))}>
            Ask to make it an assembly
          </Button>
        </div>
      ) : null}
    </Card>
  )
}

const askFor = (siblings: string[]) =>
  `Rebuild this part as an assembly that places the real ${list(siblings)} parts, passing the parameters they share, so each part is checked and printed on its own.`
