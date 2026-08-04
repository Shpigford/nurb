"""Flawed: never returns. Only the subprocess timeout can catch this one."""

from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    while True:
        pass
