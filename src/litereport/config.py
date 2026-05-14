"""Configuration loading and management for LiteReport."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


_DEFAULTS = {
    "title": "Test Report",
    "logo": None,
    "theme": "light",
    "lang": "en",
    "history_enabled": True,
    "history_max_entries": 30,
    "output_dir": "./reports",
    "output_filename": "report.html",
    "environment": {},
}


@dataclass
class LiteReportConfig:
    """LiteReport configuration."""

    title: str = "Test Report"
    logo: Optional[str] = None
    theme: str = "light"
    lang: str = "en"
    history_enabled: bool = True
    history_max_entries: int = 30
    output_dir: str = "./reports"
    output_filename: str = "report.html"
    environment: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "LiteReportConfig":
        """Load config with priority: explicit path > project dir > global > defaults."""
        merged: Dict[str, Any] = dict(_DEFAULTS)

        # Global config
        global_path = Path.home() / ".litereport" / "config.yaml"
        if global_path.exists():
            _merge_yaml(merged, global_path)

        # Project-level config
        project_path = Path("litereport.yaml")
        if project_path.exists():
            _merge_yaml(merged, project_path)

        # Explicit path
        if path:
            p = Path(path)
            if not p.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            _merge_yaml(merged, p)

        return cls(
            title=merged["title"],
            logo=merged["logo"],
            theme=merged["theme"],
            lang=merged["lang"],
            history_enabled=merged["history_enabled"],
            history_max_entries=merged["history_max_entries"],
            output_dir=merged["output_dir"],
            output_filename=merged["output_filename"],
            environment=merged["environment"],
        )


def _merge_yaml(merged: Dict[str, Any], path: Path) -> None:
    """Merge a YAML config file into the merged dict."""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        return

    report = raw.get("report", {})
    if isinstance(report, dict):
        for key in ("title", "logo", "theme", "lang"):
            if key in report:
                merged[key] = report[key]

    history = raw.get("history", {})
    if isinstance(history, dict):
        if "enabled" in history:
            merged["history_enabled"] = bool(history["enabled"])
        if "max_entries" in history:
            merged["history_max_entries"] = int(history["max_entries"])

    output = raw.get("output", {})
    if isinstance(output, dict):
        if "dir" in output:
            merged["output_dir"] = output["dir"]
        if "filename" in output:
            merged["output_filename"] = output["filename"]

    env = raw.get("environment", {})
    if isinstance(env, dict):
        merged["environment"].update(env)
