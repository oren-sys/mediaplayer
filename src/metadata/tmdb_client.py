import os
import requests
from typing import Optional
from src.db.models import Metadata
from src.paths import get_data_dir

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"


class TMDBClient:
    def __init__(self):
        self.api_key = os.environ.get("TMDB_API_KEY", "")
        self.access_token = os.environ.get("TMDB_ACCESS_TOKEN", "")
        self._poster_cache_dir = os.path.join(get_data_dir(), "posters")
        os.makedirs(self._poster_cache_dir, exist_ok=True)

    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        if not self.api_key and not self.access_token:
            print("[TMDB] No API key or access token configured — skipping lookup")
            return None
        headers = {}
        p = params.copy() if params else {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        else:
            p["api_key"] = self.api_key
        try:
            resp = requests.get(f"{TMDB_BASE}{endpoint}", params=p, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[TMDB] Request failed for {endpoint}: {e}")
            return None

    def search_movie(self, title: str, year: int = None) -> Optional[dict]:
        params = {"query": title}
        if year:
            params["year"] = year
        data = self._get("/search/movie", params)
        if data and data.get("results"):
            return data["results"][0]
        return None

    def search_tv(self, title: str, year: int = None) -> Optional[dict]:
        params = {"query": title}
        if year:
            params["first_air_date_year"] = year
        data = self._get("/search/tv", params)
        if data and data.get("results"):
            return data["results"][0]
        return None

    def get_movie_details(self, tmdb_id: int) -> Optional[Metadata]:
        data = self._get(f"/movie/{tmdb_id}", {"append_to_response": "credits"})
        if not data:
            return None
        return self._build_metadata(data, "movie")

    def get_tv_details(self, tmdb_id: int) -> Optional[Metadata]:
        data = self._get(f"/tv/{tmdb_id}", {"append_to_response": "credits"})
        if not data:
            return None
        return self._build_metadata(data, "tv")

    def _build_metadata(self, data: dict, media_type: str) -> Metadata:
        title = data.get("title") or data.get("name", "")
        original_title = data.get("original_title") or data.get("original_name", "")

        release = data.get("release_date") or data.get("first_air_date", "")
        year = int(release[:4]) if release and len(release) >= 4 else None

        genres = [g["name"] for g in data.get("genres", [])]

        credits = data.get("credits", {})
        cast = [
            {"name": c["name"], "character": c.get("character", "")}
            for c in credits.get("cast", [])[:10]
        ]

        poster_path = None
        if data.get("poster_path"):
            poster_path = self._download_poster(data["poster_path"], data["id"])

        return Metadata(
            tmdb_id=data["id"],
            title=title,
            original_title=original_title,
            year=year,
            plot=data.get("overview", ""),
            rating=data.get("vote_average"),
            poster_path=poster_path,
            backdrop_path=data.get("backdrop_path"),
            genres=genres,
            cast_info=cast,
            media_type=media_type,
            season_count=data.get("number_of_seasons"),
            episode_count=data.get("number_of_episodes"),
        )

    def _download_poster(self, poster_url: str, tmdb_id: int) -> Optional[str]:
        local_path = os.path.join(self._poster_cache_dir, f"{tmdb_id}.jpg")
        if os.path.exists(local_path):
            return local_path
        try:
            url = f"{TMDB_IMAGE_BASE}/w342{poster_url}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(resp.content)
            return local_path
        except requests.RequestException:
            return None
