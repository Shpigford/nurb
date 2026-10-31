export interface TaskStep {
    id: string;
    label: string;
    /** A right-aligned mono aside, revealed when the step completes: a duration, a count. */
    meta?: string;
}
export type TaskStepStatus = "pending" | "active" | "done" | "failed";
export interface UseTaskStepsOptions {
    steps: TaskStep[];
    /** Index of the step running now. Everything before it is done; at steps.length the run is over. */
    current: number;
    /** The run stopped at `current`. Nothing after that row pretends to have run. */
    failed?: boolean;
}
export declare function useTaskSteps({ steps, current, failed }: UseTaskStepsOptions): {
    rows: {
        status: TaskStepStatus;
        id: string;
        label: string;
        /** A right-aligned mono aside, revealed when the step completes: a duration, a count. */
        meta?: string;
    }[];
    complete: boolean;
    failed: boolean;
    sentence: string;
};
export interface TaskStepsProps extends UseTaskStepsOptions {
    label?: string;
    className?: string;
}
export default function TaskSteps({ steps, current, failed, label, className, }: TaskStepsProps): import("react").JSX.Element;
