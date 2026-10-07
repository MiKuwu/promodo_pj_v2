"""Tests for src/core/history.py — Người 3 phụ trách implement."""

import pytest
from pathlib import Path
from src.core.history import History, SessionEntry


@pytest.fixture
def history(tmp_path):
    """Fresh History instance backed by a temp file."""
    return History(path=tmp_path / "history.json")


def test_empty_on_start(history):
    """History returns empty list when no sessions saved yet."""
    result = history.get_all()
    assert result == []


def test_add_and_retrieve_session(history):
    """A saved session can be retrieved via get_all()."""
    entry = SessionEntry(
        date="09/09/2026",
        start_time="20:00",
        end_time="20:25",
        phase="Work",
        status="Completed",
    )
    history.add_session(entry)
    all_entries = history.get_all()
    assert len(all_entries) == 1
    assert all_entries[0].phase == "Work"
    assert all_entries[0].status == "Completed"


def test_get_by_date(history):
    """get_by_date() returns only sessions for the specified date."""
    history.add_session(SessionEntry("09/09/2026", "20:00", "20:25", "Work", "Completed"))
    history.add_session(SessionEntry("10/09/2026", "09:00", "09:25", "Work", "Completed"))
    result = history.get_by_date("09/09/2026")
    assert len(result) == 1
    assert result[0].date == "09/09/2026"


def test_persists_across_instances(tmp_path):
    """Sessions saved by one History instance are loaded by a new one."""
    path = tmp_path / "history.json"
    h1 = History(path=path)
    h1.add_session(SessionEntry("09/09/2026", "20:00", "20:25", "Work", "Completed"))

    h2 = History(path=path)
    assert len(h2.get_all()) == 1


def test_clear(history):
    """clear() removes all sessions."""
    history.add_session(SessionEntry("09/09/2026", "20:00", "20:25", "Work", "Completed"))
    history.clear()
    assert history.get_all() == []
