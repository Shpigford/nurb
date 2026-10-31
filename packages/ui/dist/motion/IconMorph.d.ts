export type IconMorphPreset = "check-close" | "plus-minus";
export default function IconMorph({ preset, active, size, strokeWidth, label, className, }: {
    preset?: IconMorphPreset;
    /** Which state to show. A boolean maps to 0 and 1. */
    active?: number | boolean;
    size?: number;
    strokeWidth?: number;
    /** Give the glyph its own accessible name when nothing around it carries one. */
    label?: string;
    className?: string;
}): import("react").JSX.Element;
