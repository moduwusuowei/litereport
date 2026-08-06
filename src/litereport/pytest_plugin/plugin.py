"""LiteReport pytest plugin implementation."""

import glob
import os
import platform
import sys
import time
from datetime import datetime
from typing import Dict, List

from litereport.config import LiteReportConfig
from litereport.generator import ReportGenerator
from litereport.history import HistoryManager
from litereport.models import ReportData, TestResult

#: Filename pattern for per-worker result shards written by xdist workers.
#: The master process scans this pattern, merges the shards and then removes them.
_WORKER_SHARD_PATTERN = "report_data.worker.*.json"


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
        plugin = LiteReportPlugin(config_path, title_override, config)
        config.pluginmanager.register(plugin, "litereport_plugin")


class LiteReportPlugin:
    def __init__(self, config_path=None, title_override=None, config=None):
        self.config = LiteReportConfig.load(config_path)
        if title_override:
            self.config.title = title_override
        self._results: List[TestResult] = []
        self._descriptions: Dict[str, str] = {}
        self._markers: Dict[str, List[str]] = {}
        self._start_time = 0.0

        # Detect pytest-xdist execution mode:
        #   * worker process  -> PYTEST_XDIST_WORKER env var set (e.g. "gw0")
        #   * master process  -> xdist plugin registered on the controller node
        self._xdist_worker = os.environ.get("PYTEST_XDIST_WORKER")
        self._xdist_enabled = self._xdist_worker is not None or (
            config is not None and config.pluginmanager.hasplugin("xdist")
        )

    def pytest_sessionstart(self, session):
        self._start_time = time.time()

    def pytest_runtest_setup(self, item):
        """Capture docstrings and markers early — TestReport doesn't carry them
        reliably (pytest >= 9 exposes keywords as a plain dict, so markers can
        no longer be read from the report object)."""
        try:
            doc = item.function.__doc__
            if doc:
                self._descriptions[item.nodeid] = doc.strip()
        except (AttributeError, TypeError):
            pass
        try:
            self._markers[item.nodeid] = [m.name for m in item.iter_markers()]
        except (AttributeError, TypeError):
            pass

    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return

        markers = self._markers.get(report.nodeid, [])

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
        # xdist worker: only dump a per-worker shard; the master merges it.
        if self._xdist_worker:
            self._dump_worker_shard()
            return

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
            results=self._collect_results(),
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

    # ── xdist helpers ──────────────────────────────────────────────────────

    def _collect_results(self) -> List[TestResult]:
        """Return the final result list for report generation.

        In xdist mode the authoritative data lives in the per-worker shards,
        because reports forwarded from workers to the master lose fields such
        as docstrings, markers, captured stdout and user properties. In serial
        mode results are collected locally as before.
        """
        if not self._xdist_enabled or self._xdist_worker:
            return self._results
        merged = self._load_worker_shards()
        if merged:
            return merged
        # Fallback: no shards found — keep whatever was forwarded to the master.
        return self._results

    def _dump_worker_shard(self) -> None:
        """Persist this worker's results into a shard file for the master."""
        try:
            os.makedirs(self.config.output_dir, exist_ok=True)
            data = ReportData(results=self._results)
            shard_path = os.path.join(
                self.config.output_dir,
                "report_data.worker.{}.json".format(self._xdist_worker),
            )
            with open(shard_path, "w", encoding="utf-8") as f:
                f.write(data.to_json())
        except Exception as exc:  # reporting must never break the run
            sys.stderr.write(
                "[litereport] failed to dump xdist worker shard: {}\n".format(exc)
            )

    def _load_worker_shards(self) -> List[TestResult]:
        """Merge all worker shards into one deterministically ordered list."""
        merged: List[TestResult] = []
        pattern = os.path.join(self.config.output_dir, _WORKER_SHARD_PATTERN)
        for shard_path in sorted(glob.glob(pattern)):
            try:
                with open(shard_path, "r", encoding="utf-8") as f:
                    data = ReportData.from_json(f.read())
                merged.extend(data.results)
            except Exception:
                continue
            finally:
                try:
                    os.remove(shard_path)
                except OSError:
                    pass
        merged.sort(key=lambda r: r.nodeid)
        return merged
