export type AsyncStatus = "idle" | "pending" | "success" | "error";
/** The state machine on its own: run once, settle, fall back to idle after resetAfter ms. */
export declare function useAsyncAction({ action, resetAfter, }: {
    action: () => unknown;
    resetAfter?: number;
}): {
    status: AsyncStatus;
    run: () => void;
    pending: boolean;
};
export default function LoadingButton({ label, pendingLabel, successLabel, errorLabel, onAction, resetAfter, variant, disabled, className, }: {
    label: string;
    pendingLabel?: string;
    successLabel?: string;
    errorLabel?: string;
    onAction: () => unknown;
    resetAfter?: number;
    variant?: "accent" | "ink" | "outline" | "ghost" | "danger";
    disabled?: boolean;
    className?: string;
}): import("react").JSX.Element;
