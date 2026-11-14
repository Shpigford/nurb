import { useEffect, useRef, useState, type JSX, type ReactNode } from "react"
import clsx from "clsx"
import {
  Box3,
  Color,
  DoubleSide,
  Group,
  Mesh,
  MeshStandardMaterial,
  PerspectiveCamera,
  Plane,
  Raycaster,
  Scene,
  Vector2,
  Vector3,
  WebGLRenderer,
} from "three"
import type { BufferGeometry, Material, Object3D } from "three"
import { OrbitControls } from "three/addons/controls/OrbitControls.js"
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js"
import type { Finding } from "../types"
import { duration, ease } from "../motion/tokens"
import {
  HIGHLIGHT_OPACITY,
  buildPartGroup,
  cameraSeesBox,
  capMesh,
  createLights,
  disposeGroup,
  frameCamera,
  glowMesh,
  glowOutline,
  palette,
  stageColors,
  pinMesh,
  plate,
  plateGroup,
  printedBox,
  purgeBead,
  saneCamera,
  stencilWriters,
} from "./scene"

export type Vec3 = [number, number, number]

export interface CameraState {
  position: Vec3
  target: Vec3
}

export interface Section {
  axis: "x" | "y" | "z"
  /** 0..1 along the axis; dragging right keeps more material */
  t: number
}

/** Page content pinned to a spot on the part: it rides along as the camera orbits. */
export interface ViewerAnchor {
  key: string
  /** In the part's own mm, the same space `onPick` reports. */
  point: Vec3
  node: ReactNode
}

export interface ViewerIslandProps {
  /** The part's GLB. Changing it swaps the geometry and keeps the camera. null clears the part. */
  glbUrl: string | null
  /** A reference mesh drawn as a translucent ghost, offset by `targetOffset`. */
  targetUrl?: string | null
  targetOffset?: Vec3
  findings?: Finding[]
  /** Index into `findings` of the one to emphasize. */
  highlight?: number | null
  /** Called when the user clicks a finding's glow (index) or empty space (null). */
  onHighlight?: (index: number | null) => void
  /** While set, a click on the part reports that spot instead, in the part's own mm. */
  onPick?: ((pick: { point: Vec3; normal: Vec3 }) => void) | null
  /** Printer bed [width, depth] in mm; null hides the plate. */
  bed?: [number, number] | null
  /** Print-up axis of the part's coordinates. Default [0,0,1]. */
  up?: Vec3
  section?: Section | null
  /** Drawn over the canvas, each with its top-left corner on its point. */
  anchors?: ViewerAnchor[]
  /** A view to restore, taken when it can still see the part; compared by value, so a parent may re-send it freely. */
  camera?: CameraState | null
  /** The user's orbits, debounced 250 ms after the last one. The component's own framing never reports. */
  onCamera?: (state: CameraState) => void
  /** Bump to nudge the view a notch around the part. Any new value nudges once; the first value never does. */
  settleKey?: number
  /** True once, on a project's first build, to lay the purge line across the front of the bed. */
  purge?: boolean
  className?: string
}

/** "off", without changing the clipping array's length and recompiling shaders (v1:960). */
const PARKED = 1e6

const AXES = { x: [1, 0, 0], y: [0, 1, 0], z: [0, 0, 1] } as const

/** The plate's normal minor spacing, in mm. */
const MM = 10
/** Gridfinity's unit, shown for GRIDFINITY_MS when the app asks for it. */
const GRIDFINITY_PITCH = 42
const GRIDFINITY_MS = 4000
/** A notch of azimuth, enough to read as a new angle without losing the pose you had. */
const NUDGE = Math.PI / 12
const PURGE_DRAW = 1.8
const PURGE_HOLD = 2
const PURGE_OPACITY = 0.9
/** How much stage an anchor wants to its right before it opens leftward instead. */
const ANCHOR_ROOM = 320

/** matchMedia is missing in jsdom and in a locked-down webview, and no answer means no preference. */
const reducedMotion = (): boolean => {
  try {
    return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false
  } catch {
    return false
  }
}

/** Solves a CSS cubic-bezier for y at x, so an rAF loop can move on the same curve the CSS tokens do. */
function eased(x: number, curve: readonly [number, number, number, number]): number {
  if (x <= 0) return 0
  if (x >= 1) return 1
  const [x1, y1, x2, y2] = curve
  const at = (t: number, a: number, b: number) => 3 * (1 - t) ** 2 * t * a + 3 * (1 - t) * t ** 2 * b + t ** 3
  let t = x
  for (let i = 0; i < 8; i++) {
    const dx = at(t, x1, x2) - x
    if (Math.abs(dx) < 1e-4) break
    const slope = 3 * (1 - t) ** 2 * x1 + 6 * (1 - t) * t * (x2 - x1) + 3 * t ** 2 * (1 - x2)
    if (Math.abs(slope) < 1e-6) break
    t -= dx / slope
  }
  return at(t, y1, y2)
}

type Fading = Material & { opacity: number; transparent: boolean; depthWrite: boolean }

interface Saved {
  material: Fading
  opacity: number
  transparent: boolean
  depthWrite: boolean
}

const collectMaterials = (root: Object3D): Saved[] => {
  const saved: Saved[] = []
  root.traverse((o) => {
    const held = (o as Mesh).material
    if (!held) return
    for (const material of (Array.isArray(held) ? held : [held]) as Fading[]) {
      saved.push({ material, opacity: material.opacity, transparent: material.transparent, depthWrite: material.depthWrite })
    }
  })
  return saved
}

const restoreMaterials = (saved: Saved[]) => {
  for (const s of saved) {
    s.material.opacity = s.opacity
    s.material.transparent = s.transparent
    s.material.depthWrite = s.depthWrite
  }
}

export interface CrossfadeOptions {
  seconds: number
  render: () => void
  /** Called once the fade lands, so the caller can remove and dispose the outgoing group. */
  onDone: () => void
  /** Injected by the tests; the component uses the real clock and rAF. */
  now?: () => number
  schedule?: (step: () => void) => number
  unschedule?: (id: number) => void
}

/**
 * Dissolves one group into another in place. Both keep their own transparency settings:
 * `transparent` is switched on only for the fade, because leaving it on would sort the part
 * against the whole scene for the rest of the session, and the outgoing group stops writing
 * depth so it cannot punch holes in the arriving one. Returns a cancel that restores the
 * survivor without calling onDone.
 */
export function crossfadeGroups(from: Object3D | null, to: Object3D | null, opts: CrossfadeOptions): () => void {
  const now = opts.now ?? (() => performance.now())
  const schedule = opts.schedule ?? ((step: () => void) => requestAnimationFrame(() => step()))
  const unschedule = opts.unschedule ?? ((id: number) => cancelAnimationFrame(id))
  const incoming = to ? collectMaterials(to) : []
  const outgoing = from ? collectMaterials(from) : []
  for (const s of incoming) {
    s.material.transparent = true
    s.material.opacity = 0
  }
  for (const s of outgoing) {
    s.material.transparent = true
    s.material.depthWrite = false
  }
  const start = now()
  const ms = Math.max(1, opts.seconds * 1000)
  let id = 0
  let live = true
  const step = () => {
    id = 0
    if (!live) return
    const p = Math.min(1, (now() - start) / ms)
    for (const s of incoming) s.material.opacity = s.opacity * p
    for (const s of outgoing) s.material.opacity = s.opacity * (1 - p)
    opts.render()
    if (p < 1) {
      id = schedule(step)
      return
    }
    live = false
    restoreMaterials(incoming)
    opts.onDone()
  }
  id = schedule(step)
  return () => {
    if (!live) return
    live = false
    if (id) unschedule(id)
    restoreMaterials(incoming)
  }
}

interface Holder {
  renderer: WebGLRenderer | null
  scene: Scene
  camera: PerspectiveCamera
  controls: OrbitControls | null
  plane: Plane
  root: Group
  marks: Group
  cap: Mesh
  part: Group | null
  /** The previous part, still drawn while it dissolves into the new one. */
  fading: { group: Group; cancel: () => void } | null
  ghost: Mesh | null
  plate: Group | null
  plateSize: [number, number] | null
  /** The plate's minor spacing in mm, normally MM and GRIDFINITY_PITCH while the app asks. */
  pitch: number
  purge: Mesh | null
  writers: Mesh[]
  glows: Mesh[]
  box: Box3
  size: number
  cutting: boolean
  cutAxis: "x" | "y" | "z"
  cutSign: number
  framed: boolean
  generation: number
  /** The generation whose GLB is on screen; findings wait for it to catch up. */
  loaded: number
  targetGeneration: number
  /** Set while the component itself moves the camera, so onCamera reports only the user's orbits. */
  quiet: boolean
  lastW: number
  lastH: number
  raf: number
  nudgeRaf: number
  purgeRaf: number
  camTimer: ReturnType<typeof setTimeout> | null
  render: () => void
  /** Moves each anchor's element to where its point lands on screen. */
  place: () => void
}

const sameCamera = (a: CameraState | null | undefined, b: CameraState | null | undefined) => {
  if (!a || !b) return a === b
  return a.position.every((v, i) => v === b.position[i]) && a.target.every((v, i) => v === b.target[i])
}

const firstGeometry = (scene: Object3D): BufferGeometry | null => {
  let geometry: BufferGeometry | null = null
  scene.traverse((o) => {
    if ((o as Mesh).isMesh && !geometry) geometry = (o as Mesh).geometry
  })
  return geometry
}

/** A restored camera is taken only when it can still plausibly see the part (v1:1749-1771). */
function applyCamera(h: Holder, state: CameraState, box: Box3): boolean {
  if (!h.controls) return false
  const position = new Vector3().fromArray(state.position)
  const target = new Vector3().fromArray(state.target)
  if (!saneCamera(position, target, box)) return false
  h.camera.position.copy(position)
  h.controls.target.copy(target)
  const size = box.getSize(new Vector3())
  const span = Math.max(size.x, size.y, size.z) || 10
  h.camera.near = span / 100
  h.camera.far = span * 100
  h.camera.updateProjectionMatrix()
  h.controls.update()
  return cameraSeesBox(h.camera, box)
}

/** A rebuild is a geometry swap, never a camera reset (v1:839). Nothing is written to the camera on the keep path, so the view does not drift by a float. */
function keepCamera(h: Holder, box: Box3): boolean {
  if (!h.controls) return false
  if (!saneCamera(h.camera.position, h.controls.target, box)) return false
  return cameraSeesBox(h.camera, box)
}

/** Damping decays the orbit delta but never zeroes it, so the next render after the orbit stops spends the leftover and the view drifts. Dropping it is the only way to keep the camera to the float; update() would spend it instead. */
function dropDamping(h: Holder): void {
  const held = h.controls as unknown as {
    _sphericalDelta?: { set(theta: number, phi: number, radius: number): void }
    _panOffset?: { set(x: number, y: number, z: number): void }
    _scale?: number
  } | null
  if (!held) return
  held._sphericalDelta?.set(0, 0, 0)
  held._panOffset?.set(0, 0, 0)
  held._scale = 1
}

/**
 * The grid lives under the part whether or not the project has picked a printer. With a bed
 * it is that bed; without one it is a square big enough to read as ground under what is
 * loaded, in 50mm steps. Nothing loaded and no bed draws nothing, because the workbench only
 * mounts the viewer once there is geometry to show.
 */
function syncPlate(h: Holder, bed: [number, number] | null | undefined): void {
  if (h.plate) {
    h.scene.remove(h.plate)
    disposeGroup(h.plate)
    h.plate = null
  }
  const size = bed ?? fittedBed(h)
  h.plateSize = size
  if (!size) return
  h.plate = plate(size, h.pitch)
  h.scene.add(h.plate)
}

function fittedBed(h: Holder): [number, number] | null {
  if (!h.part) return null
  // World space, because the root is rotated when the part's own up is not Z.
  const size = new Box3().setFromObject(h.part).getSize(new Vector3())
  const side = Math.max(100, Math.ceil((Math.max(size.x, size.y) * 1.8) / 50) * 50)
  return [side, side]
}

/** Plate the part and decide the camera: keep it when it still sees the part, else restore the caller's, else frame. */
function settle(h: Holder, wanted: CameraState | null | undefined): void {
  if (!h.part) return
  h.box = plateGroup(h.part)
  h.size = h.box.getSize(new Vector3()).length()
  h.quiet = true
  const taken = h.framed ? keepCamera(h, h.box) : wanted ? applyCamera(h, wanted, h.box) : false
  if (!taken && h.controls) frameCamera(h.camera, h.controls, h.box)
  h.quiet = false
  h.framed = true
}

/** A fade belongs to the generation that started it, so a newer build ends it now rather than stacking stale geometry. */
function finishFade(h: Holder): void {
  const held = h.fading
  if (!held) return
  h.fading = null
  held.cancel()
  h.root.remove(held.group)
  disposeGroup(held.group)
}

/**
 * A notch of azimuth around the part, on the coast curve. The camera stays where it lands:
 * a nudge is a look at the part from a new angle, and snapping back would undo the look.
 */
function nudgeAzimuth(h: Holder): void {
  const controls = h.controls
  if (!controls || reducedMotion()) return
  if (h.nudgeRaf) cancelAnimationFrame(h.nudgeRaf)
  const target = controls.target.clone()
  const base = h.camera.position.clone().sub(target)
  const axis = h.camera.up.clone().normalize()
  const start = performance.now()
  const ms = duration.coast * 1000
  h.quiet = true
  const step = () => {
    h.nudgeRaf = 0
    const p = Math.min(1, (performance.now() - start) / ms)
    if (p >= 1) h.quiet = false // the resting pose is the user's now, so it reports
    h.camera.position.copy(base).applyAxisAngle(axis, NUDGE * eased(p, ease.out)).add(target)
    controls.update()
    h.render()
    if (p < 1) h.nudgeRaf = requestAnimationFrame(step)
  }
  h.nudgeRaf = requestAnimationFrame(step)
}

function dropPurge(h: Holder): void {
  if (h.purgeRaf) cancelAnimationFrame(h.purgeRaf)
  h.purgeRaf = 0
  if (!h.purge) return
  h.scene.remove(h.purge)
  disposeGroup(h.purge)
  h.purge = null
}

/** The printer's first move, once: a bead of accent wiped left to right along the front of the bed. */
function runPurge(h: Holder): boolean {
  if (!h.plate || !h.plateSize || reducedMotion()) return false
  const [w, d] = h.plateSize
  const bead = purgeBead(d)
  h.purge = bead
  h.scene.add(bead)
  const material = bead.material as Fading
  const start = performance.now()
  const step = () => {
    h.purgeRaf = 0
    const t = (performance.now() - start) / 1000
    const length = Math.max(1e-3, w * eased(t / PURGE_DRAW, ease.out))
    bead.scale.x = length
    bead.position.x = -w / 2 + length / 2 // extruded from the left edge, never from the middle
    const out = t - PURGE_DRAW - PURGE_HOLD
    material.opacity = out <= 0 ? PURGE_OPACITY : PURGE_OPACITY * (1 - Math.min(1, out / duration.settle))
    h.render()
    if (out < duration.settle) {
      h.purgeRaf = requestAnimationFrame(step)
      return
    }
    dropPurge(h)
    h.render()
  }
  h.purgeRaf = requestAnimationFrame(step)
  return true
}

/**
 * The greeting is spent only once it has actually drawn. Before the GLB lands and
 * with no printer bed set there is no plate under it, so the run is tried again
 * when the part arrives.
 */
function tryPurge(h: Holder, wanted: boolean | undefined, done: { current: boolean }): void {
  if (!wanted || done.current) return
  done.current = runPurge(h)
}

function clearWriters(h: Holder) {
  for (const writer of h.writers) {
    h.scene.remove(writer)
    ;(writer.material as Material).dispose() // the geometry belongs to the part
  }
  h.writers = []
}

function attachWriters(h: Holder) {
  clearWriters(h)
  if (!h.part) return
  h.part.updateMatrixWorld(true)
  for (const child of h.part.children) {
    if (!(child as Mesh).isMesh || child.name === "context" || child.name === "target") continue
    for (const writer of stencilWriters(child as Mesh, h.plane)) {
      writer.visible = h.cutting
      h.scene.add(writer)
      h.writers.push(writer)
    }
  }
}

function applySection(h: Holder, section: Section | null | undefined) {
  if (!section) {
    h.cutting = false
    h.cutSign = 0
    h.cap.visible = false
    for (const writer of h.writers) writer.visible = false
    h.plane.constant = PARKED
    h.render()
    return
  }
  // The cut side is chosen once, from where the camera stood when the section opened or
  // the axis changed. A side that follows the camera swaps the surviving half mid-orbit (v1:1068-1073).
  if (!h.cutting || h.cutAxis !== section.axis) {
    h.cutting = true
    h.cutAxis = section.axis
    h.cutSign = 0
  }
  if (!h.part) {
    h.cap.visible = false
    h.plane.constant = PARKED
    h.render()
    return
  }
  const box = printedBox(h.part)
  const axis = section.axis
  const lo = box.min[axis]
  const hi = box.max[axis]
  if (!h.cutSign) h.cutSign = h.camera.position[axis] >= (lo + hi) / 2 ? 1 : -1
  const t = h.cutSign === 1 ? section.t : 1 - section.t
  // A hair inside the bounds at each end, so neither extreme is a cut through nothing (v1:1081).
  const at = lo + (hi - lo) * (0.02 + 0.96 * t)
  const dir = AXES[axis]
  h.plane.normal.set(-h.cutSign * dir[0], -h.cutSign * dir[1], -h.cutSign * dir[2])
  h.plane.constant = h.cutSign * at
  h.cap.visible = true
  for (const writer of h.writers) writer.visible = true
  const span = box.getSize(new Vector3()).length()
  h.cap.scale.set(span, span, 1)
  // Centered on the part, not on coplanarPoint, which is where the plane passes the world origin (v1:1084-1088).
  h.plane.projectPoint(box.getCenter(new Vector3()), h.cap.position)
  h.cap.lookAt(
    h.cap.position.x - h.plane.normal.x,
    h.cap.position.y - h.plane.normal.y,
    h.cap.position.z - h.plane.normal.z
  )
  h.render()
}

function rebuildMarks(h: Holder, findings: Finding[], highlight: number | null | undefined) {
  for (const child of h.marks.children) disposeGroup(child)
  h.marks.clear()
  h.glows = []
  if (!h.part) {
    h.render()
    return
  }
  const shift = h.part.position
  const scale = Math.max(0.6, h.size / 90)
  findings.forEach((finding, index) => {
    if (finding.face && finding.face.length) {
      const glow = glowMesh(finding.face, finding.severity, h.plane, palette)
      glow.position.copy(shift) // the same shift that plates the part
      glow.userData.finding = index
      if (index === highlight) {
        ;(glow.material as Material).opacity = HIGHLIGHT_OPACITY
        glow.add(glowOutline(finding.face, h.plane, palette))
      }
      h.marks.add(glow)
      h.glows.push(glow)
    }
    if (!finding.where) return
    const pin = pinMesh(
      [finding.where[0] + shift.x, finding.where[1] + shift.y, finding.where[2] + shift.z],
      finding.severity,
      scale,
      palette
    )
    h.marks.add(pin)
  })
  h.render()
}

export function ViewerIsland(props: ViewerIslandProps): JSX.Element {
  const { glbUrl, targetUrl, targetOffset, findings, highlight, bed, up, section, camera, settleKey, purge, className } = props
  const [gridfinity, setGridfinity] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const holderRef = useRef<Holder | null>(null)
  const downRef = useRef<[number, number] | null>(null)
  const appliedCamera = useRef<CameraState | null>(null)
  const latest = useRef(props)
  latest.current = props
  const purged = useRef(false)
  const anchorEls = useRef<(HTMLDivElement | null)[]>([])
  const anchors = props.anchors ?? []
  const anchorKey = anchors.map((a) => `${a.key}@${a.point.join(",")}`).join("|")

  useEffect(() => {
    holderRef.current?.render()
  }, [anchorKey])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const scene = new Scene()
    scene.background = new Color(stageColors().stage)
    const view = new PerspectiveCamera(45, 1, 0.1, 10000)
    view.up.set(0, 0, 1) // before OrbitControls, which reads it; never Object3D.DEFAULT_UP
    const root = new Group()
    const marks = new Group()
    root.add(marks)
    scene.add(root)
    for (const light of createLights()) scene.add(light)
    const cap = capMesh()
    scene.add(cap)

    const h: Holder = {
      renderer: null,
      scene,
      camera: view,
      controls: null,
      plane: new Plane(new Vector3(0, 0, -1), PARKED),
      root,
      marks,
      cap,
      part: null,
      fading: null,
      ghost: null,
      plate: null,
      plateSize: null,
      pitch: MM,
      purge: null,
      writers: [],
      glows: [],
      box: new Box3(),
      size: 0,
      cutting: false,
      cutAxis: "z",
      cutSign: 0,
      framed: false,
      generation: 0,
      loaded: 0,
      targetGeneration: 0,
      quiet: false,
      lastW: 0,
      lastH: 0,
      raf: 0,
      nudgeRaf: 0,
      purgeRaf: 0,
      camTimer: null,
      render: () => {},
      place: () => {},
    }
    holderRef.current = h
    ;(container as HTMLDivElement & { __nurbViewer?: Holder }).__nurbViewer = h

    try {
      // stencil: the section cap is a stencil pass and the buffer is off by default since
      // r163. Without it the cap silently never draws.
      h.renderer = new WebGLRenderer({ antialias: true, stencil: true })
    } catch {
      // No GPU is not a crash: everything but the picture still works.
      container.setAttribute("data-nogl", "")
    }

    const canvas = h.renderer?.domElement ?? null
    if (h.renderer && canvas) {
      h.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
      h.renderer.localClippingEnabled = true // per material, never renderer.clippingPlanes
      // Sized by CSS, never inline: setSize(w, h, false) must stay the only thing that
      // touches the drawing buffer. The renderer brings its own canvas because the
      // cleanup below loses its context, and a lost context cannot be reacquired on the
      // same element, which is what StrictMode's second mount would ask for.
      canvas.className = "block h-full w-full"
      container.appendChild(canvas)
      h.controls = new OrbitControls(view, canvas)
      h.controls.enableDamping = true
      // A release coasts for duration.coast. Damping is exponential, the residual velocity
      // times (1 - f) per update, so reaching 1% of the release velocity after 1.4 s at
      // 60 fps (84 frames) wants f = 1 - 0.01 ** (1 / 84) = 0.0533.
      h.controls.dampingFactor = 0.0533
    }

    // Render on demand. Damping needs frames, so the loop keeps going only while
    // controls.update() reports the camera is still moving.
    const frame = () => {
      h.raf = 0
      if (!h.renderer || !h.controls) return
      const moving = h.controls.update()
      if (!moving) dropDamping(h) // the loop parks here, and a rebuild's render must not resume the orbit
      h.renderer.render(scene, view)
      h.place()
      if (moving) h.render()
    }
    h.place = () => {
      const mesh = h.part?.children.find((o) => (o as Mesh).isMesh && o.name !== "context")
      for (const [i, anchor] of (latest.current.anchors ?? []).entries()) {
        const el = anchorEls.current[i]
        if (!el) continue
        const at = mesh ? mesh.localToWorld(new Vector3(...anchor.point)).project(view) : null
        // Behind the camera, or no part to stand on: nowhere to draw it.
        if (!at || at.z > 1) {
          el.style.visibility = "hidden"
          continue
        }
        const x = ((at.x + 1) / 2) * h.lastW
        // Near the right edge the content would run off the stage, so it opens leftward
        // from its point; the content reads data-flip to mirror itself.
        const flip = x > h.lastW - ANCHOR_ROOM
        el.toggleAttribute("data-flip", flip)
        el.style.visibility = "visible"
        el.style.transform = `translate(${x}px, ${((1 - at.y) / 2) * h.lastH}px)${flip ? " translateX(-100%)" : ""}`
      }
    }
    h.render = () => {
      if (!h.renderer || h.raf) return
      h.raf = requestAnimationFrame(frame)
    }

    const resize = (w: number, ht: number) => {
      const width = Math.floor(w)
      const height = Math.floor(ht)
      if (!width || !height || (width === h.lastW && height === h.lastH)) return
      h.lastW = width
      h.lastH = height
      // The third argument is the whole point: `true` writes inline px onto the canvas,
      // and that write-back is what ratchets the observer (v1:926-937).
      h.renderer?.setSize(width, height, false)
      view.aspect = width / height
      view.updateProjectionMatrix()
      h.render()
    }
    const observer = new ResizeObserver((entries) => {
      const rect = entries[entries.length - 1].contentRect
      resize(rect.width, rect.height)
    })
    observer.observe(container)
    resize(container.clientWidth, container.clientHeight)

    const onChange = () => {
      h.render()
      if (h.quiet) return
      if (h.camTimer) clearTimeout(h.camTimer)
      h.camTimer = setTimeout(() => {
        const report = latest.current.onCamera
        if (!report || !h.controls) return
        report({
          position: h.camera.position.toArray() as Vec3,
          target: h.controls.target.toArray() as Vec3,
        })
      }, 250)
    }
    h.controls?.addEventListener("change", onChange)

    // A theme switch repaints the stage and redraws the bed in place; the part keeps its colour.
    const themeWatch = new MutationObserver(() => {
      scene.background = new Color(stageColors().stage)
      if (h.plateSize) syncPlate(h, h.plateSize)
      h.render()
    })
    themeWatch.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] })

    return () => {
      themeWatch.disconnect()
      // StrictMode mounts, unmounts and mounts again, so a leaked context here is two contexts.
      observer.disconnect()
      if (h.raf) cancelAnimationFrame(h.raf)
      if (h.nudgeRaf) cancelAnimationFrame(h.nudgeRaf)
      if (h.camTimer) clearTimeout(h.camTimer)
      h.generation++
      h.targetGeneration++
      h.controls?.removeEventListener("change", onChange)
      h.controls?.dispose()
      clearWriters(h)
      dropPurge(h)
      for (const child of marks.children) disposeGroup(child)
      finishFade(h) // a group still dissolving is still geometry to give back
      if (h.part) disposeGroup(h.part)
      if (h.ghost) {
        h.ghost.geometry.dispose()
        ;(h.ghost.material as Material).dispose()
      }
      if (h.plate) disposeGroup(h.plate)
      disposeGroup(cap)
      h.renderer?.setAnimationLoop(null)
      h.renderer?.forceContextLoss()
      h.renderer?.dispose()
      canvas?.remove()
      delete (container as HTMLDivElement & { __nurbViewer?: Holder }).__nurbViewer
      holderRef.current = null
    }
  }, [])

  useEffect(() => {
    const h = holderRef.current
    if (!h || !h.controls) return
    const generation = ++h.generation
    finishFade(h) // an in-flight fade is a picture of two builds ago
    const drop = () => {
      if (!h.part) return
      h.root.remove(h.part)
      if (h.ghost) h.part.remove(h.ghost)
      disposeGroup(h.part)
      h.part = null
    }
    if (!glbUrl) {
      drop()
      syncPlate(h, latest.current.bed)
      clearWriters(h)
      rebuildMarks(h, [], null)
      applySection(h, latest.current.section)
      return
    }
    new GLTFLoader()
      .loadAsync(glbUrl)
      .then((gltf) => {
        // GLTFLoader has no abort, so a late arrival is dropped rather than shown.
        if (generation !== h.generation) {
          disposeGroup(gltf.scene)
          return
        }
        const part = buildPartGroup(gltf.scene, h.plane, palette)
        h.loaded = generation
        if (!part.children.length) {
          // A GLB with no mesh would plate to NaN and blank the viewer for good.
          drop()
          disposeGroup(part)
          clearWriters(h)
          rebuildMarks(h, [], null)
          applySection(h, latest.current.section)
          return
        }
        // The old part stays in the scene until the new one is in it too: dropping it first
        // is what made every rebuild blink.
        const previous = h.part
        if (previous && h.ghost) previous.remove(h.ghost)
        if (h.ghost) part.add(h.ghost)
        h.root.add(part)
        h.part = part
        settle(h, latest.current.camera)
        syncPlate(h, latest.current.bed)
        tryPurge(h, latest.current.purge, purged)
        appliedCamera.current = latest.current.camera ?? null
        attachWriters(h)
        applySection(h, latest.current.section)
        rebuildMarks(h, latest.current.findings ?? [], latest.current.highlight)
        if (previous && reducedMotion()) {
          h.root.remove(previous)
          disposeGroup(previous)
        } else if (previous) {
          h.fading = {
            group: previous,
            cancel: crossfadeGroups(previous, part, {
              seconds: duration.settle,
              render: h.render,
              onDone: () => {
                h.fading = null
                h.root.remove(previous)
                disposeGroup(previous)
                h.render()
              },
            }),
          }
        }
        h.render()
      })
      .catch((error: unknown) => {
        if (generation === h.generation) console.warn(`ViewerIsland: could not load ${glbUrl}`, error)
      })
  }, [glbUrl])

  const offsetKey = (targetOffset ?? [0, 0, 0]).join(",")
  useEffect(() => {
    const h = holderRef.current
    if (!h || !h.controls) return
    const generation = ++h.targetGeneration
    if (h.ghost) {
      h.ghost.parent?.remove(h.ghost)
      h.ghost.geometry.dispose()
      ;(h.ghost.material as Material).dispose()
      h.ghost = null
    }
    if (!targetUrl) {
      h.render()
      return
    }
    new GLTFLoader()
      .loadAsync(targetUrl)
      .then((gltf) => {
        if (generation !== h.targetGeneration) {
          disposeGroup(gltf.scene)
          return
        }
        const geometry = firstGeometry(gltf.scene)
        if (!geometry) return
        if (!geometry.attributes.normal) geometry.computeVertexNormals()
        // Amber against the part's orange, double-sided because a scan can be an open
        // surface, and never writing depth so the part reads through it (v1:843-848).
        const ghost = new Mesh(
          geometry,
          new MeshStandardMaterial({
            color: palette.ghost,
            metalness: 0,
            roughness: 0.9,
            transparent: true,
            opacity: 0.3,
            depthWrite: false,
            side: DoubleSide,
            clippingPlanes: [h.plane],
          })
        )
        ghost.name = "target"
        const offset = offsetKey.split(",").map(Number)
        ghost.position.set(offset[0], offset[1], offset[2])
        h.ghost = ghost
        h.part?.add(ghost)
        h.render()
      })
      .catch(() => {})
  }, [targetUrl, offsetKey])

  useEffect(() => {
    const h = holderRef.current
    if (!h || h.loaded !== h.generation) return // the load's own pass draws them on the new part
    rebuildMarks(h, findings ?? [], highlight)
  }, [findings, highlight])

  useEffect(() => {
    const h = holderRef.current
    if (!h) return
    syncPlate(h, bed)
    h.render()
  }, [bed?.[0], bed?.[1], !bed])

  const nudgedFrom = useRef(settleKey)
  useEffect(() => {
    const h = holderRef.current
    const previous = nudgedFrom.current
    nudgedFrom.current = settleKey
    // The value the component mounted with is the starting pose, not a request to move.
    if (!h || settleKey === undefined || settleKey === previous) return
    nudgeAzimuth(h)
  }, [settleKey])

  useEffect(() => {
    const h = holderRef.current
    if (!h) return
    tryPurge(h, purge, purged) // a bed that is not there yet still gets its one run later
  }, [purge, bed?.[0], bed?.[1]])

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null
    const onGridfinity = () => {
      setGridfinity(true)
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => setGridfinity(false), GRIDFINITY_MS)
    }
    window.addEventListener("nurb:gridfinity", onGridfinity)
    return () => {
      window.removeEventListener("nurb:gridfinity", onGridfinity)
      if (timer) clearTimeout(timer)
    }
  }, [])

  useEffect(() => {
    const h = holderRef.current
    if (!h) return
    h.pitch = gridfinity ? GRIDFINITY_PITCH : MM
    syncPlate(h, latest.current.bed)
    h.render()
  }, [gridfinity])

  const upKey = (up ?? [0, 0, 1]).join(",")
  useEffect(() => {
    const h = holderRef.current
    if (!h) return
    // Everything else in the scene is Z-up, so the part's own up is rotated into it.
    const from = new Vector3(...(upKey.split(",").map(Number) as Vec3)).normalize()
    h.root.quaternion.setFromUnitVectors(from, new Vector3(0, 0, 1))
    h.root.updateMatrixWorld(true)
    if (h.part) {
      settle(h, latest.current.camera)
      syncPlate(h, latest.current.bed)
      applySection(h, latest.current.section)
      rebuildMarks(h, latest.current.findings ?? [], latest.current.highlight)
    }
    h.render()
  }, [upKey])

  useEffect(() => {
    const h = holderRef.current
    if (!h) return
    applySection(h, section)
  }, [section])

  useEffect(() => {
    const h = holderRef.current
    if (!h || !h.part || !camera) return
    if (sameCamera(camera, appliedCamera.current)) return
    appliedCamera.current = camera
    h.quiet = true
    const taken = applyCamera(h, camera, h.box)
    h.quiet = false
    if (taken) h.render()
  }, [camera])

  return (
    <div
      ref={containerRef}
      className={clsx("relative block h-full w-full", props.onPick && "cursor-crosshair", className)}
      onPointerDown={(e) => {
        downRef.current = [e.clientX, e.clientY]
      }}
      onPointerUp={(e) => {
        const down = downRef.current
        downRef.current = null
        const h = holderRef.current
        const { onHighlight: report, onPick: pick } = latest.current
        // 5 px tells a click from the end of an orbit (v1's pick gate).
        if (!down || !h || (!report && !pick) || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return
        const rect = e.currentTarget.getBoundingClientRect()
        if (!rect.width || !rect.height) return
        const ndc = new Vector2(
          ((e.clientX - rect.left) / rect.width) * 2 - 1,
          -((e.clientY - rect.top) / rect.height) * 2 + 1
        )
        const ray = new Raycaster()
        ray.setFromCamera(ndc, h.camera)
        if (pick) {
          // The part's own meshes, never the scenery around it. Their vertices are the
          // GLB's, so the local hit point is the part's coordinates in mm.
          const meshes = (h.part?.children ?? []).filter((o) => (o as Mesh).isMesh && o.name !== "context")
          const spot = ray
            .intersectObjects(meshes, false)
            .find((i) => !h.cutting || h.plane.distanceToPoint(i.point) >= 0)
          if (spot?.face) {
            const at = spot.object.worldToLocal(spot.point.clone())
            const n = spot.face.normal
            pick({ point: [at.x, at.y, at.z], normal: [n.x, n.y, n.z] })
          }
          return
        }
        if (!report) return
        const hit = ray
          .intersectObjects(h.glows, false)
          .find((i) => !h.cutting || h.plane.distanceToPoint(i.point) >= 0)
        report(hit ? (hit.object.userData.finding as number) : null)
      }}
    >
      {anchors.map((anchor, i) => (
        <div
          key={anchor.key}
          ref={(el) => {
            anchorEls.current[i] = el
          }}
          className="group pointer-events-none absolute top-0 left-0 z-10 *:pointer-events-auto"
          style={{ visibility: "hidden" }}
          // The stage reads a pointer-up as a pick; a click on a tag is not one.
          onPointerDown={(e) => e.stopPropagation()}
          onPointerUp={(e) => e.stopPropagation()}
        >
          {anchor.node}
        </div>
      ))}
      {gridfinity && (
        <div className="mono-caption pointer-events-none absolute bottom-3 left-3 text-faint [letter-spacing:0.12em]">
          GRID 42.0 MM
        </div>
      )}
    </div>
  )
}

export default ViewerIsland
