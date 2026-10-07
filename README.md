# 🍅 Pomodoro Timer

Ứng dụng **Pomodoro Timer** desktop, xây dựng bằng **Python + CustomTkinter**.
Phát triển bởi team 3 người, mỗi người phụ trách một module độc lập.

---

## Tính năng

| Tính năng | File | Người phụ trách |
|---|---|---|
| ⏱️ Đồng hồ Work / Short Break / Long Break | `src/core/timer.py` | Người 2 |
| ▶️ Start / Pause / Resume / Reset | `src/ui/timer_widget.py` | Người 1 |
| 🎨 Dark / Light mode | `src/ui/theme.py` | Người 1 |
| ⚙️ Cài đặt thời lượng phiên | `src/ui/settings_panel.py` | Người 3 |
| 🔊 Nhạc nền + âm thanh thông báo | `src/core/music_player.py` | Người 2 |
| 🎵 Chọn playlist / file nhạc | `src/ui/music_panel.py` | Người 3 |
| 🔔 Desktop notification | `src/core/notification.py` | Người 2 |
| 📅 Lịch sử học tập | `src/core/history.py` | Người 3 |

---

## Tech Stack

| Package | Dùng cho |
|---|---|
| `customtkinter` | GUI framework |
| `pygame` | Nhạc nền |
| `plyer` | Desktop notification |
| `pytest` | Testing |

---

## Cấu trúc dự án

```
promodo_timer_PyPj/
├── main.py                     # Entry point – kết nối các module
├── requirements.txt
├── GEMINI.md                   # AI agent rules
├── POMODORO_TASK_DIVISION.md   # Bảng phân chia task
│
├── data/
│   └── history.json            # Lịch sử phiên (tự sinh, không commit)
│
├── assets/
│   ├── icons/
│   ├── sounds/                 # Âm thanh notification
│   └── music/                  # Nhạc nền
│
├── .agents/                    # Cấu hình AI – commit cùng code
│   ├── hooks.json              # Auto: activate venv + git pull khi mở Antigravity
│   ├── rules/
│   └── skills/
│
├── src/
│   ├── core/                   # 👤 Người 2 (+ history của Người 3)
│   │   ├── timer.py            # Logic Pomodoro
│   │   ├── music_player.py     # Phát nhạc nền
│   │   ├── notification.py     # Desktop notification
│   │   └── history.py          # Lịch sử phiên JSON – Người 3
│   │
│   └── ui/                     # 👤 Người 1 + Người 3
│       ├── main_window.py      # Cửa sổ chính – Người 1
│       ├── timer_widget.py     # Đồng hồ + nút – Người 1
│       ├── theme.py            # Màu sắc + font – Người 1
│       ├── settings_panel.py   # Form cài đặt – Người 3
│       └── music_panel.py      # UI chọn nhạc – Người 3
│
└── tests/
    ├── test_timer.py
    ├── test_history.py
    └── test_music_player.py
```

> **Nguyên tắc kiến trúc:**
> - `src/core/` → KHÔNG import từ `src/ui/`.
> - UI files → KHÔNG chứa business logic, chỉ gọi core qua callbacks.
> - `main.py` → nơi **DUY NHẤT** kết nối các module.

---

## ⚙️ Hướng dẫn cài đặt cho thành viên mới (Windows)

> **Đọc kỹ từng bước. Làm sai thứ tự sẽ báo lỗi.**

---

### Công cụ sử dụng

Tất cả lệnh chạy trong **Windows PowerShell**.

**Cách mở PowerShell:**
- Nhấn `Win + X` → chọn **"Windows PowerShell"** hoặc **"Terminal"**
- Hoặc nhấn `Win + R` → gõ `powershell` → Enter

> ⚠️ Không dùng **Command Prompt (CMD)**. Luôn dùng **PowerShell**.

---

### Bước 1 – Kiểm tra Python đã cài chưa

```powershell
python --version
```

**Kết quả mong đợi:** `Python 3.10.x` (hoặc cao hơn)

**Nếu báo lỗi** → Tải Python tại https://www.python.org/downloads/
(tích vào **"Add Python to PATH"** khi cài).

---

### Bước 2 – Kiểm tra Git đã cài chưa

```powershell
git --version
```

**Kết quả mong đợi:** `git version 2.x.x.windows.x`

**Nếu báo lỗi** → Tải Git tại https://git-scm.com/download/win

---

### Bước 3 – Clone dự án về máy

> **Chạy ở đâu:** PowerShell, tại thư mục bạn muốn lưu code (ví dụ `D:\`).

```powershell
git clone https://github.com/MiKuwu/promodo_timer_PyPj.git
cd promodo_timer_PyPj
```

> Từ đây trở đi, **tất cả lệnh đều chạy trong thư mục `promodo_timer_PyPj`**.
> Mỗi lần mở PowerShell mới phải `cd` vào đây trước.

---

### Bước 4 – Tạo môi trường ảo

> **Chạy ở đâu:** PowerShell, trong thư mục `promodo_timer_PyPj`. Chỉ cần làm **một lần**.

```powershell
python -m venv .venv
```

---

### Bước 5 – Kích hoạt môi trường ảo ✅ Đã tự động

> 🤖 **AI agent tự làm bước này.** Khi mở dự án trong Antigravity,
> file `.agents/hooks.json` tự kích hoạt `.venv` và AI thông báo kết quả.

**Nếu cần chạy thủ công** (terminal riêng, không qua Antigravity):

```powershell
.\.venv\Scripts\Activate.ps1
```

**Kết quả mong đợi:** Dòng nhắc lệnh có `(.venv)` ở đầu:
```
(.venv) PS D:\promodo_timer_PyPj>
```

**Nếu báo lỗi** `cannot be loaded because running scripts is disabled`:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Nhấn `Y` → Enter → chạy lại lệnh Activate.

---

### Bước 6 – Cài đặt thư viện

> **Chạy ở đâu:** PowerShell (đã có `(.venv)`), trong thư mục dự án.

```powershell
pip install -r requirements.txt
```

**Kết quả mong đợi:** Thấy `Successfully installed ...`. Chỉ cần chạy một lần.

---

### Bước 7 – Mở dự án trong Antigravity

**Antigravity 2.0 (Desktop App):**
1. Mở Antigravity 2.0
2. Sidebar trái → **Projects** → **+ Add Project**
3. Chọn thư mục `promodo_timer_PyPj`
4. AI tự đọc `GEMINI.md` và `.agents/` → sẵn sàng hỗ trợ

**Antigravity IDE:**
1. **File → Open Folder** → chọn thư mục `promodo_timer_PyPj`
2. IDE tự phát hiện `.agents/` và load toàn bộ rules + skills

---

### Bước 8 – Chạy test

> **Chạy ở đâu:** PowerShell (đã có `(.venv)`), trong thư mục dự án.

```powershell
pytest tests/ -v
```

---

## 🔄 Hướng dẫn làm việc hàng ngày

---

### Bước 1 – Mở PowerShell và vào thư mục dự án

```powershell
cd D:\promodo_timer_PyPj
```

> Thay bằng đường dẫn thực tế trên máy bạn.

---

### Bước 2 – Kích hoạt môi trường ảo ✅ Đã tự động

> 🤖 AI agent tự làm khi bạn mở Antigravity.

**Thủ công nếu cần:**
```powershell
.\.venv\Scripts\Activate.ps1
```

---

### Bước 3 – Lấy code mới nhất từ GitHub ✅ Đã tự động

> 🤖 AI agent tự chạy `git pull origin main` khi bắt đầu hội thoại mới.

**Thủ công nếu cần:**
```powershell
git pull origin main
```

**Tại sao cần bước này?**
- Đồng đội có thể đã merge code mới vào `main`.
- AI đọc code từ file — sau khi pull mới thấy đúng interface của đồng đội.

---

### Bước 4 – Tạo branch riêng trước khi code

```powershell
git checkout -b feature/tên-tính-năng
```

**Ví dụ:**
```powershell
git checkout -b feature/gui-timer-widget    # Người 1
git checkout -b feature/core-timer          # Người 2
git checkout -b feature/settings-history    # Người 3
```

---

### Bước 5 – Code cùng AI agent

Mở Antigravity, hỏi AI để implement `TODO` trong module của mình.

---

### Bước 6 – Chạy test trước khi push

```powershell
pytest tests/ -v
```

---

### Bước 7 – Commit

```powershell
git status
git add src/core/timer.py tests/test_timer.py
git commit -m "feat: implement PomodoroTimer start/pause/reset"
```

---

### Bước 8 – Push và tạo Pull Request

```powershell
git push origin tên-branch
```

Sau đó vào https://github.com/MiKuwu/promodo_timer_PyPj → nhấn **"Compare & pull request"** → tạo PR → nhờ đồng đội review.

---

## 📋 Checklist trước khi push

- [ ] `pytest tests/ -v` → tất cả PASS
- [ ] Không có `print()` debug thừa
- [ ] Không commit `.venv/`, `__pycache__/`, `data/history.json`
- [ ] Commit message đúng format (`feat:`, `fix:`, v.v.)
- [ ] File mới đặt đúng thư mục của mình

---

## 🚨 Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `'python' is not recognized` | Python chưa cài / chưa thêm PATH | Cài lại Python, tích "Add to PATH" |
| `'git' is not recognized` | Git chưa cài | Cài Git tại git-scm.com |
| `cannot be loaded because running scripts is disabled` | PowerShell chặn script | Chạy `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `ModuleNotFoundError: No module named 'customtkinter'` | Chưa activate venv hoặc chưa install | Activate `.venv` rồi `pip install -r requirements.txt` |
| `(.venv)` không hiện | Chưa activate | Chạy `.\.venv\Scripts\Activate.ps1` |
| `NotImplementedError` khi chạy app | Skeleton chưa implement | Bình thường — implement `TODO` trong module của mình |
| `CONFLICT` khi `git pull` | Xung đột với code đồng đội | Mở file bị conflict, giữ code đúng, xóa markers `<<<`/`===`/`>>>`, rồi commit |

---

## 🤖 Cách dùng AI Agent (Antigravity) hiệu quả

| Bạn nói với AI | AI sẽ làm |
|---|---|
| *"Giúp tôi setup môi trường"* | Hướng dẫn clone, venv, install từng bước |
| *"Implement `PomodoroTimer.start()`"* | Viết code vào đúng `src/core/timer.py` |
| *"Làm giao diện chọn nhạc"* | Biết là Người 3, viết vào `src/ui/music_panel.py` |
| *"Làm lịch sử học tập"* | Biết là Người 3, viết vào `src/core/history.py` + JSON |
| *"Chạy test phần core"* | Chạy `pytest tests/test_timer.py tests/test_music_player.py -v` |
| *"Review code trước khi push"* | Check PEP8, type hints, docstring, test coverage |

> AI không tự sync giữa các máy. **Git là cơ chế sync duy nhất.**
> Luôn `git pull origin main` trước khi làm việc.

---

## 📦 Về Skeleton Code

Tất cả file đã có **skeleton** (khung interface). Toàn bộ method đang `raise NotImplementedError` — app sẽ crash khi chạy. Mỗi người cần implement các `TODO` trong module của mình.

```python
# ❌ Skeleton hiện tại — chạy là crash:
def start(self) -> None:
    raise NotImplementedError

# ✅ Code thật cần viết:
def start(self) -> None:
    self._state = PomodoroState.WORK
    self._remaining_seconds = self._work_minutes * 60
    if self._phase_change_callback:
        self._phase_change_callback(self._state)
```
