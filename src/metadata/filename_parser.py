import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedFilename:
    title: str
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    is_tv: bool = False


# Common video junk tokens to strip
_JUNK = re.compile(
    r"\b(1080p|720p|480p|2160p|4k|uhd|hdr|bluray|blu-ray|brrip|bdrip|"
    r"webrip|web-dl|webdl|hdtv|dvdrip|dvdscr|x264|x265|h264|h265|hevc|"
    r"aac|ac3|dts|atmos|5\.1|7\.1|mp3|remux|proper|repack|extended|"
    r"unrated|directors\.cut|remastered|yts|yify|rarbg|eztv|ettv|"
    r"\[.*?\]|\(.*?\))\b",
    re.IGNORECASE,
)

# TV show patterns: S01E02, 1x02, Season 1 Episode 2
_TV_PATTERN = re.compile(
    r"[Ss](\d{1,2})[Ee](\d{1,3})"
    r"|(\d{1,2})[xX](\d{1,3})"
    r"|[Ss]eason\s*(\d{1,2})\s*[Ee]pisode\s*(\d{1,3})",
    re.IGNORECASE,
)

# Year pattern: (2023) or .2023.
_YEAR_PATTERN = re.compile(r"[\.\s\(]?((?:19|20)\d{2})[\.\s\)\]]?")


def parse_filename(filename: str) -> ParsedFilename:
    # Remove extension
    name = re.sub(r"\.\w{2,4}$", "", filename)

    # Replace dots and underscores with spaces
    name = name.replace(".", " ").replace("_", " ")

    # Check for TV show pattern
    tv_match = _TV_PATTERN.search(name)
    season = None
    episode = None
    is_tv = False

    if tv_match:
        is_tv = True
        groups = tv_match.groups()
        if groups[0] is not None:
            season, episode = int(groups[0]), int(groups[1])
        elif groups[2] is not None:
            season, episode = int(groups[2]), int(groups[3])
        elif groups[4] is not None:
            season, episode = int(groups[4]), int(groups[5])
        # Title is everything before the TV pattern
        name = name[:tv_match.start()]

    # Extract year
    year = None
    year_match = _YEAR_PATTERN.search(name)
    if year_match:
        year = int(year_match.group(1))
        # Title is everything before the year
        name = name[:year_match.start()]

    # Clean junk tokens
    name = _JUNK.sub("", name)

    # Clean up whitespace
    title = re.sub(r"\s+", " ", name).strip().strip("-").strip()

    return ParsedFilename(
        title=title,
        year=year,
        season=season,
        episode=episode,
        is_tv=is_tv,
    )
