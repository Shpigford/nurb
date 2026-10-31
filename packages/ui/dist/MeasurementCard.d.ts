import { Measurement } from './types';
export default function MeasurementCard({ measurement, staleParts, onAccept, onEdit, onRebuild, rebuilding, }: {
    measurement: Measurement;
    staleParts?: string[];
    onAccept?: (name: string) => void;
    onEdit?: (name: string) => void;
    onRebuild?: (staleParts: string[]) => void;
    rebuilding?: boolean;
}): import("react").JSX.Element;
