"""SQLite database management, migrations, WAL mode, and backup support."""

from __future__ import annotations

import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from eidolon.config import BACKUPS_DIR, DB_PATH

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


class Database:
    """Thread-safe SQLite connection manager with automatic schema migrations."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._apply_migrations()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _apply_migrations(self) -> None:
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        with self.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                """
            )
            applied = {
                row["version"]
                for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
            }
            for mf in migration_files:
                version = mf.stem
                if version in applied:
                    continue
                sql = mf.read_text(encoding="utf-8")
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (version, datetime.now(timezone.utc).isoformat()),
                )

    def backup(self, label: str = "manual") -> Path:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target = BACKUPS_DIR / f"eidolon_{label}_{stamp}.db"
        with self.connect() as src:
            dst = sqlite3.connect(str(target))
            src.backup(dst)
            dst.close()
        return target

    def restore(self, backup_path: Path | str) -> None:
        src_path = Path(backup_path)
        if not src_path.exists():
            raise FileNotFoundError(f"Backup not found: {src_path}")
        shutil.copy2(src_path, self.db_path)
        self._apply_migrations()

    def stats(self) -> dict[str, int | float | str]:
        size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
        with self.connect() as conn:
            exp_count = conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
            evt_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            snap_count = conn.execute("SELECT COUNT(*) FROM simulation_snapshots").fetchone()[0]
        return {
            "db_path": str(self.db_path),
            "size_mb": round(size_bytes / (1024 * 1024), 3),
            "experiments": exp_count,
            "events": evt_count,
            "snapshots": snap_count,
        }
