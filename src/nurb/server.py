"""The dev server: watch parts, rebuild, push to the browser.

One process holds the OCCT import (~2s) so every rebuild after that is ~50ms.
One port serves both the viewer and the websocket.
"""

import asyncio
import collections
import json
import pathlib
import secrets
import threading
import traceback
import webbrowser

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from websockets.asyncio.server import serve
from websockets.http11 import Response
from websockets.datastructures import Headers

from . import __version__, builder

VIEWER = pathlib.Path(__file__).parent / "viewer.html"
VENDOR = (pathlib.Path(__file__).parent / "vendor").resolve()


def _newer(current, latest):
    """Is `latest` a later X.Y.Z than `current`? Anything unparseable is not newer."""
    try:
        return tuple(map(int, latest.split("."))) > tuple(map(int, current.split(".")))
    except ValueError:
        return False


def _latest_on_pypi():
    """The newest nurb on PyPI, asked at most once a day, or None.

    Offline, slow, or an odd response all mean None: the check is a nudge, never a
    requirement.
    """
    import time
    import urllib.request

    cache = pathlib.Path.home() / ".cache" / "nurb" / "latest"
    try:
        stamp, cached = cache.read_text().split()
        if time.time() - float(stamp) < 86400:
            return cached
    except (OSError, ValueError):
        pass
    try:
        with urllib.request.urlopen("https://pypi.org/pypi/nurb/json", timeout=3) as resp:
            latest = json.load(resp)["info"]["version"]
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(f"{time.time()} {latest}")
        return latest
    except Exception:
        return None


def _upgrade_command():
    """The argv that upgrades this install, or None when we cannot know it.

    `uv tool install nurb` is the documented path and the only one recognized: its
    venvs live under .../uv/tools/nurb, so running from one is the tell. Anything
    else, pip, pipx, a dev checkout, gets the command shown and nothing run, because
    guessing wrong on a dev checkout would replace it with PyPI.
    """
    import shutil
    import sys

    prefix = pathlib.Path(sys.prefix)
    if prefix.name == "nurb" and prefix.parent.name == "tools" and shutil.which("uv"):
        return ["uv", "tool", "upgrade", "nurb"]
    return None


def _open_viewer(url):
    """Open the viewer in the user's default browser.

    On macOS the stdlib webbrowser module drives an AppleScript `open location`,
    which lands in Safari regardless of the LaunchServices default. /usr/bin/open
    consults LaunchServices, so it opens the browser the user actually set. A failed
    open is not fatal either way; the URL is already on stdout.
    """
    import subprocess
    import sys

    if sys.platform == "darwin":
        subprocess.run(["/usr/bin/open", url], check=False)
    else:
        webbrowser.open(url)


def _installed_skill_version(text):
    """The frontmatter version of an installed skill copy, or None before versioning began."""
    if not text.startswith("---\n"):
        return None
    lines = text.split("---\n")[1].splitlines()
    try:
        start = lines.index("metadata:") + 1
    except ValueError:
        return None
    for line in lines[start:]:
        if not line.startswith("  "):
            break
        if line.startswith("  version: "):
            return line.removeprefix("  version: ").strip().strip("\"'")
    return None


def _skill_nudge():
    """One line on `nurb dev` stdout when the installed skill file is older than this nurb.

    The skill is the agent's own instructions and no harness refreshes an installed
    copy by itself, so after an upgrade the agent keeps modelling from the old
    playbook. Compared by frontmatter version rather than bytes: between releases a
    skills.sh install from GitHub is ahead of the package, and a byte diff would call
    the newer copy stale and invite a downgrade.
    """
    from . import cli

    for target in cli.skill_targets():
        try:
            text = target.read_text(encoding="utf-8")
        except OSError:
            continue
        installed = _installed_skill_version(text)
        if installed is None or _newer(installed, __version__):
            print(
                f"  nurb skill {installed or 'unversioned'} ({__version__} available: nurb skill --sync)",
                flush=True,
            )
            return


def _update_nudge():
    """One line on `nurb dev` stdout when PyPI has a newer release, and one when the installed skill file lags this package.

    A thread because the primary user is an agent reading stdout, and startup must
    never wait on the network to say so. The skill check goes first: it is local, so
    its line lands even when PyPI does not answer.
    """
    _skill_nudge()
    latest = _latest_on_pypi()
    if latest and _newer(__version__, latest):
        print(f"  nurb {__version__} ({latest} available: nurb update)", flush=True)


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
    def __init__(self, root, port=7373, tolerance=0.1, draft=False, open_browser=False):
        self.root = pathlib.Path(root).resolve()
        self.port = port
        self.tolerance = tolerance
        self.draft = draft
        self.open_browser = open_browser
        self.state = {}
        # What the sliders are holding, per part, and only where it differs from the
        # file. Empty means the part is exactly what its source says.
        self.overrides = {}
        self.clients = set()
        self.loop = None
        self.queue = None
        self.observer = None
        self.drain_task = None
        # One build at a time, shared by the rebuild loop and the export route. OCCT
        # makes no thread-safety promises, and a download landing mid-rebuild is the
        # ordinary way two builds would otherwise overlap.
        self.building = asyncio.Lock()

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
        entry = {
            "name": name,
            "token": secrets.token_hex(4),
            "findings": None,
            "variants": self._variants(path),
            "variant": None,
        }
        try:
            shape, params, ms = self._build(path, name)
            entry.update(builder.stats(shape))
            entry["params"] = params
            entry["variant"] = self._active_variant(params, entry["variants"])
            try:
                up = self._context(path, entry["variant"]).up
            except Exception:
                # A bad card is reported by the check pass; it must not hide geometry.
                up = (0, 0, 1)
            entry["glb"] = builder.to_glb(shape, self.tolerance, up=up)
            entry["ms"] = round(ms, 1)
            entry["error"] = None
            entry["shape"] = shape  # kept for the check pass, never serialized
            scene = getattr(shape, "_nurb_scene", None)
            if scene is not None:
                from .assembly import wire

                entry["joints"] = wire(scene)
                # What the stl button downloads instead of the merged scene.
                entry["uses"] = sorted(pathlib.Path(u).stem for u in scene.uses)
        except Exception as exc:
            entry["glb"] = None
            entry["shape"] = None
            entry["error"] = f"{type(exc).__name__}: {exc}"
            entry["traceback"] = _user_traceback(exc, path)
        self.state[name] = entry
        return entry

    @staticmethod
    def _variants(path):
        """The card's variants, as the viewer shows them: a name, its overrides, and
        the card's note saying why it exists.

        A variant is one part flexed, which is exactly what the sliders do, so the
        viewer treats picking one as loading its params. The note rides along because
        the params are the how and never the why: `diagonal = true` explains nothing
        to someone who has not read the doctrine, and the card sentence does. A card
        that will not parse means no variants, not a broken part: the build itself
        never read the card.
        """
        from . import checks

        try:
            notes = checks.settings(path).get("variants", {})
            return [
                {"name": n, "params": p, "note": notes.get(n, {}).get("note")}
                for n, p, _ in checks.configurations(path)[1:]
            ]
        except Exception:
            return []

    @staticmethod
    def _active_variant(params, variants):
        """The card variant whose complete built values are on screen, if any."""
        rows = {p["name"]: p for p in params or []}
        for variant in variants:
            overrides = variant["params"]
            if set(overrides) <= set(rows) and all(
                p["value"] == overrides.get(name, p["default"])
                for name, p in rows.items()
            ):
                return variant["name"]
        return None

    @staticmethod
    def _context(path, variant):
        """The check context belonging to the values currently on screen."""
        from . import checks

        configs = checks.configurations(path)
        ctx = configs[0][2]
        for name, _, variant_ctx in configs[1:]:
            if name == variant:
                return variant_ctx
        return ctx

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
            # Sliders sitting exactly on a card variant are that variant, so its own
            # settings judge it: shelf_gridfinity_2x1 accepts 10 slivers, not the
            # base part's 18. Matched on the built values, never on a mode flag, so
            # one slider drag off the variant honestly puts the base rules back.
            ctx = self._context(path, entry["variant"])
            found = checks.run(entry["shape"], ctx)
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

    # ---------- http ----------

    async def http(self, connection, request):
        path = request.path.split("?")[0]
        if path == "/":
            return self._resp(200, VIEWER.read_bytes(), "text/html; charset=utf-8")
        if path.startswith("/export/"):
            return await self.export(path[len("/export/") :])
        if path == "/api/parts":
            body = json.dumps([self._wire(e) for e in self.state.values()]).encode()
            return self._resp(200, body, "application/json")
        if path.startswith("/vendor/"):
            # three.js and the UI font, shipped in the package. A CAD tool that needs
            # a CDN is broken on a plane, and `nurb render` drives this same page.
            types = {".js": "text/javascript; charset=utf-8", ".ttf": "font/ttf"}
            target = (VENDOR / path[len("/vendor/") :]).resolve()
            if target.suffix in types and target.is_relative_to(VENDOR) and target.is_file():
                return self._resp(200, target.read_bytes(), types[target.suffix])
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
    def _resp(status, body, content_type, attach=None):
        headers = Headers(
            {
                "Content-Type": content_type,
                "Content-Length": str(len(body)),
                "Cache-Control": "no-store",
                # websockets tears the connection down after a process_request
                # response. Without this header the response reads as keep-alive,
                # Chrome pools the socket, and its next request on it, including
                # the /ws upgrade, dies silently (#17).
                "Connection": "close",
            }
        )
        if attach:
            headers["Content-Disposition"] = f'attachment; filename="{attach}"'
        return Response(status, "OK" if status == 200 else "Error", headers, body)

    # What the download button serves. This is the configurator: the parameters were
    # always introspectable and the sliders already drive them, so publishing a part is
    # `nurb dev` plus this route, not a second modelling stack.
    EXPORTS = {"stl": "model/stl", "step": "application/step"}

    async def export(self, filename):
        name, _, fmt = filename.rpartition(".")
        if fmt not in self.EXPORTS or name not in self.state:
            return self._resp(404, b"not found", "text/plain")
        try:
            async with self.building:
                body, attach, mime = await asyncio.to_thread(self._export, name, fmt)
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            return self._resp(500, message.encode(), "text/plain")
        return self._resp(200, body, mime, attach=attach)

    def _export(self, name, fmt):
        """Build at the values the sliders hold and export that, as (body, filename, mime).

        Always the polished build, whatever the viewer is showing: draft is a preview
        economy, and a file somebody downloads is on its way to a slicer. An assembly
        downloads one zip of the parts it places, each exported exactly as its own
        entry would be: the merged scene is a weld, its obstacles were never going to
        be printed, and one file per part as separate downloads dies silently on the
        browser's multiple-download permission.
        """
        import io
        import tempfile
        import zipfile

        from build123d import export_step

        def solid(path, stem):
            """(bytes, None) for a part, (None, scene) for an assembly."""
            built, _, _ = builder.build(path, overrides=self.overrides.get(stem), draft=False)
            scene = getattr(built, "_nurb_scene", None)
            if scene is not None:
                return None, scene
            with tempfile.TemporaryDirectory() as scratch:
                target = pathlib.Path(scratch) / f"{stem}.{fmt}"
                if fmt == "stl":
                    builder.write_stl(built, target)
                else:
                    export_step(built, str(target))
                return target.read_bytes(), None

        path = next((p for p in builder.find_parts(self.root) if p.stem == name), None)
        if path is None:  # deleted between the click and the build
            raise builder.BuildError(f"{name} is no longer on disk")
        body, scene = solid(path, name)
        if scene is None:
            return body, f"{name}.{fmt}", self.EXPORTS[fmt]
        queue = sorted(pathlib.Path(u) for u in scene.uses)
        if not queue:
            raise builder.BuildError(f"{name} places no parts; nothing to print")
        buf = io.BytesIO()
        seen = set()
        with zipfile.ZipFile(buf, "w") as bundle:
            while queue:
                placed = queue.pop(0)
                if placed in seen:
                    continue
                seen.add(placed)
                body, nested = solid(placed, placed.stem)
                if nested is not None:  # an assembly placing an assembly
                    queue += sorted(pathlib.Path(u) for u in nested.uses)
                    continue
                bundle.writestr(f"{placed.stem}.{fmt}", body)
        return buf.getvalue(), f"{name}-{fmt}.zip", "application/zip"

    @staticmethod
    def _meta(entry):
        return {k: v for k, v in entry.items() if k not in ("glb", "shape")}

    def _family(self):
        """Parameters most of this project's parts declare identically.

        A family constant rather than one part's dimension. Notch writes
        `chamfer_size=1.0` in twelve of thirteen parts, and changing it in one of them
        does not adjust that part, it makes it disagree with the other twelve. That is a
        different kind of edit from moving a shelf's depth, and the panel says so.

        Inferred, not declared, for the same reason `nurb extract` infers: what a family
        shares is discovered once the parts exist. Both the name and the default have to
        match, so `bracket_count`, which every part declares and each at its own value,
        is correctly not one of these.

        Read off what has already been built, so it costs nothing per rebuild and needs
        no second place to keep in sync.
        """
        built = [e for e in self.state.values() if e.get("params")]
        if len(built) < 3:  # too few to tell a family constant from a coincidence
            return set()
        seen = collections.Counter(
            (p["name"], repr(p["default"])) for e in built for p in e["params"]
        )
        return {name for (name, _), n in seen.items() if n > len(built) / 2}

    def _wire(self, entry):
        """`_meta`, with each parameter told whether the whole family shares it."""
        out = self._meta(entry)
        if out.get("params"):
            family = self._family()
            out["params"] = [{**p, "family": p["name"] in family} for p in out["params"]]
        return out

    # ---------- websocket ----------

    async def ws(self, connection):
        self.clients.add(connection)
        try:
            payload = json.dumps(
                {
                    "type": "sync",
                    "project": self.root.name,
                    "version": __version__,
                    "upgradable": _upgrade_command() is not None,
                    "draft": self.draft,
                    "parts": [self._wire(e) for e in self.state.values()],
                }
            )
            await connection.send(payload)
            async for raw in connection:
                await self.command(raw)
        finally:
            self.clients.discard(connection)

    async def command(self, raw):
        """A message from the viewer: move the sliders, write them to the file, or
        flip draft mode."""
        # No queue means no watcher and no rebuild loop, which is the server `nurb
        # render` stands up around a screenshot. It has no business writing to a part
        # file, and nothing would rebuild if it moved a slider.
        if self.queue is None:
            return
        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return

        if msg.get("type") == "draft":
            # The viewer's polish toggle. Draft is a preview economy, so the viewer
            # shows the polished part unless someone turns it off, and the whole
            # project rebuilds on a flip: a mode is not per-part.
            self.draft = bool(msg.get("on"))
            for target in builder.find_parts(self.root):
                self.queue.put_nowait(str(target))
            return

        if msg.get("type") == "upgrade":
            await self.upgrade()
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
                if type(v) in (bool, int, float, str) or v is None
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

    async def upgrade(self):
        """Run the install's own upgrade, then exec ourselves so the new code serves.

        The dropped socket is the restart signal: the viewer's reconnect loop lands on
        the new process and the fresh sync carries the new version.
        """
        import os
        import subprocess
        import sys

        cmd = _upgrade_command()
        if cmd is None:
            await self.send(
                {"type": "upgraded", "error": "not a uv tool install; upgrade it the way it was installed"}
            )
            return
        print(f"  upgrading: {' '.join(cmd)}", flush=True)
        done = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=120
        )
        if done.returncode != 0:
            reason = (done.stderr or done.stdout).strip() or f"exit {done.returncode}"
            print(f"  upgrade failed: {reason}", flush=True)
            await self.send({"type": "upgraded", "error": reason})
            return
        print("  upgraded, restarting", flush=True)
        os.execv(sys.argv[0], sys.argv)

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
        await self.send({"type": kind, **self._wire(entry)})

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
                if path.name.startswith((".", "_")):
                    return
                # printer.toml changes every part's checks and measurements.toml can
                # feed any part's geometry, so either rebuilds the project the way
                # system.py does: they land in the else branch below.
                if path.suffix not in (".py", ".md") and path.name not in (
                    "printer.toml",
                    "measurements.toml",
                ):
                    return
                # A card carries what the part has already justified, so editing one
                # changes the answer even though the geometry is untouched.
                if path.suffix == ".md":
                    path = path.with_suffix(".py")
                    if not path.is_file():
                        return
                # A shared module (system.py) can feed every part, so rebuild all.
                # The suffix guard keeps a stray toml saved into parts/ from queueing
                # itself as a part.
                if path.suffix == ".py" and path.parent == parts_dir:
                    changed = [path]
                else:
                    changed = builder.find_parts(server.root)
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

    def _dependents(self, paths):
        """Assemblies whose use() placed any of these files.

        Editing a part while watching the assembly it sits in is the whole editing
        loop for an assembly, and without this the scene on screen would be the one
        part stale. Read off the scenes already built, so it costs nothing and there
        is no dependency file to keep in sync. Fixpoint, not one pass: an assembly
        can place an assembly.
        """
        found = set(paths)
        grew = True
        while grew:
            grew = False
            for entry in self.state.values():
                scene = getattr(entry.get("shape"), "_nurb_scene", None)
                if scene is None:
                    continue
                mine = str(self.root / "parts" / f"{entry['name']}.py")
                if mine not in found and any(u in found for u in scene.uses):
                    found.add(mine)
                    grew = True
        return found - set(paths)

    async def drain(self):
        """Rebuild on file change, coalescing the burst an editor save produces."""
        while True:
            paths = {await self.queue.get()}
            await asyncio.sleep(0.05)
            while not self.queue.empty():
                paths.add(self.queue.get_nowait())  # collect, don't discard:
            paths |= self._dependents(paths)
            for path in sorted(paths):              # two parts can change at once
                if not pathlib.Path(path).exists():
                    # Deleted, or renamed away. Dropping it is the whole handling: a
                    # part that is gone from disk but still in the list is one you can
                    # select, drag sliders on, and export, none of which exist.
                    name = pathlib.Path(path).stem
                    if self.state.pop(name, None) is not None:
                        self.overrides.pop(name, None)
                        print(f"  {name}: gone", flush=True)
                        await self.send({"type": "gone", "name": name})
                    continue
                async with self.building:
                    entry = await asyncio.to_thread(self.rebuild, path)
                status = entry["error"] or f"{entry['ms']}ms"
                print(f"  {entry['name']}: {status}", flush=True)
                await self.broadcast(entry)
                # Geometry has landed, so the rules can take their time.
                async with self.building:
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
        # The whole project goes through the same queue a save does, so the bind never
        # waits on a build. An agent hands out the URL the moment it prints, and a
        # project's worth of builds behind it was seconds of connection refused.
        for path in builder.find_parts(self.root):
            self.queue.put_nowait(str(path))
        async with serve(
            self.ws, "127.0.0.1", self.port, process_request=self.http, origins=self.origins
        ):
            print(f"\n  nurb  http://127.0.0.1:{self.port}\n", flush=True)
            if self.open_browser:
                # After the bind, or the browser lands on a connection refused.
                _open_viewer(f"http://127.0.0.1:{self.port}")
            threading.Thread(target=_update_nudge, daemon=True).start()
            await asyncio.Future()
