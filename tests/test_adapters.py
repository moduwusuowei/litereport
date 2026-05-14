"""Tests for adapter auto-detection."""

from pathlib import Path
import pytest
from litereport.adapters import auto_detect
from litereport.adapters.json_adapter import JsonAdapter
from litereport.adapters.junit_adapter import JUnitXMLAdapter


FIXTURES = Path(__file__).parent / "fixtures"


def test_auto_detect_json():
    adapter = auto_detect(FIXTURES / "sample_report.json")
    assert isinstance(adapter, JsonAdapter)


def test_auto_detect_junit():
    adapter = auto_detect(FIXTURES / "sample_junit.xml")
    assert isinstance(adapter, JUnitXMLAdapter)


def test_auto_detect_unknown(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("a,b,c", encoding="utf-8")
    with pytest.raises(ValueError, match="Cannot detect"):
        auto_detect(f)
