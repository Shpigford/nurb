/** The composer's drop target, lit while a photo is over it. The parent is the positioned box. */
export declare function DropHint({ active, label }: {
    active: boolean;
    label?: string;
}): import("react").JSX.Element;
/**
 * A placeholder that cycles, for the first conversation only. It crossfades, so
 * both phrases are on screen together for a moment; reduced motion still cycles,
 * because the point is the examples rather than the movement.
 */
export declare function CyclingPlaceholder({ lines, active, everyMs, className, }: {
    lines: string[];
    active: boolean;
    everyMs?: number;
    className?: string;
}): import("react").JSX.Element | null;
