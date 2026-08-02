---
name: changelog
description: Write nurb.dev changelog entries from the releases since the last published one. Filters the release's merged PRs to what a user would actually notice, drafts each in the site's voice, and inserts the release into site/changelog.html. Use when the user says "changelog", "update the changelog", "announce this", or after cutting a release.
---

# nurb changelog

One surface: `site/changelog.html`, the static page behind nurb.dev/changelog. One `<article class="release">` per released version, newest first. There is no build step and no data file; the HTML is the data.

Releases are the unit. A nurb release is a version bump merged to main; the publish workflow tags it and creates a GitHub release whose generated notes list the merged PRs. The changelog entry for a version is written from those PRs, filtered hard.

## Step 1: Find the gap

The newest `id="vX.Y.Z"` in `site/changelog.html` is the high-water mark.

```bash
grep -m1 'id="v' site/changelog.html
gh release list --limit 20
```

Every tagged release newer than the high-water mark needs an entry. If the user describes a feature in free text instead, write that one entry into the version it shipped in (or the pending version if it hasn't shipped yet) and skip the sweep.

For each missing version:

```bash
gh release view vX.Y.Z --json publishedAt,body
```

The body lists the PRs. Read a PR (`gh pr view N`) whenever its title alone doesn't tell you what a user would notice.

## Step 2: Filter to what earns a line

Most PRs are not changelog lines. A PR earns one only if **someone using nurb could notice the difference without reading the code.**

Yes: a new capability in the viewer or the modeling vocabulary, a new check, a behavior change they'd feel, a fix for something that visibly broke, a change to how their AI works with them (asks for measurements, names sliders in their words).

No: CI, tests, refactors, repo docs, CLAUDE.md, release plumbing, skill-file mechanics with no visible effect, marketing site tweaks.

Group by capability, not by PR. Several PRs polishing one feature collapse into one line. A version whose every PR is internal gets no entry at all; say so in the report rather than padding.

## Step 3: Draft the copy

The audience is a hobbyist with a printer, not a programmer. They talk to their AI and judge parts in a browser.

- Never mention Python, module names, function names, build123d, OCCT, or agent-harness jargon. `stand()` is "diagonal printing"; `nurb inspect` is "your AI can inspect a part".
- "Your AI" is the actor for agent-side changes, matching the landing page.
- Sentence case, second person, plain English. Say what changed and what they can now do, then stop. No rationale, no design defense.
- No em-dashes, no exclamation points, no emoji, no marketing fluff.
- Each line gets a tag: `new`, `improved`, or `fixed`. Only `new` also carries the class (`<b class="tag new">`); the other two are `<b class="tag">improved</b>` and `<b class="tag">fixed</b>`.
- A headline capability may lead its line with a bold two-or-three-word name: `<b>Assemblies.</b>`.

## Step 4: Write the page

Insert the new `<article class="release" id="vX.Y.Z">` at the **top** of `<main>`, right after the `.lede` paragraph. Copy the markup shape of the entry below it exactly:

```html
<article class="release" id="v0.9.0">
  <div class="meta"><span class="ver"><a href="https://github.com/Shpigford/nurb/releases/tag/v0.9.0">v0.9.0</a></span><time datetime="2026-07-31">July 31, 2026</time></div>
  <ul>
    <li><b class="tag new">new</b><span><b>Diagonal printing.</b> A part that prints better tilted...</span></li>
    <li><b class="tag">fixed</b><span>...</span></li>
  </ul>
</article>
```

The date is the release's `publishedAt` date, not today. Never reword or delete an already-published entry; its `id` is a live anchor.

## Step 5: Verify

Look at the page, don't just lint it: serve `site/` (`python3 -m http.server 7878 -d site`), open `http://localhost:7878/changelog.html` with whatever browser tooling is available, and screenshot it. Check the new entry renders like its neighbors, then kill the server. Also, silence is pass on both of these:

```bash
git diff -U0 site/changelog.html | grep '^+.*—'   # em-dashes in what you added
grep -o 'id="v[0-9.]*"' site/changelog.html | uniq -d  # duplicate versions
```

And confirm by eye that versions still descend down the page.

## Step 6: Report

List each version with its lines and tags, plus one line for what was skipped and why. Leave the change uncommitted unless asked.
