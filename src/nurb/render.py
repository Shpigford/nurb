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
import socket
import threading

from .builder import BuildError

MISSING = """nurb render needs Playwright, which is not installed. It is optional
because it pulls down a browser and nothing else in nurb needs one:

  uv add playwright
  uv run playwright install chromium"""

VIEWS = ("iso", "front", "back", "left", "right", "top")


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


def render(root, paths, out_dir, view="iso", size=(1200, 900), chrome=False, timeout=30000):
    """Write a PNG per part. Returns [(part_path, png_path)].

    One server and one browser for the whole list, because launching chromium costs more
    than every part in `examples/` put together.
    """
    if view not in VIEWS:  # before the import, so a typo says so instead of "install this"
        raise BuildError(f"no view called {view!r}. have: {', '.join(VIEWS)}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BuildError(MISSING) from exc

    from .server import Server

    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    server = Server(root, port=free_port(), draft=False)
    for path in paths:
        entry = server.rebuild(path)
        if entry["error"]:
            raise BuildError(f"{entry['name']}: {entry['error']}")
        if chrome:
            server.check(path)  # only worth its cost when the panel is actually shown

    done = _host(server)
    written = []
    try:
        with sync_playwright() as pw:
            # Default launch, which is the headless shell. Checked: it reports WebGL 2.0
            # and renders the scene, so pinning channel="chromium" would only narrow
            # which install of Playwright works.
            browser = pw.chromium.launch()
            # No device_scale_factor: --width should be the width of the file. Anyone
            # who wants it sharper can ask for a bigger one.
            page = browser.new_page(viewport={"width": size[0], "height": size[1]})
            for path in paths:
                name = pathlib.Path(path).stem
                url = f"http://127.0.0.1:{server.port}/?part={name}&view={view}"
                if not chrome:
                    url += "&bare=1"
                page.goto(url)
                try:
                    page.wait_for_function(
                        "window.__nurb && window.__nurb.ready", timeout=timeout
                    )
                except Exception as exc:
                    # Both causes are measured, and neither is the geometry, which is
                    # where a bare Playwright timeout would send the reader. `ready` is
                    # set from a requestAnimationFrame pair, so anything that stops the
                    # page painting stops it too.
                    raise BuildError(
                        f"{name}: the viewer did not finish drawing in "
                        f"{timeout / 1000:.0f}s. Two known causes: no network, since the "
                        f"viewer still loads three.js from unpkg, and a page that is not "
                        f"painting, since nothing is ever ready in a hidden tab."
                    ) from exc
                png = out_dir / f"{name}.png"
                # Bare hides the sidebar, so the canvas is the viewport and shooting it
                # gives exactly the size asked for. With the chrome kept, the sidebar is
                # part of what was asked for, so shoot the page.
                shot = page if chrome else page.locator("canvas")
                shot.screenshot(path=str(png))
                written.append((path, png))
            browser.close()
    finally:
        done.set()
    return written
