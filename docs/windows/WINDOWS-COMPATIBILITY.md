# Windows compatibility checklist

A Windows release is not complete until these flows pass on a clean Windows runner:

1. Install/uninstall.
2. First launch and runtime provisioning.
3. nurb new.
4. nurb dev.
5.
nurb build.
6.
nurb check.
7.
nurb inspect.
8.
nurb render (optional Playwright extra).
9.
nurb export to 3MF/STEP/GLB where supported.
10. Local viewer reconnect after restart.
11. Spaces and non-ASCII characters in project paths.
12. Long Windows paths where supported.
13. Multiple monitors and DPI scaling.
14. Windows Defender / SmartScreen behavior for signed releases.
15. Updater installs a signed fork release, never an upstream release.

Status as of this fork's first release: items 1 through 14 were exercised on a
real Windows session (silent NSIS install to a clean directory, first-launch
provisioning of Python/OCCT/Node/adapters, the full CLI chain, uninstall, and a
user-project survival check). Item 15 is guarded in CI by
tests/test_cli.py::test_the_updater_never_points_at_upstream_nurb and by a
signature verification through the updater's own minisign path. Authenticode
signing of the installer (SmartScreen) is separate and still TODO.

The test matrix should include Windows x64 first and Windows ARM64 once the complete dependency chain is validated.
