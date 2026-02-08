from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QProgressBar, QLabel
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal as CoreSignal, QObject

from src.db.database import get_connection
from src.ui.widgets.sidebar import Sidebar
from src.ui.library_view import LibraryView
from src.ui.detail_view import DetailView
from src.ui.settings_dialog import SettingsDialog
from src.player.player_window import PlayerWindow
from src.library.scanner import scan_folder, save_scan_results, get_all_folders, remove_missing_files
from src.library.identifier import identify_videos
from src.library.watcher import FolderWatcher
from src.debug_log import log


class ScanWorker(QObject):
    """Background worker for scanning folders and identifying videos."""
    progress = CoreSignal(str)
    finished = CoreSignal()

    def run(self):
        try:
            folders = get_all_folders()
            total = len(folders)
            for i, folder in enumerate(folders):
                self.progress.emit(f"Scanning folder {i + 1}/{total}...")
                videos = scan_folder(folder["path"], folder["id"])
                save_scan_results(videos)

            self.progress.emit("Removing missing files...")
            remove_missing_files()

            self.progress.emit("Identifying videos & fetching metadata...")
            identify_videos()
        except Exception as e:
            print(f"[Scan] Error during scanning: {e}")
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MediaPlayer")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self._player_windows = []
        self._scan_thread = None
        self._watcher = FolderWatcher(self)
        self._watcher.folders_changed.connect(self._on_folders_changed)

        self._setup_ui()
        self._connect_signals()

        QTimer.singleShot(100, self._initial_scan)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Content area (sidebar + stack)
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = Sidebar()
        layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()

        self._library_view = LibraryView()
        self._detail_view = DetailView()

        self._stack.addWidget(self._library_view)  # 0
        self._stack.addWidget(self._detail_view)    # 1

        layout.addWidget(self._stack, 1)

        main_layout.addWidget(content, 1)

        # Progress bar at the bottom
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # indeterminate
        self._progress_bar.setFixedHeight(22)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("  %v")
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a1a;
                border: none;
                color: #b3b3b3;
                font-size: 12px;
                text-align: left;
            }
            QProgressBar::chunk {
                background-color: #e50914;
            }
        """)
        self._progress_bar.hide()
        main_layout.addWidget(self._progress_bar)

        self._sidebar.set_active("all")

    def _connect_signals(self):
        self._sidebar.navigation_clicked.connect(self._on_navigation)

        self._library_view.video_selected.connect(self._show_detail)
        self._library_view.video_play_requested.connect(self._play_video)
        self._library_view.show_selected.connect(self._show_tv_detail)

        self._detail_view.play_requested.connect(self._play_video)
        self._detail_view.back_requested.connect(self._show_library)
        self._detail_view.subtitle_downloaded.connect(self._on_subtitle_downloaded)

    def _on_navigation(self, key: str):
        if key == "settings":
            self._open_settings()
        else:
            self._library_view.set_category(key)
            self._stack.setCurrentIndex(0)

    def _show_detail(self, video_id: int):
        self._detail_view.show_video(video_id)
        self._stack.setCurrentIndex(1)

    def _show_tv_detail(self, tmdb_id: int):
        self._detail_view.show_tv_show(tmdb_id)
        self._stack.setCurrentIndex(1)

    def _show_library(self):
        self._stack.setCurrentIndex(0)

    def _play_video(self, video_id: int):
        log("MAIN", f"_play_video() called with video_id={video_id}")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT file_path, play_position FROM videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            log("MAIN", f"No video found in DB for id={video_id}")
            return

        import os
        file_path = row["file_path"]
        log("MAIN", f"DB returned file_path={file_path}, exists={os.path.exists(file_path)}, play_position={row['play_position']}")

        player = PlayerWindow()
        player.setMinimumSize(800, 500)
        player.resize(1024, 600)
        player.closed.connect(self._on_player_closed)
        log("MAIN", "Calling player.show()")
        player.show()
        log("MAIN", f"Calling player.play_file(), player visible={player.isVisible()}")
        player.play_file(file_path, video_id, row["play_position"] or 0)
        self._player_windows.append(player)
        log("MAIN", "Player setup complete")

    def _on_player_closed(self, video_id: int, position: float):
        if video_id:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE videos SET play_position = ?, play_count = play_count + 1, "
                "last_played = CURRENT_TIMESTAMP WHERE id = ?",
                (position, video_id),
            )
            conn.commit()
            conn.close()

        self._player_windows = [w for w in self._player_windows if w.isVisible()]

    def _on_subtitle_downloaded(self, subtitle_path: str):
        for player in self._player_windows:
            if player.isVisible():
                player.add_subtitle(subtitle_path)
                break

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.folders_changed.connect(self._rescan_all)
        dialog.exec()

    def _initial_scan(self):
        folders = get_all_folders()
        if folders:
            self._watcher.watch([f["path"] for f in folders])
            self._rescan_all()

    def _rescan_all(self):
        if self._scan_thread and self._scan_thread.isRunning():
            return  # Already scanning

        folders = get_all_folders()
        self._watcher.watch([f["path"] for f in folders])

        # Show progress bar
        self._progress_bar.show()
        self._progress_bar.setFormat("  Starting scan...")

        # Create worker and thread
        self._scan_thread = QThread()
        self._scan_worker = ScanWorker()
        self._scan_worker.moveToThread(self._scan_thread)

        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.finished.connect(self._scan_thread.quit)

        self._scan_thread.start()

    def _on_scan_progress(self, message: str):
        self._progress_bar.setFormat(f"  {message}")

    def _on_scan_finished(self):
        self._progress_bar.hide()
        self._library_view.refresh()

    def _on_folders_changed(self):
        QTimer.singleShot(1000, self._rescan_all)
