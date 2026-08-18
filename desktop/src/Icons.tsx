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

export function IconGear({ size = 14 }: { size?: number }) {
  return (
    <svg className="row-icon" width={size} height={size} viewBox="0 0 18 18" aria-hidden="true">
      <g {...strokeProps}>
        <path d="M9 11.2495C10.2426 11.2495 11.25 10.2422 11.25 8.99951C11.25 7.75687 10.2426 6.74951 9 6.74951C7.75736 6.74951 6.75 7.75687 6.75 8.99951C6.75 10.2422 7.75736 11.2495 9 11.2495Z" />
        <path d="M16.25 9.35449V8.6445C16.25 8.1345 15.867 7.70651 15.36 7.65051L14.266 7.5285L13.763 6.31451L14.451 5.45551C14.769 5.05751 14.738 4.4845 14.377 4.1235L13.875 3.62149C13.515 3.26149 12.941 3.22949 12.543 3.54749L11.684 4.2355L10.47 3.73251L10.348 2.63849C10.292 2.13249 9.86405 1.7485 9.35405 1.7485H8.64405C8.13405 1.7485 7.70605 2.13149 7.65005 2.63849L7.52805 3.73251L6.31404 4.2355L5.45505 3.54849C5.05705 3.23049 4.48405 3.2615 4.12305 3.6225L3.62104 4.12451C3.26104 4.48451 3.22905 5.05851 3.54705 5.45651L4.23505 6.31549L3.73204 7.52951L2.63805 7.65149C2.13205 7.70749 1.74805 8.13551 1.74805 8.64551V9.3555C1.74805 9.8655 2.13105 10.2935 2.63805 10.3495L3.73204 10.4715L4.23505 11.6855L3.54805 12.5445C3.23005 12.9425 3.26105 13.5165 3.62205 13.8765L4.12405 14.3785C4.48405 14.7385 5.05805 14.7705 5.45605 14.4525L6.31504 13.7645L7.52905 14.2675L7.65105 15.3615C7.70705 15.8675 8.13505 16.2515 8.64505 16.2515H9.35505C9.86505 16.2515 10.293 15.8685 10.349 15.3615L10.471 14.2675L11.685 13.7645L12.544 14.4525C12.942 14.7705 13.515 14.7395 13.876 14.3785L14.378 13.8765C14.738 13.5165 14.77 12.9425 14.452 12.5445L13.765 11.6855L14.268 10.4715L15.362 10.3495C15.868 10.2935 16.252 9.8655 16.252 9.3555L16.25 9.35449Z" />
      </g>
    </svg>
  );
}
