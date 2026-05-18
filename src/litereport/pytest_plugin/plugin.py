"""LiteReport pytest plugin implementation."""

import os
import platform
import time
from datetime import datetime
from typing import Dict, List

from litereport.config import LiteReportConfig
from litereport.generator import ReportGenerator
from litereport.history import HistoryManager
from litereport.models import ReportData, TestResult


def pytest_addoption(parser):
    group = parser.getgroup("litereport", "LiteReport test reporting")
    group.addoption(
        "--litereport",
        action="store_true",
        default=False,
        help="Enable LiteReport HTML report generation.",
    )
    group.addoption(
        "--litereport-config",
        default=None,
        help="Path to litereport.yaml config file.",
    )
    group.addoption(
        "--litereport-title",
        default=None,
        help="Override report title.",
    )


def pytest_configure(config):
    if config.getoption("--litereport", default=False):
        config_path = config.getoption("--litereport-config", default=None)
        title_override = config.getoption("--litereport-title", default=None)
        plugin = LiteReportPlugin(config_path, title_override)
        config.pluginmanager.register(plugin, "litereport_plugin")


class LiteReportPlugin:
    def __init__(self, config_path=None, title_override=None):
        self.config = LiteReportConfig.load(config_path)
        if title_override:
            self.config.title = title_override
        self._results: List[TestResult] = []
        self._descriptions: Dict[str, str] = {}
        self._start_time = 0.0

    def pytest_sessionstart(self, session):
        self._start_time = time.time()

    def pytest_runtest_setup(self, item):
        """Capture docstrings early — TestReport doesn't have item attribute."""
        try:
            doc = item.function.__doc__
            if doc:
                self._descriptions[item.nodeid] = doc.strip()
        except (AttributeError, TypeError):
            pass

    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return

        markers = []
        try:
            for marker in report.keywords.get("pytestmark", []):
                markers.append(marker.name)
        except (AttributeError, TypeError):
            pass

        parts = report.nodeid.split("::")
        suite = parts[0].split("/")[-1].replace(".py", "") if parts else "unknown"

        # Extract user_properties (e.g. screenshots attached by fixtures)
        props = {}
        screenshots = []
        if hasattr(report, "user_properties"):
            for key, value in report.user_properties:
                if key == "screenshot":
                    # Normalize: string (legacy) -> dict with label
                    if isinstance(value, str):
                        screenshots.append({"label": "", "data": value})
                    elif isinstance(value, dict):
                        screenshots.append(value)
                else:
                    props[key] = value
        if screenshots:
            props["screenshots"] = screenshots

        result = TestResult(
            name=getattr(report, "head_line", report.nodeid.split("::")[-1]),
            nodeid=report.nodeid,
            suite=suite,
            outcome=report.outcome,
            duration=getattr(report, "duration", 0.0),
            start_time=self._start_time,
            description=self._descriptions.get(report.nodeid, ""),
            markers=markers,
            error_message=str(report.longrepr).split("\n")[0] if report.failed else "",
            error_traceback=str(report.longrepr) if report.failed else "",
            stdout=report.capstdout if hasattr(report, "capstdout") else "",
            properties=props,
        )
        self._results.append(result)

    def pytest_sessionfinish(self, session, exitstatus):
        duration = time.time() - self._start_time

        env = dict(self.config.environment)
        env.setdefault("python", platform.python_version())
        env.setdefault("platform", platform.platform())

        # Merge board/chip info injected by conftest fixtures
        board_info = getattr(session.config, "_litereport_board_info", {})
        for key, val in board_info.items():
            env.setdefault(key, val)

        data = ReportData(
            title=self.config.title,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration=duration,
            environment=env,
            results=self._results,
        )

        os.makedirs(self.config.output_dir, exist_ok=True)
        json_path = os.path.join(self.config.output_dir, "report_data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(data.to_json())

        history_entries = None
        if self.config.history_enabled:
            hm = HistoryManager(self.config.output_dir, self.config.history_max_entries)
            hm.save(data, data.to_json())
            history_entries = hm.load_index()

        gen = ReportGenerator(self.config)
        output = os.path.join(self.config.output_dir, self.config.output_filename)
        gen.generate(data, output, history_entries=history_entries)

        # Regenerate all history HTML with current template
        if self.config.history_enabled and history_entries:
            for entry in history_entries:
                json_file = entry.get("json_file", "")
                html_file = entry.get("filename", "")
                if json_file and html_file:
                    jp = os.path.join(self.config.output_dir, json_file)
                    hp = os.path.join(self.config.output_dir, html_file)
                    if os.path.exists(jp):
                        try:
                            with open(jp, "r", encoding="utf-8") as f:
                                hist_data = ReportData.from_json(f.read())
                            gen.generate(hist_data, hp, history_entries=history_entries)
                        except Exception:
                            pass
