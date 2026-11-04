#!/bin/sh
# Brings a nurb checkout up to working condition: installs what is missing (node_modules,
# engine/.venv, the built workbench page) and reports what it did. Safe to run any time; it does
# nothing when everything is already in place.
#
#   sh .claude/scripts/session-setup.sh            install what is missing, print a short report
#   sh .claude/scripts/session-setup.sh --sync      also fast-forward the branch onto origin/main
#   sh .claude/scripts/session-setup.sh --json      report as Claude Code SessionStart hook JSON
#
# The slow installs run in the background and the report names the log, so a session start that
# calls this is never blocked on npm. --sync fetches origin and fast-forwards ONLY when the branch
# is clean and has no commits of its own; with local work it reports how far behind it is and
# leaves the merge to you. Set NURB_SKIP_SESSION_SETUP=1 to make the whole thing a no-op.

set -u

[ "${NURB_SKIP_SESSION_SETUP:-0}" = "1" ] && exit 0

SYNC=0
JSON=0
for arg in "$@"; do
  case "$arg" in
    --sync) SYNC=1 ;;
    --json) JSON=1 ;;
    *) echo "session-setup.sh: unknown option $arg" >&2; exit 2 ;;
  esac
done

ROOT="${CLAUDE_PROJECT_DIR:-}"
[ -n "$ROOT" ] || ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$ROOT" 2>/dev/null || exit 0

NOTES=""
note() { NOTES="$NOTES$1
"; }

# --- latest main (--sync only) -------------------------------------------------
if [ "$SYNC" -eq 1 ]; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
  git fetch --quiet origin main 2>/dev/null

  BEHIND=0
  AHEAD=0
  if git rev-parse --verify --quiet origin/main >/dev/null; then
    set -- $(git rev-list --left-right --count origin/main...HEAD 2>/dev/null)
    BEHIND=${1:-0}
    AHEAD=${2:-0}
  fi
  DIRTY=$(git status --porcelain --untracked-files=no 2>/dev/null | head -1)

  if [ "$BEHIND" -eq 0 ]; then
    note "- main: up to date with origin/main (branch $BRANCH, $AHEAD commit(s) ahead)."
  elif [ "$AHEAD" -eq 0 ] && [ -z "$DIRTY" ]; then
    if git merge --ff-only origin/main >/dev/null 2>&1; then
      note "- main: fast-forwarded $BRANCH onto origin/main ($BEHIND commit(s))."
    else
      note "- main: $BEHIND commit(s) behind origin/main and the fast-forward failed. Merge before starting work."
    fi
  else
    note "- main: $BEHIND commit(s) behind origin/main, and this branch has its own work ($AHEAD commit(s) ahead${DIRTY:+, uncommitted changes}). Merge origin/main before starting work."
  fi
fi

# --- dependencies -------------------------------------------------------------
NEED=""
if [ ! -d node_modules ] || [ package-lock.json -nt node_modules ]; then
  NEED="$NEED npm"
fi
if [ ! -x engine/.venv/bin/python ] || [ engine/uv.lock -nt engine/.venv ]; then
  NEED="$NEED uv"
fi
if [ ! -f engine/src/nurb/workbench/index.html ]; then
  NEED="$NEED workbench"
fi

if [ -z "$NEED" ]; then
  note "- deps: node_modules, engine/.venv and the built workbench page are all present."
else
  LOG="$ROOT/.claude/session-setup.log"
  : > "$LOG"
  CMDS=""
  case "$NEED" in *npm*) CMDS="$CMDS npm ci;" ;; esac
  case "$NEED" in *uv*) CMDS="$CMDS (cd engine && uv sync);" ;; esac
  case "$NEED" in *workbench*) CMDS="$CMDS npm run build --workspace packages/workbench;" ;; esac
  nohup sh -c "cd '$ROOT' && set -x && $CMDS echo SESSION_SETUP_DONE" >>"$LOG" 2>&1 &
  note "- deps: installing$NEED in the background. Log: $LOG (it ends with SESSION_SETUP_DONE). Wait for it before running the suite, a build, or the serve."
fi

if [ "$JSON" -eq 1 ]; then
  python3 - "$NOTES" <<'PY'
import json, sys
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Session setup (.claude/scripts/session-setup.sh):\n" + sys.argv[1].rstrip(),
}}))
PY
else
  printf '%s' "$NOTES"
fi
