"""Lightweight console entry point for commands that do not need OCCT."""

import importlib.metadata
import sys


def _version():
    try:
        return importlib.metadata.version("nurb")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--version"]:
        print(f"nurb {_version()}")
        return

    # Importing the package loads build123d and OCCT. Every real command needs
    # them; the diagnostic version path above deliberately does not.
    from nurb.cli import main as cli_main

    return cli_main(args)
