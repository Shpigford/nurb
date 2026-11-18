import { json, newId, newToken, readUpload, store } from "../../_shares.js";

// A new shared part. Answers with the link and the token that later replaces or deletes it.
export async function onRequestPost({ request, env }) {
  const upload = await readUpload(request);
  if (upload.error) return json({ error: upload.error }, 400);
  let id = newId();
  while (await env.SHARES.head(`s/${id}/part.json`)) id = newId();
  const token = newToken();
  await store(env, id, upload, token);
  return json({ id, token, url: `${new URL(request.url).origin}/s/${id}` }, 201);
}
