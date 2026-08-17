#!/bin/sh
# nurb installer: curl -fsSL https://nurb.dev/install.sh | sh
#
# Installs three things, skipping whatever you already have:
#   1. uv, the Python tool manager that carries nurb
#   2. nurb itself
#   3. the nurb skill, which teaches your AI to drive it
#
# Everything lands in your home directory. Nothing needs sudo.
set -u

say() { printf '%s\n' "$1"; }
fail() { printf '\nnurb install: %s\n' "$1" >&2; exit 1; }

# Without node, skills.sh can't run; place the skill file where Claude looks.
install_skill_directly() {
  dir="$HOME/.claude/skills/nurb"
  mkdir -p "$dir"
  curl -fsSL https://raw.githubusercontent.com/Shpigford/nurb/main/skills/nurb/SKILL.md -o "$dir/SKILL.md" || return 1
  say "      skill installed for Claude at ~/.claude/skills/nurb"
}

main() {
  command -v curl >/dev/null 2>&1 || fail "curl is required and was not found"
  case "$(uname -s)" in
    Darwin|Linux) ;;
    *) fail "this installer covers macOS and Linux; for anything else see https://nurb.dev" ;;
  esac

  say ""
  say "  nurb: real CAD skills for the AI you already talk to"
  say ""

  if command -v uv >/dev/null 2>&1; then
    say "[1/3] uv is already here, moving on"
  else
    say "[1/3] installing uv, the tool manager that carries nurb..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || fail "could not install uv"
    export PATH="$HOME/.local/bin:$PATH"
    command -v uv >/dev/null 2>&1 || fail "uv installed but did not land on PATH; open a new terminal and rerun this installer"
  fi

  say "[2/3] installing nurb (a real CAD kernel rides along, this is the slow part)..."
  uv tool install --upgrade nurb || fail "could not install nurb"
  uv tool update-shell >/dev/null 2>&1 || true

  say "[3/3] teaching your AI to use nurb..."
  if command -v npx >/dev/null 2>&1; then
    # skills.sh detects every AI harness on the machine and installs into each.
    # --skill nurb keeps it to the shipped skill; the repo also carries dev-only
    # skills (release, changelog) that must not land on a user's machine.
    npx -y skills add shpigford/nurb --skill nurb -g -y </dev/null || install_skill_directly || fail "could not install the nurb skill; run manually: npx skills add shpigford/nurb --skill nurb"
  else
    install_skill_directly || fail "could not install the nurb skill; see https://nurb.dev"
  fi

  say ""
  say "  done. nurb is installed and your AI now knows how to use it."
  say ""
  say "  there is no app to open: nurb works through the AI you already talk to."
  say "  open Claude, Cursor, Codex... in a fresh folder and ask for a part:"
  say ""
  say "      \"design me a phone stand\""
  say ""
  say "  it models the part while you watch in your browser, then you print it."
  say "  later, \"nurb update\" brings nurb and the skill forward together."
  say "  if the AI says nurb is not found, restart your terminal first."
  say ""
  say "  https://nurb.dev"
  say ""
}

main
