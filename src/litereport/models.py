"""Core data models for LiteReport."""

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class TestResult:
    """A single test case result."""

    name: str
    nodeid: str = ""
    suite: str = ""
    outcome: str = "passed"
    duration: float = 0.0
    start_time: float = 0.0
    description: str = ""
    markers: List[str] = field(default_factory=list)
    error_message: str = ""
    error_traceback: str = ""
    stdout: str = ""
    properties: Dict[str, str] = field(default_factory=dict)


@dataclass
class ReportData:
    """Complete report data container."""

    title: str = "Test Report"
    timestamp: str = ""
    duration: float = 0.0
    environment: Dict[str, str] = field(default_factory=dict)
    results: List[TestResult] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ReportData":
        data = json.loads(json_str)
        results = [TestResult(**r) for r in data.pop("results", [])]
        return cls(**data, results=results)

    @property
    def summary(self) -> Dict[str, Any]:
        """Compute summary statistics."""
        total = len(self.results)
        counts: Dict[str, int] = {}
        for r in self.results:
            counts[r.outcome] = counts.get(r.outcome, 0) + 1
        passed = counts.get("passed", 0)
        return {
            "total": total,
            "passed": passed,
            "failed": counts.get("failed", 0),
            "error": counts.get("error", 0),
            "skipped": counts.get("skipped", 0),
            "xfailed": counts.get("xfailed", 0),
            "xpassed": counts.get("xpassed", 0),
            "pass_rate": (passed / total * 100) if total > 0 else 0,
        }

    @property
    def suites(self) -> Dict[str, List[TestResult]]:
        """Group results by suite name."""
        groups: Dict[str, List[TestResult]] = {}
        for r in self.results:
            groups.setdefault(r.suite or "default", []).append(r)
        return groups
