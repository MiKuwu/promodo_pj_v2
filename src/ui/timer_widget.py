"""
Timer display widget with animation.

👤 Người 1 – GUI
Phụ trách: Vòng tròn đồng hồ, countdown text, nút Start/Pause/Reset.
"""

import customtkinter
from typing import Callable
from src.ui.theme import (
    FONT_PHASE,
    FONT_TIMER,
    LONG_BREAK_COLOR,
    SHORT_BREAK_COLOR,
    WORK_COLOR,
)


class TimerWidget(customtkinter.CTkFrame):
    """Displays the countdown timer and phase controls.

    Shows remaining time, current phase label, and Start/Pause/Reset buttons.
    Receives callbacks from MainWindow — does NOT talk to core directly.

    Args:
        master: The parent widget.
        on_start: Callback invoked when Start button is pressed.
        on_pause: Callback invoked when Pause button is pressed.
        on_resume: Callback invoked when Resume button is pressed.
        on_reset: Callback invoked when Reset button is pressed.
        on_skip: Callback invoked when Skip button is pressed.
    """

    def __init__(
        self,
        master,
        on_start: Callable,
        on_pause: Callable,
        on_resume: Callable,
        on_reset: Callable,
        on_skip: Callable,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_start = on_start
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_reset = on_reset
        self._on_skip = on_skip

        self._build_ui()

    def _build_ui(self) -> None:
        """Create and arrange all internal widgets."""
        self._phase_label = customtkinter.CTkLabel(
            self,
            text="Sẵn sàng",
            font=FONT_PHASE,
            text_color=WORK_COLOR,
        )
        self._phase_label.pack(pady=(24, 8))

        self._time_label = customtkinter.CTkLabel(
            self,
            text="00:00",
            font=FONT_TIMER,
        )
        self._time_label.pack(pady=(0, 24))

        controls = customtkinter.CTkFrame(self, fg_color="transparent")
        controls.pack(pady=8)

        self._start_button = customtkinter.CTkButton(
            controls,
            text="Bắt đầu",
            command=self._on_start,
        )
        self._start_button.grid(row=0, column=0, padx=4)

        self._pause_button = customtkinter.CTkButton(
            controls,
            text="Tạm dừng",
            command=self._on_pause,
        )
        self._pause_button.grid(row=0, column=1, padx=4)

        customtkinter.CTkButton(
            controls,
            text="Đặt lại",
            command=self._on_reset,
        ).grid(row=0, column=2, padx=4)

        customtkinter.CTkButton(
            self,
            text="Bỏ qua phiên",
            command=self._on_skip,
        ).pack(pady=(8, 24))

    # ------------------------------------------------------------------
    # Public update methods (called by MainWindow)
    # ------------------------------------------------------------------

    def update_time(self, remaining_seconds: int) -> None:
        """Update the displayed countdown time.

        Args:
            remaining_seconds: Seconds remaining in the current phase.
        """
        minutes, seconds = divmod(max(0, remaining_seconds), 60)
        self._time_label.configure(text=f"{minutes:02d}:{seconds:02d}")

    def update_phase(self, phase_name: str) -> None:
        """Update the phase label and color theme.

        Args:
            phase_name: Human-readable phase name e.g. "Work", "Short Break".
        """
        phase_colors = {
            "Work": WORK_COLOR,
            "Short Break": SHORT_BREAK_COLOR,
            "Long Break": LONG_BREAK_COLOR,
        }
        
        phase_vn = {
            "Work": "Làm việc",
            "Short Break": "Nghỉ ngắn",
            "Long Break": "Nghỉ dài",
            "Ready": "Sẵn sàng"
        }
        
        self._phase_label.configure(
            text=phase_vn.get(phase_name, phase_name),
            text_color=phase_colors.get(phase_name, WORK_COLOR),
        )

    def set_paused_state(self, is_paused: bool) -> None:
        """Toggle the Start/Pause button appearance.

        Args:
            is_paused: True shows Resume button, False shows Pause button.
        """
        if is_paused:
            self._pause_button.configure(text="Tiếp tục", command=self._on_resume)
        else:
            self._pause_button.configure(text="Tạm dừng", command=self._on_pause)
