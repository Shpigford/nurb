import { ID, drop, json, owns, readUpload, store } from "../../_shares.js";

async function guarded(params, env, request) {
  if (!ID.test(params.id)) return json({ error: "no shared part at that link" }, 404);
  const owner = await owns(env, params.id, request);
  if (owner === null) return json({ error: "no shared part at that link" }, 404);
  if (!owner) return json({ error: "only the copy of nurb that shared this part can change it" }, 403);
  return null;
}

// The same link, now showing a newer build of the part.
export async function onRequestPut({ params, request, env }) {
  const refused = await guarded(params, env, request);
  if (refused) return refused;
  const upload = await readUpload(request);
  if (upload.error) return json({ error: upload.error }, 400);
  const token = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  await store(env, params.id, upload, token);
  return json({ id: params.id, url: `${new URL(request.url).origin}/s/${params.id}` });
}

// The link taken down. Its page then says the part is no longer shared.
export async function onRequestDelete({ params, request, env }) {
  const refused = await guarded(params, env, request);
  if (refused) return refused;
  await drop(env, params.id);
  return json({ deleted: params.id });
}
