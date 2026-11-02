import { CSSProperties, MouseEventHandler, ReactNode } from 'react';
export interface StageProps {
    header?: ReactNode;
    children: ReactNode;
    className?: string;
    style?: CSSProperties;
    /** Pad the top for a window titlebar. The design's 16 comes from `p-4`, so this only ever grows it. */
    topInset?: number;
    /** The desktop drags its window by the bare ground. Tauri reads the attribute
     * off the element under the pointer only, so a panel on the stage is unaffected. */
    dragRegion?: boolean;
}
export default function Stage({ header, children, className, style, topInset, dragRegion }: StageProps): import("react").JSX.Element;
export declare function StageColumn({ children, className, onContextMenu, }: {
    children: ReactNode;
    className?: string;
    onContextMenu?: MouseEventHandler;
}): import("react").JSX.Element;
export declare function StageEmpty({ children, className }: {
    children: ReactNode;
    className?: string;
}): import("react").JSX.Element;
