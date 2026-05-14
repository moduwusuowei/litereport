"""Base adapter interface for test data parsing."""

from abc import ABC, abstractmethod
from pathlib import Path

from litereport.models import ReportData


class BaseAdapter(ABC):
    """Abstract base class for test data adapters."""

    @abstractmethod
    def parse(self, source: Path) -> ReportData:
        """Parse a test data file into ReportData."""
        ...

    @classmethod
    @abstractmethod
    def can_handle(cls, source: Path) -> bool:
        """Check if this adapter can handle the given file."""
        ...
