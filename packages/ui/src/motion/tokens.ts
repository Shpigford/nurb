// The CSS tokens in tokens.css, in the units motion wants. Keep the two in step:
// a CSS transition and a motion transition on the same element must agree, or the
// element moves twice at two speeds.

/** Seconds, because motion's `transition` prop is in seconds while CSS is in ms. */
export const duration = {
  tick: 0.09,
  settle: 0.24,
  arrive: 0.42,
  coast: 1.4,
} as const

/** Cubic-bezier control points, shaped like motion's own BezierDefinition. */
type Bezier = readonly [number, number, number, number]

export const ease = {
  out: [0.23, 1, 0.32, 1],
  inOut: [0.65, 0, 0.35, 1],
} as const satisfies Record<string, Bezier>
