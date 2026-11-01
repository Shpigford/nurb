import { MenuItem } from './Menu';
export interface PartCardPart {
    id: string;
    name: string;
    identifier?: string;
    bbox?: number[] | null;
    status: "built" | "failed" | "building" | "unbuilt";
    revision?: number | null;
    builtAt?: string | null;
    thumbnailUrl?: string | null;
    /** The folder the part sits in. The footer says that instead of the revision. */
    folder?: string | null;
    /** When the running build started, so a stalled one stops claiming to be alive. */
    buildingSince?: string | null;
}
export default function PartCard({ part, onOpen, menu, renaming, onRename, }: {
    part: PartCardPart;
    onOpen: () => void;
    menu?: MenuItem[];
    /** The title is a field: Enter or leaving it hands back the name, Escape hands back null. */
    renaming?: boolean;
    onRename?: (name: string | null) => void;
}): import("react").JSX.Element;
