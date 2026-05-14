"""Tests for litereport.config."""

import os
import pytest
from pathlib import Path
from litereport.config import LiteReportConfig


class TestLiteReportConfig:
    def test_defaults(self):
        cfg = LiteReportConfig()
        assert cfg.title == "Test Report"
        assert cfg.theme == "light"
        assert cfg.lang == "en"
        assert cfg.history_enabled is True
        assert cfg.history_max_entries == 30
        assert cfg.output_dir == "./reports"

    def test_load_defaults(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cfg = LiteReportConfig.load()
        assert cfg.title == "Test Report"

    def test_load_explicit_file(self, tmp_path):
        cfg_file = tmp_path / "test.yaml"
        cfg_file.write_text(
            "report:\n  title: Custom Title\n  theme: dark\n  lang: zh\n"
            "history:\n  enabled: false\n  max_entries: 10\n"
            "output:\n  dir: ./out\n  filename: r.html\n"
            "environment:\n  project: MyProj\n",
            encoding="utf-8",
        )
        cfg = LiteReportConfig.load(str(cfg_file))
        assert cfg.title == "Custom Title"
        assert cfg.theme == "dark"
        assert cfg.lang == "zh"
        assert cfg.history_enabled is False
        assert cfg.history_max_entries == 10
        assert cfg.output_dir == "./out"
        assert cfg.output_filename == "r.html"
        assert cfg.environment["project"] == "MyProj"

    def test_load_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            LiteReportConfig.load("/nonexistent/path.yaml")

    def test_load_project_level(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "litereport.yaml").write_text(
            "report:\n  title: Project Title\n", encoding="utf-8"
        )
        cfg = LiteReportConfig.load()
        assert cfg.title == "Project Title"

    def test_load_priority(self, tmp_path, monkeypatch):
        """Explicit path overrides project-level config."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "litereport.yaml").write_text(
            "report:\n  title: Project\n", encoding="utf-8"
        )
        explicit = tmp_path / "override.yaml"
        explicit.write_text("report:\n  title: Override\n", encoding="utf-8")
        cfg = LiteReportConfig.load(str(explicit))
        assert cfg.title == "Override"

    def test_load_empty_yaml(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cfg_file = tmp_path / "empty.yaml"
        cfg_file.write_text("", encoding="utf-8")
        cfg = LiteReportConfig.load(str(cfg_file))
        assert cfg.title == "Test Report"

    def test_environment_merge(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "litereport.yaml").write_text(
            "environment:\n  a: '1'\n  b: '2'\n", encoding="utf-8"
        )
        explicit = tmp_path / "extra.yaml"
        explicit.write_text("environment:\n  b: '3'\n  c: '4'\n", encoding="utf-8")
        cfg = LiteReportConfig.load(str(explicit))
        assert cfg.environment["a"] == "1"
        assert cfg.environment["b"] == "3"
        assert cfg.environment["c"] == "4"
