import { ComponentProps } from 'react';
import { default as Button } from './Button';
export interface ApprovalAction {
    id: string;
    label: string;
    variant?: ComponentProps<typeof Button>["variant"];
}
export interface ApprovalQuestion {
    id: string | number;
    title: string;
    detail?: string;
    actions: ApprovalAction[];
}
export default function ApprovalCard({ questions, onAnswer, className, }: {
    /** The asks still waiting. The owner drops one when it is answered or withdrawn. */
    questions: ApprovalQuestion[];
    onAnswer: (questionId: ApprovalQuestion["id"], actionId: string) => void;
    className?: string;
}): import("react").JSX.Element | null;
