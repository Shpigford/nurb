import * as Qn from "react";
import { useSyncExternalStore as Zu, useState as B, useRef as D, useEffect as O, useCallback as Q, createContext as Ct, useLayoutEffect as Nt, useId as Se, useContext as ue, useInsertionEffect as wr, useMemo as de, Children as Ju, isValidElement as ef, Fragment as kr, createElement as tf, forwardRef as Tr, Component as nf } from "react";
import { jsx as d, jsxs as v, Fragment as U } from "react/jsx-runtime";
import V from "clsx";
import rf from "react-markdown";
import { DirectionalLight as sf, HemisphereLight as of, Mesh as lt, PlaneGeometry as af, MeshStandardMaterial as Sr, ReplaceStencilOp as li, NotEqualStencilFunc as lf, DoubleSide as Ar, Group as Fn, LineSegments as Cr, EdgesGeometry as Qa, LineBasicMaterial as mt, BufferGeometry as Nr, BufferAttribute as Pr, MeshBasicMaterial as Wt, SphereGeometry as cf, Box3 as Ht, Vector3 as pe, Quaternion as Ls, IncrementWrapStencilOp as ci, BackSide as uf, AlwaysStencilFunc as ff, DecrementWrapStencilOp as ui, FrontSide as df, Frustum as hf, Matrix4 as pf, BoxGeometry as mf, Scene as gf, Color as Vs, PerspectiveCamera as yf, Plane as xf, WebGLRenderer as bf, Vector2 as vf, Raycaster as wf } from "three";
import { OrbitControls as kf } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader as Fs } from "three/addons/loaders/GLTFLoader.js";
import { createPortal as Za } from "react-dom";
const Ja = {
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
function Tf(e) {
  return typeof e == "string" && Object.prototype.hasOwnProperty.call(Ja, e);
}
const Mr = 0.05, Sf = 0.05, Af = 1e-3, Cf = 4;
function Nf(e, t, n, i) {
  const r = e.createOscillator();
  if (r.type = n.waveform, r.frequency.setValueAtTime(n.frequency, i), n.detune && (r.detune.value = n.detune), n.glideTo !== void 0) {
    const s = n.glideTime ?? n.attack + n.decay;
    r.frequency.exponentialRampToValueAtTime(n.glideTo, i + s);
  }
  const o = e.createGain();
  o.gain.setValueAtTime(1e-4, i), o.gain.exponentialRampToValueAtTime(n.peak, i + n.attack), o.gain.exponentialRampToValueAtTime(1e-4, i + n.attack + n.decay), r.connect(o).connect(t), r.start(i), r.stop(i + n.attack + n.decay + Mr);
}
function Pf(e, t, n, i) {
  const r = n.attack + n.decay + Mr, o = Math.max(1, Math.floor(r * e.sampleRate)), s = e.createBuffer(1, o, e.sampleRate), a = s.getChannelData(0);
  for (let f = 0; f < o; f++)
    a[f] = 2 * Math.random() - 1;
  const l = e.createBufferSource();
  l.buffer = s;
  const c = e.createBiquadFilter();
  c.type = n.filterType, c.frequency.value = n.filterFrequency, n.filterQ !== void 0 && (c.Q.value = n.filterQ);
  const u = e.createGain();
  u.gain.setValueAtTime(1e-4, i), u.gain.exponentialRampToValueAtTime(n.peak, i + n.attack), u.gain.exponentialRampToValueAtTime(1e-4, i + n.attack + n.decay), l.connect(c).connect(u).connect(t), l.start(i), l.stop(i + r);
}
function Mf(e, t, n, i) {
  const r = e.createDelay(1);
  r.delayTime.value = i.delay;
  const o = e.createBiquadFilter();
  o.type = "lowpass", o.frequency.value = i.lowpass;
  const s = e.createGain();
  s.gain.value = i.feedback;
  const a = e.createGain();
  return a.gain.value = i.wet, t.connect(r), r.connect(o), o.connect(s), s.connect(r), o.connect(a), a.connect(n), [r, o, s, a];
}
function Ef(e) {
  return Math.max(...e.layers.map((t) => (t.offset ?? 0) + t.attack + t.decay + Mr));
}
function Df(e) {
  return !e || e.feedback <= 0 ? 0 : e.feedback >= 1 ? e.delay : e.delay * (1 + Math.ceil(Math.log(Af) / Math.log(e.feedback)));
}
let fi = null;
function Rf(e) {
  if (fi)
    return fi;
  const t = e.createGain();
  t.gain.value = Cf;
  const n = e.createDynamicsCompressor();
  return n.threshold.value = -8, n.knee.value = 6, n.ratio.value = 12, n.attack.value = 2e-3, n.release.value = 0.08, t.connect(n).connect(e.destination), fi = t, t;
}
function Is(e, t, n) {
  const i = e.currentTime, r = Rf(e), o = e.createGain();
  o.gain.value = t.masterGain * n, o.connect(r);
  const s = t.shimmer ? Mf(e, o, r, t.shimmer) : [];
  for (const l of t.layers) {
    const c = i + (l.offset ?? 0);
    l.kind === "tone" ? Nf(e, o, l, c) : Pf(e, o, l, c);
  }
  const a = (Ef(t) + Df(t.shimmer) + Sf) * 1e3;
  setTimeout(() => {
    o.disconnect();
    for (const l of s)
      l.disconnect();
  }, a);
}
let hn = null, Bi = !0, ji = 1;
function el(e, t) {
  return typeof e == "number" && Number.isFinite(e) ? Math.min(1, Math.max(0, e)) : t;
}
function Lf(e) {
  typeof e == "boolean" && (Bi = e);
}
function Vf(e) {
  ji = el(e, ji);
}
function Ff() {
  if (hn)
    return hn;
  if (typeof window > "u")
    return null;
  const e = window.AudioContext ?? window.webkitAudioContext;
  if (!e)
    return null;
  try {
    hn = new e();
  } catch {
    return null;
  }
  return hn;
}
function If(e = "chime", t) {
  if (!Bi || !Tf(e) || typeof navigator < "u" && navigator.userActivation?.hasBeenActive === !1)
    return;
  const n = ji * el(t?.volume, 1);
  if (n === 0)
    return;
  const i = Ff();
  if (!i)
    return;
  const r = Ja[e];
  if (i.state === "running")
    Is(i, r, n);
  else
    try {
      i.resume().then(() => {
        Bi && i.state === "running" && Is(i, r, n);
      }, () => {
      });
    } catch {
    }
}
const wt = "nurb-sound-enabled", Er = "nurb-sound-volume", Os = "nurb-completion-sound", Dr = 0.6;
function et(e) {
  try {
    return localStorage.getItem(e);
  } catch {
    return null;
  }
}
function In(e, t) {
  try {
    t === null ? localStorage.removeItem(e) : localStorage.setItem(e, t);
  } catch {
  }
}
function Rr(e) {
  return Number.isFinite(e) ? Math.min(1, Math.max(0, e)) : Dr;
}
function Bv() {
  const e = et(Os);
  e !== null && (e === "off" && et(wt) === null && In(wt, "off"), In(Os, null));
  const t = et(wt) !== "off", n = et(Er), i = n === null ? Dr : Rr(Number(n));
  return Lr(t, i), { enabled: t, volume: i };
}
function jv(e) {
  In(wt, e ? null : "off"), Lr(e, Of());
}
function $v(e) {
  const t = Rr(e);
  In(Er, String(t)), Lr(et(wt) !== "off", t);
}
function Of() {
  const e = et(Er);
  return e === null ? Dr : Rr(Number(e));
}
function Lr(e, t) {
  try {
    Lf(e), Vf(t);
  } catch {
  }
}
function qe(e, t) {
  if (!(typeof window > "u") && et(wt) !== "off")
    try {
      If(e, t);
    } catch {
    }
}
const $i = "nurb-theme", tl = typeof matchMedia == "function" ? matchMedia("(prefers-color-scheme: dark)") : null;
function Bf() {
  let e = null;
  try {
    e = localStorage.getItem($i);
  } catch {
  }
  return e === "light" || e === "dark" ? e : "system";
}
function zi() {
  const e = Bf(), t = e === "dark" || e === "system" && !!tl?.matches;
  document.documentElement.dataset.theme = t ? "dark" : "light";
}
function zv(e) {
  try {
    e === "system" ? localStorage.removeItem($i) : localStorage.setItem($i, e);
  } catch {
  }
  zi();
}
function _v() {
  zi(), tl?.addEventListener("change", zi);
}
const nl = () => document.documentElement.dataset.theme === "dark", jf = (e) => {
  const t = new MutationObserver(e);
  return t.observe(document.documentElement, { attributes: !0, attributeFilter: ["data-theme"] }), () => t.disconnect();
}, $f = () => Zu(jf, nl, () => !1), _ = {
  tick: 0.09,
  settle: 0.24,
  arrive: 0.42,
  coast: 1.4
}, Z = {
  out: [0.23, 1, 0.32, 1],
  inOut: [0.65, 0, 0.35, 1]
};
function Uv({ timeout: e = 1500, onCopy: t, onError: n } = {}) {
  const [i, r] = B("idle"), o = D(null);
  O(() => () => {
    o.current && clearTimeout(o.current);
  }, []);
  const s = Q(
    (l) => {
      r(l), o.current && clearTimeout(o.current), o.current = setTimeout(() => r("idle"), e);
    },
    [e]
  ), a = Q(
    async (l) => {
      try {
        if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(l);
        else if (!zf(l)) throw new Error("clipboard unavailable");
        qe("success"), t?.(l), s("copied");
      } catch (c) {
        qe("error"), n?.(c), s("error");
      }
    },
    [t, n, s]
  );
  return { status: i, copy: a };
}
function zf(e) {
  const t = document.createElement("textarea");
  t.value = e, t.setAttribute("readonly", ""), t.style.position = "fixed", t.style.opacity = "0", document.body.appendChild(t);
  try {
    return t.select(), document.execCommand("copy");
  } finally {
    t.remove();
  }
}
const _f = {
  share: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("path", { d: "M6 1V8.75" }),
    /* @__PURE__ */ d("path", { d: "M8.25 3L6 0.75L3.75 3" }),
    /* @__PURE__ */ d("path", { d: "M3 5.25H2.75C1.645 5.25 0.75 6.145 0.75 7.25V9.25C0.75 10.355 1.645 11.25 2.75 11.25H9.25C10.355 11.25 11.25 10.355 11.25 9.25V7.25C11.25 6.145 10.355 5.25 9.25 5.25H9" })
  ] }),
  "chevron-left": /* @__PURE__ */ d("polyline", { points: "7.75 1.75 3.5 6 7.75 10.25" }),
  "chevron-down": /* @__PURE__ */ d("polyline", { points: "1.75 4.25 6 8.5 10.25 4.25" }),
  "chevron-up": /* @__PURE__ */ d("polyline", { points: "10.25 7.75 6 3.5 1.75 7.75" }),
  check: /* @__PURE__ */ d("path", { d: "m1.76,7.004l2.25,3L10.24,1.746" }),
  warning: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("circle", { cx: "6", cy: "10.125", r: ".875", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ d("line", { x1: "6", y1: "4.75", x2: "6", y2: "7.75" }),
    /* @__PURE__ */ d("path", { d: "m8.625,10.25h1.164c1.123,0,1.826-1.216,1.265-2.189L7.265,1.484c-.562-.975-1.969-.975-2.53,0L.946,8.061c-.561.973.142,2.189,1.265,2.189h1.164" })
  ] }),
  lock: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("line", { x1: "6", y1: "7.5", x2: "6", y2: "8.5" }),
    /* @__PURE__ */ d("path", { d: "m3.75,4.75v-1.75c0-1.243,1.007-2.25,2.25-2.25h0c1.243,0,2.25,1.007,2.25,2.25v1.75" }),
    /* @__PURE__ */ d("rect", { x: "1.25", y: "4.75", width: "9.5", height: "6.5", rx: "1.5", ry: "1.5" })
  ] }),
  plus: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("line", { x1: "10.75", y1: "6", x2: "1.25", y2: "6" }),
    /* @__PURE__ */ d("line", { x1: "6", y1: "10.75", x2: "6", y2: "1.25" })
  ] }),
  minus: /* @__PURE__ */ d("line", { x1: "10.75", y1: "6", x2: "1.25", y2: "6" }),
  camera: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("circle", { cx: "3.25", cy: "5.75", r: ".75", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ d("rect", { x: ".75", y: "3.25", width: "10.5", height: "8", rx: "2", ry: "2" }),
    /* @__PURE__ */ d("line", { x1: "2.75", y1: ".75", x2: "4.75", y2: ".75" }),
    /* @__PURE__ */ d("circle", { cx: "7.25", cy: "7.25", r: "1", fill: "currentColor" })
  ] }),
  search: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("line", { x1: "7.652", y1: "7.652", x2: "10.75", y2: "10.75" }),
    /* @__PURE__ */ d("circle", { cx: "5", cy: "5", r: "3.75" })
  ] }),
  xmark: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("line", { x1: "2.25", y1: "9.75", x2: "9.75", y2: "2.25" }),
    /* @__PURE__ */ d("line", { x1: "9.75", y1: "9.75", x2: "2.25", y2: "2.25" })
  ] }),
  image: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("path", { d: "m2.32,10.516l4.723-4.723c.391-.391,1.024-.391,1.414,0l2.293,2.293" }),
    /* @__PURE__ */ d("circle", { cx: "4", cy: "4", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ d("rect", { x: "1.25", y: "1.25", width: "9.5", height: "9.5", rx: "2", ry: "2" })
  ] }),
  download: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("line", { x1: "6", y1: "7.75", x2: "6", y2: ".75" }),
    /* @__PURE__ */ d("polyline", { points: "3.75 5.75 6 8 8.25 5.75" }),
    /* @__PURE__ */ d("path", { d: "m8.69,2.75c1.028,0,1.888.779,1.99,1.801l.35,3.5c.118,1.177-.807,2.199-1.99,2.199H2.96c-1.183,0-2.108-1.022-1.99-2.199l.35-3.5c.102-1.022.963-1.801,1.99-1.801" })
  ] }),
  expand: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("path", { d: "m1.25,4.25v-1c0-1.105.895-2,2-2h1" }),
    /* @__PURE__ */ d("path", { d: "m7.75,1.25h1c1.105,0,2,.895,2,2v1" }),
    /* @__PURE__ */ d("path", { d: "m10.75,7.75v1c0,1.105-.895,2-2,2h-1" }),
    /* @__PURE__ */ d("path", { d: "m4.25,10.75h-1c-1.105,0-2-.895-2-2v-1" })
  ] }),
  eye: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("path", { d: "M5.99997 10.25C8.64947 10.25 10.2021 8.38538 10.9485 7.12628C11.3599 6.43238 11.3599 5.56762 10.9485 4.87372C10.2021 3.61462 8.64937 1.75 5.99997 1.75C3.42267 1.75 1.87667 3.53288 1.10727 4.78918C0.649466 5.53658 0.649466 6.46338 1.10727 7.21088C1.87667 8.46718 3.42267 10.25 5.99997 10.25Z" }),
    /* @__PURE__ */ d("circle", { cx: "6", cy: "6", r: "1.25", fill: "currentColor" })
  ] }),
  "arrow-up": /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("line", { x1: "6", y1: "11", x2: "6", y2: "1.25" }),
    /* @__PURE__ */ d("polyline", { points: "9.25 4.25 6 1 2.75 4.25" })
  ] }),
  link: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("path", { d: "M7 7C7.97631 6.02369 7.97631 4.44078 7 3.46447L5.55292 2.01788C4.57661 1.04157 2.9937 1.04157 2.01739 2.01788C1.05869 2.97658 1.0414 4.5202 1.96552 5.5" }),
    /* @__PURE__ */ d("path", { d: "M5 5C4.02369 5.97631 4.02369 7.55922 5 8.53553L6.44197 9.97758C7.41828 10.9539 9.00119 10.9539 9.9775 9.97758C10.9347 9.02036 10.9534 7.48002 10.0336 6.5" })
  ] }),
  stop: /* @__PURE__ */ d(
    "path",
    {
      d: "M3.75 11C2.23122 11 1 9.76878 1 8.25V3.75C1 2.23122 2.23122 1 3.75 1L8.25 1C9.76878 1 11 2.23122 11 3.75V8.25C11 9.76878 9.76878 11 8.25 11H3.75Z",
      fill: "currentColor",
      stroke: "none"
    }
  ),
  chat: /* @__PURE__ */ d("path", { d: "m8.75,8.75h-4.75l-2.75,2.5V3.25c0-1.105.895-2,2-2h5.5c1.105,0,2,.895,2,2v3.5c0,1.105-.895,2-2,2Z" }),
  loader: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("path", { d: "M6 2.25V0.75" }),
    /* @__PURE__ */ d("path", { opacity: "0.5", d: "M6 11.25V9.75" }),
    /* @__PURE__ */ d("path", { opacity: "0.75", d: "M9.75488 5.995L11.2549 5.995" }),
    /* @__PURE__ */ d("path", { opacity: "0.25", d: "M0.754883 5.995L2.25488 5.995" }),
    /* @__PURE__ */ d("path", { opacity: "0.88", d: "M8.65321 3.3449L9.71387 2.28424" }),
    /* @__PURE__ */ d("path", { opacity: "0.38", d: "M2.28895 9.70885L3.34961 8.64819" }),
    /* @__PURE__ */ d("path", { opacity: "0.63", d: "M8.66004 8.64811L9.7207 9.70877" }),
    /* @__PURE__ */ d("path", { opacity: "0.13", d: "M2.29627 2.28416L3.35693 3.34482" })
  ] }),
  dots: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("circle", { cx: "6", cy: "6", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ d("circle", { cx: "2", cy: "6", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ d("circle", { cx: "10", cy: "6", r: "1", fill: "currentColor", stroke: "none" })
  ] }),
  trash: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("line", { x1: "1", y1: "2.25", x2: "11", y2: "2.25" }),
    /* @__PURE__ */ d("path", { d: "m4.75,2.25v-1c0-.276.224-.5.5-.5h1.5c.276,0,.5.224.5.5v1" }),
    /* @__PURE__ */ d("path", { d: "m9.5,4.75l-.195,5.058c-.031.805-.693,1.442-1.499,1.442h-3.613c-.806,0-1.468-.637-1.499-1.442l-.195-5.058" })
  ] }),
  ruler: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("line", { x1: "6.623", y1: "6.623", x2: "7.754", y2: "7.754" }),
    /* @__PURE__ */ d("line", { x1: "7.873", y1: "4.373", x2: "9.504", y2: "6.004" }),
    /* @__PURE__ */ d("line", { x1: "4.373", y1: "7.873", x2: "6.004", y2: "9.504" }),
    /* @__PURE__ */ d("rect", { x: ".42", y: "3.52", width: "11.161", height: "4.96", rx: "1.086", ry: "1.086", transform: "translate(-2.485 6) rotate(-45)" })
  ] }),
  gear: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("circle", { cx: "6", cy: "6", r: ".75", fill: "currentColor" }),
    /* @__PURE__ */ d("circle", { cx: "6", cy: "6", r: "4" }),
    /* @__PURE__ */ d("line", { x1: "6", y1: ".75", x2: "6", y2: "2" }),
    /* @__PURE__ */ d("line", { x1: "9.086", y1: "1.753", x2: "8.351", y2: "2.764" }),
    /* @__PURE__ */ d("line", { x1: "10.993", y1: "4.378", x2: "9.804", y2: "4.764" }),
    /* @__PURE__ */ d("line", { x1: "10.993", y1: "7.622", x2: "9.804", y2: "7.236" }),
    /* @__PURE__ */ d("line", { x1: "9.086", y1: "10.247", x2: "8.351", y2: "9.236" }),
    /* @__PURE__ */ d("line", { x1: "6", y1: "11.25", x2: "6", y2: "10" }),
    /* @__PURE__ */ d("line", { x1: "2.914", y1: "10.247", x2: "3.649", y2: "9.236" }),
    /* @__PURE__ */ d("line", { x1: "1.007", y1: "7.622", x2: "2.196", y2: "7.236" }),
    /* @__PURE__ */ d("line", { x1: "1.007", y1: "4.378", x2: "2.196", y2: "4.764" }),
    /* @__PURE__ */ d("line", { x1: "2.914", y1: "1.753", x2: "3.649", y2: "2.764" })
  ] }),
  user: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("circle", { cx: "6", cy: "2.491", r: "1.75" }),
    /* @__PURE__ */ d("path", { d: "m9.425,10.458c.551-.255.759-.92.458-1.446-.773-1.349-2.215-2.262-3.882-2.262s-3.11.912-3.882,2.262c-.301.526-.093,1.192.458,1.446,2.283,1.056,4.566,1.056,6.849,0Z" })
  ] }),
  logout: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("path", { d: "M5.75 3.25V2.25c0-.828.672-1.5 1.5-1.5h2.5c.828 0 1.5.672 1.5 1.5v7.5c0 .828-.672 1.5-1.5 1.5h-2.5c-.828 0-1.5-.672-1.5-1.5v-1" }),
    /* @__PURE__ */ d("line", { x1: "8.25", y1: "6", x2: "1", y2: "6" }),
    /* @__PURE__ */ d("polyline", { points: "3 3.75 .75 6 3 8.25" })
  ] }),
  box: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("line", { x1: "1.25", y1: "3.75", x2: "10.75", y2: "3.75" }),
    /* @__PURE__ */ d("line", { x1: "6", y1: ".75", x2: "6", y2: "3.75" }),
    /* @__PURE__ */ d("line", { x1: "3.75", y1: "8.25", x2: "5.25", y2: "8.25" }),
    /* @__PURE__ */ d("path", { d: "m1.25,3.75l1.461-2.504c.179-.307.508-.496.864-.496h4.851c.356,0,.685.189.864.496l1.461,2.504v5c0,1.105-.895,2-2,2H3.25c-1.105,0-2-.895-2-2V3.75Z" })
  ] }),
  copy: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("rect", { x: "3.25", y: ".75", width: "8", height: "8", rx: "1.5", ry: "1.5" }),
    /* @__PURE__ */ d("path", { d: "m8.25,11.25H2.25c-.828,0-1.5-.672-1.5-1.5V3.75" })
  ] }),
  folder: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("path", { d: "m.75,7.25V3.25c0-1.105.895-2,2-2h1.701c.607,0,1.18.275,1.56.748l.603.752h2.636c1.105,0,2,.895,2,2v2.5" }),
    /* @__PURE__ */ d("path", { d: "m2.75,5.25h6.5c1.105,0,2,.895,2,2v1.5c0,1.105-.895,2-2,2H2.75c-1.105,0-2-.895-2-2v-1.5c0-1.105.895-2,2-2Z" })
  ] }),
  tag: /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d("circle", { cx: "4", cy: "4", r: "1", fill: "currentColor", stroke: "none" }),
    /* @__PURE__ */ d("path", { d: "m1.25,2.25v3.086c0,.265.105.52.293.707l4.105,4.105c.781.781,2.047.781,2.828,0l1.672-1.672c.781-.781.781-2.047,0-2.828L6.043,1.543c-.188-.188-.442-.293-.707-.293h-3.086c-.552,0-1,.448-1,1Z" })
  ] }),
  pointer: /* @__PURE__ */ d("path", { d: "m1.455.814l9.367,3.422c.447.163.434.801-.019.946l-4.258,1.363-1.363,4.258c-.145.454-.782.467-.946.019L.814,1.455c-.146-.399.242-.787.641-.641Z" })
};
function z({ name: e, className: t, ...n }) {
  return /* @__PURE__ */ d(
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
      children: _f[e]
    }
  );
}
const Vr = Ct({});
function tn(e) {
  const t = D(null);
  return t.current === null && (t.current = e()), t.current;
}
const Uf = typeof window < "u", Gt = Uf ? Nt : O, nn = /* @__PURE__ */ Ct(null);
function Fr(e, t) {
  e.indexOf(t) === -1 && e.push(t);
}
function ot(e, t) {
  const n = e.indexOf(t);
  n > -1 && e.splice(n, 1);
}
const Pe = (e, t, n) => n > t ? t : n < e ? e : n;
function _i(e, t) {
  return t ? `${e}. For more information and steps for solving, visit https://motion.dev/troubleshooting/${t}` : e;
}
let ct = () => {
}, Te = () => {
};
typeof process < "u" && process.env?.NODE_ENV !== "production" && (ct = (e, t, n) => {
  !e && typeof console < "u" && console.warn(_i(t, n));
}, Te = (e, t, n) => {
  if (!e)
    throw new Error(_i(t, n));
});
const je = {}, Ir = (e) => /^-?(?:\d+(?:\.\d+)?|\.\d+)$/u.test(e), Or = (e) => typeof e == "object" && e !== null, Br = (e) => /^0[^.\s]+$/u.test(e);
// @__NO_SIDE_EFFECTS__
function il(e) {
  let t;
  return () => (t === void 0 && (t = e()), t);
}
const Ne = /* @__NO_SIDE_EFFECTS__ */ (e) => e, rn = (...e) => e.reduce((t, n) => (i) => n(t(i))), St = /* @__NO_SIDE_EFFECTS__ */ (e, t, n) => {
  const i = t - e;
  return i ? (n - e) / i : 1;
};
class On {
  constructor() {
    this.subscriptions = [];
  }
  add(t) {
    return Fr(this.subscriptions, t), () => this.remove(t);
  }
  remove(t) {
    ot(this.subscriptions, t);
  }
  notify(t, n, i) {
    const r = this.subscriptions.length;
    if (r)
      if (r === 1)
        this.subscriptions[0](t, n, i);
      else
        for (let o = 0; o < r; o++) {
          const s = this.subscriptions[o];
          s && s(t, n, i);
        }
  }
  getSize() {
    return this.subscriptions.length;
  }
  clear() {
    this.subscriptions.length = 0;
  }
}
const xe = /* @__NO_SIDE_EFFECTS__ */ (e) => e * 1e3, ve = /* @__NO_SIDE_EFFECTS__ */ (e) => e / 1e3, rl = /* @__NO_SIDE_EFFECTS__ */ (e, t) => t ? e * (1e3 / t) : 0, Bs = /* @__PURE__ */ new Set();
function Zn(e, t, n) {
  e || Bs.has(t) || (console.warn(_i(t, n)), Bs.add(t));
}
const Wf = (e, t, n) => {
  const i = t - e;
  return ((n - e) % i + i) % i + e;
}, sl = (e, t, n) => (((1 - 3 * n + 3 * t) * e + (3 * n - 6 * t)) * e + 3 * t) * e, Hf = 1e-7, Gf = 12;
function Kf(e, t, n, i, r) {
  let o, s, a = 0;
  do
    s = t + (n - t) / 2, o = sl(s, i, r) - e, o > 0 ? n = s : t = s;
  while (Math.abs(o) > Hf && ++a < Gf);
  return s;
}
// @__NO_SIDE_EFFECTS__
function sn(e, t, n, i) {
  if (e === t && n === i)
    return Ne;
  const r = (o) => Kf(o, 0, 1, e, n);
  return (o) => o === 0 || o === 1 ? o : sl(r(o), t, i);
}
const ol = /* @__NO_SIDE_EFFECTS__ */ (e) => (t) => t <= 0.5 ? e(2 * t) / 2 : (2 - e(2 * (1 - t))) / 2, jr = /* @__NO_SIDE_EFFECTS__ */ (e) => (t) => 1 - e(1 - t), al = /* @__PURE__ */ sn(0.33, 1.53, 0.69, 0.99), $r = /* @__PURE__ */ jr(al), ll = /* @__PURE__ */ ol($r), cl = (e) => e >= 1 ? 1 : (e *= 2) < 1 ? 0.5 * $r(e) : 0.5 * (2 - Math.pow(2, -10 * (e - 1))), zr = (e) => 1 - Math.sin(Math.acos(e)), ul = /* @__PURE__ */ jr(zr), fl = /* @__PURE__ */ ol(zr), qf = /* @__PURE__ */ sn(0.42, 0, 1, 1), Yf = /* @__PURE__ */ sn(0, 0, 0.58, 1), dl = /* @__PURE__ */ sn(0.42, 0, 0.58, 1), hl = /* @__NO_SIDE_EFFECTS__ */ (e) => Array.isArray(e) && typeof e[0] != "number";
// @__NO_SIDE_EFFECTS__
function pl(e, t) {
  return /* @__PURE__ */ hl(e) ? e[Wf(0, e.length, t)] : e;
}
const ml = /* @__NO_SIDE_EFFECTS__ */ (e) => Array.isArray(e) && typeof e[0] == "number", js = {
  linear: Ne,
  easeIn: qf,
  easeInOut: dl,
  easeOut: Yf,
  circIn: zr,
  circInOut: fl,
  circOut: ul,
  backIn: $r,
  backInOut: ll,
  backOut: al,
  anticipate: cl
}, Xf = (e) => typeof e == "string", $s = (e) => {
  if (/* @__PURE__ */ ml(e)) {
    Te(e.length === 4, "Cubic bezier arrays must contain four numerical values.", "cubic-bezier-length");
    const [t, n, i, r] = e;
    return /* @__PURE__ */ sn(t, n, i, r);
  } else if (Xf(e))
    return Te(js[e] !== void 0, `Invalid easing type '${e}'`, "invalid-easing-type"), js[e];
  return e;
}, pn = [
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
function Qf(e) {
  let t = /* @__PURE__ */ new Set(), n = /* @__PURE__ */ new Set(), i = !1, r = !1;
  const o = /* @__PURE__ */ new Set();
  let s = {
    delta: 0,
    timestamp: 0,
    isProcessing: !1
  };
  function a(c) {
    o.has(c) && (n.add(c), e()), c(s);
  }
  const l = {
    /**
     * Schedule a process to run on the next frame.
     */
    schedule: (c, u = !1, f = !1) => {
      const m = f && i ? t : n;
      return u && o.add(c), m.add(c), c;
    },
    /**
     * Cancel the provided callback from running on the next frame.
     */
    cancel: (c) => {
      n.delete(c), o.delete(c);
    },
    /**
     * Execute all schedule callbacks.
     */
    process: (c) => {
      if (s = c, i) {
        r = !0;
        return;
      }
      i = !0;
      const u = t;
      t = n, n = u, t.forEach(a), t.clear(), i = !1, r && (r = !1, l.process(c));
    }
  };
  return l;
}
const Zf = 40;
function gl(e, t) {
  let n = !1, i = !0;
  const r = {
    delta: 0,
    timestamp: 0,
    isProcessing: !1
  }, o = () => n = !0, s = pn.reduce((x, S) => (x[S] = Qf(o), x), {}), { setup: a, read: l, resolveKeyframes: c, preUpdate: u, update: f, preRender: h, render: m, postRender: p } = s, g = () => {
    const x = je.useManualTiming, S = x ? r.timestamp : performance.now();
    n = !1, x || (r.delta = i ? 1e3 / 60 : Math.max(Math.min(S - r.timestamp, Zf), 1)), r.timestamp = S, r.isProcessing = !0, a.process(r), l.process(r), c.process(r), u.process(r), f.process(r), h.process(r), m.process(r), p.process(r), r.isProcessing = !1, n && t && (i = !1, e(g));
  }, y = () => {
    n = !0, i = !0, r.isProcessing || e(g);
  };
  return { schedule: pn.reduce((x, S) => {
    const E = s[S];
    return x[S] = (C, A = !1, N = !1) => (n || y(), E.schedule(C, A, N)), x;
  }, {}), cancel: (x) => {
    for (let S = 0; S < pn.length; S++)
      s[pn[S]].cancel(x);
  }, state: r, steps: s };
}
const { schedule: K, cancel: $e, state: ae, steps: di } = /* @__PURE__ */ gl(typeof requestAnimationFrame < "u" ? requestAnimationFrame : Ne, !0);
let An;
function Jf() {
  An = void 0;
}
const fe = {
  now: () => (An === void 0 && fe.set(ae.isProcessing || je.useManualTiming ? ae.timestamp : performance.now()), An),
  set: (e) => {
    An = e, queueMicrotask(Jf);
  }
}, kt = (e) => Math.round(e * 1e5) / 1e5, yl = (e) => (t) => typeof t == "string" && t.startsWith(e), xl = /* @__PURE__ */ yl("--"), ed = /* @__PURE__ */ yl("var(--"), _r = (e) => ed(e) ? td.test(e.split("/*")[0].trim()) : !1, td = /var\(--(?:[\w-]+\s*|[\w-]+\s*,(?:\s*[^)(\s]|\s*\((?:[^)(]|\([^)(]*\))*\))+\s*)\)$/iu;
function zs(e) {
  return typeof e != "string" ? !1 : e.split("/*")[0].includes("var(--");
}
const Pt = {
  test: (e) => typeof e == "number",
  parse: parseFloat,
  transform: (e) => e
}, Kt = {
  ...Pt,
  transform: (e) => Pe(0, 1, e)
}, mn = {
  ...Pt,
  default: 1
}, Ur = /-?(?:\d+(?:\.\d+)?|\.\d+)/gu;
function nd(e) {
  return e == null;
}
const id = /^(?:#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\))$/iu, Wr = (e, t) => (n) => !!(typeof n == "string" && id.test(n) && n.startsWith(e) || t && !nd(n) && Object.prototype.hasOwnProperty.call(n, t)), bl = (e, t, n) => (i) => {
  if (typeof i != "string")
    return i;
  const [r, o, s, a] = i.match(Ur);
  return {
    [e]: parseFloat(r),
    [t]: parseFloat(o),
    [n]: parseFloat(s),
    alpha: a !== void 0 ? parseFloat(a) : 1
  };
}, rd = (e) => Pe(0, 255, e), hi = {
  ...Pt,
  transform: (e) => Math.round(rd(e))
}, tt = {
  test: /* @__PURE__ */ Wr("rgb", "red"),
  parse: /* @__PURE__ */ bl("red", "green", "blue"),
  transform: ({ red: e, green: t, blue: n, alpha: i = 1 }) => "rgba(" + hi.transform(e) + ", " + hi.transform(t) + ", " + hi.transform(n) + ", " + kt(Kt.transform(i)) + ")"
};
function sd(e) {
  let t = "", n = "", i = "", r = "";
  return e.length > 5 ? (t = e.substring(1, 3), n = e.substring(3, 5), i = e.substring(5, 7), r = e.substring(7, 9)) : (t = e.substring(1, 2), n = e.substring(2, 3), i = e.substring(3, 4), r = e.substring(4, 5), t += t, n += n, i += i, r += r), {
    red: parseInt(t, 16),
    green: parseInt(n, 16),
    blue: parseInt(i, 16),
    alpha: r ? parseInt(r, 16) / 255 : 1
  };
}
const Ui = {
  test: /* @__PURE__ */ Wr("#"),
  parse: sd,
  transform: tt.transform
}, on = /* @__NO_SIDE_EFFECTS__ */ (e) => ({
  test: (t) => typeof t == "string" && t.endsWith(e) && t.split(" ").length === 1,
  parse: parseFloat,
  transform: (t) => `${t}${e}`
}), Ie = /* @__PURE__ */ on("deg"), Le = /* @__PURE__ */ on("%"), L = /* @__PURE__ */ on("px"), od = /* @__PURE__ */ on("vh"), ad = /* @__PURE__ */ on("vw"), _s = {
  ...Le,
  parse: (e) => Le.parse(e) / 100,
  transform: (e) => Le.transform(e * 100)
}, gt = {
  test: /* @__PURE__ */ Wr("hsl", "hue"),
  parse: /* @__PURE__ */ bl("hue", "saturation", "lightness"),
  transform: ({ hue: e, saturation: t, lightness: n, alpha: i = 1 }) => "hsla(" + Math.round(e) + ", " + Le.transform(kt(t)) + ", " + Le.transform(kt(n)) + ", " + kt(Kt.transform(i)) + ")"
}, le = {
  test: (e) => tt.test(e) || Ui.test(e) || gt.test(e),
  parse: (e) => tt.test(e) ? tt.parse(e) : gt.test(e) ? gt.parse(e) : Ui.parse(e),
  transform: (e) => typeof e == "string" ? e : e.hasOwnProperty("red") ? tt.transform(e) : gt.transform(e),
  getAnimatableNone: (e) => {
    const t = le.parse(e);
    return t.alpha = 0, le.transform(t);
  }
}, ld = /(?:#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\))/giu, vl = /* @__PURE__ */ new RegExp(Ur.source), wl = /* @__PURE__ */ new RegExp(ld.source, "i");
function cd(e) {
  return isNaN(e) && typeof e == "string" && (vl.test(e) || wl.test(e));
}
const kl = "number", Tl = "color", ud = "var", fd = "var(", Us = "${}", dd = /var\s*\(\s*--(?:[\w-]+\s*|[\w-]+\s*,(?:\s*[^)(\s]|\s*\((?:[^)(]|\([^)(]*\))*\))+\s*)\)|#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\)|-?(?:\d+(?:\.\d+)?|\.\d+)/giu;
function hd(e) {
  const t = e.toString();
  return vl.test(t) || wl.test(t);
}
function qt(e) {
  const t = e.toString(), n = [], i = {
    color: [],
    number: [],
    var: []
  }, r = [];
  let o = 0;
  const a = t.replace(dd, (l) => (le.test(l) ? (i.color.push(o), r.push(Tl), n.push(le.parse(l))) : l.startsWith(fd) ? (i.var.push(o), r.push(ud), n.push(l)) : (i.number.push(o), r.push(kl), n.push(parseFloat(l))), ++o, Us)).split(Us);
  return { values: n, split: a, indexes: i, types: r };
}
function pd(e) {
  return qt(e).values;
}
function Sl({ split: e, types: t }) {
  const n = e.length;
  return (i) => {
    let r = "";
    for (let o = 0; o < n; o++)
      if (r += e[o], i[o] !== void 0) {
        const s = t[o];
        s === kl ? r += kt(i[o]) : s === Tl ? r += le.transform(i[o]) : r += i[o];
      }
    return r;
  };
}
function md(e) {
  return Sl(qt(e));
}
const gd = (e) => typeof e == "number" ? 0 : le.test(e) ? le.getAnimatableNone(e) : e, yd = (e, t) => typeof e == "number" ? t?.trim().endsWith("/") ? e : 0 : gd(e);
function xd(e) {
  const t = qt(e);
  return Sl(t)(t.values.map((i, r) => yd(i, t.split[r])));
}
const ke = {
  test: cd,
  parse: pd,
  createTransformer: md,
  getAnimatableNone: xd
};
function pi(e, t, n) {
  return n < 0 && (n += 1), n > 1 && (n -= 1), n < 1 / 6 ? e + (t - e) * 6 * n : n < 1 / 2 ? t : n < 2 / 3 ? e + (t - e) * (2 / 3 - n) * 6 : e;
}
function bd({ hue: e, saturation: t, lightness: n, alpha: i }) {
  e /= 360, t /= 100, n /= 100;
  let r = 0, o = 0, s = 0;
  if (!t)
    r = o = s = n;
  else {
    const a = n < 0.5 ? n * (1 + t) : n + t - n * t, l = 2 * n - a;
    r = pi(l, a, e + 1 / 3), o = pi(l, a, e), s = pi(l, a, e - 1 / 3);
  }
  return {
    red: Math.round(r * 255),
    green: Math.round(o * 255),
    blue: Math.round(s * 255),
    alpha: i
  };
}
function Bn(e, t) {
  return (n) => n > 0 ? t : e;
}
const Y = (e, t, n) => e + (t - e) * n, mi = (e, t, n) => {
  const i = e * e, r = n * (t * t - i) + i;
  return r < 0 ? 0 : Math.sqrt(r);
}, vd = [Ui, tt, gt], wd = (e) => vd.find((t) => t.test(e));
function Ws(e) {
  const t = wd(e);
  if (!t)
    return ct(!1, `'${e}' is not an animatable color. Use the equivalent color code instead.`, "color-not-animatable"), !1;
  let n = t.parse(e);
  return t === gt && (n = bd(n)), n;
}
const Hs = (e, t) => {
  const n = Ws(e), i = Ws(t);
  if (!n || !i)
    return Bn(e, t);
  const r = { ...n };
  return (o) => (r.red = mi(n.red, i.red, o), r.green = mi(n.green, i.green, o), r.blue = mi(n.blue, i.blue, o), r.alpha = Y(n.alpha, i.alpha, o), tt.transform(r));
}, Wi = /* @__PURE__ */ new Set(["none", "hidden"]);
function kd(e, t) {
  return Wi.has(e) ? (n) => n <= 0 ? e : t : (n) => n >= 1 ? t : e;
}
function Td(e, t) {
  return (n) => Y(e, t, n);
}
function Hr(e) {
  return typeof e == "number" ? Td : typeof e == "string" ? _r(e) ? Bn : le.test(e) ? Hs : Cd : Array.isArray(e) ? Al : typeof e == "object" ? le.test(e) ? Hs : Sd : Bn;
}
function Al(e, t) {
  const n = [...e], i = n.length, r = e.map((o, s) => Hr(o)(o, t[s]));
  return (o) => {
    for (let s = 0; s < i; s++)
      n[s] = r[s](o);
    return n;
  };
}
function Sd(e, t) {
  const n = { ...e, ...t }, i = {};
  for (const r in n)
    e[r] !== void 0 && t[r] !== void 0 && (i[r] = Hr(e[r])(e[r], t[r]));
  return (r) => {
    for (const o in i)
      n[o] = i[o](r);
    return n;
  };
}
function Ad(e, t) {
  const n = [], i = { color: 0, var: 0, number: 0 };
  for (let r = 0; r < t.values.length; r++) {
    const o = t.types[r], s = e.indexes[o][i[o]], a = e.values[s] ?? 0;
    n[r] = a, i[o]++;
  }
  return n;
}
const Cd = (e, t) => {
  const n = ke.createTransformer(t), i = qt(e), r = qt(t);
  return i.indexes.var.length === r.indexes.var.length && i.indexes.color.length === r.indexes.color.length && i.indexes.number.length >= r.indexes.number.length ? Wi.has(e) && !r.values.length || Wi.has(t) && !i.values.length ? kd(e, t) : rn(Al(Ad(i, r), r.values), n) : (ct(!0, `Complex values '${e}' and '${t}' too different to mix. Ensure all colors are of the same type, and that each contains the same quantity of number and color values. Falling back to instant transition.`, "complex-values-different"), Bn(e, t));
}, Gs = /^(-?(?:\d+(?:\.\d*)?|\.\d+))([a-z%]*)$/iu;
function Nd(e, t) {
  const n = Gs.exec(e);
  if (!n)
    return;
  const i = Gs.exec(t);
  if (!i || n[2] !== i[2])
    return;
  const r = n[2], o = parseFloat(n[1]), s = parseFloat(i[1]);
  return (a) => kt(Y(o, s, a)) + r;
}
function Gr(e, t, n) {
  if (typeof e == "number" && typeof t == "number" && typeof n == "number")
    return Y(e, t, n);
  if (typeof e == "string" && typeof t == "string") {
    const r = Nd(e, t);
    if (r)
      return r;
  }
  return Hr(e)(e, t);
}
const Pd = (e) => {
  const t = ({ timestamp: n }) => e(n);
  return {
    start: (n = !0) => K.update(t, n),
    stop: () => $e(t),
    /**
     * If we're processing this frame we can use the
     * framelocked timestamp to keep things in sync.
     */
    now: () => ae.isProcessing ? ae.timestamp : fe.now()
  };
}, Cl = (e, t, n = 10) => {
  let i = "";
  const r = Math.max(Math.round(t / n), 2);
  for (let o = 0; o < r; o++)
    i += Math.round(e(o / (r - 1)) * 1e4) / 1e4 + ", ";
  return `linear(${i.substring(0, i.length - 2)})`;
}, Kr = 2e4;
function qr(e, t = 50, n = Kr, i) {
  let r = 0, o = e.next(r);
  for (; !o.done && r < n; )
    r += t, o = e.next(r);
  return r >= n ? 1 / 0 : r;
}
function Nl(e, t = 100, n) {
  const i = n({ ...e, keyframes: [0, t] }), r = Math.min(qr(i), Kr);
  return {
    type: "keyframes",
    ease: (o) => i.next(r * o).value / t,
    duration: /* @__PURE__ */ ve(r)
  };
}
const J = {
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
function Hi(e, t) {
  return e * Math.sqrt(1 - t * t);
}
const Md = 12;
function Ed(e, t, n) {
  let i = n;
  for (let r = 1; r < Md; r++)
    i = i - e(i) / t(i);
  return i;
}
const gi = 1e-3;
function Dd({ duration: e = J.duration, bounce: t = J.bounce, velocity: n = J.velocity, mass: i = J.mass }) {
  let r, o;
  ct(e <= /* @__PURE__ */ xe(J.maxDuration), "Spring duration must be 10 seconds or less", "spring-duration-limit");
  let s = 1 - t;
  s = Pe(J.minDamping, J.maxDamping, s), e = Pe(J.minDuration, J.maxDuration, /* @__PURE__ */ ve(e)), s < 1 ? (r = (c) => {
    const u = c * s, f = u * e, h = u - n, m = Hi(c, s), p = Math.exp(-f);
    return gi - h / m * p;
  }, o = (c) => {
    const f = c * s * e, h = f * n + n, m = s * s * c * c * e, p = Math.exp(-f), g = Hi(c * c, s);
    return (-r(c) + gi > 0 ? -1 : 1) * ((h - m) * p) / g;
  }) : (r = (c) => {
    const u = Math.exp(-c * e), f = (c - n) * e + 1;
    return -gi + u * f;
  }, o = (c) => {
    const u = Math.exp(-c * e), f = (n - c) * (e * e);
    return u * f;
  });
  const a = 5 / e, l = Ed(r, o, a);
  if (e = /* @__PURE__ */ xe(e), isNaN(l))
    return {
      stiffness: J.stiffness,
      damping: J.damping,
      duration: e
    };
  {
    const c = l * l * i;
    return {
      stiffness: c,
      damping: s * 2 * Math.sqrt(i * c),
      duration: e
    };
  }
}
const Pl = ["duration", "bounce"], Ml = ["stiffness", "damping", "mass"];
function jn(e, t) {
  return t.some((n) => e[n] !== void 0);
}
function Rd(e) {
  let t = {
    velocity: J.velocity,
    stiffness: J.stiffness,
    damping: J.damping,
    mass: J.mass,
    isResolvedFromDuration: !1,
    ...e
  };
  if (!jn(e, Ml) && jn(e, Pl))
    if (t.velocity = 0, e.visualDuration) {
      const n = e.visualDuration, i = 2 * Math.PI / (n * 1.2), r = i * i, o = 2 * Pe(0.05, 1, 1 - (e.bounce || 0)) * Math.sqrt(r);
      t = {
        ...t,
        mass: J.mass,
        stiffness: r,
        damping: o
      };
    } else {
      const n = Dd({ ...e, velocity: 0 });
      t = {
        ...t,
        ...n,
        mass: J.mass
      }, t.isResolvedFromDuration = !0;
    }
  return t;
}
function Yt(e = J.visualDuration, t = J.bounce) {
  const n = typeof e != "object" ? {
    visualDuration: e,
    keyframes: [0, 1],
    bounce: t
  } : e, i = n.keyframes[0], r = n.keyframes[n.keyframes.length - 1], o = { done: !1, value: i }, { stiffness: s, damping: a, mass: l, duration: c, velocity: u, isResolvedFromDuration: f } = Rd({
    ...n,
    velocity: -/* @__PURE__ */ ve(n.velocity || 0)
  }), h = a / (2 * Math.sqrt(s * l)), m = /* @__PURE__ */ ve(Math.sqrt(s / l)), p = h * m, g = {
    target: r,
    delta: r - i,
    velocity: u || 0,
    restSpeed: 0,
    restDelta: 0
  }, y = () => {
    const A = Math.abs(g.delta) < 5;
    g.restSpeed = n.restSpeed || (A ? J.restSpeed.granular : J.restSpeed.default), g.restDelta = n.restDelta || (A ? J.restDelta.granular : J.restDelta.default);
  };
  y();
  let b, k, x;
  if (h < 1) {
    const A = Hi(m, h), N = { A: 0, sinC: 0, cosC: 0, t: -1, env: 0, sin: 0, cos: 0 };
    x = () => {
      N.A = (g.velocity + p * g.delta) / A, N.sinC = p * N.A + g.delta * A, N.cosC = p * g.delta - N.A * A;
    };
    const P = (w) => {
      w !== N.t && (N.t = w, N.env = Math.exp(-p * w), N.sin = Math.sin(A * w), N.cos = Math.cos(A * w));
    };
    b = (w) => (P(w), g.target - N.env * (N.A * N.sin + g.delta * N.cos)), k = (w) => (P(w), N.env * (N.sinC * N.sin + N.cosC * N.cos));
  } else if (h === 1) {
    b = (N) => g.target - Math.exp(-m * N) * (g.delta + (g.velocity + m * g.delta) * N);
    const A = { C: 0 };
    x = () => {
      A.C = g.velocity + m * g.delta;
    }, k = (N) => Math.exp(-m * N) * (m * A.C * N - g.velocity);
  } else {
    const A = m * Math.sqrt(h * h - 1);
    b = (P) => {
      const w = Math.exp(-p * P), T = Math.min(A * P, 300);
      return g.target - w * ((g.velocity + p * g.delta) * Math.sinh(T) + A * g.delta * Math.cosh(T)) / A;
    };
    const N = { P: 0, sinh: 0, cosh: 0 };
    x = () => {
      N.P = (g.velocity + p * g.delta) / A, N.sinh = p * N.P - g.delta * A, N.cosh = p * g.delta - N.P * A;
    }, k = (P) => {
      const w = Math.exp(-p * P), T = Math.min(A * P, 300);
      return w * (N.sinh * Math.sinh(T) + N.cosh * Math.cosh(T));
    };
  }
  x();
  const S = !jn(n, Ml) && jn(n, Pl), E = f && c || null, C = {
    calculatedDuration: E,
    /**
     * Aim the spring at a new target from its current position and
     * velocity, reusing the resolved physics and closures.
     */
    retarget: (A, N) => {
      g.target = A[A.length - 1], g.delta = g.target - A[0], g.velocity = S ? 0 : -/* @__PURE__ */ ve(N), n.restSpeed && n.restDelta || y(), C.calculatedDuration = E, o.done = !1, x();
    },
    velocity: (A) => /* @__PURE__ */ xe(k(A)),
    next: (A) => {
      const N = b(A);
      if (f)
        o.done = A >= c;
      else {
        const P = /* @__PURE__ */ xe(k(A));
        o.done = Math.abs(P) <= g.restSpeed && Math.abs(g.target - N) <= g.restDelta;
      }
      return o.value = o.done ? g.target : N, o;
    },
    toString: () => {
      const A = Math.min(qr(C), Kr), N = Cl((P) => C.next(A * P).value, A, 30);
      return A + "ms " + N;
    },
    toTransition: () => {
    }
  };
  return C;
}
Yt.applyToOptions = (e) => {
  const t = Nl(e, 100, Yt);
  return e.ease = t.ease, e.duration = /* @__PURE__ */ xe(t.duration), e.type = "keyframes", e;
};
function Gi({ keyframes: e, velocity: t = 0, power: n = 0.8, timeConstant: i = 325, bounceDamping: r = 10, bounceStiffness: o = 500, modifyTarget: s, min: a, max: l, restDelta: c = 0.5, restSpeed: u }) {
  const f = e[0], h = {
    done: !1,
    value: f
  }, m = (A) => A < a || A > l, p = (A) => a === void 0 ? l : l === void 0 || Math.abs(a - A) < Math.abs(l - A) ? a : l;
  let g = n * t;
  const y = f + g, b = s === void 0 ? y : s(y);
  b !== y && (g = b - f);
  const k = (A) => -g * Math.exp(-A / i), x = (A) => {
    const N = k(A);
    h.done = Math.abs(N) <= c, h.value = h.done ? b : b + N;
  };
  let S, E;
  const C = (A) => {
    m(h.value) && (S = A, E = Yt({
      keyframes: [h.value, p(h.value)],
      /**
       * The friction curve is target + calcDelta(t), so its exact
       * derivative is -calcDelta(t) / timeConstant in units/ms,
       * converted here to the units/second expected by spring.
       */
      velocity: -k(A) / i * 1e3,
      damping: r,
      stiffness: o,
      restDelta: c,
      restSpeed: u
    }));
  };
  return C(0), {
    calculatedDuration: null,
    next: (A) => {
      let N = !1;
      return !E && S === void 0 && (N = !0, x(A), C(A)), S !== void 0 && A >= S ? E.next(A - S) : (!N && x(A), h);
    }
  };
}
function Ld(e, t, n) {
  const i = [], r = n || je.mix || Gr, o = e.length - 1;
  for (let s = 0; s < o; s++) {
    let a = r(e[s], e[s + 1]);
    if (t) {
      const l = Array.isArray(t) ? t[s] || Ne : t;
      a = rn(l, a);
    }
    i.push(a);
  }
  return i;
}
function El(e, t, { clamp: n = !0, ease: i, mixer: r } = {}) {
  const o = e.length;
  if (Te(o === t.length, "Both input and output ranges must be the same length", "range-length"), o === 1)
    return () => t[0];
  if (o === 2 && t[0] === t[1])
    return () => t[1];
  const s = e[0] === e[1];
  e[0] > e[o - 1] && (e = [...e].reverse(), t = [...t].reverse());
  const a = Ld(t, i, r), l = a.length, c = (u) => {
    if (s && u < e[0])
      return t[0];
    let f = 0;
    if (l > 1)
      for (; f < e.length - 2 && !(u < e[f + 1]); f++)
        ;
    const h = /* @__PURE__ */ St(e[f], e[f + 1], u);
    return a[f](h);
  };
  return n ? (u) => c(Pe(e[0], e[o - 1], u)) : c;
}
function Dl(e, t) {
  const n = e[e.length - 1];
  for (let i = 1; i <= t; i++) {
    const r = /* @__PURE__ */ St(0, t, i);
    e.push(Y(n, 1, r));
  }
}
function Rl(e) {
  const t = [0];
  return Dl(t, e.length - 1), t;
}
function Vd(e, t) {
  return e.map((n) => n * t);
}
function Fd(e, t) {
  return e.map(() => t || dl).splice(0, e.length - 1);
}
function yt({ duration: e = 300, keyframes: t, times: n, ease: i = "easeInOut" }) {
  const r = /* @__PURE__ */ hl(i) ? i.map($s) : $s(i), o = {
    done: !1,
    value: t[0]
  };
  if (t.length === 2 && !Array.isArray(r) && (!n || n.length !== 2 || n[0] === 0 && n[1] === 1)) {
    const [l, c] = t, u = l === c ? void 0 : (je.mix || Gr)(l, c);
    return {
      calculatedDuration: e,
      next: (f) => (o.value = u ? u(r(e > 0 ? Pe(0, 1, f / e) : 1)) : c, o.done = f >= e, o)
    };
  }
  const s = Vd(
    // Only use the provided offsets if they're the correct length
    // TODO Maybe we should warn here if there's a length mismatch
    n && n.length === t.length ? n : Rl(t),
    e
  ), a = El(s, t, {
    ease: Array.isArray(r) ? r : Fd(t, r)
  });
  return {
    calculatedDuration: e,
    next: (l) => (o.value = a(l), o.done = l >= e, o)
  };
}
const Id = 5;
function Od(e, t, n) {
  const i = Math.max(t - Id, 0);
  return /* @__PURE__ */ rl(n - e(i), t - i);
}
function Bd(e, t, n = 0) {
  return t <= 0 ? n : e.velocity ? e.velocity(t) : Od((i) => e.next(i).value, t, e.next(t).value);
}
const jd = (e) => e !== null;
function Jn(e, { repeat: t, repeatType: n = "loop" }, i, r = 1) {
  const o = e.filter(jd), a = r < 0 || t && n !== "loop" && t % 2 === 1 ? 0 : o.length - 1;
  return !a || i === void 0 ? o[a] : i;
}
const $d = {
  decay: Gi,
  inertia: Gi,
  tween: yt,
  keyframes: yt,
  spring: Yt
};
function Ll(e) {
  typeof e.type == "string" && (e.type = $d[e.type]);
}
function Vl(e, t) {
  return {
    kind: e,
    animation: t,
    timestamp: fe.now(),
    frameTimestamp: ae.timestamp,
    frameIsProcessing: ae.isProcessing
  };
}
function Fl(e, t, n) {
  const i = globalThis.__MOTION_INSPECT__;
  if (i)
    try {
      i({
        ...Vl("animation-start", e),
        options: n ? { ...t, ...n } : t
      });
    } catch {
    }
}
function zd(e, t) {
  const n = globalThis.__MOTION_INSPECT__;
  if (n)
    try {
      n({
        ...Vl("layout-animation-start", e),
        node: t
      });
    } catch {
    }
}
class Yr {
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
const _d = (e) => e / 100;
class $n extends Yr {
  constructor(t) {
    super(), this.state = "idle", this.startTime = null, this.isStopped = !1, this.currentTime = 0, this.holdTime = null, this.playbackSpeed = 1, this.delayState = {
      done: !1,
      value: void 0
    }, this.stop = () => {
      const { motionValue: n } = this.options;
      n && n.updatedAt !== fe.now() && this.tick(fe.now()), this.isStopped = !0, this.state !== "idle" && (this.teardown(), this.options.onStop?.());
    }, this.options = t, this.initAnimation(), this.play(), t.autoplay === !1 && this.pause(), Fl(this, this.options);
  }
  initAnimation() {
    const { options: t } = this;
    Ll(t);
    const { type: n = yt, repeat: i = 0, repeatDelay: r = 0, repeatType: o, velocity: s = 0 } = t;
    let { keyframes: a } = t;
    const l = n || yt;
    process.env.NODE_ENV !== "production" && l !== yt && Te(a.length <= 2, `Only two keyframes currently supported with spring and inertia animations. Trying to animate ${a}`, "spring-two-frames"), l !== yt && typeof a[0] != "number" && (this.mixKeyframes = rn(_d, Gr(a[0], a[1])), a = [0, 100]);
    const c = l(a === t.keyframes ? t : { ...t, keyframes: a });
    o === "mirror" && (this.mirroredGenerator = l({
      ...t,
      keyframes: [...a].reverse(),
      velocity: -s
    })), c.calculatedDuration === null && (c.calculatedDuration = qr(c));
    const { calculatedDuration: u } = c;
    this.calculatedDuration = u, this.resolvedDuration = u + r, this.totalDuration = this.resolvedDuration * (i + 1) - r, this.generator = c;
  }
  updateTime(t) {
    const n = Math.round(t - this.startTime) * this.playbackSpeed;
    this.holdTime !== null ? this.currentTime = this.holdTime : this.currentTime = n;
  }
  tick(t, n = !1) {
    const { generator: i, totalDuration: r, mixKeyframes: o, mirroredGenerator: s, resolvedDuration: a, calculatedDuration: l } = this;
    if (this.startTime === null)
      return i.next(0);
    const { delay: c = 0, keyframes: u, repeat: f, repeatType: h, repeatDelay: m, type: p, onUpdate: g, finalKeyframe: y } = this.options;
    this.speed > 0 ? this.startTime = Math.min(this.startTime, t) : this.speed < 0 && (this.startTime = Math.min(t - r / this.speed, this.startTime)), n ? this.currentTime = t : this.updateTime(t);
    const b = this.currentTime - c * (this.playbackSpeed >= 0 ? 1 : -1), k = this.playbackSpeed >= 0 ? b < 0 : b > r;
    this.currentTime = Math.max(b, 0), this.state === "finished" && this.holdTime === null && (this.currentTime = r);
    let x = this.currentTime, S = i;
    if (f) {
      const N = Math.min(this.currentTime, r) / a;
      let P = Math.floor(N), w = N % 1;
      !w && N >= 1 && (w = 1), w === 1 && P--, P = Math.min(P, f + 1), P % 2 && (h === "reverse" ? (w = 1 - w, m && (w -= m / a)) : h === "mirror" && (S = s)), x = Pe(0, 1, w) * a;
    }
    let E;
    k ? (this.delayState.value = u[0], E = this.delayState) : E = S.next(x), o && !k && (E.value = o(E.value));
    let { done: C } = E;
    !k && l !== null && (C = this.playbackSpeed >= 0 ? this.currentTime >= r : this.currentTime <= 0);
    const A = this.holdTime === null && (this.state === "finished" || this.state === "running" && C);
    return A && p !== Gi && (E.value = Jn(u, this.options, y, this.speed)), g && g(E.value), A && this.finish(), E;
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
    return /* @__PURE__ */ ve(this.calculatedDuration);
  }
  get iterationDuration() {
    const { delay: t = 0 } = this.options || {};
    return this.duration + /* @__PURE__ */ ve(t);
  }
  get time() {
    return /* @__PURE__ */ ve(this.currentTime);
  }
  set time(t) {
    t = /* @__PURE__ */ xe(t), this.currentTime = t, this.startTime === null || this.holdTime !== null || this.playbackSpeed === 0 ? this.holdTime = t : this.driver && (this.startTime = this.driver.now() - t / this.playbackSpeed), this.driver ? this.driver.start(!1) : (this.startTime = 0, this.state = "paused", this.holdTime = t, this.tick(t));
  }
  /**
   * Returns the generator's velocity at the current time in units/second.
   * Uses the analytical derivative when available (springs), avoiding
   * the MotionValue's frame-dependent velocity estimation.
   */
  getGeneratorVelocity() {
    return Bd(this.generator, this.currentTime, this.options.velocity);
  }
  get speed() {
    return this.playbackSpeed;
  }
  set speed(t) {
    const n = this.playbackSpeed !== t;
    n && this.driver && this.updateTime(fe.now()), this.playbackSpeed = t, n && this.driver && (this.time = /* @__PURE__ */ ve(this.currentTime));
  }
  play() {
    if (this.isStopped)
      return;
    const { driver: t = Pd, startTime: n } = this.options;
    this.driver || (this.driver = t((r) => this.tick(r))), this.options.onPlay?.();
    const i = this.driver.now();
    this.state === "finished" ? (this.updateFinished(), this.startTime = i) : this.holdTime !== null ? this.startTime = i - this.holdTime : this.startTime || (this.startTime = n ?? i), this.state === "finished" && this.speed < 0 && (this.startTime += this.calculatedDuration), this.holdTime = null, this.state = "running", this.driver.start();
  }
  pause() {
    this.state = "paused", this.updateTime(fe.now()), this.holdTime = this.currentTime;
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
const Ud = /* @__PURE__ */ new Set(["brightness", "contrast", "saturate", "opacity"]);
function Wd(e) {
  const [t, n] = e.slice(0, -1).split("(");
  if (t === "drop-shadow")
    return e;
  const [i] = n.match(Ur) || [];
  if (!i)
    return e;
  const r = n.replace(i, "");
  let o = Ud.has(t) ? 1 : 0;
  return i !== n && (o *= 100), t + "(" + o + r + ")";
}
const Hd = /\b([a-z-]*)\(.*?\)/gu, Ki = {
  ...ke,
  getAnimatableNone: (e) => {
    const t = e.match(Hd);
    return t ? t.map(Wd).join(" ") : e;
  }
}, qi = {
  ...ke,
  getAnimatableNone: (e) => {
    const t = ke.parse(e);
    return ke.createTransformer(e)(t.map((i) => typeof i == "number" ? 0 : typeof i == "object" ? { ...i, alpha: 1 } : i));
  }
}, Ks = {
  ...Pt,
  transform: Math.round
}, Yi = {
  rotate: Ie,
  /**
   * Internal channel for `transition.path` orientToPath. Composed onto
   * `rotate` at the transform-build sites so the user's `rotate` is
   * never read or overwritten. Not part of `transformPropOrder`.
   */
  pathRotation: Ie,
  rotateX: Ie,
  rotateY: Ie,
  rotateZ: Ie,
  scale: mn,
  scaleX: mn,
  scaleY: mn,
  scaleZ: mn,
  skew: Ie,
  skewX: Ie,
  skewY: Ie,
  distance: L,
  translateX: L,
  translateY: L,
  translateZ: L,
  x: L,
  y: L,
  z: L,
  perspective: L,
  transformPerspective: L,
  opacity: Kt,
  originX: _s,
  originY: _s,
  originZ: L
}, Ve = {
  // Border props
  borderWidth: L,
  borderTopWidth: L,
  borderRightWidth: L,
  borderBottomWidth: L,
  borderLeftWidth: L,
  borderRadius: L,
  borderTopLeftRadius: L,
  borderTopRightRadius: L,
  borderBottomRightRadius: L,
  borderBottomLeftRadius: L,
  // Positioning props
  width: L,
  maxWidth: L,
  height: L,
  maxHeight: L,
  top: L,
  right: L,
  bottom: L,
  left: L,
  inset: L,
  insetBlock: L,
  insetBlockStart: L,
  insetBlockEnd: L,
  insetInline: L,
  insetInlineStart: L,
  insetInlineEnd: L,
  // Spacing props
  padding: L,
  paddingTop: L,
  paddingRight: L,
  paddingBottom: L,
  paddingLeft: L,
  paddingBlock: L,
  paddingBlockStart: L,
  paddingBlockEnd: L,
  paddingInline: L,
  paddingInlineStart: L,
  paddingInlineEnd: L,
  margin: L,
  marginTop: L,
  marginRight: L,
  marginBottom: L,
  marginLeft: L,
  marginBlock: L,
  marginBlockStart: L,
  marginBlockEnd: L,
  marginInline: L,
  marginInlineStart: L,
  marginInlineEnd: L,
  // Typography
  fontSize: L,
  // Misc
  backgroundPositionX: L,
  backgroundPositionY: L,
  ...Yi,
  zIndex: Ks,
  // SVG
  fillOpacity: Kt,
  strokeOpacity: Kt,
  numOctaves: Ks
}, Gd = {
  ...Ve,
  // Color props
  color: le,
  backgroundColor: le,
  outlineColor: le,
  fill: le,
  stroke: le,
  // Border props
  borderColor: le,
  borderTopColor: le,
  borderRightColor: le,
  borderBottomColor: le,
  borderLeftColor: le,
  filter: Ki,
  WebkitFilter: Ki,
  mask: qi,
  WebkitMask: qi
}, Il = (e) => Gd[e], Kd = /* @__PURE__ */ new Set([Ki, qi]);
function Xr(e, t) {
  let n = Il(e);
  return Kd.has(n) || (n = ke), n.getAnimatableNone ? n.getAnimatableNone(t) : void 0;
}
function qd(e) {
  for (let t = 1; t < e.length; t++)
    e[t] ?? (e[t] = e[t - 1]);
}
const nt = (e) => e * 180 / Math.PI, Xi = (e) => {
  const t = nt(Math.atan2(e[1], e[0]));
  return Qi(t);
}, Yd = {
  x: 4,
  y: 5,
  translateX: 4,
  translateY: 5,
  scaleX: 0,
  scaleY: 3,
  scale: (e) => (Math.abs(e[0]) + Math.abs(e[3])) / 2,
  rotate: Xi,
  rotateZ: Xi,
  skewX: (e) => nt(Math.atan(e[1])),
  skewY: (e) => nt(Math.atan(e[2])),
  skew: (e) => (Math.abs(e[1]) + Math.abs(e[2])) / 2
}, Qi = (e) => (e = e % 360, e < 0 && (e += 360), e), qs = Xi, Ys = (e) => Math.sqrt(e[0] * e[0] + e[1] * e[1]), Xs = (e) => Math.sqrt(e[4] * e[4] + e[5] * e[5]), Xd = {
  x: 12,
  y: 13,
  z: 14,
  translateX: 12,
  translateY: 13,
  translateZ: 14,
  scaleX: Ys,
  scaleY: Xs,
  scale: (e) => (Ys(e) + Xs(e)) / 2,
  rotateX: (e) => Qi(nt(Math.atan2(e[6], e[5]))),
  rotateY: (e) => Qi(nt(Math.atan2(-e[2], e[0]))),
  rotateZ: qs,
  rotate: qs,
  skewX: (e) => nt(Math.atan(e[4])),
  skewY: (e) => nt(Math.atan(e[1])),
  skew: (e) => (Math.abs(e[1]) + Math.abs(e[4])) / 2
};
function Zi(e) {
  return e.includes("scale") ? 1 : 0;
}
function Ji(e, t) {
  if (!e || e === "none")
    return Zi(t);
  const n = e.match(/^matrix3d\(([-\d.e\s,]+)\)$/u);
  let i, r;
  if (n)
    i = Xd, r = n;
  else {
    const a = e.match(/^matrix\(([-\d.e\s,]+)\)$/u);
    i = Yd, r = a;
  }
  if (!r)
    return Zi(t);
  const o = i[t], s = r[1].split(",").map(Qd);
  return typeof o == "function" ? o(s) : s[o];
}
const Ol = (e, t) => {
  const { transform: n = "none" } = getComputedStyle(e);
  return Ji(n, t);
};
function Qd(e) {
  return parseFloat(e.trim());
}
const Ye = [
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
], We = /* @__PURE__ */ new Set([...Ye, "pathRotation"]), Qs = (e) => e === Pt || e === L, Zd = /* @__PURE__ */ new Set(["x", "y", "z"]), Jd = Ye.filter((e) => !Zd.has(e));
function eh(e) {
  const t = [];
  return Jd.forEach((n) => {
    const i = e.getValue(n);
    if (i !== void 0) {
      const r = i.get(), o = n.startsWith("scale") ? 1 : 0;
      if (r === o)
        return;
      t.push([n, r]), i.set(o);
    }
  }), t;
}
const th = /* @__PURE__ */ new Set(["bottom", "right"]);
function Zs(e, t, n, i, r, o) {
  const s = parseFloat(e);
  if (!isNaN(s))
    return s;
  const { min: a, max: l } = t()[n], c = l - a;
  return o === "border-box" ? c : c - parseFloat(i) - parseFloat(r);
}
const it = {
  // Dimensions
  width: ({ width: e, paddingLeft: t = "0", paddingRight: n = "0", boxSizing: i }, r) => Zs(e, r, "x", t, n, i),
  height: ({ height: e, paddingTop: t = "0", paddingBottom: n = "0", boxSizing: i }, r) => Zs(e, r, "y", t, n, i),
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
  x: ({ transform: e }) => Ji(e, "x"),
  y: ({ transform: e }) => Ji(e, "y")
};
it.translateX = it.x;
it.translateY = it.y;
const rt = /* @__PURE__ */ new Set();
let er = !1, tr = !1, nr = !1;
function Bl() {
  if (tr) {
    const e = [], t = /* @__PURE__ */ new Set(), n = /* @__PURE__ */ new Set();
    rt.forEach((r) => {
      r.needsMeasurement && (e.push(r), t.add(r.element), th.has(r.name) && n.add(r.element));
    });
    const i = /* @__PURE__ */ new Map();
    n.forEach((r) => {
      const o = eh(r);
      o.length && (i.set(r, o), r.render());
    }), e.forEach((r) => r.measureInitialState()), t.forEach((r) => {
      r.render();
      const o = i.get(r);
      o && o.forEach(([s, a]) => {
        r.getValue(s)?.set(a);
      });
    }), e.forEach((r) => r.measureEndState()), e.forEach((r) => {
      r.suspendedScrollY !== void 0 && window.scrollTo(0, r.suspendedScrollY);
    });
  }
  tr = !1, er = !1, rt.forEach((e) => e.complete(nr)), rt.clear();
}
function jl() {
  rt.forEach((e) => {
    e.readKeyframes(), e.needsMeasurement && (tr = !0);
  });
}
function nh() {
  nr = !0, jl(), Bl(), nr = !1;
}
function ih(e, t, n) {
  if (typeof e == "string") {
    if (Ir(e) || Br(e))
      return parseFloat(e);
    if (!ke.test(e) && ke.test(n))
      return Xr(t, n);
  }
  return e ?? void 0;
}
class Qr {
  constructor(t, n, i, r, o, s = !1) {
    this.state = "pending", this.isAsync = !1, this.needsMeasurement = !1, this.unresolvedKeyframes = [...t], this.onComplete = n, this.name = i, this.motionValue = r, this.element = o, this.isAsync = s;
  }
  scheduleResolve() {
    this.state = "scheduled", this.isAsync ? (rt.add(this), er || (er = !0, K.read(jl), K.resolveKeyframes(Bl))) : (this.readKeyframes(), this.complete());
  }
  readKeyframes() {
    const { unresolvedKeyframes: t, name: n, element: i, motionValue: r } = this;
    if (t[0] === null) {
      const o = r?.get(), s = t[t.length - 1];
      if (o !== void 0)
        t[0] = o;
      else if (i && n) {
        const a = ih(i.readValue(n, s), n, s);
        a !== void 0 && (t[0] = a);
      }
      t[0] === void 0 && (t[0] = s), r && o === void 0 && r.set(t[0]);
    }
    qd(t);
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
    this.state = "complete", this.onComplete(this.unresolvedKeyframes, this.finalKeyframe, t), rt.delete(this);
  }
  cancel() {
    this.state === "scheduled" && (rt.delete(this), this.state = "pending");
  }
  resume() {
    this.state === "pending" && this.scheduleResolve();
  }
}
const Zr = (e) => e.startsWith("--");
function $l(e, t, n) {
  Zr(t) ? e.style.setProperty(t, n) : e.style[t] = n;
}
const rh = {};
function zl(e, t) {
  const n = /* @__PURE__ */ il(e);
  return () => rh[t] ?? n();
}
const sh = /* @__PURE__ */ zl(() => window.ScrollTimeline !== void 0, "scrollTimeline"), _l = /* @__PURE__ */ zl(() => {
  try {
    document.createElement("div").animate({ opacity: 0 }, { easing: "linear(0, 1)" });
  } catch {
    return !1;
  }
  return !0;
}, "linearEasing"), Bt = ([e, t, n, i]) => `cubic-bezier(${e}, ${t}, ${n}, ${i})`, Js = {
  linear: "linear",
  ease: "ease",
  easeIn: "ease-in",
  easeOut: "ease-out",
  easeInOut: "ease-in-out",
  circIn: /* @__PURE__ */ Bt([0, 0.65, 0.55, 1]),
  circOut: /* @__PURE__ */ Bt([0.55, 0, 1, 0.45]),
  backIn: /* @__PURE__ */ Bt([0.31, 0.01, 0.66, -0.59]),
  backOut: /* @__PURE__ */ Bt([0.33, 1.53, 0.69, 0.99])
};
function Ul(e, t) {
  if (e)
    return typeof e == "function" ? _l() ? Cl(e, t) : "ease-out" : /* @__PURE__ */ ml(e) ? Bt(e) : Array.isArray(e) ? e.map((n) => Ul(n, t) || Js.easeOut) : Js[e];
}
function oh(e, t, n, { delay: i = 0, duration: r = 300, repeat: o = 0, repeatType: s = "loop", ease: a = "easeOut", times: l } = {}, c = void 0) {
  const u = {
    [t]: n
  };
  l && (u.offset = l);
  const f = Ul(a, r);
  Array.isArray(f) && (u.easing = f);
  const h = {
    delay: i,
    duration: r,
    easing: Array.isArray(f) ? "linear" : f,
    fill: "both",
    iterations: o + 1,
    direction: s === "reverse" ? "alternate" : "normal"
  };
  return c && (h.pseudoElement = c), e.animate(u, h);
}
function Jr(e) {
  return typeof e == "function" && "applyToOptions" in e;
}
function ah({ type: e, ...t }) {
  return Jr(e) && _l() ? e.applyToOptions(t) : (t.duration ?? (t.duration = 300), t.ease ?? (t.ease = "easeOut"), t);
}
class Wl extends Yr {
  constructor(t) {
    if (super(), this.finishedTime = null, this.isStopped = !1, this.manualStartTime = null, !t)
      return;
    const { element: n, name: i, keyframes: r, pseudoElement: o, allowFlatten: s = !1, finalKeyframe: a, onComplete: l } = t;
    this.isPseudoElement = !!o, this.allowFlatten = s, this.options = t, Te(typeof t.type != "string", `Mini animate() doesn't support "type" as a string.`, "mini-spring");
    const c = ah(t);
    this.animation = oh(n, i, r, c, o), c.autoplay === !1 && this.animation.pause(), this.animation.onfinish = () => {
      if (this.finishedTime = this.time, !o) {
        const u = Jn(r, this.options, a, this.speed);
        this.updateMotionValue && this.updateMotionValue(u), $l(n, i, u), this.animation.cancel();
      }
      l?.(), this.notifyFinished();
    }, Fl(this, t, c);
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
    return /* @__PURE__ */ ve(Number(t));
  }
  get iterationDuration() {
    const { delay: t = 0 } = this.options || {};
    return this.duration + /* @__PURE__ */ ve(t);
  }
  get time() {
    return /* @__PURE__ */ ve(Number(this.animation.currentTime) || 0);
  }
  set time(t) {
    const n = this.finishedTime !== null;
    this.manualStartTime = null, this.finishedTime = null, this.animation.currentTime = /* @__PURE__ */ xe(t), n && this.animation.pause();
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
  attachTimeline({ timeline: t, rangeStart: n, rangeEnd: i, observe: r }) {
    return this.allowFlatten && this.animation.effect?.updateTiming({ easing: "linear" }), this.animation.onfinish = null, t && sh() ? (this.animation.timeline = t, n && (this.animation.rangeStart = n), i && (this.animation.rangeEnd = i), Ne) : r(this);
  }
}
const Hl = {
  anticipate: cl,
  backInOut: ll,
  circInOut: fl
};
function lh(e) {
  return e in Hl;
}
function ch(e) {
  typeof e.ease == "string" && lh(e.ease) && (e.ease = Hl[e.ease]);
}
const yi = 10;
class uh extends Wl {
  constructor(t) {
    ch(t), Ll(t), super(t), t.startTime !== void 0 && t.autoplay !== !1 && (this.startTime = t.startTime), this.options = t;
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
    const { motionValue: n, onUpdate: i, onComplete: r, element: o, ...s } = this.options;
    if (!n)
      return;
    if (t !== void 0) {
      n.set(t);
      return;
    }
    const a = new $n({
      ...s,
      autoplay: !1
    }), l = Math.max(yi, fe.now() - this.startTime), c = Pe(0, yi, l - yi), u = a.sample(l).value, { name: f } = this.options;
    o && f && $l(o, f, u), n.setWithVelocity(a.sample(Math.max(0, l - c)).value, u, c), a.stop();
  }
}
const eo = (e, t) => t === "zIndex" ? !1 : !!(typeof e == "number" || Array.isArray(e) || typeof e == "string" && // It's animatable if we have a string
(ke.test(e) || e === "0") && // And it contains numbers and/or colors
!e.startsWith("url("));
function fh(e) {
  const t = e[0];
  if (e.length === 1)
    return !0;
  for (let n = 0; n < e.length; n++)
    if (e[n] !== t)
      return !0;
}
function dh(e, t, n, i) {
  const r = e[0];
  if (r === null)
    return !1;
  if (t === "display" || t === "visibility")
    return !0;
  const o = e[e.length - 1], s = eo(r, t), a = eo(o, t);
  return !s || !a ? (s !== a && ct(!1, `You are trying to animate ${t} from "${r}" to "${o}". "${s ? o : r}" is not an animatable value.`, "value-not-animatable"), !1) : fh(e) || (n === "spring" || Jr(n)) && i;
}
function ir(e) {
  e.duration = 0, e.type = "keyframes";
}
const rr = /* @__PURE__ */ new Set([
  "opacity",
  "clipPath",
  "filter",
  "transform",
  "backgroundColor"
]), hh = /^(?:oklch|oklab|lab|lch|color|color-mix|light-dark)\(/;
function ph(e) {
  for (let t = 0; t < e.length; t++)
    if (typeof e[t] == "string" && hh.test(e[t]))
      return !0;
  return !1;
}
const to = /* @__PURE__ */ new Set([
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
]), mh = /* @__PURE__ */ il(() => Object.hasOwnProperty.call(Element.prototype, "animate"));
function gh(e) {
  const { motionValue: t, name: n, repeatDelay: i, repeatType: r, damping: o, type: s, keyframes: a } = e;
  if (!n || !(rr.has(n) || to.has(n)))
    return !1;
  const l = t?.owner?.current;
  if (!(l instanceof HTMLElement) && !(l instanceof SVGElement))
    return !1;
  const { onUpdate: c, transformTemplate: u } = t.owner.getProps();
  return mh() && /**
   * Force WAAPI for color properties with browser-only color formats
   * (oklch, oklab, lab, lch, etc.) that the JS animation path can't parse.
   */
  (rr.has(n) || to.has(n) && ph(a)) && (n !== "transform" || !u) && /**
   * If we're outputting values to onUpdate then we can't use WAAPI as there's
   * no way to read the value from WAAPI every frame.
   */
  !c && !i && r !== "mirror" && o !== 0 && s !== "inertia";
}
const yh = 40;
class xh extends Yr {
  constructor(t) {
    super(), this.stop = () => {
      this._animation && (this._animation.stop(), this.stopTimeline?.()), this.keyframeResolver?.cancel();
    }, this.createdAt = fe.now();
    const { keyframes: n, name: i, motionValue: r, element: o } = t, s = t;
    s.autoplay ?? (s.autoplay = !0), s.delay ?? (s.delay = 0), s.type ?? (s.type = "keyframes"), s.repeat ?? (s.repeat = 0), s.repeatDelay ?? (s.repeatDelay = 0), s.repeatType ?? (s.repeatType = "loop");
    const a = o?.KeyframeResolver || Qr;
    this.keyframeResolver = new a(n, (l, c, u) => this.onKeyframesResolved(l, c, s, !u), i, r, o), this.keyframeResolver?.scheduleResolve();
  }
  onKeyframesResolved(t, n, i, r) {
    this.keyframeResolver = void 0;
    const { name: o, type: s, velocity: a, delay: l, isHandoff: c, onUpdate: u } = i;
    this.resolvedAt = fe.now();
    let f = !0;
    dh(t, o, s, a) || (f = !1, (je.instantAnimations || !l) && u?.(Jn(t, i, n)), t[0] = t[t.length - 1], ir(i), i.repeat = 0);
    const h = r ? this.resolvedAt ? this.resolvedAt - this.createdAt > yh ? this.resolvedAt : this.createdAt : this.createdAt : void 0, { onComplete: m } = i;
    i.startTime ?? (i.startTime = h), i.finalKeyframe = n, i.keyframes = t, i.onComplete = () => {
      m?.(), this.notifyFinished();
    };
    const p = f && !c && gh(i);
    let g;
    if (p) {
      i.element = i.motionValue?.owner?.current;
      try {
        g = new uh(i);
      } catch {
        g = new $n(i);
      }
    } else
      g = new $n(i);
    this.pendingTimeline && (this.stopTimeline = g.attachTimeline(this.pendingTimeline), this.pendingTimeline = void 0), this._animation = g;
  }
  get finished() {
    return this._animation ? this._animation.finished : super.finished;
  }
  then(t, n) {
    return this.finished.finally(t).then(() => {
    });
  }
  get animation() {
    return this._animation || (this.keyframeResolver?.resume(), nh()), this._animation;
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
class bh {
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
      n.forEach((i, r) => {
        i && i(), this.animations[r].stop();
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
    return no(this.animations, "duration");
  }
  get iterationDuration() {
    return no(this.animations, "iterationDuration");
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
function no(e, t) {
  let n = 0;
  for (let i = 0; i < e.length; i++) {
    const r = e[i][t];
    r !== null && r > n && (n = r);
  }
  return n;
}
class vh extends bh {
  then(t, n) {
    return this.finished.finally(t).then(() => {
    });
  }
}
function Gl(e, t, n, i = 0, r = 1) {
  const o = Array.from(e).sort((c, u) => c.sortNodePosition(u)).indexOf(t), s = e.size, a = (s - 1) * i;
  return typeof n == "function" ? n(o, s) : r === 1 ? o * i : a - o * i;
}
const io = 30, wh = (e) => !isNaN(parseFloat(e)), jt = {
  current: void 0
};
class $t {
  /**
   * @param init - The initiating value
   * @param config - Optional configuration options
   *
   * -  `transformer`: A function to transform incoming values with.
   */
  constructor(t, n = {}) {
    this.canTrackVelocity = null, this.events = {}, this.updateAndNotify = (i) => {
      const r = fe.now();
      if (this.updatedAt !== r && this.setPrevFrameValue(), this.prev = this.current, this.setCurrent(i), this.current !== this.prev && (this.notifyChange(), this.dependents))
        for (const o of this.dependents)
          o.dirty();
    }, this.hasAnimated = !1, this.setCurrent(t), this.owner = n.owner;
  }
  setCurrent(t) {
    this.current = t, this.updatedAt = fe.now(), this.canTrackVelocity === null && t !== void 0 && (this.canTrackVelocity = wh(this.current));
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
    return process.env.NODE_ENV !== "production" && Zn(!1, 'value.onChange(callback) is deprecated. Switch to value.on("change", callback).'), this.on("change", t);
  }
  on(t, n) {
    var i;
    return t === "change" ? this.onChangeSubscribe(n) : ((i = this.events)[t] || (i[t] = new On())).add(n);
  }
  onChangeSubscribe(t) {
    const { events: n } = this;
    return !n.change && !this.changeSubscriber ? this.changeSubscriber = t : (n.change || (n.change = new On(), n.change.add(this.changeSubscriber), this.changeSubscriber = void 0), n.change.add(t)), () => {
      this.changeSubscriber === t ? this.changeSubscriber = void 0 : n.change?.remove(t), this.stopIfUnobserved();
    };
  }
  /**
   * If we have no more change listeners by the start
   * of the next frame, stop active animations.
   */
  stopIfUnobserved() {
    K.read(() => {
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
    return jt.current && jt.current.push(this), this.current;
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
    const t = fe.now();
    if (!this.canTrackVelocity || this.prevFrameValue === void 0 || t - this.updatedAt > io)
      return 0;
    const n = Math.min(this.updatedAt - this.prevUpdatedAt, io);
    return /* @__PURE__ */ rl(parseFloat(this.current) - parseFloat(this.prevFrameValue), n);
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
      let i = !1, r;
      r = t(() => {
        i = !0, this.events.animationComplete?.notify(), this.animation === r && this.clearAnimation(), n();
      }), i || (this.animation = r), this.events.animationStart?.notify();
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
function ze(e, t) {
  return new $t(e, t);
}
function Kl(e, t) {
  if (e?.inherit && t) {
    const { inherit: n, ...i } = e;
    return { ...t, ...i };
  }
  return e;
}
function es(e, t) {
  const n = e?.[t] ?? e?.default ?? e;
  return n !== e ? Kl(n, e) : n;
}
const kh = {
  type: "spring",
  stiffness: 500,
  damping: 25,
  restSpeed: 10
}, Th = (e) => ({
  type: "spring",
  stiffness: 550,
  damping: e === 0 ? 2 * Math.sqrt(550) : 30,
  restSpeed: 10
}), Sh = {
  type: "keyframes",
  duration: 0.8
}, Ah = {
  type: "keyframes",
  ease: [0.25, 0.1, 0.35, 1],
  duration: 0.3
}, Ch = (e, { keyframes: t }) => t.length > 2 ? Sh : We.has(e) ? e.startsWith("scale") ? Th(t[1]) : kh : Ah, Nh = /* @__PURE__ */ new Set([
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
function Ph(e) {
  for (const t in e)
    if (!Nh.has(t))
      return !0;
  return !1;
}
const ei = (e, t, n, i = {}, r, o) => (s) => {
  const a = es(i, e) || {}, l = a.delay || i.delay || 0;
  let { elapsed: c = 0 } = i;
  c = c - /* @__PURE__ */ xe(l);
  const u = {
    keyframes: Array.isArray(n) ? n : [null, n],
    ease: "easeOut",
    velocity: t.getVelocity(),
    ...a,
    delay: -c,
    onUpdate: (h) => {
      t.set(h), a.onUpdate && a.onUpdate(h);
    },
    onComplete: () => {
      s(), a.onComplete && a.onComplete();
    },
    name: e,
    motionValue: t,
    element: o ? void 0 : r
  };
  Ph(a) || Object.assign(u, Ch(e, u)), u.duration && (u.duration = /* @__PURE__ */ xe(u.duration)), u.repeatDelay && (u.repeatDelay = /* @__PURE__ */ xe(u.repeatDelay)), u.from !== void 0 && (u.keyframes[0] = u.from);
  let f = !1;
  if ((u.type === !1 || u.duration === 0 && !u.repeatDelay) && (ir(u), u.delay === 0 && (f = !0)), (je.instantAnimations || je.skipAnimations || r?.shouldSkipAnimations || a.skipAnimations) && (f = !0, ir(u), u.delay = 0), u.allowFlatten = !a.type && !a.ease, f && !o && t.get() !== void 0) {
    const h = Jn(u.keyframes, a);
    if (h !== void 0) {
      K.update(() => {
        u.onUpdate(h), u.onComplete();
      });
      return;
    }
  }
  return a.isSync ? new $n(u) : new xh(u);
}, Mh = (
  // eslint-disable-next-line redos-detector/no-unsafe-regex -- false positive, as it can match a lot of words
  /^var\(--(?:([\w-]+)|([\w-]+), ?([a-zA-Z\d ()%#.,-]+))\)/u
);
function Eh(e) {
  const t = Mh.exec(e);
  if (!t)
    return [,];
  const [, n, i, r] = t;
  return [`--${n ?? i}`, r];
}
const Dh = 4;
function ql(e, t, n = 1) {
  Te(n <= Dh, `Max CSS variable fallback depth detected in property "${e}". This may indicate a circular fallback dependency.`, "max-css-var-depth");
  const [i, r] = Eh(e);
  if (!i)
    return;
  const o = window.getComputedStyle(t).getPropertyValue(i);
  if (o) {
    const s = o.trim();
    return Ir(s) ? parseFloat(s) : s;
  }
  return _r(r) ? ql(r, t, n + 1) : r;
}
function ro(e) {
  const t = [{}, {}];
  return e?.values.forEach((n, i) => {
    t[0][i] = n.get(), t[1][i] = n.getVelocity();
  }), t;
}
function ts(e, t, n, i) {
  if (typeof t == "function") {
    const [r, o] = ro(i);
    t = t(n !== void 0 ? n : e.custom, r, o);
  }
  if (typeof t == "string" && (t = e.variants && e.variants[t]), typeof t == "function") {
    const [r, o] = ro(i);
    t = t(n !== void 0 ? n : e.custom, r, o);
  }
  return t;
}
function st(e, t, n) {
  const i = e.getProps();
  return ts(i, t, n !== void 0 ? n : i.custom, e);
}
const ns = /* @__PURE__ */ new Set([
  "width",
  "height",
  "top",
  "left",
  "right",
  "bottom",
  ...Ye
]), sr = (e) => Array.isArray(e);
function Rh(e, t, n) {
  e.hasValue(t) ? e.getValue(t).set(n) : e.addValue(t, ze(n));
}
function Lh(e) {
  return sr(e) ? e[e.length - 1] || 0 : e;
}
function Vh(e, t) {
  const n = st(e, t);
  let { transitionEnd: i = {}, transition: r = {}, ...o } = n || {};
  o = { ...o, ...i };
  for (const s in o) {
    const a = Lh(o[s]);
    Rh(e, s, a);
  }
}
const ce = (e) => !!(e && e.getVelocity);
function Fh(e) {
  return !!(ce(e) && e.add);
}
function or(e, t) {
  const n = e.getValue("willChange");
  if (Fh(n))
    return n.add(t);
  if (!n && je.WillChange) {
    const i = new je.WillChange("auto");
    e.addValue("willChange", i), i.add(t);
  }
}
function an(e) {
  return e.replace(/([A-Z])/g, (t) => `-${t.toLowerCase()}`);
}
const Ih = "framerAppearId", Yl = "data-" + an(Ih);
function Xl(e) {
  return e.props[Yl];
}
const Oh = typeof window < "u";
function Bh({ protectedKeys: e, needsAnimating: t }, n) {
  const i = e.hasOwnProperty(n) && t[n] !== !0;
  return t[n] = !1, i;
}
function Ql(e, t, { delay: n = 0, transitionOverride: i, type: r } = {}) {
  let { transition: o, transitionEnd: s, ...a } = t;
  const l = e.getDefaultTransition();
  o = o ? Kl(o, l) : l;
  const c = o?.reduceMotion, u = o?.skipAnimations;
  i && (o = i);
  const f = [], h = r && e.animationState && e.animationState.getState()[r], m = o?.path;
  m && m.animateVisualElement(e, a, o, n, f);
  for (const p in a) {
    const g = e.getValue(p, e.latestValues[p] ?? null), y = a[p];
    if (y === void 0 || h && Bh(h, p))
      continue;
    const b = {
      delay: n,
      ...es(o || {}, p)
    };
    u && (b.skipAnimations = !0);
    const k = g.get();
    if (k !== void 0 && !g.isAnimating() && !Array.isArray(y) && y === k && !b.velocity) {
      K.update(() => g.set(y));
      continue;
    }
    let x = !1;
    if (Oh && window.MotionHandoffAnimation) {
      const C = Xl(e);
      if (C) {
        const A = window.MotionHandoffAnimation(C, p, K);
        A !== null && (b.startTime = A, x = !0);
      }
    }
    or(e, p);
    const S = c ?? e.shouldReduceMotion;
    g.start(ei(p, g, y, S && ns.has(p) ? { type: !1 } : b, e, x));
    const E = g.animation;
    E && f.push(E);
  }
  if (s) {
    const p = () => K.update(() => {
      s && Vh(e, s);
    });
    f.length ? Promise.all(f).then(p) : p();
  }
  return f;
}
function ar(e, t, n = {}) {
  const i = st(e, t, n.type === "exit" ? e.presenceContext?.custom : void 0);
  let { transition: r = e.getDefaultTransition() || {} } = i || {};
  n.transitionOverride && (r = n.transitionOverride);
  const o = i ? () => Promise.all(Ql(e, i, n)) : () => Promise.resolve(), s = e.variantChildren && e.variantChildren.size ? (l = 0) => {
    const { delayChildren: c = 0, staggerChildren: u, staggerDirection: f } = r;
    return jh(e, t, l, c, u, f, n);
  } : () => Promise.resolve(), { when: a } = r;
  if (a) {
    const [l, c] = a === "beforeChildren" ? [o, s] : [s, o];
    return l().then(() => c());
  } else
    return Promise.all([o(), s(n.delay)]);
}
function jh(e, t, n = 0, i = 0, r = 0, o = 1, s) {
  const a = [];
  for (const l of e.variantChildren)
    l.notify("AnimationStart", t), a.push(ar(l, t, {
      ...s,
      delay: n + (typeof i == "function" ? 0 : i) + Gl(e.variantChildren, l, i, r, o)
    }).then(() => l.notify("AnimationComplete", t)));
  return Promise.all(a);
}
function $h(e, t, n = {}) {
  e.notify("AnimationStart", t);
  let i;
  if (Array.isArray(t)) {
    const r = t.map((o) => ar(e, o, n));
    i = Promise.all(r);
  } else if (typeof t == "string")
    i = ar(e, t, n);
  else {
    const r = typeof t == "function" ? st(e, t, n.custom) : t;
    i = Promise.all(Ql(e, r, n));
  }
  return i.then(() => {
    e.notify("AnimationComplete", t);
  });
}
const zh = {
  test: (e) => e === "auto",
  parse: (e) => e
}, _h = (e) => (t) => t.test(e), Uh = [Pt, L, Le, Ie, ad, od, zh], so = (e) => Uh.find(_h(e));
function Wh(e) {
  return typeof e == "number" ? e === 0 : e !== null ? e === "none" || e === "0" || Br(e) : !0;
}
const Hh = /* @__PURE__ */ new Set(["auto", "none", "0"]);
function Gh(e, t, n) {
  let i = 0, r;
  for (; i < e.length && !r; ) {
    const o = e[i];
    typeof o == "string" && !Hh.has(o) && hd(o) && (r = e[i]), i++;
  }
  if (r && n)
    for (const o of t)
      e[o] !== r && (e[o] = Xr(n, r));
}
class Zl extends Qr {
  constructor(t, n, i, r, o) {
    super(t, n, i, r, o, !0);
  }
  readKeyframes() {
    const { unresolvedKeyframes: t, element: n, name: i } = this;
    if (!n || !n.current)
      return;
    super.readKeyframes();
    for (let u = 0; u < t.length; u++) {
      let f = t[u];
      if (typeof f == "string" && (f = f.trim(), _r(f))) {
        const h = ql(f, n.current);
        h !== void 0 && (t[u] = h), u === t.length - 1 && (this.finalKeyframe = f);
      }
    }
    if (this.resolveNoneKeyframes(), !ns.has(i) || t.length !== 2)
      return;
    const [r, o] = t;
    if (typeof r == "number" && typeof o == "number")
      return;
    const s = so(r), a = so(o), l = zs(r), c = zs(o);
    if (l !== c && it[i]) {
      this.needsMeasurement = !0;
      return;
    }
    if (s !== a)
      if (Qs(s) && Qs(a))
        for (let u = 0; u < t.length; u++) {
          const f = t[u];
          typeof f == "string" && (t[u] = parseFloat(f));
        }
      else it[i] && (this.needsMeasurement = !0);
  }
  resolveNoneKeyframes() {
    const { unresolvedKeyframes: t, name: n } = this, i = [];
    for (let r = 0; r < t.length; r++)
      (t[r] === null || Wh(t[r])) && i.push(r);
    i.length && Gh(t, i, n);
  }
  measure() {
    const { element: t, name: n } = this;
    return it[n](window.getComputedStyle(t.current), () => t.measureViewportBox());
  }
  measureInitialState() {
    const { element: t, unresolvedKeyframes: n, name: i } = this;
    if (!t || !t.current)
      return;
    i === "height" && (this.suspendedScrollY = window.pageYOffset), this.measuredOrigin = this.measure(), n[0] = this.measuredOrigin;
    const r = n[n.length - 1];
    r !== void 0 && this.motionValue?.jump(r, !1);
  }
  measureEndState() {
    const { element: t, unresolvedKeyframes: n } = this;
    if (!t || !t.current)
      return;
    this.motionValue?.jump(this.measuredOrigin, !1);
    const i = n.length - 1, r = n[i];
    n[i] = this.measure(), r !== null && this.finalKeyframe === void 0 && (this.finalKeyframe = r), this.removedTransforms?.length && this.removedTransforms.forEach(([o, s]) => {
      t.getValue(o).set(s);
    }), this.resolveNoneKeyframes();
  }
}
const is = [
  "borderTopLeftRadius",
  "borderTopRightRadius",
  "borderBottomRightRadius",
  "borderBottomLeftRadius"
], rs = [];
function Kh(e) {
  Te(typeof e.test == "function" && typeof e.read == "function", "Effects passed to animate.addEffect() need test() and read().", "effect-missing-test"), Jl(e), rs.unshift(e);
}
function Jl(e) {
  ot(rs, e);
}
function qh(e) {
  return rs.find((t) => t.test(e));
}
function ec(e, t, n = {}, i) {
  const r = [], { velocity: o } = n, s = n.reduceMotion ?? i?.shouldReduceMotion;
  for (const l in t) {
    if (l === "transition" || l === "transitionEnd")
      continue;
    const c = t[l];
    if (c === void 0)
      continue;
    const u = e(l), f = u.get();
    if (f !== void 0 && !u.isAnimating() && !Array.isArray(c) && c === f && !o) {
      K.update(() => u.set(c));
      continue;
    }
    u.start(ei(l, u, c, s && ns.has(l) ? { type: !1 } : n, i)), u.animation && r.push(u.animation);
  }
  const { transitionEnd: a } = t;
  if (a) {
    const l = () => K.update(() => {
      for (const c in a)
        e(c).set(a[c]);
    });
    r.length ? Promise.all(r).then(l) : l();
  }
  return r;
}
function tc(e, t, n, i, r) {
  return ec((o) => {
    let s = e.get(t, o);
    if (!s) {
      let a;
      if (!r) {
        const l = n[o];
        a = Yh(l) ?? e.read(t, o, l), Te(a !== void 0, `"${o}" can't be read from the animated subject. Provide [from, to] keyframes.`, "effect-unreadable-value");
      }
      s = ze(a, { owner: r }), e(t, { [o]: s });
    }
    return s;
  }, n, i, r);
}
function Yh(e) {
  const t = Array.isArray(e) ? e[0] : void 0;
  return t === null ? void 0 : t;
}
function Tt(e) {
  return Or(e) && "offsetHeight" in e && !("ownerSVGElement" in e);
}
function Mt(e) {
  return Or(e) && "ownerSVGElement" in e;
}
const _e = (e, t) => t && typeof e == "number" ? t.transform(e) : e;
function ss(e, t, n) {
  if (e == null)
    return [];
  if (e instanceof EventTarget)
    return [e];
  if (typeof e == "string") {
    let i = document;
    t && (i = t.current);
    const r = n?.[e] ?? i.querySelectorAll(e);
    return r ? Array.from(r) : [];
  }
  return Array.from(e).filter((i) => i != null);
}
class Xh {
  /**
   * @param step - The frameloop step renders are scheduled in. Defaults
   * to `frame.render`. Effects that feed a render loop running in
   * `frame.render` (GPU scenes) should write in `frame.preRender`.
   */
  constructor(t = K.render) {
    this.step = t, this.values = /* @__PURE__ */ new Map(), this.pending = [], this.numPending = 0, this.flush = () => {
      const { pending: n, numPending: i } = this;
      this.numPending = 0;
      for (let r = 0; r < i; r++)
        n[r]();
    };
  }
  /**
   * @param render - Writes the value to the subject. Renders read the
   * motion value directly rather than a cached copy, so there is one
   * place a value lives.
   * @param computed - A value already in this state (e.g. `transform`)
   * whose render should run whenever `value` changes.
   */
  set(t, n, i, r) {
    if (this.values.get(t)?.onRemove(), r)
      for (const l of this.values.values())
        l.value === r && (i = l.render);
    const o = () => i && this.schedule(i);
    n.get() !== void 0 && o();
    const s = n.on("change", o), a = () => {
      s(), i && !r && this.cancel(i), this.values.delete(t);
    };
    return this.values.set(t, {
      value: n,
      render: r ? void 0 : i,
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
    for (let r = 0; r < i; r++)
      if (n[r] === t)
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
function os(e, { step: t, ...n } = {}) {
  const i = /* @__PURE__ */ new WeakMap();
  return Object.assign((o, s) => {
    const a = i.get(o) ?? new Xh(t);
    i.set(o, a);
    const l = [];
    for (const c in s) {
      const u = s[c], f = e(o, a, c, u);
      l.push(f);
    }
    return () => {
      for (const c of l)
        c();
    };
  }, n, {
    get: (o, s) => i.get(o)?.get(s),
    flush: (o) => i.get(o)?.flush(),
    state: (o) => i.get(o)
  });
}
const Qh = {
  x: "translateX",
  y: "translateY",
  z: "translateZ",
  transformPerspective: "perspective"
}, oo = {};
function Zh(e) {
  let t = "";
  const { transformKeys: n = [], transformValues: i = {} } = e;
  for (let o = 0; o < n.length; o++) {
    const s = n[o], a = i[s].get();
    if (a === void 0)
      continue;
    (typeof a == "number" ? a : parseFloat(a)) !== (s.startsWith("scale") ? 1 : 0) && (t += (t && " ") + (oo[s] || (oo[s] = (Qh[s] || s) + "(")) + _e(a, Yi[s]) + ")");
  }
  const r = e.get("pathRotation")?.get();
  return r && (t += (t && " ") + "rotate(" + _e(r, Yi.pathRotation) + ")"), t || "none";
}
const Jh = /* @__PURE__ */ new Set(["originX", "originY", "originZ"]), xi = (e, t) => _e(e.get(t)?.get(), Ve[t]), as = (e, t, n, i) => {
  let r, o;
  if (We.has(n)) {
    if (n !== "pathRotation") {
      const s = t.transformKeys ?? (t.transformKeys = []);
      (t.transformValues ?? (t.transformValues = {}))[n] = i, s.includes(n) || (s.push(n), s.sort((a, l) => Ye.indexOf(a) - Ye.indexOf(l)));
    }
    t.get("transform") || (!Tt(e) && !t.get("transformBox") && as(e, t, "transformBox", new $t("fill-box")), t.set("transform", new $t("none"), () => {
      e.style.transform = Zh(t);
    })), o = t.get("transform");
  } else Jh.has(n) ? (t.get("transformOrigin") || t.set("transformOrigin", new $t(""), () => {
    const s = xi(t, "originX") ?? "50%", a = xi(t, "originY") ?? "50%", l = xi(t, "originZ") ?? 0;
    e.style.transformOrigin = `${s} ${a} ${l}`;
  }), o = t.get("transformOrigin")) : Zr(n) ? r = () => {
    e.style.setProperty(n, i.get());
  } : r = () => {
    e.style[n] = _e(i.get(), Ve[n]);
  };
  return t.set(n, i, r, o);
}, ep = (e) => Tt(e) || Mt(e), nc = (e, t) => {
  if (We.has(t))
    return Ol(e, t);
  const n = getComputedStyle(e), i = Zr(t) ? n.getPropertyValue(t) : n[t];
  return typeof i == "string" && i.trim() || 0;
}, tp = /* @__PURE__ */ os(as, {
  test: ep,
  read: nc
}), np = {
  x: "translateX",
  y: "translateY",
  z: "translateZ",
  transformPerspective: "perspective"
}, ip = Ye.length;
function rp(e, t, n) {
  let i = "", r = !0;
  for (let s = 0; s < ip; s++) {
    const a = Ye[s], l = e[a];
    if (l === void 0)
      continue;
    let c = !0;
    if (typeof l == "number")
      c = l === (a.startsWith("scale") ? 1 : 0);
    else {
      const u = parseFloat(l);
      c = a.startsWith("scale") ? u === 1 : u === 0;
    }
    if (!c || n) {
      const u = _e(l, Ve[a]);
      if (!c) {
        r = !1;
        const f = np[a] || a;
        i += `${f}(${u}) `;
      }
      n && (t[a] = u);
    }
  }
  const o = e.pathRotation;
  return o && (r = !1, i += `rotate(${_e(o, Ve.pathRotation)}) `), i = i.trim(), n ? i = n(t, r ? "" : i) : r && (i = "none"), i;
}
function ls(e, t, n) {
  const { style: i, vars: r, transformOrigin: o } = e;
  let s = !1, a = !1;
  for (const l in t) {
    const c = t[l];
    if (We.has(l)) {
      s = !0;
      continue;
    } else if (xl(l)) {
      r[l] = c;
      continue;
    } else {
      const u = _e(c, Ve[l]);
      l.startsWith("origin") ? (a = !0, o[l] = u) : i[l] = u;
    }
  }
  if (t.transform || (s || n ? i.transform = rp(t, e.transform, n) : i.transform && (i.transform = "none")), a) {
    const { originX: l = "50%", originY: c = "50%", originZ: u = 0 } = o;
    i.transformOrigin = `${l} ${c} ${u}`;
  }
}
const sp = {
  offset: "stroke-dashoffset",
  array: "stroke-dasharray"
}, op = {
  offset: "strokeDashoffset",
  array: "strokeDasharray"
};
function ap(e, t, n = 1, i = 0, r = !0) {
  e.pathLength = 1;
  const o = r ? sp : op;
  e[o.offset] = `${-i}`, e[o.array] = `${t} ${n}`;
}
const cs = [
  "transform",
  "opacity",
  "offsetDistance",
  "offsetPath",
  "offsetRotate",
  "offsetAnchor"
];
function ic(e, {
  attrX: t,
  attrY: n,
  attrScale: i,
  pathLength: r,
  pathSpacing: o = 1,
  pathOffset: s = 0,
  // This is object creation, which we try to avoid per-frame.
  ...a
}, l, c, u) {
  if (ls(e, a, c), l) {
    e.style.viewBox && (e.attrs.viewBox = e.style.viewBox);
    return;
  }
  e.attrs = e.style, e.style = {};
  const { attrs: f, style: h } = e;
  for (const m of cs)
    f[m] !== void 0 && (h[m] = f[m], delete f[m]);
  (h.transform || f.transformOrigin) && (h.transformOrigin = f.transformOrigin ?? "50% 50%", delete f.transformOrigin), h.transform && (h.transformBox = u?.transformBox ?? "fill-box", delete f.transformBox), t !== void 0 && (f.x = t), n !== void 0 && (f.y = n), i !== void 0 && (f.scale = i), r !== void 0 && ap(f, r, o, s, !1);
}
function lp(e, t) {
  if (!(t in e))
    return !1;
  const n = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e), t) || Object.getOwnPropertyDescriptor(e, t);
  return n && typeof n.set == "function";
}
const ao = (e, t, n, i, r = n) => {
  const o = lp(e, r);
  !o && (r.startsWith("data") || r.startsWith("aria")) && (r = an(r));
  const s = Ve[n] || Ve[r], a = o ? () => {
    e[r] = _e(i.get(), Ve[n]);
  } : () => {
    const l = _e(i.get(), s);
    l == null ? e.removeAttribute(r) : e.setAttribute(r, String(l));
  };
  return t.set(n, i, a);
};
function cp(e, t, n, i) {
  return K.render(() => e.setAttribute("pathLength", "1")), n === "pathOffset" ? t.set(n, i, () => {
    const r = i.get();
    e.setAttribute("stroke-dashoffset", `${-r}`);
  }) : (t.get("stroke-dasharray") || t.set("stroke-dasharray", new $t("1 1"), () => {
    const r = t.get("pathLength")?.get() ?? 1, o = t.get("pathSpacing")?.get();
    e.setAttribute("stroke-dasharray", `${r} ${o ?? 1 - Number(r)}`);
  }), t.set(n, i, void 0, t.get("stroke-dasharray")));
}
const up = (e, t, n, i) => n.startsWith("path") ? cp(e, t, n, i) : n.startsWith("attr") ? ao(e, t, n, i, rc(n)) : (n in e.style ? as : ao)(e, t, n, i), fp = (e, t) => We.has(t) ? Ve[t]?.default || 0 : cs.includes(t) ? nc(e, t) : (t = rc(t), e.getAttribute(an(t)) ?? e.getAttribute(t) ?? void 0), dp = /* @__PURE__ */ os(up, {
  test: Mt,
  read: fp
});
function rc(e) {
  return e.replace(/^attr([A-Z])/, (t, n) => n.toLowerCase());
}
function sc({ top: e, left: t, right: n, bottom: i }) {
  return {
    x: { min: t, max: n },
    y: { min: e, max: i }
  };
}
function hp({ x: e, y: t }) {
  return { top: t.min, right: e.max, bottom: t.max, left: e.min };
}
function pp(e, t) {
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
function bi(e) {
  return e === void 0 || e === 1;
}
function lr({ scale: e, scaleX: t, scaleY: n }) {
  return !bi(e) || !bi(t) || !bi(n);
}
function Je(e) {
  return lr(e) || oc(e) || e.z || e.rotate || e.rotateX || e.rotateY || e.skewX || e.skewY;
}
function oc(e) {
  return lo(e.x) || lo(e.y);
}
function lo(e) {
  return e && e !== "0%";
}
function zn(e, t, n) {
  const i = e - n, r = t * i;
  return n + r;
}
function co(e, t, n, i, r) {
  return r !== void 0 && (e = zn(e, r, i)), zn(e, n, i) + t;
}
function cr(e, t = 0, n = 1, i, r) {
  e.min = co(e.min, t, n, i, r), e.max = co(e.max, t, n, i, r);
}
function ac(e, { x: t, y: n }) {
  cr(e.x, t.translate, t.scale, t.originPoint), cr(e.y, n.translate, n.scale, n.originPoint);
}
const uo = 0.999999999999, fo = 1.0000000000001;
function mp(e, t, n, i = !1) {
  const r = n.length;
  if (!r)
    return;
  t.x = t.y = 1;
  let o, s;
  for (let a = 0; a < r; a++) {
    o = n[a], s = o.projectionDelta;
    const { visualElement: l } = o.options;
    l && l.props.style && l.props.style.display === "contents" || (i && o.options.layoutScroll && o.scroll && o !== o.root && (Re(e.x, -o.scroll.offset.x), Re(e.y, -o.scroll.offset.y)), s && (t.x *= s.x.scale, t.y *= s.y.scale, ac(e, s)), i && Je(o.latestValues) && Cn(e, o.latestValues, o.layout?.layoutBox));
  }
  t.x < fo && t.x > uo && (t.x = 1), t.y < fo && t.y > uo && (t.y = 1);
}
function Re(e, t) {
  e.min += t, e.max += t;
}
function ho(e, t, n, i, r = 0.5) {
  const o = Y(e.min, e.max, r);
  cr(e, t, n, o, i);
}
function po(e, t) {
  return typeof e == "string" ? parseFloat(e) / 100 * (t.max - t.min) : e;
}
function Cn(e, t, n) {
  const i = n ?? e;
  ho(e.x, po(t.x, i.x), t.scaleX, t.scale, t.originX), ho(e.y, po(t.y, i.y), t.scaleY, t.scale, t.originY);
}
function us(e, t) {
  return sc(pp(e.getBoundingClientRect(), t));
}
function gp(e, t, n) {
  const i = us(e, n), { scroll: r } = t;
  return r && (Re(i.x, r.offset.x), Re(i.y, r.offset.y)), i;
}
const yp = {}, xp = (e) => Mt(e) ? dp : tp;
class bp {
  constructor(t, n) {
    this.effect = t, this.current = n, this.KeyframeResolver = Zl;
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
    return us(this.current);
  }
  getProps() {
    return yp;
  }
}
function vp(e, t, n, i) {
  if (i)
    return ec((o) => i.getValue(o, null), t, n, i);
  const r = xp(e);
  return tc(r, e, t, n, new bp(r, e));
}
const wp = /* @__PURE__ */ os((e, t, n, i) => t.set(n, i, () => {
  e[n] = i.get();
}), {
  test: (e) => Or(e),
  read: (e, t) => {
    const n = e[t];
    return typeof n == "string" || typeof n == "number" ? n : void 0;
  }
}), { schedule: fs } = /* @__PURE__ */ gl(queueMicrotask, !1), Ce = {
  x: !1,
  y: !1
};
function lc() {
  return Ce.x || Ce.y;
}
function kp(e) {
  return e === "x" || e === "y" ? Ce[e] ? null : (Ce[e] = !0, () => {
    Ce[e] = !1;
  }) : Ce.x || Ce.y ? null : (Ce.x = Ce.y = !0, () => {
    Ce.x = Ce.y = !1;
  });
}
function cc(e, t) {
  const n = ss(e), i = new AbortController(), r = {
    passive: !0,
    ...t,
    signal: i.signal
  };
  return [n, r, () => i.abort()];
}
function Tp(e) {
  return !(e.pointerType === "touch" || lc());
}
function Sp(e, t, n = {}) {
  const [i, r, o] = cc(e, n);
  return i.forEach((s) => {
    let a = !1, l = !1, c;
    const u = () => {
      s.removeEventListener("pointerleave", p);
    }, f = (y) => {
      c && (c(y), c = void 0), u();
    }, h = (y) => {
      a = !1, window.removeEventListener("pointerup", h), window.removeEventListener("pointercancel", h), l && (l = !1, f(y));
    }, m = () => {
      a = !0, window.addEventListener("pointerup", h, r), window.addEventListener("pointercancel", h, r);
    }, p = (y) => {
      if (y.pointerType !== "touch") {
        if (a) {
          l = !0;
          return;
        }
        f(y);
      }
    }, g = (y) => {
      if (!Tp(y))
        return;
      l = !1;
      const b = t(s, y);
      typeof b == "function" && (c = b, s.addEventListener("pointerleave", p, r));
    };
    s.addEventListener("pointerenter", g, r), s.addEventListener("pointerdown", m, r);
  }), o;
}
const uc = (e, t) => t ? e === t ? !0 : uc(e, t.parentElement) : !1, ds = (e) => e.pointerType === "mouse" ? typeof e.button != "number" || e.button <= 0 : e.isPrimary !== !1, Ap = /* @__PURE__ */ new Set([
  "BUTTON",
  "INPUT",
  "SELECT",
  "TEXTAREA",
  "A"
]);
function Cp(e) {
  return Ap.has(e.tagName) || e.isContentEditable === !0;
}
const Np = /* @__PURE__ */ new Set(["INPUT", "SELECT", "TEXTAREA"]);
function Pp(e) {
  return Np.has(e.tagName) || e.isContentEditable === !0;
}
const Nn = /* @__PURE__ */ new WeakSet();
function mo(e) {
  return (t) => {
    t.key === "Enter" && e(t);
  };
}
function vi(e, t) {
  e.dispatchEvent(new PointerEvent("pointer" + t, { isPrimary: !0, bubbles: !0 }));
}
const Mp = (e, t) => {
  const n = e.currentTarget;
  if (!n)
    return;
  const i = mo(() => {
    if (Nn.has(n))
      return;
    vi(n, "down");
    const r = mo(() => {
      vi(n, "up");
    }), o = () => vi(n, "cancel");
    n.addEventListener("keyup", r, t), n.addEventListener("blur", o, t);
  });
  n.addEventListener("keydown", i, t), n.addEventListener("blur", () => n.removeEventListener("keydown", i), t);
};
function go(e) {
  return ds(e) && !lc();
}
const yo = /* @__PURE__ */ new WeakSet();
function Ep(e, t, n = {}) {
  const [i, r, o] = cc(e, n), s = (a) => {
    const l = a.currentTarget;
    if (!go(a) || yo.has(a))
      return;
    Nn.add(l), n.stopPropagation && yo.add(a);
    const c = t(l, a), u = { ...r, capture: !0 }, f = (p, g) => {
      window.removeEventListener("pointerup", h, u), window.removeEventListener("pointercancel", m, u), Nn.has(l) && Nn.delete(l), go(p) && typeof c == "function" && c(p, { success: g });
    }, h = (p) => {
      f(p, l === window || l === document || n.useGlobalTarget || uc(l, p.target));
    }, m = (p) => {
      f(p, !1);
    };
    window.addEventListener("pointerup", h, u), window.addEventListener("pointercancel", m, u);
  };
  return i.forEach((a) => {
    (n.useGlobalTarget ? window : a).addEventListener("pointerdown", s, r), Tt(a) && (a.addEventListener("focus", (c) => Mp(c, r)), !Cp(a) && !a.hasAttribute("tabindex") && (a.tabIndex = 0));
  }), o;
}
const Pn = /* @__PURE__ */ new WeakMap();
let Mn;
const fc = (e, t, n) => (i, r) => r && r[0] ? r[0][e + "Size"] : Mt(i) && "getBBox" in i ? i.getBBox()[t] : i[n], Dp = /* @__PURE__ */ fc("inline", "width", "offsetWidth"), Rp = /* @__PURE__ */ fc("block", "height", "offsetHeight");
function Lp({ target: e, borderBoxSize: t }) {
  Pn.get(e)?.forEach((n) => {
    n(e, {
      get width() {
        return Dp(e, t);
      },
      get height() {
        return Rp(e, t);
      }
    });
  });
}
function Vp(e) {
  e.forEach(Lp);
}
function Fp() {
  typeof ResizeObserver > "u" || (Mn = new ResizeObserver(Vp));
}
function Ip(e, t) {
  Mn || Fp();
  const n = ss(e);
  return n.forEach((i) => {
    let r = Pn.get(i);
    r || (r = /* @__PURE__ */ new Set(), Pn.set(i, r)), r.add(t), Mn?.observe(i);
  }), () => {
    n.forEach((i) => {
      const r = Pn.get(i);
      r?.delete(t), r?.size || Mn?.unobserve(i);
    });
  };
}
const En = /* @__PURE__ */ new Set();
let xt;
function Op() {
  xt = () => {
    const e = {
      get width() {
        return window.innerWidth;
      },
      get height() {
        return window.innerHeight;
      }
    };
    En.forEach((t) => t(e));
  }, window.addEventListener("resize", xt);
}
function Bp(e) {
  return En.add(e), xt || Op(), () => {
    En.delete(e), !En.size && typeof xt == "function" && (window.removeEventListener("resize", xt), xt = void 0);
  };
}
function xo(e, t) {
  return typeof e == "function" ? Bp(e) : Ip(e, t);
}
function jp(e) {
  return Mt(e) && e.tagName === "svg";
}
function $p(...e) {
  const t = !Array.isArray(e[0]), n = t ? 0 : -1, i = e[0 + n], r = e[1 + n], o = e[2 + n], s = e[3 + n], a = El(r, o, s);
  return t ? a(i) : a;
}
const bo = () => ({
  translate: 0,
  scale: 1,
  origin: 0,
  originPoint: 0
}), bt = () => ({
  x: bo(),
  y: bo()
}), vo = () => ({ min: 0, max: 0 }), oe = () => ({
  x: vo(),
  y: vo()
}), dc = /* @__PURE__ */ new WeakMap();
function ti(e) {
  return e !== null && typeof e == "object" && typeof e.start == "function";
}
function Xt(e) {
  return typeof e == "string" || Array.isArray(e);
}
const hs = [
  "animate",
  "whileInView",
  "whileFocus",
  "whileHover",
  "whileTap",
  "whileDrag",
  "exit"
], _n = ["initial", ...hs];
function ni(e) {
  if (ti(e.animate))
    return !0;
  for (let t = 0; t < _n.length; t++)
    if (Xt(e[_n[t]]))
      return !0;
  return !1;
}
function hc(e) {
  return !!(ni(e) || e.variants);
}
function zp(e, t, n) {
  for (const i in t) {
    const r = t[i], o = n[i];
    if (ce(r))
      e.addValue(i, r);
    else if (ce(o))
      e.addValue(i, ze(r, { owner: e }));
    else if (o !== r)
      if (e.hasValue(i)) {
        const s = e.getValue(i);
        s.liveStyle === !0 ? s.jump(r) : s.hasAnimated || s.set(r);
      } else {
        const s = e.getStaticValue(i);
        e.addValue(i, ze(s !== void 0 ? s : r, { owner: e }));
      }
  }
  for (const i in n)
    t[i] === void 0 && e.removeValue(i);
  return t;
}
const Un = { current: null }, ps = { current: !1 }, _p = typeof window < "u";
function pc() {
  if (ps.current = !0, !!_p)
    if (window.matchMedia) {
      const e = window.matchMedia("(prefers-reduced-motion)"), t = () => Un.current = e.matches;
      e.addEventListener("change", t), t();
    } else
      Un.current = !1;
}
const wo = [
  "AnimationStart",
  "AnimationComplete",
  "Update",
  "BeforeLayoutMeasure",
  "LayoutMeasure",
  "LayoutAnimationStart",
  "LayoutAnimationComplete"
];
let Wn = {};
function mc(e) {
  Wn = e;
}
function Up() {
  return Wn;
}
class Wp {
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
  constructor({ parent: t, props: n, presenceContext: i, reducedMotionConfig: r, skipAnimations: o, blockInitialAnimation: s, visualState: a }, l = {}) {
    this.current = null, this.children = /* @__PURE__ */ new Set(), this.isVariantNode = !1, this.isControllingVariants = !1, this.shouldReduceMotion = null, this.shouldSkipAnimations = !1, this.values = /* @__PURE__ */ new Map(), this.KeyframeResolver = Qr, this.features = {}, this.valueSubscriptions = /* @__PURE__ */ new Map(), this.prevMotionValues = {}, this.hasBeenMounted = !1, this.events = {}, this.propEventSubscriptions = {}, this.notifyUpdate = () => this.notify("Update", this.latestValues), this.render = () => {
      this.current && (this.triggerBuild(), this.renderInstance(this.current, this.renderState, this.props.style, this.projection));
    }, this.renderScheduledAt = 0, this.scheduleRender = () => {
      const m = fe.now();
      this.renderScheduledAt < m && (this.renderScheduledAt = m, K.render(this.render, !1, !0));
    };
    const { latestValues: c, renderState: u } = a;
    this.latestValues = c, this.baseTarget = { ...c }, this.initialValues = n.initial ? { ...c } : {}, this.renderState = u, this.parent = t, this.props = n, this.presenceContext = i, this.depth = t ? t.depth + 1 : 0, this.reducedMotionConfig = r, this.skipAnimationsConfig = o, this.options = l, this.blockInitialAnimation = !!s, this.isControllingVariants = ni(n), this.isVariantNode = hc(n), this.isVariantNode && (this.variantChildren = /* @__PURE__ */ new Set()), this.manuallyAnimateOnMount = !!(t && t.current);
    const { willChange: f, ...h } = this.scrapeMotionValuesFromProps(n, {}, this);
    for (const m in h) {
      const p = h[m];
      c[m] !== void 0 && ce(p) && p.set(c[m]);
    }
  }
  mount(t) {
    if (this.hasBeenMounted)
      for (const n in this.initialValues)
        this.values.get(n)?.jump(this.initialValues[n]), this.latestValues[n] = this.initialValues[n];
    this.current = t, dc.set(t, this), this.projection && !this.projection.instance && this.projection.mount(t), this.parent && this.isVariantNode && !this.isControllingVariants && (this.removeFromVariantTree = this.parent.addVariantChild(this)), this.values.forEach((n, i) => this.bindToMotionValue(i, n)), this.reducedMotionConfig === "never" ? this.shouldReduceMotion = !1 : this.reducedMotionConfig === "always" ? this.shouldReduceMotion = !0 : (ps.current || pc(), this.shouldReduceMotion = Un.current), process.env.NODE_ENV !== "production" && Zn(this.shouldReduceMotion !== !0, "You have Reduced Motion enabled on your device. Animations may not appear as expected.", "reduced-motion-disabled"), this.shouldSkipAnimations = this.skipAnimationsConfig ?? !1, this.parent?.addChild(this), this.update(this.props, this.presenceContext), this.hasBeenMounted = !0;
  }
  unmount() {
    this.projection && this.projection.unmount(), $e(this.notifyUpdate), $e(this.render), this.valueSubscriptions.forEach((t) => t()), this.valueSubscriptions.clear(), this.removeFromVariantTree && this.removeFromVariantTree(), this.parent?.removeChild(this);
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
    if (this.valueSubscriptions.has(t) && this.valueSubscriptions.get(t)(), n.accelerate && rr.has(t) && this.current instanceof HTMLElement) {
      const { factory: s, keyframes: a, times: l, ease: c, duration: u } = n.accelerate, f = new Wl({
        element: this.current,
        name: t,
        keyframes: a,
        times: l,
        ease: c,
        duration: /* @__PURE__ */ xe(u)
      }), h = s(f);
      this.valueSubscriptions.set(t, () => {
        h(), f.cancel();
      });
      return;
    }
    const i = We.has(t);
    i && this.onBindTransform && this.onBindTransform();
    const r = n.on("change", (s) => {
      this.latestValues[t] = s, this.props.onUpdate && K.preRender(this.notifyUpdate), i && this.projection && (this.projection.isTransformDirty = !0), this.scheduleRender();
    });
    let o;
    typeof window < "u" && window.MotionCheckAppearSync && (o = window.MotionCheckAppearSync(this, t, n)), this.valueSubscriptions.set(t, () => {
      r(), o && o();
    });
  }
  sortNodePosition(t) {
    return !this.current || !this.sortInstanceNodePosition || this.type !== t.type ? 0 : this.sortInstanceNodePosition(this.current, t.current);
  }
  updateFeatures() {
    let t = "animation";
    for (t in Wn) {
      const n = Wn[t];
      if (!n)
        continue;
      const { isEnabled: i, Feature: r } = n;
      if (!this.features[t] && r && i(this.props) && (this.features[t] = new r(this)), this.features[t]) {
        const o = this.features[t];
        o.isMounted ? o.update() : (o.mount(), o.isMounted = !0);
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
    return this.current ? this.measureInstanceViewportBox(this.current, this.props) : oe();
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
    for (let i = 0; i < wo.length; i++) {
      const r = wo[i];
      this.propEventSubscriptions[r] && (this.propEventSubscriptions[r](), delete this.propEventSubscriptions[r]);
      const o = "on" + r, s = t[o];
      s && (this.propEventSubscriptions[r] = this.on(r, s));
    }
    this.prevMotionValues = zp(this, this.scrapeMotionValuesFromProps(t, this.prevProps || {}, this), this.prevMotionValues), this.handleChildMotionValue && this.handleChildMotionValue();
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
    return i === void 0 && n !== void 0 && (i = ze(n === null ? void 0 : n, { owner: this }), this.addValue(t, i)), i;
  }
  /**
   * If we're trying to animate to a previously unencountered value,
   * we need to check for it in our state and as a last resort read it
   * directly from the instance (which might have performance implications).
   */
  readValue(t, n) {
    let i = this.latestValues[t] !== void 0 || !this.current ? this.latestValues[t] : this.getBaseTargetFromProps(this.props, t) ?? this.readValueFromInstance(this.current, t, this.options);
    return i != null && (typeof i == "string" && (Ir(i) || Br(i)) ? i = parseFloat(i) : (
      /**
       * If the value as read isn't animatable (e.g. "none") but
       * the target is, derive an animatable none from the target.
       * A value is animatable if it's a number or contains a
       * number or color, which is cheaper to check than trying
       * every value type in turn.
       */
      typeof i != "number" && !ke.test(i) && ke.test(n) && (i = Xr(t, n))
    ), this.setBaseTarget(t, ce(i) ? i.get() : i)), ce(i) ? i.get() : i;
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
      const o = ts(this.props, n, this.presenceContext?.custom);
      o && (i = o[t]);
    }
    if (n && i !== void 0)
      return i;
    const r = this.getBaseTargetFromProps(this.props, t);
    return r !== void 0 && !ce(r) ? r : this.initialValues[t] !== void 0 && i === void 0 ? void 0 : this.baseTarget[t];
  }
  on(t, n) {
    return this.events[t] || (this.events[t] = new On()), this.events[t].add(n);
  }
  notify(t, ...n) {
    this.events[t] && this.events[t].notify(...n);
  }
  scheduleRenderMicrotask() {
    fs.render(this.render);
  }
}
class gc extends Wp {
  constructor() {
    super(...arguments), this.KeyframeResolver = Zl;
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
    ce(t) && (this.childSubscription = t.on("change", (n) => {
      this.current && (this.current.textContent = `${n}`);
    }));
  }
}
class Xe {
  constructor(t) {
    this.isMounted = !1, this.node = t;
  }
  update() {
  }
}
function yc(e, { style: t, vars: n }, i, r) {
  const o = e.style;
  let s;
  for (s in t)
    o[s] = t[s];
  r?.applyProjectionStyles(o, i);
  for (s in n)
    o.setProperty(s, n[s]);
}
function ko(e, t) {
  return t.max === t.min ? 0 : e / (t.max - t.min) * 100;
}
const Lt = {
  correct: (e, t) => {
    if (!t.target)
      return e;
    if (typeof e == "string")
      if (L.test(e))
        e = parseFloat(e);
      else
        return e;
    const n = ko(e, t.target.x), i = ko(e, t.target.y);
    return `${n}% ${i}%`;
  }
}, Hp = {
  correct: (e, { treeScale: t, projectionDelta: n }) => {
    const i = e, r = ke.parse(e);
    if (r.length > 5)
      return i;
    const o = ke.createTransformer(e), s = typeof r[0] != "number" ? 1 : 0, a = n.x.scale * t.x, l = n.y.scale * t.y;
    r[0 + s] /= a, r[1 + s] /= l;
    const c = Y(a, l, 0.5);
    return typeof r[2 + s] == "number" && (r[2 + s] /= c), typeof r[3 + s] == "number" && (r[3 + s] /= c), o(r);
  }
}, ur = {
  borderRadius: {
    ...Lt,
    applyTo: [...is]
  },
  borderTopLeftRadius: Lt,
  borderTopRightRadius: Lt,
  borderBottomLeftRadius: Lt,
  borderBottomRightRadius: Lt,
  boxShadow: Hp
};
function xc(e, { layout: t, layoutId: n }) {
  return We.has(e) || e.startsWith("origin") || (t || n !== void 0) && (!!ur[e] || e === "opacity");
}
function ms(e, t, n) {
  const i = e.style, r = t?.style, o = {};
  if (!i)
    return o;
  for (const s in i)
    (ce(i[s]) || r && ce(r[s]) || xc(s, e) || n?.getValue(s)?.liveStyle !== void 0) && (o[s] = i[s]);
  return o;
}
function Gp(e) {
  return window.getComputedStyle(e);
}
class Kp extends gc {
  constructor() {
    super(...arguments), this.type = "html", this.renderInstance = yc;
  }
  mount(t) {
    Te(!!t.style, "motion.create() components must forward their ref to a HTML or SVG element", "custom-component-ref"), super.mount(t);
  }
  readValueFromInstance(t, n) {
    if (We.has(n))
      return this.projection?.isProjecting ? Zi(n) : Ol(t, n);
    {
      const i = Gp(t), r = (xl(n) ? i.getPropertyValue(n) : i[n]) || 0;
      return typeof r == "string" ? r.trim() : r;
    }
  }
  measureInstanceViewportBox(t, { transformPagePoint: n }) {
    return us(t, n);
  }
  build(t, n, i) {
    ls(t, n, i.transformTemplate);
  }
  scrapeMotionValuesFromProps(t, n, i) {
    return ms(t, n, i);
  }
}
const bc = /* @__PURE__ */ new Set([
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
]), vc = (e) => typeof e == "string" && e.toLowerCase() === "svg";
function qp(e, t, n, i) {
  yc(e, t, void 0, i);
  for (const r in t.attrs)
    e.setAttribute(bc.has(r) ? r : an(r), t.attrs[r]);
}
function wc(e, t, n) {
  const i = ms(e, t, n);
  for (const r in e)
    if (ce(e[r]) || ce(t[r])) {
      const o = Ye.indexOf(r) !== -1 ? "attr" + r.charAt(0).toUpperCase() + r.substring(1) : r;
      i[o] = e[r];
    }
  return i;
}
class Yp extends gc {
  constructor() {
    super(...arguments), this.type = "svg", this.isSVGTag = !1, this.measureInstanceViewportBox = oe;
  }
  getBaseTargetFromProps(t, n) {
    return t[n];
  }
  readValueFromInstance(t, n) {
    if (We.has(n)) {
      const i = Il(n);
      return i && i.default || 0;
    }
    if (cs.includes(n)) {
      const r = getComputedStyle(t)[n];
      if (typeof r == "string" && r)
        return r.trim();
    }
    return n = bc.has(n) ? n : an(n), t.getAttribute(n);
  }
  scrapeMotionValuesFromProps(t, n, i) {
    return wc(t, n, i);
  }
  build(t, n, i) {
    ic(t, n, this.isSVGTag, i.transformTemplate, i.style);
  }
  renderInstance(t, n, i, r) {
    qp(t, n, i, r);
  }
  mount(t) {
    this.isSVGTag = vc(t.tagName), super.mount(t);
  }
}
const Xp = _n.length;
function kc(e) {
  if (!e)
    return;
  if (!e.isControllingVariants) {
    const n = e.parent ? kc(e.parent) || {} : {};
    return e.props.initial !== void 0 && (n.initial = e.props.initial), n;
  }
  const t = {};
  for (let n = 0; n < Xp; n++) {
    const i = _n[n], r = e.props[i];
    (Xt(r) || r === !1) && (t[i] = r);
  }
  return t;
}
function Tc(e, t) {
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
const Qp = [...hs].reverse(), Zp = hs.length;
function Jp(e) {
  return (t) => Promise.all(t.map(({ animation: n, options: i }) => $h(e, n, i)));
}
function em(e) {
  let t = Jp(e), n = To(), i = !0, r = !1;
  const o = (c) => (u, f) => {
    const h = st(e, f, c === "exit" ? e.presenceContext?.custom : void 0);
    if (h) {
      const { transition: m, transitionEnd: p, ...g } = h;
      u = { ...u, ...g, ...p };
    }
    return u;
  };
  function s(c) {
    t = c(e);
  }
  function a(c) {
    const { props: u } = e, f = kc(e.parent) || {}, h = [], m = /* @__PURE__ */ new Set();
    let p = {}, g = 1 / 0;
    for (let b = 0; b < Zp; b++) {
      const k = Qp[b], x = n[k], S = u[k] !== void 0 ? u[k] : f[k], E = Xt(S), C = k === c ? x.isActive : null;
      C === !1 && (g = b);
      let A = S === f[k] && S !== u[k] && E;
      if (A && (i || r) && e.manuallyAnimateOnMount && (A = !1), x.protectedKeys = { ...p }, // If it isn't active and hasn't *just* been set as inactive
      !x.isActive && C === null || // If we didn't and don't have any defined prop for this animation type
      !S && !x.prevProp || // Or if the prop doesn't define an animation
      ti(S) || typeof S == "boolean")
        continue;
      if (k === "exit" && x.isActive && C !== !0) {
        x.prevResolvedValues && (p = {
          ...p,
          ...x.prevResolvedValues
        });
        continue;
      }
      const N = tm(x.prevProp, S);
      let P = N || // If we're making this variant active, we want to always make it active
      k === c && x.isActive && !A && E || // If we removed a higher-priority variant (i is in reverse order)
      b > g && E, w = !1;
      const T = Array.isArray(S) ? S : [S];
      let I = T.reduce(o(k), {});
      C === !1 && (I = {});
      const { prevResolvedValues: F = {} } = x, X = {
        ...F,
        ...I
      }, q = ($) => {
        P = !0, m.has($) && (w = !0, m.delete($)), x.needsAnimating[$] = !0;
        const ee = e.getValue($);
        ee && (ee.liveStyle = !1);
      };
      for (const $ in X) {
        const ee = I[$], re = F[$];
        if (p.hasOwnProperty($))
          continue;
        let ie = !1;
        sr(ee) && sr(re) ? ie = !Tc(ee, re) || N : ie = ee !== re, ie ? ee != null ? q($) : m.add($) : ee !== void 0 && m.has($) ? q($) : x.protectedKeys[$] = !0;
      }
      x.prevProp = S, x.prevResolvedValues = I, x.isActive && (p = { ...p, ...I }), (i || r) && e.blockInitialAnimation && (P = !1);
      const H = A && N;
      P && (!H || w) && h.push(...T.map(($) => {
        const ee = { type: k };
        if (typeof $ == "string" && (i || r) && !H && e.manuallyAnimateOnMount && e.parent) {
          const { parent: re } = e, ie = st(re, $);
          if (re.enteringChildren && ie) {
            const { delayChildren: R } = ie.transition || {};
            ee.delay = Gl(re.enteringChildren, e, R);
          }
        }
        return {
          animation: $,
          options: ee
        };
      }));
    }
    if (m.size) {
      const b = {};
      if (typeof u.initial != "boolean") {
        const k = st(e, Array.isArray(u.initial) ? u.initial[0] : u.initial);
        k && k.transition && (b.transition = k.transition);
      }
      m.forEach((k) => {
        const x = e.getBaseTarget(k), S = e.getValue(k);
        S && (S.liveStyle = !0), b[k] = x ?? null;
      }), h.push({ animation: b });
    }
    let y = !!h.length;
    return i && (u.initial === !1 || u.initial === u.animate) && !e.manuallyAnimateOnMount && (y = !1), i = !1, r = !1, y ? t(h) : Promise.resolve();
  }
  function l(c, u) {
    if (n[c].isActive === u)
      return Promise.resolve();
    e.variantChildren?.forEach((h) => h.animationState?.setActive(c, u)), n[c].isActive = u;
    const f = a(c);
    for (const h in n)
      n[h].protectedKeys = {};
    return f;
  }
  return {
    animateChanges: a,
    setActive: l,
    setAnimateFunction: s,
    getState: () => n,
    reset: () => {
      n = To(), r = !0;
    }
  };
}
function tm(e, t) {
  return typeof t == "string" ? t !== e : Array.isArray(t) ? !Tc(t, e) : !1;
}
function Qe(e = !1) {
  return {
    isActive: e,
    protectedKeys: {},
    needsAnimating: {},
    prevResolvedValues: {}
  };
}
function To() {
  return {
    animate: Qe(!0),
    whileInView: Qe(),
    whileHover: Qe(),
    whileTap: Qe(),
    whileDrag: Qe(),
    whileFocus: Qe(),
    exit: Qe()
  };
}
function fr(e, t) {
  e.min = t.min, e.max = t.max;
}
function Ae(e, t) {
  fr(e.x, t.x), fr(e.y, t.y);
}
function So(e, t) {
  e.translate = t.translate, e.scale = t.scale, e.originPoint = t.originPoint, e.origin = t.origin;
}
const Sc = 1e-4, nm = 1 - Sc, im = 1 + Sc, Ac = 0.01, rm = 0 - Ac, sm = 0 + Ac;
function me(e) {
  return e.max - e.min;
}
function om(e, t, n) {
  return Math.abs(e - t) <= n;
}
function Ao(e, t, n, i = 0.5) {
  e.origin = i, e.originPoint = Y(t.min, t.max, e.origin), e.scale = me(n) / me(t), e.translate = Y(n.min, n.max, e.origin) - e.originPoint, (e.scale >= nm && e.scale <= im || isNaN(e.scale)) && (e.scale = 1), (e.translate >= rm && e.translate <= sm || isNaN(e.translate)) && (e.translate = 0);
}
function zt(e, t, n, i) {
  Ao(e.x, t.x, n.x, i ? i.originX : void 0), Ao(e.y, t.y, n.y, i ? i.originY : void 0);
}
function Co(e, t, n, i = 0) {
  const r = i ? Y(n.min, n.max, i) : n.min;
  e.min = r + t.min, e.max = e.min + me(t);
}
function am(e, t, n, i) {
  Co(e.x, t.x, n.x, i?.x), Co(e.y, t.y, n.y, i?.y);
}
function No(e, t, n, i = 0) {
  const r = i ? Y(n.min, n.max, i) : n.min;
  e.min = t.min - r, e.max = e.min + me(t);
}
function Hn(e, t, n, i) {
  No(e.x, t.x, n.x, i?.x), No(e.y, t.y, n.y, i?.y);
}
function Po(e, t, n, i, r) {
  return e -= t, e = zn(e, 1 / n, i), r !== void 0 && (e = zn(e, 1 / r, i)), e;
}
function lm(e, t = 0, n = 1, i = 0.5, r, o = e, s = e) {
  if (Le.test(t) && (t = parseFloat(t), t = Y(s.min, s.max, t / 100) - s.min), typeof t != "number")
    return;
  let a = Y(o.min, o.max, i);
  e === o && (a -= t), e.min = Po(e.min, t, n, a, r), e.max = Po(e.max, t, n, a, r);
}
function Mo(e, t, [n, i, r], o, s) {
  lm(e, t[n], t[i], t[r], t.scale, o, s);
}
const cm = ["x", "scaleX", "originX"], um = ["y", "scaleY", "originY"];
function Eo(e, t, n, i) {
  Mo(e.x, t, cm, n ? n.x : void 0, i ? i.x : void 0), Mo(e.y, t, um, n ? n.y : void 0, i ? i.y : void 0);
}
function Do(e) {
  return e.translate === 0 && e.scale === 1;
}
function Cc(e) {
  return Do(e.x) && Do(e.y);
}
function Ro(e, t) {
  return e.min === t.min && e.max === t.max;
}
function fm(e, t) {
  return Ro(e.x, t.x) && Ro(e.y, t.y);
}
function Lo(e, t) {
  return Math.round(e.min) === Math.round(t.min) && Math.round(e.max) === Math.round(t.max);
}
function Nc(e, t) {
  return Lo(e.x, t.x) && Lo(e.y, t.y);
}
function Vo(e) {
  return me(e.x) / me(e.y);
}
function Fo(e, t) {
  return e.translate === t.translate && e.scale === t.scale && e.originPoint === t.originPoint;
}
function De(e) {
  return [e("x"), e("y")];
}
function dm(e, t, n) {
  let i = "";
  const r = e.x.translate / t.x, o = e.y.translate / t.y, s = n?.z || 0;
  if ((r || o || s) && (i = `translate3d(${r}px, ${o}px, ${s}px) `), (t.x !== 1 || t.y !== 1) && (i += `scale(${1 / t.x}, ${1 / t.y}) `), n) {
    const { transformPerspective: c, rotate: u, pathRotation: f, rotateX: h, rotateY: m, skewX: p, skewY: g } = n;
    c && (i = `perspective(${c}px) ${i}`), u && (i += `rotate(${u}deg) `), f && (i += `rotate(${f}deg) `), h && (i += `rotateX(${h}deg) `), m && (i += `rotateY(${m}deg) `), p && (i += `skewX(${p}deg) `), g && (i += `skewY(${g}deg) `);
  }
  const a = e.x.scale * t.x, l = e.y.scale * t.y;
  return (a !== 1 || l !== 1) && (i += `scale(${a}, ${l})`), i || "none";
}
const hm = is.length, Io = (e) => typeof e == "string" ? parseFloat(e) : e, Oo = (e) => typeof e == "number" || L.test(e);
function pm(e, t, n, i, r, o) {
  r ? (e.opacity = Y(0, n.opacity ?? 1, mm(i)), e.opacityExit = Y(t.opacity ?? 1, 0, gm(i))) : o && (e.opacity = Y(t.opacity ?? 1, n.opacity ?? 1, i));
  for (let s = 0; s < hm; s++) {
    const a = is[s];
    let l = Bo(t, a), c = Bo(n, a);
    if (l === void 0 && c === void 0)
      continue;
    l || (l = 0), c || (c = 0), l === 0 || c === 0 || Oo(l) === Oo(c) ? (e[a] = Math.max(Y(Io(l), Io(c), i), 0), (Le.test(c) || Le.test(l)) && (e[a] += "%")) : e[a] = c;
  }
  (t.rotate || n.rotate) && (e.rotate = Y(t.rotate || 0, n.rotate || 0, i));
}
function Bo(e, t) {
  return e[t] !== void 0 ? e[t] : e.borderRadius;
}
const mm = /* @__PURE__ */ Pc(0, 0.5, ul), gm = /* @__PURE__ */ Pc(0.5, 0.95, Ne);
function Pc(e, t, n) {
  return (i) => i < e ? 0 : i > t ? 1 : n(/* @__PURE__ */ St(e, t, i));
}
function Mc(e, t, n) {
  const i = ce(e) ? e : ze(e);
  return i.start(ei("", i, t, n)), i.animation;
}
function Qt(e, t, n, i = { passive: !0 }) {
  return e.addEventListener(t, n, i), () => e.removeEventListener(t, n, i);
}
const ym = (e, t) => e.depth - t.depth;
class xm {
  constructor() {
    this.children = [], this.isDirty = !1;
  }
  add(t) {
    Fr(this.children, t), this.isDirty = !0;
  }
  remove(t) {
    ot(this.children, t), this.isDirty = !0;
  }
  forEach(t) {
    this.isDirty && this.children.sort(ym), this.isDirty = !1, this.children.forEach(t);
  }
}
function bm(e, t) {
  const n = fe.now(), i = ({ timestamp: r }) => {
    const o = r - n;
    o >= t && ($e(i), e(o - t));
  };
  return K.setup(i, !0), () => $e(i);
}
function Dn(e) {
  return ce(e) ? e.get() : e;
}
class vm {
  constructor() {
    this.members = [];
  }
  add(t) {
    Fr(this.members, t);
    for (let n = this.members.length - 1; n >= 0; n--) {
      const i = this.members[n];
      if (i === t || i === this.lead || i === this.prevLead)
        continue;
      const r = i.instance;
      (!r || r.isConnected === !1) && !i.snapshot && (ot(this.members, i), i.unmount());
    }
    t.scheduleRender();
  }
  remove(t) {
    if (ot(this.members, t), t === this.prevLead && (this.prevLead = void 0), t === this.lead) {
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
      const { layoutDependency: r } = i.options, { layoutDependency: o } = t.options;
      (r === void 0 || r !== o) && (t.resumeFrom = i, n && (i.preserveOpacity = !0), i.snapshot && (t.snapshot = i.snapshot, t.snapshot.latestValues = i.animationValues || i.latestValues), t.root?.isUpdating && (t.isLayoutDirty = !0)), t.options.crossfade === !1 && i.hide();
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
const Rn = {
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
}, wi = ["", "X", "Y", "Z"], wm = 1e3;
let km = 0;
function ki(e, t, n, i) {
  const { latestValues: r } = t;
  r[e] && (n[e] = r[e], t.setStaticValue(e, 0), i && (i[e] = 0));
}
function Ec(e) {
  if (e.hasCheckedOptimisedAppear = !0, e.root === e)
    return;
  const { visualElement: t } = e.options;
  if (!t)
    return;
  const n = Xl(t);
  if (window.MotionHasOptimisedAnimation(n, "transform")) {
    const { layout: r, layoutId: o } = e.options;
    window.MotionCancelOptimisedAnimation(n, "transform", K, !(r || o));
  }
  const { parent: i } = e;
  i && !i.hasCheckedOptimisedAppear && Ec(i);
}
function Dc({ attachResizeListener: e, defaultParent: t, measureScroll: n, checkIsScrollRoot: i, resetTransform: r }) {
  return class {
    constructor(s = {}, a = t?.()) {
      this.id = km++, this.animationId = 0, this.animationCommitId = 0, this.children = /* @__PURE__ */ new Set(), this.options = {}, this.isTreeAnimating = !1, this.isAnimationBlocked = !1, this.isLayoutDirty = !1, this.isProjectionDirty = !1, this.isSharedProjectionDirty = !1, this.isTransformDirty = !1, this.updateManuallyBlocked = !1, this.updateBlockedByResize = !1, this.isUpdating = !1, this.isSVG = !1, this.needsReset = !1, this.shouldResetTransform = !1, this.hasCheckedOptimisedAppear = !1, this.treeScale = { x: 1, y: 1 }, this.eventHandlers = /* @__PURE__ */ new Map(), this.hasTreeAnimated = !1, this.layoutVersion = 0, this.updateScheduled = !1, this.scheduleUpdate = () => this.update(), this.projectionUpdateScheduled = !1, this.checkUpdateFailed = () => {
        this.isUpdating && (this.isUpdating = !1, this.clearAllSnapshots());
      }, this.updateProjection = () => {
        this.projectionUpdateScheduled = !1, this.nodes.forEach(Am), this.nodes.forEach(Dm), this.nodes.forEach(Rm), this.nodes.forEach(Cm);
      }, this.resolvedRelativeTargetAt = 0, this.linkedParentVersion = 0, this.hasProjected = !1, this.isVisible = !0, this.animationProgress = 0, this.sharedNodes = /* @__PURE__ */ new Map(), this.latestValues = s, this.root = a ? a.root || a : this, this.path = a ? [...a.path, a] : [], this.parent = a, this.depth = a ? a.depth + 1 : 0;
      for (let l = 0; l < this.path.length; l++)
        this.path[l].shouldResetTransform = !0;
      this.root === this && (this.nodes = new xm());
    }
    addEventListener(s, a) {
      return this.eventHandlers.has(s) || this.eventHandlers.set(s, new On()), this.eventHandlers.get(s).add(a);
    }
    notifyListeners(s, ...a) {
      const l = this.eventHandlers.get(s);
      l && l.notify(...a);
    }
    hasListeners(s) {
      return this.eventHandlers.has(s);
    }
    /**
     * Lifecycles
     */
    mount(s) {
      if (this.instance)
        return;
      this.isSVG = Mt(s) && !jp(s), this.instance = s;
      const { layoutId: a, layout: l, visualElement: c } = this.options;
      if (c && !c.current && c.mount(s), this.root.nodes.add(this), this.parent && this.parent.children.add(this), this.root.hasTreeAnimated && (l || a) && (this.isLayoutDirty = !0), e) {
        let u, f = 0;
        const h = () => this.root.updateBlockedByResize = !1;
        K.read(() => {
          f = window.innerWidth;
        }), e(s, () => {
          const m = window.innerWidth;
          m !== f && (f = m, this.root.updateBlockedByResize = !0, u && u(), u = bm(h, 250), Rn.hasAnimatedSinceResize && (Rn.hasAnimatedSinceResize = !1, this.nodes.forEach(zo)));
        });
      }
      a && this.root.registerSharedNode(a, this), this.options.animate !== !1 && c && (a || l) && this.addEventListener("didUpdate", ({ delta: u, hasLayoutChanged: f, hasRelativeLayoutChanged: h, layout: m }) => {
        if (this.isTreeAnimationBlocked()) {
          this.target = void 0, this.relativeTarget = void 0;
          return;
        }
        const p = this.options.transition || c.getDefaultTransition() || Om, { onLayoutAnimationStart: g, onLayoutAnimationComplete: y } = c.getProps(), b = !this.targetLayout || !Nc(this.targetLayout, m), k = !f && h;
        if (this.options.layoutRoot || this.resumeFrom || k || f && (b || !this.currentAnimation)) {
          this.resumeFrom && (this.resumingFrom = this.resumeFrom, this.resumingFrom.resumingFrom = void 0);
          const x = {
            ...es(p, "layout"),
            onPlay: g,
            onComplete: y
          };
          (c.shouldReduceMotion || this.options.layoutRoot) && (x.delay = 0, x.type = !1), this.startAnimation(x), this.setAnimationOrigin(u, k, x.path);
        } else
          f || zo(this), this.isLead() && this.options.onExitComplete && this.options.onExitComplete();
        this.targetLayout = m;
      });
    }
    unmount() {
      this.options.layoutId && this.willUpdate(), this.root.nodes.remove(this);
      const s = this.getStack();
      s && s.remove(this), this.parent && this.parent.children.delete(this), this.instance = void 0, this.eventHandlers.clear(), $e(this.updateProjection);
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
      this.isUpdateBlocked() || (this.isUpdating = !0, this.nodes && this.nodes.forEach(Lm), this.animationId++);
    }
    getTransformTemplate() {
      const { visualElement: s } = this.options;
      return s && s.getProps().transformTemplate;
    }
    willUpdate(s = !0) {
      if (this.root.hasTreeAnimated = !0, this.root.isUpdateBlocked()) {
        this.options.onExitComplete && this.options.onExitComplete();
        return;
      }
      if (window.MotionCancelOptimisedAnimation && !this.hasCheckedOptimisedAppear && Ec(this), !this.root.isUpdating && this.root.startUpdate(), this.isLayoutDirty)
        return;
      this.isLayoutDirty = !0;
      for (let u = 0; u < this.path.length; u++) {
        const f = this.path[u];
        f.shouldResetTransform = !0, (typeof f.latestValues.x == "string" || typeof f.latestValues.y == "string") && (f.isLayoutDirty = !0), f.updateScroll("snapshot"), f.options.layoutRoot && f.willUpdate(!1);
      }
      const { layoutId: a, layout: l } = this.options;
      if (a === void 0 && !l)
        return;
      const c = this.getTransformTemplate();
      this.prevTransformTemplateValue = c ? c(this.latestValues, "") : void 0, this.updateSnapshot(), s && this.notifyListeners("willUpdate");
    }
    update() {
      if (this.updateScheduled = !1, this.isUpdateBlocked()) {
        const l = this.updateBlockedByResize;
        this.unblockUpdate(), this.updateBlockedByResize = !1, this.clearAllSnapshots(), l && this.nodes.forEach(Pm), this.nodes.forEach(jo);
        return;
      }
      if (this.animationId <= this.animationCommitId) {
        this.nodes.forEach($o);
        return;
      }
      this.animationCommitId = this.animationId, this.isUpdating ? (this.isUpdating = !1, this.nodes.forEach(Mm), this.nodes.forEach(Em), this.nodes.forEach(Tm), this.nodes.forEach(Sm)) : this.nodes.forEach($o), this.clearAllSnapshots();
      const a = fe.now();
      ae.delta = Pe(0, 1e3 / 60, a - ae.timestamp), ae.timestamp = a, ae.isProcessing = !0, di.update.process(ae), di.preRender.process(ae), di.render.process(ae), ae.isProcessing = !1;
    }
    didUpdate() {
      this.updateScheduled || (this.updateScheduled = !0, fs.read(this.scheduleUpdate));
    }
    clearAllSnapshots() {
      this.nodes.forEach(Nm), this.sharedNodes.forEach(Vm);
    }
    scheduleUpdateProjection() {
      this.projectionUpdateScheduled || (this.projectionUpdateScheduled = !0, K.preRender(this.updateProjection, !1, !0));
    }
    scheduleCheckAfterUnmount() {
      K.postRender(() => {
        this.isLayoutDirty ? this.root.didUpdate() : this.root.checkUpdateFailed();
      });
    }
    /**
     * Update measurements
     */
    updateSnapshot() {
      this.snapshot || !this.instance || (this.snapshot = this.measure(), this.snapshot && !me(this.snapshot.measuredBox.x) && !me(this.snapshot.measuredBox.y) && (this.snapshot = void 0));
    }
    updateLayout() {
      if (!this.instance || (this.updateScroll(), !(this.options.alwaysMeasureLayout && this.isLead()) && !this.isLayoutDirty))
        return;
      if (this.resumeFrom && !this.resumeFrom.instance)
        for (let l = 0; l < this.path.length; l++)
          this.path[l].updateScroll();
      const s = this.layout;
      this.layout = this.measure(!1), this.layoutVersion++, this.layoutCorrected || (this.layoutCorrected = oe()), this.isLayoutDirty = !1, this.projectionDelta = void 0, this.notifyListeners("measure", this.layout.layoutBox);
      const { visualElement: a } = this.options;
      a && a.notify("LayoutMeasure", this.layout.layoutBox, s ? s.layoutBox : void 0);
    }
    updateScroll(s = "measure") {
      let a = !!(this.options.layoutScroll && this.instance);
      if (this.scroll && this.scroll.animationId === this.root.animationId && this.scroll.phase === s && (a = !1), a && this.instance) {
        const l = i(this.instance);
        this.scroll = {
          animationId: this.root.animationId,
          phase: s,
          isRoot: l,
          offset: n(this.instance),
          wasRoot: this.scroll ? this.scroll.isRoot : l
        };
      }
    }
    resetTransform() {
      if (!r)
        return;
      const s = this.isLayoutDirty || this.shouldResetTransform || this.options.alwaysMeasureLayout, a = this.projectionDelta && !Cc(this.projectionDelta), l = this.getTransformTemplate(), c = l ? l(this.latestValues, "") : void 0, u = c !== this.prevTransformTemplateValue;
      s && this.instance && (a || Je(this.latestValues) || u) && (r(this.instance, c), this.shouldResetTransform = !1, this.scheduleRender());
    }
    measure(s = !0) {
      const a = this.measurePageBox();
      let l = this.removeElementScroll(a);
      return s && (l = this.removeTransform(l)), Bm(l), {
        animationId: this.root.animationId,
        measuredBox: a,
        layoutBox: l,
        latestValues: {},
        source: this.id
      };
    }
    measurePageBox() {
      const { visualElement: s } = this.options;
      if (!s)
        return oe();
      const a = s.measureViewportBox();
      if (!(this.scroll?.wasRoot || this.path.some(jm))) {
        const { scroll: c } = this.root;
        c && (Re(a.x, c.offset.x), Re(a.y, c.offset.y));
      }
      return a;
    }
    removeElementScroll(s) {
      const a = oe();
      if (Ae(a, s), this.scroll?.wasRoot)
        return a;
      for (let l = 0; l < this.path.length; l++) {
        const c = this.path[l], { scroll: u, options: f } = c;
        c !== this.root && u && f.layoutScroll && (u.wasRoot && Ae(a, s), Re(a.x, u.offset.x), Re(a.y, u.offset.y));
      }
      return a;
    }
    applyTransform(s, a = !1, l) {
      const c = l || oe();
      Ae(c, s);
      for (let u = 0; u < this.path.length; u++) {
        const f = this.path[u];
        !a && f.options.layoutScroll && f.scroll && f !== f.root && (Re(c.x, -f.scroll.offset.x), Re(c.y, -f.scroll.offset.y)), Je(f.latestValues) && Cn(c, f.latestValues, f.layout?.layoutBox);
      }
      return Je(this.latestValues) && Cn(c, this.latestValues, this.layout?.layoutBox), c;
    }
    removeTransform(s) {
      const a = oe();
      Ae(a, s);
      for (let l = 0; l < this.path.length; l++) {
        const c = this.path[l];
        if (!Je(c.latestValues))
          continue;
        let u;
        c.instance && (lr(c.latestValues) && c.updateSnapshot(), u = oe(), Ae(u, c.measurePageBox())), Eo(a, c.latestValues, c.snapshot?.layoutBox, u);
      }
      return Je(this.latestValues) && Eo(a, this.latestValues), a;
    }
    setTargetDelta(s) {
      this.targetDelta = s, this.root.scheduleUpdateProjection(), this.isProjectionDirty = !0;
    }
    setOptions(s) {
      this.options = {
        ...this.options,
        ...s,
        crossfade: s.crossfade !== void 0 ? s.crossfade : !0
      };
    }
    clearMeasurements() {
      this.scroll = void 0, this.layout = void 0, this.snapshot = void 0, this.prevTransformTemplateValue = void 0, this.targetDelta = void 0, this.target = void 0, this.isLayoutDirty = !1;
    }
    forceRelativeParentToResolveTarget() {
      this.relativeParent && this.relativeParent.resolvedRelativeTargetAt !== ae.timestamp && this.relativeParent.resolveTargetDelta(!0);
    }
    resolveTargetDelta(s = !1) {
      const a = this.getLead();
      this.isProjectionDirty || (this.isProjectionDirty = a.isProjectionDirty), this.isTransformDirty || (this.isTransformDirty = a.isTransformDirty), this.isSharedProjectionDirty || (this.isSharedProjectionDirty = a.isSharedProjectionDirty);
      const l = !!this.resumingFrom || this !== a;
      if (!(s || l && this.isSharedProjectionDirty || this.isProjectionDirty || this.parent?.isProjectionDirty || this.attemptToResolveRelativeTarget || this.root.updateBlockedByResize))
        return;
      const { layout: u, layoutId: f } = this.options;
      if (!this.layout || !(u || f))
        return;
      this.resolvedRelativeTargetAt = ae.timestamp;
      const h = this.getClosestProjectingParent();
      h && this.linkedParentVersion !== h.layoutVersion && !h.options.layoutRoot && this.removeRelativeTarget(), !this.targetDelta && !this.relativeTarget && (this.options.layoutAnchor !== !1 && h && h.layout ? this.createRelativeTarget(h, this.layout.layoutBox, h.layout.layoutBox) : this.removeRelativeTarget()), !(!this.relativeTarget && !this.targetDelta) && (this.target || (this.target = oe(), this.targetWithTransforms = oe()), this.relativeTarget && this.relativeTargetOrigin && this.relativeParent && this.relativeParent.target ? (this.forceRelativeParentToResolveTarget(), am(this.target, this.relativeTarget, this.relativeParent.target, this.options.layoutAnchor || void 0)) : this.targetDelta ? (this.resumingFrom ? this.applyTransform(this.layout.layoutBox, !1, this.target) : Ae(this.target, this.layout.layoutBox), ac(this.target, this.targetDelta)) : Ae(this.target, this.layout.layoutBox), this.attemptToResolveRelativeTarget && (this.attemptToResolveRelativeTarget = !1, this.options.layoutAnchor !== !1 && h && !!h.resumingFrom == !!this.resumingFrom && !h.options.layoutScroll && h.target && this.animationProgress !== 1 ? this.createRelativeTarget(h, this.target, h.target) : this.relativeParent = this.relativeTarget = void 0));
    }
    getClosestProjectingParent() {
      if (!(!this.parent || lr(this.parent.latestValues) || oc(this.parent.latestValues)))
        return this.parent.isProjecting() ? this.parent : this.parent.getClosestProjectingParent();
    }
    isProjecting() {
      return !!((this.relativeTarget || this.targetDelta || this.options.layoutRoot) && this.layout);
    }
    createRelativeTarget(s, a, l) {
      this.relativeParent = s, this.linkedParentVersion = s.layoutVersion, this.forceRelativeParentToResolveTarget(), this.relativeTarget = oe(), this.relativeTargetOrigin = oe(), Hn(this.relativeTargetOrigin, a, l, this.options.layoutAnchor || void 0), Ae(this.relativeTarget, this.relativeTargetOrigin);
    }
    removeRelativeTarget() {
      this.relativeParent = this.relativeTarget = void 0;
    }
    calcProjection() {
      const s = this.getLead(), a = !!this.resumingFrom || this !== s;
      let l = !0;
      if ((this.isProjectionDirty || this.parent?.isProjectionDirty) && (l = !1), a && (this.isSharedProjectionDirty || this.isTransformDirty) && (l = !1), this.resolvedRelativeTargetAt === ae.timestamp && (l = !1), l)
        return;
      const { layout: c, layoutId: u } = this.options;
      if (this.isTreeAnimating = !!(this.parent && this.parent.isTreeAnimating || this.currentAnimation || this.pendingAnimation), this.isTreeAnimating || (this.targetDelta = this.relativeTarget = void 0), !this.layout || !(c || u))
        return;
      Ae(this.layoutCorrected, this.layout.layoutBox);
      const f = this.treeScale.x, h = this.treeScale.y;
      mp(this.layoutCorrected, this.treeScale, this.path, a), s.layout && !s.target && (this.treeScale.x !== 1 || this.treeScale.y !== 1) && (s.target = s.layout.layoutBox, s.targetWithTransforms = oe());
      const { target: m } = s;
      if (!m) {
        this.prevProjectionDelta && (this.createProjectionDeltas(), this.scheduleRender());
        return;
      }
      !this.projectionDelta || !this.prevProjectionDelta ? this.createProjectionDeltas() : (So(this.prevProjectionDelta.x, this.projectionDelta.x), So(this.prevProjectionDelta.y, this.projectionDelta.y)), zt(this.projectionDelta, this.layoutCorrected, m, this.latestValues), (this.treeScale.x !== f || this.treeScale.y !== h || !Fo(this.projectionDelta.x, this.prevProjectionDelta.x) || !Fo(this.projectionDelta.y, this.prevProjectionDelta.y)) && (this.hasProjected = !0, this.scheduleRender(), this.notifyListeners("projectionUpdate", m));
    }
    hide() {
      this.isVisible = !1;
    }
    show() {
      this.isVisible = !0;
    }
    scheduleRender(s = !0) {
      if (this.options.visualElement?.scheduleRender(), s) {
        const a = this.getStack();
        a && a.scheduleRender();
      }
      this.resumingFrom && !this.resumingFrom.instance && (this.resumingFrom = void 0);
    }
    createProjectionDeltas() {
      this.prevProjectionDelta = bt(), this.projectionDelta = bt(), this.projectionDeltaWithTransform = bt();
    }
    setAnimationOrigin(s, a = !1, l) {
      const c = this.snapshot, u = c ? c.latestValues : {}, f = { ...this.latestValues }, h = bt();
      (!this.relativeParent || !this.relativeParent.options.layoutRoot) && (this.relativeTarget = this.relativeTargetOrigin = void 0), this.attemptToResolveRelativeTarget = !a;
      const m = oe(), p = c ? c.source : void 0, g = this.layout ? this.layout.source : void 0, y = p !== g, b = this.getStack(), k = !b || b.members.length <= 1, x = !!(y && !k && this.options.crossfade === !0 && !this.path.some(Im));
      this.animationProgress = 0;
      let S;
      const E = l?.interpolateProjection(s);
      this.mixTargetDelta = (C) => {
        const A = C / 1e3, N = E?.(A);
        N ? (h.x.translate = N.x, h.x.scale = Y(s.x.scale, 1, A), h.x.origin = s.x.origin, h.x.originPoint = s.x.originPoint, h.y.translate = N.y, h.y.scale = Y(s.y.scale, 1, A), h.y.origin = s.y.origin, h.y.originPoint = s.y.originPoint) : (_o(h.x, s.x, A), _o(h.y, s.y, A)), this.setTargetDelta(h), this.relativeTarget && this.relativeTargetOrigin && this.layout && this.relativeParent && this.relativeParent.layout && (Hn(m, this.layout.layoutBox, this.relativeParent.layout.layoutBox, this.options.layoutAnchor || void 0), Fm(this.relativeTarget, this.relativeTargetOrigin, m, A), S && fm(this.relativeTarget, S) && (this.isProjectionDirty = !1), S || (S = oe()), Ae(S, this.relativeTarget)), y && (this.animationValues = f, pm(f, u, this.latestValues, A, x, k)), N && N.rotate !== void 0 && (this.animationValues || (this.animationValues = f), this.animationValues.pathRotation = N.rotate), this.root.scheduleUpdateProjection(), this.scheduleRender(), this.animationProgress = A;
      }, this.mixTargetDelta(this.options.layoutRoot ? 1e3 : 0);
    }
    startAnimation(s) {
      this.notifyListeners("animationStart"), this.currentAnimation?.stop(), this.resumingFrom?.currentAnimation?.stop(), this.pendingAnimation && ($e(this.pendingAnimation), this.pendingAnimation = void 0), this.pendingAnimation = K.update(() => {
        Rn.hasAnimatedSinceResize = !0, this.motionValue || (this.motionValue = ze(0)), this.motionValue.jump(0, !1), this.currentAnimation = Mc(this.motionValue, [0, 1e3], {
          ...s,
          velocity: 0,
          isSync: !0,
          onUpdate: (a) => {
            this.mixTargetDelta(a), s.onUpdate && s.onUpdate(a);
          },
          onComplete: () => {
            s.onComplete && s.onComplete(), this.completeAnimation();
          }
        }), zd(this.currentAnimation, this), this.resumingFrom && (this.resumingFrom.currentAnimation = this.currentAnimation), this.pendingAnimation = void 0;
      });
    }
    completeAnimation() {
      this.resumingFrom && (this.resumingFrom.currentAnimation = void 0, this.resumingFrom.preserveOpacity = void 0);
      const s = this.getStack();
      s && s.exitAnimationComplete(), this.resumingFrom = this.currentAnimation = this.animationValues = void 0, this.notifyListeners("animationComplete");
    }
    finishAnimation() {
      this.currentAnimation && (this.mixTargetDelta && this.mixTargetDelta(wm), this.currentAnimation.stop()), this.completeAnimation();
    }
    applyTransformsToTarget() {
      const s = this.getLead(), { targetWithTransforms: a, layout: l, latestValues: c } = s;
      let { target: u } = s;
      if (!(!a || !u || !l)) {
        if (this !== s && this.layout && l && Rc(this.options.animationType, this.layout.layoutBox, l.layoutBox)) {
          u = this.target || oe();
          const f = me(this.layout.layoutBox.x);
          u.x.min = s.target.x.min, u.x.max = u.x.min + f;
          const h = me(this.layout.layoutBox.y);
          u.y.min = s.target.y.min, u.y.max = u.y.min + h;
        }
        Ae(a, u), Cn(a, c), zt(this.projectionDeltaWithTransform, this.layoutCorrected, a, c);
      }
    }
    registerSharedNode(s, a) {
      this.sharedNodes.has(s) || this.sharedNodes.set(s, new vm()), this.sharedNodes.get(s).add(a);
      const c = a.options.initialPromotionConfig;
      a.promote({
        transition: c ? c.transition : void 0,
        preserveFollowOpacity: c && c.shouldPreserveFollowOpacity ? c.shouldPreserveFollowOpacity(a) : void 0
      });
    }
    isLead() {
      const s = this.getStack();
      return s ? s.lead === this : !0;
    }
    getLead() {
      const { layoutId: s } = this.options;
      return s ? this.getStack()?.lead || this : this;
    }
    getPrevLead() {
      const { layoutId: s } = this.options;
      return s ? this.getStack()?.prevLead : void 0;
    }
    getStack() {
      const { layoutId: s } = this.options;
      if (s)
        return this.root.sharedNodes.get(s);
    }
    promote({ needsReset: s, transition: a, preserveFollowOpacity: l } = {}) {
      const c = this.getStack();
      c && c.promote(this, l), s && (this.projectionDelta = void 0, this.needsReset = !0), a && this.setOptions({ transition: a });
    }
    relegate() {
      const s = this.getStack();
      return s ? s.relegate(this) : !1;
    }
    resetSkewAndRotation() {
      const { visualElement: s } = this.options;
      if (!s)
        return;
      let a = !1;
      const { latestValues: l } = s;
      if ((l.z || l.rotate || l.rotateX || l.rotateY || l.rotateZ || l.skewX || l.skewY) && (a = !0), !a)
        return;
      const c = {};
      l.z && ki("z", s, c, this.animationValues);
      for (let u = 0; u < wi.length; u++)
        ki(`rotate${wi[u]}`, s, c, this.animationValues), ki(`skew${wi[u]}`, s, c, this.animationValues);
      s.render();
      for (const u in c)
        s.setStaticValue(u, c[u]), this.animationValues && (this.animationValues[u] = c[u]);
      s.scheduleRender();
    }
    applyProjectionStyles(s, a) {
      if (!this.instance || this.isSVG)
        return;
      if (!this.isVisible) {
        s.visibility = "hidden";
        return;
      }
      const l = this.getTransformTemplate();
      if (this.needsReset) {
        this.needsReset = !1, s.visibility = "", s.opacity = "", s.pointerEvents = Dn(a?.pointerEvents) || "", s.transform = l ? l(this.latestValues, "") : "none";
        return;
      }
      const c = this.getLead();
      if (!this.projectionDelta || !this.layout || !c.target) {
        this.options.layoutId && (s.opacity = this.latestValues.opacity !== void 0 ? this.latestValues.opacity : 1, s.pointerEvents = Dn(a?.pointerEvents) || ""), this.hasProjected && !Je(this.latestValues) && (s.transform = l ? l({}, "") : "none", this.hasProjected = !1);
        return;
      }
      s.visibility = "";
      const u = c.animationValues || c.latestValues;
      this.applyTransformsToTarget();
      let f = dm(this.projectionDeltaWithTransform, this.treeScale, u);
      l && (f = l(u, f)), s.transform = f;
      const { x: h, y: m } = this.projectionDelta;
      s.transformOrigin = `${h.origin * 100}% ${m.origin * 100}% 0`, c.animationValues ? s.opacity = c === this ? u.opacity ?? this.latestValues.opacity ?? 1 : this.preserveOpacity ? this.latestValues.opacity : u.opacityExit : s.opacity = c === this ? u.opacity !== void 0 ? u.opacity : "" : u.opacityExit !== void 0 ? u.opacityExit : 0;
      for (const p in ur) {
        if (u[p] === void 0)
          continue;
        const { correct: g, applyTo: y, isCSSVariable: b } = ur[p], k = f === "none" ? u[p] : g(u[p], c);
        if (y) {
          const x = y.length;
          for (let S = 0; S < x; S++)
            s[y[S]] = k;
        } else
          b ? this.options.visualElement.renderState.vars[p] = k : s[p] = k;
      }
      this.options.layoutId && (s.pointerEvents = c === this ? Dn(a?.pointerEvents) || "" : "none");
    }
    clearSnapshot() {
      this.resumeFrom = this.snapshot = void 0;
    }
    // Only run on root
    resetTree() {
      this.root.nodes.forEach((s) => s.currentAnimation?.stop()), this.root.nodes.forEach(jo), this.root.sharedNodes.clear();
    }
  };
}
function Tm(e) {
  e.updateLayout();
}
function Sm(e) {
  const t = e.resumeFrom?.snapshot || e.snapshot;
  if (e.isLead() && e.layout && t && e.hasListeners("didUpdate")) {
    const { layoutBox: n, measuredBox: i } = e.layout, { animationType: r } = e.options, o = t.source !== e.layout.source;
    if (r === "size")
      De((u) => {
        const f = o ? t.measuredBox[u] : t.layoutBox[u], h = me(f);
        f.min = n[u].min, f.max = f.min + h;
      });
    else if (r === "x" || r === "y") {
      const u = r === "x" ? "y" : "x";
      fr(o ? t.measuredBox[u] : t.layoutBox[u], n[u]);
    } else Rc(r, t.layoutBox, n) && De((u) => {
      const f = o ? t.measuredBox[u] : t.layoutBox[u], h = me(n[u]);
      f.max = f.min + h, e.relativeTarget && !e.currentAnimation && (e.isProjectionDirty = !0, e.relativeTarget[u].max = e.relativeTarget[u].min + h);
    });
    const s = bt();
    zt(s, n, t.layoutBox);
    const a = bt();
    o ? zt(a, e.applyTransform(i, !0), t.measuredBox) : zt(a, n, t.layoutBox);
    const l = !Cc(s);
    let c = !1;
    if (!e.resumeFrom) {
      const u = e.getClosestProjectingParent();
      if (u && !u.resumeFrom) {
        const { snapshot: f, layout: h } = u;
        if (f && h) {
          const m = e.options.layoutAnchor || void 0, p = oe();
          Hn(p, t.layoutBox, f.layoutBox, m);
          const g = oe();
          Hn(g, n, h.layoutBox, m), Nc(p, g) || (c = !0), u.options.layoutRoot && (e.relativeTarget = g, e.relativeTargetOrigin = p, e.relativeParent = u);
        }
      }
    }
    e.notifyListeners("didUpdate", {
      layout: n,
      snapshot: t,
      delta: a,
      layoutDelta: s,
      hasLayoutChanged: l,
      hasRelativeLayoutChanged: c
    });
  } else if (e.isLead()) {
    const { onExitComplete: n } = e.options;
    n && n();
  }
  e.options.transition = void 0;
}
function Am(e) {
  e.parent && (e.isProjecting() || (e.isProjectionDirty = e.parent.isProjectionDirty), e.isSharedProjectionDirty || (e.isSharedProjectionDirty = !!(e.isProjectionDirty || e.parent.isProjectionDirty || e.parent.isSharedProjectionDirty)), e.isTransformDirty || (e.isTransformDirty = e.parent.isTransformDirty));
}
function Cm(e) {
  e.isProjectionDirty = e.isSharedProjectionDirty = e.isTransformDirty = !1;
}
function Nm(e) {
  e.clearSnapshot();
}
function jo(e) {
  e.clearMeasurements();
}
function Pm(e) {
  e.isLayoutDirty = !0, e.updateLayout();
}
function $o(e) {
  e.isLayoutDirty = !1;
}
function Mm(e) {
  e.isAnimationBlocked && e.layout && !e.isLayoutDirty && (e.snapshot = e.layout, e.isLayoutDirty = !0);
}
function Em(e) {
  const { visualElement: t } = e.options;
  t && t.getProps().onBeforeLayoutMeasure && t.notify("BeforeLayoutMeasure"), e.resetTransform();
}
function zo(e) {
  e.finishAnimation(), e.targetDelta = e.relativeTarget = e.target = void 0, e.isProjectionDirty = !0;
}
function Dm(e) {
  e.resolveTargetDelta();
}
function Rm(e) {
  e.calcProjection();
}
function Lm(e) {
  e.resetSkewAndRotation();
}
function Vm(e) {
  e.removeLeadSnapshot();
}
function _o(e, t, n) {
  e.translate = Y(t.translate, 0, n), e.scale = Y(t.scale, 1, n), e.origin = t.origin, e.originPoint = t.originPoint;
}
function Uo(e, t, n, i) {
  e.min = Y(t.min, n.min, i), e.max = Y(t.max, n.max, i);
}
function Fm(e, t, n, i) {
  Uo(e.x, t.x, n.x, i), Uo(e.y, t.y, n.y, i);
}
function Im(e) {
  return e.animationValues && e.animationValues.opacityExit !== void 0;
}
const Om = {
  duration: 0.45,
  ease: [0.4, 0, 0.1, 1]
}, Wo = (e) => typeof navigator < "u" && navigator.userAgent && navigator.userAgent.toLowerCase().includes(e), Ho = Wo("applewebkit/") && !Wo("chrome/") ? Math.round : Ne;
function Go(e) {
  e.min = Ho(e.min), e.max = Ho(e.max);
}
function Bm(e) {
  Go(e.x), Go(e.y);
}
function Rc(e, t, n) {
  return e === "position" || e === "preserve-aspect" && !om(Vo(t), Vo(n), 0.2);
}
function jm(e) {
  return e !== e.root && e.scroll?.wasRoot;
}
const $m = Dc({
  attachResizeListener: (e, t) => Qt(e, "resize", t),
  measureScroll: () => ({
    x: document.documentElement.scrollLeft || document.body?.scrollLeft || 0,
    y: document.documentElement.scrollTop || document.body?.scrollTop || 0
  }),
  checkIsScrollRoot: () => !0
}), Ti = {
  current: void 0
}, Lc = Dc({
  measureScroll: (e) => ({
    x: e.scrollLeft,
    y: e.scrollTop
  }),
  defaultParent: () => {
    if (!Ti.current) {
      const e = new $m({});
      e.mount(window), e.setOptions({ layoutScroll: !0 }), Ti.current = e;
    }
    return Ti.current;
  },
  resetTransform: (e, t) => {
    e.style.transform = t !== void 0 ? t : "none";
  },
  checkIsScrollRoot: (e) => window.getComputedStyle(e).position === "fixed"
}), ii = Ct({
  transformPagePoint: (e) => e,
  isStatic: !1,
  reducedMotion: "never"
});
function Ko(e, t) {
  if (typeof e == "function")
    return e(t);
  e != null && (e.current = t);
}
function zm(...e) {
  return (t) => {
    let n = !1;
    const i = e.map((r) => {
      const o = Ko(r, t);
      return !n && typeof o == "function" && (n = !0), o;
    });
    if (n)
      return () => {
        for (let r = 0; r < i.length; r++) {
          const o = i[r];
          typeof o == "function" ? o() : Ko(e[r], null);
        }
      };
  };
}
function _m(...e) {
  return Qn.useCallback(zm(...e), e);
}
class Um extends Qn.Component {
  getSnapshotBeforeUpdate(t) {
    const n = this.props.childRef.current;
    if (Tt(n) && t.isPresent && !this.props.isPresent && this.props.pop !== !1) {
      const i = n.offsetParent, r = Tt(i) && i.offsetWidth || 0, o = Tt(i) && i.offsetHeight || 0, s = getComputedStyle(n), a = this.props.sizeRef.current;
      a.height = parseFloat(s.height), a.width = parseFloat(s.width), a.top = n.offsetTop, a.left = n.offsetLeft, a.right = r - a.width - a.left, a.bottom = o - a.height - a.top, a.direction = s.direction;
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
function Wm({ children: e, isPresent: t, anchorX: n, anchorY: i, root: r, pop: o }) {
  const s = Se(), a = D(null), l = D({
    width: 0,
    height: 0,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    direction: "ltr"
  }), { nonce: c } = ue(ii), u = o !== !1 ? e.props?.ref ?? e?.ref : void 0, f = _m(a, u);
  return wr(() => {
    const { width: h, height: m, top: p, left: g, right: y, bottom: b, direction: k } = l.current;
    if (t || o === !1 || !a.current || !h || !m)
      return;
    const x = k === "rtl", S = n === "left" ? x ? `right: ${y}` : `left: ${g}` : x ? `left: ${g}` : `right: ${y}`, E = i === "bottom" ? `bottom: ${b}` : `top: ${p}`;
    a.current.dataset.motionPopId = s;
    const C = document.createElement("style");
    c && (C.nonce = c);
    const A = r ?? document.head;
    return A.appendChild(C), C.sheet && C.sheet.insertRule(`
          [data-motion-pop-id="${s}"] {
            position: absolute !important;
            width: ${h}px !important;
            height: ${m}px !important;
            ${S}px !important;
            ${E}px !important;
          }
        `), () => {
      a.current?.removeAttribute("data-motion-pop-id"), A.contains(C) && A.removeChild(C);
    };
  }, [t]), d(Um, { isPresent: t, childRef: a, sizeRef: l, pop: o, children: o === !1 ? e : Qn.cloneElement(e, { ref: f }) });
}
const Hm = ({ children: e, initial: t, isPresent: n, onExitComplete: i, custom: r, presenceAffectsLayout: o, mode: s, anchorX: a, anchorY: l, root: c }) => {
  const u = tn(Gm), f = Se(), h = D(n), m = D(i);
  Gt(() => {
    h.current = n, m.current = i;
  });
  let p = !0, g = de(() => (p = !1, {
    id: f,
    initial: t,
    isPresent: n,
    custom: r,
    onExitComplete: (y) => {
      u.set(y, !0);
      for (const b of u.values())
        if (!b)
          return;
      i && i();
    },
    register: (y) => (u.set(y, !1), () => {
      u.delete(y), !h.current && !u.size && m.current?.();
    })
  }), [n, u, i]);
  return o && p && (g = { ...g }), de(() => {
    u.forEach((y, b) => u.set(b, !1));
  }, [n]), Qn.useEffect(() => {
    !n && !u.size && i && i();
  }, [n]), e = d(Wm, { pop: s === "popLayout", isPresent: n, anchorX: a, anchorY: l, root: c, children: e }), d(nn.Provider, { value: g, children: e });
};
function Gm() {
  return /* @__PURE__ */ new Map();
}
function Vc(e = !0) {
  const t = ue(nn);
  if (t === null)
    return [!0, null];
  const { isPresent: n, onExitComplete: i, register: r } = t, o = Se();
  O(() => {
    if (e)
      return r(o);
  }, [e]);
  const s = Q(() => e && i && i(o), [o, i, e]);
  return !n && i ? [!1, s] : [!0];
}
function Km() {
  return qm(ue(nn));
}
function qm(e) {
  return e === null ? !0 : e.isPresent;
}
const gn = (e) => e.key || "";
function qo(e) {
  const t = [];
  return Ju.forEach(e, (n) => {
    ef(n) && t.push(n);
  }), t;
}
const ge = ({ children: e, custom: t, initial: n = !0, onExitComplete: i, presenceAffectsLayout: r = !0, mode: o = "sync", propagate: s = !1, anchorX: a = "left", anchorY: l = "top", root: c }) => {
  const [u, f] = Vc(s), h = de(() => qo(e), [e]), m = s && !u ? [] : h.map(gn), p = D(!0), g = D(h), y = tn(() => /* @__PURE__ */ new Map()), b = D(/* @__PURE__ */ new Set()), [k, x] = B(h), [S, E] = B(h);
  Gt(() => {
    s && !u && !S.length && f?.();
  }, [u, s, S.length, f]), Gt(() => {
    p.current = !1, g.current = h;
    for (let N = 0; N < S.length; N++) {
      const P = gn(S[N]);
      m.includes(P) ? (y.delete(P), b.current.delete(P)) : y.get(P) !== !0 && y.set(P, !1);
    }
  }, [S, m.length, m.join("-")]);
  const C = [];
  if (h !== k) {
    let N = [...h], P = 0;
    for (const w of S) {
      const T = m.indexOf(gn(w));
      T === -1 ? (N.splice(P++, 0, w), C.push(w)) : P = T + C.length + 1;
    }
    return o === "wait" && C.length && (N = C), E(qo(N)), x(h), null;
  }
  process.env.NODE_ENV !== "production" && o === "wait" && S.length > 1 && console.warn(`You're attempting to animate multiple children within AnimatePresence, but its mode is set to "wait". This will lead to odd visual behaviour.`);
  const { forceRender: A } = ue(Vr);
  return d(U, { children: S.map((N) => {
    const P = gn(N), w = s && !u ? !1 : h === S || m.includes(P), T = () => {
      if (b.current.has(P))
        return;
      if (y.has(P))
        b.current.add(P), y.set(P, !0);
      else
        return;
      let I = !0;
      y.forEach((F) => {
        F || (I = !1);
      }), I && (A?.(), E(g.current), s && f?.(), i && i());
    };
    return d(Hm, { isPresent: w, initial: !p.current || n ? void 0 : !1, custom: t, presenceAffectsLayout: r, mode: o, root: c, onExitComplete: w ? void 0 : T, anchorX: a, anchorY: l, children: N }, P);
  }) });
}, Fc = Ct({ strict: !1 }), Yo = {
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
let Xo = !1;
function Ym() {
  if (Xo)
    return;
  const e = {};
  for (const t in Yo)
    e[t] = {
      isEnabled: (n) => Yo[t].some((i) => !!n[i])
    };
  mc(e), Xo = !0;
}
function Ic() {
  return Ym(), Up();
}
function Xm(e) {
  const t = Ic();
  for (const n in e)
    t[n] = {
      ...t[n],
      ...e[n]
    };
  mc(t);
}
const ri = /* @__PURE__ */ Ct({});
function Qm(e, t) {
  if (ni(e)) {
    const { initial: n, animate: i } = e;
    return {
      initial: n === !1 || Xt(n) ? n : void 0,
      animate: Xt(i) ? i : void 0
    };
  }
  return e.inherit !== !1 ? t : {};
}
function Zm(e) {
  const { initial: t, animate: n } = Qm(e, ue(ri));
  return de(() => ({ initial: t, animate: n }), [Qo(t), Qo(n)]);
}
function Qo(e) {
  return Array.isArray(e) ? e.join(" ") : e;
}
const gs = () => ({
  style: {},
  transform: {},
  transformOrigin: {},
  vars: {}
});
function Oc(e, t, n) {
  for (const i in t)
    !ce(t[i]) && !xc(i, n) && (e[i] = t[i]);
}
function Jm({ transformTemplate: e }, t) {
  return de(() => {
    const n = gs();
    return ls(n, t, e), Object.assign({}, n.vars, n.style);
  }, [t]);
}
function eg(e, t) {
  const n = e.style || {}, i = {};
  return Oc(i, n, e), Object.assign(i, Jm(e, t)), i;
}
function tg(e, t) {
  const n = {}, i = eg(e, t);
  return e.drag && e.dragListener !== !1 && (n.draggable = !1, i.userSelect = i.WebkitUserSelect = i.WebkitTouchCallout = "none", i.touchAction = e.drag === !0 ? "none" : `pan-${e.drag === "x" ? "y" : "x"}`), e.tabIndex === void 0 && (e.onTap || e.onTapStart || e.whileTap) && (n.tabIndex = 0), n.style = i, n;
}
const Bc = () => ({
  ...gs(),
  attrs: {}
});
function ng(e, t, n, i) {
  const r = de(() => {
    const o = Bc();
    return ic(o, t, vc(i), e.transformTemplate, e.style), {
      ...o.attrs,
      style: { ...o.style }
    };
  }, [t]);
  if (e.style) {
    const o = {};
    Oc(o, e.style, e), r.style = { ...o, ...r.style };
  }
  return r;
}
const ig = /* @__PURE__ */ new Set([
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
function Gn(e) {
  return e.startsWith("while") || e.startsWith("drag") && e !== "draggable" || e.startsWith("layout") || e.startsWith("onTap") || e.startsWith("onPan") || e.startsWith("onLayout") || ig.has(e);
}
function rg(e, t) {
  return e.startsWith("on") ? !Gn(e) : t?.(e) ?? !Gn(e);
}
function sg(e, t, n, i) {
  const r = {};
  for (const o in e)
    o === "values" && typeof e.values == "object" || ce(e[o]) || (rg(o, i) || n === !0 && Gn(o) || !t && !Gn(o) || // If trying to use native HTML drag events, forward drag listeners
    e.draggable && o.startsWith("onDrag")) && (r[o] = e[o]);
  return r;
}
const og = [
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
function ys(e) {
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
      !!(og.indexOf(e) > -1 || /**
       * If it contains a capital letter, it's an SVG component
       */
      /[A-Z]/u.test(e))
    )
  );
}
function ag(e, t, n, { latestValues: i }, r, o = !1, s, a) {
  const c = (s ?? ys(e) ? ng : tg)(t, i, r, e), u = sg(t, typeof e == "string", o, a), f = e !== kr ? { ...u, ...c, ref: n } : {}, { children: h } = t, m = de(() => ce(h) ? h.get() : h, [h]);
  return tf(e, {
    ...f,
    children: m
  });
}
function lg({ scrapeMotionValuesFromProps: e, createRenderState: t }, n, i, r) {
  return {
    latestValues: cg(n, i, r, e),
    renderState: t()
  };
}
function cg(e, t, n, i) {
  const r = {}, o = i(e, {});
  for (const h in o)
    r[h] = Dn(o[h]);
  let { initial: s, animate: a } = e;
  const l = ni(e), c = hc(e);
  t && c && !l && e.inherit !== !1 && (s === void 0 && (s = t.initial), a === void 0 && (a = t.animate));
  let u = n ? n.initial === !1 : !1;
  u = u || s === !1;
  const f = u ? a : s;
  if (f && typeof f != "boolean" && !ti(f)) {
    const h = Array.isArray(f) ? f : [f];
    for (let m = 0; m < h.length; m++) {
      const p = ts(e, h[m]);
      if (p) {
        const { transitionEnd: g, transition: y, ...b } = p;
        for (const k in b) {
          let x = b[k];
          if (Array.isArray(x)) {
            const S = u ? x.length - 1 : 0;
            x = x[S];
          }
          x !== null && (r[k] = x);
        }
        for (const k in g)
          r[k] = g[k];
      }
    }
  }
  return r;
}
const jc = (e) => (t, n) => {
  const i = ue(ri), r = ue(nn), o = () => lg(e, t, i, r);
  return n ? o() : tn(o);
}, ug = /* @__PURE__ */ jc({
  scrapeMotionValuesFromProps: ms,
  createRenderState: gs
}), fg = /* @__PURE__ */ jc({
  scrapeMotionValuesFromProps: wc,
  createRenderState: Bc
}), dg = /* @__PURE__ */ Symbol.for("motionComponentSymbol");
function hg(e, t, n) {
  const i = D(n);
  wr(() => {
    i.current = n;
  });
  const r = D(null);
  return Q((o) => {
    o && e.onMount?.(o), t && (o ? t.mount(o) : t.unmount());
    const s = i.current;
    if (typeof s == "function")
      if (o) {
        const a = s(o);
        typeof a == "function" && (r.current = a);
      } else r.current ? (r.current(), r.current = null) : s(o);
    else s && (s.current = o);
  }, [t]);
}
const $c = Ct({});
function dt(e) {
  return e && typeof e == "object" && Object.prototype.hasOwnProperty.call(e, "current");
}
function pg(e, t, n, i, r, o) {
  const { visualElement: s } = ue(ri), a = ue(Fc), l = ue(nn), c = ue(ii), u = c.reducedMotion, f = c.skipAnimations, h = D(null), m = D(!1);
  i = i || a.renderer, !h.current && i && (h.current = i(e, {
    visualState: t,
    parent: s,
    props: n,
    presenceContext: l,
    blockInitialAnimation: l ? l.initial === !1 : !1,
    reducedMotionConfig: u,
    skipAnimations: f,
    isSVG: o
  }), m.current && h.current && (h.current.manuallyAnimateOnMount = !0));
  const p = h.current, g = ue($c);
  p && !p.projection && r && (p.type === "html" || p.type === "svg") && mg(h.current, n, r, g);
  const y = D(!1);
  wr(() => {
    p && y.current && p.update(n, l);
  });
  const b = n[Yl], k = D(!!b && typeof window < "u" && !window.MotionHandoffIsComplete?.(b) && window.MotionHasOptimisedAnimation?.(b));
  return Gt(() => {
    m.current = !0, p && (y.current = !0, window.MotionIsMounted = !0, p.updateFeatures(), p.scheduleRenderMicrotask(), k.current && p.animationState && p.animationState.animateChanges());
  }), O(() => {
    p && (!k.current && p.animationState && p.animationState.animateChanges(), k.current && (queueMicrotask(() => {
      window.MotionHandoffMarkAsComplete?.(b);
    }), k.current = !1), p.enteringChildren = void 0);
  }), p;
}
function mg(e, t, n, i) {
  const { layoutId: r, layout: o, drag: s, dragConstraints: a, layoutScroll: l, layoutRoot: c, layoutAnchor: u, layoutCrossfade: f } = t;
  e.projection = new n(e.latestValues, t["data-framer-portal-id"] ? void 0 : zc(e.parent)), e.projection.setOptions({
    layoutId: r,
    layout: o,
    alwaysMeasureLayout: !!s || a && dt(a),
    visualElement: e,
    /**
     * TODO: Update options in an effect. This could be tricky as it'll be too late
     * to update by the time layout animations run.
     * We also need to fix this safeToRemove by linking it up to the one returned by usePresence,
     * ensuring it gets called if there's no potential layout animations.
     *
     */
    animationType: typeof o == "string" ? o : "both",
    initialPromotionConfig: i,
    crossfade: f,
    layoutScroll: l,
    layoutRoot: c,
    layoutAnchor: u
  });
}
function zc(e) {
  if (e)
    return e.options.allowProjection !== !1 ? e.projection : zc(e.parent);
}
function Si(e, { forwardMotionProps: t = !1, type: n } = {}, i, r) {
  i && Xm(i);
  const o = n ? n === "svg" : ys(e), s = o ? fg : ug;
  function a(c, u) {
    let f;
    const h = {
      ...ue(ii),
      ...c,
      layoutId: gg(c)
    }, { isStatic: m, isValidProp: p } = h, g = Zm(c), y = s(c, m);
    if (!m && typeof window < "u") {
      yg(h, i);
      const b = xg(h);
      f = b.MeasureLayout, g.visualElement = pg(e, y, h, r, b.ProjectionNode, o);
    }
    return v(ri.Provider, { value: g, children: [f && g.visualElement ? d(f, { visualElement: g.visualElement, ...h }) : null, ag(e, c, hg(y, g.visualElement, u), y, m, t, o, p)] });
  }
  a.displayName = `motion.${typeof e == "string" ? e : `create(${e.displayName ?? e.name ?? ""})`}`;
  const l = Tr(a);
  return l[dg] = e, l;
}
function gg({ layoutId: e }) {
  const t = ue(Vr).id;
  return t && e !== void 0 ? t + "-" + e : e;
}
function yg(e, t) {
  const n = ue(Fc).strict;
  if (process.env.NODE_ENV !== "production" && t && n) {
    const i = "You have rendered a `motion` component within a `LazyMotion` component. This will break tree shaking. Import and render a `m` component instead.";
    e.ignoreStrict ? ct(!1, i, "lazy-strict-mode") : Te(!1, i, "lazy-strict-mode");
  }
}
function xg(e) {
  const t = Ic(), { drag: n, layout: i } = t;
  if (!n && !i)
    return {};
  const r = { ...n, ...i };
  return {
    MeasureLayout: n?.isEnabled(e) || i?.isEnabled(e) ? r.MeasureLayout : void 0,
    ProjectionNode: r.ProjectionNode
  };
}
function bg(e, t) {
  if (typeof Proxy > "u")
    return Si;
  const n = /* @__PURE__ */ new Map(), i = (o, s) => Si(o, s, e, t), r = (o, s) => (process.env.NODE_ENV !== "production" && Zn(!1, "motion() is deprecated. Use motion.create() instead."), i(o, s));
  return new Proxy(r, {
    /**
     * Called when `motion` is referenced with a prop: `motion.div`, `motion.input` etc.
     * The prop name is passed through as `key` and we can use that to generate a `motion`
     * DOM component with that name.
     */
    get: (o, s) => s === "create" ? i : (n.has(s) || n.set(s, Si(s, void 0, e, t)), n.get(s))
  });
}
const vg = (e, t) => t.isSVG ?? ys(e) ? new Yp(t) : new Kp(t, {
  allowProjection: e !== kr
});
class wg extends Xe {
  /**
   * We dynamically generate the AnimationState manager as it contains a reference
   * to the underlying animation library. We only want to load that if we load this,
   * so people can optionally code split it out using the `m` component.
   */
  constructor(t) {
    super(t), t.animationState || (t.animationState = em(t));
  }
  updateAnimationControlsSubscription() {
    const { animate: t } = this.node.getProps();
    ti(t) && (this.unmountControls = t.subscribe(this.node));
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
let kg = 0;
class Tg extends Xe {
  constructor() {
    super(...arguments), this.id = kg++, this.isExitComplete = !1;
  }
  update() {
    if (!this.node.presenceContext)
      return;
    const { isPresent: t, onExitComplete: n } = this.node.presenceContext, { isPresent: i } = this.node.prevPresenceContext || {};
    if (!this.node.animationState || t === i)
      return;
    if (t && i === !1) {
      if (this.isExitComplete) {
        const { initial: o, custom: s } = this.node.getProps();
        if (typeof o == "string" || typeof o == "object" && o !== null && !Array.isArray(o)) {
          const a = st(this.node, o, s);
          if (a) {
            const { transition: l, transitionEnd: c, ...u } = a;
            for (const f in u)
              this.node.getValue(f)?.jump(u[f]);
          }
        }
        this.node.animationState.reset(), this.node.animationState.animateChanges();
      } else
        this.node.animationState.setActive("exit", !1);
      this.isExitComplete = !1;
      return;
    }
    const r = this.node.animationState.setActive("exit", !t);
    n && !t && r.then(() => {
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
const Sg = {
  animation: {
    Feature: wg
  },
  exit: {
    Feature: Tg
  }
};
function ln(e) {
  return {
    point: {
      x: e.pageX,
      y: e.pageY
    }
  };
}
const Ag = (e) => (t) => ds(t) && e(t, ln(t));
function _t(e, t, n, i) {
  return Qt(e, t, Ag(n), i);
}
const _c = ({ current: e }) => e ? e.ownerDocument.defaultView : null, Zo = (e, t) => Math.abs(e - t);
function Cg(e, t) {
  const n = Zo(e.x, t.x), i = Zo(e.y, t.y);
  return Math.sqrt(n ** 2 + i ** 2);
}
const Jo = /* @__PURE__ */ new Set(["auto", "scroll"]);
class Uc {
  constructor(t, n, { transformPagePoint: i, contextWindow: r = window, dragSnapToOrigin: o = !1, distanceThreshold: s = 3, element: a } = {}) {
    if (this.startEvent = null, this.lastMoveEvent = null, this.lastMoveEventInfo = null, this.lastRawMoveEventInfo = null, this.handlers = {}, this.contextWindow = window, this.scrollPositions = /* @__PURE__ */ new Map(), this.removeScrollListeners = null, this.onElementScroll = (p) => {
      this.handleScroll(p.target);
    }, this.onWindowScroll = () => {
      this.handleScroll(window);
    }, this.updatePoint = () => {
      if (!(this.lastMoveEvent && this.lastMoveEventInfo))
        return;
      this.lastRawMoveEventInfo && (this.lastMoveEventInfo = yn(this.lastRawMoveEventInfo, this.transformPagePoint));
      const p = Ai(this.lastMoveEventInfo, this.history), g = this.startEvent !== null, y = Cg(p.offset, { x: 0, y: 0 }) >= this.distanceThreshold;
      if (!g && !y)
        return;
      const { point: b } = p, { timestamp: k } = ae;
      this.history.push({ ...b, timestamp: k });
      const { onStart: x, onMove: S } = this.handlers;
      g || (x && x(this.lastMoveEvent, p), this.startEvent = this.lastMoveEvent), S && S(this.lastMoveEvent, p);
    }, this.handlePointerMove = (p, g) => {
      this.lastMoveEvent = p, this.lastRawMoveEventInfo = g, this.lastMoveEventInfo = yn(g, this.transformPagePoint), K.update(this.updatePoint, !0);
    }, this.handlePointerUp = (p, g) => {
      this.end();
      const { onEnd: y, onSessionEnd: b, resumeAnimation: k } = this.handlers;
      if ((this.dragSnapToOrigin || !this.startEvent) && k && k(), !(this.lastMoveEvent && this.lastMoveEventInfo))
        return;
      const x = Ai(p.type === "pointercancel" ? this.lastMoveEventInfo : yn(g, this.transformPagePoint), this.history);
      this.startEvent && y && y(p, x), b && b(p, x);
    }, !ds(t))
      return;
    this.dragSnapToOrigin = o, this.handlers = n, this.transformPagePoint = i, this.distanceThreshold = s, this.contextWindow = r || window;
    const l = ln(t), c = yn(l, this.transformPagePoint), { point: u } = c, { timestamp: f } = ae;
    this.history = [{ ...u, timestamp: f }];
    const { onSessionStart: h } = n;
    h && h(t, Ai(c, this.history));
    const m = { passive: !0, capture: !0 };
    this.removeListeners = rn(_t(this.contextWindow, "pointermove", this.handlePointerMove, m), _t(this.contextWindow, "pointerup", this.handlePointerUp, m), _t(this.contextWindow, "pointercancel", this.handlePointerUp, m)), a && this.startScrollTracking(a);
  }
  /**
   * Start tracking scroll on ancestors and window.
   */
  startScrollTracking(t) {
    let n = t.parentElement;
    for (; n; ) {
      const i = getComputedStyle(n);
      (Jo.has(i.overflowX) || Jo.has(i.overflowY)) && this.scrollPositions.set(n, {
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
    const i = t === window, r = i ? { x: window.scrollX, y: window.scrollY } : {
      x: t.scrollLeft,
      y: t.scrollTop
    }, o = { x: r.x - n.x, y: r.y - n.y };
    o.x === 0 && o.y === 0 || (i ? this.lastMoveEventInfo && (this.lastMoveEventInfo.point.x += o.x, this.lastMoveEventInfo.point.y += o.y) : this.history.length > 0 && (this.history[0].x -= o.x, this.history[0].y -= o.y), this.scrollPositions.set(t, r), K.update(this.updatePoint, !0));
  }
  updateHandlers(t) {
    this.handlers = t;
  }
  end() {
    this.removeListeners && this.removeListeners(), this.removeScrollListeners && this.removeScrollListeners(), this.scrollPositions.clear(), $e(this.updatePoint);
  }
}
function yn(e, t) {
  return t ? { point: t(e.point) } : e;
}
function ea(e, t) {
  return { x: e.x - t.x, y: e.y - t.y };
}
function Ai({ point: e }, t) {
  return {
    point: e,
    delta: ea(e, Wc(t)),
    offset: ea(e, Ng(t)),
    velocity: Pg(t, 0.1)
  };
}
function Ng(e) {
  return e[0];
}
function Wc(e) {
  return e[e.length - 1];
}
function Pg(e, t) {
  if (e.length < 2)
    return { x: 0, y: 0 };
  let n = e.length - 1, i = null;
  const r = Wc(e);
  for (; n >= 0 && (i = e[n], !(r.timestamp - i.timestamp > /* @__PURE__ */ xe(t))); )
    n--;
  if (!i)
    return { x: 0, y: 0 };
  i === e[0] && e.length > 2 && r.timestamp - i.timestamp > /* @__PURE__ */ xe(t) * 2 && (i = e[1]);
  const o = /* @__PURE__ */ ve(r.timestamp - i.timestamp);
  if (o === 0)
    return { x: 0, y: 0 };
  const s = {
    x: (r.x - i.x) / o,
    y: (r.y - i.y) / o
  };
  return s.x === 1 / 0 && (s.x = 0), s.y === 1 / 0 && (s.y = 0), s;
}
function Mg(e, { min: t, max: n }, i) {
  return t !== void 0 && e < t ? e = i ? Y(t, e, i.min) : Math.max(e, t) : n !== void 0 && e > n && (e = i ? Y(n, e, i.max) : Math.min(e, n)), e;
}
function ta(e, t, n) {
  return {
    min: t !== void 0 ? e.min + t : void 0,
    max: n !== void 0 ? e.max + n - (e.max - e.min) : void 0
  };
}
function Eg(e, { top: t, left: n, bottom: i, right: r }) {
  return {
    x: ta(e.x, n, r),
    y: ta(e.y, t, i)
  };
}
function na(e, t) {
  let n = t.min - e.min, i = t.max - e.max;
  return t.max - t.min < e.max - e.min && ([n, i] = [i, n]), { min: n, max: i };
}
function Dg(e, t) {
  return {
    x: na(e.x, t.x),
    y: na(e.y, t.y)
  };
}
function Rg(e, t) {
  let n = 0.5;
  const i = me(e), r = me(t);
  return r > i ? n = /* @__PURE__ */ St(t.min, t.max - i, e.min) : i > r && (n = /* @__PURE__ */ St(e.min, e.max - r, t.min)), Pe(0, 1, n);
}
function Lg(e, t) {
  const n = {};
  return t.min !== void 0 && (n.min = t.min - e.min), t.max !== void 0 && (n.max = t.max - e.min), n;
}
const dr = 0.35;
function Vg(e = dr) {
  return e === !1 ? e = 0 : e === !0 && (e = dr), {
    x: ia(e, "left", "right"),
    y: ia(e, "top", "bottom")
  };
}
function ia(e, t, n) {
  return {
    min: ra(e, t),
    max: ra(e, n)
  };
}
function ra(e, t) {
  return typeof e == "number" ? e : e[t] || 0;
}
const Fg = /* @__PURE__ */ new WeakMap();
class Ig {
  constructor(t) {
    this.openDragLock = null, this.isDragging = !1, this.currentDirection = null, this.originPoint = { x: 0, y: 0 }, this.constraints = !1, this.hasMutatedConstraints = !1, this.elastic = oe(), this.latestPointerEvent = null, this.latestPanInfo = null, this.visualElement = t;
  }
  start(t, { snapToCursor: n = !1, distanceThreshold: i } = {}) {
    const { presenceContext: r } = this.visualElement;
    if (r && r.isPresent === !1)
      return;
    const o = (f) => {
      n && this.snapToCursor(ln(f).point), this.stopAnimation();
    }, s = (f, h) => {
      const { drag: m, dragPropagation: p, onDragStart: g } = this.getProps();
      if (m && !p && (this.openDragLock && this.openDragLock(), this.openDragLock = kp(m), !this.openDragLock))
        return;
      this.latestPointerEvent = f, this.latestPanInfo = h, this.isDragging = !0, this.currentDirection = null, this.resolveConstraints(), this.visualElement.projection && (this.visualElement.projection.isAnimationBlocked = !0, this.visualElement.projection.target = void 0), De((b) => {
        let k = this.getAxisMotionValue(b).get() || 0;
        if (Le.test(k)) {
          const { projection: x } = this.visualElement;
          if (x && x.layout) {
            const S = x.layout.layoutBox[b];
            S && (k = me(S) * (parseFloat(k) / 100));
          }
        }
        this.originPoint[b] = k;
      }), g && K.update(() => g(f, h), !1, !0), or(this.visualElement, "transform");
      const { animationState: y } = this.visualElement;
      y && y.setActive("whileDrag", !0);
    }, a = (f, h) => {
      this.latestPointerEvent = f, this.latestPanInfo = h;
      const { dragPropagation: m, dragDirectionLock: p, onDirectionLock: g, onDrag: y } = this.getProps();
      if (!m && !this.openDragLock)
        return;
      const { offset: b } = h;
      if (p && this.currentDirection === null) {
        this.currentDirection = Bg(b), this.currentDirection !== null && g && g(this.currentDirection);
        return;
      }
      this.updateAxis("x", h.point, b), this.updateAxis("y", h.point, b), this.visualElement.render(), y && K.update(() => y(f, h), !1, !0);
    }, l = (f, h) => {
      this.latestPointerEvent = f, this.latestPanInfo = h, this.stop(f, h), this.latestPointerEvent = null, this.latestPanInfo = null;
    }, c = () => {
      const { dragSnapToOrigin: f } = this.getProps();
      (f || this.constraints) && this.startAnimation({ x: 0, y: 0 });
    }, { dragSnapToOrigin: u } = this.getProps();
    this.panSession = new Uc(t, {
      onSessionStart: o,
      onStart: s,
      onMove: a,
      onSessionEnd: l,
      resumeAnimation: c
    }, {
      transformPagePoint: this.visualElement.getTransformPagePoint(),
      dragSnapToOrigin: u,
      distanceThreshold: i,
      contextWindow: _c(this.visualElement),
      element: this.visualElement.current
    });
  }
  /**
   * @internal
   */
  stop(t, n) {
    const i = t || this.latestPointerEvent, r = n || this.latestPanInfo, o = this.isDragging;
    if (this.cancel(), !o || !r || !i)
      return;
    const { velocity: s } = r;
    this.startAnimation(s);
    const { onDragEnd: a } = this.getProps();
    a && K.postRender(() => a(i, r));
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
    const { drag: r } = this.getProps();
    if (!i || !xn(t, r, this.currentDirection))
      return;
    const o = this.getAxisMotionValue(t);
    let s = this.originPoint[t] + i[t];
    this.constraints && this.constraints[t] && (s = Mg(s, this.constraints[t], this.elastic[t])), o.set(s);
  }
  resolveConstraints() {
    const { dragConstraints: t, dragElastic: n } = this.getProps(), i = this.visualElement.projection && !this.visualElement.projection.layout ? this.visualElement.projection.measure(!1) : this.visualElement.projection?.layout, r = this.constraints;
    t && dt(t) ? this.constraints || (this.constraints = this.resolveRefConstraints()) : t && i ? this.constraints = Eg(i.layoutBox, t) : this.constraints = !1, this.elastic = Vg(n), r !== this.constraints && !dt(t) && i && this.constraints && !this.hasMutatedConstraints && De((o) => {
      this.constraints !== !1 && this.getAxisMotionValue(o) && (this.constraints[o] = Lg(i.layoutBox[o], this.constraints[o]));
    });
  }
  resolveRefConstraints() {
    const { dragConstraints: t, onMeasureDragConstraints: n } = this.getProps();
    if (!t || !dt(t))
      return !1;
    const i = t.current;
    Te(i !== null, "If `dragConstraints` is set as a React ref, that ref must be passed to another component's `ref` prop.", "drag-constraints-ref");
    const { projection: r } = this.visualElement;
    if (!r || !r.layout)
      return !1;
    r.root && (r.root.scroll = void 0, r.root.updateScroll());
    const o = gp(i, r.root, this.visualElement.getTransformPagePoint());
    let s = Dg(r.layout.layoutBox, o);
    if (n) {
      const a = n(hp(s));
      this.hasMutatedConstraints = !!a, a && (s = sc(a));
    }
    return s;
  }
  startAnimation(t) {
    const { drag: n, dragMomentum: i, dragElastic: r, dragTransition: o, dragSnapToOrigin: s, onDragTransitionEnd: a } = this.getProps(), l = this.constraints || {}, c = De((u) => {
      if (!xn(u, n, this.currentDirection))
        return;
      let f = l && l[u] || {};
      (s === !0 || s === u) && (f = { min: 0, max: 0 });
      const h = r ? 200 : 1e6, m = r ? 40 : 1e7, p = {
        type: "inertia",
        velocity: i ? t[u] : 0,
        bounceStiffness: h,
        bounceDamping: m,
        timeConstant: 750,
        restDelta: 1,
        restSpeed: 10,
        ...o,
        ...f
      };
      return this.startAxisValueAnimation(u, p);
    });
    return Promise.all(c).then(a);
  }
  startAxisValueAnimation(t, n) {
    const i = this.getAxisMotionValue(t);
    return or(this.visualElement, t), i.start(ei(t, i, 0, n, this.visualElement, !1));
  }
  stopAnimation() {
    De((t) => this.getAxisMotionValue(t).stop());
  }
  /**
   * Drag works differently depending on which props are provided.
   *
   * - If _dragX and _dragY are provided, we output the gesture delta directly to those motion values.
   * - Otherwise, we apply the delta to the x/y motion values.
   */
  getAxisMotionValue(t) {
    const n = `_drag${t.toUpperCase()}`, r = this.visualElement.getProps()[n];
    return r || this.visualElement.getValue(t, this.visualElement.latestValues[t] ?? 0);
  }
  snapToCursor(t) {
    De((n) => {
      const { drag: i } = this.getProps();
      if (!xn(n, i, this.currentDirection))
        return;
      const { projection: r } = this.visualElement, o = this.getAxisMotionValue(n);
      if (r && r.layout) {
        const { min: s, max: a } = r.layout.layoutBox[n], l = o.get() || 0;
        o.set(t[n] - Y(s, a, 0.5) + l);
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
    if (!dt(n) || !i || !this.constraints)
      return;
    this.stopAnimation();
    const r = { x: 0, y: 0 };
    De((s) => {
      const a = this.getAxisMotionValue(s);
      if (a && this.constraints !== !1) {
        const l = a.get();
        r[s] = Rg({ min: l, max: l }, this.constraints[s]);
      }
    });
    const { transformTemplate: o } = this.visualElement.getProps();
    this.visualElement.current.style.transform = o ? o({}, "") : "none", i.root && i.root.updateScroll(), i.updateLayout(), this.constraints = !1, this.resolveConstraints(), De((s) => {
      if (!xn(s, t, null))
        return;
      const a = this.getAxisMotionValue(s), { min: l, max: c } = this.constraints[s];
      a.set(Y(l, c, r[s]));
    }), this.visualElement.render();
  }
  addListeners() {
    if (!this.visualElement.current)
      return;
    Fg.set(this.visualElement, this);
    const t = this.visualElement.current, n = _t(t, "pointerdown", (c) => {
      const { drag: u, dragListener: f = !0 } = this.getProps(), h = c.target, m = h !== t && Pp(h);
      u && f && !m && this.start(c);
    });
    let i;
    const r = () => {
      const { dragConstraints: c } = this.getProps();
      dt(c) && c.current && (this.constraints = this.resolveRefConstraints(), i || (i = Og(t, c.current, () => this.scalePositionWithinConstraints())));
    }, { projection: o } = this.visualElement, s = o.addEventListener("measure", r);
    o && !o.layout && (o.root && o.root.updateScroll(), o.updateLayout()), K.read(r);
    const a = Qt(window, "resize", () => this.scalePositionWithinConstraints()), l = o.addEventListener("didUpdate", (({ delta: c, hasLayoutChanged: u }) => {
      this.isDragging && u && (De((f) => {
        const h = this.getAxisMotionValue(f);
        h && (this.originPoint[f] += c[f].translate, h.set(h.get() + c[f].translate));
      }), this.visualElement.render());
    }));
    return () => {
      a(), n(), s(), l && l(), i && i();
    };
  }
  getProps() {
    const t = this.visualElement.getProps(), { drag: n = !1, dragDirectionLock: i = !1, dragPropagation: r = !1, dragConstraints: o = !1, dragElastic: s = dr, dragMomentum: a = !0 } = t;
    return {
      ...t,
      drag: n,
      dragDirectionLock: i,
      dragPropagation: r,
      dragConstraints: o,
      dragElastic: s,
      dragMomentum: a
    };
  }
}
function sa(e) {
  let t = !0;
  return () => {
    if (t) {
      t = !1;
      return;
    }
    e();
  };
}
function Og(e, t, n) {
  const i = xo(e, sa(n)), r = xo(t, sa(n));
  return () => {
    i(), r();
  };
}
function xn(e, t, n) {
  return (t === !0 || t === e) && (n === null || n === e);
}
function Bg(e, t = 10) {
  let n = null;
  return Math.abs(e.y) > t ? n = "y" : Math.abs(e.x) > t && (n = "x"), n;
}
class jg extends Xe {
  constructor(t) {
    super(t), this.removeGroupControls = Ne, this.removeListeners = Ne, this.controls = new Ig(t);
  }
  mount() {
    const { dragControls: t } = this.node.getProps();
    t && (this.removeGroupControls = t.subscribe(this.controls)), this.removeListeners = this.controls.addListeners() || Ne;
  }
  update() {
    const { dragControls: t } = this.node.getProps(), { dragControls: n } = this.node.prevProps || {};
    t !== n && (this.removeGroupControls(), t && (this.removeGroupControls = t.subscribe(this.controls)));
  }
  unmount() {
    this.removeGroupControls(), this.removeListeners(), this.controls.isDragging || this.controls.endPanSession();
  }
}
const Ci = (e) => (t, n) => {
  e && K.update(() => e(t, n), !1, !0);
};
class $g extends Xe {
  constructor() {
    super(...arguments), this.removePointerDownListener = Ne;
  }
  onPointerDown(t) {
    this.session = new Uc(t, this.createPanHandlers(), {
      transformPagePoint: this.node.getTransformPagePoint(),
      contextWindow: _c(this.node)
    });
  }
  createPanHandlers() {
    const { onPanSessionStart: t, onPanStart: n, onPan: i, onPanEnd: r } = this.node.getProps();
    return {
      onSessionStart: Ci(t),
      onStart: Ci(n),
      onMove: Ci(i),
      onEnd: (o, s) => {
        delete this.session, r && K.postRender(() => r(o, s));
      }
    };
  }
  mount() {
    this.removePointerDownListener = _t(this.node.current, "pointerdown", (t) => this.onPointerDown(t));
  }
  update() {
    this.session && this.session.updateHandlers(this.createPanHandlers());
  }
  unmount() {
    this.removePointerDownListener(), this.session && this.session.end();
  }
}
let Ni = !1;
class zg extends nf {
  /**
   * This only mounts projection nodes for components that
   * need measuring, we might want to do it for all components
   * in order to incorporate transforms
   */
  componentDidMount() {
    const { visualElement: t, layoutGroup: n, switchLayoutGroup: i, layoutId: r } = this.props, { projection: o } = t;
    o && (n.group && n.group.add(o), i && i.register && r && i.register(o), Ni && o.root.didUpdate(), o.addEventListener("animationComplete", () => {
      this.safeToRemove();
    }), o.setOptions({
      ...o.options,
      layoutDependency: this.props.layoutDependency,
      onExitComplete: () => this.safeToRemove()
    })), Rn.hasEverUpdated = !0;
  }
  getSnapshotBeforeUpdate(t) {
    const { layoutDependency: n, visualElement: i, drag: r, isPresent: o } = this.props, { projection: s } = i;
    return s && (s.isPresent = o, t.layoutDependency !== n && s.setOptions({
      ...s.options,
      layoutDependency: n
    }), Ni = !0, r || t.layoutDependency !== n || n === void 0 || t.isPresent !== o ? s.willUpdate() : this.safeToRemove(), t.isPresent !== o && (o ? s.promote() : s.relegate() || K.postRender(() => {
      const a = s.getStack();
      (!a || !a.members.length) && this.safeToRemove();
    }))), null;
  }
  componentDidUpdate() {
    const { visualElement: t, layoutAnchor: n } = this.props, { projection: i } = t;
    i && (i.options.layoutAnchor = n, i.root.didUpdate(), fs.postRender(() => {
      !i.currentAnimation && i.isLead() && this.safeToRemove();
    }));
  }
  componentWillUnmount() {
    const { visualElement: t, layoutGroup: n, switchLayoutGroup: i } = this.props, { projection: r } = t;
    Ni = !0, r && (r.scheduleCheckAfterUnmount(), n && n.group && n.group.remove(r), i && i.deregister && i.deregister(r));
  }
  safeToRemove() {
    const { safeToRemove: t } = this.props;
    t && t();
  }
  render() {
    return null;
  }
}
function Hc(e) {
  const [t, n] = Vc(), i = ue(Vr);
  return d(zg, { ...e, layoutGroup: i, switchLayoutGroup: ue($c), isPresent: t, safeToRemove: n });
}
const _g = {
  pan: {
    Feature: $g
  },
  drag: {
    Feature: jg,
    ProjectionNode: Lc,
    MeasureLayout: Hc
  }
};
function oa(e, t, n) {
  const { props: i } = e;
  e.animationState && i.whileHover && e.animationState.setActive("whileHover", n === "Start");
  const r = "onHover" + n, o = i[r];
  o && K.postRender(() => o(t, ln(t)));
}
class Ug extends Xe {
  mount() {
    const { current: t } = this.node;
    t && (this.unmount = Sp(t, (n, i) => (oa(this.node, i, "Start"), (r) => oa(this.node, r, "End"))));
  }
  unmount() {
  }
}
class Wg extends Xe {
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
    this.unmount = rn(Qt(this.node.current, "focus", () => this.onFocus()), Qt(this.node.current, "blur", () => this.onBlur()));
  }
  unmount() {
  }
}
function aa(e, t, n) {
  const { props: i } = e;
  if (e.current instanceof HTMLButtonElement && e.current.disabled)
    return;
  e.animationState && i.whileTap && e.animationState.setActive("whileTap", n === "Start");
  const r = "onTap" + (n === "End" ? "" : n), o = i[r];
  o && K.postRender(() => o(t, ln(t)));
}
class Hg extends Xe {
  mount() {
    const { current: t } = this.node;
    if (!t)
      return;
    const { globalTapTarget: n, propagate: i } = this.node.props;
    this.unmount = Ep(t, (r, o) => (aa(this.node, o, "Start"), (s, { success: a }) => aa(this.node, s, a ? "End" : "Cancel")), {
      useGlobalTarget: n,
      stopPropagation: i?.tap === !1
    });
  }
  unmount() {
  }
}
const hr = /* @__PURE__ */ new WeakMap(), Pi = /* @__PURE__ */ new WeakMap(), Gg = (e) => {
  const t = hr.get(e.target);
  t && t(e);
}, Kg = (e) => {
  e.forEach(Gg);
};
function qg({ root: e, ...t }) {
  const n = e || document;
  Pi.has(n) || Pi.set(n, {});
  const i = Pi.get(n), r = JSON.stringify(t);
  return i[r] || (i[r] = new IntersectionObserver(Kg, { root: e, ...t })), i[r];
}
function Yg(e, t, n) {
  const i = qg(t);
  return hr.set(e, n), i.observe(e), () => {
    hr.delete(e), i.unobserve(e);
  };
}
const Xg = {
  some: 0,
  all: 1
};
class Qg extends Xe {
  constructor() {
    super(...arguments), this.hasEnteredView = !1, this.isInView = !1;
  }
  startObserver() {
    this.stopObserver?.();
    const { viewport: t = {} } = this.node.getProps(), { root: n, margin: i, amount: r = "some", once: o } = t, s = {
      root: n ? n.current : void 0,
      rootMargin: i,
      threshold: typeof r == "number" ? r : Xg[r]
    }, a = (l) => {
      const { isIntersecting: c } = l;
      if (this.isInView === c || (this.isInView = c, o && !c && this.hasEnteredView))
        return;
      c && (this.hasEnteredView = !0), this.node.animationState && this.node.animationState.setActive("whileInView", c);
      const { onViewportEnter: u, onViewportLeave: f } = this.node.getProps(), h = c ? u : f;
      h && h(l);
    };
    this.stopObserver = Yg(this.node.current, s, a);
  }
  mount() {
    this.startObserver();
  }
  update() {
    if (typeof IntersectionObserver > "u")
      return;
    const { props: t, prevProps: n } = this.node;
    ["amount", "margin", "root"].some(Zg(t, n)) && this.startObserver();
  }
  unmount() {
    this.stopObserver?.(), this.hasEnteredView = !1, this.isInView = !1;
  }
}
function Zg({ viewport: e = {} }, { viewport: t = {} } = {}) {
  return (n) => e[n] !== t[n];
}
const Jg = {
  inView: {
    Feature: Qg
  },
  tap: {
    Feature: Hg
  },
  focus: {
    Feature: Wg
  },
  hover: {
    Feature: Ug
  }
}, e0 = {
  layout: {
    ProjectionNode: Lc,
    MeasureLayout: Hc
  }
}, t0 = {
  ...Sg,
  ...Jg,
  ..._g,
  ...e0
}, n0 = /* @__PURE__ */ bg(t0, vg);
function Gc(e) {
  const t = tn(() => ze(e)), { isStatic: n } = ue(ii);
  if (n) {
    const [, i] = B(e);
    O(() => t.on("change", i), []);
  }
  return t;
}
function Kc(e, t) {
  const n = Gc(t()), i = () => n.set(t());
  return i(), Gt(() => {
    const r = () => K.preRender(i, !1, !0), o = e.map((s) => s.on("change", r));
    return () => {
      o.forEach((s) => s()), $e(i);
    };
  }), n;
}
function i0(e) {
  jt.current = [], e();
  const t = Kc(jt.current, e);
  return jt.current = void 0, t;
}
function r0(e, t, n, i) {
  if (typeof e == "function")
    return i0(e);
  const o = typeof t == "function" ? t : $p(t, n, i), s = Array.isArray(e) ? la(e, o) : la([e], ([l]) => o(l)), a = Array.isArray(e) ? void 0 : e.accelerate;
  return a && !a.isTransformed && typeof t != "function" && Array.isArray(n) && i?.clamp !== !1 && (s.accelerate = {
    ...a,
    times: t,
    keyframes: n,
    isTransformed: !0
  }), s;
}
function la(e, t) {
  const n = tn(() => []);
  return Kc(e, () => {
    n.length = 0;
    const i = e.length;
    for (let r = 0; r < i; r++)
      n[r] = e[r].get();
    return t(n);
  });
}
function ne() {
  !ps.current && pc();
  const [e] = B(Un.current);
  return process.env.NODE_ENV !== "production" && Zn(e !== !0, "You have Reduced Motion enabled on your device. Animations may not appear as expected.", "reduced-motion-disabled"), e;
}
function xs(e) {
  return typeof e == "object" && !Array.isArray(e);
}
function qc(e, t, n, i) {
  return e == null ? [] : typeof e == "string" && xs(t) ? ss(e, n, i) : e instanceof NodeList ? Array.from(e) : Array.isArray(e) ? e.filter((r) => r != null) : [e];
}
function s0(e, t, n) {
  return e * (t + 1) + n * t;
}
function ca(e, t, n, i) {
  return typeof t == "number" ? t : t.startsWith("-") || t.startsWith("+") ? Math.max(0, e + parseFloat(t)) : t === "<" ? n : t.startsWith("<") ? Math.max(0, n + parseFloat(t.slice(1))) : i.get(t) ?? e;
}
function o0(e, t, n) {
  for (let i = 0; i < e.length; i++) {
    const r = e[i];
    r.at > t && r.at < n && (ot(e, r), i--);
  }
}
function a0(e, t, n, i, r, o) {
  o0(e, r, o);
  for (let s = 0; s < t.length; s++)
    e.push({
      value: t[s],
      at: Y(r, o, i[s]),
      easing: /* @__PURE__ */ pl(n, s)
    });
}
function l0(e, t, n = 0) {
  const i = t + 1 + t * n;
  for (let r = 0; r < e.length; r++)
    e[r] = e[r] / i;
}
function c0(e, t) {
  return e.at === t.at ? e.value === null ? 1 : t.value === null ? -1 : 0 : e.at - t.at;
}
const u0 = "easeInOut", Mi = 20;
function f0(e, { defaultTransition: t = {}, ...n } = {}, i, r) {
  const o = t.duration || 0.3, s = /* @__PURE__ */ new Map(), a = /* @__PURE__ */ new Map(), l = {}, c = /* @__PURE__ */ new Map();
  let u = 0, f = 0, h = 0;
  for (let m = 0; m < e.length; m++) {
    const p = e[m];
    if (typeof p == "string") {
      c.set(p, f);
      continue;
    } else if (!Array.isArray(p)) {
      c.set(p.name, ca(f, p.at, u, c));
      continue;
    }
    let [g, y, b = {}] = p;
    b.at !== void 0 && (f = ca(f, b.at, u, c));
    let k = 0;
    const x = (S, E, C, A = 0, N = 0) => {
      const P = d0(S), { delay: w = 0, times: T = Rl(P), type: I = t.type || "keyframes", repeat: F, repeatType: X, repeatDelay: q = 0, ...H } = E;
      let { ease: M = t.ease || "easeOut", duration: $ } = E;
      const ee = typeof w == "function" ? w(A, N) : w, re = P.length, ie = Jr(I) ? I : r?.[I || "keyframes"];
      if (re <= 2 && ie) {
        let te = 100;
        if (re === 2 && m0(P)) {
          const Ee = P[1] - P[0];
          te = Math.abs(Ee);
        }
        const he = {
          ...t,
          ...H
        };
        $ !== void 0 && (he.duration = /* @__PURE__ */ xe($));
        const se = Nl(he, te, ie);
        M = se.ease, $ = se.duration;
      }
      $ ?? ($ = o);
      const R = f + ee;
      T.length === 1 && T[0] === 0 && (T[1] = 1);
      const W = T.length - P.length;
      if (W > 0 && Dl(T, W), P.length === 1 && P.unshift(null), F && ct(F < Mi, `Sequence segments can't repeat ${F} times — ignoring repeat option. Use a value below ${Mi} or apply repeat at the sequence level instead.`), F && F < Mi) {
        const te = $ > 0 ? q / $ : 0;
        $ = s0($, F, q);
        const he = [...P], se = [...T];
        M = Array.isArray(M) ? [...M] : [M];
        const Ee = [...M], Et = X === "reverse" || X === "mirror";
        let Dt = he, Ms = Ee;
        Et && (Dt = [...he].reverse(), X === "reverse" && (Ms = [...Ee].reverse().map((Ge) => typeof Ge == "function" ? /* @__PURE__ */ jr(Ge) : Ge)));
        for (let Ge = 0; Ge < F; Ge++) {
          const Es = Et && Ge % 2 === 0, Ds = Es ? Dt : he, Qu = Es ? Ms : Ee, Rs = (Ge + 1) * (1 + te);
          te > 0 && (P.push(P[P.length - 1]), T.push(Rs), M.push("linear")), P.push(...Ds);
          for (let Rt = 0; Rt < Ds.length; Rt++)
            T.push(se[Rt] + Rs), M.push(Rt === 0 ? "linear" : /* @__PURE__ */ pl(Qu, Rt - 1));
        }
        l0(T, F, te);
      }
      const G = R + $;
      a0(C, P, M, T, R, G), k = Math.max(ee + $, k), h = Math.max(G, h);
    };
    if (ce(g)) {
      const S = ua(g, a);
      x(y, b, fa("default", S));
    } else {
      const S = qc(g, y, i, l), E = S.length;
      for (let C = 0; C < E; C++) {
        y = y, b = b;
        const A = S[C], N = ua(A, a);
        for (const P in y)
          x(y[P], h0(b, P), fa(P, N), C, E);
      }
    }
    u = f, f += k;
  }
  return a.forEach((m, p) => {
    for (const g in m) {
      const y = m[g];
      y.sort(c0);
      const b = [], k = [], x = [];
      for (let A = 0; A < y.length; A++) {
        const { at: N, value: P, easing: w } = y[A];
        b.push(P), k.push(/* @__PURE__ */ St(0, h, N)), x.push(w || "easeOut");
      }
      k[0] !== 0 && (k.unshift(0), b.unshift(b[0]), x.unshift(u0)), k[k.length - 1] !== 1 && (k.push(1), b.push(null)), s.has(p) || s.set(p, {
        keyframes: {},
        transition: {}
      });
      const S = s.get(p);
      S.keyframes[g] = b;
      const { type: E, ...C } = t;
      S.transition[g] = {
        ...C,
        duration: h,
        ease: x,
        times: k,
        ...n
      };
    }
  }), s;
}
function ua(e, t) {
  return !t.has(e) && t.set(e, {}), t.get(e);
}
function fa(e, t) {
  return t[e] || (t[e] = []), t[e];
}
function d0(e) {
  return Array.isArray(e) ? e : [e];
}
function h0(e, t) {
  return e && e[t] ? {
    ...e,
    ...e[t]
  } : { ...e };
}
const p0 = (e) => typeof e == "number", m0 = (e) => e.every(p0);
function g0(e, t) {
  return ce(e) || typeof e == "number" || typeof e == "string" && !xs(t);
}
function Yc(e, t, n, i) {
  const r = [];
  if (g0(e, t))
    r.push(Mc(e, xs(t) && t.default || t, n && (n.default || n)));
  else {
    if (e == null)
      return r;
    const o = qc(e, t, i), s = o.length;
    Te(!!s, "No valid elements provided.", "no-valid-elements");
    for (let a = 0; a < s; a++) {
      const l = o[a], c = { ...n };
      "delay" in c && typeof c.delay == "function" && (c.delay = c.delay(a, s)), l instanceof Element ? r.push(...vp(l, t, c, dc.get(l))) : r.push(...tc(qh(l) ?? wp, l, t, c));
    }
  }
  return r;
}
function y0(e, t, n) {
  const i = [], r = e.map((s) => {
    if (Array.isArray(s) && typeof s[0] == "function") {
      const a = s[0], l = ze(0);
      return l.on("change", a), s.length === 1 ? [l, [0, 1]] : s.length === 2 ? [l, [0, 1], s[1]] : [l, s[1], s[2]];
    }
    return s;
  });
  return f0(r, t, n, { spring: Yt }).forEach(({ keyframes: s, transition: a }, l) => {
    i.push(...Yc(l, s, a));
  }), i;
}
function x0(e) {
  return Array.isArray(e) && e.some(Array.isArray);
}
function b0(e = {}) {
  const { scope: t, reduceMotion: n, skipAnimations: i } = e;
  function r(o, s, a) {
    let l = [], c;
    const u = {};
    if (n !== void 0 && (u.reduceMotion = n), i !== void 0 && (u.skipAnimations = i), x0(o)) {
      const { onComplete: h, ...m } = s || {};
      typeof h == "function" && (c = h), l = y0(o, { ...u, ...m }, t);
    } else {
      const { onComplete: h, ...m } = a || {};
      typeof h == "function" && (c = h), l = Yc(o, s, { ...u, ...m }, t);
    }
    const f = new vh(l);
    return c && f.finished.then(c), t && (t.animations.push(f), f.finished.then(() => {
      ot(t.animations, f);
    })), f;
  }
  return r;
}
const Ei = Object.assign(b0(), {
  /**
   * Register an effect so `animate()` can animate the subjects it
   * claims, for instance `animate.addEffect(threeEffect)`. The most
   * recently added effect is tested first. DOM elements are always
   * animated directly.
   */
  addEffect: Kh,
  removeEffect: Jl
}), j = n0;
function Zt(e) {
  return `REV ${String(Math.max(0, e ?? 0)).padStart(2, "0")}`;
}
function Hv(e, t) {
  if (!e) return null;
  const n = e.replace(/^claude-/, "");
  return t ? `${n} ${t}` : n;
}
function Xc(e) {
  if (e == null) return null;
  const t = Math.max(0, Math.round(e));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function cn(e) {
  const t = Math.max(0, e);
  return t < 59.95 ? `${t.toFixed(1)}s` : Xc(t);
}
function v0(e, t = Date.now()) {
  if (!e) return null;
  const n = Math.max(0, Math.round((t - new Date(e).getTime()) / 1e3));
  if (n < 60) return "just now";
  const i = Math.round(n / 60);
  if (i < 60) return `${i}m ago`;
  const r = Math.round(i / 60);
  if (r < 24) return `${r}h ago`;
  const o = Math.round(r / 24);
  if (o < 7) return `${o}d ago`;
  const s = Math.round(o / 7);
  return s < 8 ? `${s}w ago` : `${Math.round(o / 30)}mo ago`;
}
function w0(e) {
  return !e || e.length !== 3 ? null : e.map((t) => Math.round(t * 10) / 10).join(" × ");
}
function Gv(e) {
  if (!e) return "·";
  if (e.includes("@")) return e.split("@")[0].slice(0, 2).toUpperCase();
  const t = e.trim().split(/\s+/);
  return (t.length > 1 ? t[0][0] + t[1][0] : t[0].slice(0, 2)).toUpperCase();
}
function Kn(e) {
  const t = e.replace(/_+/g, " ").trim();
  return t.charAt(0).toUpperCase() + t.slice(1);
}
const k0 = typeof window > "u" ? O : Nt, T0 = Z.out;
function bs(e) {
  const t = D(null), [n, i] = B(0), [r, o] = B(!1), [s, a] = B(e), l = D(e);
  l.current !== e && (l.current = e, s && a(!1)), k0(() => {
    const u = t.current;
    if (!u) return;
    const f = () => {
      const m = u.getBoundingClientRect().height;
      i((p) => Math.abs(p - m) < 0.5 ? p : m);
    };
    if (f(), o(!0), typeof ResizeObserver > "u") return;
    const h = new ResizeObserver(f);
    return h.observe(u), () => h.disconnect();
  }, []);
  const c = ne();
  return {
    ref: t,
    height: n,
    animate: { height: e ? s || !r ? "auto" : n : 0 },
    transition: { duration: c ? 0 : _.settle, ease: T0 },
    onAnimationComplete: () => {
      e && a(!0);
    },
    style: { overflow: "hidden" }
  };
}
const S0 = {
  done: "check",
  failed: "warning",
  running: "ruler"
};
function qn(e, t) {
  return e.status !== "running" ? e.elapsed_s ?? 0 : Math.max(0, (t - new Date(e.started_at).getTime()) / 1e3);
}
function A0({ startedAt: e, className: t }) {
  const [n, i] = B(() => Date.now());
  O(() => {
    const o = setInterval(() => i(Date.now()), 100);
    return () => clearInterval(o);
  }, []);
  const r = Math.max(0, (n - new Date(e).getTime()) / 1e3);
  return /* @__PURE__ */ d("span", { "aria-hidden": "true", className: t, children: cn(r) });
}
function Qc({ open: e }) {
  const t = ne() === !0;
  return /* @__PURE__ */ d(
    j.span,
    {
      "aria-hidden": "true",
      className: "flex shrink-0 items-center text-faint",
      animate: { rotate: e ? 0 : -90 },
      transition: { duration: t ? 0 : _.tick, ease: Z.out },
      children: /* @__PURE__ */ d(z, { name: "chevron-down" })
    }
  );
}
function Zc({ open: e, id: t, className: n, children: i }) {
  const r = bs(e);
  return /* @__PURE__ */ d(j.div, { id: t, style: r.style, animate: r.animate, transition: r.transition, onAnimationComplete: r.onAnimationComplete, children: /* @__PURE__ */ d("div", { ref: r.ref, className: n, children: e ? i : null }) });
}
function C0(e) {
  const t = `${e.verb.charAt(0).toUpperCase()}${e.verb.slice(1)} ${e.object}`;
  if (e.status === "running")
    return `${t}, running for ${Math.round(qn(e, Date.now()))} seconds`;
  const n = qn(e, Date.now()).toFixed(1);
  return `${t}, ${e.status === "failed" ? "failed after" : "finished in"} ${n} seconds`;
}
function Jc({ step: e, defaultOpen: t }) {
  const [n, i] = B(t ?? e.status === "failed");
  O(() => {
    e.status === "failed" && i(!0);
  }, [e.status]);
  const r = Se(), o = e.status === "running", s = e.status === "failed", a = e.input == null ? null : JSON.stringify(e.input, null, 2), l = e.output?.trim() ? e.output : null, c = a != null || l != null;
  return /* @__PURE__ */ v("div", { className: "flex flex-col", children: [
    /* @__PURE__ */ v(
      "button",
      {
        type: "button",
        onClick: c ? () => i((u) => !u) : void 0,
        "aria-expanded": c ? n : void 0,
        "aria-controls": c ? r : void 0,
        className: V(
          "flex min-h-[28px] w-full items-center gap-2 rounded-[3px] px-2 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          s ? "bg-fail-wash" : o ? "bg-accent-wash" : "bg-transparent",
          c && !s && !o && "hover:bg-raised",
          !c && "cursor-default"
        ),
        children: [
          /* @__PURE__ */ d("span", { "aria-hidden": "true", className: V("flex shrink-0 items-center", s ? "text-fail" : "text-ink-soft"), children: /* @__PURE__ */ d(z, { name: S0[e.status] }) }),
          /* @__PURE__ */ d("span", { "aria-hidden": "true", className: V("mono-label shrink-0", s ? "text-fail" : "text-muted"), children: e.verb.toUpperCase() }),
          /* @__PURE__ */ d("span", { "aria-hidden": "true", className: "min-w-0 flex-1 truncate text-[13px] leading-[19px] text-ink-soft", children: e.object }),
          o ? /* @__PURE__ */ d(A0, { startedAt: e.started_at, className: "mono-value min-w-[44px] shrink-0 text-right tabular-nums text-accent-ink" }) : /* @__PURE__ */ d("span", { "aria-hidden": "true", className: "mono-value min-w-[44px] shrink-0 text-right tabular-nums text-faint", children: cn(qn(e, Date.now())) }),
          c ? /* @__PURE__ */ d(Qc, { open: n }) : null,
          /* @__PURE__ */ d("span", { className: "sr-only", children: C0(e) })
        ]
      }
    ),
    /* @__PURE__ */ v(Zc, { open: n && c, id: r, className: "relative flex flex-col gap-1.5 pt-1.5 pr-2 pb-2.5 pl-7", children: [
      /* @__PURE__ */ d("span", { "aria-hidden": "true", className: "absolute top-0 bottom-0 left-[13px] w-px bg-line-soft" }),
      a ? /* @__PURE__ */ v("div", { className: "flex flex-col gap-1", children: [
        /* @__PURE__ */ d("span", { className: "mono-label text-muted", children: "INPUT" }),
        /* @__PURE__ */ d("pre", { className: "max-h-[216px] overflow-y-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap text-ink-soft", children: a })
      ] }) : null,
      l ? /* @__PURE__ */ v("div", { className: "flex flex-col gap-1", children: [
        /* @__PURE__ */ d("span", { className: "mono-label text-muted", children: "OUTPUT" }),
        /* @__PURE__ */ d("pre", { className: "max-h-[216px] overflow-y-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap text-ink-soft", children: l })
      ] }) : null
    ] })
  ] });
}
function N0(e) {
  const t = [];
  let n = [];
  const i = () => {
    n.length >= 3 ? t.push({ kind: "group", steps: n }) : n.forEach((r) => t.push({ kind: "step", step: r })), n = [];
  };
  for (const r of e) {
    if (r.status === "done") {
      n.push(r);
      continue;
    }
    i(), t.push({ kind: "step", step: r });
  }
  return i(), t;
}
function P0({ steps: e, defaultCollapsed: t }) {
  const [n, i] = B(!t), r = Se();
  O(() => {
    t && i(!1);
  }, [t]);
  const o = e.reduce((s, a) => s + qn(a, Date.now()), 0);
  return /* @__PURE__ */ v("div", { className: "flex flex-col", children: [
    /* @__PURE__ */ v(
      "button",
      {
        type: "button",
        onClick: () => i((s) => !s),
        "aria-expanded": n,
        "aria-controls": r,
        className: "flex min-h-[28px] items-center gap-2 self-start rounded-[3px] px-2 hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
        children: [
          /* @__PURE__ */ d("span", { "aria-hidden": "true", className: "flex shrink-0 items-center text-ink-soft", children: /* @__PURE__ */ d(z, { name: "dots" }) }),
          /* @__PURE__ */ v("span", { className: "mono-label text-muted", children: [
            e.length,
            " STEPS"
          ] }),
          /* @__PURE__ */ v("span", { className: "mono-value text-faint", children: [
            /* @__PURE__ */ d("span", { "aria-hidden": "true", children: "· " }),
            cn(o)
          ] }),
          /* @__PURE__ */ d("span", { "aria-hidden": "true", className: "ml-1.5 flex items-center", children: /* @__PURE__ */ d(Qc, { open: n }) })
        ]
      }
    ),
    /* @__PURE__ */ d(Zc, { open: n, id: r, className: "flex flex-col gap-[2px]", children: e.map((s) => /* @__PURE__ */ d(Jc, { step: s }, s.id)) })
  ] });
}
function M0({ steps: e, defaultCollapsed: t = !0 }) {
  return /* @__PURE__ */ d("div", { className: "flex flex-col gap-[2px]", children: N0(e).map(
    (n) => n.kind === "group" ? /* @__PURE__ */ d(P0, { steps: n.steps, defaultCollapsed: t }, n.steps[0].id) : /* @__PURE__ */ d(Jc, { step: n.step }, n.step.id)
  ) });
}
function E0({ findings: e, passed: t }) {
  const n = e.filter((o) => o.severity === "fail"), i = e.filter((o) => o.severity === "warn"), r = t ? i : [...n, ...i];
  return /* @__PURE__ */ v("ul", { className: "flex flex-col gap-[5px]", role: "list", children: [
    t ? /* @__PURE__ */ v("li", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ d("span", { className: "text-pass", children: /* @__PURE__ */ d(z, { name: "check" }) }),
      /* @__PURE__ */ d("span", { className: "mono-id text-ink-soft uppercase [letter-spacing:0.06em]", children: "Checks pass" })
    ] }) : n.length > 0 ? /* @__PURE__ */ v("li", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ d("span", { className: "text-fail", children: /* @__PURE__ */ d(z, { name: "xmark" }) }),
      /* @__PURE__ */ v("span", { className: "mono-id text-ink-soft uppercase [letter-spacing:0.06em]", children: [
        n.length,
        " check",
        n.length === 1 ? "" : "s",
        " failed"
      ] })
    ] }) : null,
    r.map((o, s) => /* @__PURE__ */ v("li", { className: "flex items-baseline gap-2", children: [
      /* @__PURE__ */ d("span", { className: V("flex h-[14px] items-center", o.severity === "fail" ? "text-fail" : "text-warn"), children: /* @__PURE__ */ d(z, { name: "warning" }) }),
      /* @__PURE__ */ d("span", { className: "mono-id shrink-0 text-ink-soft uppercase [letter-spacing:0.06em]", children: o.label || o.rule }),
      /* @__PURE__ */ d("span", { className: "min-w-0 text-xs leading-[14px] text-muted", children: o.message })
    ] }, `${o.rule}-${s}`))
  ] });
}
function D0({ startedAt: e }) {
  const [t, n] = B(() => Date.now());
  return O(() => {
    const i = setInterval(() => n(Date.now()), 100);
    return () => clearInterval(i);
  }, []), /* @__PURE__ */ d(U, { children: cn(Math.max(0, (t - new Date(e).getTime()) / 1e3)) });
}
function Kv({ build: e, collapsed: t }) {
  const n = e.status === "running", i = e.status === "passed", r = n ? "Building" : i ? "Built" : "Failed", o = e.status === "error" ? e.error?.trim().split(`
`).pop() || "Something broke on my end." : null, s = [
    e.revision != null ? Zt(e.revision) : null,
    n ? /* @__PURE__ */ d(D0, { startedAt: e.started_at }, "clock") : e.elapsed_s != null ? Xc(e.elapsed_s) : null
  ].filter((a) => a != null);
  return /* @__PURE__ */ v("div", { className: "flex flex-col overflow-hidden rounded-[6px] border border-line", children: [
    /* @__PURE__ */ v("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3", children: [
      /* @__PURE__ */ v("span", { className: "mono-label flex items-center gap-2 text-ink", children: [
        i ? /* @__PURE__ */ d("span", { className: "text-pass", children: /* @__PURE__ */ d(z, { name: "check" }) }) : n ? null : /* @__PURE__ */ d("span", { className: "text-fail", children: /* @__PURE__ */ d(z, { name: "xmark" }) }),
        r
      ] }),
      /* @__PURE__ */ d("span", { className: "mono-caption text-muted [letter-spacing:0.06em]", children: s.map((a, l) => /* @__PURE__ */ v("span", { children: [
        l > 0 ? " · " : "",
        a
      ] }, l)) })
    ] }),
    /* @__PURE__ */ v("div", { className: "flex flex-col gap-[9px] px-3 pt-2.5 pb-3", children: [
      e.steps.length > 0 ? /* @__PURE__ */ d(M0, { steps: e.steps, defaultCollapsed: t ?? i }) : null,
      !n && e.render_url ? /* @__PURE__ */ d(
        "img",
        {
          src: e.render_url,
          alt: `${e.part_name} from four sides`,
          className: "w-full rounded-[4px] border border-line-soft bg-raised"
        }
      ) : null,
      !n && e.findings.length > 0 ? /* @__PURE__ */ d(E0, { findings: e.findings, passed: i }) : null,
      o ? /* @__PURE__ */ d("p", { className: "text-[13px] leading-[19px] text-ink-soft", children: o }) : null
    ] })
  ] });
}
function da(e, t) {
  const n = String(e);
  if (typeof t != "string")
    throw new TypeError("Expected character");
  let i = 0, r = n.indexOf(t);
  for (; r !== -1; )
    i++, r = n.indexOf(t, r + t.length);
  return i;
}
const Jt = si(/[A-Za-z]/), vs = si(/[\dA-Za-z]/);
function R0(e) {
  return (
    // Special whitespace codes (which have negative values), C0 and Control
    // character DEL
    e !== null && (e < 32 || e === 127)
  );
}
function vt(e) {
  return e !== null && e < -2;
}
function be(e) {
  return e !== null && (e < 0 || e === 32);
}
function Oe(e) {
  return e === -2 || e === -1 || e === 32;
}
const un = si(new RegExp("\\p{P}|\\p{S}", "u")), at = si(/\s/);
function si(e) {
  return t;
  function t(n) {
    return n !== null && n > -1 && e.test(String.fromCharCode(n));
  }
}
function L0(e) {
  if (typeof e != "string")
    throw new TypeError("Expected a string");
  return e.replace(/[|\\{}()[\]^$+*?.]/g, "\\$&").replace(/-/g, "\\x2d");
}
const oi = (
  // Note: overloads in JSDoc can’t yet use different `@template`s.
  /**
   * @type {(
   *   (<Condition extends string>(test: Condition) => (node: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node & {type: Condition}) &
   *   (<Condition extends Props>(test: Condition) => (node: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node & Condition) &
   *   (<Condition extends TestFunction>(test: Condition) => (node: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node & Predicate<Condition, Node>) &
   *   ((test?: null | undefined) => (node?: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node) &
   *   ((test?: Test) => Check)
   * )}
   */
  /**
   * @param {Test} [test]
   * @returns {Check}
   */
  (function(e) {
    if (e == null)
      return O0;
    if (typeof e == "function")
      return ai(e);
    if (typeof e == "object")
      return Array.isArray(e) ? V0(e) : (
        // Cast because `ReadonlyArray` goes into the above but `isArray`
        // narrows to `Array`.
        F0(
          /** @type {Props} */
          e
        )
      );
    if (typeof e == "string")
      return I0(e);
    throw new Error("Expected function, string, or object as test");
  })
);
function V0(e) {
  const t = [];
  let n = -1;
  for (; ++n < e.length; )
    t[n] = oi(e[n]);
  return ai(i);
  function i(...r) {
    let o = -1;
    for (; ++o < t.length; )
      if (t[o].apply(this, r)) return !0;
    return !1;
  }
}
function F0(e) {
  const t = (
    /** @type {Record<string, unknown>} */
    e
  );
  return ai(n);
  function n(i) {
    const r = (
      /** @type {Record<string, unknown>} */
      /** @type {unknown} */
      i
    );
    let o;
    for (o in e)
      if (r[o] !== t[o]) return !1;
    return !0;
  }
}
function I0(e) {
  return ai(t);
  function t(n) {
    return n && n.type === e;
  }
}
function ai(e) {
  return t;
  function t(n, i, r) {
    return !!(B0(n) && e.call(
      this,
      n,
      typeof i == "number" ? i : void 0,
      r || void 0
    ));
  }
}
function O0() {
  return !0;
}
function B0(e) {
  return e !== null && typeof e == "object" && "type" in e;
}
const eu = [], j0 = !0, Ut = !1, pr = "skip";
function tu(e, t, n, i) {
  if (!e || typeof e != "object")
    throw new Error("Unexpected value `" + e + "` for `tree`, expected node");
  let r = !0, o, s, a, l;
  if (typeof n == "function" || n && typeof n == "object" ? (o = /** @type {Test} */
  t, s = n, i && (r = !1)) : (s = /** @type {Visitors | Visitor} */
  t, n && (r = !1)), typeof s == "function")
    a = s;
  else if (s && typeof s == "object") {
    if (!(s.enter === null || s.enter === void 0)) if (typeof s.enter == "function")
      a = s.enter;
    else
      throw new Error(
        "Unexpected value `" + s.enter + "` for `visitors.enter`, expected optional visitor"
      );
    if (typeof s.exit == "function")
      l = s.exit;
    else
      throw new Error(
        "Unexpected value `" + s.exit + "` for `visitors.exit`, expected visitor (pass a visitor directly if you only want an enter visitor)"
      );
  } else
    throw new Error(
      "Unexpected value `" + s + "` for `enter` or `visitors`, expected visitor or object with visitors"
    );
  const c = oi(o), u = r ? 1 : -1;
  f(e, void 0, [])();
  function f(h, m, p) {
    const g = (
      /** @type {Record<string, unknown>} */
      h && typeof h == "object" ? h : {}
    );
    if (typeof g.type == "string") {
      const b = (
        // `hast`
        typeof g.tagName == "string" ? g.tagName : (
          // `xast`
          typeof g.name == "string" ? g.name : void 0
        )
      );
      Object.defineProperty(y, "name", {
        value: "node (" + (h.type + (b ? "<" + b + ">" : "")) + ")"
      });
    }
    return y;
    function y() {
      const b = !o || c(h, m, p[p.length - 1] || void 0);
      let k = eu;
      if (a && b && (k = ha(a(h, p, m)), k[0] === Ut))
        return k;
      if ("children" in h && h.children) {
        const x = (
          /** @type {UnistParent} */
          h
        );
        if (x.children && k[0] !== pr) {
          let S = (r ? -1 : x.children.length) + u;
          const E = [...p, x];
          for (; S > -1 && S < x.children.length; ) {
            const C = x.children[S], A = f(C, S, E)();
            if (A[0] === Ut)
              return A;
            S = typeof A[1] == "number" ? A[1] : S + u;
          }
        }
      }
      if (l && b) {
        const x = ha(l(h, p, m));
        if (x[0] === pr)
          throw new Error(
            "Unexpected value `" + x[0] + "` from `exit`, expected `CONTINUE`, `EXIT`, index, or nothing"
          );
        if (x[0] === Ut || typeof x[1] == "number")
          return x;
      }
      return k;
    }
  }
}
function ha(e) {
  return Array.isArray(e) ? e : typeof e == "number" ? [j0, e] : e == null ? eu : [e];
}
function $0(e, t, n) {
  const r = oi((n || {}).ignore || []), o = z0(t);
  let s = -1;
  for (; ++s < o.length; )
    tu(e, a);
  function a(c, u, f) {
    if (c.type === "text" && typeof f == "number")
      return l(c, u, f);
    if (r(c, f, u[u.length - 1])) return pr;
  }
  function l(c, u, f) {
    const h = u[u.length - 1], m = o[s][0], p = o[s][1];
    let g = 0, y = !1, b = [];
    m.lastIndex = 0;
    let k = m.exec(c.value);
    for (; k; ) {
      const S = k.index, E = {
        index: k.index,
        input: k.input,
        stack: [...u, c]
      };
      let C = p(...k, E);
      if (typeof C == "string" && (C = C.length > 0 ? { type: "text", value: C } : void 0), C === !1)
        m.lastIndex = S + 1;
      else {
        if (g !== S && x({ type: "text", value: c.value.slice(g, S) }), Array.isArray(C))
          for (const A of C) x(A);
        else C && x(C);
        g = S + k[0].length, y = !0;
      }
      if (!m.global)
        break;
      k = m.exec(c.value);
    }
    return y ? (g < c.value.length && x({ type: "text", value: c.value.slice(g) }), h.children.splice(f, 1, ...b)) : b = [c], f + b.length;
    function x(S) {
      const E = b[b.length - 1];
      E && E.type === "text" && S.type === "text" ? E.value += S.value : b.push(S);
    }
  }
}
function z0(e) {
  if (!Array.isArray(e))
    throw new TypeError("Expected find and replace tuple or list of tuples");
  const t = [], n = !e[0] || Array.isArray(e[0]) ? (
    /** @type {FindAndReplaceList} */
    e
  ) : [
    /** @type {FindAndReplaceTuple} */
    e
  ];
  let i = -1;
  for (; ++i < n.length; ) {
    const r = n[i];
    t.push([_0(r[0]), U0(r[1])]);
  }
  return t;
}
function _0(e) {
  return typeof e == "string" ? new RegExp(L0(e), "g") : e;
}
function U0(e) {
  return typeof e == "function" ? e : function() {
    return e;
  };
}
const Di = "phrasing", Ri = ["autolink", "link", "image", "label"];
function W0() {
  return {
    transforms: [Q0],
    enter: {
      literalAutolink: G0,
      literalAutolinkEmail: Li,
      literalAutolinkHttp: Li,
      literalAutolinkWww: Li
    },
    exit: {
      literalAutolink: X0,
      literalAutolinkEmail: Y0,
      literalAutolinkHttp: K0,
      literalAutolinkWww: q0
    }
  };
}
function H0() {
  return {
    unsafe: [
      {
        character: "@",
        before: "[+\\-.\\w]",
        after: "[\\-.\\w]",
        inConstruct: Di,
        notInConstruct: Ri
      },
      {
        character: ".",
        before: "[Ww]",
        after: "[\\-.\\w]",
        inConstruct: Di,
        notInConstruct: Ri
      },
      {
        character: ":",
        before: "[ps]",
        after: "\\/",
        inConstruct: Di,
        notInConstruct: Ri
      }
    ]
  };
}
function G0(e) {
  this.enter(
    { type: "link", title: null, url: "", children: [], position: void 0 },
    e
  );
}
function Li(e) {
  this.config.enter.autolinkProtocol.call(this, e);
}
function K0(e) {
  this.config.exit.autolinkProtocol.call(this, e);
}
function q0(e) {
  this.config.exit.data.call(this, e);
  const t = this.stack[this.stack.length - 1];
  t.type, t.url = "http://" + this.sliceSerialize(e);
}
function Y0(e) {
  this.config.exit.autolinkEmail.call(this, e);
}
function X0(e) {
  this.exit(e);
}
function Q0(e) {
  $0(
    e,
    [
      [
        new RegExp("(?<![\\da-z])(https?:\\/\\/|www(?=\\.))([\\w-]*\\.[\\w\\-.]*)([^\\t\\n\\r ]*)", "gi"),
        Z0
      ],
      [
        new RegExp("(?<![\\w+\\-.@])xmpp:([\\w+\\-.]+)@([\\w-]+(?:\\.[\\w-]+)+)(\\/(?:[\\w\\-/]|\\.(?=[\\dA-Za-z]))*)?", "g"),
        t1
      ],
      [new RegExp("(?<![\\w+\\-.@])mailto:([\\w+\\-.]+)@([\\w-]+(?:\\.[\\w-]+)+)", "g"), e1],
      [
        new RegExp("(?<![\\w+\\-.]|(?:^|[^\\d@A-Za-z])(?:mailto|xmpp):)([\\w+\\-.]+)@([\\w-]+(?:\\.[\\w-]+)+)", "g"),
        J0
      ]
    ],
    { ignore: ["link", "linkReference"] }
  );
}
function Z0(e, t, n, i, r) {
  if (!r1(r))
    return !1;
  let o = "";
  if (/^w/i.test(t) && (n = t + n, t = "", o = "http://"), un(n.charCodeAt(0)) || !n1(n))
    return !1;
  const s = i1(n + i), a = {
    type: "link",
    title: null,
    url: o + t + s[0],
    children: [{ type: "text", value: t + s[0], position: void 0 }],
    position: void 0
  };
  return s[1] ? [a, { type: "text", value: s[1], position: void 0 }] : a;
}
function J0(e, t, n) {
  return /[\d\-_]$/.test(n) ? !1 : {
    type: "link",
    title: null,
    url: "mailto:" + t + "@" + n,
    children: [{ type: "text", value: t + "@" + n, position: void 0 }],
    position: void 0
  };
}
function e1(e, t, n) {
  if (/[\d\-_]$/.test(n))
    return !1;
  const i = "mailto:" + t + "@" + n;
  return {
    type: "link",
    title: null,
    url: i,
    children: [{ type: "text", value: i, position: void 0 }],
    position: void 0
  };
}
function t1(e, t, n, i, r) {
  if (/[\d\-_]$/.test(n) || i && (!/[A-Za-z]$/.test(i) || r.input.charAt(r.index + e.length) === "@"))
    return !1;
  const o = "xmpp:" + t + "@" + n + (i || "");
  return {
    type: "link",
    title: null,
    url: o,
    children: [{ type: "text", value: o, position: void 0 }],
    position: void 0
  };
}
function n1(e) {
  const t = e.split(".");
  return !(t.length < 2 || t[t.length - 1] && (/_/.test(t[t.length - 1]) || !/[\dA-Za-z]/.test(t[t.length - 1])) || t[t.length - 2] && (/_/.test(t[t.length - 2]) || !/[\dA-Za-z]/.test(t[t.length - 2])));
}
function i1(e) {
  let t = e.length;
  for (; t > 0; ) {
    const s = e.charCodeAt(t - 1);
    if (s === 33 || s === 34 || s === 38 || s === 39 || s === 41 || s === 44 || s === 46 || s === 58 || s === 59 || s === 60 || s === 62 || s === 63 || s === 93 || s === 125)
      t--;
    else
      break;
  }
  if (t === e.length)
    return [e, void 0];
  let n = e.slice(t);
  e = e.slice(0, t);
  let i = n.indexOf(")");
  const r = da(e, "(");
  let o = da(e, ")");
  for (; i !== -1 && r > o; )
    e += n.slice(0, i + 1), n = n.slice(i + 1), i = n.indexOf(")"), o++;
  return [e, n];
}
function r1(e) {
  const t = e.input.charCodeAt(e.index - 1);
  return e.index === 0 || at(t) || un(t);
}
function fn(e) {
  return e.replace(/[\t\n\r ]+/g, " ").replace(/^ | $/g, "").toLowerCase().toUpperCase();
}
nu.peek = h1;
function s1() {
  this.buffer();
}
function o1(e) {
  this.enter({ type: "footnoteReference", identifier: "", label: "" }, e);
}
function a1() {
  this.buffer();
}
function l1(e) {
  this.enter(
    { type: "footnoteDefinition", identifier: "", label: "", children: [] },
    e
  );
}
function c1(e) {
  const t = this.resume(), n = this.stack[this.stack.length - 1];
  n.type, n.identifier = fn(
    this.sliceSerialize(e)
  ).toLowerCase(), n.label = t;
}
function u1(e) {
  this.exit(e);
}
function f1(e) {
  const t = this.resume(), n = this.stack[this.stack.length - 1];
  n.type, n.identifier = fn(
    this.sliceSerialize(e)
  ).toLowerCase(), n.label = t;
}
function d1(e) {
  this.exit(e);
}
function h1() {
  return "[";
}
function nu(e, t, n, i) {
  const r = n.createTracker(i);
  let o = r.move("[^");
  const s = n.enter("footnoteReference"), a = n.enter("reference");
  return o += r.move(
    n.safe(n.associationId(e), { after: "]", before: o })
  ), a(), s(), o += r.move("]"), o;
}
function p1() {
  return {
    enter: {
      gfmFootnoteCallString: s1,
      gfmFootnoteCall: o1,
      gfmFootnoteDefinitionLabelString: a1,
      gfmFootnoteDefinition: l1
    },
    exit: {
      gfmFootnoteCallString: c1,
      gfmFootnoteCall: u1,
      gfmFootnoteDefinitionLabelString: f1,
      gfmFootnoteDefinition: d1
    }
  };
}
function m1(e) {
  let t = !1;
  return e && e.firstLineBlank && (t = !0), {
    handlers: { footnoteDefinition: n, footnoteReference: nu },
    // This is on by default already.
    unsafe: [{ character: "[", inConstruct: ["label", "phrasing", "reference"] }]
  };
  function n(i, r, o, s) {
    const a = o.createTracker(s);
    let l = a.move("[^");
    const c = o.enter("footnoteDefinition"), u = o.enter("label");
    return l += a.move(
      o.safe(o.associationId(i), { before: l, after: "]" })
    ), u(), l += a.move("]:"), i.children && i.children.length > 0 && (a.shift(4), l += a.move(
      (t ? `
` : " ") + o.indentLines(
        o.containerFlow(i, a.current()),
        t ? iu : g1
      )
    )), c(), l;
  }
}
function g1(e, t, n) {
  return t === 0 ? e : iu(e, t, n);
}
function iu(e, t, n) {
  return (n ? "" : "    ") + e;
}
const y1 = [
  "autolink",
  "destinationLiteral",
  "destinationRaw",
  "reference",
  "titleQuote",
  "titleApostrophe"
];
ws.attention = k1;
ws.peek = T1;
function x1() {
  return {
    canContainEols: ["delete"],
    enter: { strikethrough: v1 },
    exit: { strikethrough: w1 }
  };
}
function b1() {
  return {
    handlers: { delete: ws },
    unsafe: [
      {
        character: "~",
        inConstruct: "phrasing",
        notInConstruct: y1
      }
    ]
  };
}
function v1(e) {
  this.enter({ type: "delete", children: [], position: void 0 }, e);
}
function w1(e) {
  this.exit(e);
}
function ws(e, t, n, i) {
  const r = n.createTracker(i), o = n.stack.includes("strikethrough") ? "~" : "~~", s = n.enter("strikethrough");
  let a = r.move(o);
  return a += n.containerPhrasing(e, {
    ...r.current(),
    before: a,
    after: "~"
  }), a += r.move(o), s(), a;
}
function k1() {
  return { construct: "strikethrough", markers: ["~"], sizes: [2, 1] };
}
function T1() {
  return "~";
}
function S1(e) {
  return e.length;
}
function A1(e, t) {
  const n = t || {}, i = (n.align || []).concat(), r = n.stringLength || S1, o = [], s = [], a = [], l = [];
  let c = 0, u = -1;
  for (; ++u < e.length; ) {
    const g = [], y = [];
    let b = -1;
    for (e[u].length > c && (c = e[u].length); ++b < e[u].length; ) {
      const k = C1(e[u][b]);
      if (n.alignDelimiters !== !1) {
        const x = r(k);
        y[b] = x, (l[b] === void 0 || x > l[b]) && (l[b] = x);
      }
      g.push(k);
    }
    s[u] = g, a[u] = y;
  }
  let f = -1;
  if (typeof i == "object" && "length" in i)
    for (; ++f < c; )
      o[f] = pa(i[f]);
  else {
    const g = pa(i);
    for (; ++f < c; )
      o[f] = g;
  }
  f = -1;
  const h = [], m = [];
  for (; ++f < c; ) {
    const g = o[f];
    let y = "", b = "";
    g === 99 ? (y = ":", b = ":") : g === 108 ? y = ":" : g === 114 && (b = ":");
    let k = n.alignDelimiters === !1 ? 1 : Math.max(
      1,
      l[f] - y.length - b.length
    );
    const x = y + "-".repeat(k) + b;
    n.alignDelimiters !== !1 && (k = y.length + k + b.length, k > l[f] && (l[f] = k), m[f] = k), h[f] = x;
  }
  s.splice(1, 0, h), a.splice(1, 0, m), u = -1;
  const p = [];
  for (; ++u < s.length; ) {
    const g = s[u], y = a[u], b = n.fillRows === !1 ? Math.max(1, s[u === 1 ? 0 : u].length) : c;
    f = -1;
    const k = [];
    for (; ++f < b; ) {
      const x = g[f] || "";
      let S = "", E = "";
      if (n.alignDelimiters !== !1) {
        const C = l[f] - (y[f] || 0), A = o[f];
        if (A === 114)
          S = " ".repeat(C);
        else if (A === 99) {
          const N = C / 2;
          C % 2 ? (S = " ".repeat(N + 0.5), E = " ".repeat(N - 0.5)) : (S = " ".repeat(N), E = S);
        } else
          E = " ".repeat(C);
      }
      n.delimiterStart !== !1 && !f && k.push("|"), n.padding !== !1 && // Don’t add the opening space if we’re not aligning and the cell is
      // empty: there will be a closing space.
      !(n.alignDelimiters === !1 && x === "") && (n.delimiterStart !== !1 || f) && k.push(" "), n.alignDelimiters !== !1 && k.push(S), k.push(x), n.alignDelimiters !== !1 && k.push(E), n.padding !== !1 && k.push(" "), (n.delimiterEnd !== !1 || f !== b - 1) && k.push("|");
    }
    p.push(
      n.delimiterEnd === !1 ? k.join("").replace(/ +$/, "") : k.join("")
    );
  }
  return p.join(`
`);
}
function C1(e) {
  return e == null ? "" : String(e);
}
function pa(e) {
  const t = typeof e == "string" ? e.codePointAt(0) : 0;
  return t === 67 || t === 99 ? 99 : t === 76 || t === 108 ? 108 : t === 82 || t === 114 ? 114 : 0;
}
function N1(e, t, n, i) {
  const r = n.enter("blockquote"), o = n.createTracker(i);
  o.move("> "), o.shift(2);
  const s = n.indentLines(
    n.containerFlow(e, o.current()),
    P1
  );
  return r(), s;
}
function P1(e, t, n) {
  return ">" + (n ? "" : " ") + e;
}
function M1(e, t) {
  return ma(e, t.inConstruct, !0) && !ma(e, t.notInConstruct, !1);
}
function ma(e, t, n) {
  if (typeof t == "string" && (t = [t]), !t || t.length === 0)
    return n;
  let i = -1;
  for (; ++i < t.length; )
    if (e.includes(t[i]))
      return !0;
  return !1;
}
function ga(e, t, n, i) {
  let r = -1;
  for (; ++r < n.unsafe.length; )
    if (n.unsafe[r].character === `
` && M1(n.stack, n.unsafe[r]))
      return /[ \t]/.test(i.before) ? "" : " ";
  return `\\
`;
}
function E1(e, t) {
  const n = String(e);
  let i = n.indexOf(t), r = i, o = 0, s = 0;
  if (typeof t != "string")
    throw new TypeError("Expected substring");
  for (; i !== -1; )
    i === r ? ++o > s && (s = o) : o = 1, r = i + t.length, i = n.indexOf(t, r);
  return s;
}
function D1(e, t) {
  return !!(t.options.fences === !1 && e.value && // If there’s no info…
  !e.lang && // And there’s a non-whitespace character…
  /[^ \r\n]/.test(e.value) && // And the value doesn’t start or end in a blank…
  !/^[\t ]*(?:[\r\n]|$)|(?:^|[\r\n])[\t ]*$/.test(e.value));
}
function R1(e) {
  const t = e.options.fence || "`";
  if (t !== "`" && t !== "~")
    throw new Error(
      "Cannot serialize code with `" + t + "` for `options.fence`, expected `` ` `` or `~`"
    );
  return t;
}
function L1(e, t, n, i) {
  const r = R1(n), o = e.value || "", s = r === "`" ? "GraveAccent" : "Tilde";
  if (D1(e, n)) {
    const f = n.enter("codeIndented"), h = n.indentLines(o, V1);
    return f(), h;
  }
  const a = n.createTracker(i), l = r.repeat(Math.max(E1(o, r) + 1, 3)), c = n.enter("codeFenced");
  let u = a.move(l);
  if (e.lang) {
    const f = n.enter(`codeFencedLang${s}`);
    u += a.move(
      n.safe(e.lang, {
        before: u,
        after: " ",
        encode: ["`"],
        ...a.current()
      })
    ), f();
  }
  if (e.lang && e.meta) {
    const f = n.enter(`codeFencedMeta${s}`);
    u += a.move(" "), u += a.move(
      n.safe(e.meta, {
        before: u,
        after: `
`,
        encode: ["`"],
        ...a.current()
      })
    ), f();
  }
  return u += a.move(`
`), o && (u += a.move(o + `
`)), u += a.move(l), c(), u;
}
function V1(e, t, n) {
  return (n ? "" : "    ") + e;
}
function ks(e) {
  const t = e.options.quote || '"';
  if (t !== '"' && t !== "'")
    throw new Error(
      "Cannot serialize title with `" + t + "` for `options.quote`, expected `\"`, or `'`"
    );
  return t;
}
function F1(e, t, n, i) {
  const r = ks(n), o = r === '"' ? "Quote" : "Apostrophe", s = n.enter("definition");
  let a = n.enter("label");
  const l = n.createTracker(i);
  let c = l.move("[");
  return c += l.move(
    n.safe(n.associationId(e), {
      before: c,
      after: "]",
      ...l.current()
    })
  ), c += l.move("]: "), a(), // If there’s no url, or…
  !e.url || // If there are control characters or whitespace.
  /[\0- \u007F]/.test(e.url) ? (a = n.enter("destinationLiteral"), c += l.move("<"), c += l.move(
    n.safe(e.url, { before: c, after: ">", ...l.current() })
  ), c += l.move(">")) : (a = n.enter("destinationRaw"), c += l.move(
    n.safe(e.url, {
      before: c,
      after: e.title ? " " : `
`,
      ...l.current()
    })
  )), a(), e.title && (a = n.enter(`title${o}`), c += l.move(" " + r), c += l.move(
    n.safe(e.title, {
      before: c,
      after: r,
      ...l.current()
    })
  ), c += l.move(r), a()), s(), c;
}
function I1(e) {
  const t = e.options.emphasis || "*";
  if (t !== "*" && t !== "_")
    throw new Error(
      "Cannot serialize emphasis with `" + t + "` for `options.emphasis`, expected `*`, or `_`"
    );
  return t;
}
function en(e) {
  return "&#x" + e.toString(16).toUpperCase() + ";";
}
function Yn(e) {
  if (e === null || be(e) || at(e))
    return 1;
  if (un(e))
    return 2;
}
function Xn(e, t, n) {
  const i = Yn(e), r = Yn(t);
  return i === void 0 ? r === void 0 ? (
    // Letter inside:
    // we have to encode *both* letters for `_` as it is looser.
    // it already forms for `*` (and GFMs `~`).
    n === "_" ? { inside: !0, outside: !0 } : { inside: !1, outside: !1 }
  ) : r === 1 ? (
    // Whitespace inside: encode both (letter, whitespace).
    { inside: !0, outside: !0 }
  ) : (
    // Punctuation inside: encode outer (letter)
    { inside: !1, outside: !0 }
  ) : i === 1 ? r === void 0 ? (
    // Letter inside: already forms.
    { inside: !1, outside: !1 }
  ) : r === 1 ? (
    // Whitespace inside: encode both (whitespace).
    { inside: !0, outside: !0 }
  ) : (
    // Punctuation inside: already forms.
    { inside: !1, outside: !1 }
  ) : r === void 0 ? (
    // Letter inside: already forms.
    { inside: !1, outside: !1 }
  ) : r === 1 ? (
    // Whitespace inside: encode inner (whitespace).
    { inside: !0, outside: !1 }
  ) : (
    // Punctuation inside: already forms.
    { inside: !1, outside: !1 }
  );
}
ru.peek = O1;
function ru(e, t, n, i) {
  const r = I1(n), o = n.enter("emphasis"), s = n.createTracker(i), a = s.move(r);
  let l = s.move(
    n.containerPhrasing(e, {
      after: r,
      before: a,
      ...s.current()
    })
  );
  const c = l.charCodeAt(0), u = Xn(
    i.before.charCodeAt(i.before.length - 1),
    c,
    r
  );
  u.inside && (l = en(c) + l.slice(1));
  const f = l.charCodeAt(l.length - 1), h = Xn(i.after.charCodeAt(0), f, r);
  h.inside && (l = l.slice(0, -1) + en(f));
  const m = s.move(r);
  return o(), n.attentionEncodeSurroundingInfo = {
    after: h.outside,
    before: u.outside
  }, a + l + m;
}
function O1(e, t, n) {
  return n.options.emphasis || "*";
}
function su(e, t, n, i) {
  let r, o, s;
  typeof t == "function" && typeof n != "function" ? (o = void 0, s = t, r = n) : (o = t, s = n, r = i), tu(e, o, a, r);
  function a(l, c) {
    const u = c[c.length - 1], f = u ? u.children.indexOf(l) : void 0;
    return s(l, f, u);
  }
}
const B1 = {};
function Ts(e, t) {
  const n = B1, i = typeof n.includeImageAlt == "boolean" ? n.includeImageAlt : !0, r = typeof n.includeHtml == "boolean" ? n.includeHtml : !0;
  return ou(e, i, r);
}
function ou(e, t, n) {
  if (j1(e)) {
    if ("value" in e)
      return e.type === "html" && !n ? "" : e.value;
    if (t && "alt" in e && e.alt)
      return e.alt;
    if ("children" in e)
      return ya(e.children, t, n);
  }
  return Array.isArray(e) ? ya(e, t, n) : "";
}
function ya(e, t, n) {
  const i = [];
  let r = -1;
  for (; ++r < e.length; )
    i[r] = ou(e[r], t, n);
  return i.join("");
}
function j1(e) {
  return !!(e && typeof e == "object");
}
function $1(e, t) {
  let n = !1;
  return su(e, function(i) {
    if ("value" in i && /\r?\n|\r/.test(i.value) || i.type === "break")
      return n = !0, Ut;
  }), !!((!e.depth || e.depth < 3) && Ts(e) && (t.options.setext || n));
}
function z1(e, t, n, i) {
  const r = Math.max(Math.min(6, e.depth || 1), 1), o = n.createTracker(i);
  if ($1(e, n)) {
    const u = n.enter("headingSetext"), f = n.enter("phrasing"), h = n.containerPhrasing(e, {
      ...o.current(),
      before: `
`,
      after: `
`
    });
    return f(), u(), h + `
` + (r === 1 ? "=" : "-").repeat(
      // The whole size…
      h.length - // Minus the position of the character after the last EOL (or
      // 0 if there is none)…
      (Math.max(h.lastIndexOf("\r"), h.lastIndexOf(`
`)) + 1)
    );
  }
  const s = "#".repeat(r), a = n.enter("headingAtx"), l = n.enter("phrasing");
  o.move(s + " ");
  let c = n.containerPhrasing(e, {
    before: "# ",
    after: `
`,
    ...o.current()
  });
  return /^[\t ]/.test(c) && (c = en(c.charCodeAt(0)) + c.slice(1)), c = c ? s + " " + c : s, n.options.closeAtx && (c += " " + s), l(), a(), c;
}
au.peek = _1;
function au(e) {
  return e.value || "";
}
function _1() {
  return "<";
}
lu.peek = U1;
function lu(e, t, n, i) {
  const r = ks(n), o = r === '"' ? "Quote" : "Apostrophe", s = n.enter("image");
  let a = n.enter("label");
  const l = n.createTracker(i);
  let c = l.move("![");
  return c += l.move(
    n.safe(e.alt, { before: c, after: "]", ...l.current() })
  ), c += l.move("]("), a(), // If there’s no url but there is a title…
  !e.url && e.title || // If there are control characters or whitespace.
  /[\0- \u007F]/.test(e.url) ? (a = n.enter("destinationLiteral"), c += l.move("<"), c += l.move(
    n.safe(e.url, { before: c, after: ">", ...l.current() })
  ), c += l.move(">")) : (a = n.enter("destinationRaw"), c += l.move(
    n.safe(e.url, {
      before: c,
      after: e.title ? " " : ")",
      ...l.current()
    })
  )), a(), e.title && (a = n.enter(`title${o}`), c += l.move(" " + r), c += l.move(
    n.safe(e.title, {
      before: c,
      after: r,
      ...l.current()
    })
  ), c += l.move(r), a()), c += l.move(")"), s(), c;
}
function U1() {
  return "!";
}
cu.peek = W1;
function cu(e, t, n, i) {
  const r = e.referenceType, o = n.enter("imageReference");
  let s = n.enter("label");
  const a = n.createTracker(i);
  let l = a.move("![");
  const c = n.safe(e.alt, {
    before: l,
    after: "]",
    ...a.current()
  });
  l += a.move(c + "]["), s();
  const u = n.stack;
  n.stack = [], s = n.enter("reference");
  const f = n.safe(n.associationId(e), {
    before: l,
    after: "]",
    ...a.current()
  });
  return s(), n.stack = u, o(), r === "full" || !c || c !== f ? l += a.move(f + "]") : r === "shortcut" ? l = l.slice(0, -1) : l += a.move("]"), l;
}
function W1() {
  return "!";
}
uu.peek = H1;
function uu(e, t, n) {
  let i = e.value || "", r = "`", o = -1;
  for (; new RegExp("(^|[^`])" + r + "([^`]|$)").test(i); )
    r += "`";
  for (/[^ \r\n]/.test(i) && (/^[ \r\n]/.test(i) && /[ \r\n]$/.test(i) || /^`|`$/.test(i)) && (i = " " + i + " "); ++o < n.unsafe.length; ) {
    const s = n.unsafe[o], a = n.compilePattern(s);
    let l;
    if (s.atBreak)
      for (; l = a.exec(i); ) {
        let c = l.index;
        i.charCodeAt(c) === 10 && i.charCodeAt(c - 1) === 13 && c--, i = i.slice(0, c) + " " + i.slice(l.index + 1);
      }
  }
  return r + i + r;
}
function H1() {
  return "`";
}
function fu(e, t) {
  const n = Ts(e);
  return !!(!t.options.resourceLink && // If there’s a url…
  e.url && // And there’s a no title…
  !e.title && // And the content of `node` is a single text node…
  e.children && e.children.length === 1 && e.children[0].type === "text" && // And if the url is the same as the content…
  (n === e.url || "mailto:" + n === e.url) && // And that starts w/ a protocol…
  /^[a-z][a-z+.-]+:/i.test(e.url) && // And that doesn’t contain ASCII control codes (character escapes and
  // references don’t work), space, or angle brackets…
  !/[\0- <>\u007F]/.test(e.url));
}
du.peek = G1;
function du(e, t, n, i) {
  const r = ks(n), o = r === '"' ? "Quote" : "Apostrophe", s = n.createTracker(i);
  let a, l;
  if (fu(e, n)) {
    const u = n.stack;
    n.stack = [], a = n.enter("autolink");
    let f = s.move("<");
    return f += s.move(
      n.containerPhrasing(e, {
        before: f,
        after: ">",
        ...s.current()
      })
    ), f += s.move(">"), a(), n.stack = u, f;
  }
  a = n.enter("link"), l = n.enter("label");
  let c = s.move("[");
  return c += s.move(
    n.containerPhrasing(e, {
      before: c,
      after: "](",
      ...s.current()
    })
  ), c += s.move("]("), l(), // If there’s no url but there is a title…
  !e.url && e.title || // If there are control characters or whitespace.
  /[\0- \u007F]/.test(e.url) ? (l = n.enter("destinationLiteral"), c += s.move("<"), c += s.move(
    n.safe(e.url, { before: c, after: ">", ...s.current() })
  ), c += s.move(">")) : (l = n.enter("destinationRaw"), c += s.move(
    n.safe(e.url, {
      before: c,
      after: e.title ? " " : ")",
      ...s.current()
    })
  )), l(), e.title && (l = n.enter(`title${o}`), c += s.move(" " + r), c += s.move(
    n.safe(e.title, {
      before: c,
      after: r,
      ...s.current()
    })
  ), c += s.move(r), l()), c += s.move(")"), a(), c;
}
function G1(e, t, n) {
  return fu(e, n) ? "<" : "[";
}
hu.peek = K1;
function hu(e, t, n, i) {
  const r = e.referenceType, o = n.enter("linkReference");
  let s = n.enter("label");
  const a = n.createTracker(i);
  let l = a.move("[");
  const c = n.containerPhrasing(e, {
    before: l,
    after: "]",
    ...a.current()
  });
  l += a.move(c + "]["), s();
  const u = n.stack;
  n.stack = [], s = n.enter("reference");
  const f = n.safe(n.associationId(e), {
    before: l,
    after: "]",
    ...a.current()
  });
  return s(), n.stack = u, o(), r === "full" || !c || c !== f ? l += a.move(f + "]") : r === "shortcut" ? l = l.slice(0, -1) : l += a.move("]"), l;
}
function K1() {
  return "[";
}
function Ss(e) {
  const t = e.options.bullet || "*";
  if (t !== "*" && t !== "+" && t !== "-")
    throw new Error(
      "Cannot serialize items with `" + t + "` for `options.bullet`, expected `*`, `+`, or `-`"
    );
  return t;
}
function q1(e) {
  const t = Ss(e), n = e.options.bulletOther;
  if (!n)
    return t === "*" ? "-" : "*";
  if (n !== "*" && n !== "+" && n !== "-")
    throw new Error(
      "Cannot serialize items with `" + n + "` for `options.bulletOther`, expected `*`, `+`, or `-`"
    );
  if (n === t)
    throw new Error(
      "Expected `bullet` (`" + t + "`) and `bulletOther` (`" + n + "`) to be different"
    );
  return n;
}
function Y1(e) {
  const t = e.options.bulletOrdered || ".";
  if (t !== "." && t !== ")")
    throw new Error(
      "Cannot serialize items with `" + t + "` for `options.bulletOrdered`, expected `.` or `)`"
    );
  return t;
}
function pu(e) {
  const t = e.options.rule || "*";
  if (t !== "*" && t !== "-" && t !== "_")
    throw new Error(
      "Cannot serialize rules with `" + t + "` for `options.rule`, expected `*`, `-`, or `_`"
    );
  return t;
}
function X1(e, t, n, i) {
  const r = n.enter("list"), o = n.bulletCurrent;
  let s = e.ordered ? Y1(n) : Ss(n);
  const a = e.ordered ? s === "." ? ")" : "." : q1(n);
  let l = t && n.bulletLastUsed ? s === n.bulletLastUsed : !1;
  if (!e.ordered) {
    const u = e.children ? e.children[0] : void 0;
    if (
      // Bullet could be used as a thematic break marker:
      (s === "*" || s === "-") && // Empty first list item:
      u && (!u.children || !u.children[0]) && // Directly in two other list items:
      n.stack[n.stack.length - 1] === "list" && n.stack[n.stack.length - 2] === "listItem" && n.stack[n.stack.length - 3] === "list" && n.stack[n.stack.length - 4] === "listItem" && // That are each the first child.
      n.indexStack[n.indexStack.length - 1] === 0 && n.indexStack[n.indexStack.length - 2] === 0 && n.indexStack[n.indexStack.length - 3] === 0 && (l = !0), pu(n) === s && u
    ) {
      let f = -1;
      for (; ++f < e.children.length; ) {
        const h = e.children[f];
        if (h && h.type === "listItem" && h.children && h.children[0] && h.children[0].type === "thematicBreak") {
          l = !0;
          break;
        }
      }
    }
  }
  l && (s = a), n.bulletCurrent = s;
  const c = n.containerFlow(e, i);
  return n.bulletLastUsed = s, n.bulletCurrent = o, r(), c;
}
function Q1(e) {
  const t = e.options.listItemIndent || "one";
  if (t !== "tab" && t !== "one" && t !== "mixed")
    throw new Error(
      "Cannot serialize items with `" + t + "` for `options.listItemIndent`, expected `tab`, `one`, or `mixed`"
    );
  return t;
}
function Z1(e, t, n, i) {
  const r = Q1(n);
  let o = n.bulletCurrent || Ss(n);
  t && t.type === "list" && t.ordered && (o = (typeof t.start == "number" && t.start > -1 ? t.start : 1) + (n.options.incrementListMarker === !1 ? 0 : t.children.indexOf(e)) + o);
  let s = o.length + 1;
  (r === "tab" || r === "mixed" && (t && t.type === "list" && t.spread || e.spread)) && (s = Math.ceil(s / 4) * 4);
  const a = n.createTracker(i);
  a.move(o + " ".repeat(s - o.length)), a.shift(s);
  const l = n.enter("listItem"), c = n.indentLines(
    n.containerFlow(e, a.current()),
    u
  );
  return l(), c;
  function u(f, h, m) {
    return h ? (m ? "" : " ".repeat(s)) + f : (m ? o : o + " ".repeat(s - o.length)) + f;
  }
}
function J1(e, t, n, i) {
  const r = n.enter("paragraph"), o = n.enter("phrasing"), s = n.containerPhrasing(e, i);
  return o(), r(), s;
}
const ey = (
  /** @type {(node?: unknown) => node is Exclude<PhrasingContent, Html>} */
  oi([
    "break",
    "delete",
    "emphasis",
    // To do: next major: removed since footnotes were added to GFM.
    "footnote",
    "footnoteReference",
    "image",
    "imageReference",
    "inlineCode",
    // Enabled by `mdast-util-math`:
    "inlineMath",
    "link",
    "linkReference",
    // Enabled by `mdast-util-mdx`:
    "mdxJsxTextElement",
    // Enabled by `mdast-util-mdx`:
    "mdxTextExpression",
    "strong",
    "text",
    // Enabled by `mdast-util-directive`:
    "textDirective"
  ])
);
function ty(e, t, n, i) {
  return (e.children.some(function(s) {
    return ey(s);
  }) ? n.containerPhrasing : n.containerFlow).call(n, e, i);
}
function ny(e) {
  const t = e.options.strong || "*";
  if (t !== "*" && t !== "_")
    throw new Error(
      "Cannot serialize strong with `" + t + "` for `options.strong`, expected `*`, or `_`"
    );
  return t;
}
mu.peek = iy;
function mu(e, t, n, i) {
  const r = ny(n), o = n.enter("strong"), s = n.createTracker(i), a = s.move(r + r);
  let l = s.move(
    n.containerPhrasing(e, {
      after: r,
      before: a,
      ...s.current()
    })
  );
  const c = l.charCodeAt(0), u = Xn(
    i.before.charCodeAt(i.before.length - 1),
    c,
    r
  );
  u.inside && (l = en(c) + l.slice(1));
  const f = l.charCodeAt(l.length - 1), h = Xn(i.after.charCodeAt(0), f, r);
  h.inside && (l = l.slice(0, -1) + en(f));
  const m = s.move(r + r);
  return o(), n.attentionEncodeSurroundingInfo = {
    after: h.outside,
    before: u.outside
  }, a + l + m;
}
function iy(e, t, n) {
  return n.options.strong || "*";
}
function ry(e, t, n, i) {
  return n.safe(e.value, i);
}
function sy(e) {
  const t = e.options.ruleRepetition || 3;
  if (t < 3)
    throw new Error(
      "Cannot serialize rules with repetition `" + t + "` for `options.ruleRepetition`, expected `3` or more"
    );
  return t;
}
function oy(e, t, n) {
  const i = (pu(n) + (n.options.ruleSpaces ? " " : "")).repeat(sy(n));
  return n.options.ruleSpaces ? i.slice(0, -1) : i;
}
const mr = {
  blockquote: N1,
  break: ga,
  code: L1,
  definition: F1,
  emphasis: ru,
  hardBreak: ga,
  heading: z1,
  html: au,
  image: lu,
  imageReference: cu,
  inlineCode: uu,
  link: du,
  linkReference: hu,
  list: X1,
  listItem: Z1,
  paragraph: J1,
  root: ty,
  strong: mu,
  text: ry,
  thematicBreak: oy
};
function ay() {
  return {
    enter: {
      table: ly,
      tableData: xa,
      tableHeader: xa,
      tableRow: uy
    },
    exit: {
      codeText: fy,
      table: cy,
      tableData: Vi,
      tableHeader: Vi,
      tableRow: Vi
    }
  };
}
function ly(e) {
  const t = e._align;
  this.enter(
    {
      type: "table",
      align: t.map(function(n) {
        return n === "none" ? null : n;
      }),
      children: [],
      position: void 0
    },
    e
  ), this.data.inTable = !0;
}
function cy(e) {
  this.exit(e), this.data.inTable = void 0;
}
function uy(e) {
  this.enter({ type: "tableRow", children: [], position: void 0 }, e);
}
function Vi(e) {
  this.exit(e);
}
function xa(e) {
  this.enter({ type: "tableCell", children: [], position: void 0 }, e);
}
function fy(e) {
  let t = this.resume();
  this.data.inTable && (t = t.replace(/\\([\\|])/g, dy));
  const n = this.stack[this.stack.length - 1];
  n.type, n.value = t, this.exit(e);
}
function dy(e, t) {
  return t === "|" ? t : e;
}
function hy(e) {
  const t = e || {}, {
    tableCellPadding: n,
    tablePipeAlign: i,
    stringLength: r
  } = t, o = n ? " " : "|";
  return {
    handlers: {
      inlineCode: h,
      table: s,
      tableCell: l,
      tableRow: a
    },
    join: [py],
    unsafe: [
      { character: "\r", inConstruct: "tableCell" },
      { character: `
`, inConstruct: "tableCell" },
      // A pipe, when followed by a tab or space (padding), or a dash or colon
      // (unpadded delimiter row), could result in a table.
      { atBreak: !0, character: "|", after: "[	 :-]" },
      // A pipe in a cell must be encoded.
      { character: "|", inConstruct: "tableCell" },
      // A colon must be followed by a dash, in which case it could start a
      // delimiter row.
      { atBreak: !0, character: ":", after: "-" },
      // A delimiter row can also start with a dash, when followed by more
      // dashes, a colon, or a pipe.
      // This is a stricter version than the built in check for lists, thematic
      // breaks, and setex heading underlines though:
      // <https://github.com/syntax-tree/mdast-util-to-markdown/blob/51a2038/lib/unsafe.js#L57>
      { atBreak: !0, character: "-", after: "[:|-]" }
    ]
  };
  function s(m, p, g, y) {
    const b = u(m, g, y), k = b[0];
    if (k) {
      let x = m.align ? m.align.length : 0, S = -1;
      if (!x)
        for (; ++S < b.length; )
          b[S].length > x && (x = b[S].length);
      for (; k.length < x; ) k.push("");
    }
    return c(b, m.align);
  }
  function a(m, p, g, y) {
    const b = f(m, g, y), k = c([b]);
    return k.slice(0, k.indexOf(`
`));
  }
  function l(m, p, g, y) {
    const b = g.enter("tableCell"), k = g.enter("phrasing"), x = g.containerPhrasing(m, {
      ...y,
      before: o,
      after: o
    });
    return k(), b(), x;
  }
  function c(m, p) {
    return A1(m, {
      align: p,
      alignDelimiters: i,
      fillRows: !1,
      padding: n,
      stringLength: r
    });
  }
  function u(m, p, g) {
    const { children: y } = m;
    let b = -1;
    const k = [], x = p.enter("table");
    for (; ++b < y.length; )
      k[b] = f(y[b], p, g);
    return x(), k;
  }
  function f(m, p, g) {
    const { children: y } = m;
    let b = -1;
    const k = [], x = p.enter("tableRow");
    for (; ++b < y.length; )
      k[b] = l(y[b], m, p, g);
    return x(), k;
  }
  function h(m, p, g) {
    const y = mr.inlineCode(m, p, g);
    if (!g.stack.includes("tableCell")) return y;
    const b = [];
    let k = 0, x = y.indexOf("|");
    for (; x !== -1; ) {
      let S = x;
      for (; S > k && y.charCodeAt(S - 1) === 92; )
        S--;
      b.push(y.slice(k, x)), (x - S) % 2 === 0 && b.push("\\"), k = x, x = y.indexOf("|", x + 1);
    }
    return b.push(y.slice(k)), b.join("");
  }
}
function py(e, t, n, i) {
  if (e.type === "table" && n.type === "listItem" && n.spread === !1 && (t.type === "definition" || t.type === "heading" && my(t, i) || t.type === "paragraph" || t.type === "table"))
    return 1;
}
function my(e, t) {
  let n = !1;
  return su(e, function(i) {
    if (i.type === "break" || "value" in i && /\r?\n|\r/.test(i.value))
      return n = !0, Ut;
  }), !!((!e.depth || e.depth < 3) && Ts(e) && (t.options.setext || n));
}
function gy() {
  return {
    exit: {
      taskListCheckValueChecked: ba,
      taskListCheckValueUnchecked: ba,
      paragraph: xy
    }
  };
}
function yy() {
  return {
    handlers: { paragraph: by },
    join: [vy]
  };
}
function ba(e) {
  const t = this.stack[this.stack.length - 2];
  t.type, t.checked = e.type === "taskListCheckValueChecked";
}
function xy(e) {
  const t = this.stack[this.stack.length - 2];
  if (t && t.type === "listItem" && typeof t.checked == "boolean") {
    const n = this.stack[this.stack.length - 1];
    n.type;
    const i = n.children[0];
    if (i && i.type === "text") {
      const r = t.children;
      let o = -1, s;
      for (; ++o < r.length; ) {
        const a = r[o];
        if (a.type === "paragraph") {
          s = a;
          break;
        }
      }
      s === n && (i.value = i.value.slice(1), i.value.length === 0 ? n.children.shift() : n.position && i.position && typeof i.position.start.offset == "number" && (i.position.start.column++, i.position.start.offset++, n.position.start = { ...i.position.start }));
    }
  }
  this.exit(e);
}
function by(e, t, n, i) {
  if (!t || t.type !== "listItem" || gu(t) !== e)
    return mr.paragraph(e, t, n, i);
  const r = "[" + (t.checked ? "x" : " ") + "] ", o = n.createTracker(i);
  o.move(r);
  const s = mr.paragraph(
    e.children.length > 0 ? e : { type: "paragraph", children: [{ type: "text", value: " " }] },
    t,
    n,
    { ...i, ...o.current() }
  );
  return r + s;
}
function vy(e, t, n) {
  if (!(e.type === "definition" && n.type === "listItem"))
    return;
  const i = gu(n);
  if (i && n.children.indexOf(e) < n.children.indexOf(i))
    return 0;
}
function gu(e) {
  if (typeof e.checked == "boolean")
    for (const t of e.children) {
      if (t.type === "paragraph")
        return t;
      if (t.type !== "definition")
        return;
    }
}
function wy() {
  return [
    W0(),
    p1(),
    x1(),
    ay(),
    gy()
  ];
}
function ky(e) {
  return {
    extensions: [
      H0(),
      m1(e),
      b1(),
      hy(e),
      yy()
    ]
  };
}
function Ln(e, t, n, i) {
  const r = e.length;
  let o = 0, s;
  if (t < 0 ? t = -t > r ? 0 : r + t : t = t > r ? r : t, n = n > 0 ? n : 0, i.length < 1e4)
    s = Array.from(i), s.unshift(t, n), e.splice(...s);
  else
    for (n && e.splice(t, n); o < i.length; )
      s = i.slice(o, o + 1e4), s.unshift(t, 0), e.splice(...s), o += 1e4, t += 1e4;
}
const va = {}.hasOwnProperty;
function Ty(e) {
  const t = {};
  let n = -1;
  for (; ++n < e.length; )
    Sy(t, e[n]);
  return t;
}
function Sy(e, t) {
  let n;
  for (n in t) {
    const r = (va.call(e, n) ? e[n] : void 0) || (e[n] = {}), o = t[n];
    let s;
    if (o)
      for (s in o) {
        va.call(r, s) || (r[s] = []);
        const a = o[s];
        Ay(
          // @ts-expect-error Looks like a list.
          r[s],
          Array.isArray(a) ? a : a ? [a] : []
        );
      }
  }
}
function Ay(e, t) {
  let n = -1;
  const i = [];
  for (; ++n < t.length; )
    (t[n].add === "after" ? e : i).push(t[n]);
  Ln(e, 0, 0, i);
}
const Cy = {
  tokenize: Ry,
  partial: !0
}, yu = {
  tokenize: Ly,
  partial: !0
}, xu = {
  tokenize: Vy,
  partial: !0
}, bu = {
  tokenize: Fy,
  partial: !0
}, Ny = {
  tokenize: Iy,
  partial: !0
}, vu = {
  name: "wwwAutolink",
  tokenize: Ey,
  previous: ku
}, wu = {
  name: "protocolAutolink",
  tokenize: Dy,
  previous: Tu
}, He = {
  name: "emailAutolink",
  tokenize: My,
  previous: Su
}, Fe = {};
function Py() {
  return {
    text: Fe
  };
}
let Ze = 48;
for (; Ze < 123; )
  Fe[Ze] = He, Ze++, Ze === 58 ? Ze = 65 : Ze === 91 && (Ze = 97);
Fe[43] = He;
Fe[45] = He;
Fe[46] = He;
Fe[95] = He;
Fe[72] = [He, wu];
Fe[104] = [He, wu];
Fe[87] = [He, vu];
Fe[119] = [He, vu];
function My(e, t, n) {
  const i = this;
  let r, o;
  return s;
  function s(f) {
    return !gr(f) || !Su.call(i, i.previous) || As(i.events) ? n(f) : (e.enter("literalAutolink"), e.enter("literalAutolinkEmail"), a(f));
  }
  function a(f) {
    return gr(f) ? (e.consume(f), a) : f === 64 ? (e.consume(f), l) : n(f);
  }
  function l(f) {
    return f === 46 ? e.check(Ny, u, c)(f) : f === 45 || f === 95 || vs(f) ? (o = !0, e.consume(f), l) : u(f);
  }
  function c(f) {
    return e.consume(f), r = !0, l;
  }
  function u(f) {
    return o && r && Jt(i.previous) ? (e.exit("literalAutolinkEmail"), e.exit("literalAutolink"), t(f)) : n(f);
  }
}
function Ey(e, t, n) {
  const i = this;
  return r;
  function r(s) {
    return s !== 87 && s !== 119 || !ku.call(i, i.previous) || As(i.events) ? n(s) : (e.enter("literalAutolink"), e.enter("literalAutolinkWww"), e.check(Cy, e.attempt(yu, e.attempt(xu, o), n), n)(s));
  }
  function o(s) {
    return e.exit("literalAutolinkWww"), e.exit("literalAutolink"), t(s);
  }
}
function Dy(e, t, n) {
  const i = this;
  let r = "", o = !1;
  return s;
  function s(f) {
    return (f === 72 || f === 104) && Tu.call(i, i.previous) && !As(i.events) ? (e.enter("literalAutolink"), e.enter("literalAutolinkHttp"), r += String.fromCodePoint(f), e.consume(f), a) : n(f);
  }
  function a(f) {
    if (Jt(f) && r.length < 5)
      return r += String.fromCodePoint(f), e.consume(f), a;
    if (f === 58) {
      const h = r.toLowerCase();
      if (h === "http" || h === "https")
        return e.consume(f), l;
    }
    return n(f);
  }
  function l(f) {
    return f === 47 ? (e.consume(f), o ? c : (o = !0, l)) : n(f);
  }
  function c(f) {
    return f === null || R0(f) || be(f) || at(f) || un(f) ? n(f) : e.attempt(yu, e.attempt(xu, u), n)(f);
  }
  function u(f) {
    return e.exit("literalAutolinkHttp"), e.exit("literalAutolink"), t(f);
  }
}
function Ry(e, t, n) {
  let i = 0;
  return r;
  function r(s) {
    return (s === 87 || s === 119) && i < 3 ? (i++, e.consume(s), r) : s === 46 && i === 3 ? (e.consume(s), o) : n(s);
  }
  function o(s) {
    return s === null ? n(s) : t(s);
  }
}
function Ly(e, t, n) {
  let i, r, o;
  return s;
  function s(c) {
    return c === 46 || c === 95 ? e.check(bu, l, a)(c) : c === null || be(c) || at(c) || c !== 45 && un(c) ? l(c) : (o = !0, e.consume(c), s);
  }
  function a(c) {
    return c === 95 ? i = !0 : (r = i, i = void 0), e.consume(c), s;
  }
  function l(c) {
    return r || i || !o ? n(c) : t(c);
  }
}
function Vy(e, t) {
  let n = 0, i = 0;
  return r;
  function r(s) {
    return s === 40 ? (n++, e.consume(s), r) : s === 41 && i < n ? o(s) : s === 33 || s === 34 || s === 38 || s === 39 || s === 41 || s === 42 || s === 44 || s === 46 || s === 58 || s === 59 || s === 60 || s === 63 || s === 93 || s === 95 || s === 126 ? e.check(bu, t, o)(s) : s === null || be(s) || at(s) ? t(s) : (e.consume(s), r);
  }
  function o(s) {
    return s === 41 && i++, e.consume(s), r;
  }
}
function Fy(e, t, n) {
  return i;
  function i(a) {
    return a === 33 || a === 34 || a === 39 || a === 41 || a === 42 || a === 44 || a === 46 || a === 58 || a === 59 || a === 63 || a === 95 || a === 126 ? (e.consume(a), i) : a === 38 ? (e.consume(a), o) : a === 93 ? (e.consume(a), r) : (
      // `<` is an end.
      a === 60 || // So is whitespace.
      a === null || be(a) || at(a) ? t(a) : n(a)
    );
  }
  function r(a) {
    return a === null || a === 40 || a === 91 || be(a) || at(a) ? t(a) : i(a);
  }
  function o(a) {
    return Jt(a) ? s(a) : n(a);
  }
  function s(a) {
    return a === 59 ? (e.consume(a), i) : Jt(a) ? (e.consume(a), s) : n(a);
  }
}
function Iy(e, t, n) {
  return i;
  function i(o) {
    return e.consume(o), r;
  }
  function r(o) {
    return vs(o) ? n(o) : t(o);
  }
}
function ku(e) {
  return e === null || e === 40 || e === 42 || e === 95 || e === 91 || e === 93 || e === 126 || be(e);
}
function Tu(e) {
  return !Jt(e);
}
function Su(e) {
  return !(e === 47 || gr(e));
}
function gr(e) {
  return e === 43 || e === 45 || e === 46 || e === 95 || vs(e);
}
function As(e) {
  let t = e.length, n = !1;
  for (; t--; ) {
    const i = e[t][1];
    if ((i.type === "labelLink" || i.type === "labelImage") && !i._balanced) {
      n = !0;
      break;
    }
    if (i._gfmAutolinkLiteralWalkedInto) {
      n = !1;
      break;
    }
  }
  return e.length > 0 && !n && (e[e.length - 1][1]._gfmAutolinkLiteralWalkedInto = !0), n;
}
function Oy(e, t, n) {
  const i = [];
  let r = -1;
  for (; ++r < e.length; ) {
    const o = e[r].resolveAll;
    o && !i.includes(o) && (t = o(t, n), i.push(o));
  }
  return t;
}
function Be(e, t, n, i) {
  const r = i ? i - 1 : Number.POSITIVE_INFINITY;
  let o = 0;
  return s;
  function s(l) {
    return Oe(l) ? (e.enter(n), a(l)) : t(l);
  }
  function a(l) {
    return Oe(l) && o++ < r ? (e.consume(l), a) : (e.exit(n), t(l));
  }
}
const By = {
  partial: !0,
  tokenize: jy
};
function jy(e, t, n) {
  return i;
  function i(o) {
    return Oe(o) ? Be(e, r, "linePrefix")(o) : r(o);
  }
  function r(o) {
    return o === null || vt(o) ? t(o) : n(o);
  }
}
const $y = {
  tokenize: qy,
  partial: !0
};
function zy() {
  return {
    document: {
      91: {
        name: "gfmFootnoteDefinition",
        tokenize: Hy,
        continuation: {
          tokenize: Gy
        },
        exit: Ky
      }
    },
    text: {
      91: {
        name: "gfmFootnoteCall",
        tokenize: Wy
      },
      93: {
        name: "gfmPotentialFootnoteCall",
        add: "after",
        tokenize: _y,
        resolveTo: Uy
      }
    }
  };
}
function _y(e, t, n) {
  const i = this;
  let r = i.events.length;
  const o = i.parser.gfmFootnotes || (i.parser.gfmFootnotes = []);
  let s;
  for (; r--; ) {
    const l = i.events[r][1];
    if (l.type === "labelImage") {
      s = l;
      break;
    }
    if (l.type === "gfmFootnoteCall" || l.type === "labelLink" || l.type === "label" || l.type === "image" || l.type === "link")
      break;
  }
  return a;
  function a(l) {
    if (!s || !s._balanced)
      return n(l);
    const c = fn(i.sliceSerialize({
      start: s.end,
      end: i.now()
    }));
    return c.codePointAt(0) !== 94 || !o.includes(c.slice(1)) ? n(l) : (e.enter("gfmFootnoteCallLabelMarker"), e.consume(l), e.exit("gfmFootnoteCallLabelMarker"), t(l));
  }
}
function Uy(e, t) {
  let n = e.length;
  for (; n--; )
    if (e[n][1].type === "labelImage" && e[n][0] === "enter") {
      e[n][1];
      break;
    }
  e[n + 1][1].type = "data", e[n + 3][1].type = "gfmFootnoteCallLabelMarker";
  const i = {
    type: "gfmFootnoteCall",
    start: Object.assign({}, e[n + 3][1].start),
    end: Object.assign({}, e[e.length - 1][1].end)
  }, r = {
    type: "gfmFootnoteCallMarker",
    start: Object.assign({}, e[n + 3][1].end),
    end: Object.assign({}, e[n + 3][1].end)
  };
  r.end.column++, r.end.offset++, r.end._bufferIndex++;
  const o = {
    type: "gfmFootnoteCallString",
    start: Object.assign({}, r.end),
    end: Object.assign({}, e[e.length - 1][1].start)
  }, s = {
    type: "chunkString",
    contentType: "string",
    start: Object.assign({}, o.start),
    end: Object.assign({}, o.end)
  }, a = [
    // Take the `labelImageMarker` (now `data`, the `!`)
    e[n + 1],
    e[n + 2],
    ["enter", i, t],
    // The `[`
    e[n + 3],
    e[n + 4],
    // The `^`.
    ["enter", r, t],
    ["exit", r, t],
    // Everything in between.
    ["enter", o, t],
    ["enter", s, t],
    ["exit", s, t],
    ["exit", o, t],
    // The ending (`]`, properly parsed and labelled).
    e[e.length - 2],
    e[e.length - 1],
    ["exit", i, t]
  ];
  return e.splice(n, e.length - n + 1, ...a), e;
}
function Wy(e, t, n) {
  const i = this, r = i.parser.gfmFootnotes || (i.parser.gfmFootnotes = []);
  let o = 0, s;
  return a;
  function a(f) {
    return e.enter("gfmFootnoteCall"), e.enter("gfmFootnoteCallLabelMarker"), e.consume(f), e.exit("gfmFootnoteCallLabelMarker"), l;
  }
  function l(f) {
    return f !== 94 ? n(f) : (e.enter("gfmFootnoteCallMarker"), e.consume(f), e.exit("gfmFootnoteCallMarker"), e.enter("gfmFootnoteCallString"), e.enter("chunkString").contentType = "string", c);
  }
  function c(f) {
    if (
      // Too long.
      o > 999 || // Closing brace with nothing.
      f === 93 && !s || // Space or tab is not supported by GFM for some reason.
      // `\n` and `[` not being supported makes sense.
      f === null || f === 91 || be(f)
    )
      return n(f);
    if (f === 93) {
      e.exit("chunkString");
      const h = e.exit("gfmFootnoteCallString");
      return r.includes(fn(i.sliceSerialize(h))) ? (e.enter("gfmFootnoteCallLabelMarker"), e.consume(f), e.exit("gfmFootnoteCallLabelMarker"), e.exit("gfmFootnoteCall"), t) : n(f);
    }
    return be(f) || (s = !0), o++, e.consume(f), f === 92 ? u : c;
  }
  function u(f) {
    return f === 91 || f === 92 || f === 93 ? (e.consume(f), o++, c) : c(f);
  }
}
function Hy(e, t, n) {
  const i = this, r = i.parser.gfmFootnotes || (i.parser.gfmFootnotes = []);
  let o, s = 0, a;
  return l;
  function l(p) {
    return e.enter("gfmFootnoteDefinition")._container = !0, e.enter("gfmFootnoteDefinitionLabel"), e.enter("gfmFootnoteDefinitionLabelMarker"), e.consume(p), e.exit("gfmFootnoteDefinitionLabelMarker"), c;
  }
  function c(p) {
    return p === 94 ? (e.enter("gfmFootnoteDefinitionMarker"), e.consume(p), e.exit("gfmFootnoteDefinitionMarker"), e.enter("gfmFootnoteDefinitionLabelString"), e.enter("chunkString").contentType = "string", u) : n(p);
  }
  function u(p) {
    if (
      // Too long.
      s > 999 || // Closing brace with nothing.
      p === 93 && !a || // Space or tab is not supported by GFM for some reason.
      // `\n` and `[` not being supported makes sense.
      p === null || p === 91 || be(p)
    )
      return n(p);
    if (p === 93) {
      e.exit("chunkString");
      const g = e.exit("gfmFootnoteDefinitionLabelString");
      return o = fn(i.sliceSerialize(g)), e.enter("gfmFootnoteDefinitionLabelMarker"), e.consume(p), e.exit("gfmFootnoteDefinitionLabelMarker"), e.exit("gfmFootnoteDefinitionLabel"), h;
    }
    return be(p) || (a = !0), s++, e.consume(p), p === 92 ? f : u;
  }
  function f(p) {
    return p === 91 || p === 92 || p === 93 ? (e.consume(p), s++, u) : u(p);
  }
  function h(p) {
    return p === 58 ? (e.enter("definitionMarker"), e.consume(p), e.exit("definitionMarker"), r.includes(o) || r.push(o), Be(e, m, "gfmFootnoteDefinitionWhitespace")) : n(p);
  }
  function m(p) {
    return t(p);
  }
}
function Gy(e, t, n) {
  return e.check(By, t, e.attempt($y, t, n));
}
function Ky(e) {
  e.exit("gfmFootnoteDefinition");
}
function qy(e, t, n) {
  const i = this;
  return Be(e, r, "gfmFootnoteDefinitionIndent", 5);
  function r(o) {
    const s = i.events[i.events.length - 1];
    return s && s[1].type === "gfmFootnoteDefinitionIndent" && s[2].sliceSerialize(s[1], !0).length === 4 ? t(o) : n(o);
  }
}
function Yy(e) {
  let n = (e || {}).singleTilde;
  const i = {
    name: "strikethrough",
    tokenize: o,
    resolveAll: r
  };
  return n == null && (n = !0), {
    text: {
      126: i
    },
    insideSpan: {
      null: [i]
    },
    attentionMarkers: {
      null: [126]
    }
  };
  function r(s, a) {
    let l = -1;
    for (; ++l < s.length; )
      if (s[l][0] === "enter" && s[l][1].type === "strikethroughSequenceTemporary" && s[l][1]._close) {
        let c = l;
        for (; c--; )
          if (s[c][0] === "exit" && s[c][1].type === "strikethroughSequenceTemporary" && s[c][1]._open && // If the sizes are the same:
          s[l][1].end.offset - s[l][1].start.offset === s[c][1].end.offset - s[c][1].start.offset) {
            s[l][1].type = "strikethroughSequence", s[c][1].type = "strikethroughSequence";
            const u = {
              type: "strikethrough",
              start: Object.assign({}, s[c][1].start),
              end: Object.assign({}, s[l][1].end)
            }, f = {
              type: "strikethroughText",
              start: Object.assign({}, s[c][1].end),
              end: Object.assign({}, s[l][1].start)
            }, h = [["enter", u, a], ["enter", s[c][1], a], ["exit", s[c][1], a], ["enter", f, a]], m = a.parser.constructs.insideSpan.null;
            m && Ln(h, h.length, 0, Oy(m, s.slice(c + 1, l), a)), Ln(h, h.length, 0, [["exit", f, a], ["enter", s[l][1], a], ["exit", s[l][1], a], ["exit", u, a]]), Ln(s, c - 1, l - c + 3, h), l = c + h.length - 2;
            break;
          }
      }
    for (l = -1; ++l < s.length; )
      s[l][1].type === "strikethroughSequenceTemporary" && (s[l][1].type = "data");
    return s;
  }
  function o(s, a, l) {
    const c = this.previous, u = this.events;
    let f = 0;
    return h;
    function h(p) {
      return c === 126 && u[u.length - 1][1].type !== "characterEscape" ? l(p) : (s.enter("strikethroughSequenceTemporary"), m(p));
    }
    function m(p) {
      const g = Yn(c);
      if (p === 126)
        return f > 1 ? l(p) : (s.consume(p), f++, m);
      if (f < 2 && !n) return l(p);
      const y = s.exit("strikethroughSequenceTemporary"), b = Yn(p);
      return y._open = !b || b === 2 && !!g, y._close = !g || g === 2 && !!b, a(p);
    }
  }
}
class Xy {
  /**
   * Create a new edit map.
   */
  constructor() {
    this.map = [], this.index = /* @__PURE__ */ new Map();
  }
  /**
   * Create an edit: a remove and/or add at a certain place.
   *
   * @param {number} index
   *   Index at which to apply the edit.
   * @param {number} remove
   *   Count of items to remove at the index.
   * @param {Array<Event>} add
   *   Items to add at the index.
   * @returns {undefined}
   *   Nothing.
   */
  add(t, n, i) {
    Qy(this, t, n, i);
  }
  // To do: add this when moving to `micromark`.
  // /**
  //  * Create an edit: but insert `add` before existing additions.
  //  *
  //  * @param {number} index
  //  * @param {number} remove
  //  * @param {Array<Event>} add
  //  * @returns {undefined}
  //  */
  // addBefore(index, remove, add) {
  //   addImplementation(this, index, remove, add, true)
  // }
  /**
   * Done, change the events.
   *
   * @param {Array<Event>} events
   *   List of events to apply the edits to.
   * @returns {undefined}
   *   Nothing.
   */
  consume(t) {
    if (this.map.sort(function(o, s) {
      return o[0] - s[0];
    }), this.map.length === 0)
      return;
    let n = this.map.length;
    const i = [];
    for (; n > 0; )
      n -= 1, i.push(t.slice(this.map[n][0] + this.map[n][1]), this.map[n][2]), t.length = this.map[n][0];
    i.push(t.slice()), t.length = 0;
    let r = i.pop();
    for (; r; ) {
      for (const o of r)
        t.push(o);
      r = i.pop();
    }
    this.map.length = 0, this.index.clear();
  }
}
function Qy(e, t, n, i) {
  if (n === 0 && i.length === 0)
    return;
  const r = e.index.get(t);
  if (r) {
    r[1] += n, r[2].push(...i);
    return;
  }
  const o = [t, n, i];
  e.map.push(o), e.index.set(t, o);
}
function Zy(e, t) {
  let n = !1;
  const i = [];
  for (; t < e.length; ) {
    const r = e[t];
    if (n) {
      if (r[0] === "enter")
        r[1].type === "tableContent" && i.push(e[t + 1][1].type === "tableDelimiterMarker" ? "left" : "none");
      else if (r[1].type === "tableContent") {
        if (e[t - 1][1].type === "tableDelimiterMarker") {
          const o = i.length - 1;
          i[o] = i[o] === "left" ? "center" : "right";
        }
      } else if (r[1].type === "tableDelimiterRow")
        break;
    } else r[0] === "enter" && r[1].type === "tableDelimiterRow" && (n = !0);
    t += 1;
  }
  return i;
}
function Jy() {
  return {
    flow: {
      null: {
        name: "table",
        tokenize: ex,
        resolveAll: tx
      }
    }
  };
}
function ex(e, t, n) {
  const i = this;
  let r = 0, o = 0, s;
  return a;
  function a(w) {
    let T = i.events.length - 1;
    for (; T > -1; ) {
      const {
        type: X
      } = i.events[T][1];
      if (X === "lineEnding" || // Note: markdown-rs uses `whitespace` instead of `linePrefix`
      X === "linePrefix")
        T--;
      else
        break;
    }
    const I = T > -1 ? i.events[T][1].type : null, F = I === "tableHead" || I === "tableRow" ? C : l;
    return F === C && i.parser.lazy[i.now().line] ? n(w) : F(w);
  }
  function l(w) {
    return e.enter("tableHead"), e.enter("tableRow"), c(w);
  }
  function c(w) {
    return w === 124 || (s = !0, o += 1), u(w);
  }
  function u(w) {
    return w === null ? n(w) : vt(w) ? o > 1 ? (o = 0, i.interrupt = !0, e.exit("tableRow"), e.enter("lineEnding"), e.consume(w), e.exit("lineEnding"), m) : n(w) : Oe(w) ? Be(e, u, "whitespace")(w) : (o += 1, s && (s = !1, r += 1), w === 124 ? (e.enter("tableCellDivider"), e.consume(w), e.exit("tableCellDivider"), s = !0, u) : (e.enter("data"), f(w)));
  }
  function f(w) {
    return w === null || w === 124 || be(w) ? (e.exit("data"), u(w)) : (e.consume(w), w === 92 ? h : f);
  }
  function h(w) {
    return w === 92 || w === 124 ? (e.consume(w), f) : f(w);
  }
  function m(w) {
    return i.interrupt = !1, i.parser.lazy[i.now().line] ? n(w) : (e.enter("tableDelimiterRow"), s = !1, Oe(w) ? Be(e, p, "linePrefix", i.parser.constructs.disable.null.includes("codeIndented") ? void 0 : 4)(w) : p(w));
  }
  function p(w) {
    return w === 45 || w === 58 ? y(w) : w === 124 ? (s = !0, e.enter("tableCellDivider"), e.consume(w), e.exit("tableCellDivider"), g) : E(w);
  }
  function g(w) {
    return Oe(w) ? Be(e, y, "whitespace")(w) : y(w);
  }
  function y(w) {
    return w === 58 ? (o += 1, s = !0, e.enter("tableDelimiterMarker"), e.consume(w), e.exit("tableDelimiterMarker"), b) : w === 45 ? (o += 1, b(w)) : w === null || vt(w) ? S(w) : E(w);
  }
  function b(w) {
    return w === 45 ? (e.enter("tableDelimiterFiller"), k(w)) : E(w);
  }
  function k(w) {
    return w === 45 ? (e.consume(w), k) : w === 58 ? (s = !0, e.exit("tableDelimiterFiller"), e.enter("tableDelimiterMarker"), e.consume(w), e.exit("tableDelimiterMarker"), x) : (e.exit("tableDelimiterFiller"), x(w));
  }
  function x(w) {
    return Oe(w) ? Be(e, S, "whitespace")(w) : S(w);
  }
  function S(w) {
    return w === 124 ? p(w) : w === null || vt(w) ? !s || r !== o ? E(w) : (e.exit("tableDelimiterRow"), e.exit("tableHead"), t(w)) : E(w);
  }
  function E(w) {
    return n(w);
  }
  function C(w) {
    return e.enter("tableRow"), A(w);
  }
  function A(w) {
    return w === 124 ? (e.enter("tableCellDivider"), e.consume(w), e.exit("tableCellDivider"), A) : w === null || vt(w) ? (e.exit("tableRow"), t(w)) : Oe(w) ? Be(e, A, "whitespace")(w) : (e.enter("data"), N(w));
  }
  function N(w) {
    return w === null || w === 124 || be(w) ? (e.exit("data"), A(w)) : (e.consume(w), w === 92 ? P : N);
  }
  function P(w) {
    return w === 92 || w === 124 ? (e.consume(w), N) : N(w);
  }
}
function tx(e, t) {
  let n = -1, i = !0, r = 0, o = [0, 0, 0, 0], s = [0, 0, 0, 0], a = !1, l = 0, c, u, f;
  const h = new Xy();
  for (; ++n < e.length; ) {
    const m = e[n], p = m[1];
    m[0] === "enter" ? p.type === "tableHead" ? (a = !1, l !== 0 && (wa(h, t, l, c, u), u = void 0, l = 0), c = {
      type: "table",
      start: Object.assign({}, p.start),
      // Note: correct end is set later.
      end: Object.assign({}, p.end)
    }, h.add(n, 0, [["enter", c, t]])) : p.type === "tableRow" || p.type === "tableDelimiterRow" ? (i = !0, f = void 0, o = [0, 0, 0, 0], s = [0, n + 1, 0, 0], a && (a = !1, u = {
      type: "tableBody",
      start: Object.assign({}, p.start),
      // Note: correct end is set later.
      end: Object.assign({}, p.end)
    }, h.add(n, 0, [["enter", u, t]])), r = p.type === "tableDelimiterRow" ? 2 : u ? 3 : 1) : r && (p.type === "data" || p.type === "tableDelimiterMarker" || p.type === "tableDelimiterFiller") ? (i = !1, s[2] === 0 && (o[1] !== 0 && (s[0] = s[1], f = bn(h, t, o, r, void 0, f), o = [0, 0, 0, 0]), s[2] = n)) : p.type === "tableCellDivider" && (i ? i = !1 : (o[1] !== 0 && (s[0] = s[1], f = bn(h, t, o, r, void 0, f)), o = s, s = [o[1], n, 0, 0])) : p.type === "tableHead" ? (a = !0, l = n) : p.type === "tableRow" || p.type === "tableDelimiterRow" ? (l = n, o[1] !== 0 ? (s[0] = s[1], f = bn(h, t, o, r, n, f)) : s[1] !== 0 && (f = bn(h, t, s, r, n, f)), r = 0) : r && (p.type === "data" || p.type === "tableDelimiterMarker" || p.type === "tableDelimiterFiller") && (s[3] = n);
  }
  for (l !== 0 && wa(h, t, l, c, u), h.consume(t.events), n = -1; ++n < t.events.length; ) {
    const m = t.events[n];
    m[0] === "enter" && m[1].type === "table" && (m[1]._align = Zy(t.events, n));
  }
  return e;
}
function bn(e, t, n, i, r, o) {
  const s = i === 1 ? "tableHeader" : i === 2 ? "tableDelimiter" : "tableData", a = "tableContent";
  n[0] !== 0 && (o.end = Object.assign({}, ht(t.events, n[0])), e.add(n[0], 0, [["exit", o, t]]));
  const l = ht(t.events, n[1]);
  if (o = {
    type: s,
    start: Object.assign({}, l),
    // Note: correct end is set later.
    end: Object.assign({}, l)
  }, e.add(n[1], 0, [["enter", o, t]]), n[2] !== 0) {
    const c = ht(t.events, n[2]), u = ht(t.events, n[3]), f = {
      type: a,
      start: Object.assign({}, c),
      end: Object.assign({}, u)
    };
    if (e.add(n[2], 0, [["enter", f, t]]), i !== 2) {
      const h = t.events[n[2]], m = t.events[n[3]];
      if (h[1].end = Object.assign({}, m[1].end), h[1].type = "chunkText", h[1].contentType = "text", n[3] > n[2] + 1) {
        const p = n[2] + 1, g = n[3] - n[2] - 1;
        e.add(p, g, []);
      }
    }
    e.add(n[3] + 1, 0, [["exit", f, t]]);
  }
  return r !== void 0 && (o.end = Object.assign({}, ht(t.events, r)), e.add(r, 0, [["exit", o, t]]), o = void 0), o;
}
function wa(e, t, n, i, r) {
  const o = [], s = ht(t.events, n);
  r && (r.end = Object.assign({}, s), o.push(["exit", r, t])), i.end = Object.assign({}, s), o.push(["exit", i, t]), e.add(n + 1, 0, o);
}
function ht(e, t) {
  const n = e[t], i = n[0] === "enter" ? "start" : "end";
  return n[1][i];
}
const nx = {
  name: "tasklistCheck",
  tokenize: rx
};
function ix() {
  return {
    text: {
      91: nx
    }
  };
}
function rx(e, t, n) {
  const i = this;
  return r;
  function r(l) {
    return (
      // Exit if there’s stuff before.
      i.previous !== null || // Exit if not in the first content that is the first child of a list
      // item.
      !i._gfmTasklistFirstContentOfListItem ? n(l) : (e.enter("taskListCheck"), e.enter("taskListCheckMarker"), e.consume(l), e.exit("taskListCheckMarker"), o)
    );
  }
  function o(l) {
    return be(l) ? (e.enter("taskListCheckValueUnchecked"), e.consume(l), e.exit("taskListCheckValueUnchecked"), s) : l === 88 || l === 120 ? (e.enter("taskListCheckValueChecked"), e.consume(l), e.exit("taskListCheckValueChecked"), s) : n(l);
  }
  function s(l) {
    return l === 93 ? (e.enter("taskListCheckMarker"), e.consume(l), e.exit("taskListCheckMarker"), e.exit("taskListCheck"), a) : n(l);
  }
  function a(l) {
    return vt(l) ? t(l) : Oe(l) ? e.check({
      tokenize: sx
    }, t, n)(l) : n(l);
  }
}
function sx(e, t, n) {
  return Be(e, i, "whitespace");
  function i(r) {
    return r === null ? n(r) : t(r);
  }
}
function ox(e) {
  return Ty([
    Py(),
    zy(),
    Yy(e),
    Jy(),
    ix()
  ]);
}
const ax = {};
function lx(e) {
  const t = (
    /** @type {Processor<Root>} */
    this
  ), n = e || ax, i = t.data(), r = i.micromarkExtensions || (i.micromarkExtensions = []), o = i.fromMarkdownExtensions || (i.fromMarkdownExtensions = []), s = i.toMarkdownExtensions || (i.toMarkdownExtensions = []);
  r.push(ox(n)), o.push(wy()), s.push(ky(n));
}
const cx = ["img"], ux = {
  p: ({ node: e, ...t }) => /* @__PURE__ */ d("p", { className: "text-pretty [&:not(:first-child)]:mt-2", ...t }),
  ol: ({ node: e, ...t }) => /* @__PURE__ */ d("ol", { className: "mt-2 list-decimal space-y-2 pl-7 marker:font-mono marker:text-[11px] marker:text-accent-ink", ...t }),
  ul: ({ node: e, ...t }) => /* @__PURE__ */ d("ul", { className: "mt-2 list-disc space-y-2 pl-7 marker:text-faint", ...t }),
  strong: ({ node: e, ...t }) => /* @__PURE__ */ d("strong", { className: "font-semibold text-ink", ...t }),
  // A fenced block is a <pre> around a <code>; the pre resets the pill so the
  // block reads as one surface. The className merge keeps react-markdown's
  // language-* class, which it sets on fenced code only.
  pre: ({ node: e, ...t }) => /* @__PURE__ */ d("pre", { className: "mt-2 overflow-x-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] text-ink-soft [&_code]:rounded-none [&_code]:bg-transparent [&_code]:px-0 [&_code]:text-[inherit]", ...t }),
  code: ({ node: e, className: t, ...n }) => /* @__PURE__ */ d("code", { className: V("rounded-[3px] bg-raised px-1 font-mono text-[0.85em] text-ink", t), ...n }),
  // Replies compare sizes in tables. The wrapper scrolls a wide one sideways
  // instead of letting it push the chat column wider.
  table: ({ node: e, ...t }) => /* @__PURE__ */ d("div", { className: "mt-2 overflow-x-auto", children: /* @__PURE__ */ d("table", { className: "w-full border-collapse text-left text-[12.5px] leading-[18px]", ...t }) }),
  th: ({ node: e, ...t }) => /* @__PURE__ */ d("th", { className: "border-b border-line px-2 py-1.5 align-bottom font-semibold text-ink first:pl-0", ...t }),
  td: ({ node: e, ...t }) => /* @__PURE__ */ d("td", { className: "border-b border-line px-2 py-1.5 align-top first:pl-0", ...t }),
  a: ({ node: e, ...t }) => /* @__PURE__ */ d("a", { className: "underline decoration-1 underline-offset-[3px] hover:text-accent-ink", target: "_blank", rel: "noreferrer", ...t })
}, fx = [lx];
function qv({ content: e, streaming: t = !1 }) {
  return /* @__PURE__ */ d("div", { className: V(t && "md-streaming"), children: /* @__PURE__ */ d(
    rf,
    {
      skipHtml: !0,
      remarkPlugins: fx,
      disallowedElements: cx,
      components: ux,
      children: e
    }
  ) });
}
const dx = {
  standard: "Published",
  measured: "You measured",
  asked: "You told us",
  doctrine: "Rule of thumb"
};
function hx(e) {
  if (e.source) return e.source;
  const t = e.how.toLowerCase();
  return /\b(caliper|measured|ruler|tape)\b/.test(t) ? "measured" : /\b(user|stated|asked|said|told)\b/.test(t) ? "asked" : /\b(standard|spec|published|listing|datasheet|nominal)\b/.test(t) ? "standard" : "doctrine";
}
function ka({ children: e }) {
  return /* @__PURE__ */ v("div", { className: "flex items-center gap-2", children: [
    /* @__PURE__ */ d("span", { className: "mono-caption shrink-0 text-faint [letter-spacing:0.12em]", children: e }),
    /* @__PURE__ */ d("span", { className: "h-px flex-1 bg-line-soft" })
  ] });
}
function Yv({ spec: e }) {
  return /* @__PURE__ */ v("div", { className: "flex flex-col overflow-hidden rounded-[6px] border border-line", children: [
    /* @__PURE__ */ d("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3", children: /* @__PURE__ */ v("span", { className: "mono-label flex items-center gap-2 text-ink", children: [
      /* @__PURE__ */ d(z, { name: "lock" }),
      "The plan"
    ] }) }),
    /* @__PURE__ */ v("div", { className: "flex flex-col gap-3 px-3 pt-[11px] pb-3", children: [
      /* @__PURE__ */ d("p", { className: "text-[13px] leading-[19px] text-pretty text-ink-soft", children: e.summary }),
      /* @__PURE__ */ d("dl", { className: "flex flex-col gap-[5px]", children: e.dimensions.map((t) => {
        const n = hx(t);
        return /* @__PURE__ */ v(
          "div",
          {
            className: "flex items-baseline gap-2",
            title: t.provisional ? `${t.how} · a best guess until it is measured` : t.how,
            children: [
              /* @__PURE__ */ d("dt", { className: "min-w-0 flex-1 truncate text-xs leading-4 text-ink-soft", children: Kn(t.name) }),
              /* @__PURE__ */ v("dd", { className: "mono-value text-ink", children: [
                t.provisional ? "~" : "",
                t.value_mm,
                " mm"
              ] }),
              /* @__PURE__ */ d("dd", { className: n === "measured" ? "mono-caption w-24 shrink-0 text-right text-accent-ink [letter-spacing:0.06em]" : "mono-caption w-24 shrink-0 text-right text-muted [letter-spacing:0.06em]", children: dx[n] })
            ]
          },
          t.name
        );
      }) }),
      e.acceptance.length > 0 ? /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5", children: [
        /* @__PURE__ */ d(ka, { children: "Done when" }),
        /* @__PURE__ */ d("ul", { className: "flex list-disc flex-col gap-1 pl-4 marker:text-faint", role: "list", children: e.acceptance.map((t, n) => /* @__PURE__ */ d("li", { className: "text-xs leading-4 text-pretty text-ink-soft", children: t.criterion }, n)) })
      ] }) : null,
      e.params.length > 0 ? /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5", children: [
        /* @__PURE__ */ d(ka, { children: `${e.params.length} slider${e.params.length === 1 ? "" : "s"} to adjust` }),
        /* @__PURE__ */ d("ul", { className: "flex flex-wrap gap-1", role: "list", children: e.params.map((t) => /* @__PURE__ */ d("li", { className: "rounded-control bg-raised px-1.5 py-0.5 text-xs leading-4 text-ink-soft", title: t.description, children: Kn(t.name) }, t.name)) })
      ] }) : null
    ] })
  ] });
}
function px(e) {
  return e.previous_value_mm != null && e.previous_value_mm !== e.value_mm;
}
function Xv({
  measurement: e,
  staleParts: t,
  onAccept: n,
  onEdit: i,
  onRebuild: r,
  rebuilding: o
}) {
  const s = e.stale_parts ?? [], a = t ? s.filter((u) => t.includes(u)) : s, l = px(e), c = e.provisional && n;
  return /* @__PURE__ */ v("div", { className: "flex flex-col overflow-hidden rounded-[6px] border border-line", children: [
    /* @__PURE__ */ v("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3", children: [
      /* @__PURE__ */ v("span", { className: "mono-label flex items-center gap-2 text-ink", children: [
        /* @__PURE__ */ d(z, { name: "ruler" }),
        l ? "Measurement changed" : "Measurement recorded"
      ] }),
      e.provisional ? /* @__PURE__ */ d("span", { className: "mono-caption text-warn [letter-spacing:0.1em]", children: "Provisional" }) : null
    ] }),
    /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5 px-3 pt-[9px] pb-2.5", children: [
      /* @__PURE__ */ v("div", { className: "flex items-baseline gap-2", children: [
        /* @__PURE__ */ d("span", { className: "min-w-0 flex-1 truncate text-xs leading-4 text-ink-soft", children: Kn(e.name) }),
        l ? /* @__PURE__ */ v("span", { className: "mono-value text-muted line-through", children: [
          e.previous_value_mm,
          " mm"
        ] }) : null,
        /* @__PURE__ */ v("span", { className: "mono-value text-ink", children: [
          e.value_mm,
          " mm"
        ] })
      ] }),
      /* @__PURE__ */ d("p", { className: "text-xs leading-4 text-muted", children: e.how }),
      c || i ? /* @__PURE__ */ v("div", { className: "mt-0.5 flex items-center gap-1.5", children: [
        c ? /* @__PURE__ */ d(
          "button",
          {
            type: "button",
            onClick: () => n(e.name),
            className: "btn-label chrome rounded-control focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent bg-ink px-2 py-1 text-ground transition-colors hover:bg-ink-soft",
            children: "Accept"
          }
        ) : null,
        i ? /* @__PURE__ */ d(
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
        /* @__PURE__ */ d("span", { className: "size-1.5 shrink-0 rounded-full bg-warn" }),
        /* @__PURE__ */ d("span", { className: "mono-caption min-w-0 flex-1 truncate text-warn [letter-spacing:0.08em]", children: a.length === 1 ? `${a[0]} is stale` : `${a.length} parts stale · ${a.join(", ")}` }),
        r ? /* @__PURE__ */ d(
          "button",
          {
            type: "button",
            onClick: () => r(a),
            disabled: o,
            className: "btn-label chrome rounded-control focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent bg-ink px-2 py-1 text-ground transition-colors hover:bg-ink-soft disabled:opacity-60",
            children: o ? "Rebuilding…" : "Rebuild"
          }
        ) : null
      ] }) : null
    ] })
  ] });
}
const we = {
  stage: 15069435,
  part: 16732720,
  // Scenery stays neutral, and its albedo is pre-darkened because the key is bright enough
  // to clip the part's red: 0x78818d lit from above reads as the grey-blue token, 0xaab6c6.
  context: 7897485,
  // Text is the second filament. Off-white, pre-darkened like the rest so the key does
  // not clip it to paper, with a grey outline because the red one reads as a smudge.
  text: 14278116,
  textEdge: 9147814,
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
}, yr = () => nl() ? { stage: 922136, gridMinor: 1712427, gridMajor: 2436667, gridBorder: 3819095 } : { stage: we.stage, gridMinor: we.gridMinor, gridMajor: we.gridMajor, gridBorder: we.gridBorder }, mx = { fail: 0.4, warn: 0.38 }, gx = 0.62, yx = 25, Au = (e, t) => e === "fail" ? t.fail : t.warn;
function xx() {
  const e = new sf(16777215, 6);
  e.position.set(0.4, -0.9, 2.9);
  const t = new of(16777215, we.gridMajor, 1);
  return t.position.set(0, 0, 1), [t, e];
}
const vn = (e, t) => {
  const n = new Nr();
  return n.setAttribute("position", new Pr(new Float32Array(e), 3)), new Cr(n, t);
};
function bx([e, t], n = 10) {
  const i = e / 2, r = t / 2, o = n > 0 ? n : 10, s = o * 5, a = [], l = [];
  for (let m = o; m < i; m += o)
    (m % s === 0 ? l : a).push(m, -r, 0, m, r, 0, -m, -r, 0, -m, r, 0);
  for (let m = o; m < r; m += o)
    (m % s === 0 ? l : a).push(-i, m, 0, i, m, 0, -i, -m, 0, i, -m, 0);
  const c = [0, -r, 0, 0, r, 0, -i, 0, 0, i, 0, 0], u = [
    -i,
    -r,
    0,
    i,
    -r,
    0,
    i,
    -r,
    0,
    i,
    r,
    0,
    i,
    r,
    0,
    -i,
    r,
    0,
    -i,
    r,
    0,
    -i,
    -r,
    0
  ], f = yr(), h = new Fn();
  return h.add(
    vn(a, new mt({ color: f.gridMinor })),
    vn(l, new mt({ color: f.gridMajor })),
    vn(u, new mt({ color: f.gridBorder })),
    vn(c, new mt({ color: we.accent, transparent: !0, opacity: 0.35 }))
  ), h;
}
const wn = 1.2;
function vx(e) {
  const t = new lt(
    new mf(1, wn, wn),
    new Wt({ color: we.accent, transparent: !0, opacity: 0.9 })
  );
  return t.position.set(0, -e / 2 + wn * 2, wn / 2), t;
}
const Cu = (e) => {
  const t = e.getSize(new pe());
  return Math.max(t.x, t.y, t.z) || 10;
};
function wx(e, t, n) {
  const i = n.getCenter(new pe()), r = Cu(n), o = r / (2 * Math.tan(e.fov * Math.PI / 180 / 2)) * 2.1, s = [0.7, -0.75, 0.6];
  e.up.set(0, 0, 1), e.position.set(i.x + o * s[0], i.y + o * s[1], i.z + o * s[2]), t.target.copy(i), e.near = r / 100, e.far = r * 100, e.updateProjectionMatrix(), t.update();
}
function Nu(e, t, n) {
  const i = Cu(n), r = e.distanceTo(t);
  return !n.containsPoint(e) && n.clone().expandByScalar(i * 2).containsPoint(t) && r > i / 100 && r < i * 50;
}
function Pu(e, t) {
  return e.updateMatrixWorld(), new hf().setFromProjectionMatrix(
    new pf().multiplyMatrices(e.projectionMatrix, e.matrixWorldInverse)
  ).intersectsBox(t);
}
const kx = /^color-([0-9a-f]{6})-/;
function Tx(e) {
  const t = kx.exec(e);
  return t ? parseInt(t[1], 16) : null;
}
const Sx = 0.4, Ax = (e) => {
  const t = e >> 16 & 255, n = e >> 8 & 255, i = e & 255;
  return Math.round(t * 0.5) << 16 | Math.round(n * 0.5) << 8 | Math.round(i * 0.5);
};
function Cx(e, t, n) {
  const i = [];
  e.traverse((o) => {
    o.isMesh && i.push(o);
  });
  const r = new Fn();
  for (const o of i) {
    const s = o.geometry;
    s.attributes.normal || s.computeVertexNormals();
    const a = new Sr({
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
    s.attributes.color && (a.vertexColors = !0);
    const l = new lt(s, a);
    for (const c of [].concat(o.material)) c.dispose();
    if (l.name = o.name || o.parent?.name || "", l.name === "context")
      a.color.setHex(n.context), a.transparent = !0, a.opacity = 0.3;
    else {
      const c = Tx(l.name);
      l.name === "text" && a.color.setHex(n.text), c !== null && a.color.setHex(c).multiplyScalar(Sx);
      const u = new Cr(
        new Qa(s, yx),
        new mt({
          color: c !== null ? Ax(c) : l.name === "text" ? n.textEdge : n.edge,
          transparent: !0,
          opacity: 0.35,
          clippingPlanes: [t]
        })
      );
      l.add(u);
    }
    r.add(l);
  }
  return r;
}
const Mu = (e) => e.children.filter((t) => t.isMesh && t.name !== "context" && t.name !== "target");
function Nx(e) {
  e.position.set(0, 0, 0), e.updateMatrixWorld(!0);
  const t = new Ht();
  for (const s of e.children) s.name !== "target" && t.expandByObject(s);
  const n = new Ht();
  for (const s of Mu(e)) n.expandByObject(s);
  n.isEmpty() && n.copy(t);
  const i = n.getCenter(new pe()), r = new pe(-i.x, -i.y, -n.min.z), o = e.parent ? e.parent.getWorldQuaternion(new Ls()) : new Ls();
  return e.position.copy(r).applyQuaternion(o.invert()), e.updateMatrixWorld(!0), t.translate(r);
}
function Px(e) {
  const t = new Ht();
  for (const n of Mu(e)) t.expandByObject(n);
  return t;
}
const Ta = {
  depthWrite: !1,
  depthTest: !1,
  colorWrite: !1,
  stencilWrite: !0,
  stencilFunc: ff
};
function Mx(e, t) {
  const n = new Wt({
    ...Ta,
    clippingPlanes: [t],
    side: uf,
    stencilFail: ci,
    stencilZFail: ci,
    stencilZPass: ci
  }), i = new Wt({
    ...Ta,
    clippingPlanes: [t],
    side: df,
    stencilFail: ui,
    stencilZFail: ui,
    stencilZPass: ui
  });
  return [n, i].map((r) => {
    const o = new lt(e.geometry, r);
    return o.matrixAutoUpdate = !1, o.matrix = e.matrixWorld, o.renderOrder = 1, o;
  });
}
function Ex() {
  const e = new lt(
    new af(1, 1),
    new Sr({
      // Violet, because the cap is the one surface that is not part material and must not
      // impersonate a signal: amber is a warn, red a fail, orange the part itself.
      color: we.cap,
      metalness: 0,
      roughness: 0.85,
      side: Ar,
      stencilWrite: !0,
      stencilRef: 0,
      stencilFunc: lf,
      stencilFail: li,
      stencilZFail: li,
      stencilZPass: li
    })
  );
  return e.renderOrder = 1.1, e.visible = !1, e.onAfterRender = (t) => t.clearStencil(), e;
}
function Dx(e, t, n, i) {
  const r = new Nr();
  r.setAttribute("position", new Pr(new Float32Array(e), 3));
  const o = new Wt({
    color: Au(t, i),
    transparent: !0,
    opacity: mx[t],
    side: Ar,
    polygonOffset: !0,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
    depthWrite: !1,
    clippingPlanes: [n]
  });
  return new lt(r, o);
}
function Rx(e, t, n) {
  const i = new Nr();
  i.setAttribute("position", new Pr(new Float32Array(e), 3));
  const r = new Cr(
    new Qa(i, 1),
    new mt({ color: n.accent, depthTest: !1, clippingPlanes: [t] })
  );
  return r.renderOrder = 998, i.dispose(), r;
}
function Lx(e, t, n, i) {
  const r = new Wt({ color: Au(t, i), depthTest: !1, depthWrite: !1 }), o = new lt(new cf(1, 12, 8), r);
  return o.position.set(e[0], e[1], e[2]), o.scale.setScalar(n), o.renderOrder = 999, o;
}
const Vx = (e) => {
  for (const t of Array.isArray(e) ? e : [e]) t.dispose();
};
function ye(e) {
  e.traverse((t) => {
    const n = t;
    !n.geometry || t.name === "target" || (n.geometry.dispose(), Vx(n.material));
  });
}
const xr = 1e6, Fx = { x: [1, 0, 0], y: [0, 1, 0], z: [0, 0, 1] }, Sa = 10, Ix = 42, Ox = 4e3, Bx = Math.PI / 12, Aa = 1.8, jx = 2, Ca = 0.9, $x = 320, Cs = () => {
  try {
    return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? !1;
  } catch {
    return !1;
  }
};
function Eu(e, t) {
  if (e <= 0) return 0;
  if (e >= 1) return 1;
  const [n, i, r, o] = t, s = (l, c, u) => 3 * (1 - l) ** 2 * l * c + 3 * (1 - l) * l ** 2 * u + l ** 3;
  let a = e;
  for (let l = 0; l < 8; l++) {
    const c = s(a, n, r) - e;
    if (Math.abs(c) < 1e-4) break;
    const u = 3 * (1 - a) ** 2 * n + 6 * (1 - a) * a * (r - n) + 3 * a ** 2 * (1 - r);
    if (Math.abs(u) < 1e-6) break;
    a -= c / u;
  }
  return s(a, i, o);
}
const Na = (e) => {
  const t = [];
  return e.traverse((n) => {
    const i = n.material;
    if (i)
      for (const r of Array.isArray(i) ? i : [i])
        t.push({ material: r, opacity: r.opacity, transparent: r.transparent, depthWrite: r.depthWrite });
  }), t;
}, Pa = (e) => {
  for (const t of e)
    t.material.opacity = t.opacity, t.material.transparent = t.transparent, t.material.depthWrite = t.depthWrite;
};
function zx(e, t, n) {
  const i = n.now ?? (() => performance.now()), r = n.schedule ?? ((m) => requestAnimationFrame(() => m())), o = n.unschedule ?? ((m) => cancelAnimationFrame(m)), s = t ? Na(t) : [], a = e ? Na(e) : [];
  for (const m of s)
    m.material.transparent = !0, m.material.opacity = 0;
  for (const m of a)
    m.material.transparent = !0, m.material.depthWrite = !1;
  const l = i(), c = Math.max(1, n.seconds * 1e3);
  let u = 0, f = !0;
  const h = () => {
    if (u = 0, !f) return;
    const m = Math.min(1, (i() - l) / c);
    for (const p of s) p.material.opacity = p.opacity * m;
    for (const p of a) p.material.opacity = p.opacity * (1 - m);
    if (n.render(), m < 1) {
      u = r(h);
      return;
    }
    f = !1, Pa(s), n.onDone();
  };
  return u = r(h), () => {
    f && (f = !1, u && o(u), Pa(s));
  };
}
const _x = (e, t) => !e || !t ? e === t : e.position.every((n, i) => n === t.position[i]) && e.target.every((n, i) => n === t.target[i]), Ux = (e) => {
  let t = null;
  return e.traverse((n) => {
    n.isMesh && !t && (t = n.geometry);
  }), t;
};
function Du(e, t, n) {
  if (!e.controls) return !1;
  const i = new pe().fromArray(t.position), r = new pe().fromArray(t.target);
  if (!Nu(i, r, n)) return !1;
  e.camera.position.copy(i), e.controls.target.copy(r);
  const o = n.getSize(new pe()), s = Math.max(o.x, o.y, o.z) || 10;
  return e.camera.near = s / 100, e.camera.far = s * 100, e.camera.updateProjectionMatrix(), e.controls.update(), Pu(e.camera, n);
}
function Wx(e, t) {
  return !e.controls || !Nu(e.camera.position, e.controls.target, t) ? !1 : Pu(e.camera, t);
}
function Hx(e) {
  const t = e.controls;
  t && (t._sphericalDelta?.set(0, 0, 0), t._panOffset?.set(0, 0, 0), t._scale = 1);
}
function ut(e, t) {
  e.plate && (e.scene.remove(e.plate), ye(e.plate), e.plate = null);
  const n = t ?? Gx(e);
  e.plateSize = n, n && (e.plate = bx(n, e.pitch), e.scene.add(e.plate));
}
function Gx(e) {
  if (!e.part) return null;
  const t = new Ht().setFromObject(e.part).getSize(new pe()), n = Math.max(100, Math.ceil(Math.max(t.x, t.y) * 1.8 / 50) * 50);
  return [n, n];
}
function Ma(e, t) {
  if (!e.part) return;
  e.box = Nx(e.part), e.size = e.box.getSize(new pe()).length(), e.quiet = !0, !(e.framed ? Wx(e, e.box) : t && Du(e, t, e.box)) && e.controls && wx(e.camera, e.controls, e.box), e.quiet = !1, e.framed = !0;
}
function Ea(e) {
  const t = e.fading;
  t && (e.fading = null, t.cancel(), e.root.remove(t.group), ye(t.group));
}
function Kx(e) {
  const t = e.controls;
  if (!t || Cs()) return;
  e.nudgeRaf && cancelAnimationFrame(e.nudgeRaf);
  const n = t.target.clone(), i = e.camera.position.clone().sub(n), r = e.camera.up.clone().normalize(), o = performance.now(), s = _.coast * 1e3;
  e.quiet = !0;
  const a = () => {
    e.nudgeRaf = 0;
    const l = Math.min(1, (performance.now() - o) / s);
    l >= 1 && (e.quiet = !1), e.camera.position.copy(i).applyAxisAngle(r, Bx * Eu(l, Z.out)).add(n), t.update(), e.render(), l < 1 && (e.nudgeRaf = requestAnimationFrame(a));
  };
  e.nudgeRaf = requestAnimationFrame(a);
}
function Ru(e) {
  e.purgeRaf && cancelAnimationFrame(e.purgeRaf), e.purgeRaf = 0, e.purge && (e.scene.remove(e.purge), ye(e.purge), e.purge = null);
}
function qx(e) {
  if (!e.plate || !e.plateSize || Cs()) return !1;
  const [t, n] = e.plateSize, i = vx(n);
  e.purge = i, e.scene.add(i);
  const r = i.material, o = performance.now(), s = () => {
    e.purgeRaf = 0;
    const a = (performance.now() - o) / 1e3, l = Math.max(1e-3, t * Eu(a / Aa, Z.out));
    i.scale.x = l, i.position.x = -t / 2 + l / 2;
    const c = a - Aa - jx;
    if (r.opacity = c <= 0 ? Ca : Ca * (1 - Math.min(1, c / _.settle)), e.render(), c < _.settle) {
      e.purgeRaf = requestAnimationFrame(s);
      return;
    }
    Ru(e), e.render();
  };
  return e.purgeRaf = requestAnimationFrame(s), !0;
}
function Da(e, t, n) {
  !t || n.current || (n.current = qx(e));
}
function Vn(e) {
  for (const t of e.writers)
    e.scene.remove(t), t.material.dispose();
  e.writers = [];
}
function Yx(e) {
  if (Vn(e), !!e.part) {
    e.part.updateMatrixWorld(!0);
    for (const t of e.part.children)
      if (!(!t.isMesh || t.name === "context" || t.name === "target"))
        for (const n of Mx(t, e.plane))
          n.visible = e.cutting, e.scene.add(n), e.writers.push(n);
  }
}
function Vt(e, t) {
  if (!t) {
    e.cutting = !1, e.cutSign = 0, e.cap.visible = !1;
    for (const u of e.writers) u.visible = !1;
    e.plane.constant = xr, e.render();
    return;
  }
  if ((!e.cutting || e.cutAxis !== t.axis) && (e.cutting = !0, e.cutAxis = t.axis, e.cutSign = 0), !e.part) {
    e.cap.visible = !1, e.plane.constant = xr, e.render();
    return;
  }
  const n = Px(e.part), i = t.axis, r = n.min[i], o = n.max[i];
  e.cutSign || (e.cutSign = e.camera.position[i] >= (r + o) / 2 ? 1 : -1);
  const s = e.cutSign === 1 ? t.t : 1 - t.t, a = r + (o - r) * (0.02 + 0.96 * s), l = Fx[i];
  e.plane.normal.set(-e.cutSign * l[0], -e.cutSign * l[1], -e.cutSign * l[2]), e.plane.constant = e.cutSign * a, e.cap.visible = !0;
  for (const u of e.writers) u.visible = !0;
  const c = n.getSize(new pe()).length();
  e.cap.scale.set(c, c, 1), e.plane.projectPoint(n.getCenter(new pe()), e.cap.position), e.cap.lookAt(
    e.cap.position.x - e.plane.normal.x,
    e.cap.position.y - e.plane.normal.y,
    e.cap.position.z - e.plane.normal.z
  ), e.render();
}
function Ft(e, t, n) {
  for (const o of e.marks.children) ye(o);
  if (e.marks.clear(), e.glows = [], !e.part) {
    e.render();
    return;
  }
  const i = e.part.position, r = Math.max(0.6, e.size / 90);
  t.forEach((o, s) => {
    if (o.face && o.face.length) {
      const l = Dx(o.face, o.severity, e.plane, we);
      l.position.copy(i), l.userData.finding = s, s === n && (l.material.opacity = gx, l.add(Rx(o.face, e.plane, we))), e.marks.add(l), e.glows.push(l);
    }
    if (!o.where) return;
    const a = Lx(
      [o.where[0] + i.x, o.where[1] + i.y, o.where[2] + i.z],
      o.severity,
      r,
      we
    );
    e.marks.add(a);
  }), e.render();
}
function Ra(e, t) {
  for (const n of e?.children ?? []) n.name === "context" && (n.visible = t);
}
function Qv(e) {
  const { glbUrl: t, targetUrl: n, targetOffset: i, findings: r, highlight: o, bed: s, up: a, section: l, camera: c, settleKey: u, purge: f, className: h } = e, [m, p] = B(!1), g = D(null), y = D(null), b = D(null), k = D(null), x = D(e);
  x.current = e;
  const S = D(!1), E = D([]), C = e.anchors ?? [], A = C.map((T) => `${T.key}@${T.point.join(",")}`).join("|");
  O(() => {
    y.current?.render();
  }, [A]), O(() => {
    const T = g.current;
    if (!T) return;
    const I = new gf();
    I.background = new Vs(yr().stage);
    const F = new yf(45, 1, 0.1, 1e4);
    F.up.set(0, 0, 1);
    const X = new Fn(), q = new Fn();
    X.add(q), I.add(X);
    for (const G of xx()) I.add(G);
    const H = Ex();
    I.add(H);
    const M = {
      renderer: null,
      scene: I,
      camera: F,
      controls: null,
      plane: new xf(new pe(0, 0, -1), xr),
      root: X,
      marks: q,
      cap: H,
      part: null,
      fading: null,
      ghost: null,
      plate: null,
      plateSize: null,
      pitch: Sa,
      purge: null,
      writers: [],
      glows: [],
      box: new Ht(),
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
      },
      place: () => {
      }
    };
    y.current = M, T.__nurbViewer = M;
    try {
      M.renderer = new bf({ antialias: !0, stencil: !0 });
    } catch {
      T.setAttribute("data-nogl", "");
    }
    const $ = M.renderer?.domElement ?? null;
    M.renderer && $ && (M.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)), M.renderer.localClippingEnabled = !0, $.className = "block h-full w-full", T.appendChild($), M.controls = new kf(F, $), M.controls.enableDamping = !0, M.controls.dampingFactor = 0.0533);
    const ee = () => {
      if (M.raf = 0, !M.renderer || !M.controls) return;
      const G = M.controls.update();
      G || Hx(M), M.renderer.render(I, F), M.place(), G && M.render();
    };
    M.place = () => {
      const G = M.part?.children.find((te) => te.isMesh && te.name !== "context");
      for (const [te, he] of (x.current.anchors ?? []).entries()) {
        const se = E.current[te];
        if (!se) continue;
        const Ee = G ? G.localToWorld(new pe(...he.point)).project(F) : null;
        if (!Ee || Ee.z > 1) {
          se.style.visibility = "hidden";
          continue;
        }
        const Et = (Ee.x + 1) / 2 * M.lastW, Dt = Et > M.lastW - $x;
        se.toggleAttribute("data-flip", Dt), se.style.visibility = "visible", se.style.transform = `translate(${Et}px, ${(1 - Ee.y) / 2 * M.lastH}px)${Dt ? " translateX(-100%)" : ""}`;
      }
    }, M.render = () => {
      !M.renderer || M.raf || (M.raf = requestAnimationFrame(ee));
    };
    const re = (G, te) => {
      const he = Math.floor(G), se = Math.floor(te);
      !he || !se || he === M.lastW && se === M.lastH || (M.lastW = he, M.lastH = se, M.renderer?.setSize(he, se, !1), F.aspect = he / se, F.updateProjectionMatrix(), M.render());
    }, ie = new ResizeObserver((G) => {
      const te = G[G.length - 1].contentRect;
      re(te.width, te.height);
    });
    ie.observe(T), re(T.clientWidth, T.clientHeight);
    const R = () => {
      M.render(), !M.quiet && (M.camTimer && clearTimeout(M.camTimer), M.camTimer = setTimeout(() => {
        const G = x.current.onCamera;
        !G || !M.controls || G({
          position: M.camera.position.toArray(),
          target: M.controls.target.toArray()
        });
      }, 250));
    };
    M.controls?.addEventListener("change", R);
    const W = new MutationObserver(() => {
      I.background = new Vs(yr().stage), M.plateSize && ut(M, M.plateSize), M.render();
    });
    return W.observe(document.documentElement, { attributes: !0, attributeFilter: ["data-theme"] }), () => {
      W.disconnect(), ie.disconnect(), M.raf && cancelAnimationFrame(M.raf), M.nudgeRaf && cancelAnimationFrame(M.nudgeRaf), M.camTimer && clearTimeout(M.camTimer), M.generation++, M.targetGeneration++, M.controls?.removeEventListener("change", R), M.controls?.dispose(), Vn(M), Ru(M);
      for (const G of q.children) ye(G);
      Ea(M), M.part && ye(M.part), M.ghost && (M.ghost.geometry.dispose(), M.ghost.material.dispose()), M.plate && ye(M.plate), ye(H), M.renderer?.setAnimationLoop(null), M.renderer?.forceContextLoss(), M.renderer?.dispose(), $?.remove(), delete T.__nurbViewer, y.current = null;
    };
  }, []), O(() => {
    const T = y.current;
    if (!T || !T.controls) return;
    const I = ++T.generation;
    Ea(T);
    const F = () => {
      T.part && (T.root.remove(T.part), T.ghost && T.part.remove(T.ghost), ye(T.part), T.part = null);
    };
    if (!t) {
      F(), ut(T, x.current.bed), Vn(T), Ft(T, [], null), Vt(T, x.current.section);
      return;
    }
    new Fs().loadAsync(t).then((X) => {
      if (I !== T.generation) {
        ye(X.scene);
        return;
      }
      const q = Cx(X.scene, T.plane, we);
      if (T.loaded = I, !q.children.length) {
        F(), ye(q), Vn(T), Ft(T, [], null), Vt(T, x.current.section);
        return;
      }
      const H = T.part;
      H && T.ghost && H.remove(T.ghost), T.ghost && q.add(T.ghost), Ra(q, x.current.scenery ?? !0), T.root.add(q), T.part = q, Ma(T, x.current.camera), ut(T, x.current.bed), Da(T, x.current.purge, S), k.current = x.current.camera ?? null, Yx(T), Vt(T, x.current.section), Ft(T, x.current.findings ?? [], x.current.highlight), H && Cs() ? (T.root.remove(H), ye(H)) : H && (T.fading = {
        group: H,
        cancel: zx(H, q, {
          seconds: _.settle,
          render: T.render,
          onDone: () => {
            T.fading = null, T.root.remove(H), ye(H), T.render();
          }
        })
      }), T.render();
    }).catch((X) => {
      I === T.generation && console.warn(`ViewerIsland: could not load ${t}`, X);
    });
  }, [t]);
  const N = (i ?? [0, 0, 0]).join(",");
  O(() => {
    const T = y.current;
    if (!T || !T.controls) return;
    const I = ++T.targetGeneration;
    if (T.ghost && (T.ghost.parent?.remove(T.ghost), T.ghost.geometry.dispose(), T.ghost.material.dispose(), T.ghost = null), !n) {
      T.render();
      return;
    }
    new Fs().loadAsync(n).then((F) => {
      if (I !== T.targetGeneration) {
        ye(F.scene);
        return;
      }
      const X = Ux(F.scene);
      if (!X) return;
      X.attributes.normal || X.computeVertexNormals();
      const q = new lt(
        X,
        new Sr({
          color: we.ghost,
          metalness: 0,
          roughness: 0.9,
          transparent: !0,
          opacity: 0.3,
          depthWrite: !1,
          side: Ar,
          clippingPlanes: [T.plane]
        })
      );
      q.name = "target";
      const H = N.split(",").map(Number);
      q.position.set(H[0], H[1], H[2]), T.ghost = q, T.part?.add(q), T.render();
    }).catch(() => {
    });
  }, [n, N]), O(() => {
    const T = y.current;
    !T || T.loaded !== T.generation || Ft(T, r ?? [], o);
  }, [r, o]), O(() => {
    const T = y.current;
    T && (Ra(T.part, e.scenery ?? !0), T.render());
  }, [e.scenery]), O(() => {
    const T = y.current;
    T && (ut(T, s), T.render());
  }, [s?.[0], s?.[1], !s]);
  const P = D(u);
  O(() => {
    const T = y.current, I = P.current;
    P.current = u, !(!T || u === void 0 || u === I) && Kx(T);
  }, [u]), O(() => {
    const T = y.current;
    T && Da(T, f, S);
  }, [f, s?.[0], s?.[1]]), O(() => {
    let T = null;
    const I = () => {
      p(!0), T && clearTimeout(T), T = setTimeout(() => p(!1), Ox);
    };
    return window.addEventListener("nurb:gridfinity", I), () => {
      window.removeEventListener("nurb:gridfinity", I), T && clearTimeout(T);
    };
  }, []), O(() => {
    const T = y.current;
    T && (T.pitch = m ? Ix : Sa, ut(T, x.current.bed), T.render());
  }, [m]);
  const w = (a ?? [0, 0, 1]).join(",");
  return O(() => {
    const T = y.current;
    if (!T) return;
    const I = new pe(...w.split(",").map(Number)).normalize();
    T.root.quaternion.setFromUnitVectors(I, new pe(0, 0, 1)), T.root.updateMatrixWorld(!0), T.part && (Ma(T, x.current.camera), ut(T, x.current.bed), Vt(T, x.current.section), Ft(T, x.current.findings ?? [], x.current.highlight)), T.render();
  }, [w]), O(() => {
    const T = y.current;
    T && Vt(T, l);
  }, [l]), O(() => {
    const T = y.current;
    if (!T || !T.part || !c || _x(c, k.current)) return;
    k.current = c, T.quiet = !0;
    const I = Du(T, c, T.box);
    T.quiet = !1, I && T.render();
  }, [c]), /* @__PURE__ */ v(
    "div",
    {
      ref: g,
      className: V("relative block h-full w-full", e.onPick && "cursor-crosshair", h),
      onPointerDown: (T) => {
        b.current = [T.clientX, T.clientY];
      },
      onPointerUp: (T) => {
        const I = b.current;
        b.current = null;
        const F = y.current, { onHighlight: X, onPick: q } = x.current;
        if (!I || !F || !X && !q || Math.hypot(T.clientX - I[0], T.clientY - I[1]) > 5) return;
        const H = T.currentTarget.getBoundingClientRect();
        if (!H.width || !H.height) return;
        const M = new vf(
          (T.clientX - H.left) / H.width * 2 - 1,
          -((T.clientY - H.top) / H.height) * 2 + 1
        ), $ = new wf();
        if ($.setFromCamera(M, F.camera), q) {
          const re = (F.part?.children ?? []).filter((R) => R.isMesh && R.name !== "context"), ie = $.intersectObjects(re, !1).find((R) => !F.cutting || F.plane.distanceToPoint(R.point) >= 0);
          if (ie?.face) {
            const R = ie.object.worldToLocal(ie.point.clone()), W = ie.face.normal;
            q({ point: [R.x, R.y, R.z], normal: [W.x, W.y, W.z] });
          }
          return;
        }
        if (!X) return;
        const ee = $.intersectObjects(F.glows, !1).find((re) => !F.cutting || F.plane.distanceToPoint(re.point) >= 0);
        X(ee ? ee.object.userData.finding : null);
      },
      children: [
        C.map((T, I) => /* @__PURE__ */ d(
          "div",
          {
            ref: (F) => {
              E.current[I] = F;
            },
            className: "group pointer-events-none absolute top-0 left-0 z-10 *:pointer-events-auto",
            style: { visibility: "hidden" },
            onPointerDown: (F) => F.stopPropagation(),
            onPointerUp: (F) => F.stopPropagation(),
            children: T.node
          },
          T.key
        )),
        m && /* @__PURE__ */ d("div", { className: "mono-caption pointer-events-none absolute bottom-3 left-3 text-faint [letter-spacing:0.12em]", children: "GRID 42.0 MM" })
      ]
    }
  );
}
const Xx = {
  accent: "bg-accent text-white hover:bg-accent-hover",
  ink: "bg-ink text-ground hover:bg-ink-soft",
  outline: "border border-line bg-ground text-ink-soft hover:border-panel-edge hover:text-ink",
  ghost: "text-muted hover:bg-raised hover:text-ink",
  danger: "bg-fail text-white hover:bg-fail/90"
}, Qx = {
  sm: "h-7 px-3",
  md: "h-9 px-3",
  lg: "h-10 px-4"
}, Me = Tr(function({ variant: t = "outline", size: n = "sm", icon: i, trailingIcon: r, className: o, children: s, type: a = "button", ...l }, c) {
  return /* @__PURE__ */ v(
    "button",
    {
      ref: c,
      type: a,
      className: V(
        "chrome btn-label inline-flex shrink-0 items-center justify-center gap-2 rounded-[3px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50",
        Xx[t],
        Qx[n],
        i && "pl-2.5",
        r && "pr-2.5",
        o
      ),
      ...l,
      children: [
        i ? /* @__PURE__ */ d(z, { name: i }) : null,
        s,
        r ? /* @__PURE__ */ d(z, { name: r }) : null
      ]
    }
  );
});
function Ns({
  icon: e,
  label: t,
  active: n = !1,
  className: i,
  ...r
}) {
  return /* @__PURE__ */ v(
    "button",
    {
      type: "button",
      "aria-label": t,
      title: t,
      className: V(
        "chrome relative inline-flex size-7 shrink-0 items-center justify-center rounded-[4px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent disabled:opacity-40",
        n ? "bg-accent-wash text-accent-ink" : "text-ink-soft hover:bg-raised hover:text-ink",
        i
      ),
      ...r,
      children: [
        /* @__PURE__ */ d(z, { name: e }),
        /* @__PURE__ */ d("span", { className: "absolute top-1/2 left-1/2 size-[max(100%,3rem)] -translate-1/2 pointer-fine:hidden", "aria-hidden": "true" })
      ]
    }
  );
}
const Zx = Z.out, Jx = { duration: _.settle, ease: Zx }, eb = { duration: 0 };
function tb({
  action: e,
  resetAfter: t = 1400
}) {
  const [n, i] = B("idle"), r = D("idle"), o = D(0), s = D(null), a = D(!0), l = D(e);
  l.current = e;
  const c = Q(() => {
    s.current && clearTimeout(s.current), s.current = null;
  }, []), u = Q(() => {
    if (r.current === "pending") return;
    c();
    const f = ++o.current;
    r.current = "pending", i("pending");
    const h = (m) => {
      !a.current || f !== o.current || (r.current = m, i(m), s.current = setTimeout(() => {
        !a.current || f !== o.current || (r.current = "idle", i("idle"));
      }, t));
    };
    Promise.resolve().then(() => l.current()).then(
      () => h("success"),
      () => h("error")
    );
  }, [c, t]);
  return O(() => (a.current = !0, () => {
    a.current = !1, c();
  }), [c]), { status: n, run: u, pending: n === "pending" };
}
function nb({ still: e }) {
  return /* @__PURE__ */ v(
    j.svg,
    {
      width: "11",
      height: "11",
      viewBox: "0 0 12 12",
      fill: "none",
      "aria-hidden": "true",
      className: "shrink-0",
      animate: e ? void 0 : { rotate: 360 },
      transition: e ? void 0 : { duration: _.coast * 0.6, repeat: 1 / 0, ease: "linear" },
      children: [
        /* @__PURE__ */ d("circle", { cx: "6", cy: "6", r: "4.5", stroke: "currentColor", strokeWidth: "1.5", strokeOpacity: "0.22" }),
        /* @__PURE__ */ d("path", { d: "M10.5 6A4.5 4.5 0 0 0 6 1.5", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
      ]
    }
  );
}
function La({ d: e, extra: t }) {
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
        /* @__PURE__ */ d("path", { d: e }),
        t ? /* @__PURE__ */ d("path", { d: t }) : null
      ]
    }
  );
}
function ib({
  label: e,
  pendingLabel: t = e,
  successLabel: n = "Done",
  errorLabel: i = "Try again",
  onAction: r,
  resetAfter: o = 1400,
  variant: s = "outline",
  disabled: a = !1,
  className: l
}) {
  const c = ne(), { status: u, run: f, pending: h } = tb({ action: r, resetAfter: o }), m = c ? eb : Jx, p = [
    { key: "idle", text: e, color: void 0, icon: null },
    {
      key: "pending",
      text: t,
      color: "var(--color-muted)",
      icon: /* @__PURE__ */ d(nb, { still: c === !0 || u !== "pending" })
    },
    {
      key: "success",
      text: n,
      color: "var(--color-pass)",
      icon: /* @__PURE__ */ d(La, { d: "M2.6 6.3 4.9 8.6 9.4 3.6" })
    },
    {
      key: "error",
      text: i,
      color: "var(--color-fail)",
      icon: /* @__PURE__ */ d(La, { d: "M6 2.9v3.5", extra: "M6 9.05h.01" })
    }
  ], g = p.find((y) => y.key === u) ?? p[0];
  return /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d(
      Me,
      {
        variant: s,
        disabled: a,
        "aria-label": g.text,
        "aria-busy": h || void 0,
        "aria-disabled": h || void 0,
        className: l,
        onClick: () => {
          h || (qe("press"), f());
        },
        children: /* @__PURE__ */ d("span", { "aria-hidden": "true", className: "relative grid place-items-center", children: p.map((y) => /* @__PURE__ */ v(
          j.span,
          {
            initial: !1,
            animate: y.key === u ? { opacity: 1, y: 0 } : { opacity: 0, y: 2 },
            transition: m,
            style: { color: y.color },
            className: "col-start-1 row-start-1 flex items-center justify-center gap-1.5 whitespace-nowrap",
            children: [
              y.icon,
              y.text
            ]
          },
          y.key
        )) })
      }
    ),
    /* @__PURE__ */ d("span", { role: "status", "aria-live": "polite", className: "sr-only", children: u === "success" ? n : u === "error" ? i : "" })
  ] });
}
function It(e) {
  return Math.round(e * 1e6) / 1e6;
}
function rb({
  value: e,
  onValueChange: t,
  min: n,
  max: i,
  step: r,
  detents: o,
  pull: s
}) {
  const a = de(() => o.map((y) => typeof y == "number" ? { value: y } : y), [o]), l = s ?? (i - n) * 0.045, c = D(t);
  c.current = t;
  const u = de(() => a.findIndex((y) => It(y.value) === It(e)), [a, e]), f = D(u);
  f.current = u;
  const h = D(!1), m = Q(
    (y) => {
      let b = -1, k = l;
      for (let x = 0; x < a.length; x += 1) {
        const S = Math.abs(y - a[x].value);
        S <= k && (k = S, b = x);
      }
      return b >= 0 ? a[b].value : n + Math.round((y - n) / r) * r;
    },
    [l, a, n, r]
  ), p = Q(
    (y) => {
      const b = Number(y.target.value);
      if (!Number.isFinite(b)) return;
      const k = h.current;
      h.current = !1;
      const x = It(Math.min(i, Math.max(n, k ? b : m(b)))), S = a.findIndex((E) => It(E.value) === x);
      S >= 0 && S !== f.current && qe("tick"), x !== It(e) && c.current(x);
    },
    [a, i, n, m, e]
  ), g = Q((y) => {
    (y.key.startsWith("Arrow") || y.key === "PageUp" || y.key === "PageDown") && (h.current = !0);
  }, []);
  return { onChange: p, onKeyDown: g, activeDetent: u, detents: a, activeLabel: a[u]?.label };
}
function sb({
  detents: e,
  min: t,
  max: n,
  activeDetent: i,
  className: r
}) {
  const o = n - t;
  return (
    // Inset by half the 12px thumb, because that is the width the thumb's centre actually travels.
    /* @__PURE__ */ d("div", { "aria-hidden": !0, className: V("pointer-events-none absolute inset-x-[6px] bottom-0", r), children: e.map((s, a) => /* @__PURE__ */ d(
      "span",
      {
        title: s.label,
        className: V(
          "absolute bottom-0 block h-[3px] w-px -translate-x-1/2",
          a === i ? "bg-accent" : "bg-line"
        ),
        style: { left: o > 0 ? `${(s.value - t) / o * 100}%` : "0%" }
      },
      s.value
    )) })
  );
}
function ob(e, t) {
  let n, i;
  if (e === 0 ? (n = 0, i = t ? 8 : 1) : e < 0 ? (n = e * 2, i = e / 2) : (n = e / 2, i = e * 2), t)
    return n = Math.floor(n), i = Math.ceil(i), e >= 1 && (n = Math.max(1, n)), i - n < 4 && (i = n + 4), { lo: n, hi: i, step: 1 };
  const r = Math.min(10 ** (Math.floor(Math.log10(i - n)) - 1), 10 ** -Vu(e));
  return { lo: At(Math.floor(n / r) * r, r), hi: At(Math.ceil(i / r) * r, r), step: r };
}
function Lu(e, t) {
  const n = ob(e.default, t);
  return {
    lo: e.min ?? n.lo,
    hi: e.max ?? n.hi,
    step: e.step ?? n.step
  };
}
function Vu(e) {
  const t = String(e), n = t.indexOf(".");
  return n === -1 || t.includes("e") ? 0 : Math.min(t.length - n - 1, 4);
}
function At(e, t) {
  const n = Math.max(0, -Math.floor(Math.log10(t)));
  return +e.toFixed(n);
}
const ab = /* @__PURE__ */ new Set(["bool", "int", "float", "str", "choice", "color"]);
function br(e) {
  return (e.kind === "int" || e.kind === "float") && typeof e.default != "number" ? !1 : ab.has(e.kind);
}
const Fi = 200;
function lb(e, t) {
  const n = {};
  for (const i of e) {
    if (!br(i)) continue;
    const r = t[i.name];
    r === void 0 || r === i.default || (n[i.name] = r);
  }
  return n;
}
const cb = /wall|thickness|lip|rim|shell/;
function ub(e, t, n = 0.4, i = "default") {
  if (e.kind !== "float" || typeof e.default != "number") return [];
  const { lo: r, hi: o, step: s } = Lu(e, !1), a = (u) => Number.isFinite(u) && u >= r && u <= o, l = [{ value: e.default, label: i }];
  for (const u of t ?? [])
    a(u.value_mm) && l.push({ value: u.value_mm, label: "measured" });
  if (cb.test(e.name.toLowerCase()) && n > 0)
    for (let u = 2; u * n <= o; u += 1) {
      const f = At(u * n, 1e-3);
      a(f) && l.push({ value: f, label: `${u} lines` });
    }
  const c = /* @__PURE__ */ new Map();
  for (const u of l) {
    const f = At(u.value, s);
    c.has(f) || c.set(f, u);
  }
  return [...c.values()].sort((u, f) => u.value - f.value);
}
const Va = Z.out, Fa = "mm", Ia = 4, fb = 60, Oa = 6;
function ft(e, t, n) {
  return String(t ? Math.round(e) : At(e, n));
}
function Ue(e) {
  return e.replace(/_/g, " ");
}
function kn({ children: e }) {
  return /* @__PURE__ */ v("div", { className: "chrome flex items-center gap-2 px-4 pt-[11px] pb-2", children: [
    /* @__PURE__ */ d("span", { className: "mono-caption text-faint [letter-spacing:0.12em]", children: e }),
    /* @__PURE__ */ d("span", { className: "h-px flex-1 bg-line-soft" })
  ] });
}
function dn({ param: e, onReset: t }) {
  return /* @__PURE__ */ d(
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
function db({
  id: e,
  param: t,
  value: n,
  dirty: i,
  measurements: r,
  nozzle: o,
  restLabel: s,
  onValue: a
}) {
  const l = t.kind === "int", c = Lu(t, l), u = Math.min(c.lo, n), f = Math.max(c.hi, n), h = l ? 1 : Math.min(c.step, 10 ** -Vu(n)), [m, p] = B(() => ft(n, l, h)), g = D(!1);
  if (!g.current) {
    const R = ft(n, l, h);
    R !== m && p(R);
  }
  const y = ne(), b = de(
    () => ub(t, r, o, s),
    [t, r, o, s]
  ), k = rb({
    value: n,
    onValueChange: a,
    min: u,
    max: f,
    step: h,
    detents: b,
    pull: (f - u) * 0.045
  }), [x, S] = B(null), [E, C] = B(0);
  O(() => {
    if (!x) return;
    C(x.end === "max" ? 3 : -3);
    const R = setTimeout(() => C(0), y ? 0 : _.tick * 1e3), W = setTimeout(() => S(null), 1200);
    return () => {
      clearTimeout(R), clearTimeout(W);
    };
  }, [x, y]);
  const A = (R) => S({ end: R }), N = (R) => {
    if (l) {
      a(Math.round(Number(R.target.value)));
      return;
    }
    k.onChange(R);
  }, P = D(!1), w = D(!1), T = (R) => {
    R.button === 0 && (P.current = !0, w.current = !1);
  }, I = (R) => {
    if (!P.current) return;
    const W = R.currentTarget.getBoundingClientRect(), G = R.clientX > W.right + Oa ? "max" : R.clientX < W.left - Oa ? "min" : null;
    if (!G) {
      w.current = !1;
      return;
    }
    w.current || (G === "max" && n >= f ? (w.current = !0, A("max")) : G === "min" && n <= u && (w.current = !0, A("min")));
  }, F = () => {
    P.current = !1, w.current = !1;
  }, X = (R) => {
    const W = R.key === "ArrowRight" || R.key === "ArrowUp" || R.key === "PageUp", G = R.key === "ArrowLeft" || R.key === "ArrowDown" || R.key === "PageDown";
    W && n >= f ? A("max") : G && n <= u && A("min"), k.onKeyDown(R);
  }, q = () => {
    g.current = !1;
    const R = Number(m), W = l ? Math.round(R) : R;
    if (m.trim() === "" || !Number.isFinite(R) || W === n) {
      p(ft(n, l, h));
      return;
    }
    a(W);
  }, H = (R, W, G) => {
    const te = l ? Math.round(R + W * G) : At(R + W * G, G);
    return te !== n && a(te), te;
  }, M = D(null), $ = D(0), ee = (R) => {
    R.button === 0 && (M.current = { x: R.clientX, from: n, step: h, scrubbing: !1 });
  }, re = (R) => {
    const W = M.current;
    if (!W) return;
    const G = R.clientX - W.x;
    if (!W.scrubbing) {
      if (Math.abs(G) < Ia) return;
      W.scrubbing = !0, R.currentTarget.setPointerCapture?.(R.pointerId);
    }
    const te = n;
    if (H(W.from, Math.round(G / Ia), W.step) === te) return;
    const se = Date.now();
    se - $.current >= fb && ($.current = se, qe("tick"));
  }, ie = (R) => {
    const W = M.current;
    M.current = null, W?.scrubbing && R.currentTarget.hasPointerCapture?.(R.pointerId) && R.currentTarget.releasePointerCapture(R.pointerId);
  };
  return /* @__PURE__ */ v("div", { className: "flex flex-col gap-1 px-4", children: [
    /* @__PURE__ */ v("div", { className: "flex items-baseline justify-between gap-2", children: [
      /* @__PURE__ */ v("div", { className: "flex min-w-0 items-center gap-1.5", children: [
        /* @__PURE__ */ d(
          "label",
          {
            htmlFor: e,
            title: t.description,
            className: V("mono-caption min-w-0 truncate", i ? "font-medium text-ink" : "text-muted"),
            children: Ue(t.name)
          }
        ),
        i ? /* @__PURE__ */ d(dn, { param: t, onReset: () => a(t.default) }) : null
      ] }),
      /* @__PURE__ */ v("div", { className: "flex shrink-0 items-baseline gap-1.5", children: [
        k.activeLabel ? /* @__PURE__ */ d("span", { className: "mono-caption text-faint", children: k.activeLabel }) : null,
        /* @__PURE__ */ d(
          "input",
          {
            value: m,
            onChange: (R) => {
              g.current = !0, p(R.target.value);
            },
            onBlur: q,
            onPointerDown: ee,
            onPointerMove: re,
            onPointerUp: ie,
            onPointerCancel: ie,
            onKeyDown: (R) => {
              if (R.key === "Enter" && q(), R.key === "Escape") {
                const W = M.current;
                M.current = null, g.current = !1, W?.scrubbing ? a(W.from) : p(ft(n, l, h));
              }
              (R.key === "ArrowUp" || R.key === "ArrowDown") && (R.preventDefault(), H(n, (R.key === "ArrowUp" ? 1 : -1) * (R.shiftKey ? 10 : 1), h));
            },
            inputMode: l ? "numeric" : "decimal",
            "aria-label": `${t.name} value`,
            className: V(
              "mono-value w-16 cursor-ew-resize rounded-control border-0 bg-transparent p-0 text-right focus:bg-raised focus:outline-1 focus:outline-accent",
              i ? "text-accent-ink" : "text-ink"
            )
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ v(
      j.div,
      {
        className: "relative",
        animate: { x: E },
        transition: { duration: y ? 0 : _.tick, ease: Va },
        children: [
          /* @__PURE__ */ d(
            "input",
            {
              id: e,
              type: "range",
              min: u,
              max: f,
              step: h,
              value: n,
              onChange: N,
              onKeyDown: X,
              onPointerDown: T,
              onPointerMove: I,
              onPointerUp: F,
              onPointerCancel: F,
              onLostPointerCapture: F,
              "aria-label": Ue(t.name),
              "aria-valuetext": `${n}`,
              className: "param-slider w-full",
              style: { "--pct": f === u ? 0 : (n - u) / (f - u) }
            }
          ),
          /* @__PURE__ */ d(sb, { detents: k.detents, min: u, max: f, activeDetent: k.activeDetent })
        ]
      }
    ),
    /* @__PURE__ */ d(ge, { children: x ? /* @__PURE__ */ d(
      j.p,
      {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: y ? 0 : _.settle, ease: Va },
        className: "mono-caption text-accent-ink",
        children: x.end === "max" ? `${ft(f, l, h)} ${Fa} · widest this will go` : `${ft(u, l, h)} ${Fa} · thinnest this will go`
      }
    ) : null })
  ] });
}
function hb({
  id: e,
  param: t,
  value: n,
  dirty: i,
  onValue: r
}) {
  return /* @__PURE__ */ v("div", { className: "flex items-center gap-2 px-4 py-1", children: [
    /* @__PURE__ */ d(
      "label",
      {
        htmlFor: e,
        title: t.description,
        className: V("mono-caption min-w-0 truncate", i ? "font-medium text-ink" : "text-muted"),
        children: Ue(t.name)
      }
    ),
    i ? /* @__PURE__ */ d(dn, { param: t, onReset: () => r(t.default) }) : null,
    /* @__PURE__ */ d("span", { className: "flex-1" }),
    /* @__PURE__ */ d(
      "button",
      {
        id: e,
        type: "button",
        role: "switch",
        "aria-checked": n,
        "aria-label": Ue(t.name),
        onClick: () => r(!n),
        className: V(
          "relative h-4 w-7 shrink-0 rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
          n ? "bg-accent" : "bg-line"
        ),
        children: /* @__PURE__ */ d(
          "span",
          {
            className: V(
              "absolute top-0.5 size-3 rounded-full bg-ground transition-[left]",
              n ? "left-3.5" : "left-0.5"
            )
          }
        )
      }
    )
  ] });
}
function pb({
  id: e,
  param: t,
  value: n,
  dirty: i,
  onValue: r
}) {
  const o = D(n);
  return /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5 px-4", children: [
    /* @__PURE__ */ v("div", { className: "flex items-baseline justify-between gap-2", children: [
      /* @__PURE__ */ v("div", { className: "flex min-w-0 items-center gap-1.5", children: [
        /* @__PURE__ */ d(
          "label",
          {
            htmlFor: e,
            title: t.description,
            className: V("mono-caption min-w-0 truncate", i ? "font-medium text-ink" : "text-muted"),
            children: Ue(t.name)
          }
        ),
        i ? /* @__PURE__ */ d(dn, { param: t, onReset: () => r(t.default) }) : null
      ] }),
      n.length > Fi * 0.8 ? /* @__PURE__ */ v("span", { className: "mono-caption shrink-0 text-faint tabular-nums", children: [
        n.length,
        " / ",
        Fi
      ] }) : null
    ] }),
    /* @__PURE__ */ d(
      "input",
      {
        id: e,
        type: "text",
        value: n,
        maxLength: Fi,
        spellCheck: !1,
        autoComplete: "off",
        onFocus: () => {
          o.current = n;
        },
        onChange: (s) => r(s.target.value),
        onKeyDown: (s) => {
          s.key === "Escape" && r(o.current);
        },
        className: V(
          "w-full rounded-control border bg-raised px-2.5 py-1.5 text-sm text-ink outline-none transition-colors focus:border-accent",
          i ? "border-accent/60" : "border-line"
        )
      }
    )
  ] });
}
function mb({
  id: e,
  param: t,
  value: n,
  dirty: i,
  onValue: r
}) {
  const o = t.options ?? [], s = o.length <= 3 && o.every((a) => a.length <= 10);
  return /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5 px-4", children: [
    /* @__PURE__ */ v("div", { className: "flex min-w-0 items-center gap-1.5", children: [
      /* @__PURE__ */ d(
        "label",
        {
          htmlFor: e,
          id: `${e}-label`,
          title: t.description,
          className: V("mono-caption min-w-0 truncate", i ? "font-medium text-ink" : "text-muted"),
          children: Ue(t.name)
        }
      ),
      i ? /* @__PURE__ */ d(dn, { param: t, onReset: () => r(t.default) }) : null
    ] }),
    s ? /* @__PURE__ */ d(
      "div",
      {
        id: e,
        role: "radiogroup",
        "aria-labelledby": `${e}-label`,
        className: "grid overflow-hidden rounded-control border border-line",
        style: { gridTemplateColumns: `repeat(${o.length}, minmax(0, 1fr))` },
        children: o.map((a, l) => /* @__PURE__ */ d(
          "button",
          {
            type: "button",
            role: "radio",
            "aria-checked": a === n,
            onClick: () => r(a),
            className: V(
              "truncate px-2 py-1.5 text-xs capitalize transition-colors focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent",
              l > 0 && "border-l border-line",
              a === n ? "bg-raised font-medium text-ink" : "text-muted hover:text-ink"
            ),
            children: a
          },
          a
        ))
      }
    ) : /* @__PURE__ */ d(
      "select",
      {
        id: e,
        value: n,
        onChange: (a) => r(a.target.value),
        className: "w-full rounded-control border border-line bg-raised px-2 py-1.5 text-sm text-ink outline-none focus:border-accent",
        children: o.map((a) => /* @__PURE__ */ d("option", { value: a, children: a }, a))
      }
    )
  ] });
}
const Ba = [
  { name: "Black", hex: "#1a1a1a" },
  { name: "White", hex: "#f2f2ef" },
  { name: "Gray", hex: "#8e9094" },
  { name: "Red", hex: "#c8312a" },
  { name: "Orange", hex: "#f2752e" },
  { name: "Yellow", hex: "#f4c430" },
  { name: "Green", hex: "#3a9a4a" },
  { name: "Blue", hex: "#2a5bb8" }
];
function gb({
  id: e,
  param: t,
  value: n,
  dirty: i,
  onValue: r
}) {
  const o = n.toLowerCase(), s = Ba.some((a) => a.hex === o);
  return /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5 px-4", children: [
    /* @__PURE__ */ v("div", { className: "flex items-baseline justify-between gap-2", children: [
      /* @__PURE__ */ v("div", { className: "flex min-w-0 items-center gap-1.5", children: [
        /* @__PURE__ */ d(
          "span",
          {
            id: `${e}-label`,
            title: t.description,
            className: V("mono-caption min-w-0 truncate", i ? "font-medium text-ink" : "text-muted"),
            children: Ue(t.name)
          }
        ),
        i ? /* @__PURE__ */ d(dn, { param: t, onReset: () => r(t.default) }) : null
      ] }),
      /* @__PURE__ */ d("span", { className: V("mono-value shrink-0 uppercase", i ? "text-accent-ink" : "text-ink"), children: o })
    ] }),
    /* @__PURE__ */ v("div", { role: "radiogroup", "aria-labelledby": `${e}-label`, className: "flex items-center gap-1.5", children: [
      Ba.map((a) => /* @__PURE__ */ d(
        "button",
        {
          type: "button",
          role: "radio",
          "aria-checked": a.hex === o,
          "aria-label": a.name,
          title: a.name,
          onClick: () => r(a.hex),
          className: V(
            "size-5 shrink-0 rounded-control border border-line transition-shadow focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
            a.hex === o && "ring-2 ring-ink ring-offset-2 ring-offset-ground"
          ),
          style: { background: a.hex }
        },
        a.hex
      )),
      /* @__PURE__ */ d(
        "label",
        {
          title: "Any other color",
          className: V(
            "relative size-5 shrink-0 cursor-pointer overflow-hidden rounded-control border border-line focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent",
            !s && "ring-2 ring-ink ring-offset-2 ring-offset-ground"
          ),
          style: {
            background: s ? "conic-gradient(#e53935, #fdd835, #43a047, #1e88e5, #8e24aa, #e53935)" : o
          },
          children: /* @__PURE__ */ d(
            "input",
            {
              id: e,
              type: "color",
              value: o,
              onChange: (a) => r(a.target.value),
              "aria-label": `${Ue(t.name)}, any other color`,
              className: "absolute inset-0 cursor-pointer opacity-0"
            }
          )
        }
      )
    ] })
  ] });
}
function Zv({
  params: e,
  measurements: t,
  nozzle: n,
  values: i,
  onChange: r,
  onApply: o,
  building: s,
  applying: a,
  stats: l,
  error: c,
  note: u,
  onSuggestColors: f
}) {
  const h = de(() => e.filter(br), [e]), m = de(() => e.filter((C) => !br(C)), [e]), p = h.filter((C) => C.kind === "bool"), g = h.filter((C) => C.kind === "int" || C.kind === "float"), y = [...h.filter((C) => C.kind === "str"), ...h.filter((C) => C.kind === "choice")], b = h.filter((C) => C.kind === "color"), k = de(() => lb(e, i), [e, i]), x = Object.keys(k).length, S = Se(), E = (C, A) => {
    r({ ...i, [C]: A });
  };
  return h.length === 0 && !f ? null : /* @__PURE__ */ v("div", { className: "flex min-h-0 flex-1 flex-col", role: "group", "aria-label": "Part parameters", children: [
    c ? /* @__PURE__ */ v("div", { className: "border-b border-line-soft bg-fail-wash px-4 py-2.5", children: [
      /* @__PURE__ */ v("p", { className: "mono-label flex items-center gap-2 text-fail", children: [
        /* @__PURE__ */ d(z, { name: "warning" }),
        "Build failed at these values"
      ] }),
      /* @__PURE__ */ d("p", { className: "mt-1 text-xs leading-4 text-ink-soft", children: c }),
      /* @__PURE__ */ d("p", { className: "mt-0.5 text-xs leading-4 text-muted", children: "Showing the last part that built." })
    ] }) : null,
    /* @__PURE__ */ v("div", { className: "flex min-h-0 flex-1 flex-col overflow-y-auto pb-3", children: [
      m.length > 0 ? /* @__PURE__ */ v(U, { children: [
        /* @__PURE__ */ d(kn, { children: "Set by the plan" }),
        /* @__PURE__ */ d("dl", { className: "flex flex-col", children: m.map((C) => /* @__PURE__ */ v("div", { className: "flex items-center gap-[9px] px-4 py-1.5", title: C.description, children: [
          /* @__PURE__ */ d("span", { className: "text-muted", children: /* @__PURE__ */ d(z, { name: "lock" }) }),
          /* @__PURE__ */ d("dt", { className: "mono-id min-w-0 flex-1 truncate uppercase text-muted [letter-spacing:0.06em]", children: Ue(C.name) }),
          /* @__PURE__ */ d("dd", { className: "mono-value text-muted", children: String(i[C.name] ?? C.default) })
        ] }, C.name)) })
      ] }) : null,
      y.length > 0 ? /* @__PURE__ */ v(U, { children: [
        /* @__PURE__ */ d(kn, { children: "Yours to set" }),
        /* @__PURE__ */ d("div", { className: "flex flex-col gap-3 pb-2", children: y.map((C) => {
          const A = C.kind === "str" ? pb : mb;
          return /* @__PURE__ */ d(
            A,
            {
              id: `${S}${C.name}`,
              param: C,
              value: String(i[C.name] ?? C.default),
              dirty: C.name in k,
              onValue: (N) => E(C.name, N)
            },
            C.name
          );
        }) })
      ] }) : null,
      b.length > 0 || f ? /* @__PURE__ */ v(U, { children: [
        /* @__PURE__ */ d(kn, { children: "Colors" }),
        /* @__PURE__ */ v("div", { className: "flex flex-col gap-3 pb-2", children: [
          b.map((C) => /* @__PURE__ */ d(
            gb,
            {
              id: `${S}${C.name}`,
              param: C,
              value: String(i[C.name] ?? C.default),
              dirty: C.name in k,
              onValue: (A) => E(C.name, A)
            },
            C.name
          )),
          f ? /* @__PURE__ */ d("div", { className: "flex flex-col gap-1 px-4", children: /* @__PURE__ */ v(
            "button",
            {
              type: "button",
              title: "Writes the request in the chat for you to send",
              onClick: () => f(b.length > 0),
              className: "mono-label flex h-7 items-center justify-center gap-1.5 rounded-control border border-line text-ink-soft transition-colors hover:border-accent hover:text-ink focus-visible:outline-2 focus-visible:outline-accent",
              children: [
                /* @__PURE__ */ d(z, { name: "chat" }),
                b.length > 0 ? "Suggest other colors" : "Suggest colors"
              ]
            }
          ) }) : null
        ] })
      ] }) : null,
      p.length + g.length > 0 ? /* @__PURE__ */ d(kn, { children: "Yours to drag" }) : null,
      /* @__PURE__ */ v("div", { className: "flex flex-col gap-3", children: [
        p.map((C) => /* @__PURE__ */ d(
          hb,
          {
            id: `${S}${C.name}`,
            param: C,
            value: i[C.name] ?? C.default,
            dirty: C.name in k,
            onValue: (A) => E(C.name, A)
          },
          C.name
        )),
        g.map((C) => /* @__PURE__ */ d(
          db,
          {
            id: `${S}${C.name}`,
            param: C,
            value: i[C.name] ?? C.default,
            dirty: C.name in k,
            measurements: t,
            nozzle: n,
            onValue: (A) => E(C.name, A)
          },
          C.name
        ))
      ] })
    ] }),
    l?.size_mm ? /* @__PURE__ */ d("div", { className: "chrome shrink-0 border-t border-line-soft px-4 py-2", children: /* @__PURE__ */ v("span", { className: "mono-caption text-muted", children: [
      l.size_mm.map((C) => Math.round(C * 10) / 10).join(" × "),
      " mm",
      s ? " · rebuilding" : null
    ] }) }) : null,
    /* @__PURE__ */ d(
      "p",
      {
        role: "status",
        className: u ? "mx-4 mb-3 rounded-content bg-raised px-3 py-2 text-xs leading-4 text-ink-soft" : "sr-only",
        children: u
      }
    ),
    x > 0 ? /* @__PURE__ */ v("div", { className: "chrome mx-4 mb-3 flex flex-col gap-2 rounded-content bg-accent-wash p-2 pl-3", children: [
      /* @__PURE__ */ v("div", { className: "flex h-6 items-center gap-2", children: [
        /* @__PURE__ */ d("span", { className: "size-1.5 shrink-0 rounded-full bg-accent" }),
        /* @__PURE__ */ v("span", { className: "mono-id flex-1 whitespace-nowrap uppercase text-accent-ink tabular-nums [letter-spacing:0.08em]", children: [
          x,
          " ",
          x === 1 ? "change" : "changes"
        ] }),
        /* @__PURE__ */ d(
          "button",
          {
            type: "button",
            onClick: () => r({}),
            className: "mono-label shrink-0 rounded-control px-2 py-1 text-ink-soft transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-accent",
            children: "Reset"
          }
        )
      ] }),
      /* @__PURE__ */ d("span", { className: "flex [&>*]:w-full", title: "Make these values the part's defaults, so it opens and downloads this way.", children: /* @__PURE__ */ d(
        ib,
        {
          label: "Save as default",
          pendingLabel: "Saving",
          successLabel: "Saved",
          errorLabel: "Try again",
          resetAfter: 1400,
          variant: "ink",
          disabled: a,
          onAction: () => o(k)
        }
      ) })
    ] }) : null
  ] });
}
const Fu = Tr(function({ anchor: t, width: n, align: i = "right", gap: r = 6, className: o, children: s, ...a }, l) {
  const [c, u] = B(null), f = Q(() => {
    const h = t.current?.getBoundingClientRect();
    if (!h) return;
    const m = i === "right" ? h.right - n : h.left;
    u({
      left: Math.max(8, Math.min(m, window.innerWidth - n - 8)),
      bottom: Math.max(8, window.innerHeight - h.top + r)
    });
  }, [t, n, i, r]);
  return Nt(f, [f]), O(() => (window.addEventListener("resize", f), window.addEventListener("scroll", f, !0), () => {
    window.removeEventListener("resize", f), window.removeEventListener("scroll", f, !0);
  }), [f]), typeof document > "u" ? null : Za(
    /* @__PURE__ */ d(
      "div",
      {
        ref: l,
        style: { position: "fixed", left: c?.left ?? 0, bottom: c?.bottom ?? 0, width: n },
        className: o,
        ...a,
        children: s
      }
    ),
    document.body
  );
}), Iu = [
  { format: "3mf", caption: "Print-ready, keeps units and orientation.", recommended: !0 },
  { format: "stl", caption: "Print-ready mesh. Works in every slicer." },
  { format: "step", caption: "Solid model, for another CAD tool." }
];
function yb(e) {
  if (e.state === "queued") return "Estimate · slicing…";
  if (e.state === "failed") return `Estimate · ${e.error ?? "unavailable"}`;
  const t = [
    e.grams ? `${Math.round(e.grams)} g` : null,
    e.seconds ? `${(e.seconds / 3600).toFixed(1)} hr` : null
  ].filter(Boolean);
  return `Estimate · ${t.length ? t.join(" · ") : "unavailable"}`;
}
const Ou = "nurb.exportFormat";
function xb() {
  try {
    const e = localStorage.getItem(Ou);
    if (Iu.some((t) => t.format === e)) return e;
  } catch {
  }
  return "3mf";
}
function Jv({ partId: e, export: t, status: n, revision: i, runId: r, openIn: o }) {
  const [s, a] = B(xb), [l, c] = B(!1), [u, f] = B(null), [h, m] = B(null), p = D(null), g = D(null), y = D(null), b = D(null), k = D(0), x = D({ partId: e, revision: i, runId: r });
  O(() => {
    const A = x.current;
    A.partId === e && Object.is(A.revision, i) && Object.is(A.runId, r) || (x.current = { partId: e, revision: i, runId: r }, k.current += 1, f(null), m(null));
  }, [e, i, r]), O(() => {
    if (!l) return;
    const A = (P) => {
      const w = P.target;
      p.current?.contains(w) || b.current?.contains(w) || c(!1);
    }, N = (P) => {
      if (P.key === "Escape") {
        c(!1), g.current?.focus();
        return;
      }
      if (P.key !== "ArrowDown" && P.key !== "ArrowUp") return;
      const w = Array.from(y.current?.querySelectorAll('[role="menuitem"]') ?? []);
      if (w.length === 0) return;
      P.preventDefault();
      const T = P.key === "ArrowDown" ? 1 : -1, I = w.indexOf(document.activeElement), F = I === -1 ? T === 1 ? 0 : w.length - 1 : (I + T + w.length) % w.length;
      w[F].focus();
    };
    return document.addEventListener("pointerdown", A), document.addEventListener("keydown", N), () => {
      document.removeEventListener("pointerdown", A), document.removeEventListener("keydown", N);
    };
  }, [l]);
  const S = async (A, N) => {
    const P = ++k.current;
    f(A), m(null);
    try {
      await N(), P === k.current && c(!1);
    } catch (w) {
      if (P !== k.current) return;
      m(w instanceof Error ? w.message : "The export did not finish."), c(!0);
    } finally {
      P === k.current && f(null);
    }
  }, E = (A) => S(A, () => t(A)), C = (A) => {
    a(A);
    try {
      localStorage.setItem(Ou, A);
    } catch {
    }
    E(A);
  };
  return /* @__PURE__ */ v("div", { ref: p, className: "relative flex-1", children: [
    /* @__PURE__ */ v("div", { className: "flex h-9 w-full overflow-hidden rounded-control bg-accent text-white", children: [
      /* @__PURE__ */ v(
        "button",
        {
          type: "button",
          disabled: u !== null,
          onClick: () => {
            E(s);
          },
          className: "chrome btn-label inline-flex flex-1 items-center justify-center gap-2 px-3 transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-white disabled:hover:bg-transparent",
          children: [
            /* @__PURE__ */ d(z, { name: "download" }),
            u ? "Preparing…" : `Download ${s.toUpperCase()}`
          ]
        }
      ),
      /* @__PURE__ */ d(
        "button",
        {
          ref: g,
          type: "button",
          "aria-haspopup": "menu",
          "aria-expanded": l,
          "aria-label": "Choose file type",
          title: "Choose file type",
          onClick: () => c((A) => !A),
          className: "inline-flex w-9 shrink-0 items-center justify-center border-l border-white/25 transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-white",
          children: /* @__PURE__ */ d(z, { name: "chevron-down" })
        }
      )
    ] }),
    l ? /* @__PURE__ */ v(
      Fu,
      {
        ref: b,
        anchor: g,
        width: 254,
        align: "left",
        gap: 8,
        className: "z-30 overflow-hidden rounded-content border border-panel-edge bg-ground shadow-[var(--shadow-panel)]",
        children: [
          /* @__PURE__ */ v("div", { className: "chrome flex h-[30px] items-center justify-between border-b border-line-soft px-3", children: [
            /* @__PURE__ */ d("span", { className: "mono-label text-muted", children: "File type" }),
            i != null ? /* @__PURE__ */ d("span", { className: "mono-caption text-muted", children: Zt(i) }) : null
          ] }),
          h ? /* @__PURE__ */ v("div", { className: "border-b border-line-soft bg-fail-wash px-3 py-2 text-[11px] leading-4 text-ink-soft", children: [
            /* @__PURE__ */ d("p", { className: "mono-label text-fail", children: "Download failed" }),
            /* @__PURE__ */ d("p", { className: "mt-0.5", children: h })
          ] }) : null,
          /* @__PURE__ */ v(
            "div",
            {
              ref: y,
              role: "menu",
              "aria-label": "Download format",
              className: "flex flex-col py-1",
              children: [
                Iu.map((A) => {
                  const N = u === A.format, P = s === A.format;
                  return /* @__PURE__ */ v(
                    "button",
                    {
                      type: "button",
                      role: "menuitem",
                      disabled: u !== null,
                      "aria-current": P || void 0,
                      onClick: () => C(A.format),
                      className: V(
                        "flex w-full flex-col gap-0.5 px-3 py-2 text-left transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none disabled:opacity-60 disabled:hover:bg-transparent",
                        P && "bg-raised/60"
                      ),
                      children: [
                        /* @__PURE__ */ v("span", { className: "flex w-full items-center", children: [
                          /* @__PURE__ */ d("span", { className: "mono-value uppercase text-ink", children: A.format }),
                          P ? /* @__PURE__ */ d(z, { name: "check", className: "ml-1.5 text-accent-ink" }) : null,
                          N ? /* @__PURE__ */ v("span", { className: "mono-caption ml-auto flex items-center gap-1.5 text-muted", children: [
                            /* @__PURE__ */ d("span", { className: "size-1.5 rounded-full bg-accent" }),
                            "preparing"
                          ] }) : A.recommended ? /* @__PURE__ */ d("span", { className: "mono-caption ml-auto text-accent-ink", children: "Recommended" }) : null
                        ] }),
                        /* @__PURE__ */ d("span", { className: "text-xs leading-4 text-ink-soft", children: A.caption })
                      ]
                    },
                    A.format
                  );
                }),
                o ? /* @__PURE__ */ v(
                  "button",
                  {
                    type: "button",
                    role: "menuitem",
                    disabled: u !== null,
                    onClick: () => {
                      S("slicer", o.open);
                    },
                    className: "mt-1 flex w-full flex-col gap-0.5 border-t border-line-soft px-3 pt-2.5 pb-2 text-left transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none disabled:opacity-60 disabled:hover:bg-transparent",
                    children: [
                      /* @__PURE__ */ v("span", { className: "flex w-full items-center", children: [
                        /* @__PURE__ */ v("span", { className: "mono-value uppercase text-ink", children: [
                          "Open in ",
                          o.name
                        ] }),
                        u === "slicer" ? /* @__PURE__ */ v("span", { className: "mono-caption ml-auto flex items-center gap-1.5 text-muted", children: [
                          /* @__PURE__ */ d("span", { className: "size-1.5 rounded-full bg-accent" }),
                          "preparing"
                        ] }) : null
                      ] }),
                      /* @__PURE__ */ d("span", { className: "text-xs leading-4 text-ink-soft", children: "Saves a 3MF and opens it there." })
                    ]
                  }
                ) : null
              ]
            }
          ),
          n ? /* @__PURE__ */ d("div", { className: "chrome border-t border-line-soft bg-raised px-3 py-2", children: /* @__PURE__ */ d("span", { className: "mono-caption text-muted", children: yb(n) }) }) : null
        ]
      }
    ) : null
  ] });
}
function e2({
  printers: e,
  current: t,
  defaultName: n,
  onPick: i,
  onAdd: r,
  onManage: o,
  triggerRef: s,
  onClose: a
}) {
  const l = D(null);
  return O(() => {
    const c = (f) => {
      const h = f.target;
      l.current?.contains(h) || s.current?.contains(h) || a();
    }, u = (f) => {
      f.key === "Escape" && a();
    };
    return document.addEventListener("pointerdown", c), document.addEventListener("keydown", u), () => {
      document.removeEventListener("pointerdown", c), document.removeEventListener("keydown", u);
    };
  }, [a, s]), /* @__PURE__ */ v(
    Fu,
    {
      ref: l,
      anchor: s,
      width: 254,
      align: "right",
      gap: 6,
      role: "menu",
      "aria-label": "Print on",
      className: "z-30 overflow-hidden rounded-[6px] border border-panel-edge bg-ground shadow-[var(--shadow-panel)]",
      children: [
        /* @__PURE__ */ v("div", { className: "flex h-6 items-center justify-between px-3 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase", children: [
          /* @__PURE__ */ d("span", { children: "Print on" }),
          /* @__PURE__ */ d("span", { children: "This part" })
        ] }),
        e.map((c) => {
          const u = c.name === t;
          return /* @__PURE__ */ v(
            "button",
            {
              type: "button",
              role: "menuitemradio",
              "aria-checked": u,
              onClick: () => i(c.name),
              className: V(
                "chrome flex h-7 w-full items-center gap-2 px-3 text-left font-mono text-[10.5px] leading-4 transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none",
                u ? "text-ink" : "text-ink-soft hover:text-ink"
              ),
              children: [
                /* @__PURE__ */ d("span", { className: "flex size-3 shrink-0 items-center justify-center", children: u ? /* @__PURE__ */ d(z, { name: "check" }) : null }),
                /* @__PURE__ */ d("span", { className: "min-w-0 flex-1 truncate", children: c.label }),
                c.name === n ? /* @__PURE__ */ d("span", { className: "shrink-0 rounded-[2px] border border-line px-1 font-mono text-[9px] leading-[14px] tracking-[0.08em] text-muted uppercase", children: "Default" }) : null
              ]
            },
            c.name
          );
        }),
        /* @__PURE__ */ d("div", { className: "border-t border-line-soft", role: "separator" }),
        /* @__PURE__ */ v(
          "button",
          {
            type: "button",
            role: "menuitem",
            onClick: r,
            className: "chrome flex h-7 w-full items-center gap-2 px-3 text-left font-mono text-[10.5px] leading-4 text-accent-ink transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none",
            children: [
              /* @__PURE__ */ d("span", { className: "size-3 shrink-0" }),
              /* @__PURE__ */ d("span", { className: "min-w-0 flex-1 truncate", children: "+ Add a printer" })
            ]
          }
        ),
        o ? /* @__PURE__ */ v(
          "button",
          {
            type: "button",
            role: "menuitem",
            onClick: o,
            className: "chrome flex w-full items-center gap-2 border-t border-line-soft bg-raised px-3 py-2 text-left font-mono text-[9.5px] leading-3 tracking-[0.08em] text-muted uppercase transition-colors hover:text-ink focus-visible:outline-none",
            children: [
              /* @__PURE__ */ d("span", { className: "min-w-0 flex-1 truncate", children: "Manage printers in Settings" }),
              /* @__PURE__ */ d("span", { className: "shrink-0 rotate-180", children: /* @__PURE__ */ d(z, { name: "chevron-left" }) })
            ]
          }
        ) : null
      ]
    }
  );
}
function Ps({
  label: e,
  trailing: t,
  inset: n = 18
}) {
  return /* @__PURE__ */ v(
    "div",
    {
      className: `chrome flex h-[30px] shrink-0 items-center justify-between border-b border-line-soft ${n === 16 ? "px-4" : "px-[18px]"}`,
      children: [
        /* @__PURE__ */ d("div", { className: "mono-label shrink-0 text-muted", children: e }),
        t ? /* @__PURE__ */ d("div", { className: "mono-caption min-w-0 text-muted tabular-nums [letter-spacing:0.1em]", children: t }) : null
      ]
    }
  );
}
const bb = (e) => e && e.length === 3 ? e.map((t) => Math.round(t)).join(" × ") : "";
function t2({
  catalogue: e,
  owned: t,
  busy: n,
  error: i,
  onAdd: r,
  onClose: o
}) {
  const [s, a] = B(""), [l, c] = B(null), u = de(() => new Set(t), [t]);
  O(() => {
    const h = (m) => {
      m.key === "Escape" && o();
    };
    return window.addEventListener("keydown", h), () => window.removeEventListener("keydown", h);
  }, [o]);
  const f = de(() => {
    const h = s.trim().toLowerCase(), m = h ? e.filter((y) => y.label.toLowerCase().includes(h)) : e, p = [], g = /* @__PURE__ */ new Map();
    for (const y of m)
      g.has(y.brand) || (g.set(y.brand, []), p.push(y.brand)), g.get(y.brand).push(y);
    return p.map((y) => ({ brand: y, rows: g.get(y) }));
  }, [e, s]);
  return /* @__PURE__ */ d(
    "div",
    {
      className: "fixed inset-0 z-50 flex items-center justify-center bg-scrim/30 p-6",
      onClick: (h) => h.target === h.currentTarget && o(),
      children: /* @__PURE__ */ v(
        "div",
        {
          className: "panel flex max-h-full w-[520px] flex-col overflow-hidden",
          role: "dialog",
          "aria-modal": "true",
          "aria-label": "Add a printer",
          children: [
            /* @__PURE__ */ d(
              Ps,
              {
                label: "Add a printer",
                inset: 16,
                trailing: /* @__PURE__ */ d(Ns, { icon: "xmark", label: "Close", onClick: o, className: "-mr-2" })
              }
            ),
            /* @__PURE__ */ v("div", { className: "flex shrink-0 flex-col gap-3 px-5 pt-4", children: [
              /* @__PURE__ */ d("p", { className: "text-[13.5px] leading-[18px] text-ink-soft", children: "Pick the machine on your bench. Checks use its bed size; the slicer brings its own profile." }),
              /* @__PURE__ */ v("div", { className: "flex h-8 shrink-0 items-center gap-2 rounded-[3px] border border-line bg-ground px-2.5", children: [
                /* @__PURE__ */ d("span", { className: "shrink-0 text-faint", children: /* @__PURE__ */ d(z, { name: "search" }) }),
                /* @__PURE__ */ d(
                  "input",
                  {
                    name: "printer-search",
                    "aria-label": "Search printers",
                    placeholder: "SEARCH PRINTERS",
                    value: s,
                    onChange: (h) => a(h.target.value),
                    autoFocus: !0,
                    className: "min-w-0 flex-1 bg-transparent font-mono text-[10.5px] tracking-[0.08em] text-ink uppercase placeholder:text-faint focus:outline-none"
                  }
                )
              ] })
            ] }),
            /* @__PURE__ */ d("div", { className: "mt-3 min-h-0 flex-1 overflow-y-auto border-t border-line-soft", children: f.length === 0 ? /* @__PURE__ */ d("p", { className: "px-5 py-4 text-[13px] leading-[18px] text-muted", children: "No printer matches that." }) : f.map((h) => /* @__PURE__ */ v("div", { className: "flex flex-col", children: [
              /* @__PURE__ */ d("div", { className: "flex h-6 items-center bg-raised px-5 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase", children: h.brand }),
              h.rows.map((m) => {
                const p = u.has(m.name), g = l === m.name;
                return /* @__PURE__ */ v(
                  "button",
                  {
                    type: "button",
                    disabled: p,
                    "aria-pressed": g,
                    onClick: () => c(m.name),
                    className: V(
                      "chrome flex h-[30px] w-full items-center gap-2 px-5 text-left transition-colors focus-visible:outline-none",
                      p ? "cursor-default text-faint" : g ? "bg-accent-wash text-ink" : "text-ink-soft hover:bg-raised hover:text-ink"
                    ),
                    children: [
                      /* @__PURE__ */ d("span", { className: "flex size-3 shrink-0 items-center justify-center", children: g ? /* @__PURE__ */ d(z, { name: "check" }) : null }),
                      /* @__PURE__ */ d("span", { className: "min-w-0 flex-1 truncate font-mono text-[11px] leading-4", children: m.label }),
                      /* @__PURE__ */ d("span", { className: "shrink-0 font-mono text-[10px] leading-4 tracking-[0.08em] text-muted tabular-nums", children: p ? "On your bench" : bb(m.bed) })
                    ]
                  },
                  m.name
                );
              })
            ] }, h.brand)) }),
            i ? /* @__PURE__ */ d("p", { className: "shrink-0 bg-fail-wash px-5 py-2 text-[12px] leading-4 text-fail", role: "alert", children: i }) : null,
            /* @__PURE__ */ v("div", { className: "flex shrink-0 items-center gap-4 border-t border-line-soft px-5 py-4", children: [
              /* @__PURE__ */ d("p", { className: "min-w-0 flex-1 text-[12px] leading-4 text-muted", children: "Not listed? Pick the one with the closest bed size. That is all the checks use." }),
              /* @__PURE__ */ d(Me, { size: "md", className: "px-3.5", onClick: o, children: "Cancel" }),
              /* @__PURE__ */ d(
                Me,
                {
                  variant: "accent",
                  size: "md",
                  className: "px-3.5",
                  disabled: !l || n,
                  onClick: () => l && r(l),
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
const vb = "" + new URL("nurb-lockup.svg", import.meta.url).href, wb = "" + new URL("nurb-mark-16.svg", import.meta.url).href, kb = "" + new URL("nurb-mark-outline.svg", import.meta.url).href, Tb = "" + new URL("nurb-mark-small.svg", import.meta.url).href, Sb = "" + new URL("favicon.svg", import.meta.url).href, Ab = "" + new URL("auth-plane.svg", import.meta.url).href, Cb = "" + new URL("ghost-bracket.svg", import.meta.url).href, Nb = "" + new URL("404-squiggle.svg", import.meta.url).href, Bu = { lockup: vb, mark: wb, markOutline: kb, markSmall: Tb, favicon: Sb, authPlane: Ab, ghostBracket: Cb, squiggle: Nb }, ju = (e) => ({
  WebkitMask: `url("${e}") center / contain no-repeat`,
  mask: `url("${e}") center / contain no-repeat`
}), Ot = 240, Tn = 148;
function Ke(e, t, n) {
  return [(e - t) * 0.866, (e + t) * 0.5 - n];
}
function Pb({ bbox: e, ghost: t = !1, className: n }) {
  const i = e && e.length === 3 && e.every((w) => w > 0) ? e : null, r = i ?? [1, 1, 1], o = Math.max(...r), [s, a, l] = r.map((w) => w / o), c = [
    Ke(0, 0, 0),
    Ke(s, 0, 0),
    Ke(s, a, 0),
    Ke(0, a, 0),
    Ke(0, 0, l),
    Ke(s, 0, l),
    Ke(s, a, l),
    Ke(0, a, l)
  ], u = c.map((w) => w[0]), f = c.map((w) => w[1]), h = Math.min(...u), m = Math.max(...u), p = Math.min(...f), g = Math.max(...f), y = Math.min((Ot - 60) / (m - h), (Tn - 40) / (g - p)), b = Ot / 2 - (h + m) / 2 * y, k = Tn / 2 - (p + g) / 2 * y, x = (w) => `${(c[w][0] * y + b).toFixed(1)},${(c[w][1] * y + k).toFixed(1)}`, S = `${x(4)} ${x(5)} ${x(6)} ${x(7)}`, E = `${x(3)} ${x(2)} ${x(6)} ${x(7)}`, C = `${x(1)} ${x(2)} ${x(6)} ${x(5)}`, A = Ot / 2, N = Math.max(...c.map((w) => w[1])) * y + k + 6, P = (m - h) * y / 2 + 8;
  return t || !i ? /* @__PURE__ */ d("svg", { viewBox: `0 0 ${Ot} ${Tn}`, className: n, "aria-hidden": "true", children: /* @__PURE__ */ v("g", { fill: "none", stroke: "var(--color-panel-edge)", strokeWidth: "1.5", strokeLinejoin: "round", strokeDasharray: "5 4", children: [
    /* @__PURE__ */ d("polygon", { points: S }),
    /* @__PURE__ */ d("polygon", { points: E }),
    /* @__PURE__ */ d("polygon", { points: C })
  ] }) }) : /* @__PURE__ */ v("svg", { viewBox: `0 0 ${Ot} ${Tn}`, className: n, "aria-hidden": "true", children: [
    /* @__PURE__ */ d("ellipse", { cx: A, cy: N, rx: P, ry: P * 0.16, fill: "var(--color-raised)" }),
    /* @__PURE__ */ v("g", { stroke: "var(--color-part-edge)", strokeWidth: "1.2", strokeLinejoin: "round", children: [
      /* @__PURE__ */ d("polygon", { points: S, fill: "var(--color-part-top)" }),
      /* @__PURE__ */ d("polygon", { points: E, fill: "var(--color-part-front)" }),
      /* @__PURE__ */ d("polygon", { points: C, fill: "var(--color-part-side)" })
    ] })
  ] });
}
const Mb = Z.out;
function Eb({
  label: e,
  items: t,
  align: n = "right",
  above: i,
  className: r,
  menuClassName: o,
  trigger: s,
  footer: a,
  portal: l,
  disabled: c,
  triggerClassName: u,
  onOpenChange: f,
  filter: h
}) {
  const [m, p] = B(!1), [g, y] = B(""), [b, k] = B(), x = D(null), S = D(null), E = D(null), C = Se(), A = D(f);
  A.current = f, O(() => {
    A.current?.(m), m || y("");
  }, [m]);
  const N = g.trim().toLowerCase(), P = N ? t.filter((w) => typeof w.label == "string" && w.label.toLowerCase().includes(N)) : t;
  return Nt(() => {
    if (!m || !l) return;
    const w = E.current?.getBoundingClientRect();
    w && k({
      position: "fixed",
      ...i ? { bottom: window.innerHeight - w.top + 4 } : { top: w.bottom + 4 },
      ...n === "right" ? { right: window.innerWidth - w.right } : { left: w.left }
    });
  }, [m, l, n, i]), O(() => {
    if (!m) return;
    const w = (I) => {
      const F = I.target;
      !x.current?.contains(F) && !S.current?.contains(F) && p(!1);
    }, T = (I) => {
      I.key === "Escape" && (p(!1), E.current?.focus());
    };
    return document.addEventListener("pointerdown", w), document.addEventListener("keydown", T), () => {
      document.removeEventListener("pointerdown", w), document.removeEventListener("keydown", T);
    };
  }, [m]), /* @__PURE__ */ v("div", { ref: x, className: V("relative", r), children: [
    /* @__PURE__ */ d(
      "button",
      {
        ref: E,
        type: "button",
        "aria-label": e,
        title: e,
        "aria-haspopup": "menu",
        "aria-expanded": m,
        "aria-controls": C,
        disabled: c,
        onClick: (w) => {
          w.preventDefault(), w.stopPropagation(), p((T) => !T);
        },
        onKeyDown: (w) => w.stopPropagation(),
        className: V(
          "chrome inline-flex items-center justify-center rounded-[3px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          u ?? (s ? "rounded-full" : "size-5"),
          !s && (m ? "bg-raised text-ink" : "text-muted hover:bg-raised hover:text-ink")
        ),
        children: s ? s(m) : /* @__PURE__ */ d(z, { name: "dots" })
      }
    ),
    _u(
      l,
      /* @__PURE__ */ d(ge, { children: m ? /* @__PURE__ */ v(
        zu,
        {
          id: C,
          ref: S,
          style: l ? b : void 0,
          className: V(
            "z-30 min-w-[168px] overflow-hidden rounded-[6px] border border-panel-edge bg-ground shadow-[var(--shadow-panel)]",
            a ? "pt-1" : "py-1",
            !l && (i ? "absolute bottom-full mb-1" : "absolute top-full mt-1"),
            !l && (n === "right" ? "right-0" : "left-0"),
            o
          ),
          children: [
            h ? /* @__PURE__ */ v("div", { className: "sticky top-0 z-10 -mt-1 mb-1 flex h-8 items-center gap-2 border-b border-line-soft bg-ground px-3", children: [
              /* @__PURE__ */ d(z, { name: "search", className: "text-muted" }),
              /* @__PURE__ */ d(
                "input",
                {
                  autoFocus: !0,
                  value: g,
                  onChange: (w) => y(w.target.value),
                  onKeyDown: (w) => {
                    w.key === "Enter" && P[0] && (P[0].onSelect(), p(!1));
                  },
                  placeholder: h,
                  "aria-label": h,
                  className: "mono-id min-w-0 flex-1 bg-transparent text-ink outline-none placeholder:text-faint"
                }
              )
            ] }) : null,
            h && P.length === 0 ? /* @__PURE__ */ d("div", { className: "mono-id flex h-7 items-center px-3 text-faint", children: "Nothing matches" }) : null,
            /* @__PURE__ */ d(
              $u,
              {
                items: P,
                onPick: (w) => {
                  w.onSelect(), w.keepOpen || p(!1);
                }
              }
            ),
            a ? /* @__PURE__ */ d("div", { className: "sticky bottom-0 mt-1 border-t border-line-soft bg-raised px-3 py-2 font-mono text-[9.5px] leading-3 tracking-[0.08em] text-muted uppercase", children: a }) : null
          ]
        }
      ) : null })
    )
  ] });
}
function Db() {
  const [e, t] = B(null), [n, i] = B(), r = D(null), o = Se();
  Nt(() => {
    if (!e || !r.current) return;
    const { width: l, height: c } = r.current.getBoundingClientRect();
    i({
      position: "fixed",
      left: Math.max(8, Math.min(e.x, window.innerWidth - l - 8)),
      top: Math.max(8, Math.min(e.y, window.innerHeight - c - 8))
    });
  }, [e]), O(() => {
    if (!e) return;
    const l = (f) => {
      r.current?.contains(f.target) || t(null);
    }, c = (f) => f.key === "Escape" && t(null), u = () => t(null);
    return document.addEventListener("pointerdown", l, !0), document.addEventListener("keydown", c), window.addEventListener("blur", u), window.addEventListener("scroll", u, !0), () => {
      document.removeEventListener("pointerdown", l, !0), document.removeEventListener("keydown", c), window.removeEventListener("blur", u), window.removeEventListener("scroll", u, !0);
    };
  }, [e]);
  const s = (l, c) => {
    c?.length && (l.preventDefault(), l.stopPropagation(), i({ position: "fixed", left: l.clientX, top: l.clientY, visibility: "hidden" }), t({ x: l.clientX, y: l.clientY, items: c }));
  }, a = _u(
    !0,
    /* @__PURE__ */ d(ge, { children: e ? /* @__PURE__ */ d(
      zu,
      {
        id: o,
        ref: r,
        style: n,
        className: "z-30 min-w-[168px] overflow-hidden rounded-[6px] border border-panel-edge bg-ground py-1 shadow-[var(--shadow-panel)]",
        children: /* @__PURE__ */ d(
          $u,
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
  return { open: s, menu: a };
}
function $u({ items: e, onPick: t }) {
  const n = e.some((i) => i.checked !== void 0);
  return /* @__PURE__ */ d(U, { children: e.map((i, r) => /* @__PURE__ */ v(kr, { children: [
    i.section && i.section !== e[r - 1]?.section ? /* @__PURE__ */ v(U, { children: [
      r > 0 ? /* @__PURE__ */ d("div", { className: "my-1 border-t border-line-soft", role: "separator" }) : null,
      /* @__PURE__ */ d("div", { className: "flex h-6 items-center px-3 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase", children: i.section })
    ] }) : null,
    /* @__PURE__ */ v(
      "button",
      {
        type: "button",
        role: i.checkbox ? "menuitemcheckbox" : n ? "menuitemradio" : "menuitem",
        "aria-checked": n ? !!i.checked : void 0,
        disabled: i.disabled,
        title: i.title,
        onClick: (o) => {
          o.preventDefault(), o.stopPropagation(), t(i);
        },
        className: V(
          "chrome mono-id flex h-7 w-full items-center gap-2 px-3 text-left transition-colors focus-visible:bg-raised focus-visible:outline-none disabled:text-faint disabled:hover:bg-transparent",
          i.separated && "mt-1 border-t border-line-soft pt-px",
          i.tone === "danger" ? "text-fail hover:bg-fail-wash" : i.checked ? "text-ink hover:bg-raised" : "text-ink-soft hover:bg-raised hover:text-ink"
        ),
        children: [
          n ? /* @__PURE__ */ d("span", { className: "flex size-3 shrink-0 items-center justify-center", children: i.checked ? /* @__PURE__ */ d(z, { name: "check" }) : null }) : null,
          i.icon ? /* @__PURE__ */ d(z, { name: i.icon }) : null,
          /* @__PURE__ */ d("span", { className: "min-w-0 flex-1 truncate", children: i.label }),
          i.trailing ? /* @__PURE__ */ d("span", { className: "shrink-0", children: i.trailing }) : null
        ]
      }
    )
  ] }, r)) });
}
function zu({
  id: e,
  ref: t,
  style: n,
  className: i,
  children: r
}) {
  const o = Km();
  return /* @__PURE__ */ d(
    j.div,
    {
      id: e,
      ref: t,
      role: o ? "menu" : "presentation",
      "aria-hidden": o ? void 0 : !0,
      initial: { opacity: 0, y: -4 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -4 },
      transition: { duration: _.tick, ease: Mb },
      style: n,
      className: i,
      children: r
    }
  );
}
function _u(e, t) {
  return e && typeof document < "u" ? Za(t, document.body) : t;
}
const Uu = Z.out, Wu = 2.5, Sn = 20, Rb = 10;
function Lb({
  onConfirm: e,
  holdMs: t = 1800,
  disabled: n = !1
}) {
  const [i, r] = B(0), [o, s] = B("idle"), a = D("idle"), l = D(!1), c = D(0), u = D(0), f = D(0), h = D(null), m = D(e);
  m.current = e;
  const p = Q((x) => {
    a.current = x, s(x);
  }, []), g = Q(() => {
    cancelAnimationFrame(f.current), f.current = 0, l.current = !1, c.current = 0, h.current = null, r(0), p("idle");
  }, [p]), y = Q(
    (x) => {
      if (n || a.current === "committed" || a.current === "holding" || (h.current = x ?? null, l.current = !0, p("holding"), qe("press"), f.current)) return;
      u.current = performance.now();
      const S = (E) => {
        const C = Math.min(64, E - u.current);
        if (u.current = E, c.current += l.current ? C : -C * Wu, c.current >= t) {
          f.current = 0, c.current = t, l.current = !1, h.current = null, r(Sn), p("committed"), m.current();
          return;
        }
        if (c.current <= 0) {
          f.current = 0, c.current = 0, h.current = null, r(0), p("idle");
          return;
        }
        const A = Math.min(Sn, Math.floor(c.current / t * Sn));
        r((N) => N === A ? N : A), f.current = requestAnimationFrame(S);
      };
      f.current = requestAnimationFrame(S);
    },
    [n, t, p]
  ), b = Q(() => {
    a.current === "holding" && (l.current = !1, h.current = null, p("releasing"));
  }, [p]);
  return O(() => {
    const x = () => b(), S = () => {
      document.hidden && b();
    };
    return window.addEventListener("blur", x), document.addEventListener("visibilitychange", S), () => {
      window.removeEventListener("blur", x), document.removeEventListener("visibilitychange", S), cancelAnimationFrame(f.current), f.current = 0;
    };
  }, [b]), { bind: {
    onPointerDown: (x) => {
      x.pointerType === "mouse" && x.button !== 0 || (x.currentTarget.setPointerCapture?.(x.pointerId), y({ x: x.clientX, y: x.clientY }));
    },
    onPointerMove: (x) => {
      const S = h.current;
      a.current !== "holding" || !S || Math.hypot(x.clientX - S.x, x.clientY - S.y) > Rb && b();
    },
    onPointerUp: b,
    onPointerCancel: b,
    onPointerLeave: b,
    onKeyDown: (x) => {
      if (x.key === "Escape") {
        (a.current === "holding" || a.current === "releasing") && (x.preventDefault(), g());
        return;
      }
      x.repeat || (x.key === " " || x.key === "Enter") && (x.preventDefault(), y());
    },
    onKeyUp: (x) => {
      (x.key === " " || x.key === "Enter") && b();
    },
    onBlur: b,
    onClick: (x) => x.preventDefault(),
    onContextMenu: (x) => x.preventDefault()
  }, phase: o, progress: i / Sn, reset: g };
}
function Vb({
  label: e,
  confirmLabel: t = "Confirmed",
  holdMs: n = 1800,
  onConfirm: i,
  variant: r = "danger",
  disabled: o = !1,
  className: s
}) {
  const { bind: a, phase: l, reset: c } = Lb({ onConfirm: i, holdMs: n, disabled: o }), u = ne(), f = Se(), h = l === "committed", m = Math.round(n / 100) / 10, p = Gc(0), g = r0(p, (y) => `inset(0 ${(1 - y) * 100}% 0 0)`);
  return O(() => {
    if (!h) return;
    const y = setTimeout(c, 1600);
    return () => clearTimeout(y);
  }, [h, c]), O(() => {
    if (u) {
      p.set(l === "holding" || l === "committed" ? 1 : 0);
      return;
    }
    if (l === "committed") {
      const k = Ei(p, 1, { duration: _.tick, ease: "linear" });
      return () => k.stop();
    }
    const y = p.get();
    if (l === "holding") {
      const k = Ei(p, 1, { duration: n * (1 - y) / 1e3, ease: "linear" });
      return () => k.stop();
    }
    const b = Ei(p, 0, { duration: n * y / Wu / 1e3, ease: Uu });
    return () => b.stop();
  }, [l, n, u, p]), /* @__PURE__ */ v(
    Me,
    {
      variant: r,
      "aria-label": e,
      "aria-disabled": o || h,
      "aria-describedby": f,
      className: `relative isolate select-none overflow-hidden ${s ?? ""}`,
      ...a,
      children: [
        /* @__PURE__ */ d(ja, { committed: h, label: e, confirmLabel: t }),
        /* @__PURE__ */ d(
          j.span,
          {
            "aria-hidden": "true",
            style: { clipPath: g },
            className: "absolute inset-0 grid place-items-center bg-ink text-ground",
            children: /* @__PURE__ */ d(ja, { committed: h, label: e, confirmLabel: t })
          }
        ),
        /* @__PURE__ */ v("span", { id: f, className: "sr-only", children: [
          "Press and hold for ",
          m,
          " seconds to confirm. Let go early and nothing happens."
        ] }),
        /* @__PURE__ */ d("span", { role: "status", "aria-live": "polite", className: "sr-only", children: h ? t : "" })
      ]
    }
  );
}
function ja({ committed: e, label: t, confirmLabel: n }) {
  const i = { duration: _.settle, ease: Uu };
  return /* @__PURE__ */ v("span", { "aria-hidden": "true", className: "col-start-1 row-start-1 grid", children: [
    /* @__PURE__ */ d(
      j.span,
      {
        initial: !1,
        animate: { opacity: e ? 0 : 1 },
        transition: i,
        className: "col-start-1 row-start-1 flex items-center justify-center whitespace-nowrap",
        children: t
      }
    ),
    /* @__PURE__ */ v(
      j.span,
      {
        initial: !1,
        animate: { opacity: e ? 1 : 0 },
        transition: i,
        className: "col-start-1 row-start-1 flex items-center justify-center gap-1.5 whitespace-nowrap",
        children: [
          /* @__PURE__ */ d(
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
              children: /* @__PURE__ */ d("path", { d: "M2.5 6.4 4.7 8.6 9.5 3.5" })
            }
          ),
          n
        ]
      }
    )
  ] });
}
const Fb = Z.out;
function n2({
  title: e,
  children: t,
  confirmLabel: n = "Delete",
  hold: i = !1,
  onConfirm: r,
  onCancel: o
}) {
  const s = D(null), a = D(null);
  return O(() => {
    s.current?.showModal(), a.current?.focus();
  }, []), /* @__PURE__ */ v(
    j.dialog,
    {
      ref: s,
      "aria-labelledby": "confirm-title",
      initial: { opacity: 0, scale: 0.98 },
      animate: { opacity: 1, scale: 1 },
      transition: { duration: _.settle, ease: Fb },
      onCancel: (l) => {
        l.preventDefault(), o();
      },
      onClick: (l) => {
        l.target === l.currentTarget && o();
      },
      className: "panel m-auto w-[320px] max-w-[calc(100vw-32px)] p-0 text-ink backdrop:bg-scrim/30 backdrop:transition-colors backdrop:duration-[240ms] starting:backdrop:bg-scrim/0",
      children: [
        /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5 px-4 pt-4 pb-3.5", children: [
          /* @__PURE__ */ d("h2", { id: "confirm-title", className: "font-display text-[16px] leading-5 font-bold tracking-[-0.02em] text-ink", children: e }),
          /* @__PURE__ */ d("p", { className: "text-xs leading-4 text-muted", children: t })
        ] }),
        /* @__PURE__ */ v("div", { className: "flex justify-end gap-1.5 border-t border-line-soft px-4 py-3", children: [
          /* @__PURE__ */ d(Me, { ref: a, variant: "outline", onClick: o, children: "Cancel" }),
          i ? /* @__PURE__ */ d(Vb, { label: n, confirmLabel: "Done", holdMs: 1200, onConfirm: r }) : /* @__PURE__ */ d(Me, { variant: "danger", onClick: r, children: n })
        ] })
      ]
    }
  );
}
const Ib = '<svg xmlns="http://www.w3.org/2000/svg" width="166" height="46" viewBox="0 0 165.53 45.81"><g transform="translate(0,0.00)"><g transform="translate(0,4.23) scale(1.8900)"><polygon points="3.34,7.00 3.42,6.86 3.51,6.74 3.61,6.62 3.72,6.51 3.84,6.41 3.96,6.32 4.09,6.24 10.97,2.27 11.25,2.14 11.54,2.05 11.85,2.00 12.15,2.00 12.46,2.05 12.75,2.14 13.03,2.27 19.91,6.24 20.04,6.32 20.16,6.41 20.28,6.51 20.39,6.62 20.49,6.74 20.58,6.86 20.66,7.00 17.36,8.90 6.64,8.90" fill="#FF7050" stroke="#A32409" stroke-width="0.5" stroke-linejoin="round"/><polygon points="12.00,22.00 11.85,21.99 11.69,21.98 11.54,21.95 11.39,21.91 11.25,21.86 11.10,21.80 10.97,21.72 4.09,17.75 3.84,17.58 3.61,17.37 3.42,17.13 3.27,16.86 3.15,16.57 3.08,16.27 3.06,15.97 3.06,8.03 3.07,7.87 3.08,7.72 3.11,7.57 3.15,7.42 3.20,7.27 3.27,7.13 3.34,7.00 6.64,8.90 12.00,18.19" fill="#F0421F" stroke="#A32409" stroke-width="0.5" stroke-linejoin="round"/><polygon points="20.66,7.00 20.73,7.13 20.80,7.27 20.85,7.42 20.89,7.57 20.92,7.72 20.93,7.87 20.94,8.03 20.94,15.97 20.92,16.27 20.85,16.57 20.73,16.86 20.58,17.13 20.39,17.37 20.16,17.58 19.91,17.75 13.03,21.72 12.90,21.80 12.75,21.86 12.61,21.91 12.46,21.95 12.31,21.98 12.15,21.99 12.00,22.00 12.00,18.19 17.36,8.90" fill="#C42D12" stroke="#A32409" stroke-width="0.5" stroke-linejoin="round"/><polygon points="6.64,8.90 17.36,8.90 12.00,18.19" fill="#FF8A6B" stroke="#A32409" stroke-width="0.5" stroke-linejoin="round"/></g><g transform="translate(51.03,0)"><path d="M11.503875968992247 40.91472868217054H3.147286821705426V13.782945736434108H11.015503875968992L11.55813953488372 16.604651162790695Q12.806201550387597 14.868217054263564 15.003875968992247 13.891472868217052Q17.2015503875969 12.91472868217054 19.86046511627907 12.91472868217054Q24.689922480620154 12.91472868217054 27.375968992248062 15.872093023255813Q30.06201550387597 18.829457364341085 30.06201550387597 24.147286821705425V40.91472868217054H21.705426356589147V26.155038759689923Q21.705426356589147 23.604651162790695 20.4031007751938 22.05813953488372Q19.100775193798448 20.51162790697674 16.930232558139533 20.51162790697674Q14.434108527131782 20.51162790697674 12.968992248062015 22.003875968992247Q11.503875968992247 23.49612403100775 11.503875968992247 26.046511627906973Z M51.06201550387597 13.782945736434108H59.41860465116279V40.91472868217054H51.55038759689923L51.007751937984494 37.87596899224806Q49.75968992248062 39.55813953488372 47.45348837209302 40.58914728682171Q45.14728682170542 41.62015503875969 42.70542635658914 41.62015503875969Q38.093023255813954 41.62015503875969 35.406976744186046 38.71705426356589Q32.72093023255814 35.81395348837209 32.72093023255814 30.821705426356587V13.782945736434108H41.07751937984496V27.782945736434108Q41.07751937984496 31.093023255813954 42.27131782945736 32.63953488372093Q43.46511627906976 34.18604651162791 46.01550387596899 34.18604651162791Q48.72868217054263 34.18604651162791 49.8953488372093 32.6937984496124Q51.06201550387597 31.201550387596896 51.06201550387597 27.89147286821705Z M81.12403100775194 13.782945736434108V21.651162790697672H78.46511627906978Q74.88372093023256 21.651162790697672 72.84883720930233 23.387596899224803Q70.81395348837209 25.124031007751938 70.81395348837209 29.139534883720927V40.91472868217054H62.457364341085274V13.83720930232558H70.32558139534883L70.97674418604652 19.643410852713178H70.2170542635659Q70.75968992248062 16.930232558139533 72.68604651162791 15.166666666666664Q74.6124031007752 13.403100775193796 77.92248062015504 13.403100775193796Q78.68217054263566 13.403100775193796 79.46899224806202 13.484496124031006Q80.25581395348837 13.565891472868216 81.12403100775194 13.782945736434108Z M90.7829457364341 40.91472868217054H82.91472868217053V0.0H91.27131782945736V16.930232558139533Q92.51937984496124 15.085271317829456 94.98837209302326 13.972868217054263Q97.45736434108527 12.86046511627907 100.3875968992248 12.86046511627907Q104.18604651162791 12.86046511627907 106.98062015503876 14.705426356589147Q109.7751937984496 16.550387596899224 111.29457364341084 19.860465116279066Q112.81395348837208 23.17054263565891 112.81395348837208 27.620155038759687Q112.81395348837208 31.798449612403097 111.15891472868216 34.972868217054256Q109.50387596899225 38.14728682170542 106.54651162790697 39.883720930232556Q103.5891472868217 41.62015503875969 99.73643410852713 41.62015503875969Q96.91472868217053 41.62015503875969 94.60852713178294 40.45348837209302Q92.30232558139534 39.286821705426355 91.21705426356588 37.44186046511628ZM91.32558139534883 27.186046511627907Q91.32558139534883 29.1937984496124 92.16666666666666 30.74031007751938Q93.0077519379845 32.286821705426355 94.5 33.127906976744185Q95.9922480620155 33.968992248062015 97.94573643410853 33.968992248062015Q99.95348837209302 33.968992248062015 101.39147286821705 33.10077519379845Q102.82945736434108 32.23255813953488 103.61627906976744 30.71317829457364Q104.40310077519379 29.1937984496124 104.40310077519379 27.186046511627907Q104.40310077519379 25.17829457364341 103.61627906976744 23.65891472868217Q102.82945736434108 22.139534883720927 101.39147286821705 21.27131782945736Q99.95348837209302 20.403100775193796 97.94573643410853 20.403100775193796Q95.9922480620155 20.403100775193796 94.5 21.244186046511626Q93.0077519379845 22.085271317829456 92.16666666666666 23.604651162790695Q91.32558139534883 25.124031007751938 91.32558139534883 27.186046511627907Z" fill="#121821"/></g></g></svg>', Ob = Ib.replace('fill="#121821"', 'fill="currentColor"').replace(/width="[\d.]+" height="[\d.]+"/, 'width="100%" height="100%"');
function i2({
  size: e = "header",
  onNavigate: t
}) {
  const i = /* @__PURE__ */ d(
    "span",
    {
      role: "img",
      "aria-label": "nurb",
      className: `${e === "panel" ? "h-6 w-[87px]" : "h-[18px] w-[65px]"} shrink-0 text-ink`,
      dangerouslySetInnerHTML: { __html: Ob }
    }
  );
  return t ? /* @__PURE__ */ d(
    "button",
    {
      type: "button",
      onClick: t,
      className: "inline-flex rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent",
      children: i
    }
  ) : /* @__PURE__ */ d("div", { className: "inline-flex", children: i });
}
const Bb = Z.out, jb = { duration: 0 }, $b = typeof window > "u" ? O : Nt;
function zb({
  src: e,
  onReady: t,
  onError: n
}) {
  const i = D(null), [r, o] = B({ status: "loading", instant: !1 }), s = D(t);
  s.current = t;
  const a = D(n);
  return a.current = n, $b(() => {
    const l = i.current, c = (p, g) => o((y) => y.status === p && y.instant === g ? y : { status: p, instant: g });
    if (!l || !e) {
      c("loading", !1);
      return;
    }
    let u = !0;
    const f = l.complete && l.naturalWidth > 0, h = () => {
      u && (c("ready", f), s.current?.());
    }, m = () => {
      u && (c("error", f), a.current?.());
    };
    return l.complete ? (f ? h() : m(), () => {
      u = !1;
    }) : (c("loading", !1), l.addEventListener("load", h), l.addEventListener("error", m), () => {
      u = !1, l.removeEventListener("load", h), l.removeEventListener("error", m);
    });
  }, [e]), { ref: i, status: r.status, instant: r.instant, loaded: r.status === "ready" };
}
function _b({
  src: e,
  alt: t,
  width: n,
  height: i,
  placeholder: r = "var(--color-accent-wash)",
  blur: o = 14,
  sizes: s,
  loading: a = "lazy",
  onReady: l,
  onError: c,
  className: u
}) {
  const f = ne() === !0, { ref: h, status: m, instant: p } = zb({ src: e, onReady: l, onError: c }), g = m === "ready", y = f || p, b = y ? jb : { duration: _.arrive, ease: Bb };
  return /* @__PURE__ */ v(
    "div",
    {
      "aria-busy": m === "loading",
      "data-status": m,
      style: { aspectRatio: `${n} / ${i}`, backgroundColor: r },
      className: V("relative w-full overflow-hidden rounded-[6px]", u),
      children: [
        /* @__PURE__ */ d(
          j.img,
          {
            ref: h,
            src: e,
            sizes: s,
            alt: t,
            width: n,
            height: i,
            loading: a,
            decoding: "async",
            draggable: !1,
            className: "absolute inset-0 size-full object-cover",
            initial: !1,
            animate: (
              // The instant path clears the blur too: a src swapped back to a cached image
              // lands here straight from the loading pose, and would otherwise keep it.
              y ? { opacity: g ? 1 : 0, filter: "blur(0px)", scale: 1 } : g ? { opacity: 1, filter: "blur(0px)", scale: 1 } : { opacity: 0, filter: `blur(${o}px)`, scale: 1.06 }
            ),
            transition: b
          }
        ),
        m === "error" ? /* @__PURE__ */ d("div", { "aria-hidden": "true", className: "absolute inset-0 grid place-items-center bg-raised text-faint", children: /* @__PURE__ */ d(z, { name: "image" }) }) : null
      ]
    }
  );
}
const $a = 3e4;
function Ub(e, t) {
  const n = t ? Date.parse(t) : NaN, [i, r] = B(() => Date.now());
  return O(() => {
    if (!e || Number.isNaN(n)) return;
    const o = n + $a - Date.now();
    if (o <= 0) return;
    const s = setTimeout(() => r(Date.now()), o);
    return () => clearTimeout(s);
  }, [e, n]), e ? Number.isNaN(n) ? !0 : i - n < $a : !1;
}
function r2({
  part: e,
  onOpen: t,
  menu: n,
  renaming: i,
  onRename: r
}) {
  const o = w0(e.bbox), s = e.folder && e.folder.toLowerCase() !== e.name.toLowerCase() ? e.folder : null, a = v0(e.builtAt), l = e.status === "failed", c = e.status === "building", u = e.status === "draft", f = Ub(c, e.buildingSince), h = Db(), m = $f(), p = e.thumbnailUrl && m ? `${e.thumbnailUrl}&theme=dark` : e.thumbnailUrl ?? void 0;
  return /* @__PURE__ */ v(
    "div",
    {
      onContextMenu: (g) => h.open(g, i ? void 0 : n),
      className: "group relative flex flex-col rounded-[6px] border border-panel-edge bg-ground transition-shadow focus-within:shadow-[var(--shadow-panel)] hover:shadow-[var(--shadow-panel)]",
      children: [
        h.menu,
        /* @__PURE__ */ d(
          "button",
          {
            type: "button",
            onClick: t,
            "aria-label": `Open ${e.name}`,
            className: "absolute inset-0 z-10 rounded-[6px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          }
        ),
        /* @__PURE__ */ d(
          "div",
          {
            className: `relative h-[148px] overflow-hidden rounded-t-[6px] border-b border-line-soft ${u ? "bg-raised/60" : "bg-ground"}`,
            children: u ? null : e.thumbnailUrl ? (
              // The card owns the box, so the frame fills it instead of its own ratio,
              // and the whole part stays in frame rather than being cropped to it.
              /* @__PURE__ */ d(
                _b,
                {
                  src: p,
                  alt: "",
                  width: 4,
                  height: 3,
                  placeholder: "transparent",
                  className: "h-full rounded-none! [&_img]:object-contain [&_img]:p-2"
                }
              )
            ) : /* @__PURE__ */ d(Pb, { bbox: e.bbox, ghost: !e.bbox, className: "size-full" })
          }
        ),
        n && n.length > 0 ? /* @__PURE__ */ d("div", { className: "absolute top-2 right-2 z-20 flex items-center gap-1 transition-opacity lg:opacity-0 lg:group-focus-within:opacity-100 lg:group-hover:opacity-100 lg:has-[[aria-expanded=true]]:opacity-100", children: /* @__PURE__ */ d(
          Eb,
          {
            label: `More for ${e.name}`,
            className: "[&>button]:size-7 [&>button]:rounded-[4px] [&>button]:border [&>button]:border-panel-edge [&>button]:bg-ground [&>button]:shadow-[var(--shadow-control)]",
            items: n
          }
        ) }) : null,
        /* @__PURE__ */ v("div", { className: "flex flex-col gap-1.5 px-[13px] py-[11px]", children: [
          /* @__PURE__ */ v("div", { className: "flex items-center gap-2", children: [
            i ? /* @__PURE__ */ d(Wb, { name: e.name, onDone: (g) => r?.(g) }) : /* @__PURE__ */ d("h2", { className: "min-w-0 flex-1 truncate text-[13.5px] leading-[18px] font-semibold tracking-[-0.01em] text-ink", children: e.name }),
            l ? /* @__PURE__ */ d("span", { className: "text-warn", children: /* @__PURE__ */ d(z, { name: "warning" }) }) : c ? /* @__PURE__ */ d(
              "span",
              {
                "data-build": f ? "running" : "stalled",
                className: `size-1.5 rounded-full bg-accent${f ? " motion-safe:animate-pulse" : ""}`
              }
            ) : e.status === "built" ? /* @__PURE__ */ d("span", { className: "text-pass", children: /* @__PURE__ */ d(z, { name: "check" }) }) : null
          ] }),
          /* @__PURE__ */ d("p", { className: "mono-caption truncate text-muted normal-case [letter-spacing:0.08em]", children: [o ? `${o} mm` : null, e.pieces ? `${e.pieces} ${e.pieces === 1 ? "part" : "parts"}` : null].filter(Boolean).join(" · ") || " " })
        ] }),
        /* @__PURE__ */ v("div", { className: "mono-caption flex items-center justify-between border-t border-line-soft px-[13px] py-2 text-muted [letter-spacing:0.08em]", children: [
          u ? /* @__PURE__ */ v("span", { className: "flex items-center gap-2", children: [
            e.designing ? /* @__PURE__ */ d("span", { "aria-hidden": "true", className: "size-1.5 rounded-full bg-accent motion-safe:animate-pulse" }) : null,
            e.designing ? "Being designed" : "No design yet"
          ] }) : /* @__PURE__ */ d("span", { children: a ? `Built ${a}` : "Not built yet" }),
          /* @__PURE__ */ d("span", { className: l ? "text-warn" : void 0, children: l ? "Failed" : s ?? (u ? "" : Zt(e.revision)) })
        ] })
      ]
    }
  );
}
function Wb({ name: e, onDone: t }) {
  const [n, i] = B(e), r = D(!1), o = (s) => {
    r.current || (r.current = !0, t(s && s.trim() && s.trim() !== e ? s.trim() : null));
  };
  return /* @__PURE__ */ d(
    "input",
    {
      autoFocus: !0,
      "aria-label": `Rename ${e}`,
      value: n,
      onFocus: (s) => s.currentTarget.select(),
      onChange: (s) => i(s.target.value),
      onBlur: () => o(n),
      onKeyDown: (s) => {
        s.key === "Enter" ? o(n) : s.key === "Escape" && o(null);
      },
      className: "relative z-20 h-[22px] min-w-0 flex-1 rounded-[2px] border border-accent bg-ground px-1 text-[13.5px] leading-[18px] font-semibold tracking-[-0.01em] text-ink focus:outline-none"
    }
  );
}
function s2({
  caption: e = "Describe a part and it builds here, live.",
  firstRun: t = !1,
  primary: n,
  secondary: i
}) {
  return /* @__PURE__ */ v("div", { className: "flex flex-1 flex-col items-center justify-center gap-7 pb-16", children: [
    /* @__PURE__ */ d("span", { "aria-hidden": "true", style: ju(Bu.ghostBracket), className: "h-[300px] w-[231px] bg-panel-edge" }),
    /* @__PURE__ */ v("div", { className: "flex flex-col items-center gap-2", children: [
      /* @__PURE__ */ d("h2", { className: "font-display text-[20px] leading-[26px] tracking-[-0.022em] text-balance text-ink", children: "Empty shelf. What’s rattling around your bench?" }),
      /* @__PURE__ */ d("p", { className: "mono-caption text-on-stage-muted [letter-spacing:0.11em]", children: e }),
      t ? /* @__PURE__ */ d("p", { className: "mt-1 max-w-[42ch] text-center text-[13px] leading-5 text-balance text-on-stage-muted", children: "Nothing on the plate yet. Your first part goes here, and the first layer is the one that matters." }) : null
    ] }),
    n || i ? /* @__PURE__ */ v("div", { className: "flex flex-col items-center gap-3", children: [
      n ? /* @__PURE__ */ d(Me, { variant: "accent", size: "lg", icon: n.icon, onClick: n.onClick, children: n.label }) : null,
      i ? /* @__PURE__ */ d(Me, { variant: "outline", size: "md", icon: i.icon, onClick: i.onClick, disabled: i.disabled, children: i.label }) : null
    ] }) : null
  ] });
}
function o2({
  title: e = "No part yet",
  caption: t = "It appears here, live, as soon as the plan is set."
}) {
  return /* @__PURE__ */ v("div", { className: "relative flex min-h-[320px] flex-1 flex-col items-center justify-center gap-5 text-center", children: [
    /* @__PURE__ */ d("span", { "aria-hidden": "true", style: ju(Bu.markOutline), className: "size-14 bg-ink" }),
    /* @__PURE__ */ v("div", { className: "flex flex-col items-center gap-2", children: [
      /* @__PURE__ */ d("p", { className: "mono-label text-on-stage-muted", children: e }),
      /* @__PURE__ */ d("p", { className: "max-w-[34ch] text-[15px] leading-[22px] text-balance text-ink-soft", children: t })
    ] })
  ] });
}
function a2({ header: e, children: t, className: n, style: i, topInset: r, dragRegion: o }) {
  return /* @__PURE__ */ v(
    "div",
    {
      className: V("isolate flex h-dvh flex-col gap-4 bg-stage p-4 antialiased", n),
      style: r == null ? i : { ...i, paddingTop: r },
      ...o ? { "data-tauri-drag-region": !0 } : {},
      children: [
        e,
        /* @__PURE__ */ d("div", { className: "flex min-h-0 flex-1 gap-4", children: t })
      ]
    }
  );
}
function Hb({
  children: e,
  className: t,
  onContextMenu: n
}) {
  return /* @__PURE__ */ d(
    "div",
    {
      onContextMenu: n,
      className: V("relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden", t),
      children: e
    }
  );
}
function l2({ children: e, className: t }) {
  return /* @__PURE__ */ d(Hb, { className: V("items-center justify-center", t), children: e });
}
function c2({ start: e, cells: t, end: n, children: i, dragRegion: r }) {
  return /* @__PURE__ */ v(
    "header",
    {
      className: "panel chrome flex h-[52px] shrink-0 items-center overflow-hidden",
      ...r ? { "data-tauri-drag-region": !0 } : {},
      children: [
        e,
        t,
        i,
        n ? /* @__PURE__ */ v(U, { children: [
          /* @__PURE__ */ d("div", { className: "flex-1" }),
          n
        ] }) : null
      ]
    }
  );
}
function u2() {
  return /* @__PURE__ */ d("div", { className: "h-full w-px bg-line" });
}
function Hu({ children: e, className: t }) {
  return /* @__PURE__ */ d("div", { className: V("flex h-full items-center px-4", t), children: e });
}
function f2({ label: e, value: t, className: n }) {
  return /* @__PURE__ */ d(Hu, { className: n, children: /* @__PURE__ */ v("div", { className: "flex flex-col gap-[3px]", children: [
    /* @__PURE__ */ d("span", { className: "mono-label text-[9px] leading-[10px] text-faint", children: e }),
    /* @__PURE__ */ d("span", { className: "mono-value text-ink", children: t })
  ] }) });
}
const Gb = {
  pass: "bg-pass",
  warn: "bg-warn",
  fail: "bg-fail",
  none: "bg-line",
  building: "bg-accent motion-safe:animate-pulse"
}, Kb = {
  pass: "border-line bg-pass-wash",
  warn: "border-line bg-warn-wash",
  fail: "border-line bg-fail-wash",
  none: "border-transparent bg-transparent",
  building: "border-line bg-accent-wash"
}, za = "transition-colors duration-(--duration-settle) ease-out-strong";
function d2({
  tone: e,
  label: t,
  detail: n,
  className: i
}) {
  return /* @__PURE__ */ d(Hu, { className: i, children: /* @__PURE__ */ v("span", { className: V("flex h-7 items-center gap-2 rounded-[3px] border px-2.5 whitespace-nowrap", za, Kb[e]), children: [
    /* @__PURE__ */ d("span", { className: V("size-1.5 shrink-0 rounded-full", za, Gb[e]) }),
    /* @__PURE__ */ d("span", { className: "mono-label text-ink", children: t }),
    n ? /* @__PURE__ */ d("span", { className: "mono-caption text-muted", children: n }) : null
  ] }) });
}
function h2({ children: e, className: t }) {
  return /* @__PURE__ */ d("div", { className: V("flex h-full items-center gap-1 px-3", t), children: e });
}
function p2({ strip: e, picker: t, children: n, composer: i, hidden: r, dragRegion: o }) {
  return /* @__PURE__ */ v("section", { className: "panel flex w-[372px] shrink-0 flex-col overflow-hidden", hidden: r, children: [
    /* @__PURE__ */ d("div", { ...o ? { "data-tauri-drag-region": !0 } : {}, children: /* @__PURE__ */ d(
      Ps,
      {
        label: e.label,
        inset: 16,
        trailing: t || e.trailing ? /* @__PURE__ */ v("span", { className: "flex items-center gap-2", children: [
          e.trailing,
          t
        ] }) : void 0
      }
    ) }),
    /* @__PURE__ */ d("div", { className: "min-h-0 flex-1 overflow-y-auto", children: n }),
    /* @__PURE__ */ d("div", { className: "shrink-0 p-4 pt-0", children: i })
  ] });
}
function qb(e) {
  const t = Math.max(0, Math.round(e / 60));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function Ii({ value: e, unit: t }) {
  return /* @__PURE__ */ v("span", { className: "flex items-baseline gap-1", children: [
    /* @__PURE__ */ d("span", { className: "mono-value text-ink", children: e }),
    /* @__PURE__ */ d("span", { className: "mono-caption text-muted", children: t })
  ] });
}
function Yb({ children: e }) {
  return /* @__PURE__ */ v("div", { className: "chrome flex items-center gap-2 px-4 pt-[11px] pb-2", children: [
    /* @__PURE__ */ d("span", { className: "mono-caption text-faint [letter-spacing:0.12em]", children: e }),
    /* @__PURE__ */ d("span", { className: "h-px flex-1 bg-line-soft" })
  ] });
}
function m2({
  count: e,
  pinned: t,
  params: n,
  readouts: i,
  warnCount: r = 0,
  failCount: o = 0,
  disclosures: s,
  actions: a
}) {
  const l = o > 0 ? o : r;
  return /* @__PURE__ */ v("aside", { className: "panel flex w-[288px] shrink-0 flex-col overflow-hidden", children: [
    /* @__PURE__ */ d(Ps, { label: "Parameters", inset: 16, trailing: e }),
    /* @__PURE__ */ v("div", { className: "flex min-h-0 flex-1 flex-col overflow-y-auto", children: [
      t && t.length > 0 ? /* @__PURE__ */ v(U, { children: [
        /* @__PURE__ */ d(Yb, { children: "Set by the plan" }),
        /* @__PURE__ */ d("ul", { className: "flex flex-col gap-1.5 px-4 pb-1", children: t.map((c) => /* @__PURE__ */ v("li", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ d("span", { className: "shrink-0 text-faint", children: /* @__PURE__ */ d(z, { name: "lock" }) }),
          /* @__PURE__ */ d("span", { className: "mono-label truncate text-muted", children: Kn(c.name) }),
          /* @__PURE__ */ d("span", { className: "flex-1" }),
          /* @__PURE__ */ d("span", { className: "mono-value text-right text-ink", children: c.value })
        ] }, c.name)) })
      ] }) : null,
      n
    ] }),
    /* @__PURE__ */ v("div", { className: "min-h-0 overflow-y-auto border-t border-line bg-ground", children: [
      i ? /* @__PURE__ */ v("div", { className: "chrome flex items-center justify-between px-4 py-2.5", children: [
        /* @__PURE__ */ d(Ii, { value: i.grams == null ? "-" : String(Math.round(i.grams)), unit: "g" }),
        /* @__PURE__ */ d(Ii, { value: i.seconds == null ? "-" : qb(i.seconds), unit: "hr" }),
        /* @__PURE__ */ d(Ii, { value: i.heightMm == null ? "-" : String(Math.round(i.heightMm)), unit: "mm" })
      ] }) : null,
      /* @__PURE__ */ d("div", { className: "h-px bg-line-soft" }),
      l > 0 && !s ? /* @__PURE__ */ v("div", { className: "flex items-center gap-2 px-4 py-2", children: [
        /* @__PURE__ */ d("span", { className: o > 0 ? "text-fail" : "text-warn", children: /* @__PURE__ */ d(z, { name: o > 0 ? "xmark" : "warning" }) }),
        /* @__PURE__ */ v("span", { className: "mono-label text-ink", children: [
          l,
          " ",
          o > 0 ? l === 1 ? "fail" : "fails" : l === 1 ? "warn" : "warns"
        ] })
      ] }) : null,
      s,
      /* @__PURE__ */ d("div", { className: "flex gap-2 p-4", children: a })
    ] })
  ] });
}
const Xb = {
  warn: "warning",
  fail: "xmark",
  pass: "check",
  none: null
}, Qb = {
  warn: "text-warn",
  fail: "text-fail",
  pass: "text-pass",
  none: "text-muted"
};
function g2({ label: e, summary: t, tone: n = "none", open: i, onToggle: r, children: o }) {
  const s = Xb[n];
  return /* @__PURE__ */ v("div", { className: "flex flex-col", children: [
    /* @__PURE__ */ v(
      "button",
      {
        type: "button",
        onClick: r,
        "aria-expanded": i,
        className: "chrome flex h-8 w-full items-center gap-2 px-4 text-left hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent",
        children: [
          s ? /* @__PURE__ */ d("span", { className: V("shrink-0", Qb[n]), children: /* @__PURE__ */ d(z, { name: s }) }) : null,
          /* @__PURE__ */ d("span", { className: "mono-label text-ink", children: e }),
          /* @__PURE__ */ d("span", { className: "flex-1" }),
          t ? /* @__PURE__ */ d("span", { className: "mono-caption text-muted", children: t }) : null,
          /* @__PURE__ */ d("span", { className: V("shrink-0 text-muted transition-transform", i && "rotate-180"), children: /* @__PURE__ */ d(z, { name: "chevron-down" }) })
        ]
      }
    ),
    /* @__PURE__ */ d("div", { hidden: !i, className: "max-h-48 overflow-y-auto border-t border-line-soft", children: o })
  ] });
}
const _a = Z.out;
function Gu(e, t = 900) {
  const [n, i] = B({ direction: null, from: e, changeId: 0, flashing: !1 }), r = D(e), o = D(null);
  return O(() => {
    const s = r.current;
    Object.is(s, e) || (r.current = e, e - s !== 0 && (i((a) => ({
      direction: e > s ? "up" : "down",
      from: s,
      changeId: a.changeId + 1,
      flashing: !0
    })), o.current && clearTimeout(o.current), o.current = setTimeout(() => {
      o.current = null, i((a) => a.flashing ? { ...a, flashing: !1 } : a);
    }, t)));
  }, [e, t]), O(() => () => o.current ? clearTimeout(o.current) : void 0, []), n;
}
function y2({ value: e, format: t, label: n, hold: i = 900, className: r }) {
  const { direction: o, flashing: s, changeId: a } = Gu(e, i), l = ne(), c = t ? t(e) : String(e), [u, f] = B(c);
  O(() => {
    const p = setTimeout(() => f(c), 700);
    return () => clearTimeout(p);
  }, [c]);
  const h = { duration: l ? 0 : _.settle, ease: _a }, m = { duration: l ? 0 : _.tick * 2, ease: _a };
  return /* @__PURE__ */ v(
    "span",
    {
      "data-direction": s ? o : void 0,
      className: V(
        "mono-value relative inline-grid grid-flow-col items-center gap-1 rounded-[3px] px-1 py-px transition-colors",
        s ? o === "up" ? "text-pass" : "text-fail" : "text-ink",
        r
      ),
      children: [
        o ? /* @__PURE__ */ d(
          j.span,
          {
            "aria-hidden": !0,
            initial: { opacity: 0 },
            animate: { opacity: s ? 1 : 0 },
            transition: h,
            className: V(
              "pointer-events-none absolute inset-0 rounded-[3px]",
              o === "up" ? "bg-pass-wash" : "bg-fail-wash"
            )
          }
        ) : null,
        /* @__PURE__ */ d("span", { "aria-hidden": !0, className: "relative inline-grid overflow-hidden", children: /* @__PURE__ */ d(ge, { initial: !1, mode: "popLayout", children: /* @__PURE__ */ d(
          j.span,
          {
            initial: l ? { opacity: 0 } : { opacity: 0, y: o === "down" ? "-0.85em" : "0.85em" },
            animate: { opacity: 1, y: "0em" },
            exit: { opacity: 0, y: o === "down" ? "0.7em" : "-0.7em", transition: m },
            transition: m,
            className: "col-start-1 row-start-1",
            children: c
          },
          a
        ) }) }),
        /* @__PURE__ */ d("span", { "aria-hidden": !0, className: "relative grid size-[1em] place-items-center", children: /* @__PURE__ */ d(ge, { initial: !1, children: s && o ? /* @__PURE__ */ d(
          j.svg,
          {
            viewBox: "0 0 256 256",
            fill: "currentColor",
            initial: l ? { opacity: 0 } : { opacity: 0, scale: 0.4 },
            animate: { opacity: 1, scale: 1 },
            exit: { opacity: 0, transition: h },
            transition: h,
            className: "col-start-1 row-start-1 block size-[0.68em]",
            children: o === "up" ? /* @__PURE__ */ d("path", { d: "M128 68 L210 180 H46 Z" }) : /* @__PURE__ */ d("path", { d: "M128 188 L46 76 H210 Z" })
          },
          `${a}-${o}`
        ) : null }) }),
        /* @__PURE__ */ d("span", { className: "sr-only", "aria-live": "polite", children: n ? `${n}: ${u}` : u })
      ]
    }
  );
}
const Zb = Z.out;
function x2({ findings: e, verdict: t, highlight: n, onHighlight: i }) {
  const r = ne(), o = e.length, { direction: s, flashing: a } = Gu(o), l = a && !r, c = s === "up", u = o > 0 ? `${o} ${o === 1 ? "finding" : "findings"} to fix.` : t === "none" ? "Nothing checked yet" : t === "fail" ? "The build stopped before the checks ran" : "Nothing to fix. Checks pass at these numbers.", f = /* @__PURE__ */ d(
    "p",
    {
      "aria-live": "polite",
      className: V(
        "mono-caption py-1 text-center transition-colors duration-(--duration-settle) ease-out-strong",
        l ? c ? "bg-fail-wash text-fail" : "bg-pass-wash text-pass" : "text-muted"
      ),
      children: u
    }
  );
  return o === 0 ? f : /* @__PURE__ */ v(U, { children: [
    f,
    /* @__PURE__ */ d("ul", { className: "flex flex-col", children: e.map((h, m) => (
      // Keyed by what the finding says, not by where it sits, so a rebuild that
      // changes nothing leaves the rows alone instead of replaying the entrance.
      /* @__PURE__ */ d(
        j.li,
        {
          initial: { opacity: 0, y: 4 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: r ? 0 : _.settle, ease: Zb, delay: r ? 0 : m * 0.06 },
          children: /* @__PURE__ */ v(
            "button",
            {
              type: "button",
              "aria-pressed": n === m,
              onMouseEnter: () => i?.(m),
              onClick: () => i?.(n === m ? null : m),
              className: V(
                "flex w-full items-start gap-2 px-4 py-2 text-left hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent",
                n === m && "bg-raised"
              ),
              children: [
                /* @__PURE__ */ d("span", { className: V("mt-0.5 shrink-0", h.severity === "fail" ? "text-fail" : "text-warn"), children: /* @__PURE__ */ d(z, { name: h.severity === "fail" ? "xmark" : "warning" }) }),
                /* @__PURE__ */ v("span", { className: "flex min-w-0 flex-col gap-1", children: [
                  /* @__PURE__ */ d("span", { className: "mono-label text-ink", children: h.label || h.rule }),
                  /* @__PURE__ */ d("span", { className: "text-chat text-ink-soft", children: h.message })
                ] })
              ]
            }
          )
        },
        `${h.rule}:${h.message}`
      )
    )) })
  ] });
}
const Jb = Z.out;
function b2({
  open: e = !0,
  revision: t,
  shownRevision: n,
  error: i
}) {
  const r = ne();
  return /* @__PURE__ */ d(ge, { children: e ? /* @__PURE__ */ v(
    j.div,
    {
      initial: { opacity: 0, y: -8 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -8 },
      transition: { duration: r ? 0 : _.settle, ease: Jb },
      className: "flex items-start gap-2 bg-fail-wash px-4 py-2.5",
      children: [
        /* @__PURE__ */ d("span", { className: "mt-0.5 shrink-0 text-fail", children: /* @__PURE__ */ d(z, { name: "warning" }) }),
        /* @__PURE__ */ v("span", { className: "flex flex-col gap-1", children: [
          /* @__PURE__ */ v("span", { className: "mono-label text-fail", children: [
            Zt(t),
            " failed at these values"
          ] }),
          i ? /* @__PURE__ */ d("span", { className: "text-chat text-ink", children: i }) : null,
          n != null ? /* @__PURE__ */ v("span", { className: "text-chat text-ink-soft", children: [
            "Showing ",
            Zt(n).toLowerCase(),
            ", the last one that built."
          ] }) : null
        ] })
      ]
    }
  ) : null });
}
function v2({ children: e }) {
  return /* @__PURE__ */ v("div", { className: "panel chrome absolute top-4 left-4 flex h-7 items-center gap-2 rounded-full px-3", children: [
    /* @__PURE__ */ d("span", { className: "size-1.5 shrink-0 rounded-full bg-fail" }),
    /* @__PURE__ */ d("span", { className: "mono-label text-ink", children: e })
  ] });
}
const ev = Z.out;
function w2({ open: e, expected: t }) {
  return /* @__PURE__ */ d(ge, { children: e ? /* @__PURE__ */ d(tv, { expected: t ?? null }, "building") : null });
}
function tv({ expected: e }) {
  const t = ne(), [n] = B(() => performance.now()), [i, r] = B(0), [o, s] = B(!1);
  return O(() => {
    const a = setInterval(() => r((performance.now() - n) / 1e3), 100), l = requestAnimationFrame(() => s(!0));
    return () => {
      clearInterval(a), cancelAnimationFrame(l);
    };
  }, [n]), /* @__PURE__ */ v(
    j.div,
    {
      role: "status",
      initial: { opacity: 0, y: t ? 0 : -6 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: t ? 0 : -6 },
      transition: { duration: _.settle, ease: ev },
      className: "panel chrome pointer-events-none absolute top-4 left-1/2 z-10 flex h-8 -translate-x-1/2 items-center gap-2.5 overflow-hidden rounded-full pr-3.5 pl-3",
      children: [
        /* @__PURE__ */ d(
          "span",
          {
            "aria-hidden": !0,
            className: "size-3 shrink-0 rounded-full border-[1.5px] border-accent/25 border-t-accent motion-safe:animate-spin"
          }
        ),
        /* @__PURE__ */ d("span", { className: "mono-label whitespace-nowrap text-ink", children: "Rebuilding" }),
        /* @__PURE__ */ d("span", { className: "mono-label w-9 text-right whitespace-nowrap text-muted tabular-nums", children: cn(i) }),
        e ? /* @__PURE__ */ d("span", { "aria-hidden": !0, className: "absolute inset-x-0 bottom-0 h-0.5 bg-accent/15", children: /* @__PURE__ */ d(
          "span",
          {
            className: "block h-full origin-left bg-accent ease-out",
            style: {
              transform: `scaleX(${o ? 0.92 : 0})`,
              transitionProperty: "transform",
              transitionDuration: t ? "0ms" : `${Math.max(0.3, e) * 1e3}ms`
            }
          }
        ) }) : null
      ]
    }
  );
}
const nv = Z.out;
function k2({
  version: e,
  installing: t = !1,
  onLater: n,
  onInstall: i,
  className: r
}) {
  const o = ne() === !0, s = o ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } } : { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 8 } };
  return /* @__PURE__ */ v(
    j.div,
    {
      ...s,
      transition: { duration: o ? 0 : _.settle, ease: nv },
      className: V("panel flex w-[260px] flex-col gap-2 p-4", r),
      role: "status",
      children: [
        /* @__PURE__ */ d("span", { className: "mono-caption text-muted", children: "Update" }),
        /* @__PURE__ */ v("div", { className: "flex flex-col gap-1", children: [
          /* @__PURE__ */ v("h2", { className: "font-display text-[15px] leading-5 tracking-[-0.02em] text-ink", children: [
            "nurb ",
            e,
            " is ready"
          ] }),
          /* @__PURE__ */ d("p", { className: "text-[13px] leading-[18px] text-muted", children: t ? "Closing and reopening nurb." : "Downloaded. Restart to finish." })
        ] }),
        /* @__PURE__ */ v("div", { className: "mt-1 flex items-center gap-2", children: [
          t || !n ? null : /* @__PURE__ */ d(Me, { variant: "outline", onClick: n, children: "Later" }),
          /* @__PURE__ */ d(Me, { variant: "accent", disabled: t, onClick: i, children: t ? "Restarting…" : "Restart now" })
        ] })
      ]
    }
  );
}
const iv = Z.out, Ua = [100, 93, 97, 88, 95, 91];
function rv(e, t) {
  return t > 1 && e === t - 1 ? 62 : Ua[(e * 7 + 3) % Ua.length];
}
function sv({ loading: e, delay: t = 120, minVisible: n = 380 }) {
  const [i, r] = B(!1), o = D(0);
  return O(() => {
    if (e) {
      if (i) return;
      const l = setTimeout(() => {
        o.current = performance.now(), r(!0);
      }, t);
      return () => clearTimeout(l);
    }
    if (!i) return;
    const s = Math.max(0, n - (performance.now() - o.current)), a = setTimeout(() => r(!1), s);
    return () => clearTimeout(a);
  }, [e, i, t, n]), { showSkeleton: i };
}
function T2({
  loading: e,
  children: t,
  lines: n = 3,
  lineHeight: i = 21,
  reserve: r,
  delay: o = 120,
  minVisible: s = 380,
  label: a,
  className: l
}) {
  const { showSkeleton: c } = sv({ loading: e, delay: o, minVisible: s }), u = ne(), f = D(null), h = D(null), [m, p] = B(!1), g = r ?? n * i, y = { duration: u ? 0 : _.settle, ease: iv };
  return O(() => {
    const b = f.current;
    if (!b || typeof ResizeObserver > "u") return;
    const k = () => p(b.scrollHeight - b.clientHeight > 1);
    k();
    const x = new ResizeObserver(k);
    return x.observe(b), h.current && x.observe(h.current), () => x.disconnect();
  }, []), /* @__PURE__ */ v(
    "div",
    {
      ref: f,
      "aria-busy": e,
      "aria-label": a,
      tabIndex: m ? 0 : void 0,
      style: { height: g },
      className: V("relative grid overflow-y-auto overscroll-contain text-ink-soft", l),
      children: [
        /* @__PURE__ */ d(
          j.div,
          {
            ref: h,
            className: "col-start-1 row-start-1 min-w-0",
            initial: !1,
            animate: { opacity: c ? 0 : 1 },
            transition: y,
            style: { pointerEvents: c ? "none" : void 0 },
            children: t
          }
        ),
        /* @__PURE__ */ d(ge, { initial: !1, children: c ? /* @__PURE__ */ d(
          j.div,
          {
            "aria-hidden": !0,
            "data-skeleton": !0,
            className: "pointer-events-none col-start-1 row-start-1 w-full self-start",
            initial: { opacity: 0 },
            animate: { opacity: 1 },
            exit: { opacity: 0 },
            transition: y,
            children: Array.from({ length: n }, (b, k) => /* @__PURE__ */ d("div", { className: "flex items-center", style: { height: i }, children: /* @__PURE__ */ d("div", { className: "h-[8px] rounded-[3px] bg-raised", style: { width: `${rv(k, n)}%` } }) }, k))
          },
          "skeleton"
        ) : null }),
        a ? /* @__PURE__ */ d("span", { role: "status", className: "sr-only", children: e ? "" : `${a} loaded` }) : null
      ]
    }
  );
}
const Wa = Z.out, Ha = 0.35, ov = 2200;
function S2({
  value: e,
  max: t = 100,
  segments: n,
  label: i = "Progress",
  pendingLabel: r = "Working",
  completeLabel: o = "Complete",
  className: s
}) {
  const a = ne(), l = Se(), [c, u] = B(0), f = e === null;
  O(() => {
    if (!f || a) return;
    const x = performance.now();
    let S = requestAnimationFrame(function E() {
      const C = Ha * (1 - Math.exp(-(performance.now() - x) / ov));
      u((A) => Math.max(A, C)), Ha - C > 2e-3 && (S = requestAnimationFrame(E));
    });
    return () => cancelAnimationFrame(S);
  }, [f, a]);
  const h = e === null || t <= 0 ? 0 : Math.min(1, Math.max(0, e / t)), m = Math.max(f ? c : 0, h), p = n ? Math.round(m * n) / n : m, g = Math.round(p * 100), y = !f && p >= 1, b = f ? {} : { "aria-valuenow": Math.round(h * t * 100) / 100, "aria-valuetext": `${g}%` }, k = { duration: a ? 0 : _.settle, ease: Wa };
  return /* @__PURE__ */ v("div", { className: V("w-full", s), children: [
    /* @__PURE__ */ v("div", { className: "flex items-baseline justify-between gap-3", children: [
      /* @__PURE__ */ d("span", { id: l, className: "mono-label truncate text-ink-soft", children: i }),
      /* @__PURE__ */ v("span", { "aria-hidden": !0, className: "grid shrink-0 justify-items-end", children: [
        /* @__PURE__ */ d(
          j.span,
          {
            className: "mono-label col-start-1 row-start-1 whitespace-nowrap text-muted",
            initial: !1,
            animate: { opacity: f ? 1 : 0 },
            transition: k,
            children: r
          }
        ),
        /* @__PURE__ */ v(
          j.span,
          {
            className: "mono-value col-start-1 row-start-1 whitespace-nowrap text-ink",
            initial: !1,
            animate: { opacity: f ? 0 : 1 },
            transition: k,
            children: [
              g,
              "%"
            ]
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ d(
      "div",
      {
        role: "progressbar",
        "aria-labelledby": l,
        "aria-valuemin": 0,
        "aria-valuemax": t,
        ...b,
        className: "mt-2 h-[8px] overflow-hidden rounded-[3px] bg-raised",
        children: n ? /* @__PURE__ */ d("div", { className: "flex h-full gap-px", "data-cells": n, children: Array.from({ length: n }, (x, S) => /* @__PURE__ */ d(
          j.span,
          {
            "data-lit": S < Math.round(p * n) ? "" : void 0,
            className: "h-full flex-1 bg-accent first:rounded-l-[3px] last:rounded-r-[3px]",
            initial: !1,
            animate: { opacity: S < Math.round(p * n) ? 1 : 0.12 },
            transition: { duration: a ? 0 : _.tick, ease: Wa }
          },
          S
        )) }) : /* @__PURE__ */ d(
          j.span,
          {
            className: "block h-full origin-left rounded-[3px] bg-accent",
            initial: !1,
            animate: { scaleX: p },
            transition: k
          }
        )
      }
    ),
    /* @__PURE__ */ d("span", { "aria-live": "polite", className: "sr-only", children: y ? o : f ? r : "" })
  ] });
}
const Oi = Z.out, Ga = { duration: 0 }, Ka = {
  warn: { surface: "bg-warn-wash border-warn/25", mark: "text-warn" },
  fail: { surface: "bg-fail-wash border-fail/25", mark: "text-fail" },
  neutral: { surface: "bg-raised border-line", mark: "text-ink" }
};
function av({
  state: e,
  defaultState: t = "open",
  onStateChange: n,
  onDismiss: i
} = {}) {
  const [r, o] = B(t), s = e ?? r, a = D(n);
  a.current = n;
  const l = D(i);
  l.current = i;
  const c = Q((p) => {
    o(p), a.current?.(p);
  }, []), u = Q(() => c("folded"), [c]), f = Q(() => c("open"), [c]), h = Q(() => c(s === "open" ? "folded" : "open"), [c, s]), m = Q(() => {
    c("dismissed"), l.current?.();
  }, [c]);
  return {
    state: s,
    open: s === "open",
    folded: s === "folded",
    dismissed: s === "dismissed",
    fold: u,
    expand: f,
    toggle: h,
    dismiss: m
  };
}
function A2({
  title: e,
  description: t,
  children: n,
  action: i,
  tone: r = "neutral",
  dismissible: o = !0,
  state: s,
  defaultState: a = "open",
  onStateChange: l,
  onDismiss: c,
  dismissLabel: u = "Dismiss notice",
  className: f
}) {
  const h = ne() === !0, m = Se(), p = `${m}-body`, g = `${m}-title`, { state: y, open: b, dismissed: k, toggle: x, fold: S, dismiss: E } = av({
    state: s,
    defaultState: a,
    onStateChange: l,
    onDismiss: c
  }), C = !!(t || n || i), A = { duration: h ? 0 : _.settle, ease: Oi };
  return /* @__PURE__ */ v(U, { children: [
    /* @__PURE__ */ d(
      j.div,
      {
        initial: { height: 0, opacity: 0 },
        animate: { height: k ? 0 : "auto", opacity: k ? 0 : 1 },
        transition: A,
        style: { overflow: "hidden" },
        children: /* @__PURE__ */ v(
          "div",
          {
            role: "region",
            "aria-labelledby": g,
            className: V("rounded-[12px] border", Ka[r].surface, f),
            children: [
              /* @__PURE__ */ v("div", { className: "flex items-center gap-2 p-2.5", children: [
                /* @__PURE__ */ d("span", { "aria-hidden": "true", className: V("flex shrink-0", Ka[r].mark), children: /* @__PURE__ */ d(z, { name: r === "neutral" ? "box" : "warning" }) }),
                C ? /* @__PURE__ */ v(
                  "button",
                  {
                    type: "button",
                    onClick: x,
                    onKeyDown: (N) => {
                      N.key !== "Escape" || !b || (N.stopPropagation(), S());
                    },
                    "aria-expanded": b,
                    "aria-controls": p,
                    className: "chrome group flex min-w-0 flex-1 items-center gap-2 rounded-[3px] text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
                    children: [
                      /* @__PURE__ */ d("span", { id: g, className: "min-w-0 flex-1 truncate text-[13px] leading-5 font-medium text-ink", children: e }),
                      /* @__PURE__ */ d(
                        j.span,
                        {
                          "aria-hidden": "true",
                          className: "flex shrink-0 text-muted group-hover:text-ink",
                          initial: !1,
                          animate: { rotate: b ? 180 : 0 },
                          transition: h ? Ga : { duration: _.tick, ease: Oi },
                          children: /* @__PURE__ */ d(z, { name: "chevron-down" })
                        }
                      )
                    ]
                  }
                ) : /* @__PURE__ */ d("span", { id: g, className: "min-w-0 flex-1 truncate text-[13px] leading-5 font-medium text-ink", children: e }),
                o ? /* @__PURE__ */ d(Ns, { icon: "xmark", label: u, onClick: E }) : null
              ] }),
              C ? /* @__PURE__ */ d(
                j.div,
                {
                  id: p,
                  inert: !b,
                  initial: !1,
                  animate: { height: b ? "auto" : 0, opacity: b ? 1 : 0 },
                  transition: h ? Ga : { height: A, opacity: { duration: _.tick, ease: Oi, delay: b ? 0.05 : 0 } },
                  style: { overflow: "hidden" },
                  children: /* @__PURE__ */ v("div", { className: "pr-2.5 pb-2.5 pl-[30px]", children: [
                    t ? /* @__PURE__ */ d("p", { className: "text-[12.5px] leading-relaxed text-muted", children: t }) : null,
                    n,
                    i ? /* @__PURE__ */ d("div", { className: "mt-2", children: i }) : null
                  ] })
                }
              ) : null
            ]
          }
        )
      }
    ),
    /* @__PURE__ */ d("span", { role: "status", "aria-live": "polite", className: "sr-only", children: y === "dismissed" ? "Notice dismissed." : "" })
  ] });
}
const lv = Z.out, vr = { duration: 0 }, cv = { duration: _.coast, ease: "linear", repeat: 1 / 0 };
function C2({ linger: e = 2e3 } = {}) {
  const [t, n] = B(null), i = D(0), r = D(null), o = Q(() => {
    r.current && clearTimeout(r.current), r.current = null;
  }, []), s = Q(
    (f) => {
      o(), i.current += 1;
      const h = `activity-${i.current}`;
      return n({ ...f, id: h, tone: "working" }), h;
    },
    [o]
  ), a = Q((f) => {
    n((h) => h && { ...h, ...f });
  }, []), l = Q(() => {
    o(), n(null);
  }, [o]), c = Q(
    (f) => {
      n((h) => h && { ...h, ...f, tone: "done" }), o(), r.current = setTimeout(() => {
        r.current = null, n(null);
      }, e);
    },
    [o, e]
  ), u = Q(
    (f) => {
      o(), n((h) => h && { ...h, ...f, tone: "fail" });
    },
    [o]
  );
  return O(() => o, [o]), { activity: t, start: s, update: a, succeed: c, fail: u, dismiss: l };
}
function N2({
  activity: e,
  onDismiss: t,
  label: n = "Activity",
  className: i
}) {
  const r = ne() === !0, [o, s] = B(""), a = D(/* @__PURE__ */ new Set()), l = e?.tone ?? "working";
  return O(() => {
    if (!e) return;
    const c = `${e.id}:${l}`;
    a.current.has(c) || (a.current.add(c), s(
      l === "working" ? `${e.title} started.` : l === "done" ? `${e.title} finished.` : `${e.title} failed.`
    ));
  }, [e, l]), /* @__PURE__ */ v("div", { role: "region", "aria-label": n, className: V("pointer-events-none flex justify-center", i), children: [
    /* @__PURE__ */ d(ge, { initial: !1, mode: "wait", children: e ? /* @__PURE__ */ v(
      j.div,
      {
        initial: r ? { opacity: 0 } : { opacity: 0, y: -10, scale: 0.94 },
        animate: { opacity: 1, y: 0, scale: 1 },
        exit: r ? { opacity: 0, transition: vr } : { opacity: 0, y: -8, scale: 0.97 },
        transition: r ? vr : { duration: _.settle, ease: lv },
        style: { transformOrigin: "50% 0%" },
        className: "pointer-events-auto flex max-w-[320px] items-center gap-2 rounded-[12px] border border-line bg-ground px-3 py-2 shadow-[var(--shadow-panel)]",
        children: [
          /* @__PURE__ */ d(uv, { tone: l, reduced: r }),
          /* @__PURE__ */ v("span", { className: "min-w-0 flex-1", children: [
            /* @__PURE__ */ d("span", { className: "block truncate text-[13px] leading-5 font-medium text-ink", children: e.title }),
            e.detail ? /* @__PURE__ */ d("span", { className: "mono-caption block truncate text-muted", children: e.detail }) : null
          ] }),
          t && l !== "working" ? /* @__PURE__ */ d(Ns, { icon: "xmark", label: "Dismiss activity", onClick: t }) : null
        ]
      },
      e.id
    ) : null }),
    /* @__PURE__ */ d("span", { role: "status", "aria-live": "polite", className: "sr-only", children: o })
  ] });
}
function uv({ tone: e, reduced: t }) {
  return e === "done" ? /* @__PURE__ */ d("span", { className: "flex shrink-0 text-pass", "data-tone": "done", children: /* @__PURE__ */ d(z, { name: "check" }) }) : e === "fail" ? /* @__PURE__ */ d("span", { className: "flex shrink-0 text-fail", "data-tone": "fail", children: /* @__PURE__ */ d(z, { name: "warning" }) }) : /* @__PURE__ */ d(
    j.span,
    {
      className: "flex shrink-0 text-accent",
      "data-tone": "working",
      style: { transformOrigin: "50% 50%" },
      animate: t ? void 0 : { rotate: 360 },
      transition: t ? vr : cv,
      children: /* @__PURE__ */ d(z, { name: "loader" })
    }
  );
}
const fv = Z.out, qa = { duration: 0 }, dv = (e) => `${e} new ${e === 1 ? "item" : "items"}`;
function P2({
  count: e,
  onClick: t,
  anchor: n = "bottom",
  label: i = dv,
  className: r
}) {
  const o = ne() === !0, [s, a] = B(0);
  O(() => {
    if (e === 0) {
      a(0);
      return;
    }
    const u = setTimeout(() => a(e), 700);
    return () => clearTimeout(u);
  }, [e]);
  const l = i(e), c = n === "bottom" ? 10 : -10;
  return /* @__PURE__ */ v(
    "div",
    {
      className: V(
        "pointer-events-none absolute inset-x-0 z-10 flex justify-center",
        n === "bottom" ? "bottom-2" : "top-2",
        r
      ),
      children: [
        /* @__PURE__ */ d(ge, { initial: !1, children: e > 0 ? /* @__PURE__ */ v(
          j.button,
          {
            type: "button",
            onClick: t,
            "aria-label": l,
            initial: o ? { opacity: 0 } : { opacity: 0, scale: 0.94, y: c },
            animate: { opacity: 1, scale: 1, y: 0 },
            exit: o ? { opacity: 0, transition: qa } : { opacity: 0, scale: 0.96, y: c * 0.5 },
            transition: o ? qa : { duration: _.settle, ease: fv },
            className: "chrome btn-label pointer-events-auto inline-flex h-7 items-center gap-1.5 rounded-[3px] border border-line bg-ground pr-3 pl-2.5 text-ink-soft shadow-[var(--shadow-panel)] hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
            children: [
              /* @__PURE__ */ d("span", { "aria-hidden": "true", className: V("flex text-accent", n === "bottom" && "rotate-180"), children: /* @__PURE__ */ d(z, { name: "arrow-up" }) }),
              /* @__PURE__ */ d("span", { className: "tabular-nums", "aria-hidden": "true", children: l })
            ]
          }
        ) : null }),
        /* @__PURE__ */ d("span", { role: "status", "aria-live": "polite", className: "sr-only", children: s > 0 ? i(s) : "" })
      ]
    }
  );
}
const hv = Z.out;
function M2({
  options: e,
  label: t,
  value: n,
  onValueChange: i,
  className: r
}) {
  const o = Se(), s = ne(), a = D([]), [l, c] = B(null), u = e.findIndex((g) => g.value === n), f = u < 0 ? 0 : u, h = l ?? f, m = (g) => {
    const y = (g + e.length) % e.length;
    a.current[y]?.focus();
  }, p = (g) => {
    g !== n && (qe("toggle"), i(g));
  };
  return /* @__PURE__ */ d(
    "div",
    {
      role: "radiogroup",
      "aria-label": t,
      onBlur: (g) => {
        g.currentTarget.contains(g.relatedTarget) || c(null);
      },
      className: V(
        "chrome grid auto-cols-fr grid-flow-col gap-px rounded-[3px] border border-line bg-raised p-[2px]",
        r
      ),
      children: e.map((g, y) => /* @__PURE__ */ v(
        "button",
        {
          ref: (b) => {
            a.current[y] = b;
          },
          type: "button",
          role: "radio",
          "aria-checked": y === f,
          tabIndex: y === h ? 0 : -1,
          onFocus: () => c(y),
          onClick: () => p(g.value),
          onKeyDown: (b) => {
            if (b.key === "ArrowRight" || b.key === "ArrowDown") m(y + 1);
            else if (b.key === "ArrowLeft" || b.key === "ArrowUp") m(y - 1);
            else if (b.key === "Home") m(0);
            else if (b.key === "End") m(e.length - 1);
            else if (b.key === "Enter" || b.key === " ") p(g.value);
            else return;
            b.preventDefault();
          },
          className: V(
            "mono-label relative flex h-6 items-center justify-center rounded-[3px] px-2.5 whitespace-nowrap transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
            y === f ? "text-ink" : "text-muted hover:text-ink-soft"
          ),
          children: [
            y === f ? /* @__PURE__ */ d(
              j.span,
              {
                layoutId: o,
                "aria-hidden": !0,
                transition: { duration: s ? 0 : _.settle, ease: hv },
                className: "absolute inset-0 rounded-[3px] bg-ground"
              }
            ) : null,
            /* @__PURE__ */ d("span", { className: "relative", children: g.label })
          ]
        },
        g.value
      ))
    }
  );
}
const Ku = Z.out, pt = { duration: 0 };
function pv({ steps: e, current: t, failed: n = !1 }) {
  const i = !n && t >= e.length, r = e.map((a, l) => ({
    ...a,
    status: l < t ? "done" : l === t && n ? "failed" : l === t && !i ? "active" : "pending"
  })), o = r.find((a) => a.status === "active"), s = n ? `Failed at ${e[Math.min(t, e.length - 1)]?.label ?? "step"}` : i ? `All ${e.length} steps complete` : o ? `${o.label}, step ${t + 1} of ${e.length}` : "";
  return { rows: r, complete: i, failed: n, sentence: s };
}
function mv({ reduced: e }) {
  return /* @__PURE__ */ d("svg", { viewBox: "0 0 256 256", width: "11", height: "11", fill: "none", "aria-hidden": !0, children: /* @__PURE__ */ d(
    j.polyline,
    {
      points: "216 72 104 184 48 128",
      stroke: "currentColor",
      strokeWidth: "26",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      initial: { pathLength: 0 },
      animate: { pathLength: 1 },
      transition: { duration: e ? 0 : _.settle, ease: Ku }
    }
  ) });
}
function gv() {
  return /* @__PURE__ */ d("svg", { viewBox: "0 0 256 256", width: "10", height: "10", fill: "none", "aria-hidden": !0, children: /* @__PURE__ */ d("path", { d: "M200 56 56 200 M56 56l144 144", stroke: "currentColor", strokeWidth: "26", strokeLinecap: "round" }) });
}
function yv({ reduced: e }) {
  return /* @__PURE__ */ v(
    j.svg,
    {
      viewBox: "0 0 16 16",
      className: "size-3",
      "aria-hidden": !0,
      animate: { rotate: e ? 0 : 360 },
      transition: e ? pt : { duration: _.coast / 2, ease: "linear", repeat: 1 / 0 },
      children: [
        /* @__PURE__ */ d("circle", { cx: "8", cy: "8", r: "6", fill: "none", stroke: "currentColor", strokeOpacity: "0.25", strokeWidth: "2" }),
        /* @__PURE__ */ d("path", { d: "M8 2 a6 6 0 0 1 6 6", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round" })
      ]
    }
  );
}
const xv = {
  done: "text-ink-soft",
  active: "font-medium text-ink",
  failed: "font-medium text-fail",
  pending: "text-faint"
};
function E2({
  steps: e,
  current: t,
  failed: n = !1,
  label: i = "Task progress",
  className: r
}) {
  const { rows: o, complete: s, sentence: a } = pv({ steps: e, current: t, failed: n }), l = ne() === !0, [c, u] = B("");
  O(() => {
    if (!a) return;
    const h = setTimeout(() => u(a), 500);
    return () => clearTimeout(h);
  }, [a]);
  const f = { duration: l ? 0 : _.settle, ease: Ku };
  return /* @__PURE__ */ v("div", { className: V("w-full", r), children: [
    /* @__PURE__ */ d("ol", { "aria-label": i, className: "space-y-0.5", children: o.map((h) => /* @__PURE__ */ v(
      "li",
      {
        "data-status": h.status,
        "aria-current": h.status === "active" ? "step" : void 0,
        className: "flex h-7 items-center gap-2.5 px-1",
        children: [
          /* @__PURE__ */ d("span", { className: "relative grid size-4 shrink-0 place-items-center", children: /* @__PURE__ */ d(ge, { initial: !1, children: h.status === "done" ? /* @__PURE__ */ d(
            j.span,
            {
              className: "col-start-1 row-start-1 grid size-4 place-items-center rounded-[3px] bg-pass-wash text-pass",
              initial: { opacity: l ? 1 : 0 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: pt },
              transition: f,
              children: /* @__PURE__ */ d(mv, { reduced: l })
            },
            "done"
          ) : h.status === "failed" ? /* @__PURE__ */ d(
            j.span,
            {
              className: "col-start-1 row-start-1 grid size-4 place-items-center rounded-[3px] bg-fail-wash text-fail",
              initial: { opacity: l ? 1 : 0 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: pt },
              transition: f,
              children: /* @__PURE__ */ d(gv, {})
            },
            "failed"
          ) : h.status === "active" ? /* @__PURE__ */ d(
            j.span,
            {
              className: "col-start-1 row-start-1 text-accent",
              initial: { opacity: l ? 1 : 0 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: pt },
              transition: f,
              children: /* @__PURE__ */ d(yv, { reduced: l })
            },
            "active"
          ) : /* @__PURE__ */ d(
            j.span,
            {
              className: "col-start-1 row-start-1 size-[5px] rounded-[3px] bg-line",
              initial: { opacity: 1 },
              animate: { opacity: 1 },
              exit: { opacity: 0, transition: pt },
              transition: pt
            },
            "pending"
          ) }) }),
          /* @__PURE__ */ d("span", { className: V("mono-id min-w-0 flex-1 truncate transition-colors", xv[h.status]), children: h.label }),
          h.meta ? /* @__PURE__ */ d(
            "span",
            {
              "aria-hidden": h.status !== "done",
              className: V(
                "mono-caption shrink-0 text-faint transition-opacity",
                h.status === "done" ? "opacity-100" : "opacity-0"
              ),
              children: h.meta
            }
          ) : null
        ]
      },
      h.id
    )) }),
    /* @__PURE__ */ d("span", { role: "status", className: "sr-only", children: c }),
    /* @__PURE__ */ d("span", { className: "sr-only", "aria-live": s || n ? "polite" : "off", children: s ? "Run complete" : n ? "Run failed" : "" })
  ] });
}
const bv = Z.out, qu = /-?\d*\.?\d+/g, vv = "12", wv = {
  "check-close": [
    ["M 5 12.5 L 10 17.5 L 19.5 7", "M 12 12 L 12 12 L 12 12"],
    ["M 6.5 6.5 L 12 12 L 17.5 17.5", "M 17.5 6.5 L 12 12 L 6.5 17.5"]
  ],
  "plus-minus": [
    ["M 5 12 L 19 12", "M 12 5 L 12 19"],
    ["M 5 12 L 19 12", "M 5 12 L 19 12"]
  ]
};
function kv(e) {
  const t = e.match(qu);
  return !t || t.length < 4 ? !1 : t.every((n, i) => n === t[i % 2]);
}
function Tv(e, t) {
  const n = e.reduce((r, o) => Math.max(r, o.length), 0), i = e[t] ?? e[0];
  return Array.from({ length: n }, (r, o) => {
    const s = i[o], a = e.find((c) => c[o] !== void 0)?.[o] ?? "", l = s ?? a.replace(qu, vv);
    return { key: o, d: l, visible: !kv(l) };
  });
}
function D2({
  preset: e = "check-close",
  active: t = 0,
  size: n = 12,
  strokeWidth: i = 1.75,
  label: r,
  className: o
}) {
  const s = wv[e], a = typeof t == "boolean" ? t ? 1 : 0 : Math.min(Math.max(Math.trunc(t), 0), 1), l = de(() => Tv(s, a), [s, a]), u = ne() ? { duration: 0 } : { duration: _.settle, ease: bv };
  return /* @__PURE__ */ d(
    "svg",
    {
      viewBox: "0 0 24 24",
      width: n,
      height: n,
      focusable: "false",
      role: r ? "img" : void 0,
      "aria-label": r,
      "aria-hidden": r ? void 0 : !0,
      fill: "none",
      stroke: "currentColor",
      strokeWidth: i,
      strokeLinecap: "round",
      strokeLinejoin: "round",
      className: o,
      style: { display: "block" },
      children: l.map((f) => /* @__PURE__ */ d(
        j.path,
        {
          initial: !1,
          animate: { d: f.d, opacity: f.visible ? 1 : 0 },
          transition: u
        },
        f.key
      ))
    }
  );
}
const Yu = Z.out;
function Sv({ value: e }) {
  const t = ne() === !0;
  return /* @__PURE__ */ d("span", { className: "relative inline-flex h-[13px] overflow-hidden leading-[13px] tabular-nums", children: /* @__PURE__ */ d(ge, { initial: !1, mode: "popLayout", children: /* @__PURE__ */ d(
    j.span,
    {
      initial: t ? { opacity: 0 } : { y: 13, opacity: 0 },
      animate: { y: 0, opacity: 1 },
      exit: t ? { opacity: 0 } : { y: -13, opacity: 0 },
      transition: { duration: t ? 0 : _.tick, ease: Yu },
      children: e
    },
    e
  ) }) });
}
function R2({
  questions: e,
  onAnswer: t,
  className: n
}) {
  const [i, r] = B(0), o = D(!1), s = e.length;
  O(() => {
    if (s === 0) {
      o.current = !1, r(0);
      return;
    }
    o.current || (o.current = !0, qe("scan"));
  }, [s]);
  const a = bs(!0), l = e[0];
  if (!l) return null;
  const c = i + s, u = Math.min(i + 1, c), f = (h) => {
    r((m) => m + 1), t(l.id, h);
  };
  return /* @__PURE__ */ v("div", { className: V("flex flex-col gap-2.5 rounded-[6px] bg-raised p-3", n), children: [
    c > 1 ? /* @__PURE__ */ v("div", { className: "flex items-center gap-1", children: [
      /* @__PURE__ */ v("span", { "aria-hidden": "true", className: "mono-caption flex items-center gap-1 text-faint", children: [
        /* @__PURE__ */ d(Sv, { value: u }),
        "of ",
        c
      ] }),
      /* @__PURE__ */ v("span", { className: "sr-only", children: [
        "Question ",
        u,
        " of ",
        c
      ] })
    ] }) : null,
    /* @__PURE__ */ d(j.div, { style: a.style, animate: a.animate, transition: a.transition, onAnimationComplete: a.onAnimationComplete, children: /* @__PURE__ */ d("div", { ref: a.ref, children: /* @__PURE__ */ d(ge, { initial: !1, mode: "popLayout", children: /* @__PURE__ */ v(
      j.div,
      {
        initial: { y: 12, opacity: 0 },
        animate: { y: 0, opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: _.settle, ease: Yu },
        className: "flex flex-col gap-2.5",
        children: [
          /* @__PURE__ */ d("p", { className: "text-chat text-ink", children: l.title }),
          l.detail ? /* @__PURE__ */ d("p", { className: "mono-caption text-muted", children: l.detail }) : null,
          /* @__PURE__ */ d("div", { className: "flex flex-wrap gap-1.5", children: l.actions.map((h) => /* @__PURE__ */ d(Me, { variant: h.variant ?? "outline", onClick: () => f(h.id), children: h.label }, h.id)) })
        ]
      },
      l.id
    ) }) }) })
  ] });
}
const Av = /def\s+\w+\s*\(([\s\S]*?)\)\s*(?:->[^:]*?)?:/;
function Cv(e) {
  const t = [];
  let n = 0, i = 0;
  for (let r = 0; r < e.length; r++) {
    const o = e[r];
    o === "(" || o === "[" || o === "{" ? n++ : o === ")" || o === "]" || o === "}" ? n-- : o === "," && n === 0 && (t.push(e.slice(i, r)), i = r + 1);
  }
  return t.push(e.slice(i)), t;
}
function Ya(e) {
  const t = /* @__PURE__ */ new Map(), n = e.match(Av);
  if (!n) return t;
  for (const i of Cv(n[1])) {
    const r = i.indexOf("=");
    if (r < 0) continue;
    const o = i.slice(0, r).split(":")[0].trim(), s = i.slice(r + 1).trim();
    !/^[A-Za-z_]\w*$/.test(o) || !s || t.set(o, s);
  }
  return t;
}
function Nv(e, t) {
  const n = Ya(e), i = Ya(t), r = [];
  for (const [o, s] of i) {
    const a = n.get(o);
    a === void 0 ? r.push(`added ${o}`) : a !== s && r.push(`${o} ${a} to ${s}`);
  }
  for (const o of n.keys())
    i.has(o) || r.push(`removed ${o}`);
  return r;
}
function Pv(e, t) {
  const n = e ? e.split(`
`) : [], i = t ? t.split(`
`) : [];
  let r = 0;
  for (; r < n.length && r < i.length && n[r] === i[r]; ) r++;
  let o = 0;
  for (; o < n.length - r && o < i.length - r && n[n.length - 1 - o] === i[i.length - 1 - o]; ) o++;
  const s = n.slice(r, n.length - o).map((l) => ({ sign: "-", text: l })), a = i.slice(r, i.length - o).map((l) => ({ sign: "+", text: l }));
  return [...s, ...a];
}
function Mv(e) {
  if (!e || typeof e != "object") return null;
  const t = e, n = typeof t.part_name == "string" ? t.part_name : null;
  return n ? typeof t.old_string == "string" && typeof t.new_string == "string" ? { name: n, before: t.old_string, after: t.new_string } : typeof t.source == "string" ? { name: n, after: t.source } : null : null;
}
const Xa = 12;
function L2({ input: e, className: t }) {
  const [n, i] = B(null), [r, o] = B(!1), s = bs(n !== null), a = Mv(e), l = a?.before !== void 0 ? Nv(a.before, a.after) : [];
  if (!a) return null;
  const c = l.length > 0 ? l : [`edited ${a.name}`], u = Pv(a.before ?? "", a.after), f = r ? u : u.slice(0, Xa);
  return /* @__PURE__ */ v("div", { className: V("flex flex-col gap-1.5", t), children: [
    /* @__PURE__ */ d("div", { className: "flex flex-wrap gap-1", children: c.map((h) => /* @__PURE__ */ d(
      "button",
      {
        type: "button",
        "aria-expanded": n === h,
        onClick: () => i((m) => m === h ? null : h),
        className: V(
          "mono-caption rounded-[3px] bg-raised px-1.5 py-0.5 text-muted hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          n === h && "text-ink"
        ),
        children: h
      },
      h
    )) }),
    /* @__PURE__ */ d(j.div, { style: s.style, animate: s.animate, transition: s.transition, onAnimationComplete: s.onAnimationComplete, children: /* @__PURE__ */ d("div", { ref: s.ref, children: n !== null && u.length > 0 ? /* @__PURE__ */ v("div", { className: "flex flex-col rounded-[3px] bg-raised py-1", children: [
      f.map((h, m) => /* @__PURE__ */ v(
        "span",
        {
          className: V(
            "px-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap",
            h.sign === "+" ? "bg-pass-wash text-ink-soft" : "bg-fail-wash text-ink-soft"
          ),
          children: [
            h.sign,
            " ",
            h.text
          ]
        },
        m
      )),
      !r && u.length > Xa ? /* @__PURE__ */ d(
        "button",
        {
          type: "button",
          onClick: () => o(!0),
          className: "mono-caption self-start px-2 pt-1 text-faint hover:text-ink",
          children: "show more"
        }
      ) : null
    ] }) : null }) })
  ] });
}
const Xu = Z.out;
function V2({ active: e, label: t = "Drop the photo here" }) {
  const n = ne() === !0;
  return /* @__PURE__ */ d(ge, { initial: !1, children: e ? /* @__PURE__ */ d(
    j.div,
    {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
      transition: { duration: n ? 0 : _.tick, ease: Xu },
      className: "pointer-events-none absolute inset-0 z-10 flex items-center justify-center rounded-[6px] border border-dashed border-accent bg-accent-wash",
      children: /* @__PURE__ */ d("span", { className: "btn-label text-accent-ink", children: t })
    }
  ) : null });
}
function F2({
  lines: e,
  active: t,
  everyMs: n = 4e3,
  className: i
}) {
  const [r, o] = B(0), s = ne() === !0;
  return O(() => {
    if (!t || e.length < 2) return;
    const a = setInterval(() => o((l) => (l + 1) % e.length), n);
    return () => clearInterval(a);
  }, [t, e.length, n]), !t || e.length === 0 ? null : /* @__PURE__ */ d("span", { "aria-hidden": "true", className: V("pointer-events-none absolute inset-0 block", i), children: /* @__PURE__ */ d(ge, { initial: !1, children: /* @__PURE__ */ d(
    j.span,
    {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
      transition: { duration: s ? 0 : _.settle, ease: Xu },
      className: "absolute inset-x-0 top-0 block",
      children: e[r % e.length]
    },
    r % e.length
  ) }) });
}
export {
  cx as ASSISTANT_MARKDOWN_DISALLOWED_ELEMENTS,
  t2 as AddPrinterDialog,
  R2 as ApprovalCard,
  qv as AssistantMarkdown,
  _b as BlurUpImage,
  Kv as BuildCard,
  b2 as BuildFailedBanner,
  Me as Button,
  p2 as ChatPanel,
  A2 as CollapsibleBanner,
  n2 as ConfirmDialog,
  F2 as CyclingPlaceholder,
  sb as DetentMarks,
  V2 as DropHint,
  L2 as EditChips,
  o2 as EmptyProject,
  s2 as EmptyShelf,
  Jv as ExportMenu,
  x2 as FindingsList,
  Fu as Floating,
  c2 as FloatingHeader,
  Hu as HeaderCell,
  u2 as HeaderDivider,
  h2 as HeaderIcons,
  f2 as HeaderStack,
  d2 as HeaderStatus,
  Vb as HoldToConfirm,
  z as Icon,
  Ns as IconButton,
  D2 as IconMorph,
  Pb as IsoBox,
  N2 as LiveActivity,
  ib as LoadingButton,
  i2 as Lockup,
  Xv as MeasurementCard,
  Eb as Menu,
  P2 as NewItemsPill,
  Ps as PanelStrip,
  m2 as ParamRail,
  db as ParamSlider,
  Zv as ParamsPanel,
  r2 as PartCard,
  e2 as PrinterMenu,
  S2 as ProgressBar,
  g2 as RailDisclosure,
  M2 as SegmentedControl,
  T2 as SkeletonSwap,
  Yv as SpecCard,
  a2 as Stage,
  w2 as StageBuilding,
  Hb as StageColumn,
  l2 as StageEmpty,
  v2 as StageNotice,
  E2 as TaskSteps,
  Jc as ToolStepCard,
  M0 as ToolStepGroup,
  k2 as UpdateCard,
  y2 as ValueFlash,
  Qv as ViewerIsland,
  br as adjustable,
  bb as bedLine,
  Bu as brand,
  Pv as changedLines,
  px as changedSize,
  Xc as clock,
  qe as cue,
  Vu as decimals,
  Nv as diffDefaults,
  lb as dirtyValues,
  _ as duration,
  Z as ease,
  cn as elapsedLabel,
  w0 as formatBbox,
  Gv as initials,
  nl as isDark,
  Ya as keywordDefaults,
  Bv as readSoundPrefs,
  Bf as readThemeChoice,
  v0 as relativeTime,
  Zt as rev,
  jv as setSoundEnabled,
  $v as setSoundVolume,
  zv as setThemeChoice,
  ob as sliderRange,
  Mv as sourceEdit,
  Hv as stackLabel,
  _v as startTheme,
  At as tidy,
  tb as useAsyncAction,
  bs as useAutoHeight,
  zb as useBlurUpImage,
  av as useCollapsibleBanner,
  Db as useContextMenu,
  Uv as useCopyToClipboard,
  Lb as useHoldToConfirm,
  $f as useIsDark,
  C2 as useLiveActivity,
  sv as useSkeletonSwap,
  rb as useSliderDetents,
  pv as useTaskSteps,
  Gu as useValueFlash,
  Kn as words
};
