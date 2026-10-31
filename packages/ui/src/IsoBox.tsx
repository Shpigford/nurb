// A flat-shaded isometric box in the part palette, sized from a build's
// bounding box (DESIGN.md §7). The library has no thumbnail renderer yet; a
// box drawn from the real dimensions is honest, and reads as a part at a glance.
// Projection: sx = (x − y) · 0.866, sy = (x + y) · 0.5 − z.

interface IsoBoxProps {
  /** [x, y, z] in mm. Missing or degenerate → a ghost outline. */
  bbox?: number[] | null
  ghost?: boolean
  className?: string
}

const W = 240
const H = 148

function project(x: number, y: number, z: number) {
  return [(x - y) * 0.866, (x + y) * 0.5 - z] as const
}

export default function IsoBox({ bbox, ghost = false, className }: IsoBoxProps) {
  const dims = bbox && bbox.length === 3 && bbox.every((n) => n > 0) ? bbox : null
  // Normalise so the longest edge is 1, then scale to fit the well.
  const base = dims ?? [1, 1, 1]
  const longest = Math.max(...base)
  const [x, y, z] = base.map((n) => n / longest)

  const corners = [
    project(0, 0, 0),
    project(x, 0, 0),
    project(x, y, 0),
    project(0, y, 0),
    project(0, 0, z),
    project(x, 0, z),
    project(x, y, z),
    project(0, y, z),
  ]
  const xs = corners.map((c) => c[0])
  const ys = corners.map((c) => c[1])
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const scale = Math.min((W - 60) / (maxX - minX), (H - 40) / (maxY - minY))
  const ox = W / 2 - ((minX + maxX) / 2) * scale
  const oy = H / 2 - ((minY + maxY) / 2) * scale
  const p = (i: number) => `${(corners[i][0] * scale + ox).toFixed(1)},${(corners[i][1] * scale + oy).toFixed(1)}`

  const top = `${p(4)} ${p(5)} ${p(6)} ${p(7)}`
  // The camera sits at (+,+,+): the +y face lands front-left, the +x face front-right.
  const front = `${p(3)} ${p(2)} ${p(6)} ${p(7)}`
  const side = `${p(1)} ${p(2)} ${p(6)} ${p(5)}`
  const shadowCx = W / 2
  const shadowCy = Math.max(...corners.map((c) => c[1])) * scale + oy + 6
  const shadowRx = ((maxX - minX) * scale) / 2 + 8

  if (ghost || !dims) {
    return (
      <svg viewBox={`0 0 ${W} ${H}`} className={className} aria-hidden="true">
        <g fill="none" stroke="var(--color-panel-edge)" strokeWidth="1.5" strokeLinejoin="round" strokeDasharray="5 4">
          <polygon points={top} />
          <polygon points={front} />
          <polygon points={side} />
        </g>
      </svg>
    )
  }

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className={className} aria-hidden="true">
      <ellipse cx={shadowCx} cy={shadowCy} rx={shadowRx} ry={shadowRx * 0.16} fill="var(--color-raised)" />
      <g stroke="var(--color-part-edge)" strokeWidth="1.2" strokeLinejoin="round">
        <polygon points={top} fill="var(--color-part-top)" />
        <polygon points={front} fill="var(--color-part-front)" />
        <polygon points={side} fill="var(--color-part-side)" />
      </g>
    </svg>
  )
}
