import { ReactNode, RefObject } from 'react';
export interface FloatingProps {
    /** The control the panel belongs to. Its box is where the panel is placed. */
    anchor: RefObject<HTMLElement | null>;
    /** Fixed width, so the lane the panel sits in never depends on its contents. */
    width: number;
    /** Which edge of the anchor the panel lines its own edge up with. */
    align?: "left" | "right";
    /** Clear space between the anchor's top and the panel's bottom. */
    gap?: number;
    role?: string;
    "aria-label"?: string;
    className?: string;
    children: ReactNode;
}
declare const Floating: import('react').ForwardRefExoticComponent<FloatingProps & import('react').RefAttributes<HTMLDivElement>>;
export default Floating;
