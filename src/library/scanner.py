import os
from src.db.database import get_connection

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".webm", ".flv", ".mov", ".wmv", ".m4v",
    ".mpg", ".mpeg", ".ts", ".vob", ".3gp", ".ogv", ".divx",
}


def scan_folder(folder_path: str, folder_id: int) -> list[dict]:
    found = []
    for root, _dirs, files in os.walk(folder_path):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                full_path = os.path.join(root, name)
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    size = 0
                found.append({
                    "file_path": full_path,
                    "folder_id": folder_id,
                    "title": os.path.splitext(name)[0],
                    "file_size": size,
                })
    return found


def save_scan_results(videos: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()
    for v in videos:
        cursor.execute(
            """INSERT OR IGNORE INTO videos (file_path, folder_id, title, file_size)
               VALUES (?, ?, ?, ?)""",
            (v["file_path"], v["folder_id"], v["title"], v["file_size"]),
        )
    conn.commit()
    conn.close()


def remove_missing_files():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_path FROM videos")
    to_remove = []
    for row in cursor.fetchall():
        if not os.path.exists(row["file_path"]):
            to_remove.append(row["id"])
    if to_remove:
        placeholders = ",".join("?" * len(to_remove))
        cursor.execute(f"DELETE FROM videos WHERE id IN ({placeholders})", to_remove)
        conn.commit()
    conn.close()
    return len(to_remove)


def get_all_folders() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, path, folder_type FROM folders")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r["id"], "path": r["path"], "folder_type": r["folder_type"]} for r in rows]


def add_folder(path: str, folder_type: str = "movies") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO folders (path, folder_type) VALUES (?, ?)", (path, folder_type))
    conn.commit()
    cursor.execute("SELECT id FROM folders WHERE path = ?", (path,))
    row = cursor.fetchone()
    conn.close()
    return row["id"]


def remove_folder(folder_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE folder_id = ?", (folder_id,))
    cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    conn.commit()
    conn.close()
