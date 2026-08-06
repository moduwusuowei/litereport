"""Tests for CLI."""

import json
from pathlib import Path
from click.testing import CliRunner
import pytest
from litereport.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


class TestCLI:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "1.0.3" in result.output

    def test_generate_json(self, tmp_path):
        runner = CliRunner()
        out = str(tmp_path / "report.html")
        result = runner.invoke(main, ["generate", str(FIXTURES / "sample_report.json"), "-o", out])
        assert result.exit_code == 0
        assert "Report generated" in result.output
        assert Path(out).exists()

    def test_generate_junit(self, tmp_path):
        runner = CliRunner()
        out = str(tmp_path / "report.html")
        result = runner.invoke(main, ["generate", str(FIXTURES / "sample_junit.xml"), "-o", out])
        assert result.exit_code == 0
        assert Path(out).exists()

    def test_generate_with_format(self, tmp_path):
        runner = CliRunner()
        out = str(tmp_path / "report.html")
        result = runner.invoke(main, [
            "generate", str(FIXTURES / "sample_junit.xml"),
            "--format", "junit", "-o", out
        ])
        assert result.exit_code == 0

    def test_generate_with_config(self, tmp_path):
        runner = CliRunner()
        out = str(tmp_path / "report.html")
        result = runner.invoke(main, [
            "generate", str(FIXTURES / "sample_report.json"),
            "-c", str(FIXTURES / "sample_config.yaml"),
            "-o", out,
        ])
        assert result.exit_code == 0
        content = Path(out).read_text(encoding="utf-8")
        # Config sets theme=dark, lang=zh
        assert 'data-theme="dark"' in content

    def test_generate_nonexistent_source(self):
        runner = CliRunner()
        result = runner.invoke(main, ["generate", "/nonexistent/file.json"])
        assert result.exit_code != 0

    def test_init_creates_config(self, tmp_path):
        runner = CliRunner()
        out = str(tmp_path / "litereport.yaml")
        result = runner.invoke(main, ["init", "-o", out])
        assert result.exit_code == 0
        assert Path(out).exists()

    def test_init_existing_file(self, tmp_path):
        runner = CliRunner()
        out = str(tmp_path / "litereport.yaml")
        Path(out).write_text("existing", encoding="utf-8")
        result = runner.invoke(main, ["init", "-o", out])
        assert "already exists" in result.output

    def test_history_list_empty(self, tmp_path, monkeypatch):
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(main, ["history", "list"])
        assert result.exit_code == 0
        assert "No history" in result.output

    def test_history_clean(self, tmp_path, monkeypatch):
        runner = CliRunner()
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(main, ["history", "clean", "--keep", "5"])
        assert result.exit_code == 0
