#!/bin/sh
# nurb benchmark contribution: curl -fsSL https://nurb.dev/bench.sh | sh
#
# Runs the nurb model benchmark on the AI subscription you already have and stages
# a leaderboard submission. A wizard asks which model to test from a menu, so you
# never have to know how a harness spells its model names. One trial is a valid
# contribution; runs pool on the leaderboard.
set -u

say() { printf '%s\n' "$1"; }
fail() { printf '\nnurb bench: %s\n' "$1" >&2; exit 1; }

main() {
  command -v git >/dev/null 2>&1 || fail "git is required and was not found"
  command -v curl >/dev/null 2>&1 || fail "curl is required and was not found"

  say ""
  say "  nurb benchmarks: your subscription, your row on the leaderboard"
  say ""

  if command -v uv >/dev/null 2>&1; then
    say "[1/3] uv is already here, moving on"
  else
    say "[1/3] installing uv, the tool manager that carries the benchmark..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || fail "could not install uv"
    export PATH="$HOME/.local/bin:$PATH"
    command -v uv >/dev/null 2>&1 || fail "uv installed but did not land on PATH; open a new terminal and rerun"
  fi

  # Re-running from inside a checkout must never nest another clone inside it:
  # the first dogfooding run produced nurb-bench/nurb-bench and a submission
  # staged where no git command could find it.
  if [ -f "evals/src/nurb_evals/contribute.py" ]; then
    say "[2/3] already inside a nurb checkout; using it as it is"
  elif [ -f "../evals/src/nurb_evals/contribute.py" ]; then
    say "[2/3] already inside a nurb checkout; using it as it is"
    cd ..
  else
    dir="nurb-bench"
    if [ -d "$dir/evals" ]; then
      say "[2/3] $dir/ already cloned; pulling the latest benchmark"
      git -C "$dir" pull --ff-only >/dev/null 2>&1 || say "      (pull skipped; using the checkout as it is)"
    else
      say "[2/3] cloning the benchmark into ./$dir"
      git clone --depth 1 https://github.com/Shpigford/nurb "$dir" || fail "clone failed"
    fi
    cd "$dir" || fail "clone is missing"
  fi

  say "[3/3] preparing and starting the wizard"
  cd evals || fail "checkout is missing evals/"
  uv sync >/dev/null || fail "uv sync failed"

  # `curl | sh` leaves stdin owned by the pipe; the wizard needs the keyboard.
  if [ -t 0 ]; then
    exec uv run python -m nurb_evals.contribute "$@"
  elif [ -e /dev/tty ]; then
    exec uv run python -m nurb_evals.contribute "$@" </dev/tty
  else
    exec uv run python -m nurb_evals.contribute "$@"
  fi
}

main "$@"
