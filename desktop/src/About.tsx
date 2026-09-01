import { useState } from "react";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";
import { openUrl } from "@tauri-apps/plugin-opener";
import Logo from "./Logo";
import { osLabel } from "./platform";
import lgpl from "./licenses/OCCT_LICENSE_LGPL_21.txt?raw";
import occtException from "./licenses/OCCT_LGPL_EXCEPTION.txt?raw";
import uvMit from "./licenses/UV_LICENSE_MIT.txt?raw";

type Props = {
  appVersion: string;
  nurbVersion: string;
  occtVersion: string | null;
  osVersion: string;
  arch: string;
  onClose: () => void;
  /// The same check the macOS app menu offers; here it has a surface on every
  /// platform, because Windows has no app menu to carry it.
  onCheckUpdates: () => void;
};

function ExternalLink({ href, children }: { href: string; children: string }) {
  return (
    <a
      href={href}
      onClick={(e) => {
        e.preventDefault();
        openUrl(href);
      }}
    >
      {children}
    </a>
  );
}

/// About and third-party notices. The OCCT section is the load-bearing one:
/// its LGPL terms travel with every install the app performs, so the license
/// text ships here, in the app, not behind a URL.
export default function About({
  appVersion,
  nurbVersion,
  occtVersion,
  osVersion,
  arch,
  onClose,
  onCheckUpdates,
}: Props) {
  const [copied, setCopied] = useState(false);
  const debugInfo = [
    `app ${appVersion}`,
    `CAD engine ${nurbVersion}`,
    occtVersion ? `OCCT ${occtVersion}` : null,
    `${osLabel} ${osVersion} (${arch})`,
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
  return (
    <div className="about" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="about-card">
        <button className="about-close" title="close" onClick={onClose}>
          ×
        </button>
        <div className="about-head">
          <Logo size={36} />
          <div>
            <div className="about-title">nurb</div>
            <div className="about-versions">
              {appVersion === nurbVersion
                ? `version ${appVersion}`
                : `app ${appVersion} · CAD engine ${nurbVersion}`}
            </div>
          </div>
        </div>
        <div className="about-body">
          <p className="about-links">
            <ExternalLink href="https://nurb.dev">nurb.dev</ExternalLink>
            <ExternalLink href="https://github.com/Shpigford/nurb">github</ExternalLink>
            <ExternalLink href="https://github.com/Shpigford/nurb/issues/new/choose">
              report an issue
            </ExternalLink>
            <button className="about-copy" onClick={copyDebugInfo}>
              {copied ? "copied" : "copy debug info"}
            </button>
            <button className="about-copy" onClick={onCheckUpdates}>
              check for updates
            </button>
          </p>
          <p>
            © 2026 Ordinary Systems LLC. nurb is source-available under FSL-1.1-MIT; each
            release becomes MIT two years on.
          </p>
          <h3>Third-party notices</h3>
          <p>
            Geometry comes from <b>Open CASCADE Technology</b> (OCCT
            {occtVersion ? ` ${occtVersion}` : ""}), reached through build123d (Apache-2.0)
            and the OCP bindings (Apache-2.0). OCCT is licensed under LGPL-2.1 with the Open
            CASCADE exception. This app does not embed OCCT: first launch installs it into
            the app's data folder as separate, dynamically linked libraries you can inspect
            or replace, alongside the rest of the CAD engine. Sources for the exact version
            installed: <ExternalLink href={occtSources}>{occtSources}</ExternalLink>
          </p>
          <details>
            <summary>OCCT license (LGPL-2.1 with the Open CASCADE exception)</summary>
            <pre>{occtException}</pre>
            <pre>{lgpl}</pre>
          </details>
          <p>
            The app ships <b>uv</b> (MIT, also offered under Apache-2.0), which performs
            that install, and the nurb viewer's vendored copies of <b>three.js</b> r169
            (MIT) and the <b>JetBrains Mono</b> font (SIL OFL 1.1), each carrying its own
            license file.
          </p>
          <details>
            <summary>uv license (MIT)</summary>
            <pre>{uvMit}</pre>
          </details>
          <p>
            Also downloaded at first launch, not shipped in the app: Node.js (MIT), the
            Claude Code and Codex chat adapters and the Gemini CLI from npm under their
            publishers' own terms, a standalone CPython (PSF), and nurb's Python dependencies, including trimesh
            (MIT), watchdog (Apache-2.0), websockets (BSD-3-Clause), and numpy
            (BSD-3-Clause).
          </p>
        </div>
      </div>
    </div>
  );
}
