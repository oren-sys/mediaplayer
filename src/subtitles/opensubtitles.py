import hashlib
import os
import struct
import requests
from typing import Optional


OPENSUBTITLES_API = "https://api.opensubtitles.com/api/v1"


class OpenSubtitlesClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENSUBTITLES_API_KEY", "")

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Api-Key"] = self.api_key
        return h

    def search_by_file(self, file_path: str, language: str = "en") -> list[dict]:
        file_hash = self._compute_hash(file_path)
        if not file_hash:
            return []
        return self._search({"moviehash": file_hash, "languages": language})

    def search_by_title(self, title: str, year: int = None, language: str = "en") -> list[dict]:
        params = {"query": title, "languages": language}
        if year:
            params["year"] = year
        return self._search(params)

    def _search(self, params: dict) -> list[dict]:
        try:
            resp = requests.get(
                f"{OPENSUBTITLES_API}/subtitles",
                params=params,
                headers=self._headers(),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("data", []):
                attrs = item.get("attributes", {})
                files = attrs.get("files", [])
                if not files:
                    continue
                results.append({
                    "id": item["id"],
                    "file_id": files[0].get("file_id"),
                    "language": attrs.get("language", ""),
                    "release": attrs.get("release", ""),
                    "download_count": attrs.get("download_count", 0),
                    "ratings": attrs.get("ratings", 0),
                    "file_name": files[0].get("file_name", ""),
                })
            return results
        except requests.RequestException:
            return []

    def download(self, file_id: int, save_dir: str, filename: str = None) -> Optional[str]:
        try:
            resp = requests.post(
                f"{OPENSUBTITLES_API}/download",
                json={"file_id": file_id},
                headers=self._headers(),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            download_url = data.get("link")
            if not download_url:
                return None

            sub_resp = requests.get(download_url, timeout=30)
            sub_resp.raise_for_status()

            if not filename:
                filename = data.get("file_name", f"{file_id}.srt")
            save_path = os.path.join(save_dir, filename)
            with open(save_path, "wb") as f:
                f.write(sub_resp.content)
            return save_path
        except requests.RequestException:
            return None

    def get_browser_search_url(self, title: str, year: int = None) -> str:
        query = title
        if year:
            query += f" {year}"
        query = query.replace(" ", "+")
        return f"https://www.opensubtitles.org/pb/search/subs?q={query}"

    @staticmethod
    def _compute_hash(file_path: str) -> Optional[str]:
        """Compute OpenSubtitles hash for a video file."""
        try:
            file_size = os.path.getsize(file_path)
            if file_size < 65536 * 2:
                return None

            hash_val = file_size
            with open(file_path, "rb") as f:
                for _ in range(65536 // 8):
                    buf = f.read(8)
                    (val,) = struct.unpack("<q", buf)
                    hash_val += val
                    hash_val &= 0xFFFFFFFFFFFFFFFF

                f.seek(-65536, 2)
                for _ in range(65536 // 8):
                    buf = f.read(8)
                    (val,) = struct.unpack("<q", buf)
                    hash_val += val
                    hash_val &= 0xFFFFFFFFFFFFFFFF

            return f"{hash_val:016x}"
        except (OSError, struct.error):
            return None
