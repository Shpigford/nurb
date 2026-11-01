import { ReactNode } from 'react';
export interface UseSkeletonSwapOptions {
    loading: boolean;
    /** Milliseconds of silence before the skeleton may paint. A faster answer shows none. */
    delay?: number;
    /** Once painted, the skeleton stays this long, so it cannot blink. */
    minVisible?: number;
}
export declare function useSkeletonSwap({ loading, delay, minVisible }: UseSkeletonSwapOptions): {
    showSkeleton: boolean;
};
export interface SkeletonSwapProps extends UseSkeletonSwapOptions {
    children: ReactNode;
    /** How many bars the skeleton draws, and how much height it reserves. */
    lines?: number;
    /** Leading of the content this stands in for; match it and the reserve is exact. */
    lineHeight?: number;
    /** Explicit box height in pixels, for content that is not text: a chart, a thumbnail, a card. */
    reserve?: number;
    /** Names the region and announces "<label> loaded" once. */
    label?: string;
    className?: string;
}
export default function SkeletonSwap({ loading, children, lines, lineHeight, reserve, delay, minVisible, label, className, }: SkeletonSwapProps): import("react").JSX.Element;
