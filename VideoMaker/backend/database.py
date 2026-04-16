import sqlite3
from pathlib import Path
from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id              TEXT PRIMARY KEY,
                style           TEXT NOT NULL,
                title           TEXT,
                status          TEXT DEFAULT 'pending',
                created_at      TEXT,
                started_at      TEXT,
                completed_at    TEXT,
                output_video_path TEXT,
                output_dir      TEXT,
                log_file        TEXT,
                error_message   TEXT,
                youtube_video_id TEXT,
                youtube_status   TEXT
            )
        """)
        # Migration légère pour anciens schémas (ajout colonnes si manquantes)
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)")}
        if "youtube_video_id" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN youtube_video_id TEXT")
        if "youtube_status" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN youtube_status TEXT")
        if "youtube_params" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN youtube_params TEXT")
        conn.commit()


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row) if row else None
