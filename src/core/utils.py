"""
Utility functions for the Pomodoro Timer.
"""
import os
import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return Path(base_path) / relative_path
