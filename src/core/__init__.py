"""
Core module for Pomodoro Timer.

Exports:
    PomodoroTimer: Main timer logic class.
    MusicPlayer: Background music player.
    NotificationManager: Desktop notification handler.
    History: Session history manager.
"""

from src.core.timer import PomodoroTimer, PomodoroState
from src.core.music_player import MusicPlayer
from src.core.notification import NotificationManager
from src.core.history import History, SessionEntry

__all__ = [
    "PomodoroTimer",
    "PomodoroState",
    "MusicPlayer",
    "NotificationManager",
    "History",
    "SessionEntry",
]
