import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QMouseEvent


class VideoCard(QFrame):
    clicked = Signal(int)
    double_clicked = Signal(int)

    def __init__(self, video_id: int, title: str, poster_path: str = None,
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.video_id = video_id
        self.setObjectName("videoCard")
        self.setFixedSize(160, 280)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui(title, poster_path, subtitle)

    def _setup_ui(self, title: str, poster_path: str, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        poster_label = QLabel()
        poster_label.setFixedSize(152, 228)
        poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        poster_label.setStyleSheet("background-color: #252540; border-radius: 6px;")

        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path).scaled(
                152, 228,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            poster_label.setPixmap(pixmap)
        else:
            poster_label.setText("🎬")
            poster_label.setStyleSheet(
                "background-color: #252540; border-radius: 6px; "
                "font-size: 40px; color: #5555aa;"
            )

        layout.addWidget(poster_label)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(32)
        layout.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setObjectName("cardSubtitle")
            layout.addWidget(sub_label)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.video_id)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.video_id)
