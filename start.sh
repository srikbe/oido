#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill anything already on these ports
for PORT in 3456 3457; do
  PID=$(lsof -ti tcp:$PORT 2>/dev/null) && kill -9 $PID 2>/dev/null && echo "Killed existing process on :$PORT" || true
done

# Start proxy server (background)
echo "Starting proxy server on :3457…"
node "$APP_DIR/server.js" &
PROXY_PID=$!

# Start static file server (background)
echo "Starting static file server on :3456…"
npx --yes serve "$APP_DIR" --listen tcp://0.0.0.0:3456 --no-clipboard &
SERVE_PID=$!

echo ""
echo "  Oído is running:"
echo "  App  → http://localhost:3456"
echo "  API  → http://localhost:3457"
echo ""
echo "  PIDs: proxy=$PROXY_PID  serve=$SERVE_PID"
echo "  Press Ctrl-C to stop both."

# Wait and propagate Ctrl-C to both child processes
trap "kill $PROXY_PID $SERVE_PID 2>/dev/null; exit 0" INT TERM
wait
