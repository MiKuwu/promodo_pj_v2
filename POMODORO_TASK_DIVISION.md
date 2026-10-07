# Phân chia công việc dự án Pomodoro App

## 1. Phạm vi dự án sau khi tinh giản

Dự án **Pomodoro App bằng Python** tập trung vào các tính năng chính sau:

- Đồng hồ **Work / Short Break / Long Break**
- **Start / Pause / Resume / Reset**
- **Dark / Light mode**
- Cài đặt thời lượng cho từng loại phiên
- Nhạc nền và âm thanh thông báo
- Chọn playlist / file nhạc
- Desktop notification
- Lịch sử học tập

Các tính năng đã được loại bỏ để giảm khối lượng công việc:

- Chặn app gây sao nhãng
- Whitelist / Blacklist
- Dashboard thống kê
- Thống kê số phiên
- Lưu cấu hình người dùng

---

## 2. Bảng phân chia task

| Tính năng | Module | Người phụ trách |
|---|---|---|
| ⏱️ Work / Short Break / Long Break | `src/core/timer.py` | Người 2 |
| ▶️ Start / Pause / Resume / Reset | `src/ui/timer_widget.py` | Người 1 |
| 🎨 Dark / Light mode | `src/ui/theme.py` | Người 1 |
| ⚙️ Cài đặt thời lượng phiên | `src/ui/settings_panel.py` | Người 3 |
| 🔊 Nhạc nền + âm thanh thông báo | `src/core/music_player.py` | Người 2 |
| 🎵 Chọn playlist / file nhạc | `src/ui/music_panel.py` | Người 3 |
| 🔔 Desktop notification | `src/core/notification.py` | Người 2 |
| 📅 Lịch sử học tập | `src/core/history.py` | Người 3 |

---

## 3. Phân chia theo từng thành viên

### Người 1 — GUI chính

Phụ trách phần giao diện chính và các thao tác trực tiếp của người dùng.

#### Module

```text
src/ui/
├── main_window.py
├── timer_widget.py
└── theme.py
```

#### Công việc

- Thiết kế cửa sổ chính
- Hiển thị đồng hồ Pomodoro
- Xây dựng các nút:
  - Start
  - Pause
  - Resume
  - Reset
- Hiển thị trạng thái:
  - Work
  - Short Break
  - Long Break
- Xây dựng Dark / Light mode
- Thiết kế bố cục menu, button, label
- Kết nối giao diện với các module Core

**Khối lượng dự kiến:** khoảng **35%**

---

### Người 2 — Core / Logic

Phụ trách logic chính của ứng dụng.

#### Module

```text
src/core/
├── timer.py
├── music_player.py
└── notification.py
```

#### Công việc

- Xử lý logic đếm ngược
- Chuyển đổi giữa:
  - Work
  - Short Break
  - Long Break
- Xử lý Pause / Resume / Reset ở tầng logic
- Phát nhạc nền
- Phát âm thanh khi phiên kết thúc
- Gửi Desktop Notification khi hết giờ

#### Interface gợi ý cho Timer

```python
class PomodoroTimer:
    def start(self):
        pass

    def pause(self):
        pass

    def resume(self):
        pass

    def reset(self):
        pass

    def set_duration(self, work, short_break, long_break):
        pass
```

Người làm GUI chỉ cần gọi các hàm trên mà không cần biết chi tiết logic bên trong.

**Khối lượng dự kiến:** khoảng **35%**

---

### Người 3 — Settings + Music UI + History

Phụ trách các màn hình phụ và lịch sử sử dụng.

#### Module

```text
src/ui/
├── settings_panel.py
└── music_panel.py

src/core/
└── history.py
```

#### Công việc

- Giao diện chỉnh thời lượng:
  - Work
  - Short Break
  - Long Break
- Kiểm tra dữ liệu nhập
- Giao diện chọn file nhạc
- Playlist đơn giản
- Hiển thị tên bài hát đang phát
- Lưu lịch sử các phiên Pomodoro
- Hiển thị màn hình lịch sử học tập

#### Ví dụ dữ liệu lịch sử

```text
09/09/2026
20:00 - 20:25   Work      Completed
20:30 - 20:55   Work      Completed
21:00 - 21:25   Work      Interrupted
```

Có thể lưu bằng file đơn giản như:

```text
data/history.json
```

hoặc:

```text
data/history.csv
```

Không bắt buộc sử dụng database nếu muốn giữ project nhẹ.

**Khối lượng dự kiến:** khoảng **30%**

---

## 4. Cấu trúc thư mục đề xuất

```text
PomodoroApp/
│
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── src/
│   ├── core/
│   │   ├── timer.py
│   │   ├── music_player.py
│   │   ├── notification.py
│   │   └── history.py
│   │
│   └── ui/
│       ├── main_window.py
│       ├── timer_widget.py
│       ├── theme.py
│       ├── settings_panel.py
│       └── music_panel.py
│
├── data/
│   └── history.json
│
└── assets/
    ├── icons/
    ├── sounds/
    └── music/
```

---

## 5. Cách các module kết nối với nhau

```text
                    POMODORO APP
                         │
        ┌────────────────┼────────────────┐
        │                │                │
     Người 1          Người 2          Người 3
       GUI              CORE          SETTINGS
        │                │                │
 Main Window          Timer          Settings
 Timer Widget         Music          Music UI
 Theme                Notify         History
        │                │                │
        └────────────────┼────────────────┘
                         │
                      main.py
```

`main.py` không nên là nơi chứa toàn bộ logic. File này chỉ nên dùng để khởi tạo ứng dụng và kết nối các thành phần.

Ví dụ:

```python
from src.ui.main_window import MainWindow

def main():
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()
```

---

## 6. Nguyên tắc làm việc nhóm với Git

Mỗi người nên làm việc trên branch riêng.

Ví dụ:

```text
main
├── feature/gui
├── feature/core
└── feature/settings-history
```

Quy trình cơ bản:

```bash
git checkout main
git pull

git checkout -b feature/ten-tinh-nang

# Code và test

git add .
git commit -m "Add feature description"
git push origin feature/ten-tinh-nang
```

Sau đó tạo **Pull Request** trên GitHub để review trước khi merge vào `main`.

Không nên code trực tiếp trên `main`.

---

## 7. Phân bố khối lượng tổng thể

```text
Người 1: ████████░░  35%
Người 2: ████████░░  35%
Người 3: ███████░░░  30%
```

Cách chia này giúp:

- Mỗi người có module riêng để hạn chế conflict Git.
- Công việc tương đối cân bằng.
- Dễ kiểm thử từng phần độc lập.
- Dễ ghép thành một ứng dụng hoàn chỉnh.
- Project vẫn đủ tính năng để thể hiện kỹ năng lập trình GUI bằng Python mà không bị quá nặng.
