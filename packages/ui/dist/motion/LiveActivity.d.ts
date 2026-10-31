export type ActivityTone = "working" | "done" | "fail";
export type Activity = {
    id: string;
    title: string;
    detail?: string;
    tone?: ActivityTone;
};
export declare function useLiveActivity({ linger }?: {
    linger?: number;
}): {
    activity: Activity | null;
    start: (input: Omit<Activity, "id" | "tone">) => string;
    update: (patch: Partial<Omit<Activity, "id">>) => void;
    succeed: (patch?: Partial<Omit<Activity, "id" | "tone">>) => void;
    fail: (patch?: Partial<Omit<Activity, "id" | "tone">>) => void;
    dismiss: () => void;
};
export default function LiveActivity({ activity, onDismiss, label, className, }: {
    activity: Activity | null;
    /** Wired to the close affordance, once the work has resolved. */
    onDismiss?: () => void;
    label?: string;
    className?: string;
}): import("react").JSX.Element;
