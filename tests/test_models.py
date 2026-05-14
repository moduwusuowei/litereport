"""Tests for litereport.models."""

import json
import pytest
from litereport.models import TestResult, ReportData


class TestTestResult:
    def test_defaults(self):
        r = TestResult(name="test_foo")
        assert r.name == "test_foo"
        assert r.outcome == "passed"
        assert r.duration == 0.0
        assert r.markers == []
        assert r.properties == {}

    def test_all_fields(self):
        r = TestResult(
            name="test_bar",
            nodeid="tests/test_x.py::test_bar",
            suite="test_x",
            outcome="failed",
            duration=1.5,
            start_time=1000.0,
            description="A test",
            markers=["smoke"],
            error_message="AssertionError",
            error_traceback="line 10",
            stdout="output",
            properties={"key": "val"},
        )
        assert r.outcome == "failed"
        assert r.properties == {"key": "val"}


class TestReportData:
    def _make_data(self):
        return ReportData(
            title="Test",
            timestamp="2026-05-13T10:00:00",
            duration=10.0,
            environment={"python": "3.11"},
            results=[
                TestResult(name="t1", suite="s1", outcome="passed", duration=1.0),
                TestResult(name="t2", suite="s1", outcome="failed", duration=2.0),
                TestResult(name="t3", suite="s2", outcome="skipped", duration=0.1),
                TestResult(name="t4", suite="s2", outcome="passed", duration=3.0),
                TestResult(name="t5", suite="s1", outcome="error", duration=0.5),
            ],
        )

    def test_summary(self):
        data = self._make_data()
        s = data.summary
        assert s["total"] == 5
        assert s["passed"] == 2
        assert s["failed"] == 1
        assert s["error"] == 1
        assert s["skipped"] == 1
        assert s["pass_rate"] == pytest.approx(40.0)

    def test_summary_empty(self):
        data = ReportData()
        assert data.summary["total"] == 0
        assert data.summary["pass_rate"] == 0

    def test_suites(self):
        data = self._make_data()
        suites = data.suites
        assert set(suites.keys()) == {"s1", "s2"}
        assert len(suites["s1"]) == 3
        assert len(suites["s2"]) == 2

    def test_suites_default(self):
        data = ReportData(results=[TestResult(name="t1")])
        assert "default" in data.suites

    def test_to_json_from_json_roundtrip(self):
        data = self._make_data()
        json_str = data.to_json()
        restored = ReportData.from_json(json_str)
        assert restored.title == data.title
        assert restored.timestamp == data.timestamp
        assert restored.duration == data.duration
        assert restored.environment == data.environment
        assert len(restored.results) == len(data.results)
        for orig, rest in zip(data.results, restored.results):
            assert orig.name == rest.name
            assert orig.outcome == rest.outcome
            assert orig.duration == rest.duration
            assert orig.suite == rest.suite

    def test_from_json_missing_results(self):
        data = ReportData.from_json('{"title": "X"}')
        assert data.title == "X"
        assert data.results == []

    def test_extra_field(self):
        data = ReportData(extra={"custom": [1, 2, 3]})
        restored = ReportData.from_json(data.to_json())
        assert restored.extra == {"custom": [1, 2, 3]}
