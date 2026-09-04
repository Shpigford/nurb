#!/usr/bin/env python3
"""Merge one platform's entries into the desktop updater feed.

The Mac release script and the Windows CI job each build their own installers
and each finish at their own pace, but installed apps poll a single
latest.json. Whichever side finishes writes the feed by merging its platform
keys into the current one: entries from the same version are kept, an older
feed is replaced outright. Version-aware merging is what makes the order of
the two publishers irrelevant.
"""

import argparse
import datetime
import json
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--existing",
        help="path to the currently published latest.json; missing or unreadable means start fresh",
    )
    parser.add_argument(
        "--platform",
        nargs=3,
        action="append",
        required=True,
        metavar=("KEY", "SIGNATURE", "URL"),
        help="an updater platform entry, e.g. windows-x86_64 <minisign signature> <asset url>",
    )
    args = parser.parse_args()

    platforms = {}
    if args.existing:
        try:
            with open(args.existing, encoding="utf-8") as handle:
                current = json.load(handle)
            if current.get("version") == args.version:
                platforms.update(current.get("platforms", {}))
        except (OSError, ValueError):
            pass
    for key, signature, url in args.platform:
        platforms[key] = {"signature": signature, "url": url}

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    json.dump(
        {"version": args.version, "pub_date": stamp, "platforms": platforms},
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
