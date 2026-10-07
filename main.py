import tkinter as tk

def _handle_notification(state, notifier) -> None:
    from src.core.timer import PomodoroState
    if state in (PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK):
        notifier.notify_work_end()
    elif state == PomodoroState.WORK:
        notifier.notify_break_end()

def show_splash():
    splash = tk.Tk()
    splash.overrideredirect(True)
    
    width, height = 450, 250
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    splash.geometry(f"{width}x{height}+{int(x)}+{int(y)}")
    
    splash.configure(bg="#1a1a1a")
    
    border = tk.Frame(splash, bg="#3498db")
    border.pack(fill="both", expand=True, padx=1, pady=1)
    
    inner = tk.Frame(border, bg="#1a1a1a")
    inner.pack(fill="both", expand=True)
    
    tk.Label(
        inner, text="Promodo Timer", font=("Segoe UI", 28, "bold"),
        bg="#1a1a1a", fg="white"
    ).pack(expand=True, pady=(50, 5))
    
    tk.Label(
        inner, text="Made by NaHBro Team", font=("Segoe UI", 12),
        bg="#1a1a1a", fg="#aaaaaa"
    ).pack(expand=True, pady=(0, 20))
    
    progress_label = tk.Label(
        inner, text="Khởi tạo ứng dụng...", font=("Segoe UI", 9, "italic"),
        bg="#1a1a1a", fg="#3498db"
    )
    progress_label.pack(side="bottom", pady=15, anchor="w", padx=20)
    
    splash.update()
    return splash, progress_label

def main() -> None:
    splash, progress_label = show_splash()
    
    progress_label.config(text="Đang tải thư viện giao diện...")
    splash.update()
    import customtkinter
    
    progress_label.config(text="Đang tải modules hệ thống...")
    splash.update()
    from src.core.app_config import AppConfig
    from src.core.timer import PomodoroTimer
    from src.core.music_player import MusicPlayer
    from src.core.notification import NotificationManager
    from src.core.history import History
    from src.ui.main_window import MainWindow

    progress_label.config(text="Đang nạp cấu hình...")
    splash.update()
    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")
    config = AppConfig()

    progress_label.config(text="Đang nạp dữ liệu phiên...")
    splash.update()
    timer = PomodoroTimer(
        work_minutes=config.session.work_minutes,
        short_break_minutes=config.session.short_break_minutes,
        long_break_minutes=config.session.long_break_minutes,
        sessions_before_long=config.session.sessions_before_long,
    )
    music_player = MusicPlayer()
    notifier = NotificationManager()
    history = History()

    timer.on_phase_change(
        lambda state: _handle_notification(state, notifier)
    )

    # Đóng splash screen TRƯỚC KHI tạo MainWindow
    # Điều này bắt buộc để tránh lỗi TclError với pyimage (vì MainWindow tạo một Tk root mới)
    splash.destroy()
    import tkinter
    tkinter._default_root = None

    window = MainWindow(
        timer=timer,
        music_player=music_player,
        history=history,
        config=config,
    )

    window.mainloop()

if __name__ == "__main__":
    main()
