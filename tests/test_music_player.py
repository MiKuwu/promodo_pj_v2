"""Tests for core/music_player.py – Người 2 phụ trách implement.

Lưu ý: Các test này không cần thiết bị âm thanh thực.
Kiểm tra logic (volume clamp, file validation, playlist) chứ không phải audio output.
"""

import pytest
from pathlib import Path
from src.core.music_player import MusicPlayer, SUPPORTED_FORMATS


def test_music_player_initializes():
    """MusicPlayer khởi tạo thành công, không cần thiết bị âm thanh."""
    player = MusicPlayer()
    assert player is not None


def test_default_volume():
    """Volume mặc định phải là 0.5."""
    player = MusicPlayer()
    assert player.volume == 0.5


def test_set_volume_clamps_max():
    """Volume không được vượt quá 1.0."""
    player = MusicPlayer()
    player.set_volume(2.0)
    assert player.volume == 1.0


def test_set_volume_clamps_min():
    """Volume không được nhỏ hơn 0.0."""
    player = MusicPlayer()
    player.set_volume(-0.5)
    assert player.volume == 0.0


def test_set_volume_normal():
    """set_volume() lưu đúng giá trị trong phạm vi hợp lệ."""
    player = MusicPlayer()
    player.set_volume(0.75)
    assert player.volume == 0.75


def test_load_nonexistent_file_returns_false():
    """load() trả về False nếu file không tồn tại."""
    player = MusicPlayer()
    result = player.load("không_tồn_tại.mp3")
    assert result is False


def test_load_unsupported_format_returns_false(tmp_path: Path):
    """load() trả về False nếu định dạng không hỗ trợ."""
    fake = tmp_path / "track.avi"
    fake.write_bytes(b"fake")
    player = MusicPlayer()
    result = player.load(str(fake))
    assert result is False


def test_initial_state_not_playing():
    """Mới khởi tạo, is_playing phải là False."""
    player = MusicPlayer()
    assert player.is_playing is False


def test_current_track_none_when_nothing_loaded():
    """current_track phải là None khi chưa tải file."""
    player = MusicPlayer()
    assert player.current_track is None


def test_playlist_empty_initially():
    """Playlist phải rỗng khi mới tạo."""
    player = MusicPlayer()
    assert player.playlist == []


def test_load_playlist_empty_folder(tmp_path: Path):
    """load_playlist() với thư mục rỗng không gây lỗi."""
    player = MusicPlayer()
    player.load_playlist(str(tmp_path))
    assert player.playlist == []


def test_load_playlist_nonexistent_folder():
    """load_playlist() với thư mục không tồn tại không gây lỗi."""
    player = MusicPlayer()
    player.load_playlist("thư_mục_không_tồn_tại")
    assert player.playlist == []


def test_load_playlist_filters_supported_formats(tmp_path: Path):
    """load_playlist() chỉ lấy file có định dạng hỗ trợ."""
    # Tạo các file giả với đúng extension
    (tmp_path / "song.mp3").write_bytes(b"fake mp3")
    (tmp_path / "song.wav").write_bytes(b"fake wav")
    (tmp_path / "image.jpg").write_bytes(b"fake jpg")  # không hỗ trợ
    (tmp_path / "video.mp4").write_bytes(b"fake mp4")  # không hỗ trợ

    player = MusicPlayer()
    player.load_playlist(str(tmp_path))

    # Chỉ nhận .mp3 và .wav
    assert len(player.playlist) == 2
    assert all(
        Path(name).suffix.lower() in SUPPORTED_FORMATS
        for name in player.playlist
    )


def test_next_track_wraps_around(tmp_path: Path):
    """next_track() quay về bài đầu khi đang ở bài cuối."""
    for name in ["a.mp3", "b.mp3", "c.mp3"]:
        (tmp_path / name).write_bytes(b"fake")

    player = MusicPlayer()
    player.load_playlist(str(tmp_path))

    # Chuyển qua tất cả các bài
    for _ in range(len(player.playlist)):
        player.next_track()

    # Phải quay lại index 0
    assert player.playlist_index == 0


def test_previous_track_wraps_around(tmp_path: Path):
    """previous_track() từ bài đầu phải nhảy về bài cuối."""
    for name in ["a.mp3", "b.mp3", "c.mp3"]:
        (tmp_path / name).write_bytes(b"fake")

    player = MusicPlayer()
    player.load_playlist(str(tmp_path))

    # Đang ở index 0 → previous → phải ở index cuối
    player.previous_track()
    assert player.playlist_index == len(player.playlist) - 1


def test_play_sound_nonexistent_file_no_crash():
    """play_sound() với file không tồn tại không được gây lỗi."""
    player = MusicPlayer()
    player.play_sound("không_tồn_tại.wav")  # không raise Exception
