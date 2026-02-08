"""Simple file-based debug logger for the packaged app (console=False)."""

import os
import sys
import datetime


def _get_log_path() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "debug.log")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug.log")


_log_path = _get_log_path()


def log(tag: str, message: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{tag}] {message}\n"
    try:
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
