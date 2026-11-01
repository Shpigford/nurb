import { Measurement } from './types';
/** Whether a recorded measurement moved an earlier value, rather than writing a first one. */
export declare function changedSize(measurement: Measurement): boolean;
export default function MeasurementCard({ measurement, staleParts, onAccept, onEdit, onRebuild, rebuilding, }: {
    measurement: Measurement;
    staleParts?: string[];
    onAccept?: (name: string) => void;
    onEdit?: (name: string) => void;
    onRebuild?: (staleParts: string[]) => void;
    rebuilding?: boolean;
}): import("react").JSX.Element;
