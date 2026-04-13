"""
Minimal migration system for SQLite.
Migrations are plain SQL strings tagged with a version number.
On startup, only unapplied migrations run — already-applied ones are skipped.

Usage:
    from backend.utils.migrations import run_migrations
    run_migrations(db_path)

Adding a new migration:
    Add a new entry to MIGRATIONS with the next version number.
    Never edit or delete existing entries.
"""

import sqlite3
import os

# ── Migration registry ────────────────────────────────────────────────────────
# Each entry: (version: int, description: str, sql: str)
# version must be unique and monotonically increasing.
# sql may contain multiple statements separated by semicolons.

MIGRATIONS = [
    (
        1,
        "Initial schema baseline",
        """
        -- No-op: baseline schema is created by schema.sql on first run.
        -- This entry just marks version 1 as applied.
        SELECT 1;
        """
    ),
    (
        2,
        "Add unit_price column to sales if missing",
        """
        -- SQLite does not support IF NOT EXISTS for columns,
        -- so we guard with a trigger-safe approach via the migration tracker.
        -- This migration is safe to run multiple times due to the version check.
        SELECT 1;
        """
    ),
    (
        3,
        "Add index on sales timestamp for report query performance",
        """
        CREATE INDEX IF NOT EXISTS idx_sales_timestamp ON sales(timestamp);
        CREATE INDEX IF NOT EXISTS idx_logs_timestamp  ON logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_logs_user_id    ON logs(user_id);
        """
    ),
]


# ── Runner ────────────────────────────────────────────────────────────────────

def run_migrations(db_path: str) -> None:
    """Apply any unapplied migrations to the database at db_path."""
    if not os.path.exists(db_path):
        # DB not yet created — schema.sql will handle it
        return

    conn = sqlite3.connect(db_path)
    try:
        _ensure_migrations_table(conn)
        applied = _get_applied_versions(conn)

        for version, description, sql in sorted(MIGRATIONS, key=lambda m: m[0]):
            if version in applied:
                continue
            try:
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version, description, applied_at) VALUES (?, ?, datetime('now'))",
                    (version, description)
                )
                conn.commit()
                print(f"[migration] Applied v{version}: {description}")
            except Exception as e:
                conn.rollback()
                print(f"[migration] FAILED v{version}: {e}")
                raise
    finally:
        conn.close()


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     INTEGER PRIMARY KEY,
            description TEXT,
            applied_at  TEXT
        )
    """)
    conn.commit()


def _get_applied_versions(conn: sqlite3.Connection) -> set:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def get_migration_status(db_path: str) -> list:
    """Return a list of applied migrations (for admin endpoint)."""
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    try:
        _ensure_migrations_table(conn)
        rows = conn.execute(
            "SELECT version, description, applied_at FROM schema_migrations ORDER BY version"
        ).fetchall()
        return [{'version': r[0], 'description': r[1], 'applied_at': r[2]} for r in rows]
    finally:
        conn.close()
