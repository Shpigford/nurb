import { ReactNode } from 'react';
export type BannerState = "open" | "folded" | "dismissed";
export type BannerTone = "warn" | "fail" | "neutral";
export declare function useCollapsibleBanner({ state: controlled, defaultState, onStateChange, onDismiss, }?: {
    state?: BannerState;
    defaultState?: BannerState;
    onStateChange?: (state: BannerState) => void;
    onDismiss?: () => void;
}): {
    state: BannerState;
    open: boolean;
    folded: boolean;
    dismissed: boolean;
    fold: () => void;
    expand: () => void;
    toggle: () => void;
    dismiss: () => void;
};
export default function CollapsibleBanner({ title, description, children, action, tone, dismissible, state: controlled, defaultState, onStateChange, onDismiss, dismissLabel, className, }: {
    title: ReactNode;
    description?: ReactNode;
    children?: ReactNode;
    /** The control the notice is asking for, at the bottom of the fold. */
    action?: ReactNode;
    tone?: BannerTone;
    dismissible?: boolean;
    state?: BannerState;
    defaultState?: BannerState;
    onStateChange?: (state: BannerState) => void;
    onDismiss?: () => void;
    dismissLabel?: string;
    className?: string;
}): import("react").JSX.Element;
