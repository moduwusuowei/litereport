"""Tests for JSON adapter."""

from pathlib import Path
import pytest
from litereport.adapters.json_adapter import JsonAdapter


FIXTURES = Path(__file__).parent / "fixtures"


class TestJsonAdapter:
    def test_can_handle_valid(self):
        assert JsonAdapter.can_handle(FIXTURES / "sample_report.json") is True

    def test_can_handle_xml(self):
        assert JsonAdapter.can_handle(FIXTURES / "sample_junit.xml") is False

    def test_can_handle_nonexistent(self, tmp_path):
        assert JsonAdapter.can_handle(tmp_path / "nope.json") is False

    def test_can_handle_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not json", encoding="utf-8")
        assert JsonAdapter.can_handle(f) is False

    def test_can_handle_json_without_results(self, tmp_path):
        f = tmp_path / "no_results.json"
        f.write_text('{"title": "hi"}', encoding="utf-8")
        assert JsonAdapter.can_handle(f) is False

    def test_parse(self):
        adapter = JsonAdapter()
        data = adapter.parse(FIXTURES / "sample_report.json")
        assert data.title == "Sample Test Report"
        assert len(data.results) == 5
        assert data.results[0].name == "test_login"
        assert data.results[0].outcome == "passed"
        assert data.results[1].outcome == "failed"
        assert data.environment["python"] == "3.11.0"
