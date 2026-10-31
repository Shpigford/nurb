// `?no-inline` because a lib build inlines every asset as a data URI by
// default, and the 36 kB auth plane has no business riding inside index.js.
import lockup from "../brand/nurb-lockup.svg?no-inline"
import mark from "../brand/nurb-mark-16.svg?no-inline"
import markOutline from "../brand/nurb-mark-outline.svg?no-inline"
import markSmall from "../brand/nurb-mark-small.svg?no-inline"
import favicon from "../brand/favicon.svg?no-inline"
import authPlane from "../brand/auth-plane.svg?no-inline"
import ghostBracket from "../brand/ghost-bracket.svg?no-inline"
import squiggle from "../brand/404-squiggle.svg?no-inline"

// The brand marks as URLs, so a consumer points at them instead of copying the
// files into its own public directory and letting the two drift.
export const brand = { lockup, mark, markOutline, markSmall, favicon, authPlane, ghostBracket, squiggle } as const
