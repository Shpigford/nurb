import { useEffect, useRef, useState, type ComponentProps } from "react"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import Button from "./Button"
import { cue } from "./sound"
import { useAutoHeight } from "./motion/useAutoHeight"
import { duration, ease } from "./motion/tokens"

// The agent can stack up several asks in one turn. Showing them all at once reads
// as a wall of buttons, so the card shows the one in hand and says how many are
// behind it. Answering moves the queue up rather than closing and reopening a card.

const OUT = ease.out as [number, number, number, number]

export interface ApprovalAction {
  id: string
  label: string
  variant?: ComponentProps<typeof Button>["variant"]
}

export interface ApprovalQuestion {
  id: string | number
  title: string
  detail?: string
  actions: ApprovalAction[]
}

/** One digit, rolling the way a mechanical counter does: up and out, up and in. */
function Roll({ value }: { value: number }) {
  const reduced = useReducedMotion() === true
  return (
    <span className="relative inline-flex h-[13px] overflow-hidden leading-[13px] tabular-nums">
      <AnimatePresence initial={false} mode="popLayout">
        <motion.span
          key={value}
          initial={reduced ? { opacity: 0 } : { y: 13, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={reduced ? { opacity: 0 } : { y: -13, opacity: 0 }}
          transition={{ duration: reduced ? 0 : duration.tick, ease: OUT }}
        >
          {value}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}

export default function ApprovalCard({
  questions,
  onAnswer,
  className,
}: {
  /** The asks still waiting. The owner drops one when it is answered or withdrawn. */
  questions: ApprovalQuestion[]
  onAnswer: (questionId: ApprovalQuestion["id"], actionId: string) => void
  className?: string
}) {
  // Counted here, not derived from the list: the total has to hold still while the
  // queue drains, or "1 of 3" would read "1 of 2" the moment it was answered.
  const [answered, setAnswered] = useState(0)
  const announced = useRef(false)
  const waiting = questions.length

  useEffect(() => {
    if (waiting === 0) {
      // The queue drained. A later turn's asks are a new card, counted from one
      // and announced again, rather than "4 of 5" out of nowhere.
      announced.current = false
      setAnswered(0)
      return
    }
    if (announced.current) return
    announced.current = true
    cue("scan")
  }, [waiting])

  const h = useAutoHeight(true)
  const current = questions[0]
  if (!current) return null

  const total = answered + waiting
  const index = Math.min(answered + 1, total)

  const answer = (actionId: string) => {
    setAnswered((n) => n + 1)
    onAnswer(current.id, actionId)
  }

  return (
    <div className={clsx("flex flex-col gap-2.5 rounded-[6px] bg-raised p-3", className)}>
      {total > 1 ? (
        <div className="flex items-center gap-1">
          <span aria-hidden="true" className="mono-caption flex items-center gap-1 text-faint">
            <Roll value={index} />
            of {total}
          </span>
          <span className="sr-only">Question {index} of {total}</span>
        </div>
      ) : null}
      <motion.div style={h.style} animate={h.animate} transition={h.transition} onAnimationComplete={h.onAnimationComplete}>
        <div ref={h.ref}>
          <AnimatePresence initial={false} mode="popLayout">
            <motion.div
              key={current.id}
              initial={{ y: 12, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: duration.settle, ease: OUT }}
              className="flex flex-col gap-2.5"
            >
              <p className="text-chat text-ink">{current.title}</p>
              {current.detail ? <p className="mono-caption text-muted">{current.detail}</p> : null}
              <div className="flex flex-wrap gap-1.5">
                {current.actions.map((action) => (
                  <Button key={action.id} variant={action.variant ?? "outline"} onClick={() => answer(action.id)}>
                    {action.label}
                  </Button>
                ))}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  )
}
