from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QGridLayout, QFrame
)
from PySide6.QtCore import Signal, Qt

from src.db.database import get_connection
from src.db.models import Video, Metadata
from src.ui.widgets.video_card import VideoCard


class LibraryView(QWidget):
    video_selected = Signal(int)       # video id (for movies/personal)
    video_play_requested = Signal(int) # video id
    show_selected = Signal(int)        # tmdb_id (for TV shows - opens show detail)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_category = "all"
        self._search_text = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        # Header
        header = QHBoxLayout()
        self._title_label = QLabel("All Videos")
        self._title_label.setObjectName("sectionTitle")
        header.addWidget(self._title_label)
        header.addStretch()

        self._search = QLineEdit()
        self._search.setObjectName("searchBar")
        self._search.setPlaceholderText("Search...")
        self._search.setFixedWidth(280)
        self._search.textChanged.connect(self._on_search)
        header.addWidget(self._search)

        layout.addLayout(header)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setSpacing(24)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._content_widget)

        layout.addWidget(self._scroll)

    def set_category(self, category: str):
        self._current_category = category
        titles = {
            "all": "All Videos",
            "movie": "Movies",
            "tv_show": "TV Shows",
            "personal": "Personal Videos",
        }
        self._title_label.setText(titles.get(category, "Videos"))
        self.refresh()

    def _on_search(self, text: str):
        self._search_text = text.strip().lower()
        self.refresh()

    def refresh(self):
        # Clear content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        if self._current_category == "tv_show":
            self._build_tv_shows_view()
        elif self._current_category == "all":
            self._build_all_view()
        else:
            self._build_grid_view(self._current_category)

    def _build_all_view(self):
        # Movies row
        movies = self._fetch_items("movie")
        if movies:
            self._add_row("Movies", movies, is_movie=True)

        # TV Shows row (grouped)
        shows = self._fetch_tv_shows()
        if shows:
            self._add_show_row("TV Shows", shows)

        # Personal row
        personal = self._fetch_items("personal")
        if personal:
            self._add_row("Personal Videos", personal, is_movie=True)

        # Uncategorized row
        uncategorized = self._fetch_items("uncategorized")
        if uncategorized:
            self._add_row("Uncategorized", uncategorized, is_movie=True)

        if not movies and not shows and not personal and not uncategorized:
            self._add_empty_message()

    def _build_tv_shows_view(self):
        shows = self._fetch_tv_shows()
        if not shows:
            self._add_empty_message()
            return
        self._add_show_row("", shows)

    def _build_grid_view(self, category: str):
        items = self._fetch_items(category)
        if not items:
            self._add_empty_message()
            return

        grid = self._create_card_grid(items, is_movie=True)
        self._content_layout.addLayout(grid)

    def _add_row(self, title: str, items: list, is_movie: bool = True):
        if title:
            lbl = QLabel(title)
            lbl.setObjectName("rowTitle")
            self._content_layout.addWidget(lbl)

        grid = self._create_card_grid(items, is_movie=is_movie)
        self._content_layout.addLayout(grid)

    def _add_show_row(self, title: str, shows: list):
        if title:
            lbl = QLabel(title)
            lbl.setObjectName("rowTitle")
            self._content_layout.addWidget(lbl)

        cols = max(1, (self._scroll.width() - 48) // 175)
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        for i, (tmdb_id, show_name, meta, episode_count) in enumerate(shows):
            subtitle = ""
            poster = None
            if meta:
                parts = []
                if meta.year:
                    parts.append(str(meta.year))
                if meta.rating:
                    parts.append(f"{meta.rating:.1f}")
                parts.append(f"{episode_count} ep")
                subtitle = " · ".join(parts)
                poster = meta.poster_path

            card = VideoCard(tmdb_id, show_name, poster, subtitle)
            card.clicked.connect(self._on_show_clicked)
            card.double_clicked.connect(self._on_show_clicked)
            grid.addWidget(card, i // cols, i % cols)

        self._content_layout.addLayout(grid)

    def _create_card_grid(self, items: list, is_movie: bool = True) -> QGridLayout:
        cols = max(1, (self._scroll.width() - 48) // 175)
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        for i, (video, meta) in enumerate(items):
            subtitle = ""
            poster = None
            if meta:
                parts = []
                if meta.year:
                    parts.append(str(meta.year))
                if meta.rating:
                    parts.append(f"{meta.rating:.1f}")
                if meta.genres:
                    parts.append(meta.genres[0])
                subtitle = " · ".join(parts)
                poster = meta.poster_path

            card = VideoCard(video.id, video.title, poster, subtitle)
            card.clicked.connect(self.video_selected.emit)
            card.double_clicked.connect(self.video_play_requested.emit)
            grid.addWidget(card, i // cols, i % cols)

        return grid

    def _on_show_clicked(self, tmdb_id: int):
        self.show_selected.emit(tmdb_id)

    def _add_empty_message(self):
        empty = QLabel("No videos found. Add folders in Settings to get started.")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setStyleSheet("color: #666666; font-size: 15px; padding: 60px;")
        self._content_layout.addWidget(empty)

    def _fetch_items(self, category: str) -> list[tuple]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM videos WHERE category = ? ORDER BY title COLLATE NOCASE",
            (category,),
        )
        rows = cursor.fetchall()
        results = []
        for row in rows:
            video = Video.from_row(row)
            if self._search_text and self._search_text not in video.title.lower():
                continue
            meta = None
            if video.tmdb_id:
                cursor.execute("SELECT * FROM metadata WHERE tmdb_id = ?", (video.tmdb_id,))
                meta_row = cursor.fetchone()
                if meta_row:
                    meta = Metadata.from_row(meta_row)
            results.append((video, meta))
        conn.close()
        return results

    def _fetch_tv_shows(self) -> list[tuple]:
        """Returns grouped TV shows: [(tmdb_id, show_name, metadata, episode_count)]"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT show_name, tmdb_id, COUNT(*) as ep_count
            FROM videos
            WHERE category = 'tv_show' AND show_name IS NOT NULL
            GROUP BY show_name, tmdb_id
            ORDER BY show_name COLLATE NOCASE
        """)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            if self._search_text and self._search_text not in row["show_name"].lower():
                continue
            meta = None
            if row["tmdb_id"]:
                cursor.execute("SELECT * FROM metadata WHERE tmdb_id = ?", (row["tmdb_id"],))
                meta_row = cursor.fetchone()
                if meta_row:
                    meta = Metadata.from_row(meta_row)
            results.append((row["tmdb_id"], row["show_name"], meta, row["ep_count"]))
        conn.close()
        return results

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh()
