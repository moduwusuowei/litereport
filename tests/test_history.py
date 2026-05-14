"""Tests for history manager."""

import json
from pathlib import Path
import pytest
from litereport.history import HistoryManager
from litereport.models import TestResult, ReportData


def _make_data(ts="2026-05-13 10:00:00"):
    return ReportData(
        title="Test",
        timestamp=ts,
        duration=10.0,
        results=[
            TestResult(name="t1", outcome="passed"),
            TestResult(name="t2", outcome="failed"),
        ],
    )


class TestHistoryManager:
    def test_load_index_empty(self, tmp_path):
        hm = HistoryManager(str(tmp_path))
        assert hm.load_index() == []

    def test_save_creates_index(self, tmp_path):
        hm = HistoryManager(str(tmp_path))
        data = _make_data()
        hm.save(data, data.to_json())
        index = hm.load_index()
        assert len(index) == 1
        assert index[0]["total"] == 2
        assert index[0]["passed"] == 1
        assert index[0]["failed"] == 1

    def test_save_creates_json_file(self, tmp_path):
        hm = HistoryManager(str(tmp_path))
        data = _make_data()
        html_name = hm.save(data, data.to_json())
        # Check JSON file exists in history dir
        json_files = list((tmp_path / "history").glob("*.json"))
        assert any(f.name == "index.json" for f in json_files)
        assert any(f.name.startswith("report_") for f in json_files)

    def test_save_max_entries(self, tmp_path):
        hm = HistoryManager(str(tmp_path), max_entries=3)
        for i in range(5):
            data = _make_data(f"2026-05-{10+i} 10:00:00")
            hm.save(data, data.to_json())
        index = hm.load_index()
        assert len(index) == 3

    def test_clean(self, tmp_path):
        hm = HistoryManager(str(tmp_path), max_entries=10)
        for i in range(5):
            data = _make_data(f"2026-05-{10+i} 10:00:00")
            hm.save(data, data.to_json())
        removed = hm.clean(keep=2)
        assert removed == 3
        assert len(hm.load_index()) == 2

    def test_clean_nothing_to_remove(self, tmp_path):
        hm = HistoryManager(str(tmp_path))
        data = _make_data()
        hm.save(data, data.to_json())
        assert hm.clean(keep=10) == 0

    def test_save_removes_old_files(self, tmp_path):
        hm = HistoryManager(str(tmp_path), max_entries=2)
        for i in range(4):
            data = _make_data(f"2026-05-{10+i} 10:00:00")
            hm.save(data, data.to_json())
        # Only 2 report JSON files + index should remain
        json_files = [f for f in (tmp_path / "history").glob("report_*.json")]
        assert len(json_files) == 2
