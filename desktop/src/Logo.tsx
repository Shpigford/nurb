// The nurb cube, identical to the mark on nurb.dev and the viewer favicon.
export default function Logo({ size = 17 }: { size?: number }) {
  return (
    <svg
      className="logo-mark"
      width={size}
      height={size}
      viewBox="0 0 18 18"
      aria-hidden="true"
    >
      <path
        d="m7.997,2.332l-4.25,2.465c-.617.358-.997,1.017-.997,1.73v4.946c0,.713.38,1.372.997,1.73l4.25,2.465c.621.36,1.386.36,2.007,0l4.25-2.465c.617-.358.997-1.017.997-1.73v-4.946c0-.713-.38-1.372-.997-1.73l-4.25-2.465c-.621-.36-1.386-.36-2.007,0Z"
        fill="currentColor"
        opacity=".3"
      />
      <g
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      >
        <path d="m7.997,2.332l-4.25,2.465c-.617.358-.997,1.017-.997,1.73v4.946c0,.713.38,1.372.997,1.73l4.25,2.465c.621.36,1.386.36,2.007,0l4.25-2.465c.617-.358.997-1.017.997-1.73v-4.946c0-.713-.38-1.372-.997-1.73l-4.25-2.465c-.621-.36-1.386-.36-2.007,0Z" />
        <polyline points="12.251 7.1035 9 9 5.75 7.1035" />
        <line x1="9.0005" y1="12.7817" x2="9" y2="9" />
      </g>
    </svg>
  );
}
