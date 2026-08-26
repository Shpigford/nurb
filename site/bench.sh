#!/bin/sh
# nurb benchmark contribution: curl -fsSL https://nurb.dev/bench.sh | sh
#
# Runs the nurb model benchmark on the AI subscription you already have and stages
# a leaderboard submission. A wizard asks which model to test from a menu, so you
# never have to know how a harness spells its model names. One trial is a valid
# contribution; runs pool on the leaderboard.
set -u

# Color only for a terminal, and never when NO_COLOR asks for plain output.
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  BOLD="$(printf '\033[1m')"; CYAN="$(printf '\033[36m')"
  RED="$(printf '\033[31m')"; RESET="$(printf '\033[0m')"
else
  BOLD=""; CYAN=""; RED=""; RESET=""
fi

say() { printf '%s\n' "$1"; }
step() { printf '%s %s\n' "${CYAN}[$1/3]${RESET}" "$2"; }
fail() { printf '\n%snurb bench: %s%s\n' "$RED" "$1" "$RESET" >&2; exit 1; }

main() {
  command -v git >/dev/null 2>&1 || fail "git is required and was not found"
  command -v curl >/dev/null 2>&1 || fail "curl is required and was not found"

  say ""
  say "  ${BOLD}nurb benchmarks:${RESET} your subscription, your row on the leaderboard"
  say ""

  if command -v uv >/dev/null 2>&1; then
    step 1 "uv is already here, moving on"
  else
    step 1 "installing uv, the tool manager that carries the benchmark..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || fail "could not install uv"
    export PATH="$HOME/.local/bin:$PATH"
    command -v uv >/dev/null 2>&1 || fail "uv installed but did not land on PATH; open a new terminal and rerun"
  fi

  # The wizard needs a repo checkout: tasks and scorer to run, a git tree to
  # commit the submission into. It must never land in whatever directory the
  # user happens to be standing in (a dogfooding run left a full replica of the
  # repo inside a dev checkout); it lives in one fixed hidden place, like any
  # tool's cache, and re-runs and concurrent sessions all share it. Standing
  # inside a benchmark checkout already? That checkout is used as it is.
  if [ -f "src/nurb_evals/contribute.py" ]; then
    step 2 "already inside a nurb-benchmarks checkout; using it as it is"
  else
    dir="${NURB_BENCH_HOME:-$HOME/.nurb/bench}"
    # The benchmark used to live inside the nurb repo; a checkout from that era
    # has evals/ at its top level and cannot pull the new layout, so it is
    # replaced rather than updated.
    if [ -d "$dir/evals" ]; then
      step 2 "replacing the pre-split checkout at $dir"
      rm -rf "$dir"
    fi
    if [ -d "$dir" ]; then
      step 2 "updating the benchmark checkout at $dir"
      # A previous wizard run leaves this clone on a submission branch, and
      # `git pull` there never sees main. Always reset the cache to origin's
      # main so a merged wizard change is what the next curl actually runs.
      if ! git -C "$dir" fetch origin main >/dev/null 2>&1 \
         || ! git -C "$dir" checkout -f -B main origin/main >/dev/null 2>&1; then
        say "      (update skipped; using the checkout as it is)"
      fi
    else
      step 2 "cloning the benchmark into $dir"
      mkdir -p "$(dirname "$dir")"
      git clone --depth 1 https://github.com/Shpigford/nurb-benchmarks "$dir" || fail "clone failed"
    fi
    cd "$dir" || fail "checkout is missing"
  fi

  step 3 "preparing and starting the wizard"
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
