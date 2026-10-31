export type ExportFormat = "3mf" | "stl" | "step";
export interface ExportResult {
    /** Where the finished file lives. The menu hands it to the user as a link. */
    url: string;
    filename?: string;
}
/** What the slicer said about the last export, once it has answered. */
export interface ExportStatus {
    state: "queued" | "succeeded" | "failed";
    grams?: number | null;
    seconds?: number | null;
    error?: string | null;
}
export interface ExportMenuProps {
    /** Stable identity of the part being exported. */
    partId: string;
    /** Builds the file. The menu shows a pending state until this settles. */
    export: (format: ExportFormat) => Promise<ExportResult>;
    /** The slicer estimate for the export just handed out. */
    status?: ExportStatus | null;
    revision?: number;
    /** The build the prepared file came from; a newer one makes that file stale. */
    runId?: string | null;
}
export default function ExportMenu({ partId, export: runExport, status, revision, runId }: ExportMenuProps): import("react").JSX.Element;
