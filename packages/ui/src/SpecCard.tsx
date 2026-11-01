import Icon from "./Icon"
import { words } from "./format"
import type { Spec, SpecDimension } from "./types"

// The pinned spec, rendered as a card in the transcript: what gets built, from which
// numbers, and where each number came from. Where a number came from is the point
// (DESIGN.md §1), said the way the person would say it, since they are not engineers.

const SOURCE_LABELS: Record<string, string> = {
  standard: "Published",
  measured: "You measured",
  asked: "You told us",
  doctrine: "Rule of thumb",
}

// Specs pinned before `source` existed carry only prose provenance; a few
// words in it are reliable enough to pick a label.
function sourceOf(dim: SpecDimension) {
  if (dim.source) return dim.source
  const how = dim.how.toLowerCase()
  if (/\b(caliper|measured|ruler|tape)\b/.test(how)) return "measured"
  if (/\b(user|stated|asked|said|told)\b/.test(how)) return "asked"
  if (/\b(standard|spec|published|listing|datasheet|nominal)\b/.test(how)) return "standard"
  return "doctrine"
}

function Rule({ children }: { children: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="mono-caption shrink-0 text-faint [letter-spacing:0.12em]">{children}</span>
      <span className="h-px flex-1 bg-line-soft" />
    </div>
  )
}

// `model` and `effort` are what pinned it; kept on the props for callers, not shown.
export default function SpecCard({ spec }: { spec: Spec; model?: string; effort?: string }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-[6px] border border-line">
      <div className="chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3">
        <span className="mono-label flex items-center gap-2 text-ink">
          <Icon name="lock" />
          The plan
        </span>
      </div>

      <div className="flex flex-col gap-3 px-3 pt-[11px] pb-3">
        <p className="text-[13px] leading-[19px] text-pretty text-ink-soft">{spec.summary}</p>

        <dl className="flex flex-col gap-[5px]">
          {spec.dimensions.map((dim) => {
            const source = sourceOf(dim)
            return (
              <div
                key={dim.name}
                className="flex items-baseline gap-2"
                title={dim.provisional ? `${dim.how} · a best guess until it is measured` : dim.how}
              >
                <dt className="min-w-0 flex-1 truncate text-xs leading-4 text-ink-soft">{words(dim.name)}</dt>
                <dd className="mono-value text-ink">
                  {dim.provisional ? "~" : ""}
                  {dim.value_mm} mm
                </dd>
                <dd className={source === "measured" ? "mono-caption w-24 shrink-0 text-right text-accent-ink [letter-spacing:0.06em]" : "mono-caption w-24 shrink-0 text-right text-muted [letter-spacing:0.06em]"}>
                  {SOURCE_LABELS[source]}
                </dd>
              </div>
            )
          })}
        </dl>

        {spec.acceptance.length > 0 ? (
          <div className="flex flex-col gap-1.5">
            <Rule>Done when</Rule>
            <ul className="flex list-disc flex-col gap-1 pl-4 marker:text-faint" role="list">
              {spec.acceptance.map((item, index) => (
                <li key={index} className="text-xs leading-4 text-pretty text-ink-soft">
                  {item.criterion}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {spec.params.length > 0 ? (
          <div className="flex flex-col gap-1.5">
            <Rule>{`${spec.params.length} slider${spec.params.length === 1 ? "" : "s"} to adjust`}</Rule>
            <ul className="flex flex-wrap gap-1" role="list">
              {spec.params.map((p) => (
                <li key={p.name} className="rounded-control bg-raised px-1.5 py-0.5 text-xs leading-4 text-ink-soft" title={p.description}>
                  {words(p.name)}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  )
}
