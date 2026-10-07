"""
Application configuration manager — lưu/đọc cấu hình app vào JSON.

Quản lý tất cả settings: session durations, music playlist, notification sound,
background image, theme colors. Dữ liệu lưu vào Documents/PomodoroTimer/.
"""

import json
import logging
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Thư mục app dễ tìm cho người dùng
APP_DATA_DIR = Path.home() / "Documents" / "PomodoroTimer"
MUSIC_DIR = APP_DATA_DIR / "music"
SOUNDS_DIR = APP_DATA_DIR / "sounds"
BACKGROUNDS_DIR = APP_DATA_DIR / "backgrounds"
CONFIG_FILE = APP_DATA_DIR / "config.json"


@dataclass
class SessionConfig:
    """Cấu hình phiên Pomodoro."""

    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    sessions_before_long: int = 4


@dataclass
class MusicConfig:
    """Cấu hình nhạc nền và âm thanh thông báo."""

    playlist_files: List[str] = field(default_factory=list)
    notification_sound: str = ""
    playback_mode: str = "repeat_all"  # "repeat_one", "repeat_all", "shuffle"
    volume: float = 0.5


@dataclass
class BackgroundConfig:
    """Cấu hình ảnh nền và màu theme."""

    image_path: str = ""
    button_color: str = "#1f6aa5"


@dataclass
class FocusConfig:
    """Cấu hình chế độ tập trung — danh sách ứng dụng gây sao nhãng."""

    blocked_apps: List[str] = field(default_factory=list)
    """Danh sách exe-name của các app bị chặn khi đang tập trung."""

    focus_guard_enabled: bool = True
    """Bật/tắt tính năng cảnh báo app sao nhãng."""


class AppConfig:
    """Quản lý toàn bộ cấu hình ứng dụng.

    Tự tạo thư mục Documents/PomodoroTimer/ khi khởi tạo.
    Lưu cấu hình vào config.json mỗi khi thay đổi.

    Example:
        config = AppConfig()
        config.session.work_minutes = 30
        config.save()
    """

    def __init__(self) -> None:
        self.session = SessionConfig()
        self.music = MusicConfig()
        self.background = BackgroundConfig()
        self.focus = FocusConfig()
        self._ensure_dirs()
        self._load()

    def _ensure_dirs(self) -> None:
        """Tạo toàn bộ thư mục cần thiết."""
        for d in [APP_DATA_DIR, MUSIC_DIR, SOUNDS_DIR, BACKGROUNDS_DIR]:
            d.mkdir(parents=True, exist_ok=True)
            
        # Initialize default notification sound if folder is empty
        from src.core.utils import get_resource_path
        default_sound = get_resource_path("assets/sounds/Homecoming - Samsung OneUI Alarm.wav")
        if default_sound.exists():
            existing = list(SOUNDS_DIR.iterdir())
            if not existing:
                try:
                    shutil.copy2(default_sound, SOUNDS_DIR / default_sound.name)
                except Exception:
                    pass

    def save(self) -> None:
        """Ghi cấu hình ra file JSON."""
        data = {
            "session": asdict(self.session),
            "music": asdict(self.music),
            "background": asdict(self.background),
            "focus": asdict(self.focus),
        }
        try:
            with CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(f"Cannot save config: {e}")

    def _load(self) -> None:
        """Đọc cấu hình từ file JSON. Giữ default nếu file chưa có."""
        if not CONFIG_FILE.exists():
            return
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if "session" in data:
                self.session = SessionConfig(**data["session"])
            if "music" in data:
                self.music = MusicConfig(**data["music"])
            if "background" in data:
                self.background = BackgroundConfig(**data["background"])
            if "focus" in data:
                self.focus = FocusConfig(**data["focus"])
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Cannot load config, using defaults: {e}")
            
        # Ensure a default notification sound is set if empty
        if not self.music.notification_sound:
            default_dest = SOUNDS_DIR / "Homecoming - Samsung OneUI Alarm.wav"
            if default_dest.exists():
                self.music.notification_sound = str(default_dest)

    # ------------------------------------------------------------------
    # File management helpers
    # ------------------------------------------------------------------

    @staticmethod
    def import_music_file(source_path: str) -> Optional[Path]:
        """Copy file nhạc vào thư mục app và trả về đường dẫn mới.

        Args:
            source_path: Đường dẫn file gốc.

        Returns:
            Path tới file đã copy, hoặc None nếu lỗi.
        """
        src = Path(source_path)
        if not src.exists():
            return None
        dest = MUSIC_DIR / src.name
        # Nếu trùng tên thì thêm suffix
        counter = 1
        while dest.exists():
            dest = MUSIC_DIR / f"{src.stem}_{counter}{src.suffix}"
            counter += 1
        try:
            shutil.copy2(str(src), str(dest))
            return dest
        except OSError as e:
            logger.error(f"Cannot copy music file: {e}")
            return None

    @staticmethod
    def import_sound_file(source_path: str) -> Optional[Path]:
        """Copy file âm thanh thông báo vào thư mục app.

        Args:
            source_path: Đường dẫn file gốc.

        Returns:
            Path tới file đã copy, hoặc None nếu lỗi.
        """
        src = Path(source_path)
        if not src.exists():
            return None
        dest = SOUNDS_DIR / src.name
        counter = 1
        while dest.exists():
            dest = SOUNDS_DIR / f"{src.stem}_{counter}{src.suffix}"
            counter += 1
        try:
            shutil.copy2(str(src), str(dest))
            return dest
        except OSError as e:
            logger.error(f"Cannot copy sound file: {e}")
            return None

    @staticmethod
    def import_background_image(source_path: str) -> Optional[Path]:
        """Copy ảnh nền vào thư mục app.

        Args:
            source_path: Đường dẫn file ảnh gốc.

        Returns:
            Path tới file đã copy, hoặc None nếu lỗi.
        """
        src = Path(source_path)
        if not src.exists():
            return None
        dest = BACKGROUNDS_DIR / src.name
        counter = 1
        while dest.exists():
            dest = BACKGROUNDS_DIR / f"{src.stem}_{counter}{src.suffix}"
            counter += 1
        try:
            shutil.copy2(str(src), str(dest))
            return dest
        except OSError as e:
            logger.error(f"Cannot copy background image: {e}")
            return None

    @staticmethod
    def remove_file(filepath: str) -> bool:
        """Xóa file khỏi thư mục app.

        Args:
            filepath: Đường dẫn file cần xóa.

        Returns:
            True nếu xóa thành công.
        """
        try:
            p = Path(filepath)
            if p.exists():
                p.unlink()
                return True
        except OSError as e:
            logger.error(f"Cannot remove file: {e}")
        return False
