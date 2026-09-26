#!/usr/bin/env bash
# Stall-gate watcher. Runs the 45-minute gate on an interval, prints only when something fires.
# Usage: ops/watch.sh [interval_seconds]   (default 600)
set -u
cd "$(dirname "$0")/.."
INTERVAL="${1:-600}"
echo "stall watcher started (every ${INTERVAL}s) - ctrl-c to stop"
while true; do
  OUT="$(python3 ops/cadops.py stall)"
  if [ $? -ne 0 ]; then
    echo "[$(date '+%H:%M')] $OUT"
    command -v osascript >/dev/null 2>&1 && \
      osascript -e 'display notification "A lane has been on the same task for 45+ minutes." with title "Cadros stall gate"' >/dev/null 2>&1
  fi
  sleep "$INTERVAL"
done
