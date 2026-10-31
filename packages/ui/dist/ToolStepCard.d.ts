import { ToolStep } from './types';
export declare function ToolStepCard({ step, defaultOpen }: {
    step: ToolStep;
    defaultOpen?: boolean;
}): import("react").JSX.Element;
export declare function ToolStepGroup({ steps, defaultCollapsed }: {
    steps: ToolStep[];
    defaultCollapsed?: boolean;
}): import("react").JSX.Element;
export default ToolStepCard;
