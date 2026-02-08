from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class Video:
    id: Optional[int] = None
    file_path: str = ""
    folder_id: Optional[int] = None
    title: str = ""
    category: str = "uncategorized"
    tmdb_id: Optional[int] = None
    show_name: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    last_played: Optional[str] = None
    play_count: int = 0
    play_position: float = 0
    created_at: Optional[str] = None

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return Video(**{k: row[k] for k in row.keys()})


@dataclass
class Metadata:
    id: Optional[int] = None
    tmdb_id: int = 0
    title: str = ""
    original_title: str = ""
    year: Optional[int] = None
    plot: str = ""
    rating: Optional[float] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    genres: list = field(default_factory=list)
    cast_info: list = field(default_factory=list)
    media_type: str = "movie"
    season_count: Optional[int] = None
    episode_count: Optional[int] = None
    fetched_at: Optional[str] = None

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        data = {k: row[k] for k in row.keys()}
        if isinstance(data.get("genres"), str):
            data["genres"] = json.loads(data["genres"]) if data["genres"] else []
        if isinstance(data.get("cast_info"), str):
            data["cast_info"] = json.loads(data["cast_info"]) if data["cast_info"] else []
        return Metadata(**data)

    def genres_json(self):
        return json.dumps(self.genres)

    def cast_json(self):
        return json.dumps(self.cast_info)
