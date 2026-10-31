import { useEffect, useRef, type ReactNode } from "react"
import { motion } from "motion/react"
import Button from "./Button"
import HoldToConfirm from "./motion/HoldToConfirm"
import { duration, ease } from "./motion/tokens"

// The one confirmation in the app, for anything that cannot be undone. Native
// <dialog> gives us the top layer, Escape and focus containment for free.
// Mount it to open it; Cancel takes focus first so a stray Enter deletes
// nothing.

// motion's types want a tuple; ease.out is a plain number[].
const OUT = ease.out as [number, number, number, number]

export default function ConfirmDialog({
  title,
  children,
  confirmLabel = "Delete",
  hold = false,
  onConfirm,
  onCancel,
}: {
  title: string
  children: ReactNode
  confirmLabel?: string
  /** Press and hold to confirm, for a delete with no undo behind it. */
  hold?: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  const ref = useRef<HTMLDialogElement>(null)
  const cancelRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    ref.current?.showModal()
    cancelRef.current?.focus()
  }, [])

  return (
    <motion.dialog
      ref={ref}
      aria-labelledby="confirm-title"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: duration.settle, ease: OUT }}
      onCancel={(e) => {
        e.preventDefault()
        onCancel()
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel()
      }}
      // The scrim fades on its own, because ::backdrop is not ours to animate from script.
      className="panel m-auto w-[320px] max-w-[calc(100vw-32px)] p-0 text-ink backdrop:bg-ink/30 backdrop:transition-colors backdrop:duration-[240ms] starting:backdrop:bg-ink/0"
    >
      <div className="flex flex-col gap-1.5 px-4 pt-4 pb-3.5">
        <h2 id="confirm-title" className="font-display text-[16px] leading-5 font-bold tracking-[-0.02em] text-ink">
          {title}
        </h2>
        <p className="text-xs leading-4 text-muted">{children}</p>
      </div>
      <div className="flex justify-end gap-1.5 border-t border-line-soft px-4 py-3">
        <Button ref={cancelRef} variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        {hold ? (
          <HoldToConfirm label={confirmLabel} confirmLabel="Done" holdMs={1200} onConfirm={onConfirm} />
        ) : (
          <Button variant="danger" onClick={onConfirm}>
            {confirmLabel}
          </Button>
        )}
      </div>
    </motion.dialog>
  )
}
