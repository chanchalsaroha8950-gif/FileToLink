#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if pgrep -af "[p]ython" | grep -E "python (main|bot)\.py( |$)" >/dev/null 2>&1; then
  echo "A bot process is already running. Stop old instances first, then run ./run_both.sh"
  echo "Tip: pkill -f 'python main.py' && pkill -f 'python bot.py'"
  exit 1
fi

python main.py &
PID_MAIN=$!

python bot.py &
PID_SECONDARY=$!

cleanup() {
  kill "$PID_MAIN" "$PID_SECONDARY" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

wait "$PID_MAIN" "$PID_SECONDARY"
