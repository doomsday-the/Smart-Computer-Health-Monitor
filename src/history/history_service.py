"""
Historical Performance Analysis Service.
Queries stored metrics across configurable time windows (15m, 1h, 6h, 24h, custom)
and computes aggregations, peaks, averages, and trend comparisons.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from src.database.db_manager import DatabaseManager

logger = logging.getLogger("HealthMonitor.HistoryService")


@dataclass
class MetricSummary:
    count: int
    avg_cpu: float
    peak_cpu: float
    min_cpu: float
    
    avg_ram: float
    peak_ram: float
    min_ram: float
    
    avg_health_score: float
    min_health_score: float
    
    avg_disk_read_kb: float
    avg_disk_write_kb: float
    peak_disk_read_kb: float
    peak_disk_write_kb: float


class HistoryService:
    """Provides querying and analytical summaries of historical monitoring data."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_metrics_for_window(self, window_name: str) -> List[Dict[str, Any]]:
        """
        Fetch metrics for standard named windows:
        '15m', '1h', '6h', '24h', or all recent.
        """
        minutes_map = {
            "15m": 15,
            "1h": 60,
            "6h": 360,
            "24h": 1440
        }
        mins = minutes_map.get(window_name, 60)
        return self.db.get_metrics_time_window(mins)

    def get_metrics_custom_range(self, start_iso: str, end_iso: str) -> List[Dict[str, Any]]:
        """Fetch metrics for a custom date-time range."""
        return self.db.get_metrics_in_range(start_iso, end_iso)

    def calculate_summary(self, records: List[Dict[str, Any]]) -> Optional[MetricSummary]:
        """Compute statistical aggregates from a list of metric records."""
        if not records:
            return None

        cpus = [float(r.get("cpu_percent", 0.0)) for r in records]
        rams = [float(r.get("ram_percent", 0.0)) for r in records]
        scores = [float(r.get("health_score", 100.0)) for r in records]
        reads_kb = [float(r.get("disk_read_bytes", 0.0)) / 1024.0 for r in records]
        writes_kb = [float(r.get("disk_write_bytes", 0.0)) / 1024.0 for r in records]

        return MetricSummary(
            count=len(records),
            avg_cpu=round(sum(cpus) / len(cpus), 1),
            peak_cpu=round(max(cpus), 1),
            min_cpu=round(min(cpus), 1),
            avg_ram=round(sum(rams) / len(rams), 1),
            peak_ram=round(max(rams), 1),
            min_ram=round(min(rams), 1),
            avg_health_score=round(sum(scores) / len(scores), 1),
            min_health_score=round(min(scores), 1),
            avg_disk_read_kb=round(sum(reads_kb) / len(reads_kb), 1),
            avg_disk_write_kb=round(sum(writes_kb) / len(writes_kb), 1),
            peak_disk_read_kb=round(max(reads_kb), 1),
            peak_disk_write_kb=round(max(writes_kb), 1)
        )
