"""Tests for core/timer.py – Người 2 phụ trách implement."""

import pytest
from src.core.timer import PomodoroTimer, PomodoroState


def test_initial_state():
    """Timer starts in IDLE state."""
    timer = PomodoroTimer()
    assert timer.state == PomodoroState.IDLE


def test_start_transitions_to_work():
    """Calling start() from IDLE should move to WORK state."""
    timer = PomodoroTimer()
    timer.start()
    assert timer.state == PomodoroState.WORK


def test_pause_from_work():
    """Calling pause() during WORK should move to PAUSED."""
    timer = PomodoroTimer()
    timer.start()
    timer.pause()
    assert timer.state == PomodoroState.PAUSED


def test_resume_from_paused():
    """Calling resume() from PAUSED should return to WORK."""
    timer = PomodoroTimer()
    timer.start()
    timer.pause()
    timer.resume()
    assert timer.state == PomodoroState.WORK


def test_reset_returns_to_idle():
    """Calling reset() from any state should return to IDLE."""
    timer = PomodoroTimer()
    timer.start()
    timer.reset()
    assert timer.state == PomodoroState.IDLE
    assert timer.remaining_seconds == 0
    assert timer.completed_sessions == 0


def test_tick_decrements_remaining_seconds():
    """Each tick() call should reduce remaining_seconds by 1."""
    timer = PomodoroTimer(work_minutes=1)
    timer.start()
    initial = timer.remaining_seconds
    timer.tick()
    assert timer.remaining_seconds == initial - 1


def test_on_tick_callback_is_called():
    """on_tick callback fires on start() and on each tick()."""
    received = []
    timer = PomodoroTimer(work_minutes=1)
    timer.on_tick(lambda secs: received.append(secs))
    timer.start()   # fires once with 60
    timer.tick()    # fires once with 59
    # start() fires 1 time, tick() fires 1 time → total 2
    assert len(received) == 2
    assert received[0] == 60  # snapshot right after start
    assert received[1] == 59  # after first tick


def test_phase_transitions_after_work_session():
    """After a full work session completes, phase should change to SHORT_BREAK."""
    timer = PomodoroTimer(work_minutes=1, sessions_before_long=4)
    phase_changes = []
    timer.on_phase_change(lambda s: phase_changes.append(s))
    timer.start()
    # Simulate all ticks for 1 minute
    for _ in range(60):
        timer.tick()
    assert PomodoroState.SHORT_BREAK in phase_changes


def test_long_break_after_n_sessions():
    """After sessions_before_long work sessions, a long break should occur."""
    sessions_before_long = 2
    timer = PomodoroTimer(
        work_minutes=1,
        short_break_minutes=1,
        sessions_before_long=sessions_before_long,
    )
    phase_changes = []
    timer.on_phase_change(lambda s: phase_changes.append(s))
    timer.start()

    # Chạy qua 2 chu kì work+short_break để kích hoạt long break
    for _ in range(sessions_before_long):
        for _ in range(60):   # hết work (1 phút)
            timer.tick()
        for _ in range(60):   # hết short break (1 phút)
            timer.tick()

    assert PomodoroState.LONG_BREAK in phase_changes


def test_set_duration_updates_remaining_after_reset():
    """set_duration() should take effect on the next start()."""
    timer = PomodoroTimer(work_minutes=25)
    timer.set_duration(work=10, short_break=3, long_break=10)
    timer.start()
    assert timer.remaining_seconds == 10 * 60


def test_skip_phase():
    """skip_phase() should immediately advance to the next phase."""
    timer = PomodoroTimer(work_minutes=25)
    timer.start()
    assert timer.state == PomodoroState.WORK
    timer.skip_phase()
    assert timer.state == PomodoroState.SHORT_BREAK


def test_warning_callback_fires_at_correct_time():
    """on_warning callback should fire exactly when warning_seconds remain."""
    fired = []
    timer = PomodoroTimer(work_minutes=10)  # 600 giây
    timer.on_warning(lambda: fired.append(True), warning_seconds=60)
    timer.start()

    # Tick đến khi còn đúng 61 giây → chưa fire
    for _ in range(600 - 61):
        timer.tick()
    assert len(fired) == 0

    # Tick thêm 1 → còn đúng 60 giây → fire!
    timer.tick()
    assert len(fired) == 1


def test_warning_callback_fires_only_once_per_phase():
    """Warning callback chỉ được gọi đúng 1 lần mỗi pha."""
    fired = []
    timer = PomodoroTimer(work_minutes=2)  # 120 giây
    timer.on_warning(lambda: fired.append(True), warning_seconds=30)
    timer.start()

    # Chạy hết toàn bộ pha WORK (120 ticks)
    for _ in range(120):
        timer.tick()

    # Warning chỉ fire đúng 1 lần (khi còn 30 giây)
    assert len(fired) == 1


def test_warning_resets_for_next_phase():
    """Warning phải fire lại ở pha tiếp theo (SHORT_BREAK)."""
    fired_phases = []
    timer = PomodoroTimer(work_minutes=2, short_break_minutes=2)
    timer.on_warning(
        lambda: fired_phases.append(timer.state),
        warning_seconds=30,
    )
    timer.start()

    for _ in range(120):   # hết WORK
        timer.tick()
    for _ in range(120):   # hết SHORT_BREAK
        timer.tick()

    # Warning phải fire trong cả 2 pha
    assert len(fired_phases) == 2


def test_remaining_display_format():
    """remaining_display phải trả về đúng định dạng MM:SS."""
    timer = PomodoroTimer(work_minutes=25)
    timer.start()
    assert timer.remaining_display == "25:00"

    # Giả lập 61 giây đã trôi qua → còn 25*60 - 61 = 1439 giây
    for _ in range(61):
        timer.tick()
    assert timer.remaining_display == "23:59"


def test_phase_label_returns_correct_text():
    """phase_label phải trả về tên tiếng Việt đúng theo từng pha."""
    timer = PomodoroTimer(work_minutes=1)

    assert timer.phase_label == "Chờ"      # IDLE

    timer.start()
    assert timer.phase_label == "Làm việc"  # WORK

    timer.pause()
    assert timer.phase_label == "Tạm dừng"  # PAUSED

    timer.resume()
    timer.skip_phase()
    assert timer.phase_label == "Nghỉ ngắn"  # SHORT_BREAK


