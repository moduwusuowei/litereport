"""LiteReport CLI — command-line interface."""

import json
import os
import shutil
import sys
from pathlib import Path

import click

from litereport.config import LiteReportConfig
from litereport.generator import ReportGenerator
from litereport.history import HistoryManager
from litereport.adapters import auto_detect
/requesting-code-review

@click.group()
@click.version_option(package_name="litereport")
def main():
    """LiteReport — Lightweight test report visualization."""
    pass


@main.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="Output HTML path.")
@click.option("-c", "--config", "config_path", default=None, help="Config file path.")
@click.option("--format", "fmt", default=None, type=click.Choice(["json", "junit"]),
              help="Force input format (auto-detected by default).")
@click.option("--with-history", is_flag=True, help="Include history in report.")
def generate(source, output, config_path, fmt, with_history):
    """Generate an HTML report from test data."""
    cfg = LiteReportConfig.load(config_path)
    source_path = Path(source)

    # Parse input
    if fmt == "json":
        from litereport.adapters.json_adapter import JsonAdapter
        adapter = JsonAdapter()
    elif fmt == "junit":
        from litereport.adapters.junit_adapter import JUnitXMLAdapter
        adapter = JUnitXMLAdapter()
    else:
        adapter = auto_detect(source_path)

    data = adapter.parse(source_path)

    # Merge config environment into data
    merged_env = dict(cfg.environment)
    merged_env.update(data.environment)
    data.environment = merged_env

    if cfg.title != "Test Report" and data.title == "Test Report":
        data.title = cfg.title

    # Output path
    if not output:
        output = os.path.join(cfg.output_dir, cfg.output_filename)

    # History
    history_entries = None
    if with_history:
        hm = HistoryManager(cfg.output_dir, cfg.history_max_entries)
        history_entries = hm.load_index()
        if history_entries:
            click.echo(f"Loaded {len(history_entries)} history entries.")

    gen = ReportGenerator(cfg)
    path = gen.generate(data, output, history_entries=history_entries)
    click.echo(f"Report generated: {path}")


@main.group()
def history():
    """Manage report history."""
    pass


@history.command("list")
@click.option("-c", "--config", "config_path", default=None, help="Config file path.")
def history_list(config_path):
    """List history entries."""
    cfg = LiteReportConfig.load(config_path)
    hm = HistoryManager(cfg.output_dir, cfg.history_max_entries)
    index = hm.load_index()
    if not index:
        click.echo("No history entries found.")
        return
    for i, entry in enumerate(index, 1):
        ts = entry.get("timestamp", "?")
        total = entry.get("total", 0)
        passed = entry.get("passed", 0)
        failed = entry.get("failed", 0)
        click.echo(f"  {i}. {ts}  total={total} passed={passed} failed={failed}")


@history.command("clean")
@click.option("--keep", default=10, help="Number of entries to keep.")
@click.option("-c", "--config", "config_path", default=None, help="Config file path.")
def history_clean(keep, config_path):
    """Clean old history entries."""
    cfg = LiteReportConfig.load(config_path)
    hm = HistoryManager(cfg.output_dir, cfg.history_max_entries)
    removed = hm.clean(keep=keep)
    click.echo(f"Removed {removed} history entries, kept {keep}.")


@main.command()
@click.option("-o", "--output", default="litereport.yaml", help="Output config file path.")
def init(output):
    """Initialize a litereport.yaml config file."""
    if os.path.exists(output):
        click.echo(f"Config file already exists: {output}")
        return
    example = Path(__file__).parent.parent.parent / "litereport.yaml.example"
    if not example.exists():
        # Fallback: write default config inline
        content = (
            "# LiteReport Configuration\n\n"
            "report:\n"
            "  title: \"Test Report\"\n"
            "  theme: \"light\"\n"
            "  lang: \"en\"\n\n"
            "history:\n"
            "  enabled: true\n"
            "  max_entries: 30\n\n"
            "output:\n"
            "  dir: \"./reports\"\n"
            "  filename: \"report.html\"\n"
        )
    else:
        content = example.read_text(encoding="utf-8")
    Path(output).write_text(content, encoding="utf-8")
    click.echo(f"Config file created: {output}")


if __name__ == "__main__":
    main()
