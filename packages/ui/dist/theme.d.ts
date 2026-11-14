export type ThemeChoice = "system" | "light" | "dark";
export declare function readThemeChoice(): ThemeChoice;
export declare function setThemeChoice(choice: ThemeChoice): void;
/** Call once at startup, before the first render, so the page never paints in the wrong theme. */
export declare function startTheme(): void;
export declare const isDark: () => boolean;
/** For what CSS cannot reach, like a picture the engine renders for one ground or the other. */
export declare const useIsDark: () => boolean;
