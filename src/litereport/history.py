"""History management for LiteReport."""

import json
import os
import time
from pathlib import Path
from typing import List, Optional

from litereport.models import ReportData


class HistoryManager:
    """Manages historical report storage and indexing."""

    def __init__(self, output_dir: str, max_entries: int = 30):
        self.output_dir = Path(output_dir)
        self.history_dir = self.output_dir / "history"
        self.index_path = self.history_dir / "index.json"
        self.max_entries = max_entries

    def save(self, data: ReportData, json_content: str) -> str:
        """Save report data to history. Returns the history JSON filename."""
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped filename (add counter to avoid collisions)
        ts = time.strftime("%Y%m%d_%H%M%S")
        base_json = f"report_{ts}.json"
        counter = 0
        while (self.history_dir / base_json).exists():
            counter += 1
            base_json = f"report_{ts}_{counter}.json"
        json_name = base_json
        html_name = json_name.replace(".json", ".html")

        # Save JSON data
        json_path = self.history_dir / json_name
        json_path.write_text(json_content, encoding="utf-8")

        # Update index
        index = self.load_index()
        summary = data.summary
        entry = {
            "timestamp": data.timestamp,
            "filename": f"history/{html_name}",
            "json_file": f"history/{json_name}",
            "total": summary["total"],
            "passed": summary["passed"],
            "failed": summary["failed"],
            "skipped": summary["skipped"],
            "duration": data.duration,
        }
        index.insert(0, entry)

        # Trim old entries
        if len(index) > self.max_entries:
            removed = index[self.max_entries:]
            index = index[:self.max_entries]
            for old in removed:
                self._remove_files(old)

        self._save_index(index)
        return html_name

    def load_index(self) -> List[dict]:
        """Load the history index."""
        if not self.index_path.exists():
            return []
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def clean(self, keep: int) -> int:
        """Remove old history entries, keeping the most recent `keep`. Returns count removed."""
        index = self.load_index()
        if len(index) <= keep:
            return 0

        removed = index[keep:]
        index = index[:keep]

        for old in removed:
            self._remove_files(old)

        self._save_index(index)
        return len(removed)

    def _save_index(self, index: List[dict]) -> None:
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _remove_files(self, entry: dict) -> None:
        """Remove JSON and HTML files for a history entry."""
        for key in ("json_file", "filename"):
            rel = entry.get(key, "")
            if rel:
                p = self.output_dir / rel
                if p.exists():
                    p.unlink()
