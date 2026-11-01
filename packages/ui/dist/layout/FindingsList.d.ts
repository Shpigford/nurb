import { Finding } from '../types';
export type Verdict = "pass" | "warn" | "fail" | "none";
export interface FindingsListProps {
    findings: Finding[];
    verdict: Verdict;
    highlight?: number | null;
    onHighlight?: (index: number | null) => void;
}
export default function FindingsList({ findings, verdict, highlight, onHighlight }: FindingsListProps): import("react").JSX.Element;
