"""
Pomodoro timer state machine.

👤 Người 2 – Core
Phụ trách: Logic đếm giờ, chuyển pha Work/Break, callbacks cho UI.
"""

from enum import Enum, auto
from typing import Callable, Optional


class PomodoroState(Enum):
    """All valid states of the Pomodoro state machine."""

    IDLE = auto()
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()
    PAUSED = auto()


class PomodoroTimer:
    """Pomodoro state machine and time tracker.

    This class manages all timer state. It does NOT drive its own tick loop.
    The UI layer is responsible for calling tick() every second via after(1000).

    Args:
        work_minutes: Duration of a work session in minutes.
        short_break_minutes: Duration of a short break in minutes.
        long_break_minutes: Duration of a long break in minutes.
        sessions_before_long: Number of work sessions before a long break.

    Example:
        timer = PomodoroTimer()
        timer.on_tick(lambda secs: print(f"{secs}s remaining"))
        timer.on_phase_change(lambda state: print(f"Phase: {state}"))
        timer.start()
        # UI calls timer.tick() every 1 second via after(1000, ...)
    """

    def __init__(
        self,
        work_minutes: int = 25,
        short_break_minutes: int = 5,
        long_break_minutes: int = 15,
        sessions_before_long: int = 4,
    ) -> None:
        self._work_minutes = work_minutes
        self._short_break_minutes = short_break_minutes
        self._long_break_minutes = long_break_minutes
        self._sessions_before_long = sessions_before_long

        self._state: PomodoroState = PomodoroState.IDLE
        self._phase_before_pause: PomodoroState = PomodoroState.IDLE
        self._remaining_seconds: int = 0
        self._completed_sessions: int = 0

        self._tick_callback: Optional[Callable[[int], None]] = None
        self._phase_change_callback: Optional[Callable[[PomodoroState], None]] = None
        self._session_complete_callback: Optional[Callable[[], None]] = None

        # Cảnh báo trước khi hết phiên (mặc định 5 phút)
        self._warning_seconds: int = 5 * 60
        self._warning_callback: Optional[Callable[[], None]] = None
        self._warning_fired: bool = False  # chỉ báo 1 lần mỗi pha

    # ------------------------------------------------------------------
    # Public interface (UI calls these)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the timer from IDLE state. Begins a WORK phase."""
        if self._state != PomodoroState.IDLE:
            return
        self._state = PomodoroState.WORK
        self._remaining_seconds = self._work_minutes * 60
        self._notify_phase_change()
        self._notify_tick()

    def pause(self) -> None:
        """Pause the currently running timer."""
        if self._state in {
            PomodoroState.WORK,
            PomodoroState.SHORT_BREAK,
            PomodoroState.LONG_BREAK,
        }:
            self._phase_before_pause = self._state
            self._state = PomodoroState.PAUSED
            self._notify_phase_change()

    def resume(self) -> None:
        """Resume a paused timer."""
        if self._state == PomodoroState.PAUSED:
            self._state = self._phase_before_pause
            self._notify_phase_change()

    def reset(self) -> None:
        """Reset timer to IDLE state."""
        self._state = PomodoroState.IDLE
        self._phase_before_pause = PomodoroState.IDLE
        self._remaining_seconds = 0
        self._completed_sessions = 0
        self._notify_phase_change()
        self._notify_tick()

    def set_duration(self, work: int, short_break: int, long_break: int) -> None:
        """Cập nhật thời lượng các phiên. Có hiệu lực từ lần start() tiếp theo.

        Args:
            work: Thời lượng phiên làm việc (phút).
            short_break: Thời lượng nghỉ ngắn (phút).
            long_break: Thời lượng nghỉ dài (phút).
        """
        self._work_minutes = work
        self._short_break_minutes = short_break
        self._long_break_minutes = long_break

    def tick(self) -> None:
        """Advance the timer by one second. Called by UI via after(1000).

        Do NOT call time.sleep() anywhere. The UI drives this via after().
        """
        if self._state not in {
            PomodoroState.WORK,
            PomodoroState.SHORT_BREAK,
            PomodoroState.LONG_BREAK,
        }:
            return

        self._remaining_seconds -= 1

        # Kiểm tra cảnh báo trước khi hết phiên
        if (
            self._warning_callback
            and not self._warning_fired
            and self._remaining_seconds == self._warning_seconds
        ):
            self._warning_fired = True
            self._warning_callback()

        self._notify_tick()

        if self._remaining_seconds < 0:
            self._advance_phase()

    def skip_phase(self) -> None:
        """Skip the current phase and move to the next one."""
        if self._state in {
            PomodoroState.WORK,
            PomodoroState.SHORT_BREAK,
            PomodoroState.LONG_BREAK,
        }:
            self._advance_phase()

    def _advance_phase(self) -> None:
        """Complete the current phase and select the next phase."""
        self._warning_fired = False  # reset cho pha tiếp theo
        if self._state == PomodoroState.WORK:
            self._completed_sessions += 1
            if self._session_complete_callback:
                self._session_complete_callback()
            if self._completed_sessions % self._sessions_before_long == 0:
                self._state = PomodoroState.LONG_BREAK
                self._remaining_seconds = self._long_break_minutes * 60
            else:
                self._state = PomodoroState.SHORT_BREAK
                self._remaining_seconds = self._short_break_minutes * 60
        else:
            self._state = PomodoroState.WORK
            self._remaining_seconds = self._work_minutes * 60
            
        self._notify_phase_change()
        self._notify_tick()

    def _notify_tick(self) -> None:
        """Notify the UI of the current remaining time."""
        if self._tick_callback:
            self._tick_callback(self._remaining_seconds)

    def _notify_phase_change(self) -> None:
        """Notify listeners that the phase changed."""
        if self._phase_change_callback:
            self._phase_change_callback(self._state)

    # ------------------------------------------------------------------
    # Callback registration (UI subscribes to these)
    # ------------------------------------------------------------------

    def on_tick(self, callback: Callable[[int], None]) -> None:
        """Register callback fired every second with remaining seconds.

        Args:
            callback: Function receiving remaining_seconds as int.
        """
        self._tick_callback = callback

    def on_phase_change(self, callback: Callable[[PomodoroState], None]) -> None:
        """Register callback fired when the phase changes.

        Args:
            callback: Function receiving the new PomodoroState.
        """
        self._phase_change_callback = callback

    def on_session_complete(self, callback: Callable[[], None]) -> None:
        """Register callback fired when a WORK session is fully completed.

        Args:
            callback: Function called with no arguments.
        """
        self._session_complete_callback = callback

    def on_warning(self, callback: Callable[[], None], warning_seconds: int = 300) -> None:
        """Register callback fired khi còn warning_seconds giây nữa hết phiên.

        Người 3 có thể gọi lại với warning_seconds khác để thay đổi thời điểm cảnh báo.

        Args:
            callback: Hàm không nhận tham số, gọi khi đến lúc cảnh báo.
            warning_seconds: Số giây trước khi hết phiên thì báo (mặc định 300 = 5 phút).
        """
        self._warning_callback = callback
        self._warning_seconds = warning_seconds

    # ------------------------------------------------------------------
    # Read-only properties (UI reads these)
    # ------------------------------------------------------------------

    @property
    def state(self) -> PomodoroState:
        """Current state of the timer."""
        return self._state

    @property
    def remaining_seconds(self) -> int:
        """Remaining seconds in the current phase."""
        return self._remaining_seconds

    @property
    def completed_sessions(self) -> int:
        """Total number of completed WORK sessions since start."""
        return self._completed_sessions

    @property
    def durations(self) -> dict:
        """Current phase durations in minutes."""
        return {
            "work": self._work_minutes,
            "short_break": self._short_break_minutes,
            "long_break": self._long_break_minutes,
        }

    @property
    def remaining_display(self) -> str:
        """Thời gian còn lại định dạng sẵn MM:SS để hiển thị trên UI.

        Người 1 dùng property này thay vì tự format remaining_seconds,
        đảm bảo toàn bộ app hiển thị đồng nhất.

        Returns:
            Chuỗi dạng "25:00", "04:59", v.v.
        """
        mins, secs = divmod(self._remaining_seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    @property
    def phase_label(self) -> str:
        """Tên pha hiện tại bằng tiếng Việt để hiển thị trên UI.

        Returns:
            "Làm việc" | "Nghỉ ngắn" | "Nghỉ dài" | "Tạm dừng" | "Chờ"
        """
        labels = {
            PomodoroState.WORK: "Làm việc",
            PomodoroState.SHORT_BREAK: "Nghỉ ngắn",
            PomodoroState.LONG_BREAK: "Nghỉ dài",
            PomodoroState.PAUSED: "Tạm dừng",
            PomodoroState.IDLE: "Chờ",
        }
        return labels[self._state]

