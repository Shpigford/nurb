export type NewItemsAnchor = "top" | "bottom";
export default function NewItemsPill({ count, onClick, anchor, label, className, }: {
    count: number;
    onClick: () => void;
    anchor?: NewItemsAnchor;
    /** Builds the visible text and the accessible name. Pluralise here; nothing downstream guesses at grammar. */
    label?: (count: number) => string;
    className?: string;
}): import("react").JSX.Element;
