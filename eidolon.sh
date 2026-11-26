#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  echo "Missing .venv — run ./install.sh first."
  exit 1
fi

if [ ! -d "frontend/dist" ]; then
  echo "[EIDOLON] Building frontend production bundle..."
  npm --prefix frontend run build
fi

PORT="${EIDOLON_PORT:-8000}"
echo "[EIDOLON] Starting local server on http://127.0.0.1:${PORT}"
echo "[EIDOLON] 100% local, zero external AI dependencies, offline-ready."
exec .venv/bin/uvicorn eidolon.main:app --app-dir backend --host 127.0.0.1 --port "$PORT"
