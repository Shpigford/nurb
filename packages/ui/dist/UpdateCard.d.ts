export default function UpdateCard({ version, installing, onLater, onInstall, className, }: {
    version: string;
    installing?: boolean;
    onLater?: () => void;
    onInstall: () => void;
    className?: string;
}): import("react").JSX.Element;
