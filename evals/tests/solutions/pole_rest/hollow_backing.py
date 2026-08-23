"""Two thin radial skins connected only at the base: contact and backing probes
both hit material, but an air gap separates them around the support arc."""

from nurb import *


@part
def pole_rest(pole_diameter=22.0):
    length, axis_h = 20.0, 18.0
    r = pole_diameter / 2 + 0.2
    inner = Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r + 0.3, length)
    inner -= Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r, length + 2)
    outer = Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r + 1.5, length)
    outer -= Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r + 1.2, length + 2)
    cutoff = axis_h - 0.34 * r
    clip = Pos(0, 0, cutoff / 2) * Box(2 * (r + 2), length + 2, cutoff)
    base_top = axis_h - r - 0.25
    base = Pos(0, 0, base_top / 2) * Box(16.0, length, base_top)
    return (inner & clip) + (outer & clip) + base
