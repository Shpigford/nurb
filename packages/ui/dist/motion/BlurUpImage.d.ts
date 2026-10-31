export type BlurUpStatus = "loading" | "ready" | "error";
export declare function useBlurUpImage({ src, onReady, onError, }: {
    src?: string;
    onReady?: () => void;
    onError?: () => void;
}): {
    ref: import('react').RefObject<HTMLImageElement | null>;
    status: BlurUpStatus;
    instant: boolean;
    loaded: boolean;
};
export default function BlurUpImage({ src, alt, width, height, placeholder, blur, sizes, loading, onReady, onError, className, }: {
    src?: string;
    /** Lives on the real image for the whole lifecycle, so the description is available before the bytes are. */
    alt: string;
    width: number;
    height: number;
    /** The colour under everything, held while the photo resolves. */
    placeholder?: string;
    blur?: number;
    sizes?: string;
    loading?: "lazy" | "eager";
    onReady?: () => void;
    onError?: () => void;
    className?: string;
}): import("react").JSX.Element;
