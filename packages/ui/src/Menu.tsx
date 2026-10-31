import {
  Fragment,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
  type RefObject,
} from "react"
import { createPortal } from "react-dom"
import { AnimatePresence, motion, usePresence } from "motion/react"
import clsx from "clsx"
import Icon, { type IconName } from "./Icon"
import { duration, ease } from "./motion/tokens"

// motion's types want a tuple; ease.out is a plain number[].
const OUT = ease.out as [number, number, number, number]

// A "…" trigger and its popover. One component serves the library's project
// rows and part cards. Escape closes and hands focus back to the trigger.
export interface MenuItem {
  label: ReactNode
  onSelect: () => void
  icon?: IconName
  tone?: "default" | "danger"
  /** A rule above this item (Sign out sits alone under one). */
  separated?: boolean
  /** A radio-style menu: the checked item carries a check, the rest keep the slot. */
  checked?: boolean
  /** A hint at the row's end (a "sign in" pill, a model's note). */
  trailing?: ReactNode
  /** Eyebrow above this item; consecutive items with the same section share one. */
  section?: string
  /** The menu stays open after this pick (a choice with more to choose after it). */
  keepOpen?: boolean
  disabled?: boolean
  /** Hover text, for a note too long to sit in the row. */
  title?: string
}

export default function Menu({
  label,
  items,
  align = "right",
  className,
  menuClassName,
  trigger,
  footer,
  portal,
  disabled,
  triggerClassName,
  onOpenChange,
}: {
  label: string
  items: MenuItem[]
  align?: "left" | "right"
  className?: string
  menuClassName?: string
  /** Replaces the "…" glyph; the button chrome stays. */
  trigger?: (open: boolean) => ReactNode
  /** A well under the items (the note about what a choice costs). */
  footer?: ReactNode
  /** Render the popover on document.body, fixed under the trigger, so a
   * clipping ancestor (the header's overflow-hidden) cannot cut it off. */
  portal?: boolean
  disabled?: boolean
  /** Fires on every open and close, for an owner that commits a choice when the menu goes away. */
  onOpenChange?: (open: boolean) => void
  /** Replaces the trigger's own size and shape classes; the chrome and focus ring stay. */
  triggerClassName?: string
}) {
  const [open, setOpen] = useState(false)
  const [anchor, setAnchor] = useState<CSSProperties>()
  const rootRef = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const id = useId()
  const checkable = items.some((item) => item.checked !== undefined)
  const openChange = useRef(onOpenChange)
  openChange.current = onOpenChange
  useEffect(() => {
    openChange.current?.(open)
  }, [open])

  useLayoutEffect(() => {
    if (!open || !portal) return
    const rect = triggerRef.current?.getBoundingClientRect()
    if (!rect) return
    setAnchor(
      align === "right"
        ? {
            position: "fixed",
            top: rect.bottom + 4,
            right: window.innerWidth - rect.right,
          }
        : { position: "fixed", top: rect.bottom + 4, left: rect.left },
    )
  }, [open, portal, align])

  useEffect(() => {
    if (!open) return
    const onPointerDown = (e: PointerEvent) => {
      const target = e.target as Node
      if (!rootRef.current?.contains(target) && !menuRef.current?.contains(target)) setOpen(false)
    }
    const onKeyDown = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false)
        triggerRef.current?.focus()
      }
    }
    document.addEventListener("pointerdown", onPointerDown)
    document.addEventListener("keydown", onKeyDown)
    return () => {
      document.removeEventListener("pointerdown", onPointerDown)
      document.removeEventListener("keydown", onKeyDown)
    }
  }, [open])

  return (
    <div ref={rootRef} className={clsx("relative", className)}>
      <button
        ref={triggerRef}
        type="button"
        aria-label={label}
        title={label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={id}
        disabled={disabled}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setOpen((v) => !v)
        }}
        // A row that handles keys (the library's project list) must not swallow the trigger's own.
        onKeyDown={(e) => e.stopPropagation()}
        className={clsx(
          "chrome inline-flex items-center justify-center rounded-[3px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          triggerClassName ?? (trigger ? "rounded-full" : "size-5"),
          !trigger && (open ? "bg-raised text-ink" : "text-muted hover:bg-raised hover:text-ink"),
        )}
      >
        {trigger ? trigger(open) : <Icon name="dots" />}
      </button>
      {portalize(
        portal,
        <AnimatePresence>
          {open ? (
            <Popover
              id={id}
              ref={menuRef}
              style={portal ? anchor : undefined}
              className={clsx(
                "z-30 min-w-[168px] overflow-hidden rounded-[6px] border border-panel-edge bg-ground shadow-[var(--shadow-panel)]",
                footer ? "pt-1" : "py-1",
                !portal && "absolute top-full mt-1",
                !portal && (align === "right" ? "right-0" : "left-0"),
                menuClassName,
              )}
            >
              {items.map((item, index) => (
                <Fragment key={index}>
                  {item.section && item.section !== items[index - 1]?.section ? (
                    <>
                      {index > 0 ? (
                        <div className="my-1 border-t border-line-soft" role="separator" />
                      ) : null}
                      <div className="flex h-6 items-center px-3 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase">
                        {item.section}
                      </div>
                    </>
                  ) : null}
                  <button
                    type="button"
                    role={checkable ? "menuitemradio" : "menuitem"}
                    aria-checked={checkable ? Boolean(item.checked) : undefined}
                    disabled={item.disabled}
                    title={item.title}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      item.onSelect()
                      if (!item.keepOpen) setOpen(false)
                    }}
                    className={clsx(
                      "chrome mono-id flex h-7 w-full items-center gap-2 px-3 text-left transition-colors focus-visible:bg-raised focus-visible:outline-none disabled:text-faint disabled:hover:bg-transparent",
                      item.separated && "mt-1 border-t border-line-soft pt-px",
                      item.tone === "danger"
                        ? "text-fail hover:bg-fail-wash"
                        : item.checked
                          ? "text-ink hover:bg-raised"
                          : "text-ink-soft hover:bg-raised hover:text-ink",
                    )}
                  >
                    {checkable ? (
                      <span className="flex size-3 shrink-0 items-center justify-center">
                        {item.checked ? <Icon name="check" /> : null}
                      </span>
                    ) : null}
                    {item.icon ? <Icon name={item.icon} /> : null}
                    <span className="min-w-0 flex-1 truncate">{item.label}</span>
                    {item.trailing ? <span className="shrink-0">{item.trailing}</span> : null}
                  </button>
                </Fragment>
              ))}
              {footer ? (
                <div className="mt-1 border-t border-line-soft bg-raised px-3 py-2 font-mono text-[9.5px] leading-3 tracking-[0.08em] text-muted uppercase">
                  {footer}
                </div>
              ) : null}
            </Popover>
          ) : null}
        </AnimatePresence>,
      )}
    </div>
  )
}

// The popover stops being a menu the moment it closes, so a screen reader and
// `getByRole("menu")` both lose it at once while the fade plays itself out.
function Popover({
  id,
  ref,
  style,
  className,
  children,
}: {
  id: string
  ref: RefObject<HTMLDivElement | null>
  style?: CSSProperties
  className?: string
  children: ReactNode
}) {
  const [present] = usePresence()
  return (
    <motion.div
      id={id}
      ref={ref}
      role={present ? "menu" : "presentation"}
      aria-hidden={present ? undefined : true}
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: duration.tick, ease: OUT }}
      style={style}
      className={className}
    >
      {children}
    </motion.div>
  )
}

function portalize(portal: boolean | undefined, node: ReactNode) {
  return portal && typeof document !== "undefined" ? createPortal(node, document.body) : node
}
