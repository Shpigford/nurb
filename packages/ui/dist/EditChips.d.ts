/**
 * The keyword defaults of the first part function in a source, in order. A
 * parameter with no default is not a parameter of the part, so it is skipped.
 */
export declare function keywordDefaults(source: string): Map<string, string>;
/** One phrase per parameter that moved, added or went away. Empty when nothing did. */
export declare function diffDefaults(before: string, after: string): string[];
export type DiffLine = {
    sign: "+" | "-";
    text: string;
};
/** The changed lines, with the matching head and tail trimmed off. */
export declare function changedLines(before: string, after: string): DiffLine[];
type SourceEdit = {
    name: string;
    before?: string;
    after: string;
};
/** The part-source edit inside a tool call's input, or null when it is some other call. */
export declare function sourceEdit(input: unknown): SourceEdit | null;
export default function EditChips({ input, className }: {
    input: unknown;
    className?: string;
}): import("react").JSX.Element | null;
export {};
