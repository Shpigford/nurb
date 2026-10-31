import { useState } from "react"
import { motion } from "motion/react"
import clsx from "clsx"
import { useAutoHeight } from "./motion/useAutoHeight"

// What the agent actually changed, in the part's own words. A row that says
// "wall 2.0 to 2.4" is the change; "wrote the file" is only the fact that a
// change happened, so the file-level chip is the fallback and never the goal.

const SIGNATURE = /def\s+\w+\s*\(([\s\S]*?)\)\s*(?:->[^:]*?)?:/

/** Split a parameter list on the commas that separate parameters, not the ones inside a call. */
function fields(params: string): string[] {
  const out: string[] = []
  let depth = 0
  let start = 0
  for (let i = 0; i < params.length; i++) {
    const c = params[i]
    if (c === "(" || c === "[" || c === "{") depth++
    else if (c === ")" || c === "]" || c === "}") depth--
    else if (c === "," && depth === 0) {
      out.push(params.slice(start, i))
      start = i + 1
    }
  }
  out.push(params.slice(start))
  return out
}

/**
 * The keyword defaults of the first part function in a source, in order. A
 * parameter with no default is not a parameter of the part, so it is skipped.
 */
export function keywordDefaults(source: string): Map<string, string> {
  const found = new Map<string, string>()
  const match = source.match(SIGNATURE)
  if (!match) return found
  for (const field of fields(match[1])) {
    const eq = field.indexOf("=")
    if (eq < 0) continue
    const name = field.slice(0, eq).split(":")[0].trim()
    const value = field.slice(eq + 1).trim()
    if (!/^[A-Za-z_]\w*$/.test(name) || !value) continue
    found.set(name, value)
  }
  return found
}

/** One phrase per parameter that moved, added or went away. Empty when nothing did. */
export function diffDefaults(before: string, after: string): string[] {
  const was = keywordDefaults(before)
  const now = keywordDefaults(after)
  const chips: string[] = []
  for (const [name, value] of now) {
    const old = was.get(name)
    if (old === undefined) chips.push(`added ${name}`)
    else if (old !== value) chips.push(`${name} ${old} to ${value}`)
  }
  for (const name of was.keys()) {
    if (!now.has(name)) chips.push(`removed ${name}`)
  }
  return chips
}

export type DiffLine = { sign: "+" | "-"; text: string }

/** The changed lines, with the matching head and tail trimmed off. */
export function changedLines(before: string, after: string): DiffLine[] {
  const was = before ? before.split("\n") : []
  const now = after ? after.split("\n") : []
  let head = 0
  while (head < was.length && head < now.length && was[head] === now[head]) head++
  let tail = 0
  while (tail < was.length - head && tail < now.length - head && was[was.length - 1 - tail] === now[now.length - 1 - tail]) tail++
  const removed = was.slice(head, was.length - tail).map((text): DiffLine => ({ sign: "-", text }))
  const added = now.slice(head, now.length - tail).map((text): DiffLine => ({ sign: "+", text }))
  return [...removed, ...added]
}

type SourceEdit = { name: string; before?: string; after: string }

/** The part-source edit inside a tool call's input, or null when it is some other call. */
export function sourceEdit(input: unknown): SourceEdit | null {
  if (!input || typeof input !== "object") return null
  const call = input as Record<string, unknown>
  const name = typeof call.part_name === "string" ? call.part_name : null
  if (!name) return null
  if (typeof call.old_string === "string" && typeof call.new_string === "string") {
    return { name, before: call.old_string, after: call.new_string }
  }
  if (typeof call.source === "string") return { name, after: call.source }
  return null
}

const SHOWN = 12

export default function EditChips({ input, className }: { input: unknown; className?: string }) {
  const [open, setOpen] = useState<string | null>(null)
  const [all, setAll] = useState(false)
  const h = useAutoHeight(open !== null)

  const edit = sourceEdit(input)
  const chips = edit?.before !== undefined ? diffDefaults(edit.before, edit.after) : []
  if (!edit) return null
  // Nothing at parameter level: say which part was edited, which is all that is known.
  const labels = chips.length > 0 ? chips : [`edited ${edit.name}`]
  const lines = changedLines(edit.before ?? "", edit.after)
  const shown = all ? lines : lines.slice(0, SHOWN)

  return (
    <div className={clsx("flex flex-col gap-1.5", className)}>
      <div className="flex flex-wrap gap-1">
        {labels.map((label) => (
          <button
            key={label}
            type="button"
            aria-expanded={open === label}
            onClick={() => setOpen((current) => (current === label ? null : label))}
            className={clsx(
              "mono-caption rounded-[3px] bg-raised px-1.5 py-0.5 text-muted hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
              open === label && "text-ink"
            )}
          >
            {label}
          </button>
        ))}
      </div>
      <motion.div style={h.style} animate={h.animate} transition={h.transition} onAnimationComplete={h.onAnimationComplete}>
        <div ref={h.ref}>
          {open !== null && lines.length > 0 ? (
            <div className="flex flex-col rounded-[3px] bg-raised py-1">
              {shown.map((line, i) => (
                <span
                  key={i}
                  className={clsx(
                    "px-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap",
                    line.sign === "+" ? "bg-pass-wash text-ink-soft" : "bg-fail-wash text-ink-soft"
                  )}
                >
                  {line.sign} {line.text}
                </span>
              ))}
              {!all && lines.length > SHOWN ? (
                <button
                  type="button"
                  onClick={() => setAll(true)}
                  className="mono-caption self-start px-2 pt-1 text-faint hover:text-ink"
                >
                  show more
                </button>
              ) : null}
            </div>
          ) : null}
        </div>
      </motion.div>
    </div>
  )
}
