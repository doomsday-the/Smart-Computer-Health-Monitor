"""
Application configuration and threshold definitions.
Provides sensible defaults, validation, and serialization.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "health_monitor.db"
DEFAULT_LOG_PATH = BASE_DIR / "health_monitor.log"


@dataclass
class MonitorSettings:
    # Thresholds (percentage 0.0 - 100.0)
    cpu_warning_pct: float = 70.0
    cpu_critical_pct: float = 90.0
    
    ram_warning_pct: float = 70.0
    ram_critical_pct: float = 85.0
    
    disk_warning_pct: float = 70.0
    disk_critical_pct: float = 90.0
    
    battery_warning_pct: float = 30.0
    battery_critical_pct: float = 15.0
    
    # Timing & Persistence
    monitoring_interval_sec: float = 2.0
    sustained_samples: int = 3  # Number of consecutive samples to trigger sustained condition
    alert_cooldown_sec: float = 60.0
    history_retention_days: int = 7
    
    # Behavior
    auto_start_monitoring: bool = True
    theme: str = "dark_navy"

    def validate(self) -> Tuple[bool, str]:
        """Validate settings consistency and bounds."""
        if not (0.0 <= self.cpu_warning_pct < self.cpu_critical_pct <= 100.0):
            return False, "CPU warning threshold must be less than critical threshold and within 0-100%."
        if not (0.0 <= self.ram_warning_pct < self.ram_critical_pct <= 100.0):
            return False, "RAM warning threshold must be less than critical threshold and within 0-100%."
        if not (0.0 <= self.disk_warning_pct < self.disk_critical_pct <= 100.0):
            return False, "Disk warning threshold must be less than critical threshold and within 0-100%."
        if not (0.0 <= self.battery_critical_pct < self.battery_warning_pct <= 100.0):
            return False, "Battery critical threshold must be less than warning threshold and within 0-100%."
        if not (0.5 <= self.monitoring_interval_sec <= 60.0):
            return False, "Monitoring interval must be between 0.5s and 60.0s."
        if not (1 <= self.sustained_samples <= 30):
            return False, "Sustained samples must be between 1 and 30."
        if not (5.0 <= self.alert_cooldown_sec <= 3600.0):
            return False, "Alert cooldown must be between 5s and 3600s."
        if not (1 <= self.history_retention_days <= 90):
            return False, "History retention must be between 1 and 90 days."
        return True, ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonitorSettings":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        # Cast numerical fields safely
        for float_field in ["cpu_warning_pct", "cpu_critical_pct", "ram_warning_pct", 
                            "ram_critical_pct", "disk_warning_pct", "disk_critical_pct",
                            "battery_warning_pct", "battery_critical_pct", 
                            "monitoring_interval_sec", "alert_cooldown_sec"]:
            if float_field in filtered:
                try:
                    filtered[float_field] = float(filtered[float_field])
                except (ValueError, TypeError):
                    pass
        for int_field in ["sustained_samples", "history_retention_days"]:
            if int_field in filtered:
                try:
                    filtered[int_field] = int(filtered[int_field])
                except (ValueError, TypeError):
                    pass
        return cls(**filtered)
