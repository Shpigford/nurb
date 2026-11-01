"""Flat-shaded pictures of a part: a GLB in, PNG bytes or a pixel array out.

This is the renderer behind every picture nurb hands out: the still that rides
along with a build result, the four operator views behind `look`, the images an
MCP resource serves, and the `look` tool. It is a part illustration rather than a
lit render: every face takes one of five palette tones by the direction it
faces, every sharp crease and silhouette gets the edge stroke, and a raised-tone
shadow ellipse on the floor plane sets the part down instead of leaving it
floating. The named views (`VIEWS`) are the operator's eyes: after a build
passes, look at the part from the opposed corner, from above and from
underneath, because a slot cut through the face that presses on the desk passes
every check and holds nothing.

No GPU, no window, and no imaging library: triangles are projected with numpy
and rasterized into a z-buffer (one tile of pixels per triangle), the strokes
are depth-tested against it, the result is downsampled 2x for anti-aliasing, and
the PNG is built here out of zlib and struct. Nothing in this module imports
`nurb`, because importing the package pulls in OCCT and costs four seconds that
a thumbnail should not pay.
"""

import io
import struct
import zlib

import numpy as np
import trimesh

VIEW = np.array([0.7, -0.75, 0.6])
VIEWS = {
    "iso": VIEW,
    "back": np.array([-0.7, 0.75, 0.6]),
    "top": np.array([0.0, 0.0, 1.0]),
    "under": np.array([0.7, -0.75, -0.6]),
}
CAPTIONS = {
    "iso": "From the front-left corner, above.",
    "back": "From the back-right corner, above: the faces the first view hides.",
    "top": "Straight down: the plan, with the part's back at the top of the picture.",
    "under": "From underneath: the face that sits on the bed, and whatever mates there.",
}
LOOK_NOTE = "Read the pictures against how the part sits in use: find the face that touches the desk or the wall, then the faces that hold the payload. A corner or sliver that is none of those is debris left by a union or a chamfer that ran off its face. What you see is a hypothesis; confirm a fault by coordinate with the inspect report before editing."

EDGE_ANGLE_DEG = 25.0
WIDTH, HEIGHT = 640, 400
TILE = (640, 400)
SUPERSAMPLE = 2
PAD = 0.14

TOP = (0xFF, 0x70, 0x50)
CHAMFER = (0xFA, 0x64, 0x44)
FRONT = (0xF0, 0x42, 0x1F)
SIDE = (0xC4, 0x2D, 0x12)
UNDER = (0x9E, 0x24, 0x10)
EDGE = (0xA3, 0x24, 0x09)
SHADOW = (0xEE, 0xF2, 0xF8)
GHOST = (0x8B, 0x95, 0xA6)
GHOST_EDGE = (0x4B, 0x55, 0x66)
GHOST_ALPHA = 0.42
GHOST_BEHIND = 0.16
LABEL = (0x4B, 0x55, 0x66)
PAPER = (0xFF, 0xFF, 0xFF)

MAX_FACES = 400_000


class Unrenderable(ValueError):
    """The GLB carries nothing a picture can show."""


def looks(glb_bytes, names, width=WIDTH, height=HEIGHT, cut=None):
    """PNG bytes per named view, in the order asked."""
    _check_names(names)
    mesh, ghost = _split(glb_bytes)
    out = {}
    for name in names:
        view = VIEWS[name]
        out[name] = encode_png(_frame(*_sliced(mesh, cut, view), ghost, width, height, view))
    return out


def render(glb_bytes, width=WIDTH, height=HEIGHT, view=None, cut=None):
    """PNG bytes for one view, with the `context` scenery left out."""
    return encode_png(frame(glb_bytes, view, width, height, ghost=False, cut=cut))


def frame(glb_bytes, view=None, width=WIDTH, height=HEIGHT, ghost=True, cut=None):
    """The picture as an (h, w, 4) uint8 array, which is what both PNG paths render."""
    mesh, scenery = _split(glb_bytes)
    direction = _direction(view)
    return _frame(*_sliced(mesh, cut, direction), scenery if ghost else None, width, height, direction)


def composite(glb_bytes, tile=TILE, cut=None):
    """All four views tiled 2x2 on white, each under its name, as one RGB PNG.

    One picture rather than four, because a tool result carrying four images
    costs four times the tokens to say the same thing, and the operator reads
    them together anyway.
    """
    tw, th = tile
    strip = 18
    mesh, ghost = _split(glb_bytes)
    cell_h = th + strip
    canvas = np.full((cell_h * 2 + 1, tw * 2 + 1, 3), PAPER, dtype=np.uint8)
    canvas[cell_h, :] = SHADOW
    canvas[:, tw] = SHADOW
    for i, name in enumerate(VIEWS):
        view = VIEWS[name]
        picture = _flatten(_frame(*_sliced(mesh, cut, view), ghost, tw, th, view))
        y = (i // 2) * (cell_h + 1)
        x = (i % 2) * (tw + 1)
        _text(canvas[y : y + strip, x : x + tw], name.upper(), 4, 2)
        canvas[y + strip : y + strip + th, x : x + tw] = picture
    return encode_png(canvas)


def _check_names(names):
    unknown = [name for name in names if name not in VIEWS]
    if unknown:
        raise ValueError(f"unknown view {unknown[0]!r}; choose from {', '.join(VIEWS)}")


def _direction(view):
    if view is None:
        return VIEW
    if isinstance(view, str):
        _check_names([view])
        return VIEWS[view]
    return np.asarray(view, dtype=np.float64)


def _sliced(mesh, cut, view):
    """(the part cut by a plane, the cap's outward normal), keeping the half the camera looks into."""
    if cut is None:
        return mesh, None
    axis, position = cut
    i = "xyz".index(str(axis).lower())
    lo, hi = mesh.bounds[:, i]
    origin = mesh.bounds.mean(axis=0)
    if position is not None:
        origin[i] = float(position)
    # A plane past the part would silently draw it uncut; say where the part is instead.
    if not lo < origin[i] < hi:
        raise Unrenderable(
            f"the cut at {axis}={origin[i]:.4g} misses the part, which spans {axis} {lo:.4g} to {hi:.4g}"
        )
    normal = np.zeros(3)
    normal[i] = -1.0 if view[i] >= 0 else 1.0
    cut_mesh = _slice_half(mesh, origin, normal)
    if cut_mesh is None or not len(cut_mesh.faces):
        raise Unrenderable(f"the cut at {axis}={origin[i]:.4g} leaves nothing to draw")
    cut_mesh.merge_vertices()
    return cut_mesh, -normal


def _slice_half(mesh, origin, normal):
    """The open half on the normal's side; `_frame` closes it by painting the back faces the cap's tone.

    trimesh's own capping wants shapely, which nurb does not depend on, so the
    cut is clipped face by face and never capped here.
    """
    verts, faces = trimesh.intersections.slice_faces_plane(
        np.asarray(mesh.vertices), np.asarray(mesh.faces), normal, origin
    )[:2]
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


def _camera(verts, view, width, height):
    """(project, scale): world points to pixels and depth towards the eye."""
    view = view / np.linalg.norm(view)
    right = np.cross((0.0, 0.0, 1.0), view)
    if np.linalg.norm(right) < 1e-6:
        right = np.cross((0.0, 1.0, 0.0), view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    framed = np.asarray(verts, dtype=np.float64)
    flo, fhi = framed.min(axis=0), framed.max(axis=0)
    center = (flo + fhi) / 2
    fx, fy = (framed - center) @ right, (framed - center) @ up
    span_x = max(fx.max() - fx.min(), 1e-9)
    span_y = max(fy.max() - fy.min(), 1e-9)
    scale = min(width * (1 - 2 * PAD) / span_x, height * (1 - 2 * PAD) / span_y)
    mid_x, mid_y = (fx.min() + fx.max()) / 2, (fy.min() + fy.max()) / 2

    def project(points):
        r = np.asarray(points, dtype=np.float64) - center
        x = (r @ right - mid_x) * scale + width / 2
        y = height / 2 - (r @ up - mid_y) * scale
        return np.stack([x, y], axis=1), r @ view

    return project, scale


def _frame(mesh, cap_normal, ghost, width, height, view):
    if len(mesh.faces) + (len(ghost.faces) if ghost is not None else 0) > MAX_FACES:
        raise Unrenderable(f"too many triangles to draw ({len(mesh.faces)})")

    ss = SUPERSAMPLE
    w, h = width * ss, height * ss
    verts = np.asarray(mesh.vertices, dtype=np.float64)
    faces = np.asarray(mesh.faces, dtype=np.int64)
    normals = np.asarray(mesh.face_normals, dtype=np.float64)

    view = view / np.linalg.norm(view)
    lo, hi = verts.min(axis=0), verts.max(axis=0)
    framed = verts if ghost is None else np.vstack([verts, np.asarray(ghost.vertices, dtype=np.float64)])
    center = (framed.min(axis=0) + framed.max(axis=0)) / 2
    project, scale = _camera(framed, view, w, h)

    pts, depth = project(verts)
    visible = (normals @ view) > 1e-6
    colors = _colors(normals)
    strokes = _stroked_edges(mesh, faces, normals, visible)

    depth_px, face_px = _rasterize(pts, depth, faces, visible, w, h)
    color = np.zeros((h, w, 4), dtype=np.uint8)
    painted = face_px >= 0
    color[painted, :3] = np.array(colors, dtype=np.uint8)[face_px[painted]]
    color[painted, 3] = 255
    if cap_normal is not None:
        depth_px, painted = _cap(color, pts, depth, faces, visible, depth_px, painted, cap_normal)
    stroke_width = max(1, int(round(1.2 * ss)))
    color[_stroke_mask(pts, depth, strokes, depth_px, stroke_width, scale)] = (*EDGE, 255)
    if ghost is not None:
        color = _ghost_over(color, ghost, project, view, depth_px, stroke_width, scale)

    under = np.zeros((h, w, 4), dtype=np.uint8)
    # The shadow is an ellipse drawn ON the floor (the part's lowest z) around
    # its footprint, then sent through the same camera, so it lies at the
    # floor's angle under the part instead of hanging flat below its lowest pixel.
    # It is a touch wider than the footprint and slides towards the eye, so it
    # shows past the near edges the way a pool of shade does under a lit part.
    # A camera under the floor or straight above it gets no shadow: there is
    # no near edge for it to show past.
    if view[2] > 1e-6 and np.linalg.norm(view[:2]) > 1e-6:
        ex, ey = (hi - lo)[:2] / 2
        grow = 0.12 * max(ex, ey, 1e-9)
        towards_eye = view[:2] / np.linalg.norm(view[:2]) * 0.16 * max(ex, ey)
        t = np.linspace(0.0, 2 * np.pi, 96, endpoint=False)
        ground = np.stack([
            center[0] + towards_eye[0] + (ex * 1.2 + grow) * np.cos(t),
            center[1] + towards_eye[1] + (ey * 1.2 + grow) * np.sin(t),
            np.full_like(t, lo[2]),
        ], axis=1)
        gpts, _ = project(ground)
        _fill_polygon(under, gpts[:, 0], gpts[:, 1], SHADOW)
    image = _over(color, under)

    return _halve(image) if ss > 1 else image


def _cap(color, pts, depth, faces, visible, depth_px, painted, cap_normal):
    """Close an uncapped cut by painting its back faces the tone the cap would take.

    A cut mesh with no cap reads as a hollow shell, because every surface the
    camera now looks at through the opening points away from it.
    """
    back_depth, back_face = _rasterize(pts, depth, faces, ~visible, *painted.shape[::-1])
    fill = (back_face >= 0) & ~painted
    if not fill.any():
        return depth_px, painted
    color[fill, :3] = np.array(_colors(np.asarray([cap_normal], dtype=np.float64))[0], dtype=np.uint8)
    color[fill, 3] = 255
    depth_px = np.where(fill, back_depth, depth_px)
    return depth_px, painted | fill


def _over(src, dst):
    """Source-over of two straight-alpha RGBA arrays."""
    s, d = src.astype(np.float64), dst.astype(np.float64)
    sa, da = s[..., 3:4] / 255.0, d[..., 3:4] / 255.0
    out_a = sa + da * (1 - sa)
    safe = np.where(out_a > 0, out_a, 1.0)
    rgb = (s[..., :3] * sa + d[..., :3] * da * (1 - sa)) / safe
    out = np.empty_like(src)
    out[..., :3] = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.rint(out_a[..., 0] * 255), 0, 255).astype(np.uint8)
    return out


def _halve(image):
    """2x2 box mean over premultiplied alpha, which is the anti-aliasing.

    Averaging straight alpha would drag the transparent background's colour into
    every silhouette pixel and fringe the part with black.
    """
    h, w = image.shape[0] // 2, image.shape[1] // 2
    f = image[: h * 2, : w * 2].astype(np.float64)
    a = f[..., 3:4] / 255.0
    pre = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=2)
    mean = pre.reshape(h, 2, w, 2, 4).mean(axis=(1, 3))
    alpha = mean[..., 3:4] / 255.0
    safe = np.where(alpha > 0, alpha, 1.0)
    out = np.empty((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.rint(mean[..., :3] / safe), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.rint(mean[..., 3]), 0, 255).astype(np.uint8)
    return out


def _flatten(image, ground=PAPER):
    """RGBA down to RGB on an opaque ground."""
    a = image[..., 3:4].astype(np.float64) / 255.0
    rgb = image[..., :3].astype(np.float64) * a + np.array(ground, dtype=np.float64) * (1 - a)
    return np.clip(np.rint(rgb), 0, 255).astype(np.uint8)


def _fill_polygon(canvas, xs, ys, color):
    """Even-odd scanline fill, the one polygon this renderer draws."""
    h, w = canvas.shape[:2]
    y0 = max(int(np.floor(ys.min())), 0)
    y1 = min(int(np.ceil(ys.max())), h - 1)
    ax, ay = xs, ys
    bx, by = np.roll(xs, -1), np.roll(ys, -1)
    for py in range(y0, y1 + 1):
        yc = py + 0.5
        crosses = ((ay <= yc) & (by > yc)) | ((by <= yc) & (ay > yc))
        if not crosses.any():
            continue
        t = (yc - ay[crosses]) / (by[crosses] - ay[crosses])
        hits = np.sort(ax[crosses] + t * (bx[crosses] - ax[crosses]))
        for left, right in zip(hits[0::2], hits[1::2]):
            ia = max(int(np.ceil(left - 0.5)), 0)
            ib = min(int(np.floor(right - 0.5)), w - 1)
            if ib >= ia:
                canvas[py, ia : ib + 1, :3] = color
                canvas[py, ia : ib + 1, 3] = 255


def _ghost_over(color, ghost, project, view, part_depth, stroke_width, scale):
    """The payload composited over the part's picture as a see-through grey.

    Depth-tested against the part: where the ghost is nearer it reads at
    GHOST_ALPHA, where the part hides it at GHOST_BEHIND, so a speaker sitting in
    a tray shows its bottom faintly through the tray wall and its body plainly
    above it. Its own silhouette and creases get a darker stroke, because a
    round object reads as round by its outline.
    """
    h, w = part_depth.shape
    verts = np.asarray(ghost.vertices, dtype=np.float64)
    faces = np.asarray(ghost.faces, dtype=np.int64)
    normals = np.asarray(ghost.face_normals, dtype=np.float64)
    pts, depth = project(verts)
    visible = (normals @ view) > 1e-6
    depth_px, face_px = _rasterize(pts, depth, faces, visible, w, h)
    painted = face_px >= 0
    if not painted.any():
        return color
    strokes = _stroked_edges(ghost, faces, normals, visible)
    edge = _stroke_mask(pts, depth, strokes, depth_px, stroke_width, scale) & painted
    nearer = depth_px > part_depth
    alpha = np.where(nearer, GHOST_ALPHA, GHOST_BEHIND)
    alpha = np.where(edge, np.where(nearer, 0.85, 0.35), alpha)
    alpha = np.where(painted, alpha, 0.0)[..., None]
    src = np.where(edge[..., None], np.array(GHOST_EDGE, dtype=np.float64), np.array(GHOST, dtype=np.float64))
    src = np.broadcast_to(src, (h, w, 3))
    dst = color.astype(np.float64)
    dst_a = dst[..., 3:4] / 255.0
    out_a = alpha + dst_a * (1 - alpha)
    safe = np.where(out_a > 0, out_a, 1.0)
    out_rgb = (src * alpha + dst[..., :3] * dst_a * (1 - alpha)) / safe
    out = np.empty_like(color)
    out[..., :3] = np.clip(np.rint(out_rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.rint(out_a[..., 0] * 255), 0, 255).astype(np.uint8)
    return out


def _rasterize(pts, depth, faces, visible, w, h):
    """Per pixel: depth towards the eye (-inf where nothing paints) and the face index (-1).

    A z-buffer, one triangle at a time. Sorting whole triangles back to front
    paints a far wall's long sliver over a near top face whenever their
    centroids disagree with their pixels, and a pocket floor is exactly that.
    """
    zbuf = np.full((h, w), -np.inf, dtype=np.float64)
    fbuf = np.full((h, w), -1, dtype=np.int64)
    for fi in np.nonzero(visible)[0]:
        tri = faces[fi]
        x, y = pts[tri, 0], pts[tri, 1]
        z = depth[tri]
        x0, x1 = max(int(np.floor(x.min())), 0), min(int(np.ceil(x.max())), w - 1)
        y0, y1 = max(int(np.floor(y.min())), 0), min(int(np.ceil(y.max())), h - 1)
        if x0 > x1 or y0 > y1:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = (x[1] - x[0]) * (gy - y[0]) - (y[1] - y[0]) * (gx - x[0])
        w1 = (x[2] - x[1]) * (gy - y[1]) - (y[2] - y[1]) * (gx - x[1])
        w2 = (x[0] - x[2]) * (gy - y[2]) - (y[0] - y[2]) * (gx - x[2])
        area = w0 + w1 + w2
        if abs(area[0, 0]) < 1e-9:
            continue
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) if area[0, 0] > 0 else (w0 <= 0) & (w1 <= 0) & (w2 <= 0)
        if not inside.any():
            continue
        gz = (w1 * z[0] + w2 * z[1] + w0 * z[2]) / area
        ztile = zbuf[y0 : y1 + 1, x0 : x1 + 1]
        nearer = inside & (gz > ztile)
        ztile[nearer] = gz[nearer]
        fbuf[y0 : y1 + 1, x0 : x1 + 1][nearer] = fi
    return zbuf, fbuf


def _stroke_mask(pts, depth, strokes, zbuf, width, scale):
    """Boolean (h, w) of the edge stroke: crease and silhouette samples the z-buffer has in front."""
    h, w = zbuf.shape
    mask = np.zeros((h, w), dtype=bool)
    edges = {tuple(sorted(e)) for lst in strokes.values() for e in lst}
    if not edges:
        return mask
    slack = 3.0 / scale
    xs, ys = [], []
    for a, b in edges:
        pa, pb = pts[a], pts[b]
        n = max(2, int(np.ceil(np.hypot(*(pb - pa)))) + 1)
        t = np.linspace(0.0, 1.0, n)
        ix = np.clip((pa[0] + (pb[0] - pa[0]) * t).astype(np.int64), 0, w - 1)
        iy = np.clip((pa[1] + (pb[1] - pa[1]) * t).astype(np.int64), 0, h - 1)
        z = depth[a] + (depth[b] - depth[a]) * t
        keep = z >= zbuf[iy, ix] - slack
        xs.append(ix[keep])
        ys.append(iy[keep])
    xs, ys = np.concatenate(xs), np.concatenate(ys)
    r = int(np.ceil(width / 2))
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy > (width / 2) ** 2 + 0.25:
                continue
            mask[np.clip(ys + dy, 0, h - 1), np.clip(xs + dx, 0, w - 1)] = True
    return mask


def _mesh(glb_bytes):
    return _split(glb_bytes)[0]


def _split(glb_bytes):
    """(the part, the `context` scenery or None), each welded for edge finding."""
    loaded = trimesh.load(io.BytesIO(glb_bytes), file_type="glb", process=False)
    parts, context = [], []
    if isinstance(loaded, trimesh.Scene):
        for node in loaded.graph.nodes_geometry:
            transform, geom_name = loaded.graph[node]
            geom = loaded.geometry.get(geom_name)
            if not isinstance(geom, trimesh.Trimesh) or not len(geom.faces):
                continue
            (context if geom_name == "context" else parts).append(geom.copy().apply_transform(transform))
    elif isinstance(loaded, trimesh.Trimesh):
        parts.append(loaded)
    if not parts:
        raise Unrenderable("no geometry to draw")
    mesh = parts[0] if len(parts) == 1 else trimesh.util.concatenate(parts)
    if not len(mesh.faces):
        raise Unrenderable("no geometry to draw")
    ghost = None if not context else (context[0] if len(context) == 1 else trimesh.util.concatenate(context))
    # The exporter splits vertices at face boundaries (crisp normals in the
    # viewer); creases and silhouettes are only findable once they are welded.
    mesh.merge_vertices()
    if ghost is not None:
        ghost.merge_vertices()
    return mesh, ghost


def _colors(normals):
    """One palette tone per face, chosen by where the face points."""
    nz = normals[:, 2]
    front = -normals[:, 1]
    side = normals[:, 0]
    tones = np.where(front >= side, 0, 1)
    lut = np.array([FRONT, SIDE, TOP, CHAMFER, UNDER], dtype=np.uint8)
    tones = np.where(nz > 0.85, 2, tones)
    tones = np.where((nz <= 0.85) & (nz > 0.3), 3, tones)
    tones = np.where(nz < -0.3, 4, tones)
    return [tuple(int(c) for c in lut[t]) for t in tones]


def _stroked_edges(mesh, faces, normals, visible):
    """face index -> [(va, vb), ...] of the edges to stroke when that face paints.

    A crease sharper than EDGE_ANGLE_DEG between two visible faces, or a
    silhouette (one face towards the eye, the other away).
    """
    strokes = {}
    if not len(mesh.face_adjacency):
        return strokes
    pairs = np.asarray(mesh.face_adjacency)
    edges = np.asarray(mesh.face_adjacency_edges)
    angles = np.degrees(np.asarray(mesh.face_adjacency_angles))
    a_vis = visible[pairs[:, 0]]
    b_vis = visible[pairs[:, 1]]
    sharp = (angles > EDGE_ANGLE_DEG) & a_vis & b_vis
    silhouette = a_vis != b_vis
    for (fa, fb), (va, vb), keep in zip(pairs, edges, sharp | silhouette):
        if not keep:
            continue
        for f in (int(fa), int(fb)):
            if visible[f]:
                strokes.setdefault(f, []).append((int(va), int(vb)))
    return strokes


# A 5x7 uppercase font, drawn by hand for this file: the only text a picture
# carries is a view name, so the alphabet stops at letters, digits and three
# marks rather than dragging in a font file the viewer would have to ship.
FONT = {
    " ": "00000 00000 00000 00000 00000 00000 00000",
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01110",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    "-": "00000 00000 00000 01110 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 00000 00100",
    ":": "00000 00100 00000 00000 00100 00000 00000",
}
GLYPH_SCALE = 2


def _text(strip, message, x, y, color=LABEL):
    """Letter a label into an RGB strip at 2x, so glyphs are 10x14."""
    s = GLYPH_SCALE
    h, w = strip.shape[:2]
    for char in message.upper():
        rows = FONT.get(char, FONT[" "]).split()
        bits = np.array([[c == "1" for c in row] for row in rows])
        block = np.repeat(np.repeat(bits, s, axis=0), s, axis=1)
        bh, bw = block.shape
        if x + bw > w or y + bh > h:
            break
        target = strip[y : y + bh, x : x + bw]
        target[block] = color
        x += bw + s


def encode_png(array):
    """PNG bytes for an (h, w, 3) or (h, w, 4) uint8 array, byte-for-byte repeatable.

    zlib and struct rather than an imaging library, because this module has to
    stay importable without OCCT or Pillow in the environment.
    """
    array = np.ascontiguousarray(array, dtype=np.uint8)
    h, w, channels = array.shape
    color_type = {3: 2, 4: 6}.get(channels)
    if color_type is None:
        raise ValueError(f"expected 3 or 4 channels, got {channels}")
    raw = array.reshape(h, w * channels)
    body = zlib.compress(_scanlines(raw), 9)
    header = struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", header) + _chunk(b"IDAT", body) + _chunk(b"IEND", b"")


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _scanlines(raw):
    """The IDAT payload: every row prefixed by filter byte 0.

    Per-row adaptive filtering was measured and dropped. On flat-shaded art the
    long runs of one tone are what zlib is good at, and Sub or Paeth breaks
    every run into deltas: the notch composite came out 33% larger with the
    usual minimum-sum heuristic than with plain zeros.
    """
    return b"".join(b"\x00" + raw[y].tobytes() for y in range(raw.shape[0]))
