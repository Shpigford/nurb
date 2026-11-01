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
