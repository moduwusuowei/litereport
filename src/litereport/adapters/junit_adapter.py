"""JUnit XML adapter."""

import xml.etree.ElementTree as ET
from pathlib import Path

from litereport.adapters.base import BaseAdapter
from litereport.models import ReportData, TestResult


class JUnitXMLAdapter(BaseAdapter):
    """Parses standard JUnit XML format."""

    def parse(self, source: Path) -> ReportData:
        tree = ET.parse(source)
        root = tree.getroot()

        results = []
        total_duration = 0.0

        # Handle both <testsuites> and single <testsuite>
        if root.tag == "testsuites":
            suites = root.findall("testsuite")
        elif root.tag == "testsuite":
            suites = [root]
        else:
            raise ValueError(f"Unexpected root element: <{root.tag}>")

        for suite_el in suites:
            suite_name = suite_el.get("name", "unknown")
            suite_time = float(suite_el.get("time", 0))
            total_duration += suite_time

            for tc in suite_el.findall("testcase"):
                result = self._parse_testcase(tc, suite_name)
                results.append(result)

        return ReportData(
            title=root.get("name", "Test Report"),
            duration=total_duration,
            results=results,
        )

    def _parse_testcase(self, tc: ET.Element, suite_name: str) -> TestResult:
        name = tc.get("name", "unknown")
        classname = tc.get("classname", "")
        duration = float(tc.get("time", 0))

        # Determine outcome
        outcome = "passed"
        error_message = ""
        error_traceback = ""

        failure = tc.find("failure")
        error = tc.find("error")
        skipped = tc.find("skipped")

        if failure is not None:
            outcome = "failed"
            error_message = failure.get("message", "")
            error_traceback = failure.text or ""
        elif error is not None:
            outcome = "error"
            error_message = error.get("message", "")
            error_traceback = error.text or ""
        elif skipped is not None:
            outcome = "skipped"
            error_message = skipped.get("message", "")

        # stdout
        stdout_el = tc.find("system-out")
        stdout = stdout_el.text or "" if stdout_el is not None else ""

        # properties
        properties = {}
        props_el = tc.find("properties")
        if props_el is not None:
            for prop in props_el.findall("property"):
                prop_name = prop.get("name", "")
                prop_value = prop.get("value", "")
                if prop_name:
                    properties[prop_name] = prop_value

        nodeid = f"{classname}::{name}" if classname else name

        return TestResult(
            name=name,
            nodeid=nodeid,
            suite=suite_name,
            outcome=outcome,
            duration=duration,
            error_message=error_message,
            error_traceback=error_traceback,
            stdout=stdout,
            properties=properties,
        )

    @classmethod
    def can_handle(cls, source: Path) -> bool:
        if source.suffix.lower() != ".xml":
            return False
        try:
            tree = ET.parse(source)
            root = tree.getroot()
            return root.tag in ("testsuites", "testsuite")
        except (ET.ParseError, OSError):
            return False
