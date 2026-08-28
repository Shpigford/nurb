"""Write the updater feed, merging the platforms already published into it.

The two release scripts run on different machines: release.sh builds the macOS
slices on a Mac, release-linux.sh builds the Debian and AppImage packages on a
Linux box. Both publish one latest.json, so whichever ran second used to erase
the other's entries and silently strip a whole platform from the update feed.

Merging fixes that, but only within one version. The engine and the app ship as
a single version, so a feed that claims 0.24.0 while still pointing Linux at
0.23.0's AppImage would offer every Linux user an update that hands them the
old build. When the published feed names a different version its entries are
stale by definition and get dropped: a platform that has not been released yet
is better off seeing no update than the wrong one.
"""

import argparse
import datetime
import json
import pathlib
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", required=True, help="the version being released")
    p.add_argument("--current", help="latest.json as currently published, if any")
    p.add_argument("--out", required=True, help="where to write the merged feed")
    p.add_argument(
        "--platform",
        action="append",
        default=[],
        metavar="NAME=URL=SIGFILE",
        help="a platform to add, e.g. linux-x86_64=https://...tar.gz=path/to/.sig",
    )
    args = p.parse_args()

    platforms = {}
    if args.current:
        current = pathlib.Path(args.current)
        if current.is_file() and current.stat().st_size:
            try:
                published = json.loads(current.read_text())
            except json.JSONDecodeError as exc:
                sys.exit(f"{current} is not readable as JSON: {exc}")
            if published.get("version") == args.version:
                platforms = published.get("platforms", {})
            else:
                was = published.get("version", "an unnamed version")
                print(f"  the published feed is {was}, so its platforms are stale and dropped")

    for entry in args.platform:
        name, _, rest = entry.partition("=")
        url, _, signature = rest.partition("=")
        if not (name and url and signature):
            sys.exit(f"--platform wants NAME=URL=SIGFILE, got {entry!r}")
        sig = pathlib.Path(signature)
        if not sig.is_file():
            sys.exit(f"no signature at {sig}. Did the build write an updater artifact?")
        platforms[name] = {"signature": sig.read_text().strip(), "url": url}

    if not platforms:
        sys.exit("refusing to write a feed with no platforms in it")

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    feed = {"version": args.version, "pub_date": stamp, "platforms": platforms}
    pathlib.Path(args.out).write_text(json.dumps(feed, indent=2) + "\n")
    print(f"  feed carries: {', '.join(sorted(platforms))}")


if __name__ == "__main__":
    main()
