"""
Dark / Light mode color constants.

👤 Người 1 – GUI
Phụ trách: Định nghĩa toàn bộ màu sắc theo theme.
Tất cả widget phải lấy màu từ đây — không hardcode hex trong widget.
"""

# ── Phase colors ─────────────────────────────────────────────────────
WORK_COLOR = "#E74C3C"           # Red – focus / work session
SHORT_BREAK_COLOR = "#2ECC71"    # Green – short break
LONG_BREAK_COLOR = "#3498DB"     # Blue – long break

# ── Button colors ────────────────────────────────────────────────────
BTN_START_COLOR = "#27AE60"
BTN_PAUSE_COLOR = "#F39C12"
BTN_RESET_COLOR = "#95A5A6"
BTN_SKIP_COLOR = "#8E44AD"

# ── Background colors (Light / Dark) ────────────────────────────────
BG_LIGHT = "#F5F5F5"
BG_DARK = "#1E1E2E"

# ── Text colors ──────────────────────────────────────────────────────
TEXT_PRIMARY_LIGHT = "#2C3E50"
TEXT_PRIMARY_DARK = "#CDD6F4"
TEXT_SECONDARY = "#7F8C8D"

# ── Timer ring ───────────────────────────────────────────────────────
RING_BG_LIGHT = "#ECF0F1"
RING_BG_DARK = "#313244"
RING_WIDTH = 12                  # pixels

# ── Typography ───────────────────────────────────────────────────────
FONT_TIMER = ("Segoe UI", 64, "bold")
FONT_PHASE = ("Segoe UI", 16)
FONT_LABEL = ("Segoe UI", 13)
FONT_BUTTON = ("Segoe UI", 13, "bold")

# ── Spacing ──────────────────────────────────────────────────────────
PAD_SM = 8
PAD_MD = 16
PAD_LG = 24
