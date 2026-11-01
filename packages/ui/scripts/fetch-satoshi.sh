#!/bin/sh
# Fetches Satoshi from Fontshare into fonts/. Its license (the ITF Free Font
# License) lets us embed it in the app and serve it on our own pages, but not
# keep the file in a public repository, so every checkout gets its own copy.
# Without it the display face falls back to Instrument Sans, so a failed
# download only warns. NURB_REQUIRE_FONTS=1 (the release sets it) makes it fatal.
set -eu

here="$(cd "$(dirname "$0")" && pwd)"
out="$here/../fonts/Satoshi-Variable.ttf"
[ -f "$out" ] && exit 0

fail() {
  echo "fonts: could not fetch Satoshi from Fontshare ($1); headlines fall back to Instrument Sans" >&2
  [ "${NURB_REQUIRE_FONTS:-}" = 1 ] && exit 1
  exit 0
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -fsSL "https://api.fontshare.com/v2/fonts/download/satoshi" -o "$tmp/satoshi.zip" || fail "download failed"
unzip -q -j "$tmp/satoshi.zip" "*/Fonts/TTF/Satoshi-Variable.ttf" -d "$tmp" 2>/dev/null || fail "Satoshi-Variable.ttf not in the zip"
mv "$tmp/Satoshi-Variable.ttf" "$out"
echo "fonts: fetched Satoshi into packages/ui/fonts"
