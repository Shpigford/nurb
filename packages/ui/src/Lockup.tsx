import { brand } from "./brand"

// The horizontal lockup, shipped as outlines so it never depends on the font
// (DESIGN.md §9). 65×18 in app headers, 87×24 on auth panels.
export default function Lockup({
  size = "header",
  onNavigate,
}: {
  size?: "header" | "panel"
  onNavigate?: () => void
}) {
  const dims = size === "panel" ? "h-6 w-[87px]" : "h-[18px] w-[65px]"
  const img = <img src={brand.lockup} alt="nurb" className={`${dims} shrink-0`} />
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
