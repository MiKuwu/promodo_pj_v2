"""
Settings panel — giao diện cấu hình ứng dụng với 3 tab.

👤 Người 3 – Settings + Music UI + History
Tabs: Session | Music | Background
"""

import customtkinter
from pathlib import Path
from tkinter import filedialog, colorchooser
from typing import Callable, Optional

from src.core.app_config import (
    AppConfig, MUSIC_DIR, SOUNDS_DIR, BACKGROUNDS_DIR
)

SUPPORTED_FORMATS_AUDIO = {".mp3", ".wav", ".ogg"}
SUPPORTED_FORMATS_IMAGE = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


class SettingsPanel(customtkinter.CTkFrame):
    """Panel cấu hình với 4 tab: Session, Music, Background, Tập trung.

    Args:
        master: Widget cha.
        config: AppConfig instance.
        on_session_save: Callback khi lưu session settings.
        on_music_save: Callback khi lưu music settings.
        on_background_save: Callback khi lưu background settings.
        on_focus_save: Callback khi lưu focus settings.
        on_status: Callback thông báo trạng thái (str).
    """

    def __init__(
        self,
        master,
        config: "AppConfig",
        on_session_save: Callable[[dict], None],
        on_music_save: Callable,
        on_background_save: Callable,
        on_focus_save: Callable = None,
        on_status: Callable[[str], None] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._config = config
        self._on_session_save = on_session_save
        self._on_music_save = on_music_save
        self._on_background_save = on_background_save
        self._on_focus_save = on_focus_save or (lambda: None)
        self._on_status = on_status or (lambda s: None)
        self._test_sound = None

        self._build_ui()

    def cleanup(self) -> None:
        """Dọn dẹp tài nguyên (tắt nhạc thử) khi đóng cửa sổ."""
        if getattr(self, "_test_sound", None):
            try:
                self._test_sound.stop()
            except Exception:
                pass

    def _status(self, msg: str) -> None:
        """Gửi thông báo trạng thái ra UI."""
        self._on_status(msg)

    def _build_ui(self) -> None:
        """Tạo tabview với các tab."""
        self._tabview = customtkinter.CTkTabview(self, anchor="nw")
        self._tabview.pack(fill="both", expand=True, padx=4, pady=4)

        self._tabview.add("Phiên học")
        self._tabview.add("Âm nhạc")
        self._tabview.add("Tập trung")
        if hasattr(self, "_build_background_tab"):
            try:
                self._tabview.add("Giao diện")
            except Exception:
                pass

        self._build_session_tab(self._tabview.tab("Phiên học"))
        self._build_music_tab(self._tabview.tab("Âm nhạc"))
        self._build_focus_tab(self._tabview.tab("Tập trung"))
        if hasattr(self, "_build_background_tab"):
            try:
                self._build_background_tab(self._tabview.tab("Giao diện"))
            except Exception:
                pass

    # ==================================================================
    # SESSION TAB
    # ==================================================================

    def _build_session_tab(self, parent) -> None:
        """Tab cấu hình thời lượng phiên."""
        scroll = customtkinter.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True)

        self._session_entries = {}
        fields = [
            ("work", "Làm việc (phút)", self._config.session.work_minutes),
            ("short_break", "Nghỉ ngắn (phút)",
             self._config.session.short_break_minutes),
            ("long_break", "Nghỉ dài (phút)",
             self._config.session.long_break_minutes),
            ("sessions_before_long", "Số phiên để nghỉ dài",
             self._config.session.sessions_before_long),
        ]

        for key, label, default_val in fields:
            customtkinter.CTkLabel(
                scroll, text=label
            ).pack(anchor="w", padx=12, pady=(10, 0))
            entry = customtkinter.CTkEntry(scroll)
            entry.pack(fill="x", padx=12, pady=(2, 0))
            entry.insert(0, str(default_val))
            self._session_entries[key] = entry

        self._session_error = customtkinter.CTkLabel(
            scroll, text="", text_color="red"
        )
        self._session_error.pack(padx=12, pady=(6, 0))

        customtkinter.CTkButton(
            scroll, text="💾 Lưu cài đặt phiên", command=self._save_session
        ).pack(padx=12, pady=12)

    def _save_session(self) -> None:
        """Lưu cấu hình session."""
        try:
            values = {
                k: int(e.get().strip())
                for k, e in self._session_entries.items()
            }
        except ValueError:
            self._session_error.configure(text="Vui lòng nhập số nguyên.")
            return

        if any(v <= 0 for v in values.values()):
            self._session_error.configure(text="Các giá trị phải lớn hơn 0.")
            return

        self._session_error.configure(text="")
        self._config.session.work_minutes = values["work"]
        self._config.session.short_break_minutes = values["short_break"]
        self._config.session.long_break_minutes = values["long_break"]
        self._config.session.sessions_before_long = values[
            "sessions_before_long"
        ]
        self._config.save()
        self._on_session_save({
            "work": values["work"],
            "short_break": values["short_break"],
            "long_break": values["long_break"],
        })
        self._status("✅ Đã cập nhật cài đặt phiên!")

    # ==================================================================
    # MUSIC TAB
    # ==================================================================

    def _build_music_tab(self, parent) -> None:
        """Tab quản lý nhạc nền, âm thanh thông báo, playback mode."""
        scroll = customtkinter.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True)

        # --- Notification Sound ---
        customtkinter.CTkLabel(
            scroll, text="🔔 Chuông báo hết giờ",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self._sound_listbox = customtkinter.CTkFrame(scroll)
        self._sound_listbox.pack(fill="x", padx=12, pady=2)
        self._refresh_sound_list()

        sound_btns = customtkinter.CTkFrame(scroll, fg_color="transparent")
        sound_btns.pack(fill="x", padx=12, pady=4)
        customtkinter.CTkButton(
            sound_btns, text="➕ Thêm chuông", width=120,
            command=self._add_sound,
        ).pack(side="left", padx=2)

        # --- Playlist ---
        customtkinter.CTkLabel(
            scroll, text="🎵 Danh sách nhạc nền",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(16, 4))

        self._playlist_listbox = customtkinter.CTkFrame(scroll)
        self._playlist_listbox.pack(fill="x", padx=12, pady=2)
        self._refresh_playlist()

        playlist_btns = customtkinter.CTkFrame(scroll, fg_color="transparent")
        playlist_btns.pack(fill="x", padx=12, pady=4)
        customtkinter.CTkButton(
            playlist_btns, text="➕ Thêm nhạc", width=120,
            command=self._add_song,
        ).pack(side="left", padx=2)

        # --- Playback Mode ---
        customtkinter.CTkLabel(
            scroll, text="🔁 Chế độ phát nhạc",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(16, 4))

        self._playback_var = customtkinter.StringVar(
            value=self._config.music.playback_mode
        )
        modes_frame = customtkinter.CTkFrame(scroll, fg_color="transparent")
        modes_frame.pack(fill="x", padx=12, pady=4)
        for text, val in [
            ("🔂 Lặp một bài", "repeat_one"),
            ("🔁 Lặp toàn bộ", "repeat_all"),
            ("🔀 Phát ngẫu nhiên", "shuffle"),
        ]:
            customtkinter.CTkRadioButton(
                modes_frame, text=text, variable=self._playback_var,
                value=val,
            ).pack(anchor="w", pady=2)

        customtkinter.CTkButton(
            scroll, text="💾 Lưu cài đặt nhạc",
            command=self._save_music,
        ).pack(padx=12, pady=12)

        # Ghi chú đường dẫn thư mục
        customtkinter.CTkLabel(
            scroll,
            text=f"📁 Thư mục nhạc: {MUSIC_DIR}",
            text_color="gray", wraplength=400,
        ).pack(anchor="w", padx=12, pady=(0, 4))
        customtkinter.CTkLabel(
            scroll,
            text=f"📁 Thư mục chuông: {SOUNDS_DIR}",
            text_color="gray", wraplength=400,
        ).pack(anchor="w", padx=12, pady=(0, 8))

    def _refresh_sound_list(self) -> None:
        """Cập nhật danh sách âm thanh thông báo."""
        for w in self._sound_listbox.winfo_children():
            w.destroy()

        sounds = sorted(SOUNDS_DIR.iterdir()) if SOUNDS_DIR.exists() else []
        sounds = [s for s in sounds if s.suffix.lower() in SUPPORTED_FORMATS_AUDIO]

        if not sounds:
            customtkinter.CTkLabel(
                self._sound_listbox, text="Chưa có file chuông nào.",
                text_color="gray",
            ).pack(padx=8, pady=4)
            return

        current = self._config.music.notification_sound
        for sound in sounds:
            row = customtkinter.CTkFrame(
                self._sound_listbox, fg_color="transparent"
            )
            row.pack(fill="x", pady=1)

            is_selected = str(sound) == current
            indicator = "🔔" if is_selected else "  "
            
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)
            
            lbl = customtkinter.CTkLabel(
                row, text=f"{indicator} {sound.name}",
                font=customtkinter.CTkFont(
                    weight="bold" if is_selected else "normal"
                ), anchor="w"
            )
            lbl.grid(row=0, column=0, sticky="ew", padx=4)

            s_path = str(sound)
            btn_frame = customtkinter.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=1, sticky="e", padx=4)
            
            customtkinter.CTkButton(
                btn_frame, text="Chọn", width=50,
                command=lambda p=s_path: self._select_sound(p),
            ).pack(side="left", padx=2)
            customtkinter.CTkButton(
                btn_frame, text="🗑", width=30, fg_color="red",
                command=lambda p=s_path: self._remove_sound(p),
            ).pack(side="left", padx=2)

    def _add_sound(self) -> None:
        """Thêm file âm thanh thông báo. Chỉ cho phép 1 file."""
        filetypes = [("File âm thanh", "*.wav *.ogg *.mp3")]
        path = filedialog.askopenfilename(
            parent=self, title="Chọn file chuông thông báo",
            filetypes=filetypes,
        )
        if path:
            # Xóa các file cũ
            if SOUNDS_DIR.exists():
                for f in SOUNDS_DIR.iterdir():
                    if f.is_file():
                        try:
                            f.unlink()
                        except Exception:
                            pass
                            
            dest = AppConfig.import_sound_file(path)
            if dest:
                # Tự động chọn file vừa thêm
                self._select_sound(str(dest))
            else:
                self._status("❌ Thêm file chuông thất bại.")

    def _select_sound(self, path: str) -> None:
        """Chọn file làm notification sound."""
        self._config.music.notification_sound = path
        self._refresh_sound_list()
        
        # Stop previous test sound if it's playing
        if getattr(self, "_test_sound", None):
            try:
                self._test_sound.stop()
            except Exception:
                pass
        
        # Test play the sound immediately
        success = False
        try:
            import pygame
            if pygame.mixer.get_init():
                self._test_sound = pygame.mixer.Sound(path)
                self._test_sound.play()
                success = True
        except Exception:
            self._test_sound = None
            
        if success:
            self._status(f"🔔 Chuông báo: {Path(path).name}")
        else:
            self._status(f"⚠ Chú ý: File {Path(path).name} có thể không được hỗ trợ hoặc quá lớn.")

    def _remove_sound(self, path: str) -> None:
        """Xóa file âm thanh thông báo."""
        if self._config.music.notification_sound == path:
            self._config.music.notification_sound = ""
        AppConfig.remove_file(path)
        self._refresh_sound_list()
        self._status(f"🗑 Đã xóa chuông: {Path(path).name}")

    def _refresh_playlist(self) -> None:
        """Cập nhật danh sách playlist."""
        for w in self._playlist_listbox.winfo_children():
            w.destroy()

        # Update playlist config based on existing files
        existing_files = {str(f.resolve()): f for f in MUSIC_DIR.iterdir()} if MUSIC_DIR.exists() else {}
        existing_files = {k: v for k, v in existing_files.items() if v.suffix.lower() in SUPPORTED_FORMATS_AUDIO}
        
        # Keep order from config
        ordered_files = []
        for path_str in self._config.music.playlist_files:
            try:
                resolved_path = str(Path(path_str).resolve())
                if resolved_path in existing_files:
                    ordered_files.append(existing_files.pop(resolved_path))
            except Exception:
                pass
        
        # Add any remaining files (e.g., added manually)
        for f in sorted(existing_files.values(), key=lambda x: x.name):
            ordered_files.append(f)
            
        # Save back the normalized order
        self._config.music.playlist_files = [str(f.resolve()) for f in ordered_files]

        if not ordered_files:
            customtkinter.CTkLabel(
                self._playlist_listbox, text="Chưa có bài hát nào trong danh sách.",
                text_color="gray",
            ).pack(padx=8, pady=4)
            return

        for i, f in enumerate(ordered_files):
            row = customtkinter.CTkFrame(
                self._playlist_listbox, fg_color="transparent"
            )
            row.pack(fill="x", pady=1)
            
            # Using grid inside row to prevent buttons from being squished
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)
            
            lbl = customtkinter.CTkLabel(
                row, text=f"🎵 {f.name}", anchor="w"
            )
            lbl.grid(row=0, column=0, sticky="ew", padx=4)
            
            btn_frame = customtkinter.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=1, sticky="e", padx=4)
            
            f_path = str(f)
            
            # Up button
            customtkinter.CTkButton(
                btn_frame, text="↑", width=30,
                state="normal" if i > 0 else "disabled",
                command=lambda idx=i: self._move_song(idx, -1)
            ).pack(side="left", padx=1)
            
            # Down button
            customtkinter.CTkButton(
                btn_frame, text="↓", width=30,
                state="normal" if i < len(ordered_files) - 1 else "disabled",
                command=lambda idx=i: self._move_song(idx, 1)
            ).pack(side="left", padx=1)
            
            # Delete button
            customtkinter.CTkButton(
                btn_frame, text="🗑", width=30, fg_color="red",
                command=lambda p=f_path: self._remove_song(p),
            ).pack(side="left", padx=1)

    def _move_song(self, index: int, direction: int) -> None:
        """Di chuyển vị trí bài hát (Lên/Xuống)."""
        new_index = index + direction
        playlist = self._config.music.playlist_files
        if 0 <= index < len(playlist) and 0 <= new_index < len(playlist):
            playlist[index], playlist[new_index] = playlist[new_index], playlist[index]
            self._refresh_playlist()
            
    def _add_song(self) -> None:
        """Thêm bài hát vào playlist."""
        filetypes = [("File âm thanh", "*.mp3 *.wav *.ogg")]
        paths = filedialog.askopenfilenames(
            parent=self, title="Chọn bài hát",
            filetypes=filetypes,
        )
        added = 0
        for path in paths:
            dest = AppConfig.import_music_file(path)
            if dest:
                added += 1
        if added:
            self._refresh_playlist()
            self._status(f"✅ Đã thêm {added} bài hát vào danh sách!")

    def _remove_song(self, path: str) -> None:
        """Xóa bài hát khỏi playlist."""
        name = Path(path).name
        AppConfig.remove_file(path)
        self._refresh_playlist()
        self._status(f"🗑 Đã xóa bài: {name}")

    def _save_music(self) -> None:
        """Lưu music settings."""
        self._config.music.playback_mode = self._playback_var.get()

        # Cập nhật playlist files từ thư mục
        if MUSIC_DIR.exists():
            files = sorted(
                str(f) for f in MUSIC_DIR.iterdir()
                if f.suffix.lower() in SUPPORTED_FORMATS_AUDIO
            )
            self._config.music.playlist_files = files
        self._config.save()
        self._on_music_save()
        self._status("✅ Đã lưu cài đặt nhạc!")

    # ==================================================================
    # FOCUS TAB
    # ==================================================================

    def _build_focus_tab(self, parent) -> None:
        """Tab quản lý danh sách ứng dụng gây sao nhãng."""
        scroll = customtkinter.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True)

        # --- App list ---
        customtkinter.CTkLabel(
            scroll, text="🚫 Danh sách app bị chặn",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(16, 4))

        self._focus_list_frame = customtkinter.CTkFrame(scroll)
        self._focus_list_frame.pack(fill="x", padx=12, pady=2)
        self._refresh_focus_list()

        # --- Buttons ---
        btn_frame = customtkinter.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=6)

        customtkinter.CTkButton(
            btn_frame, text="➕ Thêm thủ công", width=140,
            command=self._add_app_manual,
        ).pack(side="left", padx=2)

        customtkinter.CTkButton(
            btn_frame, text="🔍 Quét máy", width=110,
            command=self._scan_running_apps,
        ).pack(side="left", padx=2)

        # --- Scan result frame (ẩn ban đầu) ---
        self._scan_frame_wrapper = customtkinter.CTkFrame(scroll, fg_color="transparent")
        self._scan_frame_wrapper.pack(fill="x", padx=12, pady=4)

        self._scan_label = customtkinter.CTkLabel(
            self._scan_frame_wrapper, text="", text_color="gray",
            font=customtkinter.CTkFont(size=11), anchor="w",
        )
        self._scan_label.pack(anchor="w")

        self._scan_result_frame = customtkinter.CTkScrollableFrame(
            self._scan_frame_wrapper, height=120, fg_color=("gray88", "gray20")
        )
        # Không pack ngay — chỉ hiện khi quét xong

        # --- Save button ---
        customtkinter.CTkButton(
            scroll, text="💾 Lưu cài đặt tập trung",
            command=self._save_focus,
        ).pack(padx=12, pady=14)

    def _refresh_focus_list(self) -> None:
        """Vẽ lại danh sách app bị chặn."""
        for w in self._focus_list_frame.winfo_children():
            w.destroy()

        apps = self._config.focus.blocked_apps
        if not apps:
            customtkinter.CTkLabel(
                self._focus_list_frame,
                text="Chưa có app nào. Thêm thủ công hoặc quét máy.",
                text_color="gray",
            ).pack(padx=8, pady=6)
            return

        for app in apps:
            row = customtkinter.CTkFrame(
                self._focus_list_frame, fg_color="transparent"
            )
            row.pack(fill="x", pady=1)
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)

            customtkinter.CTkLabel(
                row, text=f"🚫 {app}", anchor="w"
            ).grid(row=0, column=0, sticky="ew", padx=8, pady=2)

            customtkinter.CTkButton(
                row, text="🗑", width=32, fg_color="red",
                command=lambda a=app: self._remove_blocked_app(a),
            ).grid(row=0, column=1, padx=4, pady=2)

    def _add_app_manual(self) -> None:
        """Mở dialog nhập tên exe thủ công."""
        dialog = customtkinter.CTkInputDialog(
            text="Nhập tên file exe của app\n(ví dụ: chrome.exe, discord.exe)",
            title="Thêm app sao nhãng",
        )
        val = dialog.get_input()
        if val:
            val = val.strip().lower()
            if not val.endswith(".exe"):
                val += ".exe"
            if val not in self._config.focus.blocked_apps:
                self._config.focus.blocked_apps.append(val)
                self._refresh_focus_list()
                self._status(f"✅ Đã thêm: {val}")
            else:
                self._status(f"⚠ {val} đã có trong danh sách.")

    def _remove_blocked_app(self, app: str) -> None:
        """Xóa app khỏi danh sách chặn."""
        try:
            self._config.focus.blocked_apps.remove(app)
        except ValueError:
            pass
        self._refresh_focus_list()
        self._status(f"🗑 Đã xóa: {app}")

    def _scan_running_apps(self) -> None:
        """Quét tiến trình đang chạy và hiện danh sách để người dùng chọn."""
        from src.core.focus_guard import FocusGuard
        self._scan_label.configure(text="⏳ Đang quét tiến trình...")
        self.update_idletasks()

        apps = FocusGuard.scan_running_apps()
        # Loại bỏ những app đã trong danh sách
        already = set(self._config.focus.blocked_apps)
        new_apps = [a for a in apps if a not in already]

        # Xóa kết quả cũ
        for w in self._scan_result_frame.winfo_children():
            w.destroy()

        if not new_apps:
            self._scan_label.configure(text="✅ Không tìm thấy app mới để thêm.")
            self._scan_result_frame.pack_forget()
            return

        self._scan_label.configure(
            text=f"🔍 Tìm thấy {len(new_apps)} app — chọn để thêm vào danh sách chặn:"
        )
        self._scan_result_frame.pack(fill="x", pady=(4, 0))

        for app in new_apps:
            row = customtkinter.CTkFrame(
                self._scan_result_frame, fg_color="transparent"
            )
            row.pack(fill="x", pady=1)
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)

            customtkinter.CTkLabel(
                row, text=app, anchor="w",
                font=customtkinter.CTkFont(size=11),
            ).grid(row=0, column=0, sticky="ew", padx=8)

            customtkinter.CTkButton(
                row, text="+ Chặn", width=70, height=24,
                command=lambda a=app: self._add_from_scan(a),
            ).grid(row=0, column=1, padx=4, pady=1)

    def _add_from_scan(self, app: str) -> None:
        """Thêm app từ kết quả quét vào danh sách."""
        if app not in self._config.focus.blocked_apps:
            self._config.focus.blocked_apps.append(app)
            self._refresh_focus_list()
            self._status(f"✅ Đã thêm: {app}")
        else:
            self._status(f"⚠ {app} đã có trong danh sách.")

    def _save_focus(self) -> None:
        """Lưu cài đặt tập trung."""
        self._config.save()
        self._on_focus_save()
        self._status("✅ Đã lưu cài đặt tập trung!")

    # ==================================================================
    # BACKGROUND TAB
    # ==================================================================

    def _build_background_tab(self, parent) -> None:
        """Tab cấu hình ảnh nền và màu theme."""
        scroll = customtkinter.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True)

        # --- Theme Color ---
        customtkinter.CTkLabel(
            scroll, text="🎨 Màu chủ đạo (Nút bấm)",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(16, 4))

        color_row = customtkinter.CTkFrame(scroll, fg_color="transparent")
        color_row.pack(fill="x", padx=12, pady=4)

        self._color_preview = customtkinter.CTkLabel(
            color_row, text="    ",
            fg_color=self._config.background.button_color,
            corner_radius=6, width=40, height=30,
        )
        self._color_preview.pack(side="left", padx=(0, 8))

        self._color_label = customtkinter.CTkLabel(
            color_row, text=self._config.background.button_color,
        )
        self._color_label.pack(side="left", padx=4)

        customtkinter.CTkButton(
            color_row, text="Chọn màu", width=100,
            command=self._pick_color,
        ).pack(side="left", padx=8)

        customtkinter.CTkButton(
            color_row, text="Khôi phục", width=70, fg_color="gray",
            command=self._reset_color,
        ).pack(side="left", padx=2)

        customtkinter.CTkButton(
            scroll, text="💾 Lưu cài đặt giao diện",
            command=self._save_background,
        ).pack(padx=12, pady=16)



    def _pick_color(self) -> None:
        """Mở color picker để chọn màu theme."""
        color = colorchooser.askcolor(
            initialcolor=self._config.background.button_color,
            title="Chọn màu chủ đạo",
        )
        if color[1]:  # color = ((r,g,b), '#hex')
            hex_color = color[1]
            self._config.background.button_color = hex_color
            self._color_preview.configure(fg_color=hex_color)
            self._color_label.configure(text=hex_color)
            self._status(f"🎨 Đã chọn màu: {hex_color}")

    def _reset_color(self) -> None:
        """Reset về màu mặc định."""
        default = "#1f6aa5"
        self._config.background.button_color = default
        self._color_preview.configure(fg_color=default)
        self._color_label.configure(text=default)
        self._status("🎨 Đã khôi phục màu mặc định.")

    def _save_background(self) -> None:
        """Lưu background settings."""
        self._config.save()
        self._on_background_save()
        self._status("✅ Đã lưu cài đặt giao diện!")
