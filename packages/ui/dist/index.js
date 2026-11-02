import * as Cn from "react";
import { useState as F, useRef as P, useEffect as O, useCallback as Y, createContext as pt, useLayoutEffect as mt, useId as we, useContext as re, useInsertionEffect as $i, useMemo as le, Children as Pc, isValidElement as Mc, Fragment as ji, createElement as Cc, forwardRef as Ui, Component as Ec } from "react";
import { jsx as c, jsxs as x, Fragment as _ } from "react/jsx-runtime";
import R from "clsx";
import Dc from "react-markdown";
import { DirectionalLight as Vc, HemisphereLight as Rc, Mesh as Je, PlaneGeometry as Lc, MeshStandardMaterial as zi, ReplaceStencilOp as In, NotEqualStencilFunc as Fc, DoubleSide as Wi, Group as mn, LineSegments as _i, EdgesGeometry as ea, LineBasicMaterial as st, BufferGeometry as Gi, BufferAttribute as Ki, MeshBasicMaterial as Dt, SphereGeometry as Oc, Box3 as Vt, Vector3 as he, Quaternion as qs, IncrementWrapStencilOp as Bn, BackSide as Ic, AlwaysStencilFunc as Bc, DecrementWrapStencilOp as $n, FrontSide as $c, Frustum as jc, Matrix4 as Uc, BoxGeometry as zc, Scene as Wc, Color as _c, PerspectiveCamera as Gc, Plane as Kc, WebGLRenderer as Hc, Vector2 as qc, Raycaster as Yc } from "three";
import { OrbitControls as Xc } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader as Ys } from "three/addons/loaders/GLTFLoader.js";
import { createPortal as ta } from "react-dom";
const na = {
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
function Zc(e) {
  return typeof e == "string" && Object.prototype.hasOwnProperty.call(na, e);
}
const Hi = 0.05, Qc = 0.05, Jc = 1e-3, eu = 4;
function tu(e, t, n, i) {
  const s = e.createOscillator();
  if (s.type = n.waveform, s.frequency.setValueAtTime(n.frequency, i), n.detune && (s.detune.value = n.detune), n.glideTo !== void 0) {
    const o = n.glideTime ?? n.attack + n.decay;
    s.frequency.exponentialRampToValueAtTime(n.glideTo, i + o);
  }
  const r = e.createGain();
  r.gain.setValueAtTime(1e-4, i), r.gain.exponentialRampToValueAtTime(n.peak, i + n.attack), r.gain.exponentialRampToValueAtTime(1e-4, i + n.attack + n.decay), s.connect(r).connect(t), s.start(i), s.stop(i + n.attack + n.decay + Hi);
}
function nu(e, t, n, i) {
  const s = n.attack + n.decay + Hi, r = Math.max(1, Math.floor(s * e.sampleRate)), o = e.createBuffer(1, r, e.sampleRate), a = o.getChannelData(0);
  for (let h = 0; h < r; h++)
    a[h] = 2 * Math.random() - 1;
  const l = e.createBufferSource();
  l.buffer = o;
  const u = e.createBiquadFilter();
  u.type = n.filterType, u.frequency.value = n.filterFrequency, n.filterQ !== void 0 && (u.Q.value = n.filterQ);
  const d = e.createGain();
  d.gain.setValueAtTime(1e-4, i), d.gain.exponentialRampToValueAtTime(n.peak, i + n.attack), d.gain.exponentialRampToValueAtTime(1e-4, i + n.attack + n.decay), l.connect(u).connect(d).connect(t), l.start(i), l.stop(i + s);
}
function iu(e, t, n, i) {
  const s = e.createDelay(1);
  s.delayTime.value = i.delay;
  const r = e.createBiquadFilter();
  r.type = "lowpass", r.frequency.value = i.lowpass;
  const o = e.createGain();
  o.gain.value = i.feedback;
  const a = e.createGain();
  return a.gain.value = i.wet, t.connect(s), s.connect(r), r.connect(o), o.connect(s), r.connect(a), a.connect(n), [s, r, o, a];
}
function su(e) {
  return Math.max(...e.layers.map((t) => (t.offset ?? 0) + t.attack + t.decay + Hi));
}
function ru(e) {
  return !e || e.feedback <= 0 ? 0 : e.feedback >= 1 ? e.delay : e.delay * (1 + Math.ceil(Math.log(Jc) / Math.log(e.feedback)));
}
let jn = null;
function ou(e) {
  if (jn)
    return jn;
  const t = e.createGain();
  t.gain.value = eu;
  const n = e.createDynamicsCompressor();
  return n.threshold.value = -8, n.knee.value = 6, n.ratio.value = 12, n.attack.value = 2e-3, n.release.value = 0.08, t.connect(n).connect(e.destination), jn = t, t;
}
function Xs(e, t, n) {
  const i = e.currentTime, s = ou(e), r = e.createGain();
  r.gain.value = t.masterGain * n, r.connect(s);
  const o = t.shimmer ? iu(e, r, s, t.shimmer) : [];
  for (const l of t.layers) {
    const u = i + (l.offset ?? 0);
    l.kind === "tone" ? tu(e, r, l, u) : nu(e, r, l, u);
  }
  const a = (su(t) + ru(t.shimmer) + Qc) * 1e3;
  setTimeout(() => {
    r.disconnect();
    for (const l of o)
      l.disconnect();
  }, a);
}
let Yt = null, li = !0, ci = 1;
function ia(e, t) {
  return typeof e == "number" && Number.isFinite(e) ? Math.min(1, Math.max(0, e)) : t;
}
function au(e) {
  typeof e == "boolean" && (li = e);
}
function lu(e) {
  ci = ia(e, ci);
}
function cu() {
  if (Yt)
    return Yt;
  if (typeof window > "u")
    return null;
  const e = window.AudioContext ?? window.webkitAudioContext;
  if (!e)
    return null;
  try {
    Yt = new e();
  } catch {
    return null;
  }
  return Yt;
}
function uu(e = "chime", t) {
  if (!li || !Zc(e) || typeof navigator < "u" && navigator.userActivation?.hasBeenActive === !1)
    return;
  const n = ci * ia(t?.volume, 1);
  if (n === 0)
    return;
  const i = cu();
  if (!i)
    return;
  const s = na[e];
  if (i.state === "running")
    Xs(i, s, n);
  else
    try {
      i.resume().then(() => {
        li && i.state === "running" && Xs(i, s, n);
      }, () => {
      });
    } catch {
    }
}
const ct = "nurb-sound-enabled", qi = "nurb-sound-volume", Zs = "nurb-completion-sound", Yi = 0.6;
function Ke(e) {
  try {
    return localStorage.getItem(e);
  } catch {
    return null;
  }
}
function gn(e, t) {
  try {
    t === null ? localStorage.removeItem(e) : localStorage.setItem(e, t);
  } catch {
  }
}
function Xi(e) {
  return Number.isFinite(e) ? Math.min(1, Math.max(0, e)) : Yi;
}
function wy() {
  const e = Ke(Zs);
  e !== null && (e === "off" && Ke(ct) === null && gn(ct, "off"), gn(Zs, null));
  const t = Ke(ct) !== "off", n = Ke(qi), i = n === null ? Yi : Xi(Number(n));
  return Zi(t, i), { enabled: t, volume: i };
}
function ky(e) {
  gn(ct, e ? null : "off"), Zi(e, du());
}
function Ty(e) {
  const t = Xi(e);
  gn(qi, String(t)), Zi(Ke(ct) !== "off", t);
}
function du() {
  const e = Ke(qi);
  return e === null ? Yi : Xi(Number(e));
}
function Zi(e, t) {
  try {
    au(e), lu(t);
  } catch {
  }
}
function $e(e, t) {
  if (!(typeof window > "u") && Ke(ct) !== "off")
    try {
      uu(e, t);
    } catch {
    }
}
const z = {
  tick: 0.09,
  settle: 0.24,
  arrive: 0.42,
  coast: 1.4
}, X = {
  out: [0.23, 1, 0.32, 1],
  inOut: [0.65, 0, 0.35, 1]
};
function Sy({ timeout: e = 1500, onCopy: t, onError: n } = {}) {
  const [i, s] = F("idle"), r = P(null);
  O(() => () => {
    r.current && clearTimeout(r.current);
  }, []);
  const o = Y(
    (l) => {
      s(l), r.current && clearTimeout(r.current), r.current = setTimeout(() => s("idle"), e);
    },
    [e]
  ), a = Y(
    async (l) => {
      try {
        if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(l);
        else if (!fu(l)) throw new Error("clipboard unavailable");
        $e("success"), t?.(l), o("copied");
      } catch (u) {
        $e("error"), n?.(u), o("error");
      }
    },
    [t, n, o]
  );
  return { status: i, copy: a };
}
function fu(e) {
  const t = document.createElement("textarea");
  t.value = e, t.setAttribute("readonly", ""), t.style.position = "fixed", t.style.opacity = "0", document.body.appendChild(t);
  try {
    return t.select(), document.execCommand("copy");
  } finally {
    t.remove();
  }
}
const hu = {
  "chevron-left": /* @__PURE__ */ c("polyline", { points: "7.75 1.75 3.5 6 7.75 10.25" }),
  "chevron-down": /* @__PURE__ */ c("polyline", { points: "1.75 4.25 6 8.5 10.25 4.25" }),
  "chevron-up": /* @__PURE__ */ c("polyline", { points: "10.25 7.75 6 3.5 1.75 7.75" }),
  check: /* @__PURE__ */ c("path", { d: "m1.76,7.004l2.25,3L10.24,1.746" }),
  warning: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("circle", { cx: "6", cy: "10.125", r: ".875", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("line", { x1: "6", y1: "4.75", x2: "6", y2: "7.75" }),
    /* @__PURE__ */ c("path", { d: "m8.625,10.25h1.164c1.123,0,1.826-1.216,1.265-2.189L7.265,1.484c-.562-.975-1.969-.975-2.53,0L.946,8.061c-.561.973.142,2.189,1.265,2.189h1.164" })
  ] }),
  lock: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("line", { x1: "6", y1: "7.5", x2: "6", y2: "8.5" }),
    /* @__PURE__ */ c("path", { d: "m3.75,4.75v-1.75c0-1.243,1.007-2.25,2.25-2.25h0c1.243,0,2.25,1.007,2.25,2.25v1.75" }),
    /* @__PURE__ */ c("rect", { x: "1.25", y: "4.75", width: "9.5", height: "6.5", rx: "1.5", ry: "1.5" })
  ] }),
  plus: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("line", { x1: "10.75", y1: "6", x2: "1.25", y2: "6" }),
    /* @__PURE__ */ c("line", { x1: "6", y1: "10.75", x2: "6", y2: "1.25" })
  ] }),
  minus: /* @__PURE__ */ c("line", { x1: "10.75", y1: "6", x2: "1.25", y2: "6" }),
  camera: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("circle", { cx: "3.25", cy: "5.75", r: ".75", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("rect", { x: ".75", y: "3.25", width: "10.5", height: "8", rx: "2", ry: "2" }),
    /* @__PURE__ */ c("line", { x1: "2.75", y1: ".75", x2: "4.75", y2: ".75" }),
    /* @__PURE__ */ c("circle", { cx: "7.25", cy: "7.25", r: "1", fill: "currentColor" })
  ] }),
  search: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("line", { x1: "7.652", y1: "7.652", x2: "10.75", y2: "10.75" }),
    /* @__PURE__ */ c("circle", { cx: "5", cy: "5", r: "3.75" })
  ] }),
  xmark: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("line", { x1: "2.25", y1: "9.75", x2: "9.75", y2: "2.25" }),
    /* @__PURE__ */ c("line", { x1: "9.75", y1: "9.75", x2: "2.25", y2: "2.25" })
  ] }),
  image: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("path", { d: "m2.32,10.516l4.723-4.723c.391-.391,1.024-.391,1.414,0l2.293,2.293" }),
    /* @__PURE__ */ c("circle", { cx: "4", cy: "4", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("rect", { x: "1.25", y: "1.25", width: "9.5", height: "9.5", rx: "2", ry: "2" })
  ] }),
  download: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("line", { x1: "6", y1: "7.75", x2: "6", y2: ".75" }),
    /* @__PURE__ */ c("polyline", { points: "3.75 5.75 6 8 8.25 5.75" }),
    /* @__PURE__ */ c("path", { d: "m8.69,2.75c1.028,0,1.888.779,1.99,1.801l.35,3.5c.118,1.177-.807,2.199-1.99,2.199H2.96c-1.183,0-2.108-1.022-1.99-2.199l.35-3.5c.102-1.022.963-1.801,1.99-1.801" })
  ] }),
  expand: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("path", { d: "m1.25,4.25v-1c0-1.105.895-2,2-2h1" }),
    /* @__PURE__ */ c("path", { d: "m7.75,1.25h1c1.105,0,2,.895,2,2v1" }),
    /* @__PURE__ */ c("path", { d: "m10.75,7.75v1c0,1.105-.895,2-2,2h-1" }),
    /* @__PURE__ */ c("path", { d: "m4.25,10.75h-1c-1.105,0-2-.895-2-2v-1" })
  ] }),
  eye: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("path", { d: "M5.99997 10.25C8.64947 10.25 10.2021 8.38538 10.9485 7.12628C11.3599 6.43238 11.3599 5.56762 10.9485 4.87372C10.2021 3.61462 8.64937 1.75 5.99997 1.75C3.42267 1.75 1.87667 3.53288 1.10727 4.78918C0.649466 5.53658 0.649466 6.46338 1.10727 7.21088C1.87667 8.46718 3.42267 10.25 5.99997 10.25Z" }),
    /* @__PURE__ */ c("circle", { cx: "6", cy: "6", r: "1.25", fill: "currentColor" })
  ] }),
  "arrow-up": /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("line", { x1: "6", y1: "11", x2: "6", y2: "1.25" }),
    /* @__PURE__ */ c("polyline", { points: "9.25 4.25 6 1 2.75 4.25" })
  ] }),
  link: /* @__PURE__ */ x(_, { children: [
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
  loader: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("path", { d: "M6 2.25V0.75" }),
    /* @__PURE__ */ c("path", { opacity: "0.5", d: "M6 11.25V9.75" }),
    /* @__PURE__ */ c("path", { opacity: "0.75", d: "M9.75488 5.995L11.2549 5.995" }),
    /* @__PURE__ */ c("path", { opacity: "0.25", d: "M0.754883 5.995L2.25488 5.995" }),
    /* @__PURE__ */ c("path", { opacity: "0.88", d: "M8.65321 3.3449L9.71387 2.28424" }),
    /* @__PURE__ */ c("path", { opacity: "0.38", d: "M2.28895 9.70885L3.34961 8.64819" }),
    /* @__PURE__ */ c("path", { opacity: "0.63", d: "M8.66004 8.64811L9.7207 9.70877" }),
    /* @__PURE__ */ c("path", { opacity: "0.13", d: "M2.29627 2.28416L3.35693 3.34482" })
  ] }),
  dots: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("circle", { cx: "6", cy: "6", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("circle", { cx: "2", cy: "6", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ c("circle", { cx: "10", cy: "6", r: "1", fill: "currentColor", stroke: "none" })
  ] }),
  trash: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("line", { x1: "1", y1: "2.25", x2: "11", y2: "2.25" }),
    /* @__PURE__ */ c("path", { d: "m4.75,2.25v-1c0-.276.224-.5.5-.5h1.5c.276,0,.5.224.5.5v1" }),
    /* @__PURE__ */ c("path", { d: "m9.5,4.75l-.195,5.058c-.031.805-.693,1.442-1.499,1.442h-3.613c-.806,0-1.468-.637-1.499-1.442l-.195-5.058" })
  ] }),
  ruler: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("line", { x1: "6.623", y1: "6.623", x2: "7.754", y2: "7.754" }),
    /* @__PURE__ */ c("line", { x1: "7.873", y1: "4.373", x2: "9.504", y2: "6.004" }),
    /* @__PURE__ */ c("line", { x1: "4.373", y1: "7.873", x2: "6.004", y2: "9.504" }),
    /* @__PURE__ */ c("rect", { x: ".42", y: "3.52", width: "11.161", height: "4.96", rx: "1.086", ry: "1.086", transform: "translate(-2.485 6) rotate(-45)" })
  ] }),
  gear: /* @__PURE__ */ x(_, { children: [
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
  user: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("circle", { cx: "6", cy: "2.491", r: "1.75" }),
    /* @__PURE__ */ c("path", { d: "m9.425,10.458c.551-.255.759-.92.458-1.446-.773-1.349-2.215-2.262-3.882-2.262s-3.11.912-3.882,2.262c-.301.526-.093,1.192.458,1.446,2.283,1.056,4.566,1.056,6.849,0Z" })
  ] }),
  logout: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("path", { d: "M5.75 3.25V2.25c0-.828.672-1.5 1.5-1.5h2.5c.828 0 1.5.672 1.5 1.5v7.5c0 .828-.672 1.5-1.5 1.5h-2.5c-.828 0-1.5-.672-1.5-1.5v-1" }),
    /* @__PURE__ */ c("line", { x1: "8.25", y1: "6", x2: "1", y2: "6" }),
    /* @__PURE__ */ c("polyline", { points: "3 3.75 .75 6 3 8.25" })
  ] }),
  box: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("line", { x1: "1.25", y1: "3.75", x2: "10.75", y2: "3.75" }),
    /* @__PURE__ */ c("line", { x1: "6", y1: ".75", x2: "6", y2: "3.75" }),
    /* @__PURE__ */ c("line", { x1: "3.75", y1: "8.25", x2: "5.25", y2: "8.25" }),
    /* @__PURE__ */ c("path", { d: "m1.25,3.75l1.461-2.504c.179-.307.508-.496.864-.496h4.851c.356,0,.685.189.864.496l1.461,2.504v5c0,1.105-.895,2-2,2H3.25c-1.105,0-2-.895-2-2V3.75Z" })
  ] }),
  copy: /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c("rect", { x: "3.25", y: ".75", width: "8", height: "8", rx: "1.5", ry: "1.5" }),
    /* @__PURE__ */ c("path", { d: "m8.25,11.25H2.25c-.828,0-1.5-.672-1.5-1.5V3.75" })
  ] }),
  folder: /* @__PURE__ */ x(_, { children: [
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
      children: hu[e]
    }
  );
}
const Qi = pt({});
function Ut(e) {
  const t = P(null);
  return t.current === null && (t.current = e()), t.current;
}
const pu = typeof window < "u", Rt = pu ? mt : O, zt = /* @__PURE__ */ pt(null);
function Ji(e, t) {
  e.indexOf(t) === -1 && e.push(t);
}
function Qe(e, t) {
  const n = e.indexOf(t);
  n > -1 && e.splice(n, 1);
}
const Ne = (e, t, n) => n > t ? t : n < e ? e : n;
function ui(e, t) {
  return t ? `${e}. For more information and steps for solving, visit https://motion.dev/troubleshooting/${t}` : e;
}
let et = () => {
}, xe = () => {
};
typeof process < "u" && process.env?.NODE_ENV !== "production" && (et = (e, t, n) => {
  !e && typeof console < "u" && console.warn(ui(t, n));
}, xe = (e, t, n) => {
  if (!e)
    throw new Error(ui(t, n));
});
const Ve = {}, es = (e) => /^-?(?:\d+(?:\.\d+)?|\.\d+)$/u.test(e), ts = (e) => typeof e == "object" && e !== null, ns = (e) => /^0[^.\s]+$/u.test(e);
// @__NO_SIDE_EFFECTS__
function sa(e) {
  let t;
  return () => (t === void 0 && (t = e()), t);
}
const Se = /* @__NO_SIDE_EFFECTS__ */ (e) => e, Wt = (...e) => e.reduce((t, n) => (i) => n(t(i))), ft = /* @__NO_SIDE_EFFECTS__ */ (e, t, n) => {
  const i = t - e;
  return i ? (n - e) / i : 1;
};
class yn {
  constructor() {
    this.subscriptions = [];
  }
  add(t) {
    return Ji(this.subscriptions, t), () => this.remove(t);
  }
  remove(t) {
    Qe(this.subscriptions, t);
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
const pe = /* @__NO_SIDE_EFFECTS__ */ (e) => e * 1e3, me = /* @__NO_SIDE_EFFECTS__ */ (e) => e / 1e3, ra = /* @__NO_SIDE_EFFECTS__ */ (e, t) => t ? e * (1e3 / t) : 0, Qs = /* @__PURE__ */ new Set();
function En(e, t, n) {
  e || Qs.has(t) || (console.warn(ui(t, n)), Qs.add(t));
}
const mu = (e, t, n) => {
  const i = t - e;
  return ((n - e) % i + i) % i + e;
}, oa = (e, t, n) => (((1 - 3 * n + 3 * t) * e + (3 * n - 6 * t)) * e + 3 * t) * e, gu = 1e-7, yu = 12;
function xu(e, t, n, i, s) {
  let r, o, a = 0;
  do
    o = t + (n - t) / 2, r = oa(o, i, s) - e, r > 0 ? n = o : t = o;
  while (Math.abs(r) > gu && ++a < yu);
  return o;
}
// @__NO_SIDE_EFFECTS__
function _t(e, t, n, i) {
  if (e === t && n === i)
    return Se;
  const s = (r) => xu(r, 0, 1, e, n);
  return (r) => r === 0 || r === 1 ? r : oa(s(r), t, i);
}
const aa = /* @__NO_SIDE_EFFECTS__ */ (e) => (t) => t <= 0.5 ? e(2 * t) / 2 : (2 - e(2 * (1 - t))) / 2, is = /* @__NO_SIDE_EFFECTS__ */ (e) => (t) => 1 - e(1 - t), la = /* @__PURE__ */ _t(0.33, 1.53, 0.69, 0.99), ss = /* @__PURE__ */ is(la), ca = /* @__PURE__ */ aa(ss), ua = (e) => e >= 1 ? 1 : (e *= 2) < 1 ? 0.5 * ss(e) : 0.5 * (2 - Math.pow(2, -10 * (e - 1))), rs = (e) => 1 - Math.sin(Math.acos(e)), da = /* @__PURE__ */ is(rs), fa = /* @__PURE__ */ aa(rs), vu = /* @__PURE__ */ _t(0.42, 0, 1, 1), bu = /* @__PURE__ */ _t(0, 0, 0.58, 1), ha = /* @__PURE__ */ _t(0.42, 0, 0.58, 1), pa = /* @__NO_SIDE_EFFECTS__ */ (e) => Array.isArray(e) && typeof e[0] != "number";
// @__NO_SIDE_EFFECTS__
function ma(e, t) {
  return /* @__PURE__ */ pa(e) ? e[mu(0, e.length, t)] : e;
}
const ga = /* @__NO_SIDE_EFFECTS__ */ (e) => Array.isArray(e) && typeof e[0] == "number", Js = {
  linear: Se,
  easeIn: vu,
  easeInOut: ha,
  easeOut: bu,
  circIn: rs,
  circInOut: fa,
  circOut: da,
  backIn: ss,
  backInOut: ca,
  backOut: la,
  anticipate: ua
}, wu = (e) => typeof e == "string", er = (e) => {
  if (/* @__PURE__ */ ga(e)) {
    xe(e.length === 4, "Cubic bezier arrays must contain four numerical values.", "cubic-bezier-length");
    const [t, n, i, s] = e;
    return /* @__PURE__ */ _t(t, n, i, s);
  } else if (wu(e))
    return xe(Js[e] !== void 0, `Invalid easing type '${e}'`, "invalid-easing-type"), Js[e];
  return e;
}, Xt = [
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
function ku(e) {
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
const Tu = 40;
function ya(e, t) {
  let n = !1, i = !0;
  const s = {
    delta: 0,
    timestamp: 0,
    isProcessing: !1
  }, r = () => n = !0, o = Xt.reduce((y, N) => (y[N] = ku(r), y), {}), { setup: a, read: l, resolveKeyframes: u, preUpdate: d, update: h, preRender: f, render: p, postRender: g } = o, v = () => {
    const y = Ve.useManualTiming, N = y ? s.timestamp : performance.now();
    n = !1, y || (s.delta = i ? 1e3 / 60 : Math.max(Math.min(N - s.timestamp, Tu), 1)), s.timestamp = N, s.isProcessing = !0, a.process(s), l.process(s), u.process(s), d.process(s), h.process(s), f.process(s), p.process(s), g.process(s), s.isProcessing = !1, n && t && (i = !1, e(v));
  }, b = () => {
    n = !0, i = !0, s.isProcessing || e(v);
  };
  return { schedule: Xt.reduce((y, N) => {
    const V = o[N];
    return y[N] = (C, k = !1, m = !1) => (n || b(), V.schedule(C, k, m)), y;
  }, {}), cancel: (y) => {
    for (let N = 0; N < Xt.length; N++)
      o[Xt[N]].cancel(y);
  }, state: s, steps: o };
}
const { schedule: G, cancel: Re, state: te, steps: Un } = /* @__PURE__ */ ya(typeof requestAnimationFrame < "u" ? requestAnimationFrame : Se, !0);
let on;
function Su() {
  on = void 0;
}
const ae = {
  now: () => (on === void 0 && ae.set(te.isProcessing || Ve.useManualTiming ? te.timestamp : performance.now()), on),
  set: (e) => {
    on = e, queueMicrotask(Su);
  }
}, ut = (e) => Math.round(e * 1e5) / 1e5, xa = (e) => (t) => typeof t == "string" && t.startsWith(e), va = /* @__PURE__ */ xa("--"), Nu = /* @__PURE__ */ xa("var(--"), os = (e) => Nu(e) ? Au.test(e.split("/*")[0].trim()) : !1, Au = /var\(--(?:[\w-]+\s*|[\w-]+\s*,(?:\s*[^)(\s]|\s*\((?:[^)(]|\([^)(]*\))*\))+\s*)\)$/iu;
function tr(e) {
  return typeof e != "string" ? !1 : e.split("/*")[0].includes("var(--");
}
const gt = {
  test: (e) => typeof e == "number",
  parse: parseFloat,
  transform: (e) => e
}, Lt = {
  ...gt,
  transform: (e) => Ne(0, 1, e)
}, Zt = {
  ...gt,
  default: 1
}, as = /-?(?:\d+(?:\.\d+)?|\.\d+)/gu;
function Pu(e) {
  return e == null;
}
const Mu = /^(?:#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\))$/iu, ls = (e, t) => (n) => !!(typeof n == "string" && Mu.test(n) && n.startsWith(e) || t && !Pu(n) && Object.prototype.hasOwnProperty.call(n, t)), ba = (e, t, n) => (i) => {
  if (typeof i != "string")
    return i;
  const [s, r, o, a] = i.match(as);
  return {
    [e]: parseFloat(s),
    [t]: parseFloat(r),
    [n]: parseFloat(o),
    alpha: a !== void 0 ? parseFloat(a) : 1
  };
}, Cu = (e) => Ne(0, 255, e), zn = {
  ...gt,
  transform: (e) => Math.round(Cu(e))
}, He = {
  test: /* @__PURE__ */ ls("rgb", "red"),
  parse: /* @__PURE__ */ ba("red", "green", "blue"),
  transform: ({ red: e, green: t, blue: n, alpha: i = 1 }) => "rgba(" + zn.transform(e) + ", " + zn.transform(t) + ", " + zn.transform(n) + ", " + ut(Lt.transform(i)) + ")"
};
function Eu(e) {
  let t = "", n = "", i = "", s = "";
  return e.length > 5 ? (t = e.substring(1, 3), n = e.substring(3, 5), i = e.substring(5, 7), s = e.substring(7, 9)) : (t = e.substring(1, 2), n = e.substring(2, 3), i = e.substring(3, 4), s = e.substring(4, 5), t += t, n += n, i += i, s += s), {
    red: parseInt(t, 16),
    green: parseInt(n, 16),
    blue: parseInt(i, 16),
    alpha: s ? parseInt(s, 16) / 255 : 1
  };
}
const di = {
  test: /* @__PURE__ */ ls("#"),
  parse: Eu,
  transform: He.transform
}, Gt = /* @__NO_SIDE_EFFECTS__ */ (e) => ({
  test: (t) => typeof t == "string" && t.endsWith(e) && t.split(" ").length === 1,
  parse: parseFloat,
  transform: (t) => `${t}${e}`
}), De = /* @__PURE__ */ Gt("deg"), Ce = /* @__PURE__ */ Gt("%"), E = /* @__PURE__ */ Gt("px"), Du = /* @__PURE__ */ Gt("vh"), Vu = /* @__PURE__ */ Gt("vw"), nr = {
  ...Ce,
  parse: (e) => Ce.parse(e) / 100,
  transform: (e) => Ce.transform(e * 100)
}, rt = {
  test: /* @__PURE__ */ ls("hsl", "hue"),
  parse: /* @__PURE__ */ ba("hue", "saturation", "lightness"),
  transform: ({ hue: e, saturation: t, lightness: n, alpha: i = 1 }) => "hsla(" + Math.round(e) + ", " + Ce.transform(ut(t)) + ", " + Ce.transform(ut(n)) + ", " + ut(Lt.transform(i)) + ")"
}, ne = {
  test: (e) => He.test(e) || di.test(e) || rt.test(e),
  parse: (e) => He.test(e) ? He.parse(e) : rt.test(e) ? rt.parse(e) : di.parse(e),
  transform: (e) => typeof e == "string" ? e : e.hasOwnProperty("red") ? He.transform(e) : rt.transform(e),
  getAnimatableNone: (e) => {
    const t = ne.parse(e);
    return t.alpha = 0, ne.transform(t);
  }
}, Ru = /(?:#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\))/giu, wa = /* @__PURE__ */ new RegExp(as.source), ka = /* @__PURE__ */ new RegExp(Ru.source, "i");
function Lu(e) {
  return isNaN(e) && typeof e == "string" && (wa.test(e) || ka.test(e));
}
const Ta = "number", Sa = "color", Fu = "var", Ou = "var(", ir = "${}", Iu = /var\s*\(\s*--(?:[\w-]+\s*|[\w-]+\s*,(?:\s*[^)(\s]|\s*\((?:[^)(]|\([^)(]*\))*\))+\s*)\)|#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\)|-?(?:\d+(?:\.\d+)?|\.\d+)/giu;
function Bu(e) {
  const t = e.toString();
  return wa.test(t) || ka.test(t);
}
function Ft(e) {
  const t = e.toString(), n = [], i = {
    color: [],
    number: [],
    var: []
  }, s = [];
  let r = 0;
  const a = t.replace(Iu, (l) => (ne.test(l) ? (i.color.push(r), s.push(Sa), n.push(ne.parse(l))) : l.startsWith(Ou) ? (i.var.push(r), s.push(Fu), n.push(l)) : (i.number.push(r), s.push(Ta), n.push(parseFloat(l))), ++r, ir)).split(ir);
  return { values: n, split: a, indexes: i, types: s };
}
function $u(e) {
  return Ft(e).values;
}
function Na({ split: e, types: t }) {
  const n = e.length;
  return (i) => {
    let s = "";
    for (let r = 0; r < n; r++)
      if (s += e[r], i[r] !== void 0) {
        const o = t[r];
        o === Ta ? s += ut(i[r]) : o === Sa ? s += ne.transform(i[r]) : s += i[r];
      }
    return s;
  };
}
function ju(e) {
  return Na(Ft(e));
}
const Uu = (e) => typeof e == "number" ? 0 : ne.test(e) ? ne.getAnimatableNone(e) : e, zu = (e, t) => typeof e == "number" ? t?.trim().endsWith("/") ? e : 0 : Uu(e);
function Wu(e) {
  const t = Ft(e);
  return Na(t)(t.values.map((i, s) => zu(i, t.split[s])));
}
const ye = {
  test: Lu,
  parse: $u,
  createTransformer: ju,
  getAnimatableNone: Wu
};
function Wn(e, t, n) {
  return n < 0 && (n += 1), n > 1 && (n -= 1), n < 1 / 6 ? e + (t - e) * 6 * n : n < 1 / 2 ? t : n < 2 / 3 ? e + (t - e) * (2 / 3 - n) * 6 : e;
}
function _u({ hue: e, saturation: t, lightness: n, alpha: i }) {
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
function xn(e, t) {
  return (n) => n > 0 ? t : e;
}
const q = (e, t, n) => e + (t - e) * n, _n = (e, t, n) => {
  const i = e * e, s = n * (t * t - i) + i;
  return s < 0 ? 0 : Math.sqrt(s);
}, Gu = [di, He, rt], Ku = (e) => Gu.find((t) => t.test(e));
function sr(e) {
  const t = Ku(e);
  if (!t)
    return et(!1, `'${e}' is not an animatable color. Use the equivalent color code instead.`, "color-not-animatable"), !1;
  let n = t.parse(e);
  return t === rt && (n = _u(n)), n;
}
const rr = (e, t) => {
  const n = sr(e), i = sr(t);
  if (!n || !i)
    return xn(e, t);
  const s = { ...n };
  return (r) => (s.red = _n(n.red, i.red, r), s.green = _n(n.green, i.green, r), s.blue = _n(n.blue, i.blue, r), s.alpha = q(n.alpha, i.alpha, r), He.transform(s));
}, fi = /* @__PURE__ */ new Set(["none", "hidden"]);
function Hu(e, t) {
  return fi.has(e) ? (n) => n <= 0 ? e : t : (n) => n >= 1 ? t : e;
}
function qu(e, t) {
  return (n) => q(e, t, n);
}
function cs(e) {
  return typeof e == "number" ? qu : typeof e == "string" ? os(e) ? xn : ne.test(e) ? rr : Zu : Array.isArray(e) ? Aa : typeof e == "object" ? ne.test(e) ? rr : Yu : xn;
}
function Aa(e, t) {
  const n = [...e], i = n.length, s = e.map((r, o) => cs(r)(r, t[o]));
  return (r) => {
    for (let o = 0; o < i; o++)
      n[o] = s[o](r);
    return n;
  };
}
function Yu(e, t) {
  const n = { ...e, ...t }, i = {};
  for (const s in n)
    e[s] !== void 0 && t[s] !== void 0 && (i[s] = cs(e[s])(e[s], t[s]));
  return (s) => {
    for (const r in i)
      n[r] = i[r](s);
    return n;
  };
}
function Xu(e, t) {
  const n = [], i = { color: 0, var: 0, number: 0 };
  for (let s = 0; s < t.values.length; s++) {
    const r = t.types[s], o = e.indexes[r][i[r]], a = e.values[o] ?? 0;
    n[s] = a, i[r]++;
  }
  return n;
}
const Zu = (e, t) => {
  const n = ye.createTransformer(t), i = Ft(e), s = Ft(t);
  return i.indexes.var.length === s.indexes.var.length && i.indexes.color.length === s.indexes.color.length && i.indexes.number.length >= s.indexes.number.length ? fi.has(e) && !s.values.length || fi.has(t) && !i.values.length ? Hu(e, t) : Wt(Aa(Xu(i, s), s.values), n) : (et(!0, `Complex values '${e}' and '${t}' too different to mix. Ensure all colors are of the same type, and that each contains the same quantity of number and color values. Falling back to instant transition.`, "complex-values-different"), xn(e, t));
}, or = /^(-?(?:\d+(?:\.\d*)?|\.\d+))([a-z%]*)$/iu;
function Qu(e, t) {
  const n = or.exec(e);
  if (!n)
    return;
  const i = or.exec(t);
  if (!i || n[2] !== i[2])
    return;
  const s = n[2], r = parseFloat(n[1]), o = parseFloat(i[1]);
  return (a) => ut(q(r, o, a)) + s;
}
function us(e, t, n) {
  if (typeof e == "number" && typeof t == "number" && typeof n == "number")
    return q(e, t, n);
  if (typeof e == "string" && typeof t == "string") {
    const s = Qu(e, t);
    if (s)
      return s;
  }
  return cs(e)(e, t);
}
const Ju = (e) => {
  const t = ({ timestamp: n }) => e(n);
  return {
    start: (n = !0) => G.update(t, n),
    stop: () => Re(t),
    /**
     * If we're processing this frame we can use the
     * framelocked timestamp to keep things in sync.
     */
    now: () => te.isProcessing ? te.timestamp : ae.now()
  };
}, Pa = (e, t, n = 10) => {
  let i = "";
  const s = Math.max(Math.round(t / n), 2);
  for (let r = 0; r < s; r++)
    i += Math.round(e(r / (s - 1)) * 1e4) / 1e4 + ", ";
  return `linear(${i.substring(0, i.length - 2)})`;
}, ds = 2e4;
function fs(e, t = 50, n = ds, i) {
  let s = 0, r = e.next(s);
  for (; !r.done && s < n; )
    s += t, r = e.next(s);
  return s >= n ? 1 / 0 : s;
}
function Ma(e, t = 100, n) {
  const i = n({ ...e, keyframes: [0, t] }), s = Math.min(fs(i), ds);
  return {
    type: "keyframes",
    ease: (r) => i.next(s * r).value / t,
    duration: /* @__PURE__ */ me(s)
  };
}
const Q = {
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
function hi(e, t) {
  return e * Math.sqrt(1 - t * t);
}
const ed = 12;
function td(e, t, n) {
  let i = n;
  for (let s = 1; s < ed; s++)
    i = i - e(i) / t(i);
  return i;
}
const Gn = 1e-3;
function nd({ duration: e = Q.duration, bounce: t = Q.bounce, velocity: n = Q.velocity, mass: i = Q.mass }) {
  let s, r;
  et(e <= /* @__PURE__ */ pe(Q.maxDuration), "Spring duration must be 10 seconds or less", "spring-duration-limit");
  let o = 1 - t;
  o = Ne(Q.minDamping, Q.maxDamping, o), e = Ne(Q.minDuration, Q.maxDuration, /* @__PURE__ */ me(e)), o < 1 ? (s = (u) => {
    const d = u * o, h = d * e, f = d - n, p = hi(u, o), g = Math.exp(-h);
    return Gn - f / p * g;
  }, r = (u) => {
    const h = u * o * e, f = h * n + n, p = o * o * u * u * e, g = Math.exp(-h), v = hi(u * u, o);
    return (-s(u) + Gn > 0 ? -1 : 1) * ((f - p) * g) / v;
  }) : (s = (u) => {
    const d = Math.exp(-u * e), h = (u - n) * e + 1;
    return -Gn + d * h;
  }, r = (u) => {
    const d = Math.exp(-u * e), h = (n - u) * (e * e);
    return d * h;
  });
  const a = 5 / e, l = td(s, r, a);
  if (e = /* @__PURE__ */ pe(e), isNaN(l))
    return {
      stiffness: Q.stiffness,
      damping: Q.damping,
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
const Ca = ["duration", "bounce"], Ea = ["stiffness", "damping", "mass"];
function vn(e, t) {
  return t.some((n) => e[n] !== void 0);
}
function id(e) {
  let t = {
    velocity: Q.velocity,
    stiffness: Q.stiffness,
    damping: Q.damping,
    mass: Q.mass,
    isResolvedFromDuration: !1,
    ...e
  };
  if (!vn(e, Ea) && vn(e, Ca))
    if (t.velocity = 0, e.visualDuration) {
      const n = e.visualDuration, i = 2 * Math.PI / (n * 1.2), s = i * i, r = 2 * Ne(0.05, 1, 1 - (e.bounce || 0)) * Math.sqrt(s);
      t = {
        ...t,
        mass: Q.mass,
        stiffness: s,
        damping: r
      };
    } else {
      const n = nd({ ...e, velocity: 0 });
      t = {
        ...t,
        ...n,
        mass: Q.mass
      }, t.isResolvedFromDuration = !0;
    }
  return t;
}
function Ot(e = Q.visualDuration, t = Q.bounce) {
  const n = typeof e != "object" ? {
    visualDuration: e,
    keyframes: [0, 1],
    bounce: t
  } : e, i = n.keyframes[0], s = n.keyframes[n.keyframes.length - 1], r = { done: !1, value: i }, { stiffness: o, damping: a, mass: l, duration: u, velocity: d, isResolvedFromDuration: h } = id({
    ...n,
    velocity: -/* @__PURE__ */ me(n.velocity || 0)
  }), f = a / (2 * Math.sqrt(o * l)), p = /* @__PURE__ */ me(Math.sqrt(o / l)), g = f * p, v = {
    target: s,
    delta: s - i,
    velocity: d || 0,
    restSpeed: 0,
    restDelta: 0
  }, b = () => {
    const k = Math.abs(v.delta) < 5;
    v.restSpeed = n.restSpeed || (k ? Q.restSpeed.granular : Q.restSpeed.default), v.restDelta = n.restDelta || (k ? Q.restDelta.granular : Q.restDelta.default);
  };
  b();
  let w, T, y;
  if (f < 1) {
    const k = hi(p, f), m = { A: 0, sinC: 0, cosC: 0, t: -1, env: 0, sin: 0, cos: 0 };
    y = () => {
      m.A = (v.velocity + g * v.delta) / k, m.sinC = g * m.A + v.delta * k, m.cosC = g * v.delta - m.A * k;
    };
    const S = (A) => {
      A !== m.t && (m.t = A, m.env = Math.exp(-g * A), m.sin = Math.sin(k * A), m.cos = Math.cos(k * A));
    };
    w = (A) => (S(A), v.target - m.env * (m.A * m.sin + v.delta * m.cos)), T = (A) => (S(A), m.env * (m.sinC * m.sin + m.cosC * m.cos));
  } else if (f === 1) {
    w = (m) => v.target - Math.exp(-p * m) * (v.delta + (v.velocity + p * v.delta) * m);
    const k = { C: 0 };
    y = () => {
      k.C = v.velocity + p * v.delta;
    }, T = (m) => Math.exp(-p * m) * (p * k.C * m - v.velocity);
  } else {
    const k = p * Math.sqrt(f * f - 1);
    w = (S) => {
      const A = Math.exp(-g * S), L = Math.min(k * S, 300);
      return v.target - A * ((v.velocity + g * v.delta) * Math.sinh(L) + k * v.delta * Math.cosh(L)) / k;
    };
    const m = { P: 0, sinh: 0, cosh: 0 };
    y = () => {
      m.P = (v.velocity + g * v.delta) / k, m.sinh = g * m.P - v.delta * k, m.cosh = g * v.delta - m.P * k;
    }, T = (S) => {
      const A = Math.exp(-g * S), L = Math.min(k * S, 300);
      return A * (m.sinh * Math.sinh(L) + m.cosh * Math.cosh(L));
    };
  }
  y();
  const N = !vn(n, Ea) && vn(n, Ca), V = h && u || null, C = {
    calculatedDuration: V,
    /**
     * Aim the spring at a new target from its current position and
     * velocity, reusing the resolved physics and closures.
     */
    retarget: (k, m) => {
      v.target = k[k.length - 1], v.delta = v.target - k[0], v.velocity = N ? 0 : -/* @__PURE__ */ me(m), n.restSpeed && n.restDelta || b(), C.calculatedDuration = V, r.done = !1, y();
    },
    velocity: (k) => /* @__PURE__ */ pe(T(k)),
    next: (k) => {
      const m = w(k);
      if (h)
        r.done = k >= u;
      else {
        const S = /* @__PURE__ */ pe(T(k));
        r.done = Math.abs(S) <= v.restSpeed && Math.abs(v.target - m) <= v.restDelta;
      }
      return r.value = r.done ? v.target : m, r;
    },
    toString: () => {
      const k = Math.min(fs(C), ds), m = Pa((S) => C.next(k * S).value, k, 30);
      return k + "ms " + m;
    },
    toTransition: () => {
    }
  };
  return C;
}
Ot.applyToOptions = (e) => {
  const t = Ma(e, 100, Ot);
  return e.ease = t.ease, e.duration = /* @__PURE__ */ pe(t.duration), e.type = "keyframes", e;
};
function pi({ keyframes: e, velocity: t = 0, power: n = 0.8, timeConstant: i = 325, bounceDamping: s = 10, bounceStiffness: r = 500, modifyTarget: o, min: a, max: l, restDelta: u = 0.5, restSpeed: d }) {
  const h = e[0], f = {
    done: !1,
    value: h
  }, p = (k) => k < a || k > l, g = (k) => a === void 0 ? l : l === void 0 || Math.abs(a - k) < Math.abs(l - k) ? a : l;
  let v = n * t;
  const b = h + v, w = o === void 0 ? b : o(b);
  w !== b && (v = w - h);
  const T = (k) => -v * Math.exp(-k / i), y = (k) => {
    const m = T(k);
    f.done = Math.abs(m) <= u, f.value = f.done ? w : w + m;
  };
  let N, V;
  const C = (k) => {
    p(f.value) && (N = k, V = Ot({
      keyframes: [f.value, g(f.value)],
      /**
       * The friction curve is target + calcDelta(t), so its exact
       * derivative is -calcDelta(t) / timeConstant in units/ms,
       * converted here to the units/second expected by spring.
       */
      velocity: -T(k) / i * 1e3,
      damping: s,
      stiffness: r,
      restDelta: u,
      restSpeed: d
    }));
  };
  return C(0), {
    calculatedDuration: null,
    next: (k) => {
      let m = !1;
      return !V && N === void 0 && (m = !0, y(k), C(k)), N !== void 0 && k >= N ? V.next(k - N) : (!m && y(k), f);
    }
  };
}
function sd(e, t, n) {
  const i = [], s = n || Ve.mix || us, r = e.length - 1;
  for (let o = 0; o < r; o++) {
    let a = s(e[o], e[o + 1]);
    if (t) {
      const l = Array.isArray(t) ? t[o] || Se : t;
      a = Wt(l, a);
    }
    i.push(a);
  }
  return i;
}
function Da(e, t, { clamp: n = !0, ease: i, mixer: s } = {}) {
  const r = e.length;
  if (xe(r === t.length, "Both input and output ranges must be the same length", "range-length"), r === 1)
    return () => t[0];
  if (r === 2 && t[0] === t[1])
    return () => t[1];
  const o = e[0] === e[1];
  e[0] > e[r - 1] && (e = [...e].reverse(), t = [...t].reverse());
  const a = sd(t, i, s), l = a.length, u = (d) => {
    if (o && d < e[0])
      return t[0];
    let h = 0;
    if (l > 1)
      for (; h < e.length - 2 && !(d < e[h + 1]); h++)
        ;
    const f = /* @__PURE__ */ ft(e[h], e[h + 1], d);
    return a[h](f);
  };
  return n ? (d) => u(Ne(e[0], e[r - 1], d)) : u;
}
function Va(e, t) {
  const n = e[e.length - 1];
  for (let i = 1; i <= t; i++) {
    const s = /* @__PURE__ */ ft(0, t, i);
    e.push(q(n, 1, s));
  }
}
function Ra(e) {
  const t = [0];
  return Va(t, e.length - 1), t;
}
function rd(e, t) {
  return e.map((n) => n * t);
}
function od(e, t) {
  return e.map(() => t || ha).splice(0, e.length - 1);
}
function ot({ duration: e = 300, keyframes: t, times: n, ease: i = "easeInOut" }) {
  const s = /* @__PURE__ */ pa(i) ? i.map(er) : er(i), r = {
    done: !1,
    value: t[0]
  };
  if (t.length === 2 && !Array.isArray(s) && (!n || n.length !== 2 || n[0] === 0 && n[1] === 1)) {
    const [l, u] = t, d = l === u ? void 0 : (Ve.mix || us)(l, u);
    return {
      calculatedDuration: e,
      next: (h) => (r.value = d ? d(s(e > 0 ? Ne(0, 1, h / e) : 1)) : u, r.done = h >= e, r)
    };
  }
  const o = rd(
    // Only use the provided offsets if they're the correct length
    // TODO Maybe we should warn here if there's a length mismatch
    n && n.length === t.length ? n : Ra(t),
    e
  ), a = Da(o, t, {
    ease: Array.isArray(s) ? s : od(t, s)
  });
  return {
    calculatedDuration: e,
    next: (l) => (r.value = a(l), r.done = l >= e, r)
  };
}
const ad = 5;
function ld(e, t, n) {
  const i = Math.max(t - ad, 0);
  return /* @__PURE__ */ ra(n - e(i), t - i);
}
function cd(e, t, n = 0) {
  return t <= 0 ? n : e.velocity ? e.velocity(t) : ld((i) => e.next(i).value, t, e.next(t).value);
}
const ud = (e) => e !== null;
function Dn(e, { repeat: t, repeatType: n = "loop" }, i, s = 1) {
  const r = e.filter(ud), a = s < 0 || t && n !== "loop" && t % 2 === 1 ? 0 : r.length - 1;
  return !a || i === void 0 ? r[a] : i;
}
const dd = {
  decay: pi,
  inertia: pi,
  tween: ot,
  keyframes: ot,
  spring: Ot
};
function La(e) {
  typeof e.type == "string" && (e.type = dd[e.type]);
}
function Fa(e, t) {
  return {
    kind: e,
    animation: t,
    timestamp: ae.now(),
    frameTimestamp: te.timestamp,
    frameIsProcessing: te.isProcessing
  };
}
function Oa(e, t, n) {
  const i = globalThis.__MOTION_INSPECT__;
  if (i)
    try {
      i({
        ...Fa("animation-start", e),
        options: n ? { ...t, ...n } : t
      });
    } catch {
    }
}
function fd(e, t) {
  const n = globalThis.__MOTION_INSPECT__;
  if (n)
    try {
      n({
        ...Fa("layout-animation-start", e),
        node: t
      });
    } catch {
    }
}
class hs {
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
const hd = (e) => e / 100;
class bn extends hs {
  constructor(t) {
    super(), this.state = "idle", this.startTime = null, this.isStopped = !1, this.currentTime = 0, this.holdTime = null, this.playbackSpeed = 1, this.delayState = {
      done: !1,
      value: void 0
    }, this.stop = () => {
      const { motionValue: n } = this.options;
      n && n.updatedAt !== ae.now() && this.tick(ae.now()), this.isStopped = !0, this.state !== "idle" && (this.teardown(), this.options.onStop?.());
    }, this.options = t, this.initAnimation(), this.play(), t.autoplay === !1 && this.pause(), Oa(this, this.options);
  }
  initAnimation() {
    const { options: t } = this;
    La(t);
    const { type: n = ot, repeat: i = 0, repeatDelay: s = 0, repeatType: r, velocity: o = 0 } = t;
    let { keyframes: a } = t;
    const l = n || ot;
    process.env.NODE_ENV !== "production" && l !== ot && xe(a.length <= 2, `Only two keyframes currently supported with spring and inertia animations. Trying to animate ${a}`, "spring-two-frames"), l !== ot && typeof a[0] != "number" && (this.mixKeyframes = Wt(hd, us(a[0], a[1])), a = [0, 100]);
    const u = l(a === t.keyframes ? t : { ...t, keyframes: a });
    r === "mirror" && (this.mirroredGenerator = l({
      ...t,
      keyframes: [...a].reverse(),
      velocity: -o
    })), u.calculatedDuration === null && (u.calculatedDuration = fs(u));
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
    const { delay: u = 0, keyframes: d, repeat: h, repeatType: f, repeatDelay: p, type: g, onUpdate: v, finalKeyframe: b } = this.options;
    this.speed > 0 ? this.startTime = Math.min(this.startTime, t) : this.speed < 0 && (this.startTime = Math.min(t - s / this.speed, this.startTime)), n ? this.currentTime = t : this.updateTime(t);
    const w = this.currentTime - u * (this.playbackSpeed >= 0 ? 1 : -1), T = this.playbackSpeed >= 0 ? w < 0 : w > s;
    this.currentTime = Math.max(w, 0), this.state === "finished" && this.holdTime === null && (this.currentTime = s);
    let y = this.currentTime, N = i;
    if (h) {
      const m = Math.min(this.currentTime, s) / a;
      let S = Math.floor(m), A = m % 1;
      !A && m >= 1 && (A = 1), A === 1 && S--, S = Math.min(S, h + 1), S % 2 && (f === "reverse" ? (A = 1 - A, p && (A -= p / a)) : f === "mirror" && (N = o)), y = Ne(0, 1, A) * a;
    }
    let V;
    T ? (this.delayState.value = d[0], V = this.delayState) : V = N.next(y), r && !T && (V.value = r(V.value));
    let { done: C } = V;
    !T && l !== null && (C = this.playbackSpeed >= 0 ? this.currentTime >= s : this.currentTime <= 0);
    const k = this.holdTime === null && (this.state === "finished" || this.state === "running" && C);
    return k && g !== pi && (V.value = Dn(d, this.options, b, this.speed)), v && v(V.value), k && this.finish(), V;
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
    return /* @__PURE__ */ me(this.calculatedDuration);
  }
  get iterationDuration() {
    const { delay: t = 0 } = this.options || {};
    return this.duration + /* @__PURE__ */ me(t);
  }
  get time() {
    return /* @__PURE__ */ me(this.currentTime);
  }
  set time(t) {
    t = /* @__PURE__ */ pe(t), this.currentTime = t, this.startTime === null || this.holdTime !== null || this.playbackSpeed === 0 ? this.holdTime = t : this.driver && (this.startTime = this.driver.now() - t / this.playbackSpeed), this.driver ? this.driver.start(!1) : (this.startTime = 0, this.state = "paused", this.holdTime = t, this.tick(t));
  }
  /**
   * Returns the generator's velocity at the current time in units/second.
   * Uses the analytical derivative when available (springs), avoiding
   * the MotionValue's frame-dependent velocity estimation.
   */
  getGeneratorVelocity() {
    return cd(this.generator, this.currentTime, this.options.velocity);
  }
  get speed() {
    return this.playbackSpeed;
  }
  set speed(t) {
    const n = this.playbackSpeed !== t;
    n && this.driver && this.updateTime(ae.now()), this.playbackSpeed = t, n && this.driver && (this.time = /* @__PURE__ */ me(this.currentTime));
  }
  play() {
    if (this.isStopped)
      return;
    const { driver: t = Ju, startTime: n } = this.options;
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
const pd = /* @__PURE__ */ new Set(["brightness", "contrast", "saturate", "opacity"]);
function md(e) {
  const [t, n] = e.slice(0, -1).split("(");
  if (t === "drop-shadow")
    return e;
  const [i] = n.match(as) || [];
  if (!i)
    return e;
  const s = n.replace(i, "");
  let r = pd.has(t) ? 1 : 0;
  return i !== n && (r *= 100), t + "(" + r + s + ")";
}
const gd = /\b([a-z-]*)\(.*?\)/gu, mi = {
  ...ye,
  getAnimatableNone: (e) => {
    const t = e.match(gd);
    return t ? t.map(md).join(" ") : e;
  }
}, gi = {
  ...ye,
  getAnimatableNone: (e) => {
    const t = ye.parse(e);
    return ye.createTransformer(e)(t.map((i) => typeof i == "number" ? 0 : typeof i == "object" ? { ...i, alpha: 1 } : i));
  }
}, ar = {
  ...gt,
  transform: Math.round
}, yi = {
  rotate: De,
  /**
   * Internal channel for `transition.path` orientToPath. Composed onto
   * `rotate` at the transform-build sites so the user's `rotate` is
   * never read or overwritten. Not part of `transformPropOrder`.
   */
  pathRotation: De,
  rotateX: De,
  rotateY: De,
  rotateZ: De,
  scale: Zt,
  scaleX: Zt,
  scaleY: Zt,
  scaleZ: Zt,
  skew: De,
  skewX: De,
  skewY: De,
  distance: E,
  translateX: E,
  translateY: E,
  translateZ: E,
  x: E,
  y: E,
  z: E,
  perspective: E,
  transformPerspective: E,
  opacity: Lt,
  originX: nr,
  originY: nr,
  originZ: E
}, Ee = {
  // Border props
  borderWidth: E,
  borderTopWidth: E,
  borderRightWidth: E,
  borderBottomWidth: E,
  borderLeftWidth: E,
  borderRadius: E,
  borderTopLeftRadius: E,
  borderTopRightRadius: E,
  borderBottomRightRadius: E,
  borderBottomLeftRadius: E,
  // Positioning props
  width: E,
  maxWidth: E,
  height: E,
  maxHeight: E,
  top: E,
  right: E,
  bottom: E,
  left: E,
  inset: E,
  insetBlock: E,
  insetBlockStart: E,
  insetBlockEnd: E,
  insetInline: E,
  insetInlineStart: E,
  insetInlineEnd: E,
  // Spacing props
  padding: E,
  paddingTop: E,
  paddingRight: E,
  paddingBottom: E,
  paddingLeft: E,
  paddingBlock: E,
  paddingBlockStart: E,
  paddingBlockEnd: E,
  paddingInline: E,
  paddingInlineStart: E,
  paddingInlineEnd: E,
  margin: E,
  marginTop: E,
  marginRight: E,
  marginBottom: E,
  marginLeft: E,
  marginBlock: E,
  marginBlockStart: E,
  marginBlockEnd: E,
  marginInline: E,
  marginInlineStart: E,
  marginInlineEnd: E,
  // Typography
  fontSize: E,
  // Misc
  backgroundPositionX: E,
  backgroundPositionY: E,
  ...yi,
  zIndex: ar,
  // SVG
  fillOpacity: Lt,
  strokeOpacity: Lt,
  numOctaves: ar
}, yd = {
  ...Ee,
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
  filter: mi,
  WebkitFilter: mi,
  mask: gi,
  WebkitMask: gi
}, Ia = (e) => yd[e], xd = /* @__PURE__ */ new Set([mi, gi]);
function ps(e, t) {
  let n = Ia(e);
  return xd.has(n) || (n = ye), n.getAnimatableNone ? n.getAnimatableNone(t) : void 0;
}
function vd(e) {
  for (let t = 1; t < e.length; t++)
    e[t] ?? (e[t] = e[t - 1]);
}
const qe = (e) => e * 180 / Math.PI, xi = (e) => {
  const t = qe(Math.atan2(e[1], e[0]));
  return vi(t);
}, bd = {
  x: 4,
  y: 5,
  translateX: 4,
  translateY: 5,
  scaleX: 0,
  scaleY: 3,
  scale: (e) => (Math.abs(e[0]) + Math.abs(e[3])) / 2,
  rotate: xi,
  rotateZ: xi,
  skewX: (e) => qe(Math.atan(e[1])),
  skewY: (e) => qe(Math.atan(e[2])),
  skew: (e) => (Math.abs(e[1]) + Math.abs(e[2])) / 2
}, vi = (e) => (e = e % 360, e < 0 && (e += 360), e), lr = xi, cr = (e) => Math.sqrt(e[0] * e[0] + e[1] * e[1]), ur = (e) => Math.sqrt(e[4] * e[4] + e[5] * e[5]), wd = {
  x: 12,
  y: 13,
  z: 14,
  translateX: 12,
  translateY: 13,
  translateZ: 14,
  scaleX: cr,
  scaleY: ur,
  scale: (e) => (cr(e) + ur(e)) / 2,
  rotateX: (e) => vi(qe(Math.atan2(e[6], e[5]))),
  rotateY: (e) => vi(qe(Math.atan2(-e[2], e[0]))),
  rotateZ: lr,
  rotate: lr,
  skewX: (e) => qe(Math.atan(e[4])),
  skewY: (e) => qe(Math.atan(e[1])),
  skew: (e) => (Math.abs(e[1]) + Math.abs(e[4])) / 2
};
function bi(e) {
  return e.includes("scale") ? 1 : 0;
}
function wi(e, t) {
  if (!e || e === "none")
    return bi(t);
  const n = e.match(/^matrix3d\(([-\d.e\s,]+)\)$/u);
  let i, s;
  if (n)
    i = wd, s = n;
  else {
    const a = e.match(/^matrix\(([-\d.e\s,]+)\)$/u);
    i = bd, s = a;
  }
  if (!s)
    return bi(t);
  const r = i[t], o = s[1].split(",").map(kd);
  return typeof r == "function" ? r(o) : o[r];
}
const Ba = (e, t) => {
  const { transform: n = "none" } = getComputedStyle(e);
  return wi(n, t);
};
function kd(e) {
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
], Oe = /* @__PURE__ */ new Set([...je, "pathRotation"]), dr = (e) => e === gt || e === E, Td = /* @__PURE__ */ new Set(["x", "y", "z"]), Sd = je.filter((e) => !Td.has(e));
function Nd(e) {
  const t = [];
  return Sd.forEach((n) => {
    const i = e.getValue(n);
    if (i !== void 0) {
      const s = i.get(), r = n.startsWith("scale") ? 1 : 0;
      if (s === r)
        return;
      t.push([n, s]), i.set(r);
    }
  }), t;
}
const Ad = /* @__PURE__ */ new Set(["bottom", "right"]);
function fr(e, t, n, i, s, r) {
  const o = parseFloat(e);
  if (!isNaN(o))
    return o;
  const { min: a, max: l } = t()[n], u = l - a;
  return r === "border-box" ? u : u - parseFloat(i) - parseFloat(s);
}
const Ye = {
  // Dimensions
  width: ({ width: e, paddingLeft: t = "0", paddingRight: n = "0", boxSizing: i }, s) => fr(e, s, "x", t, n, i),
  height: ({ height: e, paddingTop: t = "0", paddingBottom: n = "0", boxSizing: i }, s) => fr(e, s, "y", t, n, i),
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
  x: ({ transform: e }) => wi(e, "x"),
  y: ({ transform: e }) => wi(e, "y")
};
Ye.translateX = Ye.x;
Ye.translateY = Ye.y;
const Xe = /* @__PURE__ */ new Set();
let ki = !1, Ti = !1, Si = !1;
function $a() {
  if (Ti) {
    const e = [], t = /* @__PURE__ */ new Set(), n = /* @__PURE__ */ new Set();
    Xe.forEach((s) => {
      s.needsMeasurement && (e.push(s), t.add(s.element), Ad.has(s.name) && n.add(s.element));
    });
    const i = /* @__PURE__ */ new Map();
    n.forEach((s) => {
      const r = Nd(s);
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
  Ti = !1, ki = !1, Xe.forEach((e) => e.complete(Si)), Xe.clear();
}
function ja() {
  Xe.forEach((e) => {
    e.readKeyframes(), e.needsMeasurement && (Ti = !0);
  });
}
function Pd() {
  Si = !0, ja(), $a(), Si = !1;
}
function Md(e, t, n) {
  if (typeof e == "string") {
    if (es(e) || ns(e))
      return parseFloat(e);
    if (!ye.test(e) && ye.test(n))
      return ps(t, n);
  }
  return e ?? void 0;
}
class ms {
  constructor(t, n, i, s, r, o = !1) {
    this.state = "pending", this.isAsync = !1, this.needsMeasurement = !1, this.unresolvedKeyframes = [...t], this.onComplete = n, this.name = i, this.motionValue = s, this.element = r, this.isAsync = o;
  }
  scheduleResolve() {
    this.state = "scheduled", this.isAsync ? (Xe.add(this), ki || (ki = !0, G.read(ja), G.resolveKeyframes($a))) : (this.readKeyframes(), this.complete());
  }
  readKeyframes() {
    const { unresolvedKeyframes: t, name: n, element: i, motionValue: s } = this;
    if (t[0] === null) {
      const r = s?.get(), o = t[t.length - 1];
      if (r !== void 0)
        t[0] = r;
      else if (i && n) {
        const a = Md(i.readValue(n, o), n, o);
        a !== void 0 && (t[0] = a);
      }
      t[0] === void 0 && (t[0] = o), s && r === void 0 && s.set(t[0]);
    }
    vd(t);
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
    this.state = "complete", this.onComplete(this.unresolvedKeyframes, this.finalKeyframe, t), Xe.delete(this);
  }
  cancel() {
    this.state === "scheduled" && (Xe.delete(this), this.state = "pending");
  }
  resume() {
    this.state === "pending" && this.scheduleResolve();
  }
}
const gs = (e) => e.startsWith("--");
function Ua(e, t, n) {
  gs(t) ? e.style.setProperty(t, n) : e.style[t] = n;
}
const Cd = {};
function za(e, t) {
  const n = /* @__PURE__ */ sa(e);
  return () => Cd[t] ?? n();
}
const Ed = /* @__PURE__ */ za(() => window.ScrollTimeline !== void 0, "scrollTimeline"), Wa = /* @__PURE__ */ za(() => {
  try {
    document.createElement("div").animate({ opacity: 0 }, { easing: "linear(0, 1)" });
  } catch {
    return !1;
  }
  return !0;
}, "linearEasing"), At = ([e, t, n, i]) => `cubic-bezier(${e}, ${t}, ${n}, ${i})`, hr = {
  linear: "linear",
  ease: "ease",
  easeIn: "ease-in",
  easeOut: "ease-out",
  easeInOut: "ease-in-out",
  circIn: /* @__PURE__ */ At([0, 0.65, 0.55, 1]),
  circOut: /* @__PURE__ */ At([0.55, 0, 1, 0.45]),
  backIn: /* @__PURE__ */ At([0.31, 0.01, 0.66, -0.59]),
  backOut: /* @__PURE__ */ At([0.33, 1.53, 0.69, 0.99])
};
function _a(e, t) {
  if (e)
    return typeof e == "function" ? Wa() ? Pa(e, t) : "ease-out" : /* @__PURE__ */ ga(e) ? At(e) : Array.isArray(e) ? e.map((n) => _a(n, t) || hr.easeOut) : hr[e];
}
function Dd(e, t, n, { delay: i = 0, duration: s = 300, repeat: r = 0, repeatType: o = "loop", ease: a = "easeOut", times: l } = {}, u = void 0) {
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
function ys(e) {
  return typeof e == "function" && "applyToOptions" in e;
}
function Vd({ type: e, ...t }) {
  return ys(e) && Wa() ? e.applyToOptions(t) : (t.duration ?? (t.duration = 300), t.ease ?? (t.ease = "easeOut"), t);
}
class Ga extends hs {
  constructor(t) {
    if (super(), this.finishedTime = null, this.isStopped = !1, this.manualStartTime = null, !t)
      return;
    const { element: n, name: i, keyframes: s, pseudoElement: r, allowFlatten: o = !1, finalKeyframe: a, onComplete: l } = t;
    this.isPseudoElement = !!r, this.allowFlatten = o, this.options = t, xe(typeof t.type != "string", `Mini animate() doesn't support "type" as a string.`, "mini-spring");
    const u = Vd(t);
    this.animation = Dd(n, i, s, u, r), u.autoplay === !1 && this.animation.pause(), this.animation.onfinish = () => {
      if (this.finishedTime = this.time, !r) {
        const d = Dn(s, this.options, a, this.speed);
        this.updateMotionValue && this.updateMotionValue(d), Ua(n, i, d), this.animation.cancel();
      }
      l?.(), this.notifyFinished();
    }, Oa(this, t, u);
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
    return /* @__PURE__ */ me(Number(t));
  }
  get iterationDuration() {
    const { delay: t = 0 } = this.options || {};
    return this.duration + /* @__PURE__ */ me(t);
  }
  get time() {
    return /* @__PURE__ */ me(Number(this.animation.currentTime) || 0);
  }
  set time(t) {
    const n = this.finishedTime !== null;
    this.manualStartTime = null, this.finishedTime = null, this.animation.currentTime = /* @__PURE__ */ pe(t), n && this.animation.pause();
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
    return this.allowFlatten && this.animation.effect?.updateTiming({ easing: "linear" }), this.animation.onfinish = null, t && Ed() ? (this.animation.timeline = t, n && (this.animation.rangeStart = n), i && (this.animation.rangeEnd = i), Se) : s(this);
  }
}
const Ka = {
  anticipate: ua,
  backInOut: ca,
  circInOut: fa
};
function Rd(e) {
  return e in Ka;
}
function Ld(e) {
  typeof e.ease == "string" && Rd(e.ease) && (e.ease = Ka[e.ease]);
}
const Kn = 10;
class Fd extends Ga {
  constructor(t) {
    Ld(t), La(t), super(t), t.startTime !== void 0 && t.autoplay !== !1 && (this.startTime = t.startTime), this.options = t;
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
    const a = new bn({
      ...o,
      autoplay: !1
    }), l = Math.max(Kn, ae.now() - this.startTime), u = Ne(0, Kn, l - Kn), d = a.sample(l).value, { name: h } = this.options;
    r && h && Ua(r, h, d), n.setWithVelocity(a.sample(Math.max(0, l - u)).value, d, u), a.stop();
  }
}
const pr = (e, t) => t === "zIndex" ? !1 : !!(typeof e == "number" || Array.isArray(e) || typeof e == "string" && // It's animatable if we have a string
(ye.test(e) || e === "0") && // And it contains numbers and/or colors
!e.startsWith("url("));
function Od(e) {
  const t = e[0];
  if (e.length === 1)
    return !0;
  for (let n = 0; n < e.length; n++)
    if (e[n] !== t)
      return !0;
}
function Id(e, t, n, i) {
  const s = e[0];
  if (s === null)
    return !1;
  if (t === "display" || t === "visibility")
    return !0;
  const r = e[e.length - 1], o = pr(s, t), a = pr(r, t);
  return !o || !a ? (o !== a && et(!1, `You are trying to animate ${t} from "${s}" to "${r}". "${o ? r : s}" is not an animatable value.`, "value-not-animatable"), !1) : Od(e) || (n === "spring" || ys(n)) && i;
}
function Ni(e) {
  e.duration = 0, e.type = "keyframes";
}
const Ai = /* @__PURE__ */ new Set([
  "opacity",
  "clipPath",
  "filter",
  "transform",
  "backgroundColor"
]), Bd = /^(?:oklch|oklab|lab|lch|color|color-mix|light-dark)\(/;
function $d(e) {
  for (let t = 0; t < e.length; t++)
    if (typeof e[t] == "string" && Bd.test(e[t]))
      return !0;
  return !1;
}
const mr = /* @__PURE__ */ new Set([
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
]), jd = /* @__PURE__ */ sa(() => Object.hasOwnProperty.call(Element.prototype, "animate"));
function Ud(e) {
  const { motionValue: t, name: n, repeatDelay: i, repeatType: s, damping: r, type: o, keyframes: a } = e;
  if (!n || !(Ai.has(n) || mr.has(n)))
    return !1;
  const l = t?.owner?.current;
  if (!(l instanceof HTMLElement) && !(l instanceof SVGElement))
    return !1;
  const { onUpdate: u, transformTemplate: d } = t.owner.getProps();
  return jd() && /**
   * Force WAAPI for color properties with browser-only color formats
   * (oklch, oklab, lab, lch, etc.) that the JS animation path can't parse.
   */
  (Ai.has(n) || mr.has(n) && $d(a)) && (n !== "transform" || !d) && /**
   * If we're outputting values to onUpdate then we can't use WAAPI as there's
   * no way to read the value from WAAPI every frame.
   */
  !u && !i && s !== "mirror" && r !== 0 && o !== "inertia";
}
const zd = 40;
class Wd extends hs {
  constructor(t) {
    super(), this.stop = () => {
      this._animation && (this._animation.stop(), this.stopTimeline?.()), this.keyframeResolver?.cancel();
    }, this.createdAt = ae.now();
    const { keyframes: n, name: i, motionValue: s, element: r } = t, o = t;
    o.autoplay ?? (o.autoplay = !0), o.delay ?? (o.delay = 0), o.type ?? (o.type = "keyframes"), o.repeat ?? (o.repeat = 0), o.repeatDelay ?? (o.repeatDelay = 0), o.repeatType ?? (o.repeatType = "loop");
    const a = r?.KeyframeResolver || ms;
    this.keyframeResolver = new a(n, (l, u, d) => this.onKeyframesResolved(l, u, o, !d), i, s, r), this.keyframeResolver?.scheduleResolve();
  }
  onKeyframesResolved(t, n, i, s) {
    this.keyframeResolver = void 0;
    const { name: r, type: o, velocity: a, delay: l, isHandoff: u, onUpdate: d } = i;
    this.resolvedAt = ae.now();
    let h = !0;
    Id(t, r, o, a) || (h = !1, (Ve.instantAnimations || !l) && d?.(Dn(t, i, n)), t[0] = t[t.length - 1], Ni(i), i.repeat = 0);
    const f = s ? this.resolvedAt ? this.resolvedAt - this.createdAt > zd ? this.resolvedAt : this.createdAt : this.createdAt : void 0, { onComplete: p } = i;
    i.startTime ?? (i.startTime = f), i.finalKeyframe = n, i.keyframes = t, i.onComplete = () => {
      p?.(), this.notifyFinished();
    };
    const g = h && !u && Ud(i);
    let v;
    if (g) {
      i.element = i.motionValue?.owner?.current;
      try {
        v = new Fd(i);
      } catch {
        v = new bn(i);
      }
    } else
      v = new bn(i);
    this.pendingTimeline && (this.stopTimeline = v.attachTimeline(this.pendingTimeline), this.pendingTimeline = void 0), this._animation = v;
  }
  get finished() {
    return this._animation ? this._animation.finished : super.finished;
  }
  then(t, n) {
    return this.finished.finally(t).then(() => {
    });
  }
  get animation() {
    return this._animation || (this.keyframeResolver?.resume(), Pd()), this._animation;
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
class _d {
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
    return gr(this.animations, "duration");
  }
  get iterationDuration() {
    return gr(this.animations, "iterationDuration");
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
function gr(e, t) {
  let n = 0;
  for (let i = 0; i < e.length; i++) {
    const s = e[i][t];
    s !== null && s > n && (n = s);
  }
  return n;
}
class Gd extends _d {
  then(t, n) {
    return this.finished.finally(t).then(() => {
    });
  }
}
function Ha(e, t, n, i = 0, s = 1) {
  const r = Array.from(e).sort((u, d) => u.sortNodePosition(d)).indexOf(t), o = e.size, a = (o - 1) * i;
  return typeof n == "function" ? n(r, o) : s === 1 ? r * i : a - r * i;
}
const yr = 30, Kd = (e) => !isNaN(parseFloat(e)), Pt = {
  current: void 0
};
class Mt {
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
    this.current = t, this.updatedAt = ae.now(), this.canTrackVelocity === null && t !== void 0 && (this.canTrackVelocity = Kd(this.current));
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
    return process.env.NODE_ENV !== "production" && En(!1, 'value.onChange(callback) is deprecated. Switch to value.on("change", callback).'), this.on("change", t);
  }
  on(t, n) {
    var i;
    return t === "change" ? this.onChangeSubscribe(n) : ((i = this.events)[t] || (i[t] = new yn())).add(n);
  }
  onChangeSubscribe(t) {
    const { events: n } = this;
    return !n.change && !this.changeSubscriber ? this.changeSubscriber = t : (n.change || (n.change = new yn(), n.change.add(this.changeSubscriber), this.changeSubscriber = void 0), n.change.add(t)), () => {
      this.changeSubscriber === t ? this.changeSubscriber = void 0 : n.change?.remove(t), this.stopIfUnobserved();
    };
  }
  /**
   * If we have no more change listeners by the start
   * of the next frame, stop active animations.
   */
  stopIfUnobserved() {
    G.read(() => {
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
    return Pt.current && Pt.current.push(this), this.current;
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
    if (!this.canTrackVelocity || this.prevFrameValue === void 0 || t - this.updatedAt > yr)
      return 0;
    const n = Math.min(this.updatedAt - this.prevUpdatedAt, yr);
    return /* @__PURE__ */ ra(parseFloat(this.current) - parseFloat(this.prevFrameValue), n);
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
function Le(e, t) {
  return new Mt(e, t);
}
function qa(e, t) {
  if (e?.inherit && t) {
    const { inherit: n, ...i } = e;
    return { ...t, ...i };
  }
  return e;
}
function xs(e, t) {
  const n = e?.[t] ?? e?.default ?? e;
  return n !== e ? qa(n, e) : n;
}
const Hd = {
  type: "spring",
  stiffness: 500,
  damping: 25,
  restSpeed: 10
}, qd = (e) => ({
  type: "spring",
  stiffness: 550,
  damping: e === 0 ? 2 * Math.sqrt(550) : 30,
  restSpeed: 10
}), Yd = {
  type: "keyframes",
  duration: 0.8
}, Xd = {
  type: "keyframes",
  ease: [0.25, 0.1, 0.35, 1],
  duration: 0.3
}, Zd = (e, { keyframes: t }) => t.length > 2 ? Yd : Oe.has(e) ? e.startsWith("scale") ? qd(t[1]) : Hd : Xd, Qd = /* @__PURE__ */ new Set([
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
function Jd(e) {
  for (const t in e)
    if (!Qd.has(t))
      return !0;
  return !1;
}
const Vn = (e, t, n, i = {}, s, r) => (o) => {
  const a = xs(i, e) || {}, l = a.delay || i.delay || 0;
  let { elapsed: u = 0 } = i;
  u = u - /* @__PURE__ */ pe(l);
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
  Jd(a) || Object.assign(d, Zd(e, d)), d.duration && (d.duration = /* @__PURE__ */ pe(d.duration)), d.repeatDelay && (d.repeatDelay = /* @__PURE__ */ pe(d.repeatDelay)), d.from !== void 0 && (d.keyframes[0] = d.from);
  let h = !1;
  if ((d.type === !1 || d.duration === 0 && !d.repeatDelay) && (Ni(d), d.delay === 0 && (h = !0)), (Ve.instantAnimations || Ve.skipAnimations || s?.shouldSkipAnimations || a.skipAnimations) && (h = !0, Ni(d), d.delay = 0), d.allowFlatten = !a.type && !a.ease, h && !r && t.get() !== void 0) {
    const f = Dn(d.keyframes, a);
    if (f !== void 0) {
      G.update(() => {
        d.onUpdate(f), d.onComplete();
      });
      return;
    }
  }
  return a.isSync ? new bn(d) : new Wd(d);
}, ef = (
  // eslint-disable-next-line redos-detector/no-unsafe-regex -- false positive, as it can match a lot of words
  /^var\(--(?:([\w-]+)|([\w-]+), ?([a-zA-Z\d ()%#.,-]+))\)/u
);
function tf(e) {
  const t = ef.exec(e);
  if (!t)
    return [,];
  const [, n, i, s] = t;
  return [`--${n ?? i}`, s];
}
const nf = 4;
function Ya(e, t, n = 1) {
  xe(n <= nf, `Max CSS variable fallback depth detected in property "${e}". This may indicate a circular fallback dependency.`, "max-css-var-depth");
  const [i, s] = tf(e);
  if (!i)
    return;
  const r = window.getComputedStyle(t).getPropertyValue(i);
  if (r) {
    const o = r.trim();
    return es(o) ? parseFloat(o) : o;
  }
  return os(s) ? Ya(s, t, n + 1) : s;
}
function xr(e) {
  const t = [{}, {}];
  return e?.values.forEach((n, i) => {
    t[0][i] = n.get(), t[1][i] = n.getVelocity();
  }), t;
}
function vs(e, t, n, i) {
  if (typeof t == "function") {
    const [s, r] = xr(i);
    t = t(n !== void 0 ? n : e.custom, s, r);
  }
  if (typeof t == "string" && (t = e.variants && e.variants[t]), typeof t == "function") {
    const [s, r] = xr(i);
    t = t(n !== void 0 ? n : e.custom, s, r);
  }
  return t;
}
function Ze(e, t, n) {
  const i = e.getProps();
  return vs(i, t, n !== void 0 ? n : i.custom, e);
}
const bs = /* @__PURE__ */ new Set([
  "width",
  "height",
  "top",
  "left",
  "right",
  "bottom",
  ...je
]), Pi = (e) => Array.isArray(e);
function sf(e, t, n) {
  e.hasValue(t) ? e.getValue(t).set(n) : e.addValue(t, Le(n));
}
function rf(e) {
  return Pi(e) ? e[e.length - 1] || 0 : e;
}
function of(e, t) {
  const n = Ze(e, t);
  let { transitionEnd: i = {}, transition: s = {}, ...r } = n || {};
  r = { ...r, ...i };
  for (const o in r) {
    const a = rf(r[o]);
    sf(e, o, a);
  }
}
const ie = (e) => !!(e && e.getVelocity);
function af(e) {
  return !!(ie(e) && e.add);
}
function Mi(e, t) {
  const n = e.getValue("willChange");
  if (af(n))
    return n.add(t);
  if (!n && Ve.WillChange) {
    const i = new Ve.WillChange("auto");
    e.addValue("willChange", i), i.add(t);
  }
}
function Kt(e) {
  return e.replace(/([A-Z])/g, (t) => `-${t.toLowerCase()}`);
}
const lf = "framerAppearId", Xa = "data-" + Kt(lf);
function Za(e) {
  return e.props[Xa];
}
const cf = typeof window < "u";
function uf({ protectedKeys: e, needsAnimating: t }, n) {
  const i = e.hasOwnProperty(n) && t[n] !== !0;
  return t[n] = !1, i;
}
function Qa(e, t, { delay: n = 0, transitionOverride: i, type: s } = {}) {
  let { transition: r, transitionEnd: o, ...a } = t;
  const l = e.getDefaultTransition();
  r = r ? qa(r, l) : l;
  const u = r?.reduceMotion, d = r?.skipAnimations;
  i && (r = i);
  const h = [], f = s && e.animationState && e.animationState.getState()[s], p = r?.path;
  p && p.animateVisualElement(e, a, r, n, h);
  for (const g in a) {
    const v = e.getValue(g, e.latestValues[g] ?? null), b = a[g];
    if (b === void 0 || f && uf(f, g))
      continue;
    const w = {
      delay: n,
      ...xs(r || {}, g)
    };
    d && (w.skipAnimations = !0);
    const T = v.get();
    if (T !== void 0 && !v.isAnimating() && !Array.isArray(b) && b === T && !w.velocity) {
      G.update(() => v.set(b));
      continue;
    }
    let y = !1;
    if (cf && window.MotionHandoffAnimation) {
      const C = Za(e);
      if (C) {
        const k = window.MotionHandoffAnimation(C, g, G);
        k !== null && (w.startTime = k, y = !0);
      }
    }
    Mi(e, g);
    const N = u ?? e.shouldReduceMotion;
    v.start(Vn(g, v, b, N && bs.has(g) ? { type: !1 } : w, e, y));
    const V = v.animation;
    V && h.push(V);
  }
  if (o) {
    const g = () => G.update(() => {
      o && of(e, o);
    });
    h.length ? Promise.all(h).then(g) : g();
  }
  return h;
}
function Ci(e, t, n = {}) {
  const i = Ze(e, t, n.type === "exit" ? e.presenceContext?.custom : void 0);
  let { transition: s = e.getDefaultTransition() || {} } = i || {};
  n.transitionOverride && (s = n.transitionOverride);
  const r = i ? () => Promise.all(Qa(e, i, n)) : () => Promise.resolve(), o = e.variantChildren && e.variantChildren.size ? (l = 0) => {
    const { delayChildren: u = 0, staggerChildren: d, staggerDirection: h } = s;
    return df(e, t, l, u, d, h, n);
  } : () => Promise.resolve(), { when: a } = s;
  if (a) {
    const [l, u] = a === "beforeChildren" ? [r, o] : [o, r];
    return l().then(() => u());
  } else
    return Promise.all([r(), o(n.delay)]);
}
function df(e, t, n = 0, i = 0, s = 0, r = 1, o) {
  const a = [];
  for (const l of e.variantChildren)
    l.notify("AnimationStart", t), a.push(Ci(l, t, {
      ...o,
      delay: n + (typeof i == "function" ? 0 : i) + Ha(e.variantChildren, l, i, s, r)
    }).then(() => l.notify("AnimationComplete", t)));
  return Promise.all(a);
}
function ff(e, t, n = {}) {
  e.notify("AnimationStart", t);
  let i;
  if (Array.isArray(t)) {
    const s = t.map((r) => Ci(e, r, n));
    i = Promise.all(s);
  } else if (typeof t == "string")
    i = Ci(e, t, n);
  else {
    const s = typeof t == "function" ? Ze(e, t, n.custom) : t;
    i = Promise.all(Qa(e, s, n));
  }
  return i.then(() => {
    e.notify("AnimationComplete", t);
  });
}
const hf = {
  test: (e) => e === "auto",
  parse: (e) => e
}, pf = (e) => (t) => t.test(e), mf = [gt, E, Ce, De, Vu, Du, hf], vr = (e) => mf.find(pf(e));
function gf(e) {
  return typeof e == "number" ? e === 0 : e !== null ? e === "none" || e === "0" || ns(e) : !0;
}
const yf = /* @__PURE__ */ new Set(["auto", "none", "0"]);
function xf(e, t, n) {
  let i = 0, s;
  for (; i < e.length && !s; ) {
    const r = e[i];
    typeof r == "string" && !yf.has(r) && Bu(r) && (s = e[i]), i++;
  }
  if (s && n)
    for (const r of t)
      e[r] !== s && (e[r] = ps(n, s));
}
class Ja extends ms {
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
      if (typeof h == "string" && (h = h.trim(), os(h))) {
        const f = Ya(h, n.current);
        f !== void 0 && (t[d] = f), d === t.length - 1 && (this.finalKeyframe = h);
      }
    }
    if (this.resolveNoneKeyframes(), !bs.has(i) || t.length !== 2)
      return;
    const [s, r] = t;
    if (typeof s == "number" && typeof r == "number")
      return;
    const o = vr(s), a = vr(r), l = tr(s), u = tr(r);
    if (l !== u && Ye[i]) {
      this.needsMeasurement = !0;
      return;
    }
    if (o !== a)
      if (dr(o) && dr(a))
        for (let d = 0; d < t.length; d++) {
          const h = t[d];
          typeof h == "string" && (t[d] = parseFloat(h));
        }
      else Ye[i] && (this.needsMeasurement = !0);
  }
  resolveNoneKeyframes() {
    const { unresolvedKeyframes: t, name: n } = this, i = [];
    for (let s = 0; s < t.length; s++)
      (t[s] === null || gf(t[s])) && i.push(s);
    i.length && xf(t, i, n);
  }
  measure() {
    const { element: t, name: n } = this;
    return Ye[n](window.getComputedStyle(t.current), () => t.measureViewportBox());
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
const ws = [
  "borderTopLeftRadius",
  "borderTopRightRadius",
  "borderBottomRightRadius",
  "borderBottomLeftRadius"
], ks = [];
function vf(e) {
  xe(typeof e.test == "function" && typeof e.read == "function", "Effects passed to animate.addEffect() need test() and read().", "effect-missing-test"), el(e), ks.unshift(e);
}
function el(e) {
  Qe(ks, e);
}
function bf(e) {
  return ks.find((t) => t.test(e));
}
function tl(e, t, n = {}, i) {
  const s = [], { velocity: r } = n, o = n.reduceMotion ?? i?.shouldReduceMotion;
  for (const l in t) {
    if (l === "transition" || l === "transitionEnd")
      continue;
    const u = t[l];
    if (u === void 0)
      continue;
    const d = e(l), h = d.get();
    if (h !== void 0 && !d.isAnimating() && !Array.isArray(u) && u === h && !r) {
      G.update(() => d.set(u));
      continue;
    }
    d.start(Vn(l, d, u, o && bs.has(l) ? { type: !1 } : n, i)), d.animation && s.push(d.animation);
  }
  const { transitionEnd: a } = t;
  if (a) {
    const l = () => G.update(() => {
      for (const u in a)
        e(u).set(a[u]);
    });
    s.length ? Promise.all(s).then(l) : l();
  }
  return s;
}
function nl(e, t, n, i, s) {
  return tl((r) => {
    let o = e.get(t, r);
    if (!o) {
      let a;
      if (!s) {
        const l = n[r];
        a = wf(l) ?? e.read(t, r, l), xe(a !== void 0, `"${r}" can't be read from the animated subject. Provide [from, to] keyframes.`, "effect-unreadable-value");
      }
      o = Le(a, { owner: s }), e(t, { [r]: o });
    }
    return o;
  }, n, i, s);
}
function wf(e) {
  const t = Array.isArray(e) ? e[0] : void 0;
  return t === null ? void 0 : t;
}
function dt(e) {
  return ts(e) && "offsetHeight" in e && !("ownerSVGElement" in e);
}
function yt(e) {
  return ts(e) && "ownerSVGElement" in e;
}
const Fe = (e, t) => t && typeof e == "number" ? t.transform(e) : e;
function Ts(e, t, n) {
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
class kf {
  /**
   * @param step - The frameloop step renders are scheduled in. Defaults
   * to `frame.render`. Effects that feed a render loop running in
   * `frame.render` (GPU scenes) should write in `frame.preRender`.
   */
  constructor(t = G.render) {
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
function Ss(e, { step: t, ...n } = {}) {
  const i = /* @__PURE__ */ new WeakMap();
  return Object.assign((r, o) => {
    const a = i.get(r) ?? new kf(t);
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
const Tf = {
  x: "translateX",
  y: "translateY",
  z: "translateZ",
  transformPerspective: "perspective"
}, br = {};
function Sf(e) {
  let t = "";
  const { transformKeys: n = [], transformValues: i = {} } = e;
  for (let r = 0; r < n.length; r++) {
    const o = n[r], a = i[o].get();
    if (a === void 0)
      continue;
    (typeof a == "number" ? a : parseFloat(a)) !== (o.startsWith("scale") ? 1 : 0) && (t += (t && " ") + (br[o] || (br[o] = (Tf[o] || o) + "(")) + Fe(a, yi[o]) + ")");
  }
  const s = e.get("pathRotation")?.get();
  return s && (t += (t && " ") + "rotate(" + Fe(s, yi.pathRotation) + ")"), t || "none";
}
const Nf = /* @__PURE__ */ new Set(["originX", "originY", "originZ"]), Hn = (e, t) => Fe(e.get(t)?.get(), Ee[t]), Ns = (e, t, n, i) => {
  let s, r;
  if (Oe.has(n)) {
    if (n !== "pathRotation") {
      const o = t.transformKeys ?? (t.transformKeys = []);
      (t.transformValues ?? (t.transformValues = {}))[n] = i, o.includes(n) || (o.push(n), o.sort((a, l) => je.indexOf(a) - je.indexOf(l)));
    }
    t.get("transform") || (!dt(e) && !t.get("transformBox") && Ns(e, t, "transformBox", new Mt("fill-box")), t.set("transform", new Mt("none"), () => {
      e.style.transform = Sf(t);
    })), r = t.get("transform");
  } else Nf.has(n) ? (t.get("transformOrigin") || t.set("transformOrigin", new Mt(""), () => {
    const o = Hn(t, "originX") ?? "50%", a = Hn(t, "originY") ?? "50%", l = Hn(t, "originZ") ?? 0;
    e.style.transformOrigin = `${o} ${a} ${l}`;
  }), r = t.get("transformOrigin")) : gs(n) ? s = () => {
    e.style.setProperty(n, i.get());
  } : s = () => {
    e.style[n] = Fe(i.get(), Ee[n]);
  };
  return t.set(n, i, s, r);
}, Af = (e) => dt(e) || yt(e), il = (e, t) => {
  if (Oe.has(t))
    return Ba(e, t);
  const n = getComputedStyle(e), i = gs(t) ? n.getPropertyValue(t) : n[t];
  return typeof i == "string" && i.trim() || 0;
}, Pf = /* @__PURE__ */ Ss(Ns, {
  test: Af,
  read: il
}), Mf = {
  x: "translateX",
  y: "translateY",
  z: "translateZ",
  transformPerspective: "perspective"
}, Cf = je.length;
function Ef(e, t, n) {
  let i = "", s = !0;
  for (let o = 0; o < Cf; o++) {
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
      const d = Fe(l, Ee[a]);
      if (!u) {
        s = !1;
        const h = Mf[a] || a;
        i += `${h}(${d}) `;
      }
      n && (t[a] = d);
    }
  }
  const r = e.pathRotation;
  return r && (s = !1, i += `rotate(${Fe(r, Ee.pathRotation)}) `), i = i.trim(), n ? i = n(t, s ? "" : i) : s && (i = "none"), i;
}
function As(e, t, n) {
  const { style: i, vars: s, transformOrigin: r } = e;
  let o = !1, a = !1;
  for (const l in t) {
    const u = t[l];
    if (Oe.has(l)) {
      o = !0;
      continue;
    } else if (va(l)) {
      s[l] = u;
      continue;
    } else {
      const d = Fe(u, Ee[l]);
      l.startsWith("origin") ? (a = !0, r[l] = d) : i[l] = d;
    }
  }
  if (t.transform || (o || n ? i.transform = Ef(t, e.transform, n) : i.transform && (i.transform = "none")), a) {
    const { originX: l = "50%", originY: u = "50%", originZ: d = 0 } = r;
    i.transformOrigin = `${l} ${u} ${d}`;
  }
}
const Df = {
  offset: "stroke-dashoffset",
  array: "stroke-dasharray"
}, Vf = {
  offset: "strokeDashoffset",
  array: "strokeDasharray"
};
function Rf(e, t, n = 1, i = 0, s = !0) {
  e.pathLength = 1;
  const r = s ? Df : Vf;
  e[r.offset] = `${-i}`, e[r.array] = `${t} ${n}`;
}
const Ps = [
  "transform",
  "opacity",
  "offsetDistance",
  "offsetPath",
  "offsetRotate",
  "offsetAnchor"
];
function sl(e, {
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
  for (const p of Ps)
    h[p] !== void 0 && (f[p] = h[p], delete h[p]);
  (f.transform || h.transformOrigin) && (f.transformOrigin = h.transformOrigin ?? "50% 50%", delete h.transformOrigin), f.transform && (f.transformBox = d?.transformBox ?? "fill-box", delete h.transformBox), t !== void 0 && (h.x = t), n !== void 0 && (h.y = n), i !== void 0 && (h.scale = i), s !== void 0 && Rf(h, s, r, o, !1);
}
function Lf(e, t) {
  if (!(t in e))
    return !1;
  const n = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e), t) || Object.getOwnPropertyDescriptor(e, t);
  return n && typeof n.set == "function";
}
const wr = (e, t, n, i, s = n) => {
  const r = Lf(e, s);
  !r && (s.startsWith("data") || s.startsWith("aria")) && (s = Kt(s));
  const o = Ee[n] || Ee[s], a = r ? () => {
    e[s] = Fe(i.get(), Ee[n]);
  } : () => {
    const l = Fe(i.get(), o);
    l == null ? e.removeAttribute(s) : e.setAttribute(s, String(l));
  };
  return t.set(n, i, a);
};
function Ff(e, t, n, i) {
  return G.render(() => e.setAttribute("pathLength", "1")), n === "pathOffset" ? t.set(n, i, () => {
    const s = i.get();
    e.setAttribute("stroke-dashoffset", `${-s}`);
  }) : (t.get("stroke-dasharray") || t.set("stroke-dasharray", new Mt("1 1"), () => {
    const s = t.get("pathLength")?.get() ?? 1, r = t.get("pathSpacing")?.get();
    e.setAttribute("stroke-dasharray", `${s} ${r ?? 1 - Number(s)}`);
  }), t.set(n, i, void 0, t.get("stroke-dasharray")));
}
const Of = (e, t, n, i) => n.startsWith("path") ? Ff(e, t, n, i) : n.startsWith("attr") ? wr(e, t, n, i, rl(n)) : (n in e.style ? Ns : wr)(e, t, n, i), If = (e, t) => Oe.has(t) ? Ee[t]?.default || 0 : Ps.includes(t) ? il(e, t) : (t = rl(t), e.getAttribute(Kt(t)) ?? e.getAttribute(t) ?? void 0), Bf = /* @__PURE__ */ Ss(Of, {
  test: yt,
  read: If
});
function rl(e) {
  return e.replace(/^attr([A-Z])/, (t, n) => n.toLowerCase());
}
function ol({ top: e, left: t, right: n, bottom: i }) {
  return {
    x: { min: t, max: n },
    y: { min: e, max: i }
  };
}
function $f({ x: e, y: t }) {
  return { top: t.min, right: e.max, bottom: t.max, left: e.min };
}
function jf(e, t) {
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
function qn(e) {
  return e === void 0 || e === 1;
}
function Ei({ scale: e, scaleX: t, scaleY: n }) {
  return !qn(e) || !qn(t) || !qn(n);
}
function Ge(e) {
  return Ei(e) || al(e) || e.z || e.rotate || e.rotateX || e.rotateY || e.skewX || e.skewY;
}
function al(e) {
  return kr(e.x) || kr(e.y);
}
function kr(e) {
  return e && e !== "0%";
}
function wn(e, t, n) {
  const i = e - n, s = t * i;
  return n + s;
}
function Tr(e, t, n, i, s) {
  return s !== void 0 && (e = wn(e, s, i)), wn(e, n, i) + t;
}
function Di(e, t = 0, n = 1, i, s) {
  e.min = Tr(e.min, t, n, i, s), e.max = Tr(e.max, t, n, i, s);
}
function ll(e, { x: t, y: n }) {
  Di(e.x, t.translate, t.scale, t.originPoint), Di(e.y, n.translate, n.scale, n.originPoint);
}
const Sr = 0.999999999999, Nr = 1.0000000000001;
function Uf(e, t, n, i = !1) {
  const s = n.length;
  if (!s)
    return;
  t.x = t.y = 1;
  let r, o;
  for (let a = 0; a < s; a++) {
    r = n[a], o = r.projectionDelta;
    const { visualElement: l } = r.options;
    l && l.props.style && l.props.style.display === "contents" || (i && r.options.layoutScroll && r.scroll && r !== r.root && (Me(e.x, -r.scroll.offset.x), Me(e.y, -r.scroll.offset.y)), o && (t.x *= o.x.scale, t.y *= o.y.scale, ll(e, o)), i && Ge(r.latestValues) && an(e, r.latestValues, r.layout?.layoutBox));
  }
  t.x < Nr && t.x > Sr && (t.x = 1), t.y < Nr && t.y > Sr && (t.y = 1);
}
function Me(e, t) {
  e.min += t, e.max += t;
}
function Ar(e, t, n, i, s = 0.5) {
  const r = q(e.min, e.max, s);
  Di(e, t, n, r, i);
}
function Pr(e, t) {
  return typeof e == "string" ? parseFloat(e) / 100 * (t.max - t.min) : e;
}
function an(e, t, n) {
  const i = n ?? e;
  Ar(e.x, Pr(t.x, i.x), t.scaleX, t.scale, t.originX), Ar(e.y, Pr(t.y, i.y), t.scaleY, t.scale, t.originY);
}
function Ms(e, t) {
  return ol(jf(e.getBoundingClientRect(), t));
}
function zf(e, t, n) {
  const i = Ms(e, n), { scroll: s } = t;
  return s && (Me(i.x, s.offset.x), Me(i.y, s.offset.y)), i;
}
const Wf = {}, _f = (e) => yt(e) ? Bf : Pf;
class Gf {
  constructor(t, n) {
    this.effect = t, this.current = n, this.KeyframeResolver = Ja;
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
    return Ms(this.current);
  }
  getProps() {
    return Wf;
  }
}
function Kf(e, t, n, i) {
  if (i)
    return tl((r) => i.getValue(r, null), t, n, i);
  const s = _f(e);
  return nl(s, e, t, n, new Gf(s, e));
}
const Hf = /* @__PURE__ */ Ss((e, t, n, i) => t.set(n, i, () => {
  e[n] = i.get();
}), {
  test: (e) => ts(e),
  read: (e, t) => {
    const n = e[t];
    return typeof n == "string" || typeof n == "number" ? n : void 0;
  }
}), { schedule: Cs } = /* @__PURE__ */ ya(queueMicrotask, !1), Te = {
  x: !1,
  y: !1
};
function cl() {
  return Te.x || Te.y;
}
function qf(e) {
  return e === "x" || e === "y" ? Te[e] ? null : (Te[e] = !0, () => {
    Te[e] = !1;
  }) : Te.x || Te.y ? null : (Te.x = Te.y = !0, () => {
    Te.x = Te.y = !1;
  });
}
function ul(e, t) {
  const n = Ts(e), i = new AbortController(), s = {
    passive: !0,
    ...t,
    signal: i.signal
  };
  return [n, s, () => i.abort()];
}
function Yf(e) {
  return !(e.pointerType === "touch" || cl());
}
function Xf(e, t, n = {}) {
  const [i, s, r] = ul(e, n);
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
    }, v = (b) => {
      if (!Yf(b))
        return;
      l = !1;
      const w = t(o, b);
      typeof w == "function" && (u = w, o.addEventListener("pointerleave", g, s));
    };
    o.addEventListener("pointerenter", v, s), o.addEventListener("pointerdown", p, s);
  }), r;
}
const dl = (e, t) => t ? e === t ? !0 : dl(e, t.parentElement) : !1, Es = (e) => e.pointerType === "mouse" ? typeof e.button != "number" || e.button <= 0 : e.isPrimary !== !1, Zf = /* @__PURE__ */ new Set([
  "BUTTON",
  "INPUT",
  "SELECT",
  "TEXTAREA",
  "A"
]);
function Qf(e) {
  return Zf.has(e.tagName) || e.isContentEditable === !0;
}
const Jf = /* @__PURE__ */ new Set(["INPUT", "SELECT", "TEXTAREA"]);
function eh(e) {
  return Jf.has(e.tagName) || e.isContentEditable === !0;
}
const ln = /* @__PURE__ */ new WeakSet();
function Mr(e) {
  return (t) => {
    t.key === "Enter" && e(t);
  };
}
function Yn(e, t) {
  e.dispatchEvent(new PointerEvent("pointer" + t, { isPrimary: !0, bubbles: !0 }));
}
const th = (e, t) => {
  const n = e.currentTarget;
  if (!n)
    return;
  const i = Mr(() => {
    if (ln.has(n))
      return;
    Yn(n, "down");
    const s = Mr(() => {
      Yn(n, "up");
    }), r = () => Yn(n, "cancel");
    n.addEventListener("keyup", s, t), n.addEventListener("blur", r, t);
  });
  n.addEventListener("keydown", i, t), n.addEventListener("blur", () => n.removeEventListener("keydown", i), t);
};
function Cr(e) {
  return Es(e) && !cl();
}
const Er = /* @__PURE__ */ new WeakSet();
function nh(e, t, n = {}) {
  const [i, s, r] = ul(e, n), o = (a) => {
    const l = a.currentTarget;
    if (!Cr(a) || Er.has(a))
      return;
    ln.add(l), n.stopPropagation && Er.add(a);
    const u = t(l, a), d = { ...s, capture: !0 }, h = (g, v) => {
      window.removeEventListener("pointerup", f, d), window.removeEventListener("pointercancel", p, d), ln.has(l) && ln.delete(l), Cr(g) && typeof u == "function" && u(g, { success: v });
    }, f = (g) => {
      h(g, l === window || l === document || n.useGlobalTarget || dl(l, g.target));
    }, p = (g) => {
      h(g, !1);
    };
    window.addEventListener("pointerup", f, d), window.addEventListener("pointercancel", p, d);
  };
  return i.forEach((a) => {
    (n.useGlobalTarget ? window : a).addEventListener("pointerdown", o, s), dt(a) && (a.addEventListener("focus", (u) => th(u, s)), !Qf(a) && !a.hasAttribute("tabindex") && (a.tabIndex = 0));
  }), r;
}
const cn = /* @__PURE__ */ new WeakMap();
let un;
const fl = (e, t, n) => (i, s) => s && s[0] ? s[0][e + "Size"] : yt(i) && "getBBox" in i ? i.getBBox()[t] : i[n], ih = /* @__PURE__ */ fl("inline", "width", "offsetWidth"), sh = /* @__PURE__ */ fl("block", "height", "offsetHeight");
function rh({ target: e, borderBoxSize: t }) {
  cn.get(e)?.forEach((n) => {
    n(e, {
      get width() {
        return ih(e, t);
      },
      get height() {
        return sh(e, t);
      }
    });
  });
}
function oh(e) {
  e.forEach(rh);
}
function ah() {
  typeof ResizeObserver > "u" || (un = new ResizeObserver(oh));
}
function lh(e, t) {
  un || ah();
  const n = Ts(e);
  return n.forEach((i) => {
    let s = cn.get(i);
    s || (s = /* @__PURE__ */ new Set(), cn.set(i, s)), s.add(t), un?.observe(i);
  }), () => {
    n.forEach((i) => {
      const s = cn.get(i);
      s?.delete(t), s?.size || un?.unobserve(i);
    });
  };
}
const dn = /* @__PURE__ */ new Set();
let at;
function ch() {
  at = () => {
    const e = {
      get width() {
        return window.innerWidth;
      },
      get height() {
        return window.innerHeight;
      }
    };
    dn.forEach((t) => t(e));
  }, window.addEventListener("resize", at);
}
function uh(e) {
  return dn.add(e), at || ch(), () => {
    dn.delete(e), !dn.size && typeof at == "function" && (window.removeEventListener("resize", at), at = void 0);
  };
}
function Dr(e, t) {
  return typeof e == "function" ? uh(e) : lh(e, t);
}
function dh(e) {
  return yt(e) && e.tagName === "svg";
}
function fh(...e) {
  const t = !Array.isArray(e[0]), n = t ? 0 : -1, i = e[0 + n], s = e[1 + n], r = e[2 + n], o = e[3 + n], a = Da(s, r, o);
  return t ? a(i) : a;
}
const Vr = () => ({
  translate: 0,
  scale: 1,
  origin: 0,
  originPoint: 0
}), lt = () => ({
  x: Vr(),
  y: Vr()
}), Rr = () => ({ min: 0, max: 0 }), ee = () => ({
  x: Rr(),
  y: Rr()
}), hl = /* @__PURE__ */ new WeakMap();
function Rn(e) {
  return e !== null && typeof e == "object" && typeof e.start == "function";
}
function It(e) {
  return typeof e == "string" || Array.isArray(e);
}
const Ds = [
  "animate",
  "whileInView",
  "whileFocus",
  "whileHover",
  "whileTap",
  "whileDrag",
  "exit"
], kn = ["initial", ...Ds];
function Ln(e) {
  if (Rn(e.animate))
    return !0;
  for (let t = 0; t < kn.length; t++)
    if (It(e[kn[t]]))
      return !0;
  return !1;
}
function pl(e) {
  return !!(Ln(e) || e.variants);
}
function hh(e, t, n) {
  for (const i in t) {
    const s = t[i], r = n[i];
    if (ie(s))
      e.addValue(i, s);
    else if (ie(r))
      e.addValue(i, Le(s, { owner: e }));
    else if (r !== s)
      if (e.hasValue(i)) {
        const o = e.getValue(i);
        o.liveStyle === !0 ? o.jump(s) : o.hasAnimated || o.set(s);
      } else {
        const o = e.getStaticValue(i);
        e.addValue(i, Le(o !== void 0 ? o : s, { owner: e }));
      }
  }
  for (const i in n)
    t[i] === void 0 && e.removeValue(i);
  return t;
}
const Tn = { current: null }, Vs = { current: !1 }, ph = typeof window < "u";
function ml() {
  if (Vs.current = !0, !!ph)
    if (window.matchMedia) {
      const e = window.matchMedia("(prefers-reduced-motion)"), t = () => Tn.current = e.matches;
      e.addEventListener("change", t), t();
    } else
      Tn.current = !1;
}
const Lr = [
  "AnimationStart",
  "AnimationComplete",
  "Update",
  "BeforeLayoutMeasure",
  "LayoutMeasure",
  "LayoutAnimationStart",
  "LayoutAnimationComplete"
];
let Sn = {};
function gl(e) {
  Sn = e;
}
function mh() {
  return Sn;
}
class gh {
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
    this.current = null, this.children = /* @__PURE__ */ new Set(), this.isVariantNode = !1, this.isControllingVariants = !1, this.shouldReduceMotion = null, this.shouldSkipAnimations = !1, this.values = /* @__PURE__ */ new Map(), this.KeyframeResolver = ms, this.features = {}, this.valueSubscriptions = /* @__PURE__ */ new Map(), this.prevMotionValues = {}, this.hasBeenMounted = !1, this.events = {}, this.propEventSubscriptions = {}, this.notifyUpdate = () => this.notify("Update", this.latestValues), this.render = () => {
      this.current && (this.triggerBuild(), this.renderInstance(this.current, this.renderState, this.props.style, this.projection));
    }, this.renderScheduledAt = 0, this.scheduleRender = () => {
      const p = ae.now();
      this.renderScheduledAt < p && (this.renderScheduledAt = p, G.render(this.render, !1, !0));
    };
    const { latestValues: u, renderState: d } = a;
    this.latestValues = u, this.baseTarget = { ...u }, this.initialValues = n.initial ? { ...u } : {}, this.renderState = d, this.parent = t, this.props = n, this.presenceContext = i, this.depth = t ? t.depth + 1 : 0, this.reducedMotionConfig = s, this.skipAnimationsConfig = r, this.options = l, this.blockInitialAnimation = !!o, this.isControllingVariants = Ln(n), this.isVariantNode = pl(n), this.isVariantNode && (this.variantChildren = /* @__PURE__ */ new Set()), this.manuallyAnimateOnMount = !!(t && t.current);
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
    this.current = t, hl.set(t, this), this.projection && !this.projection.instance && this.projection.mount(t), this.parent && this.isVariantNode && !this.isControllingVariants && (this.removeFromVariantTree = this.parent.addVariantChild(this)), this.values.forEach((n, i) => this.bindToMotionValue(i, n)), this.reducedMotionConfig === "never" ? this.shouldReduceMotion = !1 : this.reducedMotionConfig === "always" ? this.shouldReduceMotion = !0 : (Vs.current || ml(), this.shouldReduceMotion = Tn.current), process.env.NODE_ENV !== "production" && En(this.shouldReduceMotion !== !0, "You have Reduced Motion enabled on your device. Animations may not appear as expected.", "reduced-motion-disabled"), this.shouldSkipAnimations = this.skipAnimationsConfig ?? !1, this.parent?.addChild(this), this.update(this.props, this.presenceContext), this.hasBeenMounted = !0;
  }
  unmount() {
    this.projection && this.projection.unmount(), Re(this.notifyUpdate), Re(this.render), this.valueSubscriptions.forEach((t) => t()), this.valueSubscriptions.clear(), this.removeFromVariantTree && this.removeFromVariantTree(), this.parent?.removeChild(this);
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
      const { factory: o, keyframes: a, times: l, ease: u, duration: d } = n.accelerate, h = new Ga({
        element: this.current,
        name: t,
        keyframes: a,
        times: l,
        ease: u,
        duration: /* @__PURE__ */ pe(d)
      }), f = o(h);
      this.valueSubscriptions.set(t, () => {
        f(), h.cancel();
      });
      return;
    }
    const i = Oe.has(t);
    i && this.onBindTransform && this.onBindTransform();
    const s = n.on("change", (o) => {
      this.latestValues[t] = o, this.props.onUpdate && G.preRender(this.notifyUpdate), i && this.projection && (this.projection.isTransformDirty = !0), this.scheduleRender();
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
    for (t in Sn) {
      const n = Sn[t];
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
    for (let i = 0; i < Lr.length; i++) {
      const s = Lr[i];
      this.propEventSubscriptions[s] && (this.propEventSubscriptions[s](), delete this.propEventSubscriptions[s]);
      const r = "on" + s, o = t[r];
      o && (this.propEventSubscriptions[s] = this.on(s, o));
    }
    this.prevMotionValues = hh(this, this.scrapeMotionValuesFromProps(t, this.prevProps || {}, this), this.prevMotionValues), this.handleChildMotionValue && this.handleChildMotionValue();
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
    return i === void 0 && n !== void 0 && (i = Le(n === null ? void 0 : n, { owner: this }), this.addValue(t, i)), i;
  }
  /**
   * If we're trying to animate to a previously unencountered value,
   * we need to check for it in our state and as a last resort read it
   * directly from the instance (which might have performance implications).
   */
  readValue(t, n) {
    let i = this.latestValues[t] !== void 0 || !this.current ? this.latestValues[t] : this.getBaseTargetFromProps(this.props, t) ?? this.readValueFromInstance(this.current, t, this.options);
    return i != null && (typeof i == "string" && (es(i) || ns(i)) ? i = parseFloat(i) : (
      /**
       * If the value as read isn't animatable (e.g. "none") but
       * the target is, derive an animatable none from the target.
       * A value is animatable if it's a number or contains a
       * number or color, which is cheaper to check than trying
       * every value type in turn.
       */
      typeof i != "number" && !ye.test(i) && ye.test(n) && (i = ps(t, n))
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
      const r = vs(this.props, n, this.presenceContext?.custom);
      r && (i = r[t]);
    }
    if (n && i !== void 0)
      return i;
    const s = this.getBaseTargetFromProps(this.props, t);
    return s !== void 0 && !ie(s) ? s : this.initialValues[t] !== void 0 && i === void 0 ? void 0 : this.baseTarget[t];
  }
  on(t, n) {
    return this.events[t] || (this.events[t] = new yn()), this.events[t].add(n);
  }
  notify(t, ...n) {
    this.events[t] && this.events[t].notify(...n);
  }
  scheduleRenderMicrotask() {
    Cs.render(this.render);
  }
}
class yl extends gh {
  constructor() {
    super(...arguments), this.KeyframeResolver = Ja;
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
function xl(e, { style: t, vars: n }, i, s) {
  const r = e.style;
  let o;
  for (o in t)
    r[o] = t[o];
  s?.applyProjectionStyles(r, i);
  for (o in n)
    r.setProperty(o, n[o]);
}
function Fr(e, t) {
  return t.max === t.min ? 0 : e / (t.max - t.min) * 100;
}
const bt = {
  correct: (e, t) => {
    if (!t.target)
      return e;
    if (typeof e == "string")
      if (E.test(e))
        e = parseFloat(e);
      else
        return e;
    const n = Fr(e, t.target.x), i = Fr(e, t.target.y);
    return `${n}% ${i}%`;
  }
}, yh = {
  correct: (e, { treeScale: t, projectionDelta: n }) => {
    const i = e, s = ye.parse(e);
    if (s.length > 5)
      return i;
    const r = ye.createTransformer(e), o = typeof s[0] != "number" ? 1 : 0, a = n.x.scale * t.x, l = n.y.scale * t.y;
    s[0 + o] /= a, s[1 + o] /= l;
    const u = q(a, l, 0.5);
    return typeof s[2 + o] == "number" && (s[2 + o] /= u), typeof s[3 + o] == "number" && (s[3 + o] /= u), r(s);
  }
}, Vi = {
  borderRadius: {
    ...bt,
    applyTo: [...ws]
  },
  borderTopLeftRadius: bt,
  borderTopRightRadius: bt,
  borderBottomLeftRadius: bt,
  borderBottomRightRadius: bt,
  boxShadow: yh
};
function vl(e, { layout: t, layoutId: n }) {
  return Oe.has(e) || e.startsWith("origin") || (t || n !== void 0) && (!!Vi[e] || e === "opacity");
}
function Rs(e, t, n) {
  const i = e.style, s = t?.style, r = {};
  if (!i)
    return r;
  for (const o in i)
    (ie(i[o]) || s && ie(s[o]) || vl(o, e) || n?.getValue(o)?.liveStyle !== void 0) && (r[o] = i[o]);
  return r;
}
function xh(e) {
  return window.getComputedStyle(e);
}
class vh extends yl {
  constructor() {
    super(...arguments), this.type = "html", this.renderInstance = xl;
  }
  mount(t) {
    xe(!!t.style, "motion.create() components must forward their ref to a HTML or SVG element", "custom-component-ref"), super.mount(t);
  }
  readValueFromInstance(t, n) {
    if (Oe.has(n))
      return this.projection?.isProjecting ? bi(n) : Ba(t, n);
    {
      const i = xh(t), s = (va(n) ? i.getPropertyValue(n) : i[n]) || 0;
      return typeof s == "string" ? s.trim() : s;
    }
  }
  measureInstanceViewportBox(t, { transformPagePoint: n }) {
    return Ms(t, n);
  }
  build(t, n, i) {
    As(t, n, i.transformTemplate);
  }
  scrapeMotionValuesFromProps(t, n, i) {
    return Rs(t, n, i);
  }
}
const bl = /* @__PURE__ */ new Set([
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
]), wl = (e) => typeof e == "string" && e.toLowerCase() === "svg";
function bh(e, t, n, i) {
  xl(e, t, void 0, i);
  for (const s in t.attrs)
    e.setAttribute(bl.has(s) ? s : Kt(s), t.attrs[s]);
}
function kl(e, t, n) {
  const i = Rs(e, t, n);
  for (const s in e)
    if (ie(e[s]) || ie(t[s])) {
      const r = je.indexOf(s) !== -1 ? "attr" + s.charAt(0).toUpperCase() + s.substring(1) : s;
      i[r] = e[s];
    }
  return i;
}
class wh extends yl {
  constructor() {
    super(...arguments), this.type = "svg", this.isSVGTag = !1, this.measureInstanceViewportBox = ee;
  }
  getBaseTargetFromProps(t, n) {
    return t[n];
  }
  readValueFromInstance(t, n) {
    if (Oe.has(n)) {
      const i = Ia(n);
      return i && i.default || 0;
    }
    if (Ps.includes(n)) {
      const s = getComputedStyle(t)[n];
      if (typeof s == "string" && s)
        return s.trim();
    }
    return n = bl.has(n) ? n : Kt(n), t.getAttribute(n);
  }
  scrapeMotionValuesFromProps(t, n, i) {
    return kl(t, n, i);
  }
  build(t, n, i) {
    sl(t, n, this.isSVGTag, i.transformTemplate, i.style);
  }
  renderInstance(t, n, i, s) {
    bh(t, n, i, s);
  }
  mount(t) {
    this.isSVGTag = wl(t.tagName), super.mount(t);
  }
}
const kh = kn.length;
function Tl(e) {
  if (!e)
    return;
  if (!e.isControllingVariants) {
    const n = e.parent ? Tl(e.parent) || {} : {};
    return e.props.initial !== void 0 && (n.initial = e.props.initial), n;
  }
  const t = {};
  for (let n = 0; n < kh; n++) {
    const i = kn[n], s = e.props[i];
    (It(s) || s === !1) && (t[i] = s);
  }
  return t;
}
function Sl(e, t) {
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
const Th = [...Ds].reverse(), Sh = Ds.length;
function Nh(e) {
  return (t) => Promise.all(t.map(({ animation: n, options: i }) => ff(e, n, i)));
}
function Ah(e) {
  let t = Nh(e), n = Or(), i = !0, s = !1;
  const r = (u) => (d, h) => {
    const f = Ze(e, h, u === "exit" ? e.presenceContext?.custom : void 0);
    if (f) {
      const { transition: p, transitionEnd: g, ...v } = f;
      d = { ...d, ...v, ...g };
    }
    return d;
  };
  function o(u) {
    t = u(e);
  }
  function a(u) {
    const { props: d } = e, h = Tl(e.parent) || {}, f = [], p = /* @__PURE__ */ new Set();
    let g = {}, v = 1 / 0;
    for (let w = 0; w < Sh; w++) {
      const T = Th[w], y = n[T], N = d[T] !== void 0 ? d[T] : h[T], V = It(N), C = T === u ? y.isActive : null;
      C === !1 && (v = w);
      let k = N === h[T] && N !== d[T] && V;
      if (k && (i || s) && e.manuallyAnimateOnMount && (k = !1), y.protectedKeys = { ...g }, // If it isn't active and hasn't *just* been set as inactive
      !y.isActive && C === null || // If we didn't and don't have any defined prop for this animation type
      !N && !y.prevProp || // Or if the prop doesn't define an animation
      Rn(N) || typeof N == "boolean")
        continue;
      if (T === "exit" && y.isActive && C !== !0) {
        y.prevResolvedValues && (g = {
          ...g,
          ...y.prevResolvedValues
        });
        continue;
      }
      const m = Ph(y.prevProp, N);
      let S = m || // If we're making this variant active, we want to always make it active
      T === u && y.isActive && !k && V || // If we removed a higher-priority variant (i is in reverse order)
      w > v && V, A = !1;
      const L = Array.isArray(N) ? N : [N];
      let j = L.reduce(r(T), {});
      C === !1 && (j = {});
      const { prevResolvedValues: I = {} } = y, M = {
        ...I,
        ...j
      }, se = (U) => {
        S = !0, p.has(U) && (A = !0, p.delete(U)), y.needsAnimating[U] = !0;
        const H = e.getValue(U);
        H && (H.liveStyle = !1);
      };
      for (const U in M) {
        const H = j[U], K = I[U];
        if (g.hasOwnProperty(U))
          continue;
        let oe = !1;
        Pi(H) && Pi(K) ? oe = !Sl(H, K) || m : oe = H !== K, oe ? H != null ? se(U) : p.add(U) : H !== void 0 && p.has(U) ? se(U) : y.protectedKeys[U] = !0;
      }
      y.prevProp = N, y.prevResolvedValues = j, y.isActive && (g = { ...g, ...j }), (i || s) && e.blockInitialAnimation && (S = !1);
      const ve = k && m;
      S && (!ve || A) && f.push(...L.map((U) => {
        const H = { type: T };
        if (typeof U == "string" && (i || s) && !ve && e.manuallyAnimateOnMount && e.parent) {
          const { parent: K } = e, oe = Ze(K, U);
          if (K.enteringChildren && oe) {
            const { delayChildren: D } = oe.transition || {};
            H.delay = Ha(K.enteringChildren, e, D);
          }
        }
        return {
          animation: U,
          options: H
        };
      }));
    }
    if (p.size) {
      const w = {};
      if (typeof d.initial != "boolean") {
        const T = Ze(e, Array.isArray(d.initial) ? d.initial[0] : d.initial);
        T && T.transition && (w.transition = T.transition);
      }
      p.forEach((T) => {
        const y = e.getBaseTarget(T), N = e.getValue(T);
        N && (N.liveStyle = !0), w[T] = y ?? null;
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
      n = Or(), s = !0;
    }
  };
}
function Ph(e, t) {
  return typeof t == "string" ? t !== e : Array.isArray(t) ? !Sl(t, e) : !1;
}
function _e(e = !1) {
  return {
    isActive: e,
    protectedKeys: {},
    needsAnimating: {},
    prevResolvedValues: {}
  };
}
function Or() {
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
function Ri(e, t) {
  e.min = t.min, e.max = t.max;
}
function ke(e, t) {
  Ri(e.x, t.x), Ri(e.y, t.y);
}
function Ir(e, t) {
  e.translate = t.translate, e.scale = t.scale, e.originPoint = t.originPoint, e.origin = t.origin;
}
const Nl = 1e-4, Mh = 1 - Nl, Ch = 1 + Nl, Al = 0.01, Eh = 0 - Al, Dh = 0 + Al;
function ue(e) {
  return e.max - e.min;
}
function Vh(e, t, n) {
  return Math.abs(e - t) <= n;
}
function Br(e, t, n, i = 0.5) {
  e.origin = i, e.originPoint = q(t.min, t.max, e.origin), e.scale = ue(n) / ue(t), e.translate = q(n.min, n.max, e.origin) - e.originPoint, (e.scale >= Mh && e.scale <= Ch || isNaN(e.scale)) && (e.scale = 1), (e.translate >= Eh && e.translate <= Dh || isNaN(e.translate)) && (e.translate = 0);
}
function Ct(e, t, n, i) {
  Br(e.x, t.x, n.x, i ? i.originX : void 0), Br(e.y, t.y, n.y, i ? i.originY : void 0);
}
function $r(e, t, n, i = 0) {
  const s = i ? q(n.min, n.max, i) : n.min;
  e.min = s + t.min, e.max = e.min + ue(t);
}
function Rh(e, t, n, i) {
  $r(e.x, t.x, n.x, i?.x), $r(e.y, t.y, n.y, i?.y);
}
function jr(e, t, n, i = 0) {
  const s = i ? q(n.min, n.max, i) : n.min;
  e.min = t.min - s, e.max = e.min + ue(t);
}
function Nn(e, t, n, i) {
  jr(e.x, t.x, n.x, i?.x), jr(e.y, t.y, n.y, i?.y);
}
function Ur(e, t, n, i, s) {
  return e -= t, e = wn(e, 1 / n, i), s !== void 0 && (e = wn(e, 1 / s, i)), e;
}
function Lh(e, t = 0, n = 1, i = 0.5, s, r = e, o = e) {
  if (Ce.test(t) && (t = parseFloat(t), t = q(o.min, o.max, t / 100) - o.min), typeof t != "number")
    return;
  let a = q(r.min, r.max, i);
  e === r && (a -= t), e.min = Ur(e.min, t, n, a, s), e.max = Ur(e.max, t, n, a, s);
}
function zr(e, t, [n, i, s], r, o) {
  Lh(e, t[n], t[i], t[s], t.scale, r, o);
}
const Fh = ["x", "scaleX", "originX"], Oh = ["y", "scaleY", "originY"];
function Wr(e, t, n, i) {
  zr(e.x, t, Fh, n ? n.x : void 0, i ? i.x : void 0), zr(e.y, t, Oh, n ? n.y : void 0, i ? i.y : void 0);
}
function _r(e) {
  return e.translate === 0 && e.scale === 1;
}
function Pl(e) {
  return _r(e.x) && _r(e.y);
}
function Gr(e, t) {
  return e.min === t.min && e.max === t.max;
}
function Ih(e, t) {
  return Gr(e.x, t.x) && Gr(e.y, t.y);
}
function Kr(e, t) {
  return Math.round(e.min) === Math.round(t.min) && Math.round(e.max) === Math.round(t.max);
}
function Ml(e, t) {
  return Kr(e.x, t.x) && Kr(e.y, t.y);
}
function Hr(e) {
  return ue(e.x) / ue(e.y);
}
function qr(e, t) {
  return e.translate === t.translate && e.scale === t.scale && e.originPoint === t.originPoint;
}
function Pe(e) {
  return [e("x"), e("y")];
}
function Bh(e, t, n) {
  let i = "";
  const s = e.x.translate / t.x, r = e.y.translate / t.y, o = n?.z || 0;
  if ((s || r || o) && (i = `translate3d(${s}px, ${r}px, ${o}px) `), (t.x !== 1 || t.y !== 1) && (i += `scale(${1 / t.x}, ${1 / t.y}) `), n) {
    const { transformPerspective: u, rotate: d, pathRotation: h, rotateX: f, rotateY: p, skewX: g, skewY: v } = n;
    u && (i = `perspective(${u}px) ${i}`), d && (i += `rotate(${d}deg) `), h && (i += `rotate(${h}deg) `), f && (i += `rotateX(${f}deg) `), p && (i += `rotateY(${p}deg) `), g && (i += `skewX(${g}deg) `), v && (i += `skewY(${v}deg) `);
  }
  const a = e.x.scale * t.x, l = e.y.scale * t.y;
  return (a !== 1 || l !== 1) && (i += `scale(${a}, ${l})`), i || "none";
}
const $h = ws.length, Yr = (e) => typeof e == "string" ? parseFloat(e) : e, Xr = (e) => typeof e == "number" || E.test(e);
function jh(e, t, n, i, s, r) {
  s ? (e.opacity = q(0, n.opacity ?? 1, Uh(i)), e.opacityExit = q(t.opacity ?? 1, 0, zh(i))) : r && (e.opacity = q(t.opacity ?? 1, n.opacity ?? 1, i));
  for (let o = 0; o < $h; o++) {
    const a = ws[o];
    let l = Zr(t, a), u = Zr(n, a);
    if (l === void 0 && u === void 0)
      continue;
    l || (l = 0), u || (u = 0), l === 0 || u === 0 || Xr(l) === Xr(u) ? (e[a] = Math.max(q(Yr(l), Yr(u), i), 0), (Ce.test(u) || Ce.test(l)) && (e[a] += "%")) : e[a] = u;
  }
  (t.rotate || n.rotate) && (e.rotate = q(t.rotate || 0, n.rotate || 0, i));
}
function Zr(e, t) {
  return e[t] !== void 0 ? e[t] : e.borderRadius;
}
const Uh = /* @__PURE__ */ Cl(0, 0.5, da), zh = /* @__PURE__ */ Cl(0.5, 0.95, Se);
function Cl(e, t, n) {
  return (i) => i < e ? 0 : i > t ? 1 : n(/* @__PURE__ */ ft(e, t, i));
}
function El(e, t, n) {
  const i = ie(e) ? e : Le(e);
  return i.start(Vn("", i, t, n)), i.animation;
}
function Bt(e, t, n, i = { passive: !0 }) {
  return e.addEventListener(t, n, i), () => e.removeEventListener(t, n, i);
}
const Wh = (e, t) => e.depth - t.depth;
class _h {
  constructor() {
    this.children = [], this.isDirty = !1;
  }
  add(t) {
    Ji(this.children, t), this.isDirty = !0;
  }
  remove(t) {
    Qe(this.children, t), this.isDirty = !0;
  }
  forEach(t) {
    this.isDirty && this.children.sort(Wh), this.isDirty = !1, this.children.forEach(t);
  }
}
function Gh(e, t) {
  const n = ae.now(), i = ({ timestamp: s }) => {
    const r = s - n;
    r >= t && (Re(i), e(r - t));
  };
  return G.setup(i, !0), () => Re(i);
}
function fn(e) {
  return ie(e) ? e.get() : e;
}
class Kh {
  constructor() {
    this.members = [];
  }
  add(t) {
    Ji(this.members, t);
    for (let n = this.members.length - 1; n >= 0; n--) {
      const i = this.members[n];
      if (i === t || i === this.lead || i === this.prevLead)
        continue;
      const s = i.instance;
      (!s || s.isConnected === !1) && !i.snapshot && (Qe(this.members, i), i.unmount());
    }
    t.scheduleRender();
  }
  remove(t) {
    if (Qe(this.members, t), t === this.prevLead && (this.prevLead = void 0), t === this.lead) {
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
const hn = {
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
}, Xn = ["", "X", "Y", "Z"], Hh = 1e3;
let qh = 0;
function Zn(e, t, n, i) {
  const { latestValues: s } = t;
  s[e] && (n[e] = s[e], t.setStaticValue(e, 0), i && (i[e] = 0));
}
function Dl(e) {
  if (e.hasCheckedOptimisedAppear = !0, e.root === e)
    return;
  const { visualElement: t } = e.options;
  if (!t)
    return;
  const n = Za(t);
  if (window.MotionHasOptimisedAnimation(n, "transform")) {
    const { layout: s, layoutId: r } = e.options;
    window.MotionCancelOptimisedAnimation(n, "transform", G, !(s || r));
  }
  const { parent: i } = e;
  i && !i.hasCheckedOptimisedAppear && Dl(i);
}
function Vl({ attachResizeListener: e, defaultParent: t, measureScroll: n, checkIsScrollRoot: i, resetTransform: s }) {
  return class {
    constructor(o = {}, a = t?.()) {
      this.id = qh++, this.animationId = 0, this.animationCommitId = 0, this.children = /* @__PURE__ */ new Set(), this.options = {}, this.isTreeAnimating = !1, this.isAnimationBlocked = !1, this.isLayoutDirty = !1, this.isProjectionDirty = !1, this.isSharedProjectionDirty = !1, this.isTransformDirty = !1, this.updateManuallyBlocked = !1, this.updateBlockedByResize = !1, this.isUpdating = !1, this.isSVG = !1, this.needsReset = !1, this.shouldResetTransform = !1, this.hasCheckedOptimisedAppear = !1, this.treeScale = { x: 1, y: 1 }, this.eventHandlers = /* @__PURE__ */ new Map(), this.hasTreeAnimated = !1, this.layoutVersion = 0, this.updateScheduled = !1, this.scheduleUpdate = () => this.update(), this.projectionUpdateScheduled = !1, this.checkUpdateFailed = () => {
        this.isUpdating && (this.isUpdating = !1, this.clearAllSnapshots());
      }, this.updateProjection = () => {
        this.projectionUpdateScheduled = !1, this.nodes.forEach(Zh), this.nodes.forEach(ip), this.nodes.forEach(sp), this.nodes.forEach(Qh);
      }, this.resolvedRelativeTargetAt = 0, this.linkedParentVersion = 0, this.hasProjected = !1, this.isVisible = !0, this.animationProgress = 0, this.sharedNodes = /* @__PURE__ */ new Map(), this.latestValues = o, this.root = a ? a.root || a : this, this.path = a ? [...a.path, a] : [], this.parent = a, this.depth = a ? a.depth + 1 : 0;
      for (let l = 0; l < this.path.length; l++)
        this.path[l].shouldResetTransform = !0;
      this.root === this && (this.nodes = new _h());
    }
    addEventListener(o, a) {
      return this.eventHandlers.has(o) || this.eventHandlers.set(o, new yn()), this.eventHandlers.get(o).add(a);
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
      this.isSVG = yt(o) && !dh(o), this.instance = o;
      const { layoutId: a, layout: l, visualElement: u } = this.options;
      if (u && !u.current && u.mount(o), this.root.nodes.add(this), this.parent && this.parent.children.add(this), this.root.hasTreeAnimated && (l || a) && (this.isLayoutDirty = !0), e) {
        let d, h = 0;
        const f = () => this.root.updateBlockedByResize = !1;
        G.read(() => {
          h = window.innerWidth;
        }), e(o, () => {
          const p = window.innerWidth;
          p !== h && (h = p, this.root.updateBlockedByResize = !0, d && d(), d = Gh(f, 250), hn.hasAnimatedSinceResize && (hn.hasAnimatedSinceResize = !1, this.nodes.forEach(eo)));
        });
      }
      a && this.root.registerSharedNode(a, this), this.options.animate !== !1 && u && (a || l) && this.addEventListener("didUpdate", ({ delta: d, hasLayoutChanged: h, hasRelativeLayoutChanged: f, layout: p }) => {
        if (this.isTreeAnimationBlocked()) {
          this.target = void 0, this.relativeTarget = void 0;
          return;
        }
        const g = this.options.transition || u.getDefaultTransition() || cp, { onLayoutAnimationStart: v, onLayoutAnimationComplete: b } = u.getProps(), w = !this.targetLayout || !Ml(this.targetLayout, p), T = !h && f;
        if (this.options.layoutRoot || this.resumeFrom || T || h && (w || !this.currentAnimation)) {
          this.resumeFrom && (this.resumingFrom = this.resumeFrom, this.resumingFrom.resumingFrom = void 0);
          const y = {
            ...xs(g, "layout"),
            onPlay: v,
            onComplete: b
          };
          (u.shouldReduceMotion || this.options.layoutRoot) && (y.delay = 0, y.type = !1), this.startAnimation(y), this.setAnimationOrigin(d, T, y.path);
        } else
          h || eo(this), this.isLead() && this.options.onExitComplete && this.options.onExitComplete();
        this.targetLayout = p;
      });
    }
    unmount() {
      this.options.layoutId && this.willUpdate(), this.root.nodes.remove(this);
      const o = this.getStack();
      o && o.remove(this), this.parent && this.parent.children.delete(this), this.instance = void 0, this.eventHandlers.clear(), Re(this.updateProjection);
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
      this.isUpdateBlocked() || (this.isUpdating = !0, this.nodes && this.nodes.forEach(rp), this.animationId++);
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
      if (window.MotionCancelOptimisedAnimation && !this.hasCheckedOptimisedAppear && Dl(this), !this.root.isUpdating && this.root.startUpdate(), this.isLayoutDirty)
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
        this.unblockUpdate(), this.updateBlockedByResize = !1, this.clearAllSnapshots(), l && this.nodes.forEach(ep), this.nodes.forEach(Qr);
        return;
      }
      if (this.animationId <= this.animationCommitId) {
        this.nodes.forEach(Jr);
        return;
      }
      this.animationCommitId = this.animationId, this.isUpdating ? (this.isUpdating = !1, this.nodes.forEach(tp), this.nodes.forEach(np), this.nodes.forEach(Yh), this.nodes.forEach(Xh)) : this.nodes.forEach(Jr), this.clearAllSnapshots();
      const a = ae.now();
      te.delta = Ne(0, 1e3 / 60, a - te.timestamp), te.timestamp = a, te.isProcessing = !0, Un.update.process(te), Un.preRender.process(te), Un.render.process(te), te.isProcessing = !1;
    }
    didUpdate() {
      this.updateScheduled || (this.updateScheduled = !0, Cs.read(this.scheduleUpdate));
    }
    clearAllSnapshots() {
      this.nodes.forEach(Jh), this.sharedNodes.forEach(op);
    }
    scheduleUpdateProjection() {
      this.projectionUpdateScheduled || (this.projectionUpdateScheduled = !0, G.preRender(this.updateProjection, !1, !0));
    }
    scheduleCheckAfterUnmount() {
      G.postRender(() => {
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
      const o = this.isLayoutDirty || this.shouldResetTransform || this.options.alwaysMeasureLayout, a = this.projectionDelta && !Pl(this.projectionDelta), l = this.getTransformTemplate(), u = l ? l(this.latestValues, "") : void 0, d = u !== this.prevTransformTemplateValue;
      o && this.instance && (a || Ge(this.latestValues) || d) && (s(this.instance, u), this.shouldResetTransform = !1, this.scheduleRender());
    }
    measure(o = !0) {
      const a = this.measurePageBox();
      let l = this.removeElementScroll(a);
      return o && (l = this.removeTransform(l)), up(l), {
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
      if (!(this.scroll?.wasRoot || this.path.some(dp))) {
        const { scroll: u } = this.root;
        u && (Me(a.x, u.offset.x), Me(a.y, u.offset.y));
      }
      return a;
    }
    removeElementScroll(o) {
      const a = ee();
      if (ke(a, o), this.scroll?.wasRoot)
        return a;
      for (let l = 0; l < this.path.length; l++) {
        const u = this.path[l], { scroll: d, options: h } = u;
        u !== this.root && d && h.layoutScroll && (d.wasRoot && ke(a, o), Me(a.x, d.offset.x), Me(a.y, d.offset.y));
      }
      return a;
    }
    applyTransform(o, a = !1, l) {
      const u = l || ee();
      ke(u, o);
      for (let d = 0; d < this.path.length; d++) {
        const h = this.path[d];
        !a && h.options.layoutScroll && h.scroll && h !== h.root && (Me(u.x, -h.scroll.offset.x), Me(u.y, -h.scroll.offset.y)), Ge(h.latestValues) && an(u, h.latestValues, h.layout?.layoutBox);
      }
      return Ge(this.latestValues) && an(u, this.latestValues, this.layout?.layoutBox), u;
    }
    removeTransform(o) {
      const a = ee();
      ke(a, o);
      for (let l = 0; l < this.path.length; l++) {
        const u = this.path[l];
        if (!Ge(u.latestValues))
          continue;
        let d;
        u.instance && (Ei(u.latestValues) && u.updateSnapshot(), d = ee(), ke(d, u.measurePageBox())), Wr(a, u.latestValues, u.snapshot?.layoutBox, d);
      }
      return Ge(this.latestValues) && Wr(a, this.latestValues), a;
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
      f && this.linkedParentVersion !== f.layoutVersion && !f.options.layoutRoot && this.removeRelativeTarget(), !this.targetDelta && !this.relativeTarget && (this.options.layoutAnchor !== !1 && f && f.layout ? this.createRelativeTarget(f, this.layout.layoutBox, f.layout.layoutBox) : this.removeRelativeTarget()), !(!this.relativeTarget && !this.targetDelta) && (this.target || (this.target = ee(), this.targetWithTransforms = ee()), this.relativeTarget && this.relativeTargetOrigin && this.relativeParent && this.relativeParent.target ? (this.forceRelativeParentToResolveTarget(), Rh(this.target, this.relativeTarget, this.relativeParent.target, this.options.layoutAnchor || void 0)) : this.targetDelta ? (this.resumingFrom ? this.applyTransform(this.layout.layoutBox, !1, this.target) : ke(this.target, this.layout.layoutBox), ll(this.target, this.targetDelta)) : ke(this.target, this.layout.layoutBox), this.attemptToResolveRelativeTarget && (this.attemptToResolveRelativeTarget = !1, this.options.layoutAnchor !== !1 && f && !!f.resumingFrom == !!this.resumingFrom && !f.options.layoutScroll && f.target && this.animationProgress !== 1 ? this.createRelativeTarget(f, this.target, f.target) : this.relativeParent = this.relativeTarget = void 0));
    }
    getClosestProjectingParent() {
      if (!(!this.parent || Ei(this.parent.latestValues) || al(this.parent.latestValues)))
        return this.parent.isProjecting() ? this.parent : this.parent.getClosestProjectingParent();
    }
    isProjecting() {
      return !!((this.relativeTarget || this.targetDelta || this.options.layoutRoot) && this.layout);
    }
    createRelativeTarget(o, a, l) {
      this.relativeParent = o, this.linkedParentVersion = o.layoutVersion, this.forceRelativeParentToResolveTarget(), this.relativeTarget = ee(), this.relativeTargetOrigin = ee(), Nn(this.relativeTargetOrigin, a, l, this.options.layoutAnchor || void 0), ke(this.relativeTarget, this.relativeTargetOrigin);
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
      ke(this.layoutCorrected, this.layout.layoutBox);
      const h = this.treeScale.x, f = this.treeScale.y;
      Uf(this.layoutCorrected, this.treeScale, this.path, a), o.layout && !o.target && (this.treeScale.x !== 1 || this.treeScale.y !== 1) && (o.target = o.layout.layoutBox, o.targetWithTransforms = ee());
      const { target: p } = o;
      if (!p) {
        this.prevProjectionDelta && (this.createProjectionDeltas(), this.scheduleRender());
        return;
      }
      !this.projectionDelta || !this.prevProjectionDelta ? this.createProjectionDeltas() : (Ir(this.prevProjectionDelta.x, this.projectionDelta.x), Ir(this.prevProjectionDelta.y, this.projectionDelta.y)), Ct(this.projectionDelta, this.layoutCorrected, p, this.latestValues), (this.treeScale.x !== h || this.treeScale.y !== f || !qr(this.projectionDelta.x, this.prevProjectionDelta.x) || !qr(this.projectionDelta.y, this.prevProjectionDelta.y)) && (this.hasProjected = !0, this.scheduleRender(), this.notifyListeners("projectionUpdate", p));
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
      this.prevProjectionDelta = lt(), this.projectionDelta = lt(), this.projectionDeltaWithTransform = lt();
    }
    setAnimationOrigin(o, a = !1, l) {
      const u = this.snapshot, d = u ? u.latestValues : {}, h = { ...this.latestValues }, f = lt();
      (!this.relativeParent || !this.relativeParent.options.layoutRoot) && (this.relativeTarget = this.relativeTargetOrigin = void 0), this.attemptToResolveRelativeTarget = !a;
      const p = ee(), g = u ? u.source : void 0, v = this.layout ? this.layout.source : void 0, b = g !== v, w = this.getStack(), T = !w || w.members.length <= 1, y = !!(b && !T && this.options.crossfade === !0 && !this.path.some(lp));
      this.animationProgress = 0;
      let N;
      const V = l?.interpolateProjection(o);
      this.mixTargetDelta = (C) => {
        const k = C / 1e3, m = V?.(k);
        m ? (f.x.translate = m.x, f.x.scale = q(o.x.scale, 1, k), f.x.origin = o.x.origin, f.x.originPoint = o.x.originPoint, f.y.translate = m.y, f.y.scale = q(o.y.scale, 1, k), f.y.origin = o.y.origin, f.y.originPoint = o.y.originPoint) : (to(f.x, o.x, k), to(f.y, o.y, k)), this.setTargetDelta(f), this.relativeTarget && this.relativeTargetOrigin && this.layout && this.relativeParent && this.relativeParent.layout && (Nn(p, this.layout.layoutBox, this.relativeParent.layout.layoutBox, this.options.layoutAnchor || void 0), ap(this.relativeTarget, this.relativeTargetOrigin, p, k), N && Ih(this.relativeTarget, N) && (this.isProjectionDirty = !1), N || (N = ee()), ke(N, this.relativeTarget)), b && (this.animationValues = h, jh(h, d, this.latestValues, k, y, T)), m && m.rotate !== void 0 && (this.animationValues || (this.animationValues = h), this.animationValues.pathRotation = m.rotate), this.root.scheduleUpdateProjection(), this.scheduleRender(), this.animationProgress = k;
      }, this.mixTargetDelta(this.options.layoutRoot ? 1e3 : 0);
    }
    startAnimation(o) {
      this.notifyListeners("animationStart"), this.currentAnimation?.stop(), this.resumingFrom?.currentAnimation?.stop(), this.pendingAnimation && (Re(this.pendingAnimation), this.pendingAnimation = void 0), this.pendingAnimation = G.update(() => {
        hn.hasAnimatedSinceResize = !0, this.motionValue || (this.motionValue = Le(0)), this.motionValue.jump(0, !1), this.currentAnimation = El(this.motionValue, [0, 1e3], {
          ...o,
          velocity: 0,
          isSync: !0,
          onUpdate: (a) => {
            this.mixTargetDelta(a), o.onUpdate && o.onUpdate(a);
          },
          onComplete: () => {
            o.onComplete && o.onComplete(), this.completeAnimation();
          }
        }), fd(this.currentAnimation, this), this.resumingFrom && (this.resumingFrom.currentAnimation = this.currentAnimation), this.pendingAnimation = void 0;
      });
    }
    completeAnimation() {
      this.resumingFrom && (this.resumingFrom.currentAnimation = void 0, this.resumingFrom.preserveOpacity = void 0);
      const o = this.getStack();
      o && o.exitAnimationComplete(), this.resumingFrom = this.currentAnimation = this.animationValues = void 0, this.notifyListeners("animationComplete");
    }
    finishAnimation() {
      this.currentAnimation && (this.mixTargetDelta && this.mixTargetDelta(Hh), this.currentAnimation.stop()), this.completeAnimation();
    }
    applyTransformsToTarget() {
      const o = this.getLead(), { targetWithTransforms: a, layout: l, latestValues: u } = o;
      let { target: d } = o;
      if (!(!a || !d || !l)) {
        if (this !== o && this.layout && l && Rl(this.options.animationType, this.layout.layoutBox, l.layoutBox)) {
          d = this.target || ee();
          const h = ue(this.layout.layoutBox.x);
          d.x.min = o.target.x.min, d.x.max = d.x.min + h;
          const f = ue(this.layout.layoutBox.y);
          d.y.min = o.target.y.min, d.y.max = d.y.min + f;
        }
        ke(a, d), an(a, u), Ct(this.projectionDeltaWithTransform, this.layoutCorrected, a, u);
      }
    }
    registerSharedNode(o, a) {
      this.sharedNodes.has(o) || this.sharedNodes.set(o, new Kh()), this.sharedNodes.get(o).add(a);
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
      l.z && Zn("z", o, u, this.animationValues);
      for (let d = 0; d < Xn.length; d++)
        Zn(`rotate${Xn[d]}`, o, u, this.animationValues), Zn(`skew${Xn[d]}`, o, u, this.animationValues);
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
        this.needsReset = !1, o.visibility = "", o.opacity = "", o.pointerEvents = fn(a?.pointerEvents) || "", o.transform = l ? l(this.latestValues, "") : "none";
        return;
      }
      const u = this.getLead();
      if (!this.projectionDelta || !this.layout || !u.target) {
        this.options.layoutId && (o.opacity = this.latestValues.opacity !== void 0 ? this.latestValues.opacity : 1, o.pointerEvents = fn(a?.pointerEvents) || ""), this.hasProjected && !Ge(this.latestValues) && (o.transform = l ? l({}, "") : "none", this.hasProjected = !1);
        return;
      }
      o.visibility = "";
      const d = u.animationValues || u.latestValues;
      this.applyTransformsToTarget();
      let h = Bh(this.projectionDeltaWithTransform, this.treeScale, d);
      l && (h = l(d, h)), o.transform = h;
      const { x: f, y: p } = this.projectionDelta;
      o.transformOrigin = `${f.origin * 100}% ${p.origin * 100}% 0`, u.animationValues ? o.opacity = u === this ? d.opacity ?? this.latestValues.opacity ?? 1 : this.preserveOpacity ? this.latestValues.opacity : d.opacityExit : o.opacity = u === this ? d.opacity !== void 0 ? d.opacity : "" : d.opacityExit !== void 0 ? d.opacityExit : 0;
      for (const g in Vi) {
        if (d[g] === void 0)
          continue;
        const { correct: v, applyTo: b, isCSSVariable: w } = Vi[g], T = h === "none" ? d[g] : v(d[g], u);
        if (b) {
          const y = b.length;
          for (let N = 0; N < y; N++)
            o[b[N]] = T;
        } else
          w ? this.options.visualElement.renderState.vars[g] = T : o[g] = T;
      }
      this.options.layoutId && (o.pointerEvents = u === this ? fn(a?.pointerEvents) || "" : "none");
    }
    clearSnapshot() {
      this.resumeFrom = this.snapshot = void 0;
    }
    // Only run on root
    resetTree() {
      this.root.nodes.forEach((o) => o.currentAnimation?.stop()), this.root.nodes.forEach(Qr), this.root.sharedNodes.clear();
    }
  };
}
function Yh(e) {
  e.updateLayout();
}
function Xh(e) {
  const t = e.resumeFrom?.snapshot || e.snapshot;
  if (e.isLead() && e.layout && t && e.hasListeners("didUpdate")) {
    const { layoutBox: n, measuredBox: i } = e.layout, { animationType: s } = e.options, r = t.source !== e.layout.source;
    if (s === "size")
      Pe((d) => {
        const h = r ? t.measuredBox[d] : t.layoutBox[d], f = ue(h);
        h.min = n[d].min, h.max = h.min + f;
      });
    else if (s === "x" || s === "y") {
      const d = s === "x" ? "y" : "x";
      Ri(r ? t.measuredBox[d] : t.layoutBox[d], n[d]);
    } else Rl(s, t.layoutBox, n) && Pe((d) => {
      const h = r ? t.measuredBox[d] : t.layoutBox[d], f = ue(n[d]);
      h.max = h.min + f, e.relativeTarget && !e.currentAnimation && (e.isProjectionDirty = !0, e.relativeTarget[d].max = e.relativeTarget[d].min + f);
    });
    const o = lt();
    Ct(o, n, t.layoutBox);
    const a = lt();
    r ? Ct(a, e.applyTransform(i, !0), t.measuredBox) : Ct(a, n, t.layoutBox);
    const l = !Pl(o);
    let u = !1;
    if (!e.resumeFrom) {
      const d = e.getClosestProjectingParent();
      if (d && !d.resumeFrom) {
        const { snapshot: h, layout: f } = d;
        if (h && f) {
          const p = e.options.layoutAnchor || void 0, g = ee();
          Nn(g, t.layoutBox, h.layoutBox, p);
          const v = ee();
          Nn(v, n, f.layoutBox, p), Ml(g, v) || (u = !0), d.options.layoutRoot && (e.relativeTarget = v, e.relativeTargetOrigin = g, e.relativeParent = d);
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
function Zh(e) {
  e.parent && (e.isProjecting() || (e.isProjectionDirty = e.parent.isProjectionDirty), e.isSharedProjectionDirty || (e.isSharedProjectionDirty = !!(e.isProjectionDirty || e.parent.isProjectionDirty || e.parent.isSharedProjectionDirty)), e.isTransformDirty || (e.isTransformDirty = e.parent.isTransformDirty));
}
function Qh(e) {
  e.isProjectionDirty = e.isSharedProjectionDirty = e.isTransformDirty = !1;
}
function Jh(e) {
  e.clearSnapshot();
}
function Qr(e) {
  e.clearMeasurements();
}
function ep(e) {
  e.isLayoutDirty = !0, e.updateLayout();
}
function Jr(e) {
  e.isLayoutDirty = !1;
}
function tp(e) {
  e.isAnimationBlocked && e.layout && !e.isLayoutDirty && (e.snapshot = e.layout, e.isLayoutDirty = !0);
}
function np(e) {
  const { visualElement: t } = e.options;
  t && t.getProps().onBeforeLayoutMeasure && t.notify("BeforeLayoutMeasure"), e.resetTransform();
}
function eo(e) {
  e.finishAnimation(), e.targetDelta = e.relativeTarget = e.target = void 0, e.isProjectionDirty = !0;
}
function ip(e) {
  e.resolveTargetDelta();
}
function sp(e) {
  e.calcProjection();
}
function rp(e) {
  e.resetSkewAndRotation();
}
function op(e) {
  e.removeLeadSnapshot();
}
function to(e, t, n) {
  e.translate = q(t.translate, 0, n), e.scale = q(t.scale, 1, n), e.origin = t.origin, e.originPoint = t.originPoint;
}
function no(e, t, n, i) {
  e.min = q(t.min, n.min, i), e.max = q(t.max, n.max, i);
}
function ap(e, t, n, i) {
  no(e.x, t.x, n.x, i), no(e.y, t.y, n.y, i);
}
function lp(e) {
  return e.animationValues && e.animationValues.opacityExit !== void 0;
}
const cp = {
  duration: 0.45,
  ease: [0.4, 0, 0.1, 1]
}, io = (e) => typeof navigator < "u" && navigator.userAgent && navigator.userAgent.toLowerCase().includes(e), so = io("applewebkit/") && !io("chrome/") ? Math.round : Se;
function ro(e) {
  e.min = so(e.min), e.max = so(e.max);
}
function up(e) {
  ro(e.x), ro(e.y);
}
function Rl(e, t, n) {
  return e === "position" || e === "preserve-aspect" && !Vh(Hr(t), Hr(n), 0.2);
}
function dp(e) {
  return e !== e.root && e.scroll?.wasRoot;
}
const fp = Vl({
  attachResizeListener: (e, t) => Bt(e, "resize", t),
  measureScroll: () => ({
    x: document.documentElement.scrollLeft || document.body?.scrollLeft || 0,
    y: document.documentElement.scrollTop || document.body?.scrollTop || 0
  }),
  checkIsScrollRoot: () => !0
}), Qn = {
  current: void 0
}, Ll = Vl({
  measureScroll: (e) => ({
    x: e.scrollLeft,
    y: e.scrollTop
  }),
  defaultParent: () => {
    if (!Qn.current) {
      const e = new fp({});
      e.mount(window), e.setOptions({ layoutScroll: !0 }), Qn.current = e;
    }
    return Qn.current;
  },
  resetTransform: (e, t) => {
    e.style.transform = t !== void 0 ? t : "none";
  },
  checkIsScrollRoot: (e) => window.getComputedStyle(e).position === "fixed"
}), Fn = pt({
  transformPagePoint: (e) => e,
  isStatic: !1,
  reducedMotion: "never"
});
function oo(e, t) {
  if (typeof e == "function")
    return e(t);
  e != null && (e.current = t);
}
function hp(...e) {
  return (t) => {
    let n = !1;
    const i = e.map((s) => {
      const r = oo(s, t);
      return !n && typeof r == "function" && (n = !0), r;
    });
    if (n)
      return () => {
        for (let s = 0; s < i.length; s++) {
          const r = i[s];
          typeof r == "function" ? r() : oo(e[s], null);
        }
      };
  };
}
function pp(...e) {
  return Cn.useCallback(hp(...e), e);
}
class mp extends Cn.Component {
  getSnapshotBeforeUpdate(t) {
    const n = this.props.childRef.current;
    if (dt(n) && t.isPresent && !this.props.isPresent && this.props.pop !== !1) {
      const i = n.offsetParent, s = dt(i) && i.offsetWidth || 0, r = dt(i) && i.offsetHeight || 0, o = getComputedStyle(n), a = this.props.sizeRef.current;
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
function gp({ children: e, isPresent: t, anchorX: n, anchorY: i, root: s, pop: r }) {
  const o = we(), a = P(null), l = P({
    width: 0,
    height: 0,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    direction: "ltr"
  }), { nonce: u } = re(Fn), d = r !== !1 ? e.props?.ref ?? e?.ref : void 0, h = pp(a, d);
  return $i(() => {
    const { width: f, height: p, top: g, left: v, right: b, bottom: w, direction: T } = l.current;
    if (t || r === !1 || !a.current || !f || !p)
      return;
    const y = T === "rtl", N = n === "left" ? y ? `right: ${b}` : `left: ${v}` : y ? `left: ${v}` : `right: ${b}`, V = i === "bottom" ? `bottom: ${w}` : `top: ${g}`;
    a.current.dataset.motionPopId = o;
    const C = document.createElement("style");
    u && (C.nonce = u);
    const k = s ?? document.head;
    return k.appendChild(C), C.sheet && C.sheet.insertRule(`
          [data-motion-pop-id="${o}"] {
            position: absolute !important;
            width: ${f}px !important;
            height: ${p}px !important;
            ${N}px !important;
            ${V}px !important;
          }
        `), () => {
      a.current?.removeAttribute("data-motion-pop-id"), k.contains(C) && k.removeChild(C);
    };
  }, [t]), c(mp, { isPresent: t, childRef: a, sizeRef: l, pop: r, children: r === !1 ? e : Cn.cloneElement(e, { ref: h }) });
}
const yp = ({ children: e, initial: t, isPresent: n, onExitComplete: i, custom: s, presenceAffectsLayout: r, mode: o, anchorX: a, anchorY: l, root: u }) => {
  const d = Ut(xp), h = we(), f = P(n), p = P(i);
  Rt(() => {
    f.current = n, p.current = i;
  });
  let g = !0, v = le(() => (g = !1, {
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
  return r && g && (v = { ...v }), le(() => {
    d.forEach((b, w) => d.set(w, !1));
  }, [n]), Cn.useEffect(() => {
    !n && !d.size && i && i();
  }, [n]), e = c(gp, { pop: o === "popLayout", isPresent: n, anchorX: a, anchorY: l, root: u, children: e }), c(zt.Provider, { value: v, children: e });
};
function xp() {
  return /* @__PURE__ */ new Map();
}
function Fl(e = !0) {
  const t = re(zt);
  if (t === null)
    return [!0, null];
  const { isPresent: n, onExitComplete: i, register: s } = t, r = we();
  O(() => {
    if (e)
      return s(r);
  }, [e]);
  const o = Y(() => e && i && i(r), [r, i, e]);
  return !n && i ? [!1, o] : [!0];
}
function vp() {
  return bp(re(zt));
}
function bp(e) {
  return e === null ? !0 : e.isPresent;
}
const Qt = (e) => e.key || "";
function ao(e) {
  const t = [];
  return Pc.forEach(e, (n) => {
    Mc(n) && t.push(n);
  }), t;
}
const de = ({ children: e, custom: t, initial: n = !0, onExitComplete: i, presenceAffectsLayout: s = !0, mode: r = "sync", propagate: o = !1, anchorX: a = "left", anchorY: l = "top", root: u }) => {
  const [d, h] = Fl(o), f = le(() => ao(e), [e]), p = o && !d ? [] : f.map(Qt), g = P(!0), v = P(f), b = Ut(() => /* @__PURE__ */ new Map()), w = P(/* @__PURE__ */ new Set()), [T, y] = F(f), [N, V] = F(f);
  Rt(() => {
    o && !d && !N.length && h?.();
  }, [d, o, N.length, h]), Rt(() => {
    g.current = !1, v.current = f;
    for (let m = 0; m < N.length; m++) {
      const S = Qt(N[m]);
      p.includes(S) ? (b.delete(S), w.current.delete(S)) : b.get(S) !== !0 && b.set(S, !1);
    }
  }, [N, p.length, p.join("-")]);
  const C = [];
  if (f !== T) {
    let m = [...f], S = 0;
    for (const A of N) {
      const L = p.indexOf(Qt(A));
      L === -1 ? (m.splice(S++, 0, A), C.push(A)) : S = L + C.length + 1;
    }
    return r === "wait" && C.length && (m = C), V(ao(m)), y(f), null;
  }
  process.env.NODE_ENV !== "production" && r === "wait" && N.length > 1 && console.warn(`You're attempting to animate multiple children within AnimatePresence, but its mode is set to "wait". This will lead to odd visual behaviour.`);
  const { forceRender: k } = re(Qi);
  return c(_, { children: N.map((m) => {
    const S = Qt(m), A = o && !d ? !1 : f === N || p.includes(S), L = () => {
      if (w.current.has(S))
        return;
      if (b.has(S))
        w.current.add(S), b.set(S, !0);
      else
        return;
      let j = !0;
      b.forEach((I) => {
        I || (j = !1);
      }), j && (k?.(), V(v.current), o && h?.(), i && i());
    };
    return c(yp, { isPresent: A, initial: !g.current || n ? void 0 : !1, custom: t, presenceAffectsLayout: s, mode: r, root: u, onExitComplete: A ? void 0 : L, anchorX: a, anchorY: l, children: m }, S);
  }) });
}, Ol = pt({ strict: !1 }), lo = {
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
let co = !1;
function wp() {
  if (co)
    return;
  const e = {};
  for (const t in lo)
    e[t] = {
      isEnabled: (n) => lo[t].some((i) => !!n[i])
    };
  gl(e), co = !0;
}
function Il() {
  return wp(), mh();
}
function kp(e) {
  const t = Il();
  for (const n in e)
    t[n] = {
      ...t[n],
      ...e[n]
    };
  gl(t);
}
const On = /* @__PURE__ */ pt({});
function Tp(e, t) {
  if (Ln(e)) {
    const { initial: n, animate: i } = e;
    return {
      initial: n === !1 || It(n) ? n : void 0,
      animate: It(i) ? i : void 0
    };
  }
  return e.inherit !== !1 ? t : {};
}
function Sp(e) {
  const { initial: t, animate: n } = Tp(e, re(On));
  return le(() => ({ initial: t, animate: n }), [uo(t), uo(n)]);
}
function uo(e) {
  return Array.isArray(e) ? e.join(" ") : e;
}
const Ls = () => ({
  style: {},
  transform: {},
  transformOrigin: {},
  vars: {}
});
function Bl(e, t, n) {
  for (const i in t)
    !ie(t[i]) && !vl(i, n) && (e[i] = t[i]);
}
function Np({ transformTemplate: e }, t) {
  return le(() => {
    const n = Ls();
    return As(n, t, e), Object.assign({}, n.vars, n.style);
  }, [t]);
}
function Ap(e, t) {
  const n = e.style || {}, i = {};
  return Bl(i, n, e), Object.assign(i, Np(e, t)), i;
}
function Pp(e, t) {
  const n = {}, i = Ap(e, t);
  return e.drag && e.dragListener !== !1 && (n.draggable = !1, i.userSelect = i.WebkitUserSelect = i.WebkitTouchCallout = "none", i.touchAction = e.drag === !0 ? "none" : `pan-${e.drag === "x" ? "y" : "x"}`), e.tabIndex === void 0 && (e.onTap || e.onTapStart || e.whileTap) && (n.tabIndex = 0), n.style = i, n;
}
const $l = () => ({
  ...Ls(),
  attrs: {}
});
function Mp(e, t, n, i) {
  const s = le(() => {
    const r = $l();
    return sl(r, t, wl(i), e.transformTemplate, e.style), {
      ...r.attrs,
      style: { ...r.style }
    };
  }, [t]);
  if (e.style) {
    const r = {};
    Bl(r, e.style, e), s.style = { ...r, ...s.style };
  }
  return s;
}
const Cp = /* @__PURE__ */ new Set([
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
  return e.startsWith("while") || e.startsWith("drag") && e !== "draggable" || e.startsWith("layout") || e.startsWith("onTap") || e.startsWith("onPan") || e.startsWith("onLayout") || Cp.has(e);
}
function Ep(e, t) {
  return e.startsWith("on") ? !An(e) : t?.(e) ?? !An(e);
}
function Dp(e, t, n, i) {
  const s = {};
  for (const r in e)
    r === "values" && typeof e.values == "object" || ie(e[r]) || (Ep(r, i) || n === !0 && An(r) || !t && !An(r) || // If trying to use native HTML drag events, forward drag listeners
    e.draggable && r.startsWith("onDrag")) && (s[r] = e[r]);
  return s;
}
const Vp = [
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
function Fs(e) {
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
      !!(Vp.indexOf(e) > -1 || /**
       * If it contains a capital letter, it's an SVG component
       */
      /[A-Z]/u.test(e))
    )
  );
}
function Rp(e, t, n, { latestValues: i }, s, r = !1, o, a) {
  const u = (o ?? Fs(e) ? Mp : Pp)(t, i, s, e), d = Dp(t, typeof e == "string", r, a), h = e !== ji ? { ...d, ...u, ref: n } : {}, { children: f } = t, p = le(() => ie(f) ? f.get() : f, [f]);
  return Cc(e, {
    ...h,
    children: p
  });
}
function Lp({ scrapeMotionValuesFromProps: e, createRenderState: t }, n, i, s) {
  return {
    latestValues: Fp(n, i, s, e),
    renderState: t()
  };
}
function Fp(e, t, n, i) {
  const s = {}, r = i(e, {});
  for (const f in r)
    s[f] = fn(r[f]);
  let { initial: o, animate: a } = e;
  const l = Ln(e), u = pl(e);
  t && u && !l && e.inherit !== !1 && (o === void 0 && (o = t.initial), a === void 0 && (a = t.animate));
  let d = n ? n.initial === !1 : !1;
  d = d || o === !1;
  const h = d ? a : o;
  if (h && typeof h != "boolean" && !Rn(h)) {
    const f = Array.isArray(h) ? h : [h];
    for (let p = 0; p < f.length; p++) {
      const g = vs(e, f[p]);
      if (g) {
        const { transitionEnd: v, transition: b, ...w } = g;
        for (const T in w) {
          let y = w[T];
          if (Array.isArray(y)) {
            const N = d ? y.length - 1 : 0;
            y = y[N];
          }
          y !== null && (s[T] = y);
        }
        for (const T in v)
          s[T] = v[T];
      }
    }
  }
  return s;
}
const jl = (e) => (t, n) => {
  const i = re(On), s = re(zt), r = () => Lp(e, t, i, s);
  return n ? r() : Ut(r);
}, Op = /* @__PURE__ */ jl({
  scrapeMotionValuesFromProps: Rs,
  createRenderState: Ls
}), Ip = /* @__PURE__ */ jl({
  scrapeMotionValuesFromProps: kl,
  createRenderState: $l
}), Bp = /* @__PURE__ */ Symbol.for("motionComponentSymbol");
function $p(e, t, n) {
  const i = P(n);
  $i(() => {
    i.current = n;
  });
  const s = P(null);
  return Y((r) => {
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
const Ul = pt({});
function nt(e) {
  return e && typeof e == "object" && Object.prototype.hasOwnProperty.call(e, "current");
}
function jp(e, t, n, i, s, r) {
  const { visualElement: o } = re(On), a = re(Ol), l = re(zt), u = re(Fn), d = u.reducedMotion, h = u.skipAnimations, f = P(null), p = P(!1);
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
  const g = f.current, v = re(Ul);
  g && !g.projection && s && (g.type === "html" || g.type === "svg") && Up(f.current, n, s, v);
  const b = P(!1);
  $i(() => {
    g && b.current && g.update(n, l);
  });
  const w = n[Xa], T = P(!!w && typeof window < "u" && !window.MotionHandoffIsComplete?.(w) && window.MotionHasOptimisedAnimation?.(w));
  return Rt(() => {
    p.current = !0, g && (b.current = !0, window.MotionIsMounted = !0, g.updateFeatures(), g.scheduleRenderMicrotask(), T.current && g.animationState && g.animationState.animateChanges());
  }), O(() => {
    g && (!T.current && g.animationState && g.animationState.animateChanges(), T.current && (queueMicrotask(() => {
      window.MotionHandoffMarkAsComplete?.(w);
    }), T.current = !1), g.enteringChildren = void 0);
  }), g;
}
function Up(e, t, n, i) {
  const { layoutId: s, layout: r, drag: o, dragConstraints: a, layoutScroll: l, layoutRoot: u, layoutAnchor: d, layoutCrossfade: h } = t;
  e.projection = new n(e.latestValues, t["data-framer-portal-id"] ? void 0 : zl(e.parent)), e.projection.setOptions({
    layoutId: s,
    layout: r,
    alwaysMeasureLayout: !!o || a && nt(a),
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
function zl(e) {
  if (e)
    return e.options.allowProjection !== !1 ? e.projection : zl(e.parent);
}
function Jn(e, { forwardMotionProps: t = !1, type: n } = {}, i, s) {
  i && kp(i);
  const r = n ? n === "svg" : Fs(e), o = r ? Ip : Op;
  function a(u, d) {
    let h;
    const f = {
      ...re(Fn),
      ...u,
      layoutId: zp(u)
    }, { isStatic: p, isValidProp: g } = f, v = Sp(u), b = o(u, p);
    if (!p && typeof window < "u") {
      Wp(f, i);
      const w = _p(f);
      h = w.MeasureLayout, v.visualElement = jp(e, b, f, s, w.ProjectionNode, r);
    }
    return x(On.Provider, { value: v, children: [h && v.visualElement ? c(h, { visualElement: v.visualElement, ...f }) : null, Rp(e, u, $p(b, v.visualElement, d), b, p, t, r, g)] });
  }
  a.displayName = `motion.${typeof e == "string" ? e : `create(${e.displayName ?? e.name ?? ""})`}`;
  const l = Ui(a);
  return l[Bp] = e, l;
}
function zp({ layoutId: e }) {
  const t = re(Qi).id;
  return t && e !== void 0 ? t + "-" + e : e;
}
function Wp(e, t) {
  const n = re(Ol).strict;
  if (process.env.NODE_ENV !== "production" && t && n) {
    const i = "You have rendered a `motion` component within a `LazyMotion` component. This will break tree shaking. Import and render a `m` component instead.";
    e.ignoreStrict ? et(!1, i, "lazy-strict-mode") : xe(!1, i, "lazy-strict-mode");
  }
}
function _p(e) {
  const t = Il(), { drag: n, layout: i } = t;
  if (!n && !i)
    return {};
  const s = { ...n, ...i };
  return {
    MeasureLayout: n?.isEnabled(e) || i?.isEnabled(e) ? s.MeasureLayout : void 0,
    ProjectionNode: s.ProjectionNode
  };
}
function Gp(e, t) {
  if (typeof Proxy > "u")
    return Jn;
  const n = /* @__PURE__ */ new Map(), i = (r, o) => Jn(r, o, e, t), s = (r, o) => (process.env.NODE_ENV !== "production" && En(!1, "motion() is deprecated. Use motion.create() instead."), i(r, o));
  return new Proxy(s, {
    /**
     * Called when `motion` is referenced with a prop: `motion.div`, `motion.input` etc.
     * The prop name is passed through as `key` and we can use that to generate a `motion`
     * DOM component with that name.
     */
    get: (r, o) => o === "create" ? i : (n.has(o) || n.set(o, Jn(o, void 0, e, t)), n.get(o))
  });
}
const Kp = (e, t) => t.isSVG ?? Fs(e) ? new wh(t) : new vh(t, {
  allowProjection: e !== ji
});
class Hp extends Ue {
  /**
   * We dynamically generate the AnimationState manager as it contains a reference
   * to the underlying animation library. We only want to load that if we load this,
   * so people can optionally code split it out using the `m` component.
   */
  constructor(t) {
    super(t), t.animationState || (t.animationState = Ah(t));
  }
  updateAnimationControlsSubscription() {
    const { animate: t } = this.node.getProps();
    Rn(t) && (this.unmountControls = t.subscribe(this.node));
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
let qp = 0;
class Yp extends Ue {
  constructor() {
    super(...arguments), this.id = qp++, this.isExitComplete = !1;
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
          const a = Ze(this.node, r, o);
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
const Xp = {
  animation: {
    Feature: Hp
  },
  exit: {
    Feature: Yp
  }
};
function Ht(e) {
  return {
    point: {
      x: e.pageX,
      y: e.pageY
    }
  };
}
const Zp = (e) => (t) => Es(t) && e(t, Ht(t));
function Et(e, t, n, i) {
  return Bt(e, t, Zp(n), i);
}
const Wl = ({ current: e }) => e ? e.ownerDocument.defaultView : null, fo = (e, t) => Math.abs(e - t);
function Qp(e, t) {
  const n = fo(e.x, t.x), i = fo(e.y, t.y);
  return Math.sqrt(n ** 2 + i ** 2);
}
const ho = /* @__PURE__ */ new Set(["auto", "scroll"]);
class _l {
  constructor(t, n, { transformPagePoint: i, contextWindow: s = window, dragSnapToOrigin: r = !1, distanceThreshold: o = 3, element: a } = {}) {
    if (this.startEvent = null, this.lastMoveEvent = null, this.lastMoveEventInfo = null, this.lastRawMoveEventInfo = null, this.handlers = {}, this.contextWindow = window, this.scrollPositions = /* @__PURE__ */ new Map(), this.removeScrollListeners = null, this.onElementScroll = (g) => {
      this.handleScroll(g.target);
    }, this.onWindowScroll = () => {
      this.handleScroll(window);
    }, this.updatePoint = () => {
      if (!(this.lastMoveEvent && this.lastMoveEventInfo))
        return;
      this.lastRawMoveEventInfo && (this.lastMoveEventInfo = Jt(this.lastRawMoveEventInfo, this.transformPagePoint));
      const g = ei(this.lastMoveEventInfo, this.history), v = this.startEvent !== null, b = Qp(g.offset, { x: 0, y: 0 }) >= this.distanceThreshold;
      if (!v && !b)
        return;
      const { point: w } = g, { timestamp: T } = te;
      this.history.push({ ...w, timestamp: T });
      const { onStart: y, onMove: N } = this.handlers;
      v || (y && y(this.lastMoveEvent, g), this.startEvent = this.lastMoveEvent), N && N(this.lastMoveEvent, g);
    }, this.handlePointerMove = (g, v) => {
      this.lastMoveEvent = g, this.lastRawMoveEventInfo = v, this.lastMoveEventInfo = Jt(v, this.transformPagePoint), G.update(this.updatePoint, !0);
    }, this.handlePointerUp = (g, v) => {
      this.end();
      const { onEnd: b, onSessionEnd: w, resumeAnimation: T } = this.handlers;
      if ((this.dragSnapToOrigin || !this.startEvent) && T && T(), !(this.lastMoveEvent && this.lastMoveEventInfo))
        return;
      const y = ei(g.type === "pointercancel" ? this.lastMoveEventInfo : Jt(v, this.transformPagePoint), this.history);
      this.startEvent && b && b(g, y), w && w(g, y);
    }, !Es(t))
      return;
    this.dragSnapToOrigin = r, this.handlers = n, this.transformPagePoint = i, this.distanceThreshold = o, this.contextWindow = s || window;
    const l = Ht(t), u = Jt(l, this.transformPagePoint), { point: d } = u, { timestamp: h } = te;
    this.history = [{ ...d, timestamp: h }];
    const { onSessionStart: f } = n;
    f && f(t, ei(u, this.history));
    const p = { passive: !0, capture: !0 };
    this.removeListeners = Wt(Et(this.contextWindow, "pointermove", this.handlePointerMove, p), Et(this.contextWindow, "pointerup", this.handlePointerUp, p), Et(this.contextWindow, "pointercancel", this.handlePointerUp, p)), a && this.startScrollTracking(a);
  }
  /**
   * Start tracking scroll on ancestors and window.
   */
  startScrollTracking(t) {
    let n = t.parentElement;
    for (; n; ) {
      const i = getComputedStyle(n);
      (ho.has(i.overflowX) || ho.has(i.overflowY)) && this.scrollPositions.set(n, {
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
    r.x === 0 && r.y === 0 || (i ? this.lastMoveEventInfo && (this.lastMoveEventInfo.point.x += r.x, this.lastMoveEventInfo.point.y += r.y) : this.history.length > 0 && (this.history[0].x -= r.x, this.history[0].y -= r.y), this.scrollPositions.set(t, s), G.update(this.updatePoint, !0));
  }
  updateHandlers(t) {
    this.handlers = t;
  }
  end() {
    this.removeListeners && this.removeListeners(), this.removeScrollListeners && this.removeScrollListeners(), this.scrollPositions.clear(), Re(this.updatePoint);
  }
}
function Jt(e, t) {
  return t ? { point: t(e.point) } : e;
}
function po(e, t) {
  return { x: e.x - t.x, y: e.y - t.y };
}
function ei({ point: e }, t) {
  return {
    point: e,
    delta: po(e, Gl(t)),
    offset: po(e, Jp(t)),
    velocity: em(t, 0.1)
  };
}
function Jp(e) {
  return e[0];
}
function Gl(e) {
  return e[e.length - 1];
}
function em(e, t) {
  if (e.length < 2)
    return { x: 0, y: 0 };
  let n = e.length - 1, i = null;
  const s = Gl(e);
  for (; n >= 0 && (i = e[n], !(s.timestamp - i.timestamp > /* @__PURE__ */ pe(t))); )
    n--;
  if (!i)
    return { x: 0, y: 0 };
  i === e[0] && e.length > 2 && s.timestamp - i.timestamp > /* @__PURE__ */ pe(t) * 2 && (i = e[1]);
  const r = /* @__PURE__ */ me(s.timestamp - i.timestamp);
  if (r === 0)
    return { x: 0, y: 0 };
  const o = {
    x: (s.x - i.x) / r,
    y: (s.y - i.y) / r
  };
  return o.x === 1 / 0 && (o.x = 0), o.y === 1 / 0 && (o.y = 0), o;
}
function tm(e, { min: t, max: n }, i) {
  return t !== void 0 && e < t ? e = i ? q(t, e, i.min) : Math.max(e, t) : n !== void 0 && e > n && (e = i ? q(n, e, i.max) : Math.min(e, n)), e;
}
function mo(e, t, n) {
  return {
    min: t !== void 0 ? e.min + t : void 0,
    max: n !== void 0 ? e.max + n - (e.max - e.min) : void 0
  };
}
function nm(e, { top: t, left: n, bottom: i, right: s }) {
  return {
    x: mo(e.x, n, s),
    y: mo(e.y, t, i)
  };
}
function go(e, t) {
  let n = t.min - e.min, i = t.max - e.max;
  return t.max - t.min < e.max - e.min && ([n, i] = [i, n]), { min: n, max: i };
}
function im(e, t) {
  return {
    x: go(e.x, t.x),
    y: go(e.y, t.y)
  };
}
function sm(e, t) {
  let n = 0.5;
  const i = ue(e), s = ue(t);
  return s > i ? n = /* @__PURE__ */ ft(t.min, t.max - i, e.min) : i > s && (n = /* @__PURE__ */ ft(e.min, e.max - s, t.min)), Ne(0, 1, n);
}
function rm(e, t) {
  const n = {};
  return t.min !== void 0 && (n.min = t.min - e.min), t.max !== void 0 && (n.max = t.max - e.min), n;
}
const Li = 0.35;
function om(e = Li) {
  return e === !1 ? e = 0 : e === !0 && (e = Li), {
    x: yo(e, "left", "right"),
    y: yo(e, "top", "bottom")
  };
}
function yo(e, t, n) {
  return {
    min: xo(e, t),
    max: xo(e, n)
  };
}
function xo(e, t) {
  return typeof e == "number" ? e : e[t] || 0;
}
const am = /* @__PURE__ */ new WeakMap();
class lm {
  constructor(t) {
    this.openDragLock = null, this.isDragging = !1, this.currentDirection = null, this.originPoint = { x: 0, y: 0 }, this.constraints = !1, this.hasMutatedConstraints = !1, this.elastic = ee(), this.latestPointerEvent = null, this.latestPanInfo = null, this.visualElement = t;
  }
  start(t, { snapToCursor: n = !1, distanceThreshold: i } = {}) {
    const { presenceContext: s } = this.visualElement;
    if (s && s.isPresent === !1)
      return;
    const r = (h) => {
      n && this.snapToCursor(Ht(h).point), this.stopAnimation();
    }, o = (h, f) => {
      const { drag: p, dragPropagation: g, onDragStart: v } = this.getProps();
      if (p && !g && (this.openDragLock && this.openDragLock(), this.openDragLock = qf(p), !this.openDragLock))
        return;
      this.latestPointerEvent = h, this.latestPanInfo = f, this.isDragging = !0, this.currentDirection = null, this.resolveConstraints(), this.visualElement.projection && (this.visualElement.projection.isAnimationBlocked = !0, this.visualElement.projection.target = void 0), Pe((w) => {
        let T = this.getAxisMotionValue(w).get() || 0;
        if (Ce.test(T)) {
          const { projection: y } = this.visualElement;
          if (y && y.layout) {
            const N = y.layout.layoutBox[w];
            N && (T = ue(N) * (parseFloat(T) / 100));
          }
        }
        this.originPoint[w] = T;
      }), v && G.update(() => v(h, f), !1, !0), Mi(this.visualElement, "transform");
      const { animationState: b } = this.visualElement;
      b && b.setActive("whileDrag", !0);
    }, a = (h, f) => {
      this.latestPointerEvent = h, this.latestPanInfo = f;
      const { dragPropagation: p, dragDirectionLock: g, onDirectionLock: v, onDrag: b } = this.getProps();
      if (!p && !this.openDragLock)
        return;
      const { offset: w } = f;
      if (g && this.currentDirection === null) {
        this.currentDirection = um(w), this.currentDirection !== null && v && v(this.currentDirection);
        return;
      }
      this.updateAxis("x", f.point, w), this.updateAxis("y", f.point, w), this.visualElement.render(), b && G.update(() => b(h, f), !1, !0);
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
    a && G.postRender(() => a(i, s));
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
    if (!i || !en(t, s, this.currentDirection))
      return;
    const r = this.getAxisMotionValue(t);
    let o = this.originPoint[t] + i[t];
    this.constraints && this.constraints[t] && (o = tm(o, this.constraints[t], this.elastic[t])), r.set(o);
  }
  resolveConstraints() {
    const { dragConstraints: t, dragElastic: n } = this.getProps(), i = this.visualElement.projection && !this.visualElement.projection.layout ? this.visualElement.projection.measure(!1) : this.visualElement.projection?.layout, s = this.constraints;
    t && nt(t) ? this.constraints || (this.constraints = this.resolveRefConstraints()) : t && i ? this.constraints = nm(i.layoutBox, t) : this.constraints = !1, this.elastic = om(n), s !== this.constraints && !nt(t) && i && this.constraints && !this.hasMutatedConstraints && Pe((r) => {
      this.constraints !== !1 && this.getAxisMotionValue(r) && (this.constraints[r] = rm(i.layoutBox[r], this.constraints[r]));
    });
  }
  resolveRefConstraints() {
    const { dragConstraints: t, onMeasureDragConstraints: n } = this.getProps();
    if (!t || !nt(t))
      return !1;
    const i = t.current;
    xe(i !== null, "If `dragConstraints` is set as a React ref, that ref must be passed to another component's `ref` prop.", "drag-constraints-ref");
    const { projection: s } = this.visualElement;
    if (!s || !s.layout)
      return !1;
    s.root && (s.root.scroll = void 0, s.root.updateScroll());
    const r = zf(i, s.root, this.visualElement.getTransformPagePoint());
    let o = im(s.layout.layoutBox, r);
    if (n) {
      const a = n($f(o));
      this.hasMutatedConstraints = !!a, a && (o = ol(a));
    }
    return o;
  }
  startAnimation(t) {
    const { drag: n, dragMomentum: i, dragElastic: s, dragTransition: r, dragSnapToOrigin: o, onDragTransitionEnd: a } = this.getProps(), l = this.constraints || {}, u = Pe((d) => {
      if (!en(d, n, this.currentDirection))
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
    return Mi(this.visualElement, t), i.start(Vn(t, i, 0, n, this.visualElement, !1));
  }
  stopAnimation() {
    Pe((t) => this.getAxisMotionValue(t).stop());
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
    Pe((n) => {
      const { drag: i } = this.getProps();
      if (!en(n, i, this.currentDirection))
        return;
      const { projection: s } = this.visualElement, r = this.getAxisMotionValue(n);
      if (s && s.layout) {
        const { min: o, max: a } = s.layout.layoutBox[n], l = r.get() || 0;
        r.set(t[n] - q(o, a, 0.5) + l);
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
    if (!nt(n) || !i || !this.constraints)
      return;
    this.stopAnimation();
    const s = { x: 0, y: 0 };
    Pe((o) => {
      const a = this.getAxisMotionValue(o);
      if (a && this.constraints !== !1) {
        const l = a.get();
        s[o] = sm({ min: l, max: l }, this.constraints[o]);
      }
    });
    const { transformTemplate: r } = this.visualElement.getProps();
    this.visualElement.current.style.transform = r ? r({}, "") : "none", i.root && i.root.updateScroll(), i.updateLayout(), this.constraints = !1, this.resolveConstraints(), Pe((o) => {
      if (!en(o, t, null))
        return;
      const a = this.getAxisMotionValue(o), { min: l, max: u } = this.constraints[o];
      a.set(q(l, u, s[o]));
    }), this.visualElement.render();
  }
  addListeners() {
    if (!this.visualElement.current)
      return;
    am.set(this.visualElement, this);
    const t = this.visualElement.current, n = Et(t, "pointerdown", (u) => {
      const { drag: d, dragListener: h = !0 } = this.getProps(), f = u.target, p = f !== t && eh(f);
      d && h && !p && this.start(u);
    });
    let i;
    const s = () => {
      const { dragConstraints: u } = this.getProps();
      nt(u) && u.current && (this.constraints = this.resolveRefConstraints(), i || (i = cm(t, u.current, () => this.scalePositionWithinConstraints())));
    }, { projection: r } = this.visualElement, o = r.addEventListener("measure", s);
    r && !r.layout && (r.root && r.root.updateScroll(), r.updateLayout()), G.read(s);
    const a = Bt(window, "resize", () => this.scalePositionWithinConstraints()), l = r.addEventListener("didUpdate", (({ delta: u, hasLayoutChanged: d }) => {
      this.isDragging && d && (Pe((h) => {
        const f = this.getAxisMotionValue(h);
        f && (this.originPoint[h] += u[h].translate, f.set(f.get() + u[h].translate));
      }), this.visualElement.render());
    }));
    return () => {
      a(), n(), o(), l && l(), i && i();
    };
  }
  getProps() {
    const t = this.visualElement.getProps(), { drag: n = !1, dragDirectionLock: i = !1, dragPropagation: s = !1, dragConstraints: r = !1, dragElastic: o = Li, dragMomentum: a = !0 } = t;
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
function vo(e) {
  let t = !0;
  return () => {
    if (t) {
      t = !1;
      return;
    }
    e();
  };
}
function cm(e, t, n) {
  const i = Dr(e, vo(n)), s = Dr(t, vo(n));
  return () => {
    i(), s();
  };
}
function en(e, t, n) {
  return (t === !0 || t === e) && (n === null || n === e);
}
function um(e, t = 10) {
  let n = null;
  return Math.abs(e.y) > t ? n = "y" : Math.abs(e.x) > t && (n = "x"), n;
}
class dm extends Ue {
  constructor(t) {
    super(t), this.removeGroupControls = Se, this.removeListeners = Se, this.controls = new lm(t);
  }
  mount() {
    const { dragControls: t } = this.node.getProps();
    t && (this.removeGroupControls = t.subscribe(this.controls)), this.removeListeners = this.controls.addListeners() || Se;
  }
  update() {
    const { dragControls: t } = this.node.getProps(), { dragControls: n } = this.node.prevProps || {};
    t !== n && (this.removeGroupControls(), t && (this.removeGroupControls = t.subscribe(this.controls)));
  }
  unmount() {
    this.removeGroupControls(), this.removeListeners(), this.controls.isDragging || this.controls.endPanSession();
  }
}
const ti = (e) => (t, n) => {
  e && G.update(() => e(t, n), !1, !0);
};
class fm extends Ue {
  constructor() {
    super(...arguments), this.removePointerDownListener = Se;
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
      onSessionStart: ti(t),
      onStart: ti(n),
      onMove: ti(i),
      onEnd: (r, o) => {
        delete this.session, s && G.postRender(() => s(r, o));
      }
    };
  }
  mount() {
    this.removePointerDownListener = Et(this.node.current, "pointerdown", (t) => this.onPointerDown(t));
  }
  update() {
    this.session && this.session.updateHandlers(this.createPanHandlers());
  }
  unmount() {
    this.removePointerDownListener(), this.session && this.session.end();
  }
}
let ni = !1;
class hm extends Ec {
  /**
   * This only mounts projection nodes for components that
   * need measuring, we might want to do it for all components
   * in order to incorporate transforms
   */
  componentDidMount() {
    const { visualElement: t, layoutGroup: n, switchLayoutGroup: i, layoutId: s } = this.props, { projection: r } = t;
    r && (n.group && n.group.add(r), i && i.register && s && i.register(r), ni && r.root.didUpdate(), r.addEventListener("animationComplete", () => {
      this.safeToRemove();
    }), r.setOptions({
      ...r.options,
      layoutDependency: this.props.layoutDependency,
      onExitComplete: () => this.safeToRemove()
    })), hn.hasEverUpdated = !0;
  }
  getSnapshotBeforeUpdate(t) {
    const { layoutDependency: n, visualElement: i, drag: s, isPresent: r } = this.props, { projection: o } = i;
    return o && (o.isPresent = r, t.layoutDependency !== n && o.setOptions({
      ...o.options,
      layoutDependency: n
    }), ni = !0, s || t.layoutDependency !== n || n === void 0 || t.isPresent !== r ? o.willUpdate() : this.safeToRemove(), t.isPresent !== r && (r ? o.promote() : o.relegate() || G.postRender(() => {
      const a = o.getStack();
      (!a || !a.members.length) && this.safeToRemove();
    }))), null;
  }
  componentDidUpdate() {
    const { visualElement: t, layoutAnchor: n } = this.props, { projection: i } = t;
    i && (i.options.layoutAnchor = n, i.root.didUpdate(), Cs.postRender(() => {
      !i.currentAnimation && i.isLead() && this.safeToRemove();
    }));
  }
  componentWillUnmount() {
    const { visualElement: t, layoutGroup: n, switchLayoutGroup: i } = this.props, { projection: s } = t;
    ni = !0, s && (s.scheduleCheckAfterUnmount(), n && n.group && n.group.remove(s), i && i.deregister && i.deregister(s));
  }
  safeToRemove() {
    const { safeToRemove: t } = this.props;
    t && t();
  }
  render() {
    return null;
  }
}
function Kl(e) {
  const [t, n] = Fl(), i = re(Qi);
  return c(hm, { ...e, layoutGroup: i, switchLayoutGroup: re(Ul), isPresent: t, safeToRemove: n });
}
const pm = {
  pan: {
    Feature: fm
  },
  drag: {
    Feature: dm,
    ProjectionNode: Ll,
    MeasureLayout: Kl
  }
};
function bo(e, t, n) {
  const { props: i } = e;
  e.animationState && i.whileHover && e.animationState.setActive("whileHover", n === "Start");
  const s = "onHover" + n, r = i[s];
  r && G.postRender(() => r(t, Ht(t)));
}
class mm extends Ue {
  mount() {
    const { current: t } = this.node;
    t && (this.unmount = Xf(t, (n, i) => (bo(this.node, i, "Start"), (s) => bo(this.node, s, "End"))));
  }
  unmount() {
  }
}
class gm extends Ue {
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
    this.unmount = Wt(Bt(this.node.current, "focus", () => this.onFocus()), Bt(this.node.current, "blur", () => this.onBlur()));
  }
  unmount() {
  }
}
function wo(e, t, n) {
  const { props: i } = e;
  if (e.current instanceof HTMLButtonElement && e.current.disabled)
    return;
  e.animationState && i.whileTap && e.animationState.setActive("whileTap", n === "Start");
  const s = "onTap" + (n === "End" ? "" : n), r = i[s];
  r && G.postRender(() => r(t, Ht(t)));
}
class ym extends Ue {
  mount() {
    const { current: t } = this.node;
    if (!t)
      return;
    const { globalTapTarget: n, propagate: i } = this.node.props;
    this.unmount = nh(t, (s, r) => (wo(this.node, r, "Start"), (o, { success: a }) => wo(this.node, o, a ? "End" : "Cancel")), {
      useGlobalTarget: n,
      stopPropagation: i?.tap === !1
    });
  }
  unmount() {
  }
}
const Fi = /* @__PURE__ */ new WeakMap(), ii = /* @__PURE__ */ new WeakMap(), xm = (e) => {
  const t = Fi.get(e.target);
  t && t(e);
}, vm = (e) => {
  e.forEach(xm);
};
function bm({ root: e, ...t }) {
  const n = e || document;
  ii.has(n) || ii.set(n, {});
  const i = ii.get(n), s = JSON.stringify(t);
  return i[s] || (i[s] = new IntersectionObserver(vm, { root: e, ...t })), i[s];
}
function wm(e, t, n) {
  const i = bm(t);
  return Fi.set(e, n), i.observe(e), () => {
    Fi.delete(e), i.unobserve(e);
  };
}
const km = {
  some: 0,
  all: 1
};
class Tm extends Ue {
  constructor() {
    super(...arguments), this.hasEnteredView = !1, this.isInView = !1;
  }
  startObserver() {
    this.stopObserver?.();
    const { viewport: t = {} } = this.node.getProps(), { root: n, margin: i, amount: s = "some", once: r } = t, o = {
      root: n ? n.current : void 0,
      rootMargin: i,
      threshold: typeof s == "number" ? s : km[s]
    }, a = (l) => {
      const { isIntersecting: u } = l;
      if (this.isInView === u || (this.isInView = u, r && !u && this.hasEnteredView))
        return;
      u && (this.hasEnteredView = !0), this.node.animationState && this.node.animationState.setActive("whileInView", u);
      const { onViewportEnter: d, onViewportLeave: h } = this.node.getProps(), f = u ? d : h;
      f && f(l);
    };
    this.stopObserver = wm(this.node.current, o, a);
  }
  mount() {
    this.startObserver();
  }
  update() {
    if (typeof IntersectionObserver > "u")
      return;
    const { props: t, prevProps: n } = this.node;
    ["amount", "margin", "root"].some(Sm(t, n)) && this.startObserver();
  }
  unmount() {
    this.stopObserver?.(), this.hasEnteredView = !1, this.isInView = !1;
  }
}
function Sm({ viewport: e = {} }, { viewport: t = {} } = {}) {
  return (n) => e[n] !== t[n];
}
const Nm = {
  inView: {
    Feature: Tm
  },
  tap: {
    Feature: ym
  },
  focus: {
    Feature: gm
  },
  hover: {
    Feature: mm
  }
}, Am = {
  layout: {
    ProjectionNode: Ll,
    MeasureLayout: Kl
  }
}, Pm = {
  ...Xp,
  ...Nm,
  ...pm,
  ...Am
}, Mm = /* @__PURE__ */ Gp(Pm, Kp);
function Hl(e) {
  const t = Ut(() => Le(e)), { isStatic: n } = re(Fn);
  if (n) {
    const [, i] = F(e);
    O(() => t.on("change", i), []);
  }
  return t;
}
function ql(e, t) {
  const n = Hl(t()), i = () => n.set(t());
  return i(), Rt(() => {
    const s = () => G.preRender(i, !1, !0), r = e.map((o) => o.on("change", s));
    return () => {
      r.forEach((o) => o()), Re(i);
    };
  }), n;
}
function Cm(e) {
  Pt.current = [], e();
  const t = ql(Pt.current, e);
  return Pt.current = void 0, t;
}
function Em(e, t, n, i) {
  if (typeof e == "function")
    return Cm(e);
  const r = typeof t == "function" ? t : fh(t, n, i), o = Array.isArray(e) ? ko(e, r) : ko([e], ([l]) => r(l)), a = Array.isArray(e) ? void 0 : e.accelerate;
  return a && !a.isTransformed && typeof t != "function" && Array.isArray(n) && i?.clamp !== !1 && (o.accelerate = {
    ...a,
    times: t,
    keyframes: n,
    isTransformed: !0
  }), o;
}
function ko(e, t) {
  const n = Ut(() => []);
  return ql(e, () => {
    n.length = 0;
    const i = e.length;
    for (let s = 0; s < i; s++)
      n[s] = e[s].get();
    return t(n);
  });
}
function J() {
  !Vs.current && ml();
  const [e] = F(Tn.current);
  return process.env.NODE_ENV !== "production" && En(e !== !0, "You have Reduced Motion enabled on your device. Animations may not appear as expected.", "reduced-motion-disabled"), e;
}
function Os(e) {
  return typeof e == "object" && !Array.isArray(e);
}
function Yl(e, t, n, i) {
  return e == null ? [] : typeof e == "string" && Os(t) ? Ts(e, n, i) : e instanceof NodeList ? Array.from(e) : Array.isArray(e) ? e.filter((s) => s != null) : [e];
}
function Dm(e, t, n) {
  return e * (t + 1) + n * t;
}
function To(e, t, n, i) {
  return typeof t == "number" ? t : t.startsWith("-") || t.startsWith("+") ? Math.max(0, e + parseFloat(t)) : t === "<" ? n : t.startsWith("<") ? Math.max(0, n + parseFloat(t.slice(1))) : i.get(t) ?? e;
}
function Vm(e, t, n) {
  for (let i = 0; i < e.length; i++) {
    const s = e[i];
    s.at > t && s.at < n && (Qe(e, s), i--);
  }
}
function Rm(e, t, n, i, s, r) {
  Vm(e, s, r);
  for (let o = 0; o < t.length; o++)
    e.push({
      value: t[o],
      at: q(s, r, i[o]),
      easing: /* @__PURE__ */ ma(n, o)
    });
}
function Lm(e, t, n = 0) {
  const i = t + 1 + t * n;
  for (let s = 0; s < e.length; s++)
    e[s] = e[s] / i;
}
function Fm(e, t) {
  return e.at === t.at ? e.value === null ? 1 : t.value === null ? -1 : 0 : e.at - t.at;
}
const Om = "easeInOut", si = 20;
function Im(e, { defaultTransition: t = {}, ...n } = {}, i, s) {
  const r = t.duration || 0.3, o = /* @__PURE__ */ new Map(), a = /* @__PURE__ */ new Map(), l = {}, u = /* @__PURE__ */ new Map();
  let d = 0, h = 0, f = 0;
  for (let p = 0; p < e.length; p++) {
    const g = e[p];
    if (typeof g == "string") {
      u.set(g, h);
      continue;
    } else if (!Array.isArray(g)) {
      u.set(g.name, To(h, g.at, d, u));
      continue;
    }
    let [v, b, w = {}] = g;
    w.at !== void 0 && (h = To(h, w.at, d, u));
    let T = 0;
    const y = (N, V, C, k = 0, m = 0) => {
      const S = Bm(N), { delay: A = 0, times: L = Ra(S), type: j = t.type || "keyframes", repeat: I, repeatType: M, repeatDelay: se = 0, ...ve } = V;
      let { ease: Z = t.ease || "easeOut", duration: U } = V;
      const H = typeof A == "function" ? A(k, m) : A, K = S.length, oe = ys(j) ? j : s?.[j || "keyframes"];
      if (K <= 2 && oe) {
        let be = 100;
        if (K === 2 && Um(S)) {
          const xt = S[1] - S[0];
          be = Math.abs(xt);
        }
        const ze = {
          ...t,
          ...ve
        };
        U !== void 0 && (ze.duration = /* @__PURE__ */ pe(U));
        const We = Ma(ze, be, oe);
        Z = We.ease, U = We.duration;
      }
      U ?? (U = r);
      const D = h + H;
      L.length === 1 && L[0] === 0 && (L[1] = 1);
      const W = L.length - S.length;
      if (W > 0 && Va(L, W), S.length === 1 && S.unshift(null), I && et(I < si, `Sequence segments can't repeat ${I} times — ignoring repeat option. Use a value below ${si} or apply repeat at the sequence level instead.`), I && I < si) {
        const be = U > 0 ? se / U : 0;
        U = Dm(U, I, se);
        const ze = [...S], We = [...L];
        Z = Array.isArray(Z) ? [...Z] : [Z];
        const xt = [...Z], zs = M === "reverse" || M === "mirror";
        let Ws = ze, _s = xt;
        zs && (Ws = [...ze].reverse(), M === "reverse" && (_s = [...xt].reverse().map((Ie) => typeof Ie == "function" ? /* @__PURE__ */ is(Ie) : Ie)));
        for (let Ie = 0; Ie < I; Ie++) {
          const Gs = zs && Ie % 2 === 0, Ks = Gs ? Ws : ze, Ac = Gs ? _s : xt, Hs = (Ie + 1) * (1 + be);
          be > 0 && (S.push(S[S.length - 1]), L.push(Hs), Z.push("linear")), S.push(...Ks);
          for (let vt = 0; vt < Ks.length; vt++)
            L.push(We[vt] + Hs), Z.push(vt === 0 ? "linear" : /* @__PURE__ */ ma(Ac, vt - 1));
        }
        Lm(L, I, be);
      }
      const ce = D + U;
      Rm(C, S, Z, L, D, ce), T = Math.max(H + U, T), f = Math.max(ce, f);
    };
    if (ie(v)) {
      const N = So(v, a);
      y(b, w, No("default", N));
    } else {
      const N = Yl(v, b, i, l), V = N.length;
      for (let C = 0; C < V; C++) {
        b = b, w = w;
        const k = N[C], m = So(k, a);
        for (const S in b)
          y(b[S], $m(w, S), No(S, m), C, V);
      }
    }
    d = h, h += T;
  }
  return a.forEach((p, g) => {
    for (const v in p) {
      const b = p[v];
      b.sort(Fm);
      const w = [], T = [], y = [];
      for (let k = 0; k < b.length; k++) {
        const { at: m, value: S, easing: A } = b[k];
        w.push(S), T.push(/* @__PURE__ */ ft(0, f, m)), y.push(A || "easeOut");
      }
      T[0] !== 0 && (T.unshift(0), w.unshift(w[0]), y.unshift(Om)), T[T.length - 1] !== 1 && (T.push(1), w.push(null)), o.has(g) || o.set(g, {
        keyframes: {},
        transition: {}
      });
      const N = o.get(g);
      N.keyframes[v] = w;
      const { type: V, ...C } = t;
      N.transition[v] = {
        ...C,
        duration: f,
        ease: y,
        times: T,
        ...n
      };
    }
  }), o;
}
function So(e, t) {
  return !t.has(e) && t.set(e, {}), t.get(e);
}
function No(e, t) {
  return t[e] || (t[e] = []), t[e];
}
function Bm(e) {
  return Array.isArray(e) ? e : [e];
}
function $m(e, t) {
  return e && e[t] ? {
    ...e,
    ...e[t]
  } : { ...e };
}
const jm = (e) => typeof e == "number", Um = (e) => e.every(jm);
function zm(e, t) {
  return ie(e) || typeof e == "number" || typeof e == "string" && !Os(t);
}
function Xl(e, t, n, i) {
  const s = [];
  if (zm(e, t))
    s.push(El(e, Os(t) && t.default || t, n && (n.default || n)));
  else {
    if (e == null)
      return s;
    const r = Yl(e, t, i), o = r.length;
    xe(!!o, "No valid elements provided.", "no-valid-elements");
    for (let a = 0; a < o; a++) {
      const l = r[a], u = { ...n };
      "delay" in u && typeof u.delay == "function" && (u.delay = u.delay(a, o)), l instanceof Element ? s.push(...Kf(l, t, u, hl.get(l))) : s.push(...nl(bf(l) ?? Hf, l, t, u));
    }
  }
  return s;
}
function Wm(e, t, n) {
  const i = [], s = e.map((o) => {
    if (Array.isArray(o) && typeof o[0] == "function") {
      const a = o[0], l = Le(0);
      return l.on("change", a), o.length === 1 ? [l, [0, 1]] : o.length === 2 ? [l, [0, 1], o[1]] : [l, o[1], o[2]];
    }
    return o;
  });
  return Im(s, t, n, { spring: Ot }).forEach(({ keyframes: o, transition: a }, l) => {
    i.push(...Xl(l, o, a));
  }), i;
}
function _m(e) {
  return Array.isArray(e) && e.some(Array.isArray);
}
function Gm(e = {}) {
  const { scope: t, reduceMotion: n, skipAnimations: i } = e;
  function s(r, o, a) {
    let l = [], u;
    const d = {};
    if (n !== void 0 && (d.reduceMotion = n), i !== void 0 && (d.skipAnimations = i), _m(r)) {
      const { onComplete: f, ...p } = o || {};
      typeof f == "function" && (u = f), l = Wm(r, { ...d, ...p }, t);
    } else {
      const { onComplete: f, ...p } = a || {};
      typeof f == "function" && (u = f), l = Xl(r, o, { ...d, ...p }, t);
    }
    const h = new Gd(l);
    return u && h.finished.then(u), t && (t.animations.push(h), h.finished.then(() => {
      Qe(t.animations, h);
    })), h;
  }
  return s;
}
const ri = Object.assign(Gm(), {
  /**
   * Register an effect so `animate()` can animate the subjects it
   * claims, for instance `animate.addEffect(threeEffect)`. The most
   * recently added effect is tested first. DOM elements are always
   * animated directly.
   */
  addEffect: vf,
  removeEffect: el
}), B = Mm;
function $t(e) {
  return `REV ${String(Math.max(0, e ?? 0)).padStart(2, "0")}`;
}
function Ay(e, t) {
  if (!e) return null;
  const n = e.replace(/^claude-/, "");
  return t ? `${n} ${t}` : n;
}
function Zl(e) {
  if (e == null) return null;
  const t = Math.max(0, Math.round(e));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function qt(e) {
  const t = Math.max(0, e);
  return t < 59.95 ? `${t.toFixed(1)}s` : Zl(t);
}
function Km(e, t = Date.now()) {
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
function Hm(e) {
  return !e || e.length !== 3 ? null : e.map((t) => Math.round(t * 10) / 10).join(" × ");
}
function Py(e) {
  if (!e) return "·";
  if (e.includes("@")) return e.split("@")[0].slice(0, 2).toUpperCase();
  const t = e.trim().split(/\s+/);
  return (t.length > 1 ? t[0][0] + t[1][0] : t[0].slice(0, 2)).toUpperCase();
}
function Pn(e) {
  const t = e.replace(/_+/g, " ").trim();
  return t.charAt(0).toUpperCase() + t.slice(1);
}
const qm = typeof window > "u" ? O : mt, Ym = X.out;
function Is(e) {
  const t = P(null), [n, i] = F(0), [s, r] = F(!1), [o, a] = F(e), l = P(e);
  l.current !== e && (l.current = e, o && a(!1)), qm(() => {
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
  const u = J();
  return {
    ref: t,
    height: n,
    animate: { height: e ? o || !s ? "auto" : n : 0 },
    transition: { duration: u ? 0 : z.settle, ease: Ym },
    onAnimationComplete: () => {
      e && a(!0);
    },
    style: { overflow: "hidden" }
  };
}
const Xm = {
  done: "check",
  failed: "warning",
  running: "ruler"
};
function Mn(e, t) {
  return e.status !== "running" ? e.elapsed_s ?? 0 : Math.max(0, (t - new Date(e.started_at).getTime()) / 1e3);
}
function Zm({ startedAt: e, className: t }) {
  const [n, i] = F(() => Date.now());
  O(() => {
    const r = setInterval(() => i(Date.now()), 100);
    return () => clearInterval(r);
  }, []);
  const s = Math.max(0, (n - new Date(e).getTime()) / 1e3);
  return /* @__PURE__ */ c("span", { "aria-hidden": "true", className: t, children: qt(s) });
}
function Ql({ open: e }) {
  const t = J() === !0;
  return /* @__PURE__ */ c(
    B.span,
    {
      "aria-hidden": "true",
      className: "flex shrink-0 items-center text-faint",
      animate: { rotate: e ? 0 : -90 },
      transition: { duration: t ? 0 : z.tick, ease: X.out },
      children: /* @__PURE__ */ c($, { name: "chevron-down" })
    }
  );
}
function Jl({ open: e, id: t, className: n, children: i }) {
  const s = Is(e);
  return /* @__PURE__ */ c(B.div, { id: t, style: s.style, animate: s.animate, transition: s.transition, onAnimationComplete: s.onAnimationComplete, children: /* @__PURE__ */ c("div", { ref: s.ref, className: n, children: e ? i : null }) });
}
function Qm(e) {
  const t = `${e.verb.charAt(0).toUpperCase()}${e.verb.slice(1)} ${e.object}`;
  if (e.status === "running")
    return `${t}, running for ${Math.round(Mn(e, Date.now()))} seconds`;
  const n = Mn(e, Date.now()).toFixed(1);
  return `${t}, ${e.status === "failed" ? "failed after" : "finished in"} ${n} seconds`;
}
function ec({ step: e, defaultOpen: t }) {
  const [n, i] = F(t ?? e.status === "failed");
  O(() => {
    e.status === "failed" && i(!0);
  }, [e.status]);
  const s = we(), r = e.status === "running", o = e.status === "failed", a = e.input == null ? null : JSON.stringify(e.input, null, 2), l = e.output?.trim() ? e.output : null, u = a != null || l != null;
  return /* @__PURE__ */ x("div", { className: "flex flex-col", children: [
    /* @__PURE__ */ x(
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
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: R("flex shrink-0 items-center", o ? "text-fail" : "text-ink-soft"), children: /* @__PURE__ */ c($, { name: Xm[e.status] }) }),
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: R("mono-label shrink-0", o ? "text-fail" : "text-muted"), children: e.verb.toUpperCase() }),
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "min-w-0 flex-1 truncate text-[13px] leading-[19px] text-ink-soft", children: e.object }),
          r ? /* @__PURE__ */ c(Zm, { startedAt: e.started_at, className: "mono-value min-w-[44px] shrink-0 text-right tabular-nums text-accent-ink" }) : /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "mono-value min-w-[44px] shrink-0 text-right tabular-nums text-faint", children: qt(Mn(e, Date.now())) }),
          u ? /* @__PURE__ */ c(Ql, { open: n }) : null,
          /* @__PURE__ */ c("span", { className: "sr-only", children: Qm(e) })
        ]
      }
    ),
    /* @__PURE__ */ x(Jl, { open: n && u, id: s, className: "relative flex flex-col gap-1.5 pt-1.5 pr-2 pb-2.5 pl-7", children: [
      /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "absolute top-0 bottom-0 left-[13px] w-px bg-line-soft" }),
      a ? /* @__PURE__ */ x("div", { className: "flex flex-col gap-1", children: [
        /* @__PURE__ */ c("span", { className: "mono-label text-muted", children: "INPUT" }),
        /* @__PURE__ */ c("pre", { className: "max-h-[216px] overflow-y-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap text-ink-soft", children: a })
      ] }) : null,
      l ? /* @__PURE__ */ x("div", { className: "flex flex-col gap-1", children: [
        /* @__PURE__ */ c("span", { className: "mono-label text-muted", children: "OUTPUT" }),
        /* @__PURE__ */ c("pre", { className: "max-h-[216px] overflow-y-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap text-ink-soft", children: l })
      ] }) : null
    ] })
  ] });
}
function Jm(e) {
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
function eg({ steps: e, defaultCollapsed: t }) {
  const [n, i] = F(!t), s = we();
  O(() => {
    t && i(!1);
  }, [t]);
  const r = e.reduce((o, a) => o + Mn(a, Date.now()), 0);
  return /* @__PURE__ */ x("div", { className: "flex flex-col", children: [
    /* @__PURE__ */ x(
      "button",
      {
        type: "button",
        onClick: () => i((o) => !o),
        "aria-expanded": n,
        "aria-controls": s,
        className: "flex min-h-[28px] items-center gap-2 self-start rounded-[3px] px-2 hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
        children: [
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "flex shrink-0 items-center text-ink-soft", children: /* @__PURE__ */ c($, { name: "dots" }) }),
          /* @__PURE__ */ x("span", { className: "mono-label text-muted", children: [
            e.length,
            " STEPS"
          ] }),
          /* @__PURE__ */ x("span", { className: "mono-value text-faint", children: [
            /* @__PURE__ */ c("span", { "aria-hidden": "true", children: "· " }),
            qt(r)
          ] }),
          /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "ml-1.5 flex items-center", children: /* @__PURE__ */ c(Ql, { open: n }) })
        ]
      }
    ),
    /* @__PURE__ */ c(Jl, { open: n, id: s, className: "flex flex-col gap-[2px]", children: e.map((o) => /* @__PURE__ */ c(ec, { step: o }, o.id)) })
  ] });
}
function tg({ steps: e, defaultCollapsed: t = !0 }) {
  return /* @__PURE__ */ c("div", { className: "flex flex-col gap-[2px]", children: Jm(e).map(
    (n) => n.kind === "group" ? /* @__PURE__ */ c(eg, { steps: n.steps, defaultCollapsed: t }, n.steps[0].id) : /* @__PURE__ */ c(ec, { step: n.step }, n.step.id)
  ) });
}
function ng({ findings: e, passed: t }) {
  const n = e.filter((r) => r.severity === "fail"), i = e.filter((r) => r.severity === "warn"), s = t ? i : [...n, ...i];
  return /* @__PURE__ */ x("ul", { className: "flex flex-col gap-[5px]", role: "list", children: [
    t ? /* @__PURE__ */ x("li", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ c("span", { className: "text-pass", children: /* @__PURE__ */ c($, { name: "check" }) }),
      /* @__PURE__ */ c("span", { className: "mono-id text-ink-soft uppercase [letter-spacing:0.06em]", children: "Checks pass" })
    ] }) : n.length > 0 ? /* @__PURE__ */ x("li", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ c("span", { className: "text-fail", children: /* @__PURE__ */ c($, { name: "xmark" }) }),
      /* @__PURE__ */ x("span", { className: "mono-id text-ink-soft uppercase [letter-spacing:0.06em]", children: [
        n.length,
        " check",
        n.length === 1 ? "" : "s",
        " failed"
      ] })
    ] }) : null,
    s.map((r, o) => /* @__PURE__ */ x("li", { className: "flex items-baseline gap-2", children: [
      /* @__PURE__ */ c("span", { className: R("flex h-[14px] items-center", r.severity === "fail" ? "text-fail" : "text-warn"), children: /* @__PURE__ */ c($, { name: "warning" }) }),
      /* @__PURE__ */ c("span", { className: "mono-id shrink-0 text-ink-soft uppercase [letter-spacing:0.06em]", children: r.label || r.rule }),
      /* @__PURE__ */ c("span", { className: "min-w-0 text-xs leading-[14px] text-muted", children: r.message })
    ] }, `${r.rule}-${o}`))
  ] });
}
function ig({ startedAt: e }) {
  const [t, n] = F(() => Date.now());
  return O(() => {
    const i = setInterval(() => n(Date.now()), 100);
    return () => clearInterval(i);
  }, []), /* @__PURE__ */ c(_, { children: qt(Math.max(0, (t - new Date(e).getTime()) / 1e3)) });
}
function My({ build: e, collapsed: t }) {
  const n = e.status === "running", i = e.status === "passed", s = n ? "Building" : i ? "Built" : "Failed", r = e.status === "error" ? e.error?.trim().split(`
`).pop() || "Something broke on my end." : null, o = [
    e.revision != null ? $t(e.revision) : null,
    n ? /* @__PURE__ */ c(ig, { startedAt: e.started_at }, "clock") : e.elapsed_s != null ? Zl(e.elapsed_s) : null
  ].filter((a) => a != null);
  return /* @__PURE__ */ x("div", { className: "flex flex-col overflow-hidden rounded-[6px] border border-line", children: [
    /* @__PURE__ */ x("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3", children: [
      /* @__PURE__ */ x("span", { className: "mono-label flex items-center gap-2 text-ink", children: [
        i ? /* @__PURE__ */ c("span", { className: "text-pass", children: /* @__PURE__ */ c($, { name: "check" }) }) : n ? null : /* @__PURE__ */ c("span", { className: "text-fail", children: /* @__PURE__ */ c($, { name: "xmark" }) }),
        s
      ] }),
      /* @__PURE__ */ c("span", { className: "mono-caption text-muted [letter-spacing:0.06em]", children: o.map((a, l) => /* @__PURE__ */ x("span", { children: [
        l > 0 ? " · " : "",
        a
      ] }, l)) })
    ] }),
    /* @__PURE__ */ x("div", { className: "flex flex-col gap-[9px] px-3 pt-2.5 pb-3", children: [
      e.steps.length > 0 ? /* @__PURE__ */ c(tg, { steps: e.steps, defaultCollapsed: t ?? i }) : null,
      !n && e.render_url ? /* @__PURE__ */ c(
        "img",
        {
          src: e.render_url,
          alt: `${e.part_name} from four sides`,
          className: "w-full rounded-[4px] border border-line-soft bg-raised"
        }
      ) : null,
      !n && e.findings.length > 0 ? /* @__PURE__ */ c(ng, { findings: e.findings, passed: i }) : null,
      r ? /* @__PURE__ */ c("p", { className: "text-[13px] leading-[19px] text-ink-soft", children: r }) : null
    ] })
  ] });
}
const sg = ["img"], rg = {
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
function Cy({ content: e, streaming: t = !1 }) {
  return /* @__PURE__ */ c("div", { className: R(t && "md-streaming"), children: /* @__PURE__ */ c(
    Dc,
    {
      skipHtml: !0,
      disallowedElements: sg,
      components: rg,
      children: e
    }
  ) });
}
const og = {
  standard: "Published",
  measured: "You measured",
  asked: "You told us",
  doctrine: "Rule of thumb"
};
function ag(e) {
  if (e.source) return e.source;
  const t = e.how.toLowerCase();
  return /\b(caliper|measured|ruler|tape)\b/.test(t) ? "measured" : /\b(user|stated|asked|said|told)\b/.test(t) ? "asked" : /\b(standard|spec|published|listing|datasheet|nominal)\b/.test(t) ? "standard" : "doctrine";
}
function Ao({ children: e }) {
  return /* @__PURE__ */ x("div", { className: "flex items-center gap-2", children: [
    /* @__PURE__ */ c("span", { className: "mono-caption shrink-0 text-faint [letter-spacing:0.12em]", children: e }),
    /* @__PURE__ */ c("span", { className: "h-px flex-1 bg-line-soft" })
  ] });
}
function Ey({ spec: e }) {
  return /* @__PURE__ */ x("div", { className: "flex flex-col overflow-hidden rounded-[6px] border border-line", children: [
    /* @__PURE__ */ c("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3", children: /* @__PURE__ */ x("span", { className: "mono-label flex items-center gap-2 text-ink", children: [
      /* @__PURE__ */ c($, { name: "lock" }),
      "The plan"
    ] }) }),
    /* @__PURE__ */ x("div", { className: "flex flex-col gap-3 px-3 pt-[11px] pb-3", children: [
      /* @__PURE__ */ c("p", { className: "text-[13px] leading-[19px] text-pretty text-ink-soft", children: e.summary }),
      /* @__PURE__ */ c("dl", { className: "flex flex-col gap-[5px]", children: e.dimensions.map((t) => {
        const n = ag(t);
        return /* @__PURE__ */ x(
          "div",
          {
            className: "flex items-baseline gap-2",
            title: t.provisional ? `${t.how} · a best guess until it is measured` : t.how,
            children: [
              /* @__PURE__ */ c("dt", { className: "min-w-0 flex-1 truncate text-xs leading-4 text-ink-soft", children: Pn(t.name) }),
              /* @__PURE__ */ x("dd", { className: "mono-value text-ink", children: [
                t.provisional ? "~" : "",
                t.value_mm,
                " mm"
              ] }),
              /* @__PURE__ */ c("dd", { className: n === "measured" ? "mono-caption w-24 shrink-0 text-right text-accent-ink [letter-spacing:0.06em]" : "mono-caption w-24 shrink-0 text-right text-muted [letter-spacing:0.06em]", children: og[n] })
            ]
          },
          t.name
        );
      }) }),
      e.acceptance.length > 0 ? /* @__PURE__ */ x("div", { className: "flex flex-col gap-1.5", children: [
        /* @__PURE__ */ c(Ao, { children: "Done when" }),
        /* @__PURE__ */ c("ul", { className: "flex list-disc flex-col gap-1 pl-4 marker:text-faint", role: "list", children: e.acceptance.map((t, n) => /* @__PURE__ */ c("li", { className: "text-xs leading-4 text-pretty text-ink-soft", children: t.criterion }, n)) })
      ] }) : null,
      e.params.length > 0 ? /* @__PURE__ */ x("div", { className: "flex flex-col gap-1.5", children: [
        /* @__PURE__ */ c(Ao, { children: `${e.params.length} slider${e.params.length === 1 ? "" : "s"} to adjust` }),
        /* @__PURE__ */ c("ul", { className: "flex flex-wrap gap-1", role: "list", children: e.params.map((t) => /* @__PURE__ */ c("li", { className: "rounded-control bg-raised px-1.5 py-0.5 text-xs leading-4 text-ink-soft", title: t.description, children: Pn(t.name) }, t.name)) })
      ] }) : null
    ] })
  ] });
}
function lg(e) {
  return e.previous_value_mm != null && e.previous_value_mm !== e.value_mm;
}
function Dy({
  measurement: e,
  staleParts: t,
  onAccept: n,
  onEdit: i,
  onRebuild: s,
  rebuilding: r
}) {
  const o = e.stale_parts ?? [], a = t ? o.filter((d) => t.includes(d)) : o, l = lg(e), u = e.provisional && n;
  return /* @__PURE__ */ x("div", { className: "flex flex-col overflow-hidden rounded-[6px] border border-line", children: [
    /* @__PURE__ */ x("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3", children: [
      /* @__PURE__ */ x("span", { className: "mono-label flex items-center gap-2 text-ink", children: [
        /* @__PURE__ */ c($, { name: "ruler" }),
        l ? "Measurement changed" : "Measurement recorded"
      ] }),
      e.provisional ? /* @__PURE__ */ c("span", { className: "mono-caption text-warn [letter-spacing:0.1em]", children: "Provisional" }) : null
    ] }),
    /* @__PURE__ */ x("div", { className: "flex flex-col gap-1.5 px-3 pt-[9px] pb-2.5", children: [
      /* @__PURE__ */ x("div", { className: "flex items-baseline gap-2", children: [
        /* @__PURE__ */ c("span", { className: "min-w-0 flex-1 truncate text-xs leading-4 text-ink-soft", children: Pn(e.name) }),
        l ? /* @__PURE__ */ x("span", { className: "mono-value text-muted line-through", children: [
          e.previous_value_mm,
          " mm"
        ] }) : null,
        /* @__PURE__ */ x("span", { className: "mono-value text-ink", children: [
          e.value_mm,
          " mm"
        ] })
      ] }),
      /* @__PURE__ */ c("p", { className: "text-xs leading-4 text-muted", children: e.how }),
      u || i ? /* @__PURE__ */ x("div", { className: "mt-0.5 flex items-center gap-1.5", children: [
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
      a.length > 0 ? /* @__PURE__ */ x("div", { className: "mt-1 flex items-center gap-2 rounded-[6px] bg-warn-wash px-2.5 py-1.5", children: [
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
const ge = {
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
}, cg = { fail: 0.4, warn: 0.38 }, ug = 0.62, dg = 25, tc = (e, t) => e === "fail" ? t.fail : t.warn;
function fg() {
  const e = new Vc(16777215, 6);
  e.position.set(0.4, -0.9, 2.9);
  const t = new Rc(16777215, ge.gridMajor, 1);
  return t.position.set(0, 0, 1), [t, e];
}
const tn = (e, t) => {
  const n = new Gi();
  return n.setAttribute("position", new Ki(new Float32Array(e), 3)), new _i(n, t);
};
function hg([e, t], n = 10) {
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
  ], h = new mn();
  return h.add(
    tn(a, new st({ color: ge.gridMinor })),
    tn(l, new st({ color: ge.gridMajor })),
    tn(d, new st({ color: ge.gridBorder })),
    tn(u, new st({ color: ge.accent, transparent: !0, opacity: 0.35 }))
  ), h;
}
const nn = 1.2;
function pg(e) {
  const t = new Je(
    new zc(1, nn, nn),
    new Dt({ color: ge.accent, transparent: !0, opacity: 0.9 })
  );
  return t.position.set(0, -e / 2 + nn * 2, nn / 2), t;
}
const nc = (e) => {
  const t = e.getSize(new he());
  return Math.max(t.x, t.y, t.z) || 10;
};
function mg(e, t, n) {
  const i = n.getCenter(new he()), s = nc(n), r = s / (2 * Math.tan(e.fov * Math.PI / 180 / 2)) * 2.1, o = [0.7, -0.75, 0.6];
  e.up.set(0, 0, 1), e.position.set(i.x + r * o[0], i.y + r * o[1], i.z + r * o[2]), t.target.copy(i), e.near = s / 100, e.far = s * 100, e.updateProjectionMatrix(), t.update();
}
function ic(e, t, n) {
  const i = nc(n), s = e.distanceTo(t);
  return !n.containsPoint(e) && n.clone().expandByScalar(i * 2).containsPoint(t) && s > i / 100 && s < i * 50;
}
function sc(e, t) {
  return e.updateMatrixWorld(), new jc().setFromProjectionMatrix(
    new Uc().multiplyMatrices(e.projectionMatrix, e.matrixWorldInverse)
  ).intersectsBox(t);
}
function gg(e, t, n) {
  const i = [];
  e.traverse((r) => {
    r.isMesh && i.push(r);
  });
  const s = new mn();
  for (const r of i) {
    const o = r.geometry;
    o.attributes.normal || o.computeVertexNormals();
    const a = new zi({
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
    const l = new Je(o, a);
    for (const u of [].concat(r.material)) u.dispose();
    if (l.name = r.name || r.parent?.name || "", l.name === "context")
      a.color.setHex(n.context), a.transparent = !0, a.opacity = 0.3;
    else {
      const u = new _i(
        new ea(o, dg),
        new st({ color: n.edge, transparent: !0, opacity: 0.35, clippingPlanes: [t] })
      );
      l.add(u);
    }
    s.add(l);
  }
  return s;
}
const rc = (e) => e.children.filter((t) => t.isMesh && t.name !== "context" && t.name !== "target");
function yg(e) {
  e.position.set(0, 0, 0), e.updateMatrixWorld(!0);
  const t = new Vt();
  for (const o of e.children) o.name !== "target" && t.expandByObject(o);
  const n = new Vt();
  for (const o of rc(e)) n.expandByObject(o);
  n.isEmpty() && n.copy(t);
  const i = n.getCenter(new he()), s = new he(-i.x, -i.y, -n.min.z), r = e.parent ? e.parent.getWorldQuaternion(new qs()) : new qs();
  return e.position.copy(s).applyQuaternion(r.invert()), e.updateMatrixWorld(!0), t.translate(s);
}
function xg(e) {
  const t = new Vt();
  for (const n of rc(e)) t.expandByObject(n);
  return t;
}
const Po = {
  depthWrite: !1,
  depthTest: !1,
  colorWrite: !1,
  stencilWrite: !0,
  stencilFunc: Bc
};
function vg(e, t) {
  const n = new Dt({
    ...Po,
    clippingPlanes: [t],
    side: Ic,
    stencilFail: Bn,
    stencilZFail: Bn,
    stencilZPass: Bn
  }), i = new Dt({
    ...Po,
    clippingPlanes: [t],
    side: $c,
    stencilFail: $n,
    stencilZFail: $n,
    stencilZPass: $n
  });
  return [n, i].map((s) => {
    const r = new Je(e.geometry, s);
    return r.matrixAutoUpdate = !1, r.matrix = e.matrixWorld, r.renderOrder = 1, r;
  });
}
function bg() {
  const e = new Je(
    new Lc(1, 1),
    new zi({
      // Violet, because the cap is the one surface that is not part material and must not
      // impersonate a signal: amber is a warn, red a fail, orange the part itself.
      color: ge.cap,
      metalness: 0,
      roughness: 0.85,
      side: Wi,
      stencilWrite: !0,
      stencilRef: 0,
      stencilFunc: Fc,
      stencilFail: In,
      stencilZFail: In,
      stencilZPass: In
    })
  );
  return e.renderOrder = 1.1, e.visible = !1, e.onAfterRender = (t) => t.clearStencil(), e;
}
function wg(e, t, n, i) {
  const s = new Gi();
  s.setAttribute("position", new Ki(new Float32Array(e), 3));
  const r = new Dt({
    color: tc(t, i),
    transparent: !0,
    opacity: cg[t],
    side: Wi,
    polygonOffset: !0,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
    depthWrite: !1,
    clippingPlanes: [n]
  });
  return new Je(s, r);
}
function kg(e, t, n) {
  const i = new Gi();
  i.setAttribute("position", new Ki(new Float32Array(e), 3));
  const s = new _i(
    new ea(i, 1),
    new st({ color: n.accent, depthTest: !1, clippingPlanes: [t] })
  );
  return s.renderOrder = 998, i.dispose(), s;
}
function Tg(e, t, n, i) {
  const s = new Dt({ color: tc(t, i), depthTest: !1, depthWrite: !1 }), r = new Je(new Oc(1, 12, 8), s);
  return r.position.set(e[0], e[1], e[2]), r.scale.setScalar(n), r.renderOrder = 999, r;
}
const Sg = (e) => {
  for (const t of Array.isArray(e) ? e : [e]) t.dispose();
};
function fe(e) {
  e.traverse((t) => {
    const n = t;
    !n.geometry || t.name === "target" || (n.geometry.dispose(), Sg(n.material));
  });
}
const Oi = 1e6, Ng = { x: [1, 0, 0], y: [0, 1, 0], z: [0, 0, 1] }, Mo = 10, Ag = 42, Pg = 4e3, Mg = Math.PI / 12, Co = 1.8, Cg = 2, Eo = 0.9, Bs = () => {
  try {
    return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? !1;
  } catch {
    return !1;
  }
};
function oc(e, t) {
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
const Do = (e) => {
  const t = [];
  return e.traverse((n) => {
    const i = n.material;
    if (i)
      for (const s of Array.isArray(i) ? i : [i])
        t.push({ material: s, opacity: s.opacity, transparent: s.transparent, depthWrite: s.depthWrite });
  }), t;
}, Vo = (e) => {
  for (const t of e)
    t.material.opacity = t.opacity, t.material.transparent = t.transparent, t.material.depthWrite = t.depthWrite;
};
function Eg(e, t, n) {
  const i = n.now ?? (() => performance.now()), s = n.schedule ?? ((p) => requestAnimationFrame(() => p())), r = n.unschedule ?? ((p) => cancelAnimationFrame(p)), o = t ? Do(t) : [], a = e ? Do(e) : [];
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
    h = !1, Vo(o), n.onDone();
  };
  return d = s(f), () => {
    h && (h = !1, d && r(d), Vo(o));
  };
}
const Dg = (e, t) => !e || !t ? e === t : e.position.every((n, i) => n === t.position[i]) && e.target.every((n, i) => n === t.target[i]), Vg = (e) => {
  let t = null;
  return e.traverse((n) => {
    n.isMesh && !t && (t = n.geometry);
  }), t;
};
function ac(e, t, n) {
  if (!e.controls) return !1;
  const i = new he().fromArray(t.position), s = new he().fromArray(t.target);
  if (!ic(i, s, n)) return !1;
  e.camera.position.copy(i), e.controls.target.copy(s);
  const r = n.getSize(new he()), o = Math.max(r.x, r.y, r.z) || 10;
  return e.camera.near = o / 100, e.camera.far = o * 100, e.camera.updateProjectionMatrix(), e.controls.update(), sc(e.camera, n);
}
function Rg(e, t) {
  return !e.controls || !ic(e.camera.position, e.controls.target, t) ? !1 : sc(e.camera, t);
}
function Lg(e) {
  const t = e.controls;
  t && (t._sphericalDelta?.set(0, 0, 0), t._panOffset?.set(0, 0, 0), t._scale = 1);
}
function wt(e, t) {
  e.plate && (e.scene.remove(e.plate), fe(e.plate), e.plate = null);
  const n = t ?? Fg(e);
  e.plateSize = n, n && (e.plate = hg(n, e.pitch), e.scene.add(e.plate));
}
function Fg(e) {
  if (!e.part) return null;
  const t = new Vt().setFromObject(e.part).getSize(new he()), n = Math.max(100, Math.ceil(Math.max(t.x, t.y) * 1.8 / 50) * 50);
  return [n, n];
}
function Ro(e, t) {
  if (!e.part) return;
  e.box = yg(e.part), e.size = e.box.getSize(new he()).length(), e.quiet = !0, !(e.framed ? Rg(e, e.box) : t && ac(e, t, e.box)) && e.controls && mg(e.camera, e.controls, e.box), e.quiet = !1, e.framed = !0;
}
function Lo(e) {
  const t = e.fading;
  t && (e.fading = null, t.cancel(), e.root.remove(t.group), fe(t.group));
}
function Og(e) {
  const t = e.controls;
  if (!t || Bs()) return;
  e.nudgeRaf && cancelAnimationFrame(e.nudgeRaf);
  const n = t.target.clone(), i = e.camera.position.clone().sub(n), s = e.camera.up.clone().normalize(), r = performance.now(), o = z.coast * 1e3;
  e.quiet = !0;
  const a = () => {
    e.nudgeRaf = 0;
    const l = Math.min(1, (performance.now() - r) / o);
    l >= 1 && (e.quiet = !1), e.camera.position.copy(i).applyAxisAngle(s, Mg * oc(l, X.out)).add(n), t.update(), e.render(), l < 1 && (e.nudgeRaf = requestAnimationFrame(a));
  };
  e.nudgeRaf = requestAnimationFrame(a);
}
function lc(e) {
  e.purgeRaf && cancelAnimationFrame(e.purgeRaf), e.purgeRaf = 0, e.purge && (e.scene.remove(e.purge), fe(e.purge), e.purge = null);
}
function Ig(e) {
  if (!e.plate || !e.plateSize || Bs()) return !1;
  const [t, n] = e.plateSize, i = pg(n);
  e.purge = i, e.scene.add(i);
  const s = i.material, r = performance.now(), o = () => {
    e.purgeRaf = 0;
    const a = (performance.now() - r) / 1e3, l = Math.max(1e-3, t * oc(a / Co, X.out));
    i.scale.x = l, i.position.x = -t / 2 + l / 2;
    const u = a - Co - Cg;
    if (s.opacity = u <= 0 ? Eo : Eo * (1 - Math.min(1, u / z.settle)), e.render(), u < z.settle) {
      e.purgeRaf = requestAnimationFrame(o);
      return;
    }
    lc(e), e.render();
  };
  return e.purgeRaf = requestAnimationFrame(o), !0;
}
function Fo(e, t, n) {
  !t || n.current || (n.current = Ig(e));
}
function pn(e) {
  for (const t of e.writers)
    e.scene.remove(t), t.material.dispose();
  e.writers = [];
}
function Bg(e) {
  if (pn(e), !!e.part) {
    e.part.updateMatrixWorld(!0);
    for (const t of e.part.children)
      if (!(!t.isMesh || t.name === "context" || t.name === "target"))
        for (const n of vg(t, e.plane))
          n.visible = e.cutting, e.scene.add(n), e.writers.push(n);
  }
}
function kt(e, t) {
  if (!t) {
    e.cutting = !1, e.cutSign = 0, e.cap.visible = !1;
    for (const d of e.writers) d.visible = !1;
    e.plane.constant = Oi, e.render();
    return;
  }
  if ((!e.cutting || e.cutAxis !== t.axis) && (e.cutting = !0, e.cutAxis = t.axis, e.cutSign = 0), !e.part) {
    e.cap.visible = !1, e.plane.constant = Oi, e.render();
    return;
  }
  const n = xg(e.part), i = t.axis, s = n.min[i], r = n.max[i];
  e.cutSign || (e.cutSign = e.camera.position[i] >= (s + r) / 2 ? 1 : -1);
  const o = e.cutSign === 1 ? t.t : 1 - t.t, a = s + (r - s) * (0.02 + 0.96 * o), l = Ng[i];
  e.plane.normal.set(-e.cutSign * l[0], -e.cutSign * l[1], -e.cutSign * l[2]), e.plane.constant = e.cutSign * a, e.cap.visible = !0;
  for (const d of e.writers) d.visible = !0;
  const u = n.getSize(new he()).length();
  e.cap.scale.set(u, u, 1), e.plane.projectPoint(n.getCenter(new he()), e.cap.position), e.cap.lookAt(
    e.cap.position.x - e.plane.normal.x,
    e.cap.position.y - e.plane.normal.y,
    e.cap.position.z - e.plane.normal.z
  ), e.render();
}
function Tt(e, t, n) {
  for (const r of e.marks.children) fe(r);
  if (e.marks.clear(), e.glows = [], !e.part) {
    e.render();
    return;
  }
  const i = e.part.position, s = Math.max(0.6, e.size / 90);
  t.forEach((r, o) => {
    if (r.face && r.face.length) {
      const l = wg(r.face, r.severity, e.plane, ge);
      l.position.copy(i), l.userData.finding = o, o === n && (l.material.opacity = ug, l.add(kg(r.face, e.plane, ge))), e.marks.add(l), e.glows.push(l);
    }
    if (!r.where) return;
    const a = Tg(
      [r.where[0] + i.x, r.where[1] + i.y, r.where[2] + i.z],
      r.severity,
      s,
      ge
    );
    e.marks.add(a);
  }), e.render();
}
function Vy(e) {
  const { glbUrl: t, targetUrl: n, targetOffset: i, findings: s, highlight: r, bed: o, up: a, section: l, camera: u, settleKey: d, purge: h, className: f } = e, [p, g] = F(!1), v = P(null), b = P(null), w = P(null), T = P(null), y = P(e);
  y.current = e;
  const N = P(!1);
  O(() => {
    const m = v.current;
    if (!m) return;
    const S = new Wc();
    S.background = new _c(ge.stage);
    const A = new Gc(45, 1, 0.1, 1e4);
    A.up.set(0, 0, 1);
    const L = new mn(), j = new mn();
    L.add(j), S.add(L);
    for (const K of fg()) S.add(K);
    const I = bg();
    S.add(I);
    const M = {
      renderer: null,
      scene: S,
      camera: A,
      controls: null,
      plane: new Kc(new he(0, 0, -1), Oi),
      root: L,
      marks: j,
      cap: I,
      part: null,
      fading: null,
      ghost: null,
      plate: null,
      plateSize: null,
      pitch: Mo,
      purge: null,
      writers: [],
      glows: [],
      box: new Vt(),
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
    b.current = M, m.__nurbViewer = M;
    try {
      M.renderer = new Hc({ antialias: !0, stencil: !0 });
    } catch {
      m.setAttribute("data-nogl", "");
    }
    const se = M.renderer?.domElement ?? null;
    M.renderer && se && (M.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)), M.renderer.localClippingEnabled = !0, se.className = "block h-full w-full", m.appendChild(se), M.controls = new Xc(A, se), M.controls.enableDamping = !0, M.controls.dampingFactor = 0.0533);
    const ve = () => {
      if (M.raf = 0, !M.renderer || !M.controls) return;
      const K = M.controls.update();
      K || Lg(M), M.renderer.render(S, A), K && M.render();
    };
    M.render = () => {
      !M.renderer || M.raf || (M.raf = requestAnimationFrame(ve));
    };
    const Z = (K, oe) => {
      const D = Math.floor(K), W = Math.floor(oe);
      !D || !W || D === M.lastW && W === M.lastH || (M.lastW = D, M.lastH = W, M.renderer?.setSize(D, W, !1), A.aspect = D / W, A.updateProjectionMatrix(), M.render());
    }, U = new ResizeObserver((K) => {
      const oe = K[K.length - 1].contentRect;
      Z(oe.width, oe.height);
    });
    U.observe(m), Z(m.clientWidth, m.clientHeight);
    const H = () => {
      M.render(), !M.quiet && (M.camTimer && clearTimeout(M.camTimer), M.camTimer = setTimeout(() => {
        const K = y.current.onCamera;
        !K || !M.controls || K({
          position: M.camera.position.toArray(),
          target: M.controls.target.toArray()
        });
      }, 250));
    };
    return M.controls?.addEventListener("change", H), () => {
      U.disconnect(), M.raf && cancelAnimationFrame(M.raf), M.nudgeRaf && cancelAnimationFrame(M.nudgeRaf), M.camTimer && clearTimeout(M.camTimer), M.generation++, M.targetGeneration++, M.controls?.removeEventListener("change", H), M.controls?.dispose(), pn(M), lc(M);
      for (const K of j.children) fe(K);
      Lo(M), M.part && fe(M.part), M.ghost && (M.ghost.geometry.dispose(), M.ghost.material.dispose()), M.plate && fe(M.plate), fe(I), M.renderer?.setAnimationLoop(null), M.renderer?.forceContextLoss(), M.renderer?.dispose(), se?.remove(), delete m.__nurbViewer, b.current = null;
    };
  }, []), O(() => {
    const m = b.current;
    if (!m || !m.controls) return;
    const S = ++m.generation;
    Lo(m);
    const A = () => {
      m.part && (m.root.remove(m.part), m.ghost && m.part.remove(m.ghost), fe(m.part), m.part = null);
    };
    if (!t) {
      A(), wt(m, y.current.bed), pn(m), Tt(m, [], null), kt(m, y.current.section);
      return;
    }
    new Ys().loadAsync(t).then((L) => {
      if (S !== m.generation) {
        fe(L.scene);
        return;
      }
      const j = gg(L.scene, m.plane, ge);
      if (m.loaded = S, !j.children.length) {
        A(), fe(j), pn(m), Tt(m, [], null), kt(m, y.current.section);
        return;
      }
      const I = m.part;
      I && m.ghost && I.remove(m.ghost), m.ghost && j.add(m.ghost), m.root.add(j), m.part = j, Ro(m, y.current.camera), wt(m, y.current.bed), Fo(m, y.current.purge, N), T.current = y.current.camera ?? null, Bg(m), kt(m, y.current.section), Tt(m, y.current.findings ?? [], y.current.highlight), I && Bs() ? (m.root.remove(I), fe(I)) : I && (m.fading = {
        group: I,
        cancel: Eg(I, j, {
          seconds: z.settle,
          render: m.render,
          onDone: () => {
            m.fading = null, m.root.remove(I), fe(I), m.render();
          }
        })
      }), m.render();
    }).catch((L) => {
      S === m.generation && console.warn(`ViewerIsland: could not load ${t}`, L);
    });
  }, [t]);
  const V = (i ?? [0, 0, 0]).join(",");
  O(() => {
    const m = b.current;
    if (!m || !m.controls) return;
    const S = ++m.targetGeneration;
    if (m.ghost && (m.ghost.parent?.remove(m.ghost), m.ghost.geometry.dispose(), m.ghost.material.dispose(), m.ghost = null), !n) {
      m.render();
      return;
    }
    new Ys().loadAsync(n).then((A) => {
      if (S !== m.targetGeneration) {
        fe(A.scene);
        return;
      }
      const L = Vg(A.scene);
      if (!L) return;
      L.attributes.normal || L.computeVertexNormals();
      const j = new Je(
        L,
        new zi({
          color: ge.ghost,
          metalness: 0,
          roughness: 0.9,
          transparent: !0,
          opacity: 0.3,
          depthWrite: !1,
          side: Wi,
          clippingPlanes: [m.plane]
        })
      );
      j.name = "target";
      const I = V.split(",").map(Number);
      j.position.set(I[0], I[1], I[2]), m.ghost = j, m.part?.add(j), m.render();
    }).catch(() => {
    });
  }, [n, V]), O(() => {
    const m = b.current;
    !m || m.loaded !== m.generation || Tt(m, s ?? [], r);
  }, [s, r]), O(() => {
    const m = b.current;
    m && (wt(m, o), m.render());
  }, [o?.[0], o?.[1], !o]);
  const C = P(d);
  O(() => {
    const m = b.current, S = C.current;
    C.current = d, !(!m || d === void 0 || d === S) && Og(m);
  }, [d]), O(() => {
    const m = b.current;
    m && Fo(m, h, N);
  }, [h, o?.[0], o?.[1]]), O(() => {
    let m = null;
    const S = () => {
      g(!0), m && clearTimeout(m), m = setTimeout(() => g(!1), Pg);
    };
    return window.addEventListener("nurb:gridfinity", S), () => {
      window.removeEventListener("nurb:gridfinity", S), m && clearTimeout(m);
    };
  }, []), O(() => {
    const m = b.current;
    m && (m.pitch = p ? Ag : Mo, wt(m, y.current.bed), m.render());
  }, [p]);
  const k = (a ?? [0, 0, 1]).join(",");
  return O(() => {
    const m = b.current;
    if (!m) return;
    const S = new he(...k.split(",").map(Number)).normalize();
    m.root.quaternion.setFromUnitVectors(S, new he(0, 0, 1)), m.root.updateMatrixWorld(!0), m.part && (Ro(m, y.current.camera), wt(m, y.current.bed), kt(m, y.current.section), Tt(m, y.current.findings ?? [], y.current.highlight)), m.render();
  }, [k]), O(() => {
    const m = b.current;
    m && kt(m, l);
  }, [l]), O(() => {
    const m = b.current;
    if (!m || !m.part || !u || Dg(u, T.current)) return;
    T.current = u, m.quiet = !0;
    const S = ac(m, u, m.box);
    m.quiet = !1, S && m.render();
  }, [u]), /* @__PURE__ */ c(
    "div",
    {
      ref: v,
      className: R("relative block h-full w-full", e.onPick && "cursor-crosshair", f),
      onPointerDown: (m) => {
        w.current = [m.clientX, m.clientY];
      },
      onPointerUp: (m) => {
        const S = w.current;
        w.current = null;
        const A = b.current, { onHighlight: L, onPick: j } = y.current;
        if (!S || !A || !L && !j || Math.hypot(m.clientX - S[0], m.clientY - S[1]) > 5) return;
        const I = m.currentTarget.getBoundingClientRect();
        if (!I.width || !I.height) return;
        const M = new qc(
          (m.clientX - I.left) / I.width * 2 - 1,
          -((m.clientY - I.top) / I.height) * 2 + 1
        ), se = new Yc();
        if (se.setFromCamera(M, A.camera), j) {
          const Z = (A.part?.children ?? []).filter((H) => H.isMesh && H.name !== "context"), U = se.intersectObjects(Z, !1).find((H) => !A.cutting || A.plane.distanceToPoint(H.point) >= 0);
          if (U?.face) {
            const H = U.object.worldToLocal(U.point.clone()), K = U.face.normal;
            j({ point: [H.x, H.y, H.z], normal: [K.x, K.y, K.z] });
          }
          return;
        }
        if (!L) return;
        const ve = se.intersectObjects(A.glows, !1).find((Z) => !A.cutting || A.plane.distanceToPoint(Z.point) >= 0);
        L(ve ? ve.object.userData.finding : null);
      },
      children: p && /* @__PURE__ */ c("div", { className: "mono-caption pointer-events-none absolute bottom-3 left-3 text-faint [letter-spacing:0.12em]", children: "GRID 42.0 MM" })
    }
  );
}
const $g = {
  accent: "bg-accent text-white hover:bg-accent-hover",
  ink: "bg-ink text-white hover:bg-ink-soft",
  outline: "border border-line bg-ground text-ink-soft hover:border-panel-edge hover:text-ink",
  ghost: "text-muted hover:bg-raised hover:text-ink",
  danger: "bg-fail text-white hover:bg-fail/90"
}, jg = {
  sm: "h-7 px-3",
  md: "h-9 px-3",
  lg: "h-10 px-4"
}, Ae = Ui(function({ variant: t = "outline", size: n = "sm", icon: i, trailingIcon: s, className: r, children: o, type: a = "button", ...l }, u) {
  return /* @__PURE__ */ x(
    "button",
    {
      ref: u,
      type: a,
      className: R(
        "chrome btn-label inline-flex shrink-0 items-center justify-center gap-2 rounded-[3px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50",
        $g[t],
        jg[n],
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
function $s({
  icon: e,
  label: t,
  active: n = !1,
  className: i,
  ...s
}) {
  return /* @__PURE__ */ x(
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
const Ug = X.out, zg = { duration: z.settle, ease: Ug }, Wg = { duration: 0 };
function _g({
  action: e,
  resetAfter: t = 1400
}) {
  const [n, i] = F("idle"), s = P("idle"), r = P(0), o = P(null), a = P(!0), l = P(e);
  l.current = e;
  const u = Y(() => {
    o.current && clearTimeout(o.current), o.current = null;
  }, []), d = Y(() => {
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
  return O(() => (a.current = !0, () => {
    a.current = !1, u();
  }), [u]), { status: n, run: d, pending: n === "pending" };
}
function Gg({ still: e }) {
  return /* @__PURE__ */ x(
    B.svg,
    {
      width: "11",
      height: "11",
      viewBox: "0 0 12 12",
      fill: "none",
      "aria-hidden": "true",
      className: "shrink-0",
      animate: e ? void 0 : { rotate: 360 },
      transition: e ? void 0 : { duration: z.coast * 0.6, repeat: 1 / 0, ease: "linear" },
      children: [
        /* @__PURE__ */ c("circle", { cx: "6", cy: "6", r: "4.5", stroke: "currentColor", strokeWidth: "1.5", strokeOpacity: "0.22" }),
        /* @__PURE__ */ c("path", { d: "M10.5 6A4.5 4.5 0 0 0 6 1.5", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
      ]
    }
  );
}
function Oo({ d: e, extra: t }) {
  return /* @__PURE__ */ x(
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
function Kg({
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
  const u = J(), { status: d, run: h, pending: f } = _g({ action: s, resetAfter: r }), p = u ? Wg : zg, g = [
    { key: "idle", text: e, color: void 0, icon: null },
    {
      key: "pending",
      text: t,
      color: "var(--color-muted)",
      icon: /* @__PURE__ */ c(Gg, { still: u === !0 || d !== "pending" })
    },
    {
      key: "success",
      text: n,
      color: "var(--color-pass)",
      icon: /* @__PURE__ */ c(Oo, { d: "M2.6 6.3 4.9 8.6 9.4 3.6" })
    },
    {
      key: "error",
      text: i,
      color: "var(--color-fail)",
      icon: /* @__PURE__ */ c(Oo, { d: "M6 2.9v3.5", extra: "M6 9.05h.01" })
    }
  ], v = g.find((b) => b.key === d) ?? g[0];
  return /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c(
      Ae,
      {
        variant: o,
        disabled: a,
        "aria-label": v.text,
        "aria-busy": f || void 0,
        "aria-disabled": f || void 0,
        className: l,
        onClick: () => {
          f || ($e("press"), h());
        },
        children: /* @__PURE__ */ c("span", { "aria-hidden": "true", className: "relative grid place-items-center", children: g.map((b) => /* @__PURE__ */ x(
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
function St(e) {
  return Math.round(e * 1e6) / 1e6;
}
function Hg({
  value: e,
  onValueChange: t,
  min: n,
  max: i,
  step: s,
  detents: r,
  pull: o
}) {
  const a = le(() => r.map((b) => typeof b == "number" ? { value: b } : b), [r]), l = o ?? (i - n) * 0.045, u = P(t);
  u.current = t;
  const d = le(() => a.findIndex((b) => St(b.value) === St(e)), [a, e]), h = P(d);
  h.current = d;
  const f = P(!1), p = Y(
    (b) => {
      let w = -1, T = l;
      for (let y = 0; y < a.length; y += 1) {
        const N = Math.abs(b - a[y].value);
        N <= T && (T = N, w = y);
      }
      return w >= 0 ? a[w].value : n + Math.round((b - n) / s) * s;
    },
    [l, a, n, s]
  ), g = Y(
    (b) => {
      const w = Number(b.target.value);
      if (!Number.isFinite(w)) return;
      const T = f.current;
      f.current = !1;
      const y = St(Math.min(i, Math.max(n, T ? w : p(w)))), N = a.findIndex((V) => St(V.value) === y);
      N >= 0 && N !== h.current && $e("tick"), y !== St(e) && u.current(y);
    },
    [a, i, n, p, e]
  ), v = Y((b) => {
    (b.key.startsWith("Arrow") || b.key === "PageUp" || b.key === "PageDown") && (f.current = !0);
  }, []);
  return { onChange: g, onKeyDown: v, activeDetent: d, detents: a, activeLabel: a[d]?.label };
}
function qg({
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
function Yg(e, t) {
  let n, i;
  if (e === 0 ? (n = 0, i = t ? 8 : 1) : e < 0 ? (n = e * 2, i = e / 2) : (n = e / 2, i = e * 2), t)
    return n = Math.floor(n), i = Math.ceil(i), e >= 1 && (n = Math.max(1, n)), i - n < 4 && (i = n + 4), { lo: n, hi: i, step: 1 };
  const s = Math.min(10 ** (Math.floor(Math.log10(i - n)) - 1), 10 ** -uc(e));
  return { lo: ht(Math.floor(n / s) * s, s), hi: ht(Math.ceil(i / s) * s, s), step: s };
}
function cc(e, t) {
  const n = Yg(e.default, t);
  return {
    lo: e.min ?? n.lo,
    hi: e.max ?? n.hi,
    step: e.step ?? n.step
  };
}
function uc(e) {
  const t = String(e), n = t.indexOf(".");
  return n === -1 || t.includes("e") ? 0 : Math.min(t.length - n - 1, 4);
}
function ht(e, t) {
  const n = Math.max(0, -Math.floor(Math.log10(t)));
  return +e.toFixed(n);
}
function Ii(e) {
  return e.kind === "bool" || e.kind === "int" || e.kind === "float";
}
function Xg(e, t) {
  const n = {};
  for (const i of e) {
    if (!Ii(i)) continue;
    const s = t[i.name];
    s === void 0 || s === i.default || (n[i.name] = s);
  }
  return n;
}
const Zg = /wall|thickness|lip|rim|shell/;
function Qg(e, t, n = 0.4, i = "default") {
  if (e.kind !== "float" || typeof e.default != "number") return [];
  const { lo: s, hi: r, step: o } = cc(e, !1), a = (d) => Number.isFinite(d) && d >= s && d <= r, l = [{ value: e.default, label: i }];
  for (const d of t ?? [])
    a(d.value_mm) && l.push({ value: d.value_mm, label: "measured" });
  if (Zg.test(e.name.toLowerCase()) && n > 0)
    for (let d = 2; d * n <= r; d += 1) {
      const h = ht(d * n, 1e-3);
      a(h) && l.push({ value: h, label: `${d} lines` });
    }
  const u = /* @__PURE__ */ new Map();
  for (const d of l) {
    const h = ht(d.value, o);
    u.has(h) || u.set(h, d);
  }
  return [...u.values()].sort((d, h) => d.value - h.value);
}
const Io = X.out, Bo = "mm", $o = 4, Jg = 60, jo = 6;
function tt(e, t, n) {
  return String(t ? Math.round(e) : ht(e, n));
}
function jt(e) {
  return e.replace(/_/g, " ");
}
function Uo({ children: e }) {
  return /* @__PURE__ */ x("div", { className: "chrome flex items-center gap-2 px-4 pt-[11px] pb-2", children: [
    /* @__PURE__ */ c("span", { className: "mono-caption text-faint [letter-spacing:0.12em]", children: e }),
    /* @__PURE__ */ c("span", { className: "h-px flex-1 bg-line-soft" })
  ] });
}
function dc({ param: e, onReset: t }) {
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
function e0({
  id: e,
  param: t,
  value: n,
  dirty: i,
  measurements: s,
  nozzle: r,
  restLabel: o,
  onValue: a
}) {
  const l = t.kind === "int", u = cc(t, l), d = Math.min(u.lo, n), h = Math.max(u.hi, n), f = l ? 1 : Math.min(u.step, 10 ** -uc(n)), [p, g] = F(() => tt(n, l, f)), v = P(!1);
  if (!v.current) {
    const D = tt(n, l, f);
    D !== p && g(D);
  }
  const b = J(), w = le(
    () => Qg(t, s, r, o),
    [t, s, r, o]
  ), T = Hg({
    value: n,
    onValueChange: a,
    min: d,
    max: h,
    step: f,
    detents: w,
    pull: (h - d) * 0.045
  }), [y, N] = F(null), [V, C] = F(0);
  O(() => {
    if (!y) return;
    C(y.end === "max" ? 3 : -3);
    const D = setTimeout(() => C(0), b ? 0 : z.tick * 1e3), W = setTimeout(() => N(null), 1200);
    return () => {
      clearTimeout(D), clearTimeout(W);
    };
  }, [y, b]);
  const k = (D) => N({ end: D }), m = (D) => {
    if (l) {
      a(Math.round(Number(D.target.value)));
      return;
    }
    T.onChange(D);
  }, S = P(!1), A = P(!1), L = (D) => {
    D.button === 0 && (S.current = !0, A.current = !1);
  }, j = (D) => {
    if (!S.current) return;
    const W = D.currentTarget.getBoundingClientRect(), ce = D.clientX > W.right + jo ? "max" : D.clientX < W.left - jo ? "min" : null;
    if (!ce) {
      A.current = !1;
      return;
    }
    A.current || (ce === "max" && n >= h ? (A.current = !0, k("max")) : ce === "min" && n <= d && (A.current = !0, k("min")));
  }, I = () => {
    S.current = !1, A.current = !1;
  }, M = (D) => {
    const W = D.key === "ArrowRight" || D.key === "ArrowUp" || D.key === "PageUp", ce = D.key === "ArrowLeft" || D.key === "ArrowDown" || D.key === "PageDown";
    W && n >= h ? k("max") : ce && n <= d && k("min"), T.onKeyDown(D);
  }, se = () => {
    v.current = !1;
    const D = Number(p), W = l ? Math.round(D) : D;
    if (p.trim() === "" || !Number.isFinite(D) || W === n) {
      g(tt(n, l, f));
      return;
    }
    a(W);
  }, ve = (D, W, ce) => {
    const be = l ? Math.round(D + W * ce) : ht(D + W * ce, ce);
    return be !== n && a(be), be;
  }, Z = P(null), U = P(0), H = (D) => {
    D.button === 0 && (Z.current = { x: D.clientX, from: n, step: f, scrubbing: !1 });
  }, K = (D) => {
    const W = Z.current;
    if (!W) return;
    const ce = D.clientX - W.x;
    if (!W.scrubbing) {
      if (Math.abs(ce) < $o) return;
      W.scrubbing = !0, D.currentTarget.setPointerCapture?.(D.pointerId);
    }
    const be = n;
    if (ve(W.from, Math.round(ce / $o), W.step) === be) return;
    const We = Date.now();
    We - U.current >= Jg && (U.current = We, $e("tick"));
  }, oe = (D) => {
    const W = Z.current;
    Z.current = null, W?.scrubbing && D.currentTarget.hasPointerCapture?.(D.pointerId) && D.currentTarget.releasePointerCapture(D.pointerId);
  };
  return /* @__PURE__ */ x("div", { className: "flex flex-col gap-1 px-4", children: [
    /* @__PURE__ */ x("div", { className: "flex items-baseline justify-between gap-2", children: [
      /* @__PURE__ */ x("div", { className: "flex min-w-0 items-center gap-1.5", children: [
        /* @__PURE__ */ c(
          "label",
          {
            htmlFor: e,
            title: t.description,
            className: R("mono-caption min-w-0 truncate", i ? "font-medium text-ink" : "text-muted"),
            children: jt(t.name)
          }
        ),
        i ? /* @__PURE__ */ c(dc, { param: t, onReset: () => a(t.default) }) : null
      ] }),
      /* @__PURE__ */ x("div", { className: "flex shrink-0 items-baseline gap-1.5", children: [
        T.activeLabel ? /* @__PURE__ */ c("span", { className: "mono-caption text-faint", children: T.activeLabel }) : null,
        /* @__PURE__ */ c(
          "input",
          {
            value: p,
            onChange: (D) => {
              v.current = !0, g(D.target.value);
            },
            onBlur: se,
            onPointerDown: H,
            onPointerMove: K,
            onPointerUp: oe,
            onPointerCancel: oe,
            onKeyDown: (D) => {
              if (D.key === "Enter" && se(), D.key === "Escape") {
                const W = Z.current;
                Z.current = null, v.current = !1, W?.scrubbing ? a(W.from) : g(tt(n, l, f));
              }
              (D.key === "ArrowUp" || D.key === "ArrowDown") && (D.preventDefault(), ve(n, (D.key === "ArrowUp" ? 1 : -1) * (D.shiftKey ? 10 : 1), f));
            },
            inputMode: l ? "numeric" : "decimal",
            "aria-label": `${t.name} value`,
            className: R(
              "mono-value w-16 cursor-ew-resize rounded-control border-0 bg-transparent p-0 text-right focus:bg-raised focus:outline-1 focus:outline-accent",
              i ? "text-accent-ink" : "text-ink"
            )
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ x(
      B.div,
      {
        className: "relative",
        animate: { x: V },
        transition: { duration: b ? 0 : z.tick, ease: Io },
        children: [
          /* @__PURE__ */ c(
            "input",
            {
              id: e,
              type: "range",
              min: d,
              max: h,
              step: f,
              value: n,
              onChange: m,
              onKeyDown: M,
              onPointerDown: L,
              onPointerMove: j,
              onPointerUp: I,
              onPointerCancel: I,
              onLostPointerCapture: I,
              "aria-label": jt(t.name),
              "aria-valuetext": `${n}`,
              className: "param-slider w-full",
              style: { "--pct": h === d ? 0 : (n - d) / (h - d) }
            }
          ),
          /* @__PURE__ */ c(qg, { detents: T.detents, min: d, max: h, activeDetent: T.activeDetent })
        ]
      }
    ),
    /* @__PURE__ */ c(de, { children: y ? /* @__PURE__ */ c(
      B.p,
      {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: b ? 0 : z.settle, ease: Io },
        className: "mono-caption text-accent-ink",
        children: y.end === "max" ? `${tt(h, l, f)} ${Bo} · widest this will go` : `${tt(d, l, f)} ${Bo} · thinnest this will go`
      }
    ) : null })
  ] });
}
function t0({
  id: e,
  param: t,
  value: n,
  dirty: i,
  onValue: s
}) {
  return /* @__PURE__ */ x("div", { className: "flex items-center gap-2 px-4 py-1", children: [
    /* @__PURE__ */ c(
      "label",
      {
        htmlFor: e,
        title: t.description,
        className: R("mono-caption min-w-0 truncate", i ? "font-medium text-ink" : "text-muted"),
        children: jt(t.name)
      }
    ),
    i ? /* @__PURE__ */ c(dc, { param: t, onReset: () => s(t.default) }) : null,
    /* @__PURE__ */ c("span", { className: "flex-1" }),
    /* @__PURE__ */ c(
      "button",
      {
        id: e,
        type: "button",
        role: "switch",
        "aria-checked": n,
        "aria-label": jt(t.name),
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
function Ry({
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
  const h = le(() => e.filter(Ii), [e]), f = le(() => e.filter((y) => !Ii(y)), [e]), p = h.filter((y) => y.kind === "bool"), g = h.filter((y) => y.kind !== "bool"), v = le(() => Xg(e, i), [e, i]), b = Object.keys(v).length, w = we(), T = (y, N) => {
    s({ ...i, [y]: N });
  };
  return h.length === 0 ? null : /* @__PURE__ */ x("div", { className: "flex min-h-0 flex-1 flex-col", role: "group", "aria-label": "Part parameters", children: [
    u ? /* @__PURE__ */ x("div", { className: "border-b border-line-soft bg-fail-wash px-4 py-2.5", children: [
      /* @__PURE__ */ x("p", { className: "mono-label flex items-center gap-2 text-fail", children: [
        /* @__PURE__ */ c($, { name: "warning" }),
        "Build failed at these values"
      ] }),
      /* @__PURE__ */ c("p", { className: "mt-1 text-xs leading-4 text-ink-soft", children: u }),
      /* @__PURE__ */ c("p", { className: "mt-0.5 text-xs leading-4 text-muted", children: "Showing the last part that built." })
    ] }) : null,
    /* @__PURE__ */ x("div", { className: "flex min-h-0 flex-1 flex-col overflow-y-auto pb-3", children: [
      f.length > 0 ? /* @__PURE__ */ x(_, { children: [
        /* @__PURE__ */ c(Uo, { children: "Set by the plan" }),
        /* @__PURE__ */ c("dl", { className: "flex flex-col", children: f.map((y) => /* @__PURE__ */ x("div", { className: "flex items-center gap-[9px] px-4 py-1.5", title: y.description, children: [
          /* @__PURE__ */ c("span", { className: "text-muted", children: /* @__PURE__ */ c($, { name: "lock" }) }),
          /* @__PURE__ */ c("dt", { className: "mono-id min-w-0 flex-1 truncate uppercase text-muted [letter-spacing:0.06em]", children: jt(y.name) }),
          /* @__PURE__ */ c("dd", { className: "mono-value text-muted", children: String(i[y.name] ?? y.default) })
        ] }, y.name)) })
      ] }) : null,
      /* @__PURE__ */ c(Uo, { children: "Yours to drag" }),
      /* @__PURE__ */ x("div", { className: "flex flex-col gap-3", children: [
        p.map((y) => /* @__PURE__ */ c(
          t0,
          {
            id: `${w}${y.name}`,
            param: y,
            value: i[y.name] ?? y.default,
            dirty: y.name in v,
            onValue: (N) => T(y.name, N)
          },
          y.name
        )),
        g.map((y) => /* @__PURE__ */ c(
          e0,
          {
            id: `${w}${y.name}`,
            param: y,
            value: i[y.name] ?? y.default,
            dirty: y.name in v,
            measurements: t,
            nozzle: n,
            onValue: (N) => T(y.name, N)
          },
          y.name
        ))
      ] })
    ] }),
    l?.size_mm ? /* @__PURE__ */ c("div", { className: "chrome shrink-0 border-t border-line-soft px-4 py-2", children: /* @__PURE__ */ x("span", { className: "mono-caption text-muted", children: [
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
    b > 0 ? /* @__PURE__ */ x("div", { className: "chrome mx-4 mb-3 flex flex-col gap-2 rounded-content bg-accent-wash p-2 pl-3", children: [
      /* @__PURE__ */ x("div", { className: "flex h-6 items-center gap-2", children: [
        /* @__PURE__ */ c("span", { className: "size-1.5 shrink-0 rounded-full bg-accent" }),
        /* @__PURE__ */ x("span", { className: "mono-id flex-1 whitespace-nowrap uppercase text-accent-ink tabular-nums [letter-spacing:0.08em]", children: [
          b,
          " ",
          b === 1 ? "change" : "changes"
        ] }),
        /* @__PURE__ */ c(
          "button",
          {
            type: "button",
            onClick: () => s({}),
            className: "mono-label shrink-0 rounded-control px-2 py-1 text-ink-soft transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-accent",
            children: "Reset"
          }
        )
      ] }),
      /* @__PURE__ */ c("span", { className: "flex [&>*]:w-full", title: "Make these values the part's defaults, so it opens and downloads this way.", children: /* @__PURE__ */ c(
        Kg,
        {
          label: "Save as default",
          pendingLabel: "Saving",
          successLabel: "Saved",
          errorLabel: "Try again",
          resetAfter: 1400,
          variant: "ink",
          disabled: a,
          onAction: () => r(v)
        }
      ) })
    ] }) : null
  ] });
}
const fc = Ui(function({ anchor: t, width: n, align: i = "right", gap: s = 6, className: r, children: o, ...a }, l) {
  const [u, d] = F(null), h = Y(() => {
    const f = t.current?.getBoundingClientRect();
    if (!f) return;
    const p = i === "right" ? f.right - n : f.left;
    d({
      left: Math.max(8, Math.min(p, window.innerWidth - n - 8)),
      bottom: Math.max(8, window.innerHeight - f.top + s)
    });
  }, [t, n, i, s]);
  return mt(h, [h]), O(() => (window.addEventListener("resize", h), window.addEventListener("scroll", h, !0), () => {
    window.removeEventListener("resize", h), window.removeEventListener("scroll", h, !0);
  }), [h]), typeof document > "u" ? null : ta(
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
}), hc = [
  { format: "3mf", caption: "Print-ready, keeps units and orientation.", recommended: !0 },
  { format: "stl", caption: "Print-ready mesh. Works in every slicer." },
  { format: "step", caption: "Solid model, for another CAD tool." }
];
function n0(e) {
  if (e.state === "queued") return "Estimate · slicing…";
  if (e.state === "failed") return `Estimate · ${e.error ?? "unavailable"}`;
  const t = [
    e.grams ? `${Math.round(e.grams)} g` : null,
    e.seconds ? `${(e.seconds / 3600).toFixed(1)} hr` : null
  ].filter(Boolean);
  return `Estimate · ${t.length ? t.join(" · ") : "unavailable"}`;
}
const pc = "nurb.exportFormat";
function i0() {
  try {
    const e = localStorage.getItem(pc);
    if (hc.some((t) => t.format === e)) return e;
  } catch {
  }
  return "3mf";
}
function Ly({ partId: e, export: t, status: n, revision: i, runId: s, openIn: r }) {
  const [o, a] = F(i0), [l, u] = F(!1), [d, h] = F(null), [f, p] = F(null), g = P(null), v = P(null), b = P(null), w = P(null), T = P(0), y = P({ partId: e, revision: i, runId: s });
  O(() => {
    const k = y.current;
    k.partId === e && Object.is(k.revision, i) && Object.is(k.runId, s) || (y.current = { partId: e, revision: i, runId: s }, T.current += 1, h(null), p(null));
  }, [e, i, s]), O(() => {
    if (!l) return;
    const k = (S) => {
      const A = S.target;
      g.current?.contains(A) || w.current?.contains(A) || u(!1);
    }, m = (S) => {
      if (S.key === "Escape") {
        u(!1), v.current?.focus();
        return;
      }
      if (S.key !== "ArrowDown" && S.key !== "ArrowUp") return;
      const A = Array.from(b.current?.querySelectorAll('[role="menuitem"]') ?? []);
      if (A.length === 0) return;
      S.preventDefault();
      const L = S.key === "ArrowDown" ? 1 : -1, j = A.indexOf(document.activeElement), I = j === -1 ? L === 1 ? 0 : A.length - 1 : (j + L + A.length) % A.length;
      A[I].focus();
    };
    return document.addEventListener("pointerdown", k), document.addEventListener("keydown", m), () => {
      document.removeEventListener("pointerdown", k), document.removeEventListener("keydown", m);
    };
  }, [l]);
  const N = async (k, m) => {
    const S = ++T.current;
    h(k), p(null);
    try {
      await m(), S === T.current && u(!1);
    } catch (A) {
      if (S !== T.current) return;
      p(A instanceof Error ? A.message : "The export did not finish."), u(!0);
    } finally {
      S === T.current && h(null);
    }
  }, V = (k) => N(k, () => t(k)), C = (k) => {
    a(k);
    try {
      localStorage.setItem(pc, k);
    } catch {
    }
    V(k);
  };
  return /* @__PURE__ */ x("div", { ref: g, className: "relative flex-1", children: [
    /* @__PURE__ */ x("div", { className: "flex h-9 w-full overflow-hidden rounded-control bg-accent text-white", children: [
      /* @__PURE__ */ x(
        "button",
        {
          type: "button",
          disabled: d !== null,
          onClick: () => {
            V(o);
          },
          className: "chrome btn-label inline-flex flex-1 items-center justify-center gap-2 px-3 transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-white disabled:hover:bg-transparent",
          children: [
            /* @__PURE__ */ c($, { name: "download" }),
            d ? "Preparing…" : `Download ${o.toUpperCase()}`
          ]
        }
      ),
      /* @__PURE__ */ c(
        "button",
        {
          ref: v,
          type: "button",
          "aria-haspopup": "menu",
          "aria-expanded": l,
          "aria-label": "Choose file type",
          title: "Choose file type",
          onClick: () => u((k) => !k),
          className: "inline-flex w-9 shrink-0 items-center justify-center border-l border-white/25 transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-white",
          children: /* @__PURE__ */ c($, { name: "chevron-down" })
        }
      )
    ] }),
    l ? /* @__PURE__ */ x(
      fc,
      {
        ref: w,
        anchor: v,
        width: 254,
        align: "left",
        gap: 8,
        className: "z-30 overflow-hidden rounded-content border border-panel-edge bg-ground shadow-[var(--shadow-panel)]",
        children: [
          /* @__PURE__ */ x("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft px-3", children: [
            /* @__PURE__ */ c("span", { className: "mono-label text-muted", children: "File type" }),
            i != null ? /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: $t(i) }) : null
          ] }),
          f ? /* @__PURE__ */ x("div", { className: "border-b border-line-soft bg-fail-wash px-3 py-2 text-[11px] leading-4 text-ink-soft", children: [
            /* @__PURE__ */ c("p", { className: "mono-label text-fail", children: "Download failed" }),
            /* @__PURE__ */ c("p", { className: "mt-0.5", children: f })
          ] }) : null,
          /* @__PURE__ */ x(
            "div",
            {
              ref: b,
              role: "menu",
              "aria-label": "Download format",
              className: "flex flex-col py-1",
              children: [
                hc.map((k) => {
                  const m = d === k.format, S = o === k.format;
                  return /* @__PURE__ */ x(
                    "button",
                    {
                      type: "button",
                      role: "menuitem",
                      disabled: d !== null,
                      "aria-current": S || void 0,
                      onClick: () => C(k.format),
                      className: R(
                        "flex w-full flex-col gap-0.5 px-3 py-2 text-left transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none disabled:opacity-60 disabled:hover:bg-transparent",
                        S && "bg-raised/60"
                      ),
                      children: [
                        /* @__PURE__ */ x("span", { className: "flex w-full items-center", children: [
                          /* @__PURE__ */ c("span", { className: "mono-value uppercase text-ink", children: k.format }),
                          S ? /* @__PURE__ */ c($, { name: "check", className: "ml-1.5 text-accent-ink" }) : null,
                          m ? /* @__PURE__ */ x("span", { className: "mono-caption ml-auto flex items-center gap-1.5 text-muted", children: [
                            /* @__PURE__ */ c("span", { className: "size-1.5 rounded-full bg-accent" }),
                            "preparing"
                          ] }) : k.recommended ? /* @__PURE__ */ c("span", { className: "mono-caption ml-auto text-accent-ink", children: "Recommended" }) : null
                        ] }),
                        /* @__PURE__ */ c("span", { className: "text-xs leading-4 text-ink-soft", children: k.caption })
                      ]
                    },
                    k.format
                  );
                }),
                r ? /* @__PURE__ */ x(
                  "button",
                  {
                    type: "button",
                    role: "menuitem",
                    disabled: d !== null,
                    onClick: () => {
                      N("slicer", r.open);
                    },
                    className: "mt-1 flex w-full flex-col gap-0.5 border-t border-line-soft px-3 pt-2.5 pb-2 text-left transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none disabled:opacity-60 disabled:hover:bg-transparent",
                    children: [
                      /* @__PURE__ */ x("span", { className: "flex w-full items-center", children: [
                        /* @__PURE__ */ x("span", { className: "mono-value uppercase text-ink", children: [
                          "Open in ",
                          r.name
                        ] }),
                        d === "slicer" ? /* @__PURE__ */ x("span", { className: "mono-caption ml-auto flex items-center gap-1.5 text-muted", children: [
                          /* @__PURE__ */ c("span", { className: "size-1.5 rounded-full bg-accent" }),
                          "preparing"
                        ] }) : null
                      ] }),
                      /* @__PURE__ */ c("span", { className: "text-xs leading-4 text-ink-soft", children: "Saves a 3MF and opens it there." })
                    ]
                  }
                ) : null
              ]
            }
          ),
          n ? /* @__PURE__ */ c("div", { className: "chrome border-t border-line-soft bg-raised px-3 py-2", children: /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: n0(n) }) }) : null
        ]
      }
    ) : null
  ] });
}
function Fy({
  printers: e,
  current: t,
  defaultName: n,
  onPick: i,
  onAdd: s,
  onManage: r,
  triggerRef: o,
  onClose: a
}) {
  const l = P(null);
  return O(() => {
    const u = (h) => {
      const f = h.target;
      l.current?.contains(f) || o.current?.contains(f) || a();
    }, d = (h) => {
      h.key === "Escape" && a();
    };
    return document.addEventListener("pointerdown", u), document.addEventListener("keydown", d), () => {
      document.removeEventListener("pointerdown", u), document.removeEventListener("keydown", d);
    };
  }, [a, o]), /* @__PURE__ */ x(
    fc,
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
        /* @__PURE__ */ x("div", { className: "flex h-6 items-center justify-between px-3 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase", children: [
          /* @__PURE__ */ c("span", { children: "Print on" }),
          /* @__PURE__ */ c("span", { children: "This part" })
        ] }),
        e.map((u) => {
          const d = u.name === t;
          return /* @__PURE__ */ x(
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
        /* @__PURE__ */ x(
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
        r ? /* @__PURE__ */ x(
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
function js({
  label: e,
  trailing: t,
  inset: n = 18
}) {
  return /* @__PURE__ */ x(
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
const s0 = (e) => e && e.length === 3 ? e.map((t) => Math.round(t)).join(" × ") : "";
function Oy({
  catalogue: e,
  owned: t,
  busy: n,
  error: i,
  onAdd: s,
  onClose: r
}) {
  const [o, a] = F(""), [l, u] = F(null), d = le(() => new Set(t), [t]);
  O(() => {
    const f = (p) => {
      p.key === "Escape" && r();
    };
    return window.addEventListener("keydown", f), () => window.removeEventListener("keydown", f);
  }, [r]);
  const h = le(() => {
    const f = o.trim().toLowerCase(), p = f ? e.filter((b) => b.label.toLowerCase().includes(f)) : e, g = [], v = /* @__PURE__ */ new Map();
    for (const b of p)
      v.has(b.brand) || (v.set(b.brand, []), g.push(b.brand)), v.get(b.brand).push(b);
    return g.map((b) => ({ brand: b, rows: v.get(b) }));
  }, [e, o]);
  return /* @__PURE__ */ c(
    "div",
    {
      className: "fixed inset-0 z-50 flex items-center justify-center bg-ink/30 p-6",
      onClick: (f) => f.target === f.currentTarget && r(),
      children: /* @__PURE__ */ x(
        "div",
        {
          className: "panel flex max-h-full w-[520px] flex-col overflow-hidden",
          role: "dialog",
          "aria-modal": "true",
          "aria-label": "Add a printer",
          children: [
            /* @__PURE__ */ c(
              js,
              {
                label: "Add a printer",
                inset: 16,
                trailing: /* @__PURE__ */ c($s, { icon: "xmark", label: "Close", onClick: r, className: "-mr-2" })
              }
            ),
            /* @__PURE__ */ x("div", { className: "flex shrink-0 flex-col gap-3 px-5 pt-4", children: [
              /* @__PURE__ */ c("p", { className: "text-[13.5px] leading-[18px] text-ink-soft", children: "Pick the machine on your bench. Checks use its bed size; the slicer brings its own profile." }),
              /* @__PURE__ */ x("div", { className: "flex h-8 shrink-0 items-center gap-2 rounded-[3px] border border-line bg-ground px-2.5", children: [
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
            /* @__PURE__ */ c("div", { className: "mt-3 min-h-0 flex-1 overflow-y-auto border-t border-line-soft", children: h.length === 0 ? /* @__PURE__ */ c("p", { className: "px-5 py-4 text-[13px] leading-[18px] text-muted", children: "No printer matches that." }) : h.map((f) => /* @__PURE__ */ x("div", { className: "flex flex-col", children: [
              /* @__PURE__ */ c("div", { className: "flex h-6 items-center bg-raised px-5 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase", children: f.brand }),
              f.rows.map((p) => {
                const g = d.has(p.name), v = l === p.name;
                return /* @__PURE__ */ x(
                  "button",
                  {
                    type: "button",
                    disabled: g,
                    "aria-pressed": v,
                    onClick: () => u(p.name),
                    className: R(
                      "chrome flex h-[30px] w-full items-center gap-2 px-5 text-left transition-colors focus-visible:outline-none",
                      g ? "cursor-default text-faint" : v ? "bg-accent-wash text-ink" : "text-ink-soft hover:bg-raised hover:text-ink"
                    ),
                    children: [
                      /* @__PURE__ */ c("span", { className: "flex size-3 shrink-0 items-center justify-center", children: v ? /* @__PURE__ */ c($, { name: "check" }) : null }),
                      /* @__PURE__ */ c("span", { className: "min-w-0 flex-1 truncate font-mono text-[11px] leading-4", children: p.label }),
                      /* @__PURE__ */ c("span", { className: "shrink-0 font-mono text-[10px] leading-4 tracking-[0.08em] text-muted tabular-nums", children: g ? "On your bench" : s0(p.bed) })
                    ]
                  },
                  p.name
                );
              })
            ] }, f.brand)) }),
            i ? /* @__PURE__ */ c("p", { className: "shrink-0 bg-fail-wash px-5 py-2 text-[12px] leading-4 text-fail", role: "alert", children: i }) : null,
            /* @__PURE__ */ x("div", { className: "flex shrink-0 items-center gap-4 border-t border-line-soft px-5 py-4", children: [
              /* @__PURE__ */ c("p", { className: "min-w-0 flex-1 text-[12px] leading-4 text-muted", children: "Not listed? Pick the one with the closest bed size. That is all the checks use." }),
              /* @__PURE__ */ c(Ae, { size: "md", className: "px-3.5", onClick: r, children: "Cancel" }),
              /* @__PURE__ */ c(
                Ae,
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
const r0 = "" + new URL("nurb-lockup.svg", import.meta.url).href, o0 = "" + new URL("nurb-mark-16.svg", import.meta.url).href, a0 = "" + new URL("nurb-mark-outline.svg", import.meta.url).href, l0 = "" + new URL("nurb-mark-small.svg", import.meta.url).href, c0 = "" + new URL("favicon.svg", import.meta.url).href, u0 = "" + new URL("auth-plane.svg", import.meta.url).href, d0 = "" + new URL("ghost-bracket.svg", import.meta.url).href, f0 = "" + new URL("404-squiggle.svg", import.meta.url).href, Us = { lockup: r0, mark: o0, markOutline: a0, markSmall: l0, favicon: c0, authPlane: u0, ghostBracket: d0, squiggle: f0 }, Nt = 240, sn = 148;
function Be(e, t, n) {
  return [(e - t) * 0.866, (e + t) * 0.5 - n];
}
function h0({ bbox: e, ghost: t = !1, className: n }) {
  const i = e && e.length === 3 && e.every((A) => A > 0) ? e : null, s = i ?? [1, 1, 1], r = Math.max(...s), [o, a, l] = s.map((A) => A / r), u = [
    Be(0, 0, 0),
    Be(o, 0, 0),
    Be(o, a, 0),
    Be(0, a, 0),
    Be(0, 0, l),
    Be(o, 0, l),
    Be(o, a, l),
    Be(0, a, l)
  ], d = u.map((A) => A[0]), h = u.map((A) => A[1]), f = Math.min(...d), p = Math.max(...d), g = Math.min(...h), v = Math.max(...h), b = Math.min((Nt - 60) / (p - f), (sn - 40) / (v - g)), w = Nt / 2 - (f + p) / 2 * b, T = sn / 2 - (g + v) / 2 * b, y = (A) => `${(u[A][0] * b + w).toFixed(1)},${(u[A][1] * b + T).toFixed(1)}`, N = `${y(4)} ${y(5)} ${y(6)} ${y(7)}`, V = `${y(3)} ${y(2)} ${y(6)} ${y(7)}`, C = `${y(1)} ${y(2)} ${y(6)} ${y(5)}`, k = Nt / 2, m = Math.max(...u.map((A) => A[1])) * b + T + 6, S = (p - f) * b / 2 + 8;
  return t || !i ? /* @__PURE__ */ c("svg", { viewBox: `0 0 ${Nt} ${sn}`, className: n, "aria-hidden": "true", children: /* @__PURE__ */ x("g", { fill: "none", stroke: "var(--color-panel-edge)", strokeWidth: "1.5", strokeLinejoin: "round", strokeDasharray: "5 4", children: [
    /* @__PURE__ */ c("polygon", { points: N }),
    /* @__PURE__ */ c("polygon", { points: V }),
    /* @__PURE__ */ c("polygon", { points: C })
  ] }) }) : /* @__PURE__ */ x("svg", { viewBox: `0 0 ${Nt} ${sn}`, className: n, "aria-hidden": "true", children: [
    /* @__PURE__ */ c("ellipse", { cx: k, cy: m, rx: S, ry: S * 0.16, fill: "var(--color-raised)" }),
    /* @__PURE__ */ x("g", { stroke: "var(--color-part-edge)", strokeWidth: "1.2", strokeLinejoin: "round", children: [
      /* @__PURE__ */ c("polygon", { points: N, fill: "var(--color-part-top)" }),
      /* @__PURE__ */ c("polygon", { points: V, fill: "var(--color-part-front)" }),
      /* @__PURE__ */ c("polygon", { points: C, fill: "var(--color-part-side)" })
    ] })
  ] });
}
const p0 = X.out;
function m0({
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
  const [f, p] = F(!1), [g, v] = F(""), [b, w] = F(), T = P(null), y = P(null), N = P(null), V = we(), C = P(d);
  C.current = d, O(() => {
    C.current?.(f), f || v("");
  }, [f]);
  const k = g.trim().toLowerCase(), m = k ? t.filter((S) => typeof S.label == "string" && S.label.toLowerCase().includes(k)) : t;
  return mt(() => {
    if (!f || !a) return;
    const S = N.current?.getBoundingClientRect();
    S && w(
      n === "right" ? {
        position: "fixed",
        top: S.bottom + 4,
        right: window.innerWidth - S.right
      } : { position: "fixed", top: S.bottom + 4, left: S.left }
    );
  }, [f, a, n]), O(() => {
    if (!f) return;
    const S = (L) => {
      const j = L.target;
      !T.current?.contains(j) && !y.current?.contains(j) && p(!1);
    }, A = (L) => {
      L.key === "Escape" && (p(!1), N.current?.focus());
    };
    return document.addEventListener("pointerdown", S), document.addEventListener("keydown", A), () => {
      document.removeEventListener("pointerdown", S), document.removeEventListener("keydown", A);
    };
  }, [f]), /* @__PURE__ */ x("div", { ref: T, className: R("relative", i), children: [
    /* @__PURE__ */ c(
      "button",
      {
        ref: N,
        type: "button",
        "aria-label": e,
        title: e,
        "aria-haspopup": "menu",
        "aria-expanded": f,
        "aria-controls": V,
        disabled: l,
        onClick: (S) => {
          S.preventDefault(), S.stopPropagation(), p((A) => !A);
        },
        onKeyDown: (S) => S.stopPropagation(),
        className: R(
          "chrome inline-flex items-center justify-center rounded-[3px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          u ?? (r ? "rounded-full" : "size-5"),
          !r && (f ? "bg-raised text-ink" : "text-muted hover:bg-raised hover:text-ink")
        ),
        children: r ? r(f) : /* @__PURE__ */ c($, { name: "dots" })
      }
    ),
    yc(
      a,
      /* @__PURE__ */ c(de, { children: f ? /* @__PURE__ */ x(
        gc,
        {
          id: V,
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
            h ? /* @__PURE__ */ x("div", { className: "sticky top-0 z-10 -mt-1 mb-1 flex h-8 items-center gap-2 border-b border-line-soft bg-ground px-3", children: [
              /* @__PURE__ */ c($, { name: "search", className: "text-muted" }),
              /* @__PURE__ */ c(
                "input",
                {
                  autoFocus: !0,
                  value: g,
                  onChange: (S) => v(S.target.value),
                  onKeyDown: (S) => {
                    S.key === "Enter" && m[0] && (m[0].onSelect(), p(!1));
                  },
                  placeholder: h,
                  "aria-label": h,
                  className: "mono-id min-w-0 flex-1 bg-transparent text-ink outline-none placeholder:text-faint"
                }
              )
            ] }) : null,
            h && m.length === 0 ? /* @__PURE__ */ c("div", { className: "mono-id flex h-7 items-center px-3 text-faint", children: "Nothing matches" }) : null,
            /* @__PURE__ */ c(
              mc,
              {
                items: m,
                onPick: (S) => {
                  S.onSelect(), S.keepOpen || p(!1);
                }
              }
            ),
            o ? /* @__PURE__ */ c("div", { className: "sticky bottom-0 mt-1 border-t border-line-soft bg-raised px-3 py-2 font-mono text-[9.5px] leading-3 tracking-[0.08em] text-muted uppercase", children: o }) : null
          ]
        }
      ) : null })
    )
  ] });
}
function g0() {
  const [e, t] = F(null), [n, i] = F(), s = P(null), r = we();
  mt(() => {
    if (!e || !s.current) return;
    const { width: l, height: u } = s.current.getBoundingClientRect();
    i({
      position: "fixed",
      left: Math.max(8, Math.min(e.x, window.innerWidth - l - 8)),
      top: Math.max(8, Math.min(e.y, window.innerHeight - u - 8))
    });
  }, [e]), O(() => {
    if (!e) return;
    const l = (h) => {
      s.current?.contains(h.target) || t(null);
    }, u = (h) => h.key === "Escape" && t(null), d = () => t(null);
    return document.addEventListener("pointerdown", l, !0), document.addEventListener("keydown", u), window.addEventListener("blur", d), window.addEventListener("scroll", d, !0), () => {
      document.removeEventListener("pointerdown", l, !0), document.removeEventListener("keydown", u), window.removeEventListener("blur", d), window.removeEventListener("scroll", d, !0);
    };
  }, [e]);
  const o = (l, u) => {
    u?.length && (l.preventDefault(), l.stopPropagation(), i({ position: "fixed", left: l.clientX, top: l.clientY, visibility: "hidden" }), t({ x: l.clientX, y: l.clientY, items: u }));
  }, a = yc(
    !0,
    /* @__PURE__ */ c(de, { children: e ? /* @__PURE__ */ c(
      gc,
      {
        id: r,
        ref: s,
        style: n,
        className: "z-30 min-w-[168px] overflow-hidden rounded-[6px] border border-panel-edge bg-ground py-1 shadow-[var(--shadow-panel)]",
        children: /* @__PURE__ */ c(
          mc,
          {
            items: e.items,
            onPick: (l) => {
              l.onSelect(), l.keepOpen || t(null);
            }
          }
        )
      }
    ) : null })
  );
  return { open: o, menu: a };
}
function mc({ items: e, onPick: t }) {
  const n = e.some((i) => i.checked !== void 0);
  return /* @__PURE__ */ c(_, { children: e.map((i, s) => /* @__PURE__ */ x(ji, { children: [
    i.section && i.section !== e[s - 1]?.section ? /* @__PURE__ */ x(_, { children: [
      s > 0 ? /* @__PURE__ */ c("div", { className: "my-1 border-t border-line-soft", role: "separator" }) : null,
      /* @__PURE__ */ c("div", { className: "flex h-6 items-center px-3 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase", children: i.section })
    ] }) : null,
    /* @__PURE__ */ x(
      "button",
      {
        type: "button",
        role: n ? "menuitemradio" : "menuitem",
        "aria-checked": n ? !!i.checked : void 0,
        disabled: i.disabled,
        title: i.title,
        onClick: (r) => {
          r.preventDefault(), r.stopPropagation(), t(i);
        },
        className: R(
          "chrome mono-id flex h-7 w-full items-center gap-2 px-3 text-left transition-colors focus-visible:bg-raised focus-visible:outline-none disabled:text-faint disabled:hover:bg-transparent",
          i.separated && "mt-1 border-t border-line-soft pt-px",
          i.tone === "danger" ? "text-fail hover:bg-fail-wash" : i.checked ? "text-ink hover:bg-raised" : "text-ink-soft hover:bg-raised hover:text-ink"
        ),
        children: [
          n ? /* @__PURE__ */ c("span", { className: "flex size-3 shrink-0 items-center justify-center", children: i.checked ? /* @__PURE__ */ c($, { name: "check" }) : null }) : null,
          i.icon ? /* @__PURE__ */ c($, { name: i.icon }) : null,
          /* @__PURE__ */ c("span", { className: "min-w-0 flex-1 truncate", children: i.label }),
          i.trailing ? /* @__PURE__ */ c("span", { className: "shrink-0", children: i.trailing }) : null
        ]
      }
    )
  ] }, s)) });
}
function gc({
  id: e,
  ref: t,
  style: n,
  className: i,
  children: s
}) {
  const r = vp();
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
      transition: { duration: z.tick, ease: p0 },
      style: n,
      className: i,
      children: s
    }
  );
}
function yc(e, t) {
  return e && typeof document < "u" ? ta(t, document.body) : t;
}
const xc = X.out, vc = 2.5, rn = 20, y0 = 10;
function x0({
  onConfirm: e,
  holdMs: t = 1800,
  disabled: n = !1
}) {
  const [i, s] = F(0), [r, o] = F("idle"), a = P("idle"), l = P(!1), u = P(0), d = P(0), h = P(0), f = P(null), p = P(e);
  p.current = e;
  const g = Y((y) => {
    a.current = y, o(y);
  }, []), v = Y(() => {
    cancelAnimationFrame(h.current), h.current = 0, l.current = !1, u.current = 0, f.current = null, s(0), g("idle");
  }, [g]), b = Y(
    (y) => {
      if (n || a.current === "committed" || a.current === "holding" || (f.current = y ?? null, l.current = !0, g("holding"), $e("press"), h.current)) return;
      d.current = performance.now();
      const N = (V) => {
        const C = Math.min(64, V - d.current);
        if (d.current = V, u.current += l.current ? C : -C * vc, u.current >= t) {
          h.current = 0, u.current = t, l.current = !1, f.current = null, s(rn), g("committed"), p.current();
          return;
        }
        if (u.current <= 0) {
          h.current = 0, u.current = 0, f.current = null, s(0), g("idle");
          return;
        }
        const k = Math.min(rn, Math.floor(u.current / t * rn));
        s((m) => m === k ? m : k), h.current = requestAnimationFrame(N);
      };
      h.current = requestAnimationFrame(N);
    },
    [n, t, g]
  ), w = Y(() => {
    a.current === "holding" && (l.current = !1, f.current = null, g("releasing"));
  }, [g]);
  return O(() => {
    const y = () => w(), N = () => {
      document.hidden && w();
    };
    return window.addEventListener("blur", y), document.addEventListener("visibilitychange", N), () => {
      window.removeEventListener("blur", y), document.removeEventListener("visibilitychange", N), cancelAnimationFrame(h.current), h.current = 0;
    };
  }, [w]), { bind: {
    onPointerDown: (y) => {
      y.pointerType === "mouse" && y.button !== 0 || (y.currentTarget.setPointerCapture?.(y.pointerId), b({ x: y.clientX, y: y.clientY }));
    },
    onPointerMove: (y) => {
      const N = f.current;
      a.current !== "holding" || !N || Math.hypot(y.clientX - N.x, y.clientY - N.y) > y0 && w();
    },
    onPointerUp: w,
    onPointerCancel: w,
    onPointerLeave: w,
    onKeyDown: (y) => {
      if (y.key === "Escape") {
        (a.current === "holding" || a.current === "releasing") && (y.preventDefault(), v());
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
  }, phase: r, progress: i / rn, reset: v };
}
function v0({
  label: e,
  confirmLabel: t = "Confirmed",
  holdMs: n = 1800,
  onConfirm: i,
  variant: s = "danger",
  disabled: r = !1,
  className: o
}) {
  const { bind: a, phase: l, reset: u } = x0({ onConfirm: i, holdMs: n, disabled: r }), d = J(), h = we(), f = l === "committed", p = Math.round(n / 100) / 10, g = Hl(0), v = Em(g, (b) => `inset(0 ${(1 - b) * 100}% 0 0)`);
  return O(() => {
    if (!f) return;
    const b = setTimeout(u, 1600);
    return () => clearTimeout(b);
  }, [f, u]), O(() => {
    if (d) {
      g.set(l === "holding" || l === "committed" ? 1 : 0);
      return;
    }
    if (l === "committed") {
      const T = ri(g, 1, { duration: z.tick, ease: "linear" });
      return () => T.stop();
    }
    const b = g.get();
    if (l === "holding") {
      const T = ri(g, 1, { duration: n * (1 - b) / 1e3, ease: "linear" });
      return () => T.stop();
    }
    const w = ri(g, 0, { duration: n * b / vc / 1e3, ease: xc });
    return () => w.stop();
  }, [l, n, d, g]), /* @__PURE__ */ x(
    Ae,
    {
      variant: s,
      "aria-label": e,
      "aria-disabled": r || f,
      "aria-describedby": h,
      className: `relative isolate select-none overflow-hidden ${o ?? ""}`,
      ...a,
      children: [
        /* @__PURE__ */ c(zo, { committed: f, label: e, confirmLabel: t }),
        /* @__PURE__ */ c(
          B.span,
          {
            "aria-hidden": "true",
            style: { clipPath: v },
            className: "absolute inset-0 grid place-items-center bg-ink text-ground",
            children: /* @__PURE__ */ c(zo, { committed: f, label: e, confirmLabel: t })
          }
        ),
        /* @__PURE__ */ x("span", { id: h, className: "sr-only", children: [
          "Press and hold for ",
          p,
          " seconds to confirm. Let go early and nothing happens."
        ] }),
        /* @__PURE__ */ c("span", { role: "status", "aria-live": "polite", className: "sr-only", children: f ? t : "" })
      ]
    }
  );
}
function zo({ committed: e, label: t, confirmLabel: n }) {
  const i = { duration: z.settle, ease: xc };
  return /* @__PURE__ */ x("span", { "aria-hidden": "true", className: "col-start-1 row-start-1 grid", children: [
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
    /* @__PURE__ */ x(
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
const b0 = X.out;
function Iy({
  title: e,
  children: t,
  confirmLabel: n = "Delete",
  hold: i = !1,
  onConfirm: s,
  onCancel: r
}) {
  const o = P(null), a = P(null);
  return O(() => {
    o.current?.showModal(), a.current?.focus();
  }, []), /* @__PURE__ */ x(
    B.dialog,
    {
      ref: o,
      "aria-labelledby": "confirm-title",
      initial: { opacity: 0, scale: 0.98 },
      animate: { opacity: 1, scale: 1 },
      transition: { duration: z.settle, ease: b0 },
      onCancel: (l) => {
        l.preventDefault(), r();
      },
      onClick: (l) => {
        l.target === l.currentTarget && r();
      },
      className: "panel m-auto w-[320px] max-w-[calc(100vw-32px)] p-0 text-ink backdrop:bg-ink/30 backdrop:transition-colors backdrop:duration-[240ms] starting:backdrop:bg-ink/0",
      children: [
        /* @__PURE__ */ x("div", { className: "flex flex-col gap-1.5 px-4 pt-4 pb-3.5", children: [
          /* @__PURE__ */ c("h2", { id: "confirm-title", className: "font-display text-[16px] leading-5 font-bold tracking-[-0.02em] text-ink", children: e }),
          /* @__PURE__ */ c("p", { className: "text-xs leading-4 text-muted", children: t })
        ] }),
        /* @__PURE__ */ x("div", { className: "flex justify-end gap-1.5 border-t border-line-soft px-4 py-3", children: [
          /* @__PURE__ */ c(Ae, { ref: a, variant: "outline", onClick: r, children: "Cancel" }),
          i ? /* @__PURE__ */ c(v0, { label: n, confirmLabel: "Done", holdMs: 1200, onConfirm: s }) : /* @__PURE__ */ c(Ae, { variant: "danger", onClick: s, children: n })
        ] })
      ]
    }
  );
}
function By({
  size: e = "header",
  onNavigate: t
}) {
  const n = e === "panel" ? "h-6 w-[87px]" : "h-[18px] w-[65px]", i = /* @__PURE__ */ c("img", { src: Us.lockup, alt: "nurb", className: `${n} shrink-0` });
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
const w0 = X.out, k0 = { duration: 0 }, T0 = typeof window > "u" ? O : mt;
function S0({
  src: e,
  onReady: t,
  onError: n
}) {
  const i = P(null), [s, r] = F({ status: "loading", instant: !1 }), o = P(t);
  o.current = t;
  const a = P(n);
  return a.current = n, T0(() => {
    const l = i.current, u = (g, v) => r((b) => b.status === g && b.instant === v ? b : { status: g, instant: v });
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
function N0({
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
  const h = J() === !0, { ref: f, status: p, instant: g } = S0({ src: e, onReady: l, onError: u }), v = p === "ready", b = h || g, w = b ? k0 : { duration: z.arrive, ease: w0 };
  return /* @__PURE__ */ x(
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
            animate: b ? { opacity: v ? 1 : 0 } : v ? { opacity: 1, filter: "blur(0px)", scale: 1 } : { opacity: 0, filter: `blur(${r}px)`, scale: 1.06 },
            transition: w
          }
        ),
        p === "error" ? /* @__PURE__ */ c("div", { "aria-hidden": "true", className: "absolute inset-0 grid place-items-center bg-raised text-faint", children: /* @__PURE__ */ c($, { name: "image" }) }) : null
      ]
    }
  );
}
const Wo = 3e4;
function A0(e, t) {
  const n = t ? Date.parse(t) : NaN, [i, s] = F(() => Date.now());
  return O(() => {
    if (!e || Number.isNaN(n)) return;
    const r = n + Wo - Date.now();
    if (r <= 0) return;
    const o = setTimeout(() => s(Date.now()), r);
    return () => clearTimeout(o);
  }, [e, n]), e ? Number.isNaN(n) ? !0 : i - n < Wo : !1;
}
function $y({
  part: e,
  onOpen: t,
  menu: n,
  renaming: i,
  onRename: s
}) {
  const r = Hm(e.bbox), o = Km(e.builtAt), a = e.status === "failed", l = e.status === "building", u = A0(l, e.buildingSince), d = g0();
  return /* @__PURE__ */ x(
    "div",
    {
      onContextMenu: (h) => d.open(h, i ? void 0 : n),
      className: "group relative flex flex-col rounded-[6px] border border-panel-edge bg-ground transition-shadow focus-within:shadow-[var(--shadow-panel)] hover:shadow-[var(--shadow-panel)]",
      children: [
        d.menu,
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
            N0,
            {
              src: e.thumbnailUrl,
              alt: "",
              width: 4,
              height: 3,
              placeholder: "transparent",
              className: "h-full rounded-none! [&_img]:object-contain [&_img]:p-2"
            }
          )
        ) : /* @__PURE__ */ c(h0, { bbox: e.bbox, ghost: !e.bbox, className: "size-full" }) }),
        n && n.length > 0 ? /* @__PURE__ */ c("div", { className: "absolute top-2 right-2 z-20 flex items-center gap-1 transition-opacity lg:opacity-0 lg:group-focus-within:opacity-100 lg:group-hover:opacity-100 lg:has-[[aria-expanded=true]]:opacity-100", children: /* @__PURE__ */ c(
          m0,
          {
            label: `More for ${e.name}`,
            className: "[&>button]:size-7 [&>button]:rounded-[4px] [&>button]:border [&>button]:border-panel-edge [&>button]:bg-ground [&>button]:shadow-[var(--shadow-control)]",
            items: n
          }
        ) }) : null,
        /* @__PURE__ */ x("div", { className: "flex flex-col gap-1.5 px-[13px] py-[11px]", children: [
          /* @__PURE__ */ x("div", { className: "flex items-center gap-2", children: [
            i ? /* @__PURE__ */ c(P0, { name: e.name, onDone: (h) => s?.(h) }) : /* @__PURE__ */ c("h2", { className: "min-w-0 flex-1 truncate text-[13.5px] leading-[18px] font-semibold tracking-[-0.01em] text-ink", children: e.name }),
            a ? /* @__PURE__ */ c("span", { className: "text-warn", children: /* @__PURE__ */ c($, { name: "warning" }) }) : l ? /* @__PURE__ */ c(
              "span",
              {
                "data-build": u ? "running" : "stalled",
                className: `size-1.5 rounded-full bg-accent${u ? " motion-safe:animate-pulse" : ""}`
              }
            ) : e.status === "built" ? /* @__PURE__ */ c("span", { className: "text-pass", children: /* @__PURE__ */ c($, { name: "check" }) }) : null
          ] }),
          /* @__PURE__ */ x("p", { className: "mono-caption truncate text-muted normal-case [letter-spacing:0.08em]", children: [
            e.identifier ?? "",
            e.identifier && r ? " · " : "",
            r ? `${r} mm` : ""
          ] })
        ] }),
        /* @__PURE__ */ x("div", { className: "mono-caption flex items-center justify-between border-t border-line-soft px-[13px] py-2 text-muted [letter-spacing:0.08em]", children: [
          /* @__PURE__ */ c("span", { children: o ? `Built ${o}` : "Not built yet" }),
          /* @__PURE__ */ c("span", { className: a ? "text-warn" : void 0, children: a ? "Failed" : e.folder ?? $t(e.revision) })
        ] })
      ]
    }
  );
}
function P0({ name: e, onDone: t }) {
  const [n, i] = F(e), s = P(!1), r = (o) => {
    s.current || (s.current = !0, t(o && o.trim() && o.trim() !== e ? o.trim() : null));
  };
  return /* @__PURE__ */ c(
    "input",
    {
      autoFocus: !0,
      "aria-label": `Rename ${e}`,
      value: n,
      onFocus: (o) => o.currentTarget.select(),
      onChange: (o) => i(o.target.value),
      onBlur: () => r(n),
      onKeyDown: (o) => {
        o.key === "Enter" ? r(n) : o.key === "Escape" && r(null);
      },
      className: "relative z-20 h-[22px] min-w-0 flex-1 rounded-[2px] border border-accent bg-ground px-1 text-[13.5px] leading-[18px] font-semibold tracking-[-0.01em] text-ink focus:outline-none"
    }
  );
}
function jy({
  caption: e = "Describe a part and it builds here, live.",
  firstRun: t = !1,
  primary: n,
  secondary: i
}) {
  return /* @__PURE__ */ x("div", { className: "flex flex-1 flex-col items-center justify-center gap-7 pb-16", children: [
    /* @__PURE__ */ c("img", { src: Us.ghostBracket, alt: "", "aria-hidden": "true", className: "h-[300px] w-auto select-none" }),
    /* @__PURE__ */ x("div", { className: "flex flex-col items-center gap-2", children: [
      /* @__PURE__ */ c("h2", { className: "font-display text-[20px] leading-[26px] tracking-[-0.022em] text-balance text-ink", children: "Empty shelf. What’s rattling around your bench?" }),
      /* @__PURE__ */ c("p", { className: "mono-caption text-on-stage-muted [letter-spacing:0.11em]", children: e }),
      t ? /* @__PURE__ */ c("p", { className: "mt-1 max-w-[42ch] text-center text-[13px] leading-5 text-balance text-on-stage-muted", children: "Nothing on the plate yet. Your first part goes here, and the first layer is the one that matters." }) : null
    ] }),
    n || i ? /* @__PURE__ */ x("div", { className: "flex flex-col items-center gap-3", children: [
      n ? /* @__PURE__ */ c(Ae, { variant: "accent", size: "lg", icon: n.icon, onClick: n.onClick, children: n.label }) : null,
      i ? /* @__PURE__ */ c(Ae, { variant: "outline", size: "md", icon: i.icon, onClick: i.onClick, disabled: i.disabled, children: i.label }) : null
    ] }) : null
  ] });
}
function Uy({
  title: e = "No part yet",
  caption: t = "It appears here, live, as soon as the plan is set."
}) {
  return /* @__PURE__ */ x("div", { className: "relative flex min-h-[320px] flex-1 flex-col items-center justify-center gap-5 text-center", children: [
    /* @__PURE__ */ c("img", { src: Us.markOutline, alt: "", "aria-hidden": "true", className: "size-14 select-none" }),
    /* @__PURE__ */ x("div", { className: "flex flex-col items-center gap-2", children: [
      /* @__PURE__ */ c("p", { className: "mono-label text-on-stage-muted", children: e }),
      /* @__PURE__ */ c("p", { className: "max-w-[34ch] text-[15px] leading-[22px] text-balance text-ink-soft", children: t })
    ] })
  ] });
}
function zy({ header: e, children: t, className: n, style: i, topInset: s, dragRegion: r }) {
  return /* @__PURE__ */ x(
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
function M0({
  children: e,
  className: t,
  onContextMenu: n
}) {
  return /* @__PURE__ */ c(
    "div",
    {
      onContextMenu: n,
      className: R("relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden", t),
      children: e
    }
  );
}
function Wy({ children: e, className: t }) {
  return /* @__PURE__ */ c(M0, { className: R("items-center justify-center", t), children: e });
}
function _y({ start: e, cells: t, end: n, children: i, dragRegion: s }) {
  return /* @__PURE__ */ x(
    "header",
    {
      className: "panel chrome flex h-[52px] shrink-0 items-center overflow-hidden",
      ...s ? { "data-tauri-drag-region": !0 } : {},
      children: [
        e,
        t,
        i,
        n ? /* @__PURE__ */ x(_, { children: [
          /* @__PURE__ */ c("div", { className: "flex-1" }),
          n
        ] }) : null
      ]
    }
  );
}
function Gy() {
  return /* @__PURE__ */ c("div", { className: "h-full w-px bg-line" });
}
function bc({ children: e, className: t }) {
  return /* @__PURE__ */ c("div", { className: R("flex h-full items-center px-4", t), children: e });
}
function Ky({ label: e, value: t, className: n }) {
  return /* @__PURE__ */ c(bc, { className: n, children: /* @__PURE__ */ x("div", { className: "flex flex-col gap-[3px]", children: [
    /* @__PURE__ */ c("span", { className: "mono-label text-[9px] leading-[10px] text-faint", children: e }),
    /* @__PURE__ */ c("span", { className: "mono-value text-ink", children: t })
  ] }) });
}
const C0 = {
  pass: "bg-pass",
  warn: "bg-warn",
  fail: "bg-fail",
  none: "bg-line",
  building: "bg-accent motion-safe:animate-pulse"
}, E0 = {
  pass: "border-line bg-pass-wash",
  warn: "border-line bg-warn-wash",
  fail: "border-line bg-fail-wash",
  none: "border-transparent bg-transparent",
  building: "border-line bg-accent-wash"
}, _o = "transition-colors duration-(--duration-settle) ease-out-strong";
function Hy({
  tone: e,
  label: t,
  detail: n,
  className: i
}) {
  return /* @__PURE__ */ c(bc, { className: i, children: /* @__PURE__ */ x("span", { className: R("flex h-7 items-center gap-2 rounded-[3px] border px-2.5 whitespace-nowrap", _o, E0[e]), children: [
    /* @__PURE__ */ c("span", { className: R("size-1.5 shrink-0 rounded-full", _o, C0[e]) }),
    /* @__PURE__ */ c("span", { className: "mono-label text-ink", children: t }),
    n ? /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: n }) : null
  ] }) });
}
function qy({ children: e, className: t }) {
  return /* @__PURE__ */ c("div", { className: R("flex h-full items-center gap-1 px-3", t), children: e });
}
function Yy({ strip: e, picker: t, children: n, composer: i, hidden: s, dragRegion: r }) {
  return /* @__PURE__ */ x("section", { className: "panel flex w-[372px] shrink-0 flex-col overflow-hidden", hidden: s, children: [
    /* @__PURE__ */ c("div", { ...r ? { "data-tauri-drag-region": !0 } : {}, children: /* @__PURE__ */ c(
      js,
      {
        label: e.label,
        inset: 16,
        trailing: t || e.trailing ? /* @__PURE__ */ x("span", { className: "flex items-center gap-2", children: [
          e.trailing,
          t
        ] }) : void 0
      }
    ) }),
    /* @__PURE__ */ c("div", { className: "min-h-0 flex-1 overflow-y-auto", children: n }),
    /* @__PURE__ */ c("div", { className: "shrink-0 p-4 pt-0", children: i })
  ] });
}
function D0(e) {
  const t = Math.max(0, Math.round(e / 60));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function oi({ value: e, unit: t }) {
  return /* @__PURE__ */ x("span", { className: "flex items-baseline gap-1", children: [
    /* @__PURE__ */ c("span", { className: "mono-value text-ink", children: e }),
    /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: t })
  ] });
}
function V0({ children: e }) {
  return /* @__PURE__ */ x("div", { className: "chrome flex items-center gap-2 px-4 pt-[11px] pb-2", children: [
    /* @__PURE__ */ c("span", { className: "mono-caption text-faint [letter-spacing:0.12em]", children: e }),
    /* @__PURE__ */ c("span", { className: "h-px flex-1 bg-line-soft" })
  ] });
}
function Xy({
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
  return /* @__PURE__ */ x("aside", { className: "panel flex w-[288px] shrink-0 flex-col overflow-hidden", children: [
    /* @__PURE__ */ c(js, { label: "Parameters", inset: 16, trailing: e }),
    /* @__PURE__ */ x("div", { className: "flex min-h-0 flex-1 flex-col overflow-y-auto", children: [
      t && t.length > 0 ? /* @__PURE__ */ x(_, { children: [
        /* @__PURE__ */ c(V0, { children: "Set by the plan" }),
        /* @__PURE__ */ c("ul", { className: "flex flex-col gap-1.5 px-4 pb-1", children: t.map((u) => /* @__PURE__ */ x("li", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ c("span", { className: "shrink-0 text-faint", children: /* @__PURE__ */ c($, { name: "lock" }) }),
          /* @__PURE__ */ c("span", { className: "mono-label truncate text-muted", children: Pn(u.name) }),
          /* @__PURE__ */ c("span", { className: "flex-1" }),
          /* @__PURE__ */ c("span", { className: "mono-value text-right text-ink", children: u.value })
        ] }, u.name)) })
      ] }) : null,
      n
    ] }),
    /* @__PURE__ */ x("div", { className: "min-h-0 overflow-y-auto border-t border-line bg-ground", children: [
      i ? /* @__PURE__ */ x("div", { className: "chrome flex items-center justify-between px-4 py-2.5", children: [
        /* @__PURE__ */ c(oi, { value: i.grams == null ? "-" : String(Math.round(i.grams)), unit: "g" }),
        /* @__PURE__ */ c(oi, { value: i.seconds == null ? "-" : D0(i.seconds), unit: "hr" }),
        /* @__PURE__ */ c(oi, { value: i.heightMm == null ? "-" : String(Math.round(i.heightMm)), unit: "mm" })
      ] }) : null,
      /* @__PURE__ */ c("div", { className: "h-px bg-line-soft" }),
      l > 0 && !o ? /* @__PURE__ */ x("div", { className: "flex items-center gap-2 px-4 py-2", children: [
        /* @__PURE__ */ c("span", { className: r > 0 ? "text-fail" : "text-warn", children: /* @__PURE__ */ c($, { name: r > 0 ? "xmark" : "warning" }) }),
        /* @__PURE__ */ x("span", { className: "mono-label text-ink", children: [
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
const R0 = {
  warn: "warning",
  fail: "xmark",
  pass: "check",
  none: null
}, L0 = {
  warn: "text-warn",
  fail: "text-fail",
  pass: "text-pass",
  none: "text-muted"
};
function Zy({ label: e, summary: t, tone: n = "none", open: i, onToggle: s, children: r }) {
  const o = R0[n];
  return /* @__PURE__ */ x("div", { className: "flex flex-col", children: [
    /* @__PURE__ */ x(
      "button",
      {
        type: "button",
        onClick: s,
        "aria-expanded": i,
        className: "chrome flex h-8 w-full items-center gap-2 px-4 text-left hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent",
        children: [
          o ? /* @__PURE__ */ c("span", { className: R("shrink-0", L0[n]), children: /* @__PURE__ */ c($, { name: o }) }) : null,
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
const Go = X.out;
function wc(e, t = 900) {
  const [n, i] = F({ direction: null, from: e, changeId: 0, flashing: !1 }), s = P(e), r = P(null);
  return O(() => {
    const o = s.current;
    Object.is(o, e) || (s.current = e, e - o !== 0 && (i((a) => ({
      direction: e > o ? "up" : "down",
      from: o,
      changeId: a.changeId + 1,
      flashing: !0
    })), r.current && clearTimeout(r.current), r.current = setTimeout(() => {
      r.current = null, i((a) => a.flashing ? { ...a, flashing: !1 } : a);
    }, t)));
  }, [e, t]), O(() => () => r.current ? clearTimeout(r.current) : void 0, []), n;
}
function Qy({ value: e, format: t, label: n, hold: i = 900, className: s }) {
  const { direction: r, flashing: o, changeId: a } = wc(e, i), l = J(), u = t ? t(e) : String(e), [d, h] = F(u);
  O(() => {
    const g = setTimeout(() => h(u), 700);
    return () => clearTimeout(g);
  }, [u]);
  const f = { duration: l ? 0 : z.settle, ease: Go }, p = { duration: l ? 0 : z.tick * 2, ease: Go };
  return /* @__PURE__ */ x(
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
        /* @__PURE__ */ c("span", { "aria-hidden": !0, className: "relative inline-grid overflow-hidden", children: /* @__PURE__ */ c(de, { initial: !1, mode: "popLayout", children: /* @__PURE__ */ c(
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
        /* @__PURE__ */ c("span", { "aria-hidden": !0, className: "relative grid size-[1em] place-items-center", children: /* @__PURE__ */ c(de, { initial: !1, children: o && r ? /* @__PURE__ */ c(
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
const F0 = X.out;
function Jy({ findings: e, verdict: t, highlight: n, onHighlight: i }) {
  const s = J(), r = e.length, { direction: o, flashing: a } = wc(r), l = a && !s, u = o === "up", d = r > 0 ? `${r} ${r === 1 ? "finding" : "findings"} to fix.` : t === "none" ? "Nothing checked yet" : t === "fail" ? "The build stopped before the checks ran" : "Nothing to fix. Checks pass at these numbers.", h = /* @__PURE__ */ c(
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
  return r === 0 ? h : /* @__PURE__ */ x(_, { children: [
    h,
    /* @__PURE__ */ c("ul", { className: "flex flex-col", children: e.map((f, p) => (
      // Keyed by what the finding says, not by where it sits, so a rebuild that
      // changes nothing leaves the rows alone instead of replaying the entrance.
      /* @__PURE__ */ c(
        B.li,
        {
          initial: { opacity: 0, y: 4 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: s ? 0 : z.settle, ease: F0, delay: s ? 0 : p * 0.06 },
          children: /* @__PURE__ */ x(
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
                /* @__PURE__ */ x("span", { className: "flex min-w-0 flex-col gap-1", children: [
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
const O0 = X.out;
function ex({
  open: e = !0,
  revision: t,
  shownRevision: n,
  error: i
}) {
  const s = J();
  return /* @__PURE__ */ c(de, { children: e ? /* @__PURE__ */ x(
    B.div,
    {
      initial: { opacity: 0, y: -8 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -8 },
      transition: { duration: s ? 0 : z.settle, ease: O0 },
      className: "flex items-start gap-2 bg-fail-wash px-4 py-2.5",
      children: [
        /* @__PURE__ */ c("span", { className: "mt-0.5 shrink-0 text-fail", children: /* @__PURE__ */ c($, { name: "warning" }) }),
        /* @__PURE__ */ x("span", { className: "flex flex-col gap-1", children: [
          /* @__PURE__ */ x("span", { className: "mono-label text-fail", children: [
            $t(t),
            " failed at these values"
          ] }),
          i ? /* @__PURE__ */ c("span", { className: "text-chat text-ink", children: i }) : null,
          n != null ? /* @__PURE__ */ x("span", { className: "text-chat text-ink-soft", children: [
            "Showing ",
            $t(n).toLowerCase(),
            ", the last one that built."
          ] }) : null
        ] })
      ]
    }
  ) : null });
}
function tx({ children: e }) {
  return /* @__PURE__ */ x("div", { className: "panel chrome absolute top-4 left-4 flex h-7 items-center gap-2 rounded-full px-3", children: [
    /* @__PURE__ */ c("span", { className: "size-1.5 shrink-0 rounded-full bg-fail" }),
    /* @__PURE__ */ c("span", { className: "mono-label text-ink", children: e })
  ] });
}
const I0 = X.out;
function nx({ open: e, expected: t }) {
  return /* @__PURE__ */ c(de, { children: e ? /* @__PURE__ */ c(B0, { expected: t ?? null }, "building") : null });
}
function B0({ expected: e }) {
  const t = J(), [n] = F(() => performance.now()), [i, s] = F(0), [r, o] = F(!1);
  return O(() => {
    const a = setInterval(() => s((performance.now() - n) / 1e3), 100), l = requestAnimationFrame(() => o(!0));
    return () => {
      clearInterval(a), cancelAnimationFrame(l);
    };
  }, [n]), /* @__PURE__ */ x(
    B.div,
    {
      role: "status",
      initial: { opacity: 0, y: t ? 0 : -6 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: t ? 0 : -6 },
      transition: { duration: z.settle, ease: I0 },
      className: "panel chrome pointer-events-none absolute top-4 left-1/2 z-10 flex h-8 -translate-x-1/2 items-center gap-2.5 overflow-hidden rounded-full pr-3.5 pl-3",
      children: [
        /* @__PURE__ */ c(
          "span",
          {
            "aria-hidden": !0,
            className: "size-3 shrink-0 rounded-full border-[1.5px] border-accent/25 border-t-accent motion-safe:animate-spin"
          }
        ),
        /* @__PURE__ */ c("span", { className: "mono-label whitespace-nowrap text-ink", children: "Rebuilding" }),
        /* @__PURE__ */ c("span", { className: "mono-label w-9 text-right whitespace-nowrap text-muted tabular-nums", children: qt(i) }),
        e ? /* @__PURE__ */ c("span", { "aria-hidden": !0, className: "absolute inset-x-0 bottom-0 h-0.5 bg-accent/15", children: /* @__PURE__ */ c(
          "span",
          {
            className: "block h-full origin-left bg-accent ease-out",
            style: {
              transform: `scaleX(${r ? 0.92 : 0})`,
              transitionProperty: "transform",
              transitionDuration: t ? "0ms" : `${Math.max(0.3, e) * 1e3}ms`
            }
          }
        ) }) : null
      ]
    }
  );
}
const $0 = X.out;
function ix({
  version: e,
  installing: t = !1,
  onLater: n,
  onInstall: i,
  className: s
}) {
  const r = J() === !0, o = r ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } } : { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 8 } };
  return /* @__PURE__ */ x(
    B.div,
    {
      ...o,
      transition: { duration: r ? 0 : z.settle, ease: $0 },
      className: R("panel flex w-[260px] flex-col gap-2 p-4", s),
      role: "status",
      children: [
        /* @__PURE__ */ c("span", { className: "mono-caption text-muted", children: "Update" }),
        /* @__PURE__ */ x("div", { className: "flex flex-col gap-1", children: [
          /* @__PURE__ */ x("h2", { className: "font-display text-[15px] leading-5 tracking-[-0.02em] text-ink", children: [
            "nurb ",
            e,
            " is ready"
          ] }),
          /* @__PURE__ */ c("p", { className: "text-[13px] leading-[18px] text-muted", children: t ? "Closing and reopening nurb." : "Downloaded. Restart to finish." })
        ] }),
        /* @__PURE__ */ x("div", { className: "mt-1 flex items-center gap-2", children: [
          t || !n ? null : /* @__PURE__ */ c(Ae, { variant: "outline", onClick: n, children: "Later" }),
          /* @__PURE__ */ c(Ae, { variant: "accent", disabled: t, onClick: i, children: t ? "Restarting…" : "Restart now" })
        ] })
      ]
    }
  );
}
const j0 = X.out, Ko = [100, 93, 97, 88, 95, 91];
function U0(e, t) {
  return t > 1 && e === t - 1 ? 62 : Ko[(e * 7 + 3) % Ko.length];
}
function z0({ loading: e, delay: t = 120, minVisible: n = 380 }) {
  const [i, s] = F(!1), r = P(0);
  return O(() => {
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
function sx({
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
  const { showSkeleton: u } = z0({ loading: e, delay: r, minVisible: o }), d = J(), h = P(null), f = P(null), [p, g] = F(!1), v = s ?? n * i, b = { duration: d ? 0 : z.settle, ease: j0 };
  return O(() => {
    const w = h.current;
    if (!w || typeof ResizeObserver > "u") return;
    const T = () => g(w.scrollHeight - w.clientHeight > 1);
    T();
    const y = new ResizeObserver(T);
    return y.observe(w), f.current && y.observe(f.current), () => y.disconnect();
  }, []), /* @__PURE__ */ x(
    "div",
    {
      ref: h,
      "aria-busy": e,
      "aria-label": a,
      tabIndex: p ? 0 : void 0,
      style: { height: v },
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
        /* @__PURE__ */ c(de, { initial: !1, children: u ? /* @__PURE__ */ c(
          B.div,
          {
            "aria-hidden": !0,
            "data-skeleton": !0,
            className: "pointer-events-none col-start-1 row-start-1 w-full self-start",
            initial: { opacity: 0 },
            animate: { opacity: 1 },
            exit: { opacity: 0 },
            transition: b,
            children: Array.from({ length: n }, (w, T) => /* @__PURE__ */ c("div", { className: "flex items-center", style: { height: i }, children: /* @__PURE__ */ c("div", { className: "h-[8px] rounded-[3px] bg-raised", style: { width: `${U0(T, n)}%` } }) }, T))
          },
          "skeleton"
        ) : null }),
        a ? /* @__PURE__ */ c("span", { role: "status", className: "sr-only", children: e ? "" : `${a} loaded` }) : null
      ]
    }
  );
}
const Ho = X.out, qo = 0.35, W0 = 2200;
function rx({
  value: e,
  max: t = 100,
  segments: n,
  label: i = "Progress",
  pendingLabel: s = "Working",
  completeLabel: r = "Complete",
  className: o
}) {
  const a = J(), l = we(), [u, d] = F(0), h = e === null;
  O(() => {
    if (!h || a) return;
    const y = performance.now();
    let N = requestAnimationFrame(function V() {
      const C = qo * (1 - Math.exp(-(performance.now() - y) / W0));
      d((k) => Math.max(k, C)), qo - C > 2e-3 && (N = requestAnimationFrame(V));
    });
    return () => cancelAnimationFrame(N);
  }, [h, a]);
  const f = e === null || t <= 0 ? 0 : Math.min(1, Math.max(0, e / t)), p = Math.max(h ? u : 0, f), g = n ? Math.round(p * n) / n : p, v = Math.round(g * 100), b = !h && g >= 1, w = h ? {} : { "aria-valuenow": Math.round(f * t * 100) / 100, "aria-valuetext": `${v}%` }, T = { duration: a ? 0 : z.settle, ease: Ho };
  return /* @__PURE__ */ x("div", { className: R("w-full", o), children: [
    /* @__PURE__ */ x("div", { className: "flex items-baseline justify-between gap-3", children: [
      /* @__PURE__ */ c("span", { id: l, className: "mono-label truncate text-ink-soft", children: i }),
      /* @__PURE__ */ x("span", { "aria-hidden": !0, className: "grid shrink-0 justify-items-end", children: [
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
        /* @__PURE__ */ x(
          B.span,
          {
            className: "mono-value col-start-1 row-start-1 whitespace-nowrap text-ink",
            initial: !1,
            animate: { opacity: h ? 0 : 1 },
            transition: T,
            children: [
              v,
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
        children: n ? /* @__PURE__ */ c("div", { className: "flex h-full gap-px", "data-cells": n, children: Array.from({ length: n }, (y, N) => /* @__PURE__ */ c(
          B.span,
          {
            "data-lit": N < Math.round(g * n) ? "" : void 0,
            className: "h-full flex-1 bg-accent first:rounded-l-[3px] last:rounded-r-[3px]",
            initial: !1,
            animate: { opacity: N < Math.round(g * n) ? 1 : 0.12 },
            transition: { duration: a ? 0 : z.tick, ease: Ho }
          },
          N
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
const ai = X.out, Yo = { duration: 0 }, Xo = {
  warn: { surface: "bg-warn-wash border-warn/25", mark: "text-warn" },
  fail: { surface: "bg-fail-wash border-fail/25", mark: "text-fail" },
  neutral: { surface: "bg-raised border-line", mark: "text-ink" }
};
function _0({
  state: e,
  defaultState: t = "open",
  onStateChange: n,
  onDismiss: i
} = {}) {
  const [s, r] = F(t), o = e ?? s, a = P(n);
  a.current = n;
  const l = P(i);
  l.current = i;
  const u = Y((g) => {
    r(g), a.current?.(g);
  }, []), d = Y(() => u("folded"), [u]), h = Y(() => u("open"), [u]), f = Y(() => u(o === "open" ? "folded" : "open"), [u, o]), p = Y(() => {
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
function ox({
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
  const f = J() === !0, p = we(), g = `${p}-body`, v = `${p}-title`, { state: b, open: w, dismissed: T, toggle: y, fold: N, dismiss: V } = _0({
    state: o,
    defaultState: a,
    onStateChange: l,
    onDismiss: u
  }), C = !!(t || n || i), k = { duration: f ? 0 : z.settle, ease: ai };
  return /* @__PURE__ */ x(_, { children: [
    /* @__PURE__ */ c(
      B.div,
      {
        initial: { height: 0, opacity: 0 },
        animate: { height: T ? 0 : "auto", opacity: T ? 0 : 1 },
        transition: k,
        style: { overflow: "hidden" },
        children: /* @__PURE__ */ x(
          "div",
          {
            role: "region",
            "aria-labelledby": v,
            className: R("rounded-[12px] border", Xo[s].surface, h),
            children: [
              /* @__PURE__ */ x("div", { className: "flex items-center gap-2 p-2.5", children: [
                /* @__PURE__ */ c("span", { "aria-hidden": "true", className: R("flex shrink-0", Xo[s].mark), children: /* @__PURE__ */ c($, { name: s === "neutral" ? "box" : "warning" }) }),
                C ? /* @__PURE__ */ x(
                  "button",
                  {
                    type: "button",
                    onClick: y,
                    onKeyDown: (m) => {
                      m.key !== "Escape" || !w || (m.stopPropagation(), N());
                    },
                    "aria-expanded": w,
                    "aria-controls": g,
                    className: "chrome group flex min-w-0 flex-1 items-center gap-2 rounded-[3px] text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
                    children: [
                      /* @__PURE__ */ c("span", { id: v, className: "min-w-0 flex-1 truncate text-[13px] leading-5 font-medium text-ink", children: e }),
                      /* @__PURE__ */ c(
                        B.span,
                        {
                          "aria-hidden": "true",
                          className: "flex shrink-0 text-muted group-hover:text-ink",
                          initial: !1,
                          animate: { rotate: w ? 180 : 0 },
                          transition: f ? Yo : { duration: z.tick, ease: ai },
                          children: /* @__PURE__ */ c($, { name: "chevron-down" })
                        }
                      )
                    ]
                  }
                ) : /* @__PURE__ */ c("span", { id: v, className: "min-w-0 flex-1 truncate text-[13px] leading-5 font-medium text-ink", children: e }),
                r ? /* @__PURE__ */ c($s, { icon: "xmark", label: d, onClick: V }) : null
              ] }),
              C ? /* @__PURE__ */ c(
                B.div,
                {
                  id: g,
                  inert: !w,
                  initial: !1,
                  animate: { height: w ? "auto" : 0, opacity: w ? 1 : 0 },
                  transition: f ? Yo : { height: k, opacity: { duration: z.tick, ease: ai, delay: w ? 0.05 : 0 } },
                  style: { overflow: "hidden" },
                  children: /* @__PURE__ */ x("div", { className: "pr-2.5 pb-2.5 pl-[30px]", children: [
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
const G0 = X.out, Bi = { duration: 0 }, K0 = { duration: z.coast, ease: "linear", repeat: 1 / 0 };
function ax({ linger: e = 2e3 } = {}) {
  const [t, n] = F(null), i = P(0), s = P(null), r = Y(() => {
    s.current && clearTimeout(s.current), s.current = null;
  }, []), o = Y(
    (h) => {
      r(), i.current += 1;
      const f = `activity-${i.current}`;
      return n({ ...h, id: f, tone: "working" }), f;
    },
    [r]
  ), a = Y((h) => {
    n((f) => f && { ...f, ...h });
  }, []), l = Y(() => {
    r(), n(null);
  }, [r]), u = Y(
    (h) => {
      n((f) => f && { ...f, ...h, tone: "done" }), r(), s.current = setTimeout(() => {
        s.current = null, n(null);
      }, e);
    },
    [r, e]
  ), d = Y(
    (h) => {
      r(), n((f) => f && { ...f, ...h, tone: "fail" });
    },
    [r]
  );
  return O(() => r, [r]), { activity: t, start: o, update: a, succeed: u, fail: d, dismiss: l };
}
function lx({
  activity: e,
  onDismiss: t,
  label: n = "Activity",
  className: i
}) {
  const s = J() === !0, [r, o] = F(""), a = P(/* @__PURE__ */ new Set()), l = e?.tone ?? "working";
  return O(() => {
    if (!e) return;
    const u = `${e.id}:${l}`;
    a.current.has(u) || (a.current.add(u), o(
      l === "working" ? `${e.title} started.` : l === "done" ? `${e.title} finished.` : `${e.title} failed.`
    ));
  }, [e, l]), /* @__PURE__ */ x("div", { role: "region", "aria-label": n, className: R("pointer-events-none flex justify-center", i), children: [
    /* @__PURE__ */ c(de, { initial: !1, mode: "wait", children: e ? /* @__PURE__ */ x(
      B.div,
      {
        initial: s ? { opacity: 0 } : { opacity: 0, y: -10, scale: 0.94 },
        animate: { opacity: 1, y: 0, scale: 1 },
        exit: s ? { opacity: 0, transition: Bi } : { opacity: 0, y: -8, scale: 0.97 },
        transition: s ? Bi : { duration: z.settle, ease: G0 },
        style: { transformOrigin: "50% 0%" },
        className: "pointer-events-auto flex max-w-[320px] items-center gap-2 rounded-[12px] border border-line bg-ground px-3 py-2 shadow-[var(--shadow-panel)]",
        children: [
          /* @__PURE__ */ c(H0, { tone: l, reduced: s }),
          /* @__PURE__ */ x("span", { className: "min-w-0 flex-1", children: [
            /* @__PURE__ */ c("span", { className: "block truncate text-[13px] leading-5 font-medium text-ink", children: e.title }),
            e.detail ? /* @__PURE__ */ c("span", { className: "mono-caption block truncate text-muted", children: e.detail }) : null
          ] }),
          t && l !== "working" ? /* @__PURE__ */ c($s, { icon: "xmark", label: "Dismiss activity", onClick: t }) : null
        ]
      },
      e.id
    ) : null }),
    /* @__PURE__ */ c("span", { role: "status", "aria-live": "polite", className: "sr-only", children: r })
  ] });
}
function H0({ tone: e, reduced: t }) {
  return e === "done" ? /* @__PURE__ */ c("span", { className: "flex shrink-0 text-pass", "data-tone": "done", children: /* @__PURE__ */ c($, { name: "check" }) }) : e === "fail" ? /* @__PURE__ */ c("span", { className: "flex shrink-0 text-fail", "data-tone": "fail", children: /* @__PURE__ */ c($, { name: "warning" }) }) : /* @__PURE__ */ c(
    B.span,
    {
      className: "flex shrink-0 text-accent",
      "data-tone": "working",
      style: { transformOrigin: "50% 50%" },
      animate: t ? void 0 : { rotate: 360 },
      transition: t ? Bi : K0,
      children: /* @__PURE__ */ c($, { name: "loader" })
    }
  );
}
const q0 = X.out, Zo = { duration: 0 }, Y0 = (e) => `${e} new ${e === 1 ? "item" : "items"}`;
function cx({
  count: e,
  onClick: t,
  anchor: n = "bottom",
  label: i = Y0,
  className: s
}) {
  const r = J() === !0, [o, a] = F(0);
  O(() => {
    if (e === 0) {
      a(0);
      return;
    }
    const d = setTimeout(() => a(e), 700);
    return () => clearTimeout(d);
  }, [e]);
  const l = i(e), u = n === "bottom" ? 10 : -10;
  return /* @__PURE__ */ x(
    "div",
    {
      className: R(
        "pointer-events-none absolute inset-x-0 z-10 flex justify-center",
        n === "bottom" ? "bottom-2" : "top-2",
        s
      ),
      children: [
        /* @__PURE__ */ c(de, { initial: !1, children: e > 0 ? /* @__PURE__ */ x(
          B.button,
          {
            type: "button",
            onClick: t,
            "aria-label": l,
            initial: r ? { opacity: 0 } : { opacity: 0, scale: 0.94, y: u },
            animate: { opacity: 1, scale: 1, y: 0 },
            exit: r ? { opacity: 0, transition: Zo } : { opacity: 0, scale: 0.96, y: u * 0.5 },
            transition: r ? Zo : { duration: z.settle, ease: q0 },
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
const X0 = X.out;
function ux({
  options: e,
  label: t,
  value: n,
  onValueChange: i,
  className: s
}) {
  const r = we(), o = J(), a = P([]), [l, u] = F(null), d = e.findIndex((v) => v.value === n), h = d < 0 ? 0 : d, f = l ?? h, p = (v) => {
    const b = (v + e.length) % e.length;
    a.current[b]?.focus();
  }, g = (v) => {
    v !== n && ($e("toggle"), i(v));
  };
  return /* @__PURE__ */ c(
    "div",
    {
      role: "radiogroup",
      "aria-label": t,
      onBlur: (v) => {
        v.currentTarget.contains(v.relatedTarget) || u(null);
      },
      className: R(
        "chrome grid auto-cols-fr grid-flow-col gap-px rounded-[3px] border border-line bg-raised p-[2px]",
        s
      ),
      children: e.map((v, b) => /* @__PURE__ */ x(
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
          onClick: () => g(v.value),
          onKeyDown: (w) => {
            if (w.key === "ArrowRight" || w.key === "ArrowDown") p(b + 1);
            else if (w.key === "ArrowLeft" || w.key === "ArrowUp") p(b - 1);
            else if (w.key === "Home") p(0);
            else if (w.key === "End") p(e.length - 1);
            else if (w.key === "Enter" || w.key === " ") g(v.value);
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
                transition: { duration: o ? 0 : z.settle, ease: X0 },
                className: "absolute inset-0 rounded-[3px] bg-ground"
              }
            ) : null,
            /* @__PURE__ */ c("span", { className: "relative", children: v.label })
          ]
        },
        v.value
      ))
    }
  );
}
const kc = X.out, it = { duration: 0 };
function Z0({ steps: e, current: t, failed: n = !1 }) {
  const i = !n && t >= e.length, s = e.map((a, l) => ({
    ...a,
    status: l < t ? "done" : l === t && n ? "failed" : l === t && !i ? "active" : "pending"
  })), r = s.find((a) => a.status === "active"), o = n ? `Failed at ${e[Math.min(t, e.length - 1)]?.label ?? "step"}` : i ? `All ${e.length} steps complete` : r ? `${r.label}, step ${t + 1} of ${e.length}` : "";
  return { rows: s, complete: i, failed: n, sentence: o };
}
function Q0({ reduced: e }) {
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
      transition: { duration: e ? 0 : z.settle, ease: kc }
    }
  ) });
}
function J0() {
  return /* @__PURE__ */ c("svg", { viewBox: "0 0 256 256", width: "10", height: "10", fill: "none", "aria-hidden": !0, children: /* @__PURE__ */ c("path", { d: "M200 56 56 200 M56 56l144 144", stroke: "currentColor", strokeWidth: "26", strokeLinecap: "round" }) });
}
function ey({ reduced: e }) {
  return /* @__PURE__ */ x(
    B.svg,
    {
      viewBox: "0 0 16 16",
      className: "size-3",
      "aria-hidden": !0,
      animate: { rotate: e ? 0 : 360 },
      transition: e ? it : { duration: z.coast / 2, ease: "linear", repeat: 1 / 0 },
      children: [
        /* @__PURE__ */ c("circle", { cx: "8", cy: "8", r: "6", fill: "none", stroke: "currentColor", strokeOpacity: "0.25", strokeWidth: "2" }),
        /* @__PURE__ */ c("path", { d: "M8 2 a6 6 0 0 1 6 6", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round" })
      ]
    }
  );
}
const ty = {
  done: "text-ink-soft",
  active: "font-medium text-ink",
  failed: "font-medium text-fail",
  pending: "text-faint"
};
function dx({
  steps: e,
  current: t,
  failed: n = !1,
  label: i = "Task progress",
  className: s
}) {
  const { rows: r, complete: o, sentence: a } = Z0({ steps: e, current: t, failed: n }), l = J() === !0, [u, d] = F("");
  O(() => {
    if (!a) return;
    const f = setTimeout(() => d(a), 500);
    return () => clearTimeout(f);
  }, [a]);
  const h = { duration: l ? 0 : z.settle, ease: kc };
  return /* @__PURE__ */ x("div", { className: R("w-full", s), children: [
    /* @__PURE__ */ c("ol", { "aria-label": i, className: "space-y-0.5", children: r.map((f) => /* @__PURE__ */ x(
      "li",
      {
        "data-status": f.status,
        "aria-current": f.status === "active" ? "step" : void 0,
        className: "flex h-7 items-center gap-2.5 px-1",
        children: [
          /* @__PURE__ */ c("span", { className: "relative grid size-4 shrink-0 place-items-center", children: /* @__PURE__ */ c(de, { initial: !1, children: f.status === "done" ? /* @__PURE__ */ c(
            B.span,
            {
              className: "col-start-1 row-start-1 grid size-4 place-items-center rounded-[3px] bg-pass-wash text-pass",
              initial: { opacity: l ? 1 : 0 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: it },
              transition: h,
              children: /* @__PURE__ */ c(Q0, { reduced: l })
            },
            "done"
          ) : f.status === "failed" ? /* @__PURE__ */ c(
            B.span,
            {
              className: "col-start-1 row-start-1 grid size-4 place-items-center rounded-[3px] bg-fail-wash text-fail",
              initial: { opacity: l ? 1 : 0 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: it },
              transition: h,
              children: /* @__PURE__ */ c(J0, {})
            },
            "failed"
          ) : f.status === "active" ? /* @__PURE__ */ c(
            B.span,
            {
              className: "col-start-1 row-start-1 text-accent",
              initial: { opacity: l ? 1 : 0 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: it },
              transition: h,
              children: /* @__PURE__ */ c(ey, { reduced: l })
            },
            "active"
          ) : /* @__PURE__ */ c(
            B.span,
            {
              className: "col-start-1 row-start-1 size-[5px] rounded-[3px] bg-line",
              initial: { opacity: 1 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: it },
              transition: it
            },
            "pending"
          ) }) }),
          /* @__PURE__ */ c("span", { className: R("mono-id min-w-0 flex-1 truncate transition-colors", ty[f.status]), children: f.label }),
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
const ny = X.out, Tc = /-?\d*\.?\d+/g, iy = "12", sy = {
  "check-close": [
    ["M 5 12.5 L 10 17.5 L 19.5 7", "M 12 12 L 12 12 L 12 12"],
    ["M 6.5 6.5 L 12 12 L 17.5 17.5", "M 17.5 6.5 L 12 12 L 6.5 17.5"]
  ],
  "plus-minus": [
    ["M 5 12 L 19 12", "M 12 5 L 12 19"],
    ["M 5 12 L 19 12", "M 5 12 L 19 12"]
  ]
};
function ry(e) {
  const t = e.match(Tc);
  return !t || t.length < 4 ? !1 : t.every((n, i) => n === t[i % 2]);
}
function oy(e, t) {
  const n = e.reduce((s, r) => Math.max(s, r.length), 0), i = e[t] ?? e[0];
  return Array.from({ length: n }, (s, r) => {
    const o = i[r], a = e.find((u) => u[r] !== void 0)?.[r] ?? "", l = o ?? a.replace(Tc, iy);
    return { key: r, d: l, visible: !ry(l) };
  });
}
function fx({
  preset: e = "check-close",
  active: t = 0,
  size: n = 12,
  strokeWidth: i = 1.75,
  label: s,
  className: r
}) {
  const o = sy[e], a = typeof t == "boolean" ? t ? 1 : 0 : Math.min(Math.max(Math.trunc(t), 0), 1), l = le(() => oy(o, a), [o, a]), d = J() ? { duration: 0 } : { duration: z.settle, ease: ny };
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
const Sc = X.out;
function ay({ value: e }) {
  const t = J() === !0;
  return /* @__PURE__ */ c("span", { className: "relative inline-flex h-[13px] overflow-hidden leading-[13px] tabular-nums", children: /* @__PURE__ */ c(de, { initial: !1, mode: "popLayout", children: /* @__PURE__ */ c(
    B.span,
    {
      initial: t ? { opacity: 0 } : { y: 13, opacity: 0 },
      animate: { y: 0, opacity: 1 },
      exit: t ? { opacity: 0 } : { y: -13, opacity: 0 },
      transition: { duration: t ? 0 : z.tick, ease: Sc },
      children: e
    },
    e
  ) }) });
}
function hx({
  questions: e,
  onAnswer: t,
  className: n
}) {
  const [i, s] = F(0), r = P(!1), o = e.length;
  O(() => {
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
  return /* @__PURE__ */ x("div", { className: R("flex flex-col gap-2.5 rounded-[6px] bg-raised p-3", n), children: [
    u > 1 ? /* @__PURE__ */ x("div", { className: "flex items-center gap-1", children: [
      /* @__PURE__ */ x("span", { "aria-hidden": "true", className: "mono-caption flex items-center gap-1 text-faint", children: [
        /* @__PURE__ */ c(ay, { value: d }),
        "of ",
        u
      ] }),
      /* @__PURE__ */ x("span", { className: "sr-only", children: [
        "Question ",
        d,
        " of ",
        u
      ] })
    ] }) : null,
    /* @__PURE__ */ c(B.div, { style: a.style, animate: a.animate, transition: a.transition, onAnimationComplete: a.onAnimationComplete, children: /* @__PURE__ */ c("div", { ref: a.ref, children: /* @__PURE__ */ c(de, { initial: !1, mode: "popLayout", children: /* @__PURE__ */ x(
      B.div,
      {
        initial: { y: 12, opacity: 0 },
        animate: { y: 0, opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: z.settle, ease: Sc },
        className: "flex flex-col gap-2.5",
        children: [
          /* @__PURE__ */ c("p", { className: "text-chat text-ink", children: l.title }),
          l.detail ? /* @__PURE__ */ c("p", { className: "mono-caption text-muted", children: l.detail }) : null,
          /* @__PURE__ */ c("div", { className: "flex flex-wrap gap-1.5", children: l.actions.map((f) => /* @__PURE__ */ c(Ae, { variant: f.variant ?? "outline", onClick: () => h(f.id), children: f.label }, f.id)) })
        ]
      },
      l.id
    ) }) }) })
  ] });
}
const ly = /def\s+\w+\s*\(([\s\S]*?)\)\s*(?:->[^:]*?)?:/;
function cy(e) {
  const t = [];
  let n = 0, i = 0;
  for (let s = 0; s < e.length; s++) {
    const r = e[s];
    r === "(" || r === "[" || r === "{" ? n++ : r === ")" || r === "]" || r === "}" ? n-- : r === "," && n === 0 && (t.push(e.slice(i, s)), i = s + 1);
  }
  return t.push(e.slice(i)), t;
}
function Qo(e) {
  const t = /* @__PURE__ */ new Map(), n = e.match(ly);
  if (!n) return t;
  for (const i of cy(n[1])) {
    const s = i.indexOf("=");
    if (s < 0) continue;
    const r = i.slice(0, s).split(":")[0].trim(), o = i.slice(s + 1).trim();
    !/^[A-Za-z_]\w*$/.test(r) || !o || t.set(r, o);
  }
  return t;
}
function uy(e, t) {
  const n = Qo(e), i = Qo(t), s = [];
  for (const [r, o] of i) {
    const a = n.get(r);
    a === void 0 ? s.push(`added ${r}`) : a !== o && s.push(`${r} ${a} to ${o}`);
  }
  for (const r of n.keys())
    i.has(r) || s.push(`removed ${r}`);
  return s;
}
function dy(e, t) {
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
function fy(e) {
  if (!e || typeof e != "object") return null;
  const t = e, n = typeof t.part_name == "string" ? t.part_name : null;
  return n ? typeof t.old_string == "string" && typeof t.new_string == "string" ? { name: n, before: t.old_string, after: t.new_string } : typeof t.source == "string" ? { name: n, after: t.source } : null : null;
}
const Jo = 12;
function px({ input: e, className: t }) {
  const [n, i] = F(null), [s, r] = F(!1), o = Is(n !== null), a = fy(e), l = a?.before !== void 0 ? uy(a.before, a.after) : [];
  if (!a) return null;
  const u = l.length > 0 ? l : [`edited ${a.name}`], d = dy(a.before ?? "", a.after), h = s ? d : d.slice(0, Jo);
  return /* @__PURE__ */ x("div", { className: R("flex flex-col gap-1.5", t), children: [
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
    /* @__PURE__ */ c(B.div, { style: o.style, animate: o.animate, transition: o.transition, onAnimationComplete: o.onAnimationComplete, children: /* @__PURE__ */ c("div", { ref: o.ref, children: n !== null && d.length > 0 ? /* @__PURE__ */ x("div", { className: "flex flex-col rounded-[3px] bg-raised py-1", children: [
      h.map((f, p) => /* @__PURE__ */ x(
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
      !s && d.length > Jo ? /* @__PURE__ */ c(
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
const Nc = X.out;
function mx({ active: e, label: t = "Drop the photo here" }) {
  const n = J() === !0;
  return /* @__PURE__ */ c(de, { initial: !1, children: e ? /* @__PURE__ */ c(
    B.div,
    {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
      transition: { duration: n ? 0 : z.tick, ease: Nc },
      className: "pointer-events-none absolute inset-0 z-10 flex items-center justify-center rounded-[6px] border border-dashed border-accent bg-accent-wash",
      children: /* @__PURE__ */ c("span", { className: "btn-label text-accent-ink", children: t })
    }
  ) : null });
}
function gx({
  lines: e,
  active: t,
  everyMs: n = 4e3,
  className: i
}) {
  const [s, r] = F(0), o = J() === !0;
  return O(() => {
    if (!t || e.length < 2) return;
    const a = setInterval(() => r((l) => (l + 1) % e.length), n);
    return () => clearInterval(a);
  }, [t, e.length, n]), !t || e.length === 0 ? null : /* @__PURE__ */ c("span", { "aria-hidden": "true", className: R("pointer-events-none absolute inset-0 block", i), children: /* @__PURE__ */ c(de, { initial: !1, children: /* @__PURE__ */ c(
    B.span,
    {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
      transition: { duration: o ? 0 : z.settle, ease: Nc },
      className: "absolute inset-x-0 top-0 block",
      children: e[s % e.length]
    },
    s % e.length
  ) }) });
}
export {
  sg as ASSISTANT_MARKDOWN_DISALLOWED_ELEMENTS,
  Oy as AddPrinterDialog,
  hx as ApprovalCard,
  Cy as AssistantMarkdown,
  N0 as BlurUpImage,
  My as BuildCard,
  ex as BuildFailedBanner,
  Ae as Button,
  Yy as ChatPanel,
  ox as CollapsibleBanner,
  Iy as ConfirmDialog,
  gx as CyclingPlaceholder,
  qg as DetentMarks,
  mx as DropHint,
  px as EditChips,
  Uy as EmptyProject,
  jy as EmptyShelf,
  Ly as ExportMenu,
  Jy as FindingsList,
  fc as Floating,
  _y as FloatingHeader,
  bc as HeaderCell,
  Gy as HeaderDivider,
  qy as HeaderIcons,
  Ky as HeaderStack,
  Hy as HeaderStatus,
  v0 as HoldToConfirm,
  $ as Icon,
  $s as IconButton,
  fx as IconMorph,
  h0 as IsoBox,
  lx as LiveActivity,
  Kg as LoadingButton,
  By as Lockup,
  Dy as MeasurementCard,
  m0 as Menu,
  cx as NewItemsPill,
  js as PanelStrip,
  Xy as ParamRail,
  e0 as ParamSlider,
  Ry as ParamsPanel,
  $y as PartCard,
  Fy as PrinterMenu,
  rx as ProgressBar,
  Zy as RailDisclosure,
  ux as SegmentedControl,
  sx as SkeletonSwap,
  Ey as SpecCard,
  zy as Stage,
  nx as StageBuilding,
  M0 as StageColumn,
  Wy as StageEmpty,
  tx as StageNotice,
  dx as TaskSteps,
  ec as ToolStepCard,
  tg as ToolStepGroup,
  ix as UpdateCard,
  Qy as ValueFlash,
  Vy as ViewerIsland,
  Ii as adjustable,
  s0 as bedLine,
  Us as brand,
  dy as changedLines,
  lg as changedSize,
  Zl as clock,
  $e as cue,
  uc as decimals,
  uy as diffDefaults,
  Xg as dirtyValues,
  z as duration,
  X as ease,
  qt as elapsedLabel,
  Hm as formatBbox,
  Py as initials,
  Qo as keywordDefaults,
  wy as readSoundPrefs,
  Km as relativeTime,
  $t as rev,
  ky as setSoundEnabled,
  Ty as setSoundVolume,
  Yg as sliderRange,
  fy as sourceEdit,
  Ay as stackLabel,
  ht as tidy,
  _g as useAsyncAction,
  Is as useAutoHeight,
  S0 as useBlurUpImage,
  _0 as useCollapsibleBanner,
  g0 as useContextMenu,
  Sy as useCopyToClipboard,
  x0 as useHoldToConfirm,
  ax as useLiveActivity,
  z0 as useSkeletonSwap,
  Hg as useSliderDetents,
  Z0 as useTaskSteps,
  wc as useValueFlash,
  Pn as words
};
