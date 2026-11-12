import {
  Fragment,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type MouseEvent,
  type ReactNode,
  type RefObject,
} from "react"
import { createPortal } from "react-dom"
import { AnimatePresence, motion, useIsPresent } from "motion/react"
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
  /** An on/off row that toggles on its own, beside others that do too. */
  checkbox?: boolean
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
  above,
  className,
  menuClassName,
  trigger,
  footer,
  portal,
  disabled,
  triggerClassName,
  onOpenChange,
  filter,
}: {
  label: string
  items: MenuItem[]
  align?: "left" | "right"
  /** Open upward, for a trigger near the bottom of the window. */
  above?: boolean
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
  /** A find field above the items, with this placeholder, for a list too long to scan. */
  filter?: string
}) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [anchor, setAnchor] = useState<CSSProperties>()
  const rootRef = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const id = useId()
  const openChange = useRef(onOpenChange)
  openChange.current = onOpenChange
  useEffect(() => {
    openChange.current?.(open)
    if (!open) setQuery("")
  }, [open])
  const needle = query.trim().toLowerCase()
  const shown = needle
    ? items.filter((item) => typeof item.label === "string" && item.label.toLowerCase().includes(needle))
    : items

  useLayoutEffect(() => {
    if (!open || !portal) return
    const rect = triggerRef.current?.getBoundingClientRect()
    if (!rect) return
    setAnchor({
      position: "fixed",
      ...(above ? { bottom: window.innerHeight - rect.top + 4 } : { top: rect.bottom + 4 }),
      ...(align === "right" ? { right: window.innerWidth - rect.right } : { left: rect.left }),
    })
  }, [open, portal, align, above])

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
                !portal && (above ? "absolute bottom-full mb-1" : "absolute top-full mt-1"),
                !portal && (align === "right" ? "right-0" : "left-0"),
                menuClassName,
              )}
            >
              {filter ? (
                <div className="sticky top-0 z-10 -mt-1 mb-1 flex h-8 items-center gap-2 border-b border-line-soft bg-ground px-3">
                  <Icon name="search" className="text-muted" />
                  <input
                    autoFocus
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      // Enter takes the first match, so a typed name is one keystroke from open.
                      if (e.key === "Enter" && shown[0]) {
                        shown[0].onSelect()
                        setOpen(false)
                      }
                    }}
                    placeholder={filter}
                    aria-label={filter}
                    className="mono-id min-w-0 flex-1 bg-transparent text-ink outline-none placeholder:text-faint"
                  />
                </div>
              ) : null}
              {filter && shown.length === 0 ? (
                <div className="mono-id flex h-7 items-center px-3 text-faint">Nothing matches</div>
              ) : null}
              <MenuRows
                items={shown}
                onPick={(item) => {
                  item.onSelect()
                  if (!item.keepOpen) setOpen(false)
                }}
              />
              {footer ? (
                <div className="sticky bottom-0 mt-1 border-t border-line-soft bg-raised px-3 py-2 font-mono text-[9.5px] leading-3 tracking-[0.08em] text-muted uppercase">
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

// The same rows, opened by a right-click at the pointer. Call `open` from the
// onContextMenu of the thing the menu is about, and render `menu` once anywhere;
// it portals to the body, so one hook serves a whole list.
export function useContextMenu() {
  const [at, setAt] = useState<{ x: number; y: number; items: MenuItem[] } | null>(null)
  const [style, setStyle] = useState<CSSProperties>()
  const menuRef = useRef<HTMLDivElement>(null)
  const id = useId()

  // Placed after it renders, so a click near the window's edge opens the menu inward.
  useLayoutEffect(() => {
    if (!at || !menuRef.current) return
    const { width, height } = menuRef.current.getBoundingClientRect()
    setStyle({
      position: "fixed",
      left: Math.max(8, Math.min(at.x, window.innerWidth - width - 8)),
      top: Math.max(8, Math.min(at.y, window.innerHeight - height - 8)),
    })
  }, [at])

  useEffect(() => {
    if (!at) return
    const close = (e: Event) => {
      if (!menuRef.current?.contains(e.target as Node)) setAt(null)
    }
    const onKeyDown = (e: globalThis.KeyboardEvent) => e.key === "Escape" && setAt(null)
    const onBlur = () => setAt(null)
    document.addEventListener("pointerdown", close, true)
    document.addEventListener("keydown", onKeyDown)
    window.addEventListener("blur", onBlur)
    window.addEventListener("scroll", onBlur, true)
    return () => {
      document.removeEventListener("pointerdown", close, true)
      document.removeEventListener("keydown", onKeyDown)
      window.removeEventListener("blur", onBlur)
      window.removeEventListener("scroll", onBlur, true)
    }
  }, [at])

  const open = (e: MouseEvent, items: MenuItem[] | undefined) => {
    if (!items?.length) return
    e.preventDefault()
    e.stopPropagation()
    setStyle({ position: "fixed", left: e.clientX, top: e.clientY, visibility: "hidden" })
    setAt({ x: e.clientX, y: e.clientY, items })
  }

  const menu = portalize(
    true,
    <AnimatePresence>
      {at ? (
        <Popover
          id={id}
          ref={menuRef}
          style={style}
          className="z-30 min-w-[168px] overflow-hidden rounded-[6px] border border-panel-edge bg-ground py-1 shadow-[var(--shadow-panel)]"
        >
          <MenuRows
            items={at.items}
            onPick={(item) => {
              item.onSelect()
              if (!item.keepOpen) setAt(null)
            }}
          />
        </Popover>
      ) : null}
    </AnimatePresence>,
  )

  return { open, menu }
}

// The rows themselves, shared by the "…" menu and the right-click one.
function MenuRows({ items, onPick }: { items: MenuItem[]; onPick: (item: MenuItem) => void }) {
  const checkable = items.some((item) => item.checked !== undefined)
  return (
    <>
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
            role={item.checkbox ? "menuitemcheckbox" : checkable ? "menuitemradio" : "menuitem"}
            aria-checked={checkable ? Boolean(item.checked) : undefined}
            disabled={item.disabled}
            title={item.title}
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onPick(item)
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
    </>
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
  // useIsPresent, not usePresence: the latter holds the node until a safeToRemove
  // nobody calls, which left every closed menu on the page, invisible and catching clicks.
  const present = useIsPresent()
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
