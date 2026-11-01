import { useEffect, useRef, type RefObject } from "react"
import clsx from "clsx"
import Icon from "../Icon"
import Floating from "../layout/Floating"

/** One machine on the bench, as the menu needs to name it. */
export interface PrinterOption {
  name: string
  label: string
}

export interface PrinterMenuProps {
  printers: PrinterOption[]
  /** The machine this part prices against right now. */
  current: string | null
  /** The machine every new part starts on. */
  defaultName?: string | null
  onPick: (name: string) => void
  onAdd: () => void
  /** Only the app has a Settings screen, so the footer is only there. */
  onManage?: () => void
  /** The control that opened the menu: what it is placed from, and the one
   * pointer target that must not close it, because that click already toggles. */
  triggerRef: RefObject<HTMLElement | null>
  onClose: () => void
}

// The picker behind CHANGE. It opens upward, because the SLICE row sits at the
// foot of the rail and a menu that opened down would fall off the panel.
export default function PrinterMenu({
  printers,
  current,
  defaultName,
  onPick,
  onAdd,
  onManage,
  triggerRef,
  onClose,
}: PrinterMenuProps) {
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node
      if (rootRef.current?.contains(target)) return
      // The trigger toggles on click. Closing here as well would close and reopen
      // in one press, and CHANGE would never shut the menu.
      if (triggerRef.current?.contains(target)) return
      onClose()
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose()
    }
    document.addEventListener("pointerdown", onPointerDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("pointerdown", onPointerDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [onClose, triggerRef])

  // Portalled, because the SLICE row lives in a clipping scroller: an absolutely
  // placed menu opening upward out of it is cut to a few pixels of itself.
  return (
    <Floating
      ref={rootRef}
      anchor={triggerRef}
      width={254}
      align="right"
      gap={6}
      role="menu"
      aria-label="Print on"
      className="z-30 overflow-hidden rounded-[6px] border border-panel-edge bg-ground shadow-[var(--shadow-panel)]"
    >
      <div className="flex h-6 items-center justify-between px-3 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase">
        <span>Print on</span>
        <span>This part</span>
      </div>

      {printers.map((printer) => {
        const checked = printer.name === current
        return (
          <button
            key={printer.name}
            type="button"
            role="menuitemradio"
            aria-checked={checked}
            onClick={() => onPick(printer.name)}
            className={clsx(
              "chrome flex h-7 w-full items-center gap-2 px-3 text-left font-mono text-[10.5px] leading-4 transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none",
              checked ? "text-ink" : "text-ink-soft hover:text-ink"
            )}
          >
            <span className="flex size-3 shrink-0 items-center justify-center">
              {checked ? <Icon name="check" /> : null}
            </span>
            <span className="min-w-0 flex-1 truncate">{printer.label}</span>
            {printer.name === defaultName ? (
              <span className="shrink-0 rounded-[2px] border border-line px-1 font-mono text-[9px] leading-[14px] tracking-[0.08em] text-muted uppercase">
                Default
              </span>
            ) : null}
          </button>
        )
      })}

      <div className="border-t border-line-soft" role="separator" />

      <button
        type="button"
        role="menuitem"
        onClick={onAdd}
        className="chrome flex h-7 w-full items-center gap-2 px-3 text-left font-mono text-[10.5px] leading-4 text-accent-ink transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none"
      >
        <span className="size-3 shrink-0" />
        <span className="min-w-0 flex-1 truncate">+ Add a printer</span>
      </button>

      {onManage ? (
        <button
          type="button"
          role="menuitem"
          onClick={onManage}
          className="chrome flex w-full items-center gap-2 border-t border-line-soft bg-raised px-3 py-2 text-left font-mono text-[9.5px] leading-3 tracking-[0.08em] text-muted uppercase transition-colors hover:text-ink focus-visible:outline-none"
        >
          <span className="min-w-0 flex-1 truncate">Manage printers in Settings</span>
          <span className="shrink-0 rotate-180">
            <Icon name="chevron-left" />
          </span>
        </button>
      ) : null}
    </Floating>
  )
}
