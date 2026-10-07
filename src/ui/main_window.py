"""
Main application window.

👤 Người 1 – GUI
Phụ trách: Layout tổng thể, khởi tạo và kết nối các widget con.
"""

import customtkinter
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PIL import Image

from src.core.app_config import AppConfig, MUSIC_DIR
from src.core.history import SessionEntry
from src.core.timer import PomodoroState
from src.core.utils import get_resource_path
from src.core.notification import NotificationManager
from src.ui.music_panel import MusicPanel
from src.ui.settings_panel import SettingsPanel
from src.ui.timer_widget import TimerWidget
from src.ui.dashboard_panel import DashboardPanel
from src.ui.distraction_panel import DistractionPanel
from src.core.focus_guard import FocusGuard

if TYPE_CHECKING:
    from src.core import PomodoroTimer, MusicPlayer
    from src.core.history import History

SUPPORTED_AUDIO = {".mp3", ".wav", ".ogg"}


class MainWindow(customtkinter.CTk):
    """Root application window — 16:9 horizontal layout.

    Left pane: Dashboard (chart + history).
    Right pane: Timer, music controls, settings.
    Bottom: Status bar for notifications.
    """

    def __init__(
        self,
        timer: "PomodoroTimer",
        music_player: "MusicPlayer" = None,
        history: "History" = None,
        config: "AppConfig" = None,
    ) -> None:
        super().__init__()
        self._timer = timer
        self._music = music_player
        self._history = history
        self._config = config or AppConfig()
        self._phase_started_at = None
        self._settings_window = None
        self._tick_running = False
        self._notifier = NotificationManager()
        self._focus_guard = FocusGuard(
            on_distraction_detected=self._on_distraction_detected,
            on_distraction_cleared=self._on_distraction_cleared,
        )
        self._focus_guard.set_blocked_apps(self._config.focus.blocked_apps)

        self.title("Promodo Timer - Made by NaHBro Team")
        self.geometry("1152x648")
        self.minsize(1024, 576)

        # Apply saved config to core modules
        self._apply_config_to_core()

        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Top bar
        self.grid_rowconfigure(1, weight=1)  # Content frame
        self.grid_rowconfigure(2, weight=0)  # Status bar

        # --- Top Bar ---
        self._top_bar = customtkinter.CTkFrame(self, fg_color="transparent", height=40)
        self._top_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(8, 0))

        self._content_frame = customtkinter.CTkFrame(
            self, fg_color="transparent"
        )
        self._content_frame.grid(row=1, column=0, sticky="nsew")
        self._content_frame.grid_columnconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(1, weight=0, minsize=480)
        self._content_frame.grid_rowconfigure(0, weight=1)

        self._setup_top_bar()
        self._setup_layout()
        self._register_timer_callbacks()
        self._setup_status_bar()
        self._apply_theme_color()
        self._poll_music()
        self._poll_focus_guard()
        
        # Cấu hình đóng cửa sổ xuống khay hệ thống (Tray)
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self._tray_icon = None

    def _hide_to_tray(self) -> None:
        """Ẩn cửa sổ và chạy ngầm (System Tray)."""
        self.withdraw()
        
        import threading
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Tạo icon đơn giản bằng PIL
            image = Image.new('RGB', (64, 64), color=(31, 106, 165))
            dc = ImageDraw.Draw(image)
            dc.rectangle((32, 0, 64, 32), fill=(255, 255, 255))
            dc.rectangle((0, 32, 32, 64), fill=(255, 255, 255))
            
            menu = pystray.Menu(
                pystray.MenuItem("Hiển thị", self._restore_from_tray, default=True),
                pystray.MenuItem("Thoát", self._quit_app)
            )
            self._tray_icon = pystray.Icon("Promodo", image, "Promodo Timer - Made by NaHBro Team", menu)
            
            # Pystray cần chạy trong thread riêng để không block
            threading.Thread(target=self._tray_icon.run, daemon=True).start()
            
        except ImportError:
            # Fallback nếu pystray không được cài
            self.destroy()

    def _restore_from_tray(self, icon, item) -> None:
        """Khôi phục cửa sổ và đóng tray."""
        if self._tray_icon:
            self._tray_icon.stop()
        self.after(0, self.deiconify)

    def _quit_app(self, icon, item) -> None:
        """Thoát hoàn toàn."""
        if self._tray_icon:
            self._tray_icon.stop()
        self.after(0, self.destroy)

    def _apply_config_to_core(self) -> None:
        """Áp dụng config đã lưu cho timer và music player."""
        cfg = self._config
        self._timer.set_duration(
            cfg.session.work_minutes,
            cfg.session.short_break_minutes,
            cfg.session.long_break_minutes,
        )
        if self._music:
            self._music.set_volume(cfg.music.volume)
            self._music.set_playback_mode(cfg.music.playback_mode)
            if cfg.music.notification_sound:
                self._music.set_notification_sound(
                    cfg.music.notification_sound
                )
            # Load playlist from config or from app folder
            current_playlist = [str(p) for p in self._music.playlist] if hasattr(self._music, 'playlist') else []
            new_playlist = cfg.music.playlist_files
            if not new_playlist and MUSIC_DIR.exists():
                new_playlist = sorted(
                    str(f) for f in MUSIC_DIR.iterdir()
                    if f.suffix.lower() in SUPPORTED_AUDIO
                )
            if new_playlist and current_playlist != new_playlist:
                self._music.set_playlist_from_files(new_playlist)

    # ------------------------------------------------------------------
    # Status Bar
    # ------------------------------------------------------------------

    def _setup_status_bar(self) -> None:
        """Tạo thanh trạng thái ở cuối cửa sổ."""
        self._status_bar = customtkinter.CTkLabel(
            self, text="Sẵn sàng", anchor="w", height=32,
            font=customtkinter.CTkFont(size=13),
            text_color="gray",
        )
        self._status_bar.grid(
            row=2, column=0, sticky="ew", padx=16, pady=(0, 8)
        )

    def _setup_top_bar(self) -> None:
        """Tạo thanh điều hướng trên cùng (Settings, User Guide)."""
        self._top_bar.grid_columnconfigure(0, weight=1) # Đẩy các nút sang phải
        
        # Nút Hướng dẫn sử dụng
        customtkinter.CTkButton(
            self._top_bar, text="📖 Hướng dẫn", width=120,
            command=self._open_guide
        ).grid(row=0, column=1, padx=(0, 8))
        
        # Nút Cài đặt
        customtkinter.CTkButton(
            self._top_bar, text="⚙ Cài đặt", width=100,
            command=self._open_settings
        ).grid(row=0, column=2, padx=0)

    def _open_guide(self) -> None:
        """Mở cửa sổ Hướng dẫn sử dụng."""
        if hasattr(self, "_guide_window") and self._guide_window is not None and self._guide_window.winfo_exists():
            self._guide_window.focus()
            return
            
        self._guide_window = customtkinter.CTkToplevel(self)
        self._guide_window.title("📖 Hướng dẫn sử dụng")
        self._guide_window.geometry("600x500")
        self._guide_window.minsize(500, 400)
        
        scroll = customtkinter.CTkScrollableFrame(self._guide_window, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        guide_text = (
            "CHÀO MỪNG BẠN ĐẾN VỚI POMODORO TIMER!\n\n"
            "1. PHƯƠNG PHÁP POMODORO LÀ GÌ?\n"
            "Pomodoro là phương pháp quản lý thời gian để nâng cao tối đa sự tập trung. Bạn sẽ làm việc trong các khoảng thời gian ngắn (thường là 25 phút), gọi là 1 Pomodoro, sau đó nghỉ ngơi ngắn (5 phút). Sau 4 phiên Pomodoro, bạn sẽ nghỉ dài hơn (15-30 phút).\n\n"
            "2. HƯỚNG DẪN SỬ DỤNG ĐỒNG HỒ:\n"
            "- Nút 'Start': Bắt đầu đếm ngược thời gian.\n"
            "- Nút 'Pause': Tạm dừng thời gian.\n"
            "- Nút 'Reset': Đặt lại thời gian của phiên hiện tại về mốc ban đầu.\n"
            "- Nút 'Skip phase': Bỏ qua phiên hiện tại và chuyển ngay sang phiên tiếp theo.\n\n"
            "3. HƯỚNG DẪN TRÌNH PHÁT NHẠC (BACKGROUND MUSIC):\n"
            "Âm nhạc giúp bạn tập trung hơn. Ứng dụng tích hợp sẵn trình phát nhạc:\n"
            "- Các nút điều khiển: Lùi bài (⏮), Phát/Tạm dừng (▶/⏸), Dừng hẳn (⏹), Tiến bài (⏭).\n"
            "- Thanh gạt phía dưới: Điều chỉnh âm lượng nhạc nền.\n"
            "- Để quản lý danh sách nhạc, bấm vào nút '⚙ Cài đặt' ở góc trên bên phải màn hình, chọn tab 'Music' và dùng tính năng 'Add Song'.\n\n"
            "4. CÀI ĐẶT ỨNG DỤNG (SETTINGS):\n"
            "- Tab 'Session': Cho phép bạn thay đổi thời lượng cho Phiên làm việc (Work), Nghỉ ngắn (Short Break) và Nghỉ dài (Long Break).\n"
            "- Tab 'Music': Nơi bạn thiết lập Chuông thông báo (khi hết giờ) và thêm/xóa bài hát trong Playlist nhạc nền.\n\n"
            "Chúc bạn có những giờ phút làm việc và học tập thật hiệu quả!"
        )
        
        customtkinter.CTkLabel(
            scroll, text=guide_text, justify="left", wraplength=540,
            font=customtkinter.CTkFont(size=14, weight="normal")
        ).pack(anchor="w")
        
        self._guide_window.transient(self)
        self._guide_window.focus()

    def show_status(self, message: str, duration_ms: int = 4000) -> None:
        """Hiển thị thông báo trạng thái tạm thời.

        Args:
            message: Nội dung thông báo.
            duration_ms: Thời gian hiển thị (ms), sau đó reset về 'Ready'.
        """
        if "⚠" in message or "❌" in message:
            color = "#FFA500"  # Orange/Gold for warnings
            font = customtkinter.CTkFont(size=15, weight="bold")
        elif "🎉" in message or "✅" in message:
            color = "#4CAF50"  # Green for success
            font = customtkinter.CTkFont(size=15, weight="bold")
        else:
            color = "white"
            font = customtkinter.CTkFont(size=14, weight="normal")

        self._status_bar.configure(text=message, text_color=color, font=font)
        
        if hasattr(self, '_status_job'):
            self.after_cancel(self._status_job)
            
        self._status_job = self.after(
            duration_ms,
            lambda: self._status_bar.configure(
                text="Sẵn sàng", text_color="gray",
                font=customtkinter.CTkFont(size=13)
            )
        )


    def _apply_theme_color(self) -> None:
        """Áp dụng màu theme cho buttons."""
        color = self._config.background.button_color
        if not color:
            return

        def update_widgets(widget):
            if isinstance(widget, customtkinter.CTkButton):
                current_fg = widget.cget("fg_color")
                # Không đổi màu nút nếu nó đang là trong suốt (transparent) hoặc red (như nút Delete)
                if current_fg != "transparent" and current_fg != "red":
                    widget.configure(fg_color=color)
            for child in widget.winfo_children():
                update_widgets(child)

        update_widgets(self)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _setup_layout(self) -> None:
        """Build and place all child widgets on the window."""
        # --- Left Pane ---
        if self._history is not None:
            self._dashboard_panel = DashboardPanel(
                self._content_frame, self._history
            )
            self._dashboard_panel.grid(
                row=0, column=0, sticky="nsew", padx=(32, 16), pady=32
            )

        # --- Right Pane ---
        self._right_pane = customtkinter.CTkFrame(
            self._content_frame, corner_radius=15, fg_color="#1e1e1e"
        )
        self._right_pane.grid(
            row=0, column=1, sticky="nsew", padx=(16, 32), pady=32
        )

        self._timer_widget = TimerWidget(
            self._right_pane,
            on_start=self._start_timer,
            on_pause=self._pause_timer,
            on_resume=self._resume_timer,
            on_reset=self._reset_timer,
            on_skip=self._skip_phase,
        )
        self._right_pane.grid_columnconfigure(0, weight=1)
        self._timer_widget.grid(row=0, column=0, sticky="ew", padx=16, pady=8)
        
        if self._music is not None:
            self._music_panel = MusicPanel(
                self._right_pane,
                on_play=self._play_music,
                on_pause=self._pause_music,
                on_resume=self._resume_music,
                on_stop=self._stop_music,
                on_volume_change=self._set_music_volume,
                on_pick_folder=lambda: None,  # Moved to Settings
                on_previous=self._previous_music_track,
                on_next=self._next_music_track,
            )
            self._music_panel.grid(row=1, column=0, sticky="ew", padx=16, pady=16)
            self._music_panel.set_volume(self._music.volume)
            self._music_panel.set_seek_callback(self._seek_music)
            self._refresh_music_track_label()

            # Auto-advance check
            self._check_music_end_loop()

        # --- Distraction Panel ---
        self._distraction_panel = DistractionPanel(
            self._right_pane,
            is_guard_enabled=self._config.focus.focus_guard_enabled,
            on_toggle_guard=self._on_guard_toggled,
            on_remove_app=self._remove_blocked_app,
            on_open_settings=lambda: self._open_settings(focus_tab=True),
        )
        self._distraction_panel.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._distraction_panel.set_blocked_apps(self._config.focus.blocked_apps)
        self._right_pane.grid_rowconfigure(2, weight=1)



    def _check_music_end_loop(self) -> None:
        """Kiểm tra bài hát kết thúc để auto-advance."""
        if self._music:
            self._music.check_music_end()
        self.after(500, self._check_music_end_loop)

    # ------------------------------------------------------------------
    # Music controls
    # ------------------------------------------------------------------

    def _refresh_music_track_label(self) -> None:
        """Show the loaded track name."""
        if self._music is None:
            return
        playlist = self._music.playlist
        track_name = self._music.current_track
        if track_name is None and playlist:
            track_name = playlist[self._music.playlist_index]
        self._music_panel.update_track_label(
            track_name or "No tracks found"
        )
        self._music_panel.set_playing_state(self._music.is_playing)

    def _play_music(self) -> None:
        self._music.play()
        if self._music.is_playing:
            self._music_panel.set_playing_state(True)
            if self._music.volume < 0.05:
                self.show_status("⚠ Playing, but volume is muted!", 4000)
            else:
                self.show_status("▶ Đang phát nhạc")
        else:
            self.show_status("⚠ Chưa có nhạc để phát", 3000)

    def _pause_music(self) -> None:
        self._music.pause()
        self._music_panel.set_paused_state(True)
        self.show_status("⏸ Đã tạm dừng nhạc")

    def _resume_music(self) -> None:
        self._music.resume()
        self._music_panel.set_playing_state(self._music.is_playing)
        self.show_status("▶ Tiếp tục phát nhạc")

    def _stop_music(self) -> None:
        self._music.stop()
        self._music_panel.set_playing_state(False)
        self.show_status("⏹ Đã dừng nhạc")

    def _set_music_volume(self, volume: float) -> None:
        self._music.set_volume(volume)
        self._config.music.volume = volume

    def _previous_music_track(self) -> None:
        self._music.previous_track()
        self._refresh_music_track_label()
        self._music_panel.set_playing_state(self._music.is_playing)
        self.show_status(f"⏮ {self._music.current_track or 'Previous'}")

    def _seek_music(self, seconds: float) -> None:
        self._music.seek(seconds)
        self._music_panel.set_playing_state(self._music.is_playing)

    def _next_music_track(self) -> None:
        self._music.next_track()
        self._refresh_music_track_label()
        self._music_panel.set_playing_state(self._music.is_playing)
        self.show_status(f"⏭ {self._music.current_track or 'Next'}")

    # ------------------------------------------------------------------
    # Timer callbacks
    # ------------------------------------------------------------------

    def _register_timer_callbacks(self) -> None:
        self._timer.on_tick(self._on_tick)
        self._timer.on_phase_change(self._on_phase_change)
        self._timer.on_session_complete(self._on_session_complete)

        if self._music:
            self._music.on_track_change(self._refresh_music_track_label)

    def _on_tick(self, remaining_seconds: int) -> None:
        self._timer_widget.update_time(remaining_seconds)
        self.update_idletasks()

    def _on_phase_change(self, state) -> None:
        phase_names = {
            PomodoroState.WORK: "Work",
            PomodoroState.SHORT_BREAK: "Short Break",
            PomodoroState.LONG_BREAK: "Long Break",
        }
        name = phase_names.get(state, "Sẵn sàng")
        self._timer_widget.update_phase(name)
        self._timer_widget.set_paused_state(state == PomodoroState.PAUSED)
        
        if state == PomodoroState.WORK:
            self._phase_started_at = datetime.now()
            self.show_status("🔴 Bắt đầu làm việc!")
            
            if self._config.focus.focus_guard_enabled:
                self._focus_guard.start_guard()
                if hasattr(self, "_distraction_panel"):
                    self._distraction_panel.set_guard_active(True)
            else:
                self._focus_guard.stop_guard()
                if hasattr(self, "_distraction_panel"):
                    self._distraction_panel.set_guard_active(False)
            
            # Play sound only if it's returning from a break, not initial start
            duration = 5000
            if getattr(self, "_started_once", False):
                duration = self._play_notification_sound()
            self._started_once = True
            
            if hasattr(self, "_notifier"):
                self._notifier.notify_break_end(
                    duration=duration,
                    stop_callback=self._music.stop_notification_sound if self._music else None
                )
            
        elif state == PomodoroState.SHORT_BREAK:
            self.show_status("🟢 Nghỉ ngắn — thư giãn nào!")
            self._focus_guard.stop_guard()
            if hasattr(self, "_distraction_panel"):
                self._distraction_panel.set_guard_active(False)
            duration = self._play_notification_sound()
            if hasattr(self, "_notifier"):
                self._notifier.notify_work_end(
                    duration=duration,
                    stop_callback=self._music.stop_notification_sound if self._music else None
                )
            
        elif state == PomodoroState.LONG_BREAK:
            self.show_status("🔵 Nghỉ dài — tuyệt vời!")
            self._focus_guard.stop_guard()
            if hasattr(self, "_distraction_panel"):
                self._distraction_panel.set_guard_active(False)
            duration = self._play_notification_sound()
            if hasattr(self, "_notifier"):
                self._notifier.notify_long_break_end(
                    duration=duration,
                    stop_callback=self._music.stop_notification_sound if self._music else None
                )

    def _play_notification_sound(self) -> int:
        """Phát âm thanh thông báo khi hết phiên và trả về thời lượng (ms)."""
        duration = 5000
        if self._music:
            # Tạm ngừng nhạc nền nếu đang phát để nghe rõ chuông
            was_playing = self._music.is_playing
            if was_playing:
                self._pause_music()

            success, duration = self._music.play_notification_sound()
            if not success and self._config.music.notification_sound:
                self.show_status("⚠ Lỗi phát chuông báo (định dạng không hỗ trợ/file quá lớn).", 5000)

            if was_playing:
                # Đặt lịch tiếp tục phát nhạc sau khi chuông kết thúc
                self.after(duration, self._resume_music)
                
        return duration

    def _on_session_complete(self) -> None:
        if self._history and self._phase_started_at:
            completed_at = datetime.now()
            self._history.add_session(
                SessionEntry(
                    date=self._phase_started_at.strftime("%d/%m/%Y"),
                    start_time=self._phase_started_at.strftime("%H:%M"),
                    end_time=completed_at.strftime("%H:%M"),
                    phase="Work",
                    status="Completed",
                )
            )
            if hasattr(self, "_dashboard_panel"):
                self._dashboard_panel.refresh_data()
        self.show_status("🎉 Hoàn thành phiên làm việc!")

    # ------------------------------------------------------------------
    # Focus Guard
    # ------------------------------------------------------------------

    def _poll_focus_guard(self) -> None:
        """Kiểm tra cửa sổ đang focus mỗi 1.5 giây (UI thread)."""
        if self._config.focus.focus_guard_enabled:
            self._focus_guard.check()
        self.after(1500, self._poll_focus_guard)

    def _on_distraction_detected(self, app_name: str) -> None:
        """Callback khi FocusGuard phát hiện app sao nhãng đang được focus."""
        self._notifier.show_distraction_warning(
            app_name=app_name,
            on_focus_app=self._bring_to_front,
        )

    def _on_distraction_cleared(self) -> None:
        """Callback khi người dùng quay về app an toàn."""
        self._notifier.hide_distraction_warning()

    def _bring_to_front(self) -> None:
        """Đưa cửa sổ Promodo lên trước, đóng popup cảnh báo."""
        self._notifier.hide_distraction_warning()
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_guard_toggled(self, is_enabled: bool) -> None:
        """Callback khi bật/tắt chế độ tập trung từ DistractionPanel."""
        self._config.focus.focus_guard_enabled = is_enabled
        self._config.save()
        
        # Nếu đang ở phiên WORK, update ngay lập tức
        if self._timer.state == PomodoroState.WORK:
            if is_enabled:
                self._focus_guard.start_guard()
                if hasattr(self, "_distraction_panel"):
                    self._distraction_panel.set_guard_active(True)
            else:
                self._focus_guard.stop_guard()
                self._notifier.hide_distraction_warning()
                if hasattr(self, "_distraction_panel"):
                    self._distraction_panel.set_guard_active(False)
        else:
            if hasattr(self, "_distraction_panel"):
                self._distraction_panel.set_guard_active(False)
        
        status = "bật" if is_enabled else "tắt"
        self.show_status(f"🛡 Đã {status} chế độ tập trung!")

    def _remove_blocked_app(self, app_name: str) -> None:
        """Xóa app khỏi danh sách chặn (từ DistractionPanel)."""
        try:
            self._config.focus.blocked_apps.remove(app_name)
        except ValueError:
            pass
        self._config.save()
        self._focus_guard.set_blocked_apps(self._config.focus.blocked_apps)
        self._distraction_panel.set_blocked_apps(self._config.focus.blocked_apps)
        self.show_status(f"🗑 Đã bỏ chặn: {app_name}")

    # ------------------------------------------------------------------
    # Tick driver
    # ------------------------------------------------------------------

    def _schedule_tick(self) -> None:
        if self._music:
            self._music.check_music_end()
            self._music_panel.update_timeline(
                self._music.get_position(),
                self._music.get_length()
            )
            
        if not self._tick_running or self._timer.state == PomodoroState.IDLE:
            self._tick_running = False
            # We still need to poll music even if timer is idle
            self.after(1000, self._poll_music)
            return
            
        self._timer.tick()
        self.after(1000, self._schedule_tick)

    def _poll_music(self) -> None:
        if self._tick_running:
            return # _schedule_tick will handle it
        if self._music:
            self._music.check_music_end()
            self._music_panel.update_timeline(
                self._music.get_position(),
                self._music.get_length()
            )
        self.after(1000, self._poll_music)

    def _start_timer(self) -> None:
        self._timer.start()
        if not self._tick_running:
            self._tick_running = True
            self._schedule_tick()
        self.show_status("▶ Bắt đầu đếm ngược!")

    def _pause_timer(self) -> None:
        self._timer.pause()
        self._timer_widget.set_paused_state(True)
        self.show_status("⏸ Tạm dừng đếm ngược")

    def _resume_timer(self) -> None:
        self._timer.resume()
        self._timer_widget.set_paused_state(False)
        self.show_status("▶ Tiếp tục đếm ngược")

    def _reset_timer(self) -> None:
        self._tick_running = False
        self._timer.reset()
        self._focus_guard.stop_guard()
        if hasattr(self, "_distraction_panel"):
            self._distraction_panel.set_guard_active(False)
        self.show_status("🔄 Đã đặt lại đồng hồ")

    def _skip_phase(self) -> None:
        self._timer.skip_phase()
        self.show_status("⏭ Đã bỏ qua phiên")

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _open_settings(self, focus_tab: bool = False) -> None:
        if (
            self._settings_window is not None
            and self._settings_window.winfo_exists()
        ):
            self._settings_window.focus()
            if focus_tab:
                try:
                    self._settings_panel_ref._tabview.set("Tập trung")
                except Exception:
                    pass
            return

        self._settings_window = customtkinter.CTkToplevel(self)
        self._settings_window.title("⚙ Settings")
        self._settings_window.geometry("520x660")
        self._settings_window.resizable(True, True)
        self._settings_window.minsize(460, 500)

        panel = SettingsPanel(
            self._settings_window,
            config=self._config,
            on_session_save=self._on_session_settings_saved,
            on_music_save=self._on_music_settings_saved,
            on_background_save=self._on_background_settings_saved,
            on_focus_save=self._on_focus_settings_saved,
            on_status=self.show_status,
        )
        self._settings_panel_ref = panel
        panel.pack(fill="both", expand=True, padx=8, pady=8)

        if focus_tab:
            try:
                panel._tabview.set("Tập trung")
            except Exception:
                pass

        def on_close():
            panel.cleanup()
            self._settings_window.destroy()
            
        self._settings_window.protocol("WM_DELETE_WINDOW", on_close)
        self._settings_window.transient(self)
        self._settings_window.focus()

    def _on_session_settings_saved(self, durations: dict) -> None:
        """Apply saved session durations."""
        self._timer.set_duration(**durations)
        self.show_status("✅ Đã cập nhật thời lượng phiên!")

    def _on_music_settings_saved(self) -> None:
        """Apply saved music settings."""
        cfg = self._config
        if self._music:
            self._music.set_playback_mode(cfg.music.playback_mode)
            if cfg.music.notification_sound:
                self._music.set_notification_sound(
                    cfg.music.notification_sound
                )
            # Reload playlist from app folder
            if MUSIC_DIR.exists():
                files = sorted(
                    str(f) for f in MUSIC_DIR.iterdir()
                    if f.suffix.lower() in SUPPORTED_AUDIO
                )
                if files:
                    was_playing = self._music.is_playing
                    self._music.set_playlist_from_files(files)
                    if was_playing:
                        self._music.play()
            self._refresh_music_track_label()
        self.show_status("✅ Đã áp dụng cài đặt nhạc!")

    def _on_background_settings_saved(self) -> None:
        """Apply saved background settings."""
        self._apply_background()
        self._apply_theme_color()
        self.show_status("✅ Đã áp dụng cài đặt giao diện!")

    def _on_focus_settings_saved(self) -> None:
        """Apply saved focus/distraction settings."""
        self._focus_guard.set_blocked_apps(self._config.focus.blocked_apps)
        if hasattr(self, "_distraction_panel"):
            self._distraction_panel.set_blocked_apps(self._config.focus.blocked_apps)
        # Nếu guard tắt, đóng popup nếu có
        if not self._config.focus.focus_guard_enabled:
            self._focus_guard.stop_guard()
            self._notifier.hide_distraction_warning()
        self.show_status("✅ Đã áp dụng cài đặt tập trung!")
