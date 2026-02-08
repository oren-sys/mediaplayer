import os
import webbrowser
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QMouseEvent

from src.db.database import get_connection
from src.db.models import Video, Metadata
from src.subtitles.opensubtitles import OpenSubtitlesClient


class DetailView(QWidget):
    play_requested = Signal(int)
    back_requested = Signal()
    subtitle_downloaded = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video = None
        self._meta = None
        self._episodes = []
        self._setup_ui()

    def _setup_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._scroll_content = QWidget()
        self._layout = QVBoxLayout(self._scroll_content)
        self._layout.setContentsMargins(24, 20, 24, 20)
        self._layout.setSpacing(0)
        scroll.setWidget(self._scroll_content)

        self._main_layout.addWidget(scroll)

        # Back button
        back_btn = QPushButton("< Back")
        back_btn.setObjectName("secondaryBtn")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.back_requested.emit)
        self._layout.addWidget(back_btn)
        self._layout.addSpacing(16)

        # Hero section
        self._hero = QHBoxLayout()

        self._poster_label = QLabel()
        self._poster_label.setFixedSize(220, 330)
        self._poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._poster_label.setStyleSheet("background-color: #252540; border-radius: 8px;")
        self._hero.addWidget(self._poster_label)
        self._hero.addSpacing(24)

        details = QVBoxLayout()
        details.setSpacing(6)

        self._title_label = QLabel()
        self._title_label.setObjectName("detailTitle")
        self._title_label.setWordWrap(True)
        details.addWidget(self._title_label)

        self._info_label = QLabel()
        self._info_label.setStyleSheet("color: #999999; font-size: 14px;")
        details.addWidget(self._info_label)

        self._rating_label = QLabel()
        self._rating_label.setObjectName("ratingLabel")
        details.addWidget(self._rating_label)

        details.addSpacing(12)

        self._plot_label = QLabel()
        self._plot_label.setObjectName("detailPlot")
        self._plot_label.setWordWrap(True)
        details.addWidget(self._plot_label)

        details.addSpacing(8)

        self._cast_label = QLabel()
        self._cast_label.setStyleSheet("color: #b3b3b3; font-size: 12px;")
        self._cast_label.setWordWrap(True)
        details.addWidget(self._cast_label)

        details.addSpacing(16)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._play_btn = QPushButton("Play")
        self._play_btn.setObjectName("playBtnLarge")
        self._play_btn.clicked.connect(self._on_play)
        btn_row.addWidget(self._play_btn)

        self._sub_web_btn = QPushButton("Subtitles")
        self._sub_web_btn.setObjectName("secondaryBtn")
        self._sub_web_btn.clicked.connect(self._on_open_subtitles_web)
        btn_row.addWidget(self._sub_web_btn)

        btn_row.addStretch()
        details.addLayout(btn_row)
        details.addStretch()

        self._hero.addLayout(details, 1)
        self._layout.addLayout(self._hero)

        # Episodes section (for TV shows)
        self._episodes_container = QVBoxLayout()
        self._episodes_container.setSpacing(8)
        self._layout.addSpacing(24)
        self._layout.addLayout(self._episodes_container)
        self._layout.addStretch()

    def show_video(self, video_id: int):
        """Show detail for a single movie/video."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        self._video = Video.from_row(row)
        self._meta = None
        self._episodes = []
        if self._video.tmdb_id:
            cursor.execute("SELECT * FROM metadata WHERE tmdb_id = ?", (self._video.tmdb_id,))
            meta_row = cursor.fetchone()
            if meta_row:
                self._meta = Metadata.from_row(meta_row)
        conn.close()
        self._update_display()

    def show_tv_show(self, tmdb_id: int):
        """Show detail for a TV show with all its episodes grouped."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM metadata WHERE tmdb_id = ?", (tmdb_id,))
        meta_row = cursor.fetchone()
        self._meta = Metadata.from_row(meta_row) if meta_row else None

        cursor.execute(
            """SELECT * FROM videos WHERE tmdb_id = ?
               ORDER BY season_number, episode_number, title""",
            (tmdb_id,),
        )
        rows = cursor.fetchall()
        self._episodes = [Video.from_row(r) for r in rows]
        self._video = self._episodes[0] if self._episodes else None
        conn.close()
        self._update_display()

    def _update_display(self):
        # Clear episodes
        while self._episodes_container.count():
            item = self._episodes_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._meta:
            self._title_label.setText(self._meta.title)

            info_parts = []
            if self._meta.year:
                info_parts.append(str(self._meta.year))
            if self._meta.genres:
                info_parts.append(" · ".join(self._meta.genres[:3]))
            if self._meta.media_type == "tv" and self._meta.season_count:
                info_parts.append(f"{self._meta.season_count} Season{'s' if self._meta.season_count > 1 else ''}")
            self._info_label.setText("  |  ".join(info_parts))

            if self._meta.rating:
                self._rating_label.setText(f"{self._meta.rating:.1f} / 10")
            else:
                self._rating_label.setText("")

            self._plot_label.setText(self._meta.plot or "")

            if self._meta.cast_info:
                cast_names = [c["name"] for c in self._meta.cast_info[:8]]
                self._cast_label.setText("Cast: " + ", ".join(cast_names))
            else:
                self._cast_label.setText("")

            if self._meta.poster_path and os.path.exists(self._meta.poster_path):
                pixmap = QPixmap(self._meta.poster_path).scaled(
                    220, 330,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._poster_label.setPixmap(pixmap)
            else:
                self._poster_label.setText("🎬")
                self._poster_label.setStyleSheet("background-color: #252540; border-radius: 8px; font-size: 48px; color: #555;")
        else:
            self._title_label.setText(self._video.title if self._video else "")
            self._info_label.setText("")
            self._rating_label.setText("")
            self._plot_label.setText("")
            self._cast_label.setText("")
            self._poster_label.setText("🎬")
            self._poster_label.setStyleSheet("background-color: #252540; border-radius: 8px; font-size: 48px; color: #555;")

        # Show episodes for TV shows
        if self._episodes and len(self._episodes) > 1:
            ep_title = QLabel("Episodes")
            ep_title.setObjectName("rowTitle")
            self._episodes_container.addWidget(ep_title)

            # Group by season
            seasons = {}
            for ep in self._episodes:
                s = ep.season_number or 0
                if s not in seasons:
                    seasons[s] = []
                seasons[s].append(ep)

            for season_num in sorted(seasons.keys()):
                eps = seasons[season_num]
                if season_num > 0:
                    season_label = QLabel(f"Season {season_num}")
                    season_label.setStyleSheet("color: #e5e5e5; font-size: 14px; font-weight: bold; padding-top: 8px;")
                    self._episodes_container.addWidget(season_label)

                for ep in eps:
                    item = EpisodeItem(ep)
                    item.play_clicked.connect(self.play_requested.emit)
                    self._episodes_container.addWidget(item)

    def _on_play(self):
        if self._video:
            self.play_requested.emit(self._video.id)

    def _on_open_subtitles_web(self):
        if not self._video:
            return
        client = OpenSubtitlesClient()
        title = self._meta.title if self._meta else self._video.title
        year = self._meta.year if self._meta else None
        url = client.get_browser_search_url(title, year)
        webbrowser.open(url)


class EpisodeItem(QFrame):
    play_clicked = Signal(int)

    def __init__(self, video: Video, parent=None):
        super().__init__(parent)
        self.setObjectName("episodeItem")
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._video_id = video.id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)

        # Episode number
        ep_num = ""
        if video.episode_number is not None:
            ep_num = f"E{video.episode_number}"
        if video.season_number is not None and video.episode_number is not None:
            ep_num = f"S{video.season_number:02d}E{video.episode_number:02d}"

        if ep_num:
            num_label = QLabel(ep_num)
            num_label.setStyleSheet("color: #999999; font-size: 13px; font-weight: bold; min-width: 70px;")
            layout.addWidget(num_label)

        # Filename
        filename = os.path.basename(video.file_path)
        name_label = QLabel(filename)
        name_label.setStyleSheet("color: #e5e5e5; font-size: 13px;")
        layout.addWidget(name_label, 1)

        # File size
        if video.file_size:
            size_mb = video.file_size / (1024 * 1024)
            if size_mb > 1024:
                size_str = f"{size_mb / 1024:.1f} GB"
            else:
                size_str = f"{size_mb:.0f} MB"
            size_label = QLabel(size_str)
            size_label.setStyleSheet("color: #666666; font-size: 12px;")
            layout.addWidget(size_label)

        # Play button
        play_btn = QPushButton("▶")
        play_btn.setObjectName("playerBtn")
        play_btn.setFixedSize(32, 32)
        play_btn.clicked.connect(lambda: self.play_clicked.emit(self._video_id))
        layout.addWidget(play_btn)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.play_clicked.emit(self._video_id)
