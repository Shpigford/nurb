import type { ReactNode, SVGProps } from "react"

// Nucleo 12px outline grid, rendered 1:1. Every glyph ships a
// 1.5 stroke with round caps and joins; drawing them at 12px keeps the
// effective stroke identical everywhere. Never hand-draw one, never scale one.
//
// Ids: 2023 chevron-left · 2024 chevron-down · 1907 check · 1895 triangle-warning
// 1950 lock · 1902 plus · 1953 camera-2 · 1974 magnifier · 1896 xmark · 1954 image
// 11810 download · 11809 expand · 12597 eye · 61037 link · 2020 chevron-up
// 1903 minus · 11742 arrow-up · 61842 media-stop (glyph) · 62372 loader
// 11984 chat-bubble · 12594 dots · 1897 trash · 12065 ruler · 12602 gear
// 12383 user · 60577 rect-logout · 1942 box · 12591 copy · 1976 folder.

export type IconName =
  | "chevron-left"
  | "chevron-down"
  | "chevron-up"
  | "check"
  | "warning"
  | "lock"
  | "plus"
  | "minus"
  | "camera"
  | "search"
  | "xmark"
  | "image"
  | "download"
  | "expand"
  | "eye"
  | "arrow-up"
  | "link"
  | "stop"
  | "loader"
  | "chat"
  | "dots"
  | "trash"
  | "ruler"
  | "gear"
  | "user"
  | "logout"
  | "box"
  | "copy"
  | "folder"

const PATHS: Record<IconName, ReactNode> = {
  "chevron-left": <polyline points="7.75 1.75 3.5 6 7.75 10.25" />,
  "chevron-down": <polyline points="1.75 4.25 6 8.5 10.25 4.25" />,
  "chevron-up": <polyline points="10.25 7.75 6 3.5 1.75 7.75" />,
  check: <path d="m1.76,7.004l2.25,3L10.24,1.746" />,
  warning: (
    <>
      <circle cx="6" cy="10.125" r=".875" fill="currentColor" stroke="none" />
      <line x1="6" y1="4.75" x2="6" y2="7.75" />
      <path d="m8.625,10.25h1.164c1.123,0,1.826-1.216,1.265-2.189L7.265,1.484c-.562-.975-1.969-.975-2.53,0L.946,8.061c-.561.973.142,2.189,1.265,2.189h1.164" />
    </>
  ),
  lock: (
    <>
      <line x1="6" y1="7.5" x2="6" y2="8.5" />
      <path d="m3.75,4.75v-1.75c0-1.243,1.007-2.25,2.25-2.25h0c1.243,0,2.25,1.007,2.25,2.25v1.75" />
      <rect x="1.25" y="4.75" width="9.5" height="6.5" rx="1.5" ry="1.5" />
    </>
  ),
  plus: (
    <>
      <line x1="10.75" y1="6" x2="1.25" y2="6" />
      <line x1="6" y1="10.75" x2="6" y2="1.25" />
    </>
  ),
  minus: <line x1="10.75" y1="6" x2="1.25" y2="6" />,
  camera: (
    <>
      <circle cx="3.25" cy="5.75" r=".75" fill="currentColor" stroke="none" />
      <rect x=".75" y="3.25" width="10.5" height="8" rx="2" ry="2" />
      <line x1="2.75" y1=".75" x2="4.75" y2=".75" />
      <circle cx="7.25" cy="7.25" r="1" fill="currentColor" />
    </>
  ),
  search: (
    <>
      <line x1="7.652" y1="7.652" x2="10.75" y2="10.75" />
      <circle cx="5" cy="5" r="3.75" />
    </>
  ),
  xmark: (
    <>
      <line x1="2.25" y1="9.75" x2="9.75" y2="2.25" />
      <line x1="9.75" y1="9.75" x2="2.25" y2="2.25" />
    </>
  ),
  image: (
    <>
      <path d="m2.32,10.516l4.723-4.723c.391-.391,1.024-.391,1.414,0l2.293,2.293" />
      <circle cx="4" cy="4" r="1" fill="currentColor" stroke="none" />
      <rect x="1.25" y="1.25" width="9.5" height="9.5" rx="2" ry="2" />
    </>
  ),
  download: (
    <>
      <line x1="6" y1="7.75" x2="6" y2=".75" />
      <polyline points="3.75 5.75 6 8 8.25 5.75" />
      <path d="m8.69,2.75c1.028,0,1.888.779,1.99,1.801l.35,3.5c.118,1.177-.807,2.199-1.99,2.199H2.96c-1.183,0-2.108-1.022-1.99-2.199l.35-3.5c.102-1.022.963-1.801,1.99-1.801" />
    </>
  ),
  expand: (
    <>
      <path d="m1.25,4.25v-1c0-1.105.895-2,2-2h1" />
      <path d="m7.75,1.25h1c1.105,0,2,.895,2,2v1" />
      <path d="m10.75,7.75v1c0,1.105-.895,2-2,2h-1" />
      <path d="m4.25,10.75h-1c-1.105,0-2-.895-2-2v-1" />
    </>
  ),
  eye: (
    <>
      <path d="M5.99997 10.25C8.64947 10.25 10.2021 8.38538 10.9485 7.12628C11.3599 6.43238 11.3599 5.56762 10.9485 4.87372C10.2021 3.61462 8.64937 1.75 5.99997 1.75C3.42267 1.75 1.87667 3.53288 1.10727 4.78918C0.649466 5.53658 0.649466 6.46338 1.10727 7.21088C1.87667 8.46718 3.42267 10.25 5.99997 10.25Z" />
      <circle cx="6" cy="6" r="1.25" fill="currentColor" />
    </>
  ),
  "arrow-up": (
    <>
      <line x1="6" y1="11" x2="6" y2="1.25" />
      <polyline points="9.25 4.25 6 1 2.75 4.25" />
    </>
  ),
  link: (
    <>
      <path d="M7 7C7.97631 6.02369 7.97631 4.44078 7 3.46447L5.55292 2.01788C4.57661 1.04157 2.9937 1.04157 2.01739 2.01788C1.05869 2.97658 1.0414 4.5202 1.96552 5.5" />
      <path d="M5 5C4.02369 5.97631 4.02369 7.55922 5 8.53553L6.44197 9.97758C7.41828 10.9539 9.00119 10.9539 9.9775 9.97758C10.9347 9.02036 10.9534 7.48002 10.0336 6.5" />
    </>
  ),
  stop: (
    <path
      d="M3.75 11C2.23122 11 1 9.76878 1 8.25V3.75C1 2.23122 2.23122 1 3.75 1L8.25 1C9.76878 1 11 2.23122 11 3.75V8.25C11 9.76878 9.76878 11 8.25 11H3.75Z"
      fill="currentColor"
      stroke="none"
    />
  ),
  chat: (
    <path d="m8.75,8.75h-4.75l-2.75,2.5V3.25c0-1.105.895-2,2-2h5.5c1.105,0,2,.895,2,2v3.5c0,1.105-.895,2-2,2Z" />
  ),
  loader: (
    <>
      <path d="M6 2.25V0.75" />
      <path opacity="0.5" d="M6 11.25V9.75" />
      <path opacity="0.75" d="M9.75488 5.995L11.2549 5.995" />
      <path opacity="0.25" d="M0.754883 5.995L2.25488 5.995" />
      <path opacity="0.88" d="M8.65321 3.3449L9.71387 2.28424" />
      <path opacity="0.38" d="M2.28895 9.70885L3.34961 8.64819" />
      <path opacity="0.63" d="M8.66004 8.64811L9.7207 9.70877" />
      <path opacity="0.13" d="M2.29627 2.28416L3.35693 3.34482" />
    </>
  ),
  dots: (
    <>
      <circle cx="6" cy="6" r="1" fill="currentColor" stroke="none" />
      <circle cx="2" cy="6" r="1" fill="currentColor" stroke="none" />
      <circle cx="10" cy="6" r="1" fill="currentColor" stroke="none" />
    </>
  ),
  trash: (
    <>
      <line x1="1" y1="2.25" x2="11" y2="2.25" />
      <path d="m4.75,2.25v-1c0-.276.224-.5.5-.5h1.5c.276,0,.5.224.5.5v1" />
      <path d="m9.5,4.75l-.195,5.058c-.031.805-.693,1.442-1.499,1.442h-3.613c-.806,0-1.468-.637-1.499-1.442l-.195-5.058" />
    </>
  ),
  ruler: (
    <>
      <line x1="6.623" y1="6.623" x2="7.754" y2="7.754" />
      <line x1="7.873" y1="4.373" x2="9.504" y2="6.004" />
      <line x1="4.373" y1="7.873" x2="6.004" y2="9.504" />
      <rect x=".42" y="3.52" width="11.161" height="4.96" rx="1.086" ry="1.086" transform="translate(-2.485 6) rotate(-45)" />
    </>
  ),
  gear: (
    <>
      <circle cx="6" cy="6" r=".75" fill="currentColor" />
      <circle cx="6" cy="6" r="4" />
      <line x1="6" y1=".75" x2="6" y2="2" />
      <line x1="9.086" y1="1.753" x2="8.351" y2="2.764" />
      <line x1="10.993" y1="4.378" x2="9.804" y2="4.764" />
      <line x1="10.993" y1="7.622" x2="9.804" y2="7.236" />
      <line x1="9.086" y1="10.247" x2="8.351" y2="9.236" />
      <line x1="6" y1="11.25" x2="6" y2="10" />
      <line x1="2.914" y1="10.247" x2="3.649" y2="9.236" />
      <line x1="1.007" y1="7.622" x2="2.196" y2="7.236" />
      <line x1="1.007" y1="4.378" x2="2.196" y2="4.764" />
      <line x1="2.914" y1="1.753" x2="3.649" y2="2.764" />
    </>
  ),
  user: (
    <>
      <circle cx="6" cy="2.491" r="1.75" />
      <path d="m9.425,10.458c.551-.255.759-.92.458-1.446-.773-1.349-2.215-2.262-3.882-2.262s-3.11.912-3.882,2.262c-.301.526-.093,1.192.458,1.446,2.283,1.056,4.566,1.056,6.849,0Z" />
    </>
  ),
  logout: (
    <>
      <path d="M5.75 3.25V2.25c0-.828.672-1.5 1.5-1.5h2.5c.828 0 1.5.672 1.5 1.5v7.5c0 .828-.672 1.5-1.5 1.5h-2.5c-.828 0-1.5-.672-1.5-1.5v-1" />
      <line x1="8.25" y1="6" x2="1" y2="6" />
      <polyline points="3 3.75 .75 6 3 8.25" />
    </>
  ),
  box: (
    <>
      <line x1="1.25" y1="3.75" x2="10.75" y2="3.75" />
      <line x1="6" y1=".75" x2="6" y2="3.75" />
      <line x1="3.75" y1="8.25" x2="5.25" y2="8.25" />
      <path d="m1.25,3.75l1.461-2.504c.179-.307.508-.496.864-.496h4.851c.356,0,.685.189.864.496l1.461,2.504v5c0,1.105-.895,2-2,2H3.25c-1.105,0-2-.895-2-2V3.75Z" />
    </>
  ),
  copy: (
    <>
      <rect x="3.25" y=".75" width="8" height="8" rx="1.5" ry="1.5" />
      <path d="m8.25,11.25H2.25c-.828,0-1.5-.672-1.5-1.5V3.75" />
    </>
  ),
  folder: (
    <>
      <path d="m.75,7.25V3.25c0-1.105.895-2,2-2h1.701c.607,0,1.18.275,1.56.748l.603.752h2.636c1.105,0,2,.895,2,2v2.5" />
      <path d="m2.75,5.25h6.5c1.105,0,2,.895,2,2v1.5c0,1.105-.895,2-2,2H2.75c-1.105,0-2-.895-2-2v-1.5c0-1.105.895-2,2-2Z" />
    </>
  ),
}

export interface IconProps extends Omit<SVGProps<SVGSVGElement>, "name"> {
  name: IconName
}

export default function Icon({ name, className, ...rest }: IconProps) {
  return (
    <svg
      viewBox="0 0 12 12"
      width="12"
      height="12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className ? `size-3 shrink-0 ${className}` : "size-3 shrink-0"}
      {...rest}
    >
      {PATHS[name]}
    </svg>
  )
}
