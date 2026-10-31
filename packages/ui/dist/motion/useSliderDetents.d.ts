import { ChangeEvent, KeyboardEvent } from 'react';
export type Detent = {
    value: number;
    label?: string;
};
export interface UseSliderDetentsOptions {
    value: number;
    onValueChange: (value: number) => void;
    min: number;
    max: number;
    step: number;
    detents: (number | Detent)[];
    /** Capture radius in value units. Inside it the pointer gives way to the detent. */
    pull?: number;
}
export interface SliderDetents {
    /** Wire to the input's onChange. Snaps the raw value, then emits it. */
    onChange: (event: ChangeEvent<HTMLInputElement>) => void;
    /** Wire to the input's onKeyDown, so arrow keys step past a detent instead of sticking to it. */
    onKeyDown: (event: KeyboardEvent<HTMLInputElement>) => void;
    /** Index into `detents` the value is parked on, or -1. */
    activeDetent: number;
    detents: Detent[];
    /** The active detent's name, for a readout beside the number. */
    activeLabel?: string;
}
export declare function useSliderDetents({ value, onValueChange, min, max, step, detents, pull, }: UseSliderDetentsOptions): SliderDetents;
/** The tick marks under a slider. Goes inside a `relative` wrapper around the input. */
export declare function DetentMarks({ detents, min, max, activeDetent, className, }: {
    detents: Detent[];
    min: number;
    max: number;
    activeDetent?: number;
    className?: string;
}): import("react").JSX.Element;
