from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent

from src.player.mpv_widget import MpvWidget
from src.player.controls import PlayerControls
from src.debug_log import log


class PlayerWindow(QWidget):
    closed = Signal(int, float)  # video_id, last_position

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self._video_id = None
        self._is_fullscreen = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.mpv = MpvWidget()
        self.controls = PlayerControls()

        layout.addWidget(self.mpv, 1)
        layout.addWidget(self.controls)

    def _connect_signals(self):
        self.mpv.position_changed.connect(self._on_position)
        self.mpv.duration_changed.connect(self._on_duration)
        self.mpv.pause_changed.connect(self._on_pause)
        self.mpv.file_loaded.connect(self._on_file_loaded)

        self.controls.play_pause_clicked.connect(self.mpv.toggle_pause)
        self.controls.stop_clicked.connect(self._on_stop)
        self.controls.seek_requested.connect(self._on_seek)
        self.controls.volume_changed.connect(self.mpv.set_volume)
        self.controls.subtitle_track_selected.connect(self.mpv.set_subtitle_track)
        self.controls.fullscreen_clicked.connect(self.toggle_fullscreen)

    def play_file(self, file_path: str, video_id: int = None, start_position: float = 0):
        log("PLAYER", f"play_file() called: file={file_path}, video_id={video_id}, start_pos={start_position}")
        log("PLAYER", f"PlayerWindow visible={self.isVisible()}, mpv widget visible={self.mpv.isVisible()}")
        self._video_id = video_id
        self.mpv.play(file_path, start_position)
        self.setWindowTitle(file_path.split("\\")[-1].split("/")[-1])

    def _on_position(self, pos: float):
        self.controls.update_position(pos, self.mpv.duration)

    def _on_duration(self, dur: float):
        pass

    def _on_pause(self, paused: bool):
        self.controls.set_playing(not paused)

    def _on_file_loaded(self):
        tracks = self.mpv.get_subtitle_tracks()
        self.controls.update_subtitle_tracks(tracks)
        self.controls.set_playing(True)

    def _on_stop(self):
        self.mpv.stop()
        self.controls.set_playing(False)

    def _on_seek(self, ratio: float):
        self.mpv.seek(ratio * self.mpv.duration)

    def add_subtitle(self, file_path: str):
        self.mpv.add_subtitle(file_path)
        tracks = self.mpv.get_subtitle_tracks()
        self.controls.update_subtitle_tracks(tracks)

    def toggle_fullscreen(self):
        if self._is_fullscreen:
            self.showNormal()
            self.controls.show()
        else:
            self.showFullScreen()
        self._is_fullscreen = not self._is_fullscreen

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.mpv.toggle_pause()
        elif key == Qt.Key.Key_F or key == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif key == Qt.Key.Key_Right:
            self.mpv.seek_relative(10)
        elif key == Qt.Key.Key_Left:
            self.mpv.seek_relative(-10)
        elif key == Qt.Key.Key_Up:
            vol = min(100, self.mpv.get_volume() + 5)
            self.mpv.set_volume(vol)
        elif key == Qt.Key.Key_Down:
            vol = max(0, self.mpv.get_volume() - 5)
            self.mpv.set_volume(vol)
        elif key == Qt.Key.Key_Escape:
            if self._is_fullscreen:
                self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        pos = self.mpv.position
        self.closed.emit(self._video_id or 0, pos)
        self.mpv.cleanup()
        super().closeEvent(event)
