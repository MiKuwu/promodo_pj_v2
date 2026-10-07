"""
Desktop notification manager.

👤 Người 2 – Core
Phụ trách: Gửi desktop notification khi phiên kết thúc.
Sử dụng CustomTkinter Toplevel để tạo popup không chặn (non-blocking) góc phải màn hình.
"""

import customtkinter

class NotificationManager:
    """Sends desktop notifications when a Pomodoro session ends."""

    APP_NAME: str = "Pomodoro Timer"

    def notify_work_end(self, duration: int = 5000, stop_callback=None) -> None:
        """Gửi thông báo khi phiên làm việc kết thúc."""
        self._send(
            title="⏰ Hết giờ làm việc!",
            message="Đã đến lúc nghỉ giải lao. Thư giãn một chút nhé! 🎉",
            duration=duration, stop_callback=stop_callback
        )

    def notify_break_end(self, duration: int = 5000, stop_callback=None) -> None:
        """Gửi thông báo khi nghỉ ngắn kết thúc."""
        self._send(
            title="💪 Hết giờ nghỉ!",
            message="Đã đến lúc bắt đầu phiên học mới. Tập trung nào!",
            duration=duration, stop_callback=stop_callback
        )

    def notify_long_break_end(self, duration: int = 5000, stop_callback=None) -> None:
        """Gửi thông báo khi nghỉ dài kết thúc."""
        self._send(
            title="🚀 Hết giờ nghỉ dài!",
            message="Đã sẵn sàng cho vòng Pomodoro mới chưa? Let's go!",
            duration=duration, stop_callback=stop_callback
        )

    def notify_warning(self, minutes_left: int = 5, duration: int = 5000) -> None:
        """Gửi thông báo cảnh báo còn N phút nữa hết phiên."""
        self._send(
            title=f"⏳ Còn {minutes_left} phút!",
            message=f"Phiên sẽ kết thúc sau {minutes_left} phút nữa.",
            duration=duration
        )

    def _send(self, title: str, message: str, duration: int = 5000, stop_callback=None) -> None:
        """Gửi notification dạng popup giữa màn hình."""
        toast = customtkinter.CTkToplevel()
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        
        # Hàm đóng popup
        def close_toast():
            if stop_callback:
                stop_callback()
            toast.destroy()
        
        # Thiết kế giao diện Toast
        frame = customtkinter.CTkFrame(toast, border_width=2, border_color="#1f6aa5")
        frame.pack(fill="both", expand=True)
        
        # Header frame for title and close button
        header_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        customtkinter.CTkLabel(
            header_frame, text=title, font=customtkinter.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        customtkinter.CTkButton(
            header_frame, text="X", width=30, fg_color="red", hover_color="#darkred",
            command=close_toast
        ).pack(side="right")
        
        customtkinter.CTkLabel(
            frame, text=message, wraplength=300, justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 15))
        
        # Tính toán vị trí giữa màn hình
        toast.update_idletasks()  # Cập nhật size trước
        width = 340
        height = 110
        screen_width = toast.winfo_screenwidth()
        screen_height = toast.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        toast.geometry(f"{width}x{height}+{x}+{y}")
        
        # Tự động đóng sau duration ms
        toast.after(duration, close_toast)

    # ------------------------------------------------------------------
    # Distraction warning (blocking popup — cannot be dismissed by user)
    # ------------------------------------------------------------------

    def show_distraction_warning(self, app_name: str, on_focus_app: callable) -> None:
        """Hiển thị popup cảnh báo chặn app sao nhãng, KHÔNG cho đóng bằng tay.

        Popup ở trên cùng (topmost), có nút duy nhất là "Quay lại tập trung".
        Sẽ tự tắt khi on_focus_app() được gọi bởi FocusGuard.

        Args:
            app_name: Tên exe của app đang gây sao nhãng.
            on_focus_app: Callable mà UI gọi để đóng popup (gắn cho nút quay lại).
        """
        # Nếu đã có popup đang mở thì không mở thêm
        if getattr(self, "_distraction_popup", None):
            try:
                if self._distraction_popup.winfo_exists():
                    # Cập nhật tên app nếu cần
                    if hasattr(self, "_distraction_app_label"):
                        self._distraction_app_label.configure(
                            text=f"🚨  {app_name}"
                        )
                    return
            except Exception:
                pass

        popup = customtkinter.CTkToplevel()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        # Không cho close bằng Alt+F4
        popup.protocol("WM_DELETE_WINDOW", lambda: None)

        self._distraction_popup = popup

        outer = customtkinter.CTkFrame(
            popup, border_width=3, border_color="#cc3333",
            fg_color=("#fff0f0", "#2a0a0a"), corner_radius=14,
        )
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        customtkinter.CTkLabel(
            outer,
            text="⛔  CẢNH BÁO MẤT TẬP TRUNG",
            font=customtkinter.CTkFont(size=18, weight="bold"),
            text_color="#cc3333",
        ).pack(pady=(18, 6))

        customtkinter.CTkLabel(
            outer,
            text="Bạn đang dùng ứng dụng gây sao nhãng:",
            font=customtkinter.CTkFont(size=13),
        ).pack()

        self._distraction_app_label = customtkinter.CTkLabel(
            outer,
            text=f"🚨  {app_name}",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text_color="#e05252",
        )
        self._distraction_app_label.pack(pady=4)

        customtkinter.CTkLabel(
            outer,
            text="Hãy quay lại Promodo Timer để tiếp tục tập trung!",
            font=customtkinter.CTkFont(size=12),
            text_color="gray",
            wraplength=320,
        ).pack(pady=(0, 10))

        def _back_to_focus():
            on_focus_app()

        customtkinter.CTkButton(
            outer,
            text="✅  Quay lại tập trung",
            font=customtkinter.CTkFont(size=14, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#174f80",
            command=_back_to_focus,
            height=40,
        ).pack(pady=(0, 18), padx=32, fill="x")

        # Tính vị trí giữa màn hình
        popup.update_idletasks()
        w, h = 380, 260
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        popup.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def hide_distraction_warning(self) -> None:
        """Đóng popup cảnh báo sao nhãng (gọi khi người dùng quay về app an toàn)."""
        popup = getattr(self, "_distraction_popup", None)
        if popup:
            try:
                if popup.winfo_exists():
                    popup.destroy()
            except Exception:
                pass
            self._distraction_popup = None

