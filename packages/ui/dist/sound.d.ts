export type Cue = "ready" | "arrival" | "success" | "error" | "press" | "tick" | "toggle" | "scan" | "loading";
export interface SoundPrefs {
    enabled: boolean;
    volume: number;
}
/** Reads the stored preferences and pushes them into cuelume. */
export declare function readSoundPrefs(): SoundPrefs;
export declare function setSoundEnabled(on: boolean): void;
export declare function setSoundVolume(v: number): void;
/** Plays a cue. A no-op on the server, when muted, or when audio is unavailable. */
export declare function cue(name: Cue, opts?: {
    volume?: number;
}): void;
