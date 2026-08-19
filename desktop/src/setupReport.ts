const REPORT_URL = "https://github.com/Shpigford/nurb/issues/new";
const TRUNCATED = "\n\n[error truncated]";

export const REPORT_URL_MAX_LENGTH = 6_000;

export function setupReportUrl(version: string, error: string): string {
  const params = new URLSearchParams({
    template: "bug_report.yml",
    surface: "Desktop app",
    version,
    "what-happened": "First-launch setup failed with the error below.",
    steps: "1. Open the app",
    output: error,
  });
  const build = () => `${REPORT_URL}?${params}`;
  if (build().length <= REPORT_URL_MAX_LENGTH) return build();

  // GitHub rejects oversized issue URLs. Find the longest Unicode-safe prefix
  // that still leaves room for every field after URL encoding.
  const characters = Array.from(error);
  let low = 0;
  let high = characters.length;
  while (low < high) {
    const middle = Math.ceil((low + high) / 2);
    params.set("output", characters.slice(0, middle).join("") + TRUNCATED);
    if (build().length <= REPORT_URL_MAX_LENGTH) low = middle;
    else high = middle - 1;
  }
  params.set("output", characters.slice(0, low).join("") + TRUNCATED);
  return build();
}
