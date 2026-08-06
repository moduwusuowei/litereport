"""Report generator — renders ReportData into self-contained HTML."""

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup

from litereport.config import LiteReportConfig
from litereport.models import ReportData

# ── i18n ──

I18N: Dict[str, Dict[str, str]] = {
    "en": {
        "passed": "Passed",
        "failed": "Failed",
        "skipped": "Skipped",
        "duration": "Duration",
        "pass_rate": "Pass Rate",
        "result_distribution": "Result Distribution",
        "suite_breakdown": "Suite Breakdown",
        "failures": "Failures",
        "all_tests": "All Tests",
        "slowest_tests": "Slowest Tests",
        "search_placeholder": "Search test name or description...",
        "history": "History",
        "latest_report": "Latest Report",
        "no_history": "No history reports",
        "current": "Current",
        "screenshot": "Screenshot",
    },
    "zh": {
        "passed": "通过",
        "failed": "失败",
        "skipped": "跳过",
        "duration": "耗时",
        "pass_rate": "通过率",
        "result_distribution": "结果分布",
        "suite_breakdown": "套件分布",
        "failures": "失败详情",
        "all_tests": "全部用例",
        "slowest_tests": "最慢用例",
        "search_placeholder": "搜索用例名称或描述...",
        "history": "历史报告",
        "latest_report": "最新报告",
        "no_history": "暂无历史报告",
        "current": "当前",
        "screenshot": "截图",
    },
}


def _make_translate(lang: str):
    """Create a Jinja2 filter function for i18n."""
    table = I18N.get(lang, I18N["en"])
    fallback = I18N["en"]

    def t(key: str) -> str:
        return table.get(key, fallback.get(key, key))

    return t


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s"


class ReportGenerator:
    """Generates HTML reports from ReportData using Jinja2 templates."""

    def __init__(self, config: Optional[LiteReportConfig] = None):
        self.config = config or LiteReportConfig()
        self.env = Environment(
            loader=PackageLoader("litereport", "templates"),
            autoescape=select_autoescape(["html"]),
        )
        self.env.filters["t"] = _make_translate(self.config.lang)

        # Load Chart.js for self-contained HTML
        chartjs_path = Path(__file__).parent / "templates" / "chartjs.min.js"
        self._chartjs_code = Markup(chartjs_path.read_text(encoding="utf-8"))

    def render(self, data: ReportData, history_entries: Optional[List[dict]] = None,
               latest_url: str = "report.html") -> str:
        """Render ReportData to HTML string."""
        summary = data.summary
        suites = data.suites

        # Build suite data for template
        suites_data = []
        suite_labels = []
        suite_passed_counts = []
        suite_failed_counts = []
        suite_skipped_counts = []

        for suite_name in sorted(suites.keys()):
            results = suites[suite_name]
            s_total = len(results)
            s_passed = sum(1 for r in results if r.outcome == "passed")
            s_failed = sum(1 for r in results if r.outcome in ("failed", "error"))
            s_skipped = sum(1 for r in results if r.outcome in ("skipped", "xfailed"))
            s_duration = sum(r.duration for r in results)
            s_rate = (s_passed / s_total * 100) if s_total > 0 else 0

            suite_id = suite_name.replace("/", "_").replace(" ", "_").replace(".", "_")

            suites_data.append({
                "name": suite_name,
                "id": suite_id,
                "total": s_total,
                "passed": s_passed,
                "failed": s_failed,
                "skipped": s_skipped,
                "duration": s_duration,
                "pass_rate": s_rate,
                "bar_p": s_passed / s_total * 100 if s_total else 0,
                "bar_f": s_failed / s_total * 100 if s_total else 0,
                "bar_s": s_skipped / s_total * 100 if s_total else 0,
                "cases": results,
            })

            suite_labels.append(suite_name)
            suite_passed_counts.append(s_passed)
            suite_failed_counts.append(s_failed)
            suite_skipped_counts.append(s_skipped)

        # Failures
        failures = [r for r in data.results if r.outcome in ("failed", "error")]

        # Duration top 15
        top_duration = sorted(data.results, key=lambda r: r.duration, reverse=True)[:15]

        # Results JSON for JS
        results_json = json.dumps([asdict(r) for r in data.results], ensure_ascii=False)

        template = self.env.get_template("report.html.j2")
        return template.render(
            data=data,
            config=self.config,
            summary=summary,
            duration_str=format_duration(data.duration),
            suites_data=suites_data,
            suite_labels_json=json.dumps(suite_labels, ensure_ascii=False),
            suite_passed_json=json.dumps(suite_passed_counts),
            suite_failed_json=json.dumps(suite_failed_counts),
            suite_skipped_json=json.dumps(suite_skipped_counts),
            failures=failures,
            top_duration=top_duration,
            results_json=results_json,
            history_entries=history_entries or [],
            history_json=json.dumps(history_entries or [], ensure_ascii=False),
            latest_url=latest_url,
            version="1.0.3",
            chartjs_code=self._chartjs_code,
        )

    def generate(self, data: ReportData, output_path: str,
                 history_entries: Optional[List[dict]] = None) -> str:
        """Render and write HTML report to file. Returns the output path."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Adjust history links for files in history/ subdirectory
        is_in_history = "history" in os.path.normpath(output_path).replace("\\", "/")
        adjusted = []
        for entry in (history_entries or []):
            e = dict(entry)
            fn = e.get("filename", "")
            if is_in_history and fn.startswith("history/"):
                e["filename"] = fn[len("history/"):]
            adjusted.append(e)

        latest_url = "../" + self.config.output_filename if is_in_history else self.config.output_filename

        html = self.render(data, history_entries=adjusted, latest_url=latest_url)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
