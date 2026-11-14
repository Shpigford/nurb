import lockupSvg from "../brand/nurb-lockup.svg?raw"

// The horizontal lockup, shipped as outlines so it never depends on the font. Inlined
// rather than an <img> so the wordmark takes the ink colour, which turns over in dark.
const markup = lockupSvg
  .replace('fill="#121821"', 'fill="currentColor"')
  .replace(/width="[\d.]+" height="[\d.]+"/, 'width="100%" height="100%"')

// 65×18 in app headers, 87×24 where it stands on its own.
export default function Lockup({
  size = "header",
  onNavigate,
}: {
  size?: "header" | "panel"
  onNavigate?: () => void
}) {
  const dims = size === "panel" ? "h-6 w-[87px]" : "h-[18px] w-[65px]"
  const img = (
    <span
      role="img"
      aria-label="nurb"
      className={`${dims} shrink-0 text-ink`}
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  )
  if (!onNavigate) return <div className="inline-flex">{img}</div>
  return (
    <button
      type="button"
      onClick={onNavigate}
      className="inline-flex rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent"
    >
      {img}
    </button>
  )
}
