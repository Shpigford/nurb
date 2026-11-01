# @nurb/ui

The React components the nurb workbench is made of: the three.js viewer, the cards a build, a spec and a measurement render as, the icons, the assistant's markdown renderer, and the formatters that write every figure. One copy, shared by the desktop app (`desktop/`) and the workbench page the engine serves (`packages/workbench/`), so a card never drifts between them.

Components carry Tailwind 4 utility classes as literal strings and never import CSS, so the consuming app owns the build.

## Using it

The package is private to this repository and is not published to npm. The two apps depend on it through the npm workspace at the repository root.

React 19, React DOM 19 and `three` 0.185 are peer dependencies. The viewer imports `three/addons/controls/OrbitControls.js` and `three/addons/loaders/GLTFLoader.js`, so the consumer's bundler has to resolve `three/addons/*` (any bundler reading the package's export map does).

## Tailwind

The package ships `tokens.css`: the `@theme` block, the utilities (`panel`, `mono-label`, `mono-value`, `btn-label`, and the rest), the streaming caret, and the reduced-motion guard. Import it after Tailwind, and point Tailwind's scanner at the built components so the classes they name survive a production build.

```css
@import "tailwindcss";
@import "@nurb/ui/tokens.css";

@source "../node_modules/@nurb/ui/dist";
```

Adjust that `@source` path to reach `node_modules` from your CSS file.

## Fonts

Instrument Sans and JetBrains Mono ship inside the package under the SIL Open Font License (see `fonts/OFL.txt`), and `tokens.css` declares them.

Satoshi is the display face, but its Fontshare license keeps it out of a public repository (see `fonts/SATOSHI-LICENSE.md`). `npm run fonts:fetch` downloads your own copy into `fonts/`, and the workbench and desktop builds and the gallery screenshots run it first. Without it the display face falls back to Instrument Sans.

## Gallery

`npm run gallery` serves every component on fixture data: the cards in the 372px chat column they really live in, and the viewer on real GLBs at 640px. It is the fastest way to see a change.

## Panels

`ParamsPanel` takes the part's `params` (the keyword defaults, with `kind` telling an int from a float) and the session `values`, and calls `onChange` with the whole map on every edit so the host can rebuild. Apply calls `onApply` with only the values that differ from the defaults; the host writes those into the part and passes the new defaults back, which is what clears the change bar. `ExportMenu` takes an `export(format, profile)` promise and shows the preparing row until it settles, then a link to the file; `status` carries the slicer estimate once the host has one. Neither talks to a server.

## Viewer

`ViewerIsland` draws one part: pass `glbUrl` and it frames the part on first load, then keeps the camera across every later swap while the part is still in view. Key the mount per part and hand the last `onCamera` state back as `camera` to restore a view. `findings` with face triangles glow on the solid and `highlight` outlines one of them; `section` cuts along an axis with a capped face; `targetUrl` draws a translucent reference mesh; `bed` draws the printer plate.
