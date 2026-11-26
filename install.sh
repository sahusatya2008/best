#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "[EIDOLON] Installing Python virtual environment and dependencies..."
if command -v uv >/dev/null 2>&1; then
  uv venv --python 3.12 .venv
  uv pip install -e ".[dev]"
else
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -e ".[dev]"
fi

echo "[EIDOLON] Installing frontend dependencies and building production bundle..."
npm --prefix frontend install
npm --prefix frontend run build

echo "[EIDOLON] Installation complete. Launch offline anytime with: ./eidolon.sh"
