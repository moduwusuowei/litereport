"""Adapter registry and auto-detection."""

from pathlib import Path
from typing import List, Type

from litereport.adapters.base import BaseAdapter
from litereport.adapters.json_adapter import JsonAdapter
from litereport.adapters.junit_adapter import JUnitXMLAdapter

ADAPTERS: List[Type[BaseAdapter]] = [JsonAdapter, JUnitXMLAdapter]


def auto_detect(source: Path) -> BaseAdapter:
    """Auto-detect the appropriate adapter for a file."""
    source = Path(source)
    for adapter_cls in ADAPTERS:
        if adapter_cls.can_handle(source):
            return adapter_cls()
    raise ValueError(f"Cannot detect file format: {source}")


__all__ = ["BaseAdapter", "JsonAdapter", "JUnitXMLAdapter", "auto_detect"]
