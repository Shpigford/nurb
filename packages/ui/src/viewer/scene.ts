import {
  AlwaysStencilFunc,
  BackSide,
  Box3,
  BoxGeometry,
  BufferAttribute,
  BufferGeometry,
  DecrementWrapStencilOp,
  DirectionalLight,
  DoubleSide,
  EdgesGeometry,
  FrontSide,
  Group,
  HemisphereLight,
  IncrementWrapStencilOp,
  LineBasicMaterial,
  LineSegments,
  Matrix4,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  NotEqualStencilFunc,
  PlaneGeometry,
  ReplaceStencilOp,
  Quaternion,
  SphereGeometry,
  Vector3,
} from "three"
import type { Light, Material, Object3D, PerspectiveCamera, Plane } from "three"
import { Frustum } from "three"
import type { OrbitControls } from "three/addons/controls/OrbitControls.js"
import type { Severity } from "../types"
import { isDark } from "../theme"

// The light palette, decided in PROGRESS.md Phase 7. The part wears the brand accent, as
// the design draws it: --color-accent for the material, --color-part-edge for the outline.
// The lit faces then land on the design's own three tones, top #ff7050, front #f0421f,
// side #c42d12, which is what createLights() is tuned for.
export const palette = {
  stage: 0xe5f0fb,
  part: 0xff5230,
  // Scenery stays neutral, and its albedo is pre-darkened because the key is bright enough
  // to clip the part's red: 0x78818d lit from above reads as the grey-blue token, 0xaab6c6.
  context: 0x78818d,
  edge: 0xa32409,
  gridMinor: 0xcfe0f1,
  gridMajor: 0xbcd2e8,
  gridBorder: 0x9fb6cd,
  accent: 0xff5230,
  fail: 0xcf1228,
  warn: 0xe08700,
  // Amber and violet are lit by the same key, so both are pre-darkened the same way.
  ghost: 0x835b2a,
  cap: 0x6d659c,
} as const

export type Palette = typeof palette

// The stage and the bed follow the theme; the part, its lights and the marks do not, so
// a part looks the same printed colour in either. Dark mirrors --color-stage in tokens.css.
export const stageColors = () =>
  isDark()
    ? { stage: 0x0e1218, gridMinor: 0x1a212b, gridMajor: 0x252e3b, gridBorder: 0x3a4657 }
    : { stage: palette.stage, gridMinor: palette.gridMinor, gridMajor: palette.gridMajor, gridBorder: palette.gridBorder }

const GLOW_OPACITY: Record<Severity, number> = { fail: 0.4, warn: 0.38 }
export const HIGHLIGHT_OPACITY = 0.62

// 25 degrees keeps tessellated curves clean while every modeled corner qualifies (v1:840-846).
const EDGE_ANGLE = 25

const severityColor = (severity: Severity, pal: Palette) => (severity === "fail" ? pal.fail : pal.warn)

/**
 * One bright key, a little ambient. The key is steep and strong on purpose: the part's own
 * color is the accent, and only an exposure that clips its red lifts the top face to the
 * design's #ff7050 while the side falls to #c42d12. The hemisphere is moved to Z, which is
 * up in this scene, so that gradient runs top to bottom rather than front to back.
 */
export function createLights(): Light[] {
  const key = new DirectionalLight(0xffffff, 6)
  key.position.set(0.4, -0.9, 2.9)
  const sky = new HemisphereLight(0xffffff, palette.gridMajor, 1)
  sky.position.set(0, 0, 1)
  return [sky, key]
}

const segments = (points: number[], material: LineBasicMaterial) => {
  const geometry = new BufferGeometry()
  geometry.setAttribute("position", new BufferAttribute(new Float32Array(points), 3))
  return new LineSegments(geometry, material)
}

/**
 * The build plate at the printer's bed size. A bed is a rectangle, which is why this is not
 * a GridHelper (v1:744-768). `pitch` is the minor spacing in mm, every fifth line heavier,
 * so a gridfinity plate is the same call with 42.
 */
export function plate([w, d]: [number, number], pitch = 10): Group {
  const hw = w / 2
  const hd = d / 2
  const step = pitch > 0 ? pitch : 10
  const heavy = step * 5
  const minor: number[] = []
  const major: number[] = []
  for (let x = step; x < hw; x += step) {
    const into = x % heavy === 0 ? major : minor
    into.push(x, -hd, 0, x, hd, 0, -x, -hd, 0, -x, hd, 0)
  }
  for (let y = step; y < hd; y += step) {
    const into = y % heavy === 0 ? major : minor
    into.push(-hw, y, 0, hw, y, 0, -hw, -y, 0, hw, -y, 0)
  }
  const cross = [0, -hd, 0, 0, hd, 0, -hw, 0, 0, hw, 0, 0] // where a part lands
  const border = [
    -hw, -hd, 0, hw, -hd, 0, hw, -hd, 0, hw, hd, 0,
    hw, hd, 0, -hw, hd, 0, -hw, hd, 0, -hw, -hd, 0,
  ]
  const colors = stageColors()
  const group = new Group()
  group.add(
    segments(minor, new LineBasicMaterial({ color: colors.gridMinor })),
    segments(major, new LineBasicMaterial({ color: colors.gridMajor })),
    segments(border, new LineBasicMaterial({ color: colors.gridBorder })),
    segments(cross, new LineBasicMaterial({ color: palette.accent, transparent: true, opacity: 0.35 }))
  )
  return group
}

/** The purge line is one first-layer bead wide, the way a printer actually lays it. */
export const PURGE_WIDTH = 1.2

/**
 * The bead a printer wipes along the front of the bed before it starts. Unit length in X so
 * the caller scales it in mm, and parked a bead in from the border so it reads as on the plate
 * rather than as part of the frame.
 */
export function purgeBead(d: number): Mesh {
  const bead = new Mesh(
    new BoxGeometry(1, PURGE_WIDTH, PURGE_WIDTH),
    new MeshBasicMaterial({ color: palette.accent, transparent: true, opacity: 0.9 })
  )
  bead.position.set(0, -d / 2 + PURGE_WIDTH * 2, PURGE_WIDTH / 2)
  return bead
}

const spanOf = (box: Box3) => {
  const size = box.getSize(new Vector3())
  return Math.max(size.x, size.y, size.z) || 10
}

/** v1's fit: iso direction, 2.1 of padding, near and far from the span (v1:1785-1804). */
export function frameCamera(camera: PerspectiveCamera, controls: OrbitControls, box: Box3): void {
  const mid = box.getCenter(new Vector3())
  const span = spanOf(box)
  const dist = (span / (2 * Math.tan(((camera.fov * Math.PI) / 180) / 2))) * 2.1
  const dir = [0.7, -0.75, 0.6] // v1's VIEWS.iso, used raw rather than normalized
  camera.up.set(0, 0, 1)
  camera.position.set(mid.x + dist * dir[0], mid.y + dist * dir[1], mid.z + dist * dir[2])
  controls.target.copy(mid)
  camera.near = span / 100
  camera.far = span * 100
  camera.updateProjectionMatrix()
  controls.update()
}

/**
 * True when this viewpoint can plausibly see the part: camera outside the solid, target
 * near it, distance in a sane band. A camera can go stale when the part changes shape
 * under it, and keeping one that fails this paints a blank canvas (v1:1738-1747).
 */
export function saneCamera(position: Vector3, target: Vector3, box: Box3): boolean {
  const span = spanOf(box)
  const dist = position.distanceTo(target)
  return (
    !box.containsPoint(position) &&
    box.clone().expandByScalar(span * 2).containsPoint(target) &&
    dist > span / 100 &&
    dist < span * 50
  )
}

/** sane() is a distance argument, not a visibility one, so the part must also be in frame (v1:1765-1770). */
export function cameraSeesBox(camera: PerspectiveCamera, box: Box3): boolean {
  camera.updateMatrixWorld()
  const frustum = new Frustum().setFromProjectionMatrix(
    new Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse)
  )
  return frustum.intersectsBox(box)
}

/** One Mesh per isMesh node, each with its own material, the clip plane and an edge overlay (v1:1908-1928). */
export function buildPartGroup(gltfScene: Object3D, plane: Plane, pal: Palette): Group {
  const found: Mesh[] = []
  gltfScene.traverse((o) => {
    if ((o as Mesh).isMesh) found.push(o as Mesh)
  })
  const group = new Group()
  for (const src of found) {
    const geometry = src.geometry
    if (!geometry.attributes.normal) geometry.computeVertexNormals() // never render unlit
    const material = new MeshStandardMaterial({
      color: pal.part,
      // Flat and matte: printed plastic, no specular sheen over the accent.
      metalness: 0,
      roughness: 0.85,
      // Pushed back a hair so the edge overlay draws without z-fighting the surface.
      polygonOffset: true,
      polygonOffsetFactor: 1,
      polygonOffsetUnits: 1,
      clippingPlanes: [plane],
    })
    // The builder tints bridge surfaces via vertex colors, multipliers over the material color.
    if (geometry.attributes.color) material.vertexColors = true
    const mesh = new Mesh(geometry, material)
    for (const m of ([] as Material[]).concat(src.material)) m.dispose() // the GLB's own, never drawn
    mesh.name = src.name || src.parent?.name || ""
    if (mesh.name === "context") {
      // Obstacles are scenery: the machine a part mounts to, the wall behind it. Grey-blue,
      // never the accent, because only the part being made is the part.
      material.color.setHex(pal.context)
      material.transparent = true
      material.opacity = 0.3
    } else {
      const outline = new LineSegments(
        new EdgesGeometry(geometry, EDGE_ANGLE),
        new LineBasicMaterial({ color: pal.edge, transparent: true, opacity: 0.35, clippingPlanes: [plane] })
      )
      mesh.add(outline)
    }
    group.add(mesh)
  }
  return group
}

const printed = (group: Group) => group.children.filter((c) => (c as Mesh).isMesh && c.name !== "context" && c.name !== "target")

/**
 * A part sits on the plate, centered, the way a slicer plates it. Where its own origin
 * falls is a modeling datum and nothing to do with printing (v1:1950-1960). Returns the
 * bounds in the plated position, the box every frame, cut and pin is measured against.
 */
export function plateGroup(group: Group): Box3 {
  group.position.set(0, 0, 0)
  group.updateMatrixWorld(true)
  const all = new Box3()
  for (const child of group.children) if (child.name !== "target") all.expandByObject(child)
  const floor = new Box3()
  for (const child of printed(group)) floor.expandByObject(child)
  if (floor.isEmpty()) floor.copy(all)
  const at = floor.getCenter(new Vector3())
  // Measured in world space, where the bed is, but stored in the parent's frame: the root
  // is rotated when the part's own up is not Z, and a world shift written as a local one
  // would be rotated a second time on its way back out.
  const shift = new Vector3(-at.x, -at.y, -floor.min.z)
  const parentQuaternion = group.parent ? group.parent.getWorldQuaternion(new Quaternion()) : new Quaternion()
  group.position.copy(shift).applyQuaternion(parentQuaternion.invert())
  group.updateMatrixWorld(true)
  return all.translate(shift)
}

/** The bounds the section slider spans: the printed children only, in world space (v1:1063-1066). */
export function printedBox(group: Group): Box3 {
  const box = new Box3()
  for (const child of printed(group)) box.expandByObject(child)
  return box
}

const stencilBase = {
  depthWrite: false,
  depthTest: false,
  colorWrite: false,
  stencilWrite: true,
  stencilFunc: AlwaysStencilFunc,
}

/** Back writers increment, front writers decrement; both share the child's world matrix so a posed joint drags them (v1:1044-1060). */
export function stencilWriters(child: Mesh, plane: Plane): Mesh[] {
  const back = new MeshBasicMaterial({
    ...stencilBase,
    clippingPlanes: [plane],
    side: BackSide,
    stencilFail: IncrementWrapStencilOp,
    stencilZFail: IncrementWrapStencilOp,
    stencilZPass: IncrementWrapStencilOp,
  })
  const front = new MeshBasicMaterial({
    ...stencilBase,
    clippingPlanes: [plane],
    side: FrontSide,
    stencilFail: DecrementWrapStencilOp,
    stencilZFail: DecrementWrapStencilOp,
    stencilZPass: DecrementWrapStencilOp,
  })
  return [back, front].map((material) => {
    const writer = new Mesh(child.geometry, material)
    writer.matrixAutoUpdate = false
    writer.matrix = child.matrixWorld
    writer.renderOrder = 1
    return writer
  })
}

/** The cut is painted only where the stencil says material passes the plane (v1:1013-1034). */
export function capMesh(): Mesh {
  const mesh = new Mesh(
    new PlaneGeometry(1, 1),
    new MeshStandardMaterial({
      // Violet, because the cap is the one surface that is not part material and must not
      // impersonate a signal: amber is a warn, red a fail, orange the part itself.
      color: palette.cap,
      metalness: 0,
      roughness: 0.85,
      side: DoubleSide,
      stencilWrite: true,
      stencilRef: 0,
      stencilFunc: NotEqualStencilFunc,
      stencilFail: ReplaceStencilOp,
      stencilZFail: ReplaceStencilOp,
      stencilZPass: ReplaceStencilOp,
    })
  )
  mesh.renderOrder = 1.1
  mesh.visible = false
  mesh.onAfterRender = (r) => r.clearStencil()
  return mesh
}

/** Places the cap over the cut: the part's center projected onto the plane, not coplanarPoint (v1:1084-1090). */
export function placeCap(cap: Mesh, plane: Plane, box: Box3): void {
  const span = box.getSize(new Vector3()).length()
  cap.scale.set(span, span, 1)
  plane.projectPoint(box.getCenter(new Vector3()), cap.position)
  cap.lookAt(cap.position.x - plane.normal.x, cap.position.y - plane.normal.y, cap.position.z - plane.normal.z)
}

/**
 * The face a rule fired on, painted onto the solid. Depth-tested, unlike the pins: a glow
 * seen through a wall would accuse the wrong face (v1:1000-1010).
 */
export function glowMesh(face: number[], severity: Severity, plane: Plane, pal: Palette): Mesh {
  const geometry = new BufferGeometry()
  geometry.setAttribute("position", new BufferAttribute(new Float32Array(face), 3))
  const material = new MeshBasicMaterial({
    color: severityColor(severity, pal),
    transparent: true,
    opacity: GLOW_OPACITY[severity],
    side: DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
    depthWrite: false,
    clippingPlanes: [plane],
  })
  return new Mesh(geometry, material)
}

/** The outline that says which finding is the emphasized one. */
export function glowOutline(face: number[], plane: Plane, pal: Palette): LineSegments {
  const geometry = new BufferGeometry()
  geometry.setAttribute("position", new BufferAttribute(new Float32Array(face), 3))
  const outline = new LineSegments(
    new EdgesGeometry(geometry, 1),
    new LineBasicMaterial({ color: pal.accent, depthTest: false, clippingPlanes: [plane] })
  )
  outline.renderOrder = 998
  geometry.dispose()
  return outline
}

/**
 * Pins draw through the solid on purpose: a rule reports a point on a face, so the pin
 * sits half inside the material and a marker you cannot see is worse than none (v1:798-808).
 */
export function pinMesh(where: [number, number, number], severity: Severity, scale: number, pal: Palette): Mesh {
  const material = new MeshBasicMaterial({ color: severityColor(severity, pal), depthTest: false, depthWrite: false })
  const pin = new Mesh(new SphereGeometry(1, 12, 8), material)
  pin.position.set(where[0], where[1], where[2])
  pin.scale.setScalar(scale)
  pin.renderOrder = 999 // per mesh, not on the group: a Group's renderOrder does not reach children
  return pin
}

const disposeMaterial = (material: Mesh["material"]) => {
  for (const m of Array.isArray(material) ? material : [material]) m.dispose()
}

/** The ghost's geometry is not ours to drop, so a child named `target` is skipped (v1:1904). */
export function disposeGroup(group: Object3D): void {
  group.traverse((o) => {
    const drawable = o as Mesh
    if (!drawable.geometry || o.name === "target") return
    drawable.geometry.dispose()
    disposeMaterial(drawable.material)
  })
}
