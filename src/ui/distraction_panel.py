"""
Distraction panel — danh sách ứng dụng gây sao nhãng (hiển thị dưới Music Panel).

👤 Người 3 – Settings + Music UI + History
Chỉ hiển thị UI, không chứa logic. Kết nối qua callbacks.
"""

import customtkinter
from typing import Callable, List, Optional


class DistractionPanel(customtkinter.CTkFrame):
    """Panel nhỏ hiển thị danh sách app bị chặn và trạng thái Focus Guard.

    Args:
        master: Widget cha.
        is_guard_enabled: Trạng thái bật/tắt ban đầu.
        on_toggle_guard: Callback(bool) khi bật/tắt công tắc.
        on_remove_app: Callback(exe_name) khi người dùng xóa một app khỏi danh sách.
        on_open_settings: Callback mở tab cài đặt Tập trung trong Settings.
    """

    def __init__(
        self,
        master,
        is_guard_enabled: bool,
        on_toggle_guard: Callable[[bool], None],
        on_remove_app: Callable[[str], None],
        on_open_settings: Callable[[], None],
        **kwargs,
    ) -> None:
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self._is_guard_enabled = is_guard_enabled
        self._on_toggle_guard = on_toggle_guard
        self._on_remove_app = on_remove_app
        self._on_open_settings = on_open_settings
        self._blocked_apps: List[str] = []
        self._is_guard_active: bool = False

        self._build_ui()

    def _build_ui(self) -> None:
        """Tạo giao diện panel."""
        # Header
        header = customtkinter.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=4, pady=(6, 2))

        customtkinter.CTkLabel(
            header,
            text="🚫 App gây sao nhãng",
            font=customtkinter.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(side="left", padx=4)

        customtkinter.CTkButton(
            header,
            text="⚙",
            width=28,
            height=24,
            fg_color="transparent",
            border_width=1,
            command=self._on_open_settings,
        ).pack(side="right", padx=4)

        # Toggle Switch
        toggle_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=8, pady=(2, 4))
        
        self._guard_var = customtkinter.BooleanVar(value=self._is_guard_enabled)
        self._guard_switch = customtkinter.CTkSwitch(
            toggle_frame, 
            text="Bật chặn app",
            variable=self._guard_var,
            command=self._on_switch_toggled
        )
        self._guard_switch.pack(side="left")

        # Status badge
        self._status_label = customtkinter.CTkLabel(
            self,
            text="",
            text_color="gray",
            font=customtkinter.CTkFont(size=11),
            anchor="w",
        )
        self._status_label.pack(fill="x", padx=8, pady=(0, 4))
        self._update_status_badge()

        # App list scrollable area (giới hạn chiều cao)
        self._list_frame = customtkinter.CTkScrollableFrame(
            self, fg_color=("gray90", "gray18"), corner_radius=8
        )
        self._list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self._empty_label: Optional[customtkinter.CTkLabel] = None
        self._render_list()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_blocked_apps(self, apps: List[str]) -> None:
        """Cập nhật danh sách app bị chặn và refresh UI.

        Args:
            apps: Danh sách exe-name.
        """
        self._blocked_apps = list(apps)
        self._render_list()

    def set_guard_active(self, active: bool) -> None:
        """Cập nhật badge trạng thái guard.

        Args:
            active: True = đang bảo vệ (timer WORK đang chạy).
        """
        self._is_guard_active = active
        self._update_status_badge()

    def _update_status_badge(self) -> None:
        """Cập nhật giao diện trạng thái dựa trên toggle và timer."""
        if not self._guard_var.get():
            self._status_label.configure(
                text="❌ Đã tắt chế độ chặn app",
                text_color="gray",
            )
        elif self._is_guard_active:
            self._status_label.configure(
                text="🛡 Đang bảo vệ — chế độ tập trung bật",
                text_color="#4CAF50",
            )
        else:
            self._status_label.configure(
                text="● Chưa kích hoạt — bắt đầu timer để bật",
                text_color="gray",
            )

    def _on_switch_toggled(self) -> None:
        """Khi người dùng gạt công tắc."""
        self._update_status_badge()
        self._on_toggle_guard(self._guard_var.get())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _render_list(self) -> None:
        """Xóa và vẽ lại danh sách app."""
        for widget in self._list_frame.winfo_children():
            try:
                widget.pack_forget()
                widget.destroy()
            except Exception:
                pass

        if not self._blocked_apps:
            self._empty_label = customtkinter.CTkLabel(
                self._list_frame,
                text="Chưa có app nào trong danh sách.\nVào ⚙ Setting để thêm.",
                text_color="gray",
                font=customtkinter.CTkFont(size=11),
                justify="center",
            )
            self._empty_label.pack(pady=16)
            return

        for app in self._blocked_apps:
            row = customtkinter.CTkFrame(
                self._list_frame, fg_color="transparent", height=28
            )
            row.pack(fill="x", padx=4, pady=1)
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)

            customtkinter.CTkLabel(
                row,
                text=f"🚫 {app}",
                font=customtkinter.CTkFont(size=11),
                anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=4)

            customtkinter.CTkButton(
                row,
                text="✕",
                width=24,
                height=22,
                fg_color="transparent",
                text_color="gray",
                hover_color="#cc3333",
                command=lambda a=app: self._on_remove_app(a),
            ).grid(row=0, column=1, padx=4)
