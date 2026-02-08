from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QLabel, QComboBox
)
from PySide6.QtCore import Signal, Qt


def _format_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class PlayerControls(QFrame):
    play_pause_clicked = Signal()
    stop_clicked = Signal()
    seek_requested = Signal(float)
    volume_changed = Signal(int)
    subtitle_track_selected = Signal(int)
    fullscreen_clicked = Signal()
    subtitle_download_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("playerControls")
        self.setFixedHeight(90)
        self._is_seeking = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)

        # Seek bar row
        seek_row = QHBoxLayout()
        self._time_label = QLabel("0:00")
        self._time_label.setFixedWidth(60)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setRange(0, 1000)
        self._seek_slider.sliderPressed.connect(self._on_seek_pressed)
        self._seek_slider.sliderReleased.connect(self._on_seek_released)
        self._seek_slider.sliderMoved.connect(self._on_seek_moved)

        self._duration_label = QLabel("0:00")
        self._duration_label.setFixedWidth(60)
        self._duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        seek_row.addWidget(self._time_label)
        seek_row.addWidget(self._seek_slider)
        seek_row.addWidget(self._duration_label)
        layout.addLayout(seek_row)

        # Controls row
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        self._play_btn = QPushButton("▶")
        self._play_btn.setObjectName("playerBtn")
        self._play_btn.setFixedSize(40, 40)
        self._play_btn.clicked.connect(self.play_pause_clicked.emit)

        self._stop_btn = QPushButton("⏹")
        self._stop_btn.setObjectName("playerBtn")
        self._stop_btn.setFixedSize(40, 40)
        self._stop_btn.clicked.connect(self.stop_clicked.emit)

        controls_row.addWidget(self._play_btn)
        controls_row.addWidget(self._stop_btn)
        controls_row.addStretch()

        # Subtitle controls
        self._sub_combo = QComboBox()
        self._sub_combo.setMinimumWidth(150)
        self._sub_combo.addItem("No Subtitles", 0)
        self._sub_combo.currentIndexChanged.connect(self._on_subtitle_changed)
        controls_row.addWidget(QLabel("Subs:"))
        controls_row.addWidget(self._sub_combo)

        self._sub_download_btn = QPushButton("⬇ Subs")
        self._sub_download_btn.setObjectName("secondaryBtn")
        self._sub_download_btn.clicked.connect(self.subtitle_download_clicked.emit)
        controls_row.addWidget(self._sub_download_btn)

        controls_row.addStretch()

        # Volume
        vol_label = QLabel("🔊")
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(100)
        self._volume_slider.setFixedWidth(100)
        self._volume_slider.valueChanged.connect(self.volume_changed.emit)

        controls_row.addWidget(vol_label)
        controls_row.addWidget(self._volume_slider)

        # Fullscreen
        self._fs_btn = QPushButton("⛶")
        self._fs_btn.setObjectName("playerBtn")
        self._fs_btn.setFixedSize(40, 40)
        self._fs_btn.clicked.connect(self.fullscreen_clicked.emit)
        controls_row.addWidget(self._fs_btn)

        layout.addLayout(controls_row)

    def _on_seek_pressed(self):
        self._is_seeking = True

    def _on_seek_released(self):
        self._is_seeking = False
        value = self._seek_slider.value()
        self.seek_requested.emit(value / 1000.0)

    def _on_seek_moved(self, value):
        # Update time label during drag
        ratio = value / 1000.0
        self._time_label.setText(_format_time(ratio * self._total_duration))

    def _on_subtitle_changed(self, index):
        track_id = self._sub_combo.itemData(index)
        if track_id is not None:
            self.subtitle_track_selected.emit(track_id)

    def update_position(self, position: float, duration: float):
        self._total_duration = duration
        if not self._is_seeking and duration > 0:
            self._seek_slider.setValue(int((position / duration) * 1000))
        self._time_label.setText(_format_time(position))
        self._duration_label.setText(_format_time(duration))

    def set_playing(self, playing: bool):
        self._play_btn.setText("⏸" if playing else "▶")

    def update_subtitle_tracks(self, tracks: list):
        self._sub_combo.blockSignals(True)
        self._sub_combo.clear()
        self._sub_combo.addItem("No Subtitles", 0)
        for track in tracks:
            label = track.get("lang", "") or track.get("title", "") or f"Track {track['id']}"
            if track.get("external"):
                label += " (ext)"
            self._sub_combo.addItem(label, track["id"])
        self._sub_combo.blockSignals(False)

    _total_duration = 0
