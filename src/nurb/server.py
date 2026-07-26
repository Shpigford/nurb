"""The dev server: watch parts, rebuild, push to the browser.

One process holds the OCCT import (~2s) so every rebuild after that is ~50ms.
One port serves both the viewer and the websocket.
"""

import asyncio
import json
import pathlib
import secrets
import traceback

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from websockets.asyncio.server import serve
from websockets.http11 import Response
from websockets.datastructures import Headers

from . import builder

VIEWER = pathlib.Path(__file__).parent / "viewer.html"
VENDOR = (pathlib.Path(__file__).parent / "vendor").resolve()


def _user_traceback(exc, path):
    """Trim nurb's own frames so the trace starts in the user's part file."""
    tb = exc.__traceback__
    target = str(pathlib.Path(path).resolve())
    walk = tb
    while walk:
        if walk.tb_frame.f_code.co_filename == target:
            tb = walk
            break
        walk = walk.tb_next
    return "".join(traceback.format_exception(type(exc), exc, tb))


class Server:
    def __init__(self, root, port=7373, tolerance=0.1, draft=True):
        self.root = pathlib.Path(root).resolve()
        self.port = port
        self.tolerance = tolerance
        self.draft = draft
        self.state = {}
        # What the sliders are holding, per part, and only where it differs from the
        # file. Empty means the part is exactly what its source says.
        self.overrides = {}
        self.clients = set()
        self.loop = None
        self.queue = None
        self.observer = None
        self.drain_task = None

    @property
    def origins(self):
        """The socket takes commands that write to the user's source, and any page in
        any tab can open a socket to localhost. Only the viewer this server serves gets
        to drive it."""
        return [f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"]

    # ---------- building ----------

    def _build(self, path, name):
        """Build with whatever the sliders are holding for this part."""
        try:
            return builder.build(path, overrides=self.overrides.get(name), draft=self.draft)
        except builder.UnknownParams as exc:
            # An edit renamed or removed a parameter a slider was still holding. The
            # file is the authority, so those get dropped and the build goes ahead: a
            # stale slider is not a broken part, and reporting it as one would name a
            # parameter the user never typed.
            for gone in exc.names:
                self.overrides.get(name, {}).pop(gone, None)
            if not self.overrides.get(name):
                self.overrides.pop(name, None)
            return builder.build(path, overrides=self.overrides.get(name), draft=self.draft)

    def rebuild(self, path):
        name = pathlib.Path(path).stem
        entry = {"name": name, "token": secrets.token_hex(4), "findings": None}
        try:
            shape, params, ms = self._build(path, name)
            entry["glb"] = builder.to_glb(shape, self.tolerance)
            entry.update(builder.stats(shape))
            entry["params"] = params
            entry["ms"] = round(ms, 1)
            entry["error"] = None
            entry["shape"] = shape  # kept for the check pass, never serialized
        except Exception as exc:
            entry["glb"] = None
            entry["shape"] = None
            entry["error"] = f"{type(exc).__name__}: {exc}"
            entry["traceback"] = _user_traceback(exc, path)
        self.state[name] = entry
        return entry

    def check(self, path):
        """Run the rules on the last good build.

        Separate from `rebuild` and broadcast separately, because checking the shelf
        costs about as much again as building it. Geometry should land at the speed it
        always did and the findings can arrive a beat later.
        """
        from . import checks

        entry = self.state.get(pathlib.Path(path).stem)
        if not entry or entry.get("shape") is None:
            return entry
        try:
            found = checks.run(entry["shape"], checks.from_card(path))
            entry["findings"] = [
                {
                    "rule": f.rule,
                    "severity": f.severity,
                    "message": f.message,
                    "where": list(f.where) if f.where else None,
                }
                for f in found
            ]
        except Exception as exc:
            entry["findings"] = [
                {
                    "rule": "check",
                    "severity": "fail",
                    "message": f"{type(exc).__name__}: {exc}",
                    "where": None,
                }
            ]
        return entry

    def rebuild_all(self):
        for path in builder.find_parts(self.root):
            entry = self.rebuild(path)
            self.check(path)
            status = entry["error"] or f"{entry['ms']}ms"
            note = ""
            if entry.get("findings"):
                bad = sum(1 for f in entry["findings"] if f["severity"] == "fail")
                note = f"  {len(entry['findings'])} finding(s), {bad} to fix"
            print(f"  {entry['name']}: {status}{note}", flush=True)

    # ---------- http ----------

    def http(self, connection, request):
        path = request.path.split("?")[0]
        if path == "/":
            return self._resp(200, VIEWER.read_bytes(), "text/html; charset=utf-8")
        if path == "/api/parts":
            body = json.dumps([self._meta(e) for e in self.state.values()]).encode()
            return self._resp(200, body, "application/json")
        if path.startswith("/vendor/"):
            # three.js, shipped in the package. A CAD tool that needs a CDN is broken
            # on a plane, and `nurb render` drives this same page.
            target = (VENDOR / path[len("/vendor/") :]).resolve()
            if target.suffix == ".js" and target.is_relative_to(VENDOR) and target.is_file():
                return self._resp(200, target.read_bytes(), "text/javascript; charset=utf-8")
            return self._resp(404, b"not found", "text/plain")
        if path.startswith("/glb/"):
            entry = self.state.get(path[5:].removesuffix(".glb"))
            if entry and entry["glb"]:
                return self._resp(200, entry["glb"], "model/gltf-binary")
            return self._resp(404, b"no geometry", "text/plain")
        if path == "/ws":
            return None  # let the websocket handshake proceed
        return self._resp(404, b"not found", "text/plain")

    @staticmethod
    def _resp(status, body, content_type):
        headers = Headers(
            {
                "Content-Type": content_type,
                "Content-Length": str(len(body)),
                "Cache-Control": "no-store",
            }
        )
        return Response(status, "OK" if status == 200 else "Error", headers, body)

    @staticmethod
    def _meta(entry):
        return {k: v for k, v in entry.items() if k not in ("glb", "shape")}

    # ---------- websocket ----------

    async def ws(self, connection):
        self.clients.add(connection)
        try:
            payload = json.dumps(
                {"type": "sync", "parts": [self._meta(e) for e in self.state.values()]}
            )
            await connection.send(payload)
            async for raw in connection:
                await self.command(raw)
        finally:
            self.clients.discard(connection)

    async def command(self, raw):
        """A message from the viewer: move the sliders, or write them to the file."""
        # No queue means no watcher and no rebuild loop, which is the server `nurb
        # render` stands up around a screenshot. It has no business writing to a part
        # file, and nothing would rebuild if it moved a slider.
        if self.queue is None:
            return
        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return
        name = msg.get("name")
        if not isinstance(name, str):
            return
        # A command names a part, never a path. Without the parent check, `../victim`
        # reaches a file outside parts/ and `apply` rewrites it.
        parts_dir = (self.root / "parts").resolve()
        path = (parts_dir / f"{name}.py").resolve()
        if path.parent != parts_dir or not path.is_file():
            return

        if msg.get("type") == "params":
            values = {
                k: v
                for k, v in (msg.get("values") or {}).items()
                if type(v) in (int, float)
            }
            # The viewer sends only what differs from the file, so this is the whole
            # override set for the part and replacing it is what keeps the two honest.
            self.overrides[name] = values
            if not values:
                self.overrides.pop(name)
            self.queue.put_nowait(str(path))

        elif msg.get("type") == "apply":
            from . import edit

            try:
                written, skipped = edit.apply(path, self.overrides.get(name) or {})
            except Exception as exc:
                await self.send({"type": "applied", "name": name, "error": str(exc)})
                return
            # The written values are the file's now, so they are not overrides any more.
            # Anything skipped still is, or the slider would jump back with no reason
            # given. The watcher sees the write and rebuilds; nothing is queued here.
            keep = {n: v for n, v in (self.overrides.get(name) or {}).items() if n not in written}
            self.overrides[name] = keep
            if not keep:
                self.overrides.pop(name)
            print(f"  {name}: wrote {', '.join(written) or 'nothing'}", flush=True)
            for gone, why in skipped:
                print(f"      left {gone} alone: {why}", flush=True)
            await self.send(
                {
                    "type": "applied",
                    "name": name,
                    "written": written,
                    "skipped": [{"name": n, "why": w} for n, w in skipped],
                }
            )

    async def send(self, payload):
        if not self.clients:
            return
        text = json.dumps(payload)
        for client in list(self.clients):
            try:
                await client.send(text)
            except Exception:
                self.clients.discard(client)

    async def broadcast(self, entry, kind="rebuilt"):
        await self.send({"type": kind, **self._meta(entry)})

    # ---------- watching ----------

    def watch(self):
        server = self
        parts_dir = self.root / "parts"

        class Handler(FileSystemEventHandler):
            def on_any_event(self, event):
                if event.is_directory:
                    return
                path = pathlib.Path(getattr(event, "dest_path", "") or event.src_path)
                # "." skips the atomic-save temp files editors and sed leave behind
                if path.suffix not in (".py", ".md") or path.name.startswith((".", "_")):
                    return
                # A card carries what the part has already justified, so editing one
                # changes the answer even though the geometry is untouched.
                if path.suffix == ".md":
                    path = path.with_suffix(".py")
                    if not path.is_file():
                        return
                # A shared module (system.py) can feed every part, so rebuild all.
                changed = [path] if path.parent == parts_dir else builder.find_parts(server.root)
                for target in changed:
                    server.loop.call_soon_threadsafe(server.queue.put_nowait, str(target))

        parts_dir.mkdir(parents=True, exist_ok=True)
        # Held on self: a dropped Observer can be collected and take its
        # FSEvents stream with it, and the watcher silently stops firing.
        self.observer = Observer()
        self.observer.schedule(Handler(), str(parts_dir), recursive=False)
        self.observer.schedule(Handler(), str(self.root), recursive=False)
        self.observer.daemon = True
        self.observer.start()

    async def drain(self):
        """Rebuild on file change, coalescing the burst an editor save produces."""
        while True:
            paths = {await self.queue.get()}
            await asyncio.sleep(0.05)
            while not self.queue.empty():
                paths.add(self.queue.get_nowait())  # collect, don't discard:
            for path in sorted(paths):              # two parts can change at once
                if not pathlib.Path(path).exists():
                    continue
                entry = await asyncio.to_thread(self.rebuild, path)
                status = entry["error"] or f"{entry['ms']}ms"
                print(f"  {entry['name']}: {status}", flush=True)
                await self.broadcast(entry)
                # Geometry has landed, so the rules can take their time.
                entry = await asyncio.to_thread(self.check, path)
                if entry and entry.get("findings") is not None:
                    await self.broadcast(entry, kind="checked")
                    bad = sum(1 for f in entry["findings"] if f["severity"] == "fail")
                    if entry["findings"]:
                        print(
                            f"    {len(entry['findings'])} finding(s), {bad} to fix",
                            flush=True,
                        )

    # ---------- run ----------

    async def run(self):
        self.loop = asyncio.get_running_loop()
        self.queue = asyncio.Queue()
        self.watch()
        # Held too: asyncio only keeps weak references to tasks.
        self.drain_task = asyncio.create_task(self.drain())
        async with serve(
            self.ws, "127.0.0.1", self.port, process_request=self.http, origins=self.origins
        ):
            print(f"\n  nurb  http://127.0.0.1:{self.port}\n", flush=True)
            await asyncio.Future()
