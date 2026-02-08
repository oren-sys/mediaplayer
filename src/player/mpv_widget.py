import mpv
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal, Qt
from src.debug_log import log


class MpvWidget(QWidget):
    position_changed = Signal(float)   # current position in seconds
    duration_changed = Signal(float)   # total duration in seconds
    pause_changed = Signal(bool)       # True if paused
    eof_reached = Signal()
    file_loaded = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setMinimumSize(640, 360)
        self.setStyleSheet("background-color: black;")

        self._player = None
        self._duration = 0
        self._start_position = 0

    def init_mpv(self):
        wid = int(self.winId())
        log("MPV", f"init_mpv() called, winId={wid}, widget visible={self.isVisible()}, native={self.testAttribute(Qt.WidgetAttribute.WA_NativeWindow)}")

        def mpv_log_handler(loglevel, component, message):
            log("MPV-INTERNAL", f"[{loglevel}] {component}: {message}")

        try:
            self._player = mpv.MPV(
                wid=str(wid),
                vo="gpu",
                hwdec="auto",
                keep_open="yes",
                osd_level=0,
                input_default_bindings=False,
                input_vo_keyboard=False,
                log_handler=mpv_log_handler,
                loglevel="info",
            )
            log("MPV", "GPU init succeeded")
        except Exception as e:
            log("MPV", f"GPU init failed: {e}")
            # Fallback without gpu
            try:
                self._player = mpv.MPV(
                    wid=str(wid),
                    hwdec="auto",
                    keep_open="yes",
                    osd_level=0,
                    input_default_bindings=False,
                    input_vo_keyboard=False,
                    log_handler=mpv_log_handler,
                    loglevel="info",
                )
                log("MPV", "Fallback init succeeded (no gpu)")
            except Exception as e2:
                log("MPV", f"Fallback init also failed: {e2}")
                return

        @self._player.property_observer("time-pos")
        def on_time_pos(_name, value):
            if value is not None:
                self.position_changed.emit(value)

        @self._player.property_observer("duration")
        def on_duration(_name, value):
            if value is not None:
                self._duration = value
                self.duration_changed.emit(value)
                log("MPV", f"Duration detected: {value}s")

        @self._player.property_observer("pause")
        def on_pause(_name, value):
            if value is not None:
                self.pause_changed.emit(value)

        @self._player.property_observer("eof-reached")
        def on_eof(_name, value):
            if value:
                log("MPV", "EOF reached")
                self.eof_reached.emit()

        @self._player.event_callback("file-loaded")
        def on_file_loaded(event):
            log("MPV", f"file-loaded event fired")
            if self._start_position > 0:
                try:
                    self._player.seek(self._start_position, "absolute")
                except Exception:
                    pass
                self._start_position = 0
            self.file_loaded.emit()

        @self._player.event_callback("end-file")
        def on_end_file(event):
            log("MPV", f"end-file event fired: {event}")

        log("MPV", "All observers and callbacks registered")

    def play(self, file_path: str, start_position: float = 0):
        # Normalize path: convert forward slashes to backslashes for Windows/mpv compatibility
        # Critical for UNC paths: //server/share must become \\server\share
        file_path = file_path.replace("/", "\\")
        log("MPV", f"play() called: file_path={file_path}, start_position={start_position}")
        if self._player is None:
            log("MPV", "Player is None, calling init_mpv()")
            self.init_mpv()
        if self._player is None:
            log("MPV", "FATAL: Cannot play - player failed to initialize (still None after init)")
            return
        self._start_position = start_position
        try:
            log("MPV", f"Calling self._player.play({file_path})")
            self._player.play(file_path)
            log("MPV", "play() call returned successfully")
        except Exception as e:
            log("MPV", f"Error playing file: {e}")

    def toggle_pause(self):
        if self._player:
            self._player.pause = not self._player.pause

    def seek(self, position: float):
        if self._player:
            self._player.seek(position, "absolute")

    def seek_relative(self, seconds: float):
        if self._player:
            self._player.seek(seconds, "relative")

    def set_volume(self, volume: int):
        if self._player:
            self._player.volume = volume

    def get_volume(self) -> int:
        if self._player:
            return int(self._player.volume or 100)
        return 100

    @property
    def is_paused(self) -> bool:
        if self._player:
            return bool(self._player.pause)
        return True

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def position(self) -> float:
        if self._player and self._player.time_pos is not None:
            return self._player.time_pos
        return 0

    def get_subtitle_tracks(self) -> list:
        if not self._player:
            return []
        tracks = []
        for track in self._player.track_list:
            if track.get("type") == "sub":
                tracks.append({
                    "id": track["id"],
                    "title": track.get("title", ""),
                    "lang": track.get("lang", ""),
                    "external": track.get("external", False),
                })
        return tracks

    def set_subtitle_track(self, track_id: int):
        if self._player:
            self._player.sid = track_id

    def add_subtitle(self, file_path: str):
        if self._player:
            self._player.sub_add(file_path)

    def stop(self):
        if self._player:
            self._player.stop()

    def cleanup(self):
        if self._player:
            self._player.terminate()
            self._player = None
