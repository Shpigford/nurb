"""Headless PNG of a part, so an agent can see its own work.

It drives the same viewer a human uses, on a private port, rather than rendering
offscreen with a second graphics stack. Two reasons: the image is then the thing the
human would see, and nothing new has to know how to light a scene or where the camera
goes. It costs a browser, which is why Playwright is an optional dependency and this is
the only module that imports it.

No dev server has to be running. This starts one, serves the viewer for as long as the
screenshot takes, and stops it. The file watcher is deliberately not started: nothing is
going to change during a render.
"""

import asyncio
import pathlib
import re
import socket
import threading

from .builder import BuildError

MISSING = """nurb render needs Playwright, which is not installed. It is optional
because it pulls down a browser and nothing else in nurb needs one:

  uv add playwright
  uv run playwright install chromium"""

VIEWS = ("iso", "front", "back", "left", "right", "top")

# The viewer's grammar for a section cut: an axis, optionally with a position that is a
# fraction of the span or an absolute millimetre coordinate. Checked here so a typo is
# an error naming the grammar instead of a PNG of an uncut part.
CUT = re.compile(r"^[xyz](:-?\d*\.?\d+(mm)?)?$")


def _view(view):
    """A named view, or an `x,y,z` direction a caller computed from the geometry."""
    if view in VIEWS:
        return view
    try:
        parts = [float(p) for p in str(view).split(",")]
    except ValueError:
        parts = []
    if len(parts) == 3 and any(parts):
        return ",".join(f"{p:.3f}" for p in parts)
    raise BuildError(f"no view called {view!r}. have: {', '.join(VIEWS)}")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _host(server):
    """Serve the viewer on a background loop until the returned event is set."""
    from websockets.asyncio.server import serve

    up, done = threading.Event(), threading.Event()

    async def main():
        async with serve(
            server.ws,
            "127.0.0.1",
            server.port,
            process_request=server.http,
            origins=server.origins,
        ):
            up.set()
            await asyncio.to_thread(done.wait)

    thread = threading.Thread(target=lambda: asyncio.run(main()), daemon=True)
    thread.start()
    if not up.wait(timeout=10):
        raise BuildError(f"the viewer did not come up on port {server.port}")
    return done


def _launch(pw):
    """Launch Chromium, keeping optional-browser failures in nurb's error vocabulary."""
    try:
        return pw.chromium.launch()
    except Exception as exc:
        raise BuildError(f"Playwright could not launch Chromium: {exc}") from exc


def snapshots(root, shots, timeout=30000):
    """Write one PNG per shot, sharing one server and one browser for the whole list,
    because launching chromium costs more than every part in `examples/` put together.
    Returns the written paths, in shot order.

    A shot is a dict: `part` (the file) and `file` (the target PNG), plus optional
    `view` (a name or an `x,y,z` direction), `size`, `chrome`, `overrides` (parameter
    values, so a variant can sit for its own picture), `cut` (a section, in the
    viewer's grammar), `check` (run the rules so findings mark the picture), and
    `marks=False` (check, but picture the part clean).
    """
    for shot in shots:  # before the import, so a typo says so instead of "install this"
        _view(shot.get("view", "iso"))
        cut = shot.get("cut")
        if cut and not CUT.match(cut):
            raise BuildError(
                f"no cut like {cut!r}. want axis[:position]: z, z:0.7, or z:4mm"
            )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BuildError(MISSING) from exc

    from .server import Server

    server = Server(root, port=free_port(), draft=False)
    built = {}  # name -> [overrides it was built with, whether it has been checked]
    done = _host(server)
    written = []
    try:
        with sync_playwright() as pw:
            # Default launch, which is the headless shell. Checked: it reports WebGL 2.0
            # and renders the scene, so pinning channel="chromium" would only narrow
            # which install of Playwright works.
            browser = _launch(pw)
            page, last_size = None, None
            for shot in shots:
                path = pathlib.Path(shot["part"])
                name = path.stem
                overrides = shot.get("overrides") or None
                # Rebuilt only when this shot wants different parameter values than the
                # server is holding, so a run of shots of one part builds it once.
                if name not in built or built[name][0] != overrides:
                    if overrides:
                        server.overrides[name] = dict(overrides)
                    else:
                        server.overrides.pop(name, None)
                    entry = server.rebuild(path)
                    if entry["error"]:
                        raise BuildError(f"{entry['name']}: {entry['error']}")
                    built[name] = [overrides, False]
                wants_check = shot.get("check") or shot.get("chrome")
                if wants_check and not built[name][1]:
                    # Only when asked for: checking costs about as much as building.
                    server.check(path)
                    built[name][1] = True

                width, height = shot.get("size") or (1200, 900)
                if page is None:
                    # No device_scale_factor: the asked-for width should be the width
                    # of the file. Anyone who wants it sharper can ask for a bigger one.
                    page = browser.new_page(viewport={"width": width, "height": height})
                elif (width, height) != last_size:
                    page.set_viewport_size({"width": width, "height": height})
                last_size = (width, height)

                url = (
                    f"http://127.0.0.1:{server.port}/"
                    f"?part={name}&view={_view(shot.get('view', 'iso'))}"
                )
                if not shot.get("chrome"):
                    url += "&bare=1"
                if shot.get("cut"):
                    url += f"&cut={shot['cut']}"
                if shot.get("marks") is False:
                    url += "&marks=0"
                page.goto(url)
                try:
                    page.wait_for_function(
                        "window.__nurb && window.__nurb.ready", timeout=timeout
                    )
                except Exception as exc:
                    # Not the geometry, which is where a bare Playwright timeout would
                    # send the reader. `ready` is set from a requestAnimationFrame pair,
                    # so anything that stops the page painting stops it too, and nothing
                    # is ever painted in a hidden tab.
                    raise BuildError(
                        f"{name}: the viewer did not finish drawing in "
                        f"{timeout / 1000:.0f}s. `ready` comes from an animation frame, "
                        f"so a page that cannot paint never gets there."
                    ) from exc
                png = pathlib.Path(shot["file"])
                png.parent.mkdir(parents=True, exist_ok=True)
                # Bare hides the sidebar, so the canvas is the viewport and shooting it
                # gives exactly the size asked for. With the chrome kept, the sidebar is
                # part of what was asked for, so shoot the page.
                target = page if shot.get("chrome") else page.locator("canvas")
                target.screenshot(path=str(png))
                written.append(png)
            browser.close()
    finally:
        done.set()
    return written


def render(root, paths, out_dir, view=None, size=(1200, 900), chrome=False, timeout=30000, cut=None):
    """Write a PNG per part. Returns [(part_path, png_path)].

    A section render gets its own filename, so cutting a part open never overwrites
    the picture of it whole. A cut keeps the low side of its axis, so the exposed face
    looks up the axis; iso already faces +x and +z but looks at -y, and a y cut shot
    from there would show the intact back of the part. Unless a view was asked for, a
    section stands where the cut can be seen.
    """
    if view is None:
        view = "0.7,0.75,0.6" if cut and cut[0] == "y" else "iso"
    out_dir = pathlib.Path(out_dir)
    shots = [
        {
            "part": path,
            "file": out_dir / f"{pathlib.Path(path).stem}{'.section' if cut else ''}.png",
            "view": view,
            "size": size,
            "chrome": chrome,
            "cut": cut,
        }
        for path in paths
    ]
    return list(zip(paths, snapshots(root, shots, timeout=timeout)))
