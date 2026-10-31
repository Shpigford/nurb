import { BuildStats, Param, Params } from '../types';
import { Measurement } from './paramsState';
export interface ParamsPanelProps {
    params: Param[];
    /** Project measurements. Each one inside a float slider's range becomes a stop on it. */
    measurements?: Measurement[];
    /** Nozzle width in mm, which sets where the whole-line stops fall on a wall. */
    nozzle?: number;
    /** Session values keyed by parameter name; anything missing reads its default. */
    values: Params;
    onChange: (values: Params) => void;
    /** The edited values only, keyed by name. An untouched panel never gets here. */
    onApply: (values: Params) => void;
    /** A rebuild is in flight for these values. */
    building?: boolean;
    /** Apply is writing the values into the part's defaults. */
    applying?: boolean;
    /** The last build's numbers, for the footer line. */
    stats?: BuildStats | null;
    /** A build that failed at these values; the panel keeps showing the controls. */
    error?: string | null;
    /** What Apply said, once it landed. */
    note?: string | null;
}
export default function ParamsPanel({ params, measurements, nozzle, values, onChange, onApply, building, applying, stats, error, note, }: ParamsPanelProps): import("react").JSX.Element | null;
