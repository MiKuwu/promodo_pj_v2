"""
Session history — lưu và đọc lịch sử phiên Pomodoro.

👤 Người 3 – Settings + Music UI + History
Phụ trách: Lưu lịch sử phiên vào data/history.json, hiển thị màn hình lịch sử.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

HISTORY_PATH = Path("data/history.json")


@dataclass
class SessionEntry:
    """Một phiên Pomodoro đã chạy.

    Ví dụ hiển thị:
        09/09/2026
        20:00 - 20:25   Work      Completed
        20:30 - 20:55   Work      Interrupted
    """

    date: str         # "09/09/2026"
    start_time: str   # "20:00"
    end_time: str     # "20:25"
    phase: str        # "Work", "Short Break", "Long Break"
    status: str       # "Completed", "Interrupted"


class History:
    """Lưu và truy xuất lịch sử các phiên Pomodoro.

    Dữ liệu lưu vào file JSON đơn giản tại ``data/history.json``.
    Tự tạo file và thư mục nếu chưa có.

    Example:
        history = History()
        history.add_session(SessionEntry(
            date="09/09/2026", start_time="20:00", end_time="20:25",
            phase="Work", status="Completed"
        ))
        entries = history.get_all()
    """

    def __init__(self, path: Path = HISTORY_PATH) -> None:
        self._path = path
        self._entries: List[SessionEntry] = []
        self._load()

    def add_session(self, entry: SessionEntry) -> None:
        """Thêm một phiên mới vào lịch sử và lưu ngay.

        Args:
            entry: Thông tin phiên cần lưu.
        """
        self._entries.append(entry)
        # Giới hạn 1000 phiên gần nhất để file không bị quá lớn
        if len(self._entries) > 1000:
            self._entries = self._entries[-1000:]
        self._save()

    def get_all(self) -> List[SessionEntry]:
        """Trả về toàn bộ lịch sử, mới nhất ở cuối.

        Returns:
            Danh sách tất cả SessionEntry đã lưu.
        """
        return list(self._entries)

    def get_by_date(self, date: str) -> List[SessionEntry]:
        """Lọc lịch sử theo ngày.

        Args:
            date: Ngày cần lọc, định dạng "09/09/2026".

        Returns:
            Danh sách SessionEntry của ngày đó.
        """
        return [entry for entry in self._entries if entry.date == date]

    def clear(self) -> None:
        """Xóa toàn bộ lịch sử."""
        self._entries.clear()
        self._save()

    def _load(self) -> None:
        """Đọc dữ liệu từ file JSON. Tạo file rỗng nếu chưa có."""
        if not self._path.exists():
            self._entries = []
            return

        try:
            with self._path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("history JSON must contain a list")
            self._entries = [SessionEntry(**item) for item in data]
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            logger.warning("Could not load history from %s: %s", self._path, error)
            self._entries = []

    def _save(self) -> None:
        """Ghi danh sách phiên ra file JSON."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as file:
            json.dump(
                [asdict(entry) for entry in self._entries],
                file,
                ensure_ascii=False,
                indent=2,
            )
