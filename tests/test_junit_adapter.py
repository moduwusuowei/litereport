"""Tests for JUnit XML adapter."""

from pathlib import Path
import pytest
from litereport.adapters.junit_adapter import JUnitXMLAdapter


FIXTURES = Path(__file__).parent / "fixtures"


class TestJUnitXMLAdapter:
    def test_can_handle_valid(self):
        assert JUnitXMLAdapter.can_handle(FIXTURES / "sample_junit.xml") is True

    def test_can_handle_json(self):
        assert JUnitXMLAdapter.can_handle(FIXTURES / "sample_report.json") is False

    def test_can_handle_nonexistent(self, tmp_path):
        assert JUnitXMLAdapter.can_handle(tmp_path / "nope.xml") is False

    def test_can_handle_non_junit_xml(self, tmp_path):
        f = tmp_path / "other.xml"
        f.write_text('<?xml version="1.0"?><root/>', encoding="utf-8")
        assert JUnitXMLAdapter.can_handle(f) is False

    def test_parse(self):
        adapter = JUnitXMLAdapter()
        data = adapter.parse(FIXTURES / "sample_junit.xml")
        assert data.title == "My Test Suite"
        assert len(data.results) == 5

        # Check outcomes
        outcomes = {r.name: r.outcome for r in data.results}
        assert outcomes["test_login"] == "passed"
        assert outcomes["test_logout"] == "failed"
        assert outcomes["test_signup"] == "skipped"
        assert outcomes["test_home_page"] == "passed"
        assert outcomes["test_dashboard"] == "error"

    def test_parse_suites(self):
        adapter = JUnitXMLAdapter()
        data = adapter.parse(FIXTURES / "sample_junit.xml")
        suites = data.suites
        assert "test_auth" in suites
        assert "test_pages" in suites
        assert len(suites["test_auth"]) == 3
        assert len(suites["test_pages"]) == 2

    def test_parse_failure_details(self):
        adapter = JUnitXMLAdapter()
        data = adapter.parse(FIXTURES / "sample_junit.xml")
        failed = [r for r in data.results if r.outcome == "failed"][0]
        assert "AssertionError" in failed.error_message
        assert "line 25" in failed.error_traceback

    def test_parse_properties(self):
        adapter = JUnitXMLAdapter()
        data = adapter.parse(FIXTURES / "sample_junit.xml")
        home = [r for r in data.results if r.name == "test_home_page"][0]
        assert home.properties == {"browser": "chrome"}

    def test_parse_stdout(self):
        adapter = JUnitXMLAdapter()
        data = adapter.parse(FIXTURES / "sample_junit.xml")
        login = [r for r in data.results if r.name == "test_login"][0]
        assert login.stdout == "Login successful"

    def test_parse_single_testsuite(self, tmp_path):
        xml = tmp_path / "single.xml"
        xml.write_text(
            '<?xml version="1.0"?>'
            '<testsuite name="solo" tests="1" time="1.0">'
            '<testcase name="test_one" classname="m" time="1.0"/>'
            '</testsuite>',
            encoding="utf-8",
        )
        adapter = JUnitXMLAdapter()
        data = adapter.parse(xml)
        assert len(data.results) == 1
        assert data.results[0].name == "test_one"
