from src.db.database import init_db
from src.ui.main_window import MainWindow


class MediaPlayerApp(MainWindow):
    def __init__(self):
        init_db()
        super().__init__()
