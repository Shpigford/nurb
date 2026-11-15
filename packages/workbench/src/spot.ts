type Vec3 = [number, number, number]

const mm = (v: number) => String(Math.round(v * 10) / 10)

// Which way the clicked face points, in words a person reads and an agent can act on.
function facing([x, y, z]: Vec3): string {
  if (Math.abs(z) > 0.9) return z > 0 ? "a face pointing up" : "a face pointing down"
  if (Math.abs(x) > 0.9) return `a side face pointing ${x > 0 ? "+" : "-"}X`
  if (Math.abs(y) > 0.9) return `a side face pointing ${y > 0 ? "+" : "-"}Y`
  return "a sloped face"
}

/** The sentence a click on the part drops into the chat, ahead of whatever the person asks. */
export function spotText(point: Vec3, normal: Vec3): string {
  return `This spot on the part: ${point.map(mm).join(", ")} mm, on ${facing(normal)}.`
}

const SPOT_LINE = /^This spot on the part: (.+) mm, on .+\.$/

/** Where a spot sentence sits, as the chip shows it, or null for any other line. */
export function spotPlace(line: string): string | null {
  return SPOT_LINE.exec(line.trim())?.[1] ?? null
}

/** A message split into its spot sentences, which show as chips, and the words the person typed. */
export function splitSpots(text: string): { spots: string[]; rest: string } {
  const spots: string[] = []
  const rest: string[] = []
  for (const line of text.split("\n")) (spotPlace(line) ? spots : rest).push(line)
  return { spots: spots.map((line) => line.trim()), rest: rest.join("\n").trim() }
}

/** The spots ahead of the typed words: the agent reads them as one message. */
export function joinSpots(spots: string[], text: string): string {
  return [...spots, text].filter(Boolean).join("\n")
}
