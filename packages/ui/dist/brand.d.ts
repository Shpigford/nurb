export declare const brand: {
    readonly lockup: string;
    readonly mark: string;
    readonly markOutline: string;
    readonly markSmall: string;
    readonly favicon: string;
    readonly authPlane: string;
    readonly ghostBracket: string;
    readonly squiggle: string;
};
/** A one-colour brand drawing as a mask, so a token can paint it and it follows the theme. */
export declare const maskOf: (src: string) => {
    WebkitMask: string;
    mask: string;
};
