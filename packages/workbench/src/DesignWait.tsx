import { useEffect, useRef, useState } from "react"
import { TaskSteps, type Spec } from "@nurb/ui"
import type { ProjectMeasurement } from "./api"

// The stage while an agent plans a new part. Every agent thinks in silence for
// minutes before its first call, so the stage owes the person three things: what
// has really happened (the steps, read from what the agent has recorded), what to
// expect (the caption), and something to do meanwhile (the bed).

const LINES = [
  "The nozzle follows your cursor. It has nothing better to do yet.",
  "Measure twice, print once. Reprint once more for luck.",
  "No layers were harmed in the making of this plan.",
  "Somewhere, a spool is quietly running out.",
  "Stringing is just the printer waving goodbye.",
  "The bed is level. Probably.",
  "Drawing in mid-air is free. Plastic costs extra.",
]
const LINE_MS = 8_000

export function designSteps(spec: Spec | null | undefined, measurements: ProjectMeasurement[] | undefined) {
  const sizes = measurements?.length ?? 0
  const steps = [
    { id: "think", label: "Thinking it through" },
    { id: "sizes", label: "Noting the sizes", meta: sizes ? `${sizes} noted` : "none needed" },
    { id: "plan", label: "Pinning the plan" },
    { id: "build", label: "Building the first version" },
  ]
  return { steps, current: spec ? 3 : sizes ? 1 : 0 }
}

export default function DesignWait({
  designer,
  spec,
  measurements,
}: {
  designer: string
  spec: Spec | null | undefined
  measurements: ProjectMeasurement[] | undefined
}) {
  const { steps, current } = designSteps(spec, measurements)
  const [line, setLine] = useState(0)
  const [shown, setShown] = useState(true)
  useEffect(() => {
    // Fade out, swap, fade in: the line changes while nobody can read it.
    let swap: ReturnType<typeof setTimeout>
    const timer = setInterval(() => {
      setShown(false)
      swap = setTimeout(() => {
        setLine((n) => (n + 1) % LINES.length)
        setShown(true)
      }, 400)
    }, LINE_MS)
    return () => {
      clearInterval(timer)
      clearTimeout(swap)
    }
  }, [])

  return (
    <div className="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden p-4">
      <Bed />
      <div className="relative flex w-full max-w-[360px] flex-col items-center gap-4 rounded-[8px] border border-stage-line bg-stage/85 px-6 pt-5 pb-4 text-center backdrop-blur-[2px]">
        <p className="mono-label text-on-stage-muted">{designer} is designing this part</p>
        <div className="w-[230px] text-left">
          <TaskSteps steps={steps} current={current} label="Design progress" />
        </div>
        <p className="max-w-[36ch] text-[14px] leading-[20px] text-balance text-ink-soft">
          {designer} works out the whole part before building anything. That can take several minutes, and the first version shows up here soon after.
        </p>
        <p className={`min-h-[36px] w-full border-t border-stage-line pt-3 text-[12.5px] leading-[18px] text-balance text-on-stage-muted transition-opacity duration-400 ${shown ? "opacity-100" : "opacity-0"}`}>
          {LINES[line]}
        </p>
      </div>
    </div>
  )
}

const GRID = 24
const TRAIL_MS = 6_000

/** The whole stage as a print bed seen from above. The nozzle chases the pointer and wanders when left alone. */
function Bed() {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    const ctx = canvas?.getContext("2d")
    if (!canvas || !ctx) return
    let W = 0
    let H = 0
    const resize = () => {
      const dpr = window.devicePixelRatio || 1
      W = canvas.clientWidth
      H = canvas.clientHeight
      canvas.width = W * dpr
      canvas.height = H * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    resize()
    const sized = new ResizeObserver(resize)
    sized.observe(canvas)
    const still = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false

    const area = canvas.parentElement ?? canvas
    let pointer: { x: number; y: number; at: number } | null = null
    const onMove = (event: Event) => {
      const { clientX, clientY } = event as PointerEvent
      const box = canvas.getBoundingClientRect()
      pointer = { x: clientX - box.left, y: clientY - box.top, at: performance.now() }
    }
    area.addEventListener("pointermove", onMove)
    let colors = { line: "", accent: "", ink: "" }
    const readColors = () => {
      const css = getComputedStyle(canvas)
      colors = {
        line: css.getPropertyValue("--color-stage-line").trim() || "#888",
        accent: css.getPropertyValue("--color-accent").trim() || "#ff5230",
        ink: css.getPropertyValue("--color-ink").trim() || "#000",
      }
    }
    readColors()
    const theme = new MutationObserver(readColors)
    theme.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] })

    const nozzle = { x: W / 2, y: H / 3 }
    const trail: { x: number; y: number; at: number }[] = []
    let frame = 0

    const draw = (now: number) => {
      const wander = {
        x: W / 2 + Math.sin(now / 2300) * (W / 2 - 60) * Math.cos(now / 7100),
        y: H / 2 + Math.sin(now / 1500) * (H / 2 - 60),
      }
      const target = pointer && now - pointer.at < 2_500 ? pointer : wander
      nozzle.x += (target.x - nozzle.x) * 0.08
      nozzle.y += (target.y - nozzle.y) * 0.08
      const last = trail[trail.length - 1]
      if (!last || Math.hypot(last.x - nozzle.x, last.y - nozzle.y) > 1) trail.push({ ...nozzle, at: now })
      while (trail.length && now - trail[0].at > TRAIL_MS) trail.shift()

      ctx.clearRect(0, 0, W, H)
      ctx.globalAlpha = 1
      ctx.fillStyle = colors.line
      for (let x = GRID / 2; x < W; x += GRID) for (let y = GRID / 2; y < H; y += GRID) ctx.fillRect(x - 1, y - 1, 2, 2)

      // Filament cools as it ages: hot accent at the nozzle, fading to nothing.
      ctx.strokeStyle = colors.accent
      ctx.lineWidth = 2.5
      ctx.lineCap = "round"
      for (let i = 1; i < trail.length; i++) {
        ctx.globalAlpha = Math.max(0, 1 - (now - trail[i].at) / TRAIL_MS) * 0.9
        ctx.beginPath()
        ctx.moveTo(trail[i - 1].x, trail[i - 1].y)
        ctx.lineTo(trail[i].x, trail[i].y)
        ctx.stroke()
      }

      ctx.globalAlpha = 1
      ctx.strokeStyle = colors.ink
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.arc(nozzle.x, nozzle.y, 6, 0, Math.PI * 2)
      ctx.stroke()
      ctx.fillStyle = colors.accent
      ctx.beginPath()
      ctx.arc(nozzle.x, nozzle.y, 2, 0, Math.PI * 2)
      ctx.fill()

      if (!still) frame = requestAnimationFrame(draw)
    }
    frame = requestAnimationFrame(draw)

    return () => {
      cancelAnimationFrame(frame)
      theme.disconnect()
      sized.disconnect()
      area.removeEventListener("pointermove", onMove)
    }
  }, [])

  return <canvas ref={ref} aria-hidden="true" className="absolute inset-0 size-full" />
}
