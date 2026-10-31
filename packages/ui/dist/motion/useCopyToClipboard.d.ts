export type CopyStatus = "idle" | "copied" | "error";
export interface UseCopyToClipboardOptions {
    /** How long "copied" or "error" shows before the label goes back. */
    timeout?: number;
    onCopy?: (value: string) => void;
    onError?: (error: unknown) => void;
}
export declare function useCopyToClipboard({ timeout, onCopy, onError }?: UseCopyToClipboardOptions): {
    status: CopyStatus;
    copy: (value: string) => Promise<void>;
};
export default useCopyToClipboard;
