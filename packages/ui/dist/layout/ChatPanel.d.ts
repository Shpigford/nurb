import { ReactNode } from 'react';
export interface ChatPanelProps {
    strip: {
        label: string;
        trailing?: ReactNode;
    };
    /** The agent picker, which lives in the strip's trailing area on the desktop. */
    picker?: ReactNode;
    children: ReactNode;
    composer: ReactNode;
    /** Kept mounted but out of view, so a background conversation stays alive. */
    hidden?: boolean;
    /** The desktop drags its window by the strip. */
    dragRegion?: boolean;
}
export default function ChatPanel({ strip, picker, children, composer, hidden, dragRegion }: ChatPanelProps): import("react").JSX.Element;
