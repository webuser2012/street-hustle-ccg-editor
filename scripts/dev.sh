#!/usr/bin/env bash
# Street Hustle CCG card editor — local dev entrypoint.
#
# Static app: no npm install, no build step. Serves the REPO ROOT so the editor
# can read the canonical data in ./data/ directly (the same files CI validates)
# instead of keeping a second copy of the card DB. The app itself is at /app/.
#
#   scripts/dev.sh           # http://127.0.0.1:5173/app/
#   PORT=8080 scripts/dev.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-5173}"
HOST="${HOST:-127.0.0.1}"

echo "Street Hustle CCG card editor"
echo "  serving ${REPO_ROOT}"
echo "  → http://${HOST}:${PORT}/app/   (app)"
echo "  → http://${HOST}:${PORT}/data/  (canonical card DB)"
echo "  Ctrl+C to stop"

cd "$REPO_ROOT"
exec python3 -m http.server "$PORT" --bind "$HOST" --directory "$REPO_ROOT"