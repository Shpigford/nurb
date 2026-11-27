/**
 * The last segment of a path, on either machine.
 *
 * A path reaches the page from the Rust side, built with the operating system's
 * own separator, so on Windows a project's folder is `C:\Users\...\projects\<id>`
 * and holds no forward slash at all. Splitting on "/" alone therefore returns the
 * *whole* path as the last segment. That is not cosmetic here: the chat reads the
 * project's id out of that folder, so on Windows every request went to
 * `/api/projects/C:\Users\...\projects\<id>/...` and the engine answered
 * "no project" - nothing the person typed ever reached the transcript.
 *
 * Both separators count as separators. A Mac path never holds a backslash in a
 * folder this app builds, and a Windows path can legitimately hold a forward
 * slash when it arrives from a slicer's settings or a pasted value, so neither
 * platform can assume the other's.
 */
export function pathName(path: string): string {
  const parts = path.split(/[\\/]/).filter(Boolean);
  return parts.length ? parts[parts.length - 1] : path;
}

/** The segment above the last one, or the path itself when there is nothing above it. */
export function pathParentName(path: string): string {
  const parts = path.split(/[\\/]/).filter(Boolean);
  return parts.length >= 2 ? parts[parts.length - 2] : path;
}
