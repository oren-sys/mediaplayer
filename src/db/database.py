import sqlite3
import os
from src.paths import get_data_dir

DB_PATH = os.path.join(get_data_dir(), "media.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE NOT NULL,
            folder_type TEXT DEFAULT 'movies'
        );

        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY,
            file_path TEXT UNIQUE NOT NULL,
            folder_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
            title TEXT,
            category TEXT DEFAULT 'uncategorized',
            tmdb_id INTEGER,
            show_name TEXT,
            season_number INTEGER,
            episode_number INTEGER,
            file_size INTEGER,
            duration REAL,
            last_played TIMESTAMP,
            play_count INTEGER DEFAULT 0,
            play_position REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS metadata (
            id INTEGER PRIMARY KEY,
            tmdb_id INTEGER UNIQUE NOT NULL,
            title TEXT,
            original_title TEXT,
            year INTEGER,
            plot TEXT,
            rating REAL,
            poster_path TEXT,
            backdrop_path TEXT,
            genres TEXT,
            cast_info TEXT,
            media_type TEXT,
            season_count INTEGER,
            episode_count INTEGER,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

    """)

    # Step 2: Migrate old databases (add missing columns before indexes)
    _migrate(cursor)

    # Step 3: Create indexes (columns now guaranteed to exist)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_category ON videos(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_tmdb_id ON videos(tmdb_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_show_name ON videos(show_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_tmdb_id ON metadata(tmdb_id)")

    conn.commit()
    conn.close()


def _migrate(cursor):
    cursor.execute("PRAGMA table_info(folders)")
    folder_cols = {r["name"] for r in cursor.fetchall()}
    if "folder_type" not in folder_cols:
        cursor.execute("ALTER TABLE folders ADD COLUMN folder_type TEXT DEFAULT 'movies'")

    cursor.execute("PRAGMA table_info(videos)")
    video_cols = {r["name"] for r in cursor.fetchall()}
    if "show_name" not in video_cols:
        cursor.execute("ALTER TABLE videos ADD COLUMN show_name TEXT")
    if "season_number" not in video_cols:
        cursor.execute("ALTER TABLE videos ADD COLUMN season_number INTEGER")
    if "episode_number" not in video_cols:
        cursor.execute("ALTER TABLE videos ADD COLUMN episode_number INTEGER")
