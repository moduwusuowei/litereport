"""JSON adapter for LiteReport's native JSON format."""

import json
from pathlib import Path

from litereport.adapters.base import BaseAdapter
from litereport.models import ReportData


class JsonAdapter(BaseAdapter):
    """Parses LiteReport's own JSON format."""

    def parse(self, source: Path) -> ReportData:
        text = source.read_text(encoding="utf-8")
        return ReportData.from_json(text)

    @classmethod
    def can_handle(cls, source: Path) -> bool:
        if source.suffix.lower() != ".json":
            return False
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
            return isinstance(data, dict) and "results" in data
        except (json.JSONDecodeError, OSError):
            return False
