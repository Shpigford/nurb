export type HoldPhase = "idle" | "holding" | "releasing" | "committed";
/** The hold itself, with no surface: pointer and key bindings in, a phase and a 0..1 progress out. */
export declare function useHoldToConfirm({ onConfirm, holdMs, disabled, }: {
    onConfirm: () => void;
    holdMs?: number;
    disabled?: boolean;
}): {
    bind: {
        onPointerDown: (e: React.PointerEvent) => void;
        onPointerMove: (e: React.PointerEvent) => void;
        onPointerUp: () => void;
        onPointerCancel: () => void;
        onPointerLeave: () => void;
        onKeyDown: (e: React.KeyboardEvent) => void;
        onKeyUp: (e: React.KeyboardEvent) => void;
        onBlur: () => void;
        onClick: (e: React.MouseEvent) => void;
        onContextMenu: (e: React.MouseEvent) => void;
    };
    phase: HoldPhase;
    progress: number;
    reset: () => void;
};
export default function HoldToConfirm({ label, confirmLabel, holdMs, onConfirm, variant, disabled, className, }: {
    label: string;
    confirmLabel?: string;
    holdMs?: number;
    onConfirm: () => void;
    variant?: "accent" | "ink" | "outline" | "ghost" | "danger";
    disabled?: boolean;
    className?: string;
}): import("react").JSX.Element;
