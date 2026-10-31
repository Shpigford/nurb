/** Seconds, because motion's `transition` prop is in seconds while CSS is in ms. */
export declare const duration: {
    readonly tick: 0.09;
    readonly settle: 0.24;
    readonly arrive: 0.42;
    readonly coast: 1.4;
};
export declare const ease: {
    readonly out: readonly [0.23, 1, 0.32, 1];
    readonly inOut: readonly [0.65, 0, 0.35, 1];
};
