import { MouseEvent, ReactNode } from 'react';
import { IconName } from './Icon';
export interface MenuItem {
    label: ReactNode;
    onSelect: () => void;
    icon?: IconName;
    tone?: "default" | "danger";
    /** A rule above this item (Sign out sits alone under one). */
    separated?: boolean;
    /** A radio-style menu: the checked item carries a check, the rest keep the slot. */
    checked?: boolean;
    /** A hint at the row's end (a "sign in" pill, a model's note). */
    trailing?: ReactNode;
    /** Eyebrow above this item; consecutive items with the same section share one. */
    section?: string;
    /** The menu stays open after this pick (a choice with more to choose after it). */
    keepOpen?: boolean;
    disabled?: boolean;
    /** Hover text, for a note too long to sit in the row. */
    title?: string;
}
export default function Menu({ label, items, align, className, menuClassName, trigger, footer, portal, disabled, triggerClassName, onOpenChange, filter, }: {
    label: string;
    items: MenuItem[];
    align?: "left" | "right";
    className?: string;
    menuClassName?: string;
    /** Replaces the "…" glyph; the button chrome stays. */
    trigger?: (open: boolean) => ReactNode;
    /** A well under the items (the note about what a choice costs). */
    footer?: ReactNode;
    /** Render the popover on document.body, fixed under the trigger, so a
     * clipping ancestor (the header's overflow-hidden) cannot cut it off. */
    portal?: boolean;
    disabled?: boolean;
    /** Fires on every open and close, for an owner that commits a choice when the menu goes away. */
    onOpenChange?: (open: boolean) => void;
    /** Replaces the trigger's own size and shape classes; the chrome and focus ring stay. */
    triggerClassName?: string;
    /** A find field above the items, with this placeholder, for a list too long to scan. */
    filter?: string;
}): import("react").JSX.Element;
export declare function useContextMenu(): {
    open: (e: MouseEvent, items: MenuItem[] | undefined) => void;
    menu: ReactNode;
};
