import { ReactNode } from 'react';
export interface FloatingHeaderProps {
    /** The lockup end. */
    start?: ReactNode;
    /** The identity and status cells between the lockup and the tabs. */
    cells?: ReactNode;
    /** Tabs, icons and the avatar, pushed right. */
    end?: ReactNode;
    children?: ReactNode;
    /** The desktop drags its window by the header bar itself, not by its cells. */
    dragRegion?: boolean;
}
export default function FloatingHeader({ start, cells, end, children, dragRegion }: FloatingHeaderProps): import("react").JSX.Element;
export declare function HeaderDivider(): import("react").JSX.Element;
export declare function HeaderCell({ children, className }: {
    children: ReactNode;
    className?: string;
}): import("react").JSX.Element;
export declare function HeaderStack({ label, value, className }: {
    label: string;
    value: ReactNode;
    className?: string;
}): import("react").JSX.Element;
export type HeaderTone = "pass" | "warn" | "fail" | "none" | "building";
export declare function HeaderStatus({ tone, label, detail, className, }: {
    tone: HeaderTone;
    label: string;
    detail?: string;
    className?: string;
}): import("react").JSX.Element;
export declare function HeaderIcons({ children, className }: {
    children: ReactNode;
    className?: string;
}): import("react").JSX.Element;
