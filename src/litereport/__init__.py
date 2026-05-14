"""LiteReport — Lightweight test report visualization."""

__version__ = "1.0.0"

from litereport.models import TestResult, ReportData
from litereport.config import LiteReportConfig
from litereport.generator import ReportGenerator

__all__ = ["TestResult", "ReportData", "LiteReportConfig", "ReportGenerator", "__version__"]
