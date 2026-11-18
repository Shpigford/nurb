import { FILES, ID } from "../../_shares.js";

// One file of a shared part. The downloads are named after the part, so a slicer
// opens "shelf_bracket.3mf" rather than "part.3mf".
export async function onRequestGet({ params, env }) {
  if (!ID.test(params.id) || !(params.file in FILES)) return new Response("not found", { status: 404 });
  const object = await env.SHARES.get(`s/${params.id}/${params.file}`);
  if (!object) return new Response(JSON.stringify({ error: "no shared part at that link" }), { status: 404 });
  const headers = new Headers({
    "Content-Type": FILES[params.file],
    // A replaced share keeps its URL, so caches must ask again rather than keep the old part.
    "Cache-Control": "public, max-age=60",
    "Access-Control-Allow-Origin": "*",
    ETag: object.httpEtag,
  });
  if (params.file === "part.stl" || params.file === "part.3mf") {
    const meta = await env.SHARES.head(`s/${params.id}/part.json`);
    const name = /^[a-z0-9_]+$/.test(meta?.customMetadata?.name || "") ? meta.customMetadata.name : "part";
    headers.set("Content-Disposition", `attachment; filename="${name}${params.file.slice(4)}"`);
  }
  return new Response(object.body, { headers });
}
