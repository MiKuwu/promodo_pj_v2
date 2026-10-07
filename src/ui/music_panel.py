"""
Music panel — giao diện chọn nhạc và điều khiển phát nhạc.

👤 Người 3 – Settings + Music UI + History
Phụ trách: Giao diện chọn file nhạc, playlist đơn giản, hiển thị tên bài đang phát.
"""

import customtkinter
from typing import Callable
from PIL import Image
from src.core.utils import get_resource_path

class MusicPanel(customtkinter.CTkFrame):
    """Panel điều khiển nhạc nền.

    Hiển thị tên bài đang phát, nút play/pause/stop, slider âm lượng,
    và nút chọn file nhạc.
    Nhận callbacks từ MainWindow — KHÔNG import MusicPlayer trực tiếp.
    """

    def __init__(
        self,
        master,
        on_play: Callable,
        on_pause: Callable,
        on_resume: Callable,
        on_stop: Callable,
        on_volume_change: Callable[[float], None],
        on_pick_folder: Callable,
        on_previous: Callable,
        on_next: Callable,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_play = on_play
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_stop = on_stop
        self._on_volume_change = on_volume_change
        self._on_pick_folder = on_pick_folder
        self._on_previous = on_previous
        self._on_next = on_next

        # Load icons
        self._icon_size = (24, 24)
        self._icon_play = customtkinter.CTkImage(Image.open(get_resource_path("assets/icons/play.png")), size=self._icon_size)
        self._icon_pause = customtkinter.CTkImage(Image.open(get_resource_path("assets/icons/pause.png")), size=self._icon_size)
        self._icon_stop = customtkinter.CTkImage(Image.open(get_resource_path("assets/icons/stop.png")), size=self._icon_size)
        self._icon_prev = customtkinter.CTkImage(Image.open(get_resource_path("assets/icons/prev.png")), size=self._icon_size)
        self._icon_next = customtkinter.CTkImage(Image.open(get_resource_path("assets/icons/next.png")), size=self._icon_size)

        self._build_ui()

    def _build_ui(self) -> None:
        """Create track information and music playback controls."""
        
        main_container = customtkinter.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Khung trái: Tiêu đề, tên bài, nút điều khiển, timeline
        left_frame = customtkinter.CTkFrame(main_container, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True)
        
        # Khung phải: Thanh âm lượng dọc
        right_frame = customtkinter.CTkFrame(main_container, fg_color="transparent")
        right_frame.pack(side="right", fill="y", padx=(0, 12))

        customtkinter.CTkLabel(
            left_frame,
            text="Nhạc nền",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(4, 4))

        self._track_label = customtkinter.CTkLabel(
            left_frame,
            text="Chưa có nhạc",
            anchor="w",
            wraplength=350,
        )
        self._track_label.pack(fill="x", padx=12, pady=4)

        controls = customtkinter.CTkFrame(left_frame, fg_color="transparent")
        controls.pack(fill="x", padx=8, pady=4)
        
        # Previous
        customtkinter.CTkButton(
            controls,
            text="",
            image=self._icon_prev,
            command=self._on_previous,
            width=40, height=40,
        ).pack(side="left", expand=True, padx=3)
        
        # Play/Pause
        self._play_button = customtkinter.CTkButton(
            controls,
            text="",
            image=self._icon_play,
            command=self._on_play,
            width=40, height=40,
        )
        self._play_button.pack(side="left", expand=True, padx=3)
        
        # Stop
        customtkinter.CTkButton(
            controls,
            text="",
            image=self._icon_stop,
            command=self._on_stop,
            width=40, height=40,
        ).pack(side="left", expand=True, padx=3)
        
        # Next
        customtkinter.CTkButton(
            controls,
            text="",
            image=self._icon_next,
            command=self._on_next,
            width=40, height=40,
        ).pack(side="left", expand=True, padx=3)

        # Timeline
        timeline_row = customtkinter.CTkFrame(left_frame, fg_color="transparent")
        timeline_row.pack(fill="x", padx=12, pady=(8, 4))
        
        self._timeline_slider = customtkinter.CTkSlider(
            timeline_row, from_=0.0, to=1.0, command=self._on_seek_drag
        )
        self._timeline_slider.bind("<ButtonPress-1>", self._on_seek_press)
        self._timeline_slider.bind("<ButtonRelease-1>", self._on_seek_release)
        self._timeline_slider.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._timeline_slider.set(0)
        
        self._time_label = customtkinter.CTkLabel(timeline_row, text="00:00 / 00:00", width=80)
        self._time_label.pack(side="right")

        # Volume slider (Vertical)
        self._volume_slider = customtkinter.CTkSlider(
            right_frame,
            from_=0.0,
            to=1.0,
            command=self._on_volume_change,
            orientation="vertical",
            height=100
        )
        self._volume_slider.pack(side="top", expand=True, pady=(12, 4))
        
        customtkinter.CTkLabel(
            right_frame, text="🔊", font=("Arial", 16)
        ).pack(side="bottom", pady=(0, 4))

    def update_track_label(self, track_name: str) -> None:
        """Hiển thị tên bài hát đang phát."""
        self._track_label.configure(text=track_name or "Chưa có nhạc")

    def set_volume(self, volume: float) -> None:
        """Set the displayed volume slider."""
        self._volume_slider.set(volume)

    def _on_seek_press(self, event) -> None:
        self._is_dragging_timeline = True
        
    def _on_seek_drag(self, value: float) -> None:
        """Called when user drags the timeline slider (visual only)."""
        self._is_dragging_timeline = True
        total_sec = self._timeline_slider.cget("to")
        if total_sec > 0:
            curr_str = f"{int(value // 60):02d}:{int(value % 60):02d}"
            tot_str = f"{int(total_sec // 60):02d}:{int(total_sec % 60):02d}"
            self._time_label.configure(text=f"{curr_str} / {tot_str}")

    def _on_seek_release(self, event) -> None:
        """Called when user releases the timeline slider."""
        self._is_dragging_timeline = False
        if hasattr(self, "_on_seek_callback") and self._on_seek_callback:
            self._on_seek_callback(self._timeline_slider.get())

    def set_seek_callback(self, callback: Callable[[float], None]) -> None:
        """Gán callback khi người dùng kéo timeline."""
        self._on_seek_callback = callback

    def update_timeline(self, current_sec: float, total_sec: float) -> None:
        """Cập nhật vị trí slider và text hiển thị thời gian."""
        if getattr(self, "_is_dragging_timeline", False):
            return
        
        if total_sec > 0:
            self._timeline_slider.configure(to=total_sec)
            self._timeline_slider.set(current_sec)
            
            curr_str = f"{int(current_sec // 60):02d}:{int(current_sec % 60):02d}"
            tot_str = f"{int(total_sec // 60):02d}:{int(total_sec % 60):02d}"
            self._time_label.configure(text=f"{curr_str} / {tot_str}")
        else:
            self._timeline_slider.set(0)
            self._time_label.configure(text="00:00 / 00:00")

    def set_playing_state(self, is_playing: bool) -> None:
        """Chuyển icon nút Play/Pause theo trạng thái."""
        if is_playing:
            self._play_button.configure(image=self._icon_pause, command=self._on_pause)
        else:
            self._play_button.configure(image=self._icon_play, command=self._on_play)

    def set_paused_state(self, is_paused: bool) -> None:
        """Show Resume icon while the current track is paused."""
        if is_paused:
            self._play_button.configure(image=self._icon_play, command=self._on_resume)
