from PySide6.QtCore import QFileSystemWatcher, QObject, Signal


class FolderWatcher(QObject):
    folders_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_changed)

    def watch(self, folder_paths: list[str]):
        current = self._watcher.directories()
        if current:
            self._watcher.removePaths(current)
        if folder_paths:
            self._watcher.addPaths(folder_paths)

    def _on_changed(self, _path: str):
        self.folders_changed.emit()
