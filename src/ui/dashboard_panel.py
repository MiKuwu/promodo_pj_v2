"""
Dashboard panel — giao diện biểu đồ thống kê và lịch sử phiên học (Nửa trái màn hình).

👤 Người 3 – Settings + Music UI + History
"""

import customtkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.core.history import History, SessionEntry

class DashboardPanel(customtkinter.CTkFrame):
    """Bảng điều khiển hiển thị biểu đồ và lịch sử học tập.

    Args:
        master: Widget cha.
        history: Session history manager.
    """

    def __init__(self, master, history: "History", **kwargs) -> None:
        kwargs["fg_color"] = kwargs.get("fg_color", "#1e1e1e")
        kwargs["corner_radius"] = kwargs.get("corner_radius", 15)
        super().__init__(master, **kwargs)
        self._history = history
        self._days_var = customtkinter.StringVar(value="7 ngày")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Chart gets more space
        self.grid_rowconfigure(4, weight=1)  # History list gets some space
        
        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        """Tạo giao diện gồm combobox, chart và list lịch sử."""
        # --- Top bar with Combobox ---
        top_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        
        customtkinter.CTkLabel(
            top_frame, text="Thống kê học tập", font=customtkinter.CTkFont(size=18, weight="bold")
        ).pack(side="left")
        
        self._combo = customtkinter.CTkComboBox(
            top_frame, 
            values=["7 ngày", "14 ngày", "30 ngày"],
            variable=self._days_var,
            command=self._on_timeframe_changed,
            width=100
        )
        self._combo.pack(side="right")
        
        # --- Progress Frame ---
        self._progress_frame = customtkinter.CTkFrame(self, fg_color=("gray85", "gray16"), corner_radius=10)
        self._progress_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        
        customtkinter.CTkLabel(
            self._progress_frame, text="TIẾN TRÌNH CỦA BẠN", 
            font=customtkinter.CTkFont(size=13, weight="bold"), text_color="gray"
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(12, 8))
        
        self._progress_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Cột 0: TỔNG THỜI GIAN
        col0 = customtkinter.CTkFrame(self._progress_frame, fg_color="transparent")
        col0.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        customtkinter.CTkLabel(col0, text="TỔNG THỜI GIAN", font=customtkinter.CTkFont(size=11), text_color="gray").pack(anchor="w")
        self._lbl_total_time = customtkinter.CTkLabel(col0, text="0p", font=customtkinter.CTkFont(size=22, weight="bold"))
        self._lbl_total_time.pack(anchor="w")
        
        # Cột 1: SỐ PHIÊN
        col1 = customtkinter.CTkFrame(self._progress_frame, fg_color="transparent")
        col1.grid(row=1, column=1, sticky="nsew", padx=16, pady=(0, 16))
        customtkinter.CTkLabel(col1, text="SỐ PHIÊN", font=customtkinter.CTkFont(size=11), text_color="gray").pack(anchor="w")
        self._lbl_total_sessions = customtkinter.CTkLabel(col1, text="0", font=customtkinter.CTkFont(size=22, weight="bold"))
        self._lbl_total_sessions.pack(anchor="w")
        
        # Cột 2: CHUỖI NGÀY
        col2 = customtkinter.CTkFrame(self._progress_frame, fg_color="transparent")
        col2.grid(row=1, column=2, sticky="nsew", padx=16, pady=(0, 16))
        customtkinter.CTkLabel(col2, text="CHUỖI NGÀY", font=customtkinter.CTkFont(size=11), text_color="gray").pack(anchor="w")
        self._lbl_streak = customtkinter.CTkLabel(col2, text="0 ngày", font=customtkinter.CTkFont(size=22, weight="bold"))
        self._lbl_streak.pack(anchor="w")

        # --- Chart Container ---
        self._chart_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self._chart_container.grid(row=2, column=0, sticky="nsew", padx=12, pady=4)
        
        # --- History List Label ---
        customtkinter.CTkLabel(
            self, text="Các phiên gần đây (10 phiên cuối)", font=customtkinter.CTkFont(size=16, weight="bold"), anchor="w"
        ).grid(row=3, column=0, sticky="ew", padx=12, pady=(12, 4))
        
        # --- History Scrollable Frame ---
        self._history_frame = customtkinter.CTkScrollableFrame(self, fg_color="transparent")
        self._history_frame.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 12))
        
        # Initialize Matplotlib Figure
        self._figure = Figure(figsize=(5, 3), dpi=100)
        self._figure.patch.set_facecolor('#2b2b2b') # match customtkinter dark theme
        self._ax = self._figure.add_subplot(111)
        self._ax.set_facecolor('#2b2b2b')
        self._ax.tick_params(colors='white')
        self._ax.spines['bottom'].set_color('white')
        self._ax.spines['left'].set_color('white')
        self._ax.spines['top'].set_visible(False)
        self._ax.spines['right'].set_visible(False)
        
        self._mpl_canvas = FigureCanvasTkAgg(self._figure, master=self._chart_container)
        self._mpl_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _on_timeframe_changed(self, choice: str) -> None:
        """Callback khi người dùng đổi mốc thời gian."""
        self.refresh_data()

    def refresh_data(self) -> None:
        """Cập nhật lại dữ liệu biểu đồ, danh sách và tiến trình."""
        if not self._history:
            return
            
        entries = self._history.get_all()
        
        # 1. Update Progress Stats
        self._update_progress(entries)
        
        # 2. Update Chart
        days = int(self._days_var.get().split()[0])
        self._update_chart(entries, days)
        
        # 3. Update History List
        self._update_history_list(entries)

    def _update_progress(self, entries: List["SessionEntry"]) -> None:
        total_sessions = 0
        total_minutes = 0
        active_dates = set()
        
        for entry in entries:
            if entry.phase == "Work" and entry.status == "Completed":
                total_sessions += 1
                active_dates.add(entry.date)
                
                # Tính thời lượng
                try:
                    fmt = "%H:%M"
                    start = datetime.strptime(entry.start_time, fmt)
                    end = datetime.strptime(entry.end_time, fmt)
                    diff = end - start
                    if diff.total_seconds() < 0:
                        diff += timedelta(days=1)
                    
                    mins = int(diff.total_seconds() / 60)
                    if mins > 0:
                        total_minutes += mins
                except Exception:
                    pass

        # Tính chuỗi ngày (Streak)
        streak = 0
        if active_dates:
            today = datetime.now().date()
            today_str = today.strftime("%d/%m/%Y")
            yesterday_str = (today - timedelta(days=1)).strftime("%d/%m/%Y")
            
            check_date = today
            if today_str not in active_dates and yesterday_str in active_dates:
                check_date = today - timedelta(days=1)
                
            while check_date.strftime("%d/%m/%Y") in active_dates:
                streak += 1
                check_date -= timedelta(days=1)
                
        # Định dạng thời gian
        if total_minutes < 60:
            time_str = f"{total_minutes}p"
        else:
            h = total_minutes // 60
            m = total_minutes % 60
            time_str = f"{h}g {m}p" if m > 0 else f"{h}g"
            
        self._lbl_total_time.configure(text=time_str)
        self._lbl_total_sessions.configure(text=str(total_sessions))
        self._lbl_streak.configure(text=f"{streak} ngày")

    def _update_chart(self, entries: List["SessionEntry"], days: int) -> None:
        self._ax.clear()
        
        # Setup aesthetic again after clear
        self._ax.tick_params(colors='white')
        self._ax.spines['bottom'].set_color('white')
        self._ax.spines['left'].set_color('white')
        self._ax.spines['top'].set_visible(False)
        self._ax.spines['right'].set_visible(False)

        # Generate last N days
        today = datetime.now().date()
        date_list = [today - timedelta(days=x) for x in range(days-1, -1, -1)]
        date_strs = [d.strftime("%d/%m/%Y") for d in date_list]
        
        # Aggregate data: count completed work sessions per day
        # You could also sum minutes if durations were tracked, but count is simpler based on SessionEntry
        counts = {d: 0 for d in date_strs}
        for entry in entries:
            if entry.phase == "Work" and entry.status == "Completed":
                if entry.date in counts:
                    counts[entry.date] += 1
                    
        x_labels = [d.strftime("%d/%m") for d in date_list]
        y_values = [counts[d] for d in date_strs]
        
        # Plot
        bars = self._ax.bar(x_labels, y_values, color="#1f6aa5")
        
        # Căn chỉnh lại trục Y (Fix lỗi số thập phân và đường 0 nằm lơ lửng giữa biểu đồ)
        max_y = max(y_values) if y_values else 0
        self._ax.set_ylim(0, max(1, max_y + max_y * 0.2)) # Y min luôn là 0, Max dư 20%
        
        from matplotlib.ticker import MaxNLocator
        self._ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        # If too many days, sparse x-ticks
        if days > 14:
            self._ax.set_xticks(range(0, days, 3))
            
        self._ax.set_ylabel("Số phiên", color="white")
        self._figure.tight_layout()
        self._mpl_canvas.draw()

    def _update_history_list(self, entries: List["SessionEntry"]) -> None:
        # Xóa toàn bộ các widget cũ trong scrollable frame một cách triệt để
        for widget in self._history_frame.winfo_children():
            try:
                widget.pack_forget()
                widget.destroy()
            except Exception:
                pass
                
        self._history_rows = []
        

        # Lấy tối đa 10 phiên gần nhất
        recent_entries = list(reversed(entries))[:10]
        
        if not recent_entries:
            customtkinter.CTkLabel(
                self._history_frame, text="Chưa có phiên nào.", text_color="gray"
            ).pack(pady=20)
            return

        for i, entry in enumerate(recent_entries):
            row = customtkinter.CTkFrame(self._history_frame, fg_color=("gray85", "gray20"))
            row.pack(fill="x", pady=2, padx=4)
            self._history_rows.append(row)
            
            # Icon or colored dot based on status/phase
            color = "green" if entry.status == "Completed" else "orange"
            dot = customtkinter.CTkLabel(row, text="●", text_color=color, font=("Arial", 14))
            dot.pack(side="left", padx=8)
            
            phase_vn = {
                "Work": "Làm việc",
                "Short Break": "Nghỉ ngắn",
                "Long Break": "Nghỉ dài"
            }.get(entry.phase, entry.phase)
            
            info_text = f"{entry.date}  |  {entry.start_time} - {entry.end_time}  |  {phase_vn}"
            customtkinter.CTkLabel(row, text=info_text, font=("Arial", 12)).pack(side="left", padx=4, pady=4)
            
            status_text = "Hoàn thành" if entry.status == "Completed" else "Đã hủy"
            status_label = customtkinter.CTkLabel(row, text=status_text, text_color=color, font=("Arial", 12))
            status_label.pack(side="right", padx=8)
