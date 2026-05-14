"""Tests for report generator."""

import json
from pathlib import Path
import pytest
from litereport.models import TestResult, ReportData
from litereport.config import LiteReportConfig
from litereport.generator import ReportGenerator, format_duration


def _sample_data():
    return ReportData(
        title="Test Report",
        timestamp="2026-05-13T10:00:00",
        duration=65.0,
        environment={"python": "3.11", "platform": "Linux"},
        results=[
            TestResult(name="test_a", suite="suite1", outcome="passed", duration=1.0, description="Test A desc"),
            TestResult(name="test_b", suite="suite1", outcome="failed", duration=2.0,
                       error_message="AssertionError", error_traceback="line 10"),
            TestResult(name="test_c", suite="suite2", outcome="skipped", duration=0.0),
            TestResult(name="test_d", suite="suite2", outcome="passed", duration=3.5),
        ],
    )


class TestFormatDuration:
    def test_seconds(self):
        assert format_duration(45) == "45s"

    def test_minutes(self):
        assert format_duration(125) == "2m05s"

    def test_hours(self):
        assert format_duration(3661) == "1h01m01s"


class TestReportGenerator:
    def test_render_produces_html(self):
        gen = ReportGenerator()
        html = gen.render(_sample_data())
        assert "<!DOCTYPE html>" in html
        assert "Test Report" in html
        assert "test_a" in html
        assert "test_b" in html

    def test_render_contains_summary(self):
        gen = ReportGenerator()
        html = gen.render(_sample_data())
        assert "Passed" in html
        assert "Failed" in html

    def test_render_with_history(self):
        gen = ReportGenerator()
        history = [
            {"timestamp": "2026-05-12 10:00:00", "filename": "history/r1.html",
             "total": 4, "passed": 3, "failed": 1},
        ]
        html = gen.render(_sample_data(), history_entries=history)
        assert "2026-05-12 10:00:00" in html

    def test_render_dark_theme(self):
        cfg = LiteReportConfig(theme="dark")
        gen = ReportGenerator(cfg)
        html = gen.render(_sample_data())
        assert 'data-theme="dark"' in html

    def test_render_zh_lang(self):
        cfg = LiteReportConfig(lang="zh")
        gen = ReportGenerator(cfg)
        html = gen.render(_sample_data())
        assert "通过" in html
        assert "失败" in html

    def test_generate_writes_file(self, tmp_path):
        out = str(tmp_path / "report.html")
        gen = ReportGenerator()
        result = gen.generate(_sample_data(), out)
        assert result == out
        content = Path(out).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "test_a" in content

    def test_generate_creates_dirs(self, tmp_path):
        out = str(tmp_path / "sub" / "dir" / "report.html")
        gen = ReportGenerator()
        gen.generate(_sample_data(), out)
        assert Path(out).exists()

    def test_failures_section(self):
        gen = ReportGenerator()
        html = gen.render(_sample_data())
        assert "AssertionError" in html
        assert "line 10" in html

    def test_description_in_output(self):
        gen = ReportGenerator()
        html = gen.render(_sample_data())
        assert "Test A desc" in html
