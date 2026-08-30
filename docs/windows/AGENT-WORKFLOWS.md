# Agent workflows for maintaining nurb-windows

How the fork uses agents, skills, and subagents, and where each capability
belongs. The rule that governs every row below: **prefer the simplest
mechanism that works.** A deterministic script beats a skill (no model
invoked, no tokens spent); a skill beats a subagent (loads only when used,
no separate context window to supervise); a subagent earns its place only
when a side task would flood the main conversation with context nobody will
reference again. Never build an agent hierarchy for appearance.

## What already exists

- **The shipped skill** (`src/nurb/agents.md`, mirrored as
  `src/nurb/skill.md` and `skills/nurb/SKILL.md`): follows the Agent Skills
  open standard, which Claude Code and other tools load from `SKILL.md`
  frontmatter + body. `nurb skill --sync` writes it to the two install
  paths (`~/.agents/skills/nurb/` and `~/.claude/skills/nurb/`). It is the
  part-designer's instructions, not the maintainer's.
- **Deterministic tooling that replaced agent reasoning** (the pattern to
  copy): `tools/upstream_sync.py` classifies SAFE / REVIEW /
  WINDOWS-SPECIFIC drift; `tools/release_gate.py` checks the eight release
  invariants; both are wired into CI and both fail loudly. A maintainer
  never has to re-derive "is the fork behind upstream?" — the tool answers
  it.
- **Desktop adapters**: the app provisions Claude and Codex ACP adapters
  into app data, so the part-design loop runs inside the app. That is the
  user-facing agent surface; it is not a maintenance surface.
- **88 local skills** under `~/.agents/skills/` (development-methodology
  skills from the agent ecosystems: spec-driven-development,
  doubt-driven-development, debugging, git workflows, and so on). These are
  generic; none are fork-specific, and none should be: fork-specific
  knowledge belongs in the repo (docs, gates, the porting checklist), where
  it versions with the code.

## Where a capability belongs

| Capability | Layer | Why |
|---|---|---|
| "Is the fork behind upstream, and on which paths?" | `tools/upstream_sync.py` + CI | Deterministic; must run on schedule, not when someone remembers |
| "Are the release invariants still true?" | `tools/release_gate.py` + CI | Deterministic; must gate pushes, not advise them |
| "How do I merge the next upstream release?" | `docs/windows/PORTING-MERGE-CHECKLIST.md` | Prose procedure with real decisions; a script cannot choose ADAPT vs KEEP |
| "How do I release?" | `docs/windows/RELEASE.md` | Procedure; the steps that can be automated already are |
| "Design a part" | `src/nurb/agents.md` (the skill) | The shipped product skill; loaded only when designing |
| "Audit the fork's upstream delta and Windows impact" | A subagent, on demand | One-shot context-heavy research; keep it out of the main session |
| "Drive the merge to green" | Main agent + the gates | The gates are the verification; no subagent needed |

## Recommended additions (none required)

1. **An `upstream-port` subagent**, spawned only during a merge session:
   reads `PORTING-MERGE-CHECKLIST.md`, runs `upstream_sync.py status
   --strict` for the classification, resolves each conflict per the table,
   and returns the conflict map plus verification results. Its whole job is
   to keep merge exploration out of the main conversation. Define it where
   your harness keeps subagents (Claude Code: `.claude/agents/`); it is a
   per-maintainer convenience, not repo content, so it must not be
   committed to the public fork.

2. **A `fork-audit` skill** (personal, not repo): a `SKILL.md` that runs the
   ground-truth sequence (HEAD, upstream HEAD, merge base, strict gate,
   release gate, PR state) and formats the answer. What the maintainer does
   at the start of every session, made one command. This is exactly the
   "repeated manual work becomes a skill" case.

3. **Nothing else.** The remaining proposed roles from the contract survey
   (Windows/platform, QA, security, CI, release, docs, branding) are each
   already covered by a deterministic tool, a CI job, or a doc. Spawning
   specialist agents for them would add supervision cost without adding
   information, because the gates already say pass/fail.

## Framework notes (researched, August 2026)

- **Agent Skills open standard**: a directory with `SKILL.md` (YAML
  frontmatter `name`/`description`, then markdown instructions). Works
  across Claude Code and other tools; `npx skills add` installs whole
  directories. The fork's `skills/nurb/SKILL.md` already conforms.
- **Claude Code subagents**: separate context window, custom system prompt,
  restricted tools, independent permissions. Built-ins include Explore
  (read-only) and Plan (research). Use for side research that would
  otherwise flood the main conversation.
- **Codex**: the app already provisions the Codex ACP adapter; Codex reads
  `AGENTS.md` at repo root for instructions. The fork keeps its
  maintainer instructions in `docs/windows/` and the user-facing skill in
  `agents.md`; both are reachable from any harness that reads the repo.
The fork's maintenance knowledge is already machine-addressable (gates,
docs, checklist). The only genuinely useful additions are the two personal
items above, because they remove repeated model reasoning, which is exactly
the cost a deterministic or on-demand mechanism should remove.
