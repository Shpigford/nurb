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

The bump also stales `evals/uv.lock`, because evals is its own uv project with nurb as an editable path dependency and CI syncs it with `--locked`. Relock it and commit the one-line change with the bump:

```bash
cd evals && uv lock && cd ..
```

Then write the changelog into the same PR: run /changelog for the pending version. Pre-merge there is no tag or GitHub release yet, so it draws from the PRs merged since the last release plus this branch's own changes, dated today.

Prove the agreement before pushing: `uv run pytest tests/test_cli.py -q`. Commit the bump and the changelog together with a plain-sentence message, push, and open the PR against main with the release summary as the body (what shipped, in user-visible terms). Then stop and hand the merge to the user.

## Step 3: After the merge

publish.yml reacts to the merge on its own: PyPI upload, tag `vX.Y.Z`, GitHub release with generated notes. Do not wait for it; start the desktop half immediately, because it builds while publish.yml runs and then waits for the release before uploading:

```bash
cd desktop && scripts/release.sh
```

A fresh worktree has no `desktop/node_modules`, and the script dies immediately with `tauri: command not found`. Run `npm ci` in `desktop/` first if it is missing.

About ten minutes: signed build, notarization, stapling, chain verification, upload of `nurb.dmg` plus the updater archive into the `vX.Y.Z` release, and the `desktop-latest` feed refresh. It refuses to double-upload, so re-running after a failure is safe. It needs this Mac; the signing cert and updater key live here by design.

## Step 4: Verify, then report

Three probes, all of which must say X.Y.Z (the DMG check must return a redirect or 200):

```bash
curl -sfI https://github.com/Shpigford/nurb/releases/latest/download/nurb.dmg | head -1
curl -sfL https://github.com/Shpigford/nurb/releases/download/desktop-latest/latest.json | python3 -c "import json,sys; print(json.load(sys.stdin)['version'])"
curl -sf https://pypi.org/pypi/nurb/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
```

Report with the release URL and what is now true: package users get the new version from `nurb update` and the viewer's nudge, desktop users see the one-click update at next launch, and the site's changelog names what changed. If any probe disagrees, say which channel is not live yet instead of calling the release done.
