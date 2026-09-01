"""The dev server: watch parts, rebuild, push to the browser.

One process holds the OCCT import (~2s) so every rebuild after that is ~50ms.
One port serves both the viewer and the websocket.
"""

import asyncio
import collections
import hashlib
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

from . import __version__, builder, extract, registry

VIEWER = pathlib.Path(__file__).parent / "viewer.html"
VENDOR = (pathlib.Path(__file__).parent / "vendor").resolve()


def _export_name(label):
    """A catalog label made safe for a download header and build/ filename.

    Windows reserves a handful of device names (CON, NUL, COM1...) that fail to
    open as files, and the rule travels with the export, not the platform: a
    part exported on a Mac still has to unzip on a PC.
    """
    safe = "".join(
        c if c.isascii() and (c.isalnum() or c in "._-") else "_"
        for c in str(label)
    )
    safe = safe.strip("._") or "part"
    stem = safe.split(".")[0].upper()
    if stem in ("CON", "PRN", "AUX", "NUL") or (
        len(stem) == 4 and stem[:3] in ("COM", "LPT") and stem[3].isdigit()
    ):
        safe = f"part-{safe}"
    return safe


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
        stamp, cached = cache.read_text(encoding="utf-8").split()
        if time.time() - float(stamp) < 86400:
            return cached
    except (OSError, ValueError):
        pass
    try:
        with urllib.request.urlopen("https://pypi.org/pypi/nurb/json", timeout=3) as resp:
            latest = json.load(resp)["info"]["version"]
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(f"{time.time()} {latest}", encoding="utf-8")
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
        # Loaded target meshes, keyed by (file, units) and stamped with the file's
        # mtime: a scan can be a quarter-million triangles, and re-reading it on
        # every save would put a constant tax on the loop for a file that never moves.
        self.targets = {}
        # What the sliders are holding, per part, and only where it differs from the
        # file. Empty means the part is exactly what its source says.
        self.overrides = {}
        # Constructions the parts say twice, recomputed after every rebuild burst so
        # the viewer's nudge never outlives the geometry it described.
        self.shared = []
        # Per part, what the last build was made of and what it produced: the source
        # bytes, the sliders, and the shape. An edit that lands entirely outside the
        # body is a legal no-op in OCCT, so without this nothing in the loop would say
        # the file changed and the geometry did not.
        self.prints = {}
        self.clients = set()
        self.loop = None
        self.queue = None
        self.observer = None
        self.drain_task = None
        # One build at a time, shared by the rebuild loop and the export route. OCCT
        # makes no thread-safety promises, and a download landing mid-rebuild is the
        # ordinary way two builds would otherwise overlap.
        self.building = asyncio.Lock()
        # The adapter stages by output name and the slicers carry process-global
        # caches. One request at a time prevents two tabs from deleting or renaming
        # each other's files.
        self.slice_lock = asyncio.Lock()
        # The websocket HTTP shim only accepts GET. A secret header still makes the
        # state-changing slice route same-origin in practice: the viewer learns it
        # through the origin-checked socket, while another site cannot set it without
        # a CORS preflight this server doesn't accept.
        self.http_token = secrets.token_urlsafe(24)

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
        previous = self.state.get(name) or {}
        inputs_before = self._source_snapshot(path)
        entry = {
            "name": name,
            "token": secrets.token_hex(4),
            "findings": None,
            "variants": self._variants(path),
            "variant": None,
            "stress_spots": None,
            # Alongside findings, and cleared with them: the panel's supports control
            # describes the build it was drawn for, so a rebuild must not leave the old
            # answer sitting under new geometry.
            "supports": False,
            "marks": 0,
        }
        try:
            shape, params, ms = self._build(path, name)
            entry.update(builder.stats(shape))
            entry["params"] = params
            entry["variant"] = self._active_variant(params, entry["variants"])
            # Card picks describe the default geometry. A variant or free slider edit
            # can move the named faces while leaving the old coordinates on some other
            # face, which is worse than an explicit auto-aim. Keep card picks only for
            # the exact defaults they were written against.
            spots = self._stress_spots(path)
            if spots and (entry["variant"] is not None or self.overrides.get(name)):
                # Weight and material still describe the use case; only coordinates
                # become untrustworthy when geometry moves.
                spots = {k: spots[k] for k in ("kg", "material") if k in spots}
            entry["stress_spots"] = spots or None
            try:
                up = self._context(path, entry["variant"]).up
            except Exception:
                # A bad card is reported by the check pass; it must not hide geometry.
                up = (0, 0, 1)
            entry["up"] = up  # the print orientation, which is also the stress solver's layer normal
            entry["glb"] = builder.to_glb(shape, self.tolerance, up=up)
            # What this build is, as opposed to that it happened. The tessellation is
            # deterministic, so identical geometry hashes identically, and a rebuild
            # that changed nothing (a printer.toml edit, a touched file) keeps its id.
            # The viewer needs that to tell a moved slider from a rebuild that only
            # re-ran the checks, because a print estimate outlives one and not the other.
            entry["shape_id"] = hashlib.blake2b(entry["glb"], digest_size=8).hexdigest()
            entry["ms"] = round(ms, 1)
            entry["error"] = None
            entry["shape"] = shape  # kept for the check pass, never serialized
            self._attach_target(entry, path, shape)
            scene = getattr(shape, "_nurb_scene", None)
            if scene is not None:
                from .assembly import wire

                entry["joints"] = wire(scene)
                # What the stl button downloads instead of the merged scene.
                entry["uses"] = sorted(pathlib.Path(u).stem for u in scene.uses)
        except registry.Rejected as exc:
            # The part refusing this configuration via reject(). Not a crash, so no
            # traceback: the message and the parameter it names are the whole story,
            # and the viewer presents them as a limit of the design.
            entry["glb"] = None
            entry["shape"] = None
            entry["error"] = str(exc)
            entry["refused"] = exc.param or True
            # Unlike a crash, a refusal is recoverable from the parameter panel. The
            # builder carries the attempted values; the previous build covers a rare
            # refusal during module loading, before a function signature was found.
            entry["params"] = (
                exc.params if exc.params is not None else previous.get("params", [])
            )
        except Exception as exc:
            entry["glb"] = None
            entry["shape"] = None
            entry["error"] = f"{type(exc).__name__}: {exc}"
            entry["traceback"] = _user_traceback(exc, path)
        inputs_after = self._source_snapshot(path)
        previous_sources = self._build_sources(
            path, previous.get("shape"), inputs_before
        )
        current_sources = self._build_sources(path, entry.get("shape"), inputs_after)
        absent = object()
        stable = inputs_before is not None and inputs_after is not None and all(
            inputs_before.get(source, absent) == inputs_after.get(source, absent)
            for source in previous_sources | current_sources
        )
        self._mark_unchanged(
            entry,
            name,
            self._build_inputs(current_sources, inputs_after) if stable else None,
        )
        self.state[name] = entry
        return entry

    def _source_snapshot(self, path):
        """Bytes of every file a build could discover, captured at one instant."""
        sources = {
            pathlib.Path(path).resolve(),
            *builder.find_parts(self.root),
            *(
                source.resolve()
                for source in self.root.glob("*.py")
                if not source.name.startswith((".", "_"))
            ),
            (self.root / "measurements.toml").resolve(),
        }
        snapshot = {}
        for source in sources:
            try:
                snapshot[source] = source.read_bytes()
            except FileNotFoundError:
                snapshot[source] = None
            except OSError:
                return None
        return snapshot

    def _build_sources(self, path, shape, snapshot):
        """The snapshot paths that one part or assembly can consume."""
        sources = {
            pathlib.Path(path).resolve(),
            (self.root / "measurements.toml").resolve(),
        }
        for source in snapshot or {}:
            if (
                source.parent == self.root
                and source.suffix == ".py"
                and not source.name.startswith((".", "_"))
            ):
                sources.add(source)
        pending = [shape] if shape is not None else []
        visited = set()
        while pending:
            current = pending.pop()
            scene = getattr(current, "_nurb_scene", None)
            if scene is None or id(scene) in visited:
                continue
            visited.add(id(scene))
            for used in scene.uses:
                source = pathlib.Path(used).resolve()
                sources.add(source)
                nested = (self.state.get(source.stem) or {}).get("shape")
                if nested is not None:
                    pending.append(nested)
        return sources

    @staticmethod
    def _build_inputs(sources, snapshot):
        """Identity of the selected source bytes that fed one build."""
        if snapshot is None or any(source not in snapshot for source in sources):
            return None
        digest = hashlib.blake2b(digest_size=8)
        for source in sorted(sources):
            digest.update(str(source).encode("utf-8"))
            digest.update(b"\0")
            data = snapshot[source]
            if data is None:
                digest.update(b"\0")
                continue
            digest.update(b"\1")
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
        return digest.hexdigest()

    def _mark_unchanged(self, entry, name, inputs):
        """Say when an edit to the file left the geometry exactly as it was.

        A boolean cut that misses the body subtracts nothing and OCCT reports success,
        so the build, the timing and the picture all look like the edit landed. The
        flag is recomputed here on every rebuild, so it never outlives its build.
        """
        if inputs is None:
            self.prints.pop(name, None)
            return
        sliders = repr(sorted((self.overrides.get(name) or {}).items()))
        before = self.prints.get(name)
        self.prints[name] = (inputs, sliders, entry.get("shape_id"))
        if not before or entry.get("shape_id") is None:
            return
        # Only for a source edit. A slider move and an `apply` write both rebuild with
        # the same geometry on purpose, and the user can see why in both cases.
        if before[1] == sliders and before[0] != inputs and before[2] == entry["shape_id"]:
            entry["unchanged"] = True

    @staticmethod
    def _stress_spots(path):
        """The card's [stress] block, as the viewer's pre-aimed picks.

        This is how the agent that built the part hands its context to the button: it
        knows a shelf hangs on four hooks and the user should not have to. Malformed
        or absent both mean None, because the button works fine unaimed.
        """
        from . import checks

        try:
            block = checks.settings(path).get("stress")
            load = [float(v) for v in block["load"]][:3]
            hold = [[float(v) for v in p][:3] for p in block["hold"]]
            if len(load) != 3 or not hold or any(len(point) != 3 for point in hold):
                return None
            spots = {"load": load, "hold": hold, "kg": float(block.get("kg", 1.0))}
            if block.get("material"):
                spots["material"] = str(block["material"])
            return spots
        except Exception:
            return None

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

    def check(self, path, stop=None):
        """Run the rules on the last good build.

        Separate from `rebuild` and broadcast separately, because checking the shelf
        costs about as much again as building it. Geometry should land at the speed it
        always did and the findings can arrive a beat later. `stop` reaches the motion
        sweep, the one check that can hold the build lock for seconds.
        """
        from . import checks, supports
        from .assembly import Interrupted

        entry = self.state.get(pathlib.Path(path).stem)
        if not entry or entry.get("shape") is None:
            return entry
        try:
            # Sliders sitting exactly on a card variant are that variant, so its own
            # settings judge it: shelf_gridfinity_2x1 accepts 10 slivers, not the
            # base part's 18. Matched on the built values, never on a mode flag, so
            # one slider drag off the variant honestly puts the base rules back.
            ctx = self._context(path, entry["variant"])
            found = checks.run(entry["shape"], ctx, stop=stop)
            # Each finding carries the triangles of the face it fired on, so the viewer
            # can paint the face itself instead of dropping a pin near it. Rounded to
            # 0.01mm, which is display precision, not geometry.
            from . import probe

            # Resolved only when something fired: most checks in the dev loop come
            # back clean, and measuring every face to annotate nothing is pure cost.
            rows = probe.finding_faces(entry["shape"], ctx, found) if found else []
            if any(row is not None for row in rows):
                # checks.run cleans the tessellation the rebuild left on the shape,
                # so the faces have to be meshed again before their triangles exist.
                # Same tolerance as the GLB, so the glow lies exactly on the mesh.
                entry["shape"].mesh(self.tolerance)
            entry["findings"] = [
                {
                    "rule": f.rule,
                    # Both, because they answer different questions: the label is for
                    # whoever is looking at the part, the rule for whoever is fixing it.
                    "label": f.label,
                    "severity": f.severity,
                    # `said` is the plain twin where a rule has one, the message where
                    # it does not. The viewer never needs the doctrine's vocabulary.
                    "message": f.said,
                    "where": list(f.where) if f.where else None,
                    "face": [round(v, 2) for v in builder.face_triangles(row["face"])]
                    if row is not None
                    else None,
                }
                for f, row in zip(found, rows)
            ]
            # What the panel's supports control needs to draw itself: whether the card
            # already declares the part, and whether the part file marks features of its
            # own. A part with marks is not offered the card flag, because the card flag
            # is the blunter of the two and would silently widen what they chose.
            entry["supports"] = bool(ctx.supports)
            entry["marks"] = len(supports.regions(entry["shape"]))
        except Interrupted:
            # A rebuild is queued, so let its geometry land before spending more time
            # here. None tells drain to keep this path pending and retry it afterward.
            return None
        except Exception as exc:
            entry["findings"] = [
                {
                    "rule": "check",
                    "label": "the check itself failed",
                    "severity": "fail",
                    "message": f"{type(exc).__name__}: {exc}",
                    "where": None,
                }
            ]
        target = entry.get("target")
        if target and not target.get("error"):
            from . import compare

            try:
                hit = self._target_mesh(target["file"], target.get("units"))
                metrics = compare.against(entry["shape"], hit["mesh"], self.tolerance)
                # The ghost draws at the offset the numbers used, never a stale one.
                target["offset"] = metrics.pop("offset")
                target["metrics"] = metrics
            except Exception as exc:
                target["error"] = f"{type(exc).__name__}: {exc}"
        return entry

    # ---------- target mesh ----------

    def _attach_target(self, entry, path, shape):
        """The card's target mesh, riding the entry: the ghost's GLB and where it
        sits relative to this build. The deviation numbers cost a beat, so they
        arrive with the check pass, the way findings already do."""
        from . import checks, compare

        try:
            declared = compare.setting(checks.settings(path))
        except ValueError as exc:
            entry["target"] = {"error": str(exc)}
            return
        if not declared:
            return
        file, units = declared
        try:
            hit = self._target_mesh(file, units)
        except Exception as exc:
            # Broad on purpose: a target that will not load is a target problem, and
            # letting it escape here would report a part that builds fine as broken.
            entry["target"] = {"file": file, "error": str(exc)}
            return
        bb = shape.bounding_box()
        part = ((bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, (bb.min.Z + bb.max.Z) / 2)
        mesh = hit["mesh"].bounds.mean(axis=0)
        entry["target"] = {
            "file": file,
            "units": units,
            "stamp": hit["stamp"],
            "offset": [round(float(p - m), 2) for p, m in zip(part, mesh)],
        }
        entry["target_glb"] = hit["glb"]

    def _target_mesh(self, file, units):
        """The loaded target, cached by the file's mtime."""
        import trimesh

        from . import compare

        path = pathlib.Path(file)
        if not path.is_absolute():
            path = self.root / path
        if not path.is_file():
            # The stat would say the same thing in errno, which is not a message.
            raise ValueError(f"no file at {path}")
        # This stamp also versions the browser's geometry cache. The same bytes read
        # as metres and millimetres are different ghosts even though their mtime is
        # identical, and changing the card must replace the one already on screen.
        identity = f"{path.resolve()}\0{units or ''}\0{path.stat().st_mtime_ns}"
        stamp = hashlib.blake2b(identity.encode(), digest_size=8).hexdigest()
        hit = self.targets.get((file, units))
        if hit and hit["stamp"] == stamp:
            return hit
        mesh, _, _ = compare.load(self.root, file, units=units)
        hit = {
            "mesh": mesh,
            "glb": trimesh.Scene([mesh]).export(file_type="glb"),
            "stamp": stamp,
        }
        self.targets[(file, units)] = hit
        return hit

    # ---------- http ----------

    async def http(self, connection, request):
        path = request.path.split("?")[0]
        if path == "/":
            return self._resp(200, VIEWER.read_bytes(), "text/html; charset=utf-8")
        if path.startswith("/export/"):
            # ?save is the desktop shell, which has no browser download but does have
            # the project folder open.
            save = "save" in request.path.partition("?")[2].split("&")
            return await self.export(path[len("/export/") :], save=save)
        if path.startswith("/api/slice/"):
            token = request.headers.get("X-Nurb-Token")
            if not token or not secrets.compare_digest(token, self.http_token):
                return self._resp(403, b"forbidden", "text/plain")
            return await self.slice(path[len("/api/slice/") :])
        if path == "/api/sync":
            body = json.dumps(self._sync()).encode()
            return self._resp(200, body, "application/json")
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
            # The ghost first: the generic route would read x.target.glb as a part
            # named x.target and answer 404 for a file that exists.
            if path.endswith(".target.glb"):
                entry = self.state.get(path[5:].removesuffix(".target.glb"))
                if entry and entry.get("target_glb"):
                    return self._resp(200, entry["target_glb"], "model/gltf-binary")
                return self._resp(404, b"no target", "text/plain")
            entry = self.state.get(path[5:].removesuffix(".glb"))
            if entry and entry["glb"]:
                return self._resp(200, entry["glb"], "model/gltf-binary")
            return self._resp(404, b"no geometry", "text/plain")
        if path == "/ws":
            return None  # let the websocket handshake proceed
        return self._resp(404, b"not found", "text/plain")

    @staticmethod
    def _resp(status, body, content_type, attach=None, said=None):
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
        if said:
            # What the 3MF carries besides geometry, for the note under the toolbar.
            headers["X-Nurb-Print-Settings"] = said
        return Response(status, "OK" if status == 200 else "Error", headers, body)

    # What the download button serves. This is the configurator: the parameters were
    # always introspectable and the sliders already drive them, so publishing a part is
    # `nurb dev` plus this route, not a second modelling stack.
    EXPORTS = {"3mf": "model/3mf", "stl": "model/stl", "step": "application/step"}

    async def export(self, filename, save=False):
        name, _, fmt = filename.rpartition(".")
        if fmt not in self.EXPORTS or name not in self.state:
            return self._resp(404, b"not found", "text/plain")
        # A variant is a catalog entry, so its file carries the catalog name: sliders
        # sitting on hook_utility export hook_utility.stl, not hook_scissors.stl.
        label = self.state[name].get("variant") or name
        try:
            async with self.building:
                body, attach, mime, said = await asyncio.to_thread(self._export, name, fmt, label)
        except Exception as exc:
            if save:
                # The desktop viewer writes into build/. A failed rebuild must not
                # leave yesterday's part or assembly bundle looking current there.
                out = (self.root / "build").resolve()
                for stale in (
                    out / f"{_export_name(label or name)}.{fmt}",
                    out / f"{_export_name(name)}-{fmt}.zip",
                ):
                    stale.unlink(missing_ok=True)
            message = f"{type(exc).__name__}: {exc}"
            return self._resp(500, message.encode(), "text/plain")
        if save:
            # Into build/, beside what `nurb export` writes, and the path comes back so
            # a shell can show the file where it landed.
            out = (self.root / "build").resolve()
            out.mkdir(exist_ok=True)
            target = (out / attach).resolve()
            if target.parent != out:
                return self._resp(500, b"unsafe export filename", "text/plain")
            target.write_bytes(body)
            saved = {"path": str(target), **({"settings": said} if said else {})}
            body = json.dumps(saved).encode()
            return self._resp(200, body, "application/json")
        return self._resp(200, body, mime, attach=attach, said=said)

    def _export(self, name, fmt, label=None):
        """Build at the values the sliders hold and export that, as (body, filename, mime).

        `label` is what the file is called when it is not just the part's own name,
        which is how a variant's export carries the catalog name instead.

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

        from . import slicing

        # A 3MF leaves here carrying the print settings the part justifies, exactly as
        # `nurb export` writes it, when a slicer and a printer are in place. `said` is
        # the sentence about that for the note: what was embedded, or what a bare file
        # is missing, because a download that quietly lost its settings teaches nobody.
        kit = why = None
        if fmt == "3mf":
            kit, why = slicing.kit(self.root)
            if why and "printer.toml" in why:
                # The CLI's reason names the file; here the printer picker is already
                # on screen under print time, so point at that instead.
                why = "choose a printer under print time to embed tuned settings"

        def solid(path, stem):
            """(bytes, None, said) for a part, (None, scene, None) for an assembly."""
            built, _, _ = builder.build(path, overrides=self.overrides.get(stem), draft=False)
            scene = getattr(built, "_nurb_scene", None)
            if scene is not None:
                return None, scene, None
            said = None
            with tempfile.TemporaryDirectory() as scratch:
                target = pathlib.Path(scratch) / f"{stem}.{fmt}"
                if fmt == "3mf":
                    builder.write_3mf(built, target)
                    if kit:
                        variant = (self.state.get(stem) or {}).get("variant")
                        settings, notes = slicing.tuned(built, self._context(path, variant))
                        machine, process, filament, exe = kit
                        try:
                            slicing.write_project(target, target, machine, process, filament, exe, settings=settings)
                            said = ", ".join(notes)
                        except slicing.Unavailable as exc:
                            said = f"geometry only: {exc}"
                    else:
                        said = f"geometry only: {why}"
                elif fmt == "stl":
                    builder.write_stl(built, target)
                else:
                    export_step(built, str(target))
                return target.read_bytes(), None, said

        path = next((p for p in builder.find_parts(self.root) if p.stem == name), None)
        if path is None:  # deleted between the click and the build
            raise builder.BuildError(f"{name} is no longer on disk")
        body, scene, said = solid(path, name)
        if scene is None:
            return body, f"{_export_name(label or name)}.{fmt}", self.EXPORTS[fmt], said
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
                body, nested, _ = solid(placed, placed.stem)
                if nested is not None:  # an assembly placing an assembly
                    queue += sorted(pathlib.Path(u) for u in nested.uses)
                    continue
                bundle.writestr(f"{_export_name(placed.stem)}.{fmt}", body)
        return buf.getvalue(), f"{_export_name(name)}-{fmt}.zip", "application/zip", None

    # ---------- what the print costs ----------
    # The two numbers a slicer knows and nothing upstream of it does. They belong on
    # screen next to the part rather than in a terminal, because the moment they change
    # a decision is while the sliders are still under someone's hand: a wall going from
    # 2 to 3mm is a shrug in the viewer and forty minutes on the plate.
    #
    # Anything other than a number here is a UI state and not a crash, so it comes back
    # as 200 with a `kind` the viewer can act on. `choose` is the common one and is the
    # reason `profiles` rides along: the answer to a machine nobody has named yet is a
    # picker, not a sentence about a file the user has never opened.

    # What a print estimate assumes when nobody has said otherwise. Named here rather
    # than spelled again in the viewer, so the card cannot drift from what was sliced.
    LAYER, MATERIAL = "0.20", "PLA"

    async def slice(self, name):
        from . import checks, slicing

        if name not in self.state:
            return self._json(404, {"error": "no such part"})
        exe = slicing.app()
        if exe is None:
            # Not a fault and not the user's mistake: nurb reads these two numbers out of
            # a slicer rather than re-deriving them, so without one there is no answer to
            # give. Says which apps and stops, because no retry fixes this and the viewer
            # cannot install anything.
            return self._json(200, {
                "kind": "slicer",
                "error": "no slicer found. print time comes out of "
                         f"{' or '.join(slicing.SLICERS)}, both free.",
            })
        try:
            wanted, profile = checks.slicer_name(self.root)
        except ValueError as exc:
            return self._json(200, {"kind": "printer", "error": str(exc), "profiles": self._machines()})
        if not wanted:
            # Never chosen, which is a question rather than a fault: `choose` is the
            # kind that gets a plain prompt and a picker instead of a red line.
            return self._json(200, {"kind": "choose", "profiles": self._machines()})
        vendors = slicing.vendors(exe)
        if vendors is None:
            # This one is a fault: the app is here and its own profiles are not, which
            # is a broken install rather than a missing one.
            return self._json(200, {
                "kind": "profile",
                "error": f"found {slicing.label(exe)} but not its profile bundle",
            })
        # Read before the slice, not after: an answer is only about the shape it was
        # measured from, and if that shape moves while the slicer runs, the viewer has
        # to be able to see that the two no longer match.
        shape_id = (self.state.get(name) or {}).get("shape_id")
        try:
            machine = slicing.machine(vendors, wanted)
            process, filament = slicing.profiles_for(machine, self.LAYER, self.MATERIAL)
        except slicing.Unavailable as exc:
            # The machines ride along: this fault is "your slicer does not carry that
            # one", and the thing that fixes it is choosing a different machine, not
            # pressing the same button again.
            return self._json(
                200, {"kind": "profile", "error": str(exc), "profiles": self._machines()}
            )
        try:
            totals = await self._sliced(name, machine, process, filament, exe)
        except slicing.Unavailable as exc:
            # The profile resolved and the slicer rejected this model. A printer
            # picker cannot fix malformed geometry or a failed slicer process.
            return self._json(200, {"kind": "slice", "error": str(exc)})
        except Exception as exc:
            return self._json(200, {"kind": "build", "error": f"{type(exc).__name__}: {exc}"})
        seconds, grams, plates = totals
        return self._json(200, {
            "seconds": seconds,
            "spoken": slicing.spoken(seconds),
            "weight": slicing.weighed(grams),
            "grams": grams,
            "plates": plates,
            "shape_id": shape_id,
            # The machine alone on the row, because with two printers in the workshop
            # that is the one word that changes how the number reads. The layer height,
            # the filament and the full preset names are the hover: worth having next
            # to a prediction, not worth a line that pushes the row into a second one.
            "profile": profile,
            "settings": f"{profile} / {process.stem} / {filament.stem} / {slicing.PLATE}",
        })

    async def _sliced(self, name, machine, process, filament, exe):
        """(seconds, grams, plates) for a part, or for everything an assembly places.

        An assembly is a weld and not one printable solid, so it costs what its parts
        cost. Each distinct configuration is sliced once; repeated identical instances
        reuse that prediction but still contribute separately to the totals.

        The OCCT lock covers the build and the STL write only. A slicer is a separate
        process with no opinion about our kernel, and holding the lock across it would
        stall every rebuild for the seconds it takes.
        """
        from . import checks, slicing

        async with self.slice_lock:
            out = (self.root / "build").resolve()
            out.mkdir(exist_ok=True)
            seconds, grams, plates = 0, 0, 0
            sliced, names = {}, collections.Counter()
            for path, overrides in self._printable(name):
                key = (str(path), tuple(sorted(overrides.items())))
                if key not in sliced:
                    names[path.stem] += 1
                    suffix = "" if names[path.stem] == 1 else f"-{names[path.stem]}"
                    label = f"{path.stem}{suffix}"
                    async with self.building:
                        built, model = await asyncio.to_thread(
                            self._solid, path, overrides, out / f"{label}.stl"
                        )
                    # The same settings the 3MF is written with, so the button prices
                    # the file `nurb export` hands out rather than a stock slice.
                    # Resolved per path, not once per call: an assembly's instances are
                    # different parts with cards of their own, and only the part the
                    # estimate was asked for has a variant on screen.
                    ctx = (
                        self._context(path, (self.state.get(name) or {}).get("variant"))
                        if path.stem == name
                        else checks.from_card(path)
                    )
                    settings, _ = slicing.tuned(built, ctx)
                    sliced[key], _ = await asyncio.to_thread(
                        slicing.run,
                        model,
                        out / f"{label}.gcode",
                        machine,
                        process,
                        filament,
                        exe,
                        settings=settings,
                    )
                took, weighs = sliced[key]
                # One unreadable number makes that number unknown for the whole answer
                # rather than a total that silently counts fewer parts than it names.
                seconds = None if seconds is None or took is None else seconds + took
                grams = None if grams is None or weighs is None else grams + weighs
                plates += 1
            return seconds, grams, plates

    def _printable(self, name):
        """The (path, overrides) instances a print estimate covers."""
        entry = self.state.get(name) or {}
        scene = getattr(entry.get("shape"), "_nurb_scene", None)
        if scene is None:
            path = next((p for p in builder.find_parts(self.root) if p.stem == name), None)
            if path is None:
                raise builder.BuildError(f"{name} is no longer on disk")
            return [(path, dict(self.overrides.get(name) or {}))]
        out = [
            (pathlib.Path(instance.path), dict(instance.overrides))
            for instance in scene.instances
        ]
        if not out:
            raise builder.BuildError(f"{name} places no parts; nothing to print")
        return out

    @staticmethod
    def _solid(path, overrides, target):
        """The polished build at the exact values the estimate names, written as STL.

        Returns the solid alongside the file, because the settings that go with it are
        read off the geometry and rebuilding to ask would double the wait.
        """
        if not path.is_file():
            raise builder.BuildError(f"{path.stem} is no longer on disk")
        built, _, _ = builder.build(path, overrides=overrides or None, draft=False)
        builder.write_stl(built, target)
        return built, target

    # ---------- stress ----------
    # One load case, asked for by two clicks in the viewer: where the weight sits and
    # where the part is held. Solved here rather than client-side because the solver
    # needs the B-rep faces and a sparse solve. The answer returns only to the tab that
    # asked: each tab owns its own load, material, and markers.

    async def stress(self, msg, client=None):
        from . import stress as solver

        name = msg.get("name")
        entry = self.state.get(name) if isinstance(name, str) else None
        if not entry or entry.get("shape") is None:
            await self.reply(
                client,
                {"type": "stressed", "name": name, "error": "no built part to analyze"},
            )
            return
        auto = bool(msg.get("auto"))
        try:
            kg = float(msg.get("kg", 1.0))
            material = str(msg.get("material") or "PLA")
            hold = None if auto else [[float(v) for v in p][:3] for p in msg["hold"]]
            load = None if auto else [float(v) for v in msg["load"]][:3]
        except (KeyError, TypeError, ValueError):
            await self.reply(
                client,
                {"type": "stressed", "name": name, "error": "malformed stress request"},
            )
            return
        # Read before the solve, like the slice route: the answer is about this shape,
        # and the viewer has to see when a rebuild has moved on underneath it.
        shape_id = entry.get("shape_id")
        try:
            # The lock matters twice over: the solver tessellates via OCCT, which makes
            # no thread-safety promises, and a rebuild swapping the shape mid-solve
            # would hand back a map for geometry nobody can see any more.
            # `auto` is the button pressed on a part whose card never aimed it: the
            # solver guesses the spots the way the CLI does, and the answer carries
            # them back so the viewer can show the guess as movable markers.
            def solve():
                holds, at = (hold, load)
                if auto:
                    holds, at = solver.default_spots(entry["shape"])
                return solver.analyze(
                    entry["shape"], holds, at, kg, self.tolerance,
                    material=material, up=entry.get("up") or (0, 0, 1),
                )

            async with self.building:
                result = await asyncio.to_thread(solve)
        except Exception as exc:
            said = str(exc) if isinstance(exc, ValueError) else f"{type(exc).__name__}: {exc}"
            await self.reply(client, {"type": "stressed", "name": name, "error": said})
            return
        print(
            f"  {name}: stress {result['max_mpa']}MPa peak under {kg}kg, "
            f"{result['elements']} elements",
            flush=True,
        )
        await self.reply(
            client,
            {"type": "stressed", "name": name, "shape_id": shape_id, **result},
        )

    @staticmethod
    def _machines():
        """Every shipped profile, for the picker an unnamed machine gets."""
        from . import checks

        return sorted(checks.profiles())

    @classmethod
    def _json(cls, status, payload):
        return cls._resp(status, json.dumps(payload).encode(), "application/json")

    @staticmethod
    def _meta(entry):
        return {k: v for k, v in entry.items() if k not in ("glb", "shape", "target_glb")}

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

    def _shared(self):
        """Constructions repeated across enough parts to be worth a nudge.

        `nurb extract`'s full report is the agent's; the viewer only needs enough to
        say "these parts repeat themselves". The bar is higher than the report's:
        three or more parts (same "too few to tell from a coincidence" line _family
        draws) and at least four statements, calibrated on the notch examples, whose
        finished extraction still shares short residue runs on purpose. Wired as part
        names and a count only; the agent rediscovers lines itself, and the panel's
        audience never sees files.
        """
        try:
            runs = extract.duplication(builder.find_parts(self.root))
        except (OSError, SyntaxError, UnicodeError):
            # A part mid-edit may not parse, may briefly disappear during an atomic
            # save, or may not be UTF-8. No nudge beats a dead rebuild loop.
            return []
        return [
            {
                "parts": sorted({site[0].stem for site in run["sites"]}),
                "statements": run["statements"],
            }
            for run in runs
            if len({site[0] for site in run["sites"]}) >= 3 and run["statements"] >= 4
        ]

    def _wire(self, entry):
        """`_meta`, with each parameter told whether the whole family shares it."""
        out = self._meta(entry)
        if out.get("params"):
            family = self._family()
            out["params"] = [{**p, "family": p["name"] in family} for p in out["params"]]
        return out

    def _bed(self):
        """The plate the viewer draws, in mm, from the project's printer profile.

        A broken printer.toml must not take the handshake down with it; the checks
        already report it per part, so the viewer just gets the default bed.
        """
        from . import checks

        try:
            return list(checks.printer(self.root).bed[:2])
        except Exception:
            return list(checks.Context().bed[:2])

    # ---------- websocket ----------

    def _sync(self, include_token=False):
        """The project snapshot shared by the socket and its HTTP fallback."""
        payload = {
            "type": "sync",
            "project": self.root.name,
            # How a second `nurb dev` recognizes this server as its own project and
            # refuses to double up instead of walking to the next port.
            "root": str(self.root),
            "bed": self._bed(),
            "version": __version__,
            "upgradable": _upgrade_command() is not None,
            "draft": self.draft,
            # `parts` only contains completed builds. The viewer needs the
            # source list too, or it cannot tell a slow deep link from a
            # deleted or misspelled one.
            "sources": [p.stem for p in builder.find_parts(self.root)],
            "parts": [self._wire(e) for e in self.state.values()],
            "shared": self.shared,
        }
        if include_token:
            # HTTP fallback is intentionally read-only. Only the origin-checked socket
            # receives the capability for routes that launch tools or write artifacts.
            payload["request_token"] = self.http_token
        return payload

    async def ws(self, connection):
        self.clients.add(connection)
        try:
            await connection.send(json.dumps(self._sync(include_token=True)))
            async for raw in connection:
                await self.command(raw, connection)
        finally:
            self.clients.discard(connection)

    async def command(self, raw, client=None):
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

        if msg.get("type") == "printer":
            # The picker behind a print estimate that has no machine to slice for.
            # It writes the same `profile` line every other command reads, so naming
            # the machine once in the viewer also settles the bed the checks use.
            from . import checks

            try:
                target = checks.choose_profile(self.root, msg.get("profile"))
            except (ValueError, OSError) as exc:
                await self.reply(client, {"type": "printer", "error": str(exc)})
                return
            print(f"  printer: {msg['profile']}, written to {target.name}", flush=True)
            # Bed size is a check setting, so every part's verdict can move with it.
            for part in builder.find_parts(self.root):
                self.queue.put_nowait(str(part))
            await self.reply(
                client,
                {"type": "printer", "profile": msg["profile"], "bed": self._bed()},
            )
            return

        if msg.get("type") == "stress":
            await self.stress(msg, client)
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

        elif msg.get("type") == "apply_variant":
            from . import edit

            variant = msg.get("variant")
            if not isinstance(variant, str):
                return
            held = {k: v for k, v in (self.overrides.get(name) or {}).items() if v is not None}
            try:
                written = edit.apply_variant(path, variant, held)
            except Exception as exc:
                await self.send({"type": "applied", "name": name, "variant": variant, "error": str(exc)})
                return
            # The overrides stay: they are what differs from the file's defaults, which
            # is exactly what the variant now says. The watcher sees the card write and
            # rebuilds, and that build is the one that re-matches the variant.
            print(f"  {name}: updated variant {variant} ({', '.join(written) or 'no overrides'})", flush=True)
            await self.send(
                {"type": "applied", "name": name, "variant": variant, "written": written, "skipped": []}
            )

        elif msg.get("type") == "supports":
            from . import edit

            on = bool(msg.get("on"))
            try:
                edit.set_supports(path, on)
            except Exception as exc:
                await self.send({"type": "applied", "name": name, "error": str(exc)})
                return
            # The card write is what the watcher sees, and the rebuild after it is what
            # re-runs the rules, so nothing here touches the findings directly.
            print(f"  {name}: supports {'on' if on else 'off'} in the card", flush=True)
            await self.send(
                {
                    "type": "applied",
                    "name": name,
                    "written": [],
                    "skipped": [],
                    # The flag has no room for a reason the way `supported()` does, so
                    # this is the only place the user gets asked for one.
                    "said": "the whole part now prints on supports. Say why on its card, "
                    "and use supported() in the part file if it is really one feature"
                    if on
                    else "supports off; the overhang rules apply to the whole part again",
                }
            )
            
    # What a Windows upgrade exits with instead of exec'ing itself; the desktop
    # app's supervisor relaunches on exactly this code. The twin constant lives
    # in desktop/src-tauri/src/supervisor.rs.
    RESTART_EXIT_CODE = 42

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
        if sys.platform == "win32":
            # os.execv on Windows starts a second process and exits this one,
            # which orphans the server from whoever spawned it (the desktop
            # app would see its child die and kill the orphan's tree). Exit
            # with the restart code instead: the app relaunches on it, and a
            # terminal user restarts by hand.
            print("  restart nurb dev to serve the new version", flush=True)
            os._exit(self.RESTART_EXIT_CODE)
            return  # only reached when a test patches os._exit
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

    async def reply(self, client, payload):
        """Send a command acknowledgement only to the socket that issued it."""
        if client is None:  # direct command calls in tests and non-socket adapters
            await self.send(payload)
            return
        try:
            await client.send(json.dumps(payload))
        except Exception:
            self.clients.discard(client)

    async def broadcast(self, entry, kind="rebuilt"):
        # Printer settings are watched like part sources. Carrying the current bed on
        # the rebuild is what lets an edit resize an already-open viewer.
        await self.send({"type": kind, "bed": self._bed(), **self._wire(entry)})

    # ---------- watching ----------

    def watch(self):
        from . import checks

        server = self
        parts_dir = self.root / "parts"
        # Event paths arrive resolved below, so the directories they are
        # compared against must be resolved too: on Windows the same folder
        # can reach the handler under a different drive-letter case or an 8.3
        # short name, and an unresolved compare would drop every event.
        watched_parts = parts_dir.resolve()
        watched_root = self.root.resolve()
        global_config = checks.global_file().resolve()

        class Handler(FileSystemEventHandler):
            # Reads are not changes. Newer watchdog reports inotify's IN_OPEN and
            # IN_CLOSE_NOWRITE as events, and the server opens every card on every
            # check, so without this the loop feeds itself: check reads the card, the
            # read queues a rebuild, the rebuild checks, forever. It presents as a part
            # rebuilding a few hundred times a minute with nothing on disk changing.
            READS = ("opened", "closed_no_write")

            def on_any_event(self, event):
                if event.is_directory or getattr(event, "event_type", None) in self.READS:
                    return
                path = pathlib.Path(
                    getattr(event, "dest_path", "") or event.src_path
                ).resolve()
                # "." skips the atomic-save temp files editors and sed leave behind
                if path.name.startswith((".", "_")):
                    return
                if path != global_config and path.parent not in (watched_parts, watched_root):
                    return
                # Printer settings change every part's checks, whether they came from
                # the project or the global config. measurements.toml can feed any
                # part's geometry, so all three rebuild the whole project below.
                if (
                    path != global_config
                    and path.suffix not in (".py", ".md")
                    and path.name not in ("printer.toml", "measurements.toml")
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
                if path.suffix == ".py" and path.parent == watched_parts:
                    changed = [parts_dir / path.name]
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
        global_dir = global_config.parent
        if global_dir.is_dir() and global_dir not in {
            parts_dir.resolve(),
            self.root.resolve(),
        }:
            self.observer.schedule(Handler(), str(global_dir), recursive=False)
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

    async def _finish_check(self, path):
        """Check one settled build; False means a newer rebuild interrupted it."""
        async with self.building:
            entry = await asyncio.to_thread(
                self.check, path, lambda: not self.queue.empty()
            )
        if entry is None:
            return False
        if entry.get("findings") is not None:
            await self.broadcast(entry, kind="checked")
            bad = sum(1 for f in entry["findings"] if f["severity"] == "fail")
            if entry["findings"]:
                print(
                    f"    {len(entry['findings'])} finding(s), {bad} to fix",
                    flush=True,
                )
        return True

    async def drain(self):
        """Rebuild on file change, coalescing the burst an editor save produces."""
        pending_checks = set()
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
                    existed = self.state.pop(name, None) is not None
                    self.overrides.pop(name, None)
                    self.prints.pop(name, None)
                    pending_checks.discard(path)
                    if existed:
                        print(f"  {name}: gone", flush=True)
                    # Also notify for a source deleted before its first build. A
                    # deep link may be waiting for that name even though state has
                    # never held a completed entry for it.
                    await self.send({"type": "gone", "name": name})
                    continue
                async with self.building:
                    entry = await asyncio.to_thread(self.rebuild, path)
                status = entry["error"] or f"{entry['ms']}ms"
                if entry.get("unchanged"):
                    status += ", geometry unchanged"
                print(f"  {entry['name']}: {status}", flush=True)
                await self.broadcast(entry)
                pending_checks.add(path)
            # Every geometry update in the burst lands before its checks start. If a
            # new rebuild arrives during a motion sweep, leave that check pending,
            # service the rebuild, then retry against the latest settled state.
            while pending_checks and self.queue.empty():
                path = min(pending_checks)
                if not pathlib.Path(path).exists():
                    pending_checks.discard(path)
                    continue
                if await self._finish_check(path):
                    pending_checks.discard(path)
                else:
                    break
            # The duplication scan reads every part file, so once per settled burst,
            # not per path; a burst still queuing gets it on its last round instead.
            if self.queue.empty():
                shared = await asyncio.to_thread(self._shared)
                if shared != self.shared:
                    self.shared = shared
                    await self.send({"type": "shared", "runs": shared})

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
        # open_timeout=None: process_request serves the HTTP routes inside the
        # handshake window, and the default 10s guillotines any export whose polished
        # build runs longer, closing the connection with no response at all. The
        # download button then waits on a reply that is never coming. Local sockets
        # from our own viewer do not need a handshake deadline.
        async with serve(
            self.ws, "127.0.0.1", self.port, process_request=self.http,
            origins=self.origins, open_timeout=None,
        ):
            print(f"\n  nurb  http://127.0.0.1:{self.port}\n", flush=True)
            if self.open_browser:
                # After the bind, or the browser lands on a connection refused.
                _open_viewer(f"http://127.0.0.1:{self.port}")
            threading.Thread(target=_update_nudge, daemon=True).start()
            await asyncio.Future()
