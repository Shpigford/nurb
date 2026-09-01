"""Geometry answers, so nobody writes a probe script to get them.

A finding says what is wrong and by how much. What it cannot say is which piece of
geometry to move, and that is the question an agent actually has to answer before it
can edit the part. With no way to ask, it builds its own measuring tools: in one
recorded session twelve of thirty-eight shell commands were throwaway Python that
imported the part, built it, and printed a face centre. This is that, once, in the
package.

**Everything here is reported in the units the rules use**, and mostly by calling the
same helpers. An inspector that measured overhang from horizontal while the rule
measured it from the build direction would leave the agent reconciling two numbers for
one face, which is worse than not having it.
"""

from math import asin, degrees

from build123d import Vector

from . import checks

AXES = {
    (1, 0, 0): "+X",
    (-1, 0, 0): "-X",
    (0, 1, 0): "+Y",
    (0, -1, 0): "-Y",
    (0, 0, 1): "+Z",
    (0, 0, -1): "-Z",
}


def _label(v):
    """`+Z` where a normal is axis-aligned, the components otherwise."""
    parts = (v.X, v.Y, v.Z)
    if all(abs(c - round(c)) < 1e-6 for c in parts):
        key = tuple(int(round(c)) for c in parts)
        if key in AXES:
            return AXES[key]
    return f"({v.X:+.2f}, {v.Y:+.2f}, {v.Z:+.2f})"


def _droop(face, up):
    """Degrees away from the build direction, measured the way the overhang rule does.

    A vertical wall is 0 and a downward-facing ceiling is 90, and the sampling comes
    from `checks` rather than a second copy, so a face this prints at 52 degrees is the
    same face the rule fires on at 52 degrees.
    """
    return max(
        degrees(asin(max(-1.0, min(1.0, -n.dot(up))))) for n in checks._sample_normals(face)
    )


def faces(shape, ctx):
    """One row per face, largest first, in the rules' units."""
    up = Vector(*ctx.up).normalized()
    bed, _ = checks._span(shape, up)
    rows = []
    for face in shape.faces():
        try:
            normal = face.normal_at(face.center())
            droop = _droop(face, up)
        except Exception:  # a face OCCT will not give a normal for still has an area
            normal, droop = None, None
        rows.append(
            {
                "face": face,
                "area": face.area,
                "center": face.center(),
                "normal": normal,
                "droop": droop,
                "grounded": checks._span(face, up)[1] <= bed + 1e-4,
                "kind": face.geom_type.name.lower(),
            }
        )
    rows.sort(key=lambda r: -r["area"])
    return rows, bed


# A `where` is rounded to two decimals before it is reported, so a point that really is
# a face's centre, or really is on it, can sit that far off.
ON_FACE = 0.05


def _on_face(rows, where):
    """The face row a finding's `where` came from, or None.

    Two ways, in this order, and never a nearest-neighbour search. Six of the seven
    rules set `where` to a face's centre, so matching centres is an exact recovery of
    what the rule was looking at. That has to come first, because **a face's centre is
    not always on the face**: the underside of a plate with a pocket in it is an annulus
    whose centroid sits in the hole, and containment alone silently misses every one of
    them. `min_wall` is the other case, setting `where` to a probe point that is on its
    face but is not the centre, which is what the containment pass is for.

    Stability sets `where` to the solid's centre of mass and matches neither, which is
    correct: nearest-neighbour would answer it with a confident, meaningless face and
    the agent would go and edit that face.
    """
    if not where:
        return None
    point = Vector(*where)
    for row in rows:
        if (row["center"] - point).length <= ON_FACE:
            return row
    hits = []
    for row in rows:
        try:
            if row["face"].distance_to(point) <= ON_FACE:
                hits.append(row)
        except Exception:
            continue
    return max(hits, key=lambda r: r["area"]) if hits else None


def finding_faces(shape, ctx, findings):
    """The face row each finding fired on, in findings order, None where there is none.

    This is `_on_face` run for a whole findings list, and it is what lets anything
    downstream point at a finding instead of quoting its coordinate: the viewer paints
    the row's face, and `inspect --render` stands a camera along its normal.
    """
    rows, _ = faces(shape, ctx)
    return [_on_face(rows, f.where) for f in findings]


def _face_line(row):
    normal = _label(row["normal"]) if row["normal"] is not None else row["kind"]
    value = row["droop"]
    if value is None:
        droop = "    -"
    else:
        droop = f"{0.0 if abs(value) < 0.05 else value:5.1f}"  # never print -0.0
    c = row["center"]
    note = "  on the bed" if row["grounded"] else ""
    return (
        f"{row['area']:9.1f}mm2  {droop} deg  {normal:>22}"
        f"  at ({c.X:7.2f},{c.Y:7.2f},{c.Z:7.2f}){note}"
    )


def report(name, shape, ctx, findings, limit=12):
    rows, bed = faces(shape, ctx)
    box = shape.bounding_box()
    concave = checks.concave_edges(shape)
    up = Vector(*ctx.up).normalized()

    lines = [
        f"  {name}  {box.size.X:.2f} x {box.size.Y:.2f} x {box.size.Z:.2f} mm"
        f"  {shape.volume:.1f}mm3"
        f"  {len(shape.solids())} solid, {len(rows)} faces, {len(shape.edges())} edges",
        f"  building {_label(up)}, bed plane at {bed:.2f}, "
        f"{sum(1 for r in rows if r['grounded'])} face(s) on it",
        "",
    ]

    # Findings first, and each one resolved to the face it fired on. This is the whole
    # point: "52deg over 210mm2" plus a coordinate is a lookup the agent was doing by
    # hand, and the answer is already sitting in the rows above.
    if findings:
        lines.append(f"  findings  {len(findings)}")
        for finding in findings:
            lines.append(f"      {finding}")
            row = _on_face(rows, finding.where)
            if row is not None:
                lines.append(f"          {_face_line(row)}")
        lines.append("")
    else:
        lines += ["  findings  none", ""]

    shown = rows[:limit]
    lines.append(
        f"  faces  showing {len(shown)} of {len(rows)}, largest first. droop is degrees"
    )
    lines.append(
        f"      from the build direction, as the overhang rule measures it: 0 is a wall,"
        f" +90 a ceiling,"
    )
    lines.append(
        f"      negative faces up. Past {ctx.overhang_limit:.0f} is a finding unless it is"
        f" on the bed, a short bridge,"
        f" or declared to print on supports."
    )
    for row in shown:
        lines.append(f"      {_face_line(row)}")
    kinds = {}
    for row in rows:
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
    lines.append("      " + ", ".join(f"{n} {k}" for k, n in sorted(kinds.items())))
    lines.append("")

    lines.append(f"  concave edges  {len(concave)}, where polish is forbidden")
    for edge in sorted(concave, key=lambda e: -e.length)[:limit]:
        c = edge.center()
        lines.append(
            f"      {edge.length:8.2f}mm  at ({c.X:7.2f},{c.Y:7.2f},{c.Z:7.2f})"
        )
    if len(concave) > limit:
        lines.append(f"      and {len(concave) - limit} more")
    return lines
