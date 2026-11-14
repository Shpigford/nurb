import { useEffect, useLayoutEffect, useRef, useState } from "react"
import { motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import Icon from "../Icon"
import { duration, ease } from "./tokens"

// Ported from interior.dev (MIT) and restyled onto the nurb tokens. The box is
// reserved from width and height, so a caption under a photo sits in its final
// position before a byte arrives, and the frame keeps that space when the URL is
// dead instead of collapsing the page.

const OUT = ease.out as [number, number, number, number]
const INSTANT = { duration: 0 } as const

export type BlurUpStatus = "loading" | "ready" | "error"

const useIsoLayoutEffect = typeof window === "undefined" ? useEffect : useLayoutEffect

export function useBlurUpImage({
  src,
  onReady,
  onError,
}: {
  src?: string
  onReady?: () => void
  onError?: () => void
}) {
  const ref = useRef<HTMLImageElement>(null)
  const [state, setState] = useState<{ status: BlurUpStatus; instant: boolean }>({ status: "loading", instant: false })

  const ready = useRef(onReady)
  ready.current = onReady
  const failed = useRef(onError)
  failed.current = onError

  useIsoLayoutEffect(() => {
    const img = ref.current
    const set = (status: BlurUpStatus, instant: boolean) =>
      setState((prev) => (prev.status === status && prev.instant === instant ? prev : { status, instant }))

    if (!img || !src) {
      set("loading", false)
      return
    }

    let alive = true
    // A cached image is caught before paint and revealed instantly, so it never
    // flashes its own placeholder or plays a fade nobody asked for.
    const cached = img.complete && img.naturalWidth > 0

    const reveal = () => {
      if (!alive) return
      set("ready", cached)
      ready.current?.()
    }
    const fail = () => {
      if (!alive) return
      set("error", cached)
      failed.current?.()
    }

    if (img.complete) {
      if (cached) reveal()
      else fail()
      return () => {
        alive = false
      }
    }

    set("loading", false)
    img.addEventListener("load", reveal)
    img.addEventListener("error", fail)
    return () => {
      alive = false
      img.removeEventListener("load", reveal)
      img.removeEventListener("error", fail)
    }
  }, [src])

  return { ref, status: state.status, instant: state.instant, loaded: state.status === "ready" }
}

export default function BlurUpImage({
  src,
  alt,
  width,
  height,
  placeholder = "var(--color-accent-wash)",
  blur = 14,
  sizes,
  loading = "lazy",
  onReady,
  onError,
  className,
}: {
  src?: string
  /** Lives on the real image for the whole lifecycle, so the description is available before the bytes are. */
  alt: string
  width: number
  height: number
  /** The colour under everything, held while the photo resolves. */
  placeholder?: string
  blur?: number
  sizes?: string
  loading?: "lazy" | "eager"
  onReady?: () => void
  onError?: () => void
  className?: string
}) {
  const reduced = useReducedMotion() === true
  const { ref, status, instant } = useBlurUpImage({ src, onReady, onError })

  const shown = status === "ready"
  const still = reduced || instant
  const transition = still ? INSTANT : { duration: duration.arrive, ease: OUT }

  return (
    <div
      aria-busy={status === "loading"}
      data-status={status}
      style={{ aspectRatio: `${width} / ${height}`, backgroundColor: placeholder }}
      className={clsx("relative w-full overflow-hidden rounded-[6px]", className)}
    >
      <motion.img
        ref={ref}
        src={src}
        sizes={sizes}
        alt={alt}
        width={width}
        height={height}
        loading={loading}
        decoding="async"
        draggable={false}
        className="absolute inset-0 size-full object-cover"
        initial={false}
        // Only opacity and scale animate once sharp: an animated filter repaints the whole image every frame.
        animate={
          // The instant path clears the blur too: a src swapped back to a cached image
          // lands here straight from the loading pose, and would otherwise keep it.
          still
            ? { opacity: shown ? 1 : 0, filter: "blur(0px)", scale: 1 }
            : shown
              ? { opacity: 1, filter: "blur(0px)", scale: 1 }
              : { opacity: 0, filter: `blur(${blur}px)`, scale: 1.06 }
        }
        transition={transition}
      />

      {status === "error" ? (
        <div aria-hidden="true" className="absolute inset-0 grid place-items-center bg-raised text-faint">
          <Icon name="image" />
        </div>
      ) : null}
    </div>
  )
}
