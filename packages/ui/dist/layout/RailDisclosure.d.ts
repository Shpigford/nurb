import { ReactNode } from 'react';
export type DisclosureTone = "warn" | "fail" | "pass" | "none";
export interface RailDisclosureProps {
    label: string;
    summary?: ReactNode;
    tone?: DisclosureTone;
    open: boolean;
    onToggle: () => void;
    children: ReactNode;
}
export default function RailDisclosure({ label, summary, tone, open, onToggle, children }: RailDisclosureProps): import("react").JSX.Element;
