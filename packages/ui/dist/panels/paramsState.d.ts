import { Detent } from '../motion/useSliderDetents';
import { Param, Params } from '../types';
export declare function sliderRange(defaultValue: number, int: boolean): {
    lo: number;
    hi: number;
    step: number;
};
export declare function rangeFor(param: Param, int: boolean): {
    lo: number;
    hi: number;
    step: number;
};
export declare function decimals(value: number): number;
export declare function tidy(value: number, step: number): number;
export declare function adjustable(param: Param): boolean;
export declare function dirtyValues(params: Param[], values: Params): Params;
export interface Measurement {
    value_mm: number;
}
export declare function detentsFor(param: Param, measurements: Measurement[] | undefined, nozzle?: number): Detent[];
