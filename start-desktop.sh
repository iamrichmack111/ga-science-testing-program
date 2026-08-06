#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$APP_DIR/.venv/bin/python"
URL="${GA_SCIENCE_URL:-http://127.0.0.1:5075}"
STATE_DIR="$HOME/.local/state/ga-science-testing-program"
LOG_FILE="$STATE_DIR/app.log"
mkdir -p "$STATE_DIR" "$HOME/KIDS-HW/grades"
if [[ ! -x "$PYTHON" ]]; then
  notify-send "Georgia Science Testing Program" "Run install-desktop.sh first." 2>/dev/null || true
  exit 1
fi
if ! curl -fsS "$URL/health" >/dev/null 2>&1; then
  cd "$APP_DIR"
  nohup "$PYTHON" app.py >>"$LOG_FILE" 2>&1 &
  for _ in $(seq 1 40); do
    curl -fsS "$URL/health" >/dev/null 2>&1 && break
    sleep .25
  done
fi
if curl -fsS "$URL/health" >/dev/null 2>&1; then
  if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 &
  else open "$URL"; fi
else
  notify-send "Science app failed to start" "Check $LOG_FILE" 2>/dev/null || true
  exit 1
fi
