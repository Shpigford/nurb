import * as Pn from "react";
import { useState as O, useRef as M, useEffect as F, useCallback as q, createContext as ht, useLayoutEffect as $t, useId as Se, useContext as se, useInsertionEffect as Bi, useMemo as le, Children as wc, isValidElement as kc, Fragment as $i, createElement as Tc, forwardRef as ji, Component as Sc } from "react";
import { jsx as c, jsxs as v, Fragment as G } from "react/jsx-runtime";
import R from "clsx";
import Ac from "react-markdown";
import { DirectionalLight as Nc, HemisphereLight as Pc, Mesh as Qe, PlaneGeometry as Mc, MeshStandardMaterial as Ui, ReplaceStencilOp as In, NotEqualStencilFunc as Cc, DoubleSide as Wi, Group as pn, LineSegments as _i, EdgesGeometry as Jo, LineBasicMaterial as it, BufferGeometry as zi, BufferAttribute as Gi, MeshBasicMaterial as Ct, SphereGeometry as Ec, Box3 as Et, Vector3 as fe, Quaternion as Hs, IncrementWrapStencilOp as On, BackSide as Dc, AlwaysStencilFunc as Vc, DecrementWrapStencilOp as Bn, FrontSide as Rc, Frustum as Lc, Matrix4 as Fc, BoxGeometry as Ic, Scene as Oc, Color as Bc, PerspectiveCamera as $c, Plane as jc, WebGLRenderer as Uc, Vector2 as Wc, Raycaster as _c } from "three";
import { OrbitControls as zc } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader as qs } from "three/addons/loaders/GLTFLoader.js";
import { createPortal as ea } from "react-dom";
const ta = {
  /** A soft two-note ascending bell, like an iOS/macOS confirmation tink. */
  chime: {
    masterGain: 0.5,
    layers: [
      { kind: "tone", waveform: "sine", frequency: 1046.5, attack: 6e-3, decay: 0.22, peak: 0.09 },
      { kind: "tone", waveform: "sine", frequency: 1568, offset: 0.09, attack: 6e-3, decay: 0.26, peak: 0.08 }
    ],
    shimmer: { delay: 0.12, feedback: 0.25, wet: 0.18, lowpass: 4e3 }
  },
  /** A quick ascending twinkle of four notes — bright and playful. */
  sparkle: {
    masterGain: 0.5,
    layers: [
      { kind: "tone", waveform: "sine", frequency: 1760, offset: 0, attack: 3e-3, decay: 0.09, peak: 0.045 },
      { kind: "tone", waveform: "sine", frequency: 2217, offset: 0.045, attack: 3e-3, decay: 0.09, peak: 0.04 },
      { kind: "tone", waveform: "sine", frequency: 2637, offset: 0.09, attack: 3e-3, decay: 0.1, peak: 0.038 },
      { kind: "tone", waveform: "sine", frequency: 3520, offset: 0.135, attack: 3e-3, decay: 0.12, peak: 0.032 }
    ],
    shimmer: { delay: 0.07, feedback: 0.35, wet: 0.22, lowpass: 6e3 }
  },
  /** A single note gliding smoothly downward, like a drop of water. */
  droplet: {
    masterGain: 0.55,
    layers: [
      { kind: "tone", waveform: "sine", frequency: 1200, glideTo: 550, glideTime: 0.14, attack: 4e-3, decay: 0.2, peak: 0.075 }
    ],
    shimmer: { delay: 0.09, feedback: 0.2, wet: 0.15, lowpass: 3e3 }
  },
  /** A warm, slow-swelling pad from two gently detuned sines. */
  bloom: {
    masterGain: 0.5,
    layers: [
      { kind: "tone", waveform: "sine", frequency: 528, attack: 0.06, decay: 0.32, peak: 0.06 },
      { kind: "tone", waveform: "sine", frequency: 528, detune: 12, attack: 0.06, decay: 0.34, peak: 0.05 }
    ],
    shimmer: { delay: 0.15, feedback: 0.2, wet: 0.12, lowpass: 2500 }
  },
  /** A soft hush with a falling tone — for tooltips and low-priority previews. */
  whisper: {
    masterGain: 0.48,
    layers: [
      { kind: "noise", filterType: "lowpass", filterFrequency: 1600, filterQ: 0.7, attack: 0.025, decay: 0.13, peak: 0.04 },
      { kind: "tone", waveform: "sine", frequency: 880, glideTo: 660, glideTime: 0.14, offset: 0.01, attack: 0.012, decay: 0.14, peak: 0.025 }
    ]
  },
  /** A focused, bandpass-filtered tick with a bright sine ping on top — crisp and instant. */
  tick: {
    masterGain: 0.4,
    layers: [
      { kind: "noise", filterType: "bandpass", filterFrequency: 5400, filterQ: 1.8, attack: 1e-3, decay: 0.018, peak: 0.14 },
      { kind: "tone", waveform: "sine", frequency: 2600, attack: 1e-3, decay: 0.012, peak: 0.018 }
    ]
  },
  /** A dull, muted knock — the "down" half of a press/release pair, like a key bottoming out. */
  press: {
    masterGain: 0.4,
    layers: [
      { kind: "noise", filterType: "bandpass", filterFrequency: 1700, filterQ: 1.4, attack: 1e-3, decay: 0.02, peak: 0.13 }
    ]
  },
  /** A brighter, springier tick — the "up" half of a press/release pair, like a key returning. */
  release: {
    masterGain: 0.4,
    layers: [
      { kind: "noise", filterType: "bandpass", filterFrequency: 4600, filterQ: 1.8, attack: 1e-3, decay: 0.016, peak: 0.12 },
      { kind: "tone", waveform: "sine", frequency: 3200, offset: 6e-3, attack: 1e-3, decay: 0.05, peak: 0.02 }
    ]
  },
  /** A two-part click-clack, like a mechanical switch flipping between states. */
  toggle: {
    masterGain: 0.4,
    layers: [
      { kind: "noise", filterType: "bandpass", filterFrequency: 2200, filterQ: 1.6, attack: 1e-3, decay: 0.016, peak: 0.12 },
      { kind: "noise", filterType: "bandpass", filterFrequency: 3800, filterQ: 1.6, offset: 0.024, attack: 1e-3, decay: 0.02, peak: 0.1 }
    ]
  },
  /** A short, warm three-note ascending confirmation — "done", not a fanfare. */
  success: {
    masterGain: 0.5,
    layers: [
      { kind: "tone", waveform: "sine", frequency: 880, attack: 4e-3, decay: 0.09, peak: 0.06 },
      { kind: "tone", waveform: "sine", frequency: 1108.73, offset: 0.06, attack: 4e-3, decay: 0.1, peak: 0.06 },
      { kind: "tone", waveform: "sine", frequency: 1318.51, offset: 0.12, attack: 4e-3, decay: 0.18, peak: 0.07 }
    ],
    shimmer: { delay: 0.1, feedback: 0.22, wet: 0.16, lowpass: 4500 }
  },
  /** A muted knock followed by two descending tones — a calm, recoverable refusal. */
  error: {
    masterGain: 0.42,
    layers: [
      { kind: "noise", filterType: "bandpass", filterFrequency: 850, filterQ: 1.1, attack: 1e-3, decay: 0.035, peak: 0.13 },
      { kind: "tone", waveform: "triangle", frequency: 440, offset: 0.025, attack: 4e-3, decay: 0.09, peak: 0.045 },
      { kind: "tone", waveform: "triangle", frequency: 349.23, offset: 0.1, attack: 4e-3, decay: 0.14, peak: 0.04 }
    ]
  },
  /** A papery filtered flick with a tiny glass tick — for pages, galleries, and carousels. */
  page: {
    masterGain: 0.38,
    layers: [
      { kind: "noise", filterType: "lowpass", filterFrequency: 1800, filterQ: 0.7, attack: 6e-3, decay: 0.08, peak: 0.11 },
      { kind: "noise", filterType: "bandpass", filterFrequency: 4200, filterQ: 1.2, offset: 0.04, attack: 4e-3, decay: 0.065, peak: 0.08 },
      { kind: "tone", waveform: "sine", frequency: 2400, offset: 0.075, attack: 2e-3, decay: 0.045, peak: 0.02 }
    ]
  },
  /** A brief unresolved lift — signals that user-initiated work has started. */
  loading: {
    masterGain: 0.42,
    layers: [
      { kind: "noise", filterType: "lowpass", filterFrequency: 1400, filterQ: 0.6, attack: 0.035, decay: 0.14, peak: 0.035 },
      { kind: "tone", waveform: "sine", frequency: 420, glideTo: 630, glideTime: 0.18, attack: 0.025, decay: 0.18, peak: 0.05 }
    ],
    shimmer: { delay: 0.11, feedback: 0.18, wet: 0.12, lowpass: 2800 }
  },
  /** A quick lock-on sweep resolving to a clear tone — the system is ready. */
  ready: {
    masterGain: 0.48,
    layers: [
      { kind: "noise", filterType: "bandpass", filterFrequency: 3600, filterQ: 1.8, attack: 1e-3, decay: 0.02, peak: 0.11 },
      { kind: "tone", waveform: "triangle", frequency: 330, glideTo: 660, glideTime: 0.12, offset: 0.012, attack: 4e-3, decay: 0.16, peak: 0.055 },
      { kind: "tone", waveform: "sine", frequency: 990, offset: 0.13, attack: 4e-3, decay: 0.22, peak: 0.06 }
    ],
    shimmer: { delay: 0.1, feedback: 0.16, wet: 0.1, lowpass: 4200 }
  },
  /** A compact synthetic chirp — crisp feedback for primary buttons and controls. */
  pulse: {
    masterGain: 0.42,
    layers: [
      { kind: "noise", filterType: "bandpass", filterFrequency: 2600, filterQ: 2.4, attack: 1e-3, decay: 0.022, peak: 0.08 },
      { kind: "tone", waveform: "triangle", frequency: 620, glideTo: 1240, glideTime: 0.07, attack: 2e-3, decay: 0.085, peak: 0.055 }
    ]
  },
  /** A fast three-step locator signal — playful feedback for menus and secondary buttons. */
  scan: {
    masterGain: 0.4,
    layers: [
      { kind: "tone", waveform: "sine", frequency: 740, attack: 2e-3, decay: 0.055, peak: 0.05 },
      { kind: "tone", waveform: "sine", frequency: 1110, offset: 0.045, attack: 2e-3, decay: 0.055, peak: 0.045 },
      { kind: "tone", waveform: "sine", frequency: 1665, offset: 0.09, attack: 2e-3, decay: 0.07, peak: 0.04 }
    ],
    shimmer: { delay: 0.065, feedback: 0.16, wet: 0.1, lowpass: 4200 }
  },
  /** A rising harmonic portal with a soft tail — for client-side page arrivals. */
  arrival: {
    masterGain: 0.44,
    layers: [
      { kind: "noise", filterType: "lowpass", filterFrequency: 900, filterQ: 0.8, attack: 0.05, decay: 0.24, peak: 0.035 },
      { kind: "tone", waveform: "sine", frequency: 220, glideTo: 440, glideTime: 0.32, attack: 0.04, decay: 0.34, peak: 0.055 },
      { kind: "tone", waveform: "sine", frequency: 659.25, offset: 0.12, attack: 0.045, decay: 0.32, peak: 0.04 },
      { kind: "tone", waveform: "sine", frequency: 987.77, offset: 0.19, attack: 0.045, decay: 0.34, peak: 0.032 }
    ],
    shimmer: { delay: 0.16, feedback: 0.28, wet: 0.18, lowpass: 3200 }
  }
};
function Gc(e) {
  return typeof e == "string" && Object.prototype.hasOwnProperty.call(ta, e);
}
const Ki = 0.05, Kc = 0.05, Hc = 1e-3, qc = 4;
function Yc(e, t, n, i) {
  const s = e.createOscillator();
  if (s.type = n.waveform, s.frequency.setValueAtTime(n.frequency, i), n.detune && (s.detune.value = n.detune), n.glideTo !== void 0) {
    const o = n.glideTime ?? n.attack + n.decay;
    s.frequency.exponentialRampToValueAtTime(n.glideTo, i + o);
  }
  const r = e.createGain();
  r.gain.setValueAtTime(1e-4, i), r.gain.exponentialRampToValueAtTime(n.peak, i + n.attack), r.gain.exponentialRampToValueAtTime(1e-4, i + n.attack + n.decay), s.connect(r).connect(t), s.start(i), s.stop(i + n.attack + n.decay + Ki);
}
function Xc(e, t, n, i) {
  const s = n.attack + n.decay + Ki, r = Math.max(1, Math.floor(s * e.sampleRate)), o = e.createBuffer(1, r, e.sampleRate), a = o.getChannelData(0);
  for (let h = 0; h < r; h++)
    a[h] = 2 * Math.random() - 1;
  const l = e.createBufferSource();
  l.buffer = o;
  const u = e.createBiquadFilter();
  u.type = n.filterType, u.frequency.value = n.filterFrequency, n.filterQ !== void 0 && (u.Q.value = n.filterQ);
  const d = e.createGain();
  d.gain.setValueAtTime(1e-4, i), d.gain.exponentialRampToValueAtTime(n.peak, i + n.attack), d.gain.exponentialRampToValueAtTime(1e-4, i + n.attack + n.decay), l.connect(u).connect(d).connect(t), l.start(i), l.stop(i + s);
}
function Zc(e, t, n, i) {
  const s = e.createDelay(1);
  s.delayTime.value = i.delay;
  const r = e.createBiquadFilter();
  r.type = "lowpass", r.frequency.value = i.lowpass;
  const o = e.createGain();
  o.gain.value = i.feedback;
  const a = e.createGain();
  return a.gain.value = i.wet, t.connect(s), s.connect(r), r.connect(o), o.connect(s), r.connect(a), a.connect(n), [s, r, o, a];
}
function Qc(e) {
  return Math.max(...e.layers.map((t) => (t.offset ?? 0) + t.attack + t.decay + Ki));
}
function Jc(e) {
  return !e || e.feedback <= 0 ? 0 : e.feedback >= 1 ? e.delay : e.delay * (1 + Math.ceil(Math.log(Hc) / Math.log(e.feedback)));
}
let $n = null;
function eu(e) {
  if ($n)
    return $n;
  const t = e.createGain();
  t.gain.value = qc;
  const n = e.createDynamicsCompressor();
  return n.threshold.value = -8, n.knee.value = 6, n.ratio.value = 12, n.attack.value = 2e-3, n.release.value = 0.08, t.connect(n).connect(e.destination), $n = t, t;
}
function Ys(e, t, n) {
  const i = e.currentTime, s = eu(e), r = e.createGain();
  r.gain.value = t.masterGain * n, r.connect(s);
  const o = t.shimmer ? Zc(e, r, s, t.shimmer) : [];
  for (const l of t.layers) {
    const u = i + (l.offset ?? 0);
    l.kind === "tone" ? Yc(e, r, l, u) : Xc(e, r, l, u);
  }
  const a = (Qc(t) + Jc(t.shimmer) + Kc) * 1e3;
  setTimeout(() => {
    r.disconnect();
    for (const l of o)
      l.disconnect();
  }, a);
}
let qt = null, ai = !0, li = 1;
function na(e, t) {
  return typeof e == "number" && Number.isFinite(e) ? Math.min(1, Math.max(0, e)) : t;
}
function tu(e) {
  typeof e == "boolean" && (ai = e);
}
function nu(e) {
  li = na(e, li);
}
function iu() {
  if (qt)
    return qt;
  if (typeof window > "u")
    return null;
  const e = window.AudioContext ?? window.webkitAudioContext;
  if (!e)
    return null;
  try {
    qt = new e();
  } catch {
    return null;
  }
  return qt;
}
function su(e = "chime", t) {
  if (!ai || !Gc(e) || typeof navigator < "u" && navigator.userActivation?.hasBeenActive === !1)
    return;
  const n = li * na(t?.volume, 1);
  if (n === 0)
    return;
  const i = iu();
  if (!i)
    return;
  const s = ta[e];
  if (i.state === "running")
    Ys(i, s, n);
  else
    try {
      i.resume().then(() => {
        ai && i.state === "running" && Ys(i, s, n);
      }, () => {
      });
    } catch {
    }
}
const lt = "nurb-sound-enabled", Hi = "nurb-sound-volume", Xs = "nurb-completion-sound", qi = 0.6;
function Ge(e) {
  try {
    return localStorage.getItem(e);
  } catch {
    return null;
  }
}
function mn(e, t) {
  try {
    t === null ? localStorage.removeItem(e) : localStorage.setItem(e, t);
  } catch {
  }
}
function Yi(e) {
  return Number.isFinite(e) ? Math.min(1, Math.max(0, e)) : qi;
}
function py() {
  const e = Ge(Xs);
  e !== null && (e === "off" && Ge(lt) === null && mn(lt, "off"), mn(Xs, null));
  const t = Ge(lt) !== "off", n = Ge(Hi), i = n === null ? qi : Yi(Number(n));
  return Xi(t, i), { enabled: t, volume: i };
}
function my(e) {
  mn(lt, e ? null : "off"), Xi(e, ru());
}
function gy(e) {
  const t = Yi(e);
  mn(Hi, String(t)), Xi(Ge(lt) !== "off", t);
}
function ru() {
  const e = Ge(Hi);
  return e === null ? qi : Yi(Number(e));
}
function Xi(e, t) {
  try {
    tu(e), nu(t);
  } catch {
  }
}
function $e(e, t) {
  if (!(typeof window > "u") && Ge(lt) !== "off")
    try {
      su(e, t);
    } catch {
    }
}
const U = {
  tick: 0.09,
  settle: 0.24,
  arrive: 0.42,
  coast: 1.4
}, Y = {
  out: [0.23, 1, 0.32, 1],
  inOut: [0.65, 0, 0.35, 1]
};
function yy({ timeout: e = 1500, onCopy: t, onError: n } = {}) {
  const [i, s] = O("idle"), r = M(null);
  F(() => () => {
    r.current && clearTimeout(r.current);
  }, []);
  const o = q(
    (l) => {
      s(l), r.current && clearTimeout(r.current), r.current = setTimeout(() => s("idle"), e);
    },
    [e]
  ), a = q(
    async (l) => {
      try {
        if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(l);
        else if (!ou(l)) throw new Error("clipboard unavailable");
        $e("success"), t?.(l), o("copied");
      } catch (u) {
        $e("error"), n?.(u), o("error");
      }
    },
    [t, n, o]
  );
  return { status: i, copy: a };
}
function ou(e) {
  const t = document.createElement("textarea");
  t.value = e, t.setAttribute("readonly", ""), t.style.position = "fixed", t.style.opacity = "0", document.body.appendChild(t);
  try {
    return t.select(), document.execCommand("copy");
  } finally {
    t.remove();
  }
}
const au = {
  "chevron-left": /* @__PURE__ */ c("polyline", { points: "7.75 1.75 3.5 6 7.75 10.25" }),
  "chevron-down": /* @__PURE__ */ c("polyline", { points: "1.75 4.25 6 8.5 10.25 4.25" }),
  "chevron-up": /* @__PURE__ */ c("polyline", { points: "10.25 7.75 6 3.5 1.75 7.75" }),
  check: /* @__PURE__ */ c("path", { d: "m1.76,7.004l2.25,3L10.24,1.746" }),
  warning: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("circle", { cx: "6", cy: "10.125", r: ".875", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("line", { x1: "6", y1: "4.75", x2: "6", y2: "7.75" }),
    /* @__PURE__ */ c("path", { d: "m8.625,10.25h1.164c1.123,0,1.826-1.216,1.265-2.189L7.265,1.484c-.562-.975-1.969-.975-2.53,0L.946,8.061c-.561.973.142,2.189,1.265,2.189h1.164" })
  ] }),
  lock: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("line", { x1: "6", y1: "7.5", x2: "6", y2: "8.5" }),
    /* @__PURE__ */ c("path", { d: "m3.75,4.75v-1.75c0-1.243,1.007-2.25,2.25-2.25h0c1.243,0,2.25,1.007,2.25,2.25v1.75" }),
    /* @__PURE__ */ c("rect", { x: "1.25", y: "4.75", width: "9.5", height: "6.5", rx: "1.5", ry: "1.5" })
  ] }),
  plus: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("line", { x1: "10.75", y1: "6", x2: "1.25", y2: "6" }),
    /* @__PURE__ */ c("line", { x1: "6", y1: "10.75", x2: "6", y2: "1.25" })
  ] }),
  minus: /* @__PURE__ */ c("line", { x1: "10.75", y1: "6", x2: "1.25", y2: "6" }),
  camera: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("circle", { cx: "3.25", cy: "5.75", r: ".75", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("rect", { x: ".75", y: "3.25", width: "10.5", height: "8", rx: "2", ry: "2" }),
    /* @__PURE__ */ c("line", { x1: "2.75", y1: ".75", x2: "4.75", y2: ".75" }),
    /* @__PURE__ */ c("circle", { cx: "7.25", cy: "7.25", r: "1", fill: "currentColor" })
  ] }),
  search: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("line", { x1: "7.652", y1: "7.652", x2: "10.75", y2: "10.75" }),
    /* @__PURE__ */ c("circle", { cx: "5", cy: "5", r: "3.75" })
  ] }),
  xmark: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("line", { x1: "2.25", y1: "9.75", x2: "9.75", y2: "2.25" }),
    /* @__PURE__ */ c("line", { x1: "9.75", y1: "9.75", x2: "2.25", y2: "2.25" })
  ] }),
  image: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("path", { d: "m2.32,10.516l4.723-4.723c.391-.391,1.024-.391,1.414,0l2.293,2.293" }),
    /* @__PURE__ */ c("circle", { cx: "4", cy: "4", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("rect", { x: "1.25", y: "1.25", width: "9.5", height: "9.5", rx: "2", ry: "2" })
  ] }),
  download: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("line", { x1: "6", y1: "7.75", x2: "6", y2: ".75" }),
    /* @__PURE__ */ c("polyline", { points: "3.75 5.75 6 8 8.25 5.75" }),
    /* @__PURE__ */ c("path", { d: "m8.69,2.75c1.028,0,1.888.779,1.99,1.801l.35,3.5c.118,1.177-.807,2.199-1.99,2.199H2.96c-1.183,0-2.108-1.022-1.99-2.199l.35-3.5c.102-1.022.963-1.801,1.99-1.801" })
  ] }),
  expand: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("path", { d: "m1.25,4.25v-1c0-1.105.895-2,2-2h1" }),
    /* @__PURE__ */ c("path", { d: "m7.75,1.25h1c1.105,0,2,.895,2,2v1" }),
    /* @__PURE__ */ c("path", { d: "m10.75,7.75v1c0,1.105-.895,2-2,2h-1" }),
    /* @__PURE__ */ c("path", { d: "m4.25,10.75h-1c-1.105,0-2-.895-2-2v-1" })
  ] }),
  eye: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("path", { d: "M5.99997 10.25C8.64947 10.25 10.2021 8.38538 10.9485 7.12628C11.3599 6.43238 11.3599 5.56762 10.9485 4.87372C10.2021 3.61462 8.64937 1.75 5.99997 1.75C3.42267 1.75 1.87667 3.53288 1.10727 4.78918C0.649466 5.53658 0.649466 6.46338 1.10727 7.21088C1.87667 8.46718 3.42267 10.25 5.99997 10.25Z" }),
    /* @__PURE__ */ c("circle", { cx: "6", cy: "6", r: "1.25", fill: "currentColor" })
  ] }),
  "arrow-up": /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("line", { x1: "6", y1: "11", x2: "6", y2: "1.25" }),
    /* @__PURE__ */ c("polyline", { points: "9.25 4.25 6 1 2.75 4.25" })
  ] }),
  link: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("path", { d: "M7 7C7.97631 6.02369 7.97631 4.44078 7 3.46447L5.55292 2.01788C4.57661 1.04157 2.9937 1.04157 2.01739 2.01788C1.05869 2.97658 1.0414 4.5202 1.96552 5.5" }),
    /* @__PURE__ */ c("path", { d: "M5 5C4.02369 5.97631 4.02369 7.55922 5 8.53553L6.44197 9.97758C7.41828 10.9539 9.00119 10.9539 9.9775 9.97758C10.9347 9.02036 10.9534 7.48002 10.0336 6.5" })
  ] }),
  stop: /* @__PURE__ */ c(
    "path",
    {
      d: "M3.75 11C2.23122 11 1 9.76878 1 8.25V3.75C1 2.23122 2.23122 1 3.75 1L8.25 1C9.76878 1 11 2.23122 11 3.75V8.25C11 9.76878 9.76878 11 8.25 11H3.75Z",
      fill: "currentColor",
      stroke: "none"
    }
  ),
  chat: /* @__PURE__ */ c("path", { d: "m8.75,8.75h-4.75l-2.75,2.5V3.25c0-1.105.895-2,2-2h5.5c1.105,0,2,.895,2,2v3.5c0,1.105-.895,2-2,2Z" }),
  loader: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("path", { d: "M6 2.25V0.75" }),
    /* @__PURE__ */ c("path", { opacity: "0.5", d: "M6 11.25V9.75" }),
    /* @__PURE__ */ c("path", { opacity: "0.75", d: "M9.75488 5.995L11.2549 5.995" }),
    /* @__PURE__ */ c("path", { opacity: "0.25", d: "M0.754883 5.995L2.25488 5.995" }),
    /* @__PURE__ */ c("path", { opacity: "0.88", d: "M8.65321 3.3449L9.71387 2.28424" }),
    /* @__PURE__ */ c("path", { opacity: "0.38", d: "M2.28895 9.70885L3.34961 8.64819" }),
    /* @__PURE__ */ c("path", { opacity: "0.63", d: "M8.66004 8.64811L9.7207 9.70877" }),
    /* @__PURE__ */ c("path", { opacity: "0.13", d: "M2.29627 2.28416L3.35693 3.34482" })
  ] }),
  dots: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("circle", { cx: "6", cy: "6", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("circle", { cx: "2", cy: "6", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("circle", { cx: "10", cy: "6", r: "1", fill: "currentColor", stroke: "none" })
  ] }),
  trash: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("line", { x1: "1", y1: "2.25", x2: "11", y2: "2.25" }),
    /* @__PURE__ */ c("path", { d: "m4.75,2.25v-1c0-.276.224-.5.5-.5h1.5c.276,0,.5.224.5.5v1" }),
    /* @__PURE__ */ c("path", { d: "m9.5,4.75l-.195,5.058c-.031.805-.693,1.442-1.499,1.442h-3.613c-.806,0-1.468-.637-1.499-1.442l-.195-5.058" })
  ] }),
  ruler: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("line", { x1: "6.623", y1: "6.623", x2: "7.754", y2: "7.754" }),
    /* @__PURE__ */ c("line", { x1: "7.873", y1: "4.373", x2: "9.504", y2: "6.004" }),
    /* @__PURE__ */ c("line", { x1: "4.373", y1: "7.873", x2: "6.004", y2: "9.504" }),
    /* @__PURE__ */ c("rect", { x: ".42", y: "3.52", width: "11.161", height: "4.96", rx: "1.086", ry: "1.086", transform: "translate(-2.485 6) rotate(-45)" })
  ] }),
  gear: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("circle", { cx: "6", cy: "6", r: ".75", fill: "currentColor" }),
    /* @__PURE__ */ c("circle", { cx: "6", cy: "6", r: "4" }),
    /* @__PURE__ */ c("line", { x1: "6", y1: ".75", x2: "6", y2: "2" }),
    /* @__PURE__ */ c("line", { x1: "9.086", y1: "1.753", x2: "8.351", y2: "2.764" }),
    /* @__PURE__ */ c("line", { x1: "10.993", y1: "4.378", x2: "9.804", y2: "4.764" }),
    /* @__PURE__ */ c("line", { x1: "10.993", y1: "7.622", x2: "9.804", y2: "7.236" }),
    /* @__PURE__ */ c("line", { x1: "9.086", y1: "10.247", x2: "8.351", y2: "9.236" }),
    /* @__PURE__ */ c("line", { x1: "6", y1: "11.25", x2: "6", y2: "10" }),
    /* @__PURE__ */ c("line", { x1: "2.914", y1: "10.247", x2: "3.649", y2: "9.236" }),
    /* @__PURE__ */ c("line", { x1: "1.007", y1: "7.622", x2: "2.196", y2: "7.236" }),
    /* @__PURE__ */ c("line", { x1: "1.007", y1: "4.378", x2: "2.196", y2: "4.764" }),
    /* @__PURE__ */ c("line", { x1: "2.914", y1: "1.753", x2: "3.649", y2: "2.764" })
  ] }),
  user: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("circle", { cx: "6", cy: "2.491", r: "1.75" }),
    /* @__PURE__ */ c("path", { d: "m9.425,10.458c.551-.255.759-.92.458-1.446-.773-1.349-2.215-2.262-3.882-2.262s-3.11.912-3.882,2.262c-.301.526-.093,1.192.458,1.446,2.283,1.056,4.566,1.056,6.849,0Z" })
  ] }),
  logout: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("path", { d: "M5.75 3.25V2.25c0-.828.672-1.5 1.5-1.5h2.5c.828 0 1.5.672 1.5 1.5v7.5c0 .828-.672 1.5-1.5 1.5h-2.5c-.828 0-1.5-.672-1.5-1.5v-1" }),
    /* @__PURE__ */ c("line", { x1: "8.25", y1: "6", x2: "1", y2: "6" }),
    /* @__PURE__ */ c("polyline", { points: "3 3.75 .75 6 3 8.25" })
  ] }),
  box: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("line", { x1: "1.25", y1: "3.75", x2: "10.75", y2: "3.75" }),
    /* @__PURE__ */ c("line", { x1: "6", y1: ".75", x2: "6", y2: "3.75" }),
    /* @__PURE__ */ c("line", { x1: "3.75", y1: "8.25", x2: "5.25", y2: "8.25" }),
    /* @__PURE__ */ c("path", { d: "m1.25,3.75l1.461-2.504c.179-.307.508-.496.864-.496h4.851c.356,0,.685.189.864.496l1.461,2.504v5c0,1.105-.895,2-2,2H3.25c-1.105,0-2-.895-2-2V3.75Z" })
  ] }),
  copy: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("rect", { x: "3.25", y: ".75", width: "8", height: "8", rx: "1.5", ry: "1.5" }),
    /* @__PURE__ */ c("path", { d: "m8.25,11.25H2.25c-.828,0-1.5-.672-1.5-1.5V3.75" })
  ] }),
  folder: /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c("path", { d: "m.75,7.25V3.25c0-1.105.895-2,2-2h1.701c.607,0,1.18.275,1.56.748l.603.752h2.636c1.105,0,2,.895,2,2v2.5" }),
    /* @__PURE__ */ c("path", { d: "m2.75,5.25h6.5c1.105,0,2,.895,2,2v1.5c0,1.105-.895,2-2,2H2.75c-1.105,0-2-.895-2-2v-1.5c0-1.105.895-2,2-2Z" })
  ] })
};
function $({ name: e, className: t, ...n }) {
  return /* @__PURE__ */ c(
    "svg",
    {
      viewBox: "0 0 12 12",
      width: "12",
      height: "12",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: "1.5",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      "aria-hidden": "true",
      className: t ? `size-3 shrink-0 ${t}` : "size-3 shrink-0",
      ...n,
      children: au[e]
    }
  );
}
const Zi = ht({});
function jt(e) {
  const t = M(null);
  return t.current === null && (t.current = e()), t.current;
}
const lu = typeof window < "u", Dt = lu ? $t : F, Ut = /* @__PURE__ */ ht(null);
function Qi(e, t) {
  e.indexOf(t) === -1 && e.push(t);
}
function Ze(e, t) {
  const n = e.indexOf(t);
  n > -1 && e.splice(n, 1);
}
const ke = (e, t, n) => n > t ? t : n < e ? e : n;
function ci(e, t) {
  return t ? `${e}. For more information and steps for solving, visit https://motion.dev/troubleshooting/${t}` : e;
}
let Je = () => {
}, ye = () => {
};
typeof process < "u" && process.env?.NODE_ENV !== "production" && (Je = (e, t, n) => {
  !e && typeof console < "u" && console.warn(ci(t, n));
}, ye = (e, t, n) => {
  if (!e)
    throw new Error(ci(t, n));
});
const De = {}, Ji = (e) => /^-?(?:\d+(?:\.\d+)?|\.\d+)$/u.test(e), es = (e) => typeof e == "object" && e !== null, ts = (e) => /^0[^.\s]+$/u.test(e);
// @__NO_SIDE_EFFECTS__
function ia(e) {
  let t;
  return () => (t === void 0 && (t = e()), t);
}
const we = /* @__NO_SIDE_EFFECTS__ */ (e) => e, Wt = (...e) => e.reduce((t, n) => (i) => n(t(i))), dt = /* @__NO_SIDE_EFFECTS__ */ (e, t, n) => {
  const i = t - e;
  return i ? (n - e) / i : 1;
};
class gn {
  constructor() {
    this.subscriptions = [];
  }
  add(t) {
    return Qi(this.subscriptions, t), () => this.remove(t);
  }
  remove(t) {
    Ze(this.subscriptions, t);
  }
  notify(t, n, i) {
    const s = this.subscriptions.length;
    if (s)
      if (s === 1)
        this.subscriptions[0](t, n, i);
      else
        for (let r = 0; r < s; r++) {
          const o = this.subscriptions[r];
          o && o(t, n, i);
        }
  }
  getSize() {
    return this.subscriptions.length;
  }
  clear() {
    this.subscriptions.length = 0;
  }
}
const he = /* @__NO_SIDE_EFFECTS__ */ (e) => e * 1e3, pe = /* @__NO_SIDE_EFFECTS__ */ (e) => e / 1e3, sa = /* @__NO_SIDE_EFFECTS__ */ (e, t) => t ? e * (1e3 / t) : 0, Zs = /* @__PURE__ */ new Set();
function Mn(e, t, n) {
  e || Zs.has(t) || (console.warn(ci(t, n)), Zs.add(t));
}
const cu = (e, t, n) => {
  const i = t - e;
  return ((n - e) % i + i) % i + e;
}, ra = (e, t, n) => (((1 - 3 * n + 3 * t) * e + (3 * n - 6 * t)) * e + 3 * t) * e, uu = 1e-7, du = 12;
function fu(e, t, n, i, s) {
  let r, o, a = 0;
  do
    o = t + (n - t) / 2, r = ra(o, i, s) - e, r > 0 ? n = o : t = o;
  while (Math.abs(r) > uu && ++a < du);
  return o;
}
// @__NO_SIDE_EFFECTS__
function _t(e, t, n, i) {
  if (e === t && n === i)
    return we;
  const s = (r) => fu(r, 0, 1, e, n);
  return (r) => r === 0 || r === 1 ? r : ra(s(r), t, i);
}
const oa = /* @__NO_SIDE_EFFECTS__ */ (e) => (t) => t <= 0.5 ? e(2 * t) / 2 : (2 - e(2 * (1 - t))) / 2, ns = /* @__NO_SIDE_EFFECTS__ */ (e) => (t) => 1 - e(1 - t), aa = /* @__PURE__ */ _t(0.33, 1.53, 0.69, 0.99), is = /* @__PURE__ */ ns(aa), la = /* @__PURE__ */ oa(is), ca = (e) => e >= 1 ? 1 : (e *= 2) < 1 ? 0.5 * is(e) : 0.5 * (2 - Math.pow(2, -10 * (e - 1))), ss = (e) => 1 - Math.sin(Math.acos(e)), ua = /* @__PURE__ */ ns(ss), da = /* @__PURE__ */ oa(ss), hu = /* @__PURE__ */ _t(0.42, 0, 1, 1), pu = /* @__PURE__ */ _t(0, 0, 0.58, 1), fa = /* @__PURE__ */ _t(0.42, 0, 0.58, 1), ha = /* @__NO_SIDE_EFFECTS__ */ (e) => Array.isArray(e) && typeof e[0] != "number";
// @__NO_SIDE_EFFECTS__
function pa(e, t) {
  return /* @__PURE__ */ ha(e) ? e[cu(0, e.length, t)] : e;
}
const ma = /* @__NO_SIDE_EFFECTS__ */ (e) => Array.isArray(e) && typeof e[0] == "number", Qs = {
  linear: we,
  easeIn: hu,
  easeInOut: fa,
  easeOut: pu,
  circIn: ss,
  circInOut: da,
  circOut: ua,
  backIn: is,
  backInOut: la,
  backOut: aa,
  anticipate: ca
}, mu = (e) => typeof e == "string", Js = (e) => {
  if (/* @__PURE__ */ ma(e)) {
    ye(e.length === 4, "Cubic bezier arrays must contain four numerical values.", "cubic-bezier-length");
    const [t, n, i, s] = e;
    return /* @__PURE__ */ _t(t, n, i, s);
  } else if (mu(e))
    return ye(Qs[e] !== void 0, `Invalid easing type '${e}'`, "invalid-easing-type"), Qs[e];
  return e;
}, Yt = [
  "setup",
  // Compute
  "read",
  // Read
  "resolveKeyframes",
  // Write/Read/Write/Read
  "preUpdate",
  // Compute
  "update",
  // Compute
  "preRender",
  // Compute
  "render",
  // Write
  "postRender"
  // Compute
];
function gu(e) {
  let t = /* @__PURE__ */ new Set(), n = /* @__PURE__ */ new Set(), i = !1, s = !1;
  const r = /* @__PURE__ */ new Set();
  let o = {
    delta: 0,
    timestamp: 0,
    isProcessing: !1
  };
  function a(u) {
    r.has(u) && (n.add(u), e()), u(o);
  }
  const l = {
    /**
     * Schedule a process to run on the next frame.
     */
    schedule: (u, d = !1, h = !1) => {
      const p = h && i ? t : n;
      return d && r.add(u), p.add(u), u;
    },
    /**
     * Cancel the provided callback from running on the next frame.
     */
    cancel: (u) => {
      n.delete(u), r.delete(u);
    },
    /**
     * Execute all schedule callbacks.
     */
    process: (u) => {
      if (o = u, i) {
        s = !0;
        return;
      }
      i = !0;
      const d = t;
      t = n, n = d, t.forEach(a), t.clear(), i = !1, s && (s = !1, l.process(u));
    }
  };
  return l;
}
const yu = 40;
function ga(e, t) {
  let n = !1, i = !0;
  const s = {
    delta: 0,
    timestamp: 0,
    isProcessing: !1
  }, r = () => n = !0, o = Yt.reduce((y, k) => (y[k] = gu(r), y), {}), { setup: a, read: l, resolveKeyframes: u, preUpdate: d, update: h, preRender: f, render: p, postRender: g } = o, x = () => {
    const y = De.useManualTiming, k = y ? s.timestamp : performance.now();
    n = !1, y || (s.delta = i ? 1e3 / 60 : Math.max(Math.min(k - s.timestamp, yu), 1)), s.timestamp = k, s.isProcessing = !0, a.process(s), l.process(s), u.process(s), d.process(s), h.process(s), f.process(s), p.process(s), g.process(s), s.isProcessing = !1, n && t && (i = !1, e(x));
  }, b = () => {
    n = !0, i = !0, s.isProcessing || e(x);
  };
  return { schedule: Yt.reduce((y, k) => {
    const E = o[k];
    return y[k] = (P, S = !1, m = !1) => (n || b(), E.schedule(P, S, m)), y;
  }, {}), cancel: (y) => {
    for (let k = 0; k < Yt.length; k++)
      o[Yt[k]].cancel(y);
  }, state: s, steps: o };
}
const { schedule: z, cancel: Ve, state: te, steps: jn } = /* @__PURE__ */ ga(typeof requestAnimationFrame < "u" ? requestAnimationFrame : we, !0);
let rn;
function xu() {
  rn = void 0;
}
const ae = {
  now: () => (rn === void 0 && ae.set(te.isProcessing || De.useManualTiming ? te.timestamp : performance.now()), rn),
  set: (e) => {
    rn = e, queueMicrotask(xu);
  }
}, ct = (e) => Math.round(e * 1e5) / 1e5, ya = (e) => (t) => typeof t == "string" && t.startsWith(e), xa = /* @__PURE__ */ ya("--"), vu = /* @__PURE__ */ ya("var(--"), rs = (e) => vu(e) ? bu.test(e.split("/*")[0].trim()) : !1, bu = /var\(--(?:[\w-]+\s*|[\w-]+\s*,(?:\s*[^)(\s]|\s*\((?:[^)(]|\([^)(]*\))*\))+\s*)\)$/iu;
function er(e) {
  return typeof e != "string" ? !1 : e.split("/*")[0].includes("var(--");
}
const pt = {
  test: (e) => typeof e == "number",
  parse: parseFloat,
  transform: (e) => e
}, Vt = {
  ...pt,
  transform: (e) => ke(0, 1, e)
}, Xt = {
  ...pt,
  default: 1
}, os = /-?(?:\d+(?:\.\d+)?|\.\d+)/gu;
function wu(e) {
  return e == null;
}
const ku = /^(?:#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\))$/iu, as = (e, t) => (n) => !!(typeof n == "string" && ku.test(n) && n.startsWith(e) || t && !wu(n) && Object.prototype.hasOwnProperty.call(n, t)), va = (e, t, n) => (i) => {
  if (typeof i != "string")
    return i;
  const [s, r, o, a] = i.match(os);
  return {
    [e]: parseFloat(s),
    [t]: parseFloat(r),
    [n]: parseFloat(o),
    alpha: a !== void 0 ? parseFloat(a) : 1
  };
}, Tu = (e) => ke(0, 255, e), Un = {
  ...pt,
  transform: (e) => Math.round(Tu(e))
}, Ke = {
  test: /* @__PURE__ */ as("rgb", "red"),
  parse: /* @__PURE__ */ va("red", "green", "blue"),
  transform: ({ red: e, green: t, blue: n, alpha: i = 1 }) => "rgba(" + Un.transform(e) + ", " + Un.transform(t) + ", " + Un.transform(n) + ", " + ct(Vt.transform(i)) + ")"
};
function Su(e) {
  let t = "", n = "", i = "", s = "";
  return e.length > 5 ? (t = e.substring(1, 3), n = e.substring(3, 5), i = e.substring(5, 7), s = e.substring(7, 9)) : (t = e.substring(1, 2), n = e.substring(2, 3), i = e.substring(3, 4), s = e.substring(4, 5), t += t, n += n, i += i, s += s), {
    red: parseInt(t, 16),
    green: parseInt(n, 16),
    blue: parseInt(i, 16),
    alpha: s ? parseInt(s, 16) / 255 : 1
  };
}
const ui = {
  test: /* @__PURE__ */ as("#"),
  parse: Su,
  transform: Ke.transform
}, zt = /* @__NO_SIDE_EFFECTS__ */ (e) => ({
  test: (t) => typeof t == "string" && t.endsWith(e) && t.split(" ").length === 1,
  parse: parseFloat,
  transform: (t) => `${t}${e}`
}), Ee = /* @__PURE__ */ zt("deg"), Pe = /* @__PURE__ */ zt("%"), V = /* @__PURE__ */ zt("px"), Au = /* @__PURE__ */ zt("vh"), Nu = /* @__PURE__ */ zt("vw"), tr = {
  ...Pe,
  parse: (e) => Pe.parse(e) / 100,
  transform: (e) => Pe.transform(e * 100)
}, st = {
  test: /* @__PURE__ */ as("hsl", "hue"),
  parse: /* @__PURE__ */ va("hue", "saturation", "lightness"),
  transform: ({ hue: e, saturation: t, lightness: n, alpha: i = 1 }) => "hsla(" + Math.round(e) + ", " + Pe.transform(ct(t)) + ", " + Pe.transform(ct(n)) + ", " + ct(Vt.transform(i)) + ")"
}, ne = {
  test: (e) => Ke.test(e) || ui.test(e) || st.test(e),
  parse: (e) => Ke.test(e) ? Ke.parse(e) : st.test(e) ? st.parse(e) : ui.parse(e),
  transform: (e) => typeof e == "string" ? e : e.hasOwnProperty("red") ? Ke.transform(e) : st.transform(e),
  getAnimatableNone: (e) => {
    const t = ne.parse(e);
    return t.alpha = 0, ne.transform(t);
  }
}, Pu = /(?:#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\))/giu, ba = /* @__PURE__ */ new RegExp(os.source), wa = /* @__PURE__ */ new RegExp(Pu.source, "i");
function Mu(e) {
  return isNaN(e) && typeof e == "string" && (ba.test(e) || wa.test(e));
}
const ka = "number", Ta = "color", Cu = "var", Eu = "var(", nr = "${}", Du = /var\s*\(\s*--(?:[\w-]+\s*|[\w-]+\s*,(?:\s*[^)(\s]|\s*\((?:[^)(]|\([^)(]*\))*\))+\s*)\)|#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\)|-?(?:\d+(?:\.\d+)?|\.\d+)/giu;
function Vu(e) {
  const t = e.toString();
  return ba.test(t) || wa.test(t);
}
function Rt(e) {
  const t = e.toString(), n = [], i = {
    color: [],
    number: [],
    var: []
  }, s = [];
  let r = 0;
  const a = t.replace(Du, (l) => (ne.test(l) ? (i.color.push(r), s.push(Ta), n.push(ne.parse(l))) : l.startsWith(Eu) ? (i.var.push(r), s.push(Cu), n.push(l)) : (i.number.push(r), s.push(ka), n.push(parseFloat(l))), ++r, nr)).split(nr);
  return { values: n, split: a, indexes: i, types: s };
}
function Ru(e) {
  return Rt(e).values;
}
function Sa({ split: e, types: t }) {
  const n = e.length;
  return (i) => {
    let s = "";
    for (let r = 0; r < n; r++)
      if (s += e[r], i[r] !== void 0) {
        const o = t[r];
        o === ka ? s += ct(i[r]) : o === Ta ? s += ne.transform(i[r]) : s += i[r];
      }
    return s;
  };
}
function Lu(e) {
  return Sa(Rt(e));
}
const Fu = (e) => typeof e == "number" ? 0 : ne.test(e) ? ne.getAnimatableNone(e) : e, Iu = (e, t) => typeof e == "number" ? t?.trim().endsWith("/") ? e : 0 : Fu(e);
function Ou(e) {
  const t = Rt(e);
  return Sa(t)(t.values.map((i, s) => Iu(i, t.split[s])));
}
const ge = {
  test: Mu,
  parse: Ru,
  createTransformer: Lu,
  getAnimatableNone: Ou
};
function Wn(e, t, n) {
  return n < 0 && (n += 1), n > 1 && (n -= 1), n < 1 / 6 ? e + (t - e) * 6 * n : n < 1 / 2 ? t : n < 2 / 3 ? e + (t - e) * (2 / 3 - n) * 6 : e;
}
function Bu({ hue: e, saturation: t, lightness: n, alpha: i }) {
  e /= 360, t /= 100, n /= 100;
  let s = 0, r = 0, o = 0;
  if (!t)
    s = r = o = n;
  else {
    const a = n < 0.5 ? n * (1 + t) : n + t - n * t, l = 2 * n - a;
    s = Wn(l, a, e + 1 / 3), r = Wn(l, a, e), o = Wn(l, a, e - 1 / 3);
  }
  return {
    red: Math.round(s * 255),
    green: Math.round(r * 255),
    blue: Math.round(o * 255),
    alpha: i
  };
}
function yn(e, t) {
  return (n) => n > 0 ? t : e;
}
const K = (e, t, n) => e + (t - e) * n, _n = (e, t, n) => {
  const i = e * e, s = n * (t * t - i) + i;
  return s < 0 ? 0 : Math.sqrt(s);
}, $u = [ui, Ke, st], ju = (e) => $u.find((t) => t.test(e));
function ir(e) {
  const t = ju(e);
  if (!t)
    return Je(!1, `'${e}' is not an animatable color. Use the equivalent color code instead.`, "color-not-animatable"), !1;
  let n = t.parse(e);
  return t === st && (n = Bu(n)), n;
}
const sr = (e, t) => {
  const n = ir(e), i = ir(t);
  if (!n || !i)
    return yn(e, t);
  const s = { ...n };
  return (r) => (s.red = _n(n.red, i.red, r), s.green = _n(n.green, i.green, r), s.blue = _n(n.blue, i.blue, r), s.alpha = K(n.alpha, i.alpha, r), Ke.transform(s));
}, di = /* @__PURE__ */ new Set(["none", "hidden"]);
function Uu(e, t) {
  return di.has(e) ? (n) => n <= 0 ? e : t : (n) => n >= 1 ? t : e;
}
function Wu(e, t) {
  return (n) => K(e, t, n);
}
function ls(e) {
  return typeof e == "number" ? Wu : typeof e == "string" ? rs(e) ? yn : ne.test(e) ? sr : Gu : Array.isArray(e) ? Aa : typeof e == "object" ? ne.test(e) ? sr : _u : yn;
}
function Aa(e, t) {
  const n = [...e], i = n.length, s = e.map((r, o) => ls(r)(r, t[o]));
  return (r) => {
    for (let o = 0; o < i; o++)
      n[o] = s[o](r);
    return n;
  };
}
function _u(e, t) {
  const n = { ...e, ...t }, i = {};
  for (const s in n)
    e[s] !== void 0 && t[s] !== void 0 && (i[s] = ls(e[s])(e[s], t[s]));
  return (s) => {
    for (const r in i)
      n[r] = i[r](s);
    return n;
  };
}
function zu(e, t) {
  const n = [], i = { color: 0, var: 0, number: 0 };
  for (let s = 0; s < t.values.length; s++) {
    const r = t.types[s], o = e.indexes[r][i[r]], a = e.values[o] ?? 0;
    n[s] = a, i[r]++;
  }
  return n;
}
const Gu = (e, t) => {
  const n = ge.createTransformer(t), i = Rt(e), s = Rt(t);
  return i.indexes.var.length === s.indexes.var.length && i.indexes.color.length === s.indexes.color.length && i.indexes.number.length >= s.indexes.number.length ? di.has(e) && !s.values.length || di.has(t) && !i.values.length ? Uu(e, t) : Wt(Aa(zu(i, s), s.values), n) : (Je(!0, `Complex values '${e}' and '${t}' too different to mix. Ensure all colors are of the same type, and that each contains the same quantity of number and color values. Falling back to instant transition.`, "complex-values-different"), yn(e, t));
}, rr = /^(-?(?:\d+(?:\.\d*)?|\.\d+))([a-z%]*)$/iu;
function Ku(e, t) {
  const n = rr.exec(e);
  if (!n)
    return;
  const i = rr.exec(t);
  if (!i || n[2] !== i[2])
    return;
  const s = n[2], r = parseFloat(n[1]), o = parseFloat(i[1]);
  return (a) => ct(K(r, o, a)) + s;
}
function cs(e, t, n) {
  if (typeof e == "number" && typeof t == "number" && typeof n == "number")
    return K(e, t, n);
  if (typeof e == "string" && typeof t == "string") {
    const s = Ku(e, t);
    if (s)
      return s;
  }
  return ls(e)(e, t);
}
const Hu = (e) => {
  const t = ({ timestamp: n }) => e(n);
  return {
    start: (n = !0) => z.update(t, n),
    stop: () => Ve(t),
    /**
     * If we're processing this frame we can use the
     * framelocked timestamp to keep things in sync.
     */
    now: () => te.isProcessing ? te.timestamp : ae.now()
  };
}, Na = (e, t, n = 10) => {
  let i = "";
  const s = Math.max(Math.round(t / n), 2);
  for (let r = 0; r < s; r++)
    i += Math.round(e(r / (s - 1)) * 1e4) / 1e4 + ", ";
  return `linear(${i.substring(0, i.length - 2)})`;
}, us = 2e4;
function ds(e, t = 50, n = us, i) {
  let s = 0, r = e.next(s);
  for (; !r.done && s < n; )
    s += t, r = e.next(s);
  return s >= n ? 1 / 0 : s;
}
function Pa(e, t = 100, n) {
  const i = n({ ...e, keyframes: [0, t] }), s = Math.min(ds(i), us);
  return {
    type: "keyframes",
    ease: (r) => i.next(s * r).value / t,
    duration: /* @__PURE__ */ pe(s)
  };
}
const X = {
  // Default spring physics
  stiffness: 100,
  damping: 10,
  mass: 1,
  velocity: 0,
  // Default duration/bounce-based options
  duration: 800,
  // in ms
  bounce: 0.3,
  visualDuration: 0.3,
  // in seconds
  // Rest thresholds
  restSpeed: {
    granular: 0.01,
    default: 2
  },
  restDelta: {
    granular: 5e-3,
    default: 0.5
  },
  // Limits
  minDuration: 0.01,
  // in seconds
  maxDuration: 10,
  // in seconds
  minDamping: 0.05,
  maxDamping: 1
};
function fi(e, t) {
  return e * Math.sqrt(1 - t * t);
}
const qu = 12;
function Yu(e, t, n) {
  let i = n;
  for (let s = 1; s < qu; s++)
    i = i - e(i) / t(i);
  return i;
}
const zn = 1e-3;
function Xu({ duration: e = X.duration, bounce: t = X.bounce, velocity: n = X.velocity, mass: i = X.mass }) {
  let s, r;
  Je(e <= /* @__PURE__ */ he(X.maxDuration), "Spring duration must be 10 seconds or less", "spring-duration-limit");
  let o = 1 - t;
  o = ke(X.minDamping, X.maxDamping, o), e = ke(X.minDuration, X.maxDuration, /* @__PURE__ */ pe(e)), o < 1 ? (s = (u) => {
    const d = u * o, h = d * e, f = d - n, p = fi(u, o), g = Math.exp(-h);
    return zn - f / p * g;
  }, r = (u) => {
    const h = u * o * e, f = h * n + n, p = o * o * u * u * e, g = Math.exp(-h), x = fi(u * u, o);
    return (-s(u) + zn > 0 ? -1 : 1) * ((f - p) * g) / x;
  }) : (s = (u) => {
    const d = Math.exp(-u * e), h = (u - n) * e + 1;
    return -zn + d * h;
  }, r = (u) => {
    const d = Math.exp(-u * e), h = (n - u) * (e * e);
    return d * h;
  });
  const a = 5 / e, l = Yu(s, r, a);
  if (e = /* @__PURE__ */ he(e), isNaN(l))
    return {
      stiffness: X.stiffness,
      damping: X.damping,
      duration: e
    };
  {
    const u = l * l * i;
    return {
      stiffness: u,
      damping: o * 2 * Math.sqrt(i * u),
      duration: e
    };
  }
}
const Ma = ["duration", "bounce"], Ca = ["stiffness", "damping", "mass"];
function xn(e, t) {
  return t.some((n) => e[n] !== void 0);
}
function Zu(e) {
  let t = {
    velocity: X.velocity,
    stiffness: X.stiffness,
    damping: X.damping,
    mass: X.mass,
    isResolvedFromDuration: !1,
    ...e
  };
  if (!xn(e, Ca) && xn(e, Ma))
    if (t.velocity = 0, e.visualDuration) {
      const n = e.visualDuration, i = 2 * Math.PI / (n * 1.2), s = i * i, r = 2 * ke(0.05, 1, 1 - (e.bounce || 0)) * Math.sqrt(s);
      t = {
        ...t,
        mass: X.mass,
        stiffness: s,
        damping: r
      };
    } else {
      const n = Xu({ ...e, velocity: 0 });
      t = {
        ...t,
        ...n,
        mass: X.mass
      }, t.isResolvedFromDuration = !0;
    }
  return t;
}
function Lt(e = X.visualDuration, t = X.bounce) {
  const n = typeof e != "object" ? {
    visualDuration: e,
    keyframes: [0, 1],
    bounce: t
  } : e, i = n.keyframes[0], s = n.keyframes[n.keyframes.length - 1], r = { done: !1, value: i }, { stiffness: o, damping: a, mass: l, duration: u, velocity: d, isResolvedFromDuration: h } = Zu({
    ...n,
    velocity: -/* @__PURE__ */ pe(n.velocity || 0)
  }), f = a / (2 * Math.sqrt(o * l)), p = /* @__PURE__ */ pe(Math.sqrt(o / l)), g = f * p, x = {
    target: s,
    delta: s - i,
    velocity: d || 0,
    restSpeed: 0,
    restDelta: 0
  }, b = () => {
    const S = Math.abs(x.delta) < 5;
    x.restSpeed = n.restSpeed || (S ? X.restSpeed.granular : X.restSpeed.default), x.restDelta = n.restDelta || (S ? X.restDelta.granular : X.restDelta.default);
  };
  b();
  let w, T, y;
  if (f < 1) {
    const S = fi(p, f), m = { A: 0, sinC: 0, cosC: 0, t: -1, env: 0, sin: 0, cos: 0 };
    y = () => {
      m.A = (x.velocity + g * x.delta) / S, m.sinC = g * m.A + x.delta * S, m.cosC = g * x.delta - m.A * S;
    };
    const N = (A) => {
      A !== m.t && (m.t = A, m.env = Math.exp(-g * A), m.sin = Math.sin(S * A), m.cos = Math.cos(S * A));
    };
    w = (A) => (N(A), x.target - m.env * (m.A * m.sin + x.delta * m.cos)), T = (A) => (N(A), m.env * (m.sinC * m.sin + m.cosC * m.cos));
  } else if (f === 1) {
    w = (m) => x.target - Math.exp(-p * m) * (x.delta + (x.velocity + p * x.delta) * m);
    const S = { C: 0 };
    y = () => {
      S.C = x.velocity + p * x.delta;
    }, T = (m) => Math.exp(-p * m) * (p * S.C * m - x.velocity);
  } else {
    const S = p * Math.sqrt(f * f - 1);
    w = (N) => {
      const A = Math.exp(-g * N), L = Math.min(S * N, 300);
      return x.target - A * ((x.velocity + g * x.delta) * Math.sinh(L) + S * x.delta * Math.cosh(L)) / S;
    };
    const m = { P: 0, sinh: 0, cosh: 0 };
    y = () => {
      m.P = (x.velocity + g * x.delta) / S, m.sinh = g * m.P - x.delta * S, m.cosh = g * x.delta - m.P * S;
    }, T = (N) => {
      const A = Math.exp(-g * N), L = Math.min(S * N, 300);
      return A * (m.sinh * Math.sinh(L) + m.cosh * Math.cosh(L));
    };
  }
  y();
  const k = !xn(n, Ca) && xn(n, Ma), E = h && u || null, P = {
    calculatedDuration: E,
    /**
     * Aim the spring at a new target from its current position and
     * velocity, reusing the resolved physics and closures.
     */
    retarget: (S, m) => {
      x.target = S[S.length - 1], x.delta = x.target - S[0], x.velocity = k ? 0 : -/* @__PURE__ */ pe(m), n.restSpeed && n.restDelta || b(), P.calculatedDuration = E, r.done = !1, y();
    },
    velocity: (S) => /* @__PURE__ */ he(T(S)),
    next: (S) => {
      const m = w(S);
      if (h)
        r.done = S >= u;
      else {
        const N = /* @__PURE__ */ he(T(S));
        r.done = Math.abs(N) <= x.restSpeed && Math.abs(x.target - m) <= x.restDelta;
      }
      return r.value = r.done ? x.target : m, r;
    },
    toString: () => {
      const S = Math.min(ds(P), us), m = Na((N) => P.next(S * N).value, S, 30);
      return S + "ms " + m;
    },
    toTransition: () => {
    }
  };
  return P;
}
Lt.applyToOptions = (e) => {
  const t = Pa(e, 100, Lt);
  return e.ease = t.ease, e.duration = /* @__PURE__ */ he(t.duration), e.type = "keyframes", e;
};
function hi({ keyframes: e, velocity: t = 0, power: n = 0.8, timeConstant: i = 325, bounceDamping: s = 10, bounceStiffness: r = 500, modifyTarget: o, min: a, max: l, restDelta: u = 0.5, restSpeed: d }) {
  const h = e[0], f = {
    done: !1,
    value: h
  }, p = (S) => S < a || S > l, g = (S) => a === void 0 ? l : l === void 0 || Math.abs(a - S) < Math.abs(l - S) ? a : l;
  let x = n * t;
  const b = h + x, w = o === void 0 ? b : o(b);
  w !== b && (x = w - h);
  const T = (S) => -x * Math.exp(-S / i), y = (S) => {
    const m = T(S);
    f.done = Math.abs(m) <= u, f.value = f.done ? w : w + m;
  };
  let k, E;
  const P = (S) => {
    p(f.value) && (k = S, E = Lt({
      keyframes: [f.value, g(f.value)],
      /**
       * The friction curve is target + calcDelta(t), so its exact
       * derivative is -calcDelta(t) / timeConstant in units/ms,
       * converted here to the units/second expected by spring.
       */
      velocity: -T(S) / i * 1e3,
      damping: s,
      stiffness: r,
      restDelta: u,
      restSpeed: d
    }));
  };
  return P(0), {
    calculatedDuration: null,
    next: (S) => {
      let m = !1;
      return !E && k === void 0 && (m = !0, y(S), P(S)), k !== void 0 && S >= k ? E.next(S - k) : (!m && y(S), f);
    }
  };
}
function Qu(e, t, n) {
  const i = [], s = n || De.mix || cs, r = e.length - 1;
  for (let o = 0; o < r; o++) {
    let a = s(e[o], e[o + 1]);
    if (t) {
      const l = Array.isArray(t) ? t[o] || we : t;
      a = Wt(l, a);
    }
    i.push(a);
  }
  return i;
}
function Ea(e, t, { clamp: n = !0, ease: i, mixer: s } = {}) {
  const r = e.length;
  if (ye(r === t.length, "Both input and output ranges must be the same length", "range-length"), r === 1)
    return () => t[0];
  if (r === 2 && t[0] === t[1])
    return () => t[1];
  const o = e[0] === e[1];
  e[0] > e[r - 1] && (e = [...e].reverse(), t = [...t].reverse());
  const a = Qu(t, i, s), l = a.length, u = (d) => {
    if (o && d < e[0])
      return t[0];
    let h = 0;
    if (l > 1)
      for (; h < e.length - 2 && !(d < e[h + 1]); h++)
        ;
    const f = /* @__PURE__ */ dt(e[h], e[h + 1], d);
    return a[h](f);
  };
  return n ? (d) => u(ke(e[0], e[r - 1], d)) : u;
}
function Da(e, t) {
  const n = e[e.length - 1];
  for (let i = 1; i <= t; i++) {
    const s = /* @__PURE__ */ dt(0, t, i);
    e.push(K(n, 1, s));
  }
}
function Va(e) {
  const t = [0];
  return Da(t, e.length - 1), t;
}
function Ju(e, t) {
  return e.map((n) => n * t);
}
function ed(e, t) {
  return e.map(() => t || fa).splice(0, e.length - 1);
}
function rt({ duration: e = 300, keyframes: t, times: n, ease: i = "easeInOut" }) {
  const s = /* @__PURE__ */ ha(i) ? i.map(Js) : Js(i), r = {
    done: !1,
    value: t[0]
  };
  if (t.length === 2 && !Array.isArray(s) && (!n || n.length !== 2 || n[0] === 0 && n[1] === 1)) {
    const [l, u] = t, d = l === u ? void 0 : (De.mix || cs)(l, u);
    return {
      calculatedDuration: e,
      next: (h) => (r.value = d ? d(s(e > 0 ? ke(0, 1, h / e) : 1)) : u, r.done = h >= e, r)
    };
  }
  const o = Ju(
    // Only use the provided offsets if they're the correct length
    // TODO Maybe we should warn here if there's a length mismatch
    n && n.length === t.length ? n : Va(t),
    e
  ), a = Ea(o, t, {
    ease: Array.isArray(s) ? s : ed(t, s)
  });
  return {
    calculatedDuration: e,
    next: (l) => (r.value = a(l), r.done = l >= e, r)
  };
}
const td = 5;
function nd(e, t, n) {
  const i = Math.max(t - td, 0);
  return /* @__PURE__ */ sa(n - e(i), t - i);
}
function id(e, t, n = 0) {
  return t <= 0 ? n : e.velocity ? e.velocity(t) : nd((i) => e.next(i).value, t, e.next(t).value);
}
const sd = (e) => e !== null;
function Cn(e, { repeat: t, repeatType: n = "loop" }, i, s = 1) {
  const r = e.filter(sd), a = s < 0 || t && n !== "loop" && t % 2 === 1 ? 0 : r.length - 1;
  return !a || i === void 0 ? r[a] : i;
}
const rd = {
  decay: hi,
  inertia: hi,
  tween: rt,
  keyframes: rt,
  spring: Lt
};
function Ra(e) {
  typeof e.type == "string" && (e.type = rd[e.type]);
}
function La(e, t) {
  return {
    kind: e,
    animation: t,
    timestamp: ae.now(),
    frameTimestamp: te.timestamp,
    frameIsProcessing: te.isProcessing
  };
}
function Fa(e, t, n) {
  const i = globalThis.__MOTION_INSPECT__;
  if (i)
    try {
      i({
        ...La("animation-start", e),
        options: n ? { ...t, ...n } : t
      });
    } catch {
    }
}
function od(e, t) {
  const n = globalThis.__MOTION_INSPECT__;
  if (n)
    try {
      n({
        ...La("layout-animation-start", e),
        node: t
      });
    } catch {
    }
}
class fs {
  constructor() {
    this.isResolved = !1;
  }
  get finished() {
    return this._finished || (this._finished = this.isResolved ? Promise.resolve() : new Promise((t) => {
      this._resolve = t;
    })), this._finished;
  }
  updateFinished() {
    this._finished = this._resolve = void 0, this.isResolved = !1;
  }
  notifyFinished() {
    this.isResolved = !0, this._resolve?.();
  }
  /**
   * Allows the animation to be awaited.
   *
   * @deprecated Use `finished` instead.
   */
  then(t, n) {
    return this.finished.then(t, n);
  }
}
const ad = (e) => e / 100;
class vn extends fs {
  constructor(t) {
    super(), this.state = "idle", this.startTime = null, this.isStopped = !1, this.currentTime = 0, this.holdTime = null, this.playbackSpeed = 1, this.delayState = {
      done: !1,
      value: void 0
    }, this.stop = () => {
      const { motionValue: n } = this.options;
      n && n.updatedAt !== ae.now() && this.tick(ae.now()), this.isStopped = !0, this.state !== "idle" && (this.teardown(), this.options.onStop?.());
    }, this.options = t, this.initAnimation(), this.play(), t.autoplay === !1 && this.pause(), Fa(this, this.options);
  }
  initAnimation() {
    const { options: t } = this;
    Ra(t);
    const { type: n = rt, repeat: i = 0, repeatDelay: s = 0, repeatType: r, velocity: o = 0 } = t;
    let { keyframes: a } = t;
    const l = n || rt;
    process.env.NODE_ENV !== "production" && l !== rt && ye(a.length <= 2, `Only two keyframes currently supported with spring and inertia animations. Trying to animate ${a}`, "spring-two-frames"), l !== rt && typeof a[0] != "number" && (this.mixKeyframes = Wt(ad, cs(a[0], a[1])), a = [0, 100]);
    const u = l(a === t.keyframes ? t : { ...t, keyframes: a });
    r === "mirror" && (this.mirroredGenerator = l({
      ...t,
      keyframes: [...a].reverse(),
      velocity: -o
    })), u.calculatedDuration === null && (u.calculatedDuration = ds(u));
    const { calculatedDuration: d } = u;
    this.calculatedDuration = d, this.resolvedDuration = d + s, this.totalDuration = this.resolvedDuration * (i + 1) - s, this.generator = u;
  }
  updateTime(t) {
    const n = Math.round(t - this.startTime) * this.playbackSpeed;
    this.holdTime !== null ? this.currentTime = this.holdTime : this.currentTime = n;
  }
  tick(t, n = !1) {
    const { generator: i, totalDuration: s, mixKeyframes: r, mirroredGenerator: o, resolvedDuration: a, calculatedDuration: l } = this;
    if (this.startTime === null)
      return i.next(0);
    const { delay: u = 0, keyframes: d, repeat: h, repeatType: f, repeatDelay: p, type: g, onUpdate: x, finalKeyframe: b } = this.options;
    this.speed > 0 ? this.startTime = Math.min(this.startTime, t) : this.speed < 0 && (this.startTime = Math.min(t - s / this.speed, this.startTime)), n ? this.currentTime = t : this.updateTime(t);
    const w = this.currentTime - u * (this.playbackSpeed >= 0 ? 1 : -1), T = this.playbackSpeed >= 0 ? w < 0 : w > s;
    this.currentTime = Math.max(w, 0), this.state === "finished" && this.holdTime === null && (this.currentTime = s);
    let y = this.currentTime, k = i;
    if (h) {
      const m = Math.min(this.currentTime, s) / a;
      let N = Math.floor(m), A = m % 1;
      !A && m >= 1 && (A = 1), A === 1 && N--, N = Math.min(N, h + 1), N % 2 && (f === "reverse" ? (A = 1 - A, p && (A -= p / a)) : f === "mirror" && (k = o)), y = ke(0, 1, A) * a;
    }
    let E;
    T ? (this.delayState.value = d[0], E = this.delayState) : E = k.next(y), r && !T && (E.value = r(E.value));
    let { done: P } = E;
    !T && l !== null && (P = this.playbackSpeed >= 0 ? this.currentTime >= s : this.currentTime <= 0);
    const S = this.holdTime === null && (this.state === "finished" || this.state === "running" && P);
    return S && g !== hi && (E.value = Cn(d, this.options, b, this.speed)), x && x(E.value), S && this.finish(), E;
  }
  /**
   * Allows the returned animation to be awaited or promise-chained. Currently
   * resolves when the animation finishes at all but in a future update could/should
   * reject if its cancels.
   */
  then(t, n) {
    return this.finished.then(t, n);
  }
  get duration() {
    return /* @__PURE__ */ pe(this.calculatedDuration);
  }
  get iterationDuration() {
    const { delay: t = 0 } = this.options || {};
    return this.duration + /* @__PURE__ */ pe(t);
  }
  get time() {
    return /* @__PURE__ */ pe(this.currentTime);
  }
  set time(t) {
    t = /* @__PURE__ */ he(t), this.currentTime = t, this.startTime === null || this.holdTime !== null || this.playbackSpeed === 0 ? this.holdTime = t : this.driver && (this.startTime = this.driver.now() - t / this.playbackSpeed), this.driver ? this.driver.start(!1) : (this.startTime = 0, this.state = "paused", this.holdTime = t, this.tick(t));
  }
  /**
   * Returns the generator's velocity at the current time in units/second.
   * Uses the analytical derivative when available (springs), avoiding
   * the MotionValue's frame-dependent velocity estimation.
   */
  getGeneratorVelocity() {
    return id(this.generator, this.currentTime, this.options.velocity);
  }
  get speed() {
    return this.playbackSpeed;
  }
  set speed(t) {
    const n = this.playbackSpeed !== t;
    n && this.driver && this.updateTime(ae.now()), this.playbackSpeed = t, n && this.driver && (this.time = /* @__PURE__ */ pe(this.currentTime));
  }
  play() {
    if (this.isStopped)
      return;
    const { driver: t = Hu, startTime: n } = this.options;
    this.driver || (this.driver = t((s) => this.tick(s))), this.options.onPlay?.();
    const i = this.driver.now();
    this.state === "finished" ? (this.updateFinished(), this.startTime = i) : this.holdTime !== null ? this.startTime = i - this.holdTime : this.startTime || (this.startTime = n ?? i), this.state === "finished" && this.speed < 0 && (this.startTime += this.calculatedDuration), this.holdTime = null, this.state = "running", this.driver.start();
  }
  pause() {
    this.state = "paused", this.updateTime(ae.now()), this.holdTime = this.currentTime;
  }
  complete() {
    this.state !== "running" && this.play(), this.state = "finished", this.holdTime = null;
  }
  finish() {
    this.notifyFinished(), this.teardown(), this.state = "finished", this.options.onComplete?.();
  }
  cancel() {
    this.holdTime = null, this.startTime = 0, this.tick(0), this.teardown(), this.options.onCancel?.();
  }
  teardown() {
    this.state = "idle", this.stopDriver(), this.startTime = this.holdTime = null;
  }
  stopDriver() {
    this.driver && (this.driver.stop(), this.driver = void 0);
  }
  sample(t) {
    return this.startTime = 0, this.tick(t, !0);
  }
  attachTimeline(t) {
    return this.options.allowFlatten && (this.options.type = "keyframes", this.options.ease = "linear", this.initAnimation()), this.driver?.stop(), t.observe(this);
  }
}
const ld = /* @__PURE__ */ new Set(["brightness", "contrast", "saturate", "opacity"]);
function cd(e) {
  const [t, n] = e.slice(0, -1).split("(");
  if (t === "drop-shadow")
    return e;
  const [i] = n.match(os) || [];
  if (!i)
    return e;
  const s = n.replace(i, "");
  let r = ld.has(t) ? 1 : 0;
  return i !== n && (r *= 100), t + "(" + r + s + ")";
}
const ud = /\b([a-z-]*)\(.*?\)/gu, pi = {
  ...ge,
  getAnimatableNone: (e) => {
    const t = e.match(ud);
    return t ? t.map(cd).join(" ") : e;
  }
}, mi = {
  ...ge,
  getAnimatableNone: (e) => {
    const t = ge.parse(e);
    return ge.createTransformer(e)(t.map((i) => typeof i == "number" ? 0 : typeof i == "object" ? { ...i, alpha: 1 } : i));
  }
}, or = {
  ...pt,
  transform: Math.round
}, gi = {
  rotate: Ee,
  /**
   * Internal channel for `transition.path` orientToPath. Composed onto
   * `rotate` at the transform-build sites so the user's `rotate` is
   * never read or overwritten. Not part of `transformPropOrder`.
   */
  pathRotation: Ee,
  rotateX: Ee,
  rotateY: Ee,
  rotateZ: Ee,
  scale: Xt,
  scaleX: Xt,
  scaleY: Xt,
  scaleZ: Xt,
  skew: Ee,
  skewX: Ee,
  skewY: Ee,
  distance: V,
  translateX: V,
  translateY: V,
  translateZ: V,
  x: V,
  y: V,
  z: V,
  perspective: V,
  transformPerspective: V,
  opacity: Vt,
  originX: tr,
  originY: tr,
  originZ: V
}, Me = {
  // Border props
  borderWidth: V,
  borderTopWidth: V,
  borderRightWidth: V,
  borderBottomWidth: V,
  borderLeftWidth: V,
  borderRadius: V,
  borderTopLeftRadius: V,
  borderTopRightRadius: V,
  borderBottomRightRadius: V,
  borderBottomLeftRadius: V,
  // Positioning props
  width: V,
  maxWidth: V,
  height: V,
  maxHeight: V,
  top: V,
  right: V,
  bottom: V,
  left: V,
  inset: V,
  insetBlock: V,
  insetBlockStart: V,
  insetBlockEnd: V,
  insetInline: V,
  insetInlineStart: V,
  insetInlineEnd: V,
  // Spacing props
  padding: V,
  paddingTop: V,
  paddingRight: V,
  paddingBottom: V,
  paddingLeft: V,
  paddingBlock: V,
  paddingBlockStart: V,
  paddingBlockEnd: V,
  paddingInline: V,
  paddingInlineStart: V,
  paddingInlineEnd: V,
  margin: V,
  marginTop: V,
  marginRight: V,
  marginBottom: V,
  marginLeft: V,
  marginBlock: V,
  marginBlockStart: V,
  marginBlockEnd: V,
  marginInline: V,
  marginInlineStart: V,
  marginInlineEnd: V,
  // Typography
  fontSize: V,
  // Misc
  backgroundPositionX: V,
  backgroundPositionY: V,
  ...gi,
  zIndex: or,
  // SVG
  fillOpacity: Vt,
  strokeOpacity: Vt,
  numOctaves: or
}, dd = {
  ...Me,
  // Color props
  color: ne,
  backgroundColor: ne,
  outlineColor: ne,
  fill: ne,
  stroke: ne,
  // Border props
  borderColor: ne,
  borderTopColor: ne,
  borderRightColor: ne,
  borderBottomColor: ne,
  borderLeftColor: ne,
  filter: pi,
  WebkitFilter: pi,
  mask: mi,
  WebkitMask: mi
}, Ia = (e) => dd[e], fd = /* @__PURE__ */ new Set([pi, mi]);
function hs(e, t) {
  let n = Ia(e);
  return fd.has(n) || (n = ge), n.getAnimatableNone ? n.getAnimatableNone(t) : void 0;
}
function hd(e) {
  for (let t = 1; t < e.length; t++)
    e[t] ?? (e[t] = e[t - 1]);
}
const He = (e) => e * 180 / Math.PI, yi = (e) => {
  const t = He(Math.atan2(e[1], e[0]));
  return xi(t);
}, pd = {
  x: 4,
  y: 5,
  translateX: 4,
  translateY: 5,
  scaleX: 0,
  scaleY: 3,
  scale: (e) => (Math.abs(e[0]) + Math.abs(e[3])) / 2,
  rotate: yi,
  rotateZ: yi,
  skewX: (e) => He(Math.atan(e[1])),
  skewY: (e) => He(Math.atan(e[2])),
  skew: (e) => (Math.abs(e[1]) + Math.abs(e[2])) / 2
}, xi = (e) => (e = e % 360, e < 0 && (e += 360), e), ar = yi, lr = (e) => Math.sqrt(e[0] * e[0] + e[1] * e[1]), cr = (e) => Math.sqrt(e[4] * e[4] + e[5] * e[5]), md = {
  x: 12,
  y: 13,
  z: 14,
  translateX: 12,
  translateY: 13,
  translateZ: 14,
  scaleX: lr,
  scaleY: cr,
  scale: (e) => (lr(e) + cr(e)) / 2,
  rotateX: (e) => xi(He(Math.atan2(e[6], e[5]))),
  rotateY: (e) => xi(He(Math.atan2(-e[2], e[0]))),
  rotateZ: ar,
  rotate: ar,
  skewX: (e) => He(Math.atan(e[4])),
  skewY: (e) => He(Math.atan(e[1])),
  skew: (e) => (Math.abs(e[1]) + Math.abs(e[4])) / 2
};
function vi(e) {
  return e.includes("scale") ? 1 : 0;
}
function bi(e, t) {
  if (!e || e === "none")
    return vi(t);
  const n = e.match(/^matrix3d\(([-\d.e\s,]+)\)$/u);
  let i, s;
  if (n)
    i = md, s = n;
  else {
    const a = e.match(/^matrix\(([-\d.e\s,]+)\)$/u);
    i = pd, s = a;
  }
  if (!s)
    return vi(t);
  const r = i[t], o = s[1].split(",").map(gd);
  return typeof r == "function" ? r(o) : o[r];
}
const Oa = (e, t) => {
  const { transform: n = "none" } = getComputedStyle(e);
  return bi(n, t);
};
function gd(e) {
  return parseFloat(e.trim());
}
const je = [
  "transformPerspective",
  "x",
  "y",
  "z",
  "translateX",
  "translateY",
  "translateZ",
  "scale",
  "scaleX",
  "scaleY",
  "rotate",
  "rotateX",
  "rotateY",
  "rotateZ",
  "skew",
  "skewX",
  "skewY"
], Fe = /* @__PURE__ */ new Set([...je, "pathRotation"]), ur = (e) => e === pt || e === V, yd = /* @__PURE__ */ new Set(["x", "y", "z"]), xd = je.filter((e) => !yd.has(e));
function vd(e) {
  const t = [];
  return xd.forEach((n) => {
    const i = e.getValue(n);
    if (i !== void 0) {
      const s = i.get(), r = n.startsWith("scale") ? 1 : 0;
      if (s === r)
        return;
      t.push([n, s]), i.set(r);
    }
  }), t;
}
const bd = /* @__PURE__ */ new Set(["bottom", "right"]);
function dr(e, t, n, i, s, r) {
  const o = parseFloat(e);
  if (!isNaN(o))
    return o;
  const { min: a, max: l } = t()[n], u = l - a;
  return r === "border-box" ? u : u - parseFloat(i) - parseFloat(s);
}
const qe = {
  // Dimensions
  width: ({ width: e, paddingLeft: t = "0", paddingRight: n = "0", boxSizing: i }, s) => dr(e, s, "x", t, n, i),
  height: ({ height: e, paddingTop: t = "0", paddingBottom: n = "0", boxSizing: i }, s) => dr(e, s, "y", t, n, i),
  top: ({ top: e }) => parseFloat(e),
  left: ({ left: e }) => parseFloat(e),
  bottom: ({ top: e }, t) => {
    const { y: n } = t();
    return parseFloat(e) + (n.max - n.min);
  },
  right: ({ left: e }, t) => {
    const { x: n } = t();
    return parseFloat(e) + (n.max - n.min);
  },
  // Transform
  x: ({ transform: e }) => bi(e, "x"),
  y: ({ transform: e }) => bi(e, "y")
};
qe.translateX = qe.x;
qe.translateY = qe.y;
const Ye = /* @__PURE__ */ new Set();
let wi = !1, ki = !1, Ti = !1;
function Ba() {
  if (ki) {
    const e = [], t = /* @__PURE__ */ new Set(), n = /* @__PURE__ */ new Set();
    Ye.forEach((s) => {
      s.needsMeasurement && (e.push(s), t.add(s.element), bd.has(s.name) && n.add(s.element));
    });
    const i = /* @__PURE__ */ new Map();
    n.forEach((s) => {
      const r = vd(s);
      r.length && (i.set(s, r), s.render());
    }), e.forEach((s) => s.measureInitialState()), t.forEach((s) => {
      s.render();
      const r = i.get(s);
      r && r.forEach(([o, a]) => {
        s.getValue(o)?.set(a);
      });
    }), e.forEach((s) => s.measureEndState()), e.forEach((s) => {
      s.suspendedScrollY !== void 0 && window.scrollTo(0, s.suspendedScrollY);
    });
  }
  ki = !1, wi = !1, Ye.forEach((e) => e.complete(Ti)), Ye.clear();
}
function $a() {
  Ye.forEach((e) => {
    e.readKeyframes(), e.needsMeasurement && (ki = !0);
  });
}
function wd() {
  Ti = !0, $a(), Ba(), Ti = !1;
}
function kd(e, t, n) {
  if (typeof e == "string") {
    if (Ji(e) || ts(e))
      return parseFloat(e);
    if (!ge.test(e) && ge.test(n))
      return hs(t, n);
  }
  return e ?? void 0;
}
class ps {
  constructor(t, n, i, s, r, o = !1) {
    this.state = "pending", this.isAsync = !1, this.needsMeasurement = !1, this.unresolvedKeyframes = [...t], this.onComplete = n, this.name = i, this.motionValue = s, this.element = r, this.isAsync = o;
  }
  scheduleResolve() {
    this.state = "scheduled", this.isAsync ? (Ye.add(this), wi || (wi = !0, z.read($a), z.resolveKeyframes(Ba))) : (this.readKeyframes(), this.complete());
  }
  readKeyframes() {
    const { unresolvedKeyframes: t, name: n, element: i, motionValue: s } = this;
    if (t[0] === null) {
      const r = s?.get(), o = t[t.length - 1];
      if (r !== void 0)
        t[0] = r;
      else if (i && n) {
        const a = kd(i.readValue(n, o), n, o);
        a !== void 0 && (t[0] = a);
      }
      t[0] === void 0 && (t[0] = o), s && r === void 0 && s.set(t[0]);
    }
    hd(t);
  }
  setFinalKeyframe() {
  }
  measureInitialState() {
  }
  renderEndStyles() {
  }
  measureEndState() {
  }
  complete(t = !1) {
    this.state = "complete", this.onComplete(this.unresolvedKeyframes, this.finalKeyframe, t), Ye.delete(this);
  }
  cancel() {
    this.state === "scheduled" && (Ye.delete(this), this.state = "pending");
  }
  resume() {
    this.state === "pending" && this.scheduleResolve();
  }
}
const ms = (e) => e.startsWith("--");
function ja(e, t, n) {
  ms(t) ? e.style.setProperty(t, n) : e.style[t] = n;
}
const Td = {};
function Ua(e, t) {
  const n = /* @__PURE__ */ ia(e);
  return () => Td[t] ?? n();
}
const Sd = /* @__PURE__ */ Ua(() => window.ScrollTimeline !== void 0, "scrollTimeline"), Wa = /* @__PURE__ */ Ua(() => {
  try {
    document.createElement("div").animate({ opacity: 0 }, { easing: "linear(0, 1)" });
  } catch {
    return !1;
  }
  return !0;
}, "linearEasing"), St = ([e, t, n, i]) => `cubic-bezier(${e}, ${t}, ${n}, ${i})`, fr = {
  linear: "linear",
  ease: "ease",
  easeIn: "ease-in",
  easeOut: "ease-out",
  easeInOut: "ease-in-out",
  circIn: /* @__PURE__ */ St([0, 0.65, 0.55, 1]),
  circOut: /* @__PURE__ */ St([0.55, 0, 1, 0.45]),
  backIn: /* @__PURE__ */ St([0.31, 0.01, 0.66, -0.59]),
  backOut: /* @__PURE__ */ St([0.33, 1.53, 0.69, 0.99])
};
function _a(e, t) {
  if (e)
    return typeof e == "function" ? Wa() ? Na(e, t) : "ease-out" : /* @__PURE__ */ ma(e) ? St(e) : Array.isArray(e) ? e.map((n) => _a(n, t) || fr.easeOut) : fr[e];
}
function Ad(e, t, n, { delay: i = 0, duration: s = 300, repeat: r = 0, repeatType: o = "loop", ease: a = "easeOut", times: l } = {}, u = void 0) {
  const d = {
    [t]: n
  };
  l && (d.offset = l);
  const h = _a(a, s);
  Array.isArray(h) && (d.easing = h);
  const f = {
    delay: i,
    duration: s,
    easing: Array.isArray(h) ? "linear" : h,
    fill: "both",
    iterations: r + 1,
    direction: o === "reverse" ? "alternate" : "normal"
  };
  return u && (f.pseudoElement = u), e.animate(d, f);
}
function gs(e) {
  return typeof e == "function" && "applyToOptions" in e;
}
function Nd({ type: e, ...t }) {
  return gs(e) && Wa() ? e.applyToOptions(t) : (t.duration ?? (t.duration = 300), t.ease ?? (t.ease = "easeOut"), t);
}
class za extends fs {
  constructor(t) {
    if (super(), this.finishedTime = null, this.isStopped = !1, this.manualStartTime = null, !t)
      return;
    const { element: n, name: i, keyframes: s, pseudoElement: r, allowFlatten: o = !1, finalKeyframe: a, onComplete: l } = t;
    this.isPseudoElement = !!r, this.allowFlatten = o, this.options = t, ye(typeof t.type != "string", `Mini animate() doesn't support "type" as a string.`, "mini-spring");
    const u = Nd(t);
    this.animation = Ad(n, i, s, u, r), u.autoplay === !1 && this.animation.pause(), this.animation.onfinish = () => {
      if (this.finishedTime = this.time, !r) {
        const d = Cn(s, this.options, a, this.speed);
        this.updateMotionValue && this.updateMotionValue(d), ja(n, i, d), this.animation.cancel();
      }
      l?.(), this.notifyFinished();
    }, Fa(this, t, u);
  }
  play() {
    this.isStopped || (this.manualStartTime = null, this.animation.play(), this.state === "finished" && this.updateFinished());
  }
  pause() {
    this.animation.pause();
  }
  complete() {
    this.animation.finish?.();
  }
  cancel() {
    try {
      this.animation.cancel();
    } catch {
    }
  }
  stop() {
    if (this.isStopped)
      return;
    this.isStopped = !0;
    const { state: t } = this;
    t === "idle" || t === "finished" || (this.updateMotionValue ? this.updateMotionValue() : this.commitStyles(), this.isPseudoElement || this.cancel());
  }
  /**
   * WAAPI doesn't natively have any interruption capabilities.
   *
   * In this method, we commit styles back to the DOM before cancelling
   * the animation.
   *
   * This is designed to be overridden by NativeAnimationExtended, which
   * will create a renderless JS animation and sample it twice to calculate
   * its current value, "previous" value, and therefore allow
   * Motion to also correctly calculate velocity for any subsequent animation
   * while deferring the commit until the next animation frame.
   */
  commitStyles() {
    const t = this.options?.element;
    !this.isPseudoElement && t?.isConnected && this.animation.commitStyles?.();
  }
  get duration() {
    const t = this.animation.effect?.getComputedTiming?.().duration || 0;
    return /* @__PURE__ */ pe(Number(t));
  }
  get iterationDuration() {
    const { delay: t = 0 } = this.options || {};
    return this.duration + /* @__PURE__ */ pe(t);
  }
  get time() {
    return /* @__PURE__ */ pe(Number(this.animation.currentTime) || 0);
  }
  set time(t) {
    const n = this.finishedTime !== null;
    this.manualStartTime = null, this.finishedTime = null, this.animation.currentTime = /* @__PURE__ */ he(t), n && this.animation.pause();
  }
  /**
   * The playback speed of the animation.
   * 1 = normal speed, 2 = double speed, 0.5 = half speed.
   */
  get speed() {
    return this.animation.playbackRate;
  }
  set speed(t) {
    t < 0 && (this.finishedTime = null), this.animation.playbackRate = t;
  }
  get state() {
    return this.finishedTime !== null ? "finished" : this.animation.playState;
  }
  get startTime() {
    return this.manualStartTime ?? Number(this.animation.startTime);
  }
  set startTime(t) {
    this.manualStartTime = this.animation.startTime = t;
  }
  /**
   * Attaches a timeline to the animation, for instance the `ScrollTimeline`.
   */
  attachTimeline({ timeline: t, rangeStart: n, rangeEnd: i, observe: s }) {
    return this.allowFlatten && this.animation.effect?.updateTiming({ easing: "linear" }), this.animation.onfinish = null, t && Sd() ? (this.animation.timeline = t, n && (this.animation.rangeStart = n), i && (this.animation.rangeEnd = i), we) : s(this);
  }
}
const Ga = {
  anticipate: ca,
  backInOut: la,
  circInOut: da
};
function Pd(e) {
  return e in Ga;
}
function Md(e) {
  typeof e.ease == "string" && Pd(e.ease) && (e.ease = Ga[e.ease]);
}
const Gn = 10;
class Cd extends za {
  constructor(t) {
    Md(t), Ra(t), super(t), t.startTime !== void 0 && t.autoplay !== !1 && (this.startTime = t.startTime), this.options = t;
  }
  /**
   * WAAPI doesn't natively have any interruption capabilities.
   *
   * Rather than read committed styles back out of the DOM, we can
   * create a renderless JS animation and sample it twice to calculate
   * its current value, "previous" value, and therefore allow
   * Motion to calculate velocity for any subsequent animation.
   */
  updateMotionValue(t) {
    const { motionValue: n, onUpdate: i, onComplete: s, element: r, ...o } = this.options;
    if (!n)
      return;
    if (t !== void 0) {
      n.set(t);
      return;
    }
    const a = new vn({
      ...o,
      autoplay: !1
    }), l = Math.max(Gn, ae.now() - this.startTime), u = ke(0, Gn, l - Gn), d = a.sample(l).value, { name: h } = this.options;
    r && h && ja(r, h, d), n.setWithVelocity(a.sample(Math.max(0, l - u)).value, d, u), a.stop();
  }
}
const hr = (e, t) => t === "zIndex" ? !1 : !!(typeof e == "number" || Array.isArray(e) || typeof e == "string" && // It's animatable if we have a string
(ge.test(e) || e === "0") && // And it contains numbers and/or colors
!e.startsWith("url("));
function Ed(e) {
  const t = e[0];
  if (e.length === 1)
    return !0;
  for (let n = 0; n < e.length; n++)
    if (e[n] !== t)
      return !0;
}
function Dd(e, t, n, i) {
  const s = e[0];
  if (s === null)
    return !1;
  if (t === "display" || t === "visibility")
    return !0;
  const r = e[e.length - 1], o = hr(s, t), a = hr(r, t);
  return !o || !a ? (o !== a && Je(!1, `You are trying to animate ${t} from "${s}" to "${r}". "${o ? r : s}" is not an animatable value.`, "value-not-animatable"), !1) : Ed(e) || (n === "spring" || gs(n)) && i;
}
function Si(e) {
  e.duration = 0, e.type = "keyframes";
}
const Ai = /* @__PURE__ */ new Set([
  "opacity",
  "clipPath",
  "filter",
  "transform",
  "backgroundColor"
]), Vd = /^(?:oklch|oklab|lab|lch|color|color-mix|light-dark)\(/;
function Rd(e) {
  for (let t = 0; t < e.length; t++)
    if (typeof e[t] == "string" && Vd.test(e[t]))
      return !0;
  return !1;
}
const pr = /* @__PURE__ */ new Set([
  "color",
  "backgroundColor",
  "outlineColor",
  "fill",
  "stroke",
  "borderColor",
  "borderTopColor",
  "borderRightColor",
  "borderBottomColor",
  "borderLeftColor"
]), Ld = /* @__PURE__ */ ia(() => Object.hasOwnProperty.call(Element.prototype, "animate"));
function Fd(e) {
  const { motionValue: t, name: n, repeatDelay: i, repeatType: s, damping: r, type: o, keyframes: a } = e;
  if (!n || !(Ai.has(n) || pr.has(n)))
    return !1;
  const l = t?.owner?.current;
  if (!(l instanceof HTMLElement) && !(l instanceof SVGElement))
    return !1;
  const { onUpdate: u, transformTemplate: d } = t.owner.getProps();
  return Ld() && /**
   * Force WAAPI for color properties with browser-only color formats
   * (oklch, oklab, lab, lch, etc.) that the JS animation path can't parse.
   */
  (Ai.has(n) || pr.has(n) && Rd(a)) && (n !== "transform" || !d) && /**
   * If we're outputting values to onUpdate then we can't use WAAPI as there's
   * no way to read the value from WAAPI every frame.
   */
  !u && !i && s !== "mirror" && r !== 0 && o !== "inertia";
}
const Id = 40;
class Od extends fs {
  constructor(t) {
    super(), this.stop = () => {
      this._animation && (this._animation.stop(), this.stopTimeline?.()), this.keyframeResolver?.cancel();
    }, this.createdAt = ae.now();
    const { keyframes: n, name: i, motionValue: s, element: r } = t, o = t;
    o.autoplay ?? (o.autoplay = !0), o.delay ?? (o.delay = 0), o.type ?? (o.type = "keyframes"), o.repeat ?? (o.repeat = 0), o.repeatDelay ?? (o.repeatDelay = 0), o.repeatType ?? (o.repeatType = "loop");
    const a = r?.KeyframeResolver || ps;
    this.keyframeResolver = new a(n, (l, u, d) => this.onKeyframesResolved(l, u, o, !d), i, s, r), this.keyframeResolver?.scheduleResolve();
  }
  onKeyframesResolved(t, n, i, s) {
    this.keyframeResolver = void 0;
    const { name: r, type: o, velocity: a, delay: l, isHandoff: u, onUpdate: d } = i;
    this.resolvedAt = ae.now();
    let h = !0;
    Dd(t, r, o, a) || (h = !1, (De.instantAnimations || !l) && d?.(Cn(t, i, n)), t[0] = t[t.length - 1], Si(i), i.repeat = 0);
    const f = s ? this.resolvedAt ? this.resolvedAt - this.createdAt > Id ? this.resolvedAt : this.createdAt : this.createdAt : void 0, { onComplete: p } = i;
    i.startTime ?? (i.startTime = f), i.finalKeyframe = n, i.keyframes = t, i.onComplete = () => {
      p?.(), this.notifyFinished();
    };
    const g = h && !u && Fd(i);
    let x;
    if (g) {
      i.element = i.motionValue?.owner?.current;
      try {
        x = new Cd(i);
      } catch {
        x = new vn(i);
      }
    } else
      x = new vn(i);
    this.pendingTimeline && (this.stopTimeline = x.attachTimeline(this.pendingTimeline), this.pendingTimeline = void 0), this._animation = x;
  }
  get finished() {
    return this._animation ? this._animation.finished : super.finished;
  }
  then(t, n) {
    return this.finished.finally(t).then(() => {
    });
  }
  get animation() {
    return this._animation || (this.keyframeResolver?.resume(), wd()), this._animation;
  }
  get duration() {
    return this.animation.duration;
  }
  get iterationDuration() {
    return this.animation.iterationDuration;
  }
  get time() {
    return this.animation.time;
  }
  set time(t) {
    this.animation.time = t;
  }
  get speed() {
    return this.animation.speed;
  }
  get state() {
    return this.animation.state;
  }
  set speed(t) {
    this.animation.speed = t;
  }
  get startTime() {
    return this.animation.startTime;
  }
  attachTimeline(t) {
    return this._animation ? this.stopTimeline = this.animation.attachTimeline(t) : this.pendingTimeline = t, () => this.stop();
  }
  play() {
    this.animation.play();
  }
  pause() {
    this.animation.pause();
  }
  complete() {
    this.animation.complete();
  }
  cancel() {
    this._animation && this.animation.cancel(), this.keyframeResolver?.cancel();
  }
}
class Bd {
  constructor(t) {
    this.stop = () => this.runAll("stop"), this.animations = t.filter(Boolean);
  }
  get finished() {
    return Promise.all(this.animations.map((t) => t.finished));
  }
  /**
   * TODO: Filter out cancelled or stopped animations before returning
   */
  getAll(t) {
    return this.animations[0][t];
  }
  setAll(t, n) {
    for (let i = 0; i < this.animations.length; i++)
      this.animations[i][t] = n;
  }
  attachTimeline(t) {
    const n = this.animations.map((i) => i.attachTimeline(t));
    return () => {
      n.forEach((i, s) => {
        i && i(), this.animations[s].stop();
      });
    };
  }
  get time() {
    return this.getAll("time");
  }
  set time(t) {
    this.setAll("time", t);
  }
  get speed() {
    return this.getAll("speed");
  }
  set speed(t) {
    this.setAll("speed", t);
  }
  get state() {
    return this.getAll("state");
  }
  get startTime() {
    return this.getAll("startTime");
  }
  get duration() {
    return mr(this.animations, "duration");
  }
  get iterationDuration() {
    return mr(this.animations, "iterationDuration");
  }
  runAll(t) {
    this.animations.forEach((n) => n[t]());
  }
  play() {
    this.runAll("play");
  }
  pause() {
    this.runAll("pause");
  }
  cancel() {
    this.runAll("cancel");
  }
  complete() {
    this.runAll("complete");
  }
}
function mr(e, t) {
  let n = 0;
  for (let i = 0; i < e.length; i++) {
    const s = e[i][t];
    s !== null && s > n && (n = s);
  }
  return n;
}
class $d extends Bd {
  then(t, n) {
    return this.finished.finally(t).then(() => {
    });
  }
}
function Ka(e, t, n, i = 0, s = 1) {
  const r = Array.from(e).sort((u, d) => u.sortNodePosition(d)).indexOf(t), o = e.size, a = (o - 1) * i;
  return typeof n == "function" ? n(r, o) : s === 1 ? r * i : a - r * i;
}
const gr = 30, jd = (e) => !isNaN(parseFloat(e)), At = {
  current: void 0
};
class Nt {
  /**
   * @param init - The initiating value
   * @param config - Optional configuration options
   *
   * -  `transformer`: A function to transform incoming values with.
   */
  constructor(t, n = {}) {
    this.canTrackVelocity = null, this.events = {}, this.updateAndNotify = (i) => {
      const s = ae.now();
      if (this.updatedAt !== s && this.setPrevFrameValue(), this.prev = this.current, this.setCurrent(i), this.current !== this.prev && (this.notifyChange(), this.dependents))
        for (const r of this.dependents)
          r.dirty();
    }, this.hasAnimated = !1, this.setCurrent(t), this.owner = n.owner;
  }
  setCurrent(t) {
    this.current = t, this.updatedAt = ae.now(), this.canTrackVelocity === null && t !== void 0 && (this.canTrackVelocity = jd(this.current));
  }
  setPrevFrameValue(t = this.current) {
    this.prevFrameValue = t, this.prevUpdatedAt = this.updatedAt;
  }
  /**
   * Adds a function that will be notified when the `MotionValue` is updated.
   *
   * It returns a function that, when called, will cancel the subscription.
   *
   * When calling `onChange` inside a React component, it should be wrapped with the
   * `useEffect` hook. As it returns an unsubscribe function, this should be returned
   * from the `useEffect` function to ensure you don't add duplicate subscribers..
   *
   * ```jsx
   * export const MyComponent = () => {
   *   const x = useMotionValue(0)
   *   const y = useMotionValue(0)
   *   const opacity = useMotionValue(1)
   *
   *   useEffect(() => {
   *     function updateOpacity() {
   *       const maxXY = Math.max(x.get(), y.get())
   *       const newOpacity = transform(maxXY, [0, 100], [1, 0])
   *       opacity.set(newOpacity)
   *     }
   *
   *     const unsubscribeX = x.on("change", updateOpacity)
   *     const unsubscribeY = y.on("change", updateOpacity)
   *
   *     return () => {
   *       unsubscribeX()
   *       unsubscribeY()
   *     }
   *   }, [])
   *
   *   return <motion.div style={{ x }} />
   * }
   * ```
   *
   * @param subscriber - A function that receives the latest value.
   * @returns A function that, when called, will cancel this subscription.
   *
   * @deprecated
   */
  onChange(t) {
    return process.env.NODE_ENV !== "production" && Mn(!1, 'value.onChange(callback) is deprecated. Switch to value.on("change", callback).'), this.on("change", t);
  }
  on(t, n) {
    var i;
    return t === "change" ? this.onChangeSubscribe(n) : ((i = this.events)[t] || (i[t] = new gn())).add(n);
  }
  onChangeSubscribe(t) {
    const { events: n } = this;
    return !n.change && !this.changeSubscriber ? this.changeSubscriber = t : (n.change || (n.change = new gn(), n.change.add(this.changeSubscriber), this.changeSubscriber = void 0), n.change.add(t)), () => {
      this.changeSubscriber === t ? this.changeSubscriber = void 0 : n.change?.remove(t), this.stopIfUnobserved();
    };
  }
  /**
   * If we have no more change listeners by the start
   * of the next frame, stop active animations.
   */
  stopIfUnobserved() {
    z.read(() => {
      !this.changeSubscriber && !this.events.change?.getSize() && this.stop();
    });
  }
  clearListeners() {
    this.changeSubscriber = void 0;
    for (const t in this.events)
      this.events[t].clear();
  }
  /**
   * Attaches a passive effect to the `MotionValue`.
   */
  attach(t, n) {
    this.passiveEffect = t, this.stopPassiveEffect = n;
  }
  /**
   * Sets the state of the `MotionValue`.
   *
   * @remarks
   *
   * ```jsx
   * const x = useMotionValue(0)
   * x.set(10)
   * ```
   *
   * @param latest - Latest value to set.
   * @param render - Whether to notify render subscribers. Defaults to `true`
   *
   * @public
   */
  set(t) {
    this.passiveEffect ? this.passiveEffect(t, this.updateAndNotify) : this.updateAndNotify(t);
  }
  setWithVelocity(t, n, i) {
    this.set(n), this.prev = void 0, this.prevFrameValue = t, this.prevUpdatedAt = this.updatedAt - i;
  }
  /**
   * Set the state of the `MotionValue`, stopping any active animations,
   * effects, and resets velocity to `0`.
   */
  jump(t, n = !0) {
    this.updateAndNotify(t), this.prev = t, this.prevUpdatedAt = this.prevFrameValue = void 0, n && this.stop(), this.stopPassiveEffect && this.stopPassiveEffect();
  }
  dirty() {
    this.notifyChange();
  }
  notifyChange() {
    const { current: t, changeSubscriber: n } = this;
    n ? n(t) : this.events.change?.notify(t);
  }
  addDependent(t) {
    this.dependents || (this.dependents = /* @__PURE__ */ new Set()), this.dependents.add(t);
  }
  removeDependent(t) {
    this.dependents && this.dependents.delete(t);
  }
  /**
   * Returns the latest state of `MotionValue`
   *
   * @returns - The latest state of `MotionValue`
   *
   * @public
   */
  get() {
    return At.current && At.current.push(this), this.current;
  }
  /**
   * @public
   */
  getPrevious() {
    return this.prev;
  }
  /**
   * Returns the latest velocity of `MotionValue`
   *
   * @returns - The latest velocity of `MotionValue`. Returns `0` if the state is non-numerical.
   *
   * @public
   */
  getVelocity() {
    const t = ae.now();
    if (!this.canTrackVelocity || this.prevFrameValue === void 0 || t - this.updatedAt > gr)
      return 0;
    const n = Math.min(this.updatedAt - this.prevUpdatedAt, gr);
    return /* @__PURE__ */ sa(parseFloat(this.current) - parseFloat(this.prevFrameValue), n);
  }
  /**
   * Registers a new animation to control this `MotionValue`. Only one
   * animation can drive a `MotionValue` at one time.
   *
   * ```jsx
   * value.start()
   * ```
   *
   * @param animation - A function that starts the provided animation
   */
  start(t) {
    return this.stop(), new Promise((n) => {
      this.hasAnimated = !0;
      let i = !1, s;
      s = t(() => {
        i = !0, this.events.animationComplete?.notify(), this.animation === s && this.clearAnimation(), n();
      }), i || (this.animation = s), this.events.animationStart?.notify();
    });
  }
  /**
   * Stop the currently active animation.
   *
   * @public
   */
  stop() {
    this.animation && (this.animation.stop(), this.events.animationCancel && this.events.animationCancel.notify()), this.clearAnimation();
  }
  /**
   * Returns `true` if this value is currently animating.
   *
   * @public
   */
  isAnimating() {
    return !!this.animation;
  }
  clearAnimation() {
    this.animation = void 0;
  }
  /**
   * Destroy and clean up subscribers to this `MotionValue`.
   *
   * The `MotionValue` hooks like `useMotionValue` and `useTransform` automatically
   * handle the lifecycle of the returned `MotionValue`, so this method is only necessary if you've manually
   * created a `MotionValue` via the `motionValue` function.
   *
   * @public
   */
  destroy() {
    this.dependents?.clear(), this.events.destroy?.notify(), this.clearListeners(), this.stop(), this.stopPassiveEffect && this.stopPassiveEffect();
  }
}
function Re(e, t) {
  return new Nt(e, t);
}
function Ha(e, t) {
  if (e?.inherit && t) {
    const { inherit: n, ...i } = e;
    return { ...t, ...i };
  }
  return e;
}
function ys(e, t) {
  const n = e?.[t] ?? e?.default ?? e;
  return n !== e ? Ha(n, e) : n;
}
const Ud = {
  type: "spring",
  stiffness: 500,
  damping: 25,
  restSpeed: 10
}, Wd = (e) => ({
  type: "spring",
  stiffness: 550,
  damping: e === 0 ? 2 * Math.sqrt(550) : 30,
  restSpeed: 10
}), _d = {
  type: "keyframes",
  duration: 0.8
}, zd = {
  type: "keyframes",
  ease: [0.25, 0.1, 0.35, 1],
  duration: 0.3
}, Gd = (e, { keyframes: t }) => t.length > 2 ? _d : Fe.has(e) ? e.startsWith("scale") ? Wd(t[1]) : Ud : zd, Kd = /* @__PURE__ */ new Set([
  "when",
  "delay",
  "delayChildren",
  "staggerChildren",
  "staggerDirection",
  "repeat",
  "repeatType",
  "repeatDelay",
  "from",
  "elapsed"
]);
function Hd(e) {
  for (const t in e)
    if (!Kd.has(t))
      return !0;
  return !1;
}
const En = (e, t, n, i = {}, s, r) => (o) => {
  const a = ys(i, e) || {}, l = a.delay || i.delay || 0;
  let { elapsed: u = 0 } = i;
  u = u - /* @__PURE__ */ he(l);
  const d = {
    keyframes: Array.isArray(n) ? n : [null, n],
    ease: "easeOut",
    velocity: t.getVelocity(),
    ...a,
    delay: -u,
    onUpdate: (f) => {
      t.set(f), a.onUpdate && a.onUpdate(f);
    },
    onComplete: () => {
      o(), a.onComplete && a.onComplete();
    },
    name: e,
    motionValue: t,
    element: r ? void 0 : s
  };
  Hd(a) || Object.assign(d, Gd(e, d)), d.duration && (d.duration = /* @__PURE__ */ he(d.duration)), d.repeatDelay && (d.repeatDelay = /* @__PURE__ */ he(d.repeatDelay)), d.from !== void 0 && (d.keyframes[0] = d.from);
  let h = !1;
  if ((d.type === !1 || d.duration === 0 && !d.repeatDelay) && (Si(d), d.delay === 0 && (h = !0)), (De.instantAnimations || De.skipAnimations || s?.shouldSkipAnimations || a.skipAnimations) && (h = !0, Si(d), d.delay = 0), d.allowFlatten = !a.type && !a.ease, h && !r && t.get() !== void 0) {
    const f = Cn(d.keyframes, a);
    if (f !== void 0) {
      z.update(() => {
        d.onUpdate(f), d.onComplete();
      });
      return;
    }
  }
  return a.isSync ? new vn(d) : new Od(d);
}, qd = (
  // eslint-disable-next-line redos-detector/no-unsafe-regex -- false positive, as it can match a lot of words
  /^var\(--(?:([\w-]+)|([\w-]+), ?([a-zA-Z\d ()%#.,-]+))\)/u
);
function Yd(e) {
  const t = qd.exec(e);
  if (!t)
    return [,];
  const [, n, i, s] = t;
  return [`--${n ?? i}`, s];
}
const Xd = 4;
function qa(e, t, n = 1) {
  ye(n <= Xd, `Max CSS variable fallback depth detected in property "${e}". This may indicate a circular fallback dependency.`, "max-css-var-depth");
  const [i, s] = Yd(e);
  if (!i)
    return;
  const r = window.getComputedStyle(t).getPropertyValue(i);
  if (r) {
    const o = r.trim();
    return Ji(o) ? parseFloat(o) : o;
  }
  return rs(s) ? qa(s, t, n + 1) : s;
}
function yr(e) {
  const t = [{}, {}];
  return e?.values.forEach((n, i) => {
    t[0][i] = n.get(), t[1][i] = n.getVelocity();
  }), t;
}
function xs(e, t, n, i) {
  if (typeof t == "function") {
    const [s, r] = yr(i);
    t = t(n !== void 0 ? n : e.custom, s, r);
  }
  if (typeof t == "string" && (t = e.variants && e.variants[t]), typeof t == "function") {
    const [s, r] = yr(i);
    t = t(n !== void 0 ? n : e.custom, s, r);
  }
  return t;
}
function Xe(e, t, n) {
  const i = e.getProps();
  return xs(i, t, n !== void 0 ? n : i.custom, e);
}
const vs = /* @__PURE__ */ new Set([
  "width",
  "height",
  "top",
  "left",
  "right",
  "bottom",
  ...je
]), Ni = (e) => Array.isArray(e);
function Zd(e, t, n) {
  e.hasValue(t) ? e.getValue(t).set(n) : e.addValue(t, Re(n));
}
function Qd(e) {
  return Ni(e) ? e[e.length - 1] || 0 : e;
}
function Jd(e, t) {
  const n = Xe(e, t);
  let { transitionEnd: i = {}, transition: s = {}, ...r } = n || {};
  r = { ...r, ...i };
  for (const o in r) {
    const a = Qd(r[o]);
    Zd(e, o, a);
  }
}
const ie = (e) => !!(e && e.getVelocity);
function ef(e) {
  return !!(ie(e) && e.add);
}
function Pi(e, t) {
  const n = e.getValue("willChange");
  if (ef(n))
    return n.add(t);
  if (!n && De.WillChange) {
    const i = new De.WillChange("auto");
    e.addValue("willChange", i), i.add(t);
  }
}
function Gt(e) {
  return e.replace(/([A-Z])/g, (t) => `-${t.toLowerCase()}`);
}
const tf = "framerAppearId", Ya = "data-" + Gt(tf);
function Xa(e) {
  return e.props[Ya];
}
const nf = typeof window < "u";
function sf({ protectedKeys: e, needsAnimating: t }, n) {
  const i = e.hasOwnProperty(n) && t[n] !== !0;
  return t[n] = !1, i;
}
function Za(e, t, { delay: n = 0, transitionOverride: i, type: s } = {}) {
  let { transition: r, transitionEnd: o, ...a } = t;
  const l = e.getDefaultTransition();
  r = r ? Ha(r, l) : l;
  const u = r?.reduceMotion, d = r?.skipAnimations;
  i && (r = i);
  const h = [], f = s && e.animationState && e.animationState.getState()[s], p = r?.path;
  p && p.animateVisualElement(e, a, r, n, h);
  for (const g in a) {
    const x = e.getValue(g, e.latestValues[g] ?? null), b = a[g];
    if (b === void 0 || f && sf(f, g))
      continue;
    const w = {
      delay: n,
      ...ys(r || {}, g)
    };
    d && (w.skipAnimations = !0);
    const T = x.get();
    if (T !== void 0 && !x.isAnimating() && !Array.isArray(b) && b === T && !w.velocity) {
      z.update(() => x.set(b));
      continue;
    }
    let y = !1;
    if (nf && window.MotionHandoffAnimation) {
      const P = Xa(e);
      if (P) {
        const S = window.MotionHandoffAnimation(P, g, z);
        S !== null && (w.startTime = S, y = !0);
      }
    }
    Pi(e, g);
    const k = u ?? e.shouldReduceMotion;
    x.start(En(g, x, b, k && vs.has(g) ? { type: !1 } : w, e, y));
    const E = x.animation;
    E && h.push(E);
  }
  if (o) {
    const g = () => z.update(() => {
      o && Jd(e, o);
    });
    h.length ? Promise.all(h).then(g) : g();
  }
  return h;
}
function Mi(e, t, n = {}) {
  const i = Xe(e, t, n.type === "exit" ? e.presenceContext?.custom : void 0);
  let { transition: s = e.getDefaultTransition() || {} } = i || {};
  n.transitionOverride && (s = n.transitionOverride);
  const r = i ? () => Promise.all(Za(e, i, n)) : () => Promise.resolve(), o = e.variantChildren && e.variantChildren.size ? (l = 0) => {
    const { delayChildren: u = 0, staggerChildren: d, staggerDirection: h } = s;
    return rf(e, t, l, u, d, h, n);
  } : () => Promise.resolve(), { when: a } = s;
  if (a) {
    const [l, u] = a === "beforeChildren" ? [r, o] : [o, r];
    return l().then(() => u());
  } else
    return Promise.all([r(), o(n.delay)]);
}
function rf(e, t, n = 0, i = 0, s = 0, r = 1, o) {
  const a = [];
  for (const l of e.variantChildren)
    l.notify("AnimationStart", t), a.push(Mi(l, t, {
      ...o,
      delay: n + (typeof i == "function" ? 0 : i) + Ka(e.variantChildren, l, i, s, r)
    }).then(() => l.notify("AnimationComplete", t)));
  return Promise.all(a);
}
function of(e, t, n = {}) {
  e.notify("AnimationStart", t);
  let i;
  if (Array.isArray(t)) {
    const s = t.map((r) => Mi(e, r, n));
    i = Promise.all(s);
  } else if (typeof t == "string")
    i = Mi(e, t, n);
  else {
    const s = typeof t == "function" ? Xe(e, t, n.custom) : t;
    i = Promise.all(Za(e, s, n));
  }
  return i.then(() => {
    e.notify("AnimationComplete", t);
  });
}
const af = {
  test: (e) => e === "auto",
  parse: (e) => e
}, lf = (e) => (t) => t.test(e), cf = [pt, V, Pe, Ee, Nu, Au, af], xr = (e) => cf.find(lf(e));
function uf(e) {
  return typeof e == "number" ? e === 0 : e !== null ? e === "none" || e === "0" || ts(e) : !0;
}
const df = /* @__PURE__ */ new Set(["auto", "none", "0"]);
function ff(e, t, n) {
  let i = 0, s;
  for (; i < e.length && !s; ) {
    const r = e[i];
    typeof r == "string" && !df.has(r) && Vu(r) && (s = e[i]), i++;
  }
  if (s && n)
    for (const r of t)
      e[r] !== s && (e[r] = hs(n, s));
}
class Qa extends ps {
  constructor(t, n, i, s, r) {
    super(t, n, i, s, r, !0);
  }
  readKeyframes() {
    const { unresolvedKeyframes: t, element: n, name: i } = this;
    if (!n || !n.current)
      return;
    super.readKeyframes();
    for (let d = 0; d < t.length; d++) {
      let h = t[d];
      if (typeof h == "string" && (h = h.trim(), rs(h))) {
        const f = qa(h, n.current);
        f !== void 0 && (t[d] = f), d === t.length - 1 && (this.finalKeyframe = h);
      }
    }
    if (this.resolveNoneKeyframes(), !vs.has(i) || t.length !== 2)
      return;
    const [s, r] = t;
    if (typeof s == "number" && typeof r == "number")
      return;
    const o = xr(s), a = xr(r), l = er(s), u = er(r);
    if (l !== u && qe[i]) {
      this.needsMeasurement = !0;
      return;
    }
    if (o !== a)
      if (ur(o) && ur(a))
        for (let d = 0; d < t.length; d++) {
          const h = t[d];
          typeof h == "string" && (t[d] = parseFloat(h));
        }
      else qe[i] && (this.needsMeasurement = !0);
  }
  resolveNoneKeyframes() {
    const { unresolvedKeyframes: t, name: n } = this, i = [];
    for (let s = 0; s < t.length; s++)
      (t[s] === null || uf(t[s])) && i.push(s);
    i.length && ff(t, i, n);
  }
  measure() {
    const { element: t, name: n } = this;
    return qe[n](window.getComputedStyle(t.current), () => t.measureViewportBox());
  }
  measureInitialState() {
    const { element: t, unresolvedKeyframes: n, name: i } = this;
    if (!t || !t.current)
      return;
    i === "height" && (this.suspendedScrollY = window.pageYOffset), this.measuredOrigin = this.measure(), n[0] = this.measuredOrigin;
    const s = n[n.length - 1];
    s !== void 0 && this.motionValue?.jump(s, !1);
  }
  measureEndState() {
    const { element: t, unresolvedKeyframes: n } = this;
    if (!t || !t.current)
      return;
    this.motionValue?.jump(this.measuredOrigin, !1);
    const i = n.length - 1, s = n[i];
    n[i] = this.measure(), s !== null && this.finalKeyframe === void 0 && (this.finalKeyframe = s), this.removedTransforms?.length && this.removedTransforms.forEach(([r, o]) => {
      t.getValue(r).set(o);
    }), this.resolveNoneKeyframes();
  }
}
const bs = [
  "borderTopLeftRadius",
  "borderTopRightRadius",
  "borderBottomRightRadius",
  "borderBottomLeftRadius"
], ws = [];
function hf(e) {
  ye(typeof e.test == "function" && typeof e.read == "function", "Effects passed to animate.addEffect() need test() and read().", "effect-missing-test"), Ja(e), ws.unshift(e);
}
function Ja(e) {
  Ze(ws, e);
}
function pf(e) {
  return ws.find((t) => t.test(e));
}
function el(e, t, n = {}, i) {
  const s = [], { velocity: r } = n, o = n.reduceMotion ?? i?.shouldReduceMotion;
  for (const l in t) {
    if (l === "transition" || l === "transitionEnd")
      continue;
    const u = t[l];
    if (u === void 0)
      continue;
    const d = e(l), h = d.get();
    if (h !== void 0 && !d.isAnimating() && !Array.isArray(u) && u === h && !r) {
      z.update(() => d.set(u));
      continue;
    }
    d.start(En(l, d, u, o && vs.has(l) ? { type: !1 } : n, i)), d.animation && s.push(d.animation);
  }
  const { transitionEnd: a } = t;
  if (a) {
    const l = () => z.update(() => {
      for (const u in a)
        e(u).set(a[u]);
    });
    s.length ? Promise.all(s).then(l) : l();
  }
  return s;
}
function tl(e, t, n, i, s) {
  return el((r) => {
    let o = e.get(t, r);
    if (!o) {
      let a;
      if (!s) {
        const l = n[r];
        a = mf(l) ?? e.read(t, r, l), ye(a !== void 0, `"${r}" can't be read from the animated subject. Provide [from, to] keyframes.`, "effect-unreadable-value");
      }
      o = Re(a, { owner: s }), e(t, { [r]: o });
    }
    return o;
  }, n, i, s);
}
function mf(e) {
  const t = Array.isArray(e) ? e[0] : void 0;
  return t === null ? void 0 : t;
}
function ut(e) {
  return es(e) && "offsetHeight" in e && !("ownerSVGElement" in e);
}
function mt(e) {
  return es(e) && "ownerSVGElement" in e;
}
const Le = (e, t) => t && typeof e == "number" ? t.transform(e) : e;
function ks(e, t, n) {
  if (e == null)
    return [];
  if (e instanceof EventTarget)
    return [e];
  if (typeof e == "string") {
    let i = document;
    t && (i = t.current);
    const s = n?.[e] ?? i.querySelectorAll(e);
    return s ? Array.from(s) : [];
  }
  return Array.from(e).filter((i) => i != null);
}
class gf {
  /**
   * @param step - The frameloop step renders are scheduled in. Defaults
   * to `frame.render`. Effects that feed a render loop running in
   * `frame.render` (GPU scenes) should write in `frame.preRender`.
   */
  constructor(t = z.render) {
    this.step = t, this.values = /* @__PURE__ */ new Map(), this.pending = [], this.numPending = 0, this.flush = () => {
      const { pending: n, numPending: i } = this;
      this.numPending = 0;
      for (let s = 0; s < i; s++)
        n[s]();
    };
  }
  /**
   * @param render - Writes the value to the subject. Renders read the
   * motion value directly rather than a cached copy, so there is one
   * place a value lives.
   * @param computed - A value already in this state (e.g. `transform`)
   * whose render should run whenever `value` changes.
   */
  set(t, n, i, s) {
    if (this.values.get(t)?.onRemove(), s)
      for (const l of this.values.values())
        l.value === s && (i = l.render);
    const r = () => i && this.schedule(i);
    n.get() !== void 0 && r();
    const o = n.on("change", r), a = () => {
      o(), i && !s && this.cancel(i), this.values.delete(t);
    };
    return this.values.set(t, {
      value: n,
      render: s ? void 0 : i,
      onRemove: a
    }), a;
  }
  get(t) {
    return this.values.get(t)?.value;
  }
  /**
   * Detach every value from this state and return them, so another
   * renderer can take them over. The state stays cached by its effect,
   * so the bound transforms are reset too rather than leaking into
   * values bound later.
   */
  release() {
    const t = /* @__PURE__ */ new Map();
    return this.values.forEach((n, i) => {
      t.set(i, n.value), n.onRemove();
    }), this.transformKeys = this.transformValues = void 0, t;
  }
  schedule(t) {
    const { pending: n, numPending: i } = this;
    for (let s = 0; s < i; s++)
      if (n[s] === t)
        return;
    i || this.step(this.flush), n[this.numPending++] = t;
  }
  cancel(t) {
    const { pending: n } = this;
    for (let i = 0; i < this.numPending; i++)
      if (n[i] === t) {
        n[i] = n[--this.numPending];
        return;
      }
  }
}
function Ts(e, { step: t, ...n } = {}) {
  const i = /* @__PURE__ */ new WeakMap();
  return Object.assign((r, o) => {
    const a = i.get(r) ?? new gf(t);
    i.set(r, a);
    const l = [];
    for (const u in o) {
      const d = o[u], h = e(r, a, u, d);
      l.push(h);
    }
    return () => {
      for (const u of l)
        u();
    };
  }, n, {
    get: (r, o) => i.get(r)?.get(o),
    flush: (r) => i.get(r)?.flush(),
    state: (r) => i.get(r)
  });
}
const yf = {
  x: "translateX",
  y: "translateY",
  z: "translateZ",
  transformPerspective: "perspective"
}, vr = {};
function xf(e) {
  let t = "";
  const { transformKeys: n = [], transformValues: i = {} } = e;
  for (let r = 0; r < n.length; r++) {
    const o = n[r], a = i[o].get();
    if (a === void 0)
      continue;
    (typeof a == "number" ? a : parseFloat(a)) !== (o.startsWith("scale") ? 1 : 0) && (t += (t && " ") + (vr[o] || (vr[o] = (yf[o] || o) + "(")) + Le(a, gi[o]) + ")");
  }
  const s = e.get("pathRotation")?.get();
  return s && (t += (t && " ") + "rotate(" + Le(s, gi.pathRotation) + ")"), t || "none";
}
const vf = /* @__PURE__ */ new Set(["originX", "originY", "originZ"]), Kn = (e, t) => Le(e.get(t)?.get(), Me[t]), Ss = (e, t, n, i) => {
  let s, r;
  if (Fe.has(n)) {
    if (n !== "pathRotation") {
      const o = t.transformKeys ?? (t.transformKeys = []);
      (t.transformValues ?? (t.transformValues = {}))[n] = i, o.includes(n) || (o.push(n), o.sort((a, l) => je.indexOf(a) - je.indexOf(l)));
    }
    t.get("transform") || (!ut(e) && !t.get("transformBox") && Ss(e, t, "transformBox", new Nt("fill-box")), t.set("transform", new Nt("none"), () => {
      e.style.transform = xf(t);
    })), r = t.get("transform");
  } else vf.has(n) ? (t.get("transformOrigin") || t.set("transformOrigin", new Nt(""), () => {
    const o = Kn(t, "originX") ?? "50%", a = Kn(t, "originY") ?? "50%", l = Kn(t, "originZ") ?? 0;
    e.style.transformOrigin = `${o} ${a} ${l}`;
  }), r = t.get("transformOrigin")) : ms(n) ? s = () => {
    e.style.setProperty(n, i.get());
  } : s = () => {
    e.style[n] = Le(i.get(), Me[n]);
  };
  return t.set(n, i, s, r);
}, bf = (e) => ut(e) || mt(e), nl = (e, t) => {
  if (Fe.has(t))
    return Oa(e, t);
  const n = getComputedStyle(e), i = ms(t) ? n.getPropertyValue(t) : n[t];
  return typeof i == "string" && i.trim() || 0;
}, wf = /* @__PURE__ */ Ts(Ss, {
  test: bf,
  read: nl
}), kf = {
  x: "translateX",
  y: "translateY",
  z: "translateZ",
  transformPerspective: "perspective"
}, Tf = je.length;
function Sf(e, t, n) {
  let i = "", s = !0;
  for (let o = 0; o < Tf; o++) {
    const a = je[o], l = e[a];
    if (l === void 0)
      continue;
    let u = !0;
    if (typeof l == "number")
      u = l === (a.startsWith("scale") ? 1 : 0);
    else {
      const d = parseFloat(l);
      u = a.startsWith("scale") ? d === 1 : d === 0;
    }
    if (!u || n) {
      const d = Le(l, Me[a]);
      if (!u) {
        s = !1;
        const h = kf[a] || a;
        i += `${h}(${d}) `;
      }
      n && (t[a] = d);
    }
  }
  const r = e.pathRotation;
  return r && (s = !1, i += `rotate(${Le(r, Me.pathRotation)}) `), i = i.trim(), n ? i = n(t, s ? "" : i) : s && (i = "none"), i;
}
function As(e, t, n) {
  const { style: i, vars: s, transformOrigin: r } = e;
  let o = !1, a = !1;
  for (const l in t) {
    const u = t[l];
    if (Fe.has(l)) {
      o = !0;
      continue;
    } else if (xa(l)) {
      s[l] = u;
      continue;
    } else {
      const d = Le(u, Me[l]);
      l.startsWith("origin") ? (a = !0, r[l] = d) : i[l] = d;
    }
  }
  if (t.transform || (o || n ? i.transform = Sf(t, e.transform, n) : i.transform && (i.transform = "none")), a) {
    const { originX: l = "50%", originY: u = "50%", originZ: d = 0 } = r;
    i.transformOrigin = `${l} ${u} ${d}`;
  }
}
const Af = {
  offset: "stroke-dashoffset",
  array: "stroke-dasharray"
}, Nf = {
  offset: "strokeDashoffset",
  array: "strokeDasharray"
};
function Pf(e, t, n = 1, i = 0, s = !0) {
  e.pathLength = 1;
  const r = s ? Af : Nf;
  e[r.offset] = `${-i}`, e[r.array] = `${t} ${n}`;
}
const Ns = [
  "transform",
  "opacity",
  "offsetDistance",
  "offsetPath",
  "offsetRotate",
  "offsetAnchor"
];
function il(e, {
  attrX: t,
  attrY: n,
  attrScale: i,
  pathLength: s,
  pathSpacing: r = 1,
  pathOffset: o = 0,
  // This is object creation, which we try to avoid per-frame.
  ...a
}, l, u, d) {
  if (As(e, a, u), l) {
    e.style.viewBox && (e.attrs.viewBox = e.style.viewBox);
    return;
  }
  e.attrs = e.style, e.style = {};
  const { attrs: h, style: f } = e;
  for (const p of Ns)
    h[p] !== void 0 && (f[p] = h[p], delete h[p]);
  (f.transform || h.transformOrigin) && (f.transformOrigin = h.transformOrigin ?? "50% 50%", delete h.transformOrigin), f.transform && (f.transformBox = d?.transformBox ?? "fill-box", delete h.transformBox), t !== void 0 && (h.x = t), n !== void 0 && (h.y = n), i !== void 0 && (h.scale = i), s !== void 0 && Pf(h, s, r, o, !1);
}
function Mf(e, t) {
  if (!(t in e))
    return !1;
  const n = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e), t) || Object.getOwnPropertyDescriptor(e, t);
  return n && typeof n.set == "function";
}
const br = (e, t, n, i, s = n) => {
  const r = Mf(e, s);
  !r && (s.startsWith("data") || s.startsWith("aria")) && (s = Gt(s));
  const o = Me[n] || Me[s], a = r ? () => {
    e[s] = Le(i.get(), Me[n]);
  } : () => {
    const l = Le(i.get(), o);
    l == null ? e.removeAttribute(s) : e.setAttribute(s, String(l));
  };
  return t.set(n, i, a);
};
function Cf(e, t, n, i) {
  return z.render(() => e.setAttribute("pathLength", "1")), n === "pathOffset" ? t.set(n, i, () => {
    const s = i.get();
    e.setAttribute("stroke-dashoffset", `${-s}`);
  }) : (t.get("stroke-dasharray") || t.set("stroke-dasharray", new Nt("1 1"), () => {
    const s = t.get("pathLength")?.get() ?? 1, r = t.get("pathSpacing")?.get();
    e.setAttribute("stroke-dasharray", `${s} ${r ?? 1 - Number(s)}`);
  }), t.set(n, i, void 0, t.get("stroke-dasharray")));
}
const Ef = (e, t, n, i) => n.startsWith("path") ? Cf(e, t, n, i) : n.startsWith("attr") ? br(e, t, n, i, sl(n)) : (n in e.style ? Ss : br)(e, t, n, i), Df = (e, t) => Fe.has(t) ? Me[t]?.default || 0 : Ns.includes(t) ? nl(e, t) : (t = sl(t), e.getAttribute(Gt(t)) ?? e.getAttribute(t) ?? void 0), Vf = /* @__PURE__ */ Ts(Ef, {
  test: mt,
  read: Df
});
function sl(e) {
  return e.replace(/^attr([A-Z])/, (t, n) => n.toLowerCase());
}
function rl({ top: e, left: t, right: n, bottom: i }) {
  return {
    x: { min: t, max: n },
    y: { min: e, max: i }
  };
}
function Rf({ x: e, y: t }) {
  return { top: t.min, right: e.max, bottom: t.max, left: e.min };
}
function Lf(e, t) {
  if (!t)
    return e;
  const n = t({ x: e.left, y: e.top }), i = t({ x: e.right, y: e.bottom });
  return {
    top: n.y,
    left: n.x,
    bottom: i.y,
    right: i.x
  };
}
function Hn(e) {
  return e === void 0 || e === 1;
}
function Ci({ scale: e, scaleX: t, scaleY: n }) {
  return !Hn(e) || !Hn(t) || !Hn(n);
}
function ze(e) {
  return Ci(e) || ol(e) || e.z || e.rotate || e.rotateX || e.rotateY || e.skewX || e.skewY;
}
function ol(e) {
  return wr(e.x) || wr(e.y);
}
function wr(e) {
  return e && e !== "0%";
}
function bn(e, t, n) {
  const i = e - n, s = t * i;
  return n + s;
}
function kr(e, t, n, i, s) {
  return s !== void 0 && (e = bn(e, s, i)), bn(e, n, i) + t;
}
function Ei(e, t = 0, n = 1, i, s) {
  e.min = kr(e.min, t, n, i, s), e.max = kr(e.max, t, n, i, s);
}
function al(e, { x: t, y: n }) {
  Ei(e.x, t.translate, t.scale, t.originPoint), Ei(e.y, n.translate, n.scale, n.originPoint);
}
const Tr = 0.999999999999, Sr = 1.0000000000001;
function Ff(e, t, n, i = !1) {
  const s = n.length;
  if (!s)
    return;
  t.x = t.y = 1;
  let r, o;
  for (let a = 0; a < s; a++) {
    r = n[a], o = r.projectionDelta;
    const { visualElement: l } = r.options;
    l && l.props.style && l.props.style.display === "contents" || (i && r.options.layoutScroll && r.scroll && r !== r.root && (Ne(e.x, -r.scroll.offset.x), Ne(e.y, -r.scroll.offset.y)), o && (t.x *= o.x.scale, t.y *= o.y.scale, al(e, o)), i && ze(r.latestValues) && on(e, r.latestValues, r.layout?.layoutBox));
  }
  t.x < Sr && t.x > Tr && (t.x = 1), t.y < Sr && t.y > Tr && (t.y = 1);
}
function Ne(e, t) {
  e.min += t, e.max += t;
}
function Ar(e, t, n, i, s = 0.5) {
  const r = K(e.min, e.max, s);
  Ei(e, t, n, r, i);
}
function Nr(e, t) {
  return typeof e == "string" ? parseFloat(e) / 100 * (t.max - t.min) : e;
}
function on(e, t, n) {
  const i = n ?? e;
  Ar(e.x, Nr(t.x, i.x), t.scaleX, t.scale, t.originX), Ar(e.y, Nr(t.y, i.y), t.scaleY, t.scale, t.originY);
}
function Ps(e, t) {
  return rl(Lf(e.getBoundingClientRect(), t));
}
function If(e, t, n) {
  const i = Ps(e, n), { scroll: s } = t;
  return s && (Ne(i.x, s.offset.x), Ne(i.y, s.offset.y)), i;
}
const Of = {}, Bf = (e) => mt(e) ? Vf : wf;
class $f {
  constructor(t, n) {
    this.effect = t, this.current = n, this.KeyframeResolver = Qa;
  }
  getValue(t) {
    return this.effect.get(this.current, t);
  }
  readValue(t, n) {
    return this.effect.read(this.current, t, n);
  }
  render() {
    this.effect.flush(this.current);
  }
  measureViewportBox() {
    return Ps(this.current);
  }
  getProps() {
    return Of;
  }
}
function jf(e, t, n, i) {
  if (i)
    return el((r) => i.getValue(r, null), t, n, i);
  const s = Bf(e);
  return tl(s, e, t, n, new $f(s, e));
}
const Uf = /* @__PURE__ */ Ts((e, t, n, i) => t.set(n, i, () => {
  e[n] = i.get();
}), {
  test: (e) => es(e),
  read: (e, t) => {
    const n = e[t];
    return typeof n == "string" || typeof n == "number" ? n : void 0;
  }
}), { schedule: Ms } = /* @__PURE__ */ ga(queueMicrotask, !1), be = {
  x: !1,
  y: !1
};
function ll() {
  return be.x || be.y;
}
function Wf(e) {
  return e === "x" || e === "y" ? be[e] ? null : (be[e] = !0, () => {
    be[e] = !1;
  }) : be.x || be.y ? null : (be.x = be.y = !0, () => {
    be.x = be.y = !1;
  });
}
function cl(e, t) {
  const n = ks(e), i = new AbortController(), s = {
    passive: !0,
    ...t,
    signal: i.signal
  };
  return [n, s, () => i.abort()];
}
function _f(e) {
  return !(e.pointerType === "touch" || ll());
}
function zf(e, t, n = {}) {
  const [i, s, r] = cl(e, n);
  return i.forEach((o) => {
    let a = !1, l = !1, u;
    const d = () => {
      o.removeEventListener("pointerleave", g);
    }, h = (b) => {
      u && (u(b), u = void 0), d();
    }, f = (b) => {
      a = !1, window.removeEventListener("pointerup", f), window.removeEventListener("pointercancel", f), l && (l = !1, h(b));
    }, p = () => {
      a = !0, window.addEventListener("pointerup", f, s), window.addEventListener("pointercancel", f, s);
    }, g = (b) => {
      if (b.pointerType !== "touch") {
        if (a) {
          l = !0;
          return;
        }
        h(b);
      }
    }, x = (b) => {
      if (!_f(b))
        return;
      l = !1;
      const w = t(o, b);
      typeof w == "function" && (u = w, o.addEventListener("pointerleave", g, s));
    };
    o.addEventListener("pointerenter", x, s), o.addEventListener("pointerdown", p, s);
  }), r;
}
const ul = (e, t) => t ? e === t ? !0 : ul(e, t.parentElement) : !1, Cs = (e) => e.pointerType === "mouse" ? typeof e.button != "number" || e.button <= 0 : e.isPrimary !== !1, Gf = /* @__PURE__ */ new Set([
  "BUTTON",
  "INPUT",
  "SELECT",
  "TEXTAREA",
  "A"
]);
function Kf(e) {
  return Gf.has(e.tagName) || e.isContentEditable === !0;
}
const Hf = /* @__PURE__ */ new Set(["INPUT", "SELECT", "TEXTAREA"]);
function qf(e) {
  return Hf.has(e.tagName) || e.isContentEditable === !0;
}
const an = /* @__PURE__ */ new WeakSet();
function Pr(e) {
  return (t) => {
    t.key === "Enter" && e(t);
  };
}
function qn(e, t) {
  e.dispatchEvent(new PointerEvent("pointer" + t, { isPrimary: !0, bubbles: !0 }));
}
const Yf = (e, t) => {
  const n = e.currentTarget;
  if (!n)
    return;
  const i = Pr(() => {
    if (an.has(n))
      return;
    qn(n, "down");
    const s = Pr(() => {
      qn(n, "up");
    }), r = () => qn(n, "cancel");
    n.addEventListener("keyup", s, t), n.addEventListener("blur", r, t);
  });
  n.addEventListener("keydown", i, t), n.addEventListener("blur", () => n.removeEventListener("keydown", i), t);
};
function Mr(e) {
  return Cs(e) && !ll();
}
const Cr = /* @__PURE__ */ new WeakSet();
function Xf(e, t, n = {}) {
  const [i, s, r] = cl(e, n), o = (a) => {
    const l = a.currentTarget;
    if (!Mr(a) || Cr.has(a))
      return;
    an.add(l), n.stopPropagation && Cr.add(a);
    const u = t(l, a), d = { ...s, capture: !0 }, h = (g, x) => {
      window.removeEventListener("pointerup", f, d), window.removeEventListener("pointercancel", p, d), an.has(l) && an.delete(l), Mr(g) && typeof u == "function" && u(g, { success: x });
    }, f = (g) => {
      h(g, l === window || l === document || n.useGlobalTarget || ul(l, g.target));
    }, p = (g) => {
      h(g, !1);
    };
    window.addEventListener("pointerup", f, d), window.addEventListener("pointercancel", p, d);
  };
  return i.forEach((a) => {
    (n.useGlobalTarget ? window : a).addEventListener("pointerdown", o, s), ut(a) && (a.addEventListener("focus", (u) => Yf(u, s)), !Kf(a) && !a.hasAttribute("tabindex") && (a.tabIndex = 0));
  }), r;
}
const ln = /* @__PURE__ */ new WeakMap();
let cn;
const dl = (e, t, n) => (i, s) => s && s[0] ? s[0][e + "Size"] : mt(i) && "getBBox" in i ? i.getBBox()[t] : i[n], Zf = /* @__PURE__ */ dl("inline", "width", "offsetWidth"), Qf = /* @__PURE__ */ dl("block", "height", "offsetHeight");
function Jf({ target: e, borderBoxSize: t }) {
  ln.get(e)?.forEach((n) => {
    n(e, {
      get width() {
        return Zf(e, t);
      },
      get height() {
        return Qf(e, t);
      }
    });
  });
}
function eh(e) {
  e.forEach(Jf);
}
function th() {
  typeof ResizeObserver > "u" || (cn = new ResizeObserver(eh));
}
function nh(e, t) {
  cn || th();
  const n = ks(e);
  return n.forEach((i) => {
    let s = ln.get(i);
    s || (s = /* @__PURE__ */ new Set(), ln.set(i, s)), s.add(t), cn?.observe(i);
  }), () => {
    n.forEach((i) => {
      const s = ln.get(i);
      s?.delete(t), s?.size || cn?.unobserve(i);
    });
  };
}
const un = /* @__PURE__ */ new Set();
let ot;
function ih() {
  ot = () => {
    const e = {
      get width() {
        return window.innerWidth;
      },
      get height() {
        return window.innerHeight;
      }
    };
    un.forEach((t) => t(e));
  }, window.addEventListener("resize", ot);
}
function sh(e) {
  return un.add(e), ot || ih(), () => {
    un.delete(e), !un.size && typeof ot == "function" && (window.removeEventListener("resize", ot), ot = void 0);
  };
}
function Er(e, t) {
  return typeof e == "function" ? sh(e) : nh(e, t);
}
function rh(e) {
  return mt(e) && e.tagName === "svg";
}
function oh(...e) {
  const t = !Array.isArray(e[0]), n = t ? 0 : -1, i = e[0 + n], s = e[1 + n], r = e[2 + n], o = e[3 + n], a = Ea(s, r, o);
  return t ? a(i) : a;
}
const Dr = () => ({
  translate: 0,
  scale: 1,
  origin: 0,
  originPoint: 0
}), at = () => ({
  x: Dr(),
  y: Dr()
}), Vr = () => ({ min: 0, max: 0 }), ee = () => ({
  x: Vr(),
  y: Vr()
}), fl = /* @__PURE__ */ new WeakMap();
function Dn(e) {
  return e !== null && typeof e == "object" && typeof e.start == "function";
}
function Ft(e) {
  return typeof e == "string" || Array.isArray(e);
}
const Es = [
  "animate",
  "whileInView",
  "whileFocus",
  "whileHover",
  "whileTap",
  "whileDrag",
  "exit"
], wn = ["initial", ...Es];
function Vn(e) {
  if (Dn(e.animate))
    return !0;
  for (let t = 0; t < wn.length; t++)
    if (Ft(e[wn[t]]))
      return !0;
  return !1;
}
function hl(e) {
  return !!(Vn(e) || e.variants);
}
function ah(e, t, n) {
  for (const i in t) {
    const s = t[i], r = n[i];
    if (ie(s))
      e.addValue(i, s);
    else if (ie(r))
      e.addValue(i, Re(s, { owner: e }));
    else if (r !== s)
      if (e.hasValue(i)) {
        const o = e.getValue(i);
        o.liveStyle === !0 ? o.jump(s) : o.hasAnimated || o.set(s);
      } else {
        const o = e.getStaticValue(i);
        e.addValue(i, Re(o !== void 0 ? o : s, { owner: e }));
      }
  }
  for (const i in n)
    t[i] === void 0 && e.removeValue(i);
  return t;
}
const kn = { current: null }, Ds = { current: !1 }, lh = typeof window < "u";
function pl() {
  if (Ds.current = !0, !!lh)
    if (window.matchMedia) {
      const e = window.matchMedia("(prefers-reduced-motion)"), t = () => kn.current = e.matches;
      e.addEventListener("change", t), t();
    } else
      kn.current = !1;
}
const Rr = [
  "AnimationStart",
  "AnimationComplete",
  "Update",
  "BeforeLayoutMeasure",
  "LayoutMeasure",
  "LayoutAnimationStart",
  "LayoutAnimationComplete"
];
let Tn = {};
function ml(e) {
  Tn = e;
}
function ch() {
  return Tn;
}
class uh {
  /**
   * This method takes React props and returns found MotionValues. For example, HTML
   * MotionValues will be found within the style prop, whereas for Three.js within attribute arrays.
   *
   * This isn't an abstract method as it needs calling in the constructor, but it is
   * intended to be one.
   */
  scrapeMotionValuesFromProps(t, n, i) {
    return {};
  }
  constructor({ parent: t, props: n, presenceContext: i, reducedMotionConfig: s, skipAnimations: r, blockInitialAnimation: o, visualState: a }, l = {}) {
    this.current = null, this.children = /* @__PURE__ */ new Set(), this.isVariantNode = !1, this.isControllingVariants = !1, this.shouldReduceMotion = null, this.shouldSkipAnimations = !1, this.values = /* @__PURE__ */ new Map(), this.KeyframeResolver = ps, this.features = {}, this.valueSubscriptions = /* @__PURE__ */ new Map(), this.prevMotionValues = {}, this.hasBeenMounted = !1, this.events = {}, this.propEventSubscriptions = {}, this.notifyUpdate = () => this.notify("Update", this.latestValues), this.render = () => {
      this.current && (this.triggerBuild(), this.renderInstance(this.current, this.renderState, this.props.style, this.projection));
    }, this.renderScheduledAt = 0, this.scheduleRender = () => {
      const p = ae.now();
      this.renderScheduledAt < p && (this.renderScheduledAt = p, z.render(this.render, !1, !0));
    };
    const { latestValues: u, renderState: d } = a;
    this.latestValues = u, this.baseTarget = { ...u }, this.initialValues = n.initial ? { ...u } : {}, this.renderState = d, this.parent = t, this.props = n, this.presenceContext = i, this.depth = t ? t.depth + 1 : 0, this.reducedMotionConfig = s, this.skipAnimationsConfig = r, this.options = l, this.blockInitialAnimation = !!o, this.isControllingVariants = Vn(n), this.isVariantNode = hl(n), this.isVariantNode && (this.variantChildren = /* @__PURE__ */ new Set()), this.manuallyAnimateOnMount = !!(t && t.current);
    const { willChange: h, ...f } = this.scrapeMotionValuesFromProps(n, {}, this);
    for (const p in f) {
      const g = f[p];
      u[p] !== void 0 && ie(g) && g.set(u[p]);
    }
  }
  mount(t) {
    if (this.hasBeenMounted)
      for (const n in this.initialValues)
        this.values.get(n)?.jump(this.initialValues[n]), this.latestValues[n] = this.initialValues[n];
    this.current = t, fl.set(t, this), this.projection && !this.projection.instance && this.projection.mount(t), this.parent && this.isVariantNode && !this.isControllingVariants && (this.removeFromVariantTree = this.parent.addVariantChild(this)), this.values.forEach((n, i) => this.bindToMotionValue(i, n)), this.reducedMotionConfig === "never" ? this.shouldReduceMotion = !1 : this.reducedMotionConfig === "always" ? this.shouldReduceMotion = !0 : (Ds.current || pl(), this.shouldReduceMotion = kn.current), process.env.NODE_ENV !== "production" && Mn(this.shouldReduceMotion !== !0, "You have Reduced Motion enabled on your device. Animations may not appear as expected.", "reduced-motion-disabled"), this.shouldSkipAnimations = this.skipAnimationsConfig ?? !1, this.parent?.addChild(this), this.update(this.props, this.presenceContext), this.hasBeenMounted = !0;
  }
  unmount() {
    this.projection && this.projection.unmount(), Ve(this.notifyUpdate), Ve(this.render), this.valueSubscriptions.forEach((t) => t()), this.valueSubscriptions.clear(), this.removeFromVariantTree && this.removeFromVariantTree(), this.parent?.removeChild(this);
    for (const t in this.events)
      this.events[t].clear();
    for (const t in this.features) {
      const n = this.features[t];
      n && (n.unmount(), n.isMounted = !1);
    }
    this.current = null;
  }
  addChild(t) {
    this.children.add(t), this.enteringChildren ?? (this.enteringChildren = /* @__PURE__ */ new Set()), this.enteringChildren.add(t);
  }
  removeChild(t) {
    this.children.delete(t), this.enteringChildren && this.enteringChildren.delete(t);
  }
  bindToMotionValue(t, n) {
    if (this.valueSubscriptions.has(t) && this.valueSubscriptions.get(t)(), n.accelerate && Ai.has(t) && this.current instanceof HTMLElement) {
      const { factory: o, keyframes: a, times: l, ease: u, duration: d } = n.accelerate, h = new za({
        element: this.current,
        name: t,
        keyframes: a,
        times: l,
        ease: u,
        duration: /* @__PURE__ */ he(d)
      }), f = o(h);
      this.valueSubscriptions.set(t, () => {
        f(), h.cancel();
      });
      return;
    }
    const i = Fe.has(t);
    i && this.onBindTransform && this.onBindTransform();
    const s = n.on("change", (o) => {
      this.latestValues[t] = o, this.props.onUpdate && z.preRender(this.notifyUpdate), i && this.projection && (this.projection.isTransformDirty = !0), this.scheduleRender();
    });
    let r;
    typeof window < "u" && window.MotionCheckAppearSync && (r = window.MotionCheckAppearSync(this, t, n)), this.valueSubscriptions.set(t, () => {
      s(), r && r();
    });
  }
  sortNodePosition(t) {
    return !this.current || !this.sortInstanceNodePosition || this.type !== t.type ? 0 : this.sortInstanceNodePosition(this.current, t.current);
  }
  updateFeatures() {
    let t = "animation";
    for (t in Tn) {
      const n = Tn[t];
      if (!n)
        continue;
      const { isEnabled: i, Feature: s } = n;
      if (!this.features[t] && s && i(this.props) && (this.features[t] = new s(this)), this.features[t]) {
        const r = this.features[t];
        r.isMounted ? r.update() : (r.mount(), r.isMounted = !0);
      }
    }
  }
  triggerBuild() {
    this.build(this.renderState, this.latestValues, this.props);
  }
  /**
   * Measure the current viewport box with or without transforms.
   * Only measures axis-aligned boxes, rotate and skew must be manually
   * removed with a re-render to work.
   */
  measureViewportBox() {
    return this.current ? this.measureInstanceViewportBox(this.current, this.props) : ee();
  }
  getStaticValue(t) {
    return this.latestValues[t];
  }
  setStaticValue(t, n) {
    this.latestValues[t] = n;
  }
  /**
   * Update the provided props. Ensure any newly-added motion values are
   * added to our map, old ones removed, and listeners updated.
   */
  update(t, n) {
    (t.transformTemplate || this.props.transformTemplate) && this.scheduleRender(), this.prevProps = this.props, this.props = t, this.prevPresenceContext = this.presenceContext, this.presenceContext = n;
    for (let i = 0; i < Rr.length; i++) {
      const s = Rr[i];
      this.propEventSubscriptions[s] && (this.propEventSubscriptions[s](), delete this.propEventSubscriptions[s]);
      const r = "on" + s, o = t[r];
      o && (this.propEventSubscriptions[s] = this.on(s, o));
    }
    this.prevMotionValues = ah(this, this.scrapeMotionValuesFromProps(t, this.prevProps || {}, this), this.prevMotionValues), this.handleChildMotionValue && this.handleChildMotionValue();
  }
  getProps() {
    return this.props;
  }
  /**
   * Returns the variant definition with a given name.
   */
  getVariant(t) {
    return this.props.variants ? this.props.variants[t] : void 0;
  }
  /**
   * Returns the defined default transition on this component.
   */
  getDefaultTransition() {
    return this.props.transition;
  }
  getTransformPagePoint() {
    return this.props.transformPagePoint;
  }
  getClosestVariantNode() {
    return this.isVariantNode ? this : this.parent ? this.parent.getClosestVariantNode() : void 0;
  }
  /**
   * Add a child visual element to our set of children.
   */
  addVariantChild(t) {
    const n = this.getClosestVariantNode();
    if (n)
      return n.variantChildren && n.variantChildren.add(t), () => n.variantChildren.delete(t);
  }
  /**
   * Add a motion value and bind it to this visual element.
   */
  addValue(t, n) {
    const i = this.values.get(t);
    n !== i && (i && this.removeValue(t), this.bindToMotionValue(t, n), this.values.set(t, n), this.latestValues[t] = n.get());
  }
  /**
   * Remove a motion value and unbind any active subscriptions.
   */
  removeValue(t) {
    this.values.delete(t);
    const n = this.valueSubscriptions.get(t);
    n && (n(), this.valueSubscriptions.delete(t)), delete this.latestValues[t], this.removeValueFromRenderState(t, this.renderState);
  }
  /**
   * Check whether we have a motion value for this key
   */
  hasValue(t) {
    return this.values.has(t);
  }
  getValue(t, n) {
    if (this.props.values && this.props.values[t])
      return this.props.values[t];
    let i = this.values.get(t);
    return i === void 0 && n !== void 0 && (i = Re(n === null ? void 0 : n, { owner: this }), this.addValue(t, i)), i;
  }
  /**
   * If we're trying to animate to a previously unencountered value,
   * we need to check for it in our state and as a last resort read it
   * directly from the instance (which might have performance implications).
   */
  readValue(t, n) {
    let i = this.latestValues[t] !== void 0 || !this.current ? this.latestValues[t] : this.getBaseTargetFromProps(this.props, t) ?? this.readValueFromInstance(this.current, t, this.options);
    return i != null && (typeof i == "string" && (Ji(i) || ts(i)) ? i = parseFloat(i) : (
      /**
       * If the value as read isn't animatable (e.g. "none") but
       * the target is, derive an animatable none from the target.
       * A value is animatable if it's a number or contains a
       * number or color, which is cheaper to check than trying
       * every value type in turn.
       */
      typeof i != "number" && !ge.test(i) && ge.test(n) && (i = hs(t, n))
    ), this.setBaseTarget(t, ie(i) ? i.get() : i)), ie(i) ? i.get() : i;
  }
  /**
   * Set the base target to later animate back to. This is currently
   * only hydrated on creation and when we first read a value.
   */
  setBaseTarget(t, n) {
    this.baseTarget[t] = n;
  }
  /**
   * Find the base target for a value thats been removed from all animation
   * props.
   */
  getBaseTarget(t) {
    const { initial: n } = this.props;
    let i;
    if (typeof n == "string" || typeof n == "object") {
      const r = xs(this.props, n, this.presenceContext?.custom);
      r && (i = r[t]);
    }
    if (n && i !== void 0)
      return i;
    const s = this.getBaseTargetFromProps(this.props, t);
    return s !== void 0 && !ie(s) ? s : this.initialValues[t] !== void 0 && i === void 0 ? void 0 : this.baseTarget[t];
  }
  on(t, n) {
    return this.events[t] || (this.events[t] = new gn()), this.events[t].add(n);
  }
  notify(t, ...n) {
    this.events[t] && this.events[t].notify(...n);
  }
  scheduleRenderMicrotask() {
    Ms.render(this.render);
  }
}
class gl extends uh {
  constructor() {
    super(...arguments), this.KeyframeResolver = Qa;
  }
  sortInstanceNodePosition(t, n) {
    return t.compareDocumentPosition(n) & 2 ? 1 : -1;
  }
  getBaseTargetFromProps(t, n) {
    const i = t.style;
    return i ? i[n] : void 0;
  }
  removeValueFromRenderState(t, { vars: n, style: i }) {
    delete n[t], delete i[t];
  }
  handleChildMotionValue() {
    this.childSubscription && (this.childSubscription(), delete this.childSubscription);
    const { children: t } = this.props;
    ie(t) && (this.childSubscription = t.on("change", (n) => {
      this.current && (this.current.textContent = `${n}`);
    }));
  }
}
class Ue {
  constructor(t) {
    this.isMounted = !1, this.node = t;
  }
  update() {
  }
}
function yl(e, { style: t, vars: n }, i, s) {
  const r = e.style;
  let o;
  for (o in t)
    r[o] = t[o];
  s?.applyProjectionStyles(r, i);
  for (o in n)
    r.setProperty(o, n[o]);
}
function Lr(e, t) {
  return t.max === t.min ? 0 : e / (t.max - t.min) * 100;
}
const xt = {
  correct: (e, t) => {
    if (!t.target)
      return e;
    if (typeof e == "string")
      if (V.test(e))
        e = parseFloat(e);
      else
        return e;
    const n = Lr(e, t.target.x), i = Lr(e, t.target.y);
    return `${n}% ${i}%`;
  }
}, dh = {
  correct: (e, { treeScale: t, projectionDelta: n }) => {
    const i = e, s = ge.parse(e);
    if (s.length > 5)
      return i;
    const r = ge.createTransformer(e), o = typeof s[0] != "number" ? 1 : 0, a = n.x.scale * t.x, l = n.y.scale * t.y;
    s[0 + o] /= a, s[1 + o] /= l;
    const u = K(a, l, 0.5);
    return typeof s[2 + o] == "number" && (s[2 + o] /= u), typeof s[3 + o] == "number" && (s[3 + o] /= u), r(s);
  }
}, Di = {
  borderRadius: {
    ...xt,
    applyTo: [...bs]
  },
  borderTopLeftRadius: xt,
  borderTopRightRadius: xt,
  borderBottomLeftRadius: xt,
  borderBottomRightRadius: xt,
  boxShadow: dh
};
function xl(e, { layout: t, layoutId: n }) {
  return Fe.has(e) || e.startsWith("origin") || (t || n !== void 0) && (!!Di[e] || e === "opacity");
}
function Vs(e, t, n) {
  const i = e.style, s = t?.style, r = {};
  if (!i)
    return r;
  for (const o in i)
    (ie(i[o]) || s && ie(s[o]) || xl(o, e) || n?.getValue(o)?.liveStyle !== void 0) && (r[o] = i[o]);
  return r;
}
function fh(e) {
  return window.getComputedStyle(e);
}
class hh extends gl {
  constructor() {
    super(...arguments), this.type = "html", this.renderInstance = yl;
  }
  mount(t) {
    ye(!!t.style, "motion.create() components must forward their ref to a HTML or SVG element", "custom-component-ref"), super.mount(t);
  }
  readValueFromInstance(t, n) {
    if (Fe.has(n))
      return this.projection?.isProjecting ? vi(n) : Oa(t, n);
    {
      const i = fh(t), s = (xa(n) ? i.getPropertyValue(n) : i[n]) || 0;
      return typeof s == "string" ? s.trim() : s;
    }
  }
  measureInstanceViewportBox(t, { transformPagePoint: n }) {
    return Ps(t, n);
  }
  build(t, n, i) {
    As(t, n, i.transformTemplate);
  }
  scrapeMotionValuesFromProps(t, n, i) {
    return Vs(t, n, i);
  }
}
const vl = /* @__PURE__ */ new Set([
  "baseFrequency",
  "diffuseConstant",
  "kernelMatrix",
  "kernelUnitLength",
  "keySplines",
  "keyTimes",
  "limitingConeAngle",
  "markerHeight",
  "markerWidth",
  "numOctaves",
  "targetX",
  "targetY",
  "surfaceScale",
  "specularConstant",
  "specularExponent",
  "stdDeviation",
  "tableValues",
  "viewBox",
  "gradientTransform",
  "pathLength",
  "startOffset",
  "textLength",
  "lengthAdjust"
]), bl = (e) => typeof e == "string" && e.toLowerCase() === "svg";
function ph(e, t, n, i) {
  yl(e, t, void 0, i);
  for (const s in t.attrs)
    e.setAttribute(vl.has(s) ? s : Gt(s), t.attrs[s]);
}
function wl(e, t, n) {
  const i = Vs(e, t, n);
  for (const s in e)
    if (ie(e[s]) || ie(t[s])) {
      const r = je.indexOf(s) !== -1 ? "attr" + s.charAt(0).toUpperCase() + s.substring(1) : s;
      i[r] = e[s];
    }
  return i;
}
class mh extends gl {
  constructor() {
    super(...arguments), this.type = "svg", this.isSVGTag = !1, this.measureInstanceViewportBox = ee;
  }
  getBaseTargetFromProps(t, n) {
    return t[n];
  }
  readValueFromInstance(t, n) {
    if (Fe.has(n)) {
      const i = Ia(n);
      return i && i.default || 0;
    }
    if (Ns.includes(n)) {
      const s = getComputedStyle(t)[n];
      if (typeof s == "string" && s)
        return s.trim();
    }
    return n = vl.has(n) ? n : Gt(n), t.getAttribute(n);
  }
  scrapeMotionValuesFromProps(t, n, i) {
    return wl(t, n, i);
  }
  build(t, n, i) {
    il(t, n, this.isSVGTag, i.transformTemplate, i.style);
  }
  renderInstance(t, n, i, s) {
    ph(t, n, i, s);
  }
  mount(t) {
    this.isSVGTag = bl(t.tagName), super.mount(t);
  }
}
const gh = wn.length;
function kl(e) {
  if (!e)
    return;
  if (!e.isControllingVariants) {
    const n = e.parent ? kl(e.parent) || {} : {};
    return e.props.initial !== void 0 && (n.initial = e.props.initial), n;
  }
  const t = {};
  for (let n = 0; n < gh; n++) {
    const i = wn[n], s = e.props[i];
    (Ft(s) || s === !1) && (t[i] = s);
  }
  return t;
}
function Tl(e, t) {
  if (!Array.isArray(t))
    return !1;
  const n = t.length;
  if (n !== e.length)
    return !1;
  for (let i = 0; i < n; i++)
    if (t[i] !== e[i])
      return !1;
  return !0;
}
const yh = [...Es].reverse(), xh = Es.length;
function vh(e) {
  return (t) => Promise.all(t.map(({ animation: n, options: i }) => of(e, n, i)));
}
function bh(e) {
  let t = vh(e), n = Fr(), i = !0, s = !1;
  const r = (u) => (d, h) => {
    const f = Xe(e, h, u === "exit" ? e.presenceContext?.custom : void 0);
    if (f) {
      const { transition: p, transitionEnd: g, ...x } = f;
      d = { ...d, ...x, ...g };
    }
    return d;
  };
  function o(u) {
    t = u(e);
  }
  function a(u) {
    const { props: d } = e, h = kl(e.parent) || {}, f = [], p = /* @__PURE__ */ new Set();
    let g = {}, x = 1 / 0;
    for (let w = 0; w < xh; w++) {
      const T = yh[w], y = n[T], k = d[T] !== void 0 ? d[T] : h[T], E = Ft(k), P = T === u ? y.isActive : null;
      P === !1 && (x = w);
      let S = k === h[T] && k !== d[T] && E;
      if (S && (i || s) && e.manuallyAnimateOnMount && (S = !1), y.protectedKeys = { ...g }, // If it isn't active and hasn't *just* been set as inactive
      !y.isActive && P === null || // If we didn't and don't have any defined prop for this animation type
      !k && !y.prevProp || // Or if the prop doesn't define an animation
      Dn(k) || typeof k == "boolean")
        continue;
      if (T === "exit" && y.isActive && P !== !0) {
        y.prevResolvedValues && (g = {
          ...g,
          ...y.prevResolvedValues
        });
        continue;
      }
      const m = wh(y.prevProp, k);
      let N = m || // If we're making this variant active, we want to always make it active
      T === u && y.isActive && !S && E || // If we removed a higher-priority variant (i is in reverse order)
      w > x && E, A = !1;
      const L = Array.isArray(k) ? k : [k];
      let I = L.reduce(r(T), {});
      P === !1 && (I = {});
      const { prevResolvedValues: j = {} } = y, C = {
        ...j,
        ...I
      }, re = (W) => {
        N = !0, p.has(W) && (A = !0, p.delete(W)), y.needsAnimating[W] = !0;
        const J = e.getValue(W);
        J && (J.liveStyle = !1);
      };
      for (const W in C) {
        const J = I[W], H = j[W];
        if (g.hasOwnProperty(W))
          continue;
        let D = !1;
        Ni(J) && Ni(H) ? D = !Tl(J, H) || m : D = J !== H, D ? J != null ? re(W) : p.add(W) : J !== void 0 && p.has(W) ? re(W) : y.protectedKeys[W] = !0;
      }
      y.prevProp = k, y.prevResolvedValues = I, y.isActive && (g = { ...g, ...I }), (i || s) && e.blockInitialAnimation && (N = !1);
      const ce = S && m;
      N && (!ce || A) && f.push(...L.map((W) => {
        const J = { type: T };
        if (typeof W == "string" && (i || s) && !ce && e.manuallyAnimateOnMount && e.parent) {
          const { parent: H } = e, D = Xe(H, W);
          if (H.enteringChildren && D) {
            const { delayChildren: _ } = D.transition || {};
            J.delay = Ka(H.enteringChildren, e, _);
          }
        }
        return {
          animation: W,
          options: J
        };
      }));
    }
    if (p.size) {
      const w = {};
      if (typeof d.initial != "boolean") {
        const T = Xe(e, Array.isArray(d.initial) ? d.initial[0] : d.initial);
        T && T.transition && (w.transition = T.transition);
      }
      p.forEach((T) => {
        const y = e.getBaseTarget(T), k = e.getValue(T);
        k && (k.liveStyle = !0), w[T] = y ?? null;
      }), f.push({ animation: w });
    }
    let b = !!f.length;
    return i && (d.initial === !1 || d.initial === d.animate) && !e.manuallyAnimateOnMount && (b = !1), i = !1, s = !1, b ? t(f) : Promise.resolve();
  }
  function l(u, d) {
    if (n[u].isActive === d)
      return Promise.resolve();
    e.variantChildren?.forEach((f) => f.animationState?.setActive(u, d)), n[u].isActive = d;
    const h = a(u);
    for (const f in n)
      n[f].protectedKeys = {};
    return h;
  }
  return {
    animateChanges: a,
    setActive: l,
    setAnimateFunction: o,
    getState: () => n,
    reset: () => {
      n = Fr(), s = !0;
    }
  };
}
function wh(e, t) {
  return typeof t == "string" ? t !== e : Array.isArray(t) ? !Tl(t, e) : !1;
}
function _e(e = !1) {
  return {
    isActive: e,
    protectedKeys: {},
    needsAnimating: {},
    prevResolvedValues: {}
  };
}
function Fr() {
  return {
    animate: _e(!0),
    whileInView: _e(),
    whileHover: _e(),
    whileTap: _e(),
    whileDrag: _e(),
    whileFocus: _e(),
    exit: _e()
  };
}
function Vi(e, t) {
  e.min = t.min, e.max = t.max;
}
function ve(e, t) {
  Vi(e.x, t.x), Vi(e.y, t.y);
}
function Ir(e, t) {
  e.translate = t.translate, e.scale = t.scale, e.originPoint = t.originPoint, e.origin = t.origin;
}
const Sl = 1e-4, kh = 1 - Sl, Th = 1 + Sl, Al = 0.01, Sh = 0 - Al, Ah = 0 + Al;
function ue(e) {
  return e.max - e.min;
}
function Nh(e, t, n) {
  return Math.abs(e - t) <= n;
}
function Or(e, t, n, i = 0.5) {
  e.origin = i, e.originPoint = K(t.min, t.max, e.origin), e.scale = ue(n) / ue(t), e.translate = K(n.min, n.max, e.origin) - e.originPoint, (e.scale >= kh && e.scale <= Th || isNaN(e.scale)) && (e.scale = 1), (e.translate >= Sh && e.translate <= Ah || isNaN(e.translate)) && (e.translate = 0);
}
function Pt(e, t, n, i) {
  Or(e.x, t.x, n.x, i ? i.originX : void 0), Or(e.y, t.y, n.y, i ? i.originY : void 0);
}
function Br(e, t, n, i = 0) {
  const s = i ? K(n.min, n.max, i) : n.min;
  e.min = s + t.min, e.max = e.min + ue(t);
}
function Ph(e, t, n, i) {
  Br(e.x, t.x, n.x, i?.x), Br(e.y, t.y, n.y, i?.y);
}
function $r(e, t, n, i = 0) {
  const s = i ? K(n.min, n.max, i) : n.min;
  e.min = t.min - s, e.max = e.min + ue(t);
}
function Sn(e, t, n, i) {
  $r(e.x, t.x, n.x, i?.x), $r(e.y, t.y, n.y, i?.y);
}
function jr(e, t, n, i, s) {
  return e -= t, e = bn(e, 1 / n, i), s !== void 0 && (e = bn(e, 1 / s, i)), e;
}
function Mh(e, t = 0, n = 1, i = 0.5, s, r = e, o = e) {
  if (Pe.test(t) && (t = parseFloat(t), t = K(o.min, o.max, t / 100) - o.min), typeof t != "number")
    return;
  let a = K(r.min, r.max, i);
  e === r && (a -= t), e.min = jr(e.min, t, n, a, s), e.max = jr(e.max, t, n, a, s);
}
function Ur(e, t, [n, i, s], r, o) {
  Mh(e, t[n], t[i], t[s], t.scale, r, o);
}
const Ch = ["x", "scaleX", "originX"], Eh = ["y", "scaleY", "originY"];
function Wr(e, t, n, i) {
  Ur(e.x, t, Ch, n ? n.x : void 0, i ? i.x : void 0), Ur(e.y, t, Eh, n ? n.y : void 0, i ? i.y : void 0);
}
function _r(e) {
  return e.translate === 0 && e.scale === 1;
}
function Nl(e) {
  return _r(e.x) && _r(e.y);
}
function zr(e, t) {
  return e.min === t.min && e.max === t.max;
}
function Dh(e, t) {
  return zr(e.x, t.x) && zr(e.y, t.y);
}
function Gr(e, t) {
  return Math.round(e.min) === Math.round(t.min) && Math.round(e.max) === Math.round(t.max);
}
function Pl(e, t) {
  return Gr(e.x, t.x) && Gr(e.y, t.y);
}
function Kr(e) {
  return ue(e.x) / ue(e.y);
}
function Hr(e, t) {
  return e.translate === t.translate && e.scale === t.scale && e.originPoint === t.originPoint;
}
function Ae(e) {
  return [e("x"), e("y")];
}
function Vh(e, t, n) {
  let i = "";
  const s = e.x.translate / t.x, r = e.y.translate / t.y, o = n?.z || 0;
  if ((s || r || o) && (i = `translate3d(${s}px, ${r}px, ${o}px) `), (t.x !== 1 || t.y !== 1) && (i += `scale(${1 / t.x}, ${1 / t.y}) `), n) {
    const { transformPerspective: u, rotate: d, pathRotation: h, rotateX: f, rotateY: p, skewX: g, skewY: x } = n;
    u && (i = `perspective(${u}px) ${i}`), d && (i += `rotate(${d}deg) `), h && (i += `rotate(${h}deg) `), f && (i += `rotateX(${f}deg) `), p && (i += `rotateY(${p}deg) `), g && (i += `skewX(${g}deg) `), x && (i += `skewY(${x}deg) `);
  }
  const a = e.x.scale * t.x, l = e.y.scale * t.y;
  return (a !== 1 || l !== 1) && (i += `scale(${a}, ${l})`), i || "none";
}
const Rh = bs.length, qr = (e) => typeof e == "string" ? parseFloat(e) : e, Yr = (e) => typeof e == "number" || V.test(e);
function Lh(e, t, n, i, s, r) {
  s ? (e.opacity = K(0, n.opacity ?? 1, Fh(i)), e.opacityExit = K(t.opacity ?? 1, 0, Ih(i))) : r && (e.opacity = K(t.opacity ?? 1, n.opacity ?? 1, i));
  for (let o = 0; o < Rh; o++) {
    const a = bs[o];
    let l = Xr(t, a), u = Xr(n, a);
    if (l === void 0 && u === void 0)
      continue;
    l || (l = 0), u || (u = 0), l === 0 || u === 0 || Yr(l) === Yr(u) ? (e[a] = Math.max(K(qr(l), qr(u), i), 0), (Pe.test(u) || Pe.test(l)) && (e[a] += "%")) : e[a] = u;
  }
  (t.rotate || n.rotate) && (e.rotate = K(t.rotate || 0, n.rotate || 0, i));
}
function Xr(e, t) {
  return e[t] !== void 0 ? e[t] : e.borderRadius;
}
const Fh = /* @__PURE__ */ Ml(0, 0.5, ua), Ih = /* @__PURE__ */ Ml(0.5, 0.95, we);
function Ml(e, t, n) {
  return (i) => i < e ? 0 : i > t ? 1 : n(/* @__PURE__ */ dt(e, t, i));
}
function Cl(e, t, n) {
  const i = ie(e) ? e : Re(e);
  return i.start(En("", i, t, n)), i.animation;
}
function It(e, t, n, i = { passive: !0 }) {
  return e.addEventListener(t, n, i), () => e.removeEventListener(t, n, i);
}
const Oh = (e, t) => e.depth - t.depth;
class Bh {
  constructor() {
    this.children = [], this.isDirty = !1;
  }
  add(t) {
    Qi(this.children, t), this.isDirty = !0;
  }
  remove(t) {
    Ze(this.children, t), this.isDirty = !0;
  }
  forEach(t) {
    this.isDirty && this.children.sort(Oh), this.isDirty = !1, this.children.forEach(t);
  }
}
function $h(e, t) {
  const n = ae.now(), i = ({ timestamp: s }) => {
    const r = s - n;
    r >= t && (Ve(i), e(r - t));
  };
  return z.setup(i, !0), () => Ve(i);
}
function dn(e) {
  return ie(e) ? e.get() : e;
}
class jh {
  constructor() {
    this.members = [];
  }
  add(t) {
    Qi(this.members, t);
    for (let n = this.members.length - 1; n >= 0; n--) {
      const i = this.members[n];
      if (i === t || i === this.lead || i === this.prevLead)
        continue;
      const s = i.instance;
      (!s || s.isConnected === !1) && !i.snapshot && (Ze(this.members, i), i.unmount());
    }
    t.scheduleRender();
  }
  remove(t) {
    if (Ze(this.members, t), t === this.prevLead && (this.prevLead = void 0), t === this.lead) {
      const n = this.members[this.members.length - 1];
      n && this.promote(n);
    }
  }
  relegate(t) {
    for (let n = this.members.indexOf(t) - 1; n >= 0; n--) {
      const i = this.members[n];
      if (i.isPresent !== !1 && i.instance?.isConnected !== !1)
        return this.promote(i), !0;
    }
    return !1;
  }
  promote(t, n) {
    const i = this.lead;
    if (t !== i && (this.prevLead = i, this.lead = t, t.show(), i)) {
      i.updateSnapshot(), t.scheduleRender();
      const { layoutDependency: s } = i.options, { layoutDependency: r } = t.options;
      (s === void 0 || s !== r) && (t.resumeFrom = i, n && (i.preserveOpacity = !0), i.snapshot && (t.snapshot = i.snapshot, t.snapshot.latestValues = i.animationValues || i.latestValues), t.root?.isUpdating && (t.isLayoutDirty = !0)), t.options.crossfade === !1 && i.hide();
    }
  }
  exitAnimationComplete() {
    this.members.forEach((t) => {
      t.options.onExitComplete?.(), t.resumingFrom?.options.onExitComplete?.();
    });
  }
  scheduleRender() {
    this.members.forEach((t) => t.instance && t.scheduleRender(!1));
  }
  removeLeadSnapshot() {
    this.lead?.snapshot && (this.lead.snapshot = void 0);
  }
}
const fn = {
  /**
   * Global flag as to whether the tree has animated since the last time
   * we resized the window
   */
  hasAnimatedSinceResize: !0,
  /**
   * We set this to true once, on the first update. Any nodes added to the tree beyond that
   * update will be given a `data-projection-id` attribute.
   */
  hasEverUpdated: !1
}, Yn = ["", "X", "Y", "Z"], Uh = 1e3;
let Wh = 0;
function Xn(e, t, n, i) {
  const { latestValues: s } = t;
  s[e] && (n[e] = s[e], t.setStaticValue(e, 0), i && (i[e] = 0));
}
function El(e) {
  if (e.hasCheckedOptimisedAppear = !0, e.root === e)
    return;
  const { visualElement: t } = e.options;
  if (!t)
    return;
  const n = Xa(t);
  if (window.MotionHasOptimisedAnimation(n, "transform")) {
    const { layout: s, layoutId: r } = e.options;
    window.MotionCancelOptimisedAnimation(n, "transform", z, !(s || r));
  }
  const { parent: i } = e;
  i && !i.hasCheckedOptimisedAppear && El(i);
}
function Dl({ attachResizeListener: e, defaultParent: t, measureScroll: n, checkIsScrollRoot: i, resetTransform: s }) {
  return class {
    constructor(o = {}, a = t?.()) {
      this.id = Wh++, this.animationId = 0, this.animationCommitId = 0, this.children = /* @__PURE__ */ new Set(), this.options = {}, this.isTreeAnimating = !1, this.isAnimationBlocked = !1, this.isLayoutDirty = !1, this.isProjectionDirty = !1, this.isSharedProjectionDirty = !1, this.isTransformDirty = !1, this.updateManuallyBlocked = !1, this.updateBlockedByResize = !1, this.isUpdating = !1, this.isSVG = !1, this.needsReset = !1, this.shouldResetTransform = !1, this.hasCheckedOptimisedAppear = !1, this.treeScale = { x: 1, y: 1 }, this.eventHandlers = /* @__PURE__ */ new Map(), this.hasTreeAnimated = !1, this.layoutVersion = 0, this.updateScheduled = !1, this.scheduleUpdate = () => this.update(), this.projectionUpdateScheduled = !1, this.checkUpdateFailed = () => {
        this.isUpdating && (this.isUpdating = !1, this.clearAllSnapshots());
      }, this.updateProjection = () => {
        this.projectionUpdateScheduled = !1, this.nodes.forEach(Gh), this.nodes.forEach(Zh), this.nodes.forEach(Qh), this.nodes.forEach(Kh);
      }, this.resolvedRelativeTargetAt = 0, this.linkedParentVersion = 0, this.hasProjected = !1, this.isVisible = !0, this.animationProgress = 0, this.sharedNodes = /* @__PURE__ */ new Map(), this.latestValues = o, this.root = a ? a.root || a : this, this.path = a ? [...a.path, a] : [], this.parent = a, this.depth = a ? a.depth + 1 : 0;
      for (let l = 0; l < this.path.length; l++)
        this.path[l].shouldResetTransform = !0;
      this.root === this && (this.nodes = new Bh());
    }
    addEventListener(o, a) {
      return this.eventHandlers.has(o) || this.eventHandlers.set(o, new gn()), this.eventHandlers.get(o).add(a);
    }
    notifyListeners(o, ...a) {
      const l = this.eventHandlers.get(o);
      l && l.notify(...a);
    }
    hasListeners(o) {
      return this.eventHandlers.has(o);
    }
    /**
     * Lifecycles
     */
    mount(o) {
      if (this.instance)
        return;
      this.isSVG = mt(o) && !rh(o), this.instance = o;
      const { layoutId: a, layout: l, visualElement: u } = this.options;
      if (u && !u.current && u.mount(o), this.root.nodes.add(this), this.parent && this.parent.children.add(this), this.root.hasTreeAnimated && (l || a) && (this.isLayoutDirty = !0), e) {
        let d, h = 0;
        const f = () => this.root.updateBlockedByResize = !1;
        z.read(() => {
          h = window.innerWidth;
        }), e(o, () => {
          const p = window.innerWidth;
          p !== h && (h = p, this.root.updateBlockedByResize = !0, d && d(), d = $h(f, 250), fn.hasAnimatedSinceResize && (fn.hasAnimatedSinceResize = !1, this.nodes.forEach(Jr)));
        });
      }
      a && this.root.registerSharedNode(a, this), this.options.animate !== !1 && u && (a || l) && this.addEventListener("didUpdate", ({ delta: d, hasLayoutChanged: h, hasRelativeLayoutChanged: f, layout: p }) => {
        if (this.isTreeAnimationBlocked()) {
          this.target = void 0, this.relativeTarget = void 0;
          return;
        }
        const g = this.options.transition || u.getDefaultTransition() || ip, { onLayoutAnimationStart: x, onLayoutAnimationComplete: b } = u.getProps(), w = !this.targetLayout || !Pl(this.targetLayout, p), T = !h && f;
        if (this.options.layoutRoot || this.resumeFrom || T || h && (w || !this.currentAnimation)) {
          this.resumeFrom && (this.resumingFrom = this.resumeFrom, this.resumingFrom.resumingFrom = void 0);
          const y = {
            ...ys(g, "layout"),
            onPlay: x,
            onComplete: b
          };
          (u.shouldReduceMotion || this.options.layoutRoot) && (y.delay = 0, y.type = !1), this.startAnimation(y), this.setAnimationOrigin(d, T, y.path);
        } else
          h || Jr(this), this.isLead() && this.options.onExitComplete && this.options.onExitComplete();
        this.targetLayout = p;
      });
    }
    unmount() {
      this.options.layoutId && this.willUpdate(), this.root.nodes.remove(this);
      const o = this.getStack();
      o && o.remove(this), this.parent && this.parent.children.delete(this), this.instance = void 0, this.eventHandlers.clear(), Ve(this.updateProjection);
    }
    // only on the root
    blockUpdate() {
      this.updateManuallyBlocked = !0;
    }
    unblockUpdate() {
      this.updateManuallyBlocked = !1;
    }
    isUpdateBlocked() {
      return this.updateManuallyBlocked || this.updateBlockedByResize;
    }
    isTreeAnimationBlocked() {
      return this.isAnimationBlocked || this.parent && this.parent.isTreeAnimationBlocked() || !1;
    }
    // Note: currently only running on root node
    startUpdate() {
      this.isUpdateBlocked() || (this.isUpdating = !0, this.nodes && this.nodes.forEach(Jh), this.animationId++);
    }
    getTransformTemplate() {
      const { visualElement: o } = this.options;
      return o && o.getProps().transformTemplate;
    }
    willUpdate(o = !0) {
      if (this.root.hasTreeAnimated = !0, this.root.isUpdateBlocked()) {
        this.options.onExitComplete && this.options.onExitComplete();
        return;
      }
      if (window.MotionCancelOptimisedAnimation && !this.hasCheckedOptimisedAppear && El(this), !this.root.isUpdating && this.root.startUpdate(), this.isLayoutDirty)
        return;
      this.isLayoutDirty = !0;
      for (let d = 0; d < this.path.length; d++) {
        const h = this.path[d];
        h.shouldResetTransform = !0, (typeof h.latestValues.x == "string" || typeof h.latestValues.y == "string") && (h.isLayoutDirty = !0), h.updateScroll("snapshot"), h.options.layoutRoot && h.willUpdate(!1);
      }
      const { layoutId: a, layout: l } = this.options;
      if (a === void 0 && !l)
        return;
      const u = this.getTransformTemplate();
      this.prevTransformTemplateValue = u ? u(this.latestValues, "") : void 0, this.updateSnapshot(), o && this.notifyListeners("willUpdate");
    }
    update() {
      if (this.updateScheduled = !1, this.isUpdateBlocked()) {
        const l = this.updateBlockedByResize;
        this.unblockUpdate(), this.updateBlockedByResize = !1, this.clearAllSnapshots(), l && this.nodes.forEach(qh), this.nodes.forEach(Zr);
        return;
      }
      if (this.animationId <= this.animationCommitId) {
        this.nodes.forEach(Qr);
        return;
      }
      this.animationCommitId = this.animationId, this.isUpdating ? (this.isUpdating = !1, this.nodes.forEach(Yh), this.nodes.forEach(Xh), this.nodes.forEach(_h), this.nodes.forEach(zh)) : this.nodes.forEach(Qr), this.clearAllSnapshots();
      const a = ae.now();
      te.delta = ke(0, 1e3 / 60, a - te.timestamp), te.timestamp = a, te.isProcessing = !0, jn.update.process(te), jn.preRender.process(te), jn.render.process(te), te.isProcessing = !1;
    }
    didUpdate() {
      this.updateScheduled || (this.updateScheduled = !0, Ms.read(this.scheduleUpdate));
    }
    clearAllSnapshots() {
      this.nodes.forEach(Hh), this.sharedNodes.forEach(ep);
    }
    scheduleUpdateProjection() {
      this.projectionUpdateScheduled || (this.projectionUpdateScheduled = !0, z.preRender(this.updateProjection, !1, !0));
    }
    scheduleCheckAfterUnmount() {
      z.postRender(() => {
        this.isLayoutDirty ? this.root.didUpdate() : this.root.checkUpdateFailed();
      });
    }
    /**
     * Update measurements
     */
    updateSnapshot() {
      this.snapshot || !this.instance || (this.snapshot = this.measure(), this.snapshot && !ue(this.snapshot.measuredBox.x) && !ue(this.snapshot.measuredBox.y) && (this.snapshot = void 0));
    }
    updateLayout() {
      if (!this.instance || (this.updateScroll(), !(this.options.alwaysMeasureLayout && this.isLead()) && !this.isLayoutDirty))
        return;
      if (this.resumeFrom && !this.resumeFrom.instance)
        for (let l = 0; l < this.path.length; l++)
          this.path[l].updateScroll();
      const o = this.layout;
      this.layout = this.measure(!1), this.layoutVersion++, this.layoutCorrected || (this.layoutCorrected = ee()), this.isLayoutDirty = !1, this.projectionDelta = void 0, this.notifyListeners("measure", this.layout.layoutBox);
      const { visualElement: a } = this.options;
      a && a.notify("LayoutMeasure", this.layout.layoutBox, o ? o.layoutBox : void 0);
    }
    updateScroll(o = "measure") {
      let a = !!(this.options.layoutScroll && this.instance);
      if (this.scroll && this.scroll.animationId === this.root.animationId && this.scroll.phase === o && (a = !1), a && this.instance) {
        const l = i(this.instance);
        this.scroll = {
          animationId: this.root.animationId,
          phase: o,
          isRoot: l,
          offset: n(this.instance),
          wasRoot: this.scroll ? this.scroll.isRoot : l
        };
      }
    }
    resetTransform() {
      if (!s)
        return;
      const o = this.isLayoutDirty || this.shouldResetTransform || this.options.alwaysMeasureLayout, a = this.projectionDelta && !Nl(this.projectionDelta), l = this.getTransformTemplate(), u = l ? l(this.latestValues, "") : void 0, d = u !== this.prevTransformTemplateValue;
      o && this.instance && (a || ze(this.latestValues) || d) && (s(this.instance, u), this.shouldResetTransform = !1, this.scheduleRender());
    }
    measure(o = !0) {
      const a = this.measurePageBox();
      let l = this.removeElementScroll(a);
      return o && (l = this.removeTransform(l)), sp(l), {
        animationId: this.root.animationId,
        measuredBox: a,
        layoutBox: l,
        latestValues: {},
        source: this.id
      };
    }
    measurePageBox() {
      const { visualElement: o } = this.options;
      if (!o)
        return ee();
      const a = o.measureViewportBox();
      if (!(this.scroll?.wasRoot || this.path.some(rp))) {
        const { scroll: u } = this.root;
        u && (Ne(a.x, u.offset.x), Ne(a.y, u.offset.y));
      }
      return a;
    }
    removeElementScroll(o) {
      const a = ee();
      if (ve(a, o), this.scroll?.wasRoot)
        return a;
      for (let l = 0; l < this.path.length; l++) {
        const u = this.path[l], { scroll: d, options: h } = u;
        u !== this.root && d && h.layoutScroll && (d.wasRoot && ve(a, o), Ne(a.x, d.offset.x), Ne(a.y, d.offset.y));
      }
      return a;
    }
    applyTransform(o, a = !1, l) {
      const u = l || ee();
      ve(u, o);
      for (let d = 0; d < this.path.length; d++) {
        const h = this.path[d];
        !a && h.options.layoutScroll && h.scroll && h !== h.root && (Ne(u.x, -h.scroll.offset.x), Ne(u.y, -h.scroll.offset.y)), ze(h.latestValues) && on(u, h.latestValues, h.layout?.layoutBox);
      }
      return ze(this.latestValues) && on(u, this.latestValues, this.layout?.layoutBox), u;
    }
    removeTransform(o) {
      const a = ee();
      ve(a, o);
      for (let l = 0; l < this.path.length; l++) {
        const u = this.path[l];
        if (!ze(u.latestValues))
          continue;
        let d;
        u.instance && (Ci(u.latestValues) && u.updateSnapshot(), d = ee(), ve(d, u.measurePageBox())), Wr(a, u.latestValues, u.snapshot?.layoutBox, d);
      }
      return ze(this.latestValues) && Wr(a, this.latestValues), a;
    }
    setTargetDelta(o) {
      this.targetDelta = o, this.root.scheduleUpdateProjection(), this.isProjectionDirty = !0;
    }
    setOptions(o) {
      this.options = {
        ...this.options,
        ...o,
        crossfade: o.crossfade !== void 0 ? o.crossfade : !0
      };
    }
    clearMeasurements() {
      this.scroll = void 0, this.layout = void 0, this.snapshot = void 0, this.prevTransformTemplateValue = void 0, this.targetDelta = void 0, this.target = void 0, this.isLayoutDirty = !1;
    }
    forceRelativeParentToResolveTarget() {
      this.relativeParent && this.relativeParent.resolvedRelativeTargetAt !== te.timestamp && this.relativeParent.resolveTargetDelta(!0);
    }
    resolveTargetDelta(o = !1) {
      const a = this.getLead();
      this.isProjectionDirty || (this.isProjectionDirty = a.isProjectionDirty), this.isTransformDirty || (this.isTransformDirty = a.isTransformDirty), this.isSharedProjectionDirty || (this.isSharedProjectionDirty = a.isSharedProjectionDirty);
      const l = !!this.resumingFrom || this !== a;
      if (!(o || l && this.isSharedProjectionDirty || this.isProjectionDirty || this.parent?.isProjectionDirty || this.attemptToResolveRelativeTarget || this.root.updateBlockedByResize))
        return;
      const { layout: d, layoutId: h } = this.options;
      if (!this.layout || !(d || h))
        return;
      this.resolvedRelativeTargetAt = te.timestamp;
      const f = this.getClosestProjectingParent();
      f && this.linkedParentVersion !== f.layoutVersion && !f.options.layoutRoot && this.removeRelativeTarget(), !this.targetDelta && !this.relativeTarget && (this.options.layoutAnchor !== !1 && f && f.layout ? this.createRelativeTarget(f, this.layout.layoutBox, f.layout.layoutBox) : this.removeRelativeTarget()), !(!this.relativeTarget && !this.targetDelta) && (this.target || (this.target = ee(), this.targetWithTransforms = ee()), this.relativeTarget && this.relativeTargetOrigin && this.relativeParent && this.relativeParent.target ? (this.forceRelativeParentToResolveTarget(), Ph(this.target, this.relativeTarget, this.relativeParent.target, this.options.layoutAnchor || void 0)) : this.targetDelta ? (this.resumingFrom ? this.applyTransform(this.layout.layoutBox, !1, this.target) : ve(this.target, this.layout.layoutBox), al(this.target, this.targetDelta)) : ve(this.target, this.layout.layoutBox), this.attemptToResolveRelativeTarget && (this.attemptToResolveRelativeTarget = !1, this.options.layoutAnchor !== !1 && f && !!f.resumingFrom == !!this.resumingFrom && !f.options.layoutScroll && f.target && this.animationProgress !== 1 ? this.createRelativeTarget(f, this.target, f.target) : this.relativeParent = this.relativeTarget = void 0));
    }
    getClosestProjectingParent() {
      if (!(!this.parent || Ci(this.parent.latestValues) || ol(this.parent.latestValues)))
        return this.parent.isProjecting() ? this.parent : this.parent.getClosestProjectingParent();
    }
    isProjecting() {
      return !!((this.relativeTarget || this.targetDelta || this.options.layoutRoot) && this.layout);
    }
    createRelativeTarget(o, a, l) {
      this.relativeParent = o, this.linkedParentVersion = o.layoutVersion, this.forceRelativeParentToResolveTarget(), this.relativeTarget = ee(), this.relativeTargetOrigin = ee(), Sn(this.relativeTargetOrigin, a, l, this.options.layoutAnchor || void 0), ve(this.relativeTarget, this.relativeTargetOrigin);
    }
    removeRelativeTarget() {
      this.relativeParent = this.relativeTarget = void 0;
    }
    calcProjection() {
      const o = this.getLead(), a = !!this.resumingFrom || this !== o;
      let l = !0;
      if ((this.isProjectionDirty || this.parent?.isProjectionDirty) && (l = !1), a && (this.isSharedProjectionDirty || this.isTransformDirty) && (l = !1), this.resolvedRelativeTargetAt === te.timestamp && (l = !1), l)
        return;
      const { layout: u, layoutId: d } = this.options;
      if (this.isTreeAnimating = !!(this.parent && this.parent.isTreeAnimating || this.currentAnimation || this.pendingAnimation), this.isTreeAnimating || (this.targetDelta = this.relativeTarget = void 0), !this.layout || !(u || d))
        return;
      ve(this.layoutCorrected, this.layout.layoutBox);
      const h = this.treeScale.x, f = this.treeScale.y;
      Ff(this.layoutCorrected, this.treeScale, this.path, a), o.layout && !o.target && (this.treeScale.x !== 1 || this.treeScale.y !== 1) && (o.target = o.layout.layoutBox, o.targetWithTransforms = ee());
      const { target: p } = o;
      if (!p) {
        this.prevProjectionDelta && (this.createProjectionDeltas(), this.scheduleRender());
        return;
      }
      !this.projectionDelta || !this.prevProjectionDelta ? this.createProjectionDeltas() : (Ir(this.prevProjectionDelta.x, this.projectionDelta.x), Ir(this.prevProjectionDelta.y, this.projectionDelta.y)), Pt(this.projectionDelta, this.layoutCorrected, p, this.latestValues), (this.treeScale.x !== h || this.treeScale.y !== f || !Hr(this.projectionDelta.x, this.prevProjectionDelta.x) || !Hr(this.projectionDelta.y, this.prevProjectionDelta.y)) && (this.hasProjected = !0, this.scheduleRender(), this.notifyListeners("projectionUpdate", p));
    }
    hide() {
      this.isVisible = !1;
    }
    show() {
      this.isVisible = !0;
    }
    scheduleRender(o = !0) {
      if (this.options.visualElement?.scheduleRender(), o) {
        const a = this.getStack();
        a && a.scheduleRender();
      }
      this.resumingFrom && !this.resumingFrom.instance && (this.resumingFrom = void 0);
    }
    createProjectionDeltas() {
      this.prevProjectionDelta = at(), this.projectionDelta = at(), this.projectionDeltaWithTransform = at();
    }
    setAnimationOrigin(o, a = !1, l) {
      const u = this.snapshot, d = u ? u.latestValues : {}, h = { ...this.latestValues }, f = at();
      (!this.relativeParent || !this.relativeParent.options.layoutRoot) && (this.relativeTarget = this.relativeTargetOrigin = void 0), this.attemptToResolveRelativeTarget = !a;
      const p = ee(), g = u ? u.source : void 0, x = this.layout ? this.layout.source : void 0, b = g !== x, w = this.getStack(), T = !w || w.members.length <= 1, y = !!(b && !T && this.options.crossfade === !0 && !this.path.some(np));
      this.animationProgress = 0;
      let k;
      const E = l?.interpolateProjection(o);
      this.mixTargetDelta = (P) => {
        const S = P / 1e3, m = E?.(S);
        m ? (f.x.translate = m.x, f.x.scale = K(o.x.scale, 1, S), f.x.origin = o.x.origin, f.x.originPoint = o.x.originPoint, f.y.translate = m.y, f.y.scale = K(o.y.scale, 1, S), f.y.origin = o.y.origin, f.y.originPoint = o.y.originPoint) : (eo(f.x, o.x, S), eo(f.y, o.y, S)), this.setTargetDelta(f), this.relativeTarget && this.relativeTargetOrigin && this.layout && this.relativeParent && this.relativeParent.layout && (Sn(p, this.layout.layoutBox, this.relativeParent.layout.layoutBox, this.options.layoutAnchor || void 0), tp(this.relativeTarget, this.relativeTargetOrigin, p, S), k && Dh(this.relativeTarget, k) && (this.isProjectionDirty = !1), k || (k = ee()), ve(k, this.relativeTarget)), b && (this.animationValues = h, Lh(h, d, this.latestValues, S, y, T)), m && m.rotate !== void 0 && (this.animationValues || (this.animationValues = h), this.animationValues.pathRotation = m.rotate), this.root.scheduleUpdateProjection(), this.scheduleRender(), this.animationProgress = S;
      }, this.mixTargetDelta(this.options.layoutRoot ? 1e3 : 0);
    }
    startAnimation(o) {
      this.notifyListeners("animationStart"), this.currentAnimation?.stop(), this.resumingFrom?.currentAnimation?.stop(), this.pendingAnimation && (Ve(this.pendingAnimation), this.pendingAnimation = void 0), this.pendingAnimation = z.update(() => {
        fn.hasAnimatedSinceResize = !0, this.motionValue || (this.motionValue = Re(0)), this.motionValue.jump(0, !1), this.currentAnimation = Cl(this.motionValue, [0, 1e3], {
          ...o,
          velocity: 0,
          isSync: !0,
          onUpdate: (a) => {
            this.mixTargetDelta(a), o.onUpdate && o.onUpdate(a);
          },
          onComplete: () => {
            o.onComplete && o.onComplete(), this.completeAnimation();
          }
        }), od(this.currentAnimation, this), this.resumingFrom && (this.resumingFrom.currentAnimation = this.currentAnimation), this.pendingAnimation = void 0;
      });
    }
    completeAnimation() {
      this.resumingFrom && (this.resumingFrom.currentAnimation = void 0, this.resumingFrom.preserveOpacity = void 0);
      const o = this.getStack();
      o && o.exitAnimationComplete(), this.resumingFrom = this.currentAnimation = this.animationValues = void 0, this.notifyListeners("animationComplete");
    }
    finishAnimation() {
      this.currentAnimation && (this.mixTargetDelta && this.mixTargetDelta(Uh), this.currentAnimation.stop()), this.completeAnimation();
    }
    applyTransformsToTarget() {
      const o = this.getLead(), { targetWithTransforms: a, layout: l, latestValues: u } = o;
      let { target: d } = o;
      if (!(!a || !d || !l)) {
        if (this !== o && this.layout && l && Vl(this.options.animationType, this.layout.layoutBox, l.layoutBox)) {
          d = this.target || ee();
          const h = ue(this.layout.layoutBox.x);
          d.x.min = o.target.x.min, d.x.max = d.x.min + h;
          const f = ue(this.layout.layoutBox.y);
          d.y.min = o.target.y.min, d.y.max = d.y.min + f;
        }
        ve(a, d), on(a, u), Pt(this.projectionDeltaWithTransform, this.layoutCorrected, a, u);
      }
    }
    registerSharedNode(o, a) {
      this.sharedNodes.has(o) || this.sharedNodes.set(o, new jh()), this.sharedNodes.get(o).add(a);
      const u = a.options.initialPromotionConfig;
      a.promote({
        transition: u ? u.transition : void 0,
        preserveFollowOpacity: u && u.shouldPreserveFollowOpacity ? u.shouldPreserveFollowOpacity(a) : void 0
      });
    }
    isLead() {
      const o = this.getStack();
      return o ? o.lead === this : !0;
    }
    getLead() {
      const { layoutId: o } = this.options;
      return o ? this.getStack()?.lead || this : this;
    }
    getPrevLead() {
      const { layoutId: o } = this.options;
      return o ? this.getStack()?.prevLead : void 0;
    }
    getStack() {
      const { layoutId: o } = this.options;
      if (o)
        return this.root.sharedNodes.get(o);
    }
    promote({ needsReset: o, transition: a, preserveFollowOpacity: l } = {}) {
      const u = this.getStack();
      u && u.promote(this, l), o && (this.projectionDelta = void 0, this.needsReset = !0), a && this.setOptions({ transition: a });
    }
    relegate() {
      const o = this.getStack();
      return o ? o.relegate(this) : !1;
    }
    resetSkewAndRotation() {
      const { visualElement: o } = this.options;
      if (!o)
        return;
      let a = !1;
      const { latestValues: l } = o;
      if ((l.z || l.rotate || l.rotateX || l.rotateY || l.rotateZ || l.skewX || l.skewY) && (a = !0), !a)
        return;
      const u = {};
      l.z && Xn("z", o, u, this.animationValues);
      for (let d = 0; d < Yn.length; d++)
        Xn(`rotate${Yn[d]}`, o, u, this.animationValues), Xn(`skew${Yn[d]}`, o, u, this.animationValues);
      o.render();
      for (const d in u)
        o.setStaticValue(d, u[d]), this.animationValues && (this.animationValues[d] = u[d]);
      o.scheduleRender();
    }
    applyProjectionStyles(o, a) {
      if (!this.instance || this.isSVG)
        return;
      if (!this.isVisible) {
        o.visibility = "hidden";
        return;
      }
      const l = this.getTransformTemplate();
      if (this.needsReset) {
        this.needsReset = !1, o.visibility = "", o.opacity = "", o.pointerEvents = dn(a?.pointerEvents) || "", o.transform = l ? l(this.latestValues, "") : "none";
        return;
      }
      const u = this.getLead();
      if (!this.projectionDelta || !this.layout || !u.target) {
        this.options.layoutId && (o.opacity = this.latestValues.opacity !== void 0 ? this.latestValues.opacity : 1, o.pointerEvents = dn(a?.pointerEvents) || ""), this.hasProjected && !ze(this.latestValues) && (o.transform = l ? l({}, "") : "none", this.hasProjected = !1);
        return;
      }
      o.visibility = "";
      const d = u.animationValues || u.latestValues;
      this.applyTransformsToTarget();
      let h = Vh(this.projectionDeltaWithTransform, this.treeScale, d);
      l && (h = l(d, h)), o.transform = h;
      const { x: f, y: p } = this.projectionDelta;
      o.transformOrigin = `${f.origin * 100}% ${p.origin * 100}% 0`, u.animationValues ? o.opacity = u === this ? d.opacity ?? this.latestValues.opacity ?? 1 : this.preserveOpacity ? this.latestValues.opacity : d.opacityExit : o.opacity = u === this ? d.opacity !== void 0 ? d.opacity : "" : d.opacityExit !== void 0 ? d.opacityExit : 0;
      for (const g in Di) {
        if (d[g] === void 0)
          continue;
        const { correct: x, applyTo: b, isCSSVariable: w } = Di[g], T = h === "none" ? d[g] : x(d[g], u);
        if (b) {
          const y = b.length;
          for (let k = 0; k < y; k++)
            o[b[k]] = T;
        } else
          w ? this.options.visualElement.renderState.vars[g] = T : o[g] = T;
      }
      this.options.layoutId && (o.pointerEvents = u === this ? dn(a?.pointerEvents) || "" : "none");
    }
    clearSnapshot() {
      this.resumeFrom = this.snapshot = void 0;
    }
    // Only run on root
    resetTree() {
      this.root.nodes.forEach((o) => o.currentAnimation?.stop()), this.root.nodes.forEach(Zr), this.root.sharedNodes.clear();
    }
  };
}
function _h(e) {
  e.updateLayout();
}
function zh(e) {
  const t = e.resumeFrom?.snapshot || e.snapshot;
  if (e.isLead() && e.layout && t && e.hasListeners("didUpdate")) {
    const { layoutBox: n, measuredBox: i } = e.layout, { animationType: s } = e.options, r = t.source !== e.layout.source;
    if (s === "size")
      Ae((d) => {
        const h = r ? t.measuredBox[d] : t.layoutBox[d], f = ue(h);
        h.min = n[d].min, h.max = h.min + f;
      });
    else if (s === "x" || s === "y") {
      const d = s === "x" ? "y" : "x";
      Vi(r ? t.measuredBox[d] : t.layoutBox[d], n[d]);
    } else Vl(s, t.layoutBox, n) && Ae((d) => {
      const h = r ? t.measuredBox[d] : t.layoutBox[d], f = ue(n[d]);
      h.max = h.min + f, e.relativeTarget && !e.currentAnimation && (e.isProjectionDirty = !0, e.relativeTarget[d].max = e.relativeTarget[d].min + f);
    });
    const o = at();
    Pt(o, n, t.layoutBox);
    const a = at();
    r ? Pt(a, e.applyTransform(i, !0), t.measuredBox) : Pt(a, n, t.layoutBox);
    const l = !Nl(o);
    let u = !1;
    if (!e.resumeFrom) {
      const d = e.getClosestProjectingParent();
      if (d && !d.resumeFrom) {
        const { snapshot: h, layout: f } = d;
        if (h && f) {
          const p = e.options.layoutAnchor || void 0, g = ee();
          Sn(g, t.layoutBox, h.layoutBox, p);
          const x = ee();
          Sn(x, n, f.layoutBox, p), Pl(g, x) || (u = !0), d.options.layoutRoot && (e.relativeTarget = x, e.relativeTargetOrigin = g, e.relativeParent = d);
        }
      }
    }
    e.notifyListeners("didUpdate", {
      layout: n,
      snapshot: t,
      delta: a,
      layoutDelta: o,
      hasLayoutChanged: l,
      hasRelativeLayoutChanged: u
    });
  } else if (e.isLead()) {
    const { onExitComplete: n } = e.options;
    n && n();
  }
  e.options.transition = void 0;
}
function Gh(e) {
  e.parent && (e.isProjecting() || (e.isProjectionDirty = e.parent.isProjectionDirty), e.isSharedProjectionDirty || (e.isSharedProjectionDirty = !!(e.isProjectionDirty || e.parent.isProjectionDirty || e.parent.isSharedProjectionDirty)), e.isTransformDirty || (e.isTransformDirty = e.parent.isTransformDirty));
}
function Kh(e) {
  e.isProjectionDirty = e.isSharedProjectionDirty = e.isTransformDirty = !1;
}
function Hh(e) {
  e.clearSnapshot();
}
function Zr(e) {
  e.clearMeasurements();
}
function qh(e) {
  e.isLayoutDirty = !0, e.updateLayout();
}
function Qr(e) {
  e.isLayoutDirty = !1;
}
function Yh(e) {
  e.isAnimationBlocked && e.layout && !e.isLayoutDirty && (e.snapshot = e.layout, e.isLayoutDirty = !0);
}
function Xh(e) {
  const { visualElement: t } = e.options;
  t && t.getProps().onBeforeLayoutMeasure && t.notify("BeforeLayoutMeasure"), e.resetTransform();
}
function Jr(e) {
  e.finishAnimation(), e.targetDelta = e.relativeTarget = e.target = void 0, e.isProjectionDirty = !0;
}
function Zh(e) {
  e.resolveTargetDelta();
}
function Qh(e) {
  e.calcProjection();
}
function Jh(e) {
  e.resetSkewAndRotation();
}
function ep(e) {
  e.removeLeadSnapshot();
}
function eo(e, t, n) {
  e.translate = K(t.translate, 0, n), e.scale = K(t.scale, 1, n), e.origin = t.origin, e.originPoint = t.originPoint;
}
function to(e, t, n, i) {
  e.min = K(t.min, n.min, i), e.max = K(t.max, n.max, i);
}
function tp(e, t, n, i) {
  to(e.x, t.x, n.x, i), to(e.y, t.y, n.y, i);
}
function np(e) {
  return e.animationValues && e.animationValues.opacityExit !== void 0;
}
const ip = {
  duration: 0.45,
  ease: [0.4, 0, 0.1, 1]
}, no = (e) => typeof navigator < "u" && navigator.userAgent && navigator.userAgent.toLowerCase().includes(e), io = no("applewebkit/") && !no("chrome/") ? Math.round : we;
function so(e) {
  e.min = io(e.min), e.max = io(e.max);
}
function sp(e) {
  so(e.x), so(e.y);
}
function Vl(e, t, n) {
  return e === "position" || e === "preserve-aspect" && !Nh(Kr(t), Kr(n), 0.2);
}
function rp(e) {
  return e !== e.root && e.scroll?.wasRoot;
}
const op = Dl({
  attachResizeListener: (e, t) => It(e, "resize", t),
  measureScroll: () => ({
    x: document.documentElement.scrollLeft || document.body?.scrollLeft || 0,
    y: document.documentElement.scrollTop || document.body?.scrollTop || 0
  }),
  checkIsScrollRoot: () => !0
}), Zn = {
  current: void 0
}, Rl = Dl({
  measureScroll: (e) => ({
    x: e.scrollLeft,
    y: e.scrollTop
  }),
  defaultParent: () => {
    if (!Zn.current) {
      const e = new op({});
      e.mount(window), e.setOptions({ layoutScroll: !0 }), Zn.current = e;
    }
    return Zn.current;
  },
  resetTransform: (e, t) => {
    e.style.transform = t !== void 0 ? t : "none";
  },
  checkIsScrollRoot: (e) => window.getComputedStyle(e).position === "fixed"
}), Rn = ht({
  transformPagePoint: (e) => e,
  isStatic: !1,
  reducedMotion: "never"
});
function ro(e, t) {
  if (typeof e == "function")
    return e(t);
  e != null && (e.current = t);
}
function ap(...e) {
  return (t) => {
    let n = !1;
    const i = e.map((s) => {
      const r = ro(s, t);
      return !n && typeof r == "function" && (n = !0), r;
    });
    if (n)
      return () => {
        for (let s = 0; s < i.length; s++) {
          const r = i[s];
          typeof r == "function" ? r() : ro(e[s], null);
        }
      };
  };
}
function lp(...e) {
  return Pn.useCallback(ap(...e), e);
}
class cp extends Pn.Component {
  getSnapshotBeforeUpdate(t) {
    const n = this.props.childRef.current;
    if (ut(n) && t.isPresent && !this.props.isPresent && this.props.pop !== !1) {
      const i = n.offsetParent, s = ut(i) && i.offsetWidth || 0, r = ut(i) && i.offsetHeight || 0, o = getComputedStyle(n), a = this.props.sizeRef.current;
      a.height = parseFloat(o.height), a.width = parseFloat(o.width), a.top = n.offsetTop, a.left = n.offsetLeft, a.right = s - a.width - a.left, a.bottom = r - a.height - a.top, a.direction = o.direction;
    }
    return null;
  }
  /**
   * Required with getSnapshotBeforeUpdate to stop React complaining.
   */
  componentDidUpdate() {
  }
  render() {
    return this.props.children;
  }
}
function up({ children: e, isPresent: t, anchorX: n, anchorY: i, root: s, pop: r }) {
  const o = Se(), a = M(null), l = M({
    width: 0,
    height: 0,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    direction: "ltr"
  }), { nonce: u } = se(Rn), d = r !== !1 ? e.props?.ref ?? e?.ref : void 0, h = lp(a, d);
  return Bi(() => {
    const { width: f, height: p, top: g, left: x, right: b, bottom: w, direction: T } = l.current;
    if (t || r === !1 || !a.current || !f || !p)
      return;
    const y = T === "rtl", k = n === "left" ? y ? `right: ${b}` : `left: ${x}` : y ? `left: ${x}` : `right: ${b}`, E = i === "bottom" ? `bottom: ${w}` : `top: ${g}`;
    a.current.dataset.motionPopId = o;
    const P = document.createElement("style");
    u && (P.nonce = u);
    const S = s ?? document.head;
    return S.appendChild(P), P.sheet && P.sheet.insertRule(`
          [data-motion-pop-id="${o}"] {
            position: absolute !important;
            width: ${f}px !important;
            height: ${p}px !important;
            ${k}px !important;
            ${E}px !important;
          }
        `), () => {
      a.current?.removeAttribute("data-motion-pop-id"), S.contains(P) && S.removeChild(P);
    };
  }, [t]), c(cp, { isPresent: t, childRef: a, sizeRef: l, pop: r, children: r === !1 ? e : Pn.cloneElement(e, { ref: h }) });
}
const dp = ({ children: e, initial: t, isPresent: n, onExitComplete: i, custom: s, presenceAffectsLayout: r, mode: o, anchorX: a, anchorY: l, root: u }) => {
  const d = jt(fp), h = Se(), f = M(n), p = M(i);
  Dt(() => {
    f.current = n, p.current = i;
  });
  let g = !0, x = le(() => (g = !1, {
    id: h,
    initial: t,
    isPresent: n,
    custom: s,
    onExitComplete: (b) => {
      d.set(b, !0);
      for (const w of d.values())
        if (!w)
          return;
      i && i();
    },
    register: (b) => (d.set(b, !1), () => {
      d.delete(b), !f.current && !d.size && p.current?.();
    })
  }), [n, d, i]);
  return r && g && (x = { ...x }), le(() => {
    d.forEach((b, w) => d.set(w, !1));
  }, [n]), Pn.useEffect(() => {
    !n && !d.size && i && i();
  }, [n]), e = c(up, { pop: o === "popLayout", isPresent: n, anchorX: a, anchorY: l, root: u, children: e }), c(Ut.Provider, { value: x, children: e });
};
function fp() {
  return /* @__PURE__ */ new Map();
}
function Ll(e = !0) {
  const t = se(Ut);
  if (t === null)
    return [!0, null];
  const { isPresent: n, onExitComplete: i, register: s } = t, r = Se();
  F(() => {
    if (e)
      return s(r);
  }, [e]);
  const o = q(() => e && i && i(r), [r, i, e]);
  return !n && i ? [!1, o] : [!0];
}
function hp() {
  return pp(se(Ut));
}
function pp(e) {
  return e === null ? !0 : e.isPresent;
}
const Zt = (e) => e.key || "";
function oo(e) {
  const t = [];
  return wc.forEach(e, (n) => {
    kc(n) && t.push(n);
  }), t;
}
const xe = ({ children: e, custom: t, initial: n = !0, onExitComplete: i, presenceAffectsLayout: s = !0, mode: r = "sync", propagate: o = !1, anchorX: a = "left", anchorY: l = "top", root: u }) => {
  const [d, h] = Ll(o), f = le(() => oo(e), [e]), p = o && !d ? [] : f.map(Zt), g = M(!0), x = M(f), b = jt(() => /* @__PURE__ */ new Map()), w = M(/* @__PURE__ */ new Set()), [T, y] = O(f), [k, E] = O(f);
  Dt(() => {
    o && !d && !k.length && h?.();
  }, [d, o, k.length, h]), Dt(() => {
    g.current = !1, x.current = f;
    for (let m = 0; m < k.length; m++) {
      const N = Zt(k[m]);
      p.includes(N) ? (b.delete(N), w.current.delete(N)) : b.get(N) !== !0 && b.set(N, !1);
    }
  }, [k, p.length, p.join("-")]);
  const P = [];
  if (f !== T) {
    let m = [...f], N = 0;
    for (const A of k) {
      const L = p.indexOf(Zt(A));
      L === -1 ? (m.splice(N++, 0, A), P.push(A)) : N = L + P.length + 1;
    }
    return r === "wait" && P.length && (m = P), E(oo(m)), y(f), null;
  }
  process.env.NODE_ENV !== "production" && r === "wait" && k.length > 1 && console.warn(`You're attempting to animate multiple children within AnimatePresence, but its mode is set to "wait". This will lead to odd visual behaviour.`);
  const { forceRender: S } = se(Zi);
  return c(G, { children: k.map((m) => {
    const N = Zt(m), A = o && !d ? !1 : f === k || p.includes(N), L = () => {
      if (w.current.has(N))
        return;
      if (b.has(N))
        w.current.add(N), b.set(N, !0);
      else
        return;
      let I = !0;
      b.forEach((j) => {
        j || (I = !1);
      }), I && (S?.(), E(x.current), o && h?.(), i && i());
    };
    return c(dp, { isPresent: A, initial: !g.current || n ? void 0 : !1, custom: t, presenceAffectsLayout: s, mode: r, root: u, onExitComplete: A ? void 0 : L, anchorX: a, anchorY: l, children: m }, N);
  }) });
}, Fl = ht({ strict: !1 }), ao = {
  animation: [
    "animate",
    "variants",
    "whileHover",
    "whileTap",
    "exit",
    "whileInView",
    "whileFocus",
    "whileDrag"
  ],
  exit: ["exit"],
  drag: ["drag", "dragControls"],
  focus: ["whileFocus"],
  hover: ["whileHover", "onHoverStart", "onHoverEnd"],
  tap: ["whileTap", "onTap", "onTapStart", "onTapCancel"],
  pan: ["onPan", "onPanStart", "onPanSessionStart", "onPanEnd"],
  inView: ["whileInView", "onViewportEnter", "onViewportLeave"],
  layout: ["layout", "layoutId"]
};
let lo = !1;
function mp() {
  if (lo)
    return;
  const e = {};
  for (const t in ao)
    e[t] = {
      isEnabled: (n) => ao[t].some((i) => !!n[i])
    };
  ml(e), lo = !0;
}
function Il() {
  return mp(), ch();
}
function gp(e) {
  const t = Il();
  for (const n in e)
    t[n] = {
      ...t[n],
      ...e[n]
    };
  ml(t);
}
const Ln = /* @__PURE__ */ ht({});
function yp(e, t) {
  if (Vn(e)) {
    const { initial: n, animate: i } = e;
    return {
      initial: n === !1 || Ft(n) ? n : void 0,
      animate: Ft(i) ? i : void 0
    };
  }
  return e.inherit !== !1 ? t : {};
}
function xp(e) {
  const { initial: t, animate: n } = yp(e, se(Ln));
  return le(() => ({ initial: t, animate: n }), [co(t), co(n)]);
}
function co(e) {
  return Array.isArray(e) ? e.join(" ") : e;
}
const Rs = () => ({
  style: {},
  transform: {},
  transformOrigin: {},
  vars: {}
});
function Ol(e, t, n) {
  for (const i in t)
    !ie(t[i]) && !xl(i, n) && (e[i] = t[i]);
}
function vp({ transformTemplate: e }, t) {
  return le(() => {
    const n = Rs();
    return As(n, t, e), Object.assign({}, n.vars, n.style);
  }, [t]);
}
function bp(e, t) {
  const n = e.style || {}, i = {};
  return Ol(i, n, e), Object.assign(i, vp(e, t)), i;
}
function wp(e, t) {
  const n = {}, i = bp(e, t);
  return e.drag && e.dragListener !== !1 && (n.draggable = !1, i.userSelect = i.WebkitUserSelect = i.WebkitTouchCallout = "none", i.touchAction = e.drag === !0 ? "none" : `pan-${e.drag === "x" ? "y" : "x"}`), e.tabIndex === void 0 && (e.onTap || e.onTapStart || e.whileTap) && (n.tabIndex = 0), n.style = i, n;
}
const Bl = () => ({
  ...Rs(),
  attrs: {}
});
function kp(e, t, n, i) {
  const s = le(() => {
    const r = Bl();
    return il(r, t, bl(i), e.transformTemplate, e.style), {
      ...r.attrs,
      style: { ...r.style }
    };
  }, [t]);
  if (e.style) {
    const r = {};
    Ol(r, e.style, e), s.style = { ...r, ...s.style };
  }
  return s;
}
const Tp = /* @__PURE__ */ new Set([
  "animate",
  "exit",
  "variants",
  "initial",
  "style",
  "values",
  "variants",
  "transition",
  "transformTemplate",
  "custom",
  "inherit",
  "onBeforeLayoutMeasure",
  "onAnimationStart",
  "onAnimationComplete",
  "onUpdate",
  "onDragStart",
  "onDrag",
  "onDragEnd",
  "onMeasureDragConstraints",
  "onDirectionLock",
  "onDragTransitionEnd",
  "_dragX",
  "_dragY",
  "onHoverStart",
  "onHoverEnd",
  "onViewportEnter",
  "onViewportLeave",
  "globalTapTarget",
  "propagate",
  "ignoreStrict",
  "viewport"
]);
function An(e) {
  return e.startsWith("while") || e.startsWith("drag") && e !== "draggable" || e.startsWith("layout") || e.startsWith("onTap") || e.startsWith("onPan") || e.startsWith("onLayout") || Tp.has(e);
}
function Sp(e, t) {
  return e.startsWith("on") ? !An(e) : t?.(e) ?? !An(e);
}
function Ap(e, t, n, i) {
  const s = {};
  for (const r in e)
    r === "values" && typeof e.values == "object" || ie(e[r]) || (Sp(r, i) || n === !0 && An(r) || !t && !An(r) || // If trying to use native HTML drag events, forward drag listeners
    e.draggable && r.startsWith("onDrag")) && (s[r] = e[r]);
  return s;
}
const Np = [
  "animate",
  "circle",
  "defs",
  "desc",
  "ellipse",
  "g",
  "image",
  "line",
  "filter",
  "marker",
  "mask",
  "metadata",
  "path",
  "pattern",
  "polygon",
  "polyline",
  "rect",
  "stop",
  "switch",
  "symbol",
  "svg",
  "text",
  "tspan",
  "use",
  "view"
];
function Ls(e) {
  return (
    /**
     * If it's not a string, it's a custom React component. Currently we only support
     * HTML custom React components.
     */
    typeof e != "string" || /**
     * If it contains a dash, the element is a custom HTML webcomponent.
     */
    e.includes("-") ? !1 : (
      /**
       * If it's in our list of lowercase SVG tags, it's an SVG component
       */
      !!(Np.indexOf(e) > -1 || /**
       * If it contains a capital letter, it's an SVG component
       */
      /[A-Z]/u.test(e))
    )
  );
}
function Pp(e, t, n, { latestValues: i }, s, r = !1, o, a) {
  const u = (o ?? Ls(e) ? kp : wp)(t, i, s, e), d = Ap(t, typeof e == "string", r, a), h = e !== $i ? { ...d, ...u, ref: n } : {}, { children: f } = t, p = le(() => ie(f) ? f.get() : f, [f]);
  return Tc(e, {
    ...h,
    children: p
  });
}
function Mp({ scrapeMotionValuesFromProps: e, createRenderState: t }, n, i, s) {
  return {
    latestValues: Cp(n, i, s, e),
    renderState: t()
  };
}
function Cp(e, t, n, i) {
  const s = {}, r = i(e, {});
  for (const f in r)
    s[f] = dn(r[f]);
  let { initial: o, animate: a } = e;
  const l = Vn(e), u = hl(e);
  t && u && !l && e.inherit !== !1 && (o === void 0 && (o = t.initial), a === void 0 && (a = t.animate));
  let d = n ? n.initial === !1 : !1;
  d = d || o === !1;
  const h = d ? a : o;
  if (h && typeof h != "boolean" && !Dn(h)) {
    const f = Array.isArray(h) ? h : [h];
    for (let p = 0; p < f.length; p++) {
      const g = xs(e, f[p]);
      if (g) {
        const { transitionEnd: x, transition: b, ...w } = g;
        for (const T in w) {
          let y = w[T];
          if (Array.isArray(y)) {
            const k = d ? y.length - 1 : 0;
            y = y[k];
          }
          y !== null && (s[T] = y);
        }
        for (const T in x)
          s[T] = x[T];
      }
    }
  }
  return s;
}
const $l = (e) => (t, n) => {
  const i = se(Ln), s = se(Ut), r = () => Mp(e, t, i, s);
  return n ? r() : jt(r);
}, Ep = /* @__PURE__ */ $l({
  scrapeMotionValuesFromProps: Vs,
  createRenderState: Rs
}), Dp = /* @__PURE__ */ $l({
  scrapeMotionValuesFromProps: wl,
  createRenderState: Bl
}), Vp = /* @__PURE__ */ Symbol.for("motionComponentSymbol");
function Rp(e, t, n) {
  const i = M(n);
  Bi(() => {
    i.current = n;
  });
  const s = M(null);
  return q((r) => {
    r && e.onMount?.(r), t && (r ? t.mount(r) : t.unmount());
    const o = i.current;
    if (typeof o == "function")
      if (r) {
        const a = o(r);
        typeof a == "function" && (s.current = a);
      } else s.current ? (s.current(), s.current = null) : o(r);
    else o && (o.current = r);
  }, [t]);
}
const jl = ht({});
function tt(e) {
  return e && typeof e == "object" && Object.prototype.hasOwnProperty.call(e, "current");
}
function Lp(e, t, n, i, s, r) {
  const { visualElement: o } = se(Ln), a = se(Fl), l = se(Ut), u = se(Rn), d = u.reducedMotion, h = u.skipAnimations, f = M(null), p = M(!1);
  i = i || a.renderer, !f.current && i && (f.current = i(e, {
    visualState: t,
    parent: o,
    props: n,
    presenceContext: l,
    blockInitialAnimation: l ? l.initial === !1 : !1,
    reducedMotionConfig: d,
    skipAnimations: h,
    isSVG: r
  }), p.current && f.current && (f.current.manuallyAnimateOnMount = !0));
  const g = f.current, x = se(jl);
  g && !g.projection && s && (g.type === "html" || g.type === "svg") && Fp(f.current, n, s, x);
  const b = M(!1);
  Bi(() => {
    g && b.current && g.update(n, l);
  });
  const w = n[Ya], T = M(!!w && typeof window < "u" && !window.MotionHandoffIsComplete?.(w) && window.MotionHasOptimisedAnimation?.(w));
  return Dt(() => {
    p.current = !0, g && (b.current = !0, window.MotionIsMounted = !0, g.updateFeatures(), g.scheduleRenderMicrotask(), T.current && g.animationState && g.animationState.animateChanges());
  }), F(() => {
    g && (!T.current && g.animationState && g.animationState.animateChanges(), T.current && (queueMicrotask(() => {
      window.MotionHandoffMarkAsComplete?.(w);
    }), T.current = !1), g.enteringChildren = void 0);
  }), g;
}
function Fp(e, t, n, i) {
  const { layoutId: s, layout: r, drag: o, dragConstraints: a, layoutScroll: l, layoutRoot: u, layoutAnchor: d, layoutCrossfade: h } = t;
  e.projection = new n(e.latestValues, t["data-framer-portal-id"] ? void 0 : Ul(e.parent)), e.projection.setOptions({
    layoutId: s,
    layout: r,
    alwaysMeasureLayout: !!o || a && tt(a),
    visualElement: e,
    /**
     * TODO: Update options in an effect. This could be tricky as it'll be too late
     * to update by the time layout animations run.
     * We also need to fix this safeToRemove by linking it up to the one returned by usePresence,
     * ensuring it gets called if there's no potential layout animations.
     *
     */
    animationType: typeof r == "string" ? r : "both",
    initialPromotionConfig: i,
    crossfade: h,
    layoutScroll: l,
    layoutRoot: u,
    layoutAnchor: d
  });
}
function Ul(e) {
  if (e)
    return e.options.allowProjection !== !1 ? e.projection : Ul(e.parent);
}
function Qn(e, { forwardMotionProps: t = !1, type: n } = {}, i, s) {
  i && gp(i);
  const r = n ? n === "svg" : Ls(e), o = r ? Dp : Ep;
  function a(u, d) {
    let h;
    const f = {
      ...se(Rn),
      ...u,
      layoutId: Ip(u)
    }, { isStatic: p, isValidProp: g } = f, x = xp(u), b = o(u, p);
    if (!p && typeof window < "u") {
      Op(f, i);
      const w = Bp(f);
      h = w.MeasureLayout, x.visualElement = Lp(e, b, f, s, w.ProjectionNode, r);
    }
    return v(Ln.Provider, { value: x, children: [h && x.visualElement ? c(h, { visualElement: x.visualElement, ...f }) : null, Pp(e, u, Rp(b, x.visualElement, d), b, p, t, r, g)] });
  }
  a.displayName = `motion.${typeof e == "string" ? e : `create(${e.displayName ?? e.name ?? ""})`}`;
  const l = ji(a);
  return l[Vp] = e, l;
}
function Ip({ layoutId: e }) {
  const t = se(Zi).id;
  return t && e !== void 0 ? t + "-" + e : e;
}
function Op(e, t) {
  const n = se(Fl).strict;
  if (process.env.NODE_ENV !== "production" && t && n) {
    const i = "You have rendered a `motion` component within a `LazyMotion` component. This will break tree shaking. Import and render a `m` component instead.";
    e.ignoreStrict ? Je(!1, i, "lazy-strict-mode") : ye(!1, i, "lazy-strict-mode");
  }
}
function Bp(e) {
  const t = Il(), { drag: n, layout: i } = t;
  if (!n && !i)
    return {};
  const s = { ...n, ...i };
  return {
    MeasureLayout: n?.isEnabled(e) || i?.isEnabled(e) ? s.MeasureLayout : void 0,
    ProjectionNode: s.ProjectionNode
  };
}
function $p(e, t) {
  if (typeof Proxy > "u")
    return Qn;
  const n = /* @__PURE__ */ new Map(), i = (r, o) => Qn(r, o, e, t), s = (r, o) => (process.env.NODE_ENV !== "production" && Mn(!1, "motion() is deprecated. Use motion.create() instead."), i(r, o));
  return new Proxy(s, {
    /**
     * Called when `motion` is referenced with a prop: `motion.div`, `motion.input` etc.
     * The prop name is passed through as `key` and we can use that to generate a `motion`
     * DOM component with that name.
     */
    get: (r, o) => o === "create" ? i : (n.has(o) || n.set(o, Qn(o, void 0, e, t)), n.get(o))
  });
}
const jp = (e, t) => t.isSVG ?? Ls(e) ? new mh(t) : new hh(t, {
  allowProjection: e !== $i
});
class Up extends Ue {
  /**
   * We dynamically generate the AnimationState manager as it contains a reference
   * to the underlying animation library. We only want to load that if we load this,
   * so people can optionally code split it out using the `m` component.
   */
  constructor(t) {
    super(t), t.animationState || (t.animationState = bh(t));
  }
  updateAnimationControlsSubscription() {
    const { animate: t } = this.node.getProps();
    Dn(t) && (this.unmountControls = t.subscribe(this.node));
  }
  /**
   * Subscribe any provided AnimationControls to the component's VisualElement
   */
  mount() {
    this.updateAnimationControlsSubscription();
  }
  update() {
    const { animate: t } = this.node.getProps(), { animate: n } = this.node.prevProps || {};
    t !== n && this.updateAnimationControlsSubscription();
  }
  unmount() {
    this.node.animationState.reset(), this.unmountControls?.();
  }
}
let Wp = 0;
class _p extends Ue {
  constructor() {
    super(...arguments), this.id = Wp++, this.isExitComplete = !1;
  }
  update() {
    if (!this.node.presenceContext)
      return;
    const { isPresent: t, onExitComplete: n } = this.node.presenceContext, { isPresent: i } = this.node.prevPresenceContext || {};
    if (!this.node.animationState || t === i)
      return;
    if (t && i === !1) {
      if (this.isExitComplete) {
        const { initial: r, custom: o } = this.node.getProps();
        if (typeof r == "string" || typeof r == "object" && r !== null && !Array.isArray(r)) {
          const a = Xe(this.node, r, o);
          if (a) {
            const { transition: l, transitionEnd: u, ...d } = a;
            for (const h in d)
              this.node.getValue(h)?.jump(d[h]);
          }
        }
        this.node.animationState.reset(), this.node.animationState.animateChanges();
      } else
        this.node.animationState.setActive("exit", !1);
      this.isExitComplete = !1;
      return;
    }
    const s = this.node.animationState.setActive("exit", !t);
    n && !t && s.then(() => {
      this.isExitComplete = !0, n(this.id);
    });
  }
  mount() {
    const { register: t, onExitComplete: n } = this.node.presenceContext || {};
    n && n(this.id), t && (this.unmount = t(this.id));
  }
  unmount() {
  }
}
const zp = {
  animation: {
    Feature: Up
  },
  exit: {
    Feature: _p
  }
};
function Kt(e) {
  return {
    point: {
      x: e.pageX,
      y: e.pageY
    }
  };
}
const Gp = (e) => (t) => Cs(t) && e(t, Kt(t));
function Mt(e, t, n, i) {
  return It(e, t, Gp(n), i);
}
const Wl = ({ current: e }) => e ? e.ownerDocument.defaultView : null, uo = (e, t) => Math.abs(e - t);
function Kp(e, t) {
  const n = uo(e.x, t.x), i = uo(e.y, t.y);
  return Math.sqrt(n ** 2 + i ** 2);
}
const fo = /* @__PURE__ */ new Set(["auto", "scroll"]);
class _l {
  constructor(t, n, { transformPagePoint: i, contextWindow: s = window, dragSnapToOrigin: r = !1, distanceThreshold: o = 3, element: a } = {}) {
    if (this.startEvent = null, this.lastMoveEvent = null, this.lastMoveEventInfo = null, this.lastRawMoveEventInfo = null, this.handlers = {}, this.contextWindow = window, this.scrollPositions = /* @__PURE__ */ new Map(), this.removeScrollListeners = null, this.onElementScroll = (g) => {
      this.handleScroll(g.target);
    }, this.onWindowScroll = () => {
      this.handleScroll(window);
    }, this.updatePoint = () => {
      if (!(this.lastMoveEvent && this.lastMoveEventInfo))
        return;
      this.lastRawMoveEventInfo && (this.lastMoveEventInfo = Qt(this.lastRawMoveEventInfo, this.transformPagePoint));
      const g = Jn(this.lastMoveEventInfo, this.history), x = this.startEvent !== null, b = Kp(g.offset, { x: 0, y: 0 }) >= this.distanceThreshold;
      if (!x && !b)
        return;
      const { point: w } = g, { timestamp: T } = te;
      this.history.push({ ...w, timestamp: T });
      const { onStart: y, onMove: k } = this.handlers;
      x || (y && y(this.lastMoveEvent, g), this.startEvent = this.lastMoveEvent), k && k(this.lastMoveEvent, g);
    }, this.handlePointerMove = (g, x) => {
      this.lastMoveEvent = g, this.lastRawMoveEventInfo = x, this.lastMoveEventInfo = Qt(x, this.transformPagePoint), z.update(this.updatePoint, !0);
    }, this.handlePointerUp = (g, x) => {
      this.end();
      const { onEnd: b, onSessionEnd: w, resumeAnimation: T } = this.handlers;
      if ((this.dragSnapToOrigin || !this.startEvent) && T && T(), !(this.lastMoveEvent && this.lastMoveEventInfo))
        return;
      const y = Jn(g.type === "pointercancel" ? this.lastMoveEventInfo : Qt(x, this.transformPagePoint), this.history);
      this.startEvent && b && b(g, y), w && w(g, y);
    }, !Cs(t))
      return;
    this.dragSnapToOrigin = r, this.handlers = n, this.transformPagePoint = i, this.distanceThreshold = o, this.contextWindow = s || window;
    const l = Kt(t), u = Qt(l, this.transformPagePoint), { point: d } = u, { timestamp: h } = te;
    this.history = [{ ...d, timestamp: h }];
    const { onSessionStart: f } = n;
    f && f(t, Jn(u, this.history));
    const p = { passive: !0, capture: !0 };
    this.removeListeners = Wt(Mt(this.contextWindow, "pointermove", this.handlePointerMove, p), Mt(this.contextWindow, "pointerup", this.handlePointerUp, p), Mt(this.contextWindow, "pointercancel", this.handlePointerUp, p)), a && this.startScrollTracking(a);
  }
  /**
   * Start tracking scroll on ancestors and window.
   */
  startScrollTracking(t) {
    let n = t.parentElement;
    for (; n; ) {
      const i = getComputedStyle(n);
      (fo.has(i.overflowX) || fo.has(i.overflowY)) && this.scrollPositions.set(n, {
        x: n.scrollLeft,
        y: n.scrollTop
      }), n = n.parentElement;
    }
    this.scrollPositions.set(window, {
      x: window.scrollX,
      y: window.scrollY
    }), window.addEventListener("scroll", this.onElementScroll, {
      capture: !0
    }), window.addEventListener("scroll", this.onWindowScroll), this.removeScrollListeners = () => {
      window.removeEventListener("scroll", this.onElementScroll, {
        capture: !0
      }), window.removeEventListener("scroll", this.onWindowScroll);
    };
  }
  /**
   * Handle scroll compensation during drag.
   *
   * For element scroll: adjusts history origin since pageX/pageY doesn't change.
   * For window scroll: adjusts lastMoveEventInfo since pageX/pageY would change.
   */
  handleScroll(t) {
    const n = this.scrollPositions.get(t);
    if (!n)
      return;
    const i = t === window, s = i ? { x: window.scrollX, y: window.scrollY } : {
      x: t.scrollLeft,
      y: t.scrollTop
    }, r = { x: s.x - n.x, y: s.y - n.y };
    r.x === 0 && r.y === 0 || (i ? this.lastMoveEventInfo && (this.lastMoveEventInfo.point.x += r.x, this.lastMoveEventInfo.point.y += r.y) : this.history.length > 0 && (this.history[0].x -= r.x, this.history[0].y -= r.y), this.scrollPositions.set(t, s), z.update(this.updatePoint, !0));
  }
  updateHandlers(t) {
    this.handlers = t;
  }
  end() {
    this.removeListeners && this.removeListeners(), this.removeScrollListeners && this.removeScrollListeners(), this.scrollPositions.clear(), Ve(this.updatePoint);
  }
}
function Qt(e, t) {
  return t ? { point: t(e.point) } : e;
}
function ho(e, t) {
  return { x: e.x - t.x, y: e.y - t.y };
}
function Jn({ point: e }, t) {
  return {
    point: e,
    delta: ho(e, zl(t)),
    offset: ho(e, Hp(t)),
    velocity: qp(t, 0.1)
  };
}
function Hp(e) {
  return e[0];
}
function zl(e) {
  return e[e.length - 1];
}
function qp(e, t) {
  if (e.length < 2)
    return { x: 0, y: 0 };
  let n = e.length - 1, i = null;
  const s = zl(e);
  for (; n >= 0 && (i = e[n], !(s.timestamp - i.timestamp > /* @__PURE__ */ he(t))); )
    n--;
  if (!i)
    return { x: 0, y: 0 };
  i === e[0] && e.length > 2 && s.timestamp - i.timestamp > /* @__PURE__ */ he(t) * 2 && (i = e[1]);
  const r = /* @__PURE__ */ pe(s.timestamp - i.timestamp);
  if (r === 0)
    return { x: 0, y: 0 };
  const o = {
    x: (s.x - i.x) / r,
    y: (s.y - i.y) / r
  };
  return o.x === 1 / 0 && (o.x = 0), o.y === 1 / 0 && (o.y = 0), o;
}
function Yp(e, { min: t, max: n }, i) {
  return t !== void 0 && e < t ? e = i ? K(t, e, i.min) : Math.max(e, t) : n !== void 0 && e > n && (e = i ? K(n, e, i.max) : Math.min(e, n)), e;
}
function po(e, t, n) {
  return {
    min: t !== void 0 ? e.min + t : void 0,
    max: n !== void 0 ? e.max + n - (e.max - e.min) : void 0
  };
}
function Xp(e, { top: t, left: n, bottom: i, right: s }) {
  return {
    x: po(e.x, n, s),
    y: po(e.y, t, i)
  };
}
function mo(e, t) {
  let n = t.min - e.min, i = t.max - e.max;
  return t.max - t.min < e.max - e.min && ([n, i] = [i, n]), { min: n, max: i };
}
function Zp(e, t) {
  return {
    x: mo(e.x, t.x),
    y: mo(e.y, t.y)
  };
}
function Qp(e, t) {
  let n = 0.5;
  const i = ue(e), s = ue(t);
  return s > i ? n = /* @__PURE__ */ dt(t.min, t.max - i, e.min) : i > s && (n = /* @__PURE__ */ dt(e.min, e.max - s, t.min)), ke(0, 1, n);
}
function Jp(e, t) {
  const n = {};
  return t.min !== void 0 && (n.min = t.min - e.min), t.max !== void 0 && (n.max = t.max - e.min), n;
}
const Ri = 0.35;
function em(e = Ri) {
  return e === !1 ? e = 0 : e === !0 && (e = Ri), {
    x: go(e, "left", "right"),
    y: go(e, "top", "bottom")
  };
}
function go(e, t, n) {
  return {
    min: yo(e, t),
    max: yo(e, n)
  };
}
function yo(e, t) {
  return typeof e == "number" ? e : e[t] || 0;
}
const tm = /* @__PURE__ */ new WeakMap();
class nm {
  constructor(t) {
    this.openDragLock = null, this.isDragging = !1, this.currentDirection = null, this.originPoint = { x: 0, y: 0 }, this.constraints = !1, this.hasMutatedConstraints = !1, this.elastic = ee(), this.latestPointerEvent = null, this.latestPanInfo = null, this.visualElement = t;
  }
  start(t, { snapToCursor: n = !1, distanceThreshold: i } = {}) {
    const { presenceContext: s } = this.visualElement;
    if (s && s.isPresent === !1)
      return;
    const r = (h) => {
      n && this.snapToCursor(Kt(h).point), this.stopAnimation();
    }, o = (h, f) => {
      const { drag: p, dragPropagation: g, onDragStart: x } = this.getProps();
      if (p && !g && (this.openDragLock && this.openDragLock(), this.openDragLock = Wf(p), !this.openDragLock))
        return;
      this.latestPointerEvent = h, this.latestPanInfo = f, this.isDragging = !0, this.currentDirection = null, this.resolveConstraints(), this.visualElement.projection && (this.visualElement.projection.isAnimationBlocked = !0, this.visualElement.projection.target = void 0), Ae((w) => {
        let T = this.getAxisMotionValue(w).get() || 0;
        if (Pe.test(T)) {
          const { projection: y } = this.visualElement;
          if (y && y.layout) {
            const k = y.layout.layoutBox[w];
            k && (T = ue(k) * (parseFloat(T) / 100));
          }
        }
        this.originPoint[w] = T;
      }), x && z.update(() => x(h, f), !1, !0), Pi(this.visualElement, "transform");
      const { animationState: b } = this.visualElement;
      b && b.setActive("whileDrag", !0);
    }, a = (h, f) => {
      this.latestPointerEvent = h, this.latestPanInfo = f;
      const { dragPropagation: p, dragDirectionLock: g, onDirectionLock: x, onDrag: b } = this.getProps();
      if (!p && !this.openDragLock)
        return;
      const { offset: w } = f;
      if (g && this.currentDirection === null) {
        this.currentDirection = sm(w), this.currentDirection !== null && x && x(this.currentDirection);
        return;
      }
      this.updateAxis("x", f.point, w), this.updateAxis("y", f.point, w), this.visualElement.render(), b && z.update(() => b(h, f), !1, !0);
    }, l = (h, f) => {
      this.latestPointerEvent = h, this.latestPanInfo = f, this.stop(h, f), this.latestPointerEvent = null, this.latestPanInfo = null;
    }, u = () => {
      const { dragSnapToOrigin: h } = this.getProps();
      (h || this.constraints) && this.startAnimation({ x: 0, y: 0 });
    }, { dragSnapToOrigin: d } = this.getProps();
    this.panSession = new _l(t, {
      onSessionStart: r,
      onStart: o,
      onMove: a,
      onSessionEnd: l,
      resumeAnimation: u
    }, {
      transformPagePoint: this.visualElement.getTransformPagePoint(),
      dragSnapToOrigin: d,
      distanceThreshold: i,
      contextWindow: Wl(this.visualElement),
      element: this.visualElement.current
    });
  }
  /**
   * @internal
   */
  stop(t, n) {
    const i = t || this.latestPointerEvent, s = n || this.latestPanInfo, r = this.isDragging;
    if (this.cancel(), !r || !s || !i)
      return;
    const { velocity: o } = s;
    this.startAnimation(o);
    const { onDragEnd: a } = this.getProps();
    a && z.postRender(() => a(i, s));
  }
  /**
   * @internal
   */
  cancel() {
    this.isDragging = !1;
    const { projection: t, animationState: n } = this.visualElement;
    t && (t.isAnimationBlocked = !1), this.endPanSession();
    const { dragPropagation: i } = this.getProps();
    !i && this.openDragLock && (this.openDragLock(), this.openDragLock = null), n && n.setActive("whileDrag", !1);
  }
  /**
   * Clean up the pan session without modifying other drag state.
   * This is used during unmount to ensure event listeners are removed
   * without affecting projection animations or drag locks.
   * @internal
   */
  endPanSession() {
    this.panSession && this.panSession.end(), this.panSession = void 0;
  }
  updateAxis(t, n, i) {
    const { drag: s } = this.getProps();
    if (!i || !Jt(t, s, this.currentDirection))
      return;
    const r = this.getAxisMotionValue(t);
    let o = this.originPoint[t] + i[t];
    this.constraints && this.constraints[t] && (o = Yp(o, this.constraints[t], this.elastic[t])), r.set(o);
  }
  resolveConstraints() {
    const { dragConstraints: t, dragElastic: n } = this.getProps(), i = this.visualElement.projection && !this.visualElement.projection.layout ? this.visualElement.projection.measure(!1) : this.visualElement.projection?.layout, s = this.constraints;
    t && tt(t) ? this.constraints || (this.constraints = this.resolveRefConstraints()) : t && i ? this.constraints = Xp(i.layoutBox, t) : this.constraints = !1, this.elastic = em(n), s !== this.constraints && !tt(t) && i && this.constraints && !this.hasMutatedConstraints && Ae((r) => {
      this.constraints !== !1 && this.getAxisMotionValue(r) && (this.constraints[r] = Jp(i.layoutBox[r], this.constraints[r]));
    });
  }
  resolveRefConstraints() {
    const { dragConstraints: t, onMeasureDragConstraints: n } = this.getProps();
    if (!t || !tt(t))
      return !1;
    const i = t.current;
    ye(i !== null, "If `dragConstraints` is set as a React ref, that ref must be passed to another component's `ref` prop.", "drag-constraints-ref");
    const { projection: s } = this.visualElement;
    if (!s || !s.layout)
      return !1;
    s.root && (s.root.scroll = void 0, s.root.updateScroll());
    const r = If(i, s.root, this.visualElement.getTransformPagePoint());
    let o = Zp(s.layout.layoutBox, r);
    if (n) {
      const a = n(Rf(o));
      this.hasMutatedConstraints = !!a, a && (o = rl(a));
    }
    return o;
  }
  startAnimation(t) {
    const { drag: n, dragMomentum: i, dragElastic: s, dragTransition: r, dragSnapToOrigin: o, onDragTransitionEnd: a } = this.getProps(), l = this.constraints || {}, u = Ae((d) => {
      if (!Jt(d, n, this.currentDirection))
        return;
      let h = l && l[d] || {};
      (o === !0 || o === d) && (h = { min: 0, max: 0 });
      const f = s ? 200 : 1e6, p = s ? 40 : 1e7, g = {
        type: "inertia",
        velocity: i ? t[d] : 0,
        bounceStiffness: f,
        bounceDamping: p,
        timeConstant: 750,
        restDelta: 1,
        restSpeed: 10,
        ...r,
        ...h
      };
      return this.startAxisValueAnimation(d, g);
    });
    return Promise.all(u).then(a);
  }
  startAxisValueAnimation(t, n) {
    const i = this.getAxisMotionValue(t);
    return Pi(this.visualElement, t), i.start(En(t, i, 0, n, this.visualElement, !1));
  }
  stopAnimation() {
    Ae((t) => this.getAxisMotionValue(t).stop());
  }
  /**
   * Drag works differently depending on which props are provided.
   *
   * - If _dragX and _dragY are provided, we output the gesture delta directly to those motion values.
   * - Otherwise, we apply the delta to the x/y motion values.
   */
  getAxisMotionValue(t) {
    const n = `_drag${t.toUpperCase()}`, s = this.visualElement.getProps()[n];
    return s || this.visualElement.getValue(t, this.visualElement.latestValues[t] ?? 0);
  }
  snapToCursor(t) {
    Ae((n) => {
      const { drag: i } = this.getProps();
      if (!Jt(n, i, this.currentDirection))
        return;
      const { projection: s } = this.visualElement, r = this.getAxisMotionValue(n);
      if (s && s.layout) {
        const { min: o, max: a } = s.layout.layoutBox[n], l = r.get() || 0;
        r.set(t[n] - K(o, a, 0.5) + l);
      }
    });
  }
  /**
   * When the viewport resizes we want to check if the measured constraints
   * have changed and, if so, reposition the element within those new constraints
   * relative to where it was before the resize.
   */
  scalePositionWithinConstraints() {
    if (!this.visualElement.current)
      return;
    const { drag: t, dragConstraints: n } = this.getProps(), { projection: i } = this.visualElement;
    if (!tt(n) || !i || !this.constraints)
      return;
    this.stopAnimation();
    const s = { x: 0, y: 0 };
    Ae((o) => {
      const a = this.getAxisMotionValue(o);
      if (a && this.constraints !== !1) {
        const l = a.get();
        s[o] = Qp({ min: l, max: l }, this.constraints[o]);
      }
    });
    const { transformTemplate: r } = this.visualElement.getProps();
    this.visualElement.current.style.transform = r ? r({}, "") : "none", i.root && i.root.updateScroll(), i.updateLayout(), this.constraints = !1, this.resolveConstraints(), Ae((o) => {
      if (!Jt(o, t, null))
        return;
      const a = this.getAxisMotionValue(o), { min: l, max: u } = this.constraints[o];
      a.set(K(l, u, s[o]));
    }), this.visualElement.render();
  }
  addListeners() {
    if (!this.visualElement.current)
      return;
    tm.set(this.visualElement, this);
    const t = this.visualElement.current, n = Mt(t, "pointerdown", (u) => {
      const { drag: d, dragListener: h = !0 } = this.getProps(), f = u.target, p = f !== t && qf(f);
      d && h && !p && this.start(u);
    });
    let i;
    const s = () => {
      const { dragConstraints: u } = this.getProps();
      tt(u) && u.current && (this.constraints = this.resolveRefConstraints(), i || (i = im(t, u.current, () => this.scalePositionWithinConstraints())));
    }, { projection: r } = this.visualElement, o = r.addEventListener("measure", s);
    r && !r.layout && (r.root && r.root.updateScroll(), r.updateLayout()), z.read(s);
    const a = It(window, "resize", () => this.scalePositionWithinConstraints()), l = r.addEventListener("didUpdate", (({ delta: u, hasLayoutChanged: d }) => {
      this.isDragging && d && (Ae((h) => {
        const f = this.getAxisMotionValue(h);
        f && (this.originPoint[h] += u[h].translate, f.set(f.get() + u[h].translate));
      }), this.visualElement.render());
    }));
    return () => {
      a(), n(), o(), l && l(), i && i();
    };
  }
  getProps() {
    const t = this.visualElement.getProps(), { drag: n = !1, dragDirectionLock: i = !1, dragPropagation: s = !1, dragConstraints: r = !1, dragElastic: o = Ri, dragMomentum: a = !0 } = t;
    return {
      ...t,
      drag: n,
      dragDirectionLock: i,
      dragPropagation: s,
      dragConstraints: r,
      dragElastic: o,
      dragMomentum: a
    };
  }
}
function xo(e) {
  let t = !0;
  return () => {
    if (t) {
      t = !1;
      return;
    }
    e();
  };
}
function im(e, t, n) {
  const i = Er(e, xo(n)), s = Er(t, xo(n));
  return () => {
    i(), s();
  };
}
function Jt(e, t, n) {
  return (t === !0 || t === e) && (n === null || n === e);
}
function sm(e, t = 10) {
  let n = null;
  return Math.abs(e.y) > t ? n = "y" : Math.abs(e.x) > t && (n = "x"), n;
}
class rm extends Ue {
  constructor(t) {
    super(t), this.removeGroupControls = we, this.removeListeners = we, this.controls = new nm(t);
  }
  mount() {
    const { dragControls: t } = this.node.getProps();
    t && (this.removeGroupControls = t.subscribe(this.controls)), this.removeListeners = this.controls.addListeners() || we;
  }
  update() {
    const { dragControls: t } = this.node.getProps(), { dragControls: n } = this.node.prevProps || {};
    t !== n && (this.removeGroupControls(), t && (this.removeGroupControls = t.subscribe(this.controls)));
  }
  unmount() {
    this.removeGroupControls(), this.removeListeners(), this.controls.isDragging || this.controls.endPanSession();
  }
}
const ei = (e) => (t, n) => {
  e && z.update(() => e(t, n), !1, !0);
};
class om extends Ue {
  constructor() {
    super(...arguments), this.removePointerDownListener = we;
  }
  onPointerDown(t) {
    this.session = new _l(t, this.createPanHandlers(), {
      transformPagePoint: this.node.getTransformPagePoint(),
      contextWindow: Wl(this.node)
    });
  }
  createPanHandlers() {
    const { onPanSessionStart: t, onPanStart: n, onPan: i, onPanEnd: s } = this.node.getProps();
    return {
      onSessionStart: ei(t),
      onStart: ei(n),
      onMove: ei(i),
      onEnd: (r, o) => {
        delete this.session, s && z.postRender(() => s(r, o));
      }
    };
  }
  mount() {
    this.removePointerDownListener = Mt(this.node.current, "pointerdown", (t) => this.onPointerDown(t));
  }
  update() {
    this.session && this.session.updateHandlers(this.createPanHandlers());
  }
  unmount() {
    this.removePointerDownListener(), this.session && this.session.end();
  }
}
let ti = !1;
class am extends Sc {
  /**
   * This only mounts projection nodes for components that
   * need measuring, we might want to do it for all components
   * in order to incorporate transforms
   */
  componentDidMount() {
    const { visualElement: t, layoutGroup: n, switchLayoutGroup: i, layoutId: s } = this.props, { projection: r } = t;
    r && (n.group && n.group.add(r), i && i.register && s && i.register(r), ti && r.root.didUpdate(), r.addEventListener("animationComplete", () => {
      this.safeToRemove();
    }), r.setOptions({
      ...r.options,
      layoutDependency: this.props.layoutDependency,
      onExitComplete: () => this.safeToRemove()
    })), fn.hasEverUpdated = !0;
  }
  getSnapshotBeforeUpdate(t) {
    const { layoutDependency: n, visualElement: i, drag: s, isPresent: r } = this.props, { projection: o } = i;
    return o && (o.isPresent = r, t.layoutDependency !== n && o.setOptions({
      ...o.options,
      layoutDependency: n
    }), ti = !0, s || t.layoutDependency !== n || n === void 0 || t.isPresent !== r ? o.willUpdate() : this.safeToRemove(), t.isPresent !== r && (r ? o.promote() : o.relegate() || z.postRender(() => {
      const a = o.getStack();
      (!a || !a.members.length) && this.safeToRemove();
    }))), null;
  }
  componentDidUpdate() {
    const { visualElement: t, layoutAnchor: n } = this.props, { projection: i } = t;
    i && (i.options.layoutAnchor = n, i.root.didUpdate(), Ms.postRender(() => {
      !i.currentAnimation && i.isLead() && this.safeToRemove();
    }));
  }
  componentWillUnmount() {
    const { visualElement: t, layoutGroup: n, switchLayoutGroup: i } = this.props, { projection: s } = t;
    ti = !0, s && (s.scheduleCheckAfterUnmount(), n && n.group && n.group.remove(s), i && i.deregister && i.deregister(s));
  }
  safeToRemove() {
    const { safeToRemove: t } = this.props;
    t && t();
  }
  render() {
    return null;
  }
}
function Gl(e) {
  const [t, n] = Ll(), i = se(Zi);
  return c(am, { ...e, layoutGroup: i, switchLayoutGroup: se(jl), isPresent: t, safeToRemove: n });
}
const lm = {
  pan: {
    Feature: om
  },
  drag: {
    Feature: rm,
    ProjectionNode: Rl,
    MeasureLayout: Gl
  }
};
function vo(e, t, n) {
  const { props: i } = e;
  e.animationState && i.whileHover && e.animationState.setActive("whileHover", n === "Start");
  const s = "onHover" + n, r = i[s];
  r && z.postRender(() => r(t, Kt(t)));
}
class cm extends Ue {
  mount() {
    const { current: t } = this.node;
    t && (this.unmount = zf(t, (n, i) => (vo(this.node, i, "Start"), (s) => vo(this.node, s, "End"))));
  }
  unmount() {
  }
}
class um extends Ue {
  constructor() {
    super(...arguments), this.isActive = !1;
  }
  onFocus() {
    let t = !1;
    try {
      t = this.node.current.matches(":focus-visible");
    } catch {
      t = !0;
    }
    !t || !this.node.animationState || (this.node.animationState.setActive("whileFocus", !0), this.isActive = !0);
  }
  onBlur() {
    !this.isActive || !this.node.animationState || (this.node.animationState.setActive("whileFocus", !1), this.isActive = !1);
  }
  mount() {
    this.unmount = Wt(It(this.node.current, "focus", () => this.onFocus()), It(this.node.current, "blur", () => this.onBlur()));
  }
  unmount() {
  }
}
function bo(e, t, n) {
  const { props: i } = e;
  if (e.current instanceof HTMLButtonElement && e.current.disabled)
    return;
  e.animationState && i.whileTap && e.animationState.setActive("whileTap", n === "Start");
  const s = "onTap" + (n === "End" ? "" : n), r = i[s];
  r && z.postRender(() => r(t, Kt(t)));
}
class dm extends Ue {
  mount() {
    const { current: t } = this.node;
    if (!t)
      return;
    const { globalTapTarget: n, propagate: i } = this.node.props;
    this.unmount = Xf(t, (s, r) => (bo(this.node, r, "Start"), (o, { success: a }) => bo(this.node, o, a ? "End" : "Cancel")), {
      useGlobalTarget: n,
      stopPropagation: i?.tap === !1
    });
  }
  unmount() {
  }
}
const Li = /* @__PURE__ */ new WeakMap(), ni = /* @__PURE__ */ new WeakMap(), fm = (e) => {
  const t = Li.get(e.target);
  t && t(e);
}, hm = (e) => {
  e.forEach(fm);
};
function pm({ root: e, ...t }) {
  const n = e || document;
  ni.has(n) || ni.set(n, {});
  const i = ni.get(n), s = JSON.stringify(t);
  return i[s] || (i[s] = new IntersectionObserver(hm, { root: e, ...t })), i[s];
}
function mm(e, t, n) {
  const i = pm(t);
  return Li.set(e, n), i.observe(e), () => {
    Li.delete(e), i.unobserve(e);
  };
}
const gm = {
  some: 0,
  all: 1
};
class ym extends Ue {
  constructor() {
    super(...arguments), this.hasEnteredView = !1, this.isInView = !1;
  }
  startObserver() {
    this.stopObserver?.();
    const { viewport: t = {} } = this.node.getProps(), { root: n, margin: i, amount: s = "some", once: r } = t, o = {
      root: n ? n.current : void 0,
      rootMargin: i,
      threshold: typeof s == "number" ? s : gm[s]
    }, a = (l) => {
      const { isIntersecting: u } = l;
      if (this.isInView === u || (this.isInView = u, r && !u && this.hasEnteredView))
        return;
      u && (this.hasEnteredView = !0), this.node.animationState && this.node.animationState.setActive("whileInView", u);
      const { onViewportEnter: d, onViewportLeave: h } = this.node.getProps(), f = u ? d : h;
      f && f(l);
    };
    this.stopObserver = mm(this.node.current, o, a);
  }
  mount() {
    this.startObserver();
  }
  update() {
    if (typeof IntersectionObserver > "u")
      return;
    const { props: t, prevProps: n } = this.node;
    ["amount", "margin", "root"].some(xm(t, n)) && this.startObserver();
  }
  unmount() {
    this.stopObserver?.(), this.hasEnteredView = !1, this.isInView = !1;
  }
}
function xm({ viewport: e = {} }, { viewport: t = {} } = {}) {
  return (n) => e[n] !== t[n];
}
const vm = {
  inView: {
    Feature: ym
  },
  tap: {
    Feature: dm
  },
  focus: {
    Feature: um
  },
  hover: {
    Feature: cm
  }
}, bm = {
  layout: {
    ProjectionNode: Rl,
    MeasureLayout: Gl
  }
}, wm = {
  ...zp,
  ...vm,
  ...lm,
  ...bm
}, km = /* @__PURE__ */ $p(wm, jp);
function Kl(e) {
  const t = jt(() => Re(e)), { isStatic: n } = se(Rn);
  if (n) {
    const [, i] = O(e);
    F(() => t.on("change", i), []);
  }
  return t;
}
function Hl(e, t) {
  const n = Kl(t()), i = () => n.set(t());
  return i(), Dt(() => {
    const s = () => z.preRender(i, !1, !0), r = e.map((o) => o.on("change", s));
    return () => {
      r.forEach((o) => o()), Ve(i);
    };
  }), n;
}
function Tm(e) {
  At.current = [], e();
  const t = Hl(At.current, e);
  return At.current = void 0, t;
}
function Sm(e, t, n, i) {
  if (typeof e == "function")
    return Tm(e);
  const r = typeof t == "function" ? t : oh(t, n, i), o = Array.isArray(e) ? wo(e, r) : wo([e], ([l]) => r(l)), a = Array.isArray(e) ? void 0 : e.accelerate;
  return a && !a.isTransformed && typeof t != "function" && Array.isArray(n) && i?.clamp !== !1 && (o.accelerate = {
    ...a,
    times: t,
    keyframes: n,
    isTransformed: !0
  }), o;
}
function wo(e, t) {
  const n = jt(() => []);
  return Hl(e, () => {
    n.length = 0;
    const i = e.length;
    for (let s = 0; s < i; s++)
      n[s] = e[s].get();
    return t(n);
  });
}
function Q() {
  !Ds.current && pl();
  const [e] = O(kn.current);
  return process.env.NODE_ENV !== "production" && Mn(e !== !0, "You have Reduced Motion enabled on your device. Animations may not appear as expected.", "reduced-motion-disabled"), e;
}
function Fs(e) {
  return typeof e == "object" && !Array.isArray(e);
}
function ql(e, t, n, i) {
  return e == null ? [] : typeof e == "string" && Fs(t) ? ks(e, n, i) : e instanceof NodeList ? Array.from(e) : Array.isArray(e) ? e.filter((s) => s != null) : [e];
}
function Am(e, t, n) {
  return e * (t + 1) + n * t;
}
function ko(e, t, n, i) {
  return typeof t == "number" ? t : t.startsWith("-") || t.startsWith("+") ? Math.max(0, e + parseFloat(t)) : t === "<" ? n : t.startsWith("<") ? Math.max(0, n + parseFloat(t.slice(1))) : i.get(t) ?? e;
}
function Nm(e, t, n) {
  for (let i = 0; i < e.length; i++) {
    const s = e[i];
    s.at > t && s.at < n && (Ze(e, s), i--);
  }
}
function Pm(e, t, n, i, s, r) {
  Nm(e, s, r);
  for (let o = 0; o < t.length; o++)
    e.push({
      value: t[o],
      at: K(s, r, i[o]),
      easing: /* @__PURE__ */ pa(n, o)
    });
}
function Mm(e, t, n = 0) {
  const i = t + 1 + t * n;
  for (let s = 0; s < e.length; s++)
    e[s] = e[s] / i;
}
function Cm(e, t) {
  return e.at === t.at ? e.value === null ? 1 : t.value === null ? -1 : 0 : e.at - t.at;
}
const Em = "easeInOut", ii = 20;
function Dm(e, { defaultTransition: t = {}, ...n } = {}, i, s) {
  const r = t.duration || 0.3, o = /* @__PURE__ */ new Map(), a = /* @__PURE__ */ new Map(), l = {}, u = /* @__PURE__ */ new Map();
  let d = 0, h = 0, f = 0;
  for (let p = 0; p < e.length; p++) {
    const g = e[p];
    if (typeof g == "string") {
      u.set(g, h);
      continue;
    } else if (!Array.isArray(g)) {
      u.set(g.name, ko(h, g.at, d, u));
      continue;
    }
    let [x, b, w = {}] = g;
    w.at !== void 0 && (h = ko(h, w.at, d, u));
    let T = 0;
    const y = (k, E, P, S = 0, m = 0) => {
      const N = Vm(k), { delay: A = 0, times: L = Va(N), type: I = t.type || "keyframes", repeat: j, repeatType: C, repeatDelay: re = 0, ...ce } = E;
      let { ease: oe = t.ease || "easeOut", duration: W } = E;
      const J = typeof A == "function" ? A(S, m) : A, H = N.length, D = gs(I) ? I : s?.[I || "keyframes"];
      if (H <= 2 && D) {
        let We = 100;
        if (H === 2 && Fm(N)) {
          const gt = N[1] - N[0];
          We = Math.abs(gt);
        }
        const Ce = {
          ...t,
          ...ce
        };
        W !== void 0 && (Ce.duration = /* @__PURE__ */ he(W));
        const Ht = Pa(Ce, We, D);
        oe = Ht.ease, W = Ht.duration;
      }
      W ?? (W = r);
      const _ = h + J;
      L.length === 1 && L[0] === 0 && (L[1] = 1);
      const Z = L.length - N.length;
      if (Z > 0 && Da(L, Z), N.length === 1 && N.unshift(null), j && Je(j < ii, `Sequence segments can't repeat ${j} times — ignoring repeat option. Use a value below ${ii} or apply repeat at the sequence level instead.`), j && j < ii) {
        const We = W > 0 ? re / W : 0;
        W = Am(W, j, re);
        const Ce = [...N], Ht = [...L];
        oe = Array.isArray(oe) ? [...oe] : [oe];
        const gt = [...oe], Us = C === "reverse" || C === "mirror";
        let Ws = Ce, _s = gt;
        Us && (Ws = [...Ce].reverse(), C === "reverse" && (_s = [...gt].reverse().map((Oe) => typeof Oe == "function" ? /* @__PURE__ */ ns(Oe) : Oe)));
        for (let Oe = 0; Oe < j; Oe++) {
          const zs = Us && Oe % 2 === 0, Gs = zs ? Ws : Ce, bc = zs ? _s : gt, Ks = (Oe + 1) * (1 + We);
          We > 0 && (N.push(N[N.length - 1]), L.push(Ks), oe.push("linear")), N.push(...Gs);
          for (let yt = 0; yt < Gs.length; yt++)
            L.push(Ht[yt] + Ks), oe.push(yt === 0 ? "linear" : /* @__PURE__ */ pa(bc, yt - 1));
        }
        Mm(L, j, We);
      }
      const Ie = _ + W;
      Pm(P, N, oe, L, _, Ie), T = Math.max(J + W, T), f = Math.max(Ie, f);
    };
    if (ie(x)) {
      const k = To(x, a);
      y(b, w, So("default", k));
    } else {
      const k = ql(x, b, i, l), E = k.length;
      for (let P = 0; P < E; P++) {
        b = b, w = w;
        const S = k[P], m = To(S, a);
        for (const N in b)
          y(b[N], Rm(w, N), So(N, m), P, E);
      }
    }
    d = h, h += T;
  }
  return a.forEach((p, g) => {
    for (const x in p) {
      const b = p[x];
      b.sort(Cm);
      const w = [], T = [], y = [];
      for (let S = 0; S < b.length; S++) {
        const { at: m, value: N, easing: A } = b[S];
        w.push(N), T.push(/* @__PURE__ */ dt(0, f, m)), y.push(A || "easeOut");
      }
      T[0] !== 0 && (T.unshift(0), w.unshift(w[0]), y.unshift(Em)), T[T.length - 1] !== 1 && (T.push(1), w.push(null)), o.has(g) || o.set(g, {
        keyframes: {},
        transition: {}
      });
      const k = o.get(g);
      k.keyframes[x] = w;
      const { type: E, ...P } = t;
      k.transition[x] = {
        ...P,
        duration: f,
        ease: y,
        times: T,
        ...n
      };
    }
  }), o;
}
function To(e, t) {
  return !t.has(e) && t.set(e, {}), t.get(e);
}
function So(e, t) {
  return t[e] || (t[e] = []), t[e];
}
function Vm(e) {
  return Array.isArray(e) ? e : [e];
}
function Rm(e, t) {
  return e && e[t] ? {
    ...e,
    ...e[t]
  } : { ...e };
}
const Lm = (e) => typeof e == "number", Fm = (e) => e.every(Lm);
function Im(e, t) {
  return ie(e) || typeof e == "number" || typeof e == "string" && !Fs(t);
}
function Yl(e, t, n, i) {
  const s = [];
  if (Im(e, t))
    s.push(Cl(e, Fs(t) && t.default || t, n && (n.default || n)));
  else {
    if (e == null)
      return s;
    const r = ql(e, t, i), o = r.length;
    ye(!!o, "No valid elements provided.", "no-valid-elements");
    for (let a = 0; a < o; a++) {
      const l = r[a], u = { ...n };
      "delay" in u && typeof u.delay == "function" && (u.delay = u.delay(a, o)), l instanceof Element ? s.push(...jf(l, t, u, fl.get(l))) : s.push(...tl(pf(l) ?? Uf, l, t, u));
    }
  }
  return s;
}
function Om(e, t, n) {
  const i = [], s = e.map((o) => {
    if (Array.isArray(o) && typeof o[0] == "function") {
      const a = o[0], l = Re(0);
      return l.on("change", a), o.length === 1 ? [l, [0, 1]] : o.length === 2 ? [l, [0, 1], o[1]] : [l, o[1], o[2]];
    }
    return o;
  });
  return Dm(s, t, n, { spring: Lt }).forEach(({ keyframes: o, transition: a }, l) => {
    i.push(...Yl(l, o, a));
  }), i;
}
function Bm(e) {
  return Array.isArray(e) && e.some(Array.isArray);
}
function $m(e = {}) {
  const { scope: t, reduceMotion: n, skipAnimations: i } = e;
  function s(r, o, a) {
    let l = [], u;
    const d = {};
    if (n !== void 0 && (d.reduceMotion = n), i !== void 0 && (d.skipAnimations = i), Bm(r)) {
      const { onComplete: f, ...p } = o || {};
      typeof f == "function" && (u = f), l = Om(r, { ...d, ...p }, t);
    } else {
      const { onComplete: f, ...p } = a || {};
      typeof f == "function" && (u = f), l = Yl(r, o, { ...d, ...p }, t);
    }
    const h = new $d(l);
    return u && h.finished.then(u), t && (t.animations.push(h), h.finished.then(() => {
      Ze(t.animations, h);
    })), h;
  }
  return s;
}
const si = Object.assign($m(), {
  /**
   * Register an effect so `animate()` can animate the subjects it
   * claims, for instance `animate.addEffect(threeEffect)`. The most
   * recently added effect is tested first. DOM elements are always
   * animated directly.
   */
  addEffect: hf,
  removeEffect: Ja
}), B = km;
function Ot(e) {
  return `REV ${String(Math.max(0, e ?? 0)).padStart(2, "0")}`;
}
function jm(e, t) {
  if (!e) return null;
  const n = e.replace(/^claude-/, "");
  return t ? `${n} ${t}` : n;
}
function Xl(e) {
  if (e == null) return null;
  const t = Math.max(0, Math.round(e));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function Fn(e) {
  const t = Math.max(0, e);
  return t < 59.95 ? `${t.toFixed(1)}s` : Xl(t);
}
function Um(e, t = Date.now()) {
  if (!e) return null;
  const n = Math.max(0, Math.round((t - new Date(e).getTime()) / 1e3));
  if (n < 60) return "just now";
  const i = Math.round(n / 60);
  if (i < 60) return `${i}m ago`;
  const s = Math.round(i / 60);
  if (s < 24) return `${s}h ago`;
  const r = Math.round(s / 24);
  if (r < 7) return `${r}d ago`;
  const o = Math.round(r / 7);
  return o < 8 ? `${o}w ago` : `${Math.round(r / 30)}mo ago`;
}
function Wm(e) {
  return !e || e.length !== 3 ? null : e.map((t) => Math.round(t * 10) / 10).join(" × ");
}
function vy(e) {
  if (!e) return "·";
  if (e.includes("@")) return e.split("@")[0].slice(0, 2).toUpperCase();
  const t = e.trim().split(/\s+/);
  return (t.length > 1 ? t[0][0] + t[1][0] : t[0].slice(0, 2)).toUpperCase();
}
const _m = typeof window > "u" ? F : $t, zm = Y.out;
function Is(e) {
  const t = M(null), [n, i] = O(0), [s, r] = O(!1), [o, a] = O(e), l = M(e);
  l.current !== e && (l.current = e, o && a(!1)), _m(() => {
    const d = t.current;
    if (!d) return;
    const h = () => {
      const p = d.getBoundingClientRect().height;
      i((g) => Math.abs(g - p) < 0.5 ? g : p);
    };
    if (h(), r(!0), typeof ResizeObserver > "u") return;
    const f = new ResizeObserver(h);
    return f.observe(d), () => f.disconnect();
  }, []);
  const u = Q();
  return {
    ref: t,
    height: n,
    animate: { height: e ? o || !s ? "auto" : n : 0 },
    transition: { duration: u ? 0 : U.settle, ease: zm },
    onAnimationComplete: () => {
      e && a(!0);
    },
    style: { overflow: "hidden" }
  };
}
const Gm = {
  done: "check",
  failed: "warning",
  running: "ruler"
};
function Nn(e, t) {
  return e.status !== "running" ? e.elapsed_s ?? 0 : Math.max(0, (t - new Date(e.started_at).getTime()) / 1e3);
}
function Km({ startedAt: e, className: t }) {
  const [n, i] = O(() => Date.now());
  F(() => {
    const r = setInterval(() => i(Date.now()), 100);
    return () => clearInterval(r);
  }, []);
  const s = Math.max(0, (n - new Date(e).getTime()) / 1e3);
  return /* @__PURE__ */ c("span", { "aria-hidden": "true", className: t, children: Fn(s) });
}
function Zl({ open: e }) {
  const t = Q() === !0;
  return /* @__PURE__ */ c(
    B.span,
    {
      "aria-hidden": "true",
      className: "flex shrink-0 items-center text-faint",
      animate: { rotate: e ? 0 : -90 },
      transition: { duration: t ? 0 : U.tick, ease: Y.out },
      children: /* @__PURE__ */ c($, { name: "chevron-down" })
    }
  );
}
function Ql({ open: e, id: t, className: n, children: i }) {
  const s = Is(e);
  return /* @__PURE__ */ c(B.div, { id: t, style: s.style, animate: s.animate, transition: s.transition, onAnimationComplete: s.onAnimationComplete, children: /* @__PURE__ */ c("div", { ref: s.ref, className: n, children: e ? i : null }) });
}
function Hm(e) {
  const t = `${e.verb.charAt(0).toUpperCase()}${e.verb.slice(1)} ${e.object}`;
  if (e.status === "running")
    return `${t}, running for ${Math.round(Nn(e, Date.now()))} seconds`;
  const n = Nn(e, Date.now()).toFixed(1);
  return `${t}, ${e.status === "failed" ? "failed after" : "finished in"} ${n} seconds`;
}
function Jl({ step: e, defaultOpen: t }) {
  const [n, i] = O(t ?? e.status === "failed");
  F(() => {
    e.status === "failed" && i(!0);
  }, [e.status]);
  const s = Se(), r = e.status === "running", o = e.status === "failed", a = e.input == null ? null : JSON.stringify(e.input, null, 2), l = e.output?.trim() ? e.output : null, u = a != null || l != null;
  return /* @__PURE__ */ v("div", { className: "flex flex-col", children: [
    /* @__PURE__ */ v(
      "button",
      {
        type: "button",
        onClick: u ? () => i((d) => !d) : void 0,
        "aria-expanded": u ? n : void 0,
        "aria-controls": u ? s : void 0,
        className: R(
          "flex min-h-[28px] w-full items-center gap-2 rounded-[3px] px-2 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          o ? "bg-fail-wash" : r ? "bg-accent-wash" : "bg-transparent",
          u && !o && !r && "hover:bg-raised",
          !u && "cursor-default"
        ),
        children: [
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: R("flex shrink-0 items-center", o ? "text-fail" : "text-ink-soft"), children: /* @__PURE__ */ c($, { name: Gm[e.status] }) }),
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: R("mono-label shrink-0", o ? "text-fail" : "text-muted"), children: e.verb.toUpperCase() }),
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "min-w-0 flex-1 truncate text-[13px] leading-[19px] text-ink-soft", children: e.object }),
          r ? /* @__PURE__ */ c(Km, { startedAt: e.started_at, className: "mono-value min-w-[44px] shrink-0 text-right tabular-nums text-accent-ink" }) : /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "mono-value min-w-[44px] shrink-0 text-right tabular-nums text-faint", children: Fn(Nn(e, Date.now())) }),
          u ? /* @__PURE__ */ c(Zl, { open: n }) : null,
          /* @__PURE__ */ c("span", { className: "sr-only", children: Hm(e) })
        ]
      }
    ),
    /* @__PURE__ */ v(Ql, { open: n && u, id: s, className: "relative flex flex-col gap-1.5 pt-1.5 pr-2 pb-2.5 pl-7", children: [
      /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "absolute top-0 bottom-0 left-[13px] w-px bg-line-soft" }),
      a ? /* @__PURE__ */ v("div", { className: "flex flex-col gap-1", children: [
        /* @__PURE__ */ c("span", { className: "mono-label text-muted", children: "INPUT" }),
        /* @__PURE__ */ c("pre", { className: "max-h-[216px] overflow-y-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap text-ink-soft", children: a })
      ] }) : null,
      l ? /* @__PURE__ */ v("div", { className: "flex flex-col gap-1", children: [
        /* @__PURE__ */ c("span", { className: "mono-label text-muted", children: "OUTPUT" }),
        /* @__PURE__ */ c("pre", { className: "max-h-[216px] overflow-y-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap text-ink-soft", children: l })
      ] }) : null
    ] })
  ] });
}
function qm(e) {
  const t = [];
  let n = [];
  const i = () => {
    n.length >= 3 ? t.push({ kind: "group", steps: n }) : n.forEach((s) => t.push({ kind: "step", step: s })), n = [];
  };
  for (const s of e) {
    if (s.status === "done") {
      n.push(s);
      continue;
    }
    i(), t.push({ kind: "step", step: s });
  }
  return i(), t;
}
function Ym({ steps: e, defaultCollapsed: t }) {
  const [n, i] = O(!t), s = Se();
  F(() => {
    t && i(!1);
  }, [t]);
  const r = e.reduce((o, a) => o + Nn(a, Date.now()), 0);
  return /* @__PURE__ */ v("div", { className: "flex flex-col", children: [
    /* @__PURE__ */ v(
      "button",
      {
        type: "button",
        onClick: () => i((o) => !o),
        "aria-expanded": n,
        "aria-controls": s,
        className: "flex min-h-[28px] items-center gap-2 self-start rounded-[3px] px-2 hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
        children: [
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "flex shrink-0 items-center text-ink-soft", children: /* @__PURE__ */ c($, { name: "dots" }) }),
          /* @__PURE__ */ v("span", { className: "mono-label text-muted", children: [
            e.length,
            " STEPS"
          ] }),
          /* @__PURE__ */ v("span", { className: "mono-value text-faint", children: [
            /* @__PURE__ */ c("span", { "aria-hidden": "true", children: "· " }),
            Fn(r)
          ] }),
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "ml-1.5 flex items-center", children: /* @__PURE__ */ c(Zl, { open: n }) })
        ]
      }
    ),
    /* @__PURE__ */ c(Ql, { open: n, id: s, className: "flex flex-col gap-[2px]", children: e.map((o) => /* @__PURE__ */ c(Jl, { step: o }, o.id)) })
  ] });
}
function Xm({ steps: e, defaultCollapsed: t = !0 }) {
  return /* @__PURE__ */ c("div", { className: "flex flex-col gap-[2px]", children: qm(e).map(
    (n) => n.kind === "group" ? /* @__PURE__ */ c(Ym, { steps: n.steps, defaultCollapsed: t }, n.steps[0].id) : /* @__PURE__ */ c(Jl, { step: n.step }, n.step.id)
  ) });
}
function Zm({ findings: e, passed: t }) {
  const n = e.filter((r) => r.severity === "fail"), i = e.filter((r) => r.severity === "warn"), s = t ? i : [...n, ...i];
  return /* @__PURE__ */ v("ul", { className: "flex flex-col gap-[5px]", role: "list", children: [
    t ? /* @__PURE__ */ v("li", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ c("span", { className: "text-pass", children: /* @__PURE__ */ c($, { name: "check" }) }),
      /* @__PURE__ */ c("span", { className: "mono-id text-ink-soft uppercase [letter-spacing:0.06em]", children: "Checks pass" })
    ] }) : n.length > 0 ? /* @__PURE__ */ v("li", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ c("span", { className: "text-fail", children: /* @__PURE__ */ c($, { name: "xmark" }) }),
      /* @__PURE__ */ v("span", { className: "mono-id text-ink-soft uppercase [letter-spacing:0.06em]", children: [
        n.length,
        " check",
        n.length === 1 ? "" : "s",
        " failed"
      ] })
    ] }) : null,
    s.map((r, o) => /* @__PURE__ */ v("li", { className: "flex items-baseline gap-2", children: [
      /* @__PURE__ */ c("span", { className: R("flex h-[14px] items-center", r.severity === "fail" ? "text-fail" : "text-warn"), children: /* @__PURE__ */ c($, { name: "warning" }) }),
      /* @__PURE__ */ c("span", { className: "mono-id shrink-0 text-ink-soft uppercase [letter-spacing:0.06em]", children: r.label || r.rule }),
      /* @__PURE__ */ c("span", { className: "min-w-0 text-xs leading-[14px] text-muted", children: r.message })
    ] }, `${r.rule}-${o}`))
  ] });
}
function Qm({ startedAt: e }) {
  const [t, n] = O(() => Date.now());
  return F(() => {
    const i = setInterval(() => n(Date.now()), 100);
    return () => clearInterval(i);
  }, []), /* @__PURE__ */ c(G, { children: Fn(Math.max(0, (t - new Date(e).getTime()) / 1e3)) });
}
function by({ build: e, collapsed: t }) {
  const n = e.status === "running", i = e.status === "passed", s = n ? "Building" : i ? "Built" : "Failed", r = e.status === "error" ? e.error?.trim().split(`
`).pop() || "Something broke on my end." : null, o = [
    e.revision != null ? Ot(e.revision) : null,
    n ? /* @__PURE__ */ c(Qm, { startedAt: e.started_at }, "clock") : e.elapsed_s != null ? Xl(e.elapsed_s) : null
  ].filter((a) => a != null);
  return /* @__PURE__ */ v("div", { className: "flex flex-col overflow-hidden rounded-[6px] border border-line", children: [
    /* @__PURE__ */ v("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3", children: [
      /* @__PURE__ */ v("span", { className: "mono-label flex items-center gap-2 text-ink", children: [
        i ? /* @__PURE__ */ c("span", { className: "text-pass", children: /* @__PURE__ */ c($, { name: "check" }) }) : n ? null : /* @__PURE__ */ c("span", { className: "text-fail", children: /* @__PURE__ */ c($, { name: "xmark" }) }),
        s
      ] }),
      /* @__PURE__ */ c("span", { className: "mono-caption text-muted [letter-spacing:0.06em]", children: o.map((a, l) => /* @__PURE__ */ v("span", { children: [
        l > 0 ? " · " : "",
        a
      ] }, l)) })
    ] }),
    /* @__PURE__ */ v("div", { className: "flex flex-col gap-[9px] px-3 pt-2.5 pb-3", children: [
      e.steps.length > 0 ? /* @__PURE__ */ c(Xm, { steps: e.steps, defaultCollapsed: t ?? i }) : null,
      !n && e.render_url ? /* @__PURE__ */ c(
        "img",
        {
          src: e.render_url,
          alt: `${e.part_name} from four sides`,
          className: "w-full rounded-[4px] border border-line-soft bg-raised"
        }
      ) : null,
      !n && e.findings.length > 0 ? /* @__PURE__ */ c(Zm, { findings: e.findings, passed: i }) : null,
      r ? /* @__PURE__ */ c("p", { className: "text-[13px] leading-[19px] text-ink-soft", children: r }) : null
    ] })
  ] });
}
const Jm = ["img"], eg = {
  p: ({ node: e, ...t }) => /* @__PURE__ */ c("p", { className: "text-pretty [&:not(:first-child)]:mt-2", ...t }),
  ol: ({ node: e, ...t }) => /* @__PURE__ */ c("ol", { className: "mt-2 list-decimal space-y-2 pl-7 marker:font-mono marker:text-[11px] marker:text-accent-ink", ...t }),
  ul: ({ node: e, ...t }) => /* @__PURE__ */ c("ul", { className: "mt-2 list-disc space-y-2 pl-7 marker:text-faint", ...t }),
  strong: ({ node: e, ...t }) => /* @__PURE__ */ c("strong", { className: "font-semibold text-ink", ...t }),
  // A fenced block is a <pre> around a <code>; the pre resets the pill so the
  // block reads as one surface. The className merge keeps react-markdown's
  // language-* class, which it sets on fenced code only.
  pre: ({ node: e, ...t }) => /* @__PURE__ */ c("pre", { className: "mt-2 overflow-x-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] text-ink-soft [&_code]:rounded-none [&_code]:bg-transparent [&_code]:px-0 [&_code]:text-[inherit]", ...t }),
  code: ({ node: e, className: t, ...n }) => /* @__PURE__ */ c("code", { className: R("rounded-[3px] bg-raised px-1 font-mono text-[0.85em] text-ink", t), ...n }),
  a: ({ node: e, ...t }) => /* @__PURE__ */ c("a", { className: "underline decoration-1 underline-offset-[3px] hover:text-accent-ink", target: "_blank", rel: "noreferrer", ...t })
};
function wy({ content: e, streaming: t = !1 }) {
  return /* @__PURE__ */ c("div", { className: R(t && "md-streaming"), children: /* @__PURE__ */ c(
    Ac,
    {
      skipHtml: !0,
      disallowedElements: Jm,
      components: eg,
      children: e
    }
  ) });
}
const tg = {
  standard: "Standard",
  measured: "Measured",
  asked: "Asked",
  doctrine: "Doctrine"
};
function ng(e) {
  if (e.source) return e.source;
  const t = e.how.toLowerCase();
  return /\b(caliper|measured|ruler|tape)\b/.test(t) ? "measured" : /\b(user|stated|asked|said|told)\b/.test(t) ? "asked" : /\b(standard|spec|published|listing|datasheet|nominal)\b/.test(t) ? "standard" : "doctrine";
}
function ig(e) {
  return /^[a-z][a-z0-9_]*$/.test(e.trim()) ? e.trim() : "assert";
}
function Ao({ children: e }) {
  return /* @__PURE__ */ v("div", { className: "flex items-center gap-2", children: [
    /* @__PURE__ */ c("span", { className: "mono-caption shrink-0 text-faint [letter-spacing:0.12em]", children: e }),
    /* @__PURE__ */ c("span", { className: "h-px flex-1 bg-line-soft" })
  ] });
}
function ky({ spec: e, model: t, effort: n }) {
  const i = jm(t, n);
  return /* @__PURE__ */ v("div", { className: "flex flex-col overflow-hidden rounded-[6px] border border-line", children: [
    /* @__PURE__ */ v("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3", children: [
      /* @__PURE__ */ v("span", { className: "mono-label flex items-center gap-2 text-ink", children: [
        /* @__PURE__ */ c($, { name: "lock" }),
        "Spec pinned"
      ] }),
      /* @__PURE__ */ c("span", { className: "mono-id text-muted", children: [i, e.part_name].filter(Boolean).join(" · ") })
    ] }),
    /* @__PURE__ */ v("div", { className: "flex flex-col gap-3 px-3 pt-[11px] pb-3", children: [
      /* @__PURE__ */ c("p", { className: "text-[13px] leading-[19px] text-pretty text-ink-soft", children: e.summary }),
      /* @__PURE__ */ c("dl", { className: "flex flex-col gap-[5px]", children: e.dimensions.map((s) => {
        const r = ng(s);
        return /* @__PURE__ */ v(
          "div",
          {
            className: "flex items-baseline gap-2",
            title: s.provisional ? `${s.how} · provisional, a real measurement should replace it` : s.how,
            children: [
              /* @__PURE__ */ c("dt", { className: "mono-id min-w-0 flex-1 truncate text-ink-soft", children: s.name }),
              /* @__PURE__ */ v("dd", { className: "mono-value text-ink", children: [
                s.provisional ? "~" : "",
                s.value_mm,
                " mm"
              ] }),
              /* @__PURE__ */ c("dd", { className: r === "measured" ? "mono-caption w-16 text-right text-accent-ink [letter-spacing:0.1em]" : "mono-caption w-16 text-right text-muted [letter-spacing:0.1em]", children: tg[r] })
            ]
          },
          s.name
        );
      }) }),
      e.acceptance.length > 0 ? /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5", children: [
        /* @__PURE__ */ c(Ao, { children: "Pass if" }),
        /* @__PURE__ */ c("ul", { className: "flex flex-col gap-1.5", role: "list", children: e.acceptance.map((s, r) => /* @__PURE__ */ v("li", { className: "grid grid-cols-[72px_minmax(0,1fr)] items-baseline gap-x-2", title: s.check, children: [
          /* @__PURE__ */ c("span", { className: "mono-id truncate uppercase text-muted [letter-spacing:0.06em]", children: ig(s.check) }),
          /* @__PURE__ */ c("span", { className: "text-xs leading-4 text-pretty text-ink-soft", children: s.criterion })
        ] }, r)) })
      ] }) : null,
      e.params.length > 0 ? /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5", children: [
        /* @__PURE__ */ c(Ao, { children: `${e.params.length} slider${e.params.length === 1 ? "" : "s"}` }),
        /* @__PURE__ */ c("ul", { className: "flex flex-wrap gap-1", role: "list", children: e.params.map((s) => /* @__PURE__ */ c("li", { className: "mono-id rounded-full bg-raised px-1.5 py-0.5 text-ink-soft", title: s.description, children: s.name }, s.name)) })
      ] }) : null
    ] })
  ] });
}
function Ty({
  measurement: e,
  staleParts: t,
  onAccept: n,
  onEdit: i,
  onRebuild: s,
  rebuilding: r
}) {
  const o = e.stale_parts ?? [], a = t ? o.filter((d) => t.includes(d)) : o, l = e.previous_value_mm != null && e.previous_value_mm !== e.value_mm, u = e.provisional && n;
  return /* @__PURE__ */ v("div", { className: "flex flex-col overflow-hidden rounded-[6px] border border-line", children: [
    /* @__PURE__ */ v("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3", children: [
      /* @__PURE__ */ v("span", { className: "mono-label flex items-center gap-2 text-ink", children: [
        /* @__PURE__ */ c($, { name: "ruler" }),
        l ? "Measurement changed" : "Measurement recorded"
      ] }),
      e.provisional ? /* @__PURE__ */ c("span", { className: "mono-caption text-warn [letter-spacing:0.1em]", children: "Provisional" }) : null
    ] }),
    /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5 px-3 pt-[9px] pb-2.5", children: [
      /* @__PURE__ */ v("div", { className: "flex items-baseline gap-2", children: [
        /* @__PURE__ */ c("span", { className: "mono-id min-w-0 flex-1 truncate text-ink-soft", children: e.name }),
        l ? /* @__PURE__ */ v("span", { className: "mono-value text-muted line-through", children: [
          e.previous_value_mm,
          " mm"
        ] }) : null,
        /* @__PURE__ */ v("span", { className: "mono-value text-ink", children: [
          e.value_mm,
          " mm"
        ] })
      ] }),
      /* @__PURE__ */ c("p", { className: "text-xs leading-4 text-muted", children: e.how }),
      u || i ? /* @__PURE__ */ v("div", { className: "mt-0.5 flex items-center gap-1.5", children: [
        u ? /* @__PURE__ */ c(
          "button",
          {
            type: "button",
            onClick: () => n(e.name),
            className: "btn-label chrome rounded-control focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent bg-ink px-2 py-1 text-white transition-colors hover:bg-ink-soft",
            children: "Accept"
          }
        ) : null,
        i ? /* @__PURE__ */ c(
          "button",
          {
            type: "button",
            onClick: () => i(e.name),
            className: "btn-label chrome rounded-control focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent border border-line px-2 py-1 text-ink-soft transition-colors hover:bg-raised",
            children: "Edit"
          }
        ) : null
      ] }) : null,
      a.length > 0 ? /* @__PURE__ */ v("div", { className: "mt-1 flex items-center gap-2 rounded-[6px] bg-warn-wash px-2.5 py-1.5", children: [
        /* @__PURE__ */ c("span", { className: "size-1.5 shrink-0 rounded-full bg-warn" }),
        /* @__PURE__ */ c("span", { className: "mono-caption min-w-0 flex-1 truncate text-warn [letter-spacing:0.08em]", children: a.length === 1 ? `${a[0]} is stale` : `${a.length} parts stale · ${a.join(", ")}` }),
        s ? /* @__PURE__ */ c(
          "button",
          {
            type: "button",
            onClick: () => s(a),
            disabled: r,
            className: "btn-label chrome rounded-control focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent bg-ink px-2 py-1 text-white transition-colors hover:bg-ink-soft disabled:opacity-60",
            children: r ? "Rebuilding…" : "Rebuild"
          }
        ) : null
      ] }) : null
    ] })
  ] });
}
const me = {
  stage: 15069435,
  part: 16732720,
  // Scenery stays neutral, and its albedo is pre-darkened because the key is bright enough
  // to clip the part's red: 0x78818d lit from above reads as the grey-blue token, 0xaab6c6.
  context: 7897485,
  edge: 10691593,
  gridMinor: 13623537,
  gridMajor: 12374760,
  gridBorder: 10467021,
  accent: 16732720,
  fail: 13570600,
  warn: 14714624,
  // Amber and violet are lit by the same key, so both are pre-darkened the same way.
  ghost: 8608554,
  cap: 7169436
}, sg = { fail: 0.4, warn: 0.38 }, rg = 0.62, og = 25, ec = (e, t) => e === "fail" ? t.fail : t.warn;
function ag() {
  const e = new Nc(16777215, 6);
  e.position.set(0.4, -0.9, 2.9);
  const t = new Pc(16777215, me.gridMajor, 1);
  return t.position.set(0, 0, 1), [t, e];
}
const en = (e, t) => {
  const n = new zi();
  return n.setAttribute("position", new Gi(new Float32Array(e), 3)), new _i(n, t);
};
function lg([e, t], n = 10) {
  const i = e / 2, s = t / 2, r = n > 0 ? n : 10, o = r * 5, a = [], l = [];
  for (let f = r; f < i; f += r)
    (f % o === 0 ? l : a).push(f, -s, 0, f, s, 0, -f, -s, 0, -f, s, 0);
  for (let f = r; f < s; f += r)
    (f % o === 0 ? l : a).push(-i, f, 0, i, f, 0, -i, -f, 0, i, -f, 0);
  const u = [0, -s, 0, 0, s, 0, -i, 0, 0, i, 0, 0], d = [
    -i,
    -s,
    0,
    i,
    -s,
    0,
    i,
    -s,
    0,
    i,
    s,
    0,
    i,
    s,
    0,
    -i,
    s,
    0,
    -i,
    s,
    0,
    -i,
    -s,
    0
  ], h = new pn();
  return h.add(
    en(a, new it({ color: me.gridMinor })),
    en(l, new it({ color: me.gridMajor })),
    en(d, new it({ color: me.gridBorder })),
    en(u, new it({ color: me.accent, transparent: !0, opacity: 0.35 }))
  ), h;
}
const tn = 1.2;
function cg(e) {
  const t = new Qe(
    new Ic(1, tn, tn),
    new Ct({ color: me.accent, transparent: !0, opacity: 0.9 })
  );
  return t.position.set(0, -e / 2 + tn * 2, tn / 2), t;
}
const tc = (e) => {
  const t = e.getSize(new fe());
  return Math.max(t.x, t.y, t.z) || 10;
};
function ug(e, t, n) {
  const i = n.getCenter(new fe()), s = tc(n), r = s / (2 * Math.tan(e.fov * Math.PI / 180 / 2)) * 2.1, o = [0.7, -0.75, 0.6];
  e.up.set(0, 0, 1), e.position.set(i.x + r * o[0], i.y + r * o[1], i.z + r * o[2]), t.target.copy(i), e.near = s / 100, e.far = s * 100, e.updateProjectionMatrix(), t.update();
}
function nc(e, t, n) {
  const i = tc(n), s = e.distanceTo(t);
  return !n.containsPoint(e) && n.clone().expandByScalar(i * 2).containsPoint(t) && s > i / 100 && s < i * 50;
}
function ic(e, t) {
  return e.updateMatrixWorld(), new Lc().setFromProjectionMatrix(
    new Fc().multiplyMatrices(e.projectionMatrix, e.matrixWorldInverse)
  ).intersectsBox(t);
}
function dg(e, t, n) {
  const i = [];
  e.traverse((r) => {
    r.isMesh && i.push(r);
  });
  const s = new pn();
  for (const r of i) {
    const o = r.geometry;
    o.attributes.normal || o.computeVertexNormals();
    const a = new Ui({
      color: n.part,
      // Flat and matte: printed plastic, no specular sheen over the accent.
      metalness: 0,
      roughness: 0.85,
      // Pushed back a hair so the edge overlay draws without z-fighting the surface.
      polygonOffset: !0,
      polygonOffsetFactor: 1,
      polygonOffsetUnits: 1,
      clippingPlanes: [t]
    });
    o.attributes.color && (a.vertexColors = !0);
    const l = new Qe(o, a);
    for (const u of [].concat(r.material)) u.dispose();
    if (l.name = r.name || r.parent?.name || "", l.name === "context")
      a.color.setHex(n.context), a.transparent = !0, a.opacity = 0.3;
    else {
      const u = new _i(
        new Jo(o, og),
        new it({ color: n.edge, transparent: !0, opacity: 0.35, clippingPlanes: [t] })
      );
      l.add(u);
    }
    s.add(l);
  }
  return s;
}
const sc = (e) => e.children.filter((t) => t.isMesh && t.name !== "context" && t.name !== "target");
function fg(e) {
  e.position.set(0, 0, 0), e.updateMatrixWorld(!0);
  const t = new Et();
  for (const o of e.children) o.name !== "target" && t.expandByObject(o);
  const n = new Et();
  for (const o of sc(e)) n.expandByObject(o);
  n.isEmpty() && n.copy(t);
  const i = n.getCenter(new fe()), s = new fe(-i.x, -i.y, -n.min.z), r = e.parent ? e.parent.getWorldQuaternion(new Hs()) : new Hs();
  return e.position.copy(s).applyQuaternion(r.invert()), e.updateMatrixWorld(!0), t.translate(s);
}
function hg(e) {
  const t = new Et();
  for (const n of sc(e)) t.expandByObject(n);
  return t;
}
const No = {
  depthWrite: !1,
  depthTest: !1,
  colorWrite: !1,
  stencilWrite: !0,
  stencilFunc: Vc
};
function pg(e, t) {
  const n = new Ct({
    ...No,
    clippingPlanes: [t],
    side: Dc,
    stencilFail: On,
    stencilZFail: On,
    stencilZPass: On
  }), i = new Ct({
    ...No,
    clippingPlanes: [t],
    side: Rc,
    stencilFail: Bn,
    stencilZFail: Bn,
    stencilZPass: Bn
  });
  return [n, i].map((s) => {
    const r = new Qe(e.geometry, s);
    return r.matrixAutoUpdate = !1, r.matrix = e.matrixWorld, r.renderOrder = 1, r;
  });
}
function mg() {
  const e = new Qe(
    new Mc(1, 1),
    new Ui({
      // Violet, because the cap is the one surface that is not part material and must not
      // impersonate a signal: amber is a warn, red a fail, orange the part itself.
      color: me.cap,
      metalness: 0,
      roughness: 0.85,
      side: Wi,
      stencilWrite: !0,
      stencilRef: 0,
      stencilFunc: Cc,
      stencilFail: In,
      stencilZFail: In,
      stencilZPass: In
    })
  );
  return e.renderOrder = 1.1, e.visible = !1, e.onAfterRender = (t) => t.clearStencil(), e;
}
function gg(e, t, n, i) {
  const s = new zi();
  s.setAttribute("position", new Gi(new Float32Array(e), 3));
  const r = new Ct({
    color: ec(t, i),
    transparent: !0,
    opacity: sg[t],
    side: Wi,
    polygonOffset: !0,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
    depthWrite: !1,
    clippingPlanes: [n]
  });
  return new Qe(s, r);
}
function yg(e, t, n) {
  const i = new zi();
  i.setAttribute("position", new Gi(new Float32Array(e), 3));
  const s = new _i(
    new Jo(i, 1),
    new it({ color: n.accent, depthTest: !1, clippingPlanes: [t] })
  );
  return s.renderOrder = 998, i.dispose(), s;
}
function xg(e, t, n, i) {
  const s = new Ct({ color: ec(t, i), depthTest: !1, depthWrite: !1 }), r = new Qe(new Ec(1, 12, 8), s);
  return r.position.set(e[0], e[1], e[2]), r.scale.setScalar(n), r.renderOrder = 999, r;
}
const vg = (e) => {
  for (const t of Array.isArray(e) ? e : [e]) t.dispose();
};
function de(e) {
  e.traverse((t) => {
    const n = t;
    !n.geometry || t.name === "target" || (n.geometry.dispose(), vg(n.material));
  });
}
const Fi = 1e6, bg = { x: [1, 0, 0], y: [0, 1, 0], z: [0, 0, 1] }, Po = 10, wg = 42, kg = 4e3, Tg = Math.PI / 12, Mo = 1.8, Sg = 2, Co = 0.9, Os = () => {
  try {
    return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? !1;
  } catch {
    return !1;
  }
};
function rc(e, t) {
  if (e <= 0) return 0;
  if (e >= 1) return 1;
  const [n, i, s, r] = t, o = (l, u, d) => 3 * (1 - l) ** 2 * l * u + 3 * (1 - l) * l ** 2 * d + l ** 3;
  let a = e;
  for (let l = 0; l < 8; l++) {
    const u = o(a, n, s) - e;
    if (Math.abs(u) < 1e-4) break;
    const d = 3 * (1 - a) ** 2 * n + 6 * (1 - a) * a * (s - n) + 3 * a ** 2 * (1 - s);
    if (Math.abs(d) < 1e-6) break;
    a -= u / d;
  }
  return o(a, i, r);
}
const Eo = (e) => {
  const t = [];
  return e.traverse((n) => {
    const i = n.material;
    if (i)
      for (const s of Array.isArray(i) ? i : [i])
        t.push({ material: s, opacity: s.opacity, transparent: s.transparent, depthWrite: s.depthWrite });
  }), t;
}, Do = (e) => {
  for (const t of e)
    t.material.opacity = t.opacity, t.material.transparent = t.transparent, t.material.depthWrite = t.depthWrite;
};
function Ag(e, t, n) {
  const i = n.now ?? (() => performance.now()), s = n.schedule ?? ((p) => requestAnimationFrame(() => p())), r = n.unschedule ?? ((p) => cancelAnimationFrame(p)), o = t ? Eo(t) : [], a = e ? Eo(e) : [];
  for (const p of o)
    p.material.transparent = !0, p.material.opacity = 0;
  for (const p of a)
    p.material.transparent = !0, p.material.depthWrite = !1;
  const l = i(), u = Math.max(1, n.seconds * 1e3);
  let d = 0, h = !0;
  const f = () => {
    if (d = 0, !h) return;
    const p = Math.min(1, (i() - l) / u);
    for (const g of o) g.material.opacity = g.opacity * p;
    for (const g of a) g.material.opacity = g.opacity * (1 - p);
    if (n.render(), p < 1) {
      d = s(f);
      return;
    }
    h = !1, Do(o), n.onDone();
  };
  return d = s(f), () => {
    h && (h = !1, d && r(d), Do(o));
  };
}
const Ng = (e, t) => !e || !t ? e === t : e.position.every((n, i) => n === t.position[i]) && e.target.every((n, i) => n === t.target[i]), Pg = (e) => {
  let t = null;
  return e.traverse((n) => {
    n.isMesh && !t && (t = n.geometry);
  }), t;
};
function oc(e, t, n) {
  if (!e.controls) return !1;
  const i = new fe().fromArray(t.position), s = new fe().fromArray(t.target);
  if (!nc(i, s, n)) return !1;
  e.camera.position.copy(i), e.controls.target.copy(s);
  const r = n.getSize(new fe()), o = Math.max(r.x, r.y, r.z) || 10;
  return e.camera.near = o / 100, e.camera.far = o * 100, e.camera.updateProjectionMatrix(), e.controls.update(), ic(e.camera, n);
}
function Mg(e, t) {
  return !e.controls || !nc(e.camera.position, e.controls.target, t) ? !1 : ic(e.camera, t);
}
function Cg(e) {
  const t = e.controls;
  t && (t._sphericalDelta?.set(0, 0, 0), t._panOffset?.set(0, 0, 0), t._scale = 1);
}
function vt(e, t) {
  e.plate && (e.scene.remove(e.plate), de(e.plate), e.plate = null);
  const n = t ?? Eg(e);
  e.plateSize = n, n && (e.plate = lg(n, e.pitch), e.scene.add(e.plate));
}
function Eg(e) {
  if (!e.part) return null;
  const t = new Et().setFromObject(e.part).getSize(new fe()), n = Math.max(100, Math.ceil(Math.max(t.x, t.y) * 1.8 / 50) * 50);
  return [n, n];
}
function Vo(e, t) {
  if (!e.part) return;
  e.box = fg(e.part), e.size = e.box.getSize(new fe()).length(), e.quiet = !0, !(e.framed ? Mg(e, e.box) : t && oc(e, t, e.box)) && e.controls && ug(e.camera, e.controls, e.box), e.quiet = !1, e.framed = !0;
}
function Ro(e) {
  const t = e.fading;
  t && (e.fading = null, t.cancel(), e.root.remove(t.group), de(t.group));
}
function Dg(e) {
  const t = e.controls;
  if (!t || Os()) return;
  e.nudgeRaf && cancelAnimationFrame(e.nudgeRaf);
  const n = t.target.clone(), i = e.camera.position.clone().sub(n), s = e.camera.up.clone().normalize(), r = performance.now(), o = U.coast * 1e3;
  e.quiet = !0;
  const a = () => {
    e.nudgeRaf = 0;
    const l = Math.min(1, (performance.now() - r) / o);
    l >= 1 && (e.quiet = !1), e.camera.position.copy(i).applyAxisAngle(s, Tg * rc(l, Y.out)).add(n), t.update(), e.render(), l < 1 && (e.nudgeRaf = requestAnimationFrame(a));
  };
  e.nudgeRaf = requestAnimationFrame(a);
}
function ac(e) {
  e.purgeRaf && cancelAnimationFrame(e.purgeRaf), e.purgeRaf = 0, e.purge && (e.scene.remove(e.purge), de(e.purge), e.purge = null);
}
function Vg(e) {
  if (!e.plate || !e.plateSize || Os()) return !1;
  const [t, n] = e.plateSize, i = cg(n);
  e.purge = i, e.scene.add(i);
  const s = i.material, r = performance.now(), o = () => {
    e.purgeRaf = 0;
    const a = (performance.now() - r) / 1e3, l = Math.max(1e-3, t * rc(a / Mo, Y.out));
    i.scale.x = l, i.position.x = -t / 2 + l / 2;
    const u = a - Mo - Sg;
    if (s.opacity = u <= 0 ? Co : Co * (1 - Math.min(1, u / U.settle)), e.render(), u < U.settle) {
      e.purgeRaf = requestAnimationFrame(o);
      return;
    }
    ac(e), e.render();
  };
  return e.purgeRaf = requestAnimationFrame(o), !0;
}
function Lo(e, t, n) {
  !t || n.current || (n.current = Vg(e));
}
function hn(e) {
  for (const t of e.writers)
    e.scene.remove(t), t.material.dispose();
  e.writers = [];
}
function Rg(e) {
  if (hn(e), !!e.part) {
    e.part.updateMatrixWorld(!0);
    for (const t of e.part.children)
      if (!(!t.isMesh || t.name === "context" || t.name === "target"))
        for (const n of pg(t, e.plane))
          n.visible = e.cutting, e.scene.add(n), e.writers.push(n);
  }
}
function bt(e, t) {
  if (!t) {
    e.cutting = !1, e.cutSign = 0, e.cap.visible = !1;
    for (const d of e.writers) d.visible = !1;
    e.plane.constant = Fi, e.render();
    return;
  }
  if ((!e.cutting || e.cutAxis !== t.axis) && (e.cutting = !0, e.cutAxis = t.axis, e.cutSign = 0), !e.part) {
    e.cap.visible = !1, e.plane.constant = Fi, e.render();
    return;
  }
  const n = hg(e.part), i = t.axis, s = n.min[i], r = n.max[i];
  e.cutSign || (e.cutSign = e.camera.position[i] >= (s + r) / 2 ? 1 : -1);
  const o = e.cutSign === 1 ? t.t : 1 - t.t, a = s + (r - s) * (0.02 + 0.96 * o), l = bg[i];
  e.plane.normal.set(-e.cutSign * l[0], -e.cutSign * l[1], -e.cutSign * l[2]), e.plane.constant = e.cutSign * a, e.cap.visible = !0;
  for (const d of e.writers) d.visible = !0;
  const u = n.getSize(new fe()).length();
  e.cap.scale.set(u, u, 1), e.plane.projectPoint(n.getCenter(new fe()), e.cap.position), e.cap.lookAt(
    e.cap.position.x - e.plane.normal.x,
    e.cap.position.y - e.plane.normal.y,
    e.cap.position.z - e.plane.normal.z
  ), e.render();
}
function wt(e, t, n) {
  for (const r of e.marks.children) de(r);
  if (e.marks.clear(), e.glows = [], !e.part) {
    e.render();
    return;
  }
  const i = e.part.position, s = Math.max(0.6, e.size / 90);
  t.forEach((r, o) => {
    if (r.face && r.face.length) {
      const l = gg(r.face, r.severity, e.plane, me);
      l.position.copy(i), l.userData.finding = o, o === n && (l.material.opacity = rg, l.add(yg(r.face, e.plane, me))), e.marks.add(l), e.glows.push(l);
    }
    if (!r.where) return;
    const a = xg(
      [r.where[0] + i.x, r.where[1] + i.y, r.where[2] + i.z],
      r.severity,
      s,
      me
    );
    e.marks.add(a);
  }), e.render();
}
function Sy(e) {
  const { glbUrl: t, targetUrl: n, targetOffset: i, findings: s, highlight: r, bed: o, up: a, section: l, camera: u, settleKey: d, purge: h, className: f } = e, [p, g] = O(!1), x = M(null), b = M(null), w = M(null), T = M(null), y = M(e);
  y.current = e;
  const k = M(!1);
  F(() => {
    const m = x.current;
    if (!m) return;
    const N = new Oc();
    N.background = new Bc(me.stage);
    const A = new $c(45, 1, 0.1, 1e4);
    A.up.set(0, 0, 1);
    const L = new pn(), I = new pn();
    L.add(I), N.add(L);
    for (const H of ag()) N.add(H);
    const j = mg();
    N.add(j);
    const C = {
      renderer: null,
      scene: N,
      camera: A,
      controls: null,
      plane: new jc(new fe(0, 0, -1), Fi),
      root: L,
      marks: I,
      cap: j,
      part: null,
      fading: null,
      ghost: null,
      plate: null,
      plateSize: null,
      pitch: Po,
      purge: null,
      writers: [],
      glows: [],
      box: new Et(),
      size: 0,
      cutting: !1,
      cutAxis: "z",
      cutSign: 0,
      framed: !1,
      generation: 0,
      loaded: 0,
      targetGeneration: 0,
      quiet: !1,
      lastW: 0,
      lastH: 0,
      raf: 0,
      nudgeRaf: 0,
      purgeRaf: 0,
      camTimer: null,
      render: () => {
      }
    };
    b.current = C, m.__nurbViewer = C;
    try {
      C.renderer = new Uc({ antialias: !0, stencil: !0 });
    } catch {
      m.setAttribute("data-nogl", "");
    }
    const re = C.renderer?.domElement ?? null;
    C.renderer && re && (C.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)), C.renderer.localClippingEnabled = !0, re.className = "block h-full w-full", m.appendChild(re), C.controls = new zc(A, re), C.controls.enableDamping = !0, C.controls.dampingFactor = 0.0533);
    const ce = () => {
      if (C.raf = 0, !C.renderer || !C.controls) return;
      const H = C.controls.update();
      H || Cg(C), C.renderer.render(N, A), H && C.render();
    };
    C.render = () => {
      !C.renderer || C.raf || (C.raf = requestAnimationFrame(ce));
    };
    const oe = (H, D) => {
      const _ = Math.floor(H), Z = Math.floor(D);
      !_ || !Z || _ === C.lastW && Z === C.lastH || (C.lastW = _, C.lastH = Z, C.renderer?.setSize(_, Z, !1), A.aspect = _ / Z, A.updateProjectionMatrix(), C.render());
    }, W = new ResizeObserver((H) => {
      const D = H[H.length - 1].contentRect;
      oe(D.width, D.height);
    });
    W.observe(m), oe(m.clientWidth, m.clientHeight);
    const J = () => {
      C.render(), !C.quiet && (C.camTimer && clearTimeout(C.camTimer), C.camTimer = setTimeout(() => {
        const H = y.current.onCamera;
        !H || !C.controls || H({
          position: C.camera.position.toArray(),
          target: C.controls.target.toArray()
        });
      }, 250));
    };
    return C.controls?.addEventListener("change", J), () => {
      W.disconnect(), C.raf && cancelAnimationFrame(C.raf), C.nudgeRaf && cancelAnimationFrame(C.nudgeRaf), C.camTimer && clearTimeout(C.camTimer), C.generation++, C.targetGeneration++, C.controls?.removeEventListener("change", J), C.controls?.dispose(), hn(C), ac(C);
      for (const H of I.children) de(H);
      Ro(C), C.part && de(C.part), C.ghost && (C.ghost.geometry.dispose(), C.ghost.material.dispose()), C.plate && de(C.plate), de(j), C.renderer?.setAnimationLoop(null), C.renderer?.forceContextLoss(), C.renderer?.dispose(), re?.remove(), delete m.__nurbViewer, b.current = null;
    };
  }, []), F(() => {
    const m = b.current;
    if (!m || !m.controls) return;
    const N = ++m.generation;
    Ro(m);
    const A = () => {
      m.part && (m.root.remove(m.part), m.ghost && m.part.remove(m.ghost), de(m.part), m.part = null);
    };
    if (!t) {
      A(), vt(m, y.current.bed), hn(m), wt(m, [], null), bt(m, y.current.section);
      return;
    }
    new qs().loadAsync(t).then((L) => {
      if (N !== m.generation) {
        de(L.scene);
        return;
      }
      const I = dg(L.scene, m.plane, me);
      if (m.loaded = N, !I.children.length) {
        A(), de(I), hn(m), wt(m, [], null), bt(m, y.current.section);
        return;
      }
      const j = m.part;
      j && m.ghost && j.remove(m.ghost), m.ghost && I.add(m.ghost), m.root.add(I), m.part = I, Vo(m, y.current.camera), vt(m, y.current.bed), Lo(m, y.current.purge, k), T.current = y.current.camera ?? null, Rg(m), bt(m, y.current.section), wt(m, y.current.findings ?? [], y.current.highlight), j && Os() ? (m.root.remove(j), de(j)) : j && (m.fading = {
        group: j,
        cancel: Ag(j, I, {
          seconds: U.settle,
          render: m.render,
          onDone: () => {
            m.fading = null, m.root.remove(j), de(j), m.render();
          }
        })
      }), m.render();
    }).catch((L) => {
      N === m.generation && console.warn(`ViewerIsland: could not load ${t}`, L);
    });
  }, [t]);
  const E = (i ?? [0, 0, 0]).join(",");
  F(() => {
    const m = b.current;
    if (!m || !m.controls) return;
    const N = ++m.targetGeneration;
    if (m.ghost && (m.ghost.parent?.remove(m.ghost), m.ghost.geometry.dispose(), m.ghost.material.dispose(), m.ghost = null), !n) {
      m.render();
      return;
    }
    new qs().loadAsync(n).then((A) => {
      if (N !== m.targetGeneration) {
        de(A.scene);
        return;
      }
      const L = Pg(A.scene);
      if (!L) return;
      L.attributes.normal || L.computeVertexNormals();
      const I = new Qe(
        L,
        new Ui({
          color: me.ghost,
          metalness: 0,
          roughness: 0.9,
          transparent: !0,
          opacity: 0.3,
          depthWrite: !1,
          side: Wi,
          clippingPlanes: [m.plane]
        })
      );
      I.name = "target";
      const j = E.split(",").map(Number);
      I.position.set(j[0], j[1], j[2]), m.ghost = I, m.part?.add(I), m.render();
    }).catch(() => {
    });
  }, [n, E]), F(() => {
    const m = b.current;
    !m || m.loaded !== m.generation || wt(m, s ?? [], r);
  }, [s, r]), F(() => {
    const m = b.current;
    m && (vt(m, o), m.render());
  }, [o?.[0], o?.[1], !o]);
  const P = M(d);
  F(() => {
    const m = b.current, N = P.current;
    P.current = d, !(!m || d === void 0 || d === N) && Dg(m);
  }, [d]), F(() => {
    const m = b.current;
    m && Lo(m, h, k);
  }, [h, o?.[0], o?.[1]]), F(() => {
    let m = null;
    const N = () => {
      g(!0), m && clearTimeout(m), m = setTimeout(() => g(!1), kg);
    };
    return window.addEventListener("nurb:gridfinity", N), () => {
      window.removeEventListener("nurb:gridfinity", N), m && clearTimeout(m);
    };
  }, []), F(() => {
    const m = b.current;
    m && (m.pitch = p ? wg : Po, vt(m, y.current.bed), m.render());
  }, [p]);
  const S = (a ?? [0, 0, 1]).join(",");
  return F(() => {
    const m = b.current;
    if (!m) return;
    const N = new fe(...S.split(",").map(Number)).normalize();
    m.root.quaternion.setFromUnitVectors(N, new fe(0, 0, 1)), m.root.updateMatrixWorld(!0), m.part && (Vo(m, y.current.camera), vt(m, y.current.bed), bt(m, y.current.section), wt(m, y.current.findings ?? [], y.current.highlight)), m.render();
  }, [S]), F(() => {
    const m = b.current;
    m && bt(m, l);
  }, [l]), F(() => {
    const m = b.current;
    if (!m || !m.part || !u || Ng(u, T.current)) return;
    T.current = u, m.quiet = !0;
    const N = oc(m, u, m.box);
    m.quiet = !1, N && m.render();
  }, [u]), /* @__PURE__ */ c(
    "div",
    {
      ref: x,
      className: R("relative block h-full w-full", f),
      onPointerDown: (m) => {
        w.current = [m.clientX, m.clientY];
      },
      onPointerUp: (m) => {
        const N = w.current;
        w.current = null;
        const A = b.current, L = y.current.onHighlight;
        if (!N || !A || !L || Math.hypot(m.clientX - N[0], m.clientY - N[1]) > 5) return;
        const I = m.currentTarget.getBoundingClientRect();
        if (!I.width || !I.height) return;
        const j = new Wc(
          (m.clientX - I.left) / I.width * 2 - 1,
          -((m.clientY - I.top) / I.height) * 2 + 1
        ), C = new _c();
        C.setFromCamera(j, A.camera);
        const re = C.intersectObjects(A.glows, !1).find((ce) => !A.cutting || A.plane.distanceToPoint(ce.point) >= 0);
        L(re ? re.object.userData.finding : null);
      },
      children: p && /* @__PURE__ */ c("div", { className: "mono-caption pointer-events-none absolute bottom-3 left-3 text-faint [letter-spacing:0.12em]", children: "GRID 42.0 MM" })
    }
  );
}
const Lg = {
  accent: "bg-accent text-white hover:bg-accent-hover",
  ink: "bg-ink text-white hover:bg-ink-soft",
  outline: "border border-line bg-ground text-ink-soft hover:border-panel-edge hover:text-ink",
  ghost: "text-muted hover:bg-raised hover:text-ink",
  danger: "bg-fail text-white hover:bg-fail/90"
}, Fg = {
  sm: "h-7 px-3",
  md: "h-9 px-3",
  lg: "h-10 px-4"
}, Te = ji(function({ variant: t = "outline", size: n = "sm", icon: i, trailingIcon: s, className: r, children: o, type: a = "button", ...l }, u) {
  return /* @__PURE__ */ v(
    "button",
    {
      ref: u,
      type: a,
      className: R(
        "chrome btn-label inline-flex shrink-0 items-center justify-center gap-2 rounded-[3px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50",
        Lg[t],
        Fg[n],
        i && "pl-2.5",
        s && "pr-2.5",
        r
      ),
      ...l,
      children: [
        i ? /* @__PURE__ */ c($, { name: i }) : null,
        o,
        s ? /* @__PURE__ */ c($, { name: s }) : null
      ]
    }
  );
});
function Bs({
  icon: e,
  label: t,
  active: n = !1,
  className: i,
  ...s
}) {
  return /* @__PURE__ */ v(
    "button",
    {
      type: "button",
      "aria-label": t,
      title: t,
      className: R(
        "chrome relative inline-flex size-7 shrink-0 items-center justify-center rounded-[4px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent disabled:opacity-40",
        n ? "bg-accent-wash text-accent-ink" : "text-ink-soft hover:bg-raised hover:text-ink",
        i
      ),
      ...s,
      children: [
        /* @__PURE__ */ c($, { name: e }),
        /* @__PURE__ */ c("span", { className: "absolute top-1/2 left-1/2 size-[max(100%,3rem)] -translate-1/2 pointer-fine:hidden", "aria-hidden": "true" })
      ]
    }
  );
}
const Ig = Y.out, Og = { duration: U.settle, ease: Ig }, Bg = { duration: 0 };
function $g({
  action: e,
  resetAfter: t = 1400
}) {
  const [n, i] = O("idle"), s = M("idle"), r = M(0), o = M(null), a = M(!0), l = M(e);
  l.current = e;
  const u = q(() => {
    o.current && clearTimeout(o.current), o.current = null;
  }, []), d = q(() => {
    if (s.current === "pending") return;
    u();
    const h = ++r.current;
    s.current = "pending", i("pending");
    const f = (p) => {
      !a.current || h !== r.current || (s.current = p, i(p), o.current = setTimeout(() => {
        !a.current || h !== r.current || (s.current = "idle", i("idle"));
      }, t));
    };
    Promise.resolve().then(() => l.current()).then(
      () => f("success"),
      () => f("error")
    );
  }, [u, t]);
  return F(() => (a.current = !0, () => {
    a.current = !1, u();
  }), [u]), { status: n, run: d, pending: n === "pending" };
}
function jg({ still: e }) {
  return /* @__PURE__ */ v(
    B.svg,
    {
      width: "11",
      height: "11",
      viewBox: "0 0 12 12",
      fill: "none",
      "aria-hidden": "true",
      className: "shrink-0",
      animate: e ? void 0 : { rotate: 360 },
      transition: e ? void 0 : { duration: U.coast * 0.6, repeat: 1 / 0, ease: "linear" },
      children: [
        /* @__PURE__ */ c("circle", { cx: "6", cy: "6", r: "4.5", stroke: "currentColor", strokeWidth: "1.5", strokeOpacity: "0.22" }),
        /* @__PURE__ */ c("path", { d: "M10.5 6A4.5 4.5 0 0 0 6 1.5", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
      ]
    }
  );
}
function Fo({ d: e, extra: t }) {
  return /* @__PURE__ */ v(
    "svg",
    {
      width: "11",
      height: "11",
      viewBox: "0 0 12 12",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: "1.7",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      "aria-hidden": "true",
      className: "shrink-0",
      children: [
        /* @__PURE__ */ c("path", { d: e }),
        t ? /* @__PURE__ */ c("path", { d: t }) : null
      ]
    }
  );
}
function Ug({
  label: e,
  pendingLabel: t = e,
  successLabel: n = "Done",
  errorLabel: i = "Try again",
  onAction: s,
  resetAfter: r = 1400,
  variant: o = "outline",
  disabled: a = !1,
  className: l
}) {
  const u = Q(), { status: d, run: h, pending: f } = $g({ action: s, resetAfter: r }), p = u ? Bg : Og, g = [
    { key: "idle", text: e, color: void 0, icon: null },
    {
      key: "pending",
      text: t,
      color: "var(--color-muted)",
      icon: /* @__PURE__ */ c(jg, { still: u === !0 || d !== "pending" })
    },
    {
      key: "success",
      text: n,
      color: "var(--color-pass)",
      icon: /* @__PURE__ */ c(Fo, { d: "M2.6 6.3 4.9 8.6 9.4 3.6" })
    },
    {
      key: "error",
      text: i,
      color: "var(--color-fail)",
      icon: /* @__PURE__ */ c(Fo, { d: "M6 2.9v3.5", extra: "M6 9.05h.01" })
    }
  ], x = g.find((b) => b.key === d) ?? g[0];
  return /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c(
      Te,
      {
        variant: o,
        disabled: a,
        "aria-label": x.text,
        "aria-busy": f || void 0,
        "aria-disabled": f || void 0,
        className: l,
        onClick: () => {
          f || ($e("press"), h());
        },
        children: /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "relative grid place-items-center", children: g.map((b) => /* @__PURE__ */ v(
          B.span,
          {
            initial: !1,
            animate: b.key === d ? { opacity: 1, y: 0 } : { opacity: 0, y: 2 },
            transition: p,
            style: { color: b.color },
            className: "col-start-1 row-start-1 flex items-center justify-center gap-1.5 whitespace-nowrap",
            children: [
              b.icon,
              b.text
            ]
          },
          b.key
        )) })
      }
    ),
    /* @__PURE__ */ c("span", { role: "status", "aria-live": "polite", className: "sr-only", children: d === "success" ? n : d === "error" ? i : "" })
  ] });
}
function kt(e) {
  return Math.round(e * 1e6) / 1e6;
}
function Wg({
  value: e,
  onValueChange: t,
  min: n,
  max: i,
  step: s,
  detents: r,
  pull: o
}) {
  const a = le(() => r.map((b) => typeof b == "number" ? { value: b } : b), [r]), l = o ?? (i - n) * 0.045, u = M(t);
  u.current = t;
  const d = le(() => a.findIndex((b) => kt(b.value) === kt(e)), [a, e]), h = M(d);
  h.current = d;
  const f = M(!1), p = q(
    (b) => {
      let w = -1, T = l;
      for (let y = 0; y < a.length; y += 1) {
        const k = Math.abs(b - a[y].value);
        k <= T && (T = k, w = y);
      }
      return w >= 0 ? a[w].value : n + Math.round((b - n) / s) * s;
    },
    [l, a, n, s]
  ), g = q(
    (b) => {
      const w = Number(b.target.value);
      if (!Number.isFinite(w)) return;
      const T = f.current;
      f.current = !1;
      const y = kt(Math.min(i, Math.max(n, T ? w : p(w)))), k = a.findIndex((E) => kt(E.value) === y);
      k >= 0 && k !== h.current && $e("tick"), y !== kt(e) && u.current(y);
    },
    [a, i, n, p, e]
  ), x = q((b) => {
    (b.key.startsWith("Arrow") || b.key === "PageUp" || b.key === "PageDown") && (f.current = !0);
  }, []);
  return { onChange: g, onKeyDown: x, activeDetent: d, detents: a, activeLabel: a[d]?.label };
}
function _g({
  detents: e,
  min: t,
  max: n,
  activeDetent: i,
  className: s
}) {
  const r = n - t;
  return (
    // Inset by half the 12px thumb, because that is the width the thumb's centre actually travels.
    /* @__PURE__ */ c("div", { "aria-hidden": !0, className: R("pointer-events-none absolute inset-x-[6px] bottom-0", s), children: e.map((o, a) => /* @__PURE__ */ c(
      "span",
      {
        title: o.label,
        className: R(
          "absolute bottom-0 block h-[3px] w-px -translate-x-1/2",
          a === i ? "bg-accent" : "bg-line"
        ),
        style: { left: r > 0 ? `${(o.value - t) / r * 100}%` : "0%" }
      },
      o.value
    )) })
  );
}
function zg(e, t) {
  let n, i;
  if (e === 0 ? (n = 0, i = t ? 8 : 1) : e < 0 ? (n = e * 2, i = e / 2) : (n = e / 2, i = e * 2), t)
    return n = Math.floor(n), i = Math.ceil(i), e >= 1 && (n = Math.max(1, n)), i - n < 4 && (i = n + 4), { lo: n, hi: i, step: 1 };
  const s = Math.min(10 ** (Math.floor(Math.log10(i - n)) - 1), 10 ** -cc(e));
  return { lo: ft(Math.floor(n / s) * s, s), hi: ft(Math.ceil(i / s) * s, s), step: s };
}
function lc(e, t) {
  const n = zg(e.default, t);
  return {
    lo: e.min ?? n.lo,
    hi: e.max ?? n.hi,
    step: e.step ?? n.step
  };
}
function cc(e) {
  const t = String(e), n = t.indexOf(".");
  return n === -1 || t.includes("e") ? 0 : Math.min(t.length - n - 1, 4);
}
function ft(e, t) {
  const n = Math.max(0, -Math.floor(Math.log10(t)));
  return +e.toFixed(n);
}
function Ii(e) {
  return e.kind === "bool" || e.kind === "int" || e.kind === "float";
}
function Gg(e, t) {
  const n = {};
  for (const i of e) {
    if (!Ii(i)) continue;
    const s = t[i.name];
    s === void 0 || s === i.default || (n[i.name] = s);
  }
  return n;
}
const Kg = /wall|thickness|lip|rim|shell/;
function Hg(e, t, n = 0.4) {
  if (e.kind !== "float" || typeof e.default != "number") return [];
  const { lo: i, hi: s, step: r } = lc(e, !1), o = (u) => Number.isFinite(u) && u >= i && u <= s, a = [{ value: e.default, label: "default" }];
  for (const u of t ?? [])
    o(u.value_mm) && a.push({ value: u.value_mm, label: "measured" });
  if (Kg.test(e.name.toLowerCase()) && n > 0)
    for (let u = 2; u * n <= s; u += 1) {
      const d = ft(u * n, 1e-3);
      o(d) && a.push({ value: d, label: `${u} lines` });
    }
  const l = /* @__PURE__ */ new Map();
  for (const u of a) {
    const d = ft(u.value, r);
    l.has(d) || l.set(d, u);
  }
  return [...l.values()].sort((u, d) => u.value - d.value);
}
const Io = Y.out, Oo = "mm", Bo = 4, qg = 60, $o = 6;
function et(e, t, n) {
  return String(t ? Math.round(e) : ft(e, n));
}
function Bt(e) {
  return e.replace(/_/g, " ");
}
function jo({ children: e }) {
  return /* @__PURE__ */ v("div", { className: "chrome flex items-center gap-2 px-4 pt-[11px] pb-2", children: [
    /* @__PURE__ */ c("span", { className: "mono-caption text-faint [letter-spacing:0.12em]", children: e }),
    /* @__PURE__ */ c("span", { className: "h-px flex-1 bg-line-soft" })
  ] });
}
function uc({ param: e, onReset: t }) {
  return /* @__PURE__ */ c(
    "button",
    {
      type: "button",
      title: `Default ${e.default}`,
      onClick: t,
      "aria-label": `Reset ${e.name} to default`,
      className: "size-1.5 shrink-0 rounded-full bg-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    }
  );
}
function Yg({
  id: e,
  param: t,
  value: n,
  dirty: i,
  measurements: s,
  nozzle: r,
  onValue: o
}) {
  const a = t.kind === "int", l = lc(t, a), u = Math.min(l.lo, n), d = Math.max(l.hi, n), h = a ? 1 : Math.min(l.step, 10 ** -cc(n)), [f, p] = O(() => et(n, a, h)), g = M(!1);
  if (!g.current) {
    const D = et(n, a, h);
    D !== f && p(D);
  }
  const x = Q(), b = le(() => Hg(t, s, r), [t, s, r]), w = Wg({
    value: n,
    onValueChange: o,
    min: u,
    max: d,
    step: h,
    detents: b,
    pull: (d - u) * 0.045
  }), [T, y] = O(null), [k, E] = O(0);
  F(() => {
    if (!T) return;
    E(T.end === "max" ? 3 : -3);
    const D = setTimeout(() => E(0), x ? 0 : U.tick * 1e3), _ = setTimeout(() => y(null), 1200);
    return () => {
      clearTimeout(D), clearTimeout(_);
    };
  }, [T, x]);
  const P = (D) => y({ end: D }), S = (D) => {
    if (a) {
      o(Math.round(Number(D.target.value)));
      return;
    }
    w.onChange(D);
  }, m = M(!1), N = M(!1), A = (D) => {
    D.button === 0 && (m.current = !0, N.current = !1);
  }, L = (D) => {
    if (!m.current) return;
    const _ = D.currentTarget.getBoundingClientRect(), Z = D.clientX > _.right + $o ? "max" : D.clientX < _.left - $o ? "min" : null;
    if (!Z) {
      N.current = !1;
      return;
    }
    N.current || (Z === "max" && n >= d ? (N.current = !0, P("max")) : Z === "min" && n <= u && (N.current = !0, P("min")));
  }, I = () => {
    m.current = !1, N.current = !1;
  }, j = (D) => {
    const _ = D.key === "ArrowRight" || D.key === "ArrowUp" || D.key === "PageUp", Z = D.key === "ArrowLeft" || D.key === "ArrowDown" || D.key === "PageDown";
    _ && n >= d ? P("max") : Z && n <= u && P("min"), w.onKeyDown(D);
  }, C = () => {
    g.current = !1;
    const D = Number(f);
    if (f.trim() === "" || !Number.isFinite(D)) {
      p(et(n, a, h));
      return;
    }
    o(a ? Math.round(D) : D);
  }, re = (D, _, Z) => {
    const Ie = a ? Math.round(D + _ * Z) : ft(D + _ * Z, Z);
    return Ie !== n && o(Ie), Ie;
  }, ce = M(null), oe = M(0), W = (D) => {
    D.button === 0 && (ce.current = { x: D.clientX, from: n, step: h, scrubbing: !1 });
  }, J = (D) => {
    const _ = ce.current;
    if (!_) return;
    const Z = D.clientX - _.x;
    if (!_.scrubbing) {
      if (Math.abs(Z) < Bo) return;
      _.scrubbing = !0, D.currentTarget.setPointerCapture?.(D.pointerId);
    }
    const Ie = n;
    if (re(_.from, Math.round(Z / Bo), _.step) === Ie) return;
    const Ce = Date.now();
    Ce - oe.current >= qg && (oe.current = Ce, $e("tick"));
  }, H = (D) => {
    const _ = ce.current;
    ce.current = null, _?.scrubbing && D.currentTarget.hasPointerCapture?.(D.pointerId) && D.currentTarget.releasePointerCapture(D.pointerId);
  };
  return /* @__PURE__ */ v("div", { className: "flex flex-col gap-1 px-4", children: [
    /* @__PURE__ */ v("div", { className: "flex items-baseline justify-between gap-2", children: [
      /* @__PURE__ */ v("div", { className: "flex min-w-0 items-center gap-1.5", children: [
        /* @__PURE__ */ c(
          "label",
          {
            htmlFor: e,
            title: t.description,
            className: R("mono-caption min-w-0 truncate", i ? "font-medium text-ink" : "text-muted"),
            children: Bt(t.name)
          }
        ),
        i ? /* @__PURE__ */ c(uc, { param: t, onReset: () => o(t.default) }) : null
      ] }),
      /* @__PURE__ */ v("div", { className: "flex shrink-0 items-baseline gap-1.5", children: [
        w.activeLabel ? /* @__PURE__ */ c("span", { className: "mono-caption text-faint", children: w.activeLabel }) : null,
        /* @__PURE__ */ c(
          "input",
          {
            value: f,
            onChange: (D) => {
              g.current = !0, p(D.target.value);
            },
            onBlur: C,
            onPointerDown: W,
            onPointerMove: J,
            onPointerUp: H,
            onPointerCancel: H,
            onKeyDown: (D) => {
              if (D.key === "Enter" && C(), D.key === "Escape") {
                const _ = ce.current;
                ce.current = null, g.current = !1, _?.scrubbing ? o(_.from) : p(et(n, a, h));
              }
              (D.key === "ArrowUp" || D.key === "ArrowDown") && (D.preventDefault(), re(n, (D.key === "ArrowUp" ? 1 : -1) * (D.shiftKey ? 10 : 1), h));
            },
            inputMode: a ? "numeric" : "decimal",
            "aria-label": `${t.name} value`,
            className: R(
              "mono-value w-16 cursor-ew-resize rounded-control border-0 bg-transparent p-0 text-right focus:bg-raised focus:outline-1 focus:outline-accent",
              i ? "text-accent-ink" : "text-ink"
            )
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ v(
      B.div,
      {
        className: "relative",
        animate: { x: k },
        transition: { duration: x ? 0 : U.tick, ease: Io },
        children: [
          /* @__PURE__ */ c(
            "input",
            {
              id: e,
              type: "range",
              min: u,
              max: d,
              step: h,
              value: n,
              onChange: S,
              onKeyDown: j,
              onPointerDown: A,
              onPointerMove: L,
              onPointerUp: I,
              onPointerCancel: I,
              onLostPointerCapture: I,
              "aria-label": Bt(t.name),
              "aria-valuetext": `${n}`,
              className: "param-slider w-full",
              style: { "--pct": d === u ? 0 : (n - u) / (d - u) }
            }
          ),
          /* @__PURE__ */ c(_g, { detents: w.detents, min: u, max: d, activeDetent: w.activeDetent })
        ]
      }
    ),
    /* @__PURE__ */ c(xe, { children: T ? /* @__PURE__ */ c(
      B.p,
      {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: x ? 0 : U.settle, ease: Io },
        className: "mono-caption text-accent-ink",
        children: T.end === "max" ? `${et(d, a, h)} ${Oo} · widest this will go` : `${et(u, a, h)} ${Oo} · thinnest this will go`
      }
    ) : null })
  ] });
}
function Xg({
  id: e,
  param: t,
  value: n,
  dirty: i,
  onValue: s
}) {
  return /* @__PURE__ */ v("div", { className: "flex items-center gap-2 px-4 py-1", children: [
    /* @__PURE__ */ c(
      "label",
      {
        htmlFor: e,
        title: t.description,
        className: R("mono-caption min-w-0 truncate", i ? "font-medium text-ink" : "text-muted"),
        children: Bt(t.name)
      }
    ),
    i ? /* @__PURE__ */ c(uc, { param: t, onReset: () => s(t.default) }) : null,
    /* @__PURE__ */ c("span", { className: "flex-1" }),
    /* @__PURE__ */ c(
      "button",
      {
        id: e,
        type: "button",
        role: "switch",
        "aria-checked": n,
        "aria-label": Bt(t.name),
        onClick: () => s(!n),
        className: R(
          "relative h-4 w-7 shrink-0 rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
          n ? "bg-accent" : "bg-line"
        ),
        children: /* @__PURE__ */ c(
          "span",
          {
            className: R(
              "absolute top-0.5 size-3 rounded-full bg-ground transition-[left]",
              n ? "left-3.5" : "left-0.5"
            )
          }
        )
      }
    )
  ] });
}
function Ay({
  params: e,
  measurements: t,
  nozzle: n,
  values: i,
  onChange: s,
  onApply: r,
  building: o,
  applying: a,
  stats: l,
  error: u,
  note: d
}) {
  const h = le(() => e.filter(Ii), [e]), f = le(() => e.filter((y) => !Ii(y)), [e]), p = h.filter((y) => y.kind === "bool"), g = h.filter((y) => y.kind !== "bool"), x = le(() => Gg(e, i), [e, i]), b = Object.keys(x).length, w = Se(), T = (y, k) => {
    s({ ...i, [y]: k });
  };
  return h.length === 0 ? null : /* @__PURE__ */ v("div", { className: "flex min-h-0 flex-1 flex-col", role: "group", "aria-label": "Part parameters", children: [
    u ? /* @__PURE__ */ v("div", { className: "border-b border-line-soft bg-fail-wash px-4 py-2.5", children: [
      /* @__PURE__ */ v("p", { className: "mono-label flex items-center gap-2 text-fail", children: [
        /* @__PURE__ */ c($, { name: "warning" }),
        "Build failed at these values"
      ] }),
      /* @__PURE__ */ c("p", { className: "mt-1 text-xs leading-4 text-ink-soft", children: u }),
      /* @__PURE__ */ c("p", { className: "mt-0.5 text-xs leading-4 text-muted", children: "Showing the last part that built." })
    ] }) : null,
    /* @__PURE__ */ v("div", { className: "flex min-h-0 flex-1 flex-col overflow-y-auto pb-3", children: [
      f.length > 0 ? /* @__PURE__ */ v(G, { children: [
        /* @__PURE__ */ c(jo, { children: "Pinned by spec" }),
        /* @__PURE__ */ c("dl", { className: "flex flex-col", children: f.map((y) => /* @__PURE__ */ v("div", { className: "flex items-center gap-[9px] px-4 py-1.5", title: y.description, children: [
          /* @__PURE__ */ c("span", { className: "text-muted", children: /* @__PURE__ */ c($, { name: "lock" }) }),
          /* @__PURE__ */ c("dt", { className: "mono-id min-w-0 flex-1 truncate uppercase text-muted [letter-spacing:0.06em]", children: Bt(y.name) }),
          /* @__PURE__ */ c("dd", { className: "mono-value text-muted", children: String(i[y.name] ?? y.default) })
        ] }, y.name)) })
      ] }) : null,
      /* @__PURE__ */ c(jo, { children: "Yours to drag" }),
      /* @__PURE__ */ v("div", { className: "flex flex-col gap-3", children: [
        p.map((y) => /* @__PURE__ */ c(
          Xg,
          {
            id: `${w}${y.name}`,
            param: y,
            value: i[y.name] ?? y.default,
            dirty: y.name in x,
            onValue: (k) => T(y.name, k)
          },
          y.name
        )),
        g.map((y) => /* @__PURE__ */ c(
          Yg,
          {
            id: `${w}${y.name}`,
            param: y,
            value: i[y.name] ?? y.default,
            dirty: y.name in x,
            measurements: t,
            nozzle: n,
            onValue: (k) => T(y.name, k)
          },
          y.name
        ))
      ] })
    ] }),
    l?.size_mm ? /* @__PURE__ */ c("div", { className: "chrome shrink-0 border-t border-line-soft px-4 py-2", children: /* @__PURE__ */ v("span", { className: "mono-caption text-muted", children: [
      l.size_mm.map((y) => Math.round(y * 10) / 10).join(" × "),
      " mm",
      o ? " · rebuilding" : null
    ] }) }) : null,
    /* @__PURE__ */ c(
      "p",
      {
        role: "status",
        className: d ? "mx-4 mb-3 rounded-content bg-raised px-3 py-2 text-xs leading-4 text-ink-soft" : "sr-only",
        children: d
      }
    ),
    b > 0 ? /* @__PURE__ */ v("div", { className: "chrome mx-4 mb-3 flex h-9 shrink-0 items-center gap-2 rounded-content bg-accent-wash px-3", children: [
      /* @__PURE__ */ c("span", { className: "size-1.5 shrink-0 rounded-full bg-accent" }),
      /* @__PURE__ */ v("span", { className: "mono-id flex-1 uppercase text-accent-ink tabular-nums [letter-spacing:0.08em]", children: [
        b,
        " ",
        b === 1 ? "change" : "changes"
      ] }),
      /* @__PURE__ */ c(
        "button",
        {
          type: "button",
          onClick: () => s({}),
          className: "mono-label rounded-control px-2 py-1 text-ink-soft transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-accent",
          children: "Reset"
        }
      ),
      /* @__PURE__ */ c("span", { className: "inline-flex", title: "Save these values as the part's defaults.", children: /* @__PURE__ */ c(
        Ug,
        {
          label: "Apply",
          pendingLabel: "Applying",
          successLabel: "Applied",
          errorLabel: "Try again",
          resetAfter: 1400,
          variant: "ink",
          disabled: a,
          onAction: () => r(x)
        }
      ) })
    ] }) : null
  ] });
}
const dc = ji(function({ anchor: t, width: n, align: i = "right", gap: s = 6, className: r, children: o, ...a }, l) {
  const [u, d] = O(null), h = q(() => {
    const f = t.current?.getBoundingClientRect();
    if (!f) return;
    const p = i === "right" ? f.right - n : f.left;
    d({
      left: Math.max(8, Math.min(p, window.innerWidth - n - 8)),
      bottom: Math.max(8, window.innerHeight - f.top + s)
    });
  }, [t, n, i, s]);
  return $t(h, [h]), F(() => (window.addEventListener("resize", h), window.addEventListener("scroll", h, !0), () => {
    window.removeEventListener("resize", h), window.removeEventListener("scroll", h, !0);
  }), [h]), typeof document > "u" ? null : ea(
    /* @__PURE__ */ c(
      "div",
      {
        ref: l,
        style: { position: "fixed", left: u?.left ?? 0, bottom: u?.bottom ?? 0, width: n },
        className: r,
        ...a,
        children: o
      }
    ),
    document.body
  );
}), Zg = [
  { format: "3mf", caption: "Print-ready, keeps units and orientation.", recommended: !0 },
  { format: "stl", caption: "Print-ready mesh. Works in every slicer." },
  { format: "step", caption: "Solid model, for another CAD tool." }
];
function Qg(e) {
  if (e.state === "queued") return "Estimate · slicing…";
  if (e.state === "failed") return `Estimate · ${e.error ?? "unavailable"}`;
  const t = [
    e.grams ? `${Math.round(e.grams)} g` : null,
    e.seconds ? `${(e.seconds / 3600).toFixed(1)} hr` : null
  ].filter(Boolean);
  return `Estimate · ${t.length ? t.join(" · ") : "unavailable"}`;
}
function Ny({ partId: e, export: t, status: n, revision: i, runId: s }) {
  const [r, o] = O(!1), [a, l] = O(null), [u, d] = O(null), [h, f] = O(null), p = M(null), g = M(null), x = M(null), b = M(null), w = M(0), T = M({ partId: e, revision: i, runId: s });
  F(() => {
    const k = T.current;
    k.partId === e && Object.is(k.revision, i) && Object.is(k.runId, s) || (T.current = { partId: e, revision: i, runId: s }, w.current += 1, l(null), d(null), f(null));
  }, [e, i, s]), F(() => {
    if (!r) return;
    const k = (P) => {
      const S = P.target;
      p.current?.contains(S) || b.current?.contains(S) || o(!1);
    }, E = (P) => {
      if (P.key === "Escape") {
        o(!1), g.current?.focus();
        return;
      }
      if (P.key !== "ArrowDown" && P.key !== "ArrowUp") return;
      const S = Array.from(x.current?.querySelectorAll('[role="menuitem"]') ?? []);
      if (S.length === 0) return;
      P.preventDefault();
      const m = P.key === "ArrowDown" ? 1 : -1, N = S.indexOf(document.activeElement), A = N === -1 ? m === 1 ? 0 : S.length - 1 : (N + m + S.length) % S.length;
      S[A].focus();
    };
    return document.addEventListener("pointerdown", k), document.addEventListener("keydown", E), () => {
      document.removeEventListener("pointerdown", k), document.removeEventListener("keydown", E);
    };
  }, [r]);
  const y = async (k) => {
    const E = ++w.current;
    l(k), f(null), d(null);
    try {
      const P = await t(k);
      if (E !== w.current) return;
      d({ format: k, result: P });
    } catch (P) {
      if (E !== w.current) return;
      f(P instanceof Error ? P.message : "The export did not finish.");
    } finally {
      E === w.current && l(null);
    }
  };
  return /* @__PURE__ */ v("div", { ref: p, className: "relative flex-1", children: [
    /* @__PURE__ */ v(
      "button",
      {
        ref: g,
        type: "button",
        "aria-haspopup": "menu",
        "aria-expanded": r,
        onClick: () => o((k) => !k),
        className: "chrome btn-label inline-flex h-9 w-full items-center justify-center gap-2 rounded-control bg-accent px-3 text-white transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        children: [
          /* @__PURE__ */ c($, { name: "download" }),
          a ? "Preparing…" : "Download",
          /* @__PURE__ */ c($, { name: "chevron-down" })
        ]
      }
    ),
    r ? /* @__PURE__ */ v(
      dc,
      {
        ref: b,
        anchor: g,
        width: 254,
        align: "left",
        gap: 8,
        className: "z-30 overflow-hidden rounded-content border border-panel-edge bg-ground shadow-[var(--shadow-panel)]",
        children: [
          /* @__PURE__ */ v("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft px-3", children: [
            /* @__PURE__ */ c("span", { className: "mono-label text-muted", children: "Download" }),
            i != null ? /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: Ot(i) }) : null
          ] }),
          h ? /* @__PURE__ */ v("div", { className: "border-b border-line-soft bg-fail-wash px-3 py-2 text-[11px] leading-4 text-ink-soft", children: [
            /* @__PURE__ */ c("p", { className: "mono-label text-fail", children: "Export failed" }),
            /* @__PURE__ */ c("p", { className: "mt-0.5", children: h })
          ] }) : null,
          /* @__PURE__ */ c(
            "div",
            {
              ref: x,
              role: "menu",
              "aria-label": "Download format",
              className: "flex flex-col py-1",
              children: Zg.map((k) => {
                const E = a === k.format;
                return /* @__PURE__ */ v(
                  "button",
                  {
                    type: "button",
                    role: "menuitem",
                    disabled: a !== null,
                    onClick: () => {
                      y(k.format);
                    },
                    className: R(
                      "flex w-full flex-col gap-0.5 px-3 py-2 text-left transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none disabled:opacity-60 disabled:hover:bg-transparent",
                      k.recommended && "bg-raised/60"
                    ),
                    children: [
                      /* @__PURE__ */ v("span", { className: "flex w-full items-center", children: [
                        /* @__PURE__ */ c("span", { className: "mono-value uppercase text-ink", children: k.format }),
                        E ? /* @__PURE__ */ v("span", { className: "mono-caption ml-auto flex items-center gap-1.5 text-muted", children: [
                          /* @__PURE__ */ c("span", { className: "size-1.5 rounded-full bg-accent" }),
                          "preparing"
                        ] }) : k.recommended ? /* @__PURE__ */ c("span", { className: "mono-caption ml-auto text-accent-ink", children: "Recommended" }) : null
                      ] }),
                      /* @__PURE__ */ c("span", { className: "text-xs leading-4 text-ink-soft", children: k.caption })
                    ]
                  },
                  k.format
                );
              })
            }
          ),
          u ? /* @__PURE__ */ v(
            "a",
            {
              href: u.result.url,
              download: u.result.filename,
              onClick: () => o(!1),
              className: "chrome btn-label flex items-center gap-2 border-t border-line-soft bg-ink px-3 py-2 text-white transition-colors hover:bg-ink-soft",
              children: [
                /* @__PURE__ */ c($, { name: "download" }),
                "Save ",
                u.result.filename ?? `the ${u.format.toUpperCase()}`
              ]
            }
          ) : null,
          n ? /* @__PURE__ */ c("div", { className: "chrome border-t border-line-soft bg-raised px-3 py-2", children: /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: Qg(n) }) }) : null
        ]
      }
    ) : null
  ] });
}
function Py({
  printers: e,
  current: t,
  defaultName: n,
  onPick: i,
  onAdd: s,
  onManage: r,
  triggerRef: o,
  onClose: a
}) {
  const l = M(null);
  return F(() => {
    const u = (h) => {
      const f = h.target;
      l.current?.contains(f) || o.current?.contains(f) || a();
    }, d = (h) => {
      h.key === "Escape" && a();
    };
    return document.addEventListener("pointerdown", u), document.addEventListener("keydown", d), () => {
      document.removeEventListener("pointerdown", u), document.removeEventListener("keydown", d);
    };
  }, [a, o]), /* @__PURE__ */ v(
    dc,
    {
      ref: l,
      anchor: o,
      width: 254,
      align: "right",
      gap: 6,
      role: "menu",
      "aria-label": "Print on",
      className: "z-30 overflow-hidden rounded-[6px] border border-panel-edge bg-ground shadow-[var(--shadow-panel)]",
      children: [
        /* @__PURE__ */ v("div", { className: "flex h-6 items-center justify-between px-3 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase", children: [
          /* @__PURE__ */ c("span", { children: "Print on" }),
          /* @__PURE__ */ c("span", { children: "This part" })
        ] }),
        e.map((u) => {
          const d = u.name === t;
          return /* @__PURE__ */ v(
            "button",
            {
              type: "button",
              role: "menuitemradio",
              "aria-checked": d,
              onClick: () => i(u.name),
              className: R(
                "chrome flex h-7 w-full items-center gap-2 px-3 text-left font-mono text-[10.5px] leading-4 transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none",
                d ? "text-ink" : "text-ink-soft hover:text-ink"
              ),
              children: [
                /* @__PURE__ */ c("span", { className: "flex size-3 shrink-0 items-center justify-center", children: d ? /* @__PURE__ */ c($, { name: "check" }) : null }),
                /* @__PURE__ */ c("span", { className: "min-w-0 flex-1 truncate", children: u.label }),
                u.name === n ? /* @__PURE__ */ c("span", { className: "shrink-0 rounded-[2px] border border-line px-1 font-mono text-[9px] leading-[14px] tracking-[0.08em] text-muted uppercase", children: "Default" }) : null
              ]
            },
            u.name
          );
        }),
        /* @__PURE__ */ c("div", { className: "border-t border-line-soft", role: "separator" }),
        /* @__PURE__ */ v(
          "button",
          {
            type: "button",
            role: "menuitem",
            onClick: s,
            className: "chrome flex h-7 w-full items-center gap-2 px-3 text-left font-mono text-[10.5px] leading-4 text-accent-ink transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none",
            children: [
              /* @__PURE__ */ c("span", { className: "size-3 shrink-0" }),
              /* @__PURE__ */ c("span", { className: "min-w-0 flex-1 truncate", children: "+ Add a printer" })
            ]
          }
        ),
        r ? /* @__PURE__ */ v(
          "button",
          {
            type: "button",
            role: "menuitem",
            onClick: r,
            className: "chrome flex w-full items-center gap-2 border-t border-line-soft bg-raised px-3 py-2 text-left font-mono text-[9.5px] leading-3 tracking-[0.08em] text-muted uppercase transition-colors hover:text-ink focus-visible:outline-none",
            children: [
              /* @__PURE__ */ c("span", { className: "min-w-0 flex-1 truncate", children: "Manage printers in Settings" }),
              /* @__PURE__ */ c("span", { className: "shrink-0 rotate-180", children: /* @__PURE__ */ c($, { name: "chevron-left" }) })
            ]
          }
        ) : null
      ]
    }
  );
}
function $s({
  label: e,
  trailing: t,
  inset: n = 18
}) {
  return /* @__PURE__ */ v(
    "div",
    {
      className: `chrome flex h-[30px] shrink-0 items-center justify-between border-b border-line-soft ${n === 16 ? "px-4" : "px-[18px]"}`,
      children: [
        /* @__PURE__ */ c("div", { className: "mono-label shrink-0 text-muted", children: e }),
        t ? /* @__PURE__ */ c("div", { className: "mono-caption min-w-0 text-muted tabular-nums [letter-spacing:0.1em]", children: t }) : null
      ]
    }
  );
}
const Jg = (e) => e && e.length === 3 ? e.map((t) => Math.round(t)).join(" × ") : "";
function My({
  catalogue: e,
  owned: t,
  busy: n,
  error: i,
  onAdd: s,
  onClose: r
}) {
  const [o, a] = O(""), [l, u] = O(null), d = le(() => new Set(t), [t]);
  F(() => {
    const f = (p) => {
      p.key === "Escape" && r();
    };
    return window.addEventListener("keydown", f), () => window.removeEventListener("keydown", f);
  }, [r]);
  const h = le(() => {
    const f = o.trim().toLowerCase(), p = f ? e.filter((b) => b.label.toLowerCase().includes(f)) : e, g = [], x = /* @__PURE__ */ new Map();
    for (const b of p)
      x.has(b.brand) || (x.set(b.brand, []), g.push(b.brand)), x.get(b.brand).push(b);
    return g.map((b) => ({ brand: b, rows: x.get(b) }));
  }, [e, o]);
  return /* @__PURE__ */ c(
    "div",
    {
      className: "fixed inset-0 z-50 flex items-center justify-center bg-ink/30 p-6",
      onClick: (f) => f.target === f.currentTarget && r(),
      children: /* @__PURE__ */ v(
        "div",
        {
          className: "panel flex max-h-full w-[520px] flex-col overflow-hidden",
          role: "dialog",
          "aria-modal": "true",
          "aria-label": "Add a printer",
          children: [
            /* @__PURE__ */ c(
              $s,
              {
                label: "Add a printer",
                inset: 16,
                trailing: /* @__PURE__ */ c(Bs, { icon: "xmark", label: "Close", onClick: r, className: "-mr-2" })
              }
            ),
            /* @__PURE__ */ v("div", { className: "flex shrink-0 flex-col gap-3 px-5 pt-4", children: [
              /* @__PURE__ */ c("p", { className: "text-[13.5px] leading-[18px] text-ink-soft", children: "Pick the machine on your bench. Checks use its bed size; the slicer brings its own profile." }),
              /* @__PURE__ */ v("div", { className: "flex h-8 shrink-0 items-center gap-2 rounded-[3px] border border-line bg-ground px-2.5", children: [
                /* @__PURE__ */ c("span", { className: "shrink-0 text-faint", children: /* @__PURE__ */ c($, { name: "search" }) }),
                /* @__PURE__ */ c(
                  "input",
                  {
                    name: "printer-search",
                    "aria-label": "Search printers",
                    placeholder: "SEARCH PRINTERS",
                    value: o,
                    onChange: (f) => a(f.target.value),
                    autoFocus: !0,
                    className: "min-w-0 flex-1 bg-transparent font-mono text-[10.5px] tracking-[0.08em] text-ink uppercase placeholder:text-faint focus:outline-none"
                  }
                )
              ] })
            ] }),
            /* @__PURE__ */ c("div", { className: "mt-3 min-h-0 flex-1 overflow-y-auto border-t border-line-soft", children: h.length === 0 ? /* @__PURE__ */ c("p", { className: "px-5 py-4 text-[13px] leading-[18px] text-muted", children: "No printer matches that." }) : h.map((f) => /* @__PURE__ */ v("div", { className: "flex flex-col", children: [
              /* @__PURE__ */ c("div", { className: "flex h-6 items-center bg-raised px-5 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase", children: f.brand }),
              f.rows.map((p) => {
                const g = d.has(p.name), x = l === p.name;
                return /* @__PURE__ */ v(
                  "button",
                  {
                    type: "button",
                    disabled: g,
                    "aria-pressed": x,
                    onClick: () => u(p.name),
                    className: R(
                      "chrome flex h-[30px] w-full items-center gap-2 px-5 text-left transition-colors focus-visible:outline-none",
                      g ? "cursor-default text-faint" : x ? "bg-accent-wash text-ink" : "text-ink-soft hover:bg-raised hover:text-ink"
                    ),
                    children: [
                      /* @__PURE__ */ c("span", { className: "flex size-3 shrink-0 items-center justify-center", children: x ? /* @__PURE__ */ c($, { name: "check" }) : null }),
                      /* @__PURE__ */ c("span", { className: "min-w-0 flex-1 truncate font-mono text-[11px] leading-4", children: p.label }),
                      /* @__PURE__ */ c("span", { className: "shrink-0 font-mono text-[10px] leading-4 tracking-[0.08em] text-muted tabular-nums", children: g ? "On your bench" : Jg(p.bed) })
                    ]
                  },
                  p.name
                );
              })
            ] }, f.brand)) }),
            i ? /* @__PURE__ */ c("p", { className: "shrink-0 bg-fail-wash px-5 py-2 text-[12px] leading-4 text-fail", role: "alert", children: i }) : null,
            /* @__PURE__ */ v("div", { className: "flex shrink-0 items-center gap-4 border-t border-line-soft px-5 py-4", children: [
              /* @__PURE__ */ c("p", { className: "min-w-0 flex-1 text-[12px] leading-4 text-muted", children: "Not listed? Pick the one with the closest bed size. That is all the checks use." }),
              /* @__PURE__ */ c(Te, { size: "md", className: "px-3.5", onClick: r, children: "Cancel" }),
              /* @__PURE__ */ c(
                Te,
                {
                  variant: "accent",
                  size: "md",
                  className: "px-3.5",
                  disabled: !l || n,
                  onClick: () => l && s(l),
                  children: n ? "Adding" : "Add printer"
                }
              )
            ] })
          ]
        }
      )
    }
  );
}
const e0 = "" + new URL("nurb-lockup.svg", import.meta.url).href, t0 = "" + new URL("nurb-mark-16.svg", import.meta.url).href, n0 = "" + new URL("nurb-mark-outline.svg", import.meta.url).href, i0 = "" + new URL("nurb-mark-small.svg", import.meta.url).href, s0 = "" + new URL("favicon.svg", import.meta.url).href, r0 = "" + new URL("auth-plane.svg", import.meta.url).href, o0 = "" + new URL("ghost-bracket.svg", import.meta.url).href, a0 = "" + new URL("404-squiggle.svg", import.meta.url).href, js = { lockup: e0, mark: t0, markOutline: n0, markSmall: i0, favicon: s0, authPlane: r0, ghostBracket: o0, squiggle: a0 }, Tt = 240, nn = 148;
function Be(e, t, n) {
  return [(e - t) * 0.866, (e + t) * 0.5 - n];
}
function l0({ bbox: e, ghost: t = !1, className: n }) {
  const i = e && e.length === 3 && e.every((A) => A > 0) ? e : null, s = i ?? [1, 1, 1], r = Math.max(...s), [o, a, l] = s.map((A) => A / r), u = [
    Be(0, 0, 0),
    Be(o, 0, 0),
    Be(o, a, 0),
    Be(0, a, 0),
    Be(0, 0, l),
    Be(o, 0, l),
    Be(o, a, l),
    Be(0, a, l)
  ], d = u.map((A) => A[0]), h = u.map((A) => A[1]), f = Math.min(...d), p = Math.max(...d), g = Math.min(...h), x = Math.max(...h), b = Math.min((Tt - 60) / (p - f), (nn - 40) / (x - g)), w = Tt / 2 - (f + p) / 2 * b, T = nn / 2 - (g + x) / 2 * b, y = (A) => `${(u[A][0] * b + w).toFixed(1)},${(u[A][1] * b + T).toFixed(1)}`, k = `${y(4)} ${y(5)} ${y(6)} ${y(7)}`, E = `${y(3)} ${y(2)} ${y(6)} ${y(7)}`, P = `${y(1)} ${y(2)} ${y(6)} ${y(5)}`, S = Tt / 2, m = Math.max(...u.map((A) => A[1])) * b + T + 6, N = (p - f) * b / 2 + 8;
  return t || !i ? /* @__PURE__ */ c("svg", { viewBox: `0 0 ${Tt} ${nn}`, className: n, "aria-hidden": "true", children: /* @__PURE__ */ v("g", { fill: "none", stroke: "var(--color-panel-edge)", strokeWidth: "1.5", strokeLinejoin: "round", strokeDasharray: "5 4", children: [
    /* @__PURE__ */ c("polygon", { points: k }),
    /* @__PURE__ */ c("polygon", { points: E }),
    /* @__PURE__ */ c("polygon", { points: P })
  ] }) }) : /* @__PURE__ */ v("svg", { viewBox: `0 0 ${Tt} ${nn}`, className: n, "aria-hidden": "true", children: [
    /* @__PURE__ */ c("ellipse", { cx: S, cy: m, rx: N, ry: N * 0.16, fill: "var(--color-raised)" }),
    /* @__PURE__ */ v("g", { stroke: "var(--color-part-edge)", strokeWidth: "1.2", strokeLinejoin: "round", children: [
      /* @__PURE__ */ c("polygon", { points: k, fill: "var(--color-part-top)" }),
      /* @__PURE__ */ c("polygon", { points: E, fill: "var(--color-part-front)" }),
      /* @__PURE__ */ c("polygon", { points: P, fill: "var(--color-part-side)" })
    ] })
  ] });
}
const c0 = Y.out;
function u0({
  label: e,
  items: t,
  align: n = "right",
  className: i,
  menuClassName: s,
  trigger: r,
  footer: o,
  portal: a,
  disabled: l,
  triggerClassName: u,
  onOpenChange: d,
  filter: h
}) {
  const [f, p] = O(!1), [g, x] = O(""), [b, w] = O(), T = M(null), y = M(null), k = M(null), E = Se(), P = t.some((A) => A.checked !== void 0), S = M(d);
  S.current = d, F(() => {
    S.current?.(f), f || x("");
  }, [f]);
  const m = g.trim().toLowerCase(), N = m ? t.filter((A) => typeof A.label == "string" && A.label.toLowerCase().includes(m)) : t;
  return $t(() => {
    if (!f || !a) return;
    const A = k.current?.getBoundingClientRect();
    A && w(
      n === "right" ? {
        position: "fixed",
        top: A.bottom + 4,
        right: window.innerWidth - A.right
      } : { position: "fixed", top: A.bottom + 4, left: A.left }
    );
  }, [f, a, n]), F(() => {
    if (!f) return;
    const A = (I) => {
      const j = I.target;
      !T.current?.contains(j) && !y.current?.contains(j) && p(!1);
    }, L = (I) => {
      I.key === "Escape" && (p(!1), k.current?.focus());
    };
    return document.addEventListener("pointerdown", A), document.addEventListener("keydown", L), () => {
      document.removeEventListener("pointerdown", A), document.removeEventListener("keydown", L);
    };
  }, [f]), /* @__PURE__ */ v("div", { ref: T, className: R("relative", i), children: [
    /* @__PURE__ */ c(
      "button",
      {
        ref: k,
        type: "button",
        "aria-label": e,
        title: e,
        "aria-haspopup": "menu",
        "aria-expanded": f,
        "aria-controls": E,
        disabled: l,
        onClick: (A) => {
          A.preventDefault(), A.stopPropagation(), p((L) => !L);
        },
        onKeyDown: (A) => A.stopPropagation(),
        className: R(
          "chrome inline-flex items-center justify-center rounded-[3px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          u ?? (r ? "rounded-full" : "size-5"),
          !r && (f ? "bg-raised text-ink" : "text-muted hover:bg-raised hover:text-ink")
        ),
        children: r ? r(f) : /* @__PURE__ */ c($, { name: "dots" })
      }
    ),
    f0(
      a,
      /* @__PURE__ */ c(xe, { children: f ? /* @__PURE__ */ v(
        d0,
        {
          id: E,
          ref: y,
          style: a ? b : void 0,
          className: R(
            "z-30 min-w-[168px] overflow-hidden rounded-[6px] border border-panel-edge bg-ground shadow-[var(--shadow-panel)]",
            o ? "pt-1" : "py-1",
            !a && "absolute top-full mt-1",
            !a && (n === "right" ? "right-0" : "left-0"),
            s
          ),
          children: [
            h ? /* @__PURE__ */ v("div", { className: "sticky top-0 z-10 -mt-1 mb-1 flex h-8 items-center gap-2 border-b border-line-soft bg-ground px-3", children: [
              /* @__PURE__ */ c($, { name: "search", className: "text-muted" }),
              /* @__PURE__ */ c(
                "input",
                {
                  autoFocus: !0,
                  value: g,
                  onChange: (A) => x(A.target.value),
                  onKeyDown: (A) => {
                    A.key === "Enter" && N[0] && (N[0].onSelect(), p(!1));
                  },
                  placeholder: h,
                  "aria-label": h,
                  className: "mono-id min-w-0 flex-1 bg-transparent text-ink outline-none placeholder:text-faint"
                }
              )
            ] }) : null,
            h && N.length === 0 ? /* @__PURE__ */ c("div", { className: "mono-id flex h-7 items-center px-3 text-faint", children: "Nothing matches" }) : null,
            N.map((A, L) => /* @__PURE__ */ v($i, { children: [
              A.section && A.section !== N[L - 1]?.section ? /* @__PURE__ */ v(G, { children: [
                L > 0 ? /* @__PURE__ */ c("div", { className: "my-1 border-t border-line-soft", role: "separator" }) : null,
                /* @__PURE__ */ c("div", { className: "flex h-6 items-center px-3 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase", children: A.section })
              ] }) : null,
              /* @__PURE__ */ v(
                "button",
                {
                  type: "button",
                  role: P ? "menuitemradio" : "menuitem",
                  "aria-checked": P ? !!A.checked : void 0,
                  disabled: A.disabled,
                  title: A.title,
                  onClick: (I) => {
                    I.preventDefault(), I.stopPropagation(), A.onSelect(), A.keepOpen || p(!1);
                  },
                  className: R(
                    "chrome mono-id flex h-7 w-full items-center gap-2 px-3 text-left transition-colors focus-visible:bg-raised focus-visible:outline-none disabled:text-faint disabled:hover:bg-transparent",
                    A.separated && "mt-1 border-t border-line-soft pt-px",
                    A.tone === "danger" ? "text-fail hover:bg-fail-wash" : A.checked ? "text-ink hover:bg-raised" : "text-ink-soft hover:bg-raised hover:text-ink"
                  ),
                  children: [
                    P ? /* @__PURE__ */ c("span", { className: "flex size-3 shrink-0 items-center justify-center", children: A.checked ? /* @__PURE__ */ c($, { name: "check" }) : null }) : null,
                    A.icon ? /* @__PURE__ */ c($, { name: A.icon }) : null,
                    /* @__PURE__ */ c("span", { className: "min-w-0 flex-1 truncate", children: A.label }),
                    A.trailing ? /* @__PURE__ */ c("span", { className: "shrink-0", children: A.trailing }) : null
                  ]
                }
              )
            ] }, L)),
            o ? /* @__PURE__ */ c("div", { className: "mt-1 border-t border-line-soft bg-raised px-3 py-2 font-mono text-[9.5px] leading-3 tracking-[0.08em] text-muted uppercase", children: o }) : null
          ]
        }
      ) : null })
    )
  ] });
}
function d0({
  id: e,
  ref: t,
  style: n,
  className: i,
  children: s
}) {
  const r = hp();
  return /* @__PURE__ */ c(
    B.div,
    {
      id: e,
      ref: t,
      role: r ? "menu" : "presentation",
      "aria-hidden": r ? void 0 : !0,
      initial: { opacity: 0, y: -4 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -4 },
      transition: { duration: U.tick, ease: c0 },
      style: n,
      className: i,
      children: s
    }
  );
}
function f0(e, t) {
  return e && typeof document < "u" ? ea(t, document.body) : t;
}
const fc = Y.out, hc = 2.5, sn = 20, h0 = 10;
function p0({
  onConfirm: e,
  holdMs: t = 1800,
  disabled: n = !1
}) {
  const [i, s] = O(0), [r, o] = O("idle"), a = M("idle"), l = M(!1), u = M(0), d = M(0), h = M(0), f = M(null), p = M(e);
  p.current = e;
  const g = q((y) => {
    a.current = y, o(y);
  }, []), x = q(() => {
    cancelAnimationFrame(h.current), h.current = 0, l.current = !1, u.current = 0, f.current = null, s(0), g("idle");
  }, [g]), b = q(
    (y) => {
      if (n || a.current === "committed" || a.current === "holding" || (f.current = y ?? null, l.current = !0, g("holding"), $e("press"), h.current)) return;
      d.current = performance.now();
      const k = (E) => {
        const P = Math.min(64, E - d.current);
        if (d.current = E, u.current += l.current ? P : -P * hc, u.current >= t) {
          h.current = 0, u.current = t, l.current = !1, f.current = null, s(sn), g("committed"), p.current();
          return;
        }
        if (u.current <= 0) {
          h.current = 0, u.current = 0, f.current = null, s(0), g("idle");
          return;
        }
        const S = Math.min(sn, Math.floor(u.current / t * sn));
        s((m) => m === S ? m : S), h.current = requestAnimationFrame(k);
      };
      h.current = requestAnimationFrame(k);
    },
    [n, t, g]
  ), w = q(() => {
    a.current === "holding" && (l.current = !1, f.current = null, g("releasing"));
  }, [g]);
  return F(() => {
    const y = () => w(), k = () => {
      document.hidden && w();
    };
    return window.addEventListener("blur", y), document.addEventListener("visibilitychange", k), () => {
      window.removeEventListener("blur", y), document.removeEventListener("visibilitychange", k), cancelAnimationFrame(h.current), h.current = 0;
    };
  }, [w]), { bind: {
    onPointerDown: (y) => {
      y.pointerType === "mouse" && y.button !== 0 || (y.currentTarget.setPointerCapture?.(y.pointerId), b({ x: y.clientX, y: y.clientY }));
    },
    onPointerMove: (y) => {
      const k = f.current;
      a.current !== "holding" || !k || Math.hypot(y.clientX - k.x, y.clientY - k.y) > h0 && w();
    },
    onPointerUp: w,
    onPointerCancel: w,
    onPointerLeave: w,
    onKeyDown: (y) => {
      if (y.key === "Escape") {
        (a.current === "holding" || a.current === "releasing") && (y.preventDefault(), x());
        return;
      }
      y.repeat || (y.key === " " || y.key === "Enter") && (y.preventDefault(), b());
    },
    onKeyUp: (y) => {
      (y.key === " " || y.key === "Enter") && w();
    },
    onBlur: w,
    onClick: (y) => y.preventDefault(),
    onContextMenu: (y) => y.preventDefault()
  }, phase: r, progress: i / sn, reset: x };
}
function m0({
  label: e,
  confirmLabel: t = "Confirmed",
  holdMs: n = 1800,
  onConfirm: i,
  variant: s = "danger",
  disabled: r = !1,
  className: o
}) {
  const { bind: a, phase: l, reset: u } = p0({ onConfirm: i, holdMs: n, disabled: r }), d = Q(), h = Se(), f = l === "committed", p = Math.round(n / 100) / 10, g = Kl(0), x = Sm(g, (b) => `inset(0 ${(1 - b) * 100}% 0 0)`);
  return F(() => {
    if (!f) return;
    const b = setTimeout(u, 1600);
    return () => clearTimeout(b);
  }, [f, u]), F(() => {
    if (d) {
      g.set(l === "holding" || l === "committed" ? 1 : 0);
      return;
    }
    if (l === "committed") {
      const T = si(g, 1, { duration: U.tick, ease: "linear" });
      return () => T.stop();
    }
    const b = g.get();
    if (l === "holding") {
      const T = si(g, 1, { duration: n * (1 - b) / 1e3, ease: "linear" });
      return () => T.stop();
    }
    const w = si(g, 0, { duration: n * b / hc / 1e3, ease: fc });
    return () => w.stop();
  }, [l, n, d, g]), /* @__PURE__ */ v(
    Te,
    {
      variant: s,
      "aria-label": e,
      "aria-disabled": r || f,
      "aria-describedby": h,
      className: `relative isolate select-none overflow-hidden ${o ?? ""}`,
      ...a,
      children: [
        /* @__PURE__ */ c(Uo, { committed: f, label: e, confirmLabel: t }),
        /* @__PURE__ */ c(
          B.span,
          {
            "aria-hidden": "true",
            style: { clipPath: x },
            className: "absolute inset-0 grid place-items-center bg-ink text-ground",
            children: /* @__PURE__ */ c(Uo, { committed: f, label: e, confirmLabel: t })
          }
        ),
        /* @__PURE__ */ v("span", { id: h, className: "sr-only", children: [
          "Press and hold for ",
          p,
          " seconds to confirm. Let go early and nothing happens."
        ] }),
        /* @__PURE__ */ c("span", { role: "status", "aria-live": "polite", className: "sr-only", children: f ? t : "" })
      ]
    }
  );
}
function Uo({ committed: e, label: t, confirmLabel: n }) {
  const i = { duration: U.settle, ease: fc };
  return /* @__PURE__ */ v("span", { "aria-hidden": "true", className: "col-start-1 row-start-1 grid", children: [
    /* @__PURE__ */ c(
      B.span,
      {
        initial: !1,
        animate: { opacity: e ? 0 : 1 },
        transition: i,
        className: "col-start-1 row-start-1 flex items-center justify-center whitespace-nowrap",
        children: t
      }
    ),
    /* @__PURE__ */ v(
      B.span,
      {
        initial: !1,
        animate: { opacity: e ? 1 : 0 },
        transition: i,
        className: "col-start-1 row-start-1 flex items-center justify-center gap-1.5 whitespace-nowrap",
        children: [
          /* @__PURE__ */ c(
            "svg",
            {
              width: "11",
              height: "11",
              viewBox: "0 0 12 12",
              fill: "none",
              stroke: "currentColor",
              strokeWidth: "1.7",
              strokeLinecap: "round",
              strokeLinejoin: "round",
              "aria-hidden": "true",
              children: /* @__PURE__ */ c("path", { d: "M2.5 6.4 4.7 8.6 9.5 3.5" })
            }
          ),
          n
        ]
      }
    )
  ] });
}
const g0 = Y.out;
function Cy({
  title: e,
  children: t,
  confirmLabel: n = "Delete",
  hold: i = !1,
  onConfirm: s,
  onCancel: r
}) {
  const o = M(null), a = M(null);
  return F(() => {
    o.current?.showModal(), a.current?.focus();
  }, []), /* @__PURE__ */ v(
    B.dialog,
    {
      ref: o,
      "aria-labelledby": "confirm-title",
      initial: { opacity: 0, scale: 0.98 },
      animate: { opacity: 1, scale: 1 },
      transition: { duration: U.settle, ease: g0 },
      onCancel: (l) => {
        l.preventDefault(), r();
      },
      onClick: (l) => {
        l.target === l.currentTarget && r();
      },
      className: "panel m-auto w-[320px] max-w-[calc(100vw-32px)] p-0 text-ink backdrop:bg-ink/30 backdrop:transition-colors backdrop:duration-[240ms] starting:backdrop:bg-ink/0",
      children: [
        /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5 px-4 pt-4 pb-3.5", children: [
          /* @__PURE__ */ c("h2", { id: "confirm-title", className: "font-display text-[16px] leading-5 font-bold tracking-[-0.02em] text-ink", children: e }),
          /* @__PURE__ */ c("p", { className: "text-xs leading-4 text-muted", children: t })
        ] }),
        /* @__PURE__ */ v("div", { className: "flex justify-end gap-1.5 border-t border-line-soft px-4 py-3", children: [
          /* @__PURE__ */ c(Te, { ref: a, variant: "outline", onClick: r, children: "Cancel" }),
          i ? /* @__PURE__ */ c(m0, { label: n, confirmLabel: "Done", holdMs: 1200, onConfirm: s }) : /* @__PURE__ */ c(Te, { variant: "danger", onClick: s, children: n })
        ] })
      ]
    }
  );
}
function Ey({
  size: e = "header",
  onNavigate: t
}) {
  const n = e === "panel" ? "h-6 w-[87px]" : "h-[18px] w-[65px]", i = /* @__PURE__ */ c("img", { src: js.lockup, alt: "nurb", className: `${n} shrink-0` });
  return t ? /* @__PURE__ */ c(
    "button",
    {
      type: "button",
      onClick: t,
      className: "inline-flex rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent",
      children: i
    }
  ) : /* @__PURE__ */ c("div", { className: "inline-flex", children: i });
}
const y0 = Y.out, x0 = { duration: 0 }, v0 = typeof window > "u" ? F : $t;
function b0({
  src: e,
  onReady: t,
  onError: n
}) {
  const i = M(null), [s, r] = O({ status: "loading", instant: !1 }), o = M(t);
  o.current = t;
  const a = M(n);
  return a.current = n, v0(() => {
    const l = i.current, u = (g, x) => r((b) => b.status === g && b.instant === x ? b : { status: g, instant: x });
    if (!l || !e) {
      u("loading", !1);
      return;
    }
    let d = !0;
    const h = l.complete && l.naturalWidth > 0, f = () => {
      d && (u("ready", h), o.current?.());
    }, p = () => {
      d && (u("error", h), a.current?.());
    };
    return l.complete ? (h ? f() : p(), () => {
      d = !1;
    }) : (u("loading", !1), l.addEventListener("load", f), l.addEventListener("error", p), () => {
      d = !1, l.removeEventListener("load", f), l.removeEventListener("error", p);
    });
  }, [e]), { ref: i, status: s.status, instant: s.instant, loaded: s.status === "ready" };
}
function w0({
  src: e,
  alt: t,
  width: n,
  height: i,
  placeholder: s = "var(--color-accent-wash)",
  blur: r = 14,
  sizes: o,
  loading: a = "lazy",
  onReady: l,
  onError: u,
  className: d
}) {
  const h = Q() === !0, { ref: f, status: p, instant: g } = b0({ src: e, onReady: l, onError: u }), x = p === "ready", b = h || g, w = b ? x0 : { duration: U.arrive, ease: y0 };
  return /* @__PURE__ */ v(
    "div",
    {
      "aria-busy": p === "loading",
      "data-status": p,
      style: { aspectRatio: `${n} / ${i}`, backgroundColor: s },
      className: R("relative w-full overflow-hidden rounded-[6px]", d),
      children: [
        /* @__PURE__ */ c(
          B.img,
          {
            ref: f,
            src: e,
            sizes: o,
            alt: t,
            width: n,
            height: i,
            loading: a,
            decoding: "async",
            draggable: !1,
            className: "absolute inset-0 size-full object-cover",
            initial: !1,
            animate: b ? { opacity: x ? 1 : 0 } : x ? { opacity: 1, filter: "blur(0px)", scale: 1 } : { opacity: 0, filter: `blur(${r}px)`, scale: 1.06 },
            transition: w
          }
        ),
        p === "error" ? /* @__PURE__ */ c("div", { "aria-hidden": "true", className: "absolute inset-0 grid place-items-center bg-raised text-faint", children: /* @__PURE__ */ c($, { name: "image" }) }) : null
      ]
    }
  );
}
const Wo = 3e4;
function k0(e, t) {
  const n = t ? Date.parse(t) : NaN, [i, s] = O(() => Date.now());
  return F(() => {
    if (!e || Number.isNaN(n)) return;
    const r = n + Wo - Date.now();
    if (r <= 0) return;
    const o = setTimeout(() => s(Date.now()), r);
    return () => clearTimeout(o);
  }, [e, n]), e ? Number.isNaN(n) ? !0 : i - n < Wo : !1;
}
function Dy({
  part: e,
  onOpen: t,
  menu: n
}) {
  const i = Wm(e.bbox), s = Um(e.builtAt), r = e.status === "failed", o = e.status === "building", a = k0(o, e.buildingSince);
  return /* @__PURE__ */ v("div", { className: "group relative flex flex-col rounded-[6px] border border-panel-edge bg-ground transition-shadow focus-within:shadow-[var(--shadow-panel)] hover:shadow-[var(--shadow-panel)]", children: [
    /* @__PURE__ */ c(
      "button",
      {
        type: "button",
        onClick: t,
        "aria-label": `Open ${e.name}`,
        className: "absolute inset-0 z-10 rounded-[6px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      }
    ),
    /* @__PURE__ */ c("div", { className: "relative h-[148px] overflow-hidden rounded-t-[6px] border-b border-line-soft bg-ground", children: e.thumbnailUrl ? (
      // The card owns the box, so the frame fills it instead of its own ratio,
      // and the whole part stays in frame rather than being cropped to it.
      /* @__PURE__ */ c(
        w0,
        {
          src: e.thumbnailUrl,
          alt: "",
          width: 4,
          height: 3,
          placeholder: "transparent",
          className: "h-full rounded-none! [&_img]:object-contain [&_img]:p-2"
        }
      )
    ) : /* @__PURE__ */ c(l0, { bbox: e.bbox, ghost: !e.bbox, className: "size-full" }) }),
    n && n.length > 0 ? /* @__PURE__ */ c("div", { className: "absolute top-2 right-2 z-20 flex items-center gap-1 transition-opacity lg:opacity-0 lg:group-focus-within:opacity-100 lg:group-hover:opacity-100 lg:has-[[aria-expanded=true]]:opacity-100", children: /* @__PURE__ */ c(
      u0,
      {
        label: `More for ${e.name}`,
        className: "[&>button]:size-7 [&>button]:rounded-[4px] [&>button]:border [&>button]:border-panel-edge [&>button]:bg-ground [&>button]:shadow-[var(--shadow-control)]",
        items: n
      }
    ) }) : null,
    /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5 px-[13px] py-[11px]", children: [
      /* @__PURE__ */ v("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ c("h2", { className: "min-w-0 flex-1 truncate text-[13.5px] leading-[18px] font-semibold tracking-[-0.01em] text-ink", children: e.name }),
        r ? /* @__PURE__ */ c("span", { className: "text-warn", children: /* @__PURE__ */ c($, { name: "warning" }) }) : o ? /* @__PURE__ */ c(
          "span",
          {
            "data-build": a ? "running" : "stalled",
            className: `size-1.5 rounded-full bg-accent${a ? " motion-safe:animate-pulse" : ""}`
          }
        ) : e.status === "built" ? /* @__PURE__ */ c("span", { className: "text-pass", children: /* @__PURE__ */ c($, { name: "check" }) }) : null
      ] }),
      /* @__PURE__ */ v("p", { className: "mono-caption truncate text-muted normal-case [letter-spacing:0.08em]", children: [
        e.identifier ?? "",
        e.identifier && i ? " · " : "",
        i ? `${i} mm` : ""
      ] })
    ] }),
    /* @__PURE__ */ v("div", { className: "mono-caption flex items-center justify-between border-t border-line-soft px-[13px] py-2 text-muted [letter-spacing:0.08em]", children: [
      /* @__PURE__ */ c("span", { children: s ? `Built ${s}` : "Not built yet" }),
      /* @__PURE__ */ c("span", { className: r ? "text-warn" : void 0, children: r ? "Failed" : e.folder ?? Ot(e.revision) })
    ] })
  ] });
}
function Vy({
  caption: e = "Describe a part and it builds here, live.",
  firstRun: t = !1,
  primary: n,
  secondary: i
}) {
  return /* @__PURE__ */ v("div", { className: "flex flex-1 flex-col items-center justify-center gap-7 pb-16", children: [
    /* @__PURE__ */ c("img", { src: js.ghostBracket, alt: "", "aria-hidden": "true", className: "h-[300px] w-auto select-none" }),
    /* @__PURE__ */ v("div", { className: "flex flex-col items-center gap-2", children: [
      /* @__PURE__ */ c("h2", { className: "font-display text-[20px] leading-[26px] tracking-[-0.022em] text-balance text-ink", children: "Empty shelf. What’s rattling around your bench?" }),
      /* @__PURE__ */ c("p", { className: "mono-caption text-on-stage-muted [letter-spacing:0.11em]", children: e }),
      t ? /* @__PURE__ */ c("p", { className: "mt-1 max-w-[42ch] text-center text-[13px] leading-5 text-balance text-on-stage-muted", children: "Nothing on the plate yet. Your first part goes here, and the first layer is the one that matters." }) : null
    ] }),
    n || i ? /* @__PURE__ */ v("div", { className: "flex flex-col items-center gap-3", children: [
      n ? /* @__PURE__ */ c(Te, { variant: "accent", size: "lg", icon: n.icon, onClick: n.onClick, children: n.label }) : null,
      i ? /* @__PURE__ */ c(Te, { variant: "outline", size: "md", icon: i.icon, onClick: i.onClick, disabled: i.disabled, children: i.label }) : null
    ] }) : null
  ] });
}
function Ry({
  title: e = "No part yet",
  caption: t = "It builds here, live, the moment the spec is pinned."
}) {
  return /* @__PURE__ */ v("div", { className: "relative flex min-h-[320px] flex-1 flex-col items-center justify-center gap-5 text-center", children: [
    /* @__PURE__ */ c("img", { src: js.markOutline, alt: "", "aria-hidden": "true", className: "size-14 select-none" }),
    /* @__PURE__ */ v("div", { className: "flex flex-col items-center gap-2", children: [
      /* @__PURE__ */ c("p", { className: "mono-label text-on-stage-muted", children: e }),
      /* @__PURE__ */ c("p", { className: "max-w-[34ch] text-[15px] leading-[22px] text-balance text-ink-soft", children: t })
    ] })
  ] });
}
function Ly({ header: e, children: t, className: n, style: i, topInset: s, dragRegion: r }) {
  return /* @__PURE__ */ v(
    "div",
    {
      className: R("isolate flex h-dvh flex-col gap-4 bg-stage p-4 antialiased", n),
      style: s == null ? i : { ...i, paddingTop: s },
      ...r ? { "data-tauri-drag-region": !0 } : {},
      children: [
        e,
        /* @__PURE__ */ c("div", { className: "flex min-h-0 flex-1 gap-4", children: t })
      ]
    }
  );
}
function T0({ children: e, className: t }) {
  return /* @__PURE__ */ c("div", { className: R("relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden", t), children: e });
}
function Fy({ children: e, className: t }) {
  return /* @__PURE__ */ c(T0, { className: R("items-center justify-center", t), children: e });
}
function Iy({ start: e, cells: t, end: n, children: i, dragRegion: s }) {
  return /* @__PURE__ */ v(
    "header",
    {
      className: "panel chrome flex h-[52px] shrink-0 items-center overflow-hidden",
      ...s ? { "data-tauri-drag-region": !0 } : {},
      children: [
        e,
        t,
        i,
        n ? /* @__PURE__ */ v(G, { children: [
          /* @__PURE__ */ c("div", { className: "flex-1" }),
          n
        ] }) : null
      ]
    }
  );
}
function Oy() {
  return /* @__PURE__ */ c("div", { className: "h-full w-px bg-line" });
}
function pc({ children: e, className: t }) {
  return /* @__PURE__ */ c("div", { className: R("flex h-full items-center px-4", t), children: e });
}
function By({ label: e, value: t, className: n }) {
  return /* @__PURE__ */ c(pc, { className: n, children: /* @__PURE__ */ v("div", { className: "flex flex-col gap-[3px]", children: [
    /* @__PURE__ */ c("span", { className: "mono-label text-[9px] leading-[10px] text-faint", children: e }),
    /* @__PURE__ */ c("span", { className: "mono-value text-ink", children: t })
  ] }) });
}
const S0 = {
  pass: "bg-pass",
  warn: "bg-warn",
  fail: "bg-fail",
  none: "bg-line",
  building: "bg-accent motion-safe:animate-pulse"
}, A0 = {
  pass: "border-line bg-pass-wash",
  warn: "border-line bg-warn-wash",
  fail: "border-line bg-fail-wash",
  none: "border-transparent bg-transparent",
  building: "border-line bg-accent-wash"
}, _o = "transition-colors duration-(--duration-settle) ease-out-strong";
function $y({
  tone: e,
  label: t,
  detail: n,
  className: i
}) {
  return /* @__PURE__ */ c(pc, { className: i, children: /* @__PURE__ */ v("span", { className: R("flex h-7 items-center gap-2 rounded-[3px] border px-2.5 whitespace-nowrap", _o, A0[e]), children: [
    /* @__PURE__ */ c("span", { className: R("size-1.5 shrink-0 rounded-full", _o, S0[e]) }),
    /* @__PURE__ */ c("span", { className: "mono-label text-ink", children: t }),
    n ? /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: n }) : null
  ] }) });
}
function jy({ children: e, className: t }) {
  return /* @__PURE__ */ c("div", { className: R("flex h-full items-center gap-1 px-3", t), children: e });
}
function Uy({ strip: e, picker: t, children: n, composer: i, hidden: s, dragRegion: r }) {
  return /* @__PURE__ */ v("section", { className: "panel flex w-[372px] shrink-0 flex-col overflow-hidden", hidden: s, children: [
    /* @__PURE__ */ c("div", { ...r ? { "data-tauri-drag-region": !0 } : {}, children: /* @__PURE__ */ c(
      $s,
      {
        label: e.label,
        inset: 16,
        trailing: t || e.trailing ? /* @__PURE__ */ v("span", { className: "flex items-center gap-2", children: [
          e.trailing,
          t
        ] }) : void 0
      }
    ) }),
    /* @__PURE__ */ c("div", { className: "min-h-0 flex-1 overflow-y-auto", children: n }),
    /* @__PURE__ */ c("div", { className: "shrink-0 p-4 pt-0", children: i })
  ] });
}
function N0(e) {
  const t = Math.max(0, Math.round(e / 60));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function ri({ value: e, unit: t }) {
  return /* @__PURE__ */ v("span", { className: "flex items-baseline gap-1", children: [
    /* @__PURE__ */ c("span", { className: "mono-value text-ink", children: e }),
    /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: t })
  ] });
}
function P0({ children: e }) {
  return /* @__PURE__ */ v("div", { className: "chrome flex items-center gap-2 px-4 pt-[11px] pb-2", children: [
    /* @__PURE__ */ c("span", { className: "mono-caption text-faint [letter-spacing:0.12em]", children: e }),
    /* @__PURE__ */ c("span", { className: "h-px flex-1 bg-line-soft" })
  ] });
}
function Wy({
  count: e,
  pinned: t,
  params: n,
  readouts: i,
  warnCount: s = 0,
  failCount: r = 0,
  disclosures: o,
  actions: a
}) {
  const l = r > 0 ? r : s;
  return /* @__PURE__ */ v("aside", { className: "panel flex w-[288px] shrink-0 flex-col overflow-hidden", children: [
    /* @__PURE__ */ c($s, { label: "Parameters", inset: 16, trailing: e }),
    /* @__PURE__ */ v("div", { className: "flex min-h-0 flex-1 flex-col overflow-y-auto", children: [
      t && t.length > 0 ? /* @__PURE__ */ v(G, { children: [
        /* @__PURE__ */ c(P0, { children: "Pinned by spec" }),
        /* @__PURE__ */ c("ul", { className: "flex flex-col gap-1.5 px-4 pb-1", children: t.map((u) => /* @__PURE__ */ v("li", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ c("span", { className: "shrink-0 text-faint", children: /* @__PURE__ */ c($, { name: "lock" }) }),
          /* @__PURE__ */ c("span", { className: "mono-label truncate text-muted", children: u.name }),
          /* @__PURE__ */ c("span", { className: "flex-1" }),
          /* @__PURE__ */ c("span", { className: "mono-value text-right text-ink", children: u.value })
        ] }, u.name)) })
      ] }) : null,
      n
    ] }),
    /* @__PURE__ */ v("div", { className: "min-h-0 overflow-y-auto border-t border-line bg-ground", children: [
      i ? /* @__PURE__ */ v("div", { className: "chrome flex items-center justify-between px-4 py-2.5", children: [
        /* @__PURE__ */ c(ri, { value: i.grams == null ? "-" : String(Math.round(i.grams)), unit: "g" }),
        /* @__PURE__ */ c(ri, { value: i.seconds == null ? "-" : N0(i.seconds), unit: "hr" }),
        /* @__PURE__ */ c(ri, { value: i.heightMm == null ? "-" : String(Math.round(i.heightMm)), unit: "mm" })
      ] }) : null,
      /* @__PURE__ */ c("div", { className: "h-px bg-line-soft" }),
      l > 0 && !o ? /* @__PURE__ */ v("div", { className: "flex items-center gap-2 px-4 py-2", children: [
        /* @__PURE__ */ c("span", { className: r > 0 ? "text-fail" : "text-warn", children: /* @__PURE__ */ c($, { name: r > 0 ? "xmark" : "warning" }) }),
        /* @__PURE__ */ v("span", { className: "mono-label text-ink", children: [
          l,
          " ",
          r > 0 ? l === 1 ? "fail" : "fails" : l === 1 ? "warn" : "warns"
        ] })
      ] }) : null,
      o,
      /* @__PURE__ */ c("div", { className: "flex gap-2 p-4", children: a })
    ] })
  ] });
}
const M0 = {
  warn: "warning",
  fail: "xmark",
  pass: "check",
  none: null
}, C0 = {
  warn: "text-warn",
  fail: "text-fail",
  pass: "text-pass",
  none: "text-muted"
};
function _y({ label: e, summary: t, tone: n = "none", open: i, onToggle: s, children: r }) {
  const o = M0[n];
  return /* @__PURE__ */ v("div", { className: "flex flex-col", children: [
    /* @__PURE__ */ v(
      "button",
      {
        type: "button",
        onClick: s,
        "aria-expanded": i,
        className: "chrome flex h-8 w-full items-center gap-2 px-4 text-left hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent",
        children: [
          o ? /* @__PURE__ */ c("span", { className: R("shrink-0", C0[n]), children: /* @__PURE__ */ c($, { name: o }) }) : null,
          /* @__PURE__ */ c("span", { className: "mono-label text-ink", children: e }),
          /* @__PURE__ */ c("span", { className: "flex-1" }),
          t ? /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: t }) : null,
          /* @__PURE__ */ c("span", { className: R("shrink-0 text-muted transition-transform", i && "rotate-180"), children: /* @__PURE__ */ c($, { name: "chevron-down" }) })
        ]
      }
    ),
    /* @__PURE__ */ c("div", { hidden: !i, className: "max-h-48 overflow-y-auto border-t border-line-soft", children: r })
  ] });
}
const zo = Y.out;
function mc(e, t = 900) {
  const [n, i] = O({ direction: null, from: e, changeId: 0, flashing: !1 }), s = M(e), r = M(null);
  return F(() => {
    const o = s.current;
    Object.is(o, e) || (s.current = e, e - o !== 0 && (i((a) => ({
      direction: e > o ? "up" : "down",
      from: o,
      changeId: a.changeId + 1,
      flashing: !0
    })), r.current && clearTimeout(r.current), r.current = setTimeout(() => {
      r.current = null, i((a) => a.flashing ? { ...a, flashing: !1 } : a);
    }, t)));
  }, [e, t]), F(() => () => r.current ? clearTimeout(r.current) : void 0, []), n;
}
function zy({ value: e, format: t, label: n, hold: i = 900, className: s }) {
  const { direction: r, flashing: o, changeId: a } = mc(e, i), l = Q(), u = t ? t(e) : String(e), [d, h] = O(u);
  F(() => {
    const g = setTimeout(() => h(u), 700);
    return () => clearTimeout(g);
  }, [u]);
  const f = { duration: l ? 0 : U.settle, ease: zo }, p = { duration: l ? 0 : U.tick * 2, ease: zo };
  return /* @__PURE__ */ v(
    "span",
    {
      "data-direction": o ? r : void 0,
      className: R(
        "mono-value relative inline-grid grid-flow-col items-center gap-1 rounded-[3px] px-1 py-px transition-colors",
        o ? r === "up" ? "text-pass" : "text-fail" : "text-ink",
        s
      ),
      children: [
        r ? /* @__PURE__ */ c(
          B.span,
          {
            "aria-hidden": !0,
            initial: { opacity: 0 },
            animate: { opacity: o ? 1 : 0 },
            transition: f,
            className: R(
              "pointer-events-none absolute inset-0 rounded-[3px]",
              r === "up" ? "bg-pass-wash" : "bg-fail-wash"
            )
          }
        ) : null,
        /* @__PURE__ */ c("span", { "aria-hidden": !0, className: "relative inline-grid overflow-hidden", children: /* @__PURE__ */ c(xe, { initial: !1, mode: "popLayout", children: /* @__PURE__ */ c(
          B.span,
          {
            initial: l ? { opacity: 0 } : { opacity: 0, y: r === "down" ? "-0.85em" : "0.85em" },
            animate: { opacity: 1, y: "0em" },
            exit: { opacity: 0, y: r === "down" ? "0.7em" : "-0.7em", transition: p },
            transition: p,
            className: "col-start-1 row-start-1",
            children: u
          },
          a
        ) }) }),
        /* @__PURE__ */ c("span", { "aria-hidden": !0, className: "relative grid size-[1em] place-items-center", children: /* @__PURE__ */ c(xe, { initial: !1, children: o && r ? /* @__PURE__ */ c(
          B.svg,
          {
            viewBox: "0 0 256 256",
            fill: "currentColor",
            initial: l ? { opacity: 0 } : { opacity: 0, scale: 0.4 },
            animate: { opacity: 1, scale: 1 },
            exit: { opacity: 0, transition: f },
            transition: f,
            className: "col-start-1 row-start-1 block size-[0.68em]",
            children: r === "up" ? /* @__PURE__ */ c("path", { d: "M128 68 L210 180 H46 Z" }) : /* @__PURE__ */ c("path", { d: "M128 188 L46 76 H210 Z" })
          },
          `${a}-${r}`
        ) : null }) }),
        /* @__PURE__ */ c("span", { className: "sr-only", "aria-live": "polite", children: n ? `${n}: ${d}` : d })
      ]
    }
  );
}
const E0 = Y.out;
function Gy({ findings: e, verdict: t, highlight: n, onHighlight: i }) {
  const s = Q(), r = e.length, { direction: o, flashing: a } = mc(r), l = a && !s, u = o === "up", d = r > 0 ? `${r} ${r === 1 ? "finding" : "findings"} to fix.` : t === "none" ? "Nothing checked yet" : t === "fail" ? "The build stopped before the checks ran" : "Nothing to fix. Checks pass at these numbers.", h = /* @__PURE__ */ c(
    "p",
    {
      "aria-live": "polite",
      className: R(
        "mono-caption py-1 text-center transition-colors duration-(--duration-settle) ease-out-strong",
        l ? u ? "bg-fail-wash text-fail" : "bg-pass-wash text-pass" : "text-muted"
      ),
      children: d
    }
  );
  return r === 0 ? h : /* @__PURE__ */ v(G, { children: [
    h,
    /* @__PURE__ */ c("ul", { className: "flex flex-col", children: e.map((f, p) => (
      // Keyed by what the finding says, not by where it sits, so a rebuild that
      // changes nothing leaves the rows alone instead of replaying the entrance.
      /* @__PURE__ */ c(
        B.li,
        {
          initial: { opacity: 0, y: 4 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: s ? 0 : U.settle, ease: E0, delay: s ? 0 : p * 0.06 },
          children: /* @__PURE__ */ v(
            "button",
            {
              type: "button",
              "aria-pressed": n === p,
              onMouseEnter: () => i?.(p),
              onClick: () => i?.(n === p ? null : p),
              className: R(
                "flex w-full items-start gap-2 px-4 py-2 text-left hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent",
                n === p && "bg-raised"
              ),
              children: [
                /* @__PURE__ */ c("span", { className: R("mt-0.5 shrink-0", f.severity === "fail" ? "text-fail" : "text-warn"), children: /* @__PURE__ */ c($, { name: f.severity === "fail" ? "xmark" : "warning" }) }),
                /* @__PURE__ */ v("span", { className: "flex min-w-0 flex-col gap-1", children: [
                  /* @__PURE__ */ c("span", { className: "mono-label text-ink", children: f.label || f.rule }),
                  /* @__PURE__ */ c("span", { className: "text-chat text-ink-soft", children: f.message })
                ] })
              ]
            }
          )
        },
        `${f.rule}:${f.message}`
      )
    )) })
  ] });
}
const D0 = Y.out;
function Ky({
  open: e = !0,
  revision: t,
  shownRevision: n
}) {
  const i = Q();
  return /* @__PURE__ */ c(xe, { children: e ? /* @__PURE__ */ v(
    B.div,
    {
      initial: { opacity: 0, y: -8 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -8 },
      transition: { duration: i ? 0 : U.settle, ease: D0 },
      className: "flex items-start gap-2 bg-fail-wash px-4 py-2.5",
      children: [
        /* @__PURE__ */ c("span", { className: "mt-0.5 shrink-0 text-fail", children: /* @__PURE__ */ c($, { name: "warning" }) }),
        /* @__PURE__ */ v("span", { className: "flex flex-col gap-1", children: [
          /* @__PURE__ */ v("span", { className: "mono-label text-fail", children: [
            Ot(t),
            " failed at these values"
          ] }),
          n != null ? /* @__PURE__ */ v("span", { className: "text-chat text-ink-soft", children: [
            "Showing ",
            Ot(n).toLowerCase(),
            ", the last one that built."
          ] }) : null,
          /* @__PURE__ */ c("span", { className: "text-chat text-muted", children: "That one didn't survive the checks. It didn't cost you a part either." })
        ] })
      ]
    }
  ) : null });
}
function Hy({ children: e }) {
  return /* @__PURE__ */ v("div", { className: "panel chrome absolute top-4 left-4 flex h-7 items-center gap-2 rounded-full px-3", children: [
    /* @__PURE__ */ c("span", { className: "size-1.5 shrink-0 rounded-full bg-fail" }),
    /* @__PURE__ */ c("span", { className: "mono-label text-ink", children: e })
  ] });
}
const V0 = Y.out;
function qy({
  version: e,
  installing: t = !1,
  onLater: n,
  onInstall: i,
  className: s
}) {
  const r = Q() === !0, o = r ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } } : { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 8 } };
  return /* @__PURE__ */ v(
    B.div,
    {
      ...o,
      transition: { duration: r ? 0 : U.settle, ease: V0 },
      className: R("panel flex w-[260px] flex-col gap-2 p-4", s),
      role: "status",
      children: [
        /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: "Update" }),
        /* @__PURE__ */ v("div", { className: "flex flex-col gap-1", children: [
          /* @__PURE__ */ v("h2", { className: "font-display text-[15px] leading-5 tracking-[-0.02em] text-ink", children: [
            "nurb ",
            e,
            " is ready"
          ] }),
          /* @__PURE__ */ c("p", { className: "text-[13px] leading-[18px] text-muted", children: t ? "Closing and reopening nurb." : "Downloaded. Restart to finish." })
        ] }),
        /* @__PURE__ */ v("div", { className: "mt-1 flex items-center gap-2", children: [
          t || !n ? null : /* @__PURE__ */ c(Te, { variant: "outline", onClick: n, children: "Later" }),
          /* @__PURE__ */ c(Te, { variant: "accent", disabled: t, onClick: i, children: t ? "Restarting…" : "Restart now" })
        ] })
      ]
    }
  );
}
const R0 = Y.out, Go = [100, 93, 97, 88, 95, 91];
function L0(e, t) {
  return t > 1 && e === t - 1 ? 62 : Go[(e * 7 + 3) % Go.length];
}
function F0({ loading: e, delay: t = 120, minVisible: n = 380 }) {
  const [i, s] = O(!1), r = M(0);
  return F(() => {
    if (e) {
      if (i) return;
      const l = setTimeout(() => {
        r.current = performance.now(), s(!0);
      }, t);
      return () => clearTimeout(l);
    }
    if (!i) return;
    const o = Math.max(0, n - (performance.now() - r.current)), a = setTimeout(() => s(!1), o);
    return () => clearTimeout(a);
  }, [e, i, t, n]), { showSkeleton: i };
}
function Yy({
  loading: e,
  children: t,
  lines: n = 3,
  lineHeight: i = 21,
  reserve: s,
  delay: r = 120,
  minVisible: o = 380,
  label: a,
  className: l
}) {
  const { showSkeleton: u } = F0({ loading: e, delay: r, minVisible: o }), d = Q(), h = M(null), f = M(null), [p, g] = O(!1), x = s ?? n * i, b = { duration: d ? 0 : U.settle, ease: R0 };
  return F(() => {
    const w = h.current;
    if (!w || typeof ResizeObserver > "u") return;
    const T = () => g(w.scrollHeight - w.clientHeight > 1);
    T();
    const y = new ResizeObserver(T);
    return y.observe(w), f.current && y.observe(f.current), () => y.disconnect();
  }, []), /* @__PURE__ */ v(
    "div",
    {
      ref: h,
      "aria-busy": e,
      "aria-label": a,
      tabIndex: p ? 0 : void 0,
      style: { height: x },
      className: R("relative grid overflow-y-auto overscroll-contain text-ink-soft", l),
      children: [
        /* @__PURE__ */ c(
          B.div,
          {
            ref: f,
            className: "col-start-1 row-start-1 min-w-0",
            initial: !1,
            animate: { opacity: u ? 0 : 1 },
            transition: b,
            style: { pointerEvents: u ? "none" : void 0 },
            children: t
          }
        ),
        /* @__PURE__ */ c(xe, { initial: !1, children: u ? /* @__PURE__ */ c(
          B.div,
          {
            "aria-hidden": !0,
            "data-skeleton": !0,
            className: "pointer-events-none col-start-1 row-start-1 w-full self-start",
            initial: { opacity: 0 },
            animate: { opacity: 1 },
            exit: { opacity: 0 },
            transition: b,
            children: Array.from({ length: n }, (w, T) => /* @__PURE__ */ c("div", { className: "flex items-center", style: { height: i }, children: /* @__PURE__ */ c("div", { className: "h-[8px] rounded-[3px] bg-raised", style: { width: `${L0(T, n)}%` } }) }, T))
          },
          "skeleton"
        ) : null }),
        a ? /* @__PURE__ */ c("span", { role: "status", className: "sr-only", children: e ? "" : `${a} loaded` }) : null
      ]
    }
  );
}
const Ko = Y.out, Ho = 0.35, I0 = 2200;
function Xy({
  value: e,
  max: t = 100,
  segments: n,
  label: i = "Progress",
  pendingLabel: s = "Working",
  completeLabel: r = "Complete",
  className: o
}) {
  const a = Q(), l = Se(), [u, d] = O(0), h = e === null;
  F(() => {
    if (!h || a) return;
    const y = performance.now();
    let k = requestAnimationFrame(function E() {
      const P = Ho * (1 - Math.exp(-(performance.now() - y) / I0));
      d((S) => Math.max(S, P)), Ho - P > 2e-3 && (k = requestAnimationFrame(E));
    });
    return () => cancelAnimationFrame(k);
  }, [h, a]);
  const f = e === null || t <= 0 ? 0 : Math.min(1, Math.max(0, e / t)), p = Math.max(h ? u : 0, f), g = n ? Math.round(p * n) / n : p, x = Math.round(g * 100), b = !h && g >= 1, w = h ? {} : { "aria-valuenow": Math.round(f * t * 100) / 100, "aria-valuetext": `${x}%` }, T = { duration: a ? 0 : U.settle, ease: Ko };
  return /* @__PURE__ */ v("div", { className: R("w-full", o), children: [
    /* @__PURE__ */ v("div", { className: "flex items-baseline justify-between gap-3", children: [
      /* @__PURE__ */ c("span", { id: l, className: "mono-label truncate text-ink-soft", children: i }),
      /* @__PURE__ */ v("span", { "aria-hidden": !0, className: "grid shrink-0 justify-items-end", children: [
        /* @__PURE__ */ c(
          B.span,
          {
            className: "mono-label col-start-1 row-start-1 whitespace-nowrap text-muted",
            initial: !1,
            animate: { opacity: h ? 1 : 0 },
            transition: T,
            children: s
          }
        ),
        /* @__PURE__ */ v(
          B.span,
          {
            className: "mono-value col-start-1 row-start-1 whitespace-nowrap text-ink",
            initial: !1,
            animate: { opacity: h ? 0 : 1 },
            transition: T,
            children: [
              x,
              "%"
            ]
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ c(
      "div",
      {
        role: "progressbar",
        "aria-labelledby": l,
        "aria-valuemin": 0,
        "aria-valuemax": t,
        ...w,
        className: "mt-2 h-[8px] overflow-hidden rounded-[3px] bg-raised",
        children: n ? /* @__PURE__ */ c("div", { className: "flex h-full gap-px", "data-cells": n, children: Array.from({ length: n }, (y, k) => /* @__PURE__ */ c(
          B.span,
          {
            "data-lit": k < Math.round(g * n) ? "" : void 0,
            className: "h-full flex-1 bg-accent first:rounded-l-[3px] last:rounded-r-[3px]",
            initial: !1,
            animate: { opacity: k < Math.round(g * n) ? 1 : 0.12 },
            transition: { duration: a ? 0 : U.tick, ease: Ko }
          },
          k
        )) }) : /* @__PURE__ */ c(
          B.span,
          {
            className: "block h-full origin-left rounded-[3px] bg-accent",
            initial: !1,
            animate: { scaleX: g },
            transition: T
          }
        )
      }
    ),
    /* @__PURE__ */ c("span", { "aria-live": "polite", className: "sr-only", children: b ? r : h ? s : "" })
  ] });
}
const oi = Y.out, qo = { duration: 0 }, Yo = {
  warn: { surface: "bg-warn-wash border-warn/25", mark: "text-warn" },
  fail: { surface: "bg-fail-wash border-fail/25", mark: "text-fail" },
  neutral: { surface: "bg-raised border-line", mark: "text-ink" }
};
function O0({
  state: e,
  defaultState: t = "open",
  onStateChange: n,
  onDismiss: i
} = {}) {
  const [s, r] = O(t), o = e ?? s, a = M(n);
  a.current = n;
  const l = M(i);
  l.current = i;
  const u = q((g) => {
    r(g), a.current?.(g);
  }, []), d = q(() => u("folded"), [u]), h = q(() => u("open"), [u]), f = q(() => u(o === "open" ? "folded" : "open"), [u, o]), p = q(() => {
    u("dismissed"), l.current?.();
  }, [u]);
  return {
    state: o,
    open: o === "open",
    folded: o === "folded",
    dismissed: o === "dismissed",
    fold: d,
    expand: h,
    toggle: f,
    dismiss: p
  };
}
function Zy({
  title: e,
  description: t,
  children: n,
  action: i,
  tone: s = "neutral",
  dismissible: r = !0,
  state: o,
  defaultState: a = "open",
  onStateChange: l,
  onDismiss: u,
  dismissLabel: d = "Dismiss notice",
  className: h
}) {
  const f = Q() === !0, p = Se(), g = `${p}-body`, x = `${p}-title`, { state: b, open: w, dismissed: T, toggle: y, fold: k, dismiss: E } = O0({
    state: o,
    defaultState: a,
    onStateChange: l,
    onDismiss: u
  }), P = !!(t || n || i), S = { duration: f ? 0 : U.settle, ease: oi };
  return /* @__PURE__ */ v(G, { children: [
    /* @__PURE__ */ c(
      B.div,
      {
        initial: { height: 0, opacity: 0 },
        animate: { height: T ? 0 : "auto", opacity: T ? 0 : 1 },
        transition: S,
        style: { overflow: "hidden" },
        children: /* @__PURE__ */ v(
          "div",
          {
            role: "region",
            "aria-labelledby": x,
            className: R("rounded-[12px] border", Yo[s].surface, h),
            children: [
              /* @__PURE__ */ v("div", { className: "flex items-center gap-2 p-2.5", children: [
                /* @__PURE__ */ c("span", { "aria-hidden": "true", className: R("flex shrink-0", Yo[s].mark), children: /* @__PURE__ */ c($, { name: s === "neutral" ? "box" : "warning" }) }),
                P ? /* @__PURE__ */ v(
                  "button",
                  {
                    type: "button",
                    onClick: y,
                    onKeyDown: (m) => {
                      m.key !== "Escape" || !w || (m.stopPropagation(), k());
                    },
                    "aria-expanded": w,
                    "aria-controls": g,
                    className: "chrome group flex min-w-0 flex-1 items-center gap-2 rounded-[3px] text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
                    children: [
                      /* @__PURE__ */ c("span", { id: x, className: "min-w-0 flex-1 truncate text-[13px] leading-5 font-medium text-ink", children: e }),
                      /* @__PURE__ */ c(
                        B.span,
                        {
                          "aria-hidden": "true",
                          className: "flex shrink-0 text-muted group-hover:text-ink",
                          initial: !1,
                          animate: { rotate: w ? 180 : 0 },
                          transition: f ? qo : { duration: U.tick, ease: oi },
                          children: /* @__PURE__ */ c($, { name: "chevron-down" })
                        }
                      )
                    ]
                  }
                ) : /* @__PURE__ */ c("span", { id: x, className: "min-w-0 flex-1 truncate text-[13px] leading-5 font-medium text-ink", children: e }),
                r ? /* @__PURE__ */ c(Bs, { icon: "xmark", label: d, onClick: E }) : null
              ] }),
              P ? /* @__PURE__ */ c(
                B.div,
                {
                  id: g,
                  inert: !w,
                  initial: !1,
                  animate: { height: w ? "auto" : 0, opacity: w ? 1 : 0 },
                  transition: f ? qo : { height: S, opacity: { duration: U.tick, ease: oi, delay: w ? 0.05 : 0 } },
                  style: { overflow: "hidden" },
                  children: /* @__PURE__ */ v("div", { className: "pr-2.5 pb-2.5 pl-[30px]", children: [
                    t ? /* @__PURE__ */ c("p", { className: "text-[12.5px] leading-relaxed text-muted", children: t }) : null,
                    n,
                    i ? /* @__PURE__ */ c("div", { className: "mt-2", children: i }) : null
                  ] })
                }
              ) : null
            ]
          }
        )
      }
    ),
    /* @__PURE__ */ c("span", { role: "status", "aria-live": "polite", className: "sr-only", children: b === "dismissed" ? "Notice dismissed." : "" })
  ] });
}
const B0 = Y.out, Oi = { duration: 0 }, $0 = { duration: U.coast, ease: "linear", repeat: 1 / 0 };
function Qy({ linger: e = 2e3 } = {}) {
  const [t, n] = O(null), i = M(0), s = M(null), r = q(() => {
    s.current && clearTimeout(s.current), s.current = null;
  }, []), o = q(
    (h) => {
      r(), i.current += 1;
      const f = `activity-${i.current}`;
      return n({ ...h, id: f, tone: "working" }), f;
    },
    [r]
  ), a = q((h) => {
    n((f) => f && { ...f, ...h });
  }, []), l = q(() => {
    r(), n(null);
  }, [r]), u = q(
    (h) => {
      n((f) => f && { ...f, ...h, tone: "done" }), r(), s.current = setTimeout(() => {
        s.current = null, n(null);
      }, e);
    },
    [r, e]
  ), d = q(
    (h) => {
      r(), n((f) => f && { ...f, ...h, tone: "fail" });
    },
    [r]
  );
  return F(() => r, [r]), { activity: t, start: o, update: a, succeed: u, fail: d, dismiss: l };
}
function Jy({
  activity: e,
  onDismiss: t,
  label: n = "Activity",
  className: i
}) {
  const s = Q() === !0, [r, o] = O(""), a = M(/* @__PURE__ */ new Set()), l = e?.tone ?? "working";
  return F(() => {
    if (!e) return;
    const u = `${e.id}:${l}`;
    a.current.has(u) || (a.current.add(u), o(
      l === "working" ? `${e.title} started.` : l === "done" ? `${e.title} finished.` : `${e.title} failed.`
    ));
  }, [e, l]), /* @__PURE__ */ v("div", { role: "region", "aria-label": n, className: R("pointer-events-none flex justify-center", i), children: [
    /* @__PURE__ */ c(xe, { initial: !1, mode: "wait", children: e ? /* @__PURE__ */ v(
      B.div,
      {
        initial: s ? { opacity: 0 } : { opacity: 0, y: -10, scale: 0.94 },
        animate: { opacity: 1, y: 0, scale: 1 },
        exit: s ? { opacity: 0, transition: Oi } : { opacity: 0, y: -8, scale: 0.97 },
        transition: s ? Oi : { duration: U.settle, ease: B0 },
        style: { transformOrigin: "50% 0%" },
        className: "pointer-events-auto flex max-w-[320px] items-center gap-2 rounded-[12px] border border-line bg-ground px-3 py-2 shadow-[var(--shadow-panel)]",
        children: [
          /* @__PURE__ */ c(j0, { tone: l, reduced: s }),
          /* @__PURE__ */ v("span", { className: "min-w-0 flex-1", children: [
            /* @__PURE__ */ c("span", { className: "block truncate text-[13px] leading-5 font-medium text-ink", children: e.title }),
            e.detail ? /* @__PURE__ */ c("span", { className: "mono-caption block truncate text-muted", children: e.detail }) : null
          ] }),
          t && l !== "working" ? /* @__PURE__ */ c(Bs, { icon: "xmark", label: "Dismiss activity", onClick: t }) : null
        ]
      },
      e.id
    ) : null }),
    /* @__PURE__ */ c("span", { role: "status", "aria-live": "polite", className: "sr-only", children: r })
  ] });
}
function j0({ tone: e, reduced: t }) {
  return e === "done" ? /* @__PURE__ */ c("span", { className: "flex shrink-0 text-pass", "data-tone": "done", children: /* @__PURE__ */ c($, { name: "check" }) }) : e === "fail" ? /* @__PURE__ */ c("span", { className: "flex shrink-0 text-fail", "data-tone": "fail", children: /* @__PURE__ */ c($, { name: "warning" }) }) : /* @__PURE__ */ c(
    B.span,
    {
      className: "flex shrink-0 text-accent",
      "data-tone": "working",
      style: { transformOrigin: "50% 50%" },
      animate: t ? void 0 : { rotate: 360 },
      transition: t ? Oi : $0,
      children: /* @__PURE__ */ c($, { name: "loader" })
    }
  );
}
const U0 = Y.out, Xo = { duration: 0 }, W0 = (e) => `${e} new ${e === 1 ? "item" : "items"}`;
function ex({
  count: e,
  onClick: t,
  anchor: n = "bottom",
  label: i = W0,
  className: s
}) {
  const r = Q() === !0, [o, a] = O(0);
  F(() => {
    if (e === 0) {
      a(0);
      return;
    }
    const d = setTimeout(() => a(e), 700);
    return () => clearTimeout(d);
  }, [e]);
  const l = i(e), u = n === "bottom" ? 10 : -10;
  return /* @__PURE__ */ v(
    "div",
    {
      className: R(
        "pointer-events-none absolute inset-x-0 z-10 flex justify-center",
        n === "bottom" ? "bottom-2" : "top-2",
        s
      ),
      children: [
        /* @__PURE__ */ c(xe, { initial: !1, children: e > 0 ? /* @__PURE__ */ v(
          B.button,
          {
            type: "button",
            onClick: t,
            "aria-label": l,
            initial: r ? { opacity: 0 } : { opacity: 0, scale: 0.94, y: u },
            animate: { opacity: 1, scale: 1, y: 0 },
            exit: r ? { opacity: 0, transition: Xo } : { opacity: 0, scale: 0.96, y: u * 0.5 },
            transition: r ? Xo : { duration: U.settle, ease: U0 },
            className: "chrome btn-label pointer-events-auto inline-flex h-7 items-center gap-1.5 rounded-[3px] border border-line bg-ground pr-3 pl-2.5 text-ink-soft shadow-[var(--shadow-panel)] hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
            children: [
              /* @__PURE__ */ c("span", { "aria-hidden": "true", className: R("flex text-accent", n === "bottom" && "rotate-180"), children: /* @__PURE__ */ c($, { name: "arrow-up" }) }),
              /* @__PURE__ */ c("span", { className: "tabular-nums", "aria-hidden": "true", children: l })
            ]
          }
        ) : null }),
        /* @__PURE__ */ c("span", { role: "status", "aria-live": "polite", className: "sr-only", children: o > 0 ? i(o) : "" })
      ]
    }
  );
}
const _0 = Y.out;
function tx({
  options: e,
  label: t,
  value: n,
  onValueChange: i,
  className: s
}) {
  const r = Se(), o = Q(), a = M([]), [l, u] = O(null), d = e.findIndex((x) => x.value === n), h = d < 0 ? 0 : d, f = l ?? h, p = (x) => {
    const b = (x + e.length) % e.length;
    a.current[b]?.focus();
  }, g = (x) => {
    x !== n && ($e("toggle"), i(x));
  };
  return /* @__PURE__ */ c(
    "div",
    {
      role: "radiogroup",
      "aria-label": t,
      onBlur: (x) => {
        x.currentTarget.contains(x.relatedTarget) || u(null);
      },
      className: R(
        "chrome grid auto-cols-fr grid-flow-col gap-px rounded-[3px] border border-line bg-raised p-[2px]",
        s
      ),
      children: e.map((x, b) => /* @__PURE__ */ v(
        "button",
        {
          ref: (w) => {
            a.current[b] = w;
          },
          type: "button",
          role: "radio",
          "aria-checked": b === h,
          tabIndex: b === f ? 0 : -1,
          onFocus: () => u(b),
          onClick: () => g(x.value),
          onKeyDown: (w) => {
            if (w.key === "ArrowRight" || w.key === "ArrowDown") p(b + 1);
            else if (w.key === "ArrowLeft" || w.key === "ArrowUp") p(b - 1);
            else if (w.key === "Home") p(0);
            else if (w.key === "End") p(e.length - 1);
            else if (w.key === "Enter" || w.key === " ") g(x.value);
            else return;
            w.preventDefault();
          },
          className: R(
            "mono-label relative flex h-6 items-center justify-center rounded-[3px] px-2.5 whitespace-nowrap transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
            b === h ? "text-ink" : "text-muted hover:text-ink-soft"
          ),
          children: [
            b === h ? /* @__PURE__ */ c(
              B.span,
              {
                layoutId: r,
                "aria-hidden": !0,
                transition: { duration: o ? 0 : U.settle, ease: _0 },
                className: "absolute inset-0 rounded-[3px] bg-ground"
              }
            ) : null,
            /* @__PURE__ */ c("span", { className: "relative", children: x.label })
          ]
        },
        x.value
      ))
    }
  );
}
const gc = Y.out, nt = { duration: 0 };
function z0({ steps: e, current: t, failed: n = !1 }) {
  const i = !n && t >= e.length, s = e.map((a, l) => ({
    ...a,
    status: l < t ? "done" : l === t && n ? "failed" : l === t && !i ? "active" : "pending"
  })), r = s.find((a) => a.status === "active"), o = n ? `Failed at ${e[Math.min(t, e.length - 1)]?.label ?? "step"}` : i ? `All ${e.length} steps complete` : r ? `${r.label}, step ${t + 1} of ${e.length}` : "";
  return { rows: s, complete: i, failed: n, sentence: o };
}
function G0({ reduced: e }) {
  return /* @__PURE__ */ c("svg", { viewBox: "0 0 256 256", width: "11", height: "11", fill: "none", "aria-hidden": !0, children: /* @__PURE__ */ c(
    B.polyline,
    {
      points: "216 72 104 184 48 128",
      stroke: "currentColor",
      strokeWidth: "26",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      initial: { pathLength: 0 },
      animate: { pathLength: 1 },
      transition: { duration: e ? 0 : U.settle, ease: gc }
    }
  ) });
}
function K0() {
  return /* @__PURE__ */ c("svg", { viewBox: "0 0 256 256", width: "10", height: "10", fill: "none", "aria-hidden": !0, children: /* @__PURE__ */ c("path", { d: "M200 56 56 200 M56 56l144 144", stroke: "currentColor", strokeWidth: "26", strokeLinecap: "round" }) });
}
function H0({ reduced: e }) {
  return /* @__PURE__ */ v(
    B.svg,
    {
      viewBox: "0 0 16 16",
      className: "size-3",
      "aria-hidden": !0,
      animate: { rotate: e ? 0 : 360 },
      transition: e ? nt : { duration: U.coast / 2, ease: "linear", repeat: 1 / 0 },
      children: [
        /* @__PURE__ */ c("circle", { cx: "8", cy: "8", r: "6", fill: "none", stroke: "currentColor", strokeOpacity: "0.25", strokeWidth: "2" }),
        /* @__PURE__ */ c("path", { d: "M8 2 a6 6 0 0 1 6 6", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round" })
      ]
    }
  );
}
const q0 = {
  done: "text-ink-soft",
  active: "font-medium text-ink",
  failed: "font-medium text-fail",
  pending: "text-faint"
};
function nx({
  steps: e,
  current: t,
  failed: n = !1,
  label: i = "Task progress",
  className: s
}) {
  const { rows: r, complete: o, sentence: a } = z0({ steps: e, current: t, failed: n }), l = Q() === !0, [u, d] = O("");
  F(() => {
    if (!a) return;
    const f = setTimeout(() => d(a), 500);
    return () => clearTimeout(f);
  }, [a]);
  const h = { duration: l ? 0 : U.settle, ease: gc };
  return /* @__PURE__ */ v("div", { className: R("w-full", s), children: [
    /* @__PURE__ */ c("ol", { "aria-label": i, className: "space-y-0.5", children: r.map((f) => /* @__PURE__ */ v(
      "li",
      {
        "data-status": f.status,
        "aria-current": f.status === "active" ? "step" : void 0,
        className: "flex h-7 items-center gap-2.5 px-1",
        children: [
          /* @__PURE__ */ c("span", { className: "relative grid size-4 shrink-0 place-items-center", children: /* @__PURE__ */ c(xe, { initial: !1, children: f.status === "done" ? /* @__PURE__ */ c(
            B.span,
            {
              className: "col-start-1 row-start-1 grid size-4 place-items-center rounded-[3px] bg-pass-wash text-pass",
              initial: { opacity: l ? 1 : 0 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: nt },
              transition: h,
              children: /* @__PURE__ */ c(G0, { reduced: l })
            },
            "done"
          ) : f.status === "failed" ? /* @__PURE__ */ c(
            B.span,
            {
              className: "col-start-1 row-start-1 grid size-4 place-items-center rounded-[3px] bg-fail-wash text-fail",
              initial: { opacity: l ? 1 : 0 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: nt },
              transition: h,
              children: /* @__PURE__ */ c(K0, {})
            },
            "failed"
          ) : f.status === "active" ? /* @__PURE__ */ c(
            B.span,
            {
              className: "col-start-1 row-start-1 text-accent",
              initial: { opacity: l ? 1 : 0 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: nt },
              transition: h,
              children: /* @__PURE__ */ c(H0, { reduced: l })
            },
            "active"
          ) : /* @__PURE__ */ c(
            B.span,
            {
              className: "col-start-1 row-start-1 size-[5px] rounded-[3px] bg-line",
              initial: { opacity: 1 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: nt },
              transition: nt
            },
            "pending"
          ) }) }),
          /* @__PURE__ */ c("span", { className: R("mono-id min-w-0 flex-1 truncate transition-colors", q0[f.status]), children: f.label }),
          f.meta ? /* @__PURE__ */ c(
            "span",
            {
              "aria-hidden": f.status !== "done",
              className: R(
                "mono-caption shrink-0 text-faint transition-opacity",
                f.status === "done" ? "opacity-100" : "opacity-0"
              ),
              children: f.meta
            }
          ) : null
        ]
      },
      f.id
    )) }),
    /* @__PURE__ */ c("span", { role: "status", className: "sr-only", children: u }),
    /* @__PURE__ */ c("span", { className: "sr-only", "aria-live": o || n ? "polite" : "off", children: o ? "Run complete" : n ? "Run failed" : "" })
  ] });
}
const Y0 = Y.out, yc = /-?\d*\.?\d+/g, X0 = "12", Z0 = {
  "check-close": [
    ["M 5 12.5 L 10 17.5 L 19.5 7", "M 12 12 L 12 12 L 12 12"],
    ["M 6.5 6.5 L 12 12 L 17.5 17.5", "M 17.5 6.5 L 12 12 L 6.5 17.5"]
  ],
  "plus-minus": [
    ["M 5 12 L 19 12", "M 12 5 L 12 19"],
    ["M 5 12 L 19 12", "M 5 12 L 19 12"]
  ]
};
function Q0(e) {
  const t = e.match(yc);
  return !t || t.length < 4 ? !1 : t.every((n, i) => n === t[i % 2]);
}
function J0(e, t) {
  const n = e.reduce((s, r) => Math.max(s, r.length), 0), i = e[t] ?? e[0];
  return Array.from({ length: n }, (s, r) => {
    const o = i[r], a = e.find((u) => u[r] !== void 0)?.[r] ?? "", l = o ?? a.replace(yc, X0);
    return { key: r, d: l, visible: !Q0(l) };
  });
}
function ix({
  preset: e = "check-close",
  active: t = 0,
  size: n = 12,
  strokeWidth: i = 1.75,
  label: s,
  className: r
}) {
  const o = Z0[e], a = typeof t == "boolean" ? t ? 1 : 0 : Math.min(Math.max(Math.trunc(t), 0), 1), l = le(() => J0(o, a), [o, a]), d = Q() ? { duration: 0 } : { duration: U.settle, ease: Y0 };
  return /* @__PURE__ */ c(
    "svg",
    {
      viewBox: "0 0 24 24",
      width: n,
      height: n,
      focusable: "false",
      role: s ? "img" : void 0,
      "aria-label": s,
      "aria-hidden": s ? void 0 : !0,
      fill: "none",
      stroke: "currentColor",
      strokeWidth: i,
      strokeLinecap: "round",
      strokeLinejoin: "round",
      className: r,
      style: { display: "block" },
      children: l.map((h) => /* @__PURE__ */ c(
        B.path,
        {
          initial: !1,
          animate: { d: h.d, opacity: h.visible ? 1 : 0 },
          transition: d
        },
        h.key
      ))
    }
  );
}
const xc = Y.out;
function ey({ value: e }) {
  const t = Q() === !0;
  return /* @__PURE__ */ c("span", { className: "relative inline-flex h-[13px] overflow-hidden leading-[13px] tabular-nums", children: /* @__PURE__ */ c(xe, { initial: !1, mode: "popLayout", children: /* @__PURE__ */ c(
    B.span,
    {
      initial: t ? { opacity: 0 } : { y: 13, opacity: 0 },
      animate: { y: 0, opacity: 1 },
      exit: t ? { opacity: 0 } : { y: -13, opacity: 0 },
      transition: { duration: t ? 0 : U.tick, ease: xc },
      children: e
    },
    e
  ) }) });
}
function sx({
  questions: e,
  onAnswer: t,
  className: n
}) {
  const [i, s] = O(0), r = M(!1), o = e.length;
  F(() => {
    if (o === 0) {
      r.current = !1, s(0);
      return;
    }
    r.current || (r.current = !0, $e("scan"));
  }, [o]);
  const a = Is(!0), l = e[0];
  if (!l) return null;
  const u = i + o, d = Math.min(i + 1, u), h = (f) => {
    s((p) => p + 1), t(l.id, f);
  };
  return /* @__PURE__ */ v("div", { className: R("flex flex-col gap-2.5 rounded-[6px] bg-raised p-3", n), children: [
    u > 1 ? /* @__PURE__ */ v("div", { className: "flex items-center gap-1", children: [
      /* @__PURE__ */ v("span", { "aria-hidden": "true", className: "mono-caption flex items-center gap-1 text-faint", children: [
        /* @__PURE__ */ c(ey, { value: d }),
        "of ",
        u
      ] }),
      /* @__PURE__ */ v("span", { className: "sr-only", children: [
        "Question ",
        d,
        " of ",
        u
      ] })
    ] }) : null,
    /* @__PURE__ */ c(B.div, { style: a.style, animate: a.animate, transition: a.transition, onAnimationComplete: a.onAnimationComplete, children: /* @__PURE__ */ c("div", { ref: a.ref, children: /* @__PURE__ */ c(xe, { initial: !1, mode: "popLayout", children: /* @__PURE__ */ v(
      B.div,
      {
        initial: { y: 12, opacity: 0 },
        animate: { y: 0, opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: U.settle, ease: xc },
        className: "flex flex-col gap-2.5",
        children: [
          /* @__PURE__ */ c("p", { className: "text-chat text-ink", children: l.title }),
          l.detail ? /* @__PURE__ */ c("p", { className: "mono-caption text-muted", children: l.detail }) : null,
          /* @__PURE__ */ c("div", { className: "flex flex-wrap gap-1.5", children: l.actions.map((f) => /* @__PURE__ */ c(Te, { variant: f.variant ?? "outline", onClick: () => h(f.id), children: f.label }, f.id)) })
        ]
      },
      l.id
    ) }) }) })
  ] });
}
const ty = /def\s+\w+\s*\(([\s\S]*?)\)\s*(?:->[^:]*?)?:/;
function ny(e) {
  const t = [];
  let n = 0, i = 0;
  for (let s = 0; s < e.length; s++) {
    const r = e[s];
    r === "(" || r === "[" || r === "{" ? n++ : r === ")" || r === "]" || r === "}" ? n-- : r === "," && n === 0 && (t.push(e.slice(i, s)), i = s + 1);
  }
  return t.push(e.slice(i)), t;
}
function Zo(e) {
  const t = /* @__PURE__ */ new Map(), n = e.match(ty);
  if (!n) return t;
  for (const i of ny(n[1])) {
    const s = i.indexOf("=");
    if (s < 0) continue;
    const r = i.slice(0, s).split(":")[0].trim(), o = i.slice(s + 1).trim();
    !/^[A-Za-z_]\w*$/.test(r) || !o || t.set(r, o);
  }
  return t;
}
function iy(e, t) {
  const n = Zo(e), i = Zo(t), s = [];
  for (const [r, o] of i) {
    const a = n.get(r);
    a === void 0 ? s.push(`added ${r}`) : a !== o && s.push(`${r} ${a} to ${o}`);
  }
  for (const r of n.keys())
    i.has(r) || s.push(`removed ${r}`);
  return s;
}
function sy(e, t) {
  const n = e ? e.split(`
`) : [], i = t ? t.split(`
`) : [];
  let s = 0;
  for (; s < n.length && s < i.length && n[s] === i[s]; ) s++;
  let r = 0;
  for (; r < n.length - s && r < i.length - s && n[n.length - 1 - r] === i[i.length - 1 - r]; ) r++;
  const o = n.slice(s, n.length - r).map((l) => ({ sign: "-", text: l })), a = i.slice(s, i.length - r).map((l) => ({ sign: "+", text: l }));
  return [...o, ...a];
}
function ry(e) {
  if (!e || typeof e != "object") return null;
  const t = e, n = typeof t.part_name == "string" ? t.part_name : null;
  return n ? typeof t.old_string == "string" && typeof t.new_string == "string" ? { name: n, before: t.old_string, after: t.new_string } : typeof t.source == "string" ? { name: n, after: t.source } : null : null;
}
const Qo = 12;
function rx({ input: e, className: t }) {
  const [n, i] = O(null), [s, r] = O(!1), o = Is(n !== null), a = ry(e), l = a?.before !== void 0 ? iy(a.before, a.after) : [];
  if (!a) return null;
  const u = l.length > 0 ? l : [`edited ${a.name}`], d = sy(a.before ?? "", a.after), h = s ? d : d.slice(0, Qo);
  return /* @__PURE__ */ v("div", { className: R("flex flex-col gap-1.5", t), children: [
    /* @__PURE__ */ c("div", { className: "flex flex-wrap gap-1", children: u.map((f) => /* @__PURE__ */ c(
      "button",
      {
        type: "button",
        "aria-expanded": n === f,
        onClick: () => i((p) => p === f ? null : f),
        className: R(
          "mono-caption rounded-[3px] bg-raised px-1.5 py-0.5 text-muted hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          n === f && "text-ink"
        ),
        children: f
      },
      f
    )) }),
    /* @__PURE__ */ c(B.div, { style: o.style, animate: o.animate, transition: o.transition, onAnimationComplete: o.onAnimationComplete, children: /* @__PURE__ */ c("div", { ref: o.ref, children: n !== null && d.length > 0 ? /* @__PURE__ */ v("div", { className: "flex flex-col rounded-[3px] bg-raised py-1", children: [
      h.map((f, p) => /* @__PURE__ */ v(
        "span",
        {
          className: R(
            "px-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap",
            f.sign === "+" ? "bg-pass-wash text-ink-soft" : "bg-fail-wash text-ink-soft"
          ),
          children: [
            f.sign,
            " ",
            f.text
          ]
        },
        p
      )),
      !s && d.length > Qo ? /* @__PURE__ */ c(
        "button",
        {
          type: "button",
          onClick: () => r(!0),
          className: "mono-caption self-start px-2 pt-1 text-faint hover:text-ink",
          children: "show more"
        }
      ) : null
    ] }) : null }) })
  ] });
}
const vc = Y.out;
function ox({ active: e, label: t = "Drop the photo here" }) {
  const n = Q() === !0;
  return /* @__PURE__ */ c(xe, { initial: !1, children: e ? /* @__PURE__ */ c(
    B.div,
    {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
      transition: { duration: n ? 0 : U.tick, ease: vc },
      className: "pointer-events-none absolute inset-0 z-10 flex items-center justify-center rounded-[6px] border border-dashed border-accent bg-accent-wash",
      children: /* @__PURE__ */ c("span", { className: "btn-label text-accent-ink", children: t })
    }
  ) : null });
}
function ax({
  lines: e,
  active: t,
  everyMs: n = 4e3,
  className: i
}) {
  const [s, r] = O(0), o = Q() === !0;
  return F(() => {
    if (!t || e.length < 2) return;
    const a = setInterval(() => r((l) => (l + 1) % e.length), n);
    return () => clearInterval(a);
  }, [t, e.length, n]), !t || e.length === 0 ? null : /* @__PURE__ */ c("span", { "aria-hidden": "true", className: R("pointer-events-none absolute inset-0 block", i), children: /* @__PURE__ */ c(xe, { initial: !1, children: /* @__PURE__ */ c(
    B.span,
    {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
      transition: { duration: o ? 0 : U.settle, ease: vc },
      className: "absolute inset-x-0 top-0 block",
      children: e[s % e.length]
    },
    s % e.length
  ) }) });
}
export {
  Jm as ASSISTANT_MARKDOWN_DISALLOWED_ELEMENTS,
  My as AddPrinterDialog,
  sx as ApprovalCard,
  wy as AssistantMarkdown,
  w0 as BlurUpImage,
  by as BuildCard,
  Ky as BuildFailedBanner,
  Te as Button,
  Uy as ChatPanel,
  Zy as CollapsibleBanner,
  Cy as ConfirmDialog,
  ax as CyclingPlaceholder,
  _g as DetentMarks,
  ox as DropHint,
  rx as EditChips,
  Ry as EmptyProject,
  Vy as EmptyShelf,
  Ny as ExportMenu,
  Gy as FindingsList,
  dc as Floating,
  Iy as FloatingHeader,
  pc as HeaderCell,
  Oy as HeaderDivider,
  jy as HeaderIcons,
  By as HeaderStack,
  $y as HeaderStatus,
  m0 as HoldToConfirm,
  $ as Icon,
  Bs as IconButton,
  ix as IconMorph,
  l0 as IsoBox,
  Jy as LiveActivity,
  Ug as LoadingButton,
  Ey as Lockup,
  Ty as MeasurementCard,
  u0 as Menu,
  ex as NewItemsPill,
  $s as PanelStrip,
  Wy as ParamRail,
  Ay as ParamsPanel,
  Dy as PartCard,
  Py as PrinterMenu,
  Xy as ProgressBar,
  _y as RailDisclosure,
  tx as SegmentedControl,
  Yy as SkeletonSwap,
  ky as SpecCard,
  Ly as Stage,
  T0 as StageColumn,
  Fy as StageEmpty,
  Hy as StageNotice,
  nx as TaskSteps,
  Jl as ToolStepCard,
  Xm as ToolStepGroup,
  qy as UpdateCard,
  zy as ValueFlash,
  Sy as ViewerIsland,
  Ii as adjustable,
  Jg as bedLine,
  js as brand,
  sy as changedLines,
  Xl as clock,
  $e as cue,
  cc as decimals,
  iy as diffDefaults,
  Gg as dirtyValues,
  U as duration,
  Y as ease,
  Fn as elapsedLabel,
  Wm as formatBbox,
  vy as initials,
  Zo as keywordDefaults,
  py as readSoundPrefs,
  Um as relativeTime,
  Ot as rev,
  my as setSoundEnabled,
  gy as setSoundVolume,
  zg as sliderRange,
  ry as sourceEdit,
  jm as stackLabel,
  ft as tidy,
  $g as useAsyncAction,
  Is as useAutoHeight,
  b0 as useBlurUpImage,
  O0 as useCollapsibleBanner,
  yy as useCopyToClipboard,
  p0 as useHoldToConfirm,
  Qy as useLiveActivity,
  F0 as useSkeletonSwap,
  Wg as useSliderDetents,
  z0 as useTaskSteps,
  mc as useValueFlash
};
