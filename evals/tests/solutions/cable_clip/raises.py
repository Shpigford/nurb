"""Flawed: never builds at all."""

from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    raise ValueError("cable_clip: refusing to build")
