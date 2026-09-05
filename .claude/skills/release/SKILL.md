---
name: release
description: Cut a full nurb release, one version across the engine and the desktop app. Bumps the four version strings and writes the changelog into one release PR, riding the current branch when work is in flight, then after the merge runs the desktop build and the update feed. Use when the user says "release", "cut a release", "ship it as X.Y.Z", or "push a release".
---

# Releasing nurb

One release ships everything under one version: the PyPI package, the signed DMG, the in-app update feed, and the site changelog. This skill runs the whole ceremony. The one human act left in it is merging the bump PR, and that merge is the user approving the release.

## Step 0: Preflight

All of these must pass before touching anything. If one fails, say which and stop.

```bash
gh auth status
test -f desktop/.env
test -f ~/.tauri/nurb-desktop.key
security find-identity -v -p codesigning | grep -q "Developer ID Application"
git fetch origin main
```

The updater key check matters most: without `~/.tauri/nurb-desktop.key` shipped apps cannot update, and generating a fresh key would strand every existing install. If it is missing, stop and tell the user; never regenerate it.

Start from up-to-date origin/main. One PR is the release: if the current branch has work in flight, the bump and changelog ride that branch and its PR becomes the release PR. Only cut a fresh branch when the workspace is clean and the release is just collecting already-merged work.

## Step 1: Pick the version

If the user named a version, use it. Otherwise decide and propose one: read what's merged since the last release, recommend a minor bump for new capabilities and a patch for fixes-and-polish-only, and say why in one line. The PR is the proposal; merging it is the user's yes.

```bash
gh release list --limit 5
gh pr list --state merged --base main --limit 50 --json title,mergedAt
```

## Step 2: The release PR

Four version strings move together, and tests enforce every pairing:

```bash
uv version X.Y.Z
```

then the `version:` frontmatter line in `src/nurb/skill.md` and `skills/nurb/SKILL.md`, then `version` in `desktop/src-tauri/tauri.conf.json`.

Then write the changelog into the same PR: run /changelog for the pending version. Pre-merge there is no tag or GitHub release yet, so it draws from the PRs merged since the last release plus this branch's own changes, dated today.

Prove the agreement before pushing: `uv run pytest tests/test_cli.py -q`. Commit the bump and the changelog together with a plain-sentence message, push, and open the PR against main with the release summary as the body (what shipped, in user-visible terms). Then stop and hand the merge to the user.

## Step 3: After the merge

publish.yml reacts to the merge on its own: PyPI upload, tag `vX.Y.Z`, GitHub release with generated notes. Do not wait for it; start the desktop half immediately, because it builds while publish.yml runs and then waits for the release before uploading:

```bash
cd desktop && scripts/release.sh
```

A fresh worktree has no `desktop/node_modules`, and the script dies immediately with `tauri: command not found`. Run `npm ci` in `desktop/` first if it is missing.

About ten minutes: signed build, notarization, stapling, chain verification, upload of `nurb.dmg` plus the updater archive into the `vX.Y.Z` release, and the `desktop-latest` feed refresh. It refuses to double-upload, so re-running after a failure is safe. It needs this Mac; the signing cert and updater key live here by design.

The Linux packages need no machine of yours. `.github/workflows/desktop-linux.yml` starts when publish.yml finishes, and runs `scripts/release-linux.sh` on a 22.04 runner per architecture: the `.deb` and the AppImage for x86_64 and aarch64, into the same `vX.Y.Z` release. It takes about fifteen minutes for both. Watch it with `gh run list --workflow desktop-linux.yml --limit 3`, and re-run the workflow if an architecture failed: it asks the release what is missing and builds only that.

Order against the Mac does not matter: both platforms merge their own half into `latest.json` through `scripts/feed.py` instead of overwriting it, and take a lock on the feed release while they do. What does matter is that both run for the same version, since the merge drops entries belonging to an older one rather than offer an update that hands the user the previous build. A release where only one platform ran is fine and simply carries that platform, but say so in the report.

## Step 4: Verify, then report

Expose the current tag's assets and the feed's platform keys before calling the release complete:

```bash
gh release view vX.Y.Z --json assets -q '.assets[].name' | sort
curl -sfL https://github.com/Shpigford/nurb/releases/download/desktop-latest/latest.json | python3 -c 'import json,sys; feed=json.load(sys.stdin); print(feed["version"]); print("\n".join(sorted(feed["platforms"])))'
curl -sfI https://github.com/Shpigford/nurb/releases/latest/download/nurb.dmg | head -1
curl -sf https://pypi.org/pypi/nurb/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
```

The feed and PyPI probes must say X.Y.Z. If the Mac half ran, the tag must carry both DMGs plus both `.app.tar.gz` archives and signatures, the feed must carry `darwin-aarch64` and `darwin-x86_64`, and the DMG probe must return a redirect or 200. If the Linux x86_64 half ran, the tag must carry `nurb_x86_64.deb`, `nurb_x86_64.deb.sig`, `nurb-x86_64.AppImage`, and `nurb-x86_64.AppImage.sig`, and the feed must carry `linux-x86_64` and `linux-x86_64-deb`; substitute `aarch64` for an ARM release. A deliberately one-sided release is valid only when every artifact and feed key for the half that ran is present, and the report explicitly names the half that was skipped. A missing artifact or key from a half that ran is a failed release, not a one-sided one.

Once PyPI shows the new version, relock the benchmark so future runs grade the new engine: in a checkout of [Shpigford/nurb-benchmarks](https://github.com/Shpigford/nurb-benchmarks), `uv lock` and a small PR with the lockfile change. Rows keep their identity through `benchmark_revision`, so this is routine, not a reset.

Report with the release URL and what is now true: package users get the new version from `nurb update` and the viewer's nudge, desktop users see the one-click update at next launch, and the site's changelog names what changed. If any probe disagrees, say which channel is not live yet instead of calling the release done.
