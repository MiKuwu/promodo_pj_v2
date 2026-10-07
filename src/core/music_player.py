"""
Background music player using pygame.mixer.

👤 Người 2 – Core
Phụ trách: Phát nhạc nền, quản lý playlist, điều chỉnh âm lượng,
           phát âm thanh thông báo (chuông cảnh báo).
"""

import random
from pathlib import Path
from typing import List, Optional, Callable

try:
    import pygame
    pygame.mixer.init()
    _PYGAME_OK = True
except Exception:
    _PYGAME_OK = False

from src.core.utils import get_resource_path

SUPPORTED_FORMATS = {".mp3", ".wav", ".ogg"}
DEFAULT_BELL_SOUND = str(get_resource_path("assets/sounds/bell.wav"))


class MusicPlayer:
    """Phát nhạc nền và âm thanh thông báo bằng pygame.mixer.

    Hỗ trợ 3 chế độ phát:
      - repeat_one: Lặp lại 1 bài.
      - repeat_all: Lặp cả playlist theo thứ tự.
      - shuffle: Phát ngẫu nhiên, không theo thứ tự.

    Example:
        player = MusicPlayer()
        player.add_to_playlist("path/to/song.mp3")
        player.set_playback_mode("shuffle")
        player.play()
    """

    MUSIC_END_EVENT = pygame.USEREVENT + 1 if _PYGAME_OK else None

    def __init__(self) -> None:
        self._current_file: Optional[Path] = None
        self._playlist: List[Path] = []
        self._playlist_index: int = 0
        self._volume: float = 0.5
        self._is_playing: bool = False
        self._playback_mode: str = "repeat_all"
        self._on_track_change: Optional[Callable] = None
        self._notification_sound_path: str = DEFAULT_BELL_SOUND

        if _PYGAME_OK:
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.set_endevent(self.MUSIC_END_EVENT)

    # ------------------------------------------------------------------
    # Playback mode
    # ------------------------------------------------------------------

    def set_playback_mode(self, mode: str) -> None:
        """Đổi chế độ phát nhạc.

        Args:
            mode: "repeat_one", "repeat_all", hoặc "shuffle".
        """
        if mode in ("repeat_one", "repeat_all", "shuffle"):
            self._playback_mode = mode

    @property
    def playback_mode(self) -> str:
        """Chế độ phát nhạc hiện tại."""
        return self._playback_mode

    # ------------------------------------------------------------------
    # Notification sound
    # ------------------------------------------------------------------

    def set_notification_sound(self, filepath: str) -> None:
        """Đặt file âm thanh thông báo hết phiên.

        Args:
            filepath: Đường dẫn tới file .wav/.ogg.
        """
        self._notification_sound_path = filepath

    @property
    def notification_sound(self) -> str:
        """Đường dẫn file âm thanh thông báo hiện tại."""
        return self._notification_sound_path

    # ------------------------------------------------------------------
    # Track change callback
    # ------------------------------------------------------------------

    def on_track_change(self, callback: Callable) -> None:
        """Đăng ký callback gọi khi bài hát thay đổi."""
        self._on_track_change = callback

    def _notify_track_change(self) -> None:
        """Gọi callback khi track thay đổi."""
        if self._on_track_change:
            self._on_track_change()

    # ------------------------------------------------------------------
    # Điều khiển phát nhạc nền
    # ------------------------------------------------------------------

    def load(self, filepath: str) -> bool:
        """Tải một file âm thanh vào bộ phát nhạc nền."""
        if not _PYGAME_OK:
            return False
        path = Path(filepath)
        if not path.exists():
            return False
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            return False
        try:
            pygame.mixer.music.load(str(path))
            self._current_file = path
            self._is_playing = False
            self._is_stopped = True
            self._pos_offset = 0.0
            
            # Load into Sound just to get the length in seconds
            sound = pygame.mixer.Sound(str(path))
            self._current_length = sound.get_length()
            return True
        except Exception:
            return False

    def play(self, loop: bool = False, start_pos: float = 0.0) -> None:
        """Phát nhạc nền."""
        if not _PYGAME_OK:
            return
            
        if self._current_file is None:
            if self._playlist:
                if not self.load(str(self._playlist[self._playlist_index])):
                    return
            else:
                return

        try:
            loops = -1 if self._playback_mode == "repeat_one" else 0
            pygame.mixer.music.play(loops, start_pos)
            self._pos_offset = start_pos
            self._is_playing = True
            self._is_stopped = False
        except Exception:
            self._is_playing = False

    def seek(self, seconds: float) -> None:
        """Tua bài hát tới thời điểm cụ thể (seconds)."""
        if not _PYGAME_OK or self._current_file is None:
            return
        if not hasattr(self, "_current_length"):
            return
        seconds = max(0.0, min(self._current_length, seconds))
        # Seek by re-playing from the given position
        self.play(start_pos=seconds)

    def get_length(self) -> float:
        """Trả về tổng độ dài bài hát bằng giây."""
        return getattr(self, "_current_length", 0.0)

    def get_position(self) -> float:
        """Trả về vị trí phát nhạc hiện tại bằng giây."""
        if not _PYGAME_OK or self._current_file is None:
            return 0.0
            
        if getattr(self, "_is_stopped", True):
            return 0.0
        
        # get_pos() returns ms since last play()
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0:
            return 0.0
            
        current = self._pos_offset + (pos_ms / 1000.0)
        length = self.get_length()
        
        if self._playback_mode == "repeat_one" and length > 0:
            return current % length
            
        return min(current, length)

    def pause(self) -> None:
        """Tạm dừng nhạc nền."""
        if not _PYGAME_OK:
            return
        pygame.mixer.music.pause()
        self._is_playing = False

    def resume(self) -> None:
        """Tiếp tục phát nhạc sau khi pause."""
        if not _PYGAME_OK:
            return
        pygame.mixer.music.unpause()
        self._is_playing = True

    def stop(self) -> None:
        """Dừng hẳn nhạc nền."""
        if not _PYGAME_OK:
            return
        pygame.mixer.music.stop()
        self._is_playing = False
        self._is_stopped = True

    def set_volume(self, volume: float) -> None:
        """Điều chỉnh âm lượng nhạc nền (0.0 - 1.0)."""
        self._volume = max(0.0, min(1.0, volume))
        if _PYGAME_OK:
            pygame.mixer.music.set_volume(self._volume)

    # ------------------------------------------------------------------
    # Auto-advance (gọi từ UI event loop)
    # ------------------------------------------------------------------

    def check_music_end(self) -> None:
        """Kiểm tra nếu bài hát đã kết thúc, tự chuyển bài tiếp theo.

        Gọi phương thức này từ UI event loop (after() hoặc poll).
        """
        if not _PYGAME_OK or not self._is_playing:
            return
        if pygame.mixer.music.get_busy():
            return
        # Bài đã kết thúc
        if self._playback_mode == "repeat_one":
            return  # pygame loop -1 tự lặp
        elif self._playback_mode == "repeat_all":
            self._auto_next()
        elif self._playback_mode == "shuffle":
            self._auto_shuffle()

    def _auto_next(self) -> None:
        """Chuyển bài tiếp theo trong playlist (repeat_all mode)."""
        if not self._playlist:
            self._is_playing = False
            return
        self._playlist_index = (self._playlist_index + 1) % len(self._playlist)
        self.load(str(self._playlist[self._playlist_index]))
        self.play()
        self._notify_track_change()

    def _auto_shuffle(self) -> None:
        """Chọn bài ngẫu nhiên (shuffle mode)."""
        if not self._playlist:
            self._is_playing = False
            return
        if len(self._playlist) > 1:
            choices = [i for i in range(len(self._playlist)) if i != self._playlist_index]
            self._playlist_index = random.choice(choices)
        self.load(str(self._playlist[self._playlist_index]))
        self.play()
        self._notify_track_change()

    # ------------------------------------------------------------------
    # Quản lý playlist
    # ------------------------------------------------------------------

    def load_playlist(self, folder: str) -> None:
        """Tải toàn bộ file nhạc trong một thư mục làm playlist."""
        folder_path = Path(folder)
        if not folder_path.is_dir():
            return
        self._playlist = sorted(
            p for p in folder_path.iterdir()
            if p.suffix.lower() in SUPPORTED_FORMATS
        )
        self._playlist_index = 0
        if self._playlist:
            self.load(str(self._playlist[0]))

    def set_playlist_from_files(self, filepaths: List[str]) -> None:
        """Đặt playlist từ danh sách đường dẫn file.

        Args:
            filepaths: Danh sách đường dẫn tuyệt đối tới file nhạc.
        """
        self._playlist = [Path(f) for f in filepaths if Path(f).exists()]
        self._playlist_index = 0
        if self._playlist:
            self.load(str(self._playlist[0]))

    def add_to_playlist(self, filepath: str) -> bool:
        """Thêm một file vào playlist.

        Args:
            filepath: Đường dẫn file nhạc.

        Returns:
            True nếu thêm thành công.
        """
        path = Path(filepath)
        if not path.exists() or path.suffix.lower() not in SUPPORTED_FORMATS:
            return False
        self._playlist.append(path)
        if len(self._playlist) == 1:
            self.load(str(path))
        return True

    def remove_from_playlist(self, index: int) -> bool:
        """Xóa bài tại vị trí index khỏi playlist.

        Args:
            index: Vị trí bài cần xóa.

        Returns:
            True nếu xóa thành công.
        """
        if index < 0 or index >= len(self._playlist):
            return False
        was_current = index == self._playlist_index
        self._playlist.pop(index)
        if was_current:
            self.stop()
            if self._playlist:
                self._playlist_index = min(
                    self._playlist_index, len(self._playlist) - 1
                )
                self.load(str(self._playlist[self._playlist_index]))
            else:
                self._playlist_index = 0
                self._current_file = None
        elif index < self._playlist_index:
            self._playlist_index -= 1
        return True

    def next_track(self) -> None:
        """Chuyển sang bài tiếp theo trong playlist."""
        if not self._playlist:
            return
        if self._playback_mode == "shuffle":
            self._auto_shuffle()
            return
        self._playlist_index = (self._playlist_index + 1) % len(self._playlist)
        was_playing = self._is_playing
        self.load(str(self._playlist[self._playlist_index]))
        if was_playing:
            self.play()
        self._notify_track_change()

    def previous_track(self) -> None:
        """Quay lại bài trước trong playlist."""
        if not self._playlist:
            return
        self._playlist_index = (self._playlist_index - 1) % len(self._playlist)
        was_playing = self._is_playing
        self.load(str(self._playlist[self._playlist_index]))
        if was_playing:
            self.play()
        self._notify_track_change()

    # ------------------------------------------------------------------
    # Âm thanh thông báo
    # ------------------------------------------------------------------

    def play_sound(self, filepath: str = "") -> tuple[bool, int]:
        """Phát một âm thanh ngắn (chuông thông báo).

        Args:
            filepath: Đường dẫn file. Nếu rỗng, dùng notification sound đã set.
        Returns:
            (success, duration_ms)
        """
        if not _PYGAME_OK:
            return False, 5000
        sound_file = filepath or self._notification_sound_path
        path = Path(sound_file)
        if not path.exists():
            return False, 5000
        try:
            # Lư reference của Sound để không bị Python gom rác (garbage collection)
            # Ngăn lỗi âm thanh bị ngắt ngay lập tức khi ra khỏi hàm.
            self._current_notification_sound = pygame.mixer.Sound(str(path))
            self._current_notification_sound.play()
            duration_ms = int(self._current_notification_sound.get_length() * 1000)
            return True, duration_ms
        except Exception:
            return False, 5000

    def play_notification_sound(self) -> tuple[bool, int]:
        """Phát âm thanh thông báo đã được cấu hình."""
        return self.play_sound(self._notification_sound_path)
        
    def stop_notification_sound(self) -> None:
        """Dừng âm thanh thông báo đang phát."""
        if hasattr(self, "_current_notification_sound") and self._current_notification_sound:
            try:
                self._current_notification_sound.stop()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_playing(self) -> bool:
        """True nếu nhạc nền đang phát."""
        return self._is_playing

    @property
    def volume(self) -> float:
        """Âm lượng hiện tại (0.0 – 1.0)."""
        return self._volume

    @property
    def current_track(self) -> Optional[str]:
        """Tên file bài nhạc đang được tải, hoặc None."""
        return self._current_file.name if self._current_file else None

    @property
    def playlist(self) -> List[str]:
        """Danh sách tên file trong playlist hiện tại."""
        return [p.name for p in self._playlist]

    @property
    def playlist_paths(self) -> List[str]:
        """Danh sách đường dẫn đầy đủ trong playlist hiện tại."""
        return [str(p) for p in self._playlist]

    @property
    def playlist_index(self) -> int:
        """Vị trí bài đang chọn trong playlist."""
        return self._playlist_index
