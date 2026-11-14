import { Box3, Group, LineSegments, Mesh, Vector3, Light, Object3D, PerspectiveCamera, Plane } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { Severity } from '../types';
export declare const palette: {
    readonly stage: 15069435;
    readonly part: 16732720;
    readonly context: 7897485;
    readonly edge: 10691593;
    readonly gridMinor: 13623537;
    readonly gridMajor: 12374760;
    readonly gridBorder: 10467021;
    readonly accent: 16732720;
    readonly fail: 13570600;
    readonly warn: 14714624;
    readonly ghost: 8608554;
    readonly cap: 7169436;
};
export type Palette = typeof palette;
export declare const stageColors: () => {
    stage: number;
    gridMinor: number;
    gridMajor: number;
    gridBorder: number;
};
export declare const HIGHLIGHT_OPACITY = 0.62;
/**
 * One bright key, a little ambient. The key is steep and strong on purpose: the part's own
 * color is the accent, and only an exposure that clips its red lifts the top face to the
 * design's #ff7050 while the side falls to #c42d12. The hemisphere is moved to Z, which is
 * up in this scene, so that gradient runs top to bottom rather than front to back.
 */
export declare function createLights(): Light[];
/**
 * The build plate at the printer's bed size. A bed is a rectangle, which is why this is not
 * a GridHelper (v1:744-768). `pitch` is the minor spacing in mm, every fifth line heavier,
 * so a gridfinity plate is the same call with 42.
 */
export declare function plate([w, d]: [number, number], pitch?: number): Group;
/** The purge line is one first-layer bead wide, the way a printer actually lays it. */
export declare const PURGE_WIDTH = 1.2;
/**
 * The bead a printer wipes along the front of the bed before it starts. Unit length in X so
 * the caller scales it in mm, and parked a bead in from the border so it reads as on the plate
 * rather than as part of the frame.
 */
export declare function purgeBead(d: number): Mesh;
/** v1's fit: iso direction, 2.1 of padding, near and far from the span (v1:1785-1804). */
export declare function frameCamera(camera: PerspectiveCamera, controls: OrbitControls, box: Box3): void;
/**
 * True when this viewpoint can plausibly see the part: camera outside the solid, target
 * near it, distance in a sane band. A camera can go stale when the part changes shape
 * under it, and keeping one that fails this paints a blank canvas (v1:1738-1747).
 */
export declare function saneCamera(position: Vector3, target: Vector3, box: Box3): boolean;
/** sane() is a distance argument, not a visibility one, so the part must also be in frame (v1:1765-1770). */
export declare function cameraSeesBox(camera: PerspectiveCamera, box: Box3): boolean;
/** One Mesh per isMesh node, each with its own material, the clip plane and an edge overlay (v1:1908-1928). */
export declare function buildPartGroup(gltfScene: Object3D, plane: Plane, pal: Palette): Group;
/**
 * A part sits on the plate, centered, the way a slicer plates it. Where its own origin
 * falls is a modeling datum and nothing to do with printing (v1:1950-1960). Returns the
 * bounds in the plated position, the box every frame, cut and pin is measured against.
 */
export declare function plateGroup(group: Group): Box3;
/** The bounds the section slider spans: the printed children only, in world space (v1:1063-1066). */
export declare function printedBox(group: Group): Box3;
/** Back writers increment, front writers decrement; both share the child's world matrix so a posed joint drags them (v1:1044-1060). */
export declare function stencilWriters(child: Mesh, plane: Plane): Mesh[];
/** The cut is painted only where the stencil says material passes the plane (v1:1013-1034). */
export declare function capMesh(): Mesh;
/** Places the cap over the cut: the part's center projected onto the plane, not coplanarPoint (v1:1084-1090). */
export declare function placeCap(cap: Mesh, plane: Plane, box: Box3): void;
/**
 * The face a rule fired on, painted onto the solid. Depth-tested, unlike the pins: a glow
 * seen through a wall would accuse the wrong face (v1:1000-1010).
 */
export declare function glowMesh(face: number[], severity: Severity, plane: Plane, pal: Palette): Mesh;
/** The outline that says which finding is the emphasized one. */
export declare function glowOutline(face: number[], plane: Plane, pal: Palette): LineSegments;
/**
 * Pins draw through the solid on purpose: a rule reports a point on a face, so the pin
 * sits half inside the material and a marker you cannot see is worse than none (v1:798-808).
 */
export declare function pinMesh(where: [number, number, number], severity: Severity, scale: number, pal: Palette): Mesh;
/** The ghost's geometry is not ours to drop, so a child named `target` is skipped (v1:1904). */
export declare function disposeGroup(group: Object3D): void;
