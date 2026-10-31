export interface SegmentedOption {
    value: string;
    label: string;
}
export default function SegmentedControl({ options, label, value, onValueChange, className, }: {
    options: SegmentedOption[];
    /** Accessible name. An unlabelled group of radios announces nothing about what it switches. */
    label: string;
    value: string;
    onValueChange: (value: string) => void;
    className?: string;
}): import("react").JSX.Element;
