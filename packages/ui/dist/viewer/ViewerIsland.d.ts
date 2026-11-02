import { JSX, ReactNode } from 'react';
import { Object3D } from 'three';
import { Finding } from '../types';
export type Vec3 = [number, number, number];
export interface CameraState {
    position: Vec3;
    target: Vec3;
}
export interface Section {
    axis: "x" | "y" | "z";
    /** 0..1 along the axis; dragging right keeps more material */
    t: number;
}
/** Page content pinned to a spot on the part: it rides along as the camera orbits. */
export interface ViewerAnchor {
    key: string;
    /** In the part's own mm, the same space `onPick` reports. */
    point: Vec3;
    node: ReactNode;
}
export interface ViewerIslandProps {
    /** The part's GLB. Changing it swaps the geometry and keeps the camera. null clears the part. */
    glbUrl: string | null;
    /** A reference mesh drawn as a translucent ghost, offset by `targetOffset`. */
    targetUrl?: string | null;
    targetOffset?: Vec3;
    findings?: Finding[];
    /** Index into `findings` of the one to emphasize. */
    highlight?: number | null;
    /** Called when the user clicks a finding's glow (index) or empty space (null). */
    onHighlight?: (index: number | null) => void;
    /** While set, a click on the part reports that spot instead, in the part's own mm. */
    onPick?: ((pick: {
        point: Vec3;
        normal: Vec3;
    }) => void) | null;
    /** Printer bed [width, depth] in mm; null hides the plate. */
    bed?: [number, number] | null;
    /** Print-up axis of the part's coordinates. Default [0,0,1]. */
    up?: Vec3;
    section?: Section | null;
    /** Drawn over the canvas, each with its top-left corner on its point. */
    anchors?: ViewerAnchor[];
    /** A view to restore, taken when it can still see the part; compared by value, so a parent may re-send it freely. */
    camera?: CameraState | null;
    /** The user's orbits, debounced 250 ms after the last one. The component's own framing never reports. */
    onCamera?: (state: CameraState) => void;
    /** Bump to nudge the view a notch around the part. Any new value nudges once; the first value never does. */
    settleKey?: number;
    /** True once, on a project's first build, to lay the purge line across the front of the bed. */
    purge?: boolean;
    className?: string;
}
export interface CrossfadeOptions {
    seconds: number;
    render: () => void;
    /** Called once the fade lands, so the caller can remove and dispose the outgoing group. */
    onDone: () => void;
    /** Injected by the tests; the component uses the real clock and rAF. */
    now?: () => number;
    schedule?: (step: () => void) => number;
    unschedule?: (id: number) => void;
}
/**
 * Dissolves one group into another in place. Both keep their own transparency settings:
 * `transparent` is switched on only for the fade, because leaving it on would sort the part
 * against the whole scene for the rest of the session, and the outgoing group stops writing
 * depth so it cannot punch holes in the arriving one. Returns a cancel that restores the
 * survivor without calling onDone.
 */
export declare function crossfadeGroups(from: Object3D | null, to: Object3D | null, opts: CrossfadeOptions): () => void;
export declare function ViewerIsland(props: ViewerIslandProps): JSX.Element;
export default ViewerIsland;
