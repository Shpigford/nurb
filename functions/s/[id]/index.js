import { ID } from "../../_shares.js";

// The page someone lands on from a shared link: the part to turn around, its numbers,
// the files, and the way to open it in nurb. Drawn from the Paper mockup "16 · Public
// share page", minus what needs an account or a hosted engine (live sliders, downloads
// counter, the sharer's name).

const DMG = "https://github.com/Shpigford/nurb/releases/latest/download/nurb.dmg";
const THREE = "https://cdn.jsdelivr.net/npm/three@0.185.1";

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// "shelf_bracket" reads as "Shelf bracket" when the sharer never gave it a title.
const titled = (meta) => (typeof meta.title === "string" && meta.title.trim()) || meta.name.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
const label = (name) => name.replace(/_/g, " ").toUpperCase();
const number = (n) => (Number.isInteger(n) ? String(n) : String(Math.round(n * 100) / 100));

function value(param) {
  if (param.kind === "bool") return param.value ? "ON" : "OFF";
  if (typeof param.value === "number") return number(param.value);
  return esc(param.value);
}

function checks(meta) {
  // Numbers only: part.json is whatever the uploader sent, and this lands in the page as HTML.
  const fail = Number(meta.checks?.fail) || 0;
  const warn = Number(meta.checks?.warn) || 0;
  const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "S"}`;
  if (!fail && !warn) return { tone: "pass", line: "NO PROBLEMS FOUND", note: "Walls, overhangs and bed contact all check out." };
  const parts = [fail && plural(fail, "PROBLEM"), warn && plural(warn, "WARNING")].filter(Boolean).join(" · ");
  return { tone: fail ? "fail" : "warn", line: parts, note: "Open it in nurb to see where." };
}

const MARK = {
  pass: '<path d="M2.3 5.8L4.4 7.9L8.7 3.2" stroke="var(--pass)"/>',
  warn: '<path d="M5.5 2.5V6.2M5.5 8.4V8.5" stroke="var(--warn)"/>',
  fail: '<path d="M2.8 2.8L8.2 8.2M8.2 2.8L2.8 8.2" stroke="var(--fail)"/>',
};

const STYLE = `
:root {
  --sans: "Instrument Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  --ground: #fff; --raised: #eef2f8; --stage: #e5f0fb; --line-soft: #e8edf4; --line: #dce3ed; --panel-edge: #bdcee2;
  --muted: #64707f; --ink-soft: #38424f; --ink: #121821;
  --accent: #ff5230; --accent-hover: #f0421f; --pass: #00a45a; --warn: #e08700; --fail: #b3001b;
  --shadow: 0 1px 2px #182a4a14, 0 3px 8px #182a4a0f;
}
@font-face { font-family: "Instrument Sans"; src: url(/vendor/fonts/InstrumentSans-Variable.ttf) format("truetype"); font-weight: 400 700; font-display: swap; }
@font-face { font-family: "JetBrains Mono"; src: url(/vendor/fonts/JetBrainsMono-Variable.ttf) format("truetype"); font-weight: 100 800; font-display: swap; }
* { box-sizing: border-box; margin: 0; }
body { background: var(--stage); color: var(--ink); font: 15px/24px var(--sans); -webkit-font-smoothing: antialiased; }
a { color: inherit; text-decoration: none; }
.page { display: flex; flex-direction: column; min-height: 100vh; max-width: 1440px; margin: 0 auto; padding: 16px; gap: 16px; }
.card { background: var(--ground); border: 1px solid var(--panel-edge); border-radius: 12px; box-shadow: var(--shadow); }
.cap { font: 500 10px/12px var(--mono); letter-spacing: .15em; color: var(--muted); text-transform: uppercase; }
.mono { font: 11px/14px var(--mono); letter-spacing: .1em; }
.bar { display: flex; align-items: center; justify-content: space-between; height: 52px; padding: 0 16px; }
.bar img { display: block; width: 76px; height: 21px; }
.bar nav { display: flex; align-items: center; gap: 20px; }
.bar nav a.quiet { color: var(--muted); letter-spacing: .12em; }
.bar nav a.quiet:hover { color: var(--ink); }
.btn { display: flex; align-items: center; justify-content: center; gap: 10px; border-radius: 3px; font: 500 11px/14px var(--mono); letter-spacing: .14em; cursor: pointer; }
.btn.accent { background: var(--accent); color: #fff; }
.btn.accent:hover { background: var(--accent-hover); }
.btn.line { border: 1px solid var(--line); color: var(--ink-soft); background: var(--ground); }
.btn.line:hover { border-color: var(--panel-edge); color: var(--ink); }
.btn.ink { border: 1.5px solid var(--ink); color: var(--ink); }
.btn.ink:hover { background: var(--ink); color: #fff; }
.btn.ink:hover svg path { stroke: #fff; }
.bar .btn { height: 32px; padding: 0 15px; }
.hero { display: flex; gap: 34px; padding: 20px 24px 8px; align-items: flex-start; }
.stage { position: relative; flex: 1 1 700px; min-width: 0; height: 560px; }
.stage canvas, .stage .poster { position: absolute; inset: 0; width: 100%; height: 100%; }
.stage .poster { object-fit: contain; transition: opacity .3s; }
.stage.live .poster { opacity: 0; pointer-events: none; }
.stage canvas { cursor: grab; touch-action: none; -webkit-mask-image: radial-gradient(closest-side, #000 70%, transparent); mask-image: radial-gradient(closest-side, #000 70%, transparent); }
.stage canvas:active { cursor: grabbing; }
.stage .foot { position: absolute; left: 0; right: 0; bottom: 0; display: flex; align-items: flex-end; justify-content: space-between; padding: 0 20px 18px; pointer-events: none; }
.stage .foot .mono { font-size: 10px; line-height: 12px; letter-spacing: .11em; color: var(--muted); }
.stage .foot button { pointer-events: auto; display: flex; align-items: center; gap: 6px; height: 28px; padding: 0 11px; border: 1px solid var(--line); border-radius: 3px; background: var(--ground); color: var(--muted); font: 10px/12px var(--mono); letter-spacing: .11em; cursor: pointer; }
.stage .foot button[aria-pressed="true"] { color: var(--ink); border-color: var(--panel-edge); }
.side { flex: 0 1 560px; min-width: 0; padding-top: 22px; }
.kicker { display: flex; align-items: center; gap: 9px; }
.kicker i { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex: none; }
.kicker b { font: 500 11px/14px var(--mono); letter-spacing: .13em; }
.kicker span { color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
h1 { margin-top: 18px; font: 600 40px/45px var(--sans); letter-spacing: -.032em; text-wrap: balance; overflow-wrap: anywhere; }
.lede { margin-top: 16px; font-size: 16px; line-height: 25px; color: var(--muted); max-width: 480px; }
.panel { margin-top: 28px; padding: 22px 24px 24px; display: flex; flex-direction: column; gap: 22px; }
.rule { display: flex; align-items: center; gap: 10px; }
.rule::after { content: ""; flex: 1; height: 1px; background: var(--line); }
.numbers { display: flex; flex-direction: column; max-height: 260px; overflow: auto; margin-top: -8px; }
.numbers div { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; padding: 9px 0; border-bottom: 1px solid var(--line-soft); }
.numbers div:last-child { border-bottom: 0; }
.numbers dt { font: 11px/14px var(--mono); letter-spacing: .08em; color: var(--ink-soft); }
.numbers dd { font: 500 15px/18px var(--mono); text-align: right; overflow-wrap: anywhere; }
.actions { display: flex; flex-direction: column; gap: 10px; }
.actions .btn.accent { height: 52px; font-size: 12.5px; line-height: 16px; }
.actions .row { display: flex; gap: 10px; }
.actions .row .btn { flex: 1; height: 38px; }
.missing { display: none; padding: 12px 14px; border-radius: 3px; background: var(--raised); font-size: 14px; line-height: 21px; color: var(--ink-soft); }
.missing.shown { display: block; }
.missing a { color: var(--ink); font-weight: 600; text-decoration: underline; text-underline-offset: 3px; }
.strip { display: flex; overflow: hidden; }
.strip > section { flex: 1 1 0; display: flex; flex-direction: column; gap: 16px; padding: 28px 32px 30px; min-width: 0; }
.strip > section + section { border-left: 1px solid var(--line-soft); }
.strip .big { display: flex; align-items: baseline; gap: 6px; font: 500 30px/42px var(--mono); letter-spacing: -.03em; }
.strip .big small { font: 13px/16px var(--mono); letter-spacing: 0; color: var(--muted); }
.strip .check { display: flex; align-items: center; gap: 10px; font: 11px/14px var(--mono); letter-spacing: .07em; color: var(--ink-soft); }
.strip .check svg { flex: none; }
.strip p { font-size: 14px; line-height: 21px; color: var(--muted); }
.strip h2 { font: 600 19px/26px var(--sans); letter-spacing: -.022em; }
.strip .btn.ink { height: 42px; margin-top: 2px; }
footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: auto; padding: 6px 16px 10px; }
footer .mono { font-size: 10.5px; letter-spacing: .12em; color: var(--muted); }
footer nav { display: flex; gap: 22px; }
footer nav a:hover, footer nav a.home { color: var(--ink); }
.gone { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; text-align: center; padding: 64px 16px; }
.gone h1 { margin: 0; font-size: 32px; line-height: 38px; }
.gone p { color: var(--muted); max-width: 420px; }
.gone .btn { height: 42px; padding: 0 18px; margin-top: 8px; }
@media (max-width: 1023px) {
  .hero { flex-direction: column; padding: 8px 0 0; gap: 8px; }
  .stage { flex: none; width: 100%; height: 62vw; min-height: 300px; max-height: 520px; }
  .side { flex: none; width: 100%; padding-top: 0; }
  .strip { flex-direction: column; }
  .strip > section + section { border-left: 0; border-top: 1px solid var(--line-soft); }
}
@media (max-width: 600px) {
  .page { padding: 12px 16px; }
  .bar nav a.quiet { display: none; }
  h1 { font-size: 30px; line-height: 35px; }
  .panel { padding: 18px 16px 20px; }
  .strip > section { padding: 22px 18px 24px; }
  footer { flex-direction: column; align-items: flex-start; }
}
`;

function head(title, description, image, url) {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} · nurb</title>
<meta name="description" content="${esc(description)}">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
${url ? `<meta property="og:url" content="${esc(url)}">` : ""}
<meta property="og:image" content="${esc(image)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/vendor/brand/favicon.svg" type="image/svg+xml">
<style>${STYLE}</style>
</head>`;
}

const BAR = `<header class="card bar">
  <a href="/" aria-label="nurb home"><img src="/vendor/brand/nurb-lockup.svg" alt="nurb"></a>
  <nav class="mono">
    <a class="quiet" href="/">WHAT IS NURB</a>
    <a class="btn accent" href="${DMG}">GET NURB FOR MAC</a>
  </nav>
</header>`;

function gone(origin) {
  return `${head("This part is no longer shared", "Whoever shared it took the link down.", `${origin}/og.png`)}
<body><div class="page">${BAR}
<main class="gone">
  <span class="cap">NOT SHARED ANYMORE</span>
  <h1>This part is no longer shared</h1>
  <p>Whoever shared it took the link down, or the link has a typo. Ask them for a new one.</p>
  <a class="btn ink" href="/">SEE WHAT NURB MAKES</a>
</main>
</div></body></html>`;
}

function page(id, meta, sharedAt, origin) {
  const title = titled(meta);
  const url = `${origin}/s/${id}`;
  const files = `/s/${id}`;
  const description = "A 3D-printable part made with nurb. Print it as is, or open it in nurb and change the numbers to fit.";
  const size = Array.isArray(meta.size_mm) ? meta.size_mm.map((n) => Math.round(n)).join(" × ") : null;
  const verdict = checks(meta);
  const when = sharedAt ? new Date(sharedAt).toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" }).toUpperCase() : "";
  const params = (Array.isArray(meta.params) ? meta.params : []).filter((p) => p && typeof p.name === "string");
  return `${head(title, description, `${origin}${files}/part.png`, url)}
<body><div class="page">${BAR}
<main class="hero">
  <div class="stage" id="stage">
    <img class="poster" src="${files}/part.png" alt="${esc(title)}">
    <div class="foot">
      <div class="mono">ISOMETRIC · MM · DRAG TO TURN IT</div>
      <button type="button" id="turn" aria-pressed="false">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M10 6A4 4 0 1 1 8.6 2.9"/><path d="M8.4 1V3.2H6.2"/></svg>
        TURNTABLE
      </button>
    </div>
  </div>
  <div class="side">
    <div class="kicker"><i></i><b>SHARED PART</b><span class="mono">${esc(meta.name)}</span></div>
    <h1>${esc(title)}</h1>
    <p class="lede">Print it as is, or open it in nurb and change the numbers to fit.</p>
    <div class="card panel">
      ${params.length ? `<div class="rule cap">THE NUMBERS IT WAS SHARED AT</div>
      <dl class="numbers">${params.map((p) => `<div><dt>${esc(label(p.name))}</dt><dd>${value(p)}</dd></div>`).join("")}</dl>` : ""}
      <div class="actions">
        <a class="btn accent" id="open" href="nurb://open/${id}">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 2.5H12.5V6.5M12.5 2.5L7 8M11 9V12H3V4H6"/></svg>
          OPEN IN NURB
        </a>
        <p class="missing" id="missing" role="status">Nothing happened? <a href="${DMG}">Get nurb for Mac</a>, then try again.</p>
        <div class="row">
          <a class="btn line" href="${files}/part.3mf" download>DOWNLOAD 3MF</a>
          <a class="btn line" href="${files}/part.stl" download>DOWNLOAD STL</a>
        </div>
      </div>
    </div>
  </div>
</main>
<div class="card strip">
  ${size ? `<section>
    <span class="cap">SIZE</span>
    <div class="big">${esc(size)}<small>mm</small></div>
  </section>` : ""}
  <section>
    <span class="cap">CHECKED BEFORE YOU PRINT</span>
    <div class="check"><svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${MARK[verdict.tone]}</svg>${esc(verdict.line)}</div>
    <p>${verdict.note}</p>
  </section>
  <section>
    <span class="cap">NEED SOMETHING ELSE</span>
    <h2>Describe the part you need, and nurb builds it.</h2>
    <a class="btn ink" href="${DMG}">GET NURB FOR MAC
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="var(--ink)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 6H9.5M6.6 3.1L9.5 6L6.6 8.9"/></svg>
    </a>
  </section>
</div>
<footer class="mono">
  <span>SHARED ${esc(when)}</span>
  <nav>
    <a href="https://github.com/Shpigford/nurb/issues/new?title=${encodeURIComponent(`Report shared part ${id}`)}">REPORT</a>
    <a class="home" href="/">MADE WITH NURB</a>
  </nav>
</footer>
</div>
<script>
  // The app answers nurb:// links. When it is not installed the click does nothing, so
  // after a moment with the page still in front, say what to do instead.
  document.getElementById("open").addEventListener("click", () => {
    let left = false;
    const away = () => { left = true; };
    window.addEventListener("blur", away, { once: true });
    document.addEventListener("visibilitychange", away, { once: true });
    setTimeout(() => { if (!left) document.getElementById("missing").classList.add("shown"); }, 1600);
  });
</script>
<script type="importmap">{"imports":{"three":"${THREE}/build/three.module.js","three/addons/":"${THREE}/examples/jsm/"}}</script>
<script type="module">
  import * as THREE from "three";
  import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
  import { OrbitControls } from "three/addons/controls/OrbitControls.js";

  // The app's look: Z up, the accent part with a darker edge, one steep key light.
  const stage = document.getElementById("stage");
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  stage.prepend(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 10000);
  camera.up.set(0, 0, 1);
  const key = new THREE.DirectionalLight(0xffffff, 6);
  key.position.set(0.4, -0.9, 2.9);
  const sky = new THREE.HemisphereLight(0xffffff, 0xbcd2e8, 1);
  sky.position.set(0, 0, 1);
  scene.add(key, sky);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enableZoom = false;

  const resize = () => {
    const { width, height } = stage.getBoundingClientRect();
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };
  new ResizeObserver(resize).observe(stage);
  resize();

  new GLTFLoader().load("${files}/part.glb", (gltf) => {
    gltf.scene.traverse((node) => {
      if (!node.isMesh) return;
      if (!node.geometry.attributes.normal) node.geometry.computeVertexNormals();
      const context = node.name === "context";
      node.material = new THREE.MeshStandardMaterial({
        color: context ? 0x78818d : node.name === "text" ? 0xd9dde4 : 0xff5230,
        metalness: 0, roughness: 0.85, transparent: context, opacity: context ? 0.3 : 1,
        polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
      });
      if (!context) node.add(new THREE.LineSegments(new THREE.EdgesGeometry(node.geometry, 25),
        new THREE.LineBasicMaterial({ color: 0xa32409, transparent: true, opacity: 0.35 })));
    });
    // Plated the way a slicer plates it: centred, standing on z = 0.
    const raw = new THREE.Box3().setFromObject(gltf.scene);
    const at = raw.getCenter(new THREE.Vector3());
    gltf.scene.position.set(-at.x, -at.y, -raw.min.z);
    scene.add(gltf.scene);
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const mid = box.getCenter(new THREE.Vector3());
    const span = box.getSize(new THREE.Vector3()).length();
    // The bed under it, in the app's grid colours, so the part sits on something.
    const size = Math.ceil((span * 1.6) / 10) * 10;
    const grid = new THREE.GridHelper(size, size / 10, 0xbcd2e8, 0xcfe0f1);
    grid.rotation.x = Math.PI / 2;
    grid.position.z = -0.01;
    scene.add(grid);
    const dist = (span / (2 * Math.tan((camera.fov * Math.PI) / 360))) * 1.35;
    const dir = new THREE.Vector3(0.7, -0.75, 0.6).normalize();
    camera.position.copy(mid).addScaledVector(dir, dist);
    camera.near = span / 100; camera.far = span * 100; camera.updateProjectionMatrix();
    controls.target.copy(mid);
    controls.update();
    stage.classList.add("live");
  });

  const turn = document.getElementById("turn");
  turn.addEventListener("click", () => {
    controls.autoRotate = !controls.autoRotate;
    turn.setAttribute("aria-pressed", String(controls.autoRotate));
  });
  renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
</script>
</body></html>`;
}

export async function onRequestGet({ params, env, request }) {
  const origin = new URL(request.url).origin;
  const html = (body, status = 200) =>
    new Response(body, { status, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=60" } });
  if (!ID.test(params.id)) return html(gone(origin), 404);
  const object = await env.SHARES.get(`s/${params.id}/part.json`);
  if (!object) return html(gone(origin), 404);
  let meta;
  try {
    meta = JSON.parse(await object.text());
  } catch {
    return html(gone(origin), 404);
  }
  return html(page(params.id, meta, object.customMetadata?.shared_at, origin));
}
