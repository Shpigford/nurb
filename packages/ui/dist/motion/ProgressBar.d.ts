export interface ProgressBarProps {
    /** The measured amount. null means the total is unknown and the bar crawls. */
    value: number | null;
    max?: number;
    /** Divide the track into cells. Progress quantizes to them, so bar and readout always agree. */
    segments?: number;
    label?: string;
    /** Readout while the total is unknown, in the same cell as the percentage. */
    pendingLabel?: string;
    /** Announced once through the live region when the bar fills. */
    completeLabel?: string;
    className?: string;
}
export default function ProgressBar({ value, max, segments, label, pendingLabel, completeLabel, className, }: ProgressBarProps): import("react").JSX.Element;
