from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal


class Sidebar(QFrame):
    navigation_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self._buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(0)

        # Logo area
        title = QLabel("  MEDIAPLAYER")
        title.setStyleSheet("color: #e50914; font-size: 20px; font-weight: bold; padding: 12px 20px; letter-spacing: 2px;")
        layout.addWidget(title)

        layout.addSpacing(30)

        categories = [
            ("all", "All Videos"),
            ("movie", "Movies"),
            ("tv_show", "TV Shows"),
            ("personal", "Personal"),
        ]

        for key, label in categories:
            btn = QPushButton(f"  {label}")
            btn.setObjectName("sidebarBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))
            self._buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        settings_btn = QPushButton("  Settings")
        settings_btn.setObjectName("sidebarBtn")
        settings_btn.clicked.connect(lambda: self.navigation_clicked.emit("settings"))
        layout.addWidget(settings_btn)

    def _on_click(self, key: str):
        for k, btn in self._buttons.items():
            btn.setChecked(k == key)
        self.navigation_clicked.emit(key)

    def set_active(self, key: str):
        for k, btn in self._buttons.items():
            btn.setChecked(k == key)
