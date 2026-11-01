import clsx from "clsx"
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react"
import Icon, { type IconName } from "./Icon"

// Two heights only: 28 (chrome, inline actions) and 36/40 (the page's one
// primary). Labels are mono caps. Filled accent carries white; secondary is a
// hairline outline on white; ghost is text.

type Variant = "accent" | "ink" | "outline" | "ghost" | "danger"
type Size = "sm" | "md" | "lg"

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  icon?: IconName
  trailingIcon?: IconName
  children: ReactNode
}

const VARIANT: Record<Variant, string> = {
  accent: "bg-accent text-white hover:bg-accent-hover",
  ink: "bg-ink text-white hover:bg-ink-soft",
  outline: "border border-line bg-ground text-ink-soft hover:border-panel-edge hover:text-ink",
  ghost: "text-muted hover:bg-raised hover:text-ink",
  danger: "bg-fail text-white hover:bg-fail/90",
}

const SIZE: Record<Size, string> = {
  sm: "h-7 px-3",
  md: "h-9 px-3",
  lg: "h-10 px-4",
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "outline", size = "sm", icon, trailingIcon, className, children, type = "button", ...rest },
  ref
) {
  return (
    <button
      ref={ref}
      type={type}
      className={clsx(
        "chrome btn-label inline-flex shrink-0 items-center justify-center gap-2 rounded-[3px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50",
        VARIANT[variant],
        SIZE[size],
        icon && "pl-2.5",
        trailingIcon && "pr-2.5",
        className
      )}
      {...rest}
    >
      {icon ? <Icon name={icon} /> : null}
      {children}
      {trailingIcon ? <Icon name={trailingIcon} /> : null}
    </button>
  )
})

export default Button

// A 28px square chrome button: header icons, composer tools, zoom cluster.
export function IconButton({
  icon,
  label,
  active = false,
  className,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { icon: IconName; label: string; active?: boolean }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={clsx(
        "chrome relative inline-flex size-7 shrink-0 items-center justify-center rounded-[4px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent disabled:opacity-40",
        active ? "bg-accent-wash text-accent-ink" : "text-ink-soft hover:bg-raised hover:text-ink",
        className
      )}
      {...rest}
    >
      <Icon name={icon} />
      <span className="absolute top-1/2 left-1/2 size-[max(100%,3rem)] -translate-1/2 pointer-fine:hidden" aria-hidden="true" />
    </button>
  )
}
