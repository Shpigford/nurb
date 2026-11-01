interface IsoBoxProps {
    /** [x, y, z] in mm. Missing or degenerate → a ghost outline. */
    bbox?: number[] | null;
    ghost?: boolean;
    className?: string;
}
export default function IsoBox({ bbox, ghost, className }: IsoBoxProps): import("react").JSX.Element;
export {};
