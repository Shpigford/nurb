import { useState, type ReactNode } from "react";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";
import { openUrl } from "@tauri-apps/plugin-opener";
import { brand, Button, Icon } from "@nurb/ui";
import lgpl from "./licenses/OCCT_LICENSE_LGPL_21.txt?raw";
import occtException from "./licenses/OCCT_LGPL_EXCEPTION.txt?raw";
import uvMit from "./licenses/UV_LICENSE_MIT.txt?raw";

type Props = {
  appVersion: string;
  nurbVersion: string;
  occtVersion: string | null;
  osVersion: string;
  arch: string;
  // Optional, so the button only appears once the shell hands it the updater.
  onCheckUpdates?: () => void;
};

// A row of the Links block: the destination on the left, what you get on the right.
function LinkRow({ label, hint, href, last }: { label: string; hint: string; href: string; last?: boolean }) {
  return (
    <button
      type="button"
      onClick={() => openUrl(href).catch(() => {})}
      className={`group flex h-[34px] shrink-0 items-center justify-between text-left ${
        last ? "" : "border-b border-line-soft"
      }`}
    >
      <span className="truncate font-mono text-[11px] text-ink group-hover:text-accent-ink">{label}</span>
      <span className="mono-label shrink-0 text-muted">{hint}</span>
    </button>
  );
}

// One licence, folded away. The text stays in the app rather than behind a URL.
function License({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="group">
      <summary className="flex h-8 shrink-0 cursor-pointer list-none items-center justify-between border-b border-line-soft [&::-webkit-details-marker]:hidden">
        <span className="btn-label text-ink">{title}</span>
        <Icon name="chevron-down" className="text-muted transition-transform group-open:rotate-180" />
      </summary>
      <div className="mt-2 max-h-64 overflow-y-auto rounded-[6px] bg-raised px-3.5 py-3">{children}</div>
    </details>
  );
}

function LicenseText({ children }: { children: string }) {
  return <pre className="font-mono text-[10px] leading-4 whitespace-pre-wrap text-ink-soft">{children}</pre>;
}

/// About and third-party notices, the last section of Settings. The OCCT
/// section is the load-bearing one:
/// its LGPL terms travel with every install the app performs, so the license
/// text ships here, in the app, not behind a URL.
export default function About({
  appVersion,
  nurbVersion,
  occtVersion,
  osVersion,
  arch,
  onCheckUpdates,
}: Props) {
  const [copied, setCopied] = useState(false);
  const debugInfo = [
    `app ${appVersion}`,
    `CAD engine ${nurbVersion}`,
    occtVersion ? `OCCT ${occtVersion}` : null,
    `macOS ${osVersion} (${arch})`,
  ]
    .filter(Boolean)
    .join("\n");
  const copyDebugInfo = () => {
    writeText(debugInfo).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  const occtSources = occtVersion
    ? `https://github.com/Open-Cascade-SAS/OCCT/tree/V${occtVersion.split(".").join("_")}`
    : "https://github.com/Open-Cascade-SAS/OCCT";
  const versionLine = [
    `Version ${appVersion}`,
    `Engine ${nurbVersion}`,
    occtVersion ? `Kernel OCCT ${occtVersion}` : null,
    `macOS ${osVersion}`,
    arch,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      <section className="flex flex-col gap-4.5 px-7 pt-5.5 pb-7">
        <img src={brand.lockup} alt="nurb" className="h-9 w-[130px] shrink-0" />
        <div className="font-mono text-[11px] leading-4 tracking-[0.02em] text-muted uppercase">
          {versionLine}
        </div>
        <div className="flex items-center gap-2">
          <Button size="md" className="px-3.5" onClick={copyDebugInfo}>
            {copied ? "Copied" : "Copy debug info"}
          </Button>
          {onCheckUpdates ? (
            <Button size="md" className="px-3.5" onClick={onCheckUpdates}>
              Check for updates
            </Button>
          ) : null}
        </div>
        <p className="text-[13.5px] leading-[18px] text-muted">
          © 2026 Ordinary Systems LLC. nurb is source-available under FSL-1.1-MIT; each release becomes MIT two years on.
        </p>
      </section>

      <div className="h-px bg-line-soft" />

      <section className="flex flex-col gap-3 px-7 py-5.5">
        <h2 className="font-display text-[17px] leading-[22px] tracking-tight text-ink">Links</h2>
        <div className="flex flex-col">
          <LinkRow label="nurb.app" hint="Guides and changelog" href="https://nurb.app" />
          <LinkRow label="GitHub issues" hint="Tell us what broke" href="https://github.com/Shpigford/nurb/issues" />
          <LinkRow label="Kernel sources" hint="OCCT source archive" href={occtSources} last />
        </div>
      </section>

      <div className="h-px bg-line-soft" />

      <section className="flex flex-col gap-3.5 px-7 pt-5.5 pb-7.5">
        <div className="flex flex-col gap-1">
          <h2 className="font-display text-[17px] leading-[22px] tracking-tight text-ink">Licenses</h2>
          <p className="text-[13.5px] leading-[18px] text-muted">
            nurb links the OCCT kernel and ships uv; their licences are below.
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <License title="OCCT · LGPL 2.1 with exception">
            <p className="mb-3 font-mono text-[10px] leading-4 text-ink-soft">
              Geometry comes from Open CASCADE Technology
              {occtVersion ? ` ${occtVersion}` : ""}, reached through build123d and the OCP bindings. nurb
              does not embed OCCT: first launch installs it into the app's data folder as separate,
              dynamically linked libraries you can inspect or replace.
            </p>
            <LicenseText>{occtException}</LicenseText>
            <LicenseText>{lgpl}</LicenseText>
          </License>
          <License title="uv · MIT">
            <LicenseText>{uvMit}</LicenseText>
          </License>
          <License title="build123d · Apache 2.0">
            <p className="font-mono text-[10px] leading-4 text-ink-soft">
              build123d and the OCP bindings are Apache-2.0. The workbench carries three.js r169 (MIT) and the
              JetBrains Mono font (SIL OFL 1.1), each with its own licence file. Fetched at first launch
              rather than shipped: Node.js (MIT), the Codex chat adapter and the Gemini CLI under their
              publishers' own terms, a standalone CPython (PSF), and the CAD engine's dependencies, including
              trimesh (MIT), websockets (BSD-3-Clause) and numpy (BSD-3-Clause).
            </p>
          </License>
        </div>
      </section>
    </>
  );
}
