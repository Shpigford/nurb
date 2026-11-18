"""A part as a link anyone can open, and the way back into a library.

nurb.app keeps a snapshot: the part's files at the values it was shared at, a picture,
and the source that rebuilds it. Opening the link in nurb copies that source into a new
part, so the person who opened it can change it like any part of their own. No account
sits on either end; the token handed back at upload is the only thing that can replace
or delete the link, and it stays in the sharer's database.
"""

import io
import json
import math
import os
import re
import urllib.error
import urllib.request
import uuid

from . import db
from .shared import placed as places

# Overridable so a test, or a local copy of the site, can stand in for nurb.app.
HOST = os.environ.get("NURB_SHARE_HOST", "https://nurb.app").rstrip("/")
FORMAT = 1
# The files a share carries, and nothing else: the site refuses any other name.
FILES = ("part.json", "part.glb", "part.stl", "part.3mf", "part.png")
# A link as a person pastes it, the app's own scheme, or the bare id.
LINK = re.compile(r"^(?:(?:https?://[^/\s]+)?/s/|nurb://open/)?([A-Za-z0-9]{10})/?$")
TIMEOUT = 60


class ShareError(Exception):
    """A sentence for the person: what went wrong with the link, and what to do."""


def share_id(text):
    """The id inside a link, or None when it is not a share link."""
    found = LINK.match((text or "").strip())
    return found.group(1) if found else None


def url_of(share):
    return f"{HOST}/s/{share}"


def bundle(conn, part, run, values):
    """What a share says about the part, and everything that rebuilds it elsewhere.

    The source carries the shared values as its defaults, so the copy someone opens is
    the part they saw rather than the one the sharer started from.
    """
    from . import edit

    source = part["source"]
    if values:
        source, _, _ = edit.apply_to_source(source, values)
    params = [
        {
            "name": p.get("name"),
            "kind": p.get("kind"),
            "value": values.get(p.get("name"), p.get("default")),
        }
        for p in json.loads(run["params"])
        if p.get("kind") in ("int", "float", "bool", "choice", "str")
    ]
    findings = json.loads(run["findings"])
    stats = json.loads(run["stats"])
    rows = db.parts_of(conn, part["project_id"])
    modules = [{"name": row["name"], "kind": row["kind"], "source": row["source"]} for row in rows if row["kind"] != "part"]
    # An assembly builds the parts it places, and the parts those place, so they travel too.
    siblings = {row["name"]: row for row in rows if row["kind"] == "part" and row["name"] != part["name"]}
    placed, waiting = [], list(places(source))
    while waiting:
        name = waiting.pop(0)
        if name in siblings and name not in placed:
            placed.append(name)
            waiting.extend(places(siblings[name]["source"]))
    parts = [
        {"name": n, "title": siblings[n]["title"], "source": siblings[n]["source"], "card_md": siblings[n]["card_md"]}
        for n in placed
    ]
    # A shared module reads measurements too (notch's system.py reads the bracket pitch).
    texts = [source, *(m["source"] for m in modules), *(p["source"] for p in parts)]
    reads = set().union(*(db.measurement_names(text) for text in texts))
    return {
        "format": FORMAT,
        "name": part["name"],
        "title": part["title"],
        "params": params,
        "size_mm": stats.get("bbox"),
        "checks": {
            "fail": sum(1 for f in findings if f.get("severity") == "fail"),
            "warn": sum(1 for f in findings if f.get("severity") == "warn"),
        },
        "source": source,
        "card_md": part["card_md"],
        "modules": modules,
        "parts": parts,
        "measurements": [
            {"name": row["name"], "value": row["value"], "unit": row["unit"], "how": row["how"]}
            for row in db.measurements_of(conn, part["project_id"])
            if row["name"] in reads
        ],
    }


def picture(glb):
    """The link preview: the part on the stage colour, wide like every link card."""
    from PIL import Image

    from . import raster

    png = raster.render(glb, width=1200, height=630, view="iso", shadow=raster.SHADOW)
    shot = Image.open(io.BytesIO(png)).convert("RGBA")
    ground = Image.new("RGBA", shot.size, (0xE5, 0xF0, 0xFB, 255))
    ground.alpha_composite(shot)
    out = io.BytesIO()
    ground.convert("RGB").save(out, "PNG", optimize=True)
    return out.getvalue()


def _request(method, url, body=None, headers=None, raw=False):
    request = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    request.add_header("User-Agent", "nurb")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = response.read()
            return data if raw else json.loads(data or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            said = json.loads(exc.read()).get("error")
        except (ValueError, AttributeError):
            said = None
        raise ShareError(said or f"nurb.app answered {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ShareError("could not reach nurb.app. Check the internet connection and try again.") from None


def upload(files, existing=None):
    """Send the files to nurb.app. Returns {id, url, token}.

    With `existing` (a stored share row), the same link is replaced in place, so a link
    already sent to someone shows the newer part.
    """
    boundary = uuid.uuid4().hex
    body = io.BytesIO()
    for name, data in files.items():
        body.write(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n".encode()
        )
        body.write(data)
        body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if existing is None:
        return _request("POST", f"{HOST}/api/shares", body.getvalue(), headers)
    headers["Authorization"] = f"Bearer {existing['token']}"
    return _request("PUT", f"{HOST}/api/shares/{existing['share_id']}", body.getvalue(), headers)


def remove(existing):
    """Take the link down. A link nurb.app no longer has is already down."""
    try:
        _request(
            "DELETE",
            f"{HOST}/api/shares/{existing['share_id']}",
            headers={"Authorization": f"Bearer {existing['token']}"},
        )
    except ShareError as exc:
        if "no shared part" not in str(exc):
            raise


def fetch(link):
    """The bundle behind a link someone was sent."""
    found = share_id(link)
    if found is None:
        raise ShareError("that is not a nurb share link. It looks like nurb.app/s/ and ten letters and numbers.")
    try:
        return _request("GET", f"{HOST}/s/{found}/part.json")
    except ShareError as exc:
        if "404" in str(exc) or "no shared part" in str(exc):
            raise ShareError("that link was taken down, or it was never shared.") from None
        raise


def peek(link):
    """What the app shows before opening a link: the part's name, its picture, and how
    many numbers come with it. Nothing is copied or built yet."""
    import base64

    shared = fetch(link)
    png = _request("GET", f"{HOST}/s/{share_id(link)}/part.png", raw=True)
    return {
        "name": shared.get("name"),
        "title": shared.get("title"),
        "params": len(shared.get("params") or []),
        "picture": "data:image/png;base64," + base64.b64encode(png).decode(),
    }


def land(conn, shared):
    """A shared bundle as a new part in this library. Returns (project id, part name)."""
    if not isinstance(shared, dict) or shared.get("format") != FORMAT:
        raise ShareError("this link was shared from a newer nurb. Update nurb, then open it again.")
    name, source = shared.get("name"), shared.get("source")
    if not isinstance(name, str) or not db.PART_NAME.match(name) or not isinstance(source, str):
        raise ShareError("this shared part is missing its source, so there is nothing to open.")
    strange = ShareError("this shared part carries a file nurb does not recognise, so it was not opened.")
    # Checked before anything is written: whatever passes here must also build, or the
    # person is left with a part in their library that fails on every build.
    modules = shared.get("modules") or []
    names = [m.get("name") if isinstance(m, dict) else None for m in modules]
    for module, module_name in zip(modules, names):
        kind = module.get("kind") if isinstance(module, dict) else None
        if (
            not isinstance(module_name, str)
            or not module_name.isidentifier()
            or kind not in ("module", db.PARTS_MODULE_KIND)
            or (kind == db.PARTS_MODULE_KIND and not module_name.startswith("_"))
            or not isinstance(module.get("source"), str)
        ):
            raise strange
    parts = shared.get("parts") or []
    for placed in parts:
        if (
            not isinstance(placed, dict)
            or not isinstance(placed.get("name"), str)
            or not db.PART_NAME.match(placed["name"])
            or not isinstance(placed.get("source"), str)
        ):
            raise strange
    names += [p["name"] for p in parts]
    if len(set(names)) != len(names) or name in names:
        raise strange
    rows = shared.get("measurements") or []
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("name"), str)
            or isinstance(row.get("value"), bool)
            or not isinstance(row.get("value"), (int, float))
            or not math.isfinite(row["value"])
        ):
            raise ShareError("this shared part carries a measurement nurb cannot read, so it was not opened.")
    with db.transaction(conn):
        project_id = db.create_project(conn, name)
        for module in modules:
            db.create_part(conn, project_id, module["name"], module["source"], kind=module["kind"])
        for row in rows:
            db.set_measurement(
                conn,
                project_id,
                row["name"],
                float(row["value"]),
                str(row.get("how") or "from a shared part"),
                unit=str(row.get("unit") or "mm"),
            )
        for placed in parts:
            _add_part(conn, project_id, placed)
        _add_part(conn, project_id, shared)
    return project_id, name


def _add_part(conn, project_id, entry):
    card = entry.get("card_md") if isinstance(entry.get("card_md"), str) else None
    part_id = db.create_part(conn, project_id, entry["name"], entry["source"], card_md=card)
    title = entry.get("title")
    if isinstance(title, str) and title.strip():
        conn.execute("UPDATE parts SET title = ? WHERE id = ?", (title.strip()[: db.NAME_LIMIT], part_id))
