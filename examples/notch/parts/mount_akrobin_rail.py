"""Mount - AkroBin Rail - 3x. Read mount_akrobin_rail.md before changing anything."""

from nurb import *

from system import (
    BLOCK_WIDTH,
    CHANNEL_WIDTH,
    EPS,
    MIN_ITEM_DEPTH,
    OVERSHOOT,
    channels,
    detent_dimples,
    pitch,
    polish as polish_pass,
)

# The bin is hardware, the same as the bracket is, so its dimensions come out of
# measurements.toml with how they were obtained. `item_depth` below is the sum of two of
# them and not a preference: get it wrong and the leg jams on the wall while the bin's
# back wall floats with nothing bearing on it.
BIN_LEG_THICKNESS = measured("akrobin_leg_thickness")  # the hanger leg, front to back
BIN_LEG_LENGTH = measured("akrobin_leg_length")  # how far it reaches into the bin's slot
BIN_SLOT_DEPTH = measured("akrobin_slot_depth")  # back wall to leg, the gap to stand in

RIB_MARGIN = 2.0  # spare rib above the slot, so a bin seats before it bottoms out

# The four convex face pairs the polish pass is allowed to touch, and the one concave
# pair the structural pass relieves. An allow-list, not a deny-list, because the Fusion
# original was a deny-list until the relief merged two faces into one plane, the role
# stopped matching, the structural set came back empty and the kernel threw a bare
# "invalid argument". Naming what gets chamfered fails loudly instead.
COSMETIC = [
    {"front", "ribtop"},
    {"front", "side"},
    {"ribtop", "side"},
    {"ribrear", "ribtop"},
]
STRUCTURAL = [{"ribrear", "platetop"}]


def _relief_bands(count, step, pad_width, y0, y1):
    """The stretches of back face carrying no bracket pad, so nothing needs full depth.

    Pads may overlap (a short `bracket_step` with a wide pad) or hang off the ends, so
    this walks the run rather than assuming one gap per interval. No bands at all is a
    solid back, which is correct rather than an error.
    """
    bands, cursor = [], y0
    for center in pitch(count, step):
        lo, hi = center - pad_width / 2, center + pad_width / 2
        if lo - cursor > EPS:
            bands.append((cursor, lo))
        cursor = max(cursor, hi)
    if y1 - cursor > EPS:
        bands.append((cursor, y1))
    return bands


def _touching(body):
    """Every edge of `body` with the faces that meet there.

    Keyed by the edges the solid itself hands back, because `chamfer` takes its target
    from `edges[0].topo_parent`.
    """
    faces = {}
    for face in body.faces():
        for edge in face.edges():
            faces.setdefault(edge, []).append(face)
    return [(edge, faces.get(edge, [])) for edge in body.edges()]


@part
def mount_akrobin_rail(
    bracket_count=3,
    bracket_step=4,
    item_depth=BIN_LEG_THICKNESS + BIN_SLOT_DEPTH,
    item_height=40.0,
    rib_height=15.0,
    rib_thickness=2.25,
    relief_depth=3.25,
    pad_width=BLOCK_WIDTH + 3.0,
    chamfer_size=1.0,
    structural_chamfer=2.0,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves too little material behind the channel "
            f"floor to hold the dovetail. Raise it above {MIN_ITEM_DEPTH}."
        )

    # The bin's leg floats in this. It is derived, never set: `rib_thickness` is the
    # driver, because the rib is a ledge for the lip to sit on and not a plug for the
    # slot. Tying the two together is what drove the relief to 6.5mm once.
    leg_gap = item_depth - rib_thickness
    if relief_depth >= leg_gap:
        raise ValueError(
            f"relief_depth {relief_depth} is at or past the {leg_gap:.2f}mm leg gap, so "
            f"the rib's rear face would hang over the relief with nothing under it. "
            f"Drop relief_depth below {leg_gap:.2f}, or thin rib_thickness."
        )

    # What the relief left of the leg-pocket ledge. The structural chamfer lands on it,
    # and a chamfer needs strictly more face than it takes: measured here, it builds at
    # 3.249mm on a 3.25mm ledge and fails at 3.25 exactly, with no slack at all.
    ledge = leg_gap - relief_depth
    if structural_chamfer >= ledge:
        raise ValueError(
            f"a {structural_chamfer}mm chamfer at the rib root runs off a {ledge:.2f}mm "
            f"ledge into the relief. Drop structural_chamfer below {ledge:.2f}, "
            f"or shallow relief_depth."
        )

    # The rib top is polished on both its front and its rear edge, so it is the one face
    # on this part carrying two chamfers. Thinning the rib 5.5 -> 2.25 left 0.25mm of
    # flat between them: measured here, it builds with 0.002mm to spare and fails the
    # moment the two bands touch. Fusion never met this because it thinned the rib
    # without ever re-running the polish at a larger size.
    if 2 * chamfer_size >= rib_thickness:
        raise ValueError(
            f"a {chamfer_size}mm polish on both edges of a {rib_thickness}mm rib top "
            f"leaves no face between them. Drop chamfer_size below "
            f"{rib_thickness / 2:.3f}, or thicken rib_thickness past {2 * chamfer_size}."
        )

    need = BIN_LEG_LENGTH + structural_chamfer + RIB_MARGIN
    if rib_height < need:
        raise ValueError(
            f"rib_height {rib_height} is under the {need:.2f}mm a bin needs: "
            f"{BIN_LEG_LENGTH}mm of slot, {structural_chamfer}mm of chamfer at the root "
            f"and {RIB_MARGIN}mm spare. Raise rib_height to {need:.2f}."
        )

    if pad_width < CHANNEL_WIDTH:
        raise ValueError(
            f"pad_width {pad_width} is narrower than the {CHANNEL_WIDTH}mm dovetail, so "
            f"the back relief would cut into the channel. Raise it above {CHANNEL_WIDTH}."
        )

    y0 = -BLOCK_WIDTH / 2
    y1 = (bracket_count - 1) * bracket_step * BLOCK_WIDTH + BLOCK_WIDTH / 2

    # Plate and rib are one profile, not two bodies fused. The front face comes out as a
    # single unbroken plane from the rib top down to the bed, which is what the bin's
    # back wall bears on over the full 55mm, and there is no weld to keep track of.
    #
    # Everything above z=0 behind the rib is the leg pocket. There is nothing to model
    # there: the Wall Control sheet closes the back of it.
    section = Plane.XZ * Polygon(
        (0, 0),
        (-leg_gap, 0),
        (-leg_gap, rib_height),
        (-item_depth, rib_height),
        (-item_depth, -item_height),
        (0, -item_height),
        align=None,
    )
    body = Pos(0, (y0 + y1) / 2, 0) * extrude(section, (y1 - y0) / 2, both=True)

    body -= channels(bracket_count, item_height, bracket_step)
    body -= detent_dimples(bracket_count, bracket_step)

    # The back relief. Open at the top and running out through the bottom edge, so it has
    # no ceiling to bridge. It cuts the back because the front is the bearing plane.
    body -= Part() + [
        Pos((OVERSHOOT - relief_depth) / 2, (lo + hi) / 2, -item_height / 2)
        * Box(relief_depth + OVERSHOOT, hi - lo, item_height + 2 * OVERSHOOT)
        for lo, hi in _relief_bands(bracket_count, bracket_step, pad_width, y0, y1)
    ]

    # Face roles, read off the live parameters. Hardcoding the planes is what broke the
    # Fusion filter: thinning the rib moved its rear face from -3.25 to -6.5 and split it
    # from the relief's back face, and a frozen x value would have gone on matching
    # nothing in silence.
    def role(face):
        if face.geom_type != GeomType.PLANE:
            return None
        n, c = face.normal_at(face.center()), face.center()
        if n.Z > 0.999:
            if abs(c.Z - rib_height) < EPS:
                return "ribtop"
            if abs(c.Z) < EPS:
                return "platetop"
        elif n.X < -0.999 and abs(c.X + item_depth) < EPS:
            return "front"
        elif n.X > 0.999 and abs(c.X + leg_gap) < EPS:
            return "ribrear"
        elif abs(n.Y) > 0.999 and (abs(c.Y - y0) < EPS or abs(c.Y - y1) < EPS):
            return "side"
        return None

    def wanted(shape, allowed):
        out = []
        for edge, faces in _touching(shape):
            if len(faces) != 2:
                continue  # a seam, with nothing on the far side to pair with
            if {role(f) for f in faces} in allowed:
                out.append((edge, faces))
        return out

    # Structural, 2mm and not the family's 3mm: the rib root is one continuous concave
    # edge and the ledge behind it is only as wide as the relief left it.
    root = wanted(body, STRUCTURAL)
    if not root:
        raise ValueError(
            "no rib root to relieve: nothing matched ribrear against platetop. The face "
            "roles have drifted from the geometry, which is how this fails silently."
        )
    if any(is_convex(edge, *faces) for edge, faces in root):
        raise ValueError("the rib root came back convex, so the roles are inside out")
    body = chamfer([edge for edge, _ in root], structural_chamfer)
    if draft:
        return body

    # Cosmetic, 1mm on four face pairs and nothing else. The structural chamfer has
    # already moved the topology, so the roles get read again against the new body; the
    # 45 degree face it left has no role, so its edges cannot land in this set.
    polish = wanted(body, COSMETIC)
    if not polish:
        raise ValueError(
            "the polish pass matched no edges, so the face roles no longer describe "
            "this geometry. Check `role` against the current parameters."
        )
    if not all(is_convex(edge, *faces) for edge, faces in polish):
        raise ValueError("the polish set contains a concave edge, which would wedge")
    return polish_pass(body, [edge for edge, _ in polish], chamfer_size)
