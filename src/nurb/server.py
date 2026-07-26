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
        self.clients = set()
        self.loop = None
        self.queue = None
        self.observer = None
        self.drain_task = None

    # ---------- building ----------

    def rebuild(self, path):
        name = pathlib.Path(path).stem
        entry = {"name": name, "token": secrets.token_hex(4)}
        try:
            shape, params, ms = builder.build(path, draft=self.draft)
            entry["glb"] = builder.to_glb(shape, self.tolerance)
            entry.update(builder.stats(shape))
            entry["params"] = params
            entry["ms"] = round(ms, 1)
            entry["error"] = None
        except Exception as exc:
            entry["glb"] = None
            entry["error"] = f"{type(exc).__name__}: {exc}"
            entry["traceback"] = _user_traceback(exc, path)
        self.state[name] = entry
        return entry

    def rebuild_all(self):
        for path in builder.find_parts(self.root):
            entry = self.rebuild(path)
            status = entry["error"] or f"{entry['ms']}ms"
            print(f"  {entry['name']}: {status}", flush=True)

    # ---------- http ----------

    def http(self, connection, request):
        path = request.path.split("?")[0]
        if path == "/":
            return self._resp(200, VIEWER.read_bytes(), "text/html; charset=utf-8")
        if path == "/api/parts":
            body = json.dumps([self._meta(e) for e in self.state.values()]).encode()
            return self._resp(200, body, "application/json")
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
        return {k: v for k, v in entry.items() if k != "glb"}

    # ---------- websocket ----------

    async def ws(self, connection):
        self.clients.add(connection)
        try:
            payload = json.dumps(
                {"type": "sync", "parts": [self._meta(e) for e in self.state.values()]}
            )
            await connection.send(payload)
            async for _ in connection:
                pass
        finally:
            self.clients.discard(connection)

    async def broadcast(self, entry):
        if not self.clients:
            return
        payload = json.dumps({"type": "rebuilt", **self._meta(entry)})
        for client in list(self.clients):
            try:
                await client.send(payload)
            except Exception:
                self.clients.discard(client)

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
                if path.suffix != ".py" or path.name.startswith((".", "_")):
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

    # ---------- run ----------

    async def run(self):
        self.loop = asyncio.get_running_loop()
        self.queue = asyncio.Queue()
        self.watch()
        # Held too: asyncio only keeps weak references to tasks.
        self.drain_task = asyncio.create_task(self.drain())
        async with serve(self.ws, "127.0.0.1", self.port, process_request=self.http):
            print(f"\n  nurb  http://127.0.0.1:{self.port}\n", flush=True)
            await asyncio.Future()
