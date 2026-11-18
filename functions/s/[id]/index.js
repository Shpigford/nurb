import { ID } from "../../_shares.js";

// The page someone lands on from a shared link: the part to turn around, its size,
// the files, and the way to open it in nurb. Drawn from the Paper mockup "16 · Public
// share page", minus what needs an account or a hosted engine (live sliders, downloads
// counter, the sharer's name).

const DMG = "https://github.com/Shpigford/nurb/releases/latest/download/nurb.dmg";
const THREE = "https://cdn.jsdelivr.net/npm/three@0.185.1";

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// "shelf_bracket" reads as "Shelf bracket" when the sharer never gave it a title.
const titled = (meta) => (typeof meta.title === "string" && meta.title.trim()) || meta.name.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
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
.page.share { height: 100vh; min-height: 640px; }
.hero { flex: 1; min-height: 0; display: flex; gap: 16px; }
.stage { position: relative; flex: 1; min-width: 0; }
.stage canvas, .stage .poster { position: absolute; inset: 0; width: 100%; height: 100%; }
.stage .poster { object-fit: contain; transition: opacity .3s; }
.stage.live .poster { opacity: 0; pointer-events: none; }
.stage canvas { cursor: grab; touch-action: none; -webkit-mask-image: radial-gradient(closest-side, #000 70%, transparent); mask-image: radial-gradient(closest-side, #000 70%, transparent); }
.stage canvas:active { cursor: grabbing; }
.stage .foot { position: absolute; left: 0; right: 0; bottom: 0; display: flex; align-items: flex-end; justify-content: space-between; padding: 0 8px 4px; pointer-events: none; }
.stage .foot .mono { font-size: 10px; line-height: 12px; letter-spacing: .11em; color: var(--muted); }
.stage .foot button { pointer-events: auto; display: flex; align-items: center; gap: 6px; height: 28px; padding: 0 11px; border: 1px solid var(--line); border-radius: 3px; background: var(--ground); color: var(--muted); font: 10px/12px var(--mono); letter-spacing: .11em; cursor: pointer; }
.stage .foot button[aria-pressed="true"] { color: var(--ink); border-color: var(--panel-edge); }
.panel { flex: 0 0 400px; display: flex; flex-direction: column; overflow: hidden; }
.panel .head { display: flex; align-items: center; justify-content: space-between; height: 30px; padding: 0 16px; border-bottom: 1px solid var(--line-soft); flex: none; }
.panel .head nav { display: flex; gap: 14px; }
.panel .head a:hover { color: var(--ink); }
.titled { padding: 28px 24px 24px; display: flex; flex-direction: column; gap: 10px; }
h1 { font: 600 34px/38px var(--sans); letter-spacing: -.032em; text-wrap: balance; overflow-wrap: anywhere; }
.lede { font-size: 15px; line-height: 23px; color: var(--muted); text-wrap: pretty; }
.size { display: flex; border-top: 1px solid var(--line-soft); border-bottom: 1px solid var(--line-soft); }
.size div { flex: 1; display: flex; flex-direction: column; gap: 6px; padding: 14px 0 14px 20px; }
.size div:first-child { padding-left: 24px; }
.size div + div { border-left: 1px solid var(--line-soft); }
.size b { font: 500 20px/24px var(--mono); }
.size small { font: 12px/16px var(--mono); color: var(--muted); }
.can { display: flex; flex-direction: column; gap: 18px; padding: 24px; }
.can li { display: flex; gap: 14px; list-style: none; }
.can ul { padding: 0; display: flex; flex-direction: column; gap: 18px; }
.can i { width: 28px; height: 28px; flex: none; display: flex; align-items: center; justify-content: center; border-radius: 4px; background: #ffede8; }
.can li b { display: block; font-weight: 600; font-size: 15px; line-height: 20px; }
.can li span { display: block; font-size: 14px; line-height: 20px; color: var(--muted); }
.actions { margin-top: auto; display: flex; flex-direction: column; gap: 10px; padding: 20px 24px 24px; border-top: 1px solid var(--line-soft); }
.actions .btn.accent { height: 48px; font-size: 12px; line-height: 16px; }
.actions .row { display: flex; gap: 10px; }
.actions .row .btn { flex: 1; height: 36px; }
.missing { display: none; padding: 12px 14px; border-radius: 3px; background: var(--raised); font-size: 14px; line-height: 21px; color: var(--ink-soft); }
.missing.shown { display: block; }
.missing a { color: var(--ink); font-weight: 600; text-decoration: underline; text-underline-offset: 3px; }
.gone { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; text-align: center; padding: 64px 16px; }
.gone h1 { margin: 0; font-size: 32px; line-height: 38px; }
.gone p { color: var(--muted); max-width: 420px; }
.gone .btn { height: 42px; padding: 0 18px; margin-top: 8px; }
@media (max-width: 1023px) {
  .page.share { height: auto; min-height: 0; }
  .hero { flex-direction: column; }
  .stage { flex: none; height: 62vw; min-height: 300px; max-height: 520px; }
  .panel { flex: none; }
}
@media (max-width: 600px) {
  .page { padding: 12px 16px; }
  .bar nav a.quiet { display: none; }
  h1 { font-size: 30px; line-height: 35px; }
  .titled, .can { padding-left: 18px; padding-right: 18px; }
  .size div:first-child { padding-left: 18px; }
  .size div { padding-left: 14px; }
  .actions { padding: 18px; }
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
  const description = "A 3D-printable part made with nurb. Print it as is, or open it in nurb and adjust it to fit.";
  // A build's bounding box is x, y, z: across, front to back, and up off the bed.
  const size = Array.isArray(meta.size_mm) && meta.size_mm.length === 3 ? meta.size_mm.map((n) => Math.round(n)) : null;
  const when = sharedAt ? new Date(sharedAt).toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" }).toUpperCase() : "";
  return `${head(title, description, `${origin}${files}/part.png`, url)}
<body><div class="page share">${BAR}
<main class="hero">
  <div class="stage" id="stage">
    <img class="poster" src="${files}/part.png" alt="${esc(title)}">
    <div class="foot">
      <div class="mono">DRAG TO TURN IT</div>
      <button type="button" id="turn" aria-pressed="false">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M10 6A4 4 0 1 1 8.6 2.9"/><path d="M8.4 1V3.2H6.2"/></svg>
        TURNTABLE
      </button>
    </div>
  </div>
  <section class="card panel">
    <div class="head cap">
      <span>SHARED PART</span>
      <nav><span>${esc(when)}</span><a href="https://github.com/Shpigford/nurb/issues/new?title=${encodeURIComponent(`Report shared part ${id}`)}">REPORT</a></nav>
    </div>
    <div class="titled">
      <h1>${esc(title)}</h1>
      <p class="lede">Print it as is, or open it in nurb and adjust it to fit.</p>
    </div>
    ${size ? `<div class="size">
      <div><span class="cap">WIDE</span><b>${size[0]}<small> mm</small></b></div>
      <div><span class="cap">DEEP</span><b>${size[1]}<small> mm</small></b></div>
      <div><span class="cap">TALL</span><b>${size[2]}<small> mm</small></b></div>
    </div>` : ""}
    <div class="can">
      <span class="cap">IN NURB YOU CAN</span>
      <ul>
        <li><i><svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="#d6380e" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4H12M2 10H12"/><circle cx="5" cy="4" r="1.6" fill="#ffede8"/><circle cx="9" cy="10" r="1.6" fill="#ffede8"/></svg></i><div><b>Resize it</b><span>Drag a slider and it rebuilds in a second.</span></div></li>
        <li><i><svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="#d6380e" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 3.5H11.5V9.5H6L3.5 11.5V9.5H2.5Z"/></svg></i><div><b>Ask for changes</b><span>Say what to change, and nurb redraws it.</span></div></li>
        <li><i><svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="#d6380e" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6V2.5H11V6M3 10.5H2V6H12V10.5H11M4 9H10V12H4Z"/></svg></i><div><b>Send it to your printer</b><span>It opens in your slicer, ready to print.</span></div></li>
      </ul>
    </div>
    <div class="actions">
      <a class="btn accent" id="open" href="nurb://open/${id}">
        <svg width="14" height="14" viewBox="0 0 15 15" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 2.5H12.5V6.5M12.5 2.5L7 8M11 9V12H3V4H6"/></svg>
        OPEN IN NURB
      </a>
      <p class="missing" id="missing" role="status">Nothing happened? <a href="${DMG}">Get nurb for Mac</a>, then try again.</p>
      <div class="row">
        <a class="btn line" href="${files}/part.3mf" download>DOWNLOAD 3MF</a>
        <a class="btn line" href="${files}/part.stl" download>DOWNLOAD STL</a>
      </div>
    </div>
  </section>
</main>
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
