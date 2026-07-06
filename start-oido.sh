#!/usr/bin/env bash

# Explicit PATH so GUI apps (Automator) find the same tools as the terminal
export PATH="/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$PATH"

# Full paths — avoids any PATH lookup failures in GUI environments
NODE="/usr/local/bin/node"
NPX="/usr/local/bin/npx"
APP_DIR="/Users/sriprestonkulkarni/spanish-listening-app"
LOG="/tmp/oido-launch.log"

echo "----------------------------------------" >> "$LOG"
echo "Starting Oído... $(date)" >> "$LOG"
echo "NODE: $NODE  (exists: $([ -f "$NODE" ] && echo yes || echo NO))" >> "$LOG"
echo "NPX:  $NPX   (exists: $([ -f "$NPX" ] && echo yes || echo NO))" >> "$LOG"

# Kill anything on ports 3456 and 3457
echo "Killing existing processes on 3456/3457..." >> "$LOG"
for PORT in 3456 3457; do
  PID=$(lsof -ti tcp:$PORT 2>/dev/null)
  if [ -n "$PID" ]; then
    kill -9 $PID 2>/dev/null
    echo "  Killed PID $PID on :$PORT" >> "$LOG"
  fi
done
sleep 1

# Start the API proxy server
echo "Starting proxy server on :3457..." >> "$LOG"
(cd "$APP_DIR" && "$NODE" server.js >> /tmp/oido-proxy.log 2>&1) &
echo "  Proxy PID: $!" >> "$LOG"

# Start the static file server
echo "Starting static file server on :3456..." >> "$LOG"
"$NPX" serve "$APP_DIR" --listen tcp://0.0.0.0:3456 --no-clipboard >> /tmp/oido-serve.log 2>&1 &
echo "  Serve PID: $!" >> "$LOG"

# Wait for the static server to be ready (up to 12 seconds)
echo "Waiting for :3456 to be ready..." >> "$LOG"
for i in $(seq 1 12); do
  sleep 1
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3456/ 2>/dev/null)
  echo "  Attempt $i: HTTP $STATUS" >> "$LOG"
  if [ "$STATUS" = "200" ]; then
    echo "Server ready. Opening browser." >> "$LOG"
    break
  fi
done

# Open the app in the default browser
open http://localhost:3456
echo "Done. Browser opened at $(date)" >> "$LOG"
