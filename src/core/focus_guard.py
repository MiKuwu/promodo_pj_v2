"""
Focus Guard — phát hiện ứng dụng gây sao nhãng khi đang tập trung.

👤 Người 2 – Core
Phụ trách: Quét tiến trình hệ thống, phát hiện cửa sổ đang focus, gọi callback cảnh báo.
"""

import threading
from typing import Callable, List, Optional


class FocusGuard:
    """Theo dõi cửa sổ đang được người dùng focus và cảnh báo khi chuyển sang app sao nhãng.

    Không import từ src.ui. Chỉ giao tiếp với UI thông qua callbacks.

    Args:
        on_distraction_detected: Callback(exe_name) khi phát hiện app sao nhãng đang được focus.
        on_distraction_cleared: Callback() khi người dùng quay lại app an toàn.
    """

    # Tên exe của chính app này (sẽ không bao giờ bị chặn)
    _OWN_PROCESS_NAMES = {"python.exe", "pythonw.exe", "pomodorotimer.exe", "pomotimer.exe"}

    def __init__(
        self,
        on_distraction_detected: Callable[[str], None],
        on_distraction_cleared: Callable[[], None],
    ) -> None:
        self._on_detected = on_distraction_detected
        self._on_cleared = on_distraction_cleared

        self._blocked_apps: List[str] = []
        self._is_active: bool = False  # chỉ guard khi đang WORK
        self._is_distracted: bool = False
        self._current_offender: str = ""
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_blocked_apps(self, app_names: List[str]) -> None:
        """Cập nhật danh sách exe-name bị chặn (không phân biệt hoa/thường).

        Args:
            app_names: Danh sách tên exe (vd: ["chrome.exe", "discord.exe"]).
        """
        with self._lock:
            self._blocked_apps = [a.lower().strip() for a in app_names if a.strip()]

    def start_guard(self) -> None:
        """Kích hoạt chế độ bảo vệ (gọi khi timer bắt đầu phiên WORK)."""
        with self._lock:
            self._is_active = True
            self._is_distracted = False
            self._current_offender = ""

    def stop_guard(self) -> None:
        """Tắt chế độ bảo vệ (gọi khi hết WORK hoặc timer dừng/reset)."""
        with self._lock:
            self._is_active = False
            was_distracted = self._is_distracted
            self._is_distracted = False
            self._current_offender = ""
        if was_distracted:
            self._on_cleared()

    def check(self) -> None:
        """Kiểm tra cửa sổ đang focus. Gọi từ UI thread mỗi 1–2 giây.

        Phát hiện app sao nhãng → gọi on_distraction_detected.
        Khi quay về app an toàn → gọi on_distraction_cleared.
        """
        with self._lock:
            if not self._is_active or not self._blocked_apps:
                return
            blocked = list(self._blocked_apps)
            was_distracted = self._is_distracted

        focused_exe = self._get_focused_exe()
        if focused_exe is None:
            return

        is_own = focused_exe in self._OWN_PROCESS_NAMES
        is_blocked = any(focused_exe == b for b in blocked)

        with self._lock:
            if is_blocked and not is_own:
                if not self._is_distracted or self._current_offender != focused_exe:
                    self._is_distracted = True
                    self._current_offender = focused_exe
                    offender = focused_exe
                else:
                    offender = None  # đã đang báo rồi, không cần trigger lại
            elif was_distracted and not is_blocked:
                self._is_distracted = False
                self._current_offender = ""
                offender = None
                self._on_cleared()
                return
            else:
                offender = None

        if offender:
            self._on_detected(offender)

    # ------------------------------------------------------------------
    # System helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_focused_exe() -> Optional[str]:
        """Lấy tên exe của cửa sổ đang được focus. Trả về None nếu lỗi."""
        try:
            import ctypes
            import ctypes.wintypes as wt

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi

            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if not pid.value:
                return None

            hproc = kernel32.OpenProcess(0x0400 | 0x0010, False, pid.value)  # QUERY + VM_READ
            if not hproc:
                return None

            buf = ctypes.create_unicode_buffer(260)
            psapi.GetModuleBaseNameW(hproc, None, buf, 260)
            kernel32.CloseHandle(hproc)

            name = buf.value.strip().lower()
            return name if name else None
        except Exception:
            return None

    @staticmethod
    def scan_running_apps() -> List[str]:
        """Quét tất cả tiến trình đang chạy và trả về danh sách tên exe duy nhất.

        Returns:
            Danh sách exe-name đã sắp xếp (vd: ["chrome.exe", "discord.exe"]).
        """
        found = set()
        try:
            import ctypes
            import ctypes.wintypes as wt

            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi

            # EnumProcesses
            arr_size = 4096
            pids = (wt.DWORD * arr_size)()
            bytes_returned = wt.DWORD()
            if not psapi.EnumProcesses(
                ctypes.byref(pids), ctypes.sizeof(pids), ctypes.byref(bytes_returned)
            ):
                return []

            count = bytes_returned.value // ctypes.sizeof(wt.DWORD)
            for i in range(count):
                pid = pids[i]
                if pid == 0:
                    continue
                hproc = kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
                if not hproc:
                    continue
                buf = ctypes.create_unicode_buffer(260)
                psapi.GetModuleBaseNameW(hproc, None, buf, 260)
                kernel32.CloseHandle(hproc)
                name = buf.value.strip().lower()
                if name and name.endswith(".exe"):
                    found.add(name)
        except Exception:
            pass

        # Filter out system / own processes
        system_prefix = {
            "system", "smss", "csrss", "wininit", "services", "lsass",
            "svchost", "dwm", "explorer", "taskmgr", "conhost",
            "python", "pythonw", "pomodorotimer",
        }
        filtered = {
            name for name in found
            if not any(name.startswith(p) for p in system_prefix)
        }
        return sorted(filtered)
