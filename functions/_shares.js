// Shared parts on nurb.app: what the desktop app uploads, and how a share is kept.
//
// A share lives in R2 under s/<id>/ as exactly the files below. There are no accounts:
// the upload answers with a token, its SHA-256 rides on part.json's metadata, and only
// that token replaces or deletes the share. Pages routes only files that export a
// handler, so this module is never a URL of its own.

export const FILES = {
  "part.json": "application/json; charset=utf-8",
  "part.glb": "model/gltf-binary",
  "part.stl": "model/stl",
  "part.3mf": "model/3mf",
  "part.png": "image/png",
  "og.png": "image/png",
};
const MOST = 40 * 1024 * 1024;
const ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
export const ID = /^[A-Za-z0-9]{10}$/;

export const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });

export function newId() {
  const bytes = crypto.getRandomValues(new Uint8Array(10));
  return Array.from(bytes, (b) => ALPHABET[b % ALPHABET.length]).join("");
}

const hex = (buffer) => Array.from(new Uint8Array(buffer), (b) => b.toString(16).padStart(2, "0")).join("");

export function newToken() {
  return hex(crypto.getRandomValues(new Uint8Array(32)));
}

export async function digest(token) {
  return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(token)));
}

/** True when the request carries the token this share was made with. */
export async function owns(env, id, request) {
  const head = await env.SHARES.head(`s/${id}/part.json`);
  if (!head) return null;
  const sent = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  return sent !== "" && head.customMetadata?.token === (await digest(sent));
}

const starts = (bytes, ...prefix) => prefix.every((b, i) => bytes[i] === b);

/** The five files out of an upload, checked, or a sentence saying what is wrong. */
export async function readUpload(request) {
  const size = Number(request.headers.get("Content-Length") || 0);
  if (size > MOST) return { error: "a shared part can be at most 40 MB" };
  let form;
  try {
    form = await request.formData();
  } catch {
    return { error: "send the part as multipart form data" };
  }
  const files = {};
  for (const [name, value] of form.entries()) {
    if (!(name in FILES) || typeof value === "string") return { error: `${name} is not part of a shared part` };
    files[name] = new Uint8Array(await value.arrayBuffer());
  }
  for (const name of Object.keys(FILES)) {
    if (!files[name]?.length) return { error: `${name} is missing` };
  }
  let meta;
  try {
    meta = JSON.parse(new TextDecoder().decode(files["part.json"]));
  } catch {
    return { error: "part.json is not JSON" };
  }
  if (meta?.format !== 1 || typeof meta.name !== "string" || typeof meta.source !== "string") {
    return { error: "part.json is not a nurb part" };
  }
  // The page renders these, so their shapes are checked here rather than trusted there.
  const numbers = (list) => Array.isArray(list) && list.every((n) => typeof n === "number");
  if (
    !/^[a-z][a-z0-9_]*$/.test(meta.name) ||
    !(meta.title == null || typeof meta.title === "string") ||
    !Array.isArray(meta.params) ||
    !(meta.size_mm == null || numbers(meta.size_mm)) ||
    !numbers([meta.checks?.fail ?? 0, meta.checks?.warn ?? 0])
  ) {
    return { error: "part.json is not a nurb part" };
  }
  // The bytes have to be what the name says, so the bucket only ever holds parts.
  if (!starts(files["part.glb"], 0x67, 0x6c, 0x54, 0x46)) return { error: "part.glb is not a GLB" };
  if (!starts(files["part.3mf"], 0x50, 0x4b)) return { error: "part.3mf is not a 3MF" };
  for (const name of ["part.png", "og.png"]) {
    if (!starts(files[name], 0x89, 0x50, 0x4e, 0x47)) return { error: `${name} is not a PNG` };
  }
  return { files, meta };
}

export async function store(env, id, upload, token) {
  const { files, meta } = upload;
  const tokenHash = await digest(token);
  // part.json last: it is what makes a share exist, so a page never finds it half written.
  const names = Object.keys(FILES).filter((name) => name !== "part.json");
  await Promise.all(
    names.map((name) => env.SHARES.put(`s/${id}/${name}`, files[name], { httpMetadata: { contentType: FILES[name] } }))
  );
  await env.SHARES.put(`s/${id}/part.json`, files["part.json"], {
    httpMetadata: { contentType: FILES["part.json"] },
    customMetadata: { token: tokenHash, name: meta.name, shared_at: new Date().toISOString() },
  });
}

export async function drop(env, id) {
  await env.SHARES.delete(Object.keys(FILES).map((name) => `s/${id}/${name}`));
}
