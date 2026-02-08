import sys
import os

# Add project/exe dir to PATH so mpv can find libmpv-2.dll
# PyInstaller places DLLs in _internal/ subdirectory, so we must add both
if getattr(sys, "frozen", False):
    _app_dir = os.path.dirname(sys.executable)
    _internal = os.path.join(_app_dir, "_internal")
    os.environ["PATH"] = _internal + os.pathsep + _app_dir + os.pathsep + os.environ["PATH"]
else:
    os.environ["PATH"] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ["PATH"]

from dotenv import load_dotenv

# Load .env from next to the executable (frozen) or project root (dev)
if getattr(sys, "frozen", False):
    _dotenv_path = os.path.join(os.path.dirname(sys.executable), ".env")
else:
    _dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_dotenv_path)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.paths import get_base_path
from src.debug_log import log
from src.app import MediaPlayerApp

# Log startup info
log("STARTUP", f"frozen={getattr(sys, 'frozen', False)}")
log("STARTUP", f"sys.executable={sys.executable}")
log("STARTUP", f"PATH (first 500 chars)={os.environ.get('PATH', '')[:500]}")
log("STARTUP", f".env path={_dotenv_path}, exists={os.path.exists(_dotenv_path)}")
log("STARTUP", f"TMDB_ACCESS_TOKEN set={'yes' if os.environ.get('TMDB_ACCESS_TOKEN') else 'no'}")

# Check if libmpv-2.dll is findable
import ctypes.util
_mpv_lib = ctypes.util.find_library("mpv")
log("STARTUP", f"ctypes.util.find_library('mpv') = {_mpv_lib}")
if getattr(sys, "frozen", False):
    _internal_mpv = os.path.join(os.path.dirname(sys.executable), "_internal", "libmpv-2.dll")
    log("STARTUP", f"_internal/libmpv-2.dll exists={os.path.exists(_internal_mpv)}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MediaPlayer")
    app.setOrganizationName("MediaPlayer")

    # Load dark theme from bundled assets
    style_path = os.path.join(get_base_path(), "assets", "styles", "dark.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())

    window = MediaPlayerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
