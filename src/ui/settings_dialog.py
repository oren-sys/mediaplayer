from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QFileDialog, QListWidgetItem, QComboBox
)
from PySide6.QtCore import Signal

from src.library.scanner import get_all_folders, add_folder, remove_folder

FOLDER_TYPE_LABELS = {
    "movies": "Movies",
    "tv_shows": "TV Shows",
    "personal": "Personal Videos",
}


class SettingsDialog(QDialog):
    folders_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(550, 450)
        self._setup_ui()
        self._load_folders()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Media Folders")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        desc = QLabel("Add folders and specify their content type. Videos will be scanned and categorized accordingly.")
        desc.setStyleSheet("color: #999999; margin-bottom: 8px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._folder_list = QListWidget()
        layout.addWidget(self._folder_list)

        btn_row = QHBoxLayout()

        add_btn = QPushButton("+ Add Folder")
        add_btn.setObjectName("actionBtn")
        add_btn.clicked.connect(self._add_folder)
        btn_row.addWidget(add_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.setObjectName("secondaryBtn")
        remove_btn.clicked.connect(self._remove_folder)
        btn_row.addWidget(remove_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addSpacing(16)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("secondaryBtn")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _load_folders(self):
        self._folder_list.clear()
        folders = get_all_folders()
        for f in folders:
            type_label = FOLDER_TYPE_LABELS.get(f["folder_type"], f["folder_type"])
            display = f"{f['path']}  [{type_label}]"
            item = QListWidgetItem(display)
            item.setData(256, f["id"])
            self._folder_list.addItem(item)

    def _add_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not path:
            return

        # Ask user what type of content is in this folder
        dialog = FolderTypeDialog(path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            folder_type = dialog.selected_type()
            add_folder(path, folder_type)
            self._load_folders()
            self.folders_changed.emit()

    def _remove_folder(self):
        item = self._folder_list.currentItem()
        if item:
            folder_id = item.data(256)
            remove_folder(folder_id)
            self._load_folders()
            self.folders_changed.emit()


class FolderTypeDialog(QDialog):
    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Folder Content Type")
        self.setFixedSize(420, 220)
        self._setup_ui(folder_path)

    def _setup_ui(self, folder_path: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("What's in this folder?")
        title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        path_label = QLabel(folder_path)
        path_label.setStyleSheet("color: #999999; font-size: 12px;")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)

        self._combo = QComboBox()
        self._combo.addItem("Movies", "movies")
        self._combo.addItem("TV Shows", "tv_shows")
        self._combo.addItem("Personal Videos", "personal")
        layout.addWidget(self._combo)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("Add Folder")
        ok_btn.setObjectName("actionBtn")
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)

    def selected_type(self) -> str:
        return self._combo.currentData()
