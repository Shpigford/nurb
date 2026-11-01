import { motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import Button from "./Button"
import { duration, ease } from "./motion/tokens"

// motion's types want a tuple; ease.out is a plain number[].
const OUT = ease.out as [number, number, number, number]

// Sheet 28: a downloaded update, offered as a small floating card where the
// version lives. The caller positions it; while installing, Later goes away.
export default function UpdateCard({
  version,
  installing = false,
  onLater,
  onInstall,
  className,
}: {
  version: string
  installing?: boolean
  onLater?: () => void
  onInstall: () => void
  className?: string
}) {
  const reduced = useReducedMotion() === true
  // It arrives over the rail footer rather than appearing on it, and it is the one
  // card that never makes a sound.
  const rise = reduced
    ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } }
    : { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 8 } }
  return (
    <motion.div
      {...rise}
      transition={{ duration: reduced ? 0 : duration.settle, ease: OUT }}
      className={clsx("panel flex w-[260px] flex-col gap-2 p-4", className)}
      role="status"
    >
      <span className="mono-caption text-muted">Update</span>
      <div className="flex flex-col gap-1">
        <h2 className="font-display text-[15px] leading-5 tracking-[-0.02em] text-ink">nurb {version} is ready</h2>
        <p className="text-[13px] leading-[18px] text-muted">
          {installing ? "Closing and reopening nurb." : "Downloaded. Restart to finish."}
        </p>
      </div>
      <div className="mt-1 flex items-center gap-2">
        {installing || !onLater ? null : (
          <Button variant="outline" onClick={onLater}>
            Later
          </Button>
        )}
        <Button variant="accent" disabled={installing} onClick={onInstall}>
          {installing ? "Restarting…" : "Restart now"}
        </Button>
      </div>
    </motion.div>
  )
}
