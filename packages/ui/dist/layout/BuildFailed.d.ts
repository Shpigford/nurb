import { ReactNode } from 'react';
export declare function BuildFailedBanner({ open, revision, shownRevision, }: {
    /** False sends the banner back up the way it came. */
    open?: boolean;
    revision: number;
    shownRevision?: number | null;
}): import("react").JSX.Element;
export declare function StageNotice({ children }: {
    children: ReactNode;
}): import("react").JSX.Element;
