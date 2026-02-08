"""Central path resolution for both dev and PyInstaller-frozen modes."""

import os
import sys


def get_base_path() -> str:
    """Return the base path for bundled assets (QSS, icons, etc.).
    In frozen mode: sys._MEIPASS (temp extraction dir).
    In dev mode: project root directory.
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_app_dir() -> str:
    """Return the directory where the executable (or main.py) lives.
    Used for finding .env and other user-writable files.
    In frozen mode: directory containing the .exe.
    In dev mode: project root directory.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir() -> str:
    """Return the persistent data directory (DB, posters, etc.).
    Always relative to the app directory so data persists across runs.
    """
    return os.path.join(get_app_dir(), "data")
