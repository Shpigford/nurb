import { CSSProperties, RefObject } from 'react';
export interface AutoHeight {
    /** Goes on the inner content element, the one that is measured. */
    ref: RefObject<HTMLDivElement | null>;
    /** The measured content height, in pixels. */
    height: number;
    /** Spread onto the outer motion.div along with `style`. */
    animate: {
        height: number | "auto";
    };
    transition: {
        duration: number;
        ease: [number, number, number, number];
    };
    onAnimationComplete: () => void;
    style: CSSProperties;
}
export declare function useAutoHeight(open: boolean): AutoHeight;
