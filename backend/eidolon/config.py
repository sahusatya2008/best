"""Configuration constants and paths for EIDOLON."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("EIDOLON_DATA_DIR", PROJECT_ROOT / "data"))
DB_PATH = Path(os.environ.get("EIDOLON_DB_PATH", DATA_DIR / "eidolon.db"))
EXPORTS_DIR = DATA_DIR / "exports"
REPORTS_DIR = DATA_DIR / "reports"
BACKUPS_DIR = DATA_DIR / "backups"

# Ensure local directories exist
for _d in (DATA_DIR, EXPORTS_DIR, REPORTS_DIR, BACKUPS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
