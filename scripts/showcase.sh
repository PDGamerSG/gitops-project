#!/usr/bin/env bash
# Serve the public showcase locally so the hosted presentation can be demoed offline.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${SHOWCASE_PORT:-4173}"

if command -v python >/dev/null 2>&1; then
  PYTHON="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  printf 'Python 3 is required to serve the showcase.\n' >&2
  exit 1
fi

printf 'GitOps showcase: http://localhost:%s/\n' "$PORT"
printf 'Press Ctrl+C to stop the local showcase server.\n'
exec "$PYTHON" -m http.server "$PORT" --directory "$ROOT_DIR/public"
