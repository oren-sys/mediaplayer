import os
from src.db.database import get_connection
from src.metadata.filename_parser import parse_filename
from src.metadata.tmdb_client import TMDBClient


def identify_videos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, v.file_path, v.title, f.folder_type
        FROM videos v
        JOIN folders f ON v.folder_id = f.id
        WHERE v.tmdb_id IS NULL
    """)
    unidentified = cursor.fetchall()
    conn.close()

    if not unidentified:
        return

    client = TMDBClient()

    for row in unidentified:
        filename = os.path.basename(row["file_path"])
        parsed = parse_filename(filename)
        folder_type = row["folder_type"]

        # Personal videos: skip TMDB lookup
        if folder_type == "personal":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE videos SET title = ?, category = 'personal' WHERE id = ?",
                (parsed.title, row["id"]),
            )
            conn.commit()
            conn.close()
            continue

        result = None
        media_type = None

        # Use folder type as primary hint
        if folder_type == "tv_shows" or parsed.is_tv:
            result = client.search_tv(parsed.title, parsed.year)
            media_type = "tv"

        if not result and folder_type != "tv_shows":
            result = client.search_movie(parsed.title, parsed.year)
            media_type = "movie"

        if not result and media_type != "tv":
            result = client.search_tv(parsed.title, parsed.year)
            media_type = "tv"

        if result:
            tmdb_id = result["id"]
            category = "tv_show" if media_type == "tv" else "movie"

            if media_type == "tv":
                meta = client.get_tv_details(tmdb_id)
            else:
                meta = client.get_movie_details(tmdb_id)

            if meta:
                _save_metadata(meta)

            display_title = meta.title if meta else parsed.title
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE videos SET tmdb_id = ?, category = ?, title = ?,
                   show_name = ?, season_number = ?, episode_number = ?
                   WHERE id = ?""",
                (
                    tmdb_id, category, display_title,
                    display_title if category == "tv_show" else None,
                    parsed.season, parsed.episode,
                    row["id"],
                ),
            )
            conn.commit()
            conn.close()
        else:
            # Use folder type as fallback category when TMDB lookup fails
            _fallback = {"movies": "movie", "tv_shows": "tv_show", "personal": "personal"}
            category = _fallback.get(folder_type, "uncategorized")
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE videos SET title = ?, category = ? WHERE id = ?",
                (parsed.title, category, row["id"]),
            )
            conn.commit()
            conn.close()


def _save_metadata(meta):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO metadata
           (tmdb_id, title, original_title, year, plot, rating,
            poster_path, backdrop_path, genres, cast_info, media_type,
            season_count, episode_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            meta.tmdb_id, meta.title, meta.original_title, meta.year,
            meta.plot, meta.rating, meta.poster_path, meta.backdrop_path,
            meta.genres_json(), meta.cast_json(), meta.media_type,
            meta.season_count, meta.episode_count,
        ),
    )
    conn.commit()
    conn.close()
