import { ReactNode } from 'react';
export default function ConfirmDialog({ title, children, confirmLabel, hold, onConfirm, onCancel, }: {
    title: string;
    children: ReactNode;
    confirmLabel?: string;
    /** Press and hold to confirm, for a delete with no undo behind it. */
    hold?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}): import("react").JSX.Element;
