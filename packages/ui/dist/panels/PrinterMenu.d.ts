import { RefObject } from 'react';
/** One machine on the bench, as the menu needs to name it. */
export interface PrinterOption {
    name: string;
    label: string;
}
export interface PrinterMenuProps {
    printers: PrinterOption[];
    /** The machine this part prices against right now. */
    current: string | null;
    /** The machine every new part starts on. */
    defaultName?: string | null;
    onPick: (name: string) => void;
    onAdd: () => void;
    /** Only the app has a Settings screen, so the footer is only there. */
    onManage?: () => void;
    /** The control that opened the menu: what it is placed from, and the one
     * pointer target that must not close it, because that click already toggles. */
    triggerRef: RefObject<HTMLElement | null>;
    onClose: () => void;
}
export default function PrinterMenu({ printers, current, defaultName, onPick, onAdd, onManage, triggerRef, onClose, }: PrinterMenuProps): import("react").JSX.Element;
