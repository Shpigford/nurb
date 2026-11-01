export type FlashDirection = "up" | "down";
export interface ValueFlashState {
    direction: FlashDirection | null;
    from: number;
    changeId: number;
    flashing: boolean;
}
/** Watches a number and reports which way it moved, for a caller drawing its own cell. */
export declare function useValueFlash(value: number, hold?: number): ValueFlashState;
export interface ValueFlashProps {
    value: number;
    /** Formats the figure. Tabular by construction, so equal-length values never jitter. */
    format?: (value: number) => string;
    /** Prefixes the announcement, so a screen reader hears which figure moved. */
    label?: string;
    /** Milliseconds the tint and the mark stay lit. */
    hold?: number;
    className?: string;
}
export default function ValueFlash({ value, format, label, hold, className }: ValueFlashProps): import("react").JSX.Element;
