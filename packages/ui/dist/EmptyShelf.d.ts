import { IconName } from './Icon';
export default function EmptyShelf({ caption, firstRun, primary, secondary, }: {
    caption?: string;
    /** The library has never held a part. Said once, and never again after the first one. */
    firstRun?: boolean;
    primary?: {
        label: string;
        onClick: () => void;
        icon?: IconName;
    };
    /** The quieter way in, under the primary: importing a folder you already have. */
    secondary?: {
        label: string;
        icon?: IconName;
        onClick: () => void;
        disabled?: boolean;
    };
}): import("react").JSX.Element;
