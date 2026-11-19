import type { Part, ProjectMeasurement } from "./api"

// A fit test is a small part named after the long one with `_fit_test` on the end,
// reading the same measurements. The doctrine tells the agent to name it that way.
const SUFFIX = "_fit_test"

// Under an hour the part is its own fit test, so the nudge stays quiet.
export const LONG_PRINT_S = 60 * 60

export const isFitTest = (name: string) => name.endsWith(SUFFIX)

/** The measurements this part reads that nobody has printed yet. */
export function untested(part: Part, measurements: ProjectMeasurement[]): string[] {
  const guesses = new Set(measurements.filter((m) => m.provisional).map((m) => m.name))
  return (part.measures ?? []).filter((name) => guesses.has(name))
}

/** The fit test for a part: its `_fit_test` twin first, else one that reads a fit it still owes. */
export function fitTestFor(part: Part, parts: Part[], owed: string[]): Part | null {
  const tests = parts.filter(
    (p) => p.name !== part.name && isFitTest(p.name) && p.measures?.some((name) => owed.includes(name)),
  )
  return tests.find((p) => p.name === part.name + SUFFIX) ?? tests[0] ?? null
}

/** The part a fit test was made for, when it is still in the project. */
export function parentOf(test: Part, parts: Part[]): Part | null {
  const name = test.name.slice(0, -SUFFIX.length)
  return parts.find((p) => p.name === name) ?? null
}
