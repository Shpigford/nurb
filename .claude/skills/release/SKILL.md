---
name: release
description: Cut a full nurb release, one version across the engine and the desktop app. Bumps every version and workspace pin and writes the changelog into one release PR, riding the current branch when work is in flight, then after the merge runs the desktop build and uploads the DMGs and the update feed to GitHub Releases. Use when the user says "release", "cut a release", "ship it as X.Y.Z", or "push a release".
---

# Releasing nurb

One release ships everything under one version: the signed DMGs, the in-app update feed, and the site changelog. The engine is not published on its own; the app bundles its wheel, so the `vX.Y.Z` GitHub release carries the DMGs and the updater archives, and the rolling `desktop-latest` prerelease carries the `latest.json` installed apps poll. This skill runs the whole ceremony. The one human act left in it is merging the bump PR, and that merge is the user approving the release.

## Step 0: Preflight

All of these must pass before touching anything. If one fails, say which and stop.

```bash
gh auth status
test -f desktop/.env
test -f ~/.tauri/nurb-desktop.key
security find-identity -v -p codesigning | grep -q "Developer ID Application"
command -v shlock
git fetch origin main --tags
```

The updater key check matters most: without `~/.tauri/nurb-desktop.key` shipped apps cannot update, and generating a fresh key would strand every existing install. If it is missing, stop and tell the user; never regenerate it. The `gh` login must be able to write to Shpigford/nurb; the script checks that before it builds.

Start from up-to-date origin/main. One PR is the release: if the current branch has work in flight, the bump and changelog ride that branch and its PR becomes the release PR. Only cut a fresh branch when the workspace is clean and the release is just collecting already-merged work.

## Step 1: Pick the version

If the user named a version, use it. Otherwise decide and propose one: read what's merged since the last tag, recommend a minor bump for new capabilities and a patch for fixes-and-polish-only, and say why in one line. The PR is the proposal; merging it is the user's yes.

```bash
gh release list --limit 5
gh pr list --state merged --base main --limit 50 --json title,mergedAt
```

Versions are PEP 440 in `engine/pyproject.toml` and SemVer everywhere else: `1.0.0a1` there is `1.0.0-alpha.1` in the app. A prerelease such as `1.0.0b1` is `1.0.0-beta.1` in the app, and its git tag keeps the PEP 440 spelling (`v1.0.0b1`).

## Step 2: The release PR

Three shipped versions and the two exact workspace pins move together; tests enforce the whole set:

```bash
cd engine && uv version X.Y.Z
```

then, using the SemVer spelling:

- `version` in `desktop/src-tauri/tauri.conf.json`
- `version` in `packages/ui/package.json`
- `@nurb/ui` in `desktop/package.json`
- `@nurb/ui` in `packages/workbench/package.json`

Run `npm install --package-lock-only` at the repository root after those edits, so `package-lock.json` records the new package version and both pins. A stale exact pin makes a clean `npm ci` look for the unpublished package on npm instead of linking the workspace.

Then write the changelog into the same PR: run /changelog for the pending version. Pre-merge there is no tag yet, so it draws from the PRs merged since the last tag plus this branch's own changes, dated today.

Refresh the site's hero in the same PR: `npm run site:hero --workspace packages/ui`. It draws the `hero` sheet in `packages/ui/gallery/sheets.tsx` from the components the app ships and writes `site/app.jpg`, so nurb.dev shows the app as it is in this release. Look at `site/app.jpg` before committing it. If the part, the conversation or the numbers on that sheet no longer match what the app does, fix the sheet, not the image.

Prove the agreement before pushing: `cd engine && uv run pytest tests/test_version.py -q`, then run `npm ci --ignore-scripts` at the repository root to prove a clean workspace install. Commit the bump, lockfile, changelog and hero images together with a plain-sentence message, push, and open the PR against main with the release summary as the body (what shipped, in user-visible terms). Then stop and hand the merge to the user.

## Step 3: After the merge

Check out the merged main, then run the desktop half:

```bash
RELEASE_ROOT="${CONDUCTOR_ROOT_PATH:-$(git rev-parse --show-toplevel)}"
git -C "$RELEASE_ROOT" checkout main
git -C "$RELEASE_ROOT" pull --ff-only origin main
(cd "$RELEASE_ROOT/desktop" && scripts/release.sh)
```

In Conductor, `CONDUCTOR_ROOT_PATH` selects the repository's main checkout; do not try to check out `main` inside the workspace worktree because Git already has that branch checked out there.

A fresh worktree has no `desktop/node_modules`, and the script dies immediately with `tauri: command not found`. Run `npm ci` at the repo root first if it is missing.

About fifteen minutes: signed builds for Apple silicon and Intel, notarization, stapling, chain verification, then the `v<engine version>` git tag pushed to origin, a draft `vX.Y.Z` release with `nurb.dmg`, `nurb-intel.dmg`, both updater archives and their signatures, the release published as Latest, and `latest.json` uploaded to `desktop-latest`. The draft keeps the site's download links on the previous release until every file is up. Re-running resumes an unpublished draft; once the release is published or the version is in the feed, it refuses to upload twice, and a missing artifact under a live version is a hard stop rather than an in-place repair. A machine-local lock serializes releases on this Mac, and the feed is rechecked after the build before anything uploads. It needs this Mac; the signing cert and updater key live here by design.

## Step 4: Verify, then report

Three probes. The two downloads must return a redirect, and the feed must say X.Y.Z:

```bash
curl -sI https://github.com/Shpigford/nurb/releases/latest/download/nurb.dmg | head -1
curl -sI https://github.com/Shpigford/nurb/releases/latest/download/nurb-intel.dmg | head -1
curl -sL https://github.com/Shpigford/nurb/releases/download/desktop-latest/latest.json | python3 -c "import json,sys; print(json.load(sys.stdin)['version'])"
```

Report with the release URL and what is now true: desktop users see the one-click update at next launch, new downloads from the site carry the new version, and the site's changelog names what changed. If any probe disagrees, say which channel is not live yet instead of calling the release done.
