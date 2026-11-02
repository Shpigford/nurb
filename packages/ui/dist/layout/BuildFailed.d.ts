import { ReactNode } from 'react';
export declare function BuildFailedBanner({ open, revision, shownRevision, error, }: {
    /** False sends the banner back up the way it came. */
    open?: boolean;
    revision: number;
    shownRevision?: number | null;
    /** The failure's own last line, so the reason sits under the headline whatever raised it. */
    error?: string | null;
}): import("react").JSX.Element;
export declare function StageNotice({ children }: {
    children: ReactNode;
}): import("react").JSX.Element;
