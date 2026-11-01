import type { Verdict } from "@nurb/ui"
import type { PartBuild } from "./api"

export type { Verdict }

export function verdictOf(build: PartBuild | null | undefined): Verdict {
  if (!build) return "none"
  if (build.status === "error") return "fail"
  const findings = build.findings ?? []
  if (!build.passed || findings.some((f) => f.severity === "fail")) return "fail"
  if (findings.length > 0) return "warn"
  return "pass"
}

export function verdictCaption(verdict: Verdict, build: PartBuild | null | undefined): string {
  if (verdict === "none") return "Not built yet"
  if (build && build.status === "error") return "Build failed"
  if (verdict === "pass") return "Checks pass at these numbers"
  return "Checks found something to fix"
}

export function verdictDot(verdict: Verdict): string {
  if (verdict === "fail") return "bg-fail"
  if (verdict === "warn") return "bg-warn"
  if (verdict === "pass") return "bg-pass"
  return "bg-line"
}
