#!/bin/bash
# SessionStart hook: make sure `nurb dev` is running for this checkout and hand the
# session its viewer URL. The pid and log live in .claude/ and are gitignored, so
# each worktree gets its own server on its own port.
cd "$(dirname "$0")/../.." || exit 0
log=.claude/dev-server.log
pidfile=.claude/dev-server.pid

url_from_log() { grep -oE 'http://127\.0\.0\.1:[0-9]+' "$log" 2>/dev/null | tail -1; }

if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
  url=$(url_from_log)
else
  rm -f "$log"
  nohup uv run nurb dev >"$log" 2>&1 &
  echo $! >"$pidfile"
  # A fresh worktree builds a venv first, so give it a moment but never block long:
  # if the URL is not up yet, the per-turn reminder hook picks it up once it is.
  for _ in $(seq 1 30); do
    url=$(url_from_log)
    [ -n "$url" ] && break
    sleep 0.5
  done
fi

if [ -n "$url" ]; then
  printf '{"systemMessage":"nurb viewer: %s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"The nurb dev server for this workspace is running. Viewer URL: %s. Include this URL in every reply so the user can open the viewer."}}\n' "$url" "$url"
else
  printf '{"systemMessage":"nurb dev is starting; URL will appear in %s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"The nurb dev server is still starting. Its URL will appear in %s; share it with the user as soon as it does."}}\n' "$log" "$log"
fi
