import { ReactNode } from 'react';
export interface PinnedParam {
    name: string;
    value: string;
}
export interface RailReadouts {
    grams?: number | null;
    seconds?: number | null;
    heightMm?: number | null;
}
export interface ParamRailProps {
    count: number;
    /** What the spec fixed. These carry a lock and never get a slider. */
    pinned?: PinnedParam[];
    /** Where the consumer drops <ParamsPanel/>. */
    params: ReactNode;
    readouts?: RailReadouts;
    warnCount?: number;
    failCount?: number;
    disclosures?: ReactNode;
    actions: ReactNode;
}
export default function ParamRail({ count, pinned, params, readouts, warnCount, failCount, disclosures, actions, }: ParamRailProps): import("react").JSX.Element;
