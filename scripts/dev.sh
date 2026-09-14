#!/usr/bin/env bash
# Street Hustle CCG card editor — local dev entrypoint.
#
# Static scaffold: no npm install, no build step. Serves ./app over HTTP so the
# editor shell, design tokens and card CSS load exactly as they will in prod.
#
#   scripts/dev.sh          # http://127.0.0.1:5173
#   PORT=8080 scripts/dev.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-5173}"
HOST="${HOST:-127.0.0.1}"

echo "Street Hustle CCG card editor"
echo "  serving ${REPO_ROOT}/app"
echo "  → http://${HOST}:${PORT}/"
echo "  Ctrl+C to stop"

cd "$REPO_ROOT"
exec python3 -m http.server "$PORT" --bind "$HOST" --directory app