// Nucleo outline icons, stroke style matching the site's marks (1.5 stroke,
// round caps, currentColor).
const strokeProps = {
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  strokeWidth: 1.5,
} as const;

export function IconFolder({ size = 12 }: { size?: number }) {
  return (
    <svg className="row-icon" width={size} height={size} viewBox="0 0 12 12" aria-hidden="true">
      <g {...strokeProps}>
        <path d="m.75,7.25V3.25c0-1.105.895-2,2-2h1.701c.607,0,1.18.275,1.56.748l.603.752h2.636c1.105,0,2,.895,2,2v2.5" />
        <path d="m2.75,5.25h6.5c1.105,0,2,.895,2,2v1.5c0,1.105-.895,2-2,2H2.75c-1.105,0-2-.895-2-2v-1.5c0-1.105.895-2,2-2Z" />
      </g>
    </svg>
  );
}

export function IconFolderPlus({ size = 13 }: { size?: number }) {
  return (
    <svg className="row-icon" width={size} height={size} viewBox="0 0 18 18" aria-hidden="true">
      <g {...strokeProps}>
        <path d="M2.25 8.75V4.75C2.25 3.645 3.145 2.75 4.25 2.75H6.201C6.808 2.75 7.381 3.02499 7.761 3.49799L8.364 4.25H13.75C14.855 4.25 15.75 5.145 15.75 6.25V9.09399" />
        <path d="M14.75 12.25V17.25" />
        <path d="M15.75 9.42221V8.75C15.75 7.646 14.855 6.75 13.75 6.75H4.25C3.145 6.75 2.25 7.646 2.25 8.75V13.25C2.25 14.354 3.145 15.25 4.25 15.25H9.2919" />
        <path d="M17.25 14.75H12.25" />
      </g>
    </svg>
  );
}

export function IconMessagePlus({ size = 12 }: { size?: number }) {
  return (
    <svg className="row-icon" width={size} height={size} viewBox="0 0 18 18" aria-hidden="true">
      <g {...strokeProps}>
        <path d="M13.75 11.25V16.25" />
        <path d="M16.25 13.75H11.25" />
        <path d="M16.25 9.62671V4.25C16.25 3.146 15.355 2.25 14.25 2.25H3.75C2.645 2.25 1.75 3.146 1.75 4.25V11.25C1.75 12.354 2.645 13.25 3.75 13.25H5.75V16.25L8.29269 14.2158" />
      </g>
    </svg>
  );
}

// The assembly mark, the same three cubes the viewer's own list uses. Unlike the
// other icons it carries a label: it is the only thing on the row saying that this
// is placed parts rather than one solid, so hiding it from the AX tree would hide
// the distinction entirely.
export function IconCubes({ size = 13, label }: { size?: number; label?: string }) {
  return (
    <svg
      className="row-icon"
      width={size}
      height={size}
      viewBox="0 0 18 18"
      role="img"
      aria-label={label ?? "assembly"}
    >
      <g {...strokeProps}>
        <path d="M4.648,8.086l-2.55,1.479c-.37,.215-.598,.61-.598,1.038v2.968c0,.428,.228,.823,.598,1.038l2.55,1.479c.372,.216,.832,.216,1.204,0l2.55-1.479c.37-.215,.598-.61,.598-1.038v-2.968c0-.428-.228-.823-.598-1.038l-2.55-1.479c-.372-.216-.832-.216-1.204,0Z" />
        <polyline points="8.84 10.005 5.25 12.087 1.66 10.005" />
        <line x1="5.25" y1="16.25" x2="5.25" y2="12.087" />
        <path d="M12.148,8.086l-2.55,1.479c-.37,.215-.598,.61-.598,1.038v2.968c0,.428,.228,.823,.598,1.038l2.55,1.479c.372,.216,.832,.216,1.204,0l2.55-1.479c.37-.215,.598-.61,.598-1.038v-2.968c0-.428-.228-.823-.598-1.038l-2.55-1.479c-.372-.216-.832-.216-1.204,0Z" />
        <polyline points="16.34 10.005 12.75 12.087 9.16 10.005" />
        <line x1="12.75" y1="16.25" x2="12.75" y2="12.087" />
        <path d="M8.398,1.586l-2.55,1.479c-.37,.215-.598,.61-.598,1.038v2.968c0,.428,.228,.823,.598,1.038l2.55,1.479c.372,.216,.832,.216,1.204,0l2.55-1.479c.37-.215,.598-.61,.598-1.038v-2.968c0-.428-.228-.823-.598-1.038l-2.55-1.479c-.372-.216-.832-.216-1.204,0Z" />
        <polyline points="12.59 3.505 9 5.587 5.41 3.505" />
        <line x1="9" y1="9.75" x2="9" y2="5.587" />
      </g>
    </svg>
  );
}

export function IconPaperclip({ size = 14 }: { size?: number }) {
  return (
    <svg className="row-icon" width={size} height={size} viewBox="0 0 18 18" aria-hidden="true">
      <g {...strokeProps}>
        <path d="M15.1 8.65l-5.63 5.63a3.5 3.5 0 0 1-4.95-4.95l6.01-6.01a2.333 2.333 0 0 1 3.3 3.3l-5.83 5.83a1.167 1.167 0 0 1-1.65-1.65l5.3-5.3" />
      </g>
    </svg>
  );
}

export function IconCheck({ size = 11, className }: { size?: number; className?: string }) {
  return (
    <svg
      className={className ?? "row-icon"}
      width={size}
      height={size}
      viewBox="0 0 18 18"
      aria-hidden="true"
    >
      <g {...strokeProps}>
        <polyline points="3 9.75 6.75 13.5 15 4.5" />
      </g>
    </svg>
  );
}

export function IconChevronDown({ size = 10 }: { size?: number }) {
  return (
    <svg className="row-icon" width={size} height={size} viewBox="0 0 18 18" aria-hidden="true">
      <g {...strokeProps}>
        <polyline points="3.75 6.75 9 12 14.25 6.75" />
      </g>
    </svg>
  );
}

// The viewer's sliders glyph for a variant: the same part at other values.
export function IconVariant({ size = 11 }: { size?: number }) {
  return (
    <svg className="row-icon" width={size} height={size} viewBox="0 0 12 12" aria-hidden="true">
      <g {...strokeProps}>
        <line x1="11.25" y1="8.75" x2="6.25" y2="8.75" />
        <circle cx="4.25" cy="8.75" r="2" />
        <line x1="2.25" y1="8.75" x2=".75" y2="8.75" />
        <line x1=".75" y1="3.25" x2="5.75" y2="3.25" />
        <circle cx="7.75" cy="3.25" r="2" />
        <line x1="9.75" y1="3.25" x2="11.25" y2="3.25" />
      </g>
    </svg>
  );
}

export function IconCube({ size = 12 }: { size?: number }) {
  return (
    <svg className="row-icon" width={size} height={size} viewBox="0 0 18 18" aria-hidden="true">
      <g {...strokeProps}>
        <polyline points="14.983 5.53 9 9 3.017 5.53" />
        <line x1="9" y1="15.938" x2="9" y2="9" />
        <path d="M7.997,2.332L3.747,4.797c-.617,.358-.997,1.017-.997,1.73v4.946c0,.713,.38,1.372,.997,1.73l4.25,2.465c.621,.36,1.386,.36,2.007,0l4.25-2.465c.617-.358,.997-1.017,.997-1.73V6.527c0-.713-.38-1.372-.997-1.73l-4.25-2.465c-.621-.36-1.386-.36-2.007,0Z" />
      </g>
    </svg>
  );
}
