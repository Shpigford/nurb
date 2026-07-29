# three.js, vendored

three.js r169 (npm `three@0.169.0`), MIT, see `LICENSE`.

Here rather than on a CDN because a CAD tool that needs the network is broken on a
plane, and because `nurb render` drives this same page: without the network it used to
serve the viewer, load the canvas, and then draw nothing at all, forever.

Copied verbatim from the npm tarball, with one comment-only exception noted below:

| here | from `three@0.169.0` |
|---|---|
| `build/three.module.min.js` | `build/three.module.min.js` |
| `addons/controls/OrbitControls.js` | `examples/jsm/controls/OrbitControls.js` |
| `addons/loaders/GLTFLoader.js` | `examples/jsm/loaders/GLTFLoader.js` |
| `addons/utils/BufferGeometryUtils.js` | `examples/jsm/utils/BufferGeometryUtils.js` |
| `LICENSE` | `LICENSE` |

`BufferGeometryUtils` is not imported by the viewer. `GLTFLoader` imports it, and
leaving it out is a 404 that only shows up when a model loads.

The one deviation: four upstream comments in `GLTFLoader.js` (near `resourcePath`, around line 199) used a made-up personal-CDN domain as a placeholder URL, and security scanners auditing the repo flagged that unregistered domain as a suspicious download source (Snyk marked the nurb skill CRITICAL on skills.sh over it, GitHub issue #34). The comments here say `example.com` instead. Re-apply this when vendoring a new version if upstream still has its own placeholder.

The build is minified and the addons are not, because that is how the package ships
them. The `@license` header at the top of the minified build is part of the licence
condition and stays.

To move to another version, take the same five files from that version's tarball and
check the import graph has not grown: r171 split `three.core.js` out of
`three.module.js`, and later releases add `addons/utils/SkeletonUtils.js` to what
`GLTFLoader` imports. Both are files that must be copied too, and both fail as a blank
canvas rather than as an error.
